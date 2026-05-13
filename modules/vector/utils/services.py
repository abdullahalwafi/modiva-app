import uuid
from datetime import datetime, timezone

from .chroma import get_chroma, get_docs_collection
from .cleaner import clean_row_text
from .embedding import embed
from .extractors import extract_text_from_file
from .text import guess_source_type, split_to_sentences

def list_docs_from_chroma():
    docs_coll = get_docs_collection()
    try:
        res = docs_coll.get(include=["metadatas", "documents", "ids"])
    except Exception:
        res = docs_coll.get()

    ids = res.get("ids", []) or []
    metas = res.get("metadatas", []) or []
    docs = res.get("documents", []) or []

    out = []
    for i, doc_id in enumerate(ids):
        meta = metas[i] if i < len(metas) and metas[i] is not None else {}
        title = meta.get("title") or (docs[i] if i < len(docs) else "") or str(doc_id)
        created_at_raw = meta.get("created_at") or ""
        uploaded_at = None
        if created_at_raw:
            try:
                uploaded_at = datetime.fromisoformat(str(created_at_raw))
            except Exception:
                uploaded_at = None
        out.append(
            {
                "id": str(doc_id),
                "title": str(title),
                "uploaded_at": uploaded_at,
                "created_at": str(created_at_raw),
                "source_type": str(meta.get("source_type") or ""),
            }
        )

    out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return out


def upload_document_to_chroma(uploaded_file):
    extracted_rows = extract_text_from_file(uploaded_file)
    if not extracted_rows:
        return {"ok": False, "error": "Tidak ada data teks yang bisa diekstrak dari dokumen."}

    _, rag = get_chroma()
    docs_coll = get_docs_collection()

    doc_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    filename_lower = uploaded_file.name.lower()
    source_type = guess_source_type(filename_lower)

    ids_batch, docs_batch, metas_batch, embs_batch = [], [], [], []
    added = 0
    cleaned_by_ai = 0
    raw_fallback = 0

    for idx, row_text in enumerate(extracted_rows):
        row_text = str(row_text).strip()
        if not row_text:
            continue

        cleaned_text, clean_mode = clean_row_text(row_text)
        if not cleaned_text:
            continue

        if clean_mode == "cleaner_ai":
            cleaned_by_ai += 1
        else:
            raw_fallback += 1

        chunk_id = f"{doc_id}:{idx}"
        meta = {
            "doc_id": doc_id,
            "title": uploaded_file.name,
            "created_at": created_at,
            "source_type": source_type,
            "chunk_index": int(idx),
            "clean_mode": clean_mode,
            "raw_length": int(len(row_text)),
            "clean_length": int(len(cleaned_text)),
        }

        emb = embed(cleaned_text)
        ids_batch.append(chunk_id)
        docs_batch.append(cleaned_text)
        metas_batch.append(meta)
        embs_batch.append(emb)
        added += 1

    if not ids_batch:
        return {"ok": False, "error": "Gagal membuat embedding (tidak ada chunk valid)."}

    # commit chunks
    rag.add(ids=ids_batch, documents=docs_batch, metadatas=metas_batch, embeddings=embs_batch)

    # catalog doc (kalau gagal, jangan bikin upload gagal)
    try:
        docs_coll.add(
            ids=[doc_id],
            documents=[uploaded_file.name],
                metadatas=[{
                    "doc_id": doc_id,
                    "title": uploaded_file.name,
                    "created_at": created_at,
                    "source_type": source_type,
                    "chunks": int(added),
                    "cleaned_by_ai": int(cleaned_by_ai),
                    "raw_fallback": int(raw_fallback),
                }],
        )
    except Exception:
        pass

    return {
        "ok": True,
        "doc_id": doc_id,
        "chunks": added,
        "title": uploaded_file.name,
        "cleaned_by_ai": cleaned_by_ai,
        "raw_fallback": raw_fallback,
    }


def delete_document_from_chroma(doc_id: str):
    _, rag = get_chroma()
    docs_coll = get_docs_collection()

    chunk_ids = []
    try:
        res = rag.get(where={"doc_id": str(doc_id)}, include=["ids"])
        chunk_ids = res.get("ids", []) or []
    except Exception:
        chunk_ids = []

    if chunk_ids:
        rag.delete(ids=chunk_ids)
    else:
        # fallback delete by where (kalau didukung)
        try:
            rag.delete(where={"doc_id": str(doc_id)})
        except Exception:
            pass

    try:
        docs_coll.delete(ids=[str(doc_id)])
    except Exception:
        pass

    return {"ok": True}


def healthcheck_counts():
    _, rag = get_chroma()
    docs_coll = get_docs_collection()
    rag_count = rag.count() if hasattr(rag, "count") else None
    docs_count = docs_coll.count() if hasattr(docs_coll, "count") else None
    return {"docs_collection": docs_count, "rag_collection": rag_count}


def search_answer(q: str, n: int = 5, threshold: float = 0.60):
    """
    Cari jawaban terbaik dari ChromaDB menggunakan native vector query.
    Lebih cepat karena tidak re-encode semua chunk di memori.
    """
    _, rag = get_chroma()
    q_emb = embed(q)

    results = rag.query(
        query_embeddings=[q_emb],
        n_results=n,
        include=["documents", "metadatas", "ids", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not docs:
        return {"answer": "Tidak tahu"}

    # Ambil chunk terbaik (jarak terkecil = paling mirip)
    best_doc = docs[0]
    best_meta = metas[0] if metas else {}
    best_cid = ids[0] if ids else None
    best_sim = 1.0 - float(distances[0]) if distances else 0.0

    if best_sim < threshold:
        return {"answer": "Tidak tahu"}

    # Pilih kalimat terbaik dari chunk teratas dengan keyword matching
    best_sent = _pick_best_sentence(best_doc, q)
    answer = best_sent if best_sent else best_doc.strip()

    return {"answer": answer, "source": {"chunk_id": best_cid, "metadata": best_meta}}


def _pick_best_sentence(doc_text: str, query: str) -> str:
    """Pilih kalimat paling relevan dari chunk menggunakan keyword overlap."""
    sents = split_to_sentences(doc_text)
    if not sents:
        return doc_text.strip()

    q_words = set(query.lower().split())
    best, best_score = sents[0], -1
    for s in sents:
        s_words = set(s.lower().split())
        score = len(q_words & s_words)
        if score > best_score:
            best_score = score
            best = s
    return best.strip()
