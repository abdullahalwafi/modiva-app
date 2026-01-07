import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
GROQ_URL = os.getenv("GROQ_URL")

SYSTEM_WITH_CONTEXT = (
    "Kamu adalah asisten ekstraksi informasi dari dokumen. "
    "Jawab pertanyaan dengan mengambil informasi yang ada di REFERENSI. "
    "Jika pertanyaan menanyakan 'siapa', jawab minimal: Nama, lokasi (jika ada), kontak (jika ada), ringkasan singkat. "
    "Jika benar-benar tidak ada di referensi, jawab 'Tidak tahu'. "
    "Wajib bahasa indonesia dan full HTML. "
    "kalo ada kalimat atau paragraf yang menggunakan bahasa selain indonesia, tolong translate ke indonesia"
    "Jangan menyebutkan dokumen atau sumber. Gunakan HTML rapi."
)

SYSTEM_NO_CONTEXT = (
    "Jika benar-benar tidak ada, jawab 'Tidak tahu'. "
    "Wajib bahasa indonesia dan full HTML. "
    "Jangan menyebutkan dokumen atau sumber. Gunakan HTML rapi. "
    "kalo ada kalimat atau paragraf yang menggunakan bahasa selain indonesia, tolong translate ke indonesia"
)

def ask_groq(user_message: str, context_text: str | None, temperature_with_ctx=0.1, temperature_no_ctx=0.5):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    if context_text and context_text.strip():
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_WITH_CONTEXT},
                {"role": "user", "content": (
                    f"Pertanyaan: {user_message}\n\n"
                    f"REFERENSI (gunakan untuk menjawab):\n{context_text}\n\n"
                    "Instruksi: Jawab berdasarkan referensi di atas."
                )},
            ],
            "temperature": float(temperature_with_ctx),
        }
    else:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_NO_CONTEXT},
                {"role": "user", "content": user_message},
            ],
            "temperature": float(temperature_no_ctx),
        }

    return requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
