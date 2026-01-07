import uuid
from datetime import datetime, timezone

from .chroma import get_chroma, get_docs_collection
from .embedding import embed, get_model
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
        out.append(
            {
                "doc_id": str(doc_id),
                "title": str(title),
                "created_at": str(meta.get("created_at") or ""),
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

    for idx, row_text in enumerate(extracted_rows):
        row_text = str(row_text).strip()
        if not row_text:
            continue

        chunk_id = f"{doc_id}:{idx}"
        meta = {
            "doc_id": doc_id,
            "title": uploaded_file.name,
            "created_at": created_at,
            "source_type": source_type,
            "chunk_index": int(idx),
        }

        emb = embed(row_text)
        ids_batch.append(chunk_id)
        docs_batch.append(row_text)
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
            }],
        )
    except Exception:
        pass

    return {"ok": True, "doc_id": doc_id, "chunks": added, "title": uploaded_file.name}


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
    _, rag = get_chroma()
    q_emb = embed(q)

    def best_sentence_from_text(doc_text: str):
        sents = split_to_sentences(doc_text)
        if not sents:
            return None, 0.0
        try:
            import numpy as np
            sent_embs = get_model().encode(sents)
            sent_embs = np.array(sent_embs).astype("float32")
            qv = np.array(q_emb).astype("float32")
            sent_norms = np.linalg.norm(sent_embs, axis=1) + 1e-12
            q_norm = np.linalg.norm(qv) + 1e-12
            sims = (sent_embs @ qv) / (sent_norms * q_norm)
            idx = int(np.argmax(sims))
            return sents[idx], float(sims[idx])
        except Exception:
            q_lower = q.lower()
            for s in sents:
                if q_lower in s.lower():
                    return s, 1.0
            return None, 0.0

    results = rag.query(query_embeddings=[q_emb], n_results=n, include=["documents", "metadatas", "ids"])

    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    best_overall = None
    for i, doc_text in enumerate(docs):
        sent, score = best_sentence_from_text(str(doc_text))
        meta = metas[i] if i < len(metas) else {}
        cid = ids[i] if i < len(ids) else None

        if sent and score >= threshold:
            return {"answer": sent, "source": {"chunk_id": cid, "metadata": meta}}

        if sent and (best_overall is None or score > best_overall[0]):
            best_overall = (score, sent, meta, cid)

    return {"answer": "Tidak tahu"}
