import streamlit as st
from rag.ingest import ingest_uploaded_documents
from rag.faiss_store import index_ready, search_factory
from database.repository import list_documents
from llm.groq_client import ask_json
from llm.prompts import CHAT
from config import RAG_TOP_K, RAG_MIN_SCORE

def render_knowledge_base(factory):
    st.title("📚 Knowledge Base")
    st.caption("Upload the factory's SOPs, HACCP plans and procedures that should ground factory-specific AI audits.")

    docs = list_documents(factory["id"])
    ready = index_ready(factory["id"])

    if ready:
        st.success(f"🟢 RAG READY — {len(docs)} document(s) available in the factory knowledge base.")
    elif docs:
        st.warning("🟠 Documents exist, but the RAG index is not ready. Re-process the documents.")
    else:
        st.info("🔵 No factory SOP/HACCP documents uploaded yet.")

    st.markdown("### 1. Upload factory documents")
    doc_type = st.selectbox(
        "Document type *",
        ["SOP", "HACCP Plan", "Product Specification", "Procedure", "Other"],
    )
    files = st.file_uploader(
        "Choose documents",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Use the actual factory documents. For best results, use searchable PDFs or DOCX files.",
    )

    if st.button("Index / Update Knowledge Base", type="primary", disabled=not files):
        with st.spinner("Processing all factory documents and rebuilding the FAISS index..."):
            result = ingest_uploaded_documents(factory["id"], files, doc_type)
        if result["saved"]:
            st.success(
                f"Processed {len(result['saved'])} new/updated document(s). "
                f"The complete factory knowledge base now contains {result['chunks']} indexed chunks."
            )
        for error in result["errors"]:
            st.error(error)

    docs = list_documents(factory["id"])
    if docs:
        st.markdown("### 2. Uploaded documents")
        for d in docs:
            status = "✓ Indexed" if d["indexed"] else "⚠ Not indexed"
            st.write(f"📄 **{d['name']}** — {d['doc_type']} — {status}")

    st.divider()
    st.markdown("### 3. 🔎 Search the factory knowledge base")
    st.caption("Answers in this section are restricted to the uploaded factory documents.")

    query = st.text_input(
        "Enter your question",
        placeholder="e.g. What temperature range does our cold-storage SOP require?",
    )
    if st.button("Search Documents", disabled=not query.strip()):
        if not ready:
            st.error("The factory knowledge base is not ready. Upload and index SOP/HACCP documents first.")
            return

        hits = search_factory(factory["id"], query, RAG_TOP_K, RAG_MIN_SCORE)
        if not hits:
            st.warning("This information was not found in the uploaded factory documents.")
            return

        context = "\n\n".join(
            f"[SOURCE: {h['document_name']} | PAGE: {h.get('page','?')} | "
            f"SECTION: {h.get('section','Document content')}]\n{h['text']}"
            for h in hits
        )
        try:
            answer = ask_json(
                CHAT,
                f"USER QUESTION:\n{query}\n\nRETRIEVED FACTORY DOCUMENTS:\n{context}",
            )
            st.markdown("#### Answer")
            st.write(answer.get("answer", "No answer was returned."))

            st.markdown("#### Retrieved sources")
            for h in hits:
                with st.expander(
                    f"{h['document_name']} • page {h.get('page','?')} • relevance {h['score']:.2f}"
                ):
                    st.write(h["text"])
        except Exception as exc:
            st.error(f"Knowledge Base Search could not complete: {exc}")
