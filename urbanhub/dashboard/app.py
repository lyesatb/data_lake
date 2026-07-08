"""Tableau de bord UrbanHub - Jumeau numerique urbain (Streamlit).

Visualise les indicateurs des trois flux (Batch meteo / Streaming velos /
IoT pollution) et l'analyse croisee, a partir des donnees du data lake.

Lancement :
    streamlit run urbanhub/dashboard/app.py
    # ou
    python -m urbanhub.cli dashboard
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from urbanhub import config

st.set_page_config(page_title="UrbanHub - Smart City", page_icon="🏙️", layout="wide")


# --------------------------------------------------------------------------- #
# Chargement des donnees (avec cache)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_json(path: str) -> dict:
    p = Path(path)
    if p.exists():
        with p.open(encoding="utf-8") as fh:
            return json.load(fh)
    return {}


@st.cache_data(show_spinner=False)
def load_parquet(path: str) -> pd.DataFrame:
    p = Path(path)
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


IND = config.INDICATORS_DIR
REP = config.REPORTS_DIR

weather_ind = load_json(str(IND / "weather_indicators.json"))
mobility_ind = load_json(str(IND / "mobility_indicators.json"))
pollution_ind = load_json(str(IND / "pollution_indicators.json"))
cross_ind = load_json(str(IND / "cross_indicators.json"))

weather_df = load_parquet(str(config.PROC_WEATHER_DIR / "weather_hourly.parquet"))
bikes_df = load_parquet(str(config.PROC_CITYBIKES_DIR / "citybikes.parquet"))
poll_df = load_parquet(str(config.PROC_OPENAQ_DIR / "pollution.parquet"))


def show_img(name: str, caption: str) -> None:
    p = REP / name
    if p.exists():
        st.image(str(p), caption=caption, use_container_width=True)


def records_df(ind: dict, key: str) -> pd.DataFrame:
    data = ind.get(key)
    if isinstance(data, list) and data:
        return pd.DataFrame(data)
    return pd.DataFrame()


# --------------------------------------------------------------------------- #
# En-tete + KPIs globaux
# --------------------------------------------------------------------------- #
st.title("🏙️ UrbanHub — Jumeau numérique urbain")
st.caption("Plateforme Smart City : ingestion & analyse de 3 flux Big Data "
           "(Batch météo · Streaming vélos · IoT pollution)")

if not any([weather_ind, mobility_ind, pollution_ind]):
    st.warning(
        "Aucun indicateur trouvé. Lance d'abord le pipeline :\n\n"
        "`python -m urbanhub.cli pipeline --demo --iot-backfill 72`"
    )

c1, c2, c3, c4 = st.columns(4)
c1.metric("🌡️ Observations météo", f"{weather_ind.get('n_observations', 0):,}".replace(",", " "))
c2.metric("🚲 Stations vélos", f"{mobility_ind.get('n_stations', 0):,}".replace(",", " "))
c3.metric("🏭 Mesures pollution", f"{pollution_ind.get('n_mesures', 0):,}".replace(",", " "))
c4.metric("🌍 Villes suivies", pollution_ind.get("n_villes", 0))

tab_meteo, tab_velos, tab_poll, tab_cross = st.tabs(
    ["🌡️ Météo (Batch)", "🚲 Mobilité (Streaming)", "🏭 Pollution (IoT)", "🔀 Analyse croisée"]
)


# --------------------------------------------------------------------------- #
# Onglet 1 : Meteo
# --------------------------------------------------------------------------- #
with tab_meteo:
    st.subheader("Flux Batch — Météo NOAA (France)")
    if weather_ind:
        periode = weather_ind.get("periode", ["?", "?"])
        st.caption(f"Période : {periode[0]} → {periode[1]} · "
                   f"{weather_ind.get('n_stations', 0)} stations")

    left, right = st.columns(2)
    with left:
        st.markdown("**Évolution saisonnière de la température (France)**")
        season = weather_ind.get("q3_temperature_saisonniere_france", {})
        if season:
            order = ["Hiver", "Printemps", "Ete", "Automne"]
            s = pd.Series(season).reindex([o for o in order if o in season])
            st.bar_chart(s)
        show_img("weather_saisonnier.png", "Cycle mensuel de la température")
    with right:
        st.markdown("**Corrélation des variables météo avec la visibilité**")
        corr = weather_ind.get("q2_correlation_visibilite", {})
        if corr:
            st.bar_chart(pd.Series(corr))
        show_img("weather_anomalies.png", "Anomalies de température (z-score)")

    st.markdown("**Jours aux conditions extrêmes**")
    extremes = weather_ind.get("q4_jours_extremes", {})
    if extremes:
        rows = []
        for k, v in extremes.items():
            if isinstance(v, dict) and v:
                metric = [kk for kk in v if kk != "day"]
                rows.append({"Événement": k.replace("_", " "),
                             "Date": v.get("day"),
                             "Valeur": v.get(metric[0]) if metric else None})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("**Périodes météo anormales détectées** "
                "(z-score ≥ 2.5 vs normale mensuelle)")
    anom = weather_ind.get("q1_periodes_anormales", {})
    an_df = records_df(anom, "top_anomalies")
    if not an_df.empty:
        st.dataframe(an_df, use_container_width=True, hide_index=True)
    else:
        st.info(f"{anom.get('nombre_jours_anormaux', 0)} jour(s) anormal(aux).")


# --------------------------------------------------------------------------- #
# Onglet 2 : Mobilite
# --------------------------------------------------------------------------- #
with tab_velos:
    st.subheader("Flux Streaming — Vélos en libre-service (CityBikes)")
    if mobility_ind:
        m1, m2, m3 = st.columns(3)
        m1.metric("Réseaux", mobility_ind.get("n_reseaux", 0))
        m2.metric("Stations", f"{mobility_ind.get('n_stations', 0):,}".replace(",", " "))
        m3.metric("Snapshots collectés", mobility_ind.get("n_snapshots", 0))

    if not bikes_df.empty and {"latitude", "longitude"}.issubset(bikes_df.columns):
        st.markdown("**Carte des stations vélos (dernier snapshot)**")
        last_ts = bikes_df["timestamp"].max()
        geo = bikes_df[bikes_df["timestamp"] == last_ts][["latitude", "longitude"]].dropna()
        if not geo.empty:
            st.map(geo, size=20)

    left, right = st.columns(2)
    with left:
        st.markdown("**Stations les plus sollicitées** (taux d'occupation)")
        df = records_df(mobility_ind, "q1_stations_plus_utilisees")
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True, height=300)
        show_img("mobility_profil_horaire.png", "Profil horaire de disponibilité")
    with right:
        st.markdown("**Stations critiques à rééquilibrer** (pénurie / saturation)")
        df = records_df(mobility_ind, "q5_stations_critiques")
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True, height=300)
        else:
            st.info("Pas de station critique détectée sur cet échantillon.")

    st.markdown("**Déséquilibres par ville**")
    df = records_df(mobility_ind, "q4_desequilibres_villes")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------- #
# Onglet 3 : Pollution
# --------------------------------------------------------------------------- #
with tab_poll:
    st.subheader("Flux IoT — Pollution atmosphérique (OpenAQ)")
    mode = pollution_ind.get("mode_source", [])
    if mode:
        st.caption(f"Source des mesures : {', '.join(mode)} · "
                   f"Polluants : {', '.join(pollution_ind.get('polluants', []))}")

    left, right = st.columns(2)
    with left:
        st.markdown("**Classement des villes par niveau de pollution**")
        aqi = pollution_ind.get("q4_indice_qualite_air", {}).get("classement", [])
        if aqi:
            aqi_df = pd.DataFrame(aqi).set_index("city")["indice"]
            st.bar_chart(aqi_df)
        show_img("pollution_classement_villes.png", "Indice qualité de l'air par ville")
    with right:
        st.markdown("**Profil horaire des polluants**")
        hp = records_df(pollution_ind, "q2_profil_horaire")
        if not hp.empty and "h" in hp.columns:
            st.line_chart(hp.set_index("h"))

    st.markdown("**Concentration moyenne par ville et polluant** (µg/m³)")
    df = records_df(pollution_ind, "q1_moyenne_par_ville")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("**Dépassements de seuils** (référentiel OMS indicatif)")
    dep = pollution_ind.get("q3_depassements_seuils", {})
    if dep:
        st.caption(f"Total dépassements : {dep.get('total_depassements', 0)}")
        top = pd.DataFrame(dep.get("top", []))
        if not top.empty:
            st.dataframe(top, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------- #
# Onglet 4 : Analyse croisee
# --------------------------------------------------------------------------- #
with tab_cross:
    st.subheader("Analyse croisée — Météo × Pollution × Mobilité")
    st.caption(cross_ind.get("methode", ""))
    cov = cross_ind.get("couverture_heures", {})
    if cov:
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Heures météo", cov.get("weather", 0))
        cc2.metric("Heures pollution", cov.get("pollution", 0))
        cc3.metric("Heures vélos", cov.get("bikes", 0))

    st.markdown("### Q1 — Relation météo ↔ pollution")
    q1 = cross_ind.get("q1_meteo_pollution", {})
    if q1.get("disponible"):
        corr = q1.get("correlations", {})
        if corr:
            mat = pd.DataFrame(corr).T.round(2)  # lignes = polluants, colonnes = météo
            st.dataframe(mat, use_container_width=True)
            st.caption("Corrélation forte attendue : Ozone (O₃) ↔ température "
                       "(formation photochimique).")
    else:
        st.info("Recouvrement insuffisant — lance un backfill IoT plus long.")

    show_img("cross_cycle_diurne.png", "Cycle diurne conjoint météo × pollution × mobilité")

    st.markdown("### Q2 — La météo influence-t-elle l'usage des vélos ?")
    q2 = cross_ind.get("q2_meteo_velos", {})
    if q2.get("disponible"):
        corr = q2.get("correlations", {})
        if corr:
            st.dataframe(pd.DataFrame(corr).T.round(2), use_container_width=True)
    else:
        st.info("Nécessite que le flux vélos ait tourné sur l'ensemble de la "
                "journée (ex. `stream --iterations 1440 --interval 60`).")

    st.markdown("### Q3 — Conditions météo favorables à la mobilité douce")
    q3 = cross_ind.get("q3_conditions_favorables", {})
    if q3:
        st.write("Définition :", q3.get("definition_conditions_favorables", {}))
        cA, cB = st.columns(2)
        cA.metric("Part d'heures favorables", f"{q3.get('part_heures_favorables_pct', 0)} %")
        saison = q3.get("part_favorable_par_saison_pct", {})
        if saison:
            cB.bar_chart(pd.Series(saison))

st.divider()
st.caption("UrbanHub · données data lake `data/curated` · "
           "régénérer : `python -m urbanhub.cli pipeline --demo --iot-backfill 72`")
