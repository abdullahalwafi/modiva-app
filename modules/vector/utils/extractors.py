import io
import fitz  # PyMuPDF
import pandas as pd
from docx import Document as DocxDocument

def extract_text_from_file(uploaded_file):
    filename = uploaded_file.name.lower()
    extracted_rows = []

    if filename.endswith(".pdf"):
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            text = page.get_text("text").strip()
            if text:
                extracted_rows.append(text)

    elif filename.endswith(".docx"):
        uploaded_file.seek(0)
        file_stream = io.BytesIO(uploaded_file.read())
        doc = DocxDocument(file_stream)
        for para in doc.paragraphs:
            if para.text.strip():
                extracted_rows.append(para.text.strip())

    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        uploaded_file.seek(0)
        try:
            xls = pd.read_excel(
                uploaded_file,
                sheet_name=None,
                engine="openpyxl",
                dtype=str,
                keep_default_na=False,
            )
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_excel(
                uploaded_file,
                engine="openpyxl",
                dtype=str,
                keep_default_na=False,
            )
            xls = {"Sheet1": df}

        for _, df in xls.items():
            df = df.fillna("")
            headers = [str(c).strip() for c in df.columns]
            for _, row in df.iterrows():
                pairs = []
                for h, v in zip(headers, row):
                    if str(v).strip():
                        pairs.append(f"{h}: {v}")
                if pairs:
                    extracted_rows.append(", ".join(pairs))
    else:
        raise ValueError("Format file tidak didukung.")

    return extracted_rows
