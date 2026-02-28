"""
Midolli-AI — Ingest pipeline
Reads .md knowledge files + CV PDF, chunks them,
embeds with Gemini text-embedding-004, and upserts to ChromaDB.
"""

import hashlib
import os
import time
from pathlib import Path

import chromadb
import fitz  # pymupdf
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (Super RAG 2026)
# ---------------------------------------------------------------------------
KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
PROJECT_ROOT = Path(__file__).parent.parent
AGENT_SOURCES_DIR = PROJECT_ROOT / ".agent" / "sources"
WORKSPACE_DIR = PROJECT_ROOT.parent

CV_PDF_PATH = AGENT_SOURCES_DIR / "CV_Rafael_Midolli_2026.pdf"
VECTORSTORE_DIR = Path(__file__).parent / "data" / "vectorstore"
COLLECTION_NAME = "midolli_knowledge"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
BATCH_SIZE = 50
EMBEDDING_MODEL = "models/gemini-embedding-001"


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract all text from a PDF file using pymupdf."""
    if not pdf_path.exists():
        print(f"[WARNING] CV PDF not found at {pdf_path}")
        return ""
    doc = fitz.open(str(pdf_path))
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def read_knowledge_files() -> list[dict]:
    """Read .md from knowledge/, personal profile from .agent/, and workspace READMEs."""
    documents = []
    
    # 1. Base knowledge files
    if KNOWLEDGE_DIR.exists():
        for md_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            documents.append({"source": md_file.name, "content": content})
            print(f"  [OK] Read {md_file.name} ({len(content)} chars)")
            
    # 2. Personal profiles from .agent/sources
    personal_files = ["profil_complet_utilisateur.md", "SOURCES_INDEX.md", "linkedin_profile.md"]
    for pf in personal_files:
        pf_path = AGENT_SOURCES_DIR / pf
        if pf_path.exists():
            content = pf_path.read_text(encoding="utf-8")
            documents.append({"source": pf, "content": content})
            print(f"  [OK] Read personal profile {pf} ({len(content)} chars)")

    # 3. Workspace Projects READMEs
    projects = [
        "retail-ba-diagnostic",
        "ELT_retail_analytics",
        "supply_chain_analytics",
        "fmcg_pricing_macro_monitor",
        "Customer Churn Prediction & Reactivation Propensity",
        "Midolli-AI",
    ]
    
    print("\n[Step 1.5] Reading specific workspace project READMEs...")
    for project_name in projects:
        readme_path = WORKSPACE_DIR / project_name / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            source_name = f"{project_name}/README.md"
            documents.append({"source": source_name, "content": content})
            print(f"  [OK] Read {source_name} ({len(content)} chars)")
        else:
            print(f"  [WARNING] Could not find README for {project_name}")

    return documents


def chunk_text(text: str, source: str) -> list[dict]:
    """Split text into chunks of ~CHUNK_SIZE chars with CHUNK_OVERLAP overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_content = text[start:end]
        if chunk_content.strip():
            chunk_id = hashlib.md5(f"{source}_{len(chunks)}".encode()).hexdigest()
            chunks.append({
                "id": chunk_id,
                "content": chunk_content.strip(),
                "source": source,
                "chunk_index": len(chunks),
            })
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using Gemini text-embedding-004."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=texts,
    )
    return result["embedding"]


def run_ingest():
    """Main ingest pipeline."""
    print("=" * 60)
    print("Midolli-AI — Ingest Pipeline")
    print("=" * 60)

    # Configure Gemini API
    api_key = os.getenv("GEMINI_API_KEY_1")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY_1 not found in .env")
        return
    genai.configure(api_key=api_key)

    # Step 1: Read knowledge files
    print("\n[Step 1] Reading knowledge files...")
    documents = read_knowledge_files()
    print(f"  Total documents: {len(documents)}")

    # Step 2: Extract CV PDF text
    print("\n[Step 2] Extracting CV PDF text...")
    cv_text = extract_pdf_text(CV_PDF_PATH)
    if cv_text:
        documents.append({
            "source": "CV_Rafael_Midolli_2026.pdf",
            "content": cv_text,
        })
        print(f"  [OK] CV PDF extracted ({len(cv_text)} chars)")
    else:
        print("  [SKIP] CV PDF not found or empty")

    # Step 3: Chunk all documents
    print("\n[Step 3] Chunking documents...")
    all_chunks = []
    for doc in documents:
        chunks = chunk_text(doc["content"], doc["source"])
        all_chunks.extend(chunks)
        print(f"  {doc['source']}: {len(chunks)} chunks")
    print(f"  Total chunks: {len(all_chunks)}")

    if not all_chunks:
        print("[ERROR] No chunks to ingest")
        return

    # Step 4: Initialize ChromaDB
    print("\n[Step 4] Initializing ChromaDB...")
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"  Collection '{COLLECTION_NAME}' ready")

    # Step 5: Embed and upsert in batches
    print("\n[Step 5] Embedding and upserting...")
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i : i + BATCH_SIZE]
        batch_texts = [c["content"] for c in batch]
        batch_ids = [c["id"] for c in batch]
        batch_sources = [c["source"] for c in batch]
        batch_indices = [str(c["chunk_index"]) for c in batch]

        try:
            embeddings = embed_batch(batch_texts)
            collection.upsert(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_texts,
                metadatas=[
                    {"source": src, "chunk_index": idx}
                    for src, idx in zip(batch_sources, batch_indices)
                ],
            )
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(all_chunks) + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"  Batch {batch_num}/{total_batches}: {len(batch)} chunks upserted")
        except Exception as e:
            print(f"  [ERROR] Batch {i // BATCH_SIZE + 1} failed: {e}")
            time.sleep(2)
            continue

        # Rate limit: small pause between batches
        if i + BATCH_SIZE < len(all_chunks):
            time.sleep(1)

    # Final summary
    final_count = collection.count()
    print("\n" + "=" * 60)
    print(f"Ingest complete! Total chunks in collection: {final_count}")
    print("=" * 60)


if __name__ == "__main__":
    run_ingest()
