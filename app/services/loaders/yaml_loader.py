from __future__ import annotations
from typing import Iterator
import yaml

from app.services.types import Page
from app.services.flatten import flatten_to_text


def load_yaml(
    file_path: str,
    *,
    max_depth: int = 25,
    max_items: int = 5000,
    max_list_items: int = 200,
) -> Iterator[Page]:

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        idx = 1
        for doc in yaml.safe_load_all(f):
            if doc is None:
                continue

            text = flatten_to_text(
                doc,
                max_depth=max_depth,
                max_items=max_items,
                max_list_items=max_list_items,
            )
            if text.strip():
                yield Page(page=idx, text=text)
                idx += 1
