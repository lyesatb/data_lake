# UrbanHub — Script de soutenance (15 min · 4 intervenants)

Répartition indicative : **~15 minutes** au total.

| Intervenant | Partie | Diapositives | Durée |
|-------------|--------|--------------|-------|
| **DZIRI RAYANE** | Introduction & contexte | 1 → 4 | ~3 min |
| **HAMMA SOFIANE** | Architecture, chiffres, flux Batch (météo) | 5 → 7 | ~3 min 30 |
| **LEKOUARA ABDELRAFIK** | Flux Streaming, IoT & analyse croisée | 8 → 10 | ~4 min |
| **AIT TAYEB LYES** | Démo de l'application + code + conclusion | 11 → 12 | ~4 min 30 |

> Conseil : chacun termine par une **phrase de transition** qui passe la parole au suivant (déjà incluse en fin de chaque partie).

---

## 1. DZIRI RAYANE — Introduction & contexte (~3 min)

**Diapo 1 (Titre) + Diapo 2 (Notre équipe)**

> « Bonjour à tous. Nous vous présentons aujourd'hui **UrbanHub**, un **jumeau numérique urbain** : une plateforme Big Data qui observe le fonctionnement d'une ville moderne.
> Nous sommes une équipe de quatre : Rayane, Sofiane, Abdelrafik et Lyes. Je vais commencer par le contexte, puis chacun présentera une partie, et Lyes terminera par une démonstration de l'application et du code. »

**Diapo 3 (Agenda)**

> « Voici notre plan : après le contexte, nous verrons l'architecture technique, puis les trois flux de données — la météo, les vélos et la pollution — ensuite l'analyse croisée, et enfin le tableau de bord et la conclusion. »

**Diapo 4 (Contexte Smart City)**

> « Une Smart City produit des données **en permanence** : capteurs IoT, consommation d'énergie, météo, trafic, événements urbains… Le problème, c'est que ces données sont **massives, hétérogènes et de vitesses différentes**. Il faut donc être capable de les **collecter, stocker, traiter et analyser** pour produire des indicateurs utiles aux décideurs publics.
> C'est exactement le rôle d'UrbanHub. Pour couvrir un vrai système Big Data, nous avons choisi les **trois types de flux typiques** :
> - un **flux Batch** — des données historiques massives : la météo sur 5 ans ;
> - un **flux Streaming** — des données temps réel : les vélos en libre-service ;
> - un **flux IoT** — des données capteurs : la pollution de l'air.
> Ces trois natures de flux — historique, temps réel et capteurs — sont ce qui rend le projet représentatif d'une vraie plateforme Smart City.
> Je laisse la parole à Sofiane pour l'architecture. »

---

## 2. HAMMA SOFIANE — Architecture, chiffres & flux Batch (~3 min 30)

**Diapo 5 (Architecture — chaîne de valeur)**

> « Merci Rayane. Techniquement, UrbanHub suit une **chaîne de valeur de la donnée** en six étapes : les **sources**, puis l'**ingestion**, le stockage dans un **data lake**, le **traitement**, l'**analyse**, et enfin la production d'**indicateurs urbains**.
> Le cœur, c'est le **data lake**, organisé en trois zones :
> - la zone **raw** : la donnée brute, immuable, telle qu'on l'a reçue ;
> - la zone **processed** : la donnée nettoyée et normalisée, stockée en **Parquet** ;
> - la zone **curated** : les indicateurs finaux, prêts à être exploités.
> On utilise un **partitionnement par date** — année / mois / jour — la convention standard des data lakes, qui permet un traitement incrémental. Le tout est piloté par une **interface en ligne de commande unique**. »

**Diapo 6 (Chiffres clés)**

> « Concrètement, avec des **données réelles** issues des API publiques, la plateforme a déjà traité plus de **24 000 observations météo**, collecté environ **5 600 stations de vélos** sur **65 réseaux français**, et plus de **5 300 mesures de pollution** sur les 12 principales villes. »

**Diapo 7 (Partie 1 — Batch météo NOAA)**

> « Le premier flux, le **Batch**, concerne la météo, via les données horaires du **NOAA**. Le point clé côté ingénierie : on **télécharge en parallèle** les fichiers des stations françaises — jamais un par un — sur **5 ans d'historique**, grâce à du multi-threading.
> Ensuite vient le **nettoyage**, le vrai travail de data engineering : le format brut du NOAA encode plusieurs variables dans un même champ, avec des valeurs manquantes codées. On les **décode, on convertit les unités**, on normalise l'horodatage en UTC, et on calcule même l'humidité relative avec la formule de Magnus.
> Cela nous permet de répondre à des questions métier : détecter des **périodes anormales** avec un z-score, la **corrélation entre météo et visibilité**, l'**évolution saisonnière** de la température, et les **jours extrêmes** — sur cet échantillon, un pic à +37°C et un minimum à −5,9°C.
> Abdelrafik va enchaîner avec les deux autres flux. »

---

## 3. LEKOUARA ABDELRAFIK — Streaming, IoT & analyse croisée (~4 min)

**Diapo 8 (Partie 2 — Streaming vélos CityBikes)**

> « Merci Sofiane. Le deuxième flux est un flux **Streaming**, en **temps réel** : la disponibilité des vélos en libre-service, via l'API **CityBikes**.
> On a mis en place une **récupération automatique toutes les minutes** de l'état de **toutes les stations françaises** — Vélib' compris. Pour chaque station on extrait l'identifiant, le nom, les coordonnées, le nombre de **vélos disponibles**, de **places libres** et l'horodatage.
> À partir de là, on répond à des questions d'exploitation : quelles sont les **stations les plus utilisées**, les **zones où l'offre est insuffisante**, les **pics journaliers**, les **déséquilibres entre quartiers**, et surtout les **stations critiques à rééquilibrer** — soit vides, soit saturées. C'est directement actionnable pour un opérateur de mobilité. »

**Diapo 9 (Partie 3 — IoT pollution OpenAQ)**

> « Le troisième flux est un flux **IoT** : la pollution de l'air, via l'API **OpenAQ**. On suit six polluants principaux : **PM2.5, PM10, NO₂, O₃, SO₂ et CO**.
> L'ingestion est **régulière**, elle simule un flux de capteurs. Deux modes : un **mode réel** via l'API avec une clé, ou un **simulateur réaliste** qui reproduit les cycles de la journée — les pics de NO₂ aux heures de pointe, le pic d'ozone l'après-midi. On peut aussi générer un historique.
> On identifie ainsi les **villes les plus polluées** par polluant, les **profils horaires**, les **dépassements des seuils de l'OMS**, et on construit un **indice de qualité de l'air** par ville. »

**Diapo 10 (Partie 4 — Analyse croisée)**

> « Et c'est là que la plateforme prend tout son sens : l'**analyse croisée** des trois flux. Comme ils n'ont pas la même profondeur temporelle, on les croise sur le **cycle de la journée**.
> Résultat marquant : l'**ozone est corrélé à 0,93 avec la température** — c'est la signature de sa formation photochimique, un résultat physiquement juste. On regarde aussi l'influence de la météo sur l'usage des vélos, et on définit des **conditions favorables à la mobilité douce** — température douce, sans pluie, vent faible — nettement plus fréquentes en été.
> Pour voir tout ça vivant, je passe la parole à Lyes pour la démonstration. »

---

## 4. AIT TAYEB LYES — Démo de l'application + code + conclusion (~4 min 30)

> Ta partie a deux temps : **(A)** la démo du tableau de bord, **(B)** l'explication du code. Termine par la conclusion.

### A. Diapo 11 — Le tableau de bord (démo live si possible) (~1 min 30)

> « Merci Abelrafik. Toute cette donnée est restituée dans un **tableau de bord interactif**, développé avec **Streamlit**. Je vous le montre.
> Il est organisé en **quatre onglets** — Météo, Mobilité, Pollution et Analyse croisée. En haut, des **indicateurs clés**. Et surtout, dans la barre latérale, des **filtres interactifs** — des menus déroulants à cases à cocher — pour choisir les villes, les polluants ou les réseaux : tous les graphiques **se recalculent en direct**.
> Par exemple sur l'onglet Mobilité, on a la **carte des stations vélos** ; sur Pollution, le **classement des villes** et les **profils horaires** ; et sur l'onglet croisé, la **matrice de corrélation** météo-pollution. »

*(Si pas de démo live : « Voici des captures » et commente les mêmes éléments.)*

### B. Explication du code (~2 min 30)

> Objectif : montrer que le code est **structuré comme une vraie plateforme**, pas un simple script. Suis ce fil : **arborescence → un module par étape → l'orchestrateur.**

> « Côté code, le projet est un **package Python `urbanhub`**, organisé exactement comme l'architecture, un dossier par étape de la chaîne :
>
> - **`config.py`** : la configuration centrale — les chemins du data lake, la liste des villes françaises, et les paramètres des trois sources (URL, fréquences, polluants). Tout est centralisé ici.
>
> - **`utils/`** : les briques transverses — un module **`storage.py`** qui gère la lecture/écriture dans le data lake (Parquet, JSON Lines) avec le partitionnement par date, et la journalisation.
>
> - **`ingestion/`** : un fichier par flux.
>   - `batch_weather.py` télécharge la météo **en parallèle** avec un *ThreadPoolExecutor* ;
>   - `streaming_citybikes.py` interroge l'API vélos en boucle **toutes les minutes** ;
>   - `iot_openaq.py` ingère la pollution, avec le **mode réel et le simulateur**.
>
> - **`processing/`** : le **nettoyage**. Par exemple `weather.py` décode le format brut du NOAA, convertit les unités, gère les valeurs manquantes, et écrit du **Parquet** propre. Idem pour les vélos et la pollution.
>
> - **`analysis/`** : quatre modules qui **répondent aux questions métier** et produisent les indicateurs (JSON, CSV) et les graphiques — météo, mobilité, pollution, et croisé.
>
> - **`dashboard/app.py`** : l'application Streamlit que je viens de montrer.
>
> - Et enfin **`cli.py`**, l'**orchestrateur** : c'est le chef d'orchestre. Il expose des commandes — `init`, `batch`, `stream`, `iot`, `process`, `analyze`, `dashboard` — et une commande `pipeline` qui enchaîne toute la chaîne d'un coup.
>
> Donc le flux complet est simple : on **ingère** la donnée brute, on la **stocke** dans le data lake, on la **nettoie** en Parquet, on **analyse** pour sortir les indicateurs, et on **visualise** dans le dashboard. Le même schéma pour les trois flux. Petit bonus : même cette **présentation et le document des réponses sont générés automatiquement** par le code, à partir des vrais indicateurs. »

### C. Diapo 12 — Conclusion (~30 s)

> « Pour conclure : nous livrons les **scripts de collecte** des trois flux, un **stockage structuré** en data lake, le **traitement**, les **analyses et indicateurs**, et le **tableau de bord**. En perspective, on pourrait planifier l'ingestion avec un ordonnanceur comme Airflow, passer à un stockage objet type S3, et ajouter des **modèles prédictifs** — prévision de la pollution ou de la demande de vélos. Merci de votre attention, nous sommes disponibles pour vos questions. »

---

## Mémo « comment expliquer TOUT le code » (pour Lyes)

Si le jury te demande d'aller plus loin dans le code, garde cette logique en tête. Le principe : **une étape de l'architecture = un dossier**.

1. **Point d'entrée : `urbanhub/cli.py`**
   - C'est le fichier à ouvrir en premier. Il utilise `argparse` pour créer des sous-commandes.
   - Chaque sous-commande (`batch`, `stream`, `iot`, `process`, `analyze`, `dashboard`, `slides`, `doc`) appelle une fonction `cmd_*` qui délègue au bon module.
   - La commande `pipeline` appelle tout dans l'ordre : ingestion → traitement → analyse.

2. **Configuration : `urbanhub/config.py`**
   - Définit `DATA_DIR` et les zones `RAW_DIR`, `PROCESSED_DIR`, `CURATED_DIR`.
   - Contient `FRANCE_CITIES` (les 12 villes) et trois blocs de config `NOAA`, `CITYBIKES`, `OPENAQ`.
   - `ensure_dirs()` crée l'arborescence du data lake.

3. **Data lake : `urbanhub/utils/storage.py`**
   - `write_parquet` / `read_parquet_dir` : la donnée nettoyée.
   - `append_jsonl` / `read_jsonl_dir` : les flux temps réel (un enregistrement par ligne).
   - `date_partition()` : génère `year=/month=/day=`.

4. **Ingestion — `urbanhub/ingestion/`**
   - `batch_weather.py` : `fetch_france_stations()` filtre les stations FR dans le référentiel `isd-history.csv` ; `download_weather()` lance les téléchargements **en parallèle** (`ThreadPoolExecutor`) et écrit dans `raw`.
   - `streaming_citybikes.py` : `list_france_networks()` puis `collect_once()` prend un « snapshot » de toutes les stations ; `stream()` boucle toutes les minutes.
   - `iot_openaq.py` : `collect_once()` interroge OpenAQ (ou le **simulateur** `_collect_simulated` si pas de clé API) ; `backfill()` génère un historique ; `stream()` boucle.

5. **Traitement — `urbanhub/processing/`**
   - `weather.py` : les fonctions `_parse_temp`, `_parse_wind`, `_parse_visibility`… décodent le format ISD ; conversions d'unités, valeurs manquantes, humidité (Magnus), rattachement à la ville la plus proche, puis écriture Parquet.
   - `citybikes.py` et `openaq.py` : typage, calcul du taux d'occupation / pivot par polluant, écriture Parquet.

6. **Analyse — `urbanhub/analysis/`**
   - Un module par flux + `cross_analysis.py`. Chaque `run()` lit le Parquet, calcule les réponses aux questions métier, écrit un JSON d'indicateurs et des graphiques PNG.
   - Point fort à citer : `cross_analysis.py` croise les flux sur le **cycle diurne** et sort la corrélation ozone/température.

7. **Restitution**
   - `dashboard/app.py` (Streamlit) : lit `curated` + `processed`, applique les filtres de la barre latérale, affiche KPIs, cartes et graphiques.
   - `presentation.py` et `report_doc.py` : génèrent automatiquement le `.pptx` et le document des réponses à partir des indicateurs.

**Phrase de synthèse à retenir :**
> « Le code reflète l'architecture : *ingestion → stockage → traitement → analyse → visualisation*, avec un module dédié par flux et un orchestrateur CLI unique. On peut relancer toute la chaîne avec une seule commande : `python -m urbanhub.cli pipeline`. »

---

### Astuces de présentation
- **Démo** : lance le dashboard **avant** de commencer (`python -m urbanhub.cli dashboard`) pour éviter le temps de chargement.
- **Plan B** : si pas d'internet/démo, utilise les captures d'écran.
- **Répétez les transitions** : c'est ce qui donne une impression d'équipe fluide.
- **Timing** : gardez ~1 min de marge pour les questions.
