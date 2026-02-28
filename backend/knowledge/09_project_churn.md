<!-- RAG NOTE: only answer questions about this project if at least 2 chunks
     from this file are in the top-5 retrieved context. If context is weak,
     say: "Je n'ai pas assez d'informations précises sur ce point —
     consultez le portfolio de Rafael pour les détails complets." -->

# Customer Churn Prediction & Reactivation Propensity

## Problème Métier
Comment identifier avec précision les clients FMCG Retail sur le point de churner et allouer efficacement le budget de réactivation marketing ? La distribution aveugle de coupons érode le ROI des campagnes.

## Solution
Pipeline Machine Learning avec XGBoost sur le dataset Dunnhumby Complete Journey. Optimisation du seuil par simulation du coût business réel. Segmentation par CLV (Customer Lifetime Value) pour recommander des coupons personnalisés (5€, 10€, 20€).

## Stack Technique
- Python, pandas, scikit-learn, XGBoost, SHAP
- HTML/JS (simulateur interactif sur le portfolio)

## Impact
- AUC-ROC de 0.84 sur le jeu de test
- Lift de 3.2x au premier décile
- ROI simulé de +45% vs sélection aléatoire
- IA explicable : SHAP Values pour chaque décision

## Liens
- GitHub : https://github.com/R-midolli/Customer-Churn-Prediction-Reactivation-Propensity
- Portfolio : https://r-midolli.github.io/portfolio_rafael_midolli/project-churn.html
