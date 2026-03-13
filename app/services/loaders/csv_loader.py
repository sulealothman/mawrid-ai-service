from __future__ import annotations
import csv
from typing import Iterator
from app.services.types import Page


def load_csv(file_path: str) -> Iterator[Page]:
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            lines = []
            for key, value in row.items():
                if value and str(value).strip():
                    lines.append(f"{key.strip()}: {str(value).strip()}")

            text = "\n".join(lines).strip()

            if text:
                yield Page(page=i + 1, text=text)
