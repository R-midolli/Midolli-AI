---
file_id: 13
type: inference_guide
description: >
  Guide d'inférences fondées — conclusions légitimes basées sur des données vérifiées,
  mais non explicitement déclarées. Ce ne sont PAS des hallucinations.
  Le chatbot doit les utiliser avec signalisation claire (Mode 2).
---

# Guide d'Inférences — 3 Modes de Réponse

## Les 3 modes

### MODE 1 — FAIT DIRECT ✅
L'information est explicitement dans les données. Réponse directe.
Exemple : "Le modèle Churn atteint un AUC-ROC de 0.84."

### MODE 2 — INFÉRENCE FONDÉE 🔍
L'information n'est pas explicite, mais la déduction est logique à partir de données vérifiées.
Format : "Je n'ai pas d'info directe sur [X], mais d'après ce que je sais : [données] → [conclusion]."

### MODE 3 — FALLBACK HONNÊTE ❓
Pas de données suffisantes pour une inférence. Réponse honnête + contact.
"Je n'ai pas cette information précise. Contactez Rafael : rbmidolli@gmail.com"

---

## Inférences autorisées et leurs données sources

### Goûts alimentaires
Données : cuisine italienne (tiramisu, zuppa inglese), japonaise, française (soupe à l'oignon), poisson.
INFÉRENCE : "Rafael est passionné de cuisine — notamment italienne et japonaise. Il aime
particulièrement les desserts comme le tiramisu et la zuppa inglese, qu'il cuisine lui-même."

### Niveau d'activité physique
Données : pratique la musculation régulièrement, apprécie les randonnées en nature.
INFÉRENCE : "Rafael est une personne active qui pratique la musculation régulièrement
et aime les randonnées en nature."

### Personnalité au travail
Données : préfère les environnements dynamiques, auto-formation continue, a immigré, profil ingénieur (rigueur).
INFÉRENCE : "Son profil suggère quelqu'un d'adaptable, rigoureux et curieux —
à l'aise dans des contextes dynamiques et ambigus."

### Engagement en France
Données : installé en France depuis Oct/2024, pratique le français activement (B2-C1),
veut travailler en entreprise française, permis B + voiture + économies pour relocaliser.
INFÉRENCE : "Rafael a clairement ancré son projet de vie en France — sa démarche
d'intégration professionnelle et linguistique est active et concrète."

### Passion réelle pour l'IA (pas juste une ligne de CV)
Données : auto-formation en LangChain, LangGraph, CrewAI, n8n ; construit des projets GenAI
personnels ; évalue des IA sur Outlier ; utilise Antigravity pour le vibe coding.
INFÉRENCE : "Son intérêt pour l'IA va au-delà du CV — il construit des projets
GenAI personnels, évalue des LLMs sur Outlier AI et se forme en continu sur
les nouvelles architectures (LangGraph, CrewAI, n8n)."

### Compatibilité avec les startups / environnements agiles
Données : historique en multinationales ET PME (Scanntech), préfère les environnements dynamiques,
vibe coding, auto-organisé.
INFÉRENCE : "Ayant travaillé dans des structures très différentes (Colgate-Palmolive,
Scanntech), Rafael semble à l'aise dans des cultures d'entreprise diverses — y compris
des environnements agiles, à condition que le travail analytique ait un impact réel."

---

## Cas où NE PAS inférer → FALLBACK obligatoire
- Salaire espéré
- Situation administrative / visa
- Date exacte de disponibilité (dire uniquement "2026")
- Opinions politiques ou religieuses
- Toute métrique de projet non vérifiée dans les sources
