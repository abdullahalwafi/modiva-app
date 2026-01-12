import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
GROQ_URL = os.getenv("GROQ_URL")

SYSTEM_WITH_CONTEXT = (
    "Kamu adalah asisten ekstraksi informasi dari dokumen. "
    "Jawab singkat (1-3 kalimat), spesifik, dan langsung ke inti. "
    "Jawaban wajib hanya berdasarkan REFERENSI, jangan menambahkan informasi di luar referensi. "
    "Jika pertanyaan tentang HB/hemoglobin siswa, wajib cantumkan: Nama, NIS, Sekolah, Tahun, Hb, dan Status (keterangan). "
    "Jika ada lebih dari satu data (tahun berbeda), tampilkan semuanya per tahun. "
    "Jika tidak ada informasi yang menjawab, balas persis: 'Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen.' "
    "Jangan menyebutkan dokumen atau sumber. Wajib bahasa indonesia dan full HTML. Gunakan HTML rapi."
)

SYSTEM_NO_CONTEXT = (
    "Jika benar-benar tidak ada, jawab persis: 'Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen.' "
    "Jangan menyebutkan dokumen atau sumber. Wajib bahasa indonesia dan full HTML. Gunakan HTML rapi."
)

def ask_groq(user_message: str, context_text: str | None, temperature_with_ctx=0.0, temperature_no_ctx=0.0):
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
