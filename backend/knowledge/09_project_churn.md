---
project_id: 09
project_name: Customer Churn Prediction & Reactivation Propensity
github: https://github.com/R-midolli/Customer-Churn-Prediction-Reactivation-Propensity
portfolio_page: https://r-midolli.github.io/portfolio_rafael_midolli/project-churn.html
local_path: C:\Users\rafae\workspace\Customer Churn Prediction & Reactivation Propensity
---

# Customer Churn Prediction & Reactivation Propensity

## Problème métier
Distribuer des coupons de réactivation à grande échelle sans ciblage détruit le ROI.
Ce projet prédit les clients sur le point de churner et recommande un bon de réduction
personnalisé selon leur CLV, maximisant le retour réel de la campagne marketing.

## Dataset
Dunnhumby Complete Journey — données transactionnelles FMCG retail.

## MÉTRIQUES VÉRIFIÉES (source de vérité — README officiel)
- AUC-ROC (Test Set) : 0.84
- Lift @ Decile 1 : 3.2x
- Simulated ROI : +45% vs sélection aléatoire

## Features du modèle (vérifiées dans src/features.py)
### RFM (compute_rfm — fenêtre 90 jours)
- recency_days : jours depuis le dernier achat
- frequency_90d : nombre de paniers uniques
- monetary_90d : dépense totale
- avg_basket : panier moyen (monetary / frequency)

### Behavioral (compute_behavioral)
- category_diversity : nombre de catégories produit distinctes
- promo_sensitivity : % d'achats avec réduction (coupon ou retail discount)
- trend_freq_4w : variation de fréquence entre les 2 dernières périodes de 4 semaines
- inactive_weeks : semaines sans achat dans les 30 derniers jours

### Label (compute_churn_label)
- churned : 1 si aucun achat dans les 30 jours suivant la date de référence

## Modèle ML (vérifié dans src/model.py)
- Modèle : XGBoost (n_estimators=500, lr=0.05, max_depth=5, subsample=0.8)
- Validation : Walk-forward temporal split (TimeSeriesSplit, 4 folds)
- Anti-leakage : assertion train_idx.max() < val_idx.min()
- Threshold optimization : minimisation du coût business réel (FN=50€, FP=5€)
- Explicabilité : SHAP Explainer (global + local)

## Logique de recommandation coupons (vérifiée dans src/roi.py)
### Segmentation CLV
- Percentile 40 → seuil Low/Mid
- Percentile 75 → seuil Mid/High
- 3 segments : Low, Mid, High

### Matrice coupon × segment (response rates vérifiées)
| Segment | Coupon €5 | Coupon €10 | Coupon €20 |
|---------|-----------|------------|------------|
| Low     | 5%        | 9%         | 14%        |
| Mid     | 10%       | 16%        | 24%        |
| High    | 15%       | 23%        | 35%        |

### Formule ROI
`ROI = CLV × 0.5 × response_rate − coupon_cost`
Si ROI > 0 → recommander le coupon optimal. Sinon → pas de coupon.

### Actions CRM générées
- churn_score > threshold + ROI > €50 → "Priority contact"
- churn_score > threshold → "Contact"
- churn_score < threshold → "Do not contact"

## Pipeline complet
1. data.py : ingestion Dunnhumby, nettoyage
2. features.py : RFM + behavioral features + churn label
3. model.py : XGBoost + walk-forward CV + threshold optimization + SHAP
4. roi.py : segmentation CLV → matrice coupon → CRM export
5. Export "Hot Leads" CSV pour système CRM

## Stack vérifiée
Python 3.13, XGBoost, scikit-learn, shap, pandas, marimo (notebooks), uv, HTML/JS (démo interactive)

## Affirmations autorisées (métriques vérifiées)
AUC-ROC 0.84 | Lift D1 3.2x | ROI simulé +45% | 3 segments CLV (Low/Mid/High)
Coupons €5/€10/€20 | Walk-forward validation | SHAP global + local
8 features (4 RFM + 4 behavioral) | Threshold business-cost (FN 50€, FP 5€)

## Affirmations interdites → FALLBACK
- Accuracy ou F1 score (non publiés)
- Taille exacte du dataset en lignes
- Noms de marques ou distributeurs dans les données
- Recall ou precision isolés (seuls AUC-ROC et Lift sont publiés)

## FAQ
Q: AUC-ROC du modèle ?
A: 0.84 sur le test set.

Q: Lift @ Decile 1 de 3.2x — qu'est-ce que ça signifie ?
A: Les 10% de clients les mieux scorés présentent un taux de churn réel 3.2x supérieur à la moyenne. Cibler uniquement ce décile capture une concentration de churners 3x supérieure au hasard.

Q: Quels coupons le modèle recommande-t-il ?
A: CLV High : €10 ou €20 (ROI net positif). CLV Mid : €5 ou €10. CLV Low : pas de coupon (ROI négatif).

Q: Comment le projet évite le data leakage ?
A: Walk-forward temporal validation — chaque split d'entraînement utilise uniquement des données strictement antérieures à la période de test. Assertion codée : train_idx.max() < val_idx.min().

Q: Pourquoi SHAP ?
A: Expliquer pourquoi chaque client est prédit churner — feature importance globale (quelles variables comptent le plus) et locale (pourquoi ce client spécifique). Indispensable pour valider auprès des équipes marketing.

Q: Dataset ?
A: Dunnhumby Complete Journey — données transactionnelles FMCG retail.

Q: Modèle ML ?
A: XGBoost (500 arbres, lr=0.05, max_depth=5) avec walk-forward temporal validation et optimisation du seuil basée sur le coût business réel (perte client FN=50€ >> coupon gaspillé FP=5€).

Q: Quelles features sont utilisées ?
A: 8 features : recency_days, frequency_90d, monetary_90d, avg_basket (RFM) + category_diversity, promo_sensitivity, trend_freq_4w, inactive_weeks (behavioral).

Q: Comment fonctionne la segmentation CLV ?
A: 3 segments basés sur les percentiles de dépense : Low (< p40), Mid (p40-p75), High (> p75). Chaque segment a des taux de réponse coupon différents qui déterminent le ROI net.
