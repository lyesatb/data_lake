"""Analyse CROISEE des trois flux - reponses aux questions metier (Partie 4).

Questions traitees :
    Q1. Existe-t-il une relation entre conditions meteo et pollution ?
    Q2. Les conditions meteo influencent-elles l'utilisation des velos ?
    Q3. Peut-on identifier des conditions meteo favorables a la mobilite douce ?
    Q4. Existe-t-il des periodes ou mobilite, pollution et meteo interagissent ?

Difficulte structurelle : les trois flux n'ont pas la meme profondeur temporelle
(meteo = historique batch pluriannuel ; velos et pollution = flux temps reel).
Un croisement sur l'horodatage exact serait donc quasi vide.

Solution : on croise sur le CYCLE DIURNE (heure de la journee 0-23). Chaque flux
est reduit a son profil journalier typique (moyenne par heure), ce qui est
robuste, physiquement pertinent (cycles jour/nuit, pics de trafic, photochimie
de l'ozone) et toujours calculable. Un croisement complementaire sur l'horodatage
exact est egalement tente pour la fenetre temps reel recente.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from urbanhub import config
from urbanhub.processing import openaq as openaq_proc
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("analysis.cross")


def _load(path):
    return storage.read_parquet(path) if path.exists() else pd.DataFrame()


def _weather_diurnal() -> pd.DataFrame:
    w = _load(config.PROC_WEATHER_DIR / "weather_hourly.parquet")
    if w.empty:
        return w
    w = w.copy()
    w["hod"] = w["timestamp"].dt.hour
    return w.groupby("hod").agg(
        temperature_c=("temperature_c", "mean"),
        humidity_pct=("humidity_pct", "mean"),
        wind_speed_ms=("wind_speed_ms", "mean"),
        visibility_m=("visibility_m", "mean"),
        precip_mm=("precip_mm", "mean"),
    )


def _pollution_diurnal() -> pd.DataFrame:
    p = _load(config.PROC_OPENAQ_DIR / "pollution.parquet")
    if p.empty:
        return p
    p = p.copy()
    p["hod"] = p["timestamp"].dt.hour
    return p.groupby(["hod", "parameter"])["value"].mean().unstack("parameter")


def _bikes_diurnal() -> pd.DataFrame:
    b = _load(config.PROC_CITYBIKES_DIR / "citybikes.parquet")
    if b.empty:
        return b
    b = b.copy()
    b["hod"] = b["timestamp"].dt.hour
    return b.groupby("hod").agg(
        bikes_available=("bikes_available", "mean"),
        occupancy_rate=("occupancy_rate", "mean"),
    )


def _corr(df: pd.DataFrame, xs: list[str], ys: list[str]) -> dict:
    """Correlations entre variables meteo (xs) et cibles (ys) sur profils diurnes."""
    n = len(df)
    if n < 5:
        return {"disponible": False, "n_heures": int(n),
                "message": "Moins de 5 heures distinctes : recouvrement insuffisant."}
    out = {"disponible": True, "n_heures": int(n), "correlations": {}}
    for y in ys:
        if y not in df:
            continue
        cc = {}
        for x in xs:
            if x not in df:
                continue
            pair = df[[x, y]].dropna()
            if len(pair) >= 5 and pair[x].std() > 0 and pair[y].std() > 0:
                cc[x] = round(float(pair[x].corr(pair[y])), 3)
        if cc:
            out["correlations"][y] = cc
    return out


def run() -> dict:
    weather = _weather_diurnal()
    pollution = _pollution_diurnal()
    bikes = _bikes_diurnal()

    indicators: dict = {
        "methode": "Croisement sur le cycle diurne (heure de la journee, 0-23).",
        "couverture_heures": {
            "weather": int(len(weather)),
            "pollution": int(len(pollution)),
            "bikes": int(len(bikes)),
        },
    }

    # --- Q1 : meteo x pollution ---
    if not weather.empty and not pollution.empty:
        wp = weather.join(pollution, how="inner")
        pol_cols = [c for c in config.OPENAQ.pollutants if c in wp.columns]
        indicators["q1_meteo_pollution"] = _corr(
            wp, ["temperature_c", "humidity_pct", "wind_speed_ms"], pol_cols)
    else:
        indicators["q1_meteo_pollution"] = {"disponible": False}

    # --- Q2 : meteo x velos ---
    if not weather.empty and not bikes.empty:
        wb = weather.join(bikes, how="inner")
        indicators["q2_meteo_velos"] = _corr(
            wb, ["temperature_c", "humidity_pct", "wind_speed_ms", "precip_mm"],
            ["bikes_available", "occupancy_rate"])
    else:
        indicators["q2_meteo_velos"] = {"disponible": False}

    # --- Q3 : conditions favorables a la mobilite douce ---
    indicators["q3_conditions_favorables"] = _favorable_conditions()

    # --- Q4 : triple interaction meteo x pollution x velos ---
    frames = [f for f in (weather, pollution, bikes) if not f.empty]
    if len(frames) == 3:
        triple = weather.join(pollution, how="inner").join(bikes, how="inner")
        indicators["q4_triple_interaction"] = {
            "n_heures_communes": int(len(triple)),
            "profil_diurne": triple.round(2).reset_index().to_dict("records")
            if not triple.empty else [],
        }
        _plot_triple(triple)
    else:
        indicators["q4_triple_interaction"] = {
            "disponible": False,
            "message": "Necessite les trois flux avec >= quelques heures de couverture.",
        }

    storage.write_json(indicators, config.INDICATORS_DIR / "cross_indicators.json")
    return indicators


def _favorable_conditions() -> dict:
    """Conditions meteo favorables a la mobilite douce (velo)."""
    w = _load(config.PROC_WEATHER_DIR / "weather_hourly.parquet")
    definition = {"temperature_c": "[12, 25]", "precip_mm": "= 0", "wind_speed_ms": "< 6"}
    out: dict = {"definition_conditions_favorables": definition}
    if w.empty:
        out["disponible"] = False
        return out
    fav = w[
        w["temperature_c"].between(12, 25)
        & (w["precip_mm"].fillna(0) == 0)
        & (w["wind_speed_ms"].fillna(0) < 6)
    ]
    out["part_heures_favorables_pct"] = round(100 * len(fav) / max(1, len(w)), 2)
    # Repartition saisonniere des heures favorables
    if "season" in w.columns:
        by_season = (
            w.assign(fav=(
                w["temperature_c"].between(12, 25)
                & (w["precip_mm"].fillna(0) == 0)
                & (w["wind_speed_ms"].fillna(0) < 6)))
            .groupby("season")["fav"].mean().mul(100).round(2)
        )
        out["part_favorable_par_saison_pct"] = by_season.to_dict()
    return out


def _plot_triple(triple: pd.DataFrame) -> None:
    try:
        fig, ax1 = plt.subplots(figsize=(9, 4.5))
        ax1.plot(triple.index, triple["temperature_c"], color="#d1495b",
                 marker="o", label="Temperature (C)")
        ax1.set_xlabel("Heure de la journee (UTC)")
        ax1.set_ylabel("Temperature (C)", color="#d1495b")
        ax2 = ax1.twinx()
        if "no2" in triple:
            ax2.plot(triple.index, triple["no2"], color="#9b5de5",
                     marker="s", label="NO2 (ug/m3)")
        if "bikes_available" in triple:
            ax2.plot(triple.index, triple["bikes_available"], color="#2a9d8f",
                     marker="^", label="Velos dispo")
        ax2.set_ylabel("Pollution / Velos")
        ax1.set_title("Cycle diurne croise : meteo x pollution x mobilite")
        fig.legend(loc="upper right", bbox_to_anchor=(0.98, 0.96))
        fig.tight_layout()
        fig.savefig(config.REPORTS_DIR / "cross_cycle_diurne.png", dpi=110)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover - rendu
        log.warning("Plot croise ignore : %s", exc)
