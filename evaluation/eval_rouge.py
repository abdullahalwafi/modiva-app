import pandas as pd
from rouge_score import rouge_scorer
from config import Config

def _fmt_pct(val: float) -> str:
    return f"{val * 100:.2f}%"

def safe_text(x) -> str:
    if x is None:
        return ""
    return str(x).strip()

def main():
    cfg = Config()

    # ROUGE metrics
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

    xls = pd.ExcelFile(cfg.xlsx_out)  # gunakan file yang sudah ada Candidate
    rows = []
    table_rows = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)

        required = {"Pertanyaan", "Jawaban", "Candidate"}
        if not required.issubset(set(df.columns)):
            print(f"[SKIP] Sheet '{sheet}' belum lengkap kolom {required}")
            continue

        for idx, r in df.iterrows():
            q = safe_text(r["Pertanyaan"])
            ref = safe_text(r["Jawaban"])      # ground truth
            cand = safe_text(r["Candidate"])   # model output

            # skip kalau error atau kosong
            if not q or not ref or not cand or cand.startswith("[ERROR]"):
                continue

            scores = scorer.score(ref, cand)

            rows.append({
                "sheet": sheet,
                "pertanyaan": q,
                "reference": ref,
                "candidate": cand,

                "rouge1_p": scores["rouge1"].precision,
                "rouge1_r": scores["rouge1"].recall,
                "rouge1_f": scores["rouge1"].fmeasure,

                "rouge2_p": scores["rouge2"].precision,
                "rouge2_r": scores["rouge2"].recall,
                "rouge2_f": scores["rouge2"].fmeasure,

                "rougeL_p": scores["rougeL"].precision,
                "rougeL_r": scores["rougeL"].recall,
                "rougeL_f": scores["rougeL"].fmeasure,
            })

            table_rows.append({
                "No": len(table_rows) + 1,
                "ROUGE1_P": _fmt_pct(scores["rouge1"].precision),
                "ROUGE1_R": _fmt_pct(scores["rouge1"].recall),
                "ROUGE1_F1": _fmt_pct(scores["rouge1"].fmeasure),
                "ROUGE2_P": _fmt_pct(scores["rouge2"].precision),
                "ROUGE2_R": _fmt_pct(scores["rouge2"].recall),
                "ROUGE2_F1": _fmt_pct(scores["rouge2"].fmeasure),
                "ROUGEL_P": _fmt_pct(scores["rougeL"].precision),
                "ROUGEL_R": _fmt_pct(scores["rougeL"].recall),
                "ROUGEL_F1": _fmt_pct(scores["rougeL"].fmeasure),
            })

    detail = pd.DataFrame(rows)
    if detail.empty:
        print("❌ Tidak ada data yang bisa dihitung (cek Candidate/ref kosong atau error).")
        return

    detail.to_csv(cfg.rouge_detail_csv, index=False)

    # Summary per sheet (dokumen) dan overall
    summary_sheet = (
        detail.groupby("sheet")[["rouge1_f", "rouge2_f", "rougeL_f"]]
        .mean()
        .reset_index()
    )
    summary_overall = pd.DataFrame([{
        "sheet": "OVERALL",
        "rouge1_f": detail["rouge1_f"].mean(),
        "rouge2_f": detail["rouge2_f"].mean(),
        "rougeL_f": detail["rougeL_f"].mean(),
    }])

    summary = pd.concat([summary_sheet, summary_overall], ignore_index=True)
    summary.to_csv(cfg.rouge_summary_csv, index=False)

    # Build table like the requested format
    table_df = pd.DataFrame(table_rows)
    if not table_df.empty:
        avg = {
            "No": "Rerata",
            "ROUGE1_P": _fmt_pct(detail["rouge1_p"].mean()),
            "ROUGE1_R": _fmt_pct(detail["rouge1_r"].mean()),
            "ROUGE1_F1": _fmt_pct(detail["rouge1_f"].mean()),
            "ROUGE2_P": _fmt_pct(detail["rouge2_p"].mean()),
            "ROUGE2_R": _fmt_pct(detail["rouge2_r"].mean()),
            "ROUGE2_F1": _fmt_pct(detail["rouge2_f"].mean()),
            "ROUGEL_P": _fmt_pct(detail["rougeL_p"].mean()),
            "ROUGEL_R": _fmt_pct(detail["rougeL_r"].mean()),
            "ROUGEL_F1": _fmt_pct(detail["rougeL_f"].mean()),
        }
        table_df = pd.concat([table_df, pd.DataFrame([avg])], ignore_index=True)
        table_df.to_csv(cfg.eval_table_csv, index=False)
        try:
            table_df.to_excel(cfg.eval_table_xlsx, index=False)
        except Exception:
            pass

    print("\n✅ ROUGE selesai dihitung.")
    print(f"- Detail : {cfg.rouge_detail_csv}")
    print(f"- Summary: {cfg.rouge_summary_csv}")
    if table_rows:
        print(f"- Table  : {cfg.eval_table_csv}")
        print(f"- TableX : {cfg.eval_table_xlsx}")
    print("\n=== OVERALL (F1) ===")
    print(summary_overall.to_string(index=False))

if __name__ == "__main__":
    main()
