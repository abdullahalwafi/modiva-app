from datetime import datetime, timezone

from modules.vector.utils.chroma import get_chroma, get_docs_collection
from modules.vector.utils.embedding import embed


HB_DOC_ID = "hb_dataset_v1"  # doc_id tetap untuk data HB


def hb_to_text(hb_obj) -> str:
    """
    Teks yang akan di-embed & disimpan ke Chroma.
    Ini yang nanti jadi "REFERENSI" untuk LLM.
    """
    siswa = hb_obj.siswa
    sekolah = getattr(siswa, "sekolah", None)

    nis = getattr(siswa, "nis", "")
    nama = getattr(siswa, "nama", "")
    nama_sekolah = getattr(sekolah, "nama", "")

    tahun = hb_obj.tahun
    hb = hb_obj.hb  # Decimal
    ket = hb_obj.keterangan or ""

    # buat variasi kalimat biar pencarian natural lebih kena
    return (
        f"Hemoglobin {nama} dengan NIS {nis} dari {nama_sekolah} pada tahun {tahun} "
        f"sebesar {hb} dengan status {ket}."
        f"\nData: nama={nama}, nis={nis}, sekolah={nama_sekolah}, tahun={tahun}, hb={hb}, keterangan={ket}."
    )


def export_siswahb_queryset_to_chroma(qs):
    """
    Export queryset SiswaHB ke Chroma.
    - Upsert pakai id stabil (hb:<pk>) supaya kalau export ulang tidak dobel.
    - Return jumlah item yang berhasil diupsert.
    """
    _, rag = get_chroma()
    if rag is None:
        raise RuntimeError("Chroma collection tidak tersedia")

    ids, docs, metas, embs = [], [], [], []

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    for obj in qs.select_related("siswa__sekolah"):
        chunk_id = f"hb:{obj.pk}"  # stabil, tidak duplikat

        siswa = obj.siswa
        sekolah = getattr(siswa, "sekolah", None)

        meta = {
            "doc_id": HB_DOC_ID,
            "title": "Data HB Siswa",
            "source_type": "db",
            "source_doc": "Data HB Siswa",
            "domain": "hb_records",
            "doc_type": "hb_record",
            "record_type": "hb",
            "audience": "internal",
            "topic": "hemoglobin",
            "created_at": now_iso,
            "type": "hb",
            "hb_id": int(obj.pk),
            "tahun": int(obj.tahun),
            "year": int(obj.tahun),
            "nis": str(getattr(siswa, "nis", "")),
            "nama": str(getattr(siswa, "nama", "")),
            "entity": str(getattr(siswa, "nama", "")),
            "sekolah": str(getattr(sekolah, "nama", "")),
            "hb": str(obj.hb),
            "status": str(obj.keterangan or ""),
        }

        text = hb_to_text(obj)
        vec = embed(text)

        ids.append(chunk_id)
        docs.append(text)
        metas.append(meta)
        embs.append(vec)

    if not ids:
        return 0

    # Upsert supaya tidak dobel saat export ulang
    try:
        rag.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
    except Exception:
        # fallback kalau versi chroma tidak ada upsert
        # strategi: delete dulu ids yang sama, lalu add
        try:
            rag.delete(ids=ids)
        except Exception:
            pass
        rag.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)

    # Catalog entry for docs list
    docs_coll = get_docs_collection()
    title_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = f"sinc_HB_{title_ts}"
    doc_meta = {
        "doc_id": HB_DOC_ID,
        "title": title,
        "created_at": now_iso,
        "source_type": "hb",
        "source_doc": "Data HB Siswa",
        "domain": "hb_records",
        "doc_type": "hb_dataset",
        "record_type": "hb",
        "audience": "internal",
        "topic": "hemoglobin",
        "chunks": int(len(ids)),
    }
    try:
        docs_coll.upsert(
            ids=[HB_DOC_ID],
            documents=[title],
            metadatas=[doc_meta],
        )
    except Exception:
        try:
            docs_coll.delete(ids=[HB_DOC_ID])
        except Exception:
            pass
        try:
            docs_coll.add(
                ids=[HB_DOC_ID],
                documents=[title],
                metadatas=[doc_meta],
            )
        except Exception:
            pass

    return len(ids)


def delete_all_hb_from_chroma():
    """
    Opsional: hapus semua data HB dari rag_collection (berdasarkan doc_id hb_dataset_v1)
    """
    _, rag = get_chroma()
    if rag is None:
        raise RuntimeError("Chroma collection tidak tersedia")
    try:
        rag.delete(where={"doc_id": HB_DOC_ID})
    except Exception:
        # fallback: get ids lalu delete by ids
        res = rag.get(where={"doc_id": HB_DOC_ID}, include=["ids"])
        ids = res.get("ids", []) or []
        if ids:
            rag.delete(ids=ids)
