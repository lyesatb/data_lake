"""Traitement des donnees CityBikes (velos en libre-service).

Consolide les snapshots JSON Lines de la zone raw en un jeu de donnees propre :
    - typage des colonnes numeriques et du timestamp ;
    - calcul de la capacite et du taux d'occupation par station/snapshot ;
    - suppression des enregistrements incoherents.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from urbanhub import config
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("processing.citybikes")


def process_citybikes(raw_dir: Path | None = None,
                      out_path: Path | None = None) -> pd.DataFrame:
    raw_dir = raw_dir or config.RAW_CITYBIKES_DIR
    out_path = out_path or (config.PROC_CITYBIKES_DIR / "citybikes.parquet")

    df = storage.read_jsonl_dir(raw_dir)
    if df.empty:
        log.warning("Aucun snapshot velos a traiter.")
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for col in ("bikes_available", "free_slots", "latitude", "longitude"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["timestamp", "station_id"])
    df["capacity"] = df["bikes_available"].fillna(0) + df["free_slots"].fillna(0)
    df["occupancy_rate"] = np.where(
        df["capacity"] > 0, df["bikes_available"] / df["capacity"], np.nan
    )
    df["is_empty"] = df["bikes_available"].fillna(0) == 0
    df["is_full"] = df["free_slots"].fillna(0) == 0
    df["hour"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date.astype("string")

    df = df.drop_duplicates(subset=["network_id", "station_id", "timestamp"])
    storage.write_parquet(df, out_path)
    log.info("Velos nettoyes : %d observations, %d stations, %d reseaux",
             len(df), df["station_id"].nunique(), df["network_id"].nunique())
    return df
