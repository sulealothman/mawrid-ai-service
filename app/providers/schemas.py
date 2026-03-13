from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: List[List[float]]
    usage: Optional[Usage]


@dataclass(frozen=True)
class ChatResult:
    text: str
    usage: Optional[Usage]
    model: Optional[str] = None
