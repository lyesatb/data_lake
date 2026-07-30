# UrbanHub — Architecture Big Data (Lambda) & justification des choix

> Re-présentation du projet UrbanHub avec une **véritable architecture Big Data**.
> L'objectif n'est plus seulement de *traiter des données dans une base classique*,
> mais de construire une **architecture capable d'ingérer, stocker, transformer et
> restituer des données à grande échelle, en batch ET en temps réel**.

![Architecture Big Data d'UrbanHub](images/architecture_bigdata.png)

---

## 1. Pourquoi changer de paradigme ?

L'implémentation initiale d'UrbanHub (Python + pandas + fichiers Parquet locaux +
Streamlit) est parfaite pour **prototyper** et **répondre aux questions métier**.
Mais elle atteint vite ses limites à l'échelle d'une vraie Smart City :

| Limite d'une base/traitement classique | Réponse d'une architecture Big Data |
|----------------------------------------|-------------------------------------|
| Un seul serveur, mémoire limitée | Traitement **distribué** (Spark) |
| Traitement uniquement en batch | **Batch + temps réel** (Lambda) |
| Fichiers locaux, pas de tolérance de panne | **Data lake objet** répliqué (MinIO/S3) |
| Ingestion ponctuelle | **Bus d'événements** continu (Kafka) |
| Restitution figée | **Serving layer** interrogeable en direct |

On passe donc d'un **script** à une **plateforme**.

---

## 2. Le modèle : architecture **Lambda**

L'architecture Lambda combine deux chemins de traitement qui convergent vers une
couche de restitution unique :

- **Couche Batch** : recalcule périodiquement des vues exactes à partir de
  **tout** l'historique (données massives, latence élevée mais précision totale).
- **Couche Speed (temps réel)** : traite les événements **au fil de l'eau** pour
  fournir des vues fraîches à faible latence (précision approchée).
- **Couche Serving** : fusionne les vues batch et temps réel et les expose aux
  applications.

C'est idéal pour UrbanHub, qui mêle justement de l'**historique massif** (météo 5
ans) et du **temps réel** (vélos, pollution).

---

## 3. Les couches, les technologies et **pourquoi celles-ci**

### 3.1 Ingestion

**Choix : Apache Kafka** (+ Kafka Connect) pour les flux temps réel ;
téléchargement parallèle / **Apache NiFi** pour l'acquisition batch.

*Rôle :* absorber les flux CityBikes (streaming) et OpenAQ (IoT) sous forme
d'**événements**, découpler producteurs et consommateurs, et encaisser les pics.

**Pourquoi Kafka et pas une autre techno ?**
- vs **RabbitMQ** : Kafka conserve les messages (log rejouable, *replay*), monte
  bien mieux en débit et en rétention — indispensable pour ré-alimenter la couche
  batch. RabbitMQ est un excellent *broker* de tâches, mais orienté file éphémère.
- vs **AWS Kinesis** : Kafka est **open source** et non lié à un cloud.
- vs **Apache Pulsar** : Pulsar est excellent mais son écosystème et sa communauté
  sont plus petits ; Kafka est le **standard de fait**, très documenté, avec
  Kafka Connect (des centaines de connecteurs Source/Sink prêts à l'emploi).

### 3.2 Stockage — le Data Lake

**Choix : MinIO** (stockage objet compatible S3) stockant des fichiers **Apache
Parquet**, organisés en zones **raw / processed / curated**.

**Pourquoi MinIO et pas une autre techno ?**
- vs **HDFS (Hadoop)** : HDFS impose un cluster lourd (NameNode/DataNodes) à
  opérer. MinIO est **léger, S3-compatible**, cloud-native, et se déploie en un
  conteneur — la tendance actuelle est au découplage *stockage objet + moteur de
  calcul*.
- vs **base relationnelle classique (PostgreSQL seul)** : une base SQL n'est pas
  faite pour stocker des téraoctets de fichiers bruts hétérogènes ; le data lake
  garde la donnée **telle quelle**, on structure au moment du traitement
  (*schema-on-read*).

**Pourquoi Parquet et pas un autre format ?**
- vs **CSV** : Parquet est **colonne**, compressé, typé → lectures 5 à 50× plus
  rapides pour l'analytique.
- vs **Avro** : Avro est orienté *ligne* (idéal pour l'échange/streaming), Parquet
  est orienté *colonne* (idéal pour l'analyse) — on utilise donc **Avro dans Kafka**
  et **Parquet dans le data lake**.
- vs **ORC** : très proche de Parquet ; on retient Parquet pour son support
  universel (Spark, pandas, DuckDB, Arrow…).

### 3.3 Couche Batch

**Choix : Apache Spark.**

*Rôle :* recalculer sur **tout l'historique** (5 ans de météo, agrégats, jointures,
z-scores…) des vues exactes, en **distribué**.

**Pourquoi Spark et pas une autre techno ?**
- vs **Hadoop MapReduce** : Spark travaille **en mémoire** → 10 à 100× plus rapide,
  API plus simple (DataFrame/SQL), et il fait batch **et** streaming.
- vs **Dask** : Dask est excellent en Python pur mais Spark reste le standard
  industriel, avec un écosystème SQL/ML mûr et une meilleure tolérance de panne à
  très grande échelle.

### 3.4 Couche Speed (temps réel)

**Choix : Spark Structured Streaming / Kafka Streams**, puis stockage dans
**QuestDB**.

*Rôle :* transformer les événements vélos/pollution au fil de l'eau (fenêtrage,
agrégats glissants) et les rendre immédiatement interrogeables.

**Pourquoi QuestDB comme base temps réel ?** (voir la veille dédiée)
- base **time-series** open source, ingestion **~500 000+ lignes/s** (ILP),
  requêtes SQL avec extensions temporelles (`SAMPLE BY`, `LATEST ON`, `ASOF JOIN`).
- vs **InfluxDB** : QuestDB offre du **vrai SQL** + compatibilité PostgreSQL.
- vs **Cassandra** : bien plus simple à exploiter et à requêter pour du
  time-series (SQL vs CQL), là où Cassandra vise l'écriture massivement distribuée.
- vs **PostgreSQL seul** : PostgreSQL ne tient pas le débit d'ingestion IoT ni les
  requêtes de fenêtrage temporel aussi efficacement.

### 3.5 Couche Serving

**Choix : QuestDB** (vues temps réel) **+ PostgreSQL** (indicateurs *curated*).

*Rôle :* fusionner vues batch et temps réel et exposer des requêtes rapides aux
applications (via SQL / PostgreSQL wire).

### 3.6 Restitution (Dataviz)

**Choix : Streamlit** (déjà réalisé) et/ou **Grafana**.

**Pourquoi ?**
- **Streamlit** : dashboards analytiques riches en Python, parfait pour l'exploration.
- **Grafana** : idéal pour le **monitoring temps réel** ; il se branche nativement
  sur QuestDB via le protocole PostgreSQL.

### 3.7 Orchestration

**Choix : Apache Airflow.**

**Pourquoi Airflow et pas cron ?**
- Airflow modélise les pipelines en **DAG** (dépendances, reprises sur erreur,
  *backfill*, monitoring, alerting) là où `cron` ne fait que lancer des scripts
  isolés sans visibilité ni gestion d'échec.

---

## 4. Cartographie : les 3 flux UrbanHub → les couches

| Flux UrbanHub | Nature | Couche | Chemin technique |
|---------------|--------|--------|------------------|
| **Météo NOAA** | Batch, 5 ans | **Batch** | Download // → Data Lake (MinIO/Parquet) → Spark → vues |
| **Vélos CityBikes** | Streaming /min | **Speed** | Kafka → Structured Streaming → QuestDB |
| **Pollution OpenAQ** | IoT capteurs | **Speed** | Kafka (Connect) → Streaming → QuestDB |
| **Analyse croisée** | Batch + RT | **Serving** | QuestDB + PostgreSQL → Streamlit / Grafana |

---

## 5. Correspondance avec l'implémentation actuelle (et migration)

L'architecture cible **réutilise** tout le travail déjà réalisé — elle industrialise
les mêmes étapes :

| Aujourd'hui (prototype) | Cible Big Data | Migration |
|-------------------------|----------------|-----------|
| `ingestion/` (requests, threads) | Kafka + Kafka Connect + NiFi | les producteurs publient dans des topics |
| `data/` local (Parquet) | MinIO (S3) zones raw/processed/curated | même format Parquet, stockage objet |
| `processing/` (pandas) | Spark (batch) + Structured Streaming | même logique de nettoyage, distribuée |
| `analysis/` (pandas) | Spark SQL + QuestDB | requêtes SQL sur la serving layer |
| `dashboard/` (Streamlit) | Streamlit + Grafana | Streamlit conservé, Grafana pour le RT |
| CLI `pipeline` | DAG Airflow | orchestration planifiée |

**Le prototype pandas reste la « spécification exécutable » de la logique métier ;**
la version Big Data en est le passage à l'échelle.

---

## 6. Synthèse des choix (open source) vs alternatives

| Couche | Techno retenue | Alternatives écartées | Raison principale |
|--------|----------------|------------------------|-------------------|
| Ingestion | **Apache Kafka** | RabbitMQ, Pulsar, Kinesis | log rejouable, débit, standard, connecteurs |
| Data Lake | **MinIO** (S3) | HDFS, NAS, base SQL | léger, cloud-native, découplage calcul/stockage |
| Format | **Parquet** (+ Avro dans Kafka) | CSV, ORC | colonne + compression pour l'analytique |
| Batch | **Apache Spark** | MapReduce, Dask | en mémoire, distribué, SQL/ML |
| Speed | **Structured Streaming / Kafka Streams** | Storm, Flink | intégration Spark/Kafka, courbe d'apprentissage |
| Temps réel (store) | **QuestDB** | InfluxDB, Cassandra, PostgreSQL | time-series SQL, ingestion massive |
| Serving | **QuestDB + PostgreSQL** | — | RT + indicateurs relationnels |
| Restitution | **Streamlit + Grafana** | Superset, Metabase | exploration + monitoring temps réel |
| Orchestration | **Apache Airflow** | cron, Luigi | DAG, reprises, monitoring |

---

## 7. Conclusion

En re-formulant UrbanHub sous forme d'**architecture Lambda**, on obtient une
plateforme qui **ingère** (Kafka), **stocke** (data lake MinIO/Parquet),
**transforme** (Spark en batch, Structured Streaming en temps réel) et **restitue**
(QuestDB + Streamlit/Grafana) des données urbaines **à grande échelle, en batch et
en temps réel**. Chaque brique est **open source** et choisie pour une raison
précise face à ses concurrentes — ce qui répond directement à l'exigence
« *pourquoi telle techno open source et non une autre* ».
