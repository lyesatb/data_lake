"""Traitement des donnees meteo NOAA (Global Hourly).

Le format ISD encode plusieurs variables dans des champs composites separes par
des virgules, avec des valeurs sentinelles pour les manquants. Ce module :
    - parse les champs WND, TMP, DEW, SLP, VIS, AA1 ;
    - convertit les unites (temperature en degres C, pression en hPa, ...) ;
    - gere les valeurs manquantes (sentinelles 999/9999/99999) ;
    - normalise le timestamp en UTC ;
    - rattache chaque station a la principale ville francaise la plus proche ;
    - ecrit un jeu de donnees propre au format Parquet.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from urbanhub import config
from urbanhub.config import FRANCE_CITIES
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("processing.weather")

# Colonnes brutes utiles du format Global Hourly
_RAW_COLS = ["STATION", "DATE", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME",
             "WND", "TMP", "DEW", "SLP", "VIS", "AA1"]


def _scaled(value: str, scale: float, missing: str) -> float:
    """Convertit une valeur ISD entiere (avec signe) en flottant reel."""
    if value is None:
        return np.nan
    value = value.strip()
    if value == "" or value == missing:
        return np.nan
    try:
        return int(value) / scale
    except ValueError:
        return np.nan


def _parse_temp(field: str) -> float:
    # TMP : "+0102,1" -> 10.2 C ; manquant = +9999
    if not isinstance(field, str):
        return np.nan
    parts = field.split(",")
    return _scaled(parts[0], 10.0, "+9999")


def _parse_pressure(field: str) -> float:
    # SLP : "09981,1" -> 998.1 hPa ; manquant = 99999
    if not isinstance(field, str):
        return np.nan
    parts = field.split(",")
    return _scaled(parts[0], 10.0, "99999")


def _parse_visibility(field: str) -> float:
    # VIS : "008000,1,9,9" -> 8000 m ; manquant = 999999
    if not isinstance(field, str):
        return np.nan
    parts = field.split(",")
    return _scaled(parts[0], 1.0, "999999")


def _parse_wind(field: str) -> tuple[float, float]:
    # WND : "250,1,N,0149,1" -> direction 250 deg, vitesse 14.9 m/s
    if not isinstance(field, str):
        return np.nan, np.nan
    parts = field.split(",")
    if len(parts) < 5:
        return np.nan, np.nan
    direction = _scaled(parts[0], 1.0, "999")
    speed = _scaled(parts[3], 10.0, "9999")
    return direction, speed


def _parse_precip(field: str) -> float:
    # AA1 : "01,0010,3,1" -> periode 1h, 1.0 mm ; manquant = 9999
    if not isinstance(field, str):
        return np.nan
    parts = field.split(",")
    if len(parts) < 2:
        return np.nan
    return _scaled(parts[1], 10.0, "9999")


def _nearest_city(lat: float, lon: float, max_km: float = 40.0) -> str:
    """Rattache une station a la principale ville FR la plus proche (< max_km)."""
    if lat is None or lon is None or math.isnan(lat) or math.isnan(lon):
        return "Autre"
    best, best_d = "Autre", float("inf")
    for c in FRANCE_CITIES:
        # distance approximative (equirectangulaire) suffisante a cette echelle
        dlat = math.radians(c.latitude - lat)
        dlon = math.radians(c.longitude - lon) * math.cos(math.radians(lat))
        d = 6371.0 * math.sqrt(dlat * dlat + dlon * dlon)
        if d < best_d:
            best, best_d = c.name, d
    return best if best_d <= max_km else "Autre"


def _process_file(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, dtype=str, usecols=lambda c: c in _RAW_COLS,
                         low_memory=False)
    except (ValueError, pd.errors.EmptyDataError):
        return pd.DataFrame()
    if df.empty:
        return df

    out = pd.DataFrame()
    out["station_id"] = df["STATION"]
    out["station_name"] = df.get("NAME")
    out["timestamp"] = pd.to_datetime(df["DATE"], utc=True, errors="coerce")
    out["latitude"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
    out["longitude"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
    out["elevation_m"] = pd.to_numeric(df["ELEVATION"], errors="coerce")

    out["temperature_c"] = df["TMP"].map(_parse_temp)
    out["dew_point_c"] = df["DEW"].map(_parse_temp)
    out["pressure_hpa"] = df["SLP"].map(_parse_pressure)
    out["visibility_m"] = df["VIS"].map(_parse_visibility)
    wind = df["WND"].map(_parse_wind)
    out["wind_dir_deg"] = wind.map(lambda t: t[0])
    out["wind_speed_ms"] = wind.map(lambda t: t[1])
    out["precip_mm"] = df["AA1"].map(_parse_precip) if "AA1" in df else np.nan

    # Humidite relative approximee a partir de T et point de rosee (formule Magnus)
    t, td = out["temperature_c"], out["dew_point_c"]
    out["humidity_pct"] = 100 * (
        np.exp((17.625 * td) / (243.04 + td)) / np.exp((17.625 * t) / (243.04 + t))
    )
    out.loc[out["humidity_pct"] > 100, "humidity_pct"] = 100

    out = out.dropna(subset=["timestamp"])
    # Filtre de plausibilite physique
    out = out[(out["temperature_c"].between(-40, 55)) | out["temperature_c"].isna()]
    return out


def process_weather(raw_dir: Path | None = None,
                    out_path: Path | None = None,
                    max_files: int | None = None) -> pd.DataFrame:
    """Parse et nettoie l'ensemble des fichiers meteo bruts -> Parquet propre."""
    raw_dir = raw_dir or config.RAW_WEATHER_DIR
    out_path = out_path or (config.PROC_WEATHER_DIR / "weather_hourly.parquet")

    files = sorted(raw_dir.glob("year=*/*.csv"))
    if max_files:
        files = files[:max_files]
    log.info("Traitement de %d fichiers meteo bruts...", len(files))

    frames = []
    for i, f in enumerate(files, 1):
        part = _process_file(f)
        if not part.empty:
            frames.append(part)
        if i % 25 == 0 or i == len(files):
            log.info("Fichiers traites : %d/%d", i, len(files))

    if not frames:
        log.warning("Aucune donnee meteo exploitable.")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df["city"] = [
        _nearest_city(la, lo) for la, lo in zip(df["latitude"], df["longitude"])
    ]
    df["date"] = df["timestamp"].dt.date.astype("string")
    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month
    df["season"] = df["month"].map(_season)

    df = df.drop_duplicates(subset=["station_id", "timestamp"])
    storage.write_parquet(df, out_path)
    log.info("Meteo nettoyee : %d observations, %d stations, periode %s -> %s",
             len(df), df["station_id"].nunique(),
             df["timestamp"].min(), df["timestamp"].max())
    return df


def _season(month: int) -> str:
    if month in (12, 1, 2):
        return "Hiver"
    if month in (3, 4, 5):
        return "Printemps"
    if month in (6, 7, 8):
        return "Ete"
    return "Automne"
