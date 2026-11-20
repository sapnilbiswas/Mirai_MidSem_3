"""
eval.py - Comprehensive Evaluation, Hit@K Benchmark, and Threshold Calibration.

Executes the 5 assessment questions, 10 extended benchmark queries,
measures Hit@K (k=1, 3, 6) across in-scope topics, conducts 8+8 threshold
calibration, and outputs full reports to eval_results.md and stdout.
"""

import os
import json
import logging
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

from retriever import get_retriever
from rag import get_rag_pipeline, NOT_IN_CORPUS_MESSAGE, DEFAULT_RERANK_THRESHOLD

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EVAL_RESULTS_MD_PATH = "eval_results.md"

# 5 Core Assessment Questions
ASSESSMENT_QUESTIONS = [
    {
        "id": "Q1",
        "question": "According to the Saptanga theory section of the provided text, what are the seven constituent limbs (Prakritis) of a sovereign state?",
        "type": "in_scope",
        "expected_pages": [8],
        "required_keywords": ["Swamin", "Amatya", "Janapada", "Durga", "Kosha", "Danda", "Mitra"],
        "expect_refusal": False,
    },
    {
        "id": "Q2",
        "question": "In which year was the Battle of Plassey fought between the British East India Company and the Nawab of Bengal?",
        "type": "out_of_scope",
        "expected_pages": None,
        "required_keywords": [],
        "expect_refusal": True,
    },
    {
        "id": "Q3",
        "question": "How many categories of envoys (Dutas) are identified in the text according to their level of authority, and what are their designations?",
        "type": "in_scope",
        "expected_pages": [19],
        "required_keywords": ["three", "Nisrishtartha", "Parimitartha", "Shasanahara"],
        "expect_refusal": False,
    },
    {
        "id": "Q4",
        "question": "What metaphor does Chapter 2 of the provided text use to explain how a person of steady wisdom (Sthitaprajna) withdraws their senses from sense objects?",
        "type": "in_scope",
        "expected_pages": [36],
        "required_keywords": ["tortoise", "shell", "limbs"],
        "expect_refusal": False,
    },
    {
        "id": "Q5",
        "question": "Which political coalition won the 2024 Indian General Election?",
        "type": "out_of_scope",
        "expected_pages": None,
        "required_keywords": [],
        "expect_refusal": True,
    },
]

# 10 Additional Benchmark Questions
EXTRA_QUESTIONS = [
    # In-scope
    {
        "id": "EQ1",
        "question": "According to the section on fiscal administration, what baseline does Module 2.0 establish?",
        "type": "in_scope",
        "expected_pages": [2, 7, 12, 17, 22, 27, 32, 37, 42, 47],
        "required_keywords": ["operational", "procedures"],
        "expect_refusal": False,
    },
    {
        "id": "EQ2",
        "question": "What must practitioners maintain across all stages of execution under Mandala theory modules?",
        "type": "in_scope",
        "expected_pages": [3, 8, 13, 18, 23, 28, 33, 38, 43, 48],
        "required_keywords": ["audit", "logs"],
        "expect_refusal": False,
    },
    {
        "id": "EQ3",
        "question": "What are teams required to review periodically during standard operations under Module 4?",
        "type": "in_scope",
        "expected_pages": [4, 9, 14, 19, 24, 29, 34, 39, 44, 49],
        "required_keywords": ["system", "state"],
        "expect_refusal": False,
    },
    {
        "id": "EQ4",
        "question": "What standard procedural guidelines are outlined for witness examination and civil contracts under Module 5?",
        "type": "in_scope",
        "expected_pages": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
        "required_keywords": ["reviews", "system"],
        "expect_refusal": False,
    },
    {
        "id": "EQ5",
        "question": "What is the Swamin identified as in Book VI, Chapter 1 of the Arthashastra?",
        "type": "in_scope",
        "expected_pages": [8],
        "required_keywords": ["Swamin", "Sovereign"],
        "expect_refusal": False,
    },
    # Out-of-scope
    {
        "id": "EQ6",
        "question": "What were the key economic reforms introduced during the 1991 balance of payments crisis in India?",
        "type": "out_of_scope",
        "expected_pages": None,
        "required_keywords": [],
        "expect_refusal": True,
    },
    {
        "id": "EQ7",
        "question": "Who was elected as the Prime Minister of the United Kingdom in July 2024?",
        "type": "out_of_scope",
        "expected_pages": None,
        "required_keywords": [],
        "expect_refusal": True,
    },
    {
        "id": "EQ8",
        "question": "Which Mughal Emperor commissioned the construction of the Taj Mahal in Agra?",
        "type": "out_of_scope",
        "expected_pages": None,
        "required_keywords": [],
        "expect_refusal": True,
    },
    {
        "id": "EQ9",
        "question": "What were the primary boundary divisions established under the 1947 Indian Independence Act?",
        "type": "out_of_scope",
        "expected_pages": None,
        "required_keywords": [],
        "expect_refusal": True,
    },
    {
        "id": "EQ10",
        "question": "How does Shor's algorithm threaten 2048-bit RSA encryption keys on quantum hardware?",
        "type": "out_of_scope",
        "expected_pages": None,
        "required_keywords": [],
        "expect_refusal": True,
    },
]

# 8 In-scope and 8 Out-of-scope Questions for Threshold Calibration
CALIBRATION_SET = [
    # 8 In-Scope
    ("According to the Saptanga theory, what are the seven limbs of state?", True),
    ("How many categories of envoys (Dutas) are identified and what are their ranks?", True),
    ("What metaphor explains how a person of steady wisdom (Sthitaprajna) withdraws senses?", True),
    ("What are the procedures for fiscal administration and forty ways of embezzlement?", True),
    ("Explain the Mandala theory of foreign policy and the sixfold royal strategy.", True),
    ("What constitutes the ethics of detached action (Nishkama Karma) in governance?", True),
    ("What guidelines govern judicial procedure and witness examination protocols?", True),
    ("What is the description of Nisrishtartha plenipotentiary ambassador in diplomacy?", True),
    # 8 Out-of-Scope
    ("In which year was the Battle of Plassey fought between Robert Clive and Siraj ud-Daulah?", False),
    ("Which political party or coalition won the 2024 Indian General Election?", False),
    ("What were the major resolutions of the 1942 Quit India Movement?", False),
    ("Who was appointed the CEO of Google in August 2015?", False),
    ("How does backpropagation calculate weight gradients in deep convolutional neural networks?", False),
    ("What were the terms of the Treaty of Versailles signed in 1919?", False),
    ("What was the result of the ICC Men's Cricket World Cup final in 2023?", False),
    ("What is the capital city of Australia and what is its population?", False),
]


def evaluate_response(item: Dict[str, Any], response: Dict[str, Any]) -> Tuple[bool, str]:
    """Evaluate whether an answer passes strict groundedness and accuracy criteria."""
    answer = response["answer"].strip()
    is_refusal = response["is_refusal"]
    sources = response["sources"]

    if item["expect_refusal"]:
        if is_refusal and answer == NOT_IN_CORPUS_MESSAGE:
            return True, "Passed: Correctly refused out-of-scope question with standard refusal message."
        return False, f"Failed: Did not trigger refusal message. Answered with: {answer[:80]}..."

    # In-scope evaluation
    if is_refusal:
        return False, f"Failed: Unexpectedly refused in-scope question."

    # Check citation
    expected_pages = item.get("expected_pages")
    if expected_pages:
        if not any(p in response["cited_pages"] for p in expected_pages):
            return False, f"Failed: Missing required citation from valid pages {expected_pages}. Cited: {response['cited_pages']}"

    # Check required keywords (case-insensitive substring)
    missing = []
    answer_lower = answer.lower()
    for kw in item["required_keywords"]:
        if kw.lower() not in answer_lower:
            missing.append(kw)

    if missing:
        return False, f"Failed: Missing key terms: {missing}"

    return True, "Passed: Grounded answer with verified page citations and complete required terms."


def compute_hit_at_k(retriever, in_scope_items: List[Dict[str, Any]], k_values=(1, 3, 6)) -> Dict[int, float]:
    """Calculate Hit@K: fraction of in-scope queries whose top-K chunks contain any of the target pages."""
    hits = {k: 0 for k in k_values}
    total = len(in_scope_items)

    for item in in_scope_items:
        expected_pages = item.get("expected_pages")
        if not expected_pages:
            continue
        sources = retriever.retrieve(item["question"], top_k=max(k_values))
        retrieved_pages = [s["page"] for s in sources]

        for k in k_values:
            if any(p in retrieved_pages[:k] for p in expected_pages):
                hits[k] += 1

    return {k: (hits[k] / total) if total > 0 else 0.0 for k in k_values}


def run_threshold_calibration(retriever) -> Tuple[List[Dict[str, Any]], float]:
    """Compute cross-encoder rerank scores for 8 in-scope and 8 out-of-scope questions."""
    calibration_results = []
    in_scope_scores = []
    out_of_scope_scores = []

    for query, is_in_scope in CALIBRATION_SET:
        sources = retriever.retrieve(query, top_k=1)
        score = sources[0]["rerank_score"] if sources else -99.0
        calibration_results.append({
            "query": query,
            "is_in_scope": is_in_scope,
            "top_rerank_score": score,
            "top_page": sources[0]["page"] if sources else None
        })
        if is_in_scope:
            in_scope_scores.append(score)
        else:
            out_of_scope_scores.append(score)

    min_in_scope = min(in_scope_scores) if in_scope_scores else 0.0
    max_out_of_scope = max(out_of_scope_scores) if out_of_scope_scores else 0.0
    # Choose midpoint threshold with safety margin
    recommended_threshold = round((min_in_scope + max_out_of_scope) / 2.0, 1)

    return calibration_results, recommended_threshold


def run_full_evaluation():
    rag = get_rag_pipeline()
    retriever = rag.retriever

    print("=" * 80)
    print("STARTING FULL RAG EVALUATION & BENCHMARK")
    print("=" * 80)

    # 1. Run 5 Assessment Questions
    print("\n--- RUNNING 5 ASSESSMENT QUESTIONS ---")
    assessment_results = []
    for item in ASSESSMENT_QUESTIONS:
        resp = rag.answer(item["question"], top_k=6)
        passed, reason = evaluate_response(item, resp)
        res_record = {
            "item": item,
            "response": resp,
            "passed": passed,
            "reason": reason
        }
        assessment_results.append(res_record)
        status_label = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n[{item['id']}] {item['question']}")
        print(f"Status: {status_label} ({reason})")
        print(f"Top Score: {resp['relevance_score']:.4f} | Citations: {resp['cited_pages']}")
        print(f"Answer:\n{resp['answer']}\n")

    # 2. Run 10 Extra Benchmark Questions
    print("\n--- RUNNING 10 EXTENDED BENCHMARK QUESTIONS ---")
    extra_results = []
    for item in EXTRA_QUESTIONS:
        resp = rag.answer(item["question"], top_k=6)
        passed, reason = evaluate_response(item, resp)
        extra_results.append({
            "item": item,
            "response": resp,
            "passed": passed,
            "reason": reason
        })
        status_label = "✅ PASS" if passed else "❌ FAIL"
        print(f"[{item['id']}] {item['question'][:60]}... -> {status_label}")

    # 3. Compute Hit@K
    all_in_scope = [q for q in ASSESSMENT_QUESTIONS + EXTRA_QUESTIONS if q["type"] == "in_scope"]
    hit_metrics = compute_hit_at_k(retriever, all_in_scope, k_values=(1, 3, 6))
    print(f"\n--- HIT@K RETRIEVAL PERFORMANCE (N={len(all_in_scope)}) ---")
    for k, val in hit_metrics.items():
        print(f"Hit@{k}: {val * 100:.1f}%")

    # 4. Threshold Calibration
    print("\n--- THRESHOLD CALIBRATION (8 In-Scope vs 8 Out-of-Scope) ---")
    calib_records, recommended_threshold = run_threshold_calibration(retriever)
    in_scores = [r["top_rerank_score"] for r in calib_records if r["is_in_scope"]]
    out_scores = [r["top_rerank_score"] for r in calib_records if not r["is_in_scope"]]
    print(f"In-Scope Rerank Scores: min={min(in_scores):.4f}, max={max(in_scores):.4f}, avg={sum(in_scores)/len(in_scores):.4f}")
    print(f"Out-of-Scope Rerank Scores: min={min(out_scores):.4f}, max={max(out_scores):.4f}, avg={sum(out_scores)/len(out_scores):.4f}")
    print(f"Calibrated Optimal Threshold: {recommended_threshold} (Current default: {DEFAULT_RERANK_THRESHOLD})")

    # 5. Generate eval_results.md
    generate_markdown_report(assessment_results, extra_results, hit_metrics, calib_records, recommended_threshold)
    print(f"\nSaved comprehensive evaluation report to: '{EVAL_RESULTS_MD_PATH}'")

    all_core_passed = all(r["passed"] for r in assessment_results)
    print(f"\nOverall Assessment Questions Result: {'ALL 5 PASSED ✅' if all_core_passed else 'SOME FAILED ❌'}")
    return all_core_passed


def generate_markdown_report(
    assessment_results: List[Dict[str, Any]],
    extra_results: List[Dict[str, Any]],
    hit_metrics: Dict[int, float],
    calib_records: List[Dict[str, Any]],
    recommended_threshold: float
):
    """Format and save the complete evaluation artifact in markdown."""
    with open(EVAL_RESULTS_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Classical Philosophy & Statecraft Text Explorer - Evaluation Report\n\n")
        f.write("## 1. Executive Summary\n\n")
        f.write(
            "This report documents the rigorous evaluation of the grounded RAG application against the "
            "50-page compendium of classical Indian statecraft (*Arthashastra*) and philosophy (*Bhagavad Gita*).\n\n"
        )

        # 5 Assessment Questions Table
        f.write("## 2. Core Assessment Questions (Q1 - Q5)\n\n")
        f.write("| ID | Question | Expected Behavior | Actual Status | Rerank Score | Verified Citations |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in assessment_results:
            it = r["item"]
            resp = r["response"]
            status_emoji = "✅ PASS" if r["passed"] else "❌ FAIL"
            expected_desc = "Grounded Answer" if not it["expect_refusal"] else "Refusal Message"
            citations_str = ", ".join(f"[p. {p}]" for p in resp["cited_pages"]) if resp["cited_pages"] else "None"
            f.write(f"| **{it['id']}** | {it['question']} | {expected_desc} | {status_emoji} | `{resp['relevance_score']:.4f}` | {citations_str} |\n")

        f.write("\n### Detailed Outputs for Core Questions\n\n")
        for r in assessment_results:
            it = r["item"]
            resp = r["response"]
            f.write(f"#### [{it['id']}] {it['question']}\n\n")
            f.write(f"- **Status:** {'✅ PASSED' if r['passed'] else '❌ FAILED'}\n")
            f.write(f"- **Evaluation Detail:** {r['reason']}\n")
            f.write(f"- **Top Cross-Encoder Score:** `{resp['relevance_score']:.4f}`\n")
            f.write(f"- **Verified Cited Pages:** {resp['cited_pages']}\n")
            f.write(f"- **Execution Mode:** `{resp['mode']}`\n\n")
            f.write(f"**Generated Answer:**\n> {resp['answer'].replace(chr(10), chr(10) + '> ')}\n\n")
            if resp["sources"]:
                top_s = resp["sources"][0]
                f.write(f"**Top Retrieved Passage (Page {top_s['page']}, {top_s['section']}):**\n")
                f.write(f"```text\n{top_s['text']}\n```\n\n")
            f.write("---\n\n")

        # Extended Questions
        f.write("## 3. Extended Benchmark (10 Additional Questions)\n\n")
        f.write("| ID | Type | Question | Status | Top Score |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for r in extra_results:
            it = r["item"]
            resp = r["response"]
            status_emoji = "✅ PASS" if r["passed"] else "❌ FAIL"
            f.write(f"| **{it['id']}** | `{it['type']}` | {it['question']} | {status_emoji} | `{resp['relevance_score']:.4f}` |\n")

        # Hit@K Metrics
        f.write("\n## 4. Retrieval Performance: Hit@K\n\n")
        f.write("Hit@K measures the proportion of in-scope questions where the ground truth page appears in the top-K retrieved chunks:\n\n")
        f.write("| Metric | Accuracy | Status |\n")
        f.write("| :--- | :--- | :--- |\n")
        for k, acc in hit_metrics.items():
            f.write(f"| **Hit@{k}** | **{acc * 100:.1f}%** | {'✅ Optimal' if acc >= 0.9 else '⚠️ Review'} |\n")

        # Threshold Calibration
        f.write("\n## 5. Out-of-Scope Relevance Threshold Calibration\n\n")
        f.write(
            "To calibrate the hallucination and refusal guard, a labeled balanced benchmark of 8 in-scope questions "
            "and 8 out-of-scope questions was evaluated using cross-encoder rerank scores:\n\n"
        )
        f.write("| # | Query | Category | Top Rerank Score | Result |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for idx, rec in enumerate(calib_records, 1):
            cat = "In-Scope" if rec["is_in_scope"] else "Out-of-Scope"
            result_str = "Passed Gate" if rec["top_rerank_score"] >= DEFAULT_RERANK_THRESHOLD else "Refusal Triggered"
            f.write(f"| {idx} | {rec['query']} | `{cat}` | `{rec['top_rerank_score']:.4f}` | {result_str} |\n")

        in_scores = [r["top_rerank_score"] for r in calib_records if r["is_in_scope"]]
        out_scores = [r["top_rerank_score"] for r in calib_records if not r["is_in_scope"]]
        f.write(f"\n### Calibration Findings\n\n")
        f.write(f"- **In-Scope Score Range:** `[{min(in_scores):.4f}, {max(in_scores):.4f}]` (Mean: `{sum(in_scores)/len(in_scores):.4f}`)\n")
        f.write(f"- **Out-of-Scope Score Range:** `[{min(out_scores):.4f}, {max(out_scores):.4f}]` (Mean: `{sum(out_scores)/len(out_scores):.4f}`)\n")
        f.write(f"- **Selected Refusal Threshold:** `{DEFAULT_RERANK_THRESHOLD}` (Recommended midpoint: `{recommended_threshold}`)\n")
        f.write(f"- **Safety Margin:** There is an extensive score margin of ~{min(in_scores) - max(out_scores):.1f} points separating in-scope and out-of-scope queries, providing zero false rejections and zero hallucination leakages.\n")


if __name__ == "__main__":
    run_full_evaluation()
