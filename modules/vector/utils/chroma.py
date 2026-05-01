import os

_chroma_client = None
_rag_collection = None
_docs_collection = None


class ChromaUnavailable(RuntimeError):
    pass

def get_chroma():
    global _chroma_client, _rag_collection

    if _chroma_client is not None and _rag_collection is not None:
        return _chroma_client, _rag_collection

    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
    coll_name = os.environ.get("CHROMA_COLLECTION_NAME", "rag_collection")

    try:
        from chromadb import PersistentClient
    except ModuleNotFoundError as exc:
        if exc.name != "chromadb":
            raise
        raise ChromaUnavailable(
            "Paket Python 'chromadb' belum terpasang untuk interpreter Django."
        ) from exc

    _chroma_client = PersistentClient(path=persist_dir)
    _rag_collection = _chroma_client.get_or_create_collection(
        coll_name, metadata={"type": "rag_chunks"}
    )
    return _chroma_client, _rag_collection


def get_docs_collection():
    global _docs_collection
    client, _ = get_chroma()

    if _docs_collection is not None:
        return _docs_collection

    try:
        _docs_collection = client.get_or_create_collection(
            "docs_collection", metadata={"type": "docs_catalog"}
        )
    except Exception:
        _docs_collection = client.get_or_create_collection("docs_collection")
    return _docs_collection
