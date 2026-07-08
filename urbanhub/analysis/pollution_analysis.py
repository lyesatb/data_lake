"""Analyse du flux IoT pollution - reponses aux questions metier.

Questions traitees :
    Q1. Quelles villes sont les plus polluees (par polluant) ?
    Q2. Quel est le profil horaire des polluants (pics de trafic, ozone) ?
    Q3. Quels episodes depassent les seuils de qualite de l'air ?
    Q4. Comment se classent les villes selon un indice de qualite de l'air ?
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from urbanhub import config
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("analysis.pollution")

# Seuils indicatifs (recommandations OMS / seuils journaliers), en ug/m3
_THRESHOLDS = {"pm25": 15, "pm10": 45, "no2": 25, "o3": 100, "so2": 40, "co": 4}


def _load() -> pd.DataFrame:
    return storage.read_parquet(config.PROC_OPENAQ_DIR / "pollution.parquet")


def run(df: pd.DataFrame | None = None) -> dict:
    df = df if df is not None else _load()
    if df.empty:
        log.warning("Pas de donnees de pollution pour l'analyse.")
        return {}

    indicators: dict = {
        "n_mesures": int(len(df)),
        "n_villes": int(df["city"].nunique()),
        "polluants": sorted(df["parameter"].unique().tolist()),
        "mode_source": sorted(df["source"].unique().tolist()) if "source" in df else [],
    }

    # --- Q1 : villes les plus polluees par polluant ---
    city_pol = df.groupby(["city", "parameter"])["value"].mean().round(2)
    pivot = city_pol.unstack("parameter")
    indicators["q1_moyenne_par_ville"] = pivot.reset_index().round(2).to_dict("records")
    top = {}
    for pol in df["parameter"].unique():
        s = city_pol.xs(pol, level="parameter").sort_values(ascending=False)
        if not s.empty:
            top[pol] = {"ville": s.index[0], "valeur": float(s.iloc[0])}
    indicators["q1_ville_plus_polluee_par_polluant"] = top

    # --- Q2 : profil horaire ---
    df["h"] = df["timestamp"].dt.hour
    hourly = df.groupby(["h", "parameter"])["value"].mean().unstack("parameter")
    indicators["q2_profil_horaire"] = hourly.round(2).reset_index().to_dict("records")

    # --- Q3 : depassements de seuils ---
    df["seuil"] = df["parameter"].map(_THRESHOLDS)
    df["depassement"] = df["value"] > df["seuil"]
    exceed = (
        df[df["depassement"]]
        .groupby(["city", "parameter"]).size()
        .reset_index(name="nb_depassements")
        .sort_values("nb_depassements", ascending=False)
    )
    indicators["q3_depassements_seuils"] = {
        "seuils_ug_m3": _THRESHOLDS,
        "total_depassements": int(df["depassement"].sum()),
        "top": exceed.head(15).to_dict("records"),
    }

    # --- Q4 : indice de qualite de l'air par ville (moyenne normalisee aux seuils) ---
    df["ratio_seuil"] = df["value"] / df["seuil"]
    aqi = (
        df.groupby("city")["ratio_seuil"].mean().sort_values(ascending=False).round(3)
    )
    indicators["q4_indice_qualite_air"] = {
        "definition": "Moyenne des ratios valeur/seuil (1.0 = niveau du seuil). Plus haut = plus pollue.",
        "classement": aqi.reset_index().rename(
            columns={"ratio_seuil": "indice"}).to_dict("records"),
    }

    _plot_city_ranking(aqi)

    storage.write_json(indicators, config.INDICATORS_DIR / "pollution_indicators.json")
    storage.write_csv(pivot.reset_index().round(2),
                      config.INDICATORS_DIR / "pollution_par_ville.csv")
    return indicators


def _plot_city_ranking(aqi: pd.Series) -> None:
    try:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        aqi.sort_values().plot(kind="barh", ax=ax, color="#9b5de5")
        ax.set_xlabel("Indice qualite de l'air (ratio moyen / seuil)")
        ax.set_title("Classement des villes par niveau de pollution")
        ax.grid(alpha=0.3, axis="x")
        fig.tight_layout()
        fig.savefig(config.REPORTS_DIR / "pollution_classement_villes.png", dpi=110)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover - rendu
        log.warning("Plot pollution ignore : %s", exc)
