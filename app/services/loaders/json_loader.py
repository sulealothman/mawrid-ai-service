from __future__ import annotations
from typing import Iterator, Any
import json
import ijson

from app.services.types import Page
from app.services.flatten import flatten_to_text


def load_json(
    file_path: str,
    *,
    max_depth: int = 25,
    max_items: int = 5000,
    max_list_items: int = 200,
) -> Iterator[Page]:

    with open(file_path, "rb") as f:
        try:
            prefix = f.read(1)
            if prefix == b"[":
                f.seek(0)
                idx = 1
                for item in ijson.items(f, "item"):
                    text = flatten_to_text(
                        item,
                        max_depth=max_depth,
                        max_items=max_items,
                        max_list_items=max_list_items,
                    )
                    if text.strip():
                        yield Page(page=idx, text=text)
                        idx += 1
                return
        except Exception:
            pass

    # fallback object mode
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        data: Any = json.load(f)
        text = flatten_to_text(
            data,
            max_depth=max_depth,
            max_items=max_items,
            max_list_items=max_list_items,
        )
        if text.strip():
            yield Page(page=1, text=text)
