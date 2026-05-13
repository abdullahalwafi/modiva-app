import numpy as np

from modules.vector.utils.embedding import embed
from .keywords import extract_keywords


def build_context_fullscan(collection, user_message: str, max_chunks: int = 8, min_similarity: float = 0.35):
    """
    Retrieval menggunakan ChromaDB native vector search (HNSW index).
    Jauh lebih cepat dari full-scan — tidak perlu load semua dokumen ke RAM.

    Strategi:
    1) Vector query via ChromaDB → ambil top-N chunk paling relevan
    2) Keyword re-ranking untuk boost chunk yang mengandung kata kunci penting
    3) Fallback ke chunk teratas jika tidak ada yang melewati threshold
    """
    if collection is None:
        return "", []

    # --- 1. Embed query & vector search via ChromaDB ---
    q_emb = embed(user_message)
    try:
        results = collection.query(
            query_embeddings=[q_emb],
            n_results=min(max_chunks * 2, 20),  # ambil 2x lebih banyak dulu, lalu filter
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return "", []

    docs = results.get("documents", [[]])[0] or []
    metas = results.get("metadatas", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []

    if not docs:
        return "", []

    query_low = user_message.lower()

    def is_hb_specific_question() -> bool:
        flags = [
            "hb ",
            "hemoglobin",
            "nis",
            "sekolah",
            "siswi",
            "siswa",
            "nama ",
            "tahun ",
            "status anemia",
        ]
        return any(flag in query_low for flag in flags)

    def noise_penalty(doc_text: str, meta: dict | None) -> int:
        text = str(doc_text).strip()
        low = text.lower()
        penalty = 0

        if meta and meta.get("type") == "hb" and not is_hb_specific_question():
            penalty += 8

        noisy_markers = [
            "buku saku pencegahan anemia",
            "kemenkes ri",
            "lampiran",
            "bagian 2",
            "616.152",
        ]
        penalty += sum(2 for marker in noisy_markers if marker in low)

        if len(text) < 40:
            penalty += 4
        if len(text.split()) < 8:
            penalty += 3
        if "\n" in text and text.count("\n") >= 5:
            penalty += 2
        if "data: nama=" in low and not is_hb_specific_question():
            penalty += 5

        return penalty

    # --- 2. Filter berdasarkan similarity threshold ---
    # ChromaDB mengembalikan cosine distance (0=sama, 2=berlawanan)
    # similarity = 1 - distance (untuk cosine)
    candidates = []
    for doc, meta, dist in zip(docs, metas, distances):
        similarity = 1.0 - float(dist)
        if not str(doc).strip():
            continue
        candidates.append((similarity, doc, meta or {}))

    if not candidates:
        return "", []

    # --- 3. Keyword re-ranking: boost chunk yang mengandung kata kunci ---
    keywords = [kw.lower() for kw in extract_keywords(user_message)]

    def keyword_score(doc_text: str) -> int:
        low = doc_text.lower()
        return sum(1 for kw in keywords if kw and kw in low)

    # sort: keyword_score DESC, lalu similarity DESC, lalu noise penalty ASC
    candidates.sort(
        key=lambda x: (
            -(keyword_score(x[1]) * 3),
            -x[0],
            noise_penalty(x[1], x[2]),
        )
    )

    # --- 4. Ambil top max_chunks yang melewati threshold ---
    top_docs, top_metas = [], []
    for sim, doc, meta in candidates:
        if noise_penalty(doc, meta) >= 8 and top_docs:
            continue
        if sim >= min_similarity or not top_docs:  # tetap ambil minimal 1 jika ada hasil
            top_docs.append(doc)
            top_metas.append(meta or {})
        if len(top_docs) >= max_chunks:
            break

    if not top_docs:
        # fallback: ambil chunk teratas meski di bawah threshold
        top_docs = [candidates[0][1]]
        top_metas = [candidates[0][2] or {}]

    return "\n\n".join(top_docs).strip(), top_metas
