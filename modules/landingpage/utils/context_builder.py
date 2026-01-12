import numpy as np

from modules.vector.utils.embedding import embed, get_model
from .chroma import safe_get_all_chunks
from .keywords import extract_keywords

def build_context_fullscan(collection, user_message: str, max_chunks: int = 10, min_similarity: float = 0.2):
    all_docs, all_metas, all_ids = safe_get_all_chunks(collection)
    if not all_docs:
        return "", []

    # 1) keyword match (deterministik)
    keywords = extract_keywords(user_message)
    low_docs = [d.lower() for d in all_docs]

    hits = []
    for kw in keywords:
        kwl = kw.lower()
        for i, dlow in enumerate(low_docs):
            if kwl in dlow:
                hits.append(i)

    if hits:
        uniq, seen = [], set()
        src = []
        for h in hits:
            doc_text = all_docs[h]
            key = doc_text[:200].lower()
            if key in seen:
                continue
            seen.add(key)
            uniq.append(doc_text)
            src.append(all_metas[h] if h < len(all_metas) else {})
            if len(uniq) >= max_chunks:
                break
        return "\n\n".join(uniq).strip(), src

    # 2) embedding fallback (mahal, tapi sesuai konsep fullscan kamu)
    q_emb = np.array(embed(user_message), dtype=np.float32)
    model = get_model()

    embs = model.encode(all_docs, batch_size=64, show_progress_bar=False)
    embs = np.array(embs, dtype=np.float32)

    doc_norm = np.linalg.norm(embs, axis=1) + 1e-12
    q_norm = np.linalg.norm(q_emb) + 1e-12
    sims = (embs @ q_emb) / (doc_norm * q_norm)

    max_sim = float(np.max(sims)) if sims.size else 0.0
    if max_sim < min_similarity:
        return "", []

    top_idx = np.argsort(-sims)[:max_chunks]
    top_docs = []
    src = []
    for i in top_idx:
        doc_text = all_docs[int(i)]
        if not str(doc_text).strip():
            continue
        top_docs.append(doc_text)
        src.append(all_metas[int(i)] if int(i) < len(all_metas) else {})
    return "\n\n".join(top_docs).strip(), src
