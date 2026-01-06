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
import numpy as np

from modules.vector.models import DocumentChunk

# =========================
# CHROMA (in-memory / optional persistent)
# =========================
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# in-memory (boleh diganti ke persistent)
client = chromadb.Client()

COLLECTION_NAME = "rag_collection"

# model embedding nyata (lebih akurat)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text: str) -> np.ndarray:
    """Embedding asli, tidak lagi dummy."""
    emb = embedder.encode([text])[0]
    return emb.astype("float32")

def get_collection():
    try:
        return client.get_collection(name=COLLECTION_NAME)
    except Exception:
        return client.create_collection(name=COLLECTION_NAME)

def rebuild_chroma_index():
    """Build ulang Chroma dari DocumentChunk."""
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except:
        pass

    collection = client.create_collection(name=COLLECTION_NAME)

    chunks = DocumentChunk.objects.all().order_by("id")
    if not chunks:
        return

    ids = []
    docs = []
    metadatas = []
    embeddings = []

    for chunk in chunks:
        ids.append(str(chunk.id))
        docs.append(chunk.content)
        metadatas.append({
            "id": str(chunk.id),
        })
        embeddings.append(embed(chunk.content).tolist())

    collection.add(
        ids=ids,
        documents=docs,
        metadatas=metadatas,
        embeddings=embeddings
    )

# build index sekali di awal
rebuild_chroma_index()

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

        # Default
        reply = None

        # 🔎 Chroma Vector Search
        collection = get_collection()

        try:
            q_emb = embed(user_message).tolist()
            results = collection.query(
                query_embeddings=[q_emb],
                n_results=3,
                include=["documents"]
            )
            docs = results["documents"][0] if results.get("documents") else []
            context_text = "\n\n".join(docs)
        except Exception as e:
            print("Chroma error:", e)
            context_text = ""

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
