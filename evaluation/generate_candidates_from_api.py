import re
import time
import pandas as pd
import requests
from tqdm import tqdm
from config import Config

INSTRUCTION = (
    "Jawab dengan teks polos tanpa HTML/Markdown/tagging. "
    "Hindari parafrase; gunakan frasa kunci yang langsung dan literal. "
    "Jika berupa daftar, pisahkan dengan koma."
)

def build_prompt(question: str) -> str:
    return f"{INSTRUCTION}\nPertanyaan: {question}"

def strip_tags(text: str) -> str:
    # Remove common HTML tags and normalize whitespace to keep CSV one-line.
    text = re.sub(r"</?li\\b[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?ul\\b[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?p\\b[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\\s+", " ", text).strip()

def call_chat_api(api_url: str, question: str, timeout_sec: int) -> str:
    """
    Menyesuaikan dengan API Anda:
    request:  {"message": "<pertanyaan>"}
    response: {"reply": "<jawaban>"}
    """
    payload = {"message": question}
    r = requests.post(api_url, json=payload, timeout=timeout_sec)
    r.raise_for_status()
    data = r.json()
    return str(data.get("reply", "")).strip()

def main():
    cfg = Config()

    xls = pd.ExcelFile(cfg.xlsx_in)
    writer = pd.ExcelWriter(cfg.xlsx_out, engine="openpyxl")
    wrote_sheet = False

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)

        # normalize columns when headers are unnamed
        if "Pertanyaan" not in df.columns or "Jawaban" not in df.columns:
            cols = list(df.columns)
            if len(cols) >= 3 and all(str(c).startswith("Unnamed") for c in cols[:3]):
                df = df.rename(columns={cols[0]: "Sumber", cols[1]: "Pertanyaan", cols[2]: "Jawaban"})

        # Wajib ada kolom
        if "Pertanyaan" not in df.columns or "Jawaban" not in df.columns:
            print(f"[SKIP] Sheet '{sheet}' tidak punya kolom Pertanyaan/Jawaban")
            continue

        if "Candidate" not in df.columns:
            df["Candidate"] = ""

        print(f"\n[INFO] Generating candidate for sheet: {sheet} ({len(df)} rows)")
        for i in tqdm(range(len(df))):
            q = str(df.loc[i, "Pertanyaan"]).strip()
            if not q:
                continue

            # Kalau sudah ada candidate (misal pernah jalan), skip
            if str(df.loc[i, "Candidate"]).strip():
                continue

            try:
                ans = call_chat_api(cfg.api_url, build_prompt(q), cfg.timeout_sec)
                df.loc[i, "Candidate"] = strip_tags(ans)
            except Exception as e:
                df.loc[i, "Candidate"] = f"[ERROR] {e}"

            time.sleep(cfg.sleep_sec)

        df.to_excel(writer, sheet_name=sheet, index=False)
        wrote_sheet = True

    if not wrote_sheet:
        # ensure at least one visible sheet to avoid openpyxl error
        pd.DataFrame(
            [{"error": "Tidak ada sheet valid dengan kolom Pertanyaan/Jawaban"}]
        ).to_excel(writer, sheet_name="ERROR", index=False)

    writer.close()
    print(f"\nSelesai. Output: {cfg.xlsx_out}")

if __name__ == "__main__":
    main()
