from pathlib import Path
from rag.document_loader import load_document
from rag.chunker import chunk_pages
from rag.faiss_store import index_factory
from database.repository import add_document, list_documents, mark_documents_indexed
from config import UPLOAD_DIR

KB_TYPES = {"SOP", "HACCP Plan", "Product Specification", "Procedure", "Other"}

def _safe_filename(name):
    return Path(name).name.replace("/", "_").replace("\\", "_")

def _rebuild_factory_index(factory_id):
    """
    Rebuild from every document stored for this factory.
    This fixes the common bug where uploading a second document replaces
    the first FAISS index instead of adding to the existing knowledge base.
    """
    all_chunks = []
    documents = list_documents(factory_id)

    for d in documents:
        path = Path(d["path"])
        if not path.exists():
            continue
        pages = load_document(str(path))
        chunks = chunk_pages(pages)
        for chunk in chunks:
            chunk["document_name"] = d["name"]
            chunk["document_type"] = d["doc_type"]
            chunk["factory_id"] = factory_id
        all_chunks.extend(chunks)

    if not all_chunks:
        mark_documents_indexed(factory_id, False)
        return 0

    index_factory(factory_id, all_chunks)
    mark_documents_indexed(factory_id, True)
    return len(all_chunks)

def ingest_uploaded_documents(factory_id, uploaded_files, doc_type):
    if doc_type not in KB_TYPES:
        raise ValueError("Invalid document type.")

    saved = []
    errors = []
    base = Path(UPLOAD_DIR) / str(factory_id)
    base.mkdir(parents=True, exist_ok=True)

    for uf in uploaded_files:
        try:
            filename = _safe_filename(uf.name)
            path = base / filename
            path.write_bytes(uf.getbuffer())

            # Validate readability before recording it as indexed.
            pages = load_document(str(path))
            chunks = chunk_pages(pages)
            if not chunks:
                raise ValueError("No readable text was found in this document.")

            add_document(factory_id, filename, doc_type, str(path), 0)
            saved.append(filename)
        except Exception as exc:
            errors.append(f"{uf.name}: {exc}")

    # Rebuild from all known factory documents so old SOPs are not lost.
    chunks_count = _rebuild_factory_index(factory_id) if saved else 0

    return {
        "saved": saved,
        "chunks": chunks_count,
        "errors": errors,
    }
