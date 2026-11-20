"""
app.py - Classical Philosophy & Statecraft Text Explorer.

Interactive Streamlit interface with conversational chat history,
expandable grounded source citations, relevance gating transparency,
and configurable retrieval settings.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Ensure environment is loaded
load_dotenv()

from rag import get_rag_pipeline, NOT_IN_CORPUS_MESSAGE, DEFAULT_RERANK_THRESHOLD


st.set_page_config(
    page_title="Classical Philosophy & Statecraft Explorer",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource(show_spinner="Loading embedding, retrieval, and reranking models...")
def load_rag_system():
    """Cache the RAG pipeline instance across user sessions."""
    return get_rag_pipeline()


def main():
    rag = load_rag_system()

    # Sidebar Controls
    st.sidebar.title("⚙️ System Settings")
    st.sidebar.markdown(
        "**Corpus:** *Arthashastra & Bhagavad Gita Compendium (50 pages)*\n\n"
        "Grounded retrieval answering with strict citation verification and out-of-scope hallucination guard."
    )

    # API Status Indicator
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if rag.genai_client and api_key and api_key != "your_key_here":
        st.sidebar.success(f"🟢 Mode: Gemini LLM ({rag.model_name})")
    else:
        st.sidebar.warning("🟡 Mode: Extractive Fallback (No Gemini API key)")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Retrieval Hyperparameters")

    top_k = st.sidebar.slider(
        "Top-K Retrieved Sources",
        min_value=1,
        max_value=10,
        value=6,
        help="Number of fused & reranked passages passed to the prompt."
    )

    threshold = st.sidebar.slider(
        "Out-of-Scope Refusal Threshold",
        min_value=-15.0,
        max_value=5.0,
        value=DEFAULT_RERANK_THRESHOLD,
        step=0.5,
        help="Cross-encoder relevance threshold below which questions are safely refused."
    )

    show_sources = st.sidebar.checkbox(
        "Show Retrieved Sources Panel",
        value=True,
        help="Display expandable evidence panel with scores and page numbers."
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Assessment Prompts")
    quick_queries = [
        "What are the seven constituent limbs (Prakritis) of state in Saptanga theory?",
        "How many categories of envoys (Dutas) are identified and what are their designations?",
        "What metaphor does Chapter 2 use to explain how steady wisdom withdraws senses?",
        "In which year was the Battle of Plassey fought?",
        "Which political coalition won the 2024 Indian General Election?"
    ]

    selected_prompt = None
    for q_text in quick_queries:
        if st.sidebar.button(q_text, key=f"btn_{q_text[:20]}"):
            selected_prompt = q_text

    # Main UI Header
    st.title("📜 Classical Philosophy & Statecraft Text Explorer")
    st.markdown(
        "Ask questions grounded strictly in the **Compendium of Classical Statecraft & Philosophy** "
        "(Arthashastra & Gita selections). Every factual claim is verified with page citations like `[p. 8]`."
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources") and show_sources:
                with st.expander("📚 Retrieved Evidence & Citations", expanded=False):
                    for idx, src in enumerate(msg["sources"], 1):
                        st.markdown(
                            f"**Source {idx}** | **Page:** {src['page']} | "
                            f"**Section:** {src['section']} | "
                            f"**Rerank Score:** `{src['rerank_score']:.4f}`"
                        )
                        st.caption(src["text"])
                        st.divider()

    # Handle incoming user query
    user_query = st.chat_input("Enter your question here...") or selected_prompt

    if user_query:
        # Display user question
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Generate answer with progress spinner
        with st.chat_message("assistant"):
            with st.spinner("Analyzing text and verifying citations..."):
                response = rag.answer(user_query, top_k=top_k, threshold_override=threshold)
                answer_text = response["answer"]
                sources = response["sources"]
                cited_pages = response["cited_pages"]
                top_score = response["relevance_score"]
                is_refusal = response["is_refusal"]

                st.markdown(answer_text)

                if cited_pages and not is_refusal:
                    st.caption(f"📌 **Verified Citations:** {', '.join(f'[p. {p}]' for p in cited_pages)}")
                elif is_refusal:
                    st.caption(f"🛡️ **Relevance Guard:** Query score `{top_score:.4f}` < threshold `{threshold:.1f}`")

                if sources and show_sources:
                    with st.expander("📚 Retrieved Evidence & Citations", expanded=False):
                        for idx, src in enumerate(sources, 1):
                            st.markdown(
                                f"**Source {idx}** | **Page:** {src['page']} | "
                                f"**Section:** {src['section']} | "
                                f"**Rerank Score:** `{src['rerank_score']:.4f}`"
                            )
                            st.caption(src["text"])
                            st.divider()

        # Save to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer_text,
            "sources": sources if show_sources else []
        })


if __name__ == "__main__":
    main()
