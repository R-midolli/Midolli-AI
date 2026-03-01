---
project_id: 08
project_name: Midolli-AI — RAG Chatbot for Data Portfolio
github: https://github.com/R-midolli/Midolli-AI
portfolio_page: https://r-midolli.github.io/portfolio_rafael_midolli/project-midolli-ai.html
---

# Midolli-AI — Chatbot RAG Portfolio

## Ce qu'est Midolli-AI
Chatbot RAG intelligent intégré au portfolio de Rafael Midolli. Répond aux questions de
recruteurs et visiteurs sur son parcours, ses compétences et ses projets — en français ou
anglais. Architecture : FastAPI + ChromaDB + Tri-Tier LLM Router.

## Architecture vérifiée
- Backend : FastAPI (Python 3.12), ChromaDB (vectorstore local)
- Knowledge Base : 12+ fichiers (.md curated + CV PDF + profils personnels + READMEs projets)
- Frontend : Widget Vanilla JS isolé (préfixe .mai-), CSS custom
- Deploy : Render.com (API) + GitHub Pages (widget)

## LLM Router Tri-Tier (vérifié dans chain.py)
- Tier 1 — Saudações (~1s) : gemini-flash-lite-latest, sans RAG, détection regex des salutations
- Tier 2/3 — Factuel & Complexe : Kimi K2.5 (moonshotai/kimi-k2.5 via NVIDIA) en priorité,
  puis GLM-5 (z-ai/glm5 via NVIDIA) en fallback, puis Gemini 3 Flash en dernier recours.
  3 tentatives + exponential backoff par modèle.

## Fallback Quadruple API
Kimi K2.5 (NVIDIA Key #1) → GLM-5 (NVIDIA Key #2) → Gemini 3 Flash (Key #1) → Gemini 2.5 Flash (Key #2)

## UX
- Timer : "⚡ répondu en Xs" sous chaque bulle de réponse
- Détection automatique de langue (FR/EN, PT si détecté)
- Widget flottant intégré au portfolio, thème dark/light synchronisé
- Mobile responsive (375px+)

## Super-RAG : Ingestion profonde (vérifié dans ingest.py)
Le pipeline d'ingestion lit directement :
- 12+ fichiers .md curated (backend/knowledge/)
- CV PDF 2026 (extraction via pymupdf)
- Profil personnel complet
- READMEs originaux des 6 projets du workspace

## Qualité & Tests
- LLM-as-a-Judge : scripts/evaluate_rag.py
- Vérité terrain : tests/qa_dataset.csv (score 1 à 5 par question)
- Tests unitaires : pytest tests/

## FAQ
Q: Comment fonctionne le LLM Router ?
A: Tier1 salutations (Gemini Flash Lite ~1s, sans RAG). Tier2/3 questions factuelles et complexes : Kimi K2.5 (NVIDIA) en priorité → GLM-5 (NVIDIA) en fallback → Gemini 3 Flash en dernier recours. Chaque modèle a 3 tentatives avec exponential backoff.

Q: Comment Midolli-AI garantit zéro downtime ?
A: Quadruple fallback — Kimi K2.5 (NVIDIA Key #1) → GLM-5 (NVIDIA Key #2) → Gemini 3 Flash (Key #1) → Gemini 2.5 Flash (Key #2).

Q: Qu'est-ce que le LLM-as-a-Judge ?
A: evaluate_rag.py compare les réponses du chatbot avec les vérités terrain du qa_dataset.csv et note de 1 à 5 par question.

Q: Stack Midolli-AI ?
A: FastAPI, ChromaDB, Gemini API (embedding + génération), NVIDIA API (LLaMA 3.1 70B), Vanilla JS (widget), CSS isolé, pymupdf, Render.com.
