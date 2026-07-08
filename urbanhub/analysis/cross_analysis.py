"""Analyse CROISEE des trois flux - reponses aux questions metier (Partie 4).

Questions traitees :
    Q1. Existe-t-il une relation entre conditions meteo et pollution ?
    Q2. Les conditions meteo influencent-elles l'utilisation des velos ?
    Q3. Peut-on identifier des conditions meteo favorables a la mobilite douce ?
    Q4. Existe-t-il des periodes ou mobilite, pollution et meteo interagissent ?

Le croisement se fait sur les cles communes ville x heure. Les trois flux
n'ayant pas la meme profondeur temporelle (meteo = historique batch, velos et
pollution = collectes temps reel), le module aligne ce qui est disponible et
degrade proprement lorsque le recouvrement est insuffisant.
"""
from __future__ import annotations

import pandas as pd

from urbanhub import config
from urbanhub.processing import openaq as openaq_proc
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("analysis.cross")


def _weather_city_hour() -> pd.DataFrame:
    p = config.PROC_WEATHER_DIR / "weather_hourly.parquet"
    if not p.exists():
        return pd.DataFrame()
    w = storage.read_parquet(p)
    if w.empty:
        return w
    w = w[w["city"] != "Autre"].copy()
    w["hour"] = w["timestamp"].dt.floor("h")
    return (
        w.groupby(["city", "hour"])
        .agg(temperature_c=("temperature_c", "mean"),
             humidity_pct=("humidity_pct", "mean"),
             wind_speed_ms=("wind_speed_ms", "mean"),
             precip_mm=("precip_mm", "sum"),
             visibility_m=("visibility_m", "mean"))
        .reset_index()
    )


def _bikes_city_hour() -> pd.DataFrame:
    p = config.PROC_CITYBIKES_DIR / "citybikes.parquet"
    if not p.exists():
        return pd.DataFrame()
    b = storage.read_parquet(p)
    if b.empty:
        return b
    b["hour"] = b["timestamp"].dt.floor("h")
    return (
        b.groupby(["city", "hour"])
        .agg(bikes_available=("bikes_available", "mean"),
             occupancy_rate=("occupancy_rate", "mean"))
        .reset_index()
    )


def _pollution_city_hour() -> pd.DataFrame:
    p = config.PROC_OPENAQ_DIR / "pollution.parquet"
    if not p.exists():
        return pd.DataFrame()
    df = storage.read_parquet(p)
    if df.empty:
        return df
    return openaq_proc.pivot_city_hour(df)


def run() -> dict:
    weather = _weather_city_hour()
    bikes = _bikes_city_hour()
    pollution = _pollution_city_hour()

    indicators: dict = {
        "recouvrement": {
            "weather_city_hour": int(len(weather)),
            "bikes_city_hour": int(len(bikes)),
            "pollution_city_hour": int(len(pollution)),
        },
        "note": (
            "Les flux temps reel (velos, pollution) sont collectes pendant "
            "l'execution : le recouvrement temporel avec l'historique meteo batch "
            "grandit a mesure que la plateforme tourne. Les correlations sont "
            "calculees sur l'intersection ville x heure disponible."
        ),
    }

    # --- Q1 : meteo x pollution ---
    if not weather.empty and not pollution.empty:
        wp = weather.merge(pollution, on=["city", "hour"], how="inner")
        indicators["q1_meteo_pollution"] = _corr_block(
            wp, ["temperature_c", "humidity_pct", "wind_speed_ms", "precip_mm"],
            [c for c in config.OPENAQ.pollutants if c in wp.columns])
    else:
        indicators["q1_meteo_pollution"] = {"disponible": False}

    # --- Q2 : meteo x velos ---
    if not weather.empty and not bikes.empty:
        wb = weather.merge(bikes, on=["city", "hour"], how="inner")
        indicators["q2_meteo_velos"] = _corr_block(
            wb, ["temperature_c", "humidity_pct", "wind_speed_ms", "precip_mm", "visibility_m"],
            ["bikes_available", "occupancy_rate"])
    else:
        indicators["q2_meteo_velos"] = {"disponible": False}

    # --- Q3 : conditions favorables a la mobilite douce ---
    indicators["q3_conditions_favorables"] = _favorable_conditions(weather, bikes)

    # --- Q4 : triple interaction meteo x pollution x velos ---
    if not weather.empty and not bikes.empty and not pollution.empty:
        triple = (weather.merge(bikes, on=["city", "hour"], how="inner")
                  .merge(pollution, on=["city", "hour"], how="inner"))
        indicators["q4_triple_interaction"] = {
            "n_points_communs": int(len(triple)),
            "apercu": triple.head(20).round(2).astype(str).to_dict("records")
            if not triple.empty else [],
        }
    else:
        indicators["q4_triple_interaction"] = {"disponible": False, "n_points_communs": 0}

    storage.write_json(indicators, config.INDICATORS_DIR / "cross_indicators.json")
    return indicators


def _corr_block(df: pd.DataFrame, meteo_cols: list[str],
                target_cols: list[str]) -> dict:
    """Matrice de correlation meteo -> cibles, robuste au faible recouvrement."""
    n = len(df)
    result: dict = {"n_points_communs": int(n)}
    if n < 5:
        result["disponible"] = False
        result["message"] = "Recouvrement insuffisant (< 5 points) pour correler."
        return result
    result["disponible"] = True
    corrs = {}
    for tgt in target_cols:
        if tgt not in df:
            continue
        cc = {}
        for m in meteo_cols:
            if m not in df:
                continue
            pair = df[[m, tgt]].dropna()
            if len(pair) >= 5 and pair[m].std() > 0 and pair[tgt].std() > 0:
                cc[m] = round(float(pair[m].corr(pair[tgt])), 3)
        if cc:
            corrs[tgt] = cc
    result["correlations"] = corrs
    return result


def _favorable_conditions(weather: pd.DataFrame, bikes: pd.DataFrame) -> dict:
    """Definit une plage meteo favorable a la mobilite douce (velo).

    Heuristique urbaine : temperature agreable (12-25 C), pas de pluie, vent
    modere (< 6 m/s). Quand le recouvrement le permet, on verifie que ces
    conditions coincident avec une plus forte utilisation des velos.
    """
    definition = {
        "temperature_c": "[12, 25]",
        "precip_mm": "= 0",
        "wind_speed_ms": "< 6",
    }
    out: dict = {"definition_conditions_favorables": definition}
    if weather.empty:
        out["disponible"] = False
        return out

    fav = weather[
        weather["temperature_c"].between(12, 25)
        & (weather["precip_mm"].fillna(0) == 0)
        & (weather["wind_speed_ms"].fillna(0) < 6)
    ]
    out["part_heures_favorables_pct"] = round(100 * len(fav) / max(1, len(weather)), 2)

    if not bikes.empty:
        wb = weather.merge(bikes, on=["city", "hour"], how="inner")
        if len(wb) >= 5:
            wb["favorable"] = (
                wb["temperature_c"].between(12, 25)
                & (wb["precip_mm"].fillna(0) == 0)
                & (wb["wind_speed_ms"].fillna(0) < 6)
            )
            grp = wb.groupby("favorable")["bikes_available"].mean().round(2)
            out["velos_dispo_moyen_par_condition"] = {
                str(k): float(v) for k, v in grp.items()
            }
    return out
