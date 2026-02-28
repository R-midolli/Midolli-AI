<!-- RAG NOTE: only answer questions about this project if at least 2 chunks
     from this file are in the top-5 retrieved context. If context is weak,
     say: "Je n'ai pas assez d'informations précises sur ce point —
     consultez le portfolio de Rafael pour les détails complets." -->

# ELT Retail Analytics — Postgres + dbt + Power BI

## Problème Métier
Les données de ventes e-commerce sont dispersées dans des fichiers Excel non structurés. L'absence de pipeline fiable empêche la production de rapports de performance cohérents et la prise de décision rapide.

## Solution
Pipeline ELT end-to-end : extraction Python (Excel → Postgres), transformation avec dbt en Star Schema (staging → marts → reporting), et dashboard exécutif Power BI connecté au modèle sémantique.

## Stack Technique
- Python, PostgreSQL (Docker), dbt, Power BI Desktop, Git/GitHub

## Impact
- Star Schema complet avec tables de faits et dimensions (dbt marts)
- Lignage dbt documenté pour la traçabilité des transformations
- Dashboard Power BI exécutif avec mesures DAX personnalisées

## Liens
- GitHub : https://github.com/R-midolli/elt_retail_analytics
