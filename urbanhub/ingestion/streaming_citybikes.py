"""Flux STREAMING - Disponibilite temps reel des velos (CityBikes).

Source : https://api.citybik.es/v2/

Systeme de recuperation automatique (par defaut toutes les minutes) des donnees
de stations des principaux reseaux francais. Pour chaque station on extrait :
    station_id, station_name, latitude, longitude,
    bikes_available, free_slots, timestamp
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from urbanhub import config
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("ingestion.streaming_citybikes")


def list_france_networks() -> list[dict[str, Any]]:
    """Retourne les reseaux de velos en libre-service situes en France."""
    url = f"{config.CITYBIKES.base_url}/networks"
    resp = requests.get(url, params={"fields": "id,name,location"},
                        timeout=config.CITYBIKES.request_timeout)
    resp.raise_for_status()
    networks = resp.json().get("networks", [])
    fr = [n for n in networks
          if n.get("location", {}).get("country") == config.CITYBIKES.country_code]
    log.info("Reseaux CityBikes en France : %d", len(fr))
    return fr


def _network_snapshot(network_id: str, network_name: str, city: str,
                      ts: datetime) -> list[dict[str, Any]]:
    """Recupere l'etat instantane de toutes les stations d'un reseau."""
    url = f"{config.CITYBIKES.base_url}/networks/{network_id}"
    resp = requests.get(url, timeout=config.CITYBIKES.request_timeout)
    resp.raise_for_status()
    stations = resp.json().get("network", {}).get("stations", []) or []
    rows = []
    for s in stations:
        extra = s.get("extra", {}) or {}
        rows.append({
            "network_id": network_id,
            "network_name": network_name,
            "city": city,
            "station_id": s.get("id") or extra.get("uid"),
            "station_name": s.get("name"),
            "latitude": s.get("latitude"),
            "longitude": s.get("longitude"),
            "bikes_available": s.get("free_bikes"),
            "free_slots": s.get("empty_slots"),
            "timestamp": ts.isoformat(),
        })
    return rows


def collect_once(networks: list[dict[str, Any]] | None = None,
                 dest_dir: Path | None = None) -> pd.DataFrame:
    """Effectue une passe de collecte (un snapshot) sur tous les reseaux FR."""
    dest_dir = dest_dir or config.RAW_CITYBIKES_DIR
    networks = networks if networks is not None else list_france_networks()
    ts = datetime.now(timezone.utc)

    all_rows: list[dict[str, Any]] = []
    for n in networks:
        city = n.get("location", {}).get("city", "")
        try:
            all_rows.extend(_network_snapshot(n["id"], n.get("name", ""), city, ts))
        except requests.RequestException as exc:  # pragma: no cover - reseau
            log.warning("Reseau %s indisponible : %s", n.get("id"), exc)

    df = pd.DataFrame(all_rows)
    if df.empty:
        log.warning("Aucune station collectee lors de ce snapshot.")
        return df

    # Ecriture partitionnee par date (JSON Lines) dans la zone raw
    part = dest_dir / storage.date_partition(ts)
    out = part / f"snapshot_{ts:%Y%m%dT%H%M%S}.jsonl"
    storage.append_jsonl(all_rows, out)
    log.info("Snapshot velos : %d stations sur %d reseaux -> %s",
             len(df), len(networks), out)
    return df


def stream(
    iterations: int | None = None,
    duration_sec: int | None = None,
    interval_sec: int | None = None,
    dest_dir: Path | None = None,
) -> int:
    """Boucle de streaming : collecte periodique des donnees velos.

    Args:
        iterations   : nombre de passes (prioritaire sur duration_sec).
        duration_sec : duree totale d'execution en secondes.
        interval_sec : intervalle entre deux collectes (defaut : 60s).

    Returns:
        Nombre de snapshots realises.
    """
    interval = interval_sec or config.CITYBIKES.poll_interval_sec
    networks = list_france_networks()
    start = time.monotonic()
    count = 0

    while True:
        collect_once(networks, dest_dir)
        count += 1

        if iterations is not None and count >= iterations:
            break
        if duration_sec is not None and (time.monotonic() - start) >= duration_sec:
            break
        if iterations is None and duration_sec is None:
            break  # une seule passe par defaut

        log.info("Attente de %ds avant la prochaine collecte...", interval)
        time.sleep(interval)

    log.info("Streaming termine : %d snapshots realises.", count)
    return count
