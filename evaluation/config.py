from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    xlsx_in: str = "PERTANYAAN DOKUMEN.xlsx"

    # Output files
    xlsx_out: str = "PERTANYAAN_DOKUMEN_with_candidate.xlsx"
    rouge_detail_csv: str = "rouge_results.csv"
    rouge_summary_csv: str = "rouge_summary.csv"
    eval_table_csv: str = "evaluation_table.csv"
    eval_table_xlsx: str = "evaluation_table.xlsx"

    api_url: str = "http://127.0.0.1:8000/chat-api"

    # Request settings
    timeout_sec: int = 60
    sleep_sec: float = 0.2  # jeda antar request biar gak ngebut

    # BERTScore settings
    bert_detail_csv: str = "bertscore_results.csv"
    bert_summary_csv: str = "bertscore_summary.csv"
    eval_bert_table_csv: str = "evaluation_bertscore_table.csv"
    eval_bert_table_xlsx: str = "evaluation_bertscore_table.xlsx"
    bert_lang: str = "id"
    bert_model: str | None = None

    def __post_init__(self):
        base_dir = Path(__file__).resolve().parent
        path_fields = [
            "xlsx_in",
            "xlsx_out",
            "rouge_detail_csv",
            "rouge_summary_csv",
            "eval_table_csv",
            "eval_table_xlsx",
            "bert_detail_csv",
            "bert_summary_csv",
            "eval_bert_table_csv",
            "eval_bert_table_xlsx",
        ]
        for field_name in path_fields:
            current = Path(getattr(self, field_name))
            if not current.is_absolute():
                setattr(self, field_name, str(base_dir / current))
