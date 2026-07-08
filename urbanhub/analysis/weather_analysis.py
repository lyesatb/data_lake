"""Analyse du flux BATCH meteo - reponses aux questions metier.

Questions traitees :
    Q1. Peut-on identifier des periodes meteorologiques anormales ?
    Q2. Existe-t-il une correlation entre conditions meteo et visibilite ?
    Q3. Quelle est l'evolution saisonniere de la temperature (France + villes) ?
    Q4. Quels sont les jours a conditions meteorologiques extremes ?
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from urbanhub import config
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("analysis.weather")


def _load() -> pd.DataFrame:
    return storage.read_parquet(config.PROC_WEATHER_DIR / "weather_hourly.parquet")


def run(df: pd.DataFrame | None = None) -> dict:
    df = df if df is not None else _load()
    if df.empty:
        log.warning("Pas de donnees meteo pour l'analyse.")
        return {}

    indicators: dict = {"n_observations": int(len(df)),
                        "n_stations": int(df["station_id"].nunique()),
                        "periode": [str(df["timestamp"].min()), str(df["timestamp"].max())]}

    daily = (
        df.assign(day=df["timestamp"].dt.date)
        .groupby("day")
        .agg(temperature_c=("temperature_c", "mean"),
             tmin=("temperature_c", "min"),
             tmax=("temperature_c", "max"),
             precip_mm=("precip_mm", "sum"),
             wind_speed_ms=("wind_speed_ms", "max"),
             visibility_m=("visibility_m", "mean"))
        .reset_index()
    )

    # --- Q1 : periodes anormales (z-score de la temperature moyenne mensuelle) ---
    daily["day"] = pd.to_datetime(daily["day"])
    daily["month"] = daily["day"].dt.month
    monthly_ref = daily.groupby("month")["temperature_c"].agg(["mean", "std"])
    daily = daily.join(monthly_ref, on="month", rsuffix="_ref")
    daily["temp_zscore"] = (daily["temperature_c"] - daily["mean"]) / daily["std"]
    anomalies = daily[daily["temp_zscore"].abs() >= 2.5].sort_values(
        "temp_zscore", key=lambda s: s.abs(), ascending=False)
    indicators["q1_periodes_anormales"] = {
        "definition": "Jours dont la temperature moyenne s'ecarte de >= 2.5 ecarts-types de la normale mensuelle",
        "nombre_jours_anormaux": int(len(anomalies)),
        "top_anomalies": anomalies.head(10)[
            ["day", "temperature_c", "temp_zscore"]].assign(
            day=lambda d: d["day"].astype(str)).to_dict("records"),
    }

    # --- Q2 : correlation conditions meteo / visibilite ---
    corr_vars = ["visibility_m", "temperature_c", "humidity_pct",
                 "wind_speed_ms", "precip_mm", "pressure_hpa"]
    sub = df[corr_vars].dropna()
    if len(sub) > 10:
        corr = sub.corr()["visibility_m"].drop("visibility_m").round(3)
        indicators["q2_correlation_visibilite"] = corr.to_dict()

    # --- Q3 : evolution saisonniere de la temperature ---
    season_fr = df.groupby("season")["temperature_c"].mean().round(2)
    season_city = (
        df[df["city"] != "Autre"]
        .groupby(["city", "season"])["temperature_c"].mean().round(2)
        .unstack("season")
    )
    indicators["q3_temperature_saisonniere_france"] = season_fr.to_dict()
    indicators["q3_temperature_saisonniere_villes"] = season_city.reset_index().to_dict("records")

    # --- Q4 : jours extremes ---
    extremes = {
        "jour_plus_chaud": _extreme_day(daily, "tmax", "idxmax"),
        "jour_plus_froid": _extreme_day(daily, "tmin", "idxmin"),
        "jour_plus_pluvieux": _extreme_day(daily, "precip_mm", "idxmax"),
        "jour_plus_vente": _extreme_day(daily, "wind_speed_ms", "idxmax"),
    }
    indicators["q4_jours_extremes"] = extremes

    _plot_seasonal(df)
    _plot_anomalies(daily)

    storage.write_json(indicators, config.INDICATORS_DIR / "weather_indicators.json")
    storage.write_csv(daily, config.INDICATORS_DIR / "weather_daily.csv")
    return indicators


def _extreme_day(daily: pd.DataFrame, col: str, how: str) -> dict:
    d = daily.dropna(subset=[col])
    if d.empty:
        return {}
    idx = getattr(d[col], how)()
    row = d.loc[idx]
    return {"day": str(row["day"].date()), col: round(float(row[col]), 2)}


def _plot_seasonal(df: pd.DataFrame) -> None:
    try:
        monthly = df.groupby(df["timestamp"].dt.month)["temperature_c"].mean()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(monthly.index, monthly.values, marker="o", color="#d1495b")
        ax.set_xlabel("Mois")
        ax.set_ylabel("Temperature moyenne (C)")
        ax.set_title("Evolution saisonniere de la temperature - France")
        ax.set_xticks(range(1, 13))
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(config.REPORTS_DIR / "weather_saisonnier.png", dpi=110)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover - rendu
        log.warning("Plot saisonnier ignore : %s", exc)


def _plot_anomalies(daily: pd.DataFrame) -> None:
    try:
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(daily["day"], daily["temp_zscore"], color="#3a6ea5", lw=0.8)
        ax.axhline(2.5, color="red", ls="--", lw=0.8)
        ax.axhline(-2.5, color="red", ls="--", lw=0.8)
        ax.set_title("Anomalies de temperature (z-score vs normale mensuelle)")
        ax.set_ylabel("z-score")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(config.REPORTS_DIR / "weather_anomalies.png", dpi=110)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover - rendu
        log.warning("Plot anomalies ignore : %s", exc)
