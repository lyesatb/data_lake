"""Demo QuestDB — Generation et ingestion de donnees urbaines temps reel.

Contexte : ce script simule la "couche Speed / IoT" d'une architecture Big Data
(type UrbanHub) en injectant dans QuestDB des mesures urbaines horodatees :
    - air_quality : capteurs de pollution (PM2.5, PM10, NO2, O3) par ville
    - weather     : conditions meteo par ville

L'ingestion se fait via ILP (InfluxDB Line Protocol), le protocole haute
performance de QuestDB, sur le port 9009.

Usage :
    python generate_and_ingest.py --days 30 --freq-min 30
"""
from __future__ import annotations

import argparse
import math
import random
import time
from datetime import datetime, timedelta, timezone

import requests
from questdb.ingress import Sender, TimestampNanos

HTTP = "http://localhost:9000"
ILP_CONF = "tcp::addr=localhost:9009;"

CITIES = {
    # ville : (facteur de pollution de fond, amplitude thermique)
    "Paris": 1.4, "Lyon": 1.3, "Marseille": 1.25, "Lille": 1.35,
    "Toulouse": 1.1, "Nice": 1.05, "Nantes": 1.0, "Strasbourg": 1.2,
}
POLLUTANTS = {
    "pm25": (5, 45), "pm10": (8, 70), "no2": (5, 90), "o3": (10, 120),
}

DDL = [
    "DROP TABLE IF EXISTS air_quality;",
    "DROP TABLE IF EXISTS weather;",
    """CREATE TABLE air_quality (
        ts TIMESTAMP, city SYMBOL, pollutant SYMBOL, value DOUBLE
    ) TIMESTAMP(ts) PARTITION BY DAY WAL;""",
    """CREATE TABLE weather (
        ts TIMESTAMP, city SYMBOL, temperature DOUBLE,
        humidity DOUBLE, wind DOUBLE
    ) TIMESTAMP(ts) PARTITION BY DAY WAL;""",
]


def run_sql(sql: str) -> dict:
    r = requests.get(f"{HTTP}/exec", params={"query": sql}, timeout=30)
    r.raise_for_status()
    return r.json()


def create_schema() -> None:
    for stmt in DDL:
        run_sql(stmt)
    print("Schema cree : tables air_quality + weather (WAL, PARTITION BY DAY).")


def diurnal_no2(hour: int) -> float:
    return 1.0 + 0.6 * (1 if hour in (7, 8, 9, 17, 18, 19) else 0)


def diurnal_o3(hour: int) -> float:
    return 1.0 + 0.7 * max(0.0, 1 - abs(hour - 15) / 8)


def diurnal_temp(hour: int) -> float:
    # cycle jour/nuit : minimum vers 5h, maximum vers 15h
    return -math.cos((hour - 5) / 24 * 2 * math.pi)


def generate_and_ingest(days: int, freq_min: int) -> None:
    rng = random.Random(42)
    start = datetime.now(timezone.utc) - timedelta(days=days)
    steps = int(days * 24 * 60 / freq_min)
    n_rows = 0
    t0 = time.time()

    with Sender.from_conf(ILP_CONF) as sender:
        for i in range(steps):
            ts = start + timedelta(minutes=i * freq_min)
            tsn = TimestampNanos.from_datetime(ts)
            hour = ts.hour
            # saisonnalite (jour de l'annee)
            doy = ts.timetuple().tm_yday
            seasonal = 10 + 10 * math.sin((doy - 80) / 365 * 2 * math.pi)

            for city, base in CITIES.items():
                # --- meteo ---
                temp = seasonal + 6 * diurnal_temp(hour) + rng.uniform(-1.5, 1.5)
                humidity = max(20, min(100, 80 - 1.2 * temp + rng.uniform(-5, 5)))
                wind = max(0, rng.gauss(4, 2))
                sender.row(
                    "weather", symbols={"city": city},
                    columns={"temperature": round(temp, 2),
                             "humidity": round(humidity, 1),
                             "wind": round(wind, 2)},
                    at=tsn,
                )
                n_rows += 1

                # --- pollution ---
                for pol, (lo, hi) in POLLUTANTS.items():
                    mid = (lo + hi) / 2
                    factor = base
                    if pol == "no2":
                        factor *= diurnal_no2(hour)
                    if pol == "o3":
                        # l'ozone augmente avec la temperature (photochimie)
                        factor *= diurnal_o3(hour) * (1 + 0.02 * (temp - 15))
                    value = max(0.0, mid * factor * (1 + rng.uniform(-0.2, 0.2)))
                    sender.row(
                        "air_quality",
                        symbols={"city": city, "pollutant": pol},
                        columns={"value": round(value, 2)},
                        at=tsn,
                    )
                    n_rows += 1
            if i % 200 == 0:
                sender.flush()
        sender.flush()

    dt = time.time() - t0
    print(f"Ingestion ILP terminee : {n_rows:,} lignes en {dt:.1f}s "
          f"(~{int(n_rows / dt):,} lignes/s).".replace(",", " "))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--freq-min", type=int, default=30)
    args = ap.parse_args()
    create_schema()
    generate_and_ingest(args.days, args.freq_min)
    # Laisse le temps au WAL d'etre applique
    time.sleep(2)
    for tbl in ("air_quality", "weather"):
        res = run_sql(f"SELECT count() FROM {tbl};")
        print(f"{tbl}: {res['dataset'][0][0]} lignes")


if __name__ == "__main__":
    main()
