<!-- RAG NOTE: only answer questions about this project if at least 2 chunks
     from this file are in the top-5 retrieved context. If context is weak,
     say: "Je n'ai pas assez d'informations précises sur ce point —
     consultez le portfolio de Rafael pour les détails complets." -->

# Midolli-AI — Chatbot RAG Portfolio

## Problème Métier
Comment permettre à un recruteur de poser des questions en temps réel sur le parcours, les compétences et les projets d'un candidat directement depuis son portfolio ? Les portfolios statiques ne permettent pas d'interaction.

## Solution
Chatbot RAG intelligent intégré au portfolio de Rafael sous forme de widget. Le backend FastAPI effectue une recherche sémantique dans une base de connaissances ChromaDB, puis génère une réponse contextualisée via Gemini API avec fallback NVIDIA. Le widget supporte le français et l'anglais, les thèmes dark/light, et fonctionne sur mobile.

## Stack Technique
- FastAPI, ChromaDB, Gemini API (embedding + génération)
- 3-API fallback : Gemini KEY_1 → KEY_2 → NVIDIA LLaMA-3.1-70B
- Vanilla JS (IIFE), CSS isolé (.mai-), pymupdf pour extraction CV PDF
- Déploiement : Render.com (backend), GitHub Pages (widget)

## Impact
- Zéro downtime grâce au triple fallback API
- Widget FR/EN avec synchronisation thème/langue en temps réel
- 12 fichiers de connaissance couvrant CV, 6 projets, FAQ, positionnement

## Liens
- GitHub : https://github.com/R-midolli/Midolli-AI
- Portfolio : https://r-midolli.github.io/portfolio_rafael_midolli
