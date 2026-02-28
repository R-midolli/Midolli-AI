# MAPA_PROJETO — Midolli-AI Project Map

Midolli-AI is a RAG chatbot embedded in Rafael Midolli's data portfolio. It answers recruiter questions about his career, projects and skills in FR/EN, using FastAPI + ChromaDB + Gemini/NVIDIA APIs with 3-API fallback for zero downtime.

---

## Files and Purpose / Fichiers et Objectif

### Configuration
| File | Purpose |
|------|---------|
| `.env` | API keys (GEMINI\_API\_KEY\_1, GEMINI\_API\_KEY\_2, NVIDIA\_API\_KEY) — gitignored |
| `.env.example` | Template for API keys |
| `.gitignore` | Ignores .env, .venv, vectorstore, pycache |
| `requirements.txt` | 8 production dependencies |
| `requirements-dev.txt` | Dev/test dependencies |
| `Makefile` | setup, ingest, serve, test, lint targets |
| `.github/workflows/ci.yml` | GitHub Actions CI (ruff + black + pytest) |

### Backend (`backend/`)
| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `ingest.py` | Reads MD + CV PDF, chunks, embeds with Gemini, upserts to ChromaDB |
| `chain.py` | RAG retrieve + answer with 3-API fallback |
| `main.py` | FastAPI app with /health and /chat endpoints |

### Knowledge Base (`backend/knowledge/`)
| File | Content |
|------|---------|
| `00_rafael_bio.md` | Identity, contact, availability |
| `01_competences.md` | Skills by category |
| `02_experiences.md` | 4 work experiences (Kantar, Scanntech, Colgate, Aperam) |
| `03_education.md` | MBA USP, UFABC, Google cert |
| `04_project_retail.md` | Retail BA Diagnostic |
| `05_project_elt.md` | ELT Retail Analytics |
| `06_project_supply.md` | Supply Chain Analytics |
| `07_project_pricing.md` | FMCG Pricing Monitor |
| `08_project_midolli_ai.md` | This project (Midolli-AI) |
| `09_project_churn.md` | Customer Churn Prediction |
| `10_rafael_positioning.md` | Recruiter-facing positioning |
| `11_faq_rafael.md` | FAQ (12 Q&A pairs) |

### Frontend (`frontend/`)
| File | Purpose |
|------|---------|
| `midolli-widget.css` | Widget styles, .mai- prefix, dark/light themes |
| `midolli-widget.js` | IIFE widget with SVG logo, I18N, MutationObserver |
| `test.html` | Local test page pointing to localhost:8000 |

### Tests (`tests/`)
| File | Purpose |
|------|---------|
| `test_chain.py` | Tests for retrieve() and answer() |
| `test_api.py` | Tests for /health and /chat endpoints |

---

## Links / Liens

| Resource | URL |
|----------|-----|
| GitHub (Midolli-AI) | https://github.com/R-midolli/Midolli-AI |
| Portfolio | https://r-midolli.github.io/portfolio_rafael_midolli |
| LinkedIn | https://linkedin.com/in/rafael-midolli |
| Retail BA Diagnostic | https://github.com/R-midolli/retail-ba-diagnostic |
| ELT Retail Analytics | https://github.com/R-midolli/elt_retail_analytics |
| Supply Chain Analytics | https://github.com/R-midolli/supply_chain_analytics |
| FMCG Pricing Monitor | https://github.com/R-midolli/fmcg_pricing_macro_monitor |
| Customer Churn | https://github.com/R-midolli/Customer-Churn-Prediction-Reactivation-Propensity |
