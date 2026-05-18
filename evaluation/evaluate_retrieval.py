from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DEFAULT_DATASET = BASE_DIR / "datasets" / "modiva_rag_eval_template.csv"

sys.path.insert(0, str(PROJECT_DIR))

from modules.landingpage.utils.context_builder import build_context_for_query
from modules.landingpage.utils.domain_router import route_domain
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


def chunk_matches_gold(chunk: dict[str, Any], gold_source: str, gold_fact: str) -> bool:
    source = safe_text(chunk.get("source")).lower()
    text = safe_text(chunk.get("text")).lower()
    meta = chunk.get("metadata") or {}
    meta_blob = " ".join(safe_text(value) for value in meta.values()).lower()
    if gold_source and gold_source.lower() in f"{source} {meta_blob}":
        return True
    if gold_fact and gold_fact.lower() in text:
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate MODIVA domain-aware retrieval.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    rows = read_rows(Path(args.dataset))
    if not rows:
        print("[WARN] Tidak ada baris evaluasi.")
        return
    if "expected_domain" not in rows[0] and "domain" not in rows[0]:
        print("[WARN] Kolom expected_domain/domain tidak tersedia. Domain accuracy tidak dihitung.")
    if "gold_source_doc" not in rows[0]:
        print("[WARN] Kolom gold_source_doc tidak tersedia. recall@k berbasis source akan dilewati.")

    domain_total = 0
    domain_correct = 0
    gold_total = 0
    recall_hits = 0
    reciprocal_ranks: list[float] = []

    for row in rows:
        question = safe_text(row.get("question") or row.get("Pertanyaan"))
        expected_domain = safe_text(row.get("expected_domain") or row.get("domain"))
        gold_source = safe_text(row.get("gold_source_doc"))
        gold_fact = safe_text(row.get("gold_chunk_or_fact"))
        if not question:
            continue

        intent_result = route_intent(question)
        domain_result = route_domain(intent_result)
        predicted_domain = safe_text(domain_result.get("domain"))
        if expected_domain:
            domain_total += 1
            if predicted_domain == expected_domain:
                domain_correct += 1

        context = build_context_for_query(
            question=question,
            domain=predicted_domain,
            intent=safe_text(intent_result.get("intent")),
            mode="evaluation_strict",
            top_k=args.top_k,
        )
        chunks = context.get("chunks") or []
        if gold_source or gold_fact:
            gold_total += 1
            first_rank = 0
            for index, chunk in enumerate(chunks, start=1):
                if chunk_matches_gold(chunk, gold_source, gold_fact):
                    first_rank = index
                    break
            if first_rank:
                recall_hits += 1
                reciprocal_ranks.append(1.0 / first_rank)
            else:
                reciprocal_ranks.append(0.0)

        print(
            f"[CASE] domain={predicted_domain} intent={intent_result.get('intent')} "
            f"confidence={context.get('retrieval_confidence', 0):.3f} q={question}"
        )

    if domain_total:
        print(f"\ndomain_accuracy={domain_correct / domain_total:.3f} ({domain_correct}/{domain_total})")
    if gold_total:
        print(f"recall@{args.top_k}={recall_hits / gold_total:.3f} ({recall_hits}/{gold_total})")
        print(f"mrr={sum(reciprocal_ranks) / len(reciprocal_ranks):.3f}")


if __name__ == "__main__":
    main()
