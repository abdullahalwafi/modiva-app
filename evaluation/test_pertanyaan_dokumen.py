from __future__ import annotations

import argparse
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from tqdm import tqdm

from config import Config


BASE_DIR = Path(__file__).resolve().parent

INSTRUCTION = (
    "Jawab dengan teks polos tanpa HTML/Markdown/tagging. "
    "Hindari parafrase; gunakan frasa kunci yang langsung dan literal. "
    "Jika berupa daftar, pisahkan dengan koma."
)


def safe_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize worksheet columns from PERTANYAAN DOKUMEN.xlsx."""
    if {"Pertanyaan", "Jawaban"}.issubset(df.columns):
        return df

    cols = list(df.columns)
    if len(cols) >= 3 and all(str(col).startswith("Unnamed") for col in cols[:3]):
        return df.rename(
            columns={
                cols[0]: "Sumber",
                cols[1]: "Pertanyaan",
                cols[2]: "Jawaban",
            }
        )

    return df


def build_prompt(question: str) -> str:
    return f"{INSTRUCTION}\nPertanyaan: {question}"


def strip_tags(text: str) -> str:
    text = re.sub(r"</?li\b[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?ul\b[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?p\b[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def call_chat_api(api_url: str, question: str, timeout_sec: int) -> str:
    payload = {"message": question, "mode": "evaluation"}
    response = requests.post(api_url, json=payload, timeout=timeout_sec)
    response.raise_for_status()
    data = response.json()
    return safe_text(data.get("reply", ""))


def generate_candidates(
    input_path: Path,
    output_path: Path,
    api_url: str,
    timeout_sec: int,
    sleep_sec: float,
    force: bool,
) -> None:
    xls = pd.ExcelFile(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wrote_sheet = False

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet in xls.sheet_names:
            df = normalize_columns(pd.read_excel(xls, sheet_name=sheet))

            if not {"Pertanyaan", "Jawaban"}.issubset(df.columns):
                print(f"[SKIP] Sheet '{sheet}' tidak punya kolom Pertanyaan/Jawaban")
                continue

            if "Candidate" not in df.columns:
                df["Candidate"] = ""

            print(f"\n[INFO] Generate Candidate: {sheet} ({len(df)} baris)")
            for idx in tqdm(df.index):
                question = safe_text(df.at[idx, "Pertanyaan"])
                current_candidate = safe_text(df.at[idx, "Candidate"])

                if not question:
                    continue
                if current_candidate and not force:
                    continue

                try:
                    answer = call_chat_api(api_url, build_prompt(question), timeout_sec)
                    df.at[idx, "Candidate"] = strip_tags(answer)
                except Exception as exc:
                    df.at[idx, "Candidate"] = f"[ERROR] {exc}"

                time.sleep(sleep_sec)

            df.to_excel(writer, sheet_name=sheet, index=False)
            wrote_sheet = True

        if not wrote_sheet:
            pd.DataFrame(
                [{"error": "Tidak ada sheet valid dengan kolom Pertanyaan/Jawaban"}]
            ).to_excel(writer, sheet_name="ERROR", index=False)

    print(f"\n[OK] Workbook Candidate: {output_path}")


def collect_rows(workbook_path: Path) -> pd.DataFrame:
    xls = pd.ExcelFile(workbook_path)
    rows: list[dict[str, str]] = []

    for sheet in xls.sheet_names:
        df = normalize_columns(pd.read_excel(xls, sheet_name=sheet))
        required = {"Pertanyaan", "Jawaban", "Candidate"}
        if not required.issubset(df.columns):
            print(f"[SKIP] Sheet '{sheet}' belum lengkap kolom {required}")
            continue

        for _, row in df.iterrows():
            question = safe_text(row["Pertanyaan"])
            reference = safe_text(row["Jawaban"])
            candidate = safe_text(row["Candidate"])

            if not question or not reference or not candidate:
                continue
            if candidate.startswith("[ERROR]"):
                continue

            rows.append(
                {
                    "sheet": sheet,
                    "pertanyaan": question,
                    "reference": reference,
                    "candidate": candidate,
                }
            )

    return pd.DataFrame(rows)


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    if len(tokens) < n:
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def prf(overlap: int, pred_count: int, ref_count: int) -> dict[str, float]:
    precision = overlap / pred_count if pred_count else 0.0
    recall = overlap / ref_count if ref_count else 0.0
    fmeasure = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "fmeasure": fmeasure,
    }


def rouge_ngram(reference: str, candidate: str, n: int) -> dict[str, float]:
    ref_ngrams = Counter(ngrams(tokenize(reference), n))
    cand_ngrams = Counter(ngrams(tokenize(candidate), n))
    overlap = sum((ref_ngrams & cand_ngrams).values())
    return prf(overlap, sum(cand_ngrams.values()), sum(ref_ngrams.values()))


def lcs_length(left: list[str], right: list[str]) -> int:
    previous = [0] * (len(right) + 1)
    for left_token in left:
        current = [0]
        for idx, right_token in enumerate(right, start=1):
            if left_token == right_token:
                current.append(previous[idx - 1] + 1)
            else:
                current.append(max(previous[idx], current[-1]))
        previous = current
    return previous[-1]


def rouge_l(reference: str, candidate: str) -> dict[str, float]:
    ref_tokens = tokenize(reference)
    cand_tokens = tokenize(candidate)
    overlap = lcs_length(ref_tokens, cand_tokens)
    return prf(overlap, len(cand_tokens), len(ref_tokens))


def score_rouge(reference: str, candidate: str) -> dict[str, dict[str, float]]:
    try:
        from rouge_score import rouge_scorer
    except ImportError:
        return {
            "rouge1": rouge_ngram(reference, candidate, 1),
            "rouge2": rouge_ngram(reference, candidate, 2),
            "rougeL": rouge_l(reference, candidate),
        }

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return {
        metric: {
            "precision": value.precision,
            "recall": value.recall,
            "fmeasure": value.fmeasure,
        }
        for metric, value in scores.items()
    }


def run_rouge(detail: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    table_rows: list[dict[str, Any]] = []

    for idx, row in detail.iterrows():
        scores = score_rouge(row["reference"], row["candidate"])
        result = {
            **row.to_dict(),
            "rouge1_p": scores["rouge1"]["precision"],
            "rouge1_r": scores["rouge1"]["recall"],
            "rouge1_f": scores["rouge1"]["fmeasure"],
            "rouge2_p": scores["rouge2"]["precision"],
            "rouge2_r": scores["rouge2"]["recall"],
            "rouge2_f": scores["rouge2"]["fmeasure"],
            "rougeL_p": scores["rougeL"]["precision"],
            "rougeL_r": scores["rougeL"]["recall"],
            "rougeL_f": scores["rougeL"]["fmeasure"],
        }
        rows.append(result)

        table_rows.append(
            {
                "No": len(table_rows) + 1,
                "ROUGE1_P": format_pct(result["rouge1_p"]),
                "ROUGE1_R": format_pct(result["rouge1_r"]),
                "ROUGE1_F1": format_pct(result["rouge1_f"]),
                "ROUGE2_P": format_pct(result["rouge2_p"]),
                "ROUGE2_R": format_pct(result["rouge2_r"]),
                "ROUGE2_F1": format_pct(result["rouge2_f"]),
                "ROUGEL_P": format_pct(result["rougeL_p"]),
                "ROUGEL_R": format_pct(result["rougeL_r"]),
                "ROUGEL_F1": format_pct(result["rougeL_f"]),
            }
        )

    rouge_detail = pd.DataFrame(rows)
    rouge_detail.to_csv(cfg.rouge_detail_csv, index=False)

    summary = (
        rouge_detail.groupby("sheet")[["rouge1_f", "rouge2_f", "rougeL_f"]]
        .mean()
        .reset_index()
    )
    overall = pd.DataFrame(
        [
            {
                "sheet": "OVERALL",
                "rouge1_f": rouge_detail["rouge1_f"].mean(),
                "rouge2_f": rouge_detail["rouge2_f"].mean(),
                "rougeL_f": rouge_detail["rougeL_f"].mean(),
            }
        ]
    )
    pd.concat([summary, overall], ignore_index=True).to_csv(cfg.rouge_summary_csv, index=False)

    table_df = pd.DataFrame(table_rows)
    table_df = pd.concat(
        [
            table_df,
            pd.DataFrame(
                [
                    {
                        "No": "Rata-rata",
                        "ROUGE1_P": format_pct(rouge_detail["rouge1_p"].mean()),
                        "ROUGE1_R": format_pct(rouge_detail["rouge1_r"].mean()),
                        "ROUGE1_F1": format_pct(rouge_detail["rouge1_f"].mean()),
                        "ROUGE2_P": format_pct(rouge_detail["rouge2_p"].mean()),
                        "ROUGE2_R": format_pct(rouge_detail["rouge2_r"].mean()),
                        "ROUGE2_F1": format_pct(rouge_detail["rouge2_f"].mean()),
                        "ROUGEL_P": format_pct(rouge_detail["rougeL_p"].mean()),
                        "ROUGEL_R": format_pct(rouge_detail["rougeL_r"].mean()),
                        "ROUGEL_F1": format_pct(rouge_detail["rougeL_f"].mean()),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    table_df.to_csv(cfg.eval_table_csv, index=False)
    table_df.to_excel(cfg.eval_table_xlsx, index=False)

    print("\n[OK] ROUGE selesai")
    print(f"- Detail : {cfg.rouge_detail_csv}")
    print(f"- Summary: {cfg.rouge_summary_csv}")
    print(f"- Table  : {cfg.eval_table_csv}")
    print(f"- TableX : {cfg.eval_table_xlsx}")
    return rouge_detail


def run_bertscore(detail: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    try:
        from bert_score import score as bert_score
    except ImportError as exc:
        raise SystemExit("Dependency belum ada: install dengan `pip install bert-score`.") from exc

    kwargs: dict[str, Any] = {
        "lang": cfg.bert_lang,
        "verbose": True,
    }
    if cfg.bert_model:
        kwargs["model_type"] = cfg.bert_model

    print(f"\n[INFO] Menghitung BERTScore untuk {len(detail)} pasangan jawaban...")
    p_vals, r_vals, f_vals = bert_score(
        detail["candidate"].tolist(),
        detail["reference"].tolist(),
        **kwargs,
    )

    bert_detail = detail.copy()
    bert_detail["bert_p"] = p_vals.tolist()
    bert_detail["bert_r"] = r_vals.tolist()
    bert_detail["bert_f1"] = f_vals.tolist()
    bert_detail["semantic_similarity"] = bert_detail["bert_f1"]
    bert_detail.to_csv(cfg.bert_detail_csv, index=False)

    summary = (
        bert_detail.groupby("sheet")[["bert_p", "bert_r", "bert_f1", "semantic_similarity"]]
        .mean()
        .reset_index()
    )
    overall = pd.DataFrame(
        [
            {
                "sheet": "OVERALL",
                "bert_p": bert_detail["bert_p"].mean(),
                "bert_r": bert_detail["bert_r"].mean(),
                "bert_f1": bert_detail["bert_f1"].mean(),
                "semantic_similarity": bert_detail["semantic_similarity"].mean(),
            }
        ]
    )
    pd.concat([summary, overall], ignore_index=True).to_csv(cfg.bert_summary_csv, index=False)

    table_rows = [
        {
            "No": idx + 1,
            "BERT_P": format_pct(row["bert_p"]),
            "BERT_R": format_pct(row["bert_r"]),
            "BERT_F1": format_pct(row["bert_f1"]),
            "SEMANTIC_SIMILARITY": format_pct(row["semantic_similarity"]),
        }
        for idx, row in bert_detail.iterrows()
    ]
    table_df = pd.DataFrame(table_rows)
    table_df = pd.concat(
        [
            table_df,
            pd.DataFrame(
                [
                    {
                        "No": "Rata-rata",
                        "BERT_P": format_pct(bert_detail["bert_p"].mean()),
                        "BERT_R": format_pct(bert_detail["bert_r"].mean()),
                        "BERT_F1": format_pct(bert_detail["bert_f1"].mean()),
                        "SEMANTIC_SIMILARITY": format_pct(
                            bert_detail["semantic_similarity"].mean()
                        ),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    table_df.to_csv(cfg.eval_bert_table_csv, index=False)
    table_df.to_excel(cfg.eval_bert_table_xlsx, index=False)

    print("\n[OK] BERTScore selesai")
    print(f"- Detail : {cfg.bert_detail_csv}")
    print(f"- Summary: {cfg.bert_summary_csv}")
    print(f"- Table  : {cfg.eval_bert_table_csv}")
    print(f"- TableX : {cfg.eval_bert_table_xlsx}")
    return bert_detail


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] + ["---:"] * (len(headers) - 1)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def rouge_report_table(rouge_detail: pd.DataFrame) -> list[str]:
    rows = []
    for idx, row in rouge_detail.iterrows():
        rows.append(
            [
                str(idx + 1),
                format_pct(row["rouge1_p"]),
                format_pct(row["rouge1_r"]),
                format_pct(row["rouge1_f"]),
                format_pct(row["rouge2_p"]),
                format_pct(row["rouge2_r"]),
                format_pct(row["rouge2_f"]),
                format_pct(row["rougeL_p"]),
                format_pct(row["rougeL_r"]),
                format_pct(row["rougeL_f"]),
            ]
        )

    rows.append(
        [
            "Rata-rata",
            format_pct(rouge_detail["rouge1_p"].mean()),
            format_pct(rouge_detail["rouge1_r"].mean()),
            format_pct(rouge_detail["rouge1_f"].mean()),
            format_pct(rouge_detail["rouge2_p"].mean()),
            format_pct(rouge_detail["rouge2_r"].mean()),
            format_pct(rouge_detail["rouge2_f"].mean()),
            format_pct(rouge_detail["rougeL_p"].mean()),
            format_pct(rouge_detail["rougeL_r"].mean()),
            format_pct(rouge_detail["rougeL_f"].mean()),
        ]
    )

    return markdown_table(
        [
            "No",
            "ROUGE1_P",
            "ROUGE1_R",
            "ROUGE1_F1",
            "ROUGE2_P",
            "ROUGE2_R",
            "ROUGE2_F1",
            "ROUGEL_P",
            "ROUGEL_R",
            "ROUGEL_F1",
        ],
        rows,
    )


def bertscore_report_table(bert_detail: pd.DataFrame) -> list[str]:
    rows = []
    for idx, row in bert_detail.iterrows():
        rows.append(
            [
                str(idx + 1),
                format_pct(row["bert_p"]),
                format_pct(row["bert_r"]),
                format_pct(row["bert_f1"]),
                format_pct(row["semantic_similarity"]),
            ]
        )

    rows.append(
        [
            "Rata-rata",
            format_pct(bert_detail["bert_p"].mean()),
            format_pct(bert_detail["bert_r"].mean()),
            format_pct(bert_detail["bert_f1"].mean()),
            format_pct(bert_detail["semantic_similarity"].mean()),
        ]
    )

    return markdown_table(
        ["No", "BERT_P", "BERT_R", "BERT_F1", "SEMANTIC_SIMILARITY"],
        rows,
    )


def write_report(
    rouge_detail: pd.DataFrame | None,
    bert_detail: pd.DataFrame | None,
    report_path: Path,
) -> None:
    lines = ["# Hasil Evaluasi", ""]

    if rouge_detail is not None:
        lines.extend(
            [
                "## 4.3.2 Hasil Evaluasi ROUGE",
                "",
                (
                    "Evaluasi ROUGE digunakan untuk mengukur kemiripan leksikal "
                    "antara jawaban sistem dan jawaban referensi. Nilai yang "
                    "digunakan meliputi precision, recall, dan F1 untuk ROUGE-1, "
                    "ROUGE-2, dan ROUGE-L."
                ),
                "",
                *rouge_report_table(rouge_detail),
                "",
            ]
        )

    if bert_detail is not None:
        lines.extend(
            [
                "## 4.3.3 Hasil Evaluasi BERTScore",
                "",
                (
                    "Evaluasi BERTScore digunakan untuk mengukur kemiripan semantik "
                    "antara jawaban sistem dan jawaban referensi. Nilai semantic "
                    "similarity diambil dari skor BERTScore F1 karena F1 "
                    "merepresentasikan keseimbangan antara precision dan recall "
                    "berbasis embedding kontekstual."
                ),
                "",
                *bertscore_report_table(bert_detail),
                "",
            ]
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[OK] Report: {report_path}")


def parse_args(cfg: Config) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Testing ROUGE dan BERTScore untuk data dokumen "
            "PERTANYAAN DOKUMEN.xlsx."
        )
    )
    parser.add_argument("--input", default=cfg.xlsx_in, help="File Excel pertanyaan dokumen.")
    parser.add_argument(
        "--candidate-output",
        default=cfg.xlsx_out,
        help="Output Excel yang berisi kolom Candidate.",
    )
    parser.add_argument("--api-url", default=cfg.api_url, help="URL endpoint chat API.")
    parser.add_argument("--timeout", type=int, default=cfg.timeout_sec)
    parser.add_argument("--sleep", type=float, default=cfg.sleep_sec)
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Lewati generate Candidate dan langsung pakai file --candidate-output.",
    )
    parser.add_argument(
        "--force-generate",
        action="store_true",
        help="Generate ulang Candidate walaupun kolom Candidate sudah terisi.",
    )
    parser.add_argument("--skip-rouge", action="store_true")
    parser.add_argument("--skip-bertscore", action="store_true")
    parser.add_argument("--bert-lang", default=cfg.bert_lang)
    parser.add_argument("--bert-model", default=cfg.bert_model)
    parser.add_argument(
        "--report",
        default=str(BASE_DIR / "evaluation_report.md"),
        help="Output ringkasan Markdown.",
    )
    return parser.parse_args()


def main() -> None:
    cfg = Config()
    args = parse_args(cfg)

    cfg.bert_lang = args.bert_lang
    cfg.bert_model = args.bert_model

    input_path = resolve_path(args.input)
    candidate_output = resolve_path(args.candidate_output)
    report_path = resolve_path(args.report)

    if not args.skip_generate:
        generate_candidates(
            input_path=input_path,
            output_path=candidate_output,
            api_url=args.api_url,
            timeout_sec=args.timeout,
            sleep_sec=args.sleep,
            force=args.force_generate,
        )

    eval_workbook = candidate_output if candidate_output.exists() else input_path
    detail = collect_rows(eval_workbook)
    if detail.empty:
        raise SystemExit(
            "Tidak ada data yang bisa dievaluasi. Pastikan kolom Pertanyaan, "
            "Jawaban, dan Candidate tersedia."
        )

    rouge_detail = None
    bert_detail = None

    if not args.skip_rouge:
        rouge_detail = run_rouge(detail, cfg)
    if not args.skip_bertscore:
        bert_detail = run_bertscore(detail, cfg)

    if args.skip_rouge and args.skip_bertscore:
        raise SystemExit("Pilih minimal satu metrik: ROUGE atau BERTScore.")

    write_report(rouge_detail, bert_detail, report_path)


if __name__ == "__main__":
    main()
