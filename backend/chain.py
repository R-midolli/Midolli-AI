"""
Midolli-AI — RAG Chain (v2 — Optimized 2026)
3-tier intelligent LLM routing with greeting detection,
singleton ChromaDB client, and API timeouts.
"""

import os
import re
import time
from pathlib import Path

import chromadb
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VECTORSTORE_DIR = Path(__file__).parent / "data" / "vectorstore"
COLLECTION_NAME = "midolli_knowledge"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# LLM Models — 3 tiers
GEMINI_FAST = "gemini-flash-lite-latest"       # Tier 1: greetings & short Q
GEMINI_NORMAL = "gemini-3-flash-preview"       # Tier 2: standard RAG Q
GEMINI_BACKUP = "gemini-2.5-flash"             # Tier 2 fallback
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"   # Tier 3: deep reasoning

TOP_K = 8

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are Midolli-AI, the intelligent assistant for Rafael Midolli's data portfolio.

RULES:
1. Detect the language of the user's question (French or English) and respond in the SAME language.
2. Answer ONLY based on the context provided below. Never invent information.
3. Be concise: maximum 3 paragraphs.
4. Use markdown formatting when mentioning technologies, code, or stack.
5. If the answer is not in the context, say clearly: "I don't have this information in my knowledge base." / "Je n'ai pas cette information dans ma base de connaissances."
6. Never mention that you are reading from "chunks" or a "vector database". Speak naturally as if you know Rafael personally.
7. Be professional, friendly, and focus on facts with real numbers when available.
8. If the retrieved context does not clearly answer the question, respond with: "Je ne dispose pas d'informations précises sur ce point. Pour plus de détails, consultez le portfolio de Rafael : https://r-midolli.github.io/portfolio_rafael_midolli/" Never guess. Never complete missing information from your training data.

CONTEXT:
{context}
"""

GREETING_PROMPT = """You are Midolli-AI, the intelligent assistant for Rafael Midolli's data portfolio.
You are speaking with a visitor on Rafael's portfolio website.

RULES:
1. Detect the language of the user's message and respond in the SAME language.
2. Keep your reply under 2 sentences.
3. Be warm, professional, and invite the user to ask about Rafael's projects, skills, or experience.
4. Never invent information about Rafael.

CONTEXT SUMMARY:
Rafael Midolli is a Business Data Analyst specialized in Retail/FMCG, based in France.
He has projects in: Retail BA Diagnostic, ELT Analytics, Supply Chain Analytics, FMCG Pricing Monitor, Customer Churn Prediction, and this very chatbot (Midolli-AI).
He speaks Portuguese (native), French (C1), English (B2), and Spanish (A2).
He is available for CDI & freelance in 2026.
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
    """Retrieve top-K relevant chunks for a query."""
    try:
        _ensure_gemini_configured()

        t0 = time.time()
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
        )
        query_embedding = result["embedding"]

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

    for msg in (history or []):
        role = "user" if msg.get("role") == "user" else "model"
        messages.append({"role": role, "parts": [msg.get("content", "")]})

    messages.append({"role": "user", "parts": [query]})
    return messages


def _try_gemini(query: str, context_chunks: list[dict], history: list, api_key: str, key_name: str, model_name: str) -> dict | None:
    """Try to get an answer from Gemini."""
    try:
        t0 = time.time()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        messages = _build_gemini_messages(query, context_chunks, history)
        response = model.generate_content(
            messages,
            request_options={"timeout": 25},
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
            request_options={"timeout": 10},
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


def _try_nvidia(query: str, context_chunks: list[dict], history: list) -> dict | None:
    """Try to get an answer from NVIDIA Build."""
    try:
        t0 = time.time()
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_key:
            raise Exception("NVIDIA_API_KEY not found in environment")

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_key,
            timeout=30.0,
        )

        context_text = "\n\n---\n\n".join(
            [f"[Source: {c['source']}]\n{c['content']}" for c in context_chunks]
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(context=context_text)},
        ]

        for msg in (history or []):
            role = msg.get("role", "user")
            messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": query})

        response = client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        elapsed = time.time() - t0
        print(f"[PERF] NVIDIA responded in {elapsed:.2f}s", flush=True)

        if response and response.choices:
            reply = response.choices[0].message.content
            sources = list(set(c["source"] for c in context_chunks if c["source"]))
            return {
                "reply": reply,
                "sources": sources,
                "api_used": f"NVIDIA ({NVIDIA_MODEL})",
            }
    except Exception as e:
        print(f"[WARNING] NVIDIA failed: {e}", flush=True)
        raise Exception(f"NVIDIA failed: {e}")


# ---------------------------------------------------------------------------
# Query Classifier
# ---------------------------------------------------------------------------
def _query_category(query: str, history: list) -> str:
    """Classify query into simple / normal / complex."""
    if _is_greeting(query):
        return "greeting"

    if len(history) >= 4 or len(query) > 200:
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

    if len(query) < 60 and len(history) <= 2:
        return "simple"

    return "normal"


# ---------------------------------------------------------------------------
# Main Answer Function
# ---------------------------------------------------------------------------
def answer(query: str, history: list | None = None) -> dict:
    """
    Answer a query using intelligent 3-tier LLM routing.
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

        # ── SIMPLE (short factual Q) ──
        if category == "simple":
            # Tier 1: Gemini Flash Lite (cheapest, fastest)
            if key2:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key2, "KEY_2", GEMINI_FAST)
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

        # ── NORMAL (standard RAG question) ──
        elif category == "normal":
            # Tier 2: Gemini 3 Flash Preview
            if key1:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key1, "KEY_1", GEMINI_NORMAL)
                    if result:
                        print(f"[PERF] Total normal time: {time.time() - t0_total:.2f}s", flush=True)
                        return result
                except Exception as e:
                    errors.append(f"G1:{e}")

            # Fallback to Flash Lite
            if key2:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key2, "KEY_2", GEMINI_FAST)
                    if result:
                        return result
                except Exception as e:
                    errors.append(f"G2:{e}")

            # Last resort: NVIDIA
            try:
                result = _try_nvidia(query, context_chunks, history_safe)
                if result:
                    return result
            except Exception as e:
                errors.append(f"NV:{e}")

        # ── COMPLEX (deep reasoning) ──
        else:
            # Tier 3: NVIDIA 70B first
            try:
                result = _try_nvidia(query, context_chunks, history_safe)
                if result:
                    print(f"[PERF] Total complex time: {time.time() - t0_total:.2f}s", flush=True)
                    return result
            except Exception as e:
                errors.append(f"NV:{e}")

            # Fallback to Gemini Normal
            if key1:
                try:
                    result = _try_gemini(query, context_chunks, history_safe, key1, "KEY_1", GEMINI_NORMAL)
                    if result:
                        return result
                except Exception as e:
                    errors.append(f"G1:{e}")

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
