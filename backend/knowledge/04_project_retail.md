<!-- RAG NOTE: only answer questions about this project if at least 2 chunks
     from this file are in the top-5 retrieved context. If context is weak,
     say: "Je n'ai pas assez d'informations précises sur ce point —
     consultez le portfolio de Rafael pour les détails complets." -->

# Retail BA Diagnostic — Store Performance Segmentation

## Problème Métier
Comment identifier les magasins sous-performants dans un réseau de distribution et quantifier les écarts de performance entre points de vente ? Les directions commerciales manquent d'outils pour segmenter objectivement leur parc magasins.

## Solution
Construction d'une couche KPI magasin à partir des données de ventes Corporación Favorita (Kaggle). Segmentation du réseau par profils de performance, avec un dashboard HTML interactif pour visualiser les écarts performance vs potentiel.

## Stack Technique
- Python, SQL, Pandas, Plotly, Jupyter, DuckDB, Git/GitHub

## Impact
- Création d'un dataset KPI magasin exploitable (`store_kpis.csv`)
- Dashboard HTML interactif pour le pilotage réseau
- Segmentation descriptive des profils magasins avec écarts quantifiés

## Liens
- GitHub : https://github.com/R-midolli/retail-ba-diagnostic
