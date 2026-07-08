"""Flux BATCH - Telechargement parallele des donnees meteo NOAA (France).

Source : NOAA Global Hourly (Integrated Surface Database)
    https://www.ncei.noaa.gov/data/global-hourly/access/<annee>/<station>.csv

Strategie :
    1. Recuperer le referentiel des stations `isd-history.csv`.
    2. Filtrer les stations situees en France (CTRY == 'FR') encore actives
       sur la periode demandee (les N dernieres annees).
    3. Telecharger EN PARALLELE (ThreadPoolExecutor) les fichiers
       <station>.csv pour chaque annee (jamais un par un sequentiellement).
"""
from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

from urbanhub import config
from urbanhub.utils.logging_utils import get_logger

log = get_logger("ingestion.batch_weather")


@dataclass
class Station:
    station_id: str      # USAF + WBAN (11 caracteres) = nom de fichier NOAA
    name: str
    lat: float
    lon: float
    elevation: float
    begin: str
    end: str


def fetch_france_stations(years_back: int | None = None) -> list[Station]:
    """Telecharge le referentiel ISD et retourne les stations francaises actives."""
    log.info("Telechargement du referentiel des stations : %s", config.NOAA.isd_history_url)
    resp = requests.get(config.NOAA.isd_history_url, timeout=config.NOAA.request_timeout)
    resp.raise_for_status()

    df = pd.read_csv(io.StringIO(resp.text), dtype=str).fillna("")
    df.columns = [c.strip().upper() for c in df.columns]

    fr = df[df["CTRY"] == config.NOAA.country_code].copy()
    log.info("Stations FR trouvees dans le referentiel : %d", len(fr))

    years = config.noaa_years(years_back)
    start_year = min(years)
    # Ne conserver que les stations encore actives durant la periode demandee
    fr["END_YEAR"] = pd.to_numeric(fr["END"].str[:4], errors="coerce")
    fr = fr[fr["END_YEAR"] >= start_year]

    stations: list[Station] = []
    for _, r in fr.iterrows():
        usaf, wban = r["USAF"].strip(), r["WBAN"].strip()
        if not usaf or not wban or usaf == "999999":
            continue
        station_id = f"{usaf}{wban}"
        try:
            lat = float(r["LAT"]) if r["LAT"] else float("nan")
            lon = float(r["LON"]) if r["LON"] else float("nan")
            elev = float(r["ELEV(M)"]) if r.get("ELEV(M)") else float("nan")
        except ValueError:
            lat = lon = elev = float("nan")
        stations.append(
            Station(station_id, r["STATION NAME"].strip(), lat, lon, elev,
                    r["BEGIN"], r["END"])
        )
    log.info("Stations FR actives sur les %d dernieres annees : %d",
             len(years), len(stations))
    return stations


def _download_one(station: Station, year: int, dest_dir: Path,
                  timeout: int) -> tuple[str, int, str]:
    """Telecharge un fichier <station>.csv pour une annee donnee."""
    url = f"{config.NOAA.access_base_url}/{year}/{station.station_id}.csv"
    out = dest_dir / f"year={year}" / f"{station.station_id}.csv"
    if out.exists() and out.stat().st_size > 0:
        return (station.station_id, year, "cache")
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 404:
            return (station.station_id, year, "absent")
        resp.raise_for_status()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(resp.content)
        return (station.station_id, year, "ok")
    except requests.RequestException as exc:  # pragma: no cover - reseau
        return (station.station_id, year, f"erreur:{exc}")


def download_weather(
    years_back: int | None = None,
    max_stations: int | None = None,
    max_workers: int | None = None,
    dest_dir: Path | None = None,
) -> pd.DataFrame:
    """Telecharge en parallele les fichiers meteo NOAA pour la France.

    Args:
        years_back   : nombre d'annees a remonter (defaut : config = 5).
        max_stations : limite le nombre de stations (utile pour un run de demo).
        max_workers  : nombre de threads de telechargement parallele.
        dest_dir     : repertoire cible (defaut : data/raw/batch/weather).

    Returns:
        DataFrame recapitulatif des telechargements (station, annee, statut).
    """
    dest_dir = dest_dir or config.RAW_WEATHER_DIR
    max_workers = max_workers or config.NOAA.max_workers
    years = config.noaa_years(years_back)

    stations = fetch_france_stations(years_back)
    if max_stations:
        stations = stations[:max_stations]

    # Persiste le referentiel des stations retenues (utile pour l'analyse par ville)
    meta = pd.DataFrame([s.__dict__ for s in stations])
    (dest_dir).mkdir(parents=True, exist_ok=True)
    meta.to_csv(dest_dir / "stations_fr.csv", index=False)

    tasks = [(s, y) for s in stations for y in years]
    log.info("Lancement de %d telechargements paralleles (%d stations x %d annees, %d threads)",
             len(tasks), len(stations), len(years), max_workers)

    results: list[tuple[str, int, str]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_download_one, s, y, dest_dir, config.NOAA.request_timeout): (s, y)
            for s, y in tasks
        }
        done = 0
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            if done % 50 == 0 or done == len(tasks):
                log.info("Progression : %d/%d", done, len(tasks))

    summary = pd.DataFrame(results, columns=["station_id", "year", "status"])
    counts = summary["status"].value_counts().to_dict()
    log.info("Telechargements termines : %s", counts)
    return summary
