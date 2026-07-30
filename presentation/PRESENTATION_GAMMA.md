# Présentation Gamma — UrbanHub : Architecture Big Data + Veille QuestDB

Ce fichier contient **tout ce qu'il faut** pour générer la présentation dans
**Gamma** (gamma.app) : un prompt court (génération auto) **ou** un plan détaillé
carte par carte (recommandé), avec le texte des diapos et les notes orateur.

---

## Option A — Prompt court (Gamma → « Générer » → « Texte »)

Colle ce prompt dans Gamma (mode *Generate from text/prompt*) :

> Crée une présentation de meetup technique (public data/dev), ton didactique et
> professionnel, ~14 diapositives, sur le projet **UrbanHub** : un jumeau numérique
> urbain (Smart City) repensé comme une **architecture Big Data Lambda** capable
> d'ingérer, stocker, transformer et restituer des données à grande échelle, en
> batch et en temps réel. Couvre : le contexte Smart City, les 3 flux (batch
> météo, streaming vélos, IoT pollution), l'architecture Lambda (couches Batch,
> Speed, Serving), la justification des choix de technos open source (Kafka,
> MinIO, Parquet, Spark, QuestDB, Airflow) face à leurs concurrentes, un **zoom
> veille technologique sur QuestDB** (base time-series), une démo de résultats
> réels, et une conclusion avec perspectives. Style visuel épuré, bleu marine +
> turquoise, icônes tech.

---

## Option B — Plan détaillé à coller (recommandé)

Dans Gamma : **New → Paste in text → Create**. Colle le bloc ci-dessous
(chaque `---` = une nouvelle carte/diapo). Ajoute l'image
`docs/images/architecture_bigdata.png` sur la diapo Architecture, et
`data/curated/reports/*.png` là où c'est indiqué.

---

# UrbanHub — Une architecture Big Data pour la Smart City

Jumeau numérique urbain : ingérer, stocker, transformer et restituer les données de la ville, en batch **et** en temps réel.

🎤 *Notes : Bonjour, aujourd'hui je vous présente UrbanHub, un jumeau numérique urbain. L'idée : construire non pas une base de données classique, mais une vraie architecture Big Data.*

---

# Le contexte : une ville qui produit des données en continu

- Capteurs IoT (pollution, bruit, incidents), énergie, météo, trafic, événements
- Des données **massives**, **hétérogènes**, à **vitesses différentes**
- Objectif : produire des **indicateurs utiles aux décideurs publics**

🎤 *Notes : Une Smart City génère des flux en permanence. Le défi n'est pas la donnée elle-même, mais l'architecture capable de l'absorber et de l'exploiter.*

---

# Le vrai enjeu : d'une base classique à une architecture Big Data

- Base classique = 1 serveur, mémoire limitée, batch seulement
- Big Data = **distribué**, **batch + temps réel**, tolérant aux pannes
- On passe d'un **script** à une **plateforme**

🎤 *Notes : L'objectif n'est plus de traiter des données dans une base classique, mais de bâtir une architecture qui ingère, stocke, transforme et restitue à grande échelle.*

---

# Trois flux, trois natures de données

- **Batch** — météo NOAA, 5 ans d'historique (données massives)
- **Streaming** — vélos CityBikes, temps réel (chaque minute)
- **IoT** — pollution OpenAQ, capteurs (PM2.5, NO₂, O₃…)

🎤 *Notes : Ces trois flux couvrent les trois grandes façons dont une ville produit de la donnée : historique, temps réel, capteurs.*

---

# L'architecture cible : Lambda (Batch + Speed + Serving)

*(Insérer l'image `docs/images/architecture_bigdata.png`)*

- **Couche Batch** : vues exactes sur tout l'historique
- **Couche Speed** : vues fraîches en temps réel
- **Couche Serving** : fusion et restitution

🎤 *Notes : L'architecture Lambda combine un chemin batch (précis, lent) et un chemin temps réel (frais, approché) qui convergent vers une couche de service unique. Parfait pour UrbanHub qui mêle historique massif et temps réel.*

---

# Ingestion — Apache Kafka

- Bus d'événements pour les flux temps réel (vélos, pollution)
- **Kafka Connect** : des centaines de connecteurs Source/Sink
- **Pourquoi Kafka ?** log rejouable, très haut débit, standard de fait

🎤 *Notes : Kafka découple producteurs et consommateurs et conserve les messages, ce qui permet de ré-alimenter la couche batch. vs RabbitMQ (file éphémère), vs Pulsar (écosystème plus petit), vs Kinesis (propriétaire).*

---

# Stockage — Data Lake MinIO + Parquet

- **MinIO** : stockage objet compatible S3, zones raw / processed / curated
- **Parquet** : format colonne compressé, idéal analytique
- **Pourquoi ?** vs HDFS (trop lourd), vs SQL (pas fait pour le brut massif)

🎤 *Notes : Le data lake garde la donnée telle quelle (schema-on-read). MinIO est léger et cloud-native. Parquet pour l'analyse ; Avro plutôt dans Kafka pour l'échange.*

---

# Couche Batch — Apache Spark

- Traitement **distribué** de tout l'historique (météo 5 ans)
- Nettoyage, agrégats, z-scores, jointures → **vues batch**
- **Pourquoi Spark ?** en mémoire (10–100× MapReduce), SQL/ML, tolérant aux pannes

🎤 *Notes : Spark remplace le pandas du prototype à l'échelle. vs MapReduce (lent), vs Dask (moins standard en entreprise).*

---

# Couche Speed + Serving — QuestDB (zoom veille)

- Streaming (Structured Streaming / Kafka Streams) → **QuestDB**
- QuestDB : base **time-series** open source, SQL, ingestion massive
- **Pourquoi QuestDB ?** vs InfluxDB (vrai SQL), vs Cassandra (bien plus simple)

🎤 *Notes : QuestDB est notre techno de veille. Elle joue à la fois la couche Speed (ingestion temps réel) et Serving (requêtes rapides pour le dashboard).*

---

# Veille : QuestDB en détail

- Ingestion **ILP** mesurée à **~500 000–600 000 lignes/seconde**
- SQL time-series : `SAMPLE BY`, `LATEST ON`, `ASOF JOIN`, `FILL`
- Console web + compatibilité **PostgreSQL wire** (Grafana, psql, BI)
- Déploiement **Docker** et **Kubernetes** (StatefulSet)

🎤 *Notes : QuestDB apporte le confort du SQL au monde du streaming/IoT. L'ASOF JOIN aligne deux flux sur l'instant le plus proche — parfait pour corréler pollution et météo.*

---

# Démo — résultats réels

*(Insérer une capture de `results/DEMO_OUTPUT.md` ou `docs/images/diurnal_profile.png`)*

- Classement des villes par ozone, dépassements de seuils OMS
- Corrélation **ozone ↔ température ≈ 0,93** (photochimie)
- Pics de NO₂ aux heures de pointe

🎤 *Notes : Ces résultats sortent de vraies requêtes SQL sur QuestDB. Le fait de retrouver la loi physique ozone/température valide l'approche.*

---

# Restitution — Streamlit / Grafana

- **Streamlit** : dashboard analytique interactif (filtres villes/polluants)
- **Grafana** : monitoring temps réel branché sur QuestDB (PostgreSQL wire)

🎤 *Notes : La couche restitution. Streamlit pour l'exploration, Grafana pour le suivi temps réel. (Montrer le dashboard 30 s si démo.)*

---

# Récapitulatif des choix open source

| Couche | Techno | Pourquoi (vs) |
|--------|--------|---------------|
| Ingestion | Kafka | vs RabbitMQ / Pulsar / Kinesis |
| Data Lake | MinIO + Parquet | vs HDFS / CSV / ORC |
| Batch | Spark | vs MapReduce / Dask |
| Temps réel | QuestDB | vs InfluxDB / Cassandra |
| Restitution | Streamlit / Grafana | exploration + monitoring |
| Orchestration | Airflow | vs cron |

🎤 *Notes : Chaque brique est open source et choisie face à ses concurrentes — c'est le cœur de la veille technologique.*

---

# Conclusion & perspectives

- Une plateforme qui **ingère, stocke, transforme, restitue** — batch **et** temps réel
- Techno **open source** justifiées, architecture **Lambda** claire
- Perspectives : Airflow en production, stockage S3, **modèles prédictifs** (IA)

🎤 *Notes : Merci ! UrbanHub montre comment passer d'un prototype à une vraie architecture Big Data. Questions ?*

---

## Réglages Gamma conseillés
- **Nombre de cartes** : 14
- **Ton** : professionnel / didactique
- **Thème** : sombre ou clair épuré, accent **bleu marine + turquoise**
- **Format** : 16:9 (présentation)
- Après génération : remplace les images par les tiennes
  (`docs/images/architecture_bigdata.png`, `docs/images/diurnal_profile.png`,
  `data/curated/reports/*.png`).
- Active les **notes orateur** (elles sont déjà écrites, préfixe 🎤) pour ton recording.

## À propos de l'app Streamlit
Non exigée pour ce livrable, mais **conservée** comme illustration de la couche
Restitution/Serving. La montrer brièvement (ou une capture) suffit.
