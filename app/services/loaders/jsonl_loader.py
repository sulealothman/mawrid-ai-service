from __future__ import annotations
from typing import Iterator, Any
import json

from app.services.types import Page
from app.services.flatten import flatten_to_text


def load_jsonl(
    file_path: str,
    *,
    max_depth: int = 25,
    max_items: int = 5000,
    max_list_items: int = 200,
) -> Iterator[Page]:

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        idx = 1
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                obj: Any = json.loads(line)
            except Exception:
                continue  # skip invalid lines safely

            text = flatten_to_text(
                obj,
                max_depth=max_depth,
                max_items=max_items,
                max_list_items=max_list_items,
            )
            if text.strip():
                yield Page(page=idx, text=text)
                idx += 1
