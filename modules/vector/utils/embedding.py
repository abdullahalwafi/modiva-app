import os

_model = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        model_name = os.environ.get("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
        _model = SentenceTransformer(model_name)
    return _model


def embed(text: str):
    m = get_model()
    emb = m.encode([text])[0]
    return emb.astype("float32").tolist()
