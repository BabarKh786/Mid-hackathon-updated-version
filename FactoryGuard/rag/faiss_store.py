import json
from pathlib import Path
import faiss
import numpy as np
from config import INDEX_DIR, RAG_MIN_SCORE
from rag.embeddings import embed

def _paths(factory_id):
    folder = Path(INDEX_DIR) / str(factory_id)
    return folder, folder / "index.faiss", folder / "metadata.json"

def index_factory(factory_id, chunks):
    if not chunks:
        raise ValueError("No readable document chunks are available for indexing.")

    folder, index_path, meta_path = _paths(factory_id)
    folder.mkdir(parents=True, exist_ok=True)

    vectors = np.asarray(embed([x["text"] for x in chunks]), dtype="float32")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    # Atomic-ish replacement: write the complete new index/metadata together.
    tmp_index = folder / "index.faiss.tmp"
    tmp_meta = folder / "metadata.json.tmp"
    faiss.write_index(index, str(tmp_index))
    tmp_meta.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    tmp_index.replace(index_path)
    tmp_meta.replace(meta_path)

def index_ready(factory_id):
    _, index_path, meta_path = _paths(factory_id)
    if not index_path.exists() or not meta_path.exists():
        return False
    try:
        index = faiss.read_index(str(index_path))
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        return index.ntotal > 0 and len(metadata) == index.ntotal
    except Exception:
        return False

def search_factory(factory_id, query, k=6, min_score=RAG_MIN_SCORE):
    if not index_ready(factory_id):
        return []

    _, index_path, meta_path = _paths(factory_id)
    index = faiss.read_index(str(index_path))
    chunks = json.loads(meta_path.read_text(encoding="utf-8"))

    q = np.asarray(embed([query]), dtype="float32")
    scores, ids = index.search(q, min(k, index.ntotal))

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0 or float(score) < min_score:
            continue
        item = dict(chunks[int(idx)])
        item["score"] = float(score)
        results.append(item)
    return results
