from __future__ import annotations
import tiktoken
from typing import Any

from app.core.config import settings

def chunk_text(
    text: str,
    *,
    max_tokens: int = settings.CHUNK_MAX_TOKENS,
    overlap_tokens: int = settings.CHUNK_OVERLAP_TOKENS,
    encoding_name: str = settings.CHUNK_ENCODING,
) -> list[dict[str, Any]]:
    """
    Split text into token-bounded chunks with token overlap.
    Returns list of dicts like: {"text": "..."} to match your current service usage.
    """
    text = (text or "").strip()
    if not text:
        return []

    enc = tiktoken.get_encoding(encoding_name)

    # Encode once
    tokens = enc.encode(text)
    if not tokens:
        return []

    if max_tokens <= 0:
        max_tokens = 4096
    if overlap_tokens < 0:
        overlap_tokens = 0
    if overlap_tokens >= max_tokens:
        overlap_tokens = max(0, max_tokens // 4)

    chunks: list[dict[str, Any]] = []

    start = 0
    n = len(tokens)

    while start < n:
        end = min(start + max_tokens, n)
        chunk_tokens = tokens[start:end]
        chunk_text_str = enc.decode(chunk_tokens).strip()

        if chunk_text_str:
            chunks.append({"text": chunk_text_str})

        if end >= n:
            break

        start = max(0, end - overlap_tokens)

    return chunks
