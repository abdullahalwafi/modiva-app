import sys
from pathlib import Path

import pandas as pd
from bert_score import score as bert_score

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from evaluation.config import Config


def _fmt_pct(val: float) -> str:
    return f"{val * 100:.2f}%"


def safe_text(x) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _compute_bertscore(cands: list[str], refs: list[str], cfg: Config):
    kwargs = {
        "lang": cfg.bert_lang,
        "verbose": True,
    }
    if cfg.bert_model:
        kwargs["model_type"] = cfg.bert_model

    p, r, f1 = bert_score(cands, refs, **kwargs)
    return p.tolist(), r.tolist(), f1.tolist()


def _semantic_label() -> str:
    return "semantic_similarity"


def main():
    cfg = Config()

    xls = pd.ExcelFile(cfg.xlsx_out)  # gunakan file yang sudah ada Candidate
    data_rows = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)

        required = {"Pertanyaan", "Jawaban", "Candidate"}
        if not required.issubset(set(df.columns)):
            print(f"[SKIP] Sheet '{sheet}' belum lengkap kolom {required}")
            continue

        for _, r in df.iterrows():
            q = safe_text(r["Pertanyaan"])
            ref = safe_text(r["Jawaban"])      # ground truth
            cand = safe_text(r["Candidate"])   # model output

            # skip kalau error atau kosong
            if not q or not ref or not cand or cand.startswith("[ERROR]"):
                continue

            data_rows.append({
                "sheet": sheet,
                "pertanyaan": q,
                "reference": ref,
                "candidate": cand,
            })

    if not data_rows:
        print("❌ Tidak ada data yang bisa dihitung (cek Candidate/ref kosong atau error).")
        return

    detail = pd.DataFrame(data_rows)

    print(f"[INFO] Menghitung BERTScore untuk {len(detail)} pasangan kalimat...")
    p_vals, r_vals, f_vals = _compute_bertscore(
        detail["candidate"].tolist(),
        detail["reference"].tolist(),
        cfg,
    )

    # Sesuai rumus: precision, recall, dan F1 BERTScore per pasangan candidate-reference.
    detail["bert_p"] = p_vals
    detail["bert_r"] = r_vals
    detail["bert_f1"] = f_vals
    detail[_semantic_label()] = detail["bert_f1"]

    detail.to_csv(cfg.bert_detail_csv, index=False)

    # Summary per sheet (dokumen) dan overall
    summary_sheet = (
        detail.groupby("sheet")[["bert_p", "bert_r", "bert_f1", _semantic_label()]]
        .mean()
        .reset_index()
    )
    summary_overall = pd.DataFrame([{
        "sheet": "OVERALL",
        "bert_p": detail["bert_p"].mean(),
        "bert_r": detail["bert_r"].mean(),
        "bert_f1": detail["bert_f1"].mean(),
        _semantic_label(): detail[_semantic_label()].mean(),
    }])

    summary = pd.concat([summary_sheet, summary_overall], ignore_index=True)
    summary.to_csv(cfg.bert_summary_csv, index=False)

    # Build table like the requested format
    table_rows = []
    for i, (_, r) in enumerate(detail.iterrows(), start=1):
        table_rows.append({
            "No": i,
            "BERT_P": _fmt_pct(r["bert_p"]),
            "BERT_R": _fmt_pct(r["bert_r"]),
            "BERT_F1": _fmt_pct(r["bert_f1"]),
            "SEMANTIC_SIMILARITY": _fmt_pct(r[_semantic_label()]),
        })

    table_df = pd.DataFrame(table_rows)
    avg = {
        "No": "Rerata",
        "BERT_P": _fmt_pct(detail["bert_p"].mean()),
        "BERT_R": _fmt_pct(detail["bert_r"].mean()),
        "BERT_F1": _fmt_pct(detail["bert_f1"].mean()),
        "SEMANTIC_SIMILARITY": _fmt_pct(detail[_semantic_label()].mean()),
    }
    table_df = pd.concat([table_df, pd.DataFrame([avg])], ignore_index=True)
    table_df.to_csv(cfg.eval_bert_table_csv, index=False)
    try:
        table_df.to_excel(cfg.eval_bert_table_xlsx, index=False)
    except Exception:
        pass

    print("\n✅ BERTScore selesai dihitung.")
    print(f"- Detail : {cfg.bert_detail_csv}")
    print(f"- Summary: {cfg.bert_summary_csv}")
    print(f"- Table  : {cfg.eval_bert_table_csv}")
    print(f"- TableX : {cfg.eval_bert_table_xlsx}")
    print("\n=== OVERALL (P/R/F1) ===")
    print(summary_overall.to_string(index=False))


if __name__ == "__main__":
    main()
