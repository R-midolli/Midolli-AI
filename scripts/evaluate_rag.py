"""
Automated RAG Evaluation Pipeline (LLM-as-a-Judge)
Tests the Midolli-AI RAG system against a ground-truth dataset.
"""

import csv
import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

import sys
sys.path.append(str(Path(__file__).parent.parent))
from backend.chain import answer

load_dotenv()

DATASET_PATH = Path(__file__).parent.parent / "tests" / "qa_dataset.csv"
REPORT_DIR = Path(__file__).parent.parent / "reports"
REPORT_PATH = REPORT_DIR / "rag_evaluation_results.csv"


def _get_eval_client() -> genai.Client:
    api_key = (
        os.getenv("GEMINI_API_KEY_1")
        or os.getenv("GOOGLE_API_KEY_1")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    return genai.Client(api_key=api_key)

EVAL_PROMPT = """You are an impartial AI judge. Evaluate the RAG system's generated answer against the ground truth Expected Answer.
Ignore formatting or language differences as long as the factual core is identical and correct.

EXPECTED ANSWER: {expected}
GENERATED ANSWER: {generated}

Score the generated answer on a scale of 1 to 5:
5: Perfect. Contains all facts from expected, no hallucinations.
4: Minor omissions, but core facts are correct.
3: Partially correct, some minor hallucinations or missing key facts.
2: Mostly incorrect or hallucinated.
1: Completely wrong.

Output ONLY a raw JSON object with no markdown fences, exactly like this:
{{"score": 5, "reasoning": "Explanation here"}}
"""

def evaluate():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not DATASET_PATH.exists():
        print(f"[ERROR] Dataset not found at {DATASET_PATH}")
        return

    results = []
    
    print("=" * 60)
    print("Midolli-AI — RAG QA Evaluation Pipeline")
    print("=" * 60)
    
    with open(DATASET_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        questions = list(reader)

    eval_client = _get_eval_client()

    total_score = 0
    
    for row in questions:
        q_id = row["question_id"]
        q_text = row["question"]
        expected = row["expected_answer"]
        category = row["category"]
        
        print(f"\n[Q{q_id}] {category.upper()}: {q_text}")
        
        # 1. Call RAG system directly
        print("  -> Querying RAG (Midolli-AI)...")
        rag_response = answer(q_text, [])
        generated = rag_response["reply"]
        api_used = rag_response["api_used"]
        print(f"  -> RAG Answer ({api_used[:15]}...): {generated[:100]}...")
        
        # 2. Call Evaluator LLM
        prompt = EVAL_PROMPT.format(expected=expected, generated=generated)
        try:
            eval_res = eval_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    maxOutputTokens=256,
                    httpOptions=types.HttpOptions(timeout=10000),
                ),
            )
            # Clean possible markdown from response
            raw_text = eval_res.text.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
            eval_json = json.loads(raw_text)
            score = eval_json.get("score", 1)
            reasoning = eval_json.get("reasoning", "Parse error")
        except Exception as e:
            print(f"  [ERROR] Eval failed: {e}")
            score = 1
            reasoning = f"Evaluation LLM failed: {e}"
            
        print(f"  -> JUDGE SCORE: {score}/5")
        print(f"  -> REASONING: {reasoning}")
        
        total_score += score
        results.append({
            "question_id": q_id,
            "category": category,
            "question": q_text,
            "expected": expected,
            "generated": generated,
            "score": score,
            "reasoning": reasoning,
            "api_used": api_used
        })
        
        # Rate limit between questions
        time.sleep(2)
        
    avg_score = total_score / len(questions)
    print("\n" + "=" * 60)
    print(f"EVALUATION COMPLETE. Average Accuracy: {avg_score:.1f} / 5.0")
    print("=" * 60)
    
    # Save report
    with open(REPORT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "question_id", "category", "question", "expected", "generated", "score", "reasoning", "api_used"
        ])
        writer.writeheader()
        writer.writerows(results)

    eval_client.close()
    
    print(f"Detailed report saved to {REPORT_PATH}")

if __name__ == "__main__":
    evaluate()
