"""Flux IoT - Capteurs de pollution atmospherique (OpenAQ).

Source : https://api.openaq.org/v3/ (necessite une cle API dans l'entete X-API-Key)

L'ingestion simule un flux IoT : a intervalle regulier, on interroge les
capteurs des principales villes francaises pour les polluants principaux
(pm25, pm10, no2, o3, so2, co).

Si aucune cle API n'est disponible (variable d'environnement OPENAQ_API_KEY),
un GENERATEUR SIMULE prend le relais afin de rendre la chaine complete
(ingestion -> stockage -> traitement -> analyse) demontrable de bout en bout.
Les enregistrements simules sont explicitement marques (`source = "simulated"`).
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from urbanhub import config
from urbanhub.config import FRANCE_CITIES
from urbanhub.utils import storage
from urbanhub.utils.logging_utils import get_logger

log = get_logger("ingestion.iot_openaq")

# Plages realistes (ug/m3, sauf CO en mg/m3) pour la simulation
_POLLUTANT_RANGES = {
    "pm25": (3, 45),
    "pm10": (5, 70),
    "no2": (5, 90),
    "o3": (10, 120),
    "so2": (0.5, 20),
    "co": (0.1, 2.5),
}


def _headers() -> dict[str, str]:
    key = config.OPENAQ.api_key
    return {"X-API-Key": key} if key else {}


def _api_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"{config.OPENAQ.base_url}{path}"
    resp = requests.get(url, params=params, headers=_headers(),
                        timeout=config.OPENAQ.request_timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_france_locations(limit: int = 1000) -> list[dict[str, Any]]:
    """Recupere les emplacements de capteurs situes en France."""
    data = _api_get("/locations", {"iso": config.OPENAQ.country_iso, "limit": limit})
    return data.get("results", [])


def _collect_real(ts: datetime) -> list[dict[str, Any]]:
    """Collecte reelle via l'API OpenAQ v3 (latest par emplacement)."""
    rows: list[dict[str, Any]] = []
    locations = fetch_france_locations()
    log.info("Emplacements OpenAQ FR : %d", len(locations))
    for loc in locations:
        coords = loc.get("coordinates", {}) or {}
        loc_id = loc.get("id")
        try:
            latest = _api_get(f"/locations/{loc_id}/latest", {})
        except requests.RequestException as exc:  # pragma: no cover - reseau
            log.warning("latest indisponible pour %s : %s", loc_id, exc)
            continue
        for m in latest.get("results", []):
            rows.append({
                "location_id": loc_id,
                "location": loc.get("name"),
                "city": loc.get("locality") or loc.get("name"),
                "parameter": (m.get("parameter") or {}).get("name")
                             if isinstance(m.get("parameter"), dict) else m.get("parameter"),
                "value": m.get("value"),
                "unit": (m.get("parameter") or {}).get("units")
                        if isinstance(m.get("parameter"), dict) else None,
                "latitude": coords.get("latitude"),
                "longitude": coords.get("longitude"),
                "timestamp": (m.get("datetime") or {}).get("utc") if isinstance(
                    m.get("datetime"), dict) else ts.isoformat(),
                "source": "openaq",
            })
    return rows


def _collect_simulated(ts: datetime, rng: random.Random) -> list[dict[str, Any]]:
    """Genere un snapshot simule realiste pour les principales villes FR.

    La simulation applique une variation diurne (pics matin/soir pour NO2, pic
    d'ozone l'apres-midi) afin que les analyses temporelles restent pertinentes.
    """
    hour = ts.hour
    rush = 1.0 + 0.5 * (1 if hour in (7, 8, 9, 17, 18, 19) else 0)   # trafic
    ozone_day = 1.0 + 0.6 * max(0.0, (1 - abs(hour - 15) / 8))        # photochimie
    rows: list[dict[str, Any]] = []
    for city in FRANCE_CITIES:
        # Chaque ville a un "profil" de fond stable (grande ville = plus pollue)
        base_factor = 1.0 + 0.4 * (city.name in ("Paris", "Lyon", "Marseille", "Lille"))
        for pol in config.OPENAQ.pollutants:
            lo, hi = _POLLUTANT_RANGES[pol]
            mid = (lo + hi) / 2
            noise = rng.uniform(-0.25, 0.25)
            factor = base_factor
            if pol == "no2":
                factor *= rush
            if pol == "o3":
                factor *= ozone_day
            value = max(0.0, mid * factor * (1 + noise))
            rows.append({
                "location_id": f"SIM-{city.name}",
                "location": f"{city.name} - station simulee",
                "city": city.name,
                "parameter": pol,
                "value": round(value, 2),
                "unit": "mg/m3" if pol == "co" else "ug/m3",
                "latitude": city.latitude + rng.uniform(-0.02, 0.02),
                "longitude": city.longitude + rng.uniform(-0.02, 0.02),
                "timestamp": ts.isoformat(),
                "source": "simulated",
            })
    return rows


def collect_once(dest_dir: Path | None = None, simulate: bool | None = None,
                 rng: random.Random | None = None) -> int:
    """Effectue une passe d'ingestion IoT (reelle si cle API, sinon simulee)."""
    dest_dir = dest_dir or config.RAW_OPENAQ_DIR
    ts = datetime.now(timezone.utc)
    rng = rng or random.Random()

    use_sim = simulate if simulate is not None else (config.OPENAQ.api_key is None)
    if use_sim:
        rows = _collect_simulated(ts, rng)
        mode = "SIMULE"
    else:
        rows = _collect_real(ts)
        mode = "REEL (OpenAQ)"

    if not rows:
        log.warning("Aucune mesure collectee (%s).", mode)
        return 0

    part = dest_dir / storage.date_partition(ts)
    out = part / f"openaq_{ts:%Y%m%dT%H%M%S}.jsonl"
    storage.append_jsonl(rows, out)
    log.info("Ingestion IoT [%s] : %d mesures -> %s", mode, len(rows), out)
    return len(rows)


def stream(
    iterations: int | None = None,
    duration_sec: int | None = None,
    interval_sec: int | None = None,
    simulate: bool | None = None,
    seed: int | None = None,
    dest_dir: Path | None = None,
) -> int:
    """Boucle d'ingestion IoT reguliere.

    Args:
        iterations   : nombre de passes.
        duration_sec : duree totale.
        interval_sec : intervalle entre deux ingestions (defaut : 300s).
        simulate     : force le mode simule (True) ou reel (False).
        seed         : graine du generateur simule (reproductibilite).
    """
    interval = interval_sec or config.OPENAQ.poll_interval_sec
    rng = random.Random(seed)
    if config.OPENAQ.api_key is None and simulate is not True:
        log.warning("Aucune cle API OpenAQ (%s) : bascule en mode SIMULE.",
                    config.OPENAQ.api_key_env)
    start = time.monotonic()
    total = 0
    count = 0

    while True:
        total += collect_once(dest_dir, simulate=simulate, rng=rng)
        count += 1

        if iterations is not None and count >= iterations:
            break
        if duration_sec is not None and (time.monotonic() - start) >= duration_sec:
            break
        if iterations is None and duration_sec is None:
            break

        log.info("Attente de %ds avant la prochaine ingestion IoT...", interval)
        time.sleep(interval)

    log.info("Ingestion IoT terminee : %d passes, %d mesures.", count, total)
    return total
