# UrbanHub — Script de soutenance (15 min · 4 intervenants)

Document à partager avec toute l'équipe. Chaque partie contient le **texte à dire mot pour mot** + la **phrase de transition** vers le suivant.

| Ordre | Intervenant | Partie | Diapos | Durée |
|-------|-------------|--------|--------|-------|
| 1 | **DZIRI RAYANE** | Introduction & contexte | 1 → 4 | ~3 min |
| 2 | **HAMMA SOFIANE** | Architecture, chiffres, flux Batch (météo) | 5 → 7 | ~3 min 30 |
| 3 | **LEKOUARA ABDELRAFIK** | Flux Streaming, IoT & analyse croisée | 8 → 10 | ~4 min |
| 4 | **AIT TAYEB LYES** | Démo appli + explication du code + conclusion | 11 → 12 | ~4 min 30 |

> Règle d'or : parler **lentement**, regarder le jury, et bien marquer les transitions — c'est ce qui donne l'impression d'une équipe soudée.

---

# 1. DZIRI RAYANE — Introduction & contexte (~3 min)

### Diapo 1 — Titre
> « Bonjour à toutes et à tous. Nous allons vous présenter notre projet : **UrbanHub**, une plateforme Big Data que nous décrivons comme un **jumeau numérique urbain** — c'est-à-dire un système qui permet d'**observer et d'analyser le fonctionnement d'une ville moderne** à partir de ses données. »

### Diapo 2 — Notre équipe
> « Nous sommes une équipe de quatre : moi-même Rayane, ainsi que Sofiane, Abdelrafik et Lyes. Chacun va présenter une partie du projet. Moi je commence par le **contexte et l'objectif**. Sofiane enchaînera sur l'**architecture** et le **premier flux de données**. Abdelrafik présentera les **deux autres flux et l'analyse croisée**. Et Lyes terminera par une **démonstration de l'application et du code**. »

### Diapo 3 — Agenda
> « Voici notre déroulé : d'abord le contexte d'une Smart City, ensuite l'architecture technique de la plateforme, puis nos trois cas d'usage — la **météo**, la **mobilité** et la **qualité de l'air** —, ensuite l'**analyse croisée** de ces données, et enfin le **tableau de bord** interactif et la conclusion. »

### Diapo 4 — Contexte Smart City
> « Alors, pourquoi ce projet ? Une **Smart City** — une ville intelligente — génère des données **en permanence** et de sources très variées : des capteurs IoT pour la pollution, le bruit ou les incidents, la consommation d'énergie, les données météo, les flux de trafic, les événements urbains…
>
> Le défi, c'est que ces données sont **massives, hétérogènes, et arrivent à des vitesses différentes**. Certaines sont historiques, d'autres en temps réel, d'autres viennent de capteurs. Il faut donc être capable de les **collecter, les stocker, les traiter et les analyser** pour en tirer des **indicateurs utiles aux décideurs publics**.
>
> C'est tout l'objectif d'UrbanHub. Et pour être représentatif d'un vrai système Big Data, nous avons volontairement choisi de couvrir les **trois grands types de flux** :
> - un **flux Batch** : des données **historiques massives** — la météo horaire sur 5 ans ;
> - un **flux Streaming** : des données **temps réel** — les vélos en libre-service ;
> - un **flux IoT** : des données **capteurs** — la pollution de l'air.
>
> Ces trois natures — historique, temps réel, capteurs — sont exactement ce qu'on retrouve dans une vraie plateforme Smart City.
>
> **Transition :** *Pour vous expliquer comment on a construit tout ça techniquement, je laisse la parole à Sofiane.* »

---

# 2. HAMMA SOFIANE — Architecture, chiffres & flux Batch (~3 min 30)

### Diapo 5 — Architecture (chaîne de valeur)
> « Merci Rayane. Techniquement, UrbanHub est bâti comme une **chaîne de valeur de la donnée**, en six étapes que vous voyez à l'écran : les **sources**, l'**ingestion**, le **stockage** dans un data lake, le **traitement**, l'**analyse**, et enfin les **indicateurs urbains**.
>
> La pièce maîtresse, c'est le **data lake**, organisé en trois zones bien distinctes :
> - la zone **raw**, la donnée **brute** telle qu'on la reçoit, qu'on ne modifie jamais ;
> - la zone **processed**, la donnée **nettoyée et normalisée**, stockée au format **Parquet**, un format colonne très efficace pour l'analyse ;
> - et la zone **curated**, qui contient les **indicateurs finaux**, prêts à être exploités.
>
> On utilise aussi un **partitionnement par date** — année, mois, jour — c'est la convention standard des data lakes, qui permet de ne retraiter que les nouvelles données. Et tout est piloté par une **interface en ligne de commande unique**, ce qui rend la plateforme simple à faire tourner. »

### Diapo 6 — Chiffres clés
> « Et ce ne sont pas des données fictives : la plateforme fonctionne avec des **données réelles**, récupérées via des API publiques. À ce stade, elle a déjà traité plus de **24 000 observations météo**, collecté environ **5 600 stations de vélos** réparties sur **65 réseaux français**, et plus de **5 300 mesures de pollution** sur les **12 principales villes** de France. »

### Diapo 7 — Partie 1 : Batch météo (NOAA)
> « Passons au premier flux, le **flux Batch**, qui concerne la **météo**. La source, ce sont les données horaires mondiales du **NOAA**, l'agence américaine d'observation océanique et atmosphérique.
>
> Le premier point technique important, c'est la **collecte** : on télécharge les fichiers de **toutes les stations françaises**, sur **5 ans d'historique**, et surtout **en parallèle** — grâce à du multi-threading — pour ne pas les télécharger un par un, ce qui serait beaucoup trop lent.
>
> Ensuite vient le **nettoyage**, qui est le vrai travail de data engineering. Le format brut du NOAA est complexe : plusieurs mesures sont encodées dans un même champ, avec des **valeurs manquantes codées** par des chiffres spéciaux. On les **décode**, on **convertit les unités** — par exemple la température est stockée en dixièmes de degré —, on normalise l'**horodatage en UTC**, et on calcule même l'**humidité relative** à partir de la température et du point de rosée.
>
> Grâce à ces données propres, on répond aux **questions métier** : on détecte des **périodes météo anormales** avec un score statistique, on mesure la **corrélation entre les conditions météo et la visibilité**, on trace l'**évolution saisonnière** de la température, et on identifie les **jours extrêmes** — ici par exemple un pic à **+37 °C** et un minimum à **−5,9 °C**.
>
> **Transition :** *Abdelrafik va maintenant vous présenter les deux flux temps réel et l'analyse croisée.* »

---

# 3. LEKOUARA ABDELRAFIK — Streaming, IoT & analyse croisée (~4 min)

### Diapo 8 — Partie 2 : Streaming vélos (CityBikes)
> « Merci Sofiane. Le deuxième flux est un flux **Streaming**, donc en **temps réel** : il s'agit de la disponibilité des **vélos en libre-service**, via l'API **CityBikes**, qui couvre les réseaux du monde entier.
>
> On a mis en place un système de **récupération automatique toutes les minutes** de l'état de **toutes les stations françaises** — Vélib' à Paris compris. À chaque relevé, pour chaque station, on extrait : l'**identifiant**, le **nom**, les **coordonnées GPS**, le nombre de **vélos disponibles**, le nombre de **places libres**, et l'**horodatage**.
>
> Avec ça, on répond à des questions très concrètes pour un exploitant : quelles sont les **stations les plus utilisées**, où l'**offre de vélos est insuffisante**, quels sont les **pics d'utilisation** dans la journée, s'il existe des **déséquilibres entre les quartiers**, et surtout quelles sont les **stations critiques à rééquilibrer** — celles qui sont trop souvent **vides** ou au contraire **pleines**. C'est directement actionnable sur le terrain. »

### Diapo 9 — Partie 3 : IoT pollution (OpenAQ)
> « Le troisième flux est un flux **IoT** : la **pollution atmosphérique**, via l'API **OpenAQ**, qui agrège des capteurs de qualité de l'air. On suit les **six polluants principaux** : les particules fines **PM2.5** et **PM10**, le dioxyde d'azote **NO₂**, l'ozone **O₃**, le dioxyde de soufre **SO₂** et le monoxyde de carbone **CO**.
>
> L'ingestion est **régulière**, elle **simule un flux de capteurs IoT**. On a prévu deux modes : un **mode réel** qui interroge l'API avec une clé, et un **simulateur réaliste** qui reproduit les cycles de la journée — par exemple les pics de **NO₂ aux heures de pointe** liés au trafic, ou le pic d'**ozone l'après-midi**. On peut même générer un historique pour alimenter les analyses.
>
> On identifie ainsi les **villes les plus polluées** par polluant, les **profils horaires**, les **dépassements des seuils de l'OMS**, et on calcule un **indice de qualité de l'air** par ville pour les classer. »

### Diapo 10 — Partie 4 : Analyse croisée
> « Et c'est ici que la plateforme prend toute sa valeur : l'**analyse croisée** des trois flux. Le défi, c'est qu'ils n'ont pas la même profondeur dans le temps — la météo est historique, les vélos et la pollution sont en temps réel. Pour les croiser proprement, on les compare sur le **cycle d'une journée type**, heure par heure.
>
> Le résultat le plus marquant : l'**ozone est corrélé à 0,93 avec la température** — un coefficient très élevé. Et c'est **physiquement juste** : l'ozone se forme par réaction photochimique, donc quand il fait chaud et ensoleillé. Ça valide notre approche.
>
> On étudie aussi l'**influence de la météo sur l'usage des vélos**, et on définit des **conditions favorables à la mobilité douce** — une température douce, pas de pluie, un vent faible — qu'on retrouve nettement plus souvent **en été**.
>
> **Transition :** *Pour voir tout cela en action, je laisse Lyes vous faire la démonstration de l'application et vous présenter le code.* »

---

# 4. AIT TAYEB LYES — Démo, code & conclusion (~4 min 30)

> Ta partie a **trois temps** : (A) la démo du tableau de bord, (B) l'explication détaillée du code — **tu montres le code à l'écran**, (C) la conclusion.

## A. Diapo 11 — Le tableau de bord (démo) (~1 min 15)

> « Merci Abdelrafik. Toutes ces données sont restituées dans un **tableau de bord interactif** que nous avons développé avec **Streamlit**. Je vous le montre en direct.
>
> Il est organisé en **quatre onglets** — Météo, Mobilité, Pollution, et Analyse croisée. En haut, on a les **indicateurs clés** de la plateforme.
>
> Et le plus important, dans la **barre latérale à gauche** : des **filtres interactifs** sous forme de menus déroulants à cases à cocher. Je peux sélectionner des **villes**, des **polluants**, des **réseaux** — et vous voyez que **tous les graphiques se recalculent en direct**.
>
> *(Clique sur les onglets en parlant.)* Sur **Mobilité**, on a la **carte des stations** de vélos ; sur **Pollution**, le **classement des villes** et les **profils horaires** ; et sur l'onglet **Analyse croisée**, la fameuse **matrice de corrélation** météo-pollution avec l'ozone et la température. »

## B. Explication du code — tu montres les fichiers (~2 min 30)

> **Conseil : ouvre le dossier `urbanhub/` dans ton éditeur.** Le message central : *« le code est organisé exactement comme l'architecture — un dossier par étape »*. Suis cet ordre :

**1) Introduction (montre l'arborescence du dossier `urbanhub/`)**
> « Le projet est un **package Python appelé `urbanhub`**. Et vous allez voir qu'il est structuré comme l'architecture qu'on vous a montrée : il y a un dossier pour chaque étape de la chaîne — ingestion, processing, analysis — plus la configuration et l'orchestrateur. »

**2) `config.py`**
> « On commence par `config.py`, la **configuration centrale**. C'est ici qu'on définit les **chemins du data lake** — les trois zones raw, processed et curated — la **liste des 12 villes françaises**, et les **paramètres des trois sources** : les URLs des API, la fréquence de collecte, la liste des polluants. Tout est centralisé, donc facile à modifier. »

**3) `utils/storage.py`**
> « Ensuite, `utils/storage.py`, c'est notre **couche d'accès au data lake**. Elle contient les fonctions pour **écrire et lire** les données : `write_parquet` pour les données nettoyées, `append_jsonl` pour les flux temps réel — un enregistrement par ligne —, et `date_partition` qui génère les dossiers `année / mois / jour`. »

**4) `ingestion/` — montre les 3 fichiers**
> « Le dossier `ingestion` contient un fichier par flux :
> - Dans `batch_weather.py`, la fonction `download_weather` lance les téléchargements **en parallèle** avec un `ThreadPoolExecutor` — c'est ce qui rend la collecte rapide.
> - Dans `streaming_citybikes.py`, la fonction `collect_once` prend un **instantané** de toutes les stations, et `stream` la répète **toutes les minutes**.
> - Dans `iot_openaq.py`, on a le **mode réel** qui appelle l'API, et le **simulateur** `_collect_simulated` qui prend le relais s'il n'y a pas de clé — avec les cycles horaires réalistes dont parlait Abdelrafik. »

**5) `processing/` — montre `weather.py`**
> « Le dossier `processing`, c'est le **nettoyage**. Regardez `weather.py` : ces petites fonctions `_parse_temp`, `_parse_wind`, `_parse_visibility`… c'est elles qui **décodent le format brut** du NOAA, gèrent les **valeurs manquantes** et **convertissent les unités**. À la fin, on écrit un fichier **Parquet** propre. C'est pareil pour les vélos et la pollution. »

**6) `analysis/` — montre `cross_analysis.py`**
> « Le dossier `analysis` contient un module par flux, plus l'analyse croisée. Chaque fonction `run` lit le Parquet, **calcule les réponses aux questions métier**, et écrit un **fichier d'indicateurs en JSON** plus des **graphiques**. Par exemple, `cross_analysis.py`, c'est lui qui croise les flux sur le cycle diurne et sort la fameuse **corrélation ozone-température**. »

**7) `dashboard/app.py`**
> « Et voilà l'application que je viens de montrer : `dashboard/app.py`. Elle lit les indicateurs et les données nettoyées, applique les filtres, et affiche les graphiques. »

**8) `cli.py` — le chef d'orchestre**
> « Enfin, le fichier le plus important pour comprendre l'ensemble : `cli.py`, l'**orchestrateur**. Il expose des commandes — `init`, `batch`, `stream`, `iot`, `process`, `analyze`, `dashboard` — et une commande `pipeline` qui **enchaîne toute la chaîne automatiquement**. Donc pour tout relancer, une seule ligne suffit : `python -m urbanhub.cli pipeline`.
>
> Petit bonus dont on est assez fiers : même **la présentation PowerPoint et le document des réponses aux questions sont générés automatiquement** par le code, à partir des vrais indicateurs. »

## C. Diapo 12 — Conclusion (~30 s)

> « Pour conclure : nous livrons les **scripts de collecte** des trois flux, un **stockage structuré** en data lake, tout le **traitement**, les **analyses et les indicateurs urbains**, et le **tableau de bord** interactif.
>
> En perspectives, on pourrait **planifier l'ingestion** avec un ordonnanceur comme Airflow, passer à un **stockage objet** type S3, et ajouter des **modèles prédictifs** — par exemple prévoir la pollution ou la demande de vélos.
>
> Merci beaucoup de votre attention. Nous sommes à votre disposition pour vos questions. »

---

# ANNEXE (spécial Lyes) — Explication approfondie du code, fichier par fichier

À garder sous la main **au cas où le jury demande des détails**. Ordre logique de navigation : *point d'entrée → config → data lake → ingestion → traitement → analyse → restitution.*

### `urbanhub/cli.py` — le point d'entrée
- Utilise le module standard `argparse` pour créer des **sous-commandes**.
- Chaque commande a une fonction `cmd_*` :
  - `cmd_init` → crée l'arborescence du data lake.
  - `cmd_batch` → appelle `batch_weather.download_weather(...)`.
  - `cmd_stream` → appelle `streaming_citybikes.stream(...)`.
  - `cmd_iot` → appelle `iot_openaq.stream(...)` ou `backfill(...)`.
  - `cmd_process` → nettoie les 3 flux.
  - `cmd_analyze` → lance les 4 analyses.
  - `cmd_dashboard` → lance Streamlit.
  - `cmd_pipeline` → **enchaîne tout** : ingestion → process → analyze.
- **À dire :** « C'est le chef d'orchestre : il ne contient pas de logique métier, il **délègue** à chaque module. »

### `urbanhub/config.py` — la configuration
- `DATA_DIR` et les zones `RAW_DIR` / `PROCESSED_DIR` / `CURATED_DIR`, avec les sous-dossiers par flux.
- `ensure_dirs()` crée tous les dossiers.
- `FRANCE_CITIES` : les 12 villes avec latitude/longitude.
- Trois blocs de config : `NOAA` (URL, 5 ans, nb de threads), `CITYBIKES` (intervalle 60 s), `OPENAQ` (polluants, clé API via variable d'environnement).
- **À dire :** « Aucune valeur "en dur" ailleurs dans le code : tout paramètre se change ici. »

### `urbanhub/utils/storage.py` — accès au data lake
- `write_parquet` / `read_parquet_dir` : la donnée nettoyée (format colonne).
- `append_jsonl` / `read_jsonl_dir` : les snapshots temps réel (JSON Lines, append).
- `write_json`, `write_csv` : les indicateurs.
- `date_partition()` : renvoie `year=YYYY/month=MM/day=DD`.
- **À dire :** « Cette couche isole le reste du code du stockage : si demain on passe sur S3, on ne modifie que ce fichier. »

### `urbanhub/ingestion/batch_weather.py` — flux Batch
- `fetch_france_stations()` : télécharge le référentiel `isd-history.csv` et **filtre les stations FR** actives sur la période.
- `_download_one()` : télécharge un fichier `station.csv` (et gère les 404).
- `download_weather()` : crée toutes les tâches (stations × années) et les exécute **en parallèle** avec `ThreadPoolExecutor`.
- **À dire :** « Le point clé, c'est le parallélisme : on lance des dizaines de téléchargements simultanés. »

### `urbanhub/ingestion/streaming_citybikes.py` — flux Streaming
- `list_france_networks()` : liste les réseaux dont le pays est la France.
- `_network_snapshot()` : récupère toutes les stations d'un réseau et extrait les 7 variables demandées.
- `collect_once()` : un instantané complet, écrit en JSON Lines partitionné par date.
- `stream()` : boucle avec un `time.sleep(interval)` — par défaut toutes les 60 s.

### `urbanhub/ingestion/iot_openaq.py` — flux IoT
- `_collect_real()` : appelle l'API OpenAQ (en-tête `X-API-Key`).
- `_collect_simulated()` : génère des mesures **réalistes** avec variation horaire (rush NO₂, ozone l'après-midi, fond plus élevé dans les grandes villes).
- `collect_once()` : choisit automatiquement réel ou simulé selon la présence de la clé.
- `backfill()` : génère un **historique** (ex. 72 h) pour les analyses temporelles.
- `stream()` : boucle régulière.
- **À dire :** « Le simulateur permet de démontrer toute la chaîne même sans clé API — et le sujet demandait justement de *simuler* un flux IoT. »

### `urbanhub/processing/weather.py` — nettoyage météo
- Fonctions `_parse_temp`, `_parse_pressure`, `_parse_visibility`, `_parse_wind`, `_parse_precip` : **décodent le format ISD** (valeurs entières signées, sentinelles pour les manquants).
- `_nearest_city()` : rattache chaque station à la ville la plus proche.
- `_season()` : mappe le mois → saison.
- `process_weather()` : lit tous les CSV bruts, applique le nettoyage, filtre les valeurs aberrantes, déduplique, écrit le Parquet.

### `urbanhub/processing/citybikes.py` & `openaq.py`
- `process_citybikes()` : type les colonnes, calcule la **capacité** et le **taux d'occupation**, les indicateurs vide/plein.
- `process_openaq()` : nettoie les mesures ; `pivot_city_hour()` fait une vue ville × heure avec une colonne par polluant.

### `urbanhub/analysis/` — les 4 analyses
- `weather_analysis.py` : z-score des anomalies, corrélation visibilité, saisons, jours extrêmes.
- `mobility_analysis.py` : stations les plus utilisées, offre insuffisante, profil horaire, déséquilibres, stations critiques.
- `pollution_analysis.py` : villes les plus polluées, profils horaires, dépassements de seuils, indice qualité de l'air.
- `cross_analysis.py` : croisement sur le **cycle diurne**, corrélations météo × pollution × vélos.
- Chaque `run()` écrit un **JSON d'indicateurs** dans `curated/indicators` et des **PNG** dans `curated/reports`.

### `urbanhub/dashboard/app.py` — Streamlit
- Charge les indicateurs (JSON) et les données (Parquet), avec cache.
- Barre latérale = **filtres** (menus déroulants à cases à cocher, fonction `dropdown_checkboxes`).
- 4 onglets ; wrappers `safe_image` / `safe_dataframe` / `safe_map` pour être **compatible toutes versions** de Streamlit.

### `urbanhub/presentation.py` & `report_doc.py`
- Génèrent automatiquement le **PowerPoint** et le **document Word/Markdown** des réponses, à partir des indicateurs. Commandes : `slides` et `doc`.

**Phrase de synthèse (à connaître par cœur) :**
> « Le code reflète exactement l'architecture : *ingestion → stockage → traitement → analyse → visualisation*, avec un module dédié par flux et un orchestrateur CLI unique. Toute la chaîne se relance avec une seule commande : `python -m urbanhub.cli pipeline`. »

---

# Astuces pour toute l'équipe
- **Répétez au moins une fois** à voix haute, chronométré.
- **Lancez la démo AVANT** de commencer (`python -m urbanhub.cli dashboard`) pour éviter le temps de chargement devant le jury.
- **Plan B** : si pas d'internet, utilisez les captures d'écran du dashboard.
- **Transitions** : chacun termine en nommant le suivant (« je laisse la parole à… »).
- **Gardez ~1 minute** de marge pour les questions.
- **Questions probables du jury** : « Pourquoi un data lake et pas une base SQL ? » (volume + hétérogénéité + formats bruts), « Comment ça passe à l'échelle ? » (partitionnement + Parquet + parallélisme, puis Spark/S3), « Le simulateur, est-ce grave ? » (non : le sujet demande de *simuler* un flux IoT, et le mode réel existe avec une clé).
