from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parents[1]
EVALUATION_DIR = PROJECT_DIR / "evaluation"
SECTION_HEADING = "## 4.3.4 Hasil Blackbox Testing RAG"


@dataclass(frozen=True)
class BlackboxCase:
    modul: str
    endpoint: str
    metode: str
    ekspektasi: str
    data: dict[str, Any] | None = None
    file_name: str | None = None
    file_content: bytes | None = None
    expected_statuses: tuple[int, ...] = (200,)
    expected_redirect_prefix: str | None = None
    expected_json_key: str | None = None


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def setup_django():
    sys.path.insert(0, str(PROJECT_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()


def build_cases() -> list[BlackboxCase]:
    return [
        BlackboxCase(
            modul="Login",
            endpoint="/login",
            metode="GET",
            ekspektasi="Halaman login dapat diakses dan menampilkan form login.",
            expected_statuses=(200,),
        ),
        BlackboxCase(
            modul="Chatbot RAG",
            endpoint="/chat-api",
            metode="POST",
            ekspektasi="Endpoint chatbot menerima request dan mengembalikan response JSON.",
            data={"message": ""},
            expected_statuses=(200,),
            expected_json_key="reply",
        ),
        BlackboxCase(
            modul="Data Pengetahuan",
            endpoint="/vector/",
            metode="GET",
            ekspektasi="Halaman data pengetahuan dapat diakses dan menampilkan daftar dokumen RAG.",
            expected_statuses=(200,),
        ),
        BlackboxCase(
            modul="Upload Dokumen",
            endpoint="/vector/",
            metode="POST",
            ekspektasi="Endpoint upload dokumen dapat menerima request POST tanpa server error.",
            expected_statuses=(200,),
        ),
        BlackboxCase(
            modul="Hapus Pengetahuan",
            endpoint="/vector/delete/blackbox-doc/",
            metode="GET",
            ekspektasi="Akses hapus pengetahuan tanpa login diarahkan ke halaman login.",
            expected_statuses=(302,),
            expected_redirect_prefix="/login",
        ),
        BlackboxCase(
            modul="Sinkronisasi HB ke RAG",
            endpoint="/vitamin/siswahb/export-rag/",
            metode="GET",
            ekspektasi="Akses sinkronisasi HB ke RAG tanpa login diarahkan ke halaman login.",
            expected_statuses=(302,),
            expected_redirect_prefix="/login",
        ),
    ]


def run_case(client, case: BlackboxCase) -> tuple[str, str]:
    kwargs: dict[str, Any] = {}
    if case.data is not None:
        kwargs["data"] = json.dumps(case.data)
        kwargs["content_type"] = "application/json"

    if case.file_name and case.file_content is not None:
        from django.core.files.uploadedfile import SimpleUploadedFile

        kwargs["data"] = {
            "file": SimpleUploadedFile(
                case.file_name,
                case.file_content,
                content_type="text/plain",
            )
        }

    response = getattr(client, case.metode.lower())(case.endpoint, **kwargs)
    status_code = response.status_code
    location = response.get("Location", "")
    detail = f"HTTP {status_code}"
    if location:
        detail += f" -> {location}"

    passed = status_code in case.expected_statuses
    if passed and case.expected_redirect_prefix:
        passed = location.startswith(case.expected_redirect_prefix)
    if passed and case.expected_json_key:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        passed = case.expected_json_key in payload

    return ("Berhasil" if passed else "Gagal", detail)


def run_tests() -> pd.DataFrame:
    setup_django()
    from django.test import Client

    client = Client(raise_request_exception=False)
    rows = []

    for number, case in enumerate(build_cases(), start=1):
        status, detail = run_case(client, case)
        rows.append(
            {
                "No": number,
                "Modul": case.modul,
                "Endpoint": case.endpoint,
                "Metode": case.metode,
                "Ekspektasi": case.ekspektasi,
                "Status": status,
                "Detail": detail,
            }
        )

    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, include_detail: bool) -> str:
    columns = ["No", "Modul", "Endpoint", "Metode", "Ekspektasi", "Status"]
    if include_detail:
        columns.append("Detail")

    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_outputs(df: pd.DataFrame, output_prefix: Path, include_detail: bool) -> Path:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    csv_path = output_prefix.with_suffix(".csv")
    xlsx_path = output_prefix.with_suffix(".xlsx")
    md_path = output_prefix.with_suffix(".md")
    output_columns = ["No", "Modul", "Endpoint", "Metode", "Ekspektasi", "Status"]
    if include_detail:
        output_columns.append("Detail")
    output_df = df[output_columns]

    output_df.to_csv(csv_path, index=False)
    output_df.to_excel(xlsx_path, index=False)

    report = "\n".join(
        [
            "# Hasil Blackbox Testing RAG",
            "",
            markdown_table(df, include_detail=include_detail),
            "",
        ]
    )
    md_path.write_text(report, encoding="utf-8")
    return md_path


def update_evaluation_report(
    evaluation_report_path: Path,
    df: pd.DataFrame,
    include_detail: bool,
) -> None:
    section = "\n".join(
        [
            SECTION_HEADING,
            "",
            "Blackbox testing dilakukan pada fitur yang berkaitan dengan RAG, yaitu login, chatbot, data pengetahuan, upload dokumen, hapus pengetahuan, dan sinkronisasi data HB ke RAG.",
            "",
            markdown_table(df, include_detail=include_detail),
            "",
        ]
    )

    if evaluation_report_path.exists():
        content = evaluation_report_path.read_text(encoding="utf-8").rstrip() + "\n\n"
    else:
        content = "# Hasil Evaluasi\n\n"

    marker_index = content.find(SECTION_HEADING)
    if marker_index >= 0:
        content = content[:marker_index].rstrip() + "\n\n" + section
    else:
        content = content.rstrip() + "\n\n" + section

    evaluation_report_path.write_text(content.rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Blackbox testing untuk fitur RAG aplikasi."
    )
    parser.add_argument(
        "--output-prefix",
        default=str(BASE_DIR / "blackbox_rag_results"),
        help="Prefix output CSV/XLSX/MD.",
    )
    parser.add_argument(
        "--evaluation-report",
        default=str(EVALUATION_DIR / "evaluation_report.md"),
        help="Path report evaluasi utama yang akan di-update.",
    )
    parser.add_argument(
        "--include-detail",
        action="store_true",
        help="Tambahkan kolom detail HTTP pada tabel Markdown.",
    )
    parser.add_argument(
        "--no-update-evaluation-report",
        action="store_true",
        help="Jangan update evaluation_report.md.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = run_tests()

    output_prefix = resolve_path(args.output_prefix)
    md_path = write_outputs(df, output_prefix, include_detail=args.include_detail)

    if not args.no_update_evaluation_report:
        update_evaluation_report(
            resolve_path(args.evaluation_report),
            df,
            include_detail=args.include_detail,
        )

    print("[OK] Blackbox RAG selesai")
    print(f"- CSV   : {output_prefix.with_suffix('.csv')}")
    print(f"- XLSX  : {output_prefix.with_suffix('.xlsx')}")
    print(f"- Report: {md_path}")
    if not args.no_update_evaluation_report:
        print(f"- Main  : {resolve_path(args.evaluation_report)}")


if __name__ == "__main__":
    main()
