"""
Midolli-AI — RAG Chain (v2 — Optimized 2026)
3-tier intelligent LLM routing with greeting detection,
singleton ChromaDB client, and API timeouts.
"""

import os
import random
import re
import time
from pathlib import Path

import httpx
import chromadb
import google.generativeai as genai
from google.api_core import retry
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VECTORSTORE_DIR = Path(__file__).parent / "data" / "vectorstore"
COLLECTION_NAME = "midolli_knowledge"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# LLM Models — 4 tiers
GEMINI_FAST = "gemini-flash-lite-latest"       # Tier 1: greetings & short Q
GEMINI_NORMAL = "gemini-3-flash-preview"       # Tier 2 fallback for Gemini
GEMINI_BACKUP = "gemini-2.5-flash"             # Last-resort Gemini fallback
KIMI_MODEL = "moonshotai/kimi-k2.5"            # Priority 1: medium/complex
GLM_MODEL = "z-ai/glm5"                        # Priority 2: medium/complex

TOP_K = 8

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Tu es Midolli-AI, l'assistant IA de Rafael Midolli, intégré à son portfolio professionnel.
Tu réponds aux questions de recruteurs et visiteurs sur son parcours, compétences, expériences et projets data.

════════════════════════════════════════════
RÈGLES ABSOLUES
════════════════════════════════════════════

RÈGLE 1 — SOURCE UNIQUE
Toutes tes réponses viennent uniquement du contexte fourni ci-dessous (fichiers .md et code source .py/.sql).

RÈGLE 2 — EXPERTISE TECHNIQUE & MÉTRIQUES
• Projet Churn : Seul projet avec métriques de performance validées : AUC-ROC 0.84 | Lift Decile 1 : 3.2x | ROI simulé +45%.
• Projet Pricing : Suit spécifiquement Cacao, Sucre, Café et Blé via Yahoo Finance.
• Autres projets : Utilise les détails techniques du contexte (colonnes SQL, hyperparamètres, étapes ETL) pour démontrer une expertise réelle, mais précise que "les métriques chiffrées de performance finale (ex: % d'amélioration) ne sont pas publiques".

RÈGLE 3 — INTERDICTIONS
❌ "haute précision", "excellent résultat", "très performant" sans chiffre ou fait technique source.
❌ Métriques inventées (ex: "99% de précision") sans source contextuelle.
❌ Attribuer les métriques d'un projet à un autre.

RÈGLE 4 — FALLBACK OBLIGATOIRE
Si l'info n'est pas dans le contexte et qu'aucune inférence solide n'est possible :
[FR] "Je n'ai pas cette information précise. Contactez Rafael : rbmidolli@gmail.com"
[EN] "I don't have that specific information. Contact Rafael: rbmidolli@gmail.com"

RÈGLE 5 — LANGUE
Détecte la langue de la question et réponds dans la même langue (FR prioritaire, EN, PT si détecté).

RÈGLE 6 — TON
Professionnel, direct, chaleureux. 3-5 phrases max sauf si détail demandé.

RÈGLE 7 — DONNÉES PERSONNELLES
Email/téléphone uniquement si explicitement demandés.

RÈGLE 8 — INFÉRENCE FONDÉE 🔍
Quand une question n'a pas de réponse directe, utilise les données techniques (ex: architecture, outils) pour déduire la réponse :
"Je n'ai pas d'info directe sur [X], mais d'après l'architecture [Outil] utilisée : [données] → [conclusion logique]."
✅ Toujours citer les données sources qui fondent la déduction.
✅ Signaler que c'est une déduction experte.

════════════════════════════════════════════
CONTEXTE RÉCUPÉRÉ
════════════════════════════════════════════
{context}
"""

GREETING_PROMPT = """Tu es Midolli-AI, l'assistant IA de Rafael Midolli, intégré à son portfolio.
Tu parles avec un visiteur sur le site portfolio de Rafael.

RÈGLES :
1. Détecte la langue du message et réponds dans la MÊME langue.
2. Réponse en 2 phrases maximum.
3. Sois chaleureux et professionnel. Invite le visiteur à poser des questions sur les projets, compétences ou parcours de Rafael.
4. Ne jamais inventer d'information sur Rafael.

CONTEXTE : Rafael Midolli est un Business Data Analyst spécialisé Retail/FMCG, basé en France.
6 projets : Retail BA, ELT Analytics, Supply Chain, FMCG Pricing Monitor, Customer Churn Prediction, Midolli-AI.
Langues : Portugais (natif), Français (C1), Anglais (B2), Espagnol (A2).
Disponible CDI & freelance 2026.
"""

# ---------------------------------------------------------------------------
# Greeting Detection
# ---------------------------------------------------------------------------
GREETING_PATTERNS = re.compile(
    r"^(h[ie]|hey|hello|howdy|yo|oi|ol[aá]|bom dia|boa (tarde|noite)|"
    r"tudo bem|bonjour|bonsoir|salut|coucou|"
    r"good (morning|afternoon|evening)|"
    r"what'?s up|sup|hola|"
    r"hi there|hey there|oi tudo|e a[ií]|"
    r"cava|ça va|comment vas|quoi de neuf)[!?.,\s]*$",
    re.IGNORECASE,
)


def _is_greeting(query: str) -> bool:
    """Fast regex check for greetings — no RAG needed."""
    return bool(GREETING_PATTERNS.match(query.strip()))


# ---------------------------------------------------------------------------
# Singleton ChromaDB Client (avoid re-creating on every call)
# ---------------------------------------------------------------------------
_chroma_client = None
_chroma_collection = None


def _get_collection():
    """Get the ChromaDB collection (singleton)."""
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        _chroma_client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))
        _chroma_collection = _chroma_client.get_collection(name=COLLECTION_NAME)
    return _chroma_collection


# ---------------------------------------------------------------------------
# Configure Gemini Once
# ---------------------------------------------------------------------------
_gemini_configured = False


def _ensure_gemini_configured():
    """Configure Gemini API key once at module level."""
    global _gemini_configured
    if not _gemini_configured:
        api_key = os.getenv("GEMINI_API_KEY_1") or os.getenv("GEMINI_API_KEY_2")
        if api_key:
            genai.configure(api_key=api_key)
            _gemini_configured = True


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
def retrieve(query: str) -> list[dict]:
    """Retrieve top-K relevant chunks for a query with API key fallback."""
    try:
        t0 = time.time()
        
        key1 = os.getenv("GEMINI_API_KEY_1")
        key2 = os.getenv("GEMINI_API_KEY_2")
        
        keys_to_try = [k for k in [key1, key2] if k]
        if not keys_to_try:
            print("[ERROR] No Gemini API key found for embeddings", flush=True)
            return []

        query_embedding = None
        last_err = None
        
        for idx, embed_key in enumerate(keys_to_try):
            try:
                genai.configure(api_key=embed_key)
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=query,
                    request_options={"timeout": 4.0, "retry": None}
                )
                query_embedding = result["embedding"]
                break  # Success
            except Exception as e:
                last_err = e
                print(f"[WARNING] Embedding failed with KEY_{idx+1}: {e}", flush=True)

        if not query_embedding:
            print(f"[ERROR] All embedding attempts failed. Last error: {last_err}", flush=True)
            return []

        collection = _get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
        )
        print(f"[PERF] Retrieval took {time.time() - t0:.2f}s", flush=True)

        chunks = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                source = ""
                if results["metadatas"] and results["metadatas"][0]:
                    source = results["metadatas"][0][i].get("source", "")
                chunks.append({"content": doc, "source": source})

        return chunks
    except Exception as e:
        print(f"[ERROR] Retrieval failed: {e}", flush=True)
        return []


# ---------------------------------------------------------------------------
# LLM Calls
# ---------------------------------------------------------------------------
def _build_gemini_messages(query: str, context_chunks: list[dict], history: list) -> list[dict]:
    """Build the chat messages for Gemini."""
    context_text = "\n\n---\n\n".join(
        [f"[Source: {c['source']}]\n{c['content']}" for c in context_chunks]
    )

    messages = [
        {"role": "user", "parts": [SYSTEM_PROMPT.format(context=context_text)]},
        {"role": "model", "parts": ["Understood. I will answer based only on the provided context, in the user's language."]},
    ]

    # Gemini strictly requires alternating roles starting with 'user'
    # Since we prepend system messages as 'user'/'model', the actual history MUST start with 'user'
    # so the sequence remains: user -> model (sys prompt) -> user (history 1) -> model (history 2) -> user (current query)
    valid_history = []
    expected_next = "user"
    for msg in (history or []):
        raw_role = msg.get("role", "user")
        role = "user" if raw_role == "user" else "model"
        
        # enforce alternation
        if role == expected_next:
            valid_history.append({"role": role, "parts": [msg.get("content", "")]})
            expected_next = "model" if role == "user" else "user"

    messages.extend(valid_history)
    
    messages.append({"role": "user", "parts": [query]})
    return messages


def _try_gemini(query: str, context_chunks: list[dict], history: list, api_key: str, key_name: str, model_name: str, custom_timeout: float = 10.0) -> dict | None:
    """Try to get an answer from Gemini."""
    try:
        t0 = time.time()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        messages = _build_gemini_messages(query, context_chunks, history)
        response = model.generate_content(
            messages,
            request_options={"timeout": custom_timeout, "retry": None},
        )

        elapsed = time.time() - t0
        print(f"[PERF] Gemini ({model_name}/{key_name}) responded in {elapsed:.2f}s", flush=True)

        if response and response.text:
            sources = list(set(c["source"] for c in context_chunks if c["source"]))
            return {
                "reply": response.text,
                "sources": sources,
                "api_used": f"Gemini ({model_name} / {key_name})",
            }
    except Exception as e:
        print(f"[WARNING] Gemini ({model_name} / {key_name}) failed: {e}", flush=True)
        raise Exception(f"Gemini {model_name} failed: {e}")


def _try_gemini_greeting(query: str, api_key: str, key_name: str, model_name: str) -> dict | None:
    """Ultra-fast Gemini call for greetings — no RAG context needed."""
    try:
        t0 = time.time()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        messages = [
            {"role": "user", "parts": [GREETING_PROMPT]},
            {"role": "model", "parts": ["Understood. I'll greet the visitor warmly and invite them to ask about Rafael."]},
            {"role": "user", "parts": [query]},
        ]

        response = model.generate_content(
            messages,
            request_options={"timeout": 8, "retry": retry.Retry(initial=0, maximum=0, multiplier=1.0, deadline=1.0)},
        )

        elapsed = time.time() - t0
        print(f"[PERF] Greeting via Gemini ({model_name}/{key_name}) in {elapsed:.2f}s", flush=True)

        if response and response.text:
            return {
                "reply": response.text,
                "sources": [],
                "api_used": f"Gemini ({model_name} / {key_name}) [greeting]",
            }
    except Exception as e:
        print(f"[WARNING] Gemini greeting ({model_name}/{key_name}) failed: {e}", flush=True)
        raise Exception(f"Gemini greeting {model_name} failed: {e}")


def _try_nvidia(
    query: str,
    context_chunks: list[dict],
    history: list,
    api_key_env: str,
    model_name: str,
    label: str,
    max_retries: int = 1,
) -> dict | None:
    """Try NVIDIA Build API. Fast-fail on timeout (cold start), only retry on 429."""
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise Exception(f"{api_key_env} not found in environment")

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
        timeout=httpx.Timeout(8.0),  # 8s hard cap for EVERYTHING (connect, read, write)
    )

    context_text = "\n\n---\n\n".join(
        [f"[Source: {c['source']}]\n{c['content']}" for c in context_chunks]
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(context=context_text)},
    ]

    # Filter out empty or misaligned history for NVIDIA
    valid_history = []
    expected_next = "user"
    for msg in (history or []):
        role = msg.get("role", "user")
        if role in ["user", "assistant"] and role == expected_next:
            valid_history.append({"role": role, "content": msg.get("content", "")})
            expected_next = "assistant" if role == "user" else "user"

    messages.extend(valid_history)
    messages.append({"role": "user", "content": query})

    last_error = None
    for attempt in range(max_retries):
        try:
            t0 = time.time()
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.4,
                max_tokens=2048,
            )

            elapsed = time.time() - t0
            print(f"[PERF] {label} ({model_name}) responded in {elapsed:.2f}s", flush=True)

            if response and response.choices and response.choices[0].message.content:
                reply = response.choices[0].message.content
                sources = list(set(c["source"] for c in context_chunks if c["source"]))
                return {
                    "reply": reply,
                    "sources": sources,
                    "api_used": f"{label} ({model_name})",
                }
            else:
                raise Exception(f"{label}: empty response")
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            # Only retry on rate limit (429). Timeout = cold start, skip immediately.
            if "429" in str(e) or "rate limit" in err_str:
                wait = (2 ** attempt) + random.random()
                print(f"[RETRY] {label} attempt {attempt + 1}/{max_retries} — 429 rate limit — waiting {wait:.1f}s", flush=True)
                time.sleep(wait)
                continue
            else:
                print(f"[SKIP] {label} failed (timeout/error, no retry): {e}", flush=True)
                break

    raise Exception(f"{label} failed: {last_error}")


# ---------------------------------------------------------------------------
# Page Context Mapping
# ---------------------------------------------------------------------------
PAGE_CONTEXT_MAP = {
    "project-retail": "Retail Analytics — Pareto & Segmentation Réseau",
    "project-elt-retail": "ELT Retail Analytics — Pipeline & Star Schema",
    "project-supply-chain": "Supply Chain Analytics — ETL & Dashboard",
    "project-pricing": "FMCG Cost Pressure Monitor — API & Dashboard",
    "project-midolli-ai": "Midolli-AI — RAG Chatbot & LLM Router",
    "project-churn": "Customer Churn Prediction & Reactivation",
}


def _resolve_page_context(page_path: str) -> str:
    """Map a page pathname to a project context hint for the LLM."""
    if not page_path:
        return ""
    path_lower = page_path.lower().rstrip("/")
    # Extract basename without extension
    basename = path_lower.rsplit("/", 1)[-1].replace(".html", "")
    for key, project_name in PAGE_CONTEXT_MAP.items():
        if key in basename:
            return project_name
    return ""


# ---------------------------------------------------------------------------
# Query Classifier
# ---------------------------------------------------------------------------
def _query_category(query: str, history: list) -> str:
    """Classify query into simple / normal / complex."""
    if _is_greeting(query):
        return "greeting"

    if len(history) >= 6 or len(query) > 250:
        return "complex"

    complex_keywords = [
        "analise", "resuma", "compare", "diferença", "explique",
        "synthesize", "analyze", "difference", "pourquoi", "comment",
        "expliquer", "détail", "detail", "architecture", "pipeline",
        "how does", "how do", "como funciona", "explain",
    ]
    query_lower = query.lower()
    for kw in complex_keywords:
        if kw in query_lower:
            return "complex"

    # Route all standard conversational queries to 'simple' (Flash Lite) for max speed
    if len(query) < 150:
        return "simple"

    return "normal"


# ---------------------------------------------------------------------------
# Main Answer Function
# ---------------------------------------------------------------------------
def answer(query: str, history: list | None = None, page_context: str = "") -> dict:
    """
    Answer a query using intelligent LLM routing with page context awareness.
    Returns: {"reply": str, "sources": list[str], "api_used": str}
    """
    if not query or not query.strip():
        return {
            "reply": "Please provide a question. / Veuillez poser une question.",
            "sources": [],
            "api_used": "none",
        }

    try:
        t0_total = time.time()
        history_safe = history or []
        category = _query_category(query, history_safe)

        # Resolve page context
        project_hint = _resolve_page_context(page_context)
        if project_hint:
            print(f"[CONTEXT] Page: {page_context} → Project: {project_hint}", flush=True)

        key1 = os.getenv("GEMINI_API_KEY_1")
        key2 = os.getenv("GEMINI_API_KEY_2")
        errors = []

        print(f"[ROUTER] Query='{query[:60]}...' Category={category}", flush=True)

        # ── GREETING (no RAG, no embedding, ultra-fast) ──
        if category == "greeting":
            if key2:
                try:
                    result = _try_gemini_greeting(query, key2, "KEY_2", GEMINI_FAST)
                    if result:
                        print(f"[PERF] Total greeting time: {time.time() - t0_total:.2f}s", flush=True)
                        return result
                except Exception as e:
                    errors.append(f"G2:{e}")

            if key1:
                try:
                    result = _try_gemini_greeting(query, key1, "KEY_1", GEMINI_FAST)
                    if result:
                        print(f"[PERF] Total greeting time: {time.time() - t0_total:.2f}s", flush=True)
                        return result
                except Exception as e:
                    errors.append(f"G1:{e}")

            # Hardcoded fallback for greetings (instant)
            return {
                "reply": "Bonjour ! Je suis Midolli-AI, l'assistant de Rafael Midolli. Comment puis-je vous aider ? 😊 / Hello! I'm Midolli-AI, Rafael Midolli's assistant. How can I help you?",
                "sources": [],
                "api_used": "fallback",
            }

        # ── RAG retrieval (only for non-greeting queries) ──
        context_chunks = retrieve(query)
        if not context_chunks:
            return {
                "reply": "I could not find relevant information in my knowledge base. / Je n'ai pas trouvé d'information pertinente dans ma base de connaissances.",
                "sources": [],
                "api_used": "none",
            }

        # ── Inject page context as priority hint ──
        if project_hint:
            page_hint_chunk = {
                "content": (
                    f"[CONTEXTE DE PAGE] L'utilisateur navigue actuellement sur la page du projet : "
                    f"**{project_hint}**. Si la question est vague ou utilise 'ce projet', "
                    f"'this project', 'este projeto', elle concerne probablement ce projet. "
                    f"Priorise les informations de ce projet dans ta réponse."
                ),
                "source": "page_context",
            }
            context_chunks = [page_hint_chunk] + context_chunks

        # ── SIMPLE (short factual Q) ──
        if category == "simple":
            # Tier 1: Gemini Flash Lite (cheapest, fastest)
            if key2:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key2, "KEY_2", GEMINI_FAST, custom_timeout=2.0)
                    if result:
                        print(f"[PERF] Total simple time: {time.time() - t0_total:.2f}s", flush=True)
                        return result
                except Exception as e:
                    errors.append(f"G2:{e}")

            # Fallback to Gemini Normal
            if key1:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key1, "KEY_1", GEMINI_NORMAL)
                    if result:
                        return result
                except Exception as e:
                    errors.append(f"G1:{e}")

            # Fallback 3: Kimi (NVIDIA)
            try:
                result = _try_nvidia(query, context_chunks, history_safe, "NVIDIA_API_KEY_1", KIMI_MODEL, "Kimi K2.5")
                if result:
                    return result
            except Exception as e:
                errors.append(f"Kimi:{e}")

            # Fallback 4: GLM-5 (NVIDIA)
            try:
                result = _try_nvidia(query, context_chunks, history_safe, "NVIDIA_API_KEY_2", GLM_MODEL, "GLM-5")
                if result:
                    return result
            except Exception as e:
                errors.append(f"GLM:{e}")

        # ── NORMAL (standard RAG question) ──
        elif category == "normal":
            # Priority 1: Kimi K2.5 (8s — if warm, responds in ~5s)
            try:
                result = _try_nvidia(query, context_chunks, history_safe, "NVIDIA_API_KEY_1", KIMI_MODEL, "Kimi K2.5")
                if result:
                    print(f"[PERF] Total normal time: {time.time() - t0_total:.2f}s", flush=True)
                    return result
            except Exception as e:
                errors.append(f"Kimi:{e}")

            # Priority 2: Gemini Normal (reliable, ~3-5s)
            if key1:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key1, "KEY_1", GEMINI_NORMAL)
                    if result:
                        return result
                except Exception as e:
                    errors.append(f"G1:{e}")

            # Priority 3: GLM-5 (8s)
            try:
                result = _try_nvidia(query, context_chunks, history_safe, "NVIDIA_API_KEY_2", GLM_MODEL, "GLM-5")
                if result:
                    return result
            except Exception as e:
                errors.append(f"GLM:{e}")

            # Last resort: Gemini Backup
            if key2:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key2, "KEY_2", GEMINI_BACKUP)
                    if result:
                        return result
                except Exception as e:
                    errors.append(f"G2:{e}")

        # ── COMPLEX (deep reasoning) ──
        else:
            # Priority 1: Kimi K2.5 (8s — best for analysis if warm)
            try:
                result = _try_nvidia(query, context_chunks, history_safe, "NVIDIA_API_KEY_1", KIMI_MODEL, "Kimi K2.5")
                if result:
                    print(f"[PERF] Total complex time: {time.time() - t0_total:.2f}s", flush=True)
                    return result
            except Exception as e:
                errors.append(f"Kimi:{e}")

            # Priority 2: Gemini Normal (reliable)
            if key1:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key1, "KEY_1", GEMINI_NORMAL)
                    if result:
                        return result
                except Exception as e:
                    errors.append(f"G1:{e}")

            # Priority 3: GLM-5 (8s)
            try:
                result = _try_nvidia(query, context_chunks, history_safe, "NVIDIA_API_KEY_2", GLM_MODEL, "GLM-5")
                if result:
                    return result
            except Exception as e:
                errors.append(f"GLM:{e}")

            # Last resort: Gemini Backup
            if key2:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key2, "KEY_2", GEMINI_BACKUP)
                    if result:
                        return result
                except Exception as e:
                    errors.append(f"G2:{e}")

        # All APIs failed
        return {
            "reply": f"All APIs are temporarily unavailable. Please try again later. / Toutes les APIs sont temporairement indisponibles. Veuillez réessayer plus tard. [DEBUG: {errors}]",
            "sources": [],
            "api_used": "none",
        }

    except Exception as e:
        print(f"[ERROR] answer() failed: {e}", flush=True)
        return {
            "reply": "An unexpected error occurred. Please try again. / Une erreur inattendue s'est produite. Veuillez réessayer.",
            "sources": [],
            "api_used": "none",
        }
