---
project_id: 04
project_name: Retail BA Diagnostic — Store Performance Segmentation
github: https://github.com/R-midolli/retail-ba-diagnostic
portfolio_page: https://r-midolli.github.io/portfolio_rafael_midolli/project-retail.html
local_path: C:\Users\rafae\workspace\retail-ba-diagnostic
---

# Retail BA Diagnostic — Store Performance Segmentation

## Problème métier
Les équipes commerciales d'un réseau de distribution manquent d'une vision synthétique
des performances magasin. Ce projet construit une couche KPI magasin, segmente le réseau
et identifie les écarts performance vs potentiel — livrable typique d'un Business Analyst retail.

## Dataset
Kaggle Store Sales — Time Series Forecasting (Corporación Favorita, Équateur).
- train.csv : ventes journalières par magasin et famille de produit
- transactions.csv : transactions journalières par magasin (proxy d'activité)
- stores.csv : référentiel magasins (type, cluster, localisation)

## Pipeline (vérifié dans src/etl_pipeline.py)
1. Ingestion des 3 CSV sources (train, transactions, stores)
2. Jointure et agrégation SQL via DuckDB en mémoire
3. Calcul des KPI magasin : active_days, avg_transactions, avg_daily_sales, basket_units
4. Export → data/processed/store_kpis.csv (54 magasins)
5. Dashboard interactif Plotly HTML → reports/dashboard_retail.html

## KPI produits (colonnes vérifiées de store_kpis.csv)
- store_nbr : identifiant magasin
- city : ville du magasin
- type : catégorie du magasin (A, B, C, D, E)
- active_days : nombre de jours avec transactions
- avg_transactions : nombre moyen de transactions par jour
- avg_daily_sales : chiffre d'affaires quotidien moyen
- basket_units : panier moyen (ventes / transactions)

## Stack vérifiée
Python, SQL, Pandas, DuckDB, Plotly, Jupyter Notebook, uv, Git/GitHub

## Affirmations autorisées
- Dataset : Kaggle Store Sales / Corporación Favorita (Équateur)
- Stack : Python, Pandas, DuckDB, Plotly, SQL
- Output : store_kpis.csv (54 magasins) + dashboard HTML Plotly
- Pas de modèle ML — analytique BA pur (ETL + KPI + segmentation descriptive)

## Affirmations interdites → FALLBACK
- Aucune métrique chiffrée de performance (pas de % d'amélioration publié)
- Ne pas inventer de valeurs de segments ou clusters

## FAQ
Q: Quel dataset utilise le Retail BA ?
A: Kaggle Store Sales — Corporación Favorita (Équateur). train.csv (ventes), transactions.csv (activité), stores.csv (référentiel).

Q: C'est du ML ?
A: Non — analytique BA pur : ETL, KPI, segmentation descriptive, dashboard Plotly.

Q: Stack ?
A: Python, Pandas, DuckDB, Plotly, SQL, Jupyter Notebook, uv.

Q: Quel est le livrable principal ?
A: Table store_kpis.csv (54 magasins, 7 colonnes KPI) + dashboard HTML Plotly interactif.

Q: Pourquoi DuckDB pour ce projet ?
A: Requêtes SQL analytiques en mémoire sur des CSV — rapide et sans serveur.
