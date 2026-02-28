"""
Midolli-AI — FastAPI Application
GET  /health → status check
POST /chat   → RAG chatbot endpoint
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.chain import answer

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Midolli-AI",
    description="RAG chatbot for Rafael Midolli's data portfolio",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://r-midolli.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    history: list = []
    lang: str = "fr"


class ChatResponse(BaseModel):
    reply: str
    sources: list[str] = []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "Midolli-AI"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint — sends question to RAG chain."""
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty. / Le message ne peut pas être vide.",
        )

    result = answer(query=request.message, history=request.history)

    return ChatResponse(
        reply=result["reply"],
        sources=result.get("sources", []),
    )
