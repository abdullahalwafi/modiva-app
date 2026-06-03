from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any
from urllib import request as urllib_request

from config import get_chat_api_url


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = BASE_DIR / "datasets" / "modiva_rag_eval_template.csv"
DEFAULT_API_URL = get_chat_api_url()


def safe_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        print(f"[WARN] Dataset tidak ditemukan: {path}")
        return []
    if path.suffix.lower() == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def call_endpoint(api_url: str, question: str, timeout: int) -> dict[str, Any]:
    payload = json.dumps({"message": question, "mode": "evaluation_strict", "debug": True}).encode("utf-8")
    req = urllib_request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def expected_answerable(value: str) -> bool | None:
    normalized = value.lower().strip()
    if normalized == "answerable":
        return True
    if normalized in {"unanswerable", "not_fully_answerable"}:
        return False
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate grounded strict answers via /chat-api.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    rows = read_rows(Path(args.dataset))
    if not rows:
        print("[WARN] Tidak ada baris evaluasi.")
        return

    for column in ["answerability", "reference_strict_answer"]:
        if column not in rows[0]:
            print(f"[WARN] Kolom {column} tidak tersedia. Metric terkait akan dilewati.")

    answerability_total = 0
    answerability_correct = 0
    abstain_total = 0
    abstain_correct = 0
    unsupported_count = 0
    exact_total = 0
    exact_hit = 0

    for row in rows:
        question = safe_text(row.get("question") or row.get("Pertanyaan"))
        if not question:
            continue
        try:
            payload = call_endpoint(args.api_url, question, args.timeout)
        except Exception as exc:
            print(f"[ERROR] {question}: {exc}")
            continue

        answer = safe_text(payload.get("answer") or payload.get("reply"))
        expected_flag = expected_answerable(safe_text(row.get("answerability")))
        if expected_flag is not None:
            answerability_total += 1
            predicted_flag = bool(payload.get("answerable"))
            if predicted_flag == expected_flag:
                answerability_correct += 1
            if not expected_flag:
                abstain_total += 1
                if answer == "UNKNOWN":
                    abstain_correct += 1
                elif predicted_flag:
                    unsupported_count += 1

        reference = safe_text(row.get("reference_strict_answer"))
        if reference and reference != "UNKNOWN":
            exact_total += 1
            if reference.lower() in answer.lower():
                exact_hit += 1

        print(
            f"[CASE] answerable={payload.get('answerable')} abstention={payload.get('abstention_type')} "
            f"intent={payload.get('intent')} domain={payload.get('domain')} answer={answer}"
        )

    if answerability_total:
        print(
            f"\nanswerability_correctness={answerability_correct / answerability_total:.3f} "
            f"({answerability_correct}/{answerability_total})"
        )
    if abstain_total:
        print(f"abstain_correctness={abstain_correct / abstain_total:.3f} ({abstain_correct}/{abstain_total})")
    if exact_total:
        print(f"reference_contains={exact_hit / exact_total:.3f} ({exact_hit}/{exact_total})")
    print(f"unsupported_answer_count={unsupported_count}")


if __name__ == "__main__":
    main()
