import os

from django.shortcuts import render, get_object_or_404, redirect
from modules.landingpage.models import ContactMessage
from .forms import *
from django.urls import reverse_lazy
from modules.vitamin.models import *
# Create your views here.

def homepage(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('landingpage:pendaftaran_sukses')
    else:
        form = ContactMessageForm()
    return render(request, 'index.html', {'form': form})

def about_us(request):
    return render(request, 'aboutUs.html')

def login(request):
    return render(request, 'login.html')

def lupa_password(request):
    return render(request, 'lupa_password.html')

def password_reset(request):
    return render(request, 'password_reset.html')

def mitra(request):
    try:
        puskesmas2 = Puskesmas.objects.all().order_by('id')[:4]
        sekolah2 = Sekolah.objects.all().order_by('id')[:4]
    except Exception as e:
        puskesmas2 = None
        sekolah2 = None
        print(f"Error occurred: {e}")
    return render(request, 'mitra.html', {'puskesmas2': puskesmas2, 'sekolah2': sekolah2})

def sk(request):
    return render(request, 'sk.html')

def privasi(request):
    return render(request, 'privasi.html')

def puskesmas(request):
    try:
        puskesmas = Puskesmas.objects.all().order_by('id')
    except Exception as e:
        puskesmas = None
        print(f"Error occurred: {e}")
    return render(request, 'puskesmas.html', {'puskesmas': puskesmas})

def sekolah(request):
    try:
        sekolah = Sekolah.objects.all().order_by('id')
    except Exception as e:
        sekolah = None
        print(f"Error occurred: {e}")
    return render(request, 'sekolah.html', {'sekolah': sekolah})

def profilpuskesmas(request, pk):
    puskesmas = get_object_or_404(Puskesmas, id=pk)
    return render(request, 'profil-puskesmas.html', {'puskesmas': puskesmas})

def profilsekolah(request, pk):
    sekolah = get_object_or_404(Sekolah, id=pk)
    return render(request, 'profil-sekolah.html', {'sekolah': sekolah})

def coba(request):
    return render(request, 'coba.html')

def daftar(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('landingpage:pendaftaran_sukses')
    else:
        form = ContactMessageForm()
    return render(request, 'daftar.html', {'form': form})

def pendaftaran_sukses(request):
    return render(request, 'pendaftaran_sukses.html')

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME')
GROQ_URL = os.getenv('GROQ_URL')

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import requests

from modules.vector.models import DocumentChunk
from modules.vector.views import embed, get_chroma, rebuild_chroma_from_db

# =========================
# CHROMA (persistent dari modules.vector)
# =========================
def get_collection():
    """
    Ambil koleksi Chroma shared dari modules.vector.
    Jika belum ada/masih kosong, coba rebuild dari DB.
    """
    client, collection = get_chroma()
    if client is None or collection is None:
        return None

    try:
        # Pastikan koleksi terisi (mis. setelah upload baru)
        if hasattr(collection, "count") and collection.count() == 0:
            rebuild_chroma_from_db()
            _, collection = get_chroma()
    except Exception:
        # Abaikan, tetap gunakan koleksi sekarang
        pass

    return collection

# =========================
# CHAT API
# =========================
@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse(
            {"message": "Chat API endpoint is running. Gunakan POST untuk mengirim pesan."}
        )

    try:
        body = json.loads(request.body.decode("utf-8"))
        user_message = body.get("message", "").strip()
        if not user_message:
            return JsonResponse({"reply": "Pesan kosong."})

        # 🔎 Chroma Vector Search
        collection = get_collection()
        context_text = ""

        if collection is not None:
            try:
                q_emb = embed(user_message)
                results = collection.query(
                    query_embeddings=[q_emb],
                    n_results=3,
                    include=["documents"],
                )
                docs = results.get("documents", [])
                if isinstance(docs, list) and docs and isinstance(docs[0], list):
                    docs = docs[0]
                normalized_docs = []
                for doc in docs:
                    if isinstance(doc, dict):
                        normalized_docs.append(" ".join([str(v) for v in doc.values()]))
                    else:
                        normalized_docs.append(str(doc))
                context_text = "\n\n".join([d for d in normalized_docs if d.strip()])
            except Exception as e:
                print("Chroma error:", e)
                # coba rebuild sekali
                try:
                    rebuild_chroma_from_db()
                    collection = get_collection()
                    if collection is not None:
                        results = collection.query(
                            query_embeddings=[embed(user_message)],
                            n_results=3,
                            include=["documents"],
                        )
                        docs = results.get("documents", [])
                        if isinstance(docs, list) and docs and isinstance(docs[0], list):
                            docs = docs[0]
                        context_text = "\n\n".join([str(d) for d in docs if str(d).strip()])
                except Exception as e2:
                    print("Chroma rebuild/query error:", e2)

        # fallback sederhana lewat DB jika koleksi tidak tersedia / kosong
        if not context_text.strip():
            lower_q = user_message.lower()
            matched = []
            for chunk in DocumentChunk.objects.all().order_by("-id"):
                text = str(chunk.content)
                if lower_q in text.lower():
                    matched.append(text)
                if len(matched) >= 3:
                    break
            context_text = "\n\n".join(matched)

        # ================================
        # Jika ada referensi → RAG
        # ================================
        if context_text.strip():
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Jawab hanya berdasarkan teks berikut. "
                            "Jangan menyebutkan dokumen atau sumber. "
                            "Gunakan HTML rapi."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Pertanyaan: {user_message}\n\nREFERENSI:\n{context_text}",
                    },
                ],
                "temperature": 0.1,
            }
        else:
            # Tanpa referensi → fallback
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": "Jawab langsung, gunakan HTML rapi."
                    },
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.5,
            }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
        data = res.json()
        answer = data["choices"][0]["message"]["content"]

        return JsonResponse({"reply": answer})

    except Exception as e:
        return JsonResponse({"reply": f"Error: {e}"}, status=500)
