"""
rag.py - Grounded Generation, Relevance Gating, Citation Verification, and Extractive Fallback.

Implements strict grounded prompting with Gemini LLM, out-of-scope refusal guard,
post-generation citation verification against retrieved chunks, and graceful
extractive fallback if the Gemini API key is missing or invalid.
"""

import os
import re
import time
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dotenv import load_dotenv

from retriever import HybridRetriever, get_retriever

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Constants
NOT_IN_CORPUS_MESSAGE = "This information is not available in the provided text."
DEFAULT_RERANK_THRESHOLD = -2.0  # Calibrated threshold separating in-scope vs out-of-scope queries
DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-flash-latest"]


GROUNDED_SYSTEM_PROMPT = (
    "You are an expert scholar and research assistant analyzing classical Indian statecraft and philosophy.\n"
    "Answer ONLY using the provided context. If the context does not contain the answer, reply exactly: "
    f"'{NOT_IN_CORPUS_MESSAGE}'\n"
    "Do NOT use outside knowledge, even if you know the answer.\n"
    "Cite pages like [p. 12] or [p. 8] for every factual statement. Be concise and complete (list ALL items when a list is asked for).\n"
    "Never speculate or invent facts beyond the provided context."
)


def extract_citations(text: str) -> List[int]:
    """Extract page citations like [p. 8], [p. 19], [p.36] from text."""
    matches = re.findall(r"\[p\.?\s*(\d+)\]", text, re.IGNORECASE)
    return [int(m) for m in matches]


def verify_citations(answer: str, retrieved_pages: Set[int]) -> Tuple[str, List[int], List[int]]:
    """
    Verify that every cited [p. N] exists in the retrieved context chunks.
    Strips or flags ungrounded page citations.
    Returns: (cleaned_answer, verified_citations, invalid_citations)
    """
    cited = extract_citations(answer)
    verified = []
    invalid = []

    def replace_citation(match):
        page_num = int(match.group(1))
        if page_num in retrieved_pages:
            verified.append(page_num)
            return f"[p. {page_num}]"
        else:
            invalid.append(page_num)
            # Remove invalid/hallucinated citation
            return ""

    cleaned_answer = re.sub(r"\[p\.?\s*(\d+)\]", replace_citation, answer, flags=re.IGNORECASE)
    # Clean up double spaces left by removed citations
    cleaned_answer = re.sub(r"[ \t]+", " ", cleaned_answer).strip()

    return cleaned_answer, sorted(list(set(verified))), sorted(list(set(invalid)))


class RAGPipeline:
    """End-to-end RAG pipeline with relevance gating and citation verification."""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        threshold: float = DEFAULT_RERANK_THRESHOLD,
        model_name: str = DEFAULT_MODEL
    ):
        self.retriever = retriever or get_retriever()
        self.threshold = threshold
        self.model_name = model_name
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.genai_client = None

        if self.api_key and self.api_key != "your_key_here":
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Gemini client with model '{self.model_name}'.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}. Falling back to extractive mode.")
                self.genai_client = None
        else:
            logger.info("No valid GEMINI_API_KEY detected in .env. Running in extractive fallback mode.")

    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Execute Gemini LLM generation with temperature 0.0 and fallback model cascade."""
        if not self.genai_client:
            return None

        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]

        for model in models_to_try:
            try:
                from google.genai import types
                response = self.genai_client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        system_instruction=GROUNDED_SYSTEM_PROMPT,
                    )
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                err_msg = str(e)
                if "API_KEY_INVALID" in err_msg or "401" in err_msg or "403" in err_msg:
                    logger.error(f"Gemini API key rejected: {err_msg}")
                    return None
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    logger.warning(f"Rate limited on {model}. Pausing 6 seconds before trying next candidate...")
                    time.sleep(6)
                else:
                    logger.warning(f"Model '{model}' failed: {e}. Trying next candidate...")

        return None

    def _extractive_fallback(self, query: str, top_chunks: List[Dict[str, Any]]) -> str:
        """
        Extractive fallback mode when no LLM API is available.
        Directly surfaces grounded text passages from the highest scoring retrieved chunks.
        """
        if not top_chunks:
            return NOT_IN_CORPUS_MESSAGE

        best_chunk = top_chunks[0]
        page = best_chunk["page"]
        text = best_chunk["text"]

        return f"{text} [p. {page}]"

    def answer(
        self,
        query: str,
        top_k: int = 6,
        threshold_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Full RAG workflow:
        1. Query validation
        2. Hybrid retrieval + Reranking
        3. Relevance Guard (Score threshold check)
        4. Grounded Generation (Gemini or Extractive Fallback)
        5. Citation verification
        """
        clean_query = query.strip() if query else ""
        active_threshold = threshold_override if threshold_override is not None else self.threshold

        # Reliability guard: Empty query
        if not clean_query:
            return {
                "query": query,
                "answer": "Please provide a valid question.",
                "sources": [],
                "cited_pages": [],
                "invalid_citations": [],
                "is_refusal": False,
                "relevance_score": -99.0,
                "mode": "none"
            }

        # Reliability guard: Handle very long queries with head+tail truncation (~150 words)
        words = clean_query.split()
        if len(words) > 150:
            clean_query = " ".join(words[:75] + words[-75:])

        # Retrieve candidates
        sources = self.retriever.retrieve(clean_query, top_k=top_k)

        # Compute best relevance score
        top_score = sources[0]["rerank_score"] if sources else -99.0
        retrieved_pages = {c["page"] for c in sources}

        # Out-of-scope guard: Threshold check
        if not sources or top_score < active_threshold:
            logger.info(
                f"Relevance gate triggered for query '{query[:40]}...'. Top score: {top_score:.4f} < threshold {active_threshold}"
            )
            return {
                "query": query,
                "answer": NOT_IN_CORPUS_MESSAGE,
                "sources": sources,
                "cited_pages": [],
                "invalid_citations": [],
                "is_refusal": True,
                "relevance_score": top_score,
                "mode": "refusal_gate"
            }

        # Format context for grounded generation
        context_blocks = []
        for s in sources:
            block = (
                f"[Source Document: {s['source_text']}, Section: {s['section']}, Page: {s['page']}]\n"
                f"{s['text']}\n"
            )
            context_blocks.append(block)
        context_str = "\n---\n".join(context_blocks)

        user_prompt = (
            f"Context:\n{context_str}\n\n"
            f"Question: {clean_query}\n\n"
            f"Provide a clear, direct answer based strictly on the context above with page citations like [p. {sources[0]['page']}]."
        )

        # Generation attempt
        llm_answer = self._call_gemini(user_prompt)
        mode = "gemini"

        if not llm_answer:
            # Fallback to extractive mode
            llm_answer = self._extractive_fallback(clean_query, sources)
            mode = "extractive_fallback"

        # Check if LLM itself determined context is insufficient
        is_refusal = (
            NOT_IN_CORPUS_MESSAGE.lower() in llm_answer.lower()
            or "not available in the provided text" in llm_answer.lower()
        )

        if is_refusal:
            final_answer = NOT_IN_CORPUS_MESSAGE
            verified_citations = []
            invalid_citations = []
        else:
            # Perform strict citation verification
            final_answer, verified_citations, invalid_citations = verify_citations(
                llm_answer, retrieved_pages
            )
            # If answer didn't explicitly include citation but came from top chunk, add it
            if not verified_citations and sources:
                final_answer += f" [p. {sources[0]['page']}]"
                verified_citations = [sources[0]["page"]]

        return {
            "query": query,
            "answer": final_answer,
            "sources": sources,
            "cited_pages": verified_citations,
            "invalid_citations": invalid_citations,
            "is_refusal": is_refusal,
            "relevance_score": top_score,
            "mode": mode
        }


# Singleton pipeline
_global_rag_pipeline = None

def get_rag_pipeline(threshold: float = DEFAULT_RERANK_THRESHOLD) -> RAGPipeline:
    global _global_rag_pipeline
    if _global_rag_pipeline is None or _global_rag_pipeline.threshold != threshold:
        _global_rag_pipeline = RAGPipeline(threshold=threshold)
    return _global_rag_pipeline


if __name__ == "__main__":
    rag = get_rag_pipeline()
    test_questions = [
        "According to the Saptanga theory section of the provided text, what are the seven constituent limbs (Prakritis) of a sovereign state?",
        "In which year was the Battle of Plassey fought between the British East India Company and the Nawab of Bengal?",
        "How many categories of envoys (Dutas) are identified in the text according to their level of authority, and what are their designations?",
        "What metaphor does Chapter 2 of the provided text use to explain how a person of steady wisdom (Sthitaprajna) withdraws their senses from sense objects?",
        "Which political coalition won the 2024 Indian General Election?"
    ]

    print("\n=== RAG PIPELINE VERIFICATION (5 ASSESSMENT QUESTIONS) ===")
    for idx, q in enumerate(test_questions, 1):
        print(f"\n[Q{idx}] {q}")
        res = rag.answer(q)
        print(f"Mode: {res['mode']} | Score: {res['relevance_score']:.4f} | Refusal: {res['is_refusal']}")
        print(f"Answer:\n{res['answer']}")
        print(f"Cited Pages: {res['cited_pages']}")
        if res['sources']:
            print(f"Top Source: Page {res['sources'][0]['page']} ({res['sources'][0]['section']})")
