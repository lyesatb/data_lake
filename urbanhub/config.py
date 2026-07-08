"""Configuration centrale de la plateforme UrbanHub.

Definit l'arborescence du data lake (raw / processed / curated), les parametres
des trois sources de donnees et la liste des principales villes francaises
utilisees comme perimetre d'analyse.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Arborescence du data lake
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("URBANHUB_DATA_DIR", PROJECT_ROOT / "data"))

# Zone "raw"       : donnees brutes telles qu'ingerees (immuables)
# Zone "processed" : donnees nettoyees / normalisees (parquet)
# Zone "curated"   : indicateurs urbains prets a l'exploitation
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CURATED_DIR = DATA_DIR / "curated"

# Sous-zones par flux
RAW_WEATHER_DIR = RAW_DIR / "batch" / "weather"
RAW_CITYBIKES_DIR = RAW_DIR / "streaming" / "citybikes"
RAW_OPENAQ_DIR = RAW_DIR / "iot" / "openaq"

PROC_WEATHER_DIR = PROCESSED_DIR / "weather"
PROC_CITYBIKES_DIR = PROCESSED_DIR / "citybikes"
PROC_OPENAQ_DIR = PROCESSED_DIR / "openaq"

INDICATORS_DIR = CURATED_DIR / "indicators"
REPORTS_DIR = CURATED_DIR / "reports"

ALL_DIRS = [
    RAW_WEATHER_DIR, RAW_CITYBIKES_DIR, RAW_OPENAQ_DIR,
    PROC_WEATHER_DIR, PROC_CITYBIKES_DIR, PROC_OPENAQ_DIR,
    INDICATORS_DIR, REPORTS_DIR,
]


def ensure_dirs() -> None:
    """Cree l'ensemble des repertoires du data lake s'ils n'existent pas."""
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Principales villes francaises (perimetre d'analyse)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class City:
    name: str
    latitude: float
    longitude: float
    # bbox utile pour filtrer certaines sources : (lat_min, lat_max, lon_min, lon_max)
    bbox: tuple[float, float, float, float] = field(default=None)


FRANCE_CITIES: list[City] = [
    City("Paris", 48.8566, 2.3522),
    City("Marseille", 43.2965, 5.3698),
    City("Lyon", 45.7640, 4.8357),
    City("Toulouse", 43.6047, 1.4442),
    City("Nice", 43.7102, 7.2620),
    City("Nantes", 47.2184, -1.5536),
    City("Montpellier", 43.6108, 3.8767),
    City("Strasbourg", 48.5734, 7.7521),
    City("Bordeaux", 44.8378, -0.5792),
    City("Lille", 50.6292, 3.0573),
    City("Rennes", 48.1173, -1.6778),
    City("Grenoble", 45.1885, 5.7245),
]

# Bornes geographiques approximatives de la France metropolitaine
FRANCE_BBOX = (41.0, 51.5, -5.5, 9.8)  # (lat_min, lat_max, lon_min, lon_max)


# --------------------------------------------------------------------------- #
# Flux Batch : NOAA Global Hourly Weather
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class NOAAConfig:
    isd_history_url: str = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
    access_base_url: str = "https://www.ncei.noaa.gov/data/global-hourly/access"
    country_code: str = "FR"          # code pays ISD pour la France
    years_back: int = 5               # dimension temporelle demandee
    max_workers: int = 12             # telechargements paralleles
    request_timeout: int = 60


NOAA = NOAAConfig()


def noaa_years(years_back: int | None = None) -> list[int]:
    """Retourne la liste des annees a telecharger (les N dernieres)."""
    n = years_back if years_back is not None else NOAA.years_back
    current = datetime.utcnow().year
    return list(range(current - n + 1, current + 1))


# --------------------------------------------------------------------------- #
# Flux Streaming : CityBikes (velos en libre-service)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CityBikesConfig:
    base_url: str = "https://api.citybik.es/v2"
    country_code: str = "FR"
    poll_interval_sec: int = 60       # recuperation toutes les minutes
    request_timeout: int = 30


CITYBIKES = CityBikesConfig()


# --------------------------------------------------------------------------- #
# Flux IoT : OpenAQ (pollution atmospherique)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class OpenAQConfig:
    base_url: str = "https://api.openaq.org/v3"
    country_iso: str = "FR"
    api_key_env: str = "OPENAQ_API_KEY"
    poll_interval_sec: int = 300      # ingestion reguliere (5 min) simulant un flux IoT
    request_timeout: int = 45
    # Polluants principaux suivis
    pollutants: tuple[str, ...] = ("pm25", "pm10", "no2", "o3", "so2", "co")

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)


OPENAQ = OpenAQConfig()
