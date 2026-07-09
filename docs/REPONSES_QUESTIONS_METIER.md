# UrbanHub — Réponses aux questions métier

_Jumeau numérique urbain · Batch météo · Streaming vélos · IoT pollution._

Réponses issues des données réellement collectées et analysées (indicateurs du data lake `data/curated`).

## Partie 1 — Flux Batch : météo urbaine (NOAA)

Périmètre : 24 216 observations, 8 stations.

### Peut-on identifier des périodes météo anormales ?

Méthode : Jours dont la temperature moyenne s'ecarte de >= 2.5 ecarts-types de la normale mensuelle.  
Réponse : **oui**, 1 jour(s) anormal(aux).

| Date | Température (°C) | z-score |
| --- | --- | --- |
| 2025-07-01 | 25.9 | 3.46 |

### Corrélation météo ↔ visibilité ?

| Variable | Corrélation |
| --- | --- |
| temperature_c | 0.358 |
| humidity_pct | -0.615 |
| wind_speed_ms | 0.227 |
| precip_mm | -0.167 |
| pressure_hpa | -0.303 |

_La visibilité baisse quand l'humidité augmente (brouillard)._

### Évolution saisonnière de la température ?

| Saison | Température moyenne (°C) |
| --- | --- |
| Ete | 19.06 |
| Hiver | 4.19 |
| Printemps | 11.6 |

### Jours aux conditions extrêmes ?

| Événement | Date | Valeur |
| --- | --- | --- |
| jour plus chaud | 2025-07-01 | 37.0 |
| jour plus froid | 2025-01-10 | -5.9 |
| jour plus pluvieux | 2025-01-05 | 180.1 |
| jour plus vente | 2025-01-08 | 19.6 |

## Partie 2 — Flux Streaming : mobilité (vélos CityBikes)

Périmètre : 5 639 stations, 65 réseaux.

### Stations les plus utilisées ?

| Ville | Station | Occupation | Capacité |
| --- | --- | --- | --- |
| Ligne TER Royan - Angoulême | Soyaux - Place du Lac | 1.0 | 6.0 |
| Ligne TER Royan - Angoulême | Torsac - Place Blanche | 1.0 | 6.0 |
| Ligne TER Royan - Angoulême | Royan Port de Royan | 1.0 | 8.0 |
| Ligne TER Royan - Angoulême | Saint-Palais-sur-Mer | 1.0 | 2.0 |
| Ligne TER Royan - Angoulême | Cognac Le Castel | 1.0 | 2.0 |
| Metz | Saint Livier | 1.0 | 1.0 |

### Zones à offre insuffisante ?

| Ville | Station | % vide | Vélos dispo |
| --- | --- | --- | --- |
| Toulouse | CITÉ DE L'HERS - ROTONDE | 1.0 | 0.0 |
| Toulouse | COLONNE - SALONIQUE | 1.0 | 0.0 |
| Toulouse | TERRASSE - LEDORMEUR | 1.0 | 0.0 |
| Toulouse | PARC DE LA VIOLETTE | 1.0 | 0.0 |
| Rennes | Pont de Châteaudun | 1.0 | 0.0 |
| Lyon | PLACE MARENGO | 1.0 | 0.0 |

### Pics d'utilisation journaliers ?

Profil horaire de disponibilité (voir `mobility_profil_horaire.png`).

### Déséquilibres géographiques ?

| Ville | Stations | Occupation | % vides | % pleines |
| --- | --- | --- | --- | --- |
| Paris | 1516 | 0.397 | 0.056 | 0.037 |
| Lyon | 461 | 0.375 | 0.171 | 0.069 |
| Toulouse | 443 | 0.356 | 0.163 | 0.072 |
| Lille | 300 | 0.376 | 0.187 | 0.063 |
| Marseille | 228 | 0.343 | 0.118 | 0.105 |
| Bordeaux | 223 | 0.344 | 0.126 | 0.013 |

### Stations critiques à rééquilibrer ?

| Ville | Station | Type | Criticité |
| --- | --- | --- | --- |
| Saint-Pierre | Mairie du Ouaki | penurie (vide) | 1.0 |
| Saint-Pierre | Cité Palissade | penurie (vide) | 1.0 |
| Saint-Pierre | Mairie de la Ravine | penurie (vide) | 1.0 |
| Saint-Pierre | Roches Maigres | penurie (vide) | 1.0 |
| Saint-Pierre | Kerveguen | penurie (vide) | 1.0 |
| Saint-Pierre | Lycée Jean Joly | penurie (vide) | 1.0 |

## Partie 3 — Flux IoT : pollution (OpenAQ)

Périmètre : 5 328 mesures, 12 villes.

### Villes les plus polluées par polluant ?

| Polluant | Ville | Valeur (µg/m³) |
| --- | --- | --- |
| pm25 | Lyon | 34.1 |
| pm10 | Paris | 52.6 |
| no2 | Paris | 76.9 |
| o3 | Marseille | 112.6 |
| so2 | Lille | 14.5 |
| co | Lyon | 1.8 |

### Dépassements des seuils OMS ?

Total : **2325** dépassements.

| Ville | Polluant | Nb dépassements |
| --- | --- | --- |
| Bordeaux | no2 | 74 |
| Bordeaux | pm25 | 74 |
| Grenoble | pm25 | 74 |
| Grenoble | no2 | 74 |
| Lyon | no2 | 74 |
| Lyon | pm25 | 74 |

### Indice de qualité de l'air par ville ?

| Ville | Indice (ratio / seuil) |
| --- | --- |
| Lyon | 1.399 |
| Paris | 1.395 |
| Marseille | 1.393 |
| Lille | 1.387 |
| Strasbourg | 1.007 |
| Grenoble | 1.005 |
| Bordeaux | 1.003 |
| Montpellier | 1.001 |

## Partie 4 — Analyse croisée

_Croisement sur le cycle diurne (heure de la journee, 0-23)._

### Relation météo ↔ pollution ?

| Polluant | humidity_pct | temperature_c | wind_speed_ms |
| --- | --- | --- | --- |
| pm25 | 0.065 | -0.057 | 0.002 |
| pm10 | -0.346 | 0.355 | 0.322 |
| no2 | -0.152 | 0.156 | 0.114 |
| o3 | -0.945 | 0.929 | 0.874 |
| so2 | 0.18 | -0.178 | -0.195 |
| co | 0.021 | -0.0 | 0.056 |

**Résultat marquant : O₃ ↔ température = 0.929** (formation photochimique de l'ozone).

### La météo influence-t-elle l'usage des vélos ?

Moins de 5 heures distinctes : recouvrement insuffisant.

### Conditions favorables à la mobilité douce ?

Définition : {'temperature_c': '[12, 25]', 'precip_mm': '= 0', 'wind_speed_ms': '< 6'}. Part d'heures favorables : **39.27 %**.

| Saison | Heures favorables (%) |
| --- | --- |
| Ete | 75.33 |
| Hiver | 1.95 |
| Printemps | 37.88 |

### Interactions météo × pollution × mobilité ?

Heures communes analysées : 1 (voir `cross_cycle_diurne.png`).
