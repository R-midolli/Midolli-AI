---
name: knowledge
description: >
  Read this skill before creating or editing any file in
  backend/knowledge/. Defines quality rules for the Midolli-AI
  knowledge base: MD format, what to write, what to avoid,
  how to structure each content type.
---

# SKILL — Knowledge Base / Base de Connaissance Midolli-AI

## Purpose / Objectif

The `.md` files in `backend/knowledge/` are the **single source of truth** for the chatbot.
What is not here, the bot does not know. What is vague, the bot will hallucinate.

---

## Rules Before Writing / Règles avant d'écrire

1. **Always read `.agent/sources/SOURCES_INDEX.md` first** — it lists all verified sources
2. **Read the CV PDF** at `.agent/sources/CV_Rafael_Midolli_2026.pdf` before writing
   experiences, education or skills
3. **Read each project's GitHub README** before writing its knowledge file
4. **Read `.agent/sources/linkedin_profile.md`** for additional context on profile and positioning
5. **Read `.agent/sources/profil_complet_utilisateur.md`** for personal context and interests

---

## Quality Rules / Règles de qualité

- **Size:** each file between 600 and 1200 characters — not more
- **Language:** write in French — it is the primary language of the portfolio
- **Numbers:** always real and verified. Never "significantly improved". Always "-40% analysis time", "20% SKUs = 80% revenue"
- **Company names:** always real (Kantar Worldpanel, Colgate-Palmolive, Scanntech, Aperam)
- **Focus:** one topic per file — never mix education with experiences
- **No invention:** if a metric is not in CV or README, write [VERIFY] and ask Rafael

---

## What to Write in Each File / Contenu de chaque fichier

**00_rafael_bio.md** → full identity: name, role, location, phone, email, LinkedIn, portfolio URL,
availability status, languages, 2-line professional summary.

**01_competences.md** → split into clear categories:
Pilotage & Performance, Business Analysis, Data & BI, ETL & Automation,
GenAI/RAG, Domain Retail/FMCG, Methods & Tools. List specific tools only.

**02_experiences.md** → for each company: name, role, period, city,
3–4 bullet points of what was done, 1 line of impact. Order: most recent first.

**03_education.md** → MBA USP (2024–2025) with thesis focus,
UFABC Engineering Management (2016–2023), Google Data Analytics (2023).
Include focus area for each.

**04 to 09 — projects** → follow this exact format:
[Project Name]
Problème Métier
[Business problem in 2 sentences — business language, not technical]

Solution
[What was built, how it works in simple terms]

Stack Technique
[Technology list — only verified from README]

Impact
[Real metrics with numbers — minimum 2 bullets]

Liens
GitHub: [repo URL]
Portfolio: [portfolio section URL if applicable]

text

---

## What to NEVER Write / Ce qu'il ne faut JAMAIS écrire

- "High accuracy" without a real number
- "Improved performance" without specifying how much
- Technologies Rafael did not actually use (verify in CV or README)
- Duplicate content between files
- Long generic HR sentences
- Anything in Portuguese
