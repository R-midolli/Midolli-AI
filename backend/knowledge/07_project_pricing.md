<!-- RAG NOTE: only answer questions about this project if at least 2 chunks
     from this file are in the top-5 retrieved context. If context is weak,
     say: "Je n'ai pas assez d'informations précises sur ce point —
     consultez le portfolio de Rafael pour les détails complets." -->

# FMCG Pricing Pressure Monitor

## Problème Métier
L'industrie agroalimentaire européenne traverse le cycle inflationniste le plus sévère de la décennie. Les équipes pricing n'ont pas de visibilité sur la transmission des chocs de matières premières vers les prix en rayon ni sur les catégories les plus vulnérables.

## Solution
Monitoring macro-économique automatisé : extraction de données via APIs officielles (BCE, INSEE, Yahoo Finance, Open Food Facts), modélisation en étoile DuckDB, dashboard interactif ECharts. Pipeline CI/CD hebdomadaire via GitHub Actions.

## Stack Technique
- Python 3.12, DuckDB, Apache ECharts, GitHub Actions (CI/CD)
- APIs : BCE, INSEE, Yahoo Finance, Open Food Facts

## Impact
- Corrélation en direct entre marchés à terme et IPC par catégorie alimentaire
- Identification des catégories vulnérables (chocolats, pains, laitiers)
- Pipeline automatisé de mise à jour hebdomadaire des données

## Liens
- GitHub : https://github.com/R-midolli/fmcg_pricing_macro_monitor
