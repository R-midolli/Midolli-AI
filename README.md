# Midolli-AI — RAG Chatbot for Data Portfolio

🇫🇷 [Version française ci-dessous](#-midolli-ai--chatbot-rag-pour-portfolio-data)

## 🇬🇧 What is Midolli-AI?

An intelligent RAG chatbot embedded in [Rafael Midolli's data portfolio](https://r-midolli.github.io/portfolio_rafael_midolli/). It answers questions about his career, CV, projects and skills in **French or English**, powered by 3 APIs with automatic fallback to guarantee zero downtime.

### Architecture

```
User sends message in JS widget
      ↓ POST /chat
FastAPI backend (Render.com)
      ↓ semantic search (top-5 chunks)
ChromaDB — knowledge base (MD files + CV PDF)
      ↓ relevant context + question
Gemini 1.5 Flash [KEY_1] → response
      ↓ fallback on quota / error
Gemini 1.5 Flash [KEY_2] → response
      ↓ final fallback
NVIDIA LLaMA-3.1-70B
      ↓
JSON response → widget renders in FR or EN
```

### Quick Setup

```bash
# 1. Clone and install
git clone https://github.com/R-midolli/Midolli-AI.git
cd Midolli-AI
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # Linux/Mac

# 2. Configure API keys
cp .env.example .env
# Edit .env with your GEMINI_API_KEY_1, GEMINI_API_KEY_2, NVIDIA_API_KEY

# 3. Ingest knowledge base
.venv/Scripts/python backend/ingest.py

# 4. Start server
.venv/Scripts/uvicorn backend.main:app --reload --port 8000

# 5. Test
curl http://localhost:8000/health
# Open frontend/test.html in browser
```

### Portfolio Integration

Add before `</body>` in your portfolio's `index.html`:

```html
<link rel="stylesheet" href="assets/midolli-widget.css">
<script src="assets/midolli-widget.js"></script>
<script>
  document.addEventListener('DOMContentLoaded', function() {
    MidolliAI.init({
      apiUrl: 'https://YOUR-APP.onrender.com',
      lang: window.currentLang || 'fr',
      theme: document.body.dataset.theme || 'dark'
    });
  });
</script>
```

### Deploy on Render.com

1. **New → Web Service** → connect Midolli-AI GitHub repo
2. **Runtime**: Python 3.11
3. **Build command**: `pip install -r requirements.txt && python backend/ingest.py`
4. **Start command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. **Region**: Frankfurt
6. **Environment Variables**: `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, `NVIDIA_API_KEY`

### Tests

```bash
.venv/Scripts/pip install -r requirements-dev.txt
.venv/Scripts/pytest tests/ -v --cov=backend
```

---

## 🇫🇷 Midolli-AI — Chatbot RAG pour Portfolio Data

Un chatbot RAG intelligent intégré au [portfolio data de Rafael Midolli](https://r-midolli.github.io/portfolio_rafael_midolli/). Il répond aux questions sur son parcours, CV, projets et compétences en **français ou anglais**, avec 3 APIs en fallback automatique pour garantir zéro interruption.

### Stack Technique

- **Backend** : FastAPI, ChromaDB, pymupdf
- **LLMs** : Gemini 1.5 Flash (×2 clés), NVIDIA LLaMA-3.1-70B (fallback)
- **Embedding** : Gemini gemini-embedding-001 (3072 dimensions)
- **Frontend** : Vanilla JS (IIFE), CSS isolé (`.mai-` prefix)
- **Déploiement** : Render.com (backend), GitHub Pages (widget)

### Fonctionnalités

- ✅ Réponses FR/EN avec détection automatique de langue
- ✅ Thème dark/light synchronisé avec le portfolio
- ✅ Toggle FR/EN synchronisé en temps réel
- ✅ 3-API fallback : Gemini KEY_1 → KEY_2 → NVIDIA
- ✅ Base de connaissances : 13 fichiers MD + CV PDF
- ✅ Zero invention : le bot ne répond que depuis le contexte vérifié
- ✅ Mobile responsive (375px+)
- ✅ Logo SVG inline (M + AI, gradient violet)

---

**Author / Auteur** : Rafael Midolli — [LinkedIn](https://linkedin.com/in/rafael-midolli) — [Portfolio](https://r-midolli.github.io/portfolio_rafael_midolli/)
