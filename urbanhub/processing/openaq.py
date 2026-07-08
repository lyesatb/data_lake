"""Traitement des donnees de pollution (OpenAQ / flux IoT simule).

Consolide les mesures JSON Lines en un jeu long (une ligne = une mesure) puis
produit egalement une vue pivotee (une colonne par polluant) par ville/heure.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from urbanhub import config
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("processing.openaq")


def process_openaq(raw_dir: Path | None = None,
                   out_path: Path | None = None) -> pd.DataFrame:
    raw_dir = raw_dir or config.RAW_OPENAQ_DIR
    out_path = out_path or (config.PROC_OPENAQ_DIR / "pollution.parquet")

    df = storage.read_jsonl_dir(raw_dir)
    if df.empty:
        log.warning("Aucune mesure de pollution a traiter.")
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["timestamp", "parameter", "value"])
    df["parameter"] = df["parameter"].str.lower()
    df = df[df["value"] >= 0]

    df["hour"] = df["timestamp"].dt.floor("h")
    df["date"] = df["timestamp"].dt.date.astype("string")

    df = df.drop_duplicates(subset=["location_id", "parameter", "timestamp"])
    storage.write_parquet(df, out_path)
    log.info("Pollution nettoyee : %d mesures, %d villes, polluants=%s",
             len(df), df["city"].nunique(), sorted(df["parameter"].unique()))
    return df


def pivot_city_hour(df: pd.DataFrame | None = None,
                    out_path: Path | None = None) -> pd.DataFrame:
    """Vue pivotee ville x heure : une colonne par polluant (moyenne)."""
    if df is None:
        df = storage.read_parquet(config.PROC_OPENAQ_DIR / "pollution.parquet")
    out_path = out_path or (config.PROC_OPENAQ_DIR / "pollution_city_hour.parquet")
    if df.empty:
        return df

    pivot = (
        df.groupby(["city", "hour", "parameter"])["value"].mean()
        .unstack("parameter")
        .reset_index()
    )
    storage.write_parquet(pivot, out_path)
    return pivot
