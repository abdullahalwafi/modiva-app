# MODIVA RAG Refactor

## Arsitektur Pipeline

Endpoint `/chat-api` sekarang memakai pipeline 5 lapis:

1. Input Router: `intent_router.route_intent()` mengklasifikasikan pertanyaan secara rule-based.
2. Domain Router: `domain_router.route_domain()` menentukan domain dan apakah retrieval boleh dilakukan.
3. Retriever: `context_builder.build_context_for_query()` melakukan retrieval domain-aware dari Chroma.
4. Grounding Judge: `grounding_judge.judge_grounding()` memutuskan apakah bukti cukup untuk dijawab.
5. Response Generator: `response_generator.generate_response()` membuat jawaban sesuai mode.

Pipeline ini memisahkan chatbot publik, evaluasi strict, dan kebutuhan data internal tanpa menghapus field response lama.

## Intent

- `smalltalk`: salam atau pembuka percakapan.
- `identity`: pertanyaan tentang identitas/fungsi asisten.
- `unclear_gibberish`: input kosong, terlalu pendek, atau tidak bermakna.
- `definition`: definisi anemia, TTD, Hb, atau istilah terkait.
- `education_faq`: gejala, penyebab, dampak, faktor risiko, edukasi anemia/TTD.
- `procedure_prevention`: pencegahan, makanan, zat besi, cara konsumsi umum.
- `program_policy`: SOP, pedoman, program, jadwal, distribusi, monitoring TTD.
- `hb_record_query`: data Hb siswa/siswi atau hasil pemeriksaan Hb.
- `symptom_or_diagnostic`: gejala personal atau permintaan diagnosis.
- `out_of_scope`: di luar cakupan anemia, TTD, Hb, atau MODIVA.

Pertanyaan diagnosis personal diprioritaskan sebagai `symptom_or_diagnostic` walaupun mengandung kata anemia.

## Domain

- `edu_anemia_ttd`: definisi, gejala umum, pencegahan, edukasi anemia dan TTD.
- `program_policy`: SOP, pedoman distribusi, monitoring, aturan konsumsi, kebijakan sekolah/puskesmas.
- `hb_records`: data Hb siswa/siswi dan metadata pemeriksaan.
- `fallback_none`: tidak melakukan retrieval.

Metadata baru yang didukung: `domain`, `doc_type`, `audience`, `topic`, `entity`, `year`, `record_type`, dan `source_doc`. Chunk lama tetap diproses dengan `infer_domain_from_metadata_or_text()` berdasarkan metadata, source, dan teks.

## Abstention Policy

Sistem abstain jika:

- Pertanyaan tidak jelas: `unclear_question`.
- Pertanyaan diagnosis personal: `needs_medical_confirmation`.
- Topik di luar cakupan: `out_of_scope`.
- Data Hb tidak cocok: `no_matching_record`.
- Dokumen tidak memberi bukti cukup: `unknown_from_docs`.

`smalltalk` dan `identity` dijawab langsung tanpa retrieval. Pertanyaan gejala personal tidak didiagnosis; jawaban publik mengarahkan pemeriksaan Hb atau konsultasi tenaga kesehatan.

## Mode Response

- `chatbot_public`: default. Bahasa Indonesia natural, ringkas, grounded, dan aman.
- `evaluation_strict`: jawaban literal dan singkat. Semua abstention menjadi `UNKNOWN`.
- `internal_data`: format ringkas untuk data Hb, tanpa narasi edukasi panjang.

Alias lama tetap didukung:

- `chatbot` -> `chatbot_public`
- `evaluation` -> `evaluation_strict`
- `data` -> `internal_data`

Response tetap mengisi `reply` dan `response` untuk kompatibilitas frontend lama, selain field baru seperti `answer`, `intent`, `domain`, `retrieval_confidence`, `answerable`, `abstention_type`, dan `sources`.

## Menjalankan Smoke Test

```bash
rtk python evaluation/smoke_test_rag_pipeline.py
```

Smoke test menjalankan pipeline lokal untuk salam, definisi anemia, gejala anemia, TTD, diagnosis personal, input ngawur, query Hb, dan out-of-scope. Jika Chroma/dokumen belum tersedia, route dan abstention tetap diuji; jawaban dokumen bisa abstain.

## Menjalankan Evaluasi

Intent routing:

```bash
rtk python evaluation/evaluate_intent_routing.py --dataset evaluation/datasets/modiva_rag_eval_template.csv
```

Retrieval:

```bash
rtk python evaluation/evaluate_retrieval.py --dataset evaluation/datasets/modiva_rag_eval_template.csv --top-k 5
```

Grounded answer via endpoint:

```bash
rtk python evaluation/evaluate_grounded_answer.py --api-url http://127.0.0.1:8000/chat-api
```

UX/safety via endpoint:

```bash
rtk python evaluation/evaluate_ux_safety.py --api-url http://127.0.0.1:8000/chat-api
```

Dataset default ada di `evaluation/datasets/modiva_rag_eval_template.csv`. Script evaluator akan memberi warning jika kolom opsional tidak tersedia, bukan crash.

## Backward Compatibility

- `/chat-api` tetap menerima POST JSON `{ "message": "..." }`.
- Request tanpa `mode` default ke `chatbot_public`.
- Field `reply` tetap tersedia untuk `static/chatbot/js/chat.js`.
- Mode lama `evaluation` tetap dipetakan ke `evaluation_strict`.
- Fungsi lama `build_context_fullscan()` tidak dihapus.
- Ingestion lama tetap kompatibel; metadata domain baru hanya menambah field untuk dokumen baru/export Hb berikutnya.
