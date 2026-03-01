---
project_id: 06
project_name: Supply Chain Analytics — Delivery Performance
github: https://github.com/R-midolli/supply_chain_analytics
portfolio_page: https://r-midolli.github.io/portfolio_rafael_midolli/project-supply-chain.html
local_path: C:\Users\rafae\workspace\supply_chain_analytics
---

# Supply Chain Analytics — ETL Python + Power BI

## Problème métier
Les retards de livraison impactent la performance opérationnelle et la satisfaction client.
Les équipes logistiques n'ont pas de visibilité sur le taux de service réel ni sur les
causes racines des écarts de livraison.

## Dataset
DataCo Supply Chain Dataset — données logistiques mondiales (commandes, livraisons, clients, produits).

## Pipeline (vérifié dans src/etl.py — 186 lignes)
1. Chargement CSV (encoding latin-1) + sélection de 28 colonnes clés
2. Parsing des dates + ajout de champs calendaires (Year, Month)
3. Normalisation des types numériques et texte (strip, coerce)
4. Feature engineering KPI logistiques :
   - is_late : indicateur binaire de retard
   - shipping_gap : écart jours réels - jours planifiés
   - late_days : nombre de jours de retard (clipped ≥ 0)
   - is_ontime : indicateur de ponctualité
   - Delivery Bucket : Late / On-time / Early / Canceled
   - is_profitable : indicateur de commande profitable
5. Rapport qualité automatique (missing %, statistiques des KPI)
6. Export → data/processed/supply_chain_cleaned.csv
7. Dashboard Power BI : OTIF, concentration des retards, impact business

## Stack vérifiée
Python (ETL + feature engineering), Power BI (dashboard), Git/GitHub

## Affirmations autorisées
- Dataset : DataCo Supply Chain Dataset
- KPI : shipping_gap, is_late, late_days, is_ontime, Delivery Bucket
- Analyse : taux de ponctualité (On-Time %), root cause par mode de livraison
- Power BI as Code (versionné sur GitHub)

## Affirmations interdites → FALLBACK
- Aucun % OTIF chiffré n'est publié
- Ne pas inventer de valeurs de taux de service

## FAQ
Q: Qu'est-ce que l'OTIF ?
A: On Time In Full — pourcentage de commandes livrées à l'heure ET en quantité complète. KPI de référence FMCG. Un OTIF < 95% indique des problèmes logistiques impactant la relation client/distributeur.

Q: Stack Supply Chain ?
A: Python (ETL + feature engineering) + Power BI (OTIF, late delivery, root cause analysis).

Q: Quel dataset ?
A: DataCo Supply Chain Dataset — données logistiques mondiales.

Q: Quels KPI sont calculés ?
A: shipping_gap (écart réel − planifié), is_late (retard binaire), late_days (jours de retard), is_ontime, Delivery Bucket (Late/On-time/Early/Canceled).
