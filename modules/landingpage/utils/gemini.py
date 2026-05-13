import os

import requests


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
# URL selalu build dari GEMINI_MODEL yang aktif agar selalu sinkron
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SYSTEM_WITH_CONTEXT_PRODUCTION = (
    "Kamu adalah asisten ekstraksi informasi dari dokumen. "
    "Jawaban wajib hanya berdasarkan REFERENSI, jangan menambahkan informasi di luar referensi. "
    "Rapikan jawaban seperlunya agar mudah dibaca, tetapi jangan berlebihan dan jangan halusinasi. "
    "Boleh gunakan HTML sederhana seperti <p>, <ul>, <ol>, <li>, <strong>, dan <br> bila membantu kerapian. "
    "Jangan membuat fakta baru, jangan mengubah makna, dan jangan menambah kesimpulan yang tidak tertulis. "
    "Jika pertanyaan tentang HB/hemoglobin siswa, cantumkan: Nama, NIS, Sekolah, Tahun, Hb, dan Status (keterangan). "
    "Jika ada lebih dari satu data (misalnya tahun berbeda), tampilkan semuanya dengan rapi. "
    "Jika tidak ada informasi yang menjawab, balas persis: 'Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen.' "
    "Jangan menyebutkan dokumen atau sumber. Wajib bahasa Indonesia."
)

SYSTEM_WITH_CONTEXT_CHATBOT = (
    "Kamu adalah asisten kesehatan yang menjelaskan isi dokumen kepada pengguna awam dengan bahasa Indonesia yang natural, jelas, dan mudah dipahami. "
    "Jawaban wajib hanya berdasarkan REFERENSI. Boleh menyusun ulang kalimat agar terasa seperti dokter yang menjelaskan ke pasien, tetapi jangan menambah fakta baru, jangan mengubah makna, dan jangan halusinasi. "
    "Utamakan menjawab inti pertanyaan terlebih dahulu, lalu beri penjelasan singkat yang relevan bila memang membantu pemahaman. "
    "Gunakan nada hangat dan manusiawi, tetapi tetap ringkas dan tidak bertele-tele. "
    "Boleh gunakan HTML sederhana seperti <p>, <ul>, <ol>, <li>, <strong>, dan <br> bila membantu kerapian. "
    "Jika pertanyaan meminta definisi, mulai dengan definisi paling langsung dan mudah dipahami, bukan gejala atau pencegahan kecuali memang ditanyakan. "
    "Jika pertanyaan tentang HB/hemoglobin siswa, cantumkan: Nama, NIS, Sekolah, Tahun, Hb, dan Status (keterangan). "
    "Jika ada lebih dari satu data, tampilkan semuanya dengan rapi. "
    "Jika tidak ada informasi yang menjawab, balas persis: 'Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen.' "
    "Jangan menyebutkan dokumen atau sumber."
)

SYSTEM_WITH_CONTEXT_EVALUATION = (
    "Kamu adalah asisten ekstraksi informasi untuk evaluasi RAG. "
    "Jawaban wajib hanya berdasarkan REFERENSI. "
    "Jawab dengan teks polos yang singkat, literal, dan sedekat mungkin dengan frasa pada referensi. "
    "Jangan memakai HTML. Jangan memberi elaborasi, pengantar, simpulan tambahan, atau parafrase yang tidak perlu. "
    "Jika berupa daftar, pisahkan dengan koma atau kalimat singkat. "
    "Jika pertanyaan meminta definisi, ambil kalimat definisi yang paling langsung dari referensi. "
    "Jika tidak ada informasi yang menjawab, balas persis: 'Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen.' "
    "Jangan menyebutkan dokumen atau sumber."
)

SYSTEM_NO_CONTEXT_PRODUCTION = (
    "Jika benar-benar tidak ada, jawab persis: 'Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen.' "
    "Jangan menyebutkan dokumen atau sumber. Wajib bahasa Indonesia."
)

TEXT_CLEANER_SYSTEM = (
    "Kamu bertugas merapikan teks hasil ekstraksi dokumen untuk indexing RAG. "
    "Jangan mengubah fakta, angka, persentase, nama, istilah, tanggal, atau makna kalimat. "
    "Jangan meringkas. Jangan menambahkan informasi baru. "
    "Hanya rapikan jika teks jelas rusak karena line break, OCR, header berulang, bullet berantakan, atau susunan paragraf yang tidak masuk akal. "
    "Jika teks sudah cukup baik, kembalikan hampir sama seperti aslinya. "
    "Output wajib teks polos tanpa HTML atau Markdown."
)


def ask_gemini(
    user_message: str,
    context_text: str | None,
    response_mode: str = "chatbot",
    temperature_with_ctx=0.0,
    temperature_no_ctx=0.0,
):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY belum diatur.")

    if context_text and context_text.strip():
        mode = str(response_mode or "chatbot").strip().lower()
        if mode == "evaluation":
            system_text = SYSTEM_WITH_CONTEXT_EVALUATION
        elif mode == "production":
            system_text = SYSTEM_WITH_CONTEXT_PRODUCTION
        else:
            system_text = SYSTEM_WITH_CONTEXT_CHATBOT
        user_text = (
            f"Pertanyaan: {user_message}\n\n"
            f"REFERENSI (gunakan untuk menjawab):\n{context_text}\n\n"
            "Instruksi: Jawab berdasarkan referensi di atas."
        )
        temperature = float(temperature_with_ctx)
    else:
        system_text = SYSTEM_NO_CONTEXT_PRODUCTION
        user_text = user_message
        temperature = float(temperature_no_ctx)

    payload = {
        "system_instruction": {
            "parts": [{"text": system_text}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_text}],
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 1024,
            # thinkingConfig di dalam generationConfig — matikan thinking mode
            # agar gemini-2.5-flash tidak "berpikir lama" untuk pertanyaan sederhana
            "thinkingConfig": {
                "thinkingBudget": 0,
            },
        },
    }

    resp = requests.post(
        GEMINI_URL,
        params={"key": GEMINI_API_KEY},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()  # lempar exception jika status 4xx/5xx
    return resp


def clean_text_with_gemini(raw_text: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY belum diatur.")

    payload = {
        "system_instruction": {
            "parts": [{"text": TEXT_CLEANER_SYSTEM}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Rapikan teks berikut sesuai aturan. "
                            "Pertahankan diksi dan data sebanyak mungkin.\n\n"
                            f"TEKS:\n{raw_text}"
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 2048,
            "thinkingConfig": {
                "thinkingBudget": 0,
            },
        },
    }

    resp = requests.post(
        GEMINI_URL,
        params={"key": GEMINI_API_KEY},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates", []) or []
    for candidate in candidates:
        content = candidate.get("content") or {}
        parts = content.get("parts", []) or []
        text_chunks = []
        for part in parts:
            text = part.get("text")
            if text:
                text_chunks.append(str(text))
        if text_chunks:
            return "\n".join(text_chunks).strip()

    return ""
