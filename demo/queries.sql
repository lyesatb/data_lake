-- =====================================================================
-- Demo QuestDB — Requetes time-series sur des donnees urbaines
-- (a executer dans la console web http://localhost:9000 ou via psql)
-- =====================================================================

-- 1) Volume et fenetre temporelle des donnees
SELECT count() AS mesures, min(ts) AS debut, max(ts) AS fin FROM air_quality;

-- 2) SAMPLE BY : moyenne journaliere des PM2.5 a Paris
--    (bucketisation temporelle native, sans GROUP BY manuel)
SELECT ts, round(avg(value), 1) AS pm25_moy
FROM air_quality
WHERE city = 'Paris' AND pollutant = 'pm25'
SAMPLE BY 1d;

-- 3) LATEST ON : derniere valeur connue de chaque capteur d'une ville
--    (parfait pour un tableau de bord "etat courant")
SELECT city, pollutant, ts, value
FROM air_quality
WHERE city = 'Lyon'
LATEST ON ts PARTITION BY city, pollutant;

-- 4) Profil diurne du NO2 (moyenne par heure de la journee)
SELECT hour(ts) AS heure, round(avg(value), 1) AS no2_moy
FROM air_quality
WHERE pollutant = 'no2'
GROUP BY hour(ts) ORDER BY heure;

-- 5) ASOF JOIN : associer chaque mesure d'ozone a la temperature la plus
--    proche dans le temps (jointure temporelle, specialite de QuestDB)
SELECT a.ts, round(a.value, 1) AS o3, round(w.temperature, 1) AS temperature
FROM (SELECT ts, city, value FROM air_quality WHERE pollutant = 'o3' AND city = 'Nice') a
ASOF JOIN (SELECT ts, city, temperature FROM weather WHERE city = 'Nice') w
LIMIT 10;

-- 6) Classement des villes les plus polluees a l'ozone
SELECT city, round(avg(value), 1) AS o3_moy
FROM air_quality
WHERE pollutant = 'o3'
GROUP BY city ORDER BY o3_moy DESC;

-- 7) Depassements de seuil OMS (PM2.5 > 25 ug/m3) par ville
SELECT city, count() AS nb_depassements
FROM air_quality
WHERE pollutant = 'pm25' AND value > 25
GROUP BY city ORDER BY nb_depassements DESC;

-- 8) SAMPLE BY avec FILL : serie horaire continue (interpolation lineaire)
SELECT ts, round(avg(value), 1) AS o3
FROM air_quality
WHERE city = 'Marseille' AND pollutant = 'o3'
SAMPLE BY 1h FILL(LINEAR)
LIMIT 6;
