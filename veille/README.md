# Big Data — Veille technologique : QuestDB

Projet **« Présenter une techno pour un Meetup »** (Data Architect).
Analyse d'un outil open source du paysage Big Data : **[QuestDB](https://questdb.io)**,
une base de données **time-series** haute performance, positionnée comme couche
**Speed / Serving** d'une architecture Big Data (en lien avec le projet UrbanHub).

> Ce dépôt est **séparé** du projet UrbanHub (data lake) : il est dédié à la veille
> technologique et au déploiement Docker / Kubernetes de QuestDB.

## Livrables

| Livrable | Emplacement |
|----------|-------------|
| **Document de synthèse (veille)** | [`docs/VEILLE_QUESTDB.md`](docs/VEILLE_QUESTDB.md) |
| **Résultats réels de la démo** | [`results/DEMO_OUTPUT.md`](results/DEMO_OUTPUT.md) |
| **Déploiement Docker** | [`docker/docker-compose.yml`](docker/docker-compose.yml) |
| **Déploiement Kubernetes** | [`k8s/questdb.yaml`](k8s/questdb.yaml) |
| **Scripts de démonstration** | [`demo/`](demo/) |

Le document de synthèse couvre : cas d'usage, prise en main (install, CLI, UI,
ingestion, requêtes), forces/faiblesses, comparaison avec les concurrents
(InfluxDB, TimescaleDB, ClickHouse, Cassandra), architecture, et déploiement
Docker/Kubernetes.

## Démarrage rapide

### 1. Lancer QuestDB (Docker)

```bash
cd docker
docker compose up -d
# Console web : http://localhost:9000
```

### 2. Charger des données et lancer les requêtes

```bash
cd demo
pip install -r requirements.txt
python generate_and_ingest.py --days 30 --freq-min 30   # ingestion via ILP
python run_queries.py                                    # requêtes -> results/DEMO_OUTPUT.md
python plot_results.py                                   # graphique du cycle diurne
```

### 3. (Optionnel) Déployer sur Kubernetes

```bash
kubectl apply -f k8s/questdb.yaml
kubectl -n bigdata port-forward svc/questdb 9000:9000 8812:8812 9009:9009
```

## Ce que démontre la démo

- **Ingestion streaming** via ILP mesurée à **~500 000–600 000 lignes/seconde**.
- Requêtes **time-series** natives : `SAMPLE BY`, `LATEST ON`, `ASOF JOIN`, `FILL`.
- Compatibilité **PostgreSQL wire** (port 8812) → outils BI / `psql`.
- Un cas concret « Smart City » : corrélation ozone ↔ température, pics de NO₂,
  dépassements de seuils OMS.

## Structure du dépôt

```
big_data/
├── README.md
├── docs/
│   ├── VEILLE_QUESTDB.md        # le rapport de synthèse
│   └── images/diurnal_profile.png
├── demo/
│   ├── generate_and_ingest.py   # génération + ingestion ILP
│   ├── run_queries.py           # requêtes -> Markdown
│   ├── plot_results.py          # graphique
│   ├── queries.sql              # requêtes commentées
│   └── requirements.txt
├── docker/
│   └── docker-compose.yml
├── k8s/
│   └── questdb.yaml
└── results/
    └── DEMO_OUTPUT.md           # sorties réelles des requêtes
```

## Outil étudié

**QuestDB** — base de données time-series open source (Apache 2.0), écrite en
Java/C++, orientée IoT / monitoring / finance. Version utilisée : **8.2.1**.
