from __future__ import annotations
from typing import Iterator
from pypdf import PdfReader
from app.services.types import Page

def load_pdf(file_path: str) -> Iterator[Page]:
    reader = PdfReader(file_path)

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            yield Page(page=i + 1, text=text)
