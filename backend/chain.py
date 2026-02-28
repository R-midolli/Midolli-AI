"""
Midolli-AI — RAG Chain
Retrieval and answer generation with 3-API fallback:
  Gemini KEY_1 → Gemini KEY_2 → NVIDIA LLaMA-3.1-70B
"""

import os
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
GEMINI_MODEL = "gemini-1.5-flash"
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"
TOP_K = 5

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


def _get_collection():
    """Get the ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))
    return client.get_collection(name=COLLECTION_NAME)


def retrieve(query: str) -> list[dict]:
    """Retrieve top-K relevant chunks for a query."""
    try:
        # Configure Gemini for embedding
        api_key = os.getenv("GEMINI_API_KEY_1") or os.getenv("GEMINI_API_KEY_2")
        if not api_key:
            return []
        genai.configure(api_key=api_key)

        # Embed the query
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
        )
        query_embedding = result["embedding"]

        # Query ChromaDB
        collection = _get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
        )

        # Format results
        chunks = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                source = ""
                if results["metadatas"] and results["metadatas"][0]:
                    source = results["metadatas"][0][i].get("source", "")
                chunks.append({"content": doc, "source": source})

        return chunks
    except Exception as e:
        print(f"[ERROR] Retrieval failed: {e}")
        return []


def _build_prompt(query: str, context_chunks: list[dict], history: list) -> list[dict]:
    """Build the chat messages for the LLM."""
    context_text = "\n\n---\n\n".join(
        [f"[Source: {c['source']}]\n{c['content']}" for c in context_chunks]
    )

    messages = [
        {"role": "user", "parts": [SYSTEM_PROMPT.format(context=context_text)]},
        {"role": "model", "parts": ["Understood. I will answer based only on the provided context, in the user's language."]},
    ]

    # Add conversation history
    for msg in (history or []):
        role = "user" if msg.get("role") == "user" else "model"
        messages.append({"role": role, "parts": [msg.get("content", "")]})

    # Add the current question
    messages.append({"role": "user", "parts": [query]})

    return messages


def _try_gemini(query: str, context_chunks: list[dict], history: list, api_key: str, key_name: str) -> dict | None:
    """Try to get an answer from Gemini."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)

        messages = _build_prompt(query, context_chunks, history)
        response = model.generate_content(messages)

        if response and response.text:
            sources = list(set(c["source"] for c in context_chunks if c["source"]))
            return {
                "reply": response.text,
                "sources": sources,
                "api_used": f"Gemini ({key_name})",
            }
    except Exception as e:
        print(f"[WARNING] Gemini {key_name} failed: {e}")
    return None


def _try_nvidia(query: str, context_chunks: list[dict], history: list) -> dict | None:
    """Try to get an answer from NVIDIA LLaMA-3.1-70B."""
    try:
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_key:
            return None

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_key,
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

        if response and response.choices:
            reply = response.choices[0].message.content
            sources = list(set(c["source"] for c in context_chunks if c["source"]))
            return {
                "reply": reply,
                "sources": sources,
                "api_used": "NVIDIA LLaMA-3.1-70B",
            }
    except Exception as e:
        print(f"[WARNING] NVIDIA failed: {e}")
    return None


def answer(query: str, history: list | None = None) -> dict:
    """
    Answer a query using RAG with 3-API fallback.
    Returns: {"reply": str, "sources": list[str], "api_used": str}
    Never raises exceptions to the caller.
    """
    if not query or not query.strip():
        return {
            "reply": "Please provide a question. / Veuillez poser une question.",
            "sources": [],
            "api_used": "none",
        }

    try:
        # Step 1: Retrieve relevant chunks
        context_chunks = retrieve(query)
        if not context_chunks:
            return {
                "reply": "I could not find relevant information in my knowledge base. / Je n'ai pas trouvé d'information pertinente dans ma base de connaissances.",
                "sources": [],
                "api_used": "none",
            }

        # Step 2: Try Gemini KEY_1
        key1 = os.getenv("GEMINI_API_KEY_1")
        if key1:
            result = _try_gemini(query, context_chunks, history, key1, "KEY_1")
            if result:
                return result

        # Step 3: Try Gemini KEY_2
        key2 = os.getenv("GEMINI_API_KEY_2")
        if key2:
            result = _try_gemini(query, context_chunks, history, key2, "KEY_2")
            if result:
                return result

        # Step 4: Try NVIDIA fallback
        result = _try_nvidia(query, context_chunks, history)
        if result:
            return result

        # All APIs failed
        return {
            "reply": "All APIs are temporarily unavailable. Please try again later. / Toutes les APIs sont temporairement indisponibles. Veuillez réessayer plus tard.",
            "sources": [],
            "api_used": "none",
        }

    except Exception as e:
        print(f"[ERROR] answer() failed: {e}")
        return {
            "reply": "An unexpected error occurred. Please try again. / Une erreur inattendue s'est produite. Veuillez réessayer.",
            "sources": [],
            "api_used": "none",
        }
