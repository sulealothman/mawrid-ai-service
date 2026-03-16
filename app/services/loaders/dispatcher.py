from __future__ import annotations
from typing import Iterable

from app.services.types import Page

from app.services.loaders.pdf_loader import load_pdf
from app.services.loaders.txt_loader import load_txt, load_markdown
from app.services.loaders.json_loader import load_json
from app.services.loaders.jsonl_loader import load_jsonl
from app.services.loaders.yaml_loader import load_yaml
from app.services.loaders.csv_loader import load_csv

SUPPORTED_EXT = {"pdf", "txt", "md", "markdown", "json", "jsonl", "yml", "yaml", "csv"}


def load_pages_by_ext(file_path: str, ext: str) -> Iterable[Page]:
    ext = ext.lower()

    if ext == "pdf":
        return load_pdf(file_path)

    if ext == "txt":
        return load_txt(file_path)

    if ext in {"md", "markdown"}:
        return load_markdown(file_path)

    if ext == "json":
        return load_json(file_path)

    if ext == "jsonl":
        return load_jsonl(file_path)

    if ext in {"yml", "yaml"}:
        return load_yaml(file_path)
    
    if ext == "csv":
        return load_csv(file_path)

    raise ValueError(f"Unsupported file type: {ext}")
