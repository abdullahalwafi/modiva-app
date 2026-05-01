from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .utils.chroma import ChromaUnavailable, get_chroma, get_docs_collection
from .utils.services import (
    list_docs_from_chroma,
    upload_document_to_chroma,
    delete_document_from_chroma,
    healthcheck_counts,
    search_answer,
)

def upload_page(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]

        try:
            client, rag = get_chroma()
            docs_coll = get_docs_collection()
        except ChromaUnavailable as e:
            messages.error(request, f"Chroma belum siap / tidak tersedia: {e}")
            return redirect("vector:upload_page")

        if client is None or rag is None or docs_coll is None:
            messages.error(request, "Chroma belum siap / tidak tersedia. Cek instalasi & konfigurasi.")
            return redirect("vector:upload_page")

        try:
            res = upload_document_to_chroma(uploaded_file)
        except ValueError:
            messages.error(request, "Format file tidak didukung. Gunakan PDF, DOCX, atau Excel.")
            return redirect("vector:upload_page")
        except Exception as e:
            messages.error(request, f"Gagal upload: {e}")
            return redirect("vector:upload_page")

        if not res.get("ok"):
            messages.error(request, res.get("error", "Gagal upload"))
            return redirect("vector:upload_page")

        messages.success(request, f"Dokumen '{res['title']}' berhasil diunggah. Chunks tersimpan: {res['chunks']}")
        return redirect("vector:upload_page")

    chroma_error = None
    try:
        docs = list_docs_from_chroma()
    except ChromaUnavailable as e:
        chroma_error = str(e)
        docs = []

    return render(request, "vector/upload.html", {"docs": docs, "chroma_error": chroma_error})


@login_required
def delete_document(request, doc_id):
    ALLOWED_DELETE_GROUPS = ["Administrator", "Puskesmas"]

    if not request.user.groups.filter(name__in=ALLOWED_DELETE_GROUPS).exists():
        messages.error(request, "Kamu tidak memiliki izin untuk menghapus dokumen.")
        return redirect("vector:upload_page")
    try:
        delete_document_from_chroma(str(doc_id))
        messages.success(request, f"Dokumen (doc_id={doc_id}) berhasil dihapus dari Chroma.")
    except Exception as e:
        messages.error(request, f"Gagal hapus dokumen: {e}")

    return redirect("vector:upload_page")


@login_required
def rebuild_index(request):
    ALLOWED_DELETE_GROUPS = ["Administrator", "Puskesmas"]

    if not request.user.groups.filter(name__in=ALLOWED_DELETE_GROUPS).exists():
        messages.error(request, "Kamu tidak memiliki izin untuk rebuild index.")
        return redirect("vector:upload_page")

    try:
        counts = healthcheck_counts()
        messages.success(
            request,
            f"Chroma OK. docs_collection={counts['docs_collection']}, rag_collection={counts['rag_collection']}"
        )
    except Exception as e:
        messages.error(request, f"Gagal cek index: {e}")

    return redirect("vector:upload_page")


def search_query(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"error": "Query kosong"}, status=400)

    n = int(request.GET.get("n", 5))
    threshold = float(request.GET.get("threshold", 0.60))

    try:
        res = search_answer(q=q, n=n, threshold=threshold)
        return JsonResponse(res)
    except Exception:
        return JsonResponse({"answer": "Tidak tahu"})
