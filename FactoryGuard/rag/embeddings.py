from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

def embed(texts):
    return get_model().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
