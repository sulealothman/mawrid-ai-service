from __future__ import annotations
from typing import Iterator
from app.services.types import Page

def _stream_text_file(file_path: str, *, max_chars: int) -> Iterator[Page]:
    buf: list[str] = []
    buf_len = 0
    page_no = 1

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line:
                continue
            buf.append(line)
            buf_len += len(line)

            if buf_len >= max_chars:
                text = "".join(buf).strip()
                if text:
                    yield Page(page=page_no, text=text)
                    page_no += 1
                buf.clear()
                buf_len = 0

    # remainder
    text = "".join(buf).strip()
    if text:
        yield Page(page=page_no, text=text)

def load_txt(file_path: str, *, max_chars: int = 20000) -> Iterator[Page]:
    return _stream_text_file(file_path, max_chars=max_chars)

def load_markdown(file_path: str, *, max_chars: int = 20000) -> Iterator[Page]:
    return _stream_text_file(file_path, max_chars=max_chars)
