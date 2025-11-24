import io
from pypdf import PdfReader

def extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(pages)
