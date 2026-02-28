---
name: widget
description: >
  Read this skill before creating any frontend file:
  midolli-widget.js, midolli-widget.css, test.html.
  Defines widget design, official SVG logo, portfolio
  integration rules and what to never do in JS.
---

# SKILL — Vanilla JS Widget + Logo + CSS

## Design Principles / Principes de design

**Total isolation:** all CSS selectors use `.mai-` prefix.
No global selectors. The widget must never break the portfolio's CSS.

**Zero external dependencies:** no React, no Vue, no jQuery.
Pure Vanilla JS — the portfolio is static with no build step.

**Mandatory IIFE:** all code inside `(function MidolliAI() { ... })()`
to avoid polluting global scope. Expose only `window.MidolliAI = { init }`.

---

## Official SVG Logo — use exactly this design

Circle with violet gradient `#6d28d9 → #4f46e5`.
Letter "M" in bold monospace white. Subtle horizontal separator line.
"AI" in light violet `#c4b5fd` below, with letter-spacing.
Clean, no effects, no glow, no decorative borders, no glitch.

FAB version (62px): large M (~17px) + line + AI (~8px, letter-spacing 4px)
Header avatar (42px): medium M (~12px) + line + AI (~6px)


SVG is inline in the JS file — not an external asset.

---

## Mandatory DOM Structure / Structure DOM obligatoire

- `#mai-pulse-ring` — animated ring appearing 3s after load,
  disappears when chat is opened for the first time
- `#mai-fab` — floating button 62px, z-index 99999, bottom 28px right 28px
- `#mai-panel` — chat panel, z-index 99998, bottom 108px right 28px, hidden by default

**Inside the panel:**
- Header: avatar (small SVG logo + green status dot), name "Midolli-AI",
  subtitle, FR/EN language button, dark/light button, close button
- Timestamp of when the chat was opened
- Message area with scroll
- Quick-action chips (clickable pills)
- Input area: textarea + send button (active only when text is present)
- Disclaimer: "Midolli-AI peut faire des erreurs." / "Midolli-AI can make mistakes."

**Themes:**
- Dark: background `#0d1117`, bot bubbles `rgba(255,255,255,0.07)`, text `#e6edf3`
- Light: background `#f3f4f8`, bot bubbles `#ffffff`, text `#111827`
- User bubbles: always violet gradient `#6d28d9 → #4f46e5`, white text

---

## i18n Object / Objet i18n

```javascript
const I18N = {
  fr: {
    welcome: "Bonjour ! Je suis Midolli-AI, l'assistant de Rafael Midolli. Je connais tout sur son parcours de Data Analyst, ses projets et son expertise. Comment puis-je vous aider ?",
    chips: ["🎓 Formation", "📊 Résultats", "🛠️ Stack", "📁 Projets"],
    placeholder: "Posez votre question...",
    disclaimer: "Midolli-AI peut faire des erreurs.",
    subtitle: "Assistant Data Portfolio",
    send: "Envoyer"
  },
  en: {
    welcome: "Hello! I'm Midolli-AI, Rafael Midolli's assistant. I know everything about his Data Analyst journey, projects and expertise. How can I help you?",
    chips: ["🎓 Education", "📊 Results", "🛠️ Stack", "📁 Projects"],
    placeholder: "Ask me anything...",
    disclaimer: "Midolli-AI can make mistakes.",
    subtitle: "Data Portfolio Assistant",
    send: "Send"
  }
}
Portfolio Sync / Synchronisation avec le portfolio
Read initial state via document.body.dataset.theme (or class) and
window.currentLang (or document.documentElement.lang)

Create MutationObserver on document.body to detect theme change in real time

Create MutationObserver on document.documentElement to detect language change

When change detected, apply immediately to panel without closing/reopening

Markdown Rendering / Rendu markdown
Implement minimal parser for bot responses:

**text** → <strong>text</strong>

`code` → <code> with dark background

Blocks ```language ... ``` → <div> with language label header + #0d1117 background

\n → <br> inside normal text

Never use innerHTML with raw API content (XSS risk).
Build all elements via createElement and textContent.

What to NEVER Do / Ce qu'il ne faut JAMAIS faire
Use innerHTML with API response content (XSS)

Hardcode apiUrl in the widget — it comes from init(config)

Add external dependencies (CDN links, imports)

Use position: fixed without correct z-index (portfolio navbar likely uses z-index 100–1000)

Load previous messages from localStorage — history is session only

Display widget wider than screen on mobile

Write comments or text in Portuguese

text

---

O arquivo completo deve ter estas **6 seções**:

1. Design Principles ✅
2. Official SVG Logo ✅
3. Mandatory DOM Structure ✅
4. i18n Object ✅
5. Portfolio Sync ← **faltava**
6. Markdown Rendering ← **faltava**
7. What to NEVER Do ← **faltava**