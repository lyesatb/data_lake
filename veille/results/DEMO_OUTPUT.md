# QuestDB — Résultats réels de la démo

Requêtes exécutées sur QuestDB 8.2.1 (données urbaines simulées, ingérées via ILP). Générées automatiquement par `demo/run_queries.py`.

## 1. Volume & fenêtre temporelle

_Nombre total de mesures et bornes de dates._

```sql
SELECT count() AS mesures, min(ts) AS debut, max(ts) AS fin FROM air_quality;
```

| mesures | debut | fin |
| --- | --- | --- |
| 46080 | 2026-06-29T13:05:35.446351Z | 2026-07-29T12:35:35.446351Z |

## 2. SAMPLE BY — moyenne journalière (PM2.5, Paris)

_Bucketisation temporelle native de QuestDB (5 premiers jours)._

```sql
SELECT ts, round(avg(value),1) AS pm25_moy FROM air_quality WHERE city='Paris' AND pollutant='pm25' SAMPLE BY 1d LIMIT 5;
```

| ts | pm25_moy |
| --- | --- |
| 2026-06-29T00:00:00.000000Z | 35.9 |
| 2026-06-30T00:00:00.000000Z | 34.4 |
| 2026-07-01T00:00:00.000000Z | 35.3 |
| 2026-07-02T00:00:00.000000Z | 35.6 |
| 2026-07-03T00:00:00.000000Z | 34.3 |

## 3. LATEST ON — dernier état de chaque capteur (Lyon)

_Récupère la dernière valeur par série : idéal pour un dashboard temps réel._

```sql
SELECT city, pollutant, ts, value FROM air_quality WHERE city='Lyon' LATEST ON ts PARTITION BY city, pollutant;
```

| city | pollutant | ts | value |
| --- | --- | --- | --- |
| Lyon | pm25 | 2026-07-29T12:35:35.446351Z | 34.75 |
| Lyon | pm10 | 2026-07-29T12:35:35.446351Z | 53.45 |
| Lyon | no2 | 2026-07-29T12:35:35.446351Z | 52.97 |
| Lyon | o3 | 2026-07-29T12:35:35.446351Z | 129.71 |

## 4. Profil diurne du NO2 (moyenne par heure)

_Met en évidence les pics de trafic (matin/soir)._

```sql
SELECT hour(ts) AS heure, round(avg(value),1) AS no2_moy FROM air_quality WHERE pollutant='no2' GROUP BY hour(ts) ORDER BY heure;
```

| heure | no2_moy |
| --- | --- |
| 0 | 57.5 |
| 1 | 58.0 |
| 2 | 57.6 |
| 3 | 57.2 |
| 4 | 57.1 |
| 5 | 58.1 |
| 6 | 57.4 |
| 7 | 90.8 |
| 8 | 91.3 |
| 9 | 90.6 |
| 10 | 56.6 |
| 11 | 57.1 |
| 12 | 57.3 |
| 13 | 57.3 |
| 14 | 57.1 |
| 15 | 57.7 |
| 16 | 57.7 |
| 17 | 92.1 |
| 18 | 92.3 |
| 19 | 92.0 |
| 20 | 57.9 |
| 21 | 57.5 |
| 22 | 57.4 |
| 23 | 57.9 |

## 5. ASOF JOIN — ozone associé à la température (Nice)

_Jointure temporelle sur l'horodatage le plus proche : spécialité de QuestDB._

```sql
SELECT a.ts, round(a.value,1) AS o3, round(w.temperature,1) AS temperature FROM (SELECT ts, city, value FROM air_quality WHERE pollutant='o3' AND city='Nice') a ASOF JOIN (SELECT ts, city, temperature FROM weather WHERE city='Nice') w LIMIT 10;
```

| ts | o3 | temperature |
| --- | --- | --- |
| 2026-06-29T13:05:35.446351Z | 100.3 | 23.9 |
| 2026-06-29T13:35:35.446351Z | 123.8 | 23.8 |
| 2026-06-29T14:05:35.446351Z | 129.1 | 23.2 |
| 2026-06-29T14:35:35.446351Z | 155.3 | 24.1 |
| 2026-06-29T15:05:35.446351Z | 153.6 | 26.2 |
| 2026-06-29T15:35:35.446351Z | 165.2 | 24.8 |
| 2026-06-29T16:05:35.446351Z | 126.0 | 26.4 |
| 2026-06-29T16:35:35.446351Z | 160.0 | 26.4 |
| 2026-06-29T17:05:35.446351Z | 134.3 | 27.0 |
| 2026-06-29T17:35:35.446351Z | 137.9 | 26.8 |

## 6. Classement des villes par ozone moyen

_Agrégation + tri._

```sql
SELECT city, round(avg(value),1) AS o3_moy FROM air_quality WHERE pollutant='o3' GROUP BY city ORDER BY o3_moy DESC;
```

| city | o3_moy |
| --- | --- |
| Paris | 122.7 |
| Lille | 118.8 |
| Lyon | 113.8 |
| Marseille | 109.7 |
| Strasbourg | 105.0 |
| Toulouse | 96.5 |
| Nice | 92.3 |
| Nantes | 88.0 |

## 7. Dépassements de seuil OMS (PM2.5 > 25 µg/m³)

_Comptage des dépassements par ville._

```sql
SELECT city, count() AS nb_depassements FROM air_quality WHERE pollutant='pm25' AND value>25 GROUP BY city ORDER BY nb_depassements DESC;
```

| city | nb_depassements |
| --- | --- |
| Paris | 1440 |
| Lyon | 1440 |
| Lille | 1440 |
| Marseille | 1439 |
| Strasbourg | 1309 |
| Toulouse | 1055 |
| Nice | 885 |
| Nantes | 728 |

## 8. SAMPLE BY 1h FILL(LINEAR) — série continue (Marseille, O3)

_Interpolation linéaire des trous de la série temporelle._

```sql
SELECT ts, round(avg(value),1) AS o3 FROM air_quality WHERE city='Marseille' AND pollutant='o3' SAMPLE BY 1h FILL(LINEAR) LIMIT 6;
```

| ts | o3 |
| --- | --- |
| 2026-06-29T13:00:00.000000Z | 147.5 |
| 2026-06-29T14:00:00.000000Z | 166.8 |
| 2026-06-29T15:00:00.000000Z | 176.1 |
| 2026-06-29T16:00:00.000000Z | 143.1 |
| 2026-06-29T17:00:00.000000Z | 142.7 |
| 2026-06-29T18:00:00.000000Z | 138.4 |
