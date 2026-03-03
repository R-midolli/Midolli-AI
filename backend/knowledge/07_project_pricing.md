---
project_id: 07
project_name: FMCG Cost Pressure Monitor
github: https://github.com/R-midolli/fmcg_pricing_macro_monitor
portfolio_page: https://r-midolli.github.io/portfolio_rafael_midolli/project-pricing.html
local_path: C:\Users\rafae\workspace\fmcg_pricing_macro_monitor
---

# FMCG Cost Pressure Monitor

## Problème métier
L'industrie agroalimentaire européenne traverse un cycle inflationniste sévère. Les équipes
pricing et category management n'ont pas de visibilité sur la transmission des chocs de
matières premières vers les prix en rayon ni sur les catégories les plus vulnérables.

## Sources de données (4 APIs vérifiées dans src/extract/)
- ecb_api.py : BCE — inflation zone euro
- insee_api.py : INSEE — inflation France (IPC par catégorie alimentaire)
- commodities_api.py : Yahoo Finance — prix des matières premières (marchés à terme)
- openfoodfacts_api.py : Open Food Facts — données produits alimentaires

## Pipeline (vérifié dans src/)
1. Extraction automatisée Python des 4 APIs externes
2. Transformation et modélisation analytique DuckDB (src/transform/build_marts.py — 11 KB)
3. Construction des marts thématiques pour le dashboard
4. CI/CD via GitHub Actions : reconstruction automatique hebdomadaire
5. Visualisations Apache ECharts interactives (src/dashboard/)
6. Génération automatique de rapport portfolio (generate_portfolio_report.py)

## Stack vérifiée
Python 3.12, DuckDB, Apache ECharts, GitHub Actions (CI/CD), Git/GitHub

## Affirmations autorisées
- 4 sources d'API : BCE, INSEE, Yahoo Finance, Open Food Facts
- Pipeline automatisé CI/CD GitHub Actions
- Corrélation matières premières vs IPC par catégorie alimentaire
- Matières premières (commodities) suivies spécifiquement : Cacao, Sucre, Café, Blé
- DuckDB comme moteur analytique embarqué
- Dashboard ECharts interactif

## Affirmations interdites → FALLBACK
- Aucune métrique chiffrée de performance (non publiée)
- Ne pas inventer de corrélations ou % spécifiques

## FAQ
Q: Quelles sources utilise le FMCG Monitor ?
A: ECB (inflation zone euro), INSEE (inflation France par catégorie), Yahoo Finance (matières premières), Open Food Facts (données produits alimentaires).

Q: Pourquoi DuckDB dans ce projet ?
A: Base analytique embarquée sans serveur — idéale pour agréger rapidement 4 sources hétérogènes en Python, sans infrastructure de base de données.

Q: Comment fonctionne l'automatisation ?
A: GitHub Actions reconstruit le pipeline automatiquement et régénère les visualisations ECharts sur un rythme hebdomadaire.

Q: Quelles catégories sont analysées ?
A: Les catégories alimentaires les plus vulnérables à la pression des coûts : chocolats, pains, produits laitiers, etc. L'analyse croise les marchés à terme avec l'IPC par catégorie.
