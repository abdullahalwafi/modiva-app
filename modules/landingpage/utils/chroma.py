from modules.vector.utils.chroma import get_chroma

def get_collection():
    client, collection = get_chroma()
    if client is None or collection is None:
        return None
    return collection


def safe_get_all_chunks(collection, page_size: int = 500):
    docs_all, metas_all, ids_all = [], [], []

    try:
        total = collection.count()
    except Exception:
        total = None

    offset = 0
    try:
        while True:
            res = collection.get(
                include=["documents", "metadatas"],
                limit=page_size,
                offset=offset,
            )
            docs = res.get("documents", []) or []
            metas = res.get("metadatas", []) or []
            ids = res.get("ids", []) or []

            if not docs:
                break

            docs_all.extend([str(d) for d in docs])
            metas_all.extend(metas)
            ids_all.extend(ids)

            offset += len(docs)
            if total is not None and offset >= total:
                break

        return docs_all, metas_all, ids_all

    except Exception:
        res = collection.get(include=["documents", "metadatas"])
        return (
            [str(d) for d in (res.get("documents", []) or [])],
            res.get("metadatas", []) or [],
            res.get("ids", []) or [],
        )
