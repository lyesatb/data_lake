"""Analyse du flux STREAMING mobilite (velos) - reponses aux questions metier.

Questions traitees :
    Q1. Quelles stations presentent le plus fort taux d'utilisation ?
    Q2. Peut-on identifier des zones ou l'offre de velos est insuffisante ?
    Q3. Quels sont les pics d'utilisation journaliers du reseau ?
    Q4. Existe-t-il des desequilibres geographiques de disponibilite ?
    Q5. Peut-on detecter des stations critiques a reequilibrer ?
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from urbanhub import config
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("analysis.mobility")


def _load() -> pd.DataFrame:
    return storage.read_parquet(config.PROC_CITYBIKES_DIR / "citybikes.parquet")


def run(df: pd.DataFrame | None = None) -> dict:
    df = df if df is not None else _load()
    if df.empty:
        log.warning("Pas de donnees velos pour l'analyse.")
        return {}

    indicators: dict = {
        "n_observations": int(len(df)),
        "n_stations": int(df["station_id"].nunique()),
        "n_reseaux": int(df["network_id"].nunique()),
        "n_snapshots": int(df["timestamp"].nunique()),
    }

    # Agregation par station (moyenne sur les snapshots)
    per_station = (
        df.groupby(["network_id", "city", "station_id", "station_name"])
        .agg(occupancy_rate=("occupancy_rate", "mean"),
             bikes_available=("bikes_available", "mean"),
             free_slots=("free_slots", "mean"),
             capacity=("capacity", "mean"),
             pct_empty=("is_empty", "mean"),
             pct_full=("is_full", "mean"),
             latitude=("latitude", "first"),
             longitude=("longitude", "first"))
        .reset_index()
    )

    # --- Q1 : stations au plus fort taux d'utilisation ---
    # "utilisation" = rotation forte -> on approxime par le taux de remplissage
    # eleve combine a une forte capacite. On expose les stations les + sollicitees.
    per_station["turnover_proxy"] = per_station["occupancy_rate"] * per_station["capacity"]
    top_use = per_station.sort_values("occupancy_rate", ascending=False).head(15)
    indicators["q1_stations_plus_utilisees"] = top_use[
        ["city", "station_name", "occupancy_rate", "capacity"]
    ].round(3).to_dict("records")

    # --- Q2 : zones ou l'offre est insuffisante (souvent vides) ---
    insufficient = per_station.sort_values("pct_empty", ascending=False).head(15)
    indicators["q2_offre_insuffisante"] = insufficient[
        ["city", "station_name", "pct_empty", "bikes_available"]
    ].round(3).to_dict("records")

    # --- Q3 : pics d'utilisation journaliers (par heure) ---
    hourly = df.groupby("hour").agg(
        bikes_available=("bikes_available", "mean"),
        occupancy_rate=("occupancy_rate", "mean"),
    ).reset_index()
    indicators["q3_profil_horaire"] = hourly.round(3).to_dict("records")

    # --- Q4 : desequilibres geographiques (par ville) ---
    per_city = per_station.groupby("city").agg(
        stations=("station_id", "nunique"),
        occupancy_moy=("occupancy_rate", "mean"),
        pct_empty_moy=("pct_empty", "mean"),
        pct_full_moy=("pct_full", "mean"),
    ).reset_index().sort_values("stations", ascending=False)
    indicators["q4_desequilibres_villes"] = per_city.round(3).to_dict("records")

    # --- Q5 : stations critiques a reequilibrer ---
    # Critique = tres souvent vide (penurie) OU tres souvent pleine (saturation)
    per_station["criticite"] = per_station[["pct_empty", "pct_full"]].max(axis=1)
    per_station["type_critique"] = per_station.apply(
        lambda r: "penurie (vide)" if r["pct_empty"] >= r["pct_full"] else "saturation (pleine)",
        axis=1,
    )
    critical = per_station[per_station["criticite"] >= 0.5].sort_values(
        "criticite", ascending=False).head(20)
    indicators["q5_stations_critiques"] = critical[
        ["city", "station_name", "type_critique", "criticite", "capacity"]
    ].round(3).to_dict("records")

    _plot_hourly(hourly)

    storage.write_json(indicators, config.INDICATORS_DIR / "mobility_indicators.json")
    storage.write_csv(per_station.round(3), config.INDICATORS_DIR / "mobility_stations.csv")
    return indicators


def _plot_hourly(hourly: pd.DataFrame) -> None:
    try:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(hourly["hour"], hourly["bikes_available"], color="#2a9d8f")
        ax.set_xlabel("Heure de la journee")
        ax.set_ylabel("Velos disponibles (moyenne)")
        ax.set_title("Profil horaire de disponibilite des velos")
        ax.grid(alpha=0.3, axis="y")
        fig.tight_layout()
        fig.savefig(config.REPORTS_DIR / "mobility_profil_horaire.png", dpi=110)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover - rendu
        log.warning("Plot horaire ignore : %s", exc)
