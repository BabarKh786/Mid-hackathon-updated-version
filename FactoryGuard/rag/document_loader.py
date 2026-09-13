from pathlib import Path
import fitz
from docx import Document

def load_document(path):
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".pdf":
        doc = fitz.open(path)
        pages = []
        for i, page in enumerate(doc):
            pages.append({
                "page": i + 1,
                "section": "PDF content",
                "text": page.get_text("text"),
            })
        return pages

    if ext == ".docx":
        doc = Document(path)
        paragraphs = [x.text.strip() for x in doc.paragraphs if x.text.strip()]
        return [{"page": 1, "section": "DOCX content", "text": "\n".join(paragraphs)}]

    if ext == ".txt":
        return [{
            "page": 1,
            "section": "Text content",
            "text": p.read_text(encoding="utf-8", errors="ignore"),
        }]

    raise ValueError("Unsupported knowledge-base document type. Use PDF, DOCX or TXT.")
