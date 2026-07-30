# Projet Archi Big Data — UrbanHub + Veille technologique

Livrable du TP **« Architecture Big Data »** (Recording + Lien GitHub + Veille).
Ce dépôt regroupe **tout ce qui est demandé** pour ce projet, en deux parties :

1. **Architecture Big Data** — re-présentation d'UrbanHub avec une architecture
   Lambda (couches **Batch / Speed / Serving**) et **justification des choix de
   technologies open source**.
2. **Veille technologique** — analyse d'un outil open source du paysage Big Data :
   **QuestDB** (base time-series), avec démonstration réelle et déploiement
   **Docker / Kubernetes**.

---

## Livrables & où les trouver

| Livrable demandé | Emplacement |
|------------------|-------------|
| **Architecture Big Data (Batch/Speed/Serving) + « pourquoi telle techno »** | [`architecture/ARCHITECTURE_BIGDATA.md`](architecture/ARCHITECTURE_BIGDATA.md) |
| Schéma d'architecture | [`architecture/architecture_bigdata.png`](architecture/architecture_bigdata.png) |
| **Veille technologique (document de synthèse)** | [`docs/VEILLE_QUESTDB.md`](docs/VEILLE_QUESTDB.md) |
| Résultats réels de la démo QuestDB | [`results/DEMO_OUTPUT.md`](results/DEMO_OUTPUT.md) |
| Déploiement **Docker** | [`docker/docker-compose.yml`](docker/docker-compose.yml) |
| Déploiement **Kubernetes** | [`k8s/questdb.yaml`](k8s/questdb.yaml) |
| Scripts de démo (ingestion ILP + requêtes SQL) | [`demo/`](demo/) |
| Support de présentation (source Gamma) | [`presentation/`](presentation/) |

---

## Partie 1 — Architecture Big Data

UrbanHub est un **jumeau numérique urbain** (Smart City) qui ingère trois flux :
- **Batch** : météo NOAA (5 ans) ;
- **Streaming** : vélos CityBikes (temps réel) ;
- **IoT** : pollution OpenAQ (capteurs).

L'architecture cible est une **architecture Lambda** :

```
Sources → Ingestion (Kafka) → Data Lake (MinIO/Parquet)
        → Couche Batch (Spark)  ┐
        → Couche Speed (Spark Streaming → QuestDB)  ├─→ Couche Serving (QuestDB + PostgreSQL)
                                                     ┘        → Restitution (Streamlit / Grafana)
        Orchestration : Apache Airflow
```

Le document [`architecture/ARCHITECTURE_BIGDATA.md`](architecture/ARCHITECTURE_BIGDATA.md)
détaille chaque couche et **justifie chaque techno open source face à ses
concurrentes** (Kafka vs RabbitMQ/Pulsar, MinIO vs HDFS, Parquet vs CSV/Avro/ORC,
Spark vs MapReduce/Dask, QuestDB vs InfluxDB/Cassandra, Airflow vs cron).

## Partie 2 — Veille technologique : QuestDB

Analyse complète (cas d'usage, prise en main, forces/faiblesses, comparatif,
architecture, déploiement) dans [`docs/VEILLE_QUESTDB.md`](docs/VEILLE_QUESTDB.md).

Démarrage de la démo :
```bash
cd docker && docker compose up -d           # console : http://localhost:9000
cd ../demo && pip install -r requirements.txt
python generate_and_ingest.py --days 30 --freq-min 30   # ingestion ILP (~500k+ lignes/s)
python run_queries.py                                    # requêtes -> results/DEMO_OUTPUT.md
```

---

## Note

Le **projet d'implémentation complet d'UrbanHub** (code Python d'ingestion,
traitement et analyse, tableau de bord Streamlit) constitue le prototype
exécutable de la logique métier ; il est disponible séparément. Ce dépôt-ci se
concentre sur le **livrable Archi Big Data + Veille** demandé pour ce TP.
