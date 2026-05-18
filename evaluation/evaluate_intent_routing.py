from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DEFAULT_DATASET = BASE_DIR / "datasets" / "modiva_rag_eval_template.csv"

sys.path.insert(0, str(PROJECT_DIR))

from modules.landingpage.utils.intent_router import route_intent


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate MODIVA intent routing.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    args = parser.parse_args()

    rows = read_rows(Path(args.dataset))
    if not rows:
        print("[WARN] Tidak ada baris evaluasi.")
        return

    if "expected_intent" not in rows[0] and "intent" not in rows[0]:
        print("[WARN] Kolom expected_intent/intent tidak tersedia. Akurasi tidak dihitung.")

    total = 0
    correct = 0
    per_intent_total: Counter[str] = Counter()
    per_intent_correct: Counter[str] = Counter()
    confusion: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        question = safe_text(row.get("question") or row.get("Pertanyaan"))
        expected = safe_text(row.get("expected_intent") or row.get("intent"))
        if not question:
            continue
        predicted = safe_text(route_intent(question).get("intent"))
        if not expected:
            print(f"[INFO] {question} -> {predicted}")
            continue

        total += 1
        per_intent_total[expected] += 1
        confusion[expected][predicted] += 1
        if predicted == expected:
            correct += 1
            per_intent_correct[expected] += 1

    if not total:
        print("[WARN] Tidak ada baris dengan expected_intent/intent.")
        return

    print(f"accuracy={correct / total:.3f} ({correct}/{total})")
    print("\nper_intent_accuracy")
    for intent in sorted(per_intent_total):
        intent_total = per_intent_total[intent]
        intent_correct = per_intent_correct[intent]
        print(f"- {intent}: {intent_correct / intent_total:.3f} ({intent_correct}/{intent_total})")

    print("\nconfusion_matrix")
    predicted_labels = sorted({pred for counters in confusion.values() for pred in counters})
    print(",".join(["expected\\predicted"] + predicted_labels))
    for expected in sorted(confusion):
        values = [str(confusion[expected].get(predicted, 0)) for predicted in predicted_labels]
        print(",".join([expected] + values))


if __name__ == "__main__":
    main()
