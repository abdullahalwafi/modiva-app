# modules/vector/views.py  (CHROMA-ONLY VERSION)

import os
import io
import json
import re
import uuid
from datetime import datetime, timezone

import fitz  # PyMuPDF
import pandas as pd
from docx import Document as DocxDocument

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# chroma & embedding lazy imports to avoid heavy work at import-time
_chroma_client = None
_rag_collection = None
_docs_collection = None
_model = None


# =========================================================
# Embedding
# =========================================================
def get_model():
    """Lazy load sentence-transformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        model_name = os.environ.get("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
        _model = SentenceTransformer(model_name)
    return _model


def embed(text: str):
    """Return embedding as list[float32]."""
    m = get_model()
    emb = m.encode([text])[0]
    return emb.astype("float32").tolist()


# =========================================================
# Chroma init (persistent)
# =========================================================
def get_chroma():
    """
    Lazy init Chroma client & the main RAG collection.
    Uses env:
      CHROMA_PERSIST_DIR (default ./chroma_db)
      CHROMA_COLLECTION_NAME (default rag_collection)
    """
    global _chroma_client, _rag_collection

    if _chroma_client is not None and _rag_collection is not None:
        return _chroma_client, _rag_collection

    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
    coll_name = os.environ.get("CHROMA_COLLECTION_NAME", "rag_collection")

    try:
        from chromadb import PersistentClient

        _chroma_client = PersistentClient(path=persist_dir)
        _rag_collection = _chroma_client.get_or_create_collection(
            coll_name, metadata={"type": "rag_chunks"}
        )
        print(f"[Chroma] PersistentClient siap. dir={persist_dir}, coll={coll_name}")
        return _chroma_client, _rag_collection
    except Exception as e:
        print("[Chroma] Chroma tidak tersedia:", repr(e))
        _chroma_client = None
        _rag_collection = None
        return None, None


def get_docs_collection():
    """
    Collection khusus untuk daftar dokumen (catalog) agar halaman upload bisa list dokumen.
    Masih persist di folder CHROMA_PERSIST_DIR.
    """
    global _docs_collection
    client, _ = get_chroma()
    if client is None:
        return None

    if _docs_collection is not None:
        return _docs_collection

    try:
        _docs_collection = client.get_or_create_collection(
            "docs_collection", metadata={"type": "docs_catalog"}
        )
    except Exception:
        # fallback name (kalau ada aturan tertentu di versi chroma)
        _docs_collection = client.get_or_create_collection("docs_collection")
    return _docs_collection


# =========================================================
# Helpers: parsing & extraction
# =========================================================
def split_to_sentences(text: str):
    parts = []
    for chunk in text.replace("\r", "\n").split("\n"):
        chunk = chunk.strip()
        if not chunk:
            continue
        for seg in re.split(r"(?<=[.?!])\s+", chunk):
            s = seg.strip()
            if s:
                parts.append(s)
    return parts


def extract_text_from_file(uploaded_file):
    """
    Extract plain text rows from PDF / DOCX / Excel.
    Returns list[str] (each element = one chunk to index).
    """
    filename = uploaded_file.name.lower()
    extracted_rows = []

    # PDF
    if filename.endswith(".pdf"):
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            text = page.get_text("text").strip()
            if text:
                extracted_rows.append(text)

    # Word docx
    elif filename.endswith(".docx"):
        uploaded_file.seek(0)
        file_stream = io.BytesIO(uploaded_file.read())
        doc = DocxDocument(file_stream)
        for para in doc.paragraphs:
            if para.text.strip():
                extracted_rows.append(para.text.strip())

    # Excel (xlsx/xls)
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        uploaded_file.seek(0)
        try:
            xls = pd.read_excel(uploaded_file, sheet_name=None, engine="openpyxl")
        except Exception:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            xls = {"Sheet1": df}

        for sheet_name, df in xls.items():
            df = df.fillna("")
            headers = [str(c).strip() for c in df.columns]
            for _, row in df.iterrows():
                pairs = []
                for h, v in zip(headers, row):
                    if str(v).strip() != "":
                        pairs.append(f"{h}: {v}")
                if pairs:
                    extracted_rows.append(", ".join(pairs))

    else:
        raise ValueError("Format file tidak didukung.")

    return extracted_rows


def guess_source_type(filename_lower: str) -> str:
    if filename_lower.endswith(".pdf"):
        return "pdf"
    if filename_lower.endswith(".docx"):
        return "docx"
    if filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        return "excel"
    return "unknown"


# =========================================================
# (Compatibility stub) Rebuild from DB
# =========================================================
def rebuild_chroma_from_db():
    """
    CHROMA-ONLY: Tidak ada DB source lagi.
    Fungsi ini dipertahankan agar import dari modul lain tidak error.
    """
    # Kalau kamu sudah update modul lain, fungsi ini bisa dihapus.
    print("[Chroma] rebuild_chroma_from_db() dipanggil, tapi mode CHROMA-ONLY (noop).")
    return 0


# =========================================================
# Internal: list docs from docs_collection
# =========================================================
def list_docs_from_chroma():
    docs_coll = get_docs_collection()
    if docs_coll is None:
        return []

    try:
        res = docs_coll.get(include=["metadatas", "documents", "ids"])
    except Exception:
        # beberapa versi chroma: include optional
        res = docs_coll.get()

    ids = res.get("ids", []) or []
    metas = res.get("metadatas", []) or []
    docs = res.get("documents", []) or []

    out = []
    for i, doc_id in enumerate(ids):
        meta = metas[i] if i < len(metas) and metas[i] is not None else {}
        title = meta.get("title") or (docs[i] if i < len(docs) else "") or str(doc_id)
        created_at = meta.get("created_at") or ""
        source_type = meta.get("source_type") or ""
        out.append(
            {
                "doc_id": str(doc_id),
                "title": str(title),
                "created_at": str(created_at),
                "source_type": str(source_type),
            }
        )

    # sort newest first (string ISO8601 works for ordering)
    out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return out


# =========================================================
# Views: upload / delete / search (CHROMA-ONLY)
# =========================================================
def upload_page(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]

        try:
            extracted_rows = extract_text_from_file(uploaded_file)
        except ValueError:
            messages.error(request, "Format file tidak didukung. Gunakan PDF, DOCX, atau Excel.")
            return redirect("vector:upload_page")

        if not extracted_rows:
            messages.error(request, "Tidak ada data teks yang bisa diekstrak dari dokumen.")
            return redirect("vector:upload_page")

        client, rag = get_chroma()
        docs_coll = get_docs_collection()
        if client is None or rag is None or docs_coll is None:
            messages.error(request, "Chroma belum siap / tidak tersedia. Cek instalasi & konfigurasi.")
            return redirect("vector:upload_page")

        # generate doc_id & metadata
        doc_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        filename_lower = uploaded_file.name.lower()
        source_type = guess_source_type(filename_lower)

        # add chunks to rag_collection
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

            try:
                emb = embed(row_text)
            except Exception as e:
                print("[Chroma] Embed gagal:", repr(e))
                continue

            ids_batch.append(chunk_id)
            docs_batch.append(row_text)
            metas_batch.append(meta)
            embs_batch.append(emb)
            added += 1

        if not ids_batch:
            messages.error(request, "Gagal membuat embedding (tidak ada chunk valid).")
            return redirect("vector:upload_page")

        # commit to Chroma
        try:
            rag.add(ids=ids_batch, documents=docs_batch, metadatas=metas_batch, embeddings=embs_batch)
        except Exception as e:
            # try alternative signature
            try:
                rag.add(documents=docs_batch, metadatas=metas_batch, ids=ids_batch, embeddings=embs_batch)
            except Exception as e2:
                print("[Chroma] rag.add gagal:", repr(e2))
                messages.error(request, f"Gagal simpan ke Chroma: {e2}")
                return redirect("vector:upload_page")

        # add doc catalog entry to docs_collection
        try:
            docs_coll.add(
                ids=[doc_id],
                documents=[uploaded_file.name],
                metadatas=[
                    {
                        "doc_id": doc_id,
                        "title": uploaded_file.name,
                        "created_at": created_at,
                        "source_type": source_type,
                        "chunks": int(added),
                    }
                ],
            )
        except Exception as e:
            # kalau gagal catalog, chunks sudah masuk—beri warning saja
            print("[Chroma] docs_coll.add gagal:", repr(e))

        messages.success(request, f"Dokumen '{uploaded_file.name}' berhasil diunggah. Chunks tersimpan: {added}")
        return redirect("vector:upload_page")

    # GET: list docs from Chroma
    docs = list_docs_from_chroma()
    return render(request, "vector/upload.html", {"docs": docs})


@login_required
def delete_document(request, doc_id):
    user = request.user
    if not user.groups.filter(name="Administrator").exists():
        messages.error(request, "Kamu tidak memiliki izin untuk menghapus dokumen.")
        return redirect("vector:upload_page")

    client, rag = get_chroma()
    docs_coll = get_docs_collection()
    if client is None or rag is None or docs_coll is None:
        messages.error(request, "Chroma belum siap / tidak tersedia.")
        return redirect("vector:upload_page")

    # 1) get all chunk ids for doc_id
    chunk_ids = []
    try:
        res = rag.get(where={"doc_id": str(doc_id)}, include=["ids"])
        chunk_ids = res.get("ids", []) or []
    except Exception:
        # fallback: some versions may not support where on get()
        # last resort: do nothing specific, require rebuild strategy (not available in chroma-only)
        chunk_ids = []

    # 2) delete chunks
    try:
        if chunk_ids:
            rag.delete(ids=chunk_ids)
        else:
            # try delete via where (some versions support)
            try:
                rag.delete(where={"doc_id": str(doc_id)})
            except Exception:
                pass
    except Exception as e:
        print("[Chroma] delete chunks gagal:", repr(e))

    # 3) delete doc catalog record
    try:
        docs_coll.delete(ids=[str(doc_id)])
    except Exception as e:
        print("[Chroma] delete doc catalog gagal:", repr(e))

    messages.success(request, f"Dokumen (doc_id={doc_id}) berhasil dihapus dari Chroma.")
    return redirect("vector:upload_page")


@login_required
def rebuild_index(request):
    """
    CHROMA-ONLY: tidak ada DB source untuk rebuild.
    Endpoint ini dibuat sebagai info/cek.
    """
    user = request.user
    if not user.groups.filter(name="Administrator").exists():
        messages.error(request, "Kamu tidak memiliki izin untuk rebuild index.")
        return redirect("vector:upload_page")

    _, rag = get_chroma()
    docs_coll = get_docs_collection()
    if rag is None or docs_coll is None:
        messages.error(request, "Chroma belum siap / tidak tersedia.")
        return redirect("vector:upload_page")

    try:
        rag_count = rag.count() if hasattr(rag, "count") else None
        docs_count = docs_coll.count() if hasattr(docs_coll, "count") else None
        messages.success(request, f"Chroma OK. docs_collection={docs_count}, rag_collection={rag_count}")
    except Exception as e:
        messages.error(request, f"Gagal cek index: {e}")

    return redirect("vector:upload_page")


# =========================================================
# Search endpoint (CHROMA-only)
# =========================================================
def search_query(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"error": "Query kosong"}, status=400)

    n = int(request.GET.get("n", 5))
    threshold = float(request.GET.get("threshold", 0.60))

    _, rag = get_chroma()
    if rag is None:
        return JsonResponse({"answer": "Tidak tahu"})

    q_emb = embed(q)

    def best_sentence_from_text(doc_text: str, q_emb_local):
        sents = split_to_sentences(doc_text)
        if not sents:
            return None, 0.0
        try:
            sent_embs = get_model().encode(sents)
            import numpy as np

            sent_embs = np.array(sent_embs).astype("float32")
            qv = np.array(q_emb_local).astype("float32")
            sent_norms = np.linalg.norm(sent_embs, axis=1) + 1e-12
            q_norm = np.linalg.norm(qv) + 1e-12
            sims = (sent_embs @ qv) / (sent_norms * q_norm)
            idx = int(np.argmax(sims))
            return sents[idx], float(sims[idx])
        except Exception:
            # fallback substring per sentence
            q_lower = q.lower()
            for s in sents:
                if q_lower in s.lower():
                    return s, 1.0
            return None, 0.0

    # Chroma query
    try:
        results = rag.query(query_embeddings=[q_emb], n_results=n, include=["documents", "metadatas", "ids"])
    except Exception:
        # fallback query_texts for older versions
        try:
            results = rag.query(query_texts=[q], n_results=n, include=["documents", "metadatas", "ids"])
        except Exception:
            return JsonResponse({"answer": "Tidak tahu"})

    ids = results.get("ids", [[]])[0] if isinstance(results.get("ids", []), list) else results.get("ids", [])
    docs = results.get("documents", [[]])[0] if isinstance(results.get("documents", []), list) else results.get("documents", [])
    metas = results.get("metadatas", [[]])[0] if isinstance(results.get("metadatas", []), list) else results.get("metadatas", [])

    best_overall = None
    for i, doc_text in enumerate(docs):
        if isinstance(doc_text, dict):
            doc_text = " ".join([str(v) for v in doc_text.values()])
        sent, score = best_sentence_from_text(str(doc_text), q_emb)
        meta = metas[i] if i < len(metas) else {}
        cid = ids[i] if i < len(ids) else None

        if sent and score >= threshold:
            return JsonResponse(
                {"answer": sent, "source": {"chunk_id": cid, "metadata": meta}}
            )

        if sent and (best_overall is None or score > best_overall[0]):
            best_overall = (score, sent, meta, cid)

    return JsonResponse({"answer": "Tidak tahu"})
