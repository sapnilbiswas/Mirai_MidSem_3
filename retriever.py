"""
retriever.py - Hybrid Retrieval with Reciprocal Rank Fusion (RRF) and Cross-Encoder Reranking.

Combines ChromaDB dense cosine similarity and BM25 sparse lexical search,
fuses candidate rankings via RRF, and applies Cross-Encoder reranking
for high-precision grounded retrieval with Sanskrit query expansion.
"""

import os
import json
import re
from typing import List, Dict, Any, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi

from ingest import (
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    CHUNKS_JSONL_PATH,
    run_ingestion,
)

RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RRF_K = 60

# Domain Synonym Maps for Light Query Expansion
SYNONYM_EXPANSIONS = [
    (
        re.compile(r"\b(seven\s+limbs?|constituents?(\s+of\s+state)?|elements?\s+of\s+state|prakritis?)\b", re.I),
        " Saptanga Prakriti Prakritis Swamin Swami Amatya Janapada Durga Kosha Danda Mitra Bala sovereign state"
    ),
    (
        re.compile(r"\b(envoys?|ambassadors?|messengers?|diplomats?|dutas?)\b", re.I),
        " Duta Dutas Nisrishtartha Nisrishtarthah Parimitartha Parimitarthah Shasanahara Shasanaharah"
    ),
    (
        re.compile(r"\b(steady\s+wisdom|sthitaprajna)\b", re.I),
        " Sthitaprajna steady wisdom Chapter 2"
    ),
    (
        re.compile(r"\b(withdraw\s+senses?|senses?|tortoise|shell|kurma)\b", re.I),
        " tortoise kurma shell limbs external sense objects withdraw"
    ),
    (
        re.compile(r"\b(sixfold\s+(royal\s+)?strategy|shadgunya|mandala\s+theory)\b", re.I),
        " Shadgunya Mandala sixfold royal strategy foreign policy"
    ),
    (
        re.compile(r"\b(detached\s+action|nishkama\s+karma|moral\s+duty)\b", re.I),
        " Nishkama Karma detached action moral duty governance"
    ),
    (
        re.compile(r"\b(embezzlement|forty\s+ways|revenue\s+auditing|fiscal)\b", re.I),
        " fiscal administration revenue auditing forty ways of embezzlement"
    ),
    (
        re.compile(r"\b(judicial\s+procedure|witness\s+examination|civil\s+contracts)\b", re.I),
        " judicial procedure civil contracts witness examination protocols"
    ),
]


def expand_query(query: str) -> str:
    """Apply light query expansion with Sanskrit and English canonical synonyms."""
    expanded = query
    for pattern, expansion in SYNONYM_EXPANSIONS:
        if pattern.search(query):
            expanded += " " + expansion
    return re.sub(r"\s+", " ", expanded).strip()


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens for BM25."""
    return re.findall(r"\w+", text.lower())


class HybridRetriever:
    """Hybrid dense + sparse retriever with cross-encoder reranking."""

    def __init__(self, chroma_dir: str = CHROMA_PERSIST_DIR, chunks_path: str = CHUNKS_JSONL_PATH):
        self.chroma_dir = chroma_dir
        self.chunks_path = chunks_path

        # Verify indexing exists or trigger auto-ingest
        if not os.path.exists(chroma_dir) or not os.path.exists(chunks_path):
            print("Vectorstore or chunk manifest missing. Auto-running ingestion...")
            run_ingestion()

        self._load_chunks()
        self._init_bm25()
        self._init_dense()
        self._init_reranker()

    def _load_chunks(self):
        """Load chunk manifest into memory."""
        self.chunks = []
        self.chunk_by_id = {}
        with open(self.chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    self.chunks.append(item)
                    self.chunk_by_id[item["chunk_id"]] = item

    def _init_bm25(self):
        """Build BM25 index on tokenized chunk documents."""
        self.corpus_tokens = [tokenize(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def _init_dense(self):
        """Initialize ChromaDB client and local embedding model."""
        self.client = chromadb.PersistentClient(
            path=self.chroma_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_collection(COLLECTION_NAME)
        self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def _init_reranker(self):
        """Initialize CrossEncoder reranker."""
        self.reranker = CrossEncoder(RERANKER_MODEL_NAME)

    def retrieve_dense(self, query: str, top_n: int = 15) -> List[Tuple[str, float]]:
        """Dense semantic retrieval via cosine similarity in ChromaDB."""
        query_vector = self.embedder.encode(query, normalize_embeddings=True).tolist()
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_n, len(self.chunks)),
            include=["metadatas", "documents", "distances"]
        )
        candidates = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(ids)
            for cid, dist in zip(ids, distances):
                # Chroma cosine distance = 1 - cosine_similarity
                sim = 1.0 - dist
                candidates.append((cid, float(sim)))
        return candidates

    def retrieve_bm25(self, query: str, top_n: int = 15) -> List[Tuple[str, float]]:
        """Sparse lexical retrieval via BM25."""
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        scored_pairs = [(self.chunks[i]["chunk_id"], float(scores[i])) for i in range(len(self.chunks))]
        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        return scored_pairs[:top_n]

    def retrieve(
        self,
        query: str,
        top_k: int = 6,
        top_candidates: int = 15,
        use_expansion: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute full hybrid retrieval pipeline:
        1. Query expansion
        2. Parallel Dense + BM25 retrieval
        3. Reciprocal Rank Fusion (RRF)
        4. Cross-Encoder reranking
        Returns top_k chunks with rerank_score and full metadata.
        """
        if not query or not query.strip():
            return []

        search_query = expand_query(query) if use_expansion else query

        # 1. Retrieve dense and sparse rankings
        dense_results = self.retrieve_dense(search_query, top_n=top_candidates)
        bm25_results = self.retrieve_bm25(search_query, top_n=top_candidates)

        # 2. Reciprocal Rank Fusion
        rrf_scores: Dict[str, float] = {}

        for rank, (cid, _) in enumerate(dense_results):
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)

        for rank, (cid, _) in enumerate(bm25_results):
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)

        # Sort combined candidates by RRF score
        fused_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        top_fused = fused_candidates[:top_candidates]

        if not top_fused:
            return []

        # 3. Cross-Encoder Reranking
        candidate_chunks = [self.chunk_by_id[cid] for cid, _ in top_fused if cid in self.chunk_by_id]
        pairs = [(query, c["text"]) for c in candidate_chunks]
        rerank_scores = self.reranker.predict(pairs)

        ranked_results = []
        for chunk, score, (_, rrf_val) in zip(candidate_chunks, rerank_scores, top_fused):
            res_item = dict(chunk)
            res_item["rerank_score"] = float(score)
            res_item["rrf_score"] = float(rrf_val)
            ranked_results.append(res_item)

        # Sort descending by cross-encoder score
        ranked_results.sort(key=lambda x: x["rerank_score"], reverse=True)

        return ranked_results[:top_k]


# Singleton helper for application-wide reuse
_global_retriever = None

def get_retriever() -> HybridRetriever:
    global _global_retriever
    if _global_retriever is None:
        _global_retriever = HybridRetriever()
    return _global_retriever


if __name__ == "__main__":
    retriever = get_retriever()
    test_queries = [
        "According to the Saptanga theory, what are the seven constituent limbs of state?",
        "In which year was the Battle of Plassey fought?",
        "How many categories of envoys (Dutas) are identified in the text?",
        "What metaphor does Chapter 2 use to explain how a person of steady wisdom withdraws senses?",
        "Which political coalition won the 2024 Indian General Election?"
    ]

    print("\n=== HYBRID RETRIEVAL & RERANK VERIFICATION ===")
    for q in test_queries:
        print(f"\nQUERY: {q}")
        res = retriever.retrieve(q, top_k=2)
        for rank, hit in enumerate(res):
            print(f"  Rank {rank+1}: Page {hit['page']} | Score: {hit['rerank_score']:.4f} | ID: {hit['chunk_id']}")
            print(f"    Preview: {hit['text'][:120]}...")
