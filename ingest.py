"""
ingest.py - Section-aware document ingestion and indexing pipeline.

Extracts text from PDF, cleans noise/headers/footers, preserves Sanskrit terms,
performs section-aware chunking without cross-chapter merging, saves chunks.jsonl,
and generates persistent ChromaDB embeddings.
"""

import os
import json
import re
import fitz  # PyMuPDF
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Constants
DEFAULT_PDF_PATH = "data/arthashastra_and_gita_compendium_50p.pdf"
FALLBACK_PDF_PATH = "arthashastra_and_gita_compendium_50p.pdf"
CHROMA_PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "classical_compendium"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNKS_JSONL_PATH = "chunks.jsonl"


def get_pdf_path() -> str:
    """Find the PDF path in data/ or root directory."""
    if os.path.exists(DEFAULT_PDF_PATH):
        return DEFAULT_PDF_PATH
    if os.path.exists(FALLBACK_PDF_PATH):
        return FALLBACK_PDF_PATH
    raise FileNotFoundError(
        f"Corpus PDF not found at {DEFAULT_PDF_PATH} or {FALLBACK_PDF_PATH}."
    )


def clean_page_text(raw_text: str, page_num: int) -> Dict[str, Any]:
    """
    Parse a single page of the compendium.
    Extracts structured metadata (chapter, module, specific section, source text)
    and returns cleaned, normalized body text with noise removed.
    """
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    # Extract chapter and module header if present
    chapter = f"Chapter {(page_num - 1) // 10 + 1}"
    module_title = ""
    specific_heading = ""
    source_text = "Classical Statecraft & Philosophy Compendium"

    # Separate header, separator, body, and footer
    body_lines = []
    past_separator = False
    in_footer = False

    separator_pattern = re.compile(r"^={5,}$")
    compliance_pattern = re.compile(r"Operational Compliance Note", re.IGNORECASE)
    doc_footer_pattern = re.compile(r"Page \d+ of 50\s*\|\s*Confidential", re.IGNORECASE)

    for line in lines:
        if separator_pattern.match(line):
            past_separator = True
            continue

        if not past_separator:
            if "CHAPTER" in line and "MODULE" in line:
                chapter_match = re.search(r"CHAPTER\s*(\d+)", line, re.IGNORECASE)
                if chapter_match:
                    chapter = f"Chapter {chapter_match.group(1)}"
                module_title = line
            elif module_title and not module_title.endswith(line):
                # Continuation of module title
                module_title += " " + line
            continue

        # In body area: detect footer start
        if compliance_pattern.search(line) or doc_footer_pattern.search(line):
            in_footer = True
            continue

        if not in_footer:
            body_lines.append(line)

    body_text = "\n".join(body_lines).strip()

    # Detect specific classical book/part heading if present in body
    for line in body_lines:
        if re.match(r"^(BOOK\s+[IVX0-9]+|PART\s+[IVX0-9]+)", line, re.IGNORECASE):
            specific_heading = line
            if "BOOK" in line.upper():
                source_text = "Arthashastra (Kautilya)"
            elif "PART" in line.upper() or "GITA" in line.upper():
                source_text = "Bhagavad Gita"
            break

    if not specific_heading:
        # Check first clause/section
        for line in body_lines:
            if re.match(r"^\d+\.\s+Overview of", line):
                specific_heading = line
                break

    # Determine source text if not explicitly detected
    if "Arthashastra" in module_title:
        source_text = "Arthashastra (Kautilya)"
    elif "Gita" in module_title or "Karma" in module_title:
        source_text = "Bhagavad Gita"

    # Clean hyphenated words broken across lines: e.g. "inter-\ndependent" -> "interdependent"
    cleaned_body = re.sub(r"(\b\w+)-\n(\w+\b)", r"\1\2", body_text)
    # Replace single line breaks inside paragraphs with spaces while keeping paragraph breaks
    paragraphs = [p.strip() for p in cleaned_body.split("\n\n") if p.strip()]
    normalized_paragraphs = []
    for p in paragraphs:
        # replace internal single newlines with space
        p_clean = " ".join(line.strip() for line in p.split("\n") if line.strip())
        # normalize whitespace while preserving unicode diacritics
        p_clean = re.sub(r"[ \t]+", " ", p_clean)
        normalized_paragraphs.append(p_clean)

    final_body = "\n\n".join(normalized_paragraphs)

    return {
        "page": page_num,
        "chapter": chapter,
        "module": module_title,
        "section": specific_heading if specific_heading else module_title,
        "source_text": source_text,
        "body": final_body,
    }


def chunk_text(
    page_data: Dict[str, Any],
    target_tokens: int = 500,
    overlap_tokens: int = 75,
) -> List[Dict[str, Any]]:
    """
    Split page body into clean, semantic chunks respecting boundaries.
    Never merges across pages/chapters.
    Appends metadata context to ensure high semantic recall.
    """
    body = page_data["body"]
    page_num = page_data["page"]
    chapter = page_data["chapter"]
    section = page_data["section"]
    source_text = page_data["source_text"]

    if not body:
        return []

    # Approximate token count by words * 1.3
    words = body.split()
    word_chunk_size = int(target_tokens / 1.3)  # ~380 words
    word_overlap = int(overlap_tokens / 1.3)   # ~55 words

    # If the page body is within target chunk size, keep it as one unified chunk
    if len(words) <= word_chunk_size + 50:
        chunk_text_content = body
        chunk_id = f"p{page_num}_c0"
        return [{
            "chunk_id": chunk_id,
            "text": chunk_text_content,
            "page": page_num,
            "chapter": chapter,
            "section": section,
            "source_text": source_text,
            "token_count_approx": int(len(words) * 1.3),
        }]

    # Otherwise slide with overlap
    chunks = []
    start = 0
    c_idx = 0
    while start < len(words):
        end = min(start + word_chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text_content = " ".join(chunk_words)
        chunk_id = f"p{page_num}_c{c_idx}"

        chunks.append({
            "chunk_id": chunk_id,
            "text": chunk_text_content,
            "page": page_num,
            "chapter": chapter,
            "section": section,
            "source_text": source_text,
            "token_count_approx": int(len(chunk_words) * 1.3),
        })

        if end == len(words):
            break
        start += max(1, word_chunk_size - word_overlap)
        c_idx += 1

    return chunks


def build_chunks(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract and chunk all pages from the PDF."""
    doc = fitz.open(pdf_path)
    all_chunks = []

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        raw_text = page.get_text()
        parsed_page = clean_page_text(raw_text, page_num)
        page_chunks = chunk_text(parsed_page)
        all_chunks.extend(page_chunks)

    doc.close()
    return all_chunks


def index_chunks_in_chroma(chunks: List[Dict[str, Any]], persist_dir: str = CHROMA_PERSIST_DIR) -> chromadb.Collection:
    """Index chunks into persistent ChromaDB with local sentence-transformers embeddings."""
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False)
    )

    # Delete existing collection if it exists to ensure fresh build
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"Loading embedding model '{EMBEDDING_MODEL_NAME}'...")
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [{
        "page": int(c["page"]),
        "chapter": str(c["chapter"]),
        "section": str(c["section"]),
        "source_text": str(c["source_text"]),
        "token_count_approx": int(c["token_count_approx"]),
    } for c in chunks]

    print(f"Generating dense embeddings for {len(chunks)} chunks...")
    embeddings = embedder.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas
    )

    print(f"Successfully indexed {len(chunks)} chunks into ChromaDB at '{persist_dir}'.")
    return collection


def run_ingestion() -> List[Dict[str, Any]]:
    """Execute complete ingestion pipeline and save artifacts."""
    pdf_path = get_pdf_path()
    print(f"Ingesting corpus from: {pdf_path}")

    chunks = build_chunks(pdf_path)
    total_chunks = len(chunks)
    total_tokens = sum(c["token_count_approx"] for c in chunks)
    avg_tokens = total_tokens / total_chunks if total_chunks > 0 else 0

    print("\n=== INGESTION STATS ===")
    print(f"Total Pages Processed: 50")
    print(f"Total Chunks Created: {total_chunks}")
    print(f"Average Chunk Size (approx tokens): {avg_tokens:.1f}")

    # Save chunks.jsonl for inspection and BM25 consumption
    with open(CHUNKS_JSONL_PATH, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"Saved chunk manifest to '{CHUNKS_JSONL_PATH}'")

    # Index into ChromaDB
    index_chunks_in_chroma(chunks)

    return chunks


if __name__ == "__main__":
    run_ingestion()
