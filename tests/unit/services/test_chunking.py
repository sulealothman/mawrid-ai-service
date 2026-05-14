from __future__ import annotations

import pytest

from app.services.chunking import chunk_text


def test_empty_input_returns_no_chunks() -> None:
    assert chunk_text("") == []


def test_whitespace_only_returns_no_chunks() -> None:
    assert chunk_text("   \n\t  ") == []


def test_short_text_returns_single_chunk() -> None:
    result = chunk_text("Hello world")
    assert len(result) == 1
    assert result[0]["text"] == "Hello world"


def test_long_text_splits_into_multiple_chunks() -> None:
    # 20 words → with max_tokens=5 and no overlap, expect several chunks
    text = " ".join(["word"] * 20)
    result = chunk_text(text, max_tokens=5, overlap_tokens=0)
    assert len(result) > 1


def test_chunk_ordering_preserves_original_order() -> None:
    words = [f"word{i}" for i in range(30)]
    text = " ".join(words)
    result = chunk_text(text, max_tokens=5, overlap_tokens=0)
    assert len(result) > 1
    # Each chunk must appear at a strictly later position than the previous one,
    # confirming the original text order is preserved across chunks.
    pos = 0
    for chunk in result:
        idx = text.find(chunk["text"], pos)
        assert idx != -1, f"Chunk text not found in original: {chunk['text']!r}"
        pos = idx + 1


def test_overlap_repeats_tokens_across_chunks() -> None:
    text = " ".join(["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"])
    result = chunk_text(text, max_tokens=4, overlap_tokens=2)
    assert len(result) > 1
    # The end of chunk N should appear at the start of chunk N+1
    end_of_first = result[0]["text"].split()[-2:]
    start_of_second = result[1]["text"].split()[:2]
    assert end_of_first == start_of_second


def test_non_ascii_text_handled_correctly() -> None:
    text = "مرحبا بالعالم"  # Arabic: "Hello world"
    result = chunk_text(text)
    assert len(result) == 1
    assert result[0]["text"] == text


@pytest.mark.parametrize(
    "max_tokens, overlap_tokens",
    [
        (0, 0),    # max_tokens <= 0 → normalised to 4096
        (-5, 0),   # max_tokens <= 0 → normalised to 4096
        (10, -3),  # overlap_tokens < 0 → normalised to 0
        (4, 4),    # overlap_tokens >= max_tokens → normalised to max_tokens // 4
        (4, 10),   # overlap_tokens >= max_tokens → normalised to max_tokens // 4
    ],
)
def test_invalid_chunk_params_normalised(max_tokens: int, overlap_tokens: int) -> None:
    text = "This is a test sentence with enough words to chunk."
    # Should not raise; normalisation rules defined in chunking.py apply
    result = chunk_text(text, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    assert isinstance(result, list)
    assert all("text" in chunk for chunk in result)
