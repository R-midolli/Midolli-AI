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
from google import genai
from google.genai import types
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VECTORSTORE_DIR = Path(__file__).parent / "data" / "vectorstore"
COLLECTION_NAME = "midolli_knowledge"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# LLM Models — Updated 2026 for max speed
GEMINI_LITE_31 = "gemini-3.1-flash-lite-preview"  # Tier 1: ultra-fast, latest
GEMINI_LITE_LATEST = "gemini-flash-lite-latest"   # Tier 2: reliable lite model
GEMINI_NORMAL = "gemini-3-flash-preview"          # Tier 3: standard flash
KIMI_MODEL = "moonshotai/kimi-k2.5"               # Fallback 1: complex queries
GLM_MODEL = "z-ai/glm5"                           # Fallback 2: complex queries
GEMINI_BACKUP = "gemini-2.5-flash"                # Last resort fallback

TOP_K = 8

LOCAL_GREETING_REPLIES = {
    "pt": "Olá! Sou o Midolli-AI, assistente do portfólio do Rafael Midolli. Posso resumir a trajetória dele, explicar os projetos e detalhar a stack usada em cada caso.",
    "en": "Hello! I'm Midolli-AI, Rafael Midolli's portfolio assistant. I can summarize his background, explain the projects, and detail the stack used in each one.",
    "fr": "Bonjour ! Je suis Midolli-AI, l'assistant du portfolio de Rafael Midolli. Je peux résumer son parcours, expliquer ses projets et détailler la stack utilisée dans chacun d'eux.",
}

LOCAL_BIO_REPLIES = {
    "pt": "Rafael Midolli é um Business Data Analyst e Analytics Engineer baseado na França, especializado em Retail e FMCG. Ele combina SQL, dbt, Python e visualização de dados para transformar dados em decisões de negócio, com foco em performance comercial, supply chain, pricing e analytics engineering.",
    "en": "Rafael Midolli is a Business Data Analyst and Analytics Engineer based in France, specialized in Retail and FMCG. He combines SQL, dbt, Python, and data visualization to turn data into business decisions, with a focus on commercial performance, supply chain, pricing, and analytics engineering.",
    "fr": "Rafael Midolli est un Business Data Analyst et Analytics Engineer basé en France, spécialisé en Retail et FMCG. Il combine SQL, dbt, Python et data visualisation pour transformer la donnée en décisions business, avec un focus sur la performance commerciale, la supply chain, le pricing et l'analytics engineering.",
}

OUT_OF_SCOPE_REPLIES = {
    "pt": "Não tenho essa informação específica na base do portfólio. Posso responder sobre o percurso do Rafael, as competências dele e os projetos do portfólio.",
    "en": "I don't have that specific information in the portfolio knowledge base. I can answer about Rafael's background, skills, and portfolio projects.",
    "fr": "Je n'ai pas cette information précise dans la base du portfolio. Je peux répondre sur le parcours de Rafael, ses compétences et les projets du portfolio.",
}

DBT_PROJECT_REPLIES = {
    "pt": "Sim. O projeto em que o uso de dbt está explicitamente documentado é o ELT Retail Analytics. Nele, o Rafael usa Python para ingestão, PostgreSQL em Docker para armazenamento e dbt para transformar os dados de staging até marts e reporting em Star Schema.",
    "en": "Yes. The project where dbt usage is explicitly documented is ELT Retail Analytics. In that project, Rafael uses Python for ingestion, PostgreSQL in Docker for storage, and dbt to transform data from staging to marts and reporting in a Star Schema.",
    "fr": "Oui. Le projet où l'utilisation de dbt est explicitement documentée est ELT Retail Analytics. Rafael y utilise Python pour l'ingestion, PostgreSQL dans Docker pour le stockage, et dbt pour transformer les données de staging vers les marts et le reporting en Star Schema.",
}

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

RÈGLE 9 — DIFFÉRENCIATION PARCOURS VS PROJETS
• Présentation Générale : Focus sur le profil Business Data Analyst, l'expertise Retail/FMCG et l'Analytics Engineering.
• INTERDICTION : Ne mentionne PAS de détails techniques ultra-spécifiques (ex: XGBoost, AUC-ROC, paramètres de scripts) dans une présentation globale de carrière, sauf si l'utilisateur pose une question technique.
• Métier : Valorise les compétences "Métier" (KPIs de vente, ROI, diagnostic business, dbt, SQL) plutôt que les modèles mathématiques purs.

════════════════════════════════════════════
BIO DE RAFAEL (BIO EXPRESS)
════════════════════════════════════════════
Rafael Midolli est un Business Data Analyst & Analytics Engineer basé en France, spécialisé dans les secteurs Retail et FMCG.
• Expertise Métier : Diagnostic de performance business, suivi de l'inflation/commodités, optimisation Supply Chain et Analytics Engineering.
• Compétences Clés : SQL expert, dbt (Star Schema), Python (automatisation), Data Visualization, KPIs Retail (Pareto, Marge, OTIF).
• Langues : Français (C1), Anglais (B2), Portugais (Natif).
• Portfolio : 6 projets data majeurs démontrant sa capacité à transformer la donnée en décisions business.
• Contact : rbmidolli@gmail.com

════════════════════════════════════════════
CONTEXTE RÉCUPÉRÉ (RAG)
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
# Broadened to catch "quem é rafael, ..." and other bio variations
GREETING_PATTERNS = re.compile(
    r"^(h[ie]|hey|hello|howdy|yo|oi|ol[aá]|bom dia|boa (tarde|noite)|"
    r"tudo bem|bonjour|bonsoir|salut|coucou|"
    r"good (morning|afternoon|evening)|"
    r"what'?s up|sup|hola|"
    r"hi there|hey there|oi tudo|e a[ií]|"
    r"cava|ça va|comment vas|quoi de neuf)[!?.,\s]*$",
    re.IGNORECASE,
)

ELONGATED_GREETING_PATTERNS = [
    re.compile(r"^o+i+$", re.IGNORECASE),
    re.compile(r"^o+l+a+$", re.IGNORECASE),
    re.compile(r"^h+i+$", re.IGNORECASE),
    re.compile(r"^h+e+y+$", re.IGNORECASE),
]

BIO_PATTERNS = [
    re.compile(r"\bquem\s+(é|e|eh)\s+(o\s+)?rafael\b", re.IGNORECASE),
    re.compile(r"\bfale\s+sobre\s+(o\s+)?rafael\b", re.IGNORECASE),
    re.compile(r"\bsobre\s+(o\s+)?rafael\b", re.IGNORECASE),
    re.compile(r"\bwho\s+is\s+rafael\b", re.IGNORECASE),
    re.compile(r"\btell\s+me\s+about\s+rafael\b", re.IGNORECASE),
    re.compile(r"\babout\s+rafael\b", re.IGNORECASE),
    re.compile(r"\bqui\s+est\s+rafael\b", re.IGNORECASE),
    re.compile(r"\bparcours\s+de\s+rafael\b", re.IGNORECASE),
    re.compile(r"\bprésente\s+rafael\b", re.IGNORECASE),
    re.compile(r"\bwho\s+are\s+you\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+can\s+you\s+do\b", re.IGNORECASE),
    re.compile(r"\bquem\s+é\s+você\b", re.IGNORECASE),
]

OUT_OF_SCOPE_PATTERNS = [
    re.compile(r"\bgosta\s+de\b", re.IGNORECASE),
    re.compile(r"\baime\b", re.IGNORECASE),
    re.compile(r"\blikes?\b", re.IGNORECASE),
    re.compile(r"\bfavorite\b", re.IGNORECASE),
    re.compile(r"\bhobb(y|ies)\b", re.IGNORECASE),
    re.compile(r"\banimais?\b", re.IGNORECASE),
    re.compile(r"\banimals?\b", re.IGNORECASE),
    re.compile(r"\bcomida\b", re.IGNORECASE),
    re.compile(r"\bfood\b", re.IGNORECASE),
    re.compile(r"\bpet(s)?\b", re.IGNORECASE),
]


def _get_env_value(*names: str) -> str | None:
    """Return the first non-empty environment variable among aliases."""
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def _get_gemini_keys() -> list[str]:
    """Return configured Gemini keys, supporting legacy and current env names."""
    keys = [
        _get_env_value("GEMINI_API_KEY_1", "GOOGLE_API_KEY_1", "GEMINI_API_KEY"),
        _get_env_value("GEMINI_API_KEY_2", "GOOGLE_API_KEY_2"),
    ]
    unique_keys = []
    for key in keys:
        if key and key not in unique_keys:
            unique_keys.append(key)
    return unique_keys


def _get_nvidia_key(slot: str) -> str | None:
    """Return NVIDIA API key, accepting both single-key and multi-key env styles."""
    if slot == "NVIDIA_API_KEY_2":
        return _get_env_value("NVIDIA_API_KEY_2", "NVIDIA_API_KEY")
    return _get_env_value("NVIDIA_API_KEY_1", "NVIDIA_API_KEY")


def _get_gemini_client(api_key: str) -> genai.Client:
    """Create a Gemini client bound to one API key."""
    return genai.Client(api_key=api_key)


def _get_gemini_http_options(timeout_seconds: float) -> types.HttpOptions:
    """google.genai enforces a minimum request timeout of 10 seconds."""
    timeout_ms = max(10000, int(timeout_seconds * 1000))
    return types.HttpOptions(timeout=timeout_ms)


def _detect_language(query: str) -> str:
    """Best-effort language detection for deterministic fallback replies."""
    q = (query or "").lower()

    pt_markers = ["quem", "projetos", "voce", "você", "quais", "sobre", "ola", "olá", "oi", "trajetória", "gosta", "animais", "comida"]
    en_markers = ["who", "what", "about", "projects", "skills", "hello", "tell me"]

    if any(marker in q for marker in pt_markers):
        return "pt"
    if any(marker in q for marker in en_markers):
        return "en"
    return "fr"


def _language_instruction(query: str) -> str:
    """Explicit response-language hint for external models."""
    language = _detect_language(query)
    if language == "pt":
        return "Réponds strictement en portugais."
    if language == "en":
        return "Respond strictly in English."
    return "Réponds strictement en français."


def _local_greeting_reply(query: str) -> str:
    return LOCAL_GREETING_REPLIES[_detect_language(query)]


def _local_bio_reply(query: str) -> str:
    return LOCAL_BIO_REPLIES[_detect_language(query)]


def _local_out_of_scope_reply(query: str) -> str:
    return OUT_OF_SCOPE_REPLIES[_detect_language(query)]


def _local_dbt_project_reply(query: str) -> str:
    return DBT_PROJECT_REPLIES[_detect_language(query)]


def _is_out_of_scope_personal_query(query: str) -> bool:
    """Detect personal-preference questions that are outside the portfolio knowledge base."""
    normalized = query.strip()
    return any(pattern.search(normalized) for pattern in OUT_OF_SCOPE_PATTERNS)


def _is_dbt_project_query(query: str) -> bool:
    """Detect direct questions about whether Rafael used dbt in his projects."""
    normalized = (query or "").lower()
    if "dbt" not in normalized:
        return False

    project_markers = [
        "project", "projects", "projet", "projets", "utilisant", "utilizando",
        "using", "used", "feito", "fait", "fez", "did", "avec", "com",
    ]
    return any(marker in normalized for marker in project_markers)

def _is_bio_query(query: str) -> bool:
    """Check for direct identity/profile questions without hijacking project questions."""
    normalized = query.strip()
    if any(pattern.search(normalized) for pattern in BIO_PATTERNS):
        return True

    normalized_lower = normalized.lower()
    if any(marker in normalized_lower for marker in ["quem é", "quem e", "quem eh", "who is", "qui est", "sobre", "about"]):
        return bool(re.search(r"\braf[a-z]*\b", normalized_lower))

    return False


def _is_greeting(query: str) -> bool:
    """Fast regex check for greetings."""
    stripped = query.strip()
    return bool(GREETING_PATTERNS.match(stripped)) or any(
        pattern.match(stripped) for pattern in ELONGATED_GREETING_PATTERNS
    )


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
# Retrieval
# ---------------------------------------------------------------------------
def retrieve(query: str) -> list[dict]:
    """Retrieve top-K relevant chunks for a query with API key fallback."""
    try:
        t0 = time.time()

        keys_to_try = _get_gemini_keys()
        if not keys_to_try:
            print("[ERROR] No Gemini API key found for embeddings", flush=True)
            return []

        query_embedding = None
        last_err = None
        
        for idx, embed_key in enumerate(keys_to_try):
            client = None
            try:
                client = _get_gemini_client(embed_key)
                result = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=query,
                    config=types.EmbedContentConfig(
                        httpOptions=_get_gemini_http_options(10.0),
                    ),
                )
                query_embedding = result.embeddings[0].values
                break  # Success
            except Exception as e:
                last_err = e
                if idx == len(keys_to_try) - 1:
                    print(f"[ERROR] Embedding failed for all keys. Last: {e}", flush=True)
            finally:
                if client is not None:
                    client.close()

        if not query_embedding:
            print(f"[ERROR] Retrieval aborted because query embedding could not be created. Last error: {last_err}", flush=True)
            return []

        collection = _get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
        )
        print(f"[PERF] Retrieval took {time.time() - t0:.2f}s | Chunks: {len(results['documents'][0]) if results and results['documents'] else 0}", flush=True)

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
def _build_gemini_contents(query: str, history: list) -> str:
    """Build a plain-text conversation transcript for google.genai."""
    lines = []
    for msg in history or []:
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        role = "User" if msg.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {content}")

    transcript = "\n".join(lines)
    if transcript:
        return f"Conversation history:\n{transcript}\n\nCurrent user question:\n{query}"
    return query


def _build_gemini_system_instruction(query: str, context_chunks: list[dict]) -> str:
    """Build the system instruction with retrieved context and language hint."""
    context_text = "\n\n---\n\n".join(
        [f"[Source: {c['source']}]\n{c['content']}" for c in context_chunks]
    )
    return f"{SYSTEM_PROMPT.format(context=context_text)}\n\n{_language_instruction(query)}"


def _try_gemini(query: str, context_chunks: list[dict], history: list, api_key: str, key_name: str, model_name: str, custom_timeout: float = 10.0) -> dict | None:
    """Try to get an answer from Gemini."""
    client = None
    try:
        t0 = time.time()
        client = _get_gemini_client(api_key)

        response = client.models.generate_content(
            model=model_name,
            contents=_build_gemini_contents(query, history),
            config=types.GenerateContentConfig(
                systemInstruction=_build_gemini_system_instruction(query, context_chunks),
                temperature=0.4,
                maxOutputTokens=2048,
                httpOptions=_get_gemini_http_options(custom_timeout),
            ),
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
    finally:
        if client is not None:
            client.close()


def _try_gemini_greeting(query: str, api_key: str, key_name: str, model_name: str) -> dict | None:
    """Ultra-fast Gemini call for greetings — no RAG context needed."""
    client = None
    try:
        t0 = time.time()
        client = _get_gemini_client(api_key)

        response = client.models.generate_content(
            model=model_name,
            contents=query,
            config=types.GenerateContentConfig(
                systemInstruction=f"{GREETING_PROMPT}\n\n{_language_instruction(query)}",
                temperature=0.3,
                maxOutputTokens=160,
                httpOptions=_get_gemini_http_options(10.0),
            ),
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
    finally:
        if client is not None:
            client.close()


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
    api_key = _get_nvidia_key(api_key_env)
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
        {"role": "system", "content": f"{SYSTEM_PROMPT.format(context=context_text)}\n\n{_language_instruction(query)}"},
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

    if len(history) >= 10 or len(query) > 250:
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
        is_bio = _is_bio_query(query)
        is_out_of_scope = _is_out_of_scope_personal_query(query)

        if category == "greeting":
            return {
                "reply": _local_greeting_reply(query),
                "sources": [],
                "api_used": "local-greeting",
            }

        if is_bio and category != "complex":
            return {
                "reply": _local_bio_reply(query),
                "sources": ["00_rafael_bio.md", "10_rafael_positioning.md"],
                "api_used": "local-bio",
            }

        if _is_dbt_project_query(query):
            return {
                "reply": _local_dbt_project_reply(query),
                "sources": ["05_project_elt.md", "01_competences.md"],
                "api_used": "local-dbt-project",
            }

        if is_out_of_scope:
            return {
                "reply": _local_out_of_scope_reply(query),
                "sources": [],
                "api_used": "local-out-of-scope",
            }

        # Resolve page context
        project_hint = _resolve_page_context(page_context)
        if project_hint:
            print(f"[CONTEXT] Page: {page_context} → Project: {project_hint}", flush=True)

        gemini_keys = _get_gemini_keys()
        key1 = gemini_keys[0] if gemini_keys else None
        key2 = gemini_keys[1] if len(gemini_keys) > 1 else None
        errors = []

        print(f"[ROUTER] Query='{query[:60]}...' Category={category} | BioPath={is_bio}", flush=True)

        # ── RAG retrieval (only for non-bio or complex queries) ──
        context_chunks = []
        if not is_bio or category == "complex":
            context_chunks = retrieve(query)
            if not context_chunks:
                print("[WARNING] RAG retrieved 0 chunks. Proceeding with System Bio context.", flush=True)
                context_chunks = []

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
            # Priority 1: Gemini Lite 3.1 (KEY 1)
            if key1:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key1, "KEY_1", GEMINI_LITE_31, custom_timeout=2.5)
                    if result: return result
                except Exception as e: errors.append(f"G31:{e}")

            # Priority 2: Gemini Lite Latest (KEY 2)
            if key2:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key2, "KEY_2", GEMINI_LITE_LATEST, custom_timeout=2.5)
                    if result: return result
                except Exception as e: errors.append(f"GLatest:{e}")

            # Fallback 3: Kimi (NVIDIA)
            try:
                result = _try_nvidia(query, context_chunks, history_safe, "NVIDIA_API_KEY_1", KIMI_MODEL, "Kimi K2.5")
                if result: return result
            except Exception as e: errors.append(f"Kimi:{e}")

            # Fallback 4: GLM-5 (NVIDIA)
            try:
                result = _try_nvidia(query, context_chunks, history_safe, "NVIDIA_API_KEY_2", GLM_MODEL, "GLM-5")
                if result:
                    return result
            except Exception as e:
                errors.append(f"GLM:{e}")

        # ── NORMAL (standard RAG question) ──
        elif category == "normal":
            # Priority 1: Gemini Lite 3.1
            if key1:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key1, "KEY_1", GEMINI_LITE_31, custom_timeout=3.5)
                    if result: return result
                except Exception as e: errors.append(f"G31:{e}")

            # Priority 2: Kimi K2.5 (Fast-ish complex analysis)
            try:
                result = _try_nvidia(query, context_chunks, history_safe, "NVIDIA_API_KEY_1", KIMI_MODEL, "Kimi K2.5")
                if result: return result
            except Exception as e: errors.append(f"Kimi:{e}")

            # Priority 3: Gemini Normal
            if key1:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key1, "KEY_1_Normal", GEMINI_NORMAL)
                    if result: return result
                except Exception as e: errors.append(f"GNormal:{e}")

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
            "reply": "All APIs are temporarily unavailable. Please try again later. / Toutes les APIs sont temporairement indisponibles. Veuillez réessayer plus tard.",
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
