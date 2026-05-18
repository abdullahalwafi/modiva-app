import re
from typing import Any

import numpy as np

from modules.vector.utils.embedding import embed
from .keywords import extract_keywords


RAG_DOMAINS = {"edu_anemia_ttd", "program_policy", "hb_records", "fallback_none"}


def build_context_fullscan(collection, user_message: str, max_chunks: int = 8, min_similarity: float = 0.35):
    """
    Retrieval menggunakan ChromaDB native vector search (HNSW index).
    Jauh lebih cepat dari full-scan — tidak perlu load semua dokumen ke RAM.

    Strategi:
    1) Vector query via ChromaDB → ambil top-N chunk paling relevan
    2) Keyword re-ranking untuk boost chunk yang mengandung kata kunci penting
    3) Fallback ke chunk teratas jika tidak ada yang melewati threshold
    """
    if collection is None:
        return "", []

    # --- 1. Embed query & vector search via ChromaDB ---
    q_emb = embed(user_message)
    try:
        results = collection.query(
            query_embeddings=[q_emb],
            n_results=min(max_chunks * 2, 20),  # ambil 2x lebih banyak dulu, lalu filter
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return "", []

    docs = results.get("documents", [[]])[0] or []
    metas = results.get("metadatas", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []

    if not docs:
        return "", []

    query_low = user_message.lower()

    def is_hb_specific_question() -> bool:
        flags = [
            "hb ",
            "hemoglobin",
            "nis",
            "sekolah",
            "siswi",
            "siswa",
            "nama ",
            "tahun ",
            "status anemia",
        ]
        return any(flag in query_low for flag in flags)

    def noise_penalty(doc_text: str, meta: dict | None) -> int:
        text = str(doc_text).strip()
        low = text.lower()
        penalty = 0

        if meta and meta.get("type") == "hb" and not is_hb_specific_question():
            penalty += 8

        noisy_markers = [
            "buku saku pencegahan anemia",
            "kemenkes ri",
            "lampiran",
            "bagian 2",
            "616.152",
        ]
        penalty += sum(2 for marker in noisy_markers if marker in low)

        if len(text) < 40:
            penalty += 4
        if len(text.split()) < 8:
            penalty += 3
        if "\n" in text and text.count("\n") >= 5:
            penalty += 2
        if "data: nama=" in low and not is_hb_specific_question():
            penalty += 5

        return penalty

    # --- 2. Filter berdasarkan similarity threshold ---
    # ChromaDB mengembalikan cosine distance (0=sama, 2=berlawanan)
    # similarity = 1 - distance (untuk cosine)
    candidates = []
    for doc, meta, dist in zip(docs, metas, distances):
        similarity = 1.0 - float(dist)
        if not str(doc).strip():
            continue
        candidates.append((similarity, doc, meta or {}))

    if not candidates:
        return "", []

    # --- 3. Keyword re-ranking: boost chunk yang mengandung kata kunci ---
    keywords = [kw.lower() for kw in extract_keywords(user_message)]

    def keyword_score(doc_text: str) -> int:
        low = doc_text.lower()
        return sum(1 for kw in keywords if kw and kw in low)

    # sort: keyword_score DESC, lalu similarity DESC, lalu noise penalty ASC
    candidates.sort(
        key=lambda x: (
            -(keyword_score(x[1]) * 3),
            -x[0],
            noise_penalty(x[1], x[2]),
        )
    )

    # --- 4. Ambil top max_chunks yang melewati threshold ---
    top_docs, top_metas = [], []
    for sim, doc, meta in candidates:
        if noise_penalty(doc, meta) >= 8 and top_docs:
            continue
        if sim >= min_similarity or not top_docs:  # tetap ambil minimal 1 jika ada hasil
            top_docs.append(doc)
            top_metas.append(meta or {})
        if len(top_docs) >= max_chunks:
            break

    if not top_docs:
        # fallback: ambil chunk teratas meski di bawah threshold
        top_docs = [candidates[0][1]]
        top_metas = [candidates[0][2] or {}]

    return "\n\n".join(top_docs).strip(), top_metas


def _normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9%/.,=\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _metadata_blob(meta: dict[str, Any] | None) -> str:
    meta = meta or {}
    keys = [
        "domain",
        "doc_type",
        "type",
        "source_type",
        "title",
        "source",
        "source_doc",
        "path",
        "topic",
        "record_type",
        "audience",
        "entity",
        "doc_id",
    ]
    return " ".join(str(meta.get(key) or "") for key in keys)


def infer_domain_from_metadata_or_text(
    metadata: dict[str, Any] | None,
    text: str = "",
    source: str = "",
) -> str:
    """
    Infer domain for old Chroma chunks that do not yet have explicit metadata.
    New ingestion should write domain/doc_type directly, but this keeps existing
    indexes usable without a forced migration.
    """
    meta = metadata or {}
    explicit = str(meta.get("domain") or "").strip()
    if explicit in RAG_DOMAINS:
        return explicit

    blob = _normalize_text(" ".join([_metadata_blob(meta), source, text[:1200]]))
    meta_blob = _normalize_text(" ".join([_metadata_blob(meta), source]))

    if (
        meta.get("type") == "hb"
        or meta.get("source_type") == "hb"
        or str(meta.get("doc_id") or "").startswith("hb_")
        or "data: nama=" in blob
        or "siswa_hb" in blob
        or "siswahb" in blob
        or "data hb" in blob
    ):
        return "hb_records"

    program_markers = [
        "sop",
        "pedoman",
        "program",
        "kebijakan",
        "distribusi",
        "monitoring",
        "jadwal",
        "sekolah",
        "puskesmas",
        "aturan konsumsi",
        "aturan minum",
    ]
    if any(marker in meta_blob for marker in program_markers):
        return "program_policy"
    if "tablet tambah darah" in blob or re.search(r"\bttd\b", blob):
        if any(marker in blob for marker in program_markers + ["diminum", "konsumsi", "seminggu"]):
            return "program_policy"

    education_markers = [
        "anemia",
        "kurang darah",
        "hemoglobin",
        "zat besi",
        "gejala",
        "pencegahan",
        "gizi",
        "remaja putri",
        "tablet tambah darah",
        "ttd",
    ]
    if any(marker in blob for marker in education_markers):
        return "edu_anemia_ttd"

    return "fallback_none"


def infer_doc_type_from_metadata_or_text(metadata: dict[str, Any] | None, text: str = "") -> str:
    meta = metadata or {}
    explicit = str(meta.get("doc_type") or meta.get("type") or "").strip()
    if explicit:
        return explicit

    blob = _normalize_text(" ".join([_metadata_blob(meta), text[:1000]]))
    if "data: nama=" in blob or meta.get("type") == "hb":
        return "hb_record"
    if any(marker in blob for marker in ["sop", "pedoman", "kebijakan"]):
        return "policy"
    if any(marker in blob for marker in ["program", "distribusi", "monitoring", "jadwal"]):
        return "program"
    if any(marker in blob for marker in ["gejala", "pencegahan", "zat besi", "anemia"]):
        return "education"
    return "unknown"


def build_domain_metadata(metadata: dict[str, Any] | None, text: str = "", source: str = "") -> dict[str, Any]:
    meta = dict(metadata or {})
    meta.setdefault("domain", infer_domain_from_metadata_or_text(meta, text=text, source=source))
    meta.setdefault("doc_type", infer_doc_type_from_metadata_or_text(meta, text=text))
    meta.setdefault("source_doc", meta.get("title") or meta.get("source") or meta.get("doc_id") or source)
    return meta


def _empty_context(domain: str, summary: str, error: str | None = None) -> dict[str, Any]:
    return {
        "chunks": [],
        "domain": domain,
        "retrieval_confidence": 0.0,
        "retrieval_summary": summary,
        "error": error,
    }


def _source_from_meta(meta: dict[str, Any], chunk_id: str | None = None) -> str:
    return str(
        meta.get("source_doc")
        or meta.get("title")
        or meta.get("source")
        or meta.get("doc_id")
        or chunk_id
        or ""
    ).strip()


def _is_domain_compatible(inferred_domain: str, requested_domain: str, text: str, intent: str) -> bool:
    if requested_domain == "fallback_none":
        return False
    if inferred_domain == requested_domain:
        return True

    low = _normalize_text(text)
    if requested_domain == "edu_anemia_ttd":
        if inferred_domain == "hb_records":
            return False
        return any(
            marker in low
            for marker in [
                "anemia",
                "kurang darah",
                "hemoglobin",
                "gejala",
                "pencegahan",
                "zat besi",
                "gizi",
                "tablet tambah darah",
                "ttd",
            ]
        )

    if requested_domain == "program_policy":
        if inferred_domain == "hb_records":
            return False
        return any(
            marker in low
            for marker in [
                "program",
                "pedoman",
                "sop",
                "kebijakan",
                "distribusi",
                "monitoring",
                "jadwal",
                "diminum",
                "konsumsi",
                "seminggu",
                "tablet tambah darah",
                "ttd",
            ]
        )

    if requested_domain == "hb_records":
        return any(marker in low for marker in ["data: nama=", "hb=", "hemoglobin", "nis=", "siswa"])

    return False


def _intent_keyword_boost(question: str, text: str, intent: str) -> float:
    low = _normalize_text(text)
    keywords = [kw.lower() for kw in extract_keywords(question)]
    score = 0.0
    score += sum(0.08 for kw in keywords if kw and kw in low)

    query_tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", _normalize_text(question))
        if len(token) >= 3
    }
    score += sum(0.03 for token in query_tokens if token in low)

    if intent == "definition":
        if any(marker in f" {low} " for marker in [" adalah ", " merupakan ", " didefinisikan ", " pengertian "]):
            score += 0.25
        if "kadar hemoglobin" in low or "kurang darah" in low:
            score += 0.12

    if intent in {"procedure_prevention", "program_policy"}:
        procedure_markers = [
            "diminum",
            "minum",
            "konsumsi",
            "seminggu",
            "minggu",
            "setiap",
            "jadwal",
            "aturan",
            "dosis",
            "distribusi",
            "monitoring",
            "program",
            "pedoman",
            "sop",
            "pencegahan",
            "zat besi",
        ]
        score += sum(0.06 for marker in procedure_markers if marker in low)

    if intent == "education_faq":
        education_markers = ["gejala", "penyebab", "pencegahan", "zat besi", "anemia", "ttd"]
        score += sum(0.06 for marker in education_markers if marker in low)

    if intent == "hb_record_query":
        hb_markers = ["data: nama=", "hb=", "nis=", "sekolah=", "tahun=", "hemoglobin"]
        score += sum(0.08 for marker in hb_markers if marker in low)
        for year in re.findall(r"\b(?:19|20)\d{2}\b", question):
            if year in low:
                score += 0.2

    return score


def _noise_penalty(text: str, metadata: dict[str, Any], requested_domain: str) -> float:
    low = _normalize_text(text)
    penalty = 0.0
    if len(text.strip()) < 40:
        penalty += 0.18
    if len(text.split()) < 8:
        penalty += 0.12
    if any(marker in low for marker in ["kata pengantar", "daftar isi", "lampiran", "halaman", "copyright"]):
        penalty += 0.16
    if requested_domain != "hb_records" and (metadata.get("type") == "hb" or "data: nama=" in low):
        penalty += 0.8
    return penalty


def _make_candidate(
    chunk_id: str | None,
    text: str,
    metadata: dict[str, Any] | None,
    similarity: float,
    question: str,
    requested_domain: str,
    intent: str,
) -> dict[str, Any] | None:
    if not str(text or "").strip():
        return None

    source = _source_from_meta(metadata or {}, chunk_id)
    enriched_meta = build_domain_metadata(metadata, text=text, source=source)
    inferred_domain = str(enriched_meta.get("domain") or "fallback_none")
    domain_match = _is_domain_compatible(inferred_domain, requested_domain, text, intent)
    if not domain_match:
        return None

    score = float(similarity or 0.0)
    score += _intent_keyword_boost(question, text, intent)
    score -= _noise_penalty(text, enriched_meta, requested_domain)
    if inferred_domain == requested_domain:
        score += 0.12
    else:
        score -= 0.1
    score = max(0.0, min(1.0, score))

    enriched_meta["domain"] = requested_domain if inferred_domain == "fallback_none" else inferred_domain
    return {
        "id": chunk_id,
        "text": str(text).strip(),
        "source": source,
        "metadata": enriched_meta,
        "score": float(score),
        "domain": requested_domain,
    }


def _collection_count(collection) -> int | None:
    try:
        return int(collection.count())
    except Exception:
        return None


def _query_vector_candidates(collection, question: str, n_results: int) -> list[tuple[str | None, str, dict[str, Any], float]]:
    q_emb = embed(question)
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    ids = results.get("ids", [[]])[0] or []
    docs = results.get("documents", [[]])[0] or []
    metas = results.get("metadatas", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []

    out: list[tuple[str | None, str, dict[str, Any], float]] = []
    for idx, doc in enumerate(docs):
        meta = metas[idx] if idx < len(metas) and metas[idx] else {}
        chunk_id = ids[idx] if idx < len(ids) else None
        distance = float(distances[idx]) if idx < len(distances) else 1.0
        similarity = max(0.0, min(1.0, 1.0 - distance))
        out.append((chunk_id, str(doc), meta, similarity))
    return out


def _get_metadata_candidates(collection, where: dict[str, Any], limit: int = 200) -> list[tuple[str | None, str, dict[str, Any], float]]:
    try:
        results = collection.get(where=where, include=["documents", "metadatas"], limit=limit)
    except Exception:
        return []
    ids = results.get("ids", []) or []
    docs = results.get("documents", []) or []
    metas = results.get("metadatas", []) or []
    out: list[tuple[str | None, str, dict[str, Any], float]] = []
    for idx, doc in enumerate(docs):
        meta = metas[idx] if idx < len(metas) and metas[idx] else {}
        chunk_id = ids[idx] if idx < len(ids) else None
        out.append((chunk_id, str(doc), meta, 0.35))
    return out


def _metadata_first_candidates(collection, domain: str) -> list[tuple[str | None, str, dict[str, Any], float]]:
    where_clauses = [{"domain": domain}]
    if domain == "hb_records":
        where_clauses.extend(
            [
                {"type": "hb"},
                {"source_type": "hb"},
                {"doc_type": "hb_record"},
                {"record_type": "hb"},
            ]
        )
    elif domain == "program_policy":
        where_clauses.extend([{"doc_type": "policy"}, {"doc_type": "program"}])
    elif domain == "edu_anemia_ttd":
        where_clauses.extend([{"doc_type": "education"}, {"topic": "anemia"}])

    candidates: list[tuple[str | None, str, dict[str, Any], float]] = []
    seen: set[str] = set()
    for where in where_clauses:
        for chunk_id, doc, meta, sim in _get_metadata_candidates(collection, where):
            dedupe_key = chunk_id or doc[:160]
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            candidates.append((chunk_id, doc, meta, sim))
    return candidates


def build_context_for_query(
    question: str,
    domain: str,
    intent: str,
    mode: str = "chatbot_public",
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Domain-aware retrieval entrypoint for the new MODIVA RAG pipeline.
    It keeps Chroma compatibility while applying metadata/domain filters and a
    small deterministic reranker before the grounding judge sees the chunks.
    """
    requested_domain = domain if domain in RAG_DOMAINS else "fallback_none"
    if requested_domain == "fallback_none":
        return _empty_context(requested_domain, "Retrieval skipped for fallback_none domain.")

    if not str(question or "").strip():
        return _empty_context(requested_domain, "Retrieval skipped for empty question.")

    try:
        from .chroma import get_collection

        collection = get_collection()
    except Exception as exc:
        return _empty_context(requested_domain, "Chroma collection unavailable.", str(exc))

    if collection is None:
        return _empty_context(requested_domain, "Chroma collection unavailable.", "collection is None")

    count = _collection_count(collection)
    if count == 0:
        return _empty_context(requested_domain, "Chroma collection is empty.")

    n_results = min(max(top_k * 8, 20), count or max(top_k * 8, 20))
    raw_candidates: list[tuple[str | None, str, dict[str, Any], float]] = []
    errors: list[str] = []

    if requested_domain == "hb_records":
        raw_candidates.extend(_metadata_first_candidates(collection, requested_domain))

    try:
        raw_candidates.extend(_query_vector_candidates(collection, question, n_results=n_results))
    except Exception as exc:
        errors.append(str(exc))

    if requested_domain != "hb_records" and len(raw_candidates) < top_k:
        raw_candidates.extend(_metadata_first_candidates(collection, requested_domain))

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for chunk_id, text, meta, similarity in raw_candidates:
        dedupe_key = chunk_id or _normalize_text(text[:240])
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        candidate = _make_candidate(
            chunk_id=chunk_id,
            text=text,
            metadata=meta,
            similarity=similarity,
            question=question,
            requested_domain=requested_domain,
            intent=intent,
        )
        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(key=lambda item: (-float(item.get("score") or 0.0), str(item.get("id") or "")))
    selected = candidates[: max(1, int(top_k or 5))]
    confidence = float(selected[0].get("score") or 0.0) if selected else 0.0

    summary = (
        f"Retrieved {len(selected)} chunks for domain={requested_domain}, intent={intent}."
        if selected
        else f"No compatible chunks for domain={requested_domain}, intent={intent}."
    )
    return {
        "chunks": selected,
        "domain": requested_domain,
        "retrieval_confidence": confidence,
        "retrieval_summary": summary,
        "error": "; ".join(errors) if errors else None,
    }
