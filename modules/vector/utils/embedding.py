import os

_model = None


class _ChromaDefaultEncoder:
    def __init__(self):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        self._embedding_function = DefaultEmbeddingFunction()

    def encode(self, texts, *args, **kwargs):
        return self._embedding_function(list(texts))


def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ModuleNotFoundError as exc:
            if exc.name != "sentence_transformers":
                raise
            _model = _ChromaDefaultEncoder()
        else:
            model_name = os.environ.get("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
            _model = SentenceTransformer(model_name)
    return _model


def embed(text: str):
    import numpy as np

    m = get_model()
    emb = m.encode([text])[0]
    return np.array(emb).astype("float32").tolist()
