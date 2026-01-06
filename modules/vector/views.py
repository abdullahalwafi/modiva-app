# modules/vector/views.py
import os
import io
import json
import re
import fitz  # PyMuPDF
import pandas as pd
from docx import Document as DocxDocument

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Document, DocumentChunk

# chroma & embedding lazy imports to avoid heavy work at import-time
_chroma_client = None
_chroma_collection = None
_model = None

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

def get_chroma():
    """
    Lazy init Chroma client & collection.
    Uses env:
      CHROMA_PERSIST_DIR (default ./chroma_db)
      CHROMA_COLLECTION_NAME (default rag_collection)
    """
    global _chroma_client, _chroma_collection
    if _chroma_client is not None and _chroma_collection is not None:
        return _chroma_client, _chroma_collection

    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
    coll_name = os.environ.get("CHROMA_COLLECTION_NAME", "rag_collection")

    try:
        import chromadb
        # try persistent client first (new API)
        try:
            from chromadb import PersistentClient
            _chroma_client = PersistentClient(path=persist_dir)
            _chroma_collection = _chroma_client.get_or_create_collection(coll_name)
            print(f"[Chroma] PersistentClient siap. dir={persist_dir}, coll={coll_name}")
            return _chroma_client, _chroma_collection
        except Exception:
            # fallback to in-memory client
            _chroma_client = chromadb.Client()
            _chroma_collection = _chroma_client.get_or_create_collection(coll_name)
            print("[Chroma] In-memory client siap.")
            return _chroma_client, _chroma_collection
    except Exception as e:
        print("[Chroma] Chroma tidak tersedia:", repr(e))
        _chroma_client = None
        _chroma_collection = None
        return None, None

# -------------------------
# Helpers: parsing & extraction
# -------------------------
def split_to_sentences(text: str):
    parts = []
    for chunk in text.replace("\r", "\n").split("\n"):
        chunk = chunk.strip()
        if not chunk:
            continue
        for seg in re.split(r'(?<=[.?!])\s+', chunk):
            s = seg.strip()
            if s:
                parts.append(s)
    return parts

def extract_text_from_file(uploaded_file):
    """
    Extract plain text rows from PDF / DOCX / Excel.
    Returns list[str] (each element = one "row"/chunk to index).
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
        # use pandas to read sheets
        try:
            xls = pd.read_excel(uploaded_file, sheet_name=None, engine="openpyxl")
        except Exception:
            # fallback single-sheet
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            xls = {"Sheet1": df}
        for sheet_name, df in xls.items():
            df = df.fillna("")
            # headers used to form "k: v" pairs per row
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

def parse_content_to_record(content: str):
    """
    If content is JSON string or dict, return (meta_dict, doc_text).
    Otherwise return ({"content": content}, content).
    """
    if isinstance(content, dict):
        doc_text = " ".join([str(v) for v in content.values()])
        return content, doc_text
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                doc_text = " ".join([str(v) for v in parsed.values()])
                return parsed, doc_text
        except Exception:
            pass
    return {"content": content}, str(content)

# -------------------------
# Rebuild Chroma from DB
# -------------------------
def rebuild_chroma_from_db():
    """
    Rebuild collection from DocumentChunk DB rows.
    Returns total added chunks.
    """
    client, coll = get_chroma()
    if client is None or coll is None:
        raise RuntimeError("Chroma client belum tersedia. Cek konfigurasi.")

    # determine collection name safely
    try:
        coll_name = coll.name
    except Exception:
        coll_name = os.environ.get("CHROMA_COLLECTION_NAME", "rag_collection")

    # recreate collection (safe)
    try:
        try:
            # some versions: client.delete_collection(name)
            client.delete_collection(coll_name)
        except Exception:
            # ignore if not supported
            pass
        coll = client.get_or_create_collection(coll_name, metadata={"hints": "document chunks"})
    except Exception as e:
        print("[Chroma] Gagal recreate collection:", repr(e))
        coll = client.get_or_create_collection(coll_name, metadata={"hints": "document chunks"})

    chunks = DocumentChunk.objects.all().order_by("id")
    ids, docs, metadatas, embeddings = [], [], [], []
    total = 0

    for chunk in chunks:
        meta_dict, doc_text = parse_content_to_record(chunk.content)
        doc_text = str(doc_text).strip()
        if not doc_text:
            continue
        try:
            emb = embed(doc_text)
        except Exception:
            print(f"[Chroma] Embed gagal untuk chunk {chunk.id}, skip.")
            continue

        ids.append(str(chunk.id))
        docs.append(doc_text)
        meta = {
            **{k: v for k, v in meta_dict.items() if not str(k).startswith("_")},
            "_chunk_id": str(chunk.id),
            "_document_id": str(getattr(chunk, "document_id", "")),
        }
        metadatas.append(meta)
        embeddings.append(emb)
        total += 1

    if ids:
        try:
            coll.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)
        except Exception as e:
            # try alternative param names if coll.add signature differs
            try:
                coll.add(documents=docs, metadatas=metadatas, ids=ids, embeddings=embeddings)
            except Exception as e2:
                print("[Chroma] coll.add() gagal:", repr(e2))
                raise

    print(f"[Chroma] Rebuild selesai, total chunks ditambahkan: {total}")
    return total

# -------------------------
# Views: upload / delete / rebuild / search
# -------------------------
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

        document = Document.objects.create(title=uploaded_file.name)
        added = 0

        ids_batch, docs_batch, metas_batch, embs_batch = [], [], [], []
        client, coll = get_chroma()

        # Save to DB first always
        for row_text in extracted_rows:
            chunk = DocumentChunk.objects.create(document=document, content=row_text)
            added += 1

            # if chroma ready, also add to collection incrementally
            if client is not None and coll is not None:
                try:
                    meta = {"_chunk_id": str(chunk.id), "_document_id": str(document.id)}
                    emb = embed(row_text)
                    ids_batch.append(str(chunk.id))
                    docs_batch.append(row_text)
                    metas_batch.append(meta)
                    embs_batch.append(emb)
                except Exception as e:
                    print("[Chroma] Gagal embed/add chunk:", repr(e))

        if ids_batch and client is not None and coll is not None:
            try:
                coll.add(ids=ids_batch, documents=docs_batch, metadatas=metas_batch, embeddings=embs_batch)
            except Exception as e:
                try:
                    coll.add(documents=docs_batch, metadatas=metas_batch, ids=ids_batch, embeddings=embs_batch)
                except Exception as e2:
                    print("[Chroma] coll.add incremental gagal:", repr(e2))

        messages.success(request, f"Dokumen '{uploaded_file.name}' berhasil diunggah. Baris terbaca: {added}")
        return redirect("vector:upload_page")

    docs = Document.objects.all().order_by("-id")
    return render(request, "vector/upload.html", {"docs": docs})

@login_required
def delete_document(request, doc_id):
    user = request.user
    if not user.groups.filter(name="Administrator").exists():
        messages.error(request, "Kamu tidak memiliki izin untuk menghapus dokumen.")
        return redirect("vector:upload_page")

    document = get_object_or_404(Document, id=doc_id)
    chunk_qs = DocumentChunk.objects.filter(document=document)
    chunk_ids = [str(c.id) for c in chunk_qs]

    chunk_qs.delete()
    document.delete()

    client, coll = get_chroma()
    if client is None or coll is None:
        # rebuild later
        try:
            rebuild_chroma_from_db()
        except Exception as e:
            print("[Chroma] Gagal rebuild setelah delete:", repr(e))
    else:
        try:
            # try delete by ids
            try:
                coll.delete(ids=chunk_ids)
            except Exception:
                # if coll.delete not available, rebuild whole index
                rebuild_chroma_from_db()
        except Exception as e:
            print("[Chroma] Hapus IDs gagal, akan rebuild:", repr(e))
            try:
                rebuild_chroma_from_db()
            except Exception as e2:
                print("[Chroma] Gagal rebuild:", repr(e2))

    messages.success(request, f"Dokumen '{document.title}' berhasil dihapus dan index diperbarui.")
    return redirect("vector:upload_page")

@login_required
def rebuild_index(request):
    user = request.user
    if not user.groups.filter(name="Administrator").exists():
        messages.error(request, "Kamu tidak memiliki izin untuk rebuild index.")
        return redirect("vector:upload_page")

    try:
        total = rebuild_chroma_from_db()
        messages.success(request, f"Chroma index berhasil dibangun ulang ({total} chunks).")
    except Exception as e:
        messages.error(request, f"Gagal rebuild index: {e}")
    return redirect("vector:upload_page")

# -------------------------
# Search endpoint (hanya baca dari dokumen; jika tidak ada jawaban -> "Tidak tahu")
# -------------------------
def search_query(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"error": "Query kosong"}, status=400)

    n = int(request.GET.get("n", 5))
    threshold = float(request.GET.get("threshold", 0.60))

    q_emb = embed(q)

    client, coll = get_chroma()
    # fallback: search DB substring + sentence scoring
    def best_sentence_from_text(doc_text, q_emb_local):
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

    if client is None or coll is None:
        # scan DB
        for chunk in DocumentChunk.objects.all():
            try:
                meta_dict, doc_text = parse_content_to_record(chunk.content)
            except Exception:
                doc_text = str(chunk.content)
            sent, score = best_sentence_from_text(str(doc_text), q_emb)
            if sent and score >= threshold:
                return JsonResponse({"answer": sent, "source": {"chunk_id": str(chunk.id), "document_id": str(chunk.document_id)}})
        return JsonResponse({"answer": "Tidak tahu"})

    # try Chroma query
    try:
        results = coll.query(query_embeddings=[q_emb], n_results=n)
    except Exception:
        # some chroma versions expect query_texts
        try:
            results = coll.query(query_texts=[q], n_results=n)
        except Exception:
            # fallback DB
            for chunk in DocumentChunk.objects.all():
                try:
                    meta_dict, doc_text = parse_content_to_record(chunk.content)
                except Exception:
                    doc_text = str(chunk.content)
                sent, score = best_sentence_from_text(str(doc_text), q_emb)
                if sent and score >= threshold:
                    return JsonResponse({"answer": sent, "source": {"chunk_id": str(chunk.id), "document_id": str(chunk.document_id)}})
            return JsonResponse({"answer": "Tidak tahu"})

    # normalize results structure
    ids = results.get("ids", [[]])[0] if isinstance(results.get("ids", []), list) else results.get("ids", [])
    docs = results.get("documents", [[]])[0] if isinstance(results.get("documents", []), list) else results.get("documents", [])
    metadatas = results.get("metadatas", [[]])[0] if isinstance(results.get("metadatas", []), list) else results.get("metadatas", [])
    # evaluate documents for best sentence
    best_overall = None
    for idx, doc_text in enumerate(docs):
        if isinstance(doc_text, dict):
            doc_text = " ".join([str(v) for v in doc_text.values()])
        sent, score = best_sentence_from_text(str(doc_text), q_emb)
        meta = metadatas[idx] if idx < len(metadatas) else {}
        cid = ids[idx] if idx < len(ids) else None
        if sent and score >= threshold:
            return JsonResponse({"answer": sent, "source": {"chunk_id": cid, "metadata": meta}})
        if sent and (best_overall is None or score > best_overall[0]):
            best_overall = (score, sent, meta, cid)

    return JsonResponse({"answer": "Tidak tahu"})
