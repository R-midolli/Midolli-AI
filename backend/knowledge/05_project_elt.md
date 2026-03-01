---
project_id: 05
project_name: ELT Retail Analytics — Sales & Profitability Pipeline
github: https://github.com/R-midolli/elt_retail_analytics
portfolio_page: https://r-midolli.github.io/portfolio_rafael_midolli/project-elt-retail.html
local_path: C:\Users\rafae\workspace\ELT_retail_analytics
---

# ELT Retail Analytics — Postgres + dbt + Power BI

## Problème métier
Les données de ventes e-commerce sont dispersées dans des fichiers Excel non structurés.
L'absence de pipeline fiable empêche la production de rapports de performance cohérents
et la prise de décision rapide.

## Dataset
Online Retail II (UCI Machine Learning Repository) — fichier Excel multi-feuilles.
Données transactionnelles e-commerce UK : factures, produits, quantités, prix, clients, pays.

## Pipeline (vérifié dans src/load_raw_online_retail.py + dbt_retail/)
1. Extraction Python : lecture Excel multi-feuilles → concaténation → normalisation des types
2. Chargement PostgreSQL (Docker) : schema `raw.sales` via SQLAlchemy
3. Transformations dbt : staging → marts → reporting (Star Schema)
4. Modèle dimensionnel : table de faits (ventes) + tables de dimensions (clients, produits, temps)
5. Dashboard exécutif Power BI connecté au modèle sémantique

## Concepts démontrés
- Architecture ELT (vs ETL classique) : charger d'abord, transformer ensuite via dbt
- Star Schema : table de faits + tables de dimensions → optimise les requêtes analytiques BI
- Lignage dbt documenté pour la traçabilité des transformations
- Docker pour le runtime PostgreSQL (reproductibilité)

## Stack vérifiée
Python (extraction), PostgreSQL (Docker), dbt (transformations Star Schema), Power BI (dashboard), SQLAlchemy, Git/GitHub

## Affirmations autorisées
- Dataset : Online Retail II (UCI)
- Architecture : ELT avec dbt Star Schema
- Stockage : PostgreSQL via Docker
- Dashboard : Power BI avec mesures DAX personnalisées

## Affirmations interdites → FALLBACK
- Aucune métrique chiffrée de performance (non publiée)
- Nombre exact de lignes du dataset (non mentionné)

## FAQ
Q: Différence ELT vs ETL ?
A: ELT charge d'abord les données brutes, puis les transforme sur place via dbt. L'ETL classique transforme avant de charger.

Q: Pourquoi Star Schema ?
A: Modèle dimensionnel (table de faits + tables de dimensions) — optimise les requêtes analytiques BI. Standard des entrepôts de données.

Q: Stack ELT Retail ?
A: Python (ingestion), dbt (Star Schema), PostgreSQL (Docker), Power BI (dashboard).

Q: Quel dataset ?
A: Online Retail II (UCI Machine Learning Repository) — données transactionnelles e-commerce UK.
