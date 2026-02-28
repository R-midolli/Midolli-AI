---
name: sources
description: >
  Read this skill at the very beginning of the session, before
  touching any file. Defines how to handle all external source
  materials: CV PDF, LinkedIn, GitHub repos, portfolio.
  Prevents hallucination by enforcing source-first workflow.
---

# SKILL - Source Materials Management

## Purpose / Objectif

All information about Rafael that enters the knowledge base must come
from a verified source. This skill defines what those sources are,
where they are, and how to use them.

---

## Source Priority / Priorite des sources

Priority 1 - Highest : CV PDF 2026 — .agent/sources/CV_Rafael_Midolli_2026.pdf
Priority 2 - High    : LinkedIn    — .agent/sources/linkedin_profile.md
Priority 3 - High    : User notes  — .agent/sources/profil_complet_utilisateur.md
Priority 4 - Per project : GitHub README — URL listed in SOURCES_INDEX.md
Priority 5 - Visual  : Portfolio   — https://r-midolli.github.io/portfolio_rafael_midolli

When sources conflict: CV wins.

---

## Workflow Before Writing Knowledge Files

STEP A - Confirm all source files are present:
  ls .agent/sources/
  Must show: CV_Rafael_Midolli_2026.pdf, linkedin_profile.md,
             profil_complet_utilisateur.md, SOURCES_INDEX.md

STEP B - For identity, experiences, education, skills:
  Read CV PDF via pymupdf.
  Cross-reference with linkedin_profile.md.

STEP C - For each portfolio project (04 to 09):
  Read the GitHub README first.
  Extract: problem, solution, stack, real metrics.
  Only write what is explicitly stated in the README.
  If a metric is not found: write [VERIFY] and ask Rafael before continuing.

STEP D - Always verify the full index:
  cat .agent/sources/SOURCES_INDEX.md

---

## Anti-Hallucination Rules

- Never invent a company name
  Only allowed: Kantar Worldpanel, Scanntech, Colgate-Palmolive, Aperam
- Never invent a metric — only numbers found in CV or README
- Never assume a technology — only tools explicitly in CV or README
- Never invent a date — all periods must match the CV exactly
- Use [VERIFY] tag if unsure — ask Rafael before writing the final file

---

## Files in .agent/sources/

CV_Rafael_Midolli_2026.pdf    — Full CV 2026 — experiences, education, skills, contact
linkedin_profile.md           — LinkedIn content — profile framing, additional context
profil_complet_utilisateur.md — Personal notes — interests, goals, personal context
SOURCES_INDEX.md              — Full index + verified data table — agent reference

---

## What to NEVER Do

- Write a knowledge file without reading the corresponding source first
- Use information from memory or training data about Rafael
- Skip the README reading step for project files
- Write anything in Portuguese
