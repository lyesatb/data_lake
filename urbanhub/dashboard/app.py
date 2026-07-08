"""Tableau de bord UrbanHub - Jumeau numerique urbain (Streamlit).

Visualise les trois flux (Batch meteo / Streaming velos / IoT pollution) et
l'analyse croisee a partir des donnees du data lake. Le tableau de bord est
INTERACTIF : une barre laterale permet de filtrer par ville et par polluant, et
les graphiques sont recalcules dynamiquement a partir des donnees nettoyees.

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

# Seuils indicatifs (OMS) pour la pollution, en ug/m3
THRESHOLDS = {"pm25": 15, "pm10": 45, "no2": 25, "o3": 100, "so2": 40, "co": 4}


# --------------------------------------------------------------------------- #
# Wrappers compatibles toutes versions de Streamlit
# --------------------------------------------------------------------------- #
def safe_dataframe(df: pd.DataFrame, height: int | None = None) -> None:
    """st.dataframe robuste (gere les differences d'API selon la version)."""
    for kw in ({"use_container_width": True, "hide_index": True},
               {"use_container_width": True}, {}):
        try:
            if height:
                st.dataframe(df, height=height, **kw)
            else:
                st.dataframe(df, **kw)
            return
        except TypeError:
            continue
    st.dataframe(df)


def safe_image(path: Path, caption: str) -> None:
    if not path.exists():
        return
    for kw in ({"use_container_width": True}, {"use_column_width": True}, {}):
        try:
            st.image(str(path), caption=caption, **kw)
            return
        except TypeError:
            continue


def safe_map(df: pd.DataFrame) -> None:
    try:
        st.map(df, size=20)
    except TypeError:
        st.map(df)


def dropdown_checkboxes(label: str, options: list, key: str) -> list:
    """Liste deroulante (repliable) a cases a cocher multiples.

    Rend un menu deroulant dans la barre laterale contenant une case par option
    + deux boutons "Tout" / "Aucun". Retourne la liste des options cochees.
    Compatible avec toutes les versions de Streamlit (n'utilise que expander,
    button, checkbox et session_state).
    """
    if not options:
        return []

    def _set_all(value: bool):
        for opt in options:
            st.session_state[f"{key}__{opt}"] = value

    # Etat courant (defaut : tout coche) pour afficher le compteur dans l'entete
    preview = [o for o in options if st.session_state.get(f"{key}__{o}", True)]
    header = f"{label} — {len(preview)}/{len(options)}"

    with st.sidebar.expander(header, expanded=False):
        c1, c2 = st.columns(2)
        c1.button("Tout", key=f"{key}_all", on_click=_set_all, args=(True,))
        c2.button("Aucun", key=f"{key}_none", on_click=_set_all, args=(False,))
        selected = []
        for opt in options:
            cbkey = f"{key}__{opt}"
            if cbkey not in st.session_state:
                st.session_state[cbkey] = True
            if st.checkbox(str(opt), key=cbkey):
                selected.append(opt)
    return selected


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


def records_df(ind: dict, key: str) -> pd.DataFrame:
    data = ind.get(key)
    if isinstance(data, list) and data:
        return pd.DataFrame(data)
    return pd.DataFrame()


# --------------------------------------------------------------------------- #
# Barre laterale : FILTRES interactifs
# --------------------------------------------------------------------------- #
st.sidebar.title("🔎 Filtres")
st.sidebar.caption("Menus déroulants à cases à cocher. "
                   "Les graphiques se recalculent selon vos sélections.")

poll_cities = sorted(poll_df["city"].dropna().unique().tolist()) if not poll_df.empty else []
sel_poll_cities = dropdown_checkboxes("Villes (pollution)", poll_cities, "pollcity")

pollutants_all = sorted(poll_df["parameter"].dropna().unique().tolist()) if not poll_df.empty else []
sel_pollutants = dropdown_checkboxes("Polluants", pollutants_all, "pollutant")

bike_cities = sorted(bikes_df["city"].dropna().unique().tolist()) if not bikes_df.empty else []
sel_bike_cities = dropdown_checkboxes("Réseaux / villes (vélos)", bike_cities, "bikecity")

weather_cities = sorted(weather_df["city"].dropna().unique().tolist()) if not weather_df.empty else []
sel_weather_cities = dropdown_checkboxes("Villes (météo)", weather_cities, "wxcity")

st.sidebar.divider()
st.sidebar.caption("Régénérer les données :\n\n"
                   "`python -m urbanhub.cli pipeline --demo --iot-backfill 72`")

# Application des filtres
poll_f = poll_df.copy()
if not poll_f.empty:
    if sel_poll_cities:
        poll_f = poll_f[poll_f["city"].isin(sel_poll_cities)]
    if sel_pollutants:
        poll_f = poll_f[poll_f["parameter"].isin(sel_pollutants)]

bikes_f = bikes_df.copy()
if not bikes_f.empty and sel_bike_cities:
    bikes_f = bikes_f[bikes_f["city"].isin(sel_bike_cities)]

weather_f = weather_df.copy()
if not weather_f.empty and sel_weather_cities:
    weather_f = weather_f[weather_f["city"].isin(sel_weather_cities)]


# --------------------------------------------------------------------------- #
# En-tete + KPIs (reagissent aux filtres)
# --------------------------------------------------------------------------- #
st.title("🏙️ UrbanHub — Jumeau numérique urbain")
st.caption("Plateforme Smart City : ingestion & analyse de 3 flux Big Data "
           "(Batch météo · Streaming vélos · IoT pollution)")

if weather_df.empty and bikes_df.empty and poll_df.empty:
    st.warning(
        "Aucune donnée trouvée. Lance d'abord le pipeline :\n\n"
        "`python -m urbanhub.cli pipeline --demo --iot-backfill 72`"
    )

c1, c2, c3, c4 = st.columns(4)
c1.metric("🌡️ Observations météo", f"{len(weather_f):,}".replace(",", " "))
c2.metric("🚲 Stations vélos", f"{bikes_f['station_id'].nunique() if not bikes_f.empty else 0:,}".replace(",", " "))
c3.metric("🏭 Mesures pollution", f"{len(poll_f):,}".replace(",", " "))
c4.metric("🌍 Villes (pollution)", poll_f["city"].nunique() if not poll_f.empty else 0)

tab_meteo, tab_velos, tab_poll, tab_cross = st.tabs(
    ["🌡️ Météo (Batch)", "🚲 Mobilité (Streaming)", "🏭 Pollution (IoT)", "🔀 Analyse croisée"]
)


# --------------------------------------------------------------------------- #
# Onglet 1 : Meteo
# --------------------------------------------------------------------------- #
with tab_meteo:
    st.subheader("Flux Batch — Météo NOAA (France)")
    if not weather_f.empty:
        st.caption(f"Période : {weather_f['timestamp'].min()} → "
                   f"{weather_f['timestamp'].max()} · "
                   f"{weather_f['station_id'].nunique()} stations · "
                   f"villes : {', '.join(sel_weather_cities) or '—'}")

        k1, k2, k3 = st.columns(3)
        k1.metric("🌡️ Température moyenne", f"{weather_f['temperature_c'].mean():.1f} °C")
        k2.metric("💧 Humidité moyenne", f"{weather_f['humidity_pct'].mean():.0f} %")
        k3.metric("🌬️ Vent max", f"{weather_f['wind_speed_ms'].max():.1f} m/s")

        left, right = st.columns(2)
        with left:
            st.markdown("**Température moyenne par mois**")
            monthly = weather_f.groupby(weather_f["timestamp"].dt.month)["temperature_c"].mean()
            monthly.index.name = "mois"
            st.line_chart(monthly)
        with right:
            st.markdown("**Température moyenne par saison**")
            order = ["Hiver", "Printemps", "Ete", "Automne"]
            season = weather_f.groupby("season")["temperature_c"].mean()
            season = season.reindex([o for o in order if o in season.index])
            st.bar_chart(season)

        st.markdown("**Jours aux conditions extrêmes** (sur la sélection)")
        wd = weather_f.assign(day=weather_f["timestamp"].dt.date)
        daily = wd.groupby("day").agg(
            tmax=("temperature_c", "max"), tmin=("temperature_c", "min"),
            pluie=("precip_mm", "sum"), vent=("wind_speed_ms", "max")).reset_index()
        if not daily.empty:
            rows = [
                {"Événement": "Jour le plus chaud", "Date": daily.loc[daily["tmax"].idxmax(), "day"],
                 "Valeur": f"{daily['tmax'].max():.1f} °C"},
                {"Événement": "Jour le plus froid", "Date": daily.loc[daily["tmin"].idxmin(), "day"],
                 "Valeur": f"{daily['tmin'].min():.1f} °C"},
                {"Événement": "Jour le plus pluvieux", "Date": daily.loc[daily["pluie"].idxmax(), "day"],
                 "Valeur": f"{daily['pluie'].max():.1f} mm"},
                {"Événement": "Jour le plus venté", "Date": daily.loc[daily["vent"].idxmax(), "day"],
                 "Valeur": f"{daily['vent'].max():.1f} m/s"},
            ]
            safe_dataframe(pd.DataFrame(rows))

        with st.expander("📊 Graphiques générés (rapports batch)"):
            safe_image(REP / "weather_saisonnier.png", "Cycle mensuel de la température")
            safe_image(REP / "weather_anomalies.png", "Anomalies de température (z-score)")
    else:
        st.info("Aucune donnée météo (lance `batch` puis `process`).")


# --------------------------------------------------------------------------- #
# Onglet 2 : Mobilite
# --------------------------------------------------------------------------- #
with tab_velos:
    st.subheader("Flux Streaming — Vélos en libre-service (CityBikes)")
    if not bikes_f.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Réseaux", bikes_f["network_id"].nunique())
        m2.metric("Stations", f"{bikes_f['station_id'].nunique():,}".replace(",", " "))
        m3.metric("Vélos dispo (moyenne)", f"{bikes_f['bikes_available'].mean():.1f}")

        if {"latitude", "longitude"}.issubset(bikes_f.columns):
            st.markdown("**Carte des stations vélos (dernier snapshot)**")
            last_ts = bikes_f["timestamp"].max()
            geo = bikes_f[bikes_f["timestamp"] == last_ts][["latitude", "longitude"]].dropna()
            if not geo.empty:
                safe_map(geo)

        # Agregation par station
        per_station = bikes_f.groupby(["city", "station_name"]).agg(
            occupancy_rate=("occupancy_rate", "mean"),
            bikes_available=("bikes_available", "mean"),
            capacity=("capacity", "mean"),
            pct_empty=("is_empty", "mean"),
            pct_full=("is_full", "mean")).reset_index()

        left, right = st.columns(2)
        with left:
            st.markdown("**Stations les plus sollicitées** (taux d'occupation)")
            top = per_station.sort_values("occupancy_rate", ascending=False).head(15)
            safe_dataframe(top.round(3), height=320)
        with right:
            st.markdown("**Stations critiques à rééquilibrer**")
            per_station["criticite"] = per_station[["pct_empty", "pct_full"]].max(axis=1)
            per_station["type"] = per_station.apply(
                lambda r: "pénurie (vide)" if r["pct_empty"] >= r["pct_full"]
                else "saturation (pleine)", axis=1)
            crit = per_station[per_station["criticite"] >= 0.5].sort_values(
                "criticite", ascending=False).head(15)
            if not crit.empty:
                safe_dataframe(crit[["city", "station_name", "type", "criticite",
                                     "capacity"]].round(3), height=320)
            else:
                st.info("Pas de station critique sur la sélection.")

        st.markdown("**Disponibilité moyenne par ville / réseau**")
        per_city = per_station.groupby("city").agg(
            stations=("station_name", "nunique"),
            occupation=("occupancy_rate", "mean"),
            pct_vide=("pct_empty", "mean")).reset_index().sort_values(
            "stations", ascending=False)
        safe_dataframe(per_city.round(3))

        with st.expander("📊 Graphique généré (profil horaire)"):
            safe_image(REP / "mobility_profil_horaire.png", "Profil horaire de disponibilité")
    else:
        st.info("Aucune donnée vélos (lance `stream` puis `process`).")


# --------------------------------------------------------------------------- #
# Onglet 3 : Pollution
# --------------------------------------------------------------------------- #
with tab_poll:
    st.subheader("Flux IoT — Pollution atmosphérique (OpenAQ)")
    if not poll_f.empty:
        mode = sorted(poll_f["source"].dropna().unique().tolist()) if "source" in poll_f else []
        st.caption(f"Source : {', '.join(mode) or '—'} · "
                   f"Polluants : {', '.join(sel_pollutants) or '—'}")

        left, right = st.columns(2)
        with left:
            st.markdown("**Concentration moyenne par ville** (µg/m³)")
            by_city = poll_f.groupby("city")["value"].mean().sort_values(ascending=False)
            st.bar_chart(by_city)
        with right:
            st.markdown("**Profil horaire des polluants**")
            hourly = (poll_f.assign(h=poll_f["timestamp"].dt.hour)
                      .groupby(["h", "parameter"])["value"].mean().unstack("parameter"))
            if not hourly.empty:
                st.line_chart(hourly)

        st.markdown("**Concentration moyenne par ville et polluant** (µg/m³)")
        pivot = poll_f.groupby(["city", "parameter"])["value"].mean().unstack("parameter")
        safe_dataframe(pivot.round(2).reset_index())

        st.markdown("**Dépassements de seuils** (référentiel OMS indicatif)")
        pf = poll_f.copy()
        pf["seuil"] = pf["parameter"].map(THRESHOLDS)
        pf["depasse"] = pf["value"] > pf["seuil"]
        total = int(pf["depasse"].sum())
        st.metric("Total de dépassements", total)
        exceed = (pf[pf["depasse"]].groupby(["city", "parameter"]).size()
                  .reset_index(name="nb_dépassements")
                  .sort_values("nb_dépassements", ascending=False).head(15))
        if not exceed.empty:
            safe_dataframe(exceed)

        with st.expander("📊 Graphique généré (classement des villes)"):
            safe_image(REP / "pollution_classement_villes.png", "Indice qualité de l'air")
    else:
        st.info("Aucune donnée pollution (lance `iot --backfill-hours 72` puis `process`).")


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
            mat = pd.DataFrame(corr).T.round(2)
            safe_dataframe(mat.reset_index().rename(columns={"index": "polluant"}))
            st.caption("Corrélation forte attendue : Ozone (O₃) ↔ température "
                       "(formation photochimique).")
    else:
        st.info("Recouvrement insuffisant — lance un backfill IoT plus long.")

    with st.expander("📊 Cycle diurne croisé (graphique généré)"):
        safe_image(REP / "cross_cycle_diurne.png",
                   "Cycle diurne conjoint météo × pollution × mobilité")

    st.markdown("### Q2 — La météo influence-t-elle l'usage des vélos ?")
    q2 = cross_ind.get("q2_meteo_velos", {})
    if q2.get("disponible"):
        corr = q2.get("correlations", {})
        if corr:
            safe_dataframe(pd.DataFrame(corr).T.round(2).reset_index().rename(
                columns={"index": "cible"}))
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
st.caption("UrbanHub · données data lake `data/curated` & `data/processed` · "
           "régénérer : `python -m urbanhub.cli pipeline --demo --iot-backfill 72`")
