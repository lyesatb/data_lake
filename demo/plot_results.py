"""Interroge QuestDB et produit un graphique du cycle diurne (NO2, O3, temperature)
a partir des donnees reellement stockees. Sortie : docs/images/diurnal_profile.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import requests

HTTP = "http://localhost:9000"


def q(sql: str):
    r = requests.get(f"{HTTP}/exec", params={"query": sql}, timeout=30)
    r.raise_for_status()
    return r.json()["dataset"]


def main() -> None:
    no2 = dict(q("SELECT hour(ts), round(avg(value),2) FROM air_quality "
                 "WHERE pollutant='no2' GROUP BY hour(ts) ORDER BY 1"))
    o3 = dict(q("SELECT hour(ts), round(avg(value),2) FROM air_quality "
                "WHERE pollutant='o3' GROUP BY hour(ts) ORDER BY 1"))
    temp = dict(q("SELECT hour(ts), round(avg(temperature),2) FROM weather "
                  "GROUP BY hour(ts) ORDER BY 1"))
    hours = sorted(no2.keys())

    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    ax1.plot(hours, [no2[h] for h in hours], marker="o", color="#9b5de5", label="NO2 (µg/m³)")
    ax1.plot(hours, [o3[h] for h in hours], marker="s", color="#2a9d8f", label="O3 (µg/m³)")
    ax1.set_xlabel("Heure de la journée (UTC)")
    ax1.set_ylabel("Concentration (µg/m³)")
    ax1.set_xticks(range(0, 24, 2))
    ax1.grid(alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(hours, [temp[h] for h in hours], marker="^", color="#d1495b",
             linestyle="--", label="Température (°C)")
    ax2.set_ylabel("Température (°C)")

    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [l.get_label() for l in lines], loc="upper left")
    ax1.set_title("Cycle diurne urbain (données QuestDB) — pic NO2 aux heures de pointe, "
                  "O3 corrélé à la température")
    fig.tight_layout()

    dest = Path(__file__).resolve().parent.parent / "docs" / "images" / "diurnal_profile.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=110)
    print("Graphique ecrit :", dest)


if __name__ == "__main__":
    main()
