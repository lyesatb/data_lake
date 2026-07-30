"""Generateur de presentation PowerPoint pour UrbanHub.

Construit un fichier .pptx de soutenance a partir des indicateurs reels du data
lake (data/curated) et des graphiques generes (data/curated/reports).

Usage :
    python -m urbanhub.cli slides
    # ou
    python -m urbanhub.presentation
"""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Pt

from urbanhub import config
from urbanhub.utils.logging_utils import get_logger

log = get_logger("presentation")

# Palette
NAVY = RGBColor(0x1F, 0x3B, 0x57)
TEAL = RGBColor(0x2A, 0x9D, 0x8F)
LIGHT = RGBColor(0xF2, 0xF5, 0xF7)
GREY = RGBColor(0x55, 0x5F, 0x66)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0xD1, 0x49, 0x5B)

# 16:9
SLIDE_W = Emu(12192000)
SLIDE_H = Emu(6858000)


def _load(name: str) -> dict:
    p = config.INDICATORS_DIR / name
    if p.exists():
        with p.open(encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _blank(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _rect(slide, x, y, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def _text(slide, x, y, w, h, text, size=18, color=NAVY, bold=False,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font="Calibri"):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    return tb


def _bullets(slide, x, y, w, h, items, size=16, color=GREY):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, (txt, lvl) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = lvl
        p.space_after = Pt(6)
        run = p.add_run()
        run.text = ("• " if lvl == 0 else "– ") + txt
        run.font.size = Pt(size - lvl * 2)
        run.font.color.rgb = NAVY if lvl == 0 else color
        run.font.name = "Calibri"
    return tb


def _content_header(slide, kicker, title):
    _rect(slide, 0, 0, SLIDE_W, Emu(180000), NAVY)
    _rect(slide, 0, Emu(180000), Emu(4200000), Emu(30000), TEAL)
    _text(slide, Emu(500000), Emu(300000), Emu(11000000), Emu(500000),
          kicker, size=14, color=TEAL, bold=True)
    _text(slide, Emu(500000), Emu(600000), Emu(11200000), Emu(700000),
          title, size=30, color=NAVY, bold=True)


def _add_image(slide, path: Path, x, y, w=None, h=None):
    if path and path.exists():
        slide.shapes.add_picture(str(path), x, y, width=w, height=h)
        return True
    return False


def _kpi_card(slide, x, y, w, value, label):
    h = Emu(1150000)
    card = _rect(slide, x, y, w, h, LIGHT)
    _rect(slide, x, y, w, Emu(70000), TEAL)
    _text(slide, x, y + Emu(180000), w, Emu(560000), value, size=30,
          color=NAVY, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    _text(slide, x, y + Emu(720000), w, Emu(380000), label, size=13,
          color=GREY, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return card


# --------------------------------------------------------------------------- #
# Construction des diapositives
# --------------------------------------------------------------------------- #
def build(output: Path | None = None) -> Path:
    weather = _load("weather_indicators.json")
    mobility = _load("mobility_indicators.json")
    pollution = _load("pollution_indicators.json")
    cross = _load("cross_indicators.json")
    rep = config.REPORTS_DIR

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # ---- 1. Titre ---------------------------------------------------------- #
    s = _blank(prs)
    _rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY)
    _rect(s, 0, Emu(3300000), SLIDE_W, Emu(40000), TEAL)
    _text(s, Emu(700000), Emu(2100000), Emu(10800000), Emu(900000),
          "UrbanHub", size=54, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    _text(s, Emu(700000), Emu(3400000), Emu(10800000), Emu(700000),
          "Jumeau numérique urbain — Plateforme Smart City Big Data",
          size=24, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    _text(s, Emu(700000), Emu(4300000), Emu(10800000), Emu(900000),
          "Ingestion & analyse de 3 flux : Batch météo · Streaming vélos · IoT pollution",
          size=16, color=WHITE, align=PP_ALIGN.CENTER)

    # ---- 2. Contexte & objectif ------------------------------------------- #
    s = _blank(prs)
    _content_header(s, "CONTEXTE", "Une Smart City génère des données en continu")
    _bullets(s, Emu(600000), Emu(1600000), Emu(11000000), Emu(4500000), [
        ("Capteurs IoT (pollution, bruit, incidents), consommation énergétique, "
         "météo, trafic, événements urbains…", 0),
        ("Ces données doivent être collectées, stockées, traitées et analysées "
         "pour produire des indicateurs utiles aux décideurs publics.", 0),
        ("Objectif : développer UrbanHub, une plateforme capable d'ingérer et "
         "d'analyser ces données — un jumeau numérique urbain.", 0),
        ("Trois types de flux typiques d'un système Big Data réel :", 0),
        ("Flux Batch — données historiques massives (météo)", 1),
        ("Flux Streaming — données temps réel (mobilité / vélos)", 1),
        ("Flux IoT — données capteurs (pollution atmosphérique)", 1),
    ])

    # ---- 3. Architecture --------------------------------------------------- #
    s = _blank(prs)
    _content_header(s, "ARCHITECTURE", "Une chaîne de valeur de la donnée")
    steps = ["Sources\n(NOAA · CityBikes · OpenAQ)", "Ingestion\n(API · download // · scraping)",
             "Data Lake\n(raw, partitionné par date)", "Traitement\n(nettoyage → Parquet)",
             "Analyse Data / IA\n(corrélations, indices)", "Indicateurs urbains\n(JSON · CSV · dashboard)"]
    n = len(steps)
    gap = Emu(200000)
    total_w = SLIDE_W - Emu(1000000) - gap * (n - 1)
    bw = Emu(int(total_w / n))
    x = Emu(500000)
    y = Emu(2600000)
    for i, stp in enumerate(steps):
        color = TEAL if i % 2 == 0 else NAVY
        _rect(s, x, y, bw, Emu(1300000), color)
        _text(s, x, y, bw, Emu(1300000), stp, size=12, color=WHITE, bold=True,
              align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < n - 1:
            _text(s, x + bw, y, gap, Emu(1300000), "›", size=24, color=GREY,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x = Emu(x + bw + gap)
    _bullets(s, Emu(600000), Emu(4400000), Emu(11000000), Emu(1800000), [
        ("Data lake structuré en 3 zones : raw (brut immuable) → processed "
         "(Parquet nettoyé) → curated (indicateurs).", 0),
        ("Partitionnement Hive year=/month=/day= pour un traitement incrémental.", 0),
        ("Orchestration via une CLI unique (init · batch · stream · iot · "
         "process · analyze · dashboard · slides).", 0),
    ])

    # ---- 4. Chiffres clés (KPIs) ------------------------------------------ #
    s = _blank(prs)
    _content_header(s, "VUE D'ENSEMBLE", "Les chiffres clés de la plateforme")
    kpis = [
        (f"{weather.get('n_observations', 0):,}".replace(",", " "), "Observations météo"),
        (f"{mobility.get('n_stations', 0):,}".replace(",", " "), "Stations vélos"),
        (f"{mobility.get('n_reseaux', 0)}", "Réseaux vélos FR"),
        (f"{pollution.get('n_mesures', 0):,}".replace(",", " "), "Mesures pollution"),
    ]
    cw = Emu(2650000)
    gap = Emu(250000)
    x = Emu(600000)
    for val, lab in kpis:
        _kpi_card(s, x, Emu(2400000), cw, val, lab)
        x = Emu(x + cw + gap)
    _text(s, Emu(600000), Emu(4000000), Emu(11000000), Emu(900000),
          "12 principales villes françaises suivies · données réelles collectées "
          "via les API publiques NOAA, CityBikes et OpenAQ.",
          size=15, color=GREY)

    # ---- 4bis. Architecture Big Data (Lambda) ----------------------------- #
    s = _blank(prs)
    _content_header(s, "ARCHITECTURE BIG DATA", "Une architecture Lambda (Batch + Temps réel)")
    if not _add_image(s, rep / "architecture_bigdata.png", Emu(500000), Emu(1450000),
                      w=Emu(11200000)):
        _text(s, Emu(600000), Emu(2600000), Emu(11000000), Emu(600000),
              "(schéma d'architecture Big Data)", size=12, color=GREY, align=PP_ALIGN.CENTER)
    _text(s, Emu(500000), Emu(6350000), Emu(11200000), Emu(700000),
          "Ingérer (Kafka) · Stocker (data lake MinIO/Parquet) · Transformer "
          "(Spark batch + Structured Streaming) · Restituer (QuestDB + Streamlit/Grafana). "
          "Chaque techno open source est choisie face à ses concurrentes.",
          size=12, color=GREY)

    # ---- 5. Partie 1 : Batch météo ---------------------------------------- #
    s = _blank(prs)
    _content_header(s, "PARTIE 1 · FLUX BATCH", "Analyse météorologique urbaine (NOAA)")
    q4 = weather.get("q4_jours_extremes", {})
    chaud = q4.get("jour_plus_chaud", {})
    froid = q4.get("jour_plus_froid", {})
    _bullets(s, Emu(600000), Emu(1550000), Emu(5600000), Emu(4500000), [
        ("Téléchargement PARALLÈLE des stations FR (ThreadPoolExecutor), 5 ans "
         "d'historique — jamais fichier par fichier.", 0),
        ("Nettoyage : parsing ISD, conversion d'unités, valeurs manquantes, "
         "timestamp UTC, humidité (Magnus).", 0),
        ("Questions métier traitées :", 0),
        ("Périodes anormales (z-score vs normale mensuelle)", 1),
        ("Corrélation météo ↔ visibilité", 1),
        ("Évolution saisonnière de la température", 1),
        ("Jours extrêmes : "
         f"chaud {chaud.get('tmax', '?')}°C, froid {froid.get('tmin', '?')}°C", 1),
    ], size=15)
    if not _add_image(s, rep / "weather_saisonnier.png", Emu(6500000), Emu(1700000),
                      w=Emu(5100000)):
        _text(s, Emu(6500000), Emu(2600000), Emu(5100000), Emu(600000),
              "(graphique météo)", size=12, color=GREY, align=PP_ALIGN.CENTER)

    # ---- 6. Partie 2 : Streaming vélos ------------------------------------ #
    s = _blank(prs)
    _content_header(s, "PARTIE 2 · FLUX STREAMING", "Mobilité urbaine (CityBikes)")
    _bullets(s, Emu(600000), Emu(1550000), Emu(5600000), Emu(4500000), [
        ("Récupération automatique toutes les minutes de l'état des stations "
         "de tous les réseaux FR (Vélib' inclus).", 0),
        ("Variables : station_id, nom, lat/lon, bikes_available, free_slots, "
         "timestamp.", 0),
        ("Questions métier traitées :", 0),
        ("Stations les plus utilisées (taux d'occupation)", 1),
        ("Zones à offre insuffisante (souvent vides)", 1),
        ("Pics d'utilisation journaliers", 1),
        ("Déséquilibres géographiques", 1),
        ("Stations critiques à rééquilibrer (pénurie / saturation)", 1),
    ], size=15)
    if not _add_image(s, rep / "mobility_profil_horaire.png", Emu(6500000),
                      Emu(1700000), w=Emu(5100000)):
        _text(s, Emu(6500000), Emu(2600000), Emu(5100000), Emu(600000),
              "(profil horaire vélos)", size=12, color=GREY, align=PP_ALIGN.CENTER)

    # ---- 7. Partie 3 : IoT pollution -------------------------------------- #
    s = _blank(prs)
    _content_header(s, "PARTIE 3 · FLUX IoT", "Pollution atmosphérique (OpenAQ)")
    _bullets(s, Emu(600000), Emu(1550000), Emu(5600000), Emu(4500000), [
        ("Ingestion régulière simulant un flux IoT pour les principales villes.", 0),
        ("Polluants : PM2.5, PM10, NO₂, O₃, SO₂, CO.", 0),
        ("Mode réel via l'API OpenAQ (clé X-API-Key) ou simulateur réaliste "
         "avec cycles diurnes + backfill d'historique.", 0),
        ("Questions métier traitées :", 0),
        ("Villes les plus polluées par polluant", 1),
        ("Profils horaires (pics trafic NO₂, ozone l'après-midi)", 1),
        ("Dépassements des seuils OMS", 1),
        ("Indice de qualité de l'air par ville", 1),
    ], size=15)
    if not _add_image(s, rep / "pollution_classement_villes.png", Emu(6500000),
                      Emu(1700000), w=Emu(5100000)):
        _text(s, Emu(6500000), Emu(2600000), Emu(5100000), Emu(600000),
              "(classement pollution)", size=12, color=GREY, align=PP_ALIGN.CENTER)

    # ---- 8. Partie 4 : Analyse croisée ------------------------------------ #
    s = _blank(prs)
    _content_header(s, "PARTIE 4 · ANALYSE CROISÉE", "Météo × Pollution × Mobilité")
    o3 = ""
    q1 = cross.get("q1_meteo_pollution", {})
    if q1.get("disponible"):
        c = q1.get("correlations", {}).get("o3", {})
        if c:
            o3 = f"O₃ ↔ température : {c.get('temperature_c', '?')}"
    _bullets(s, Emu(600000), Emu(1550000), Emu(5600000), Emu(4500000), [
        ("Croisement sur le CYCLE DIURNE (robuste aux profondeurs temporelles "
         "différentes des 3 flux).", 0),
        ("Relation météo ↔ pollution : forte corrélation ozone/température "
         "(signature photochimique).", 0),
        (o3 or "Corrélation ozone/température élevée", 1),
        ("Influence de la météo sur l'usage des vélos.", 0),
        ("Conditions favorables à la mobilité douce "
         "(T 12–25°C, sans pluie, vent < 6 m/s) — surtout en été.", 0),
        ("Interactions météo × pollution × mobilité sur la journée.", 0),
    ], size=15)
    if not _add_image(s, rep / "cross_cycle_diurne.png", Emu(6500000), Emu(1650000),
                      w=Emu(5100000)):
        _text(s, Emu(6500000), Emu(2600000), Emu(5100000), Emu(600000),
              "(cycle diurne croisé)", size=12, color=GREY, align=PP_ALIGN.CENTER)

    # ---- 9. Tableau de bord ----------------------------------------------- #
    s = _blank(prs)
    _content_header(s, "RESTITUTION", "Tableau de bord interactif (Streamlit)")
    _bullets(s, Emu(600000), Emu(1600000), Emu(11000000), Emu(3000000), [
        ("4 onglets : Météo · Mobilité · Pollution · Analyse croisée.", 0),
        ("Filtres interactifs (menus déroulants à cases à cocher) : villes, "
         "polluants, réseaux — les graphiques se recalculent en direct.", 0),
        ("KPIs, carte des stations vélos, classements, profils horaires, "
         "matrice de corrélation.", 0),
        ("Lancement : python -m urbanhub.cli dashboard  →  http://localhost:8501", 0),
    ])

    # ---- 10. Livrables & conclusion --------------------------------------- #
    s = _blank(prs)
    _content_header(s, "CONCLUSION", "Livrables & perspectives")
    _bullets(s, Emu(600000), Emu(1600000), Emu(11000000), Emu(4500000), [
        ("Livrables :", 0),
        ("Scripts de collecte des 3 flux (urbanhub/ingestion)", 1),
        ("Stockage structuré en data lake (raw / processed / curated)", 1),
        ("Traitement data engineering (urbanhub/processing)", 1),
        ("Analyses & indicateurs urbains (urbanhub/analysis)", 1),
        ("Tableau de bord Streamlit + cette présentation", 1),
        ("Perspectives :", 0),
        ("Orchestration planifiée (cron / Airflow) pour enrichir le temps réel", 1),
        ("Stockage objet (S3/MinIO) + moteur de requête (DuckDB/Spark)", 1),
        ("Modèles prédictifs (prévision pollution, demande vélos)", 1),
    ])

    output = output or (config.REPORTS_DIR / "UrbanHub_presentation.pptx")
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output))
    log.info("Présentation générée : %s (%d diapositives)", output, len(prs.slides._sldIdLst))
    return output


if __name__ == "__main__":
    build()
