"""
test_rag.py - Comprehensive Unit and Integration Test Suite.

Tests section-aware chunking, refusal guard on out-of-scope questions,
citation verification, Sanskrit diacritics preservation, and extractive fallback.
"""

import pytest
import os
import json
from rag import (
    RAGPipeline,
    get_rag_pipeline,
    verify_citations,
    extract_citations,
    NOT_IN_CORPUS_MESSAGE,
    DEFAULT_RERANK_THRESHOLD
)
from retriever import get_retriever, expand_query
from ingest import clean_page_text, chunk_text, get_pdf_path


@pytest.fixture(scope="session")
def rag_pipeline():
    """Shared RAG pipeline fixture."""
    return get_rag_pipeline()


@pytest.fixture(scope="session")
def retriever():
    """Shared Retriever fixture."""
    return get_retriever()


# ============================================================================
# 1. Chunking Tests
# ============================================================================

def test_chunking_no_cross_chapter_merge():
    """Ensure chunking never merges content across different chapters or pages."""
    raw_p1 = (
        "Compendium of Classical Statecraft & Philosophy: Arthashastra & Gita Selections - Official Referen\n"
        "Document Page 1 of 50\n"
        "CHAPTER 1 | MODULE 1.0: HISTORICAL PHILOLOGY\n"
        "========================================================================\n"
        "1. Overview Clause 1.1\nText for chapter 1 page 1.\n"
        "Operational Compliance Note (Ref-5-01): verify.\n"
        "Page 1 of 50 | Confidential Assessment Corpus - Do Not Distribute"
    )
    raw_p2 = (
        "Compendium of Classical Statecraft & Philosophy: Arthashastra & Gita Selections - Official Referen\n"
        "Document Page 2 of 50\n"
        "CHAPTER 2 | MODULE 2.0: FISCAL ADMINISTRATION\n"
        "========================================================================\n"
        "1. Overview Clause 2.1\nText for chapter 2 page 2.\n"
        "Operational Compliance Note (Ref-5-02): verify.\n"
        "Page 2 of 50 | Confidential Assessment Corpus - Do Not Distribute"
    )

    p1_data = clean_page_text(raw_p1, page_num=1)
    p2_data = clean_page_text(raw_p2, page_num=2)

    chunks_p1 = chunk_text(p1_data)
    chunks_p2 = chunk_text(p2_data)

    assert len(chunks_p1) >= 1
    assert len(chunks_p2) >= 1

    # Ensure page numbers and chapters are strictly segregated
    assert all(c["page"] == 1 for c in chunks_p1)
    assert all(c["page"] == 2 for c in chunks_p2)
    assert chunks_p1[0]["chapter"] == "Chapter 1"
    assert chunks_p2[0]["chapter"] == "Chapter 2"


def test_chunk_manifest_metadata():
    """Verify that chunks.jsonl contains valid metadata schema for all chunks."""
    assert os.path.exists("chunks.jsonl")
    with open("chunks.jsonl", "r", encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]

    assert len(chunks) == 50
    for c in chunks:
        assert "chunk_id" in c
        assert "page" in c
        assert "chapter" in c
        assert "section" in c
        assert "source_text" in c
        assert "text" in c
        assert 1 <= c["page"] <= 50
        assert len(c["text"]) > 20


def test_sanskrit_terms_preservation():
    """Verify that Sanskrit technical terms and diacritics are preserved in chunks."""
    with open("chunks.jsonl", "r", encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]

    chunk_p8 = next(c for c in chunks if c["page"] == 8)
    assert "Saptanga" in chunk_p8["text"]
    assert "Prakritis" in chunk_p8["text"]
    assert "Swamin" in chunk_p8["text"]
    assert "Amatya" in chunk_p8["text"]
    assert "Janapada" in chunk_p8["text"]
    assert "Durga" in chunk_p8["text"]
    assert "Kosha" in chunk_p8["text"]
    assert "Danda" in chunk_p8["text"]
    assert "Mitra" in chunk_p8["text"]

    chunk_p19 = next(c for c in chunks if c["page"] == 19)
    assert "Dutas" in chunk_p19["text"]
    assert "Nisrishtarthah" in chunk_p19["text"]
    assert "Parimitarthah" in chunk_p19["text"]
    assert "Shasanaharah" in chunk_p19["text"]

    chunk_p36 = next(c for c in chunks if c["page"] == 36)
    assert "Sthitaprajna" in chunk_p36["text"]
    assert "tortoise" in chunk_p36["text"].lower()


# ============================================================================
# 2. Refusal Guard Tests
# ============================================================================

def test_refusal_guard_battle_of_plassey(rag_pipeline):
    """Battle of Plassey is out of corpus and must return exact refusal message."""
    query = "In which year was the Battle of Plassey fought between the British East India Company and the Nawab of Bengal?"
    res = rag_pipeline.answer(query)
    assert res["is_refusal"] is True
    assert res["answer"] == NOT_IN_CORPUS_MESSAGE
    assert res["cited_pages"] == []
    assert res["relevance_score"] < DEFAULT_RERANK_THRESHOLD


def test_refusal_guard_2024_election(rag_pipeline):
    """2024 General Election is out of corpus and must return exact refusal message."""
    query = "Which political coalition won the 2024 Indian General Election?"
    res = rag_pipeline.answer(query)
    assert res["is_refusal"] is True
    assert res["answer"] == NOT_IN_CORPUS_MESSAGE
    assert res["cited_pages"] == []
    assert res["relevance_score"] < DEFAULT_RERANK_THRESHOLD


def test_refusal_guard_modern_tech(rag_pipeline):
    """Unrelated modern queries must be safely refused."""
    query = "How do Transformer self-attention heads compute scaled dot-product attention in PyTorch?"
    res = rag_pipeline.answer(query)
    assert res["is_refusal"] is True
    assert res["answer"] == NOT_IN_CORPUS_MESSAGE


# ============================================================================
# 3. Grounding and In-Scope Retrieval Tests
# ============================================================================

def test_saptanga_limbs_grounded(rag_pipeline):
    """Saptanga query must retrieve page 8 and cite [p. 8]."""
    query = "According to the Saptanga theory section of the provided text, what are the seven constituent limbs of state?"
    res = rag_pipeline.answer(query)
    assert res["is_refusal"] is False
    assert 8 in res["cited_pages"]
    ans_lower = res["answer"].lower()
    for limb in ["swamin", "amatya", "janapada", "durga", "kosha", "mitra"]:
        assert limb in ans_lower


def test_duta_categories_grounded(rag_pipeline):
    """Envoys query must retrieve page 19, identify 3 categories, their designations, and cite [p. 19]."""
    query = "How many categories of envoys (Dutas) are identified in the text according to their level of authority, and what are their designations?"
    res = rag_pipeline.answer(query)
    assert res["is_refusal"] is False
    assert 19 in res["cited_pages"]
    ans = res["answer"]
    assert "three" in ans.lower() or "3" in ans
    assert "nisrishtartha" in ans.lower()
    assert "parimitartha" in ans.lower()
    assert "shasanahara" in ans.lower()


def test_sthitaprajna_tortoise_grounded(rag_pipeline):
    """Sthitaprajna query must retrieve page 36, identify the tortoise metaphor and cite [p. 36]."""
    query = "What metaphor does Chapter 2 use to explain how a person of steady wisdom (Sthitaprajna) withdraws senses?"
    res = rag_pipeline.answer(query)
    assert res["is_refusal"] is False
    assert 36 in res["cited_pages"]
    assert "tortoise" in res["answer"].lower()


# ============================================================================
# 4. Citation Verification Logic Tests
# ============================================================================

def test_citation_verification_valid():
    """Valid citations matching retrieved pages must be retained."""
    answer = "The seven limbs are detailed in the text [p. 8]."
    retrieved_pages = {8, 12, 19}
    cleaned, verified, invalid = verify_citations(answer, retrieved_pages)
    assert "[p. 8]" in cleaned
    assert verified == [8]
    assert invalid == []


def test_citation_verification_strips_hallucinated_citation():
    """Ungrounded/hallucinated citations not in retrieved pages must be stripped."""
    answer = "The battle was fought long ago [p. 99] and documented [p. 8]."
    retrieved_pages = {8, 12}
    cleaned, verified, invalid = verify_citations(answer, retrieved_pages)
    assert "[p. 99]" not in cleaned
    assert "[p. 8]" in cleaned
    assert verified == [8]
    assert invalid == [99]


# ============================================================================
# 5. Query Expansion & Reliability Tests
# ============================================================================

def test_query_expansion():
    """Query expansion should append canonical Sanskrit synonyms."""
    expanded = expand_query("What are the seven limbs of state?")
    assert "Saptanga" in expanded
    assert "Prakriti" in expanded

    expanded_duta = expand_query("Who is the envoy sent to negotiate?")
    assert "Duta" in expanded_duta


def test_empty_query_handling(rag_pipeline):
    """Empty queries should return graceful guidance without error."""
    res = rag_pipeline.answer("")
    assert "valid question" in res["answer"].lower()
    assert res["is_refusal"] is False


def test_long_query_handling(rag_pipeline):
    """Very long queries should be safely truncated and processed."""
    long_query = "what are the seven constituent limbs of state in Saptanga theory? " + "additional historical context notes " * 100
    res = rag_pipeline.answer(long_query)
    assert res["is_refusal"] is False
    assert 8 in res["cited_pages"]


def test_extractive_fallback_mode(retriever):
    """Pipeline in extractive mode (no LLM) returns top grounded passage with citation."""
    extractive_rag = RAGPipeline(retriever=retriever, model_name="none")
    # Force client to None
    extractive_rag.genai_client = None

    res = extractive_rag.answer("What are the seven constituent limbs of state in Saptanga theory?")
    assert res["mode"] == "extractive_fallback"
    assert res["is_refusal"] is False
    assert "[p. 8]" in res["answer"]
    assert "Swamin" in res["answer"]
