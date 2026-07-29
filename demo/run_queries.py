"""Execute une serie de requetes QuestDB (via l'API REST) et exporte les
resultats reels au format Markdown dans results/DEMO_OUTPUT.md.

Usage :
    python run_queries.py
"""
from __future__ import annotations

from pathlib import Path

import requests

HTTP = "http://localhost:9000"

QUERIES: list[tuple[str, str, str]] = [
    ("Volume & fenêtre temporelle",
     "Nombre total de mesures et bornes de dates.",
     "SELECT count() AS mesures, min(ts) AS debut, max(ts) AS fin FROM air_quality;"),

    ("SAMPLE BY — moyenne journalière (PM2.5, Paris)",
     "Bucketisation temporelle native de QuestDB (5 premiers jours).",
     "SELECT ts, round(avg(value),1) AS pm25_moy FROM air_quality "
     "WHERE city='Paris' AND pollutant='pm25' SAMPLE BY 1d LIMIT 5;"),

    ("LATEST ON — dernier état de chaque capteur (Lyon)",
     "Récupère la dernière valeur par série : idéal pour un dashboard temps réel.",
     "SELECT city, pollutant, ts, value FROM air_quality WHERE city='Lyon' "
     "LATEST ON ts PARTITION BY city, pollutant;"),

    ("Profil diurne du NO2 (moyenne par heure)",
     "Met en évidence les pics de trafic (matin/soir).",
     "SELECT hour(ts) AS heure, round(avg(value),1) AS no2_moy FROM air_quality "
     "WHERE pollutant='no2' GROUP BY hour(ts) ORDER BY heure;"),

    ("ASOF JOIN — ozone associé à la température (Nice)",
     "Jointure temporelle sur l'horodatage le plus proche : spécialité de QuestDB.",
     "SELECT a.ts, round(a.value,1) AS o3, round(w.temperature,1) AS temperature "
     "FROM (SELECT ts, city, value FROM air_quality WHERE pollutant='o3' AND city='Nice') a "
     "ASOF JOIN (SELECT ts, city, temperature FROM weather WHERE city='Nice') w LIMIT 10;"),

    ("Classement des villes par ozone moyen",
     "Agrégation + tri.",
     "SELECT city, round(avg(value),1) AS o3_moy FROM air_quality "
     "WHERE pollutant='o3' GROUP BY city ORDER BY o3_moy DESC;"),

    ("Dépassements de seuil OMS (PM2.5 > 25 µg/m³)",
     "Comptage des dépassements par ville.",
     "SELECT city, count() AS nb_depassements FROM air_quality "
     "WHERE pollutant='pm25' AND value>25 GROUP BY city ORDER BY nb_depassements DESC;"),

    ("SAMPLE BY 1h FILL(LINEAR) — série continue (Marseille, O3)",
     "Interpolation linéaire des trous de la série temporelle.",
     "SELECT ts, round(avg(value),1) AS o3 FROM air_quality "
     "WHERE city='Marseille' AND pollutant='o3' SAMPLE BY 1h FILL(LINEAR) LIMIT 6;"),
]


def run(sql: str) -> dict:
    r = requests.get(f"{HTTP}/exec", params={"query": sql}, timeout=30)
    r.raise_for_status()
    return r.json()


def to_md_table(res: dict) -> str:
    cols = [c["name"] for c in res["columns"]]
    lines = ["| " + " | ".join(cols) + " |",
             "| " + " | ".join("---" for _ in cols) + " |"]
    for row in res["dataset"]:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def main() -> None:
    out = ["# QuestDB — Résultats réels de la démo\n",
           "Requêtes exécutées sur QuestDB 8.2.1 (données urbaines simulées, "
           "ingérées via ILP). Générées automatiquement par `demo/run_queries.py`.\n"]
    for i, (title, desc, sql) in enumerate(QUERIES, 1):
        print(f"[{i}/{len(QUERIES)}] {title}")
        res = run(sql)
        out.append(f"## {i}. {title}\n")
        out.append(f"_{desc}_\n")
        out.append("```sql\n" + sql + "\n```\n")
        out.append(to_md_table(res) + "\n")

    dest = Path(__file__).resolve().parent.parent / "results" / "DEMO_OUTPUT.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(out), encoding="utf-8")
    print(f"\nResultats ecrits dans : {dest}")


if __name__ == "__main__":
    main()
