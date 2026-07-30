"""Genere le schema de l'architecture Big Data (Lambda) d'UrbanHub.

Sortie : data/curated/reports/architecture_bigdata.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow, FancyBboxPatch

from urbanhub import config

NAVY = "#1f3b57"
TEAL = "#2a9d8f"
ORANGE = "#e07a3f"
PURPLE = "#9b5de5"
GREY = "#5b6670"
LIGHT = "#eef2f4"


def box(ax, x, y, w, h, title, sub="", fc=LIGHT, ec=NAVY, tc=NAVY, fs=10):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                       linewidth=1.5, edgecolor=ec, facecolor=fc, zorder=2)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h * (0.62 if sub else 0.5), title, ha="center",
            va="center", fontsize=fs, fontweight="bold", color=tc, zorder=3)
    if sub:
        ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center",
                fontsize=fs - 2.5, color=GREY, zorder=3)


def arrow(ax, x1, y1, x2, y2, color=GREY):
    ax.add_patch(FancyArrow(x1, y1, x2 - x1, y2 - y1, width=0.006,
                            head_width=0.12, head_length=0.18,
                            length_includes_head=True, color=color, zorder=1))


def build(out: Path | None = None) -> Path:
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(8, 8.6, "UrbanHub — Architecture Big Data (Lambda)", ha="center",
            fontsize=19, fontweight="bold", color=NAVY)
    ax.text(8, 8.15, "Ingérer · Stocker · Transformer · Restituer — en Batch ET en Temps réel",
            ha="center", fontsize=11, color=GREY, style="italic")

    # --- Colonnes / bandeaux d'etape ---
    bands = [("SOURCES", 0.3, 2.5), ("INGESTION", 3.0, 2.6),
             ("STOCKAGE / BUS", 5.9, 2.6), ("TRAITEMENT", 8.8, 2.9),
             ("SERVING", 11.9, 2.0), ("RESTITUTION", 14.1, 1.6)]
    for name, x, w in bands:
        ax.text(x + w / 2, 7.5, name, ha="center", fontsize=10.5,
                fontweight="bold", color=TEAL)

    # --- Sources ---
    box(ax, 0.3, 6.0, 2.5, 0.9, "Météo NOAA", "Batch · 5 ans", fc="#fdece4", ec=ORANGE)
    box(ax, 0.3, 4.4, 2.5, 0.9, "Vélos CityBikes", "Streaming · /min", fc="#e6f5f2", ec=TEAL)
    box(ax, 0.3, 2.8, 2.5, 0.9, "Pollution OpenAQ", "IoT · capteurs", fc="#f1e9fb", ec=PURPLE)

    # --- Ingestion ---
    box(ax, 3.0, 5.9, 2.6, 1.1, "Download // + NiFi", "acquisition batch", fc=LIGHT)
    box(ax, 3.0, 3.0, 2.6, 1.9, "Apache Kafka", "bus d'événements\n(+ Kafka Connect)",
        fc="#111111", ec="#111111", tc="white")

    # --- Stockage / Bus ---
    box(ax, 5.9, 5.4, 2.6, 1.6, "Data Lake — MinIO", "objet S3 · zones\nraw / processed / curated\n(format Parquet)",
        fc="#fdf6e3", ec=ORANGE)
    box(ax, 5.9, 3.0, 2.6, 1.9, "Kafka topics", "flux temps réel\nbufferisés", fc="#111111",
        ec="#111111", tc="white")

    # --- Traitement : Batch + Speed layers ---
    ax.add_patch(FancyBboxPatch((8.8, 5.2), 2.9, 1.9,
                 boxstyle="round,pad=0.02,rounding_size=0.08",
                 linewidth=1.2, edgecolor=ORANGE, facecolor="#fdf3ea", zorder=1))
    ax.text(10.25, 6.9, "COUCHE BATCH", ha="center", fontsize=9, fontweight="bold", color=ORANGE)
    box(ax, 8.95, 5.35, 2.6, 1.25, "Apache Spark", "traitement historique\nmassif → vues batch", fc="white", ec=ORANGE)

    ax.add_patch(FancyBboxPatch((8.8, 2.7), 2.9, 2.2,
                 boxstyle="round,pad=0.02,rounding_size=0.08",
                 linewidth=1.2, edgecolor=TEAL, facecolor="#e9f6f3", zorder=1))
    ax.text(10.25, 4.7, "COUCHE SPEED (temps réel)", ha="center", fontsize=9, fontweight="bold", color=TEAL)
    box(ax, 8.95, 2.85, 2.6, 1.6, "Spark Structured\nStreaming / Kafka Streams",
        "transformation\ntemps réel", fc="white", ec=TEAL, fs=9)

    # --- Serving ---
    ax.add_patch(FancyBboxPatch((11.9, 2.7), 2.0, 4.4,
                 boxstyle="round,pad=0.02,rounding_size=0.08",
                 linewidth=1.2, edgecolor=NAVY, facecolor="#eef2f4", zorder=1))
    ax.text(12.9, 6.9, "COUCHE SERVING", ha="center", fontsize=9, fontweight="bold", color=NAVY)
    box(ax, 12.0, 4.9, 1.8, 1.6, "QuestDB", "séries temporelles\ntemps réel", fc="#d6f0eb", ec=TEAL, fs=10)
    box(ax, 12.0, 3.0, 1.8, 1.5, "PostgreSQL", "indicateurs\ncurated", fc="#dbe7f3", ec=NAVY, fs=10)

    # --- Restitution ---
    box(ax, 14.1, 5.2, 1.6, 1.5, "Streamlit", "dashboard", fc="#e6f5f2", ec=TEAL)
    box(ax, 14.1, 3.2, 1.6, 1.5, "Grafana", "monitoring", fc="#fdece4", ec=ORANGE)

    # --- Fleches ---
    arrow(ax, 2.8, 6.4, 3.0, 6.4)           # NOAA -> download
    arrow(ax, 2.8, 4.8, 3.0, 4.4)           # bikes -> kafka
    arrow(ax, 2.8, 3.2, 3.0, 3.6)           # openaq -> kafka
    arrow(ax, 5.6, 6.4, 5.9, 6.2)           # download -> datalake
    arrow(ax, 5.6, 3.9, 5.9, 3.9)           # kafka -> topics
    arrow(ax, 8.5, 6.2, 8.95, 6.0)          # datalake -> spark
    arrow(ax, 8.5, 3.9, 8.95, 3.7)          # topics -> streaming
    arrow(ax, 11.55, 6.0, 12.0, 5.7)        # spark -> questdb/pg (batch views)
    arrow(ax, 11.55, 3.6, 12.0, 4.0)        # streaming -> questdb
    arrow(ax, 13.9, 5.7, 14.1, 5.9)         # serving -> streamlit
    arrow(ax, 13.9, 4.0, 14.1, 3.9)         # serving -> grafana

    # --- Orchestration bandeau bas ---
    ax.add_patch(FancyBboxPatch((3.0, 1.4), 8.7, 0.8,
                 boxstyle="round,pad=0.02,rounding_size=0.06",
                 linewidth=1.2, edgecolor=PURPLE, facecolor="#f4ecfb", zorder=1))
    ax.text(7.35, 1.8, "Orchestration : Apache Airflow  (planification des pipelines batch & monitoring)",
            ha="center", fontsize=10, fontweight="bold", color=PURPLE)

    ax.text(8, 0.7, "Batch layer (historique massif) + Speed layer (temps réel) → Serving layer unifiée : "
                    "c'est le principe de l'architecture Lambda.",
            ha="center", fontsize=9.5, color=GREY, style="italic")

    out = out or (config.REPORTS_DIR / "architecture_bigdata.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("Schema ecrit :", out)
    return out


if __name__ == "__main__":
    build()
