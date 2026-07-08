"""Couche d'acces au data lake.

Fournit des helpers pour ecrire / lire des donnees dans les differentes zones
(raw, processed, curated) avec un partitionnement par date, et gere de maniere
transparente les formats Parquet / CSV / JSON.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from urbanhub.utils.logging_utils import get_logger

log = get_logger("storage")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def date_partition(dt: datetime | None = None) -> str:
    """Chemin de partition type Hive : year=YYYY/month=MM/day=DD."""
    dt = dt or utcnow()
    return f"year={dt:%Y}/month={dt:%m}/day={dt:%d}"


def write_parquet(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    log.info("Parquet ecrit : %s (%d lignes)", path, len(df))
    return path


def read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def read_parquet_dir(directory: Path, pattern: str = "**/*.parquet") -> pd.DataFrame:
    """Concatene tous les parquet d'un repertoire (partitionne ou non)."""
    files = sorted(Path(directory).glob(pattern))
    if not files:
        return pd.DataFrame()
    frames = [pd.read_parquet(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def append_jsonl(records: list[dict[str, Any]], path: Path) -> Path:
    """Ajoute des enregistrements dans un fichier JSON Lines (append)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    return path


def read_jsonl_dir(directory: Path, pattern: str = "**/*.jsonl") -> pd.DataFrame:
    files = sorted(Path(directory).glob(pattern))
    if not files:
        return pd.DataFrame()
    frames = []
    for f in files:
        try:
            frames.append(pd.read_json(f, lines=True))
        except ValueError:
            continue
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def write_json(obj: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2, default=str)
    log.info("JSON ecrit : %s", path)
    return path


def write_csv(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log.info("CSV ecrit : %s (%d lignes)", path, len(df))
    return path
