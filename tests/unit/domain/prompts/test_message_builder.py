from __future__ import annotations

import pytest

from app.domain.prompts.message_builder import build_rag_messages
from app.prompts.rag_prompt import RAG_PROMPT


def test_always_starts_with_system_message() -> None:
    result = build_rag_messages("q", [], [])
    assert result[0] == {"role": "system", "content": RAG_PROMPT}


def test_empty_history_adds_no_history_messages() -> None:
    result = build_rag_messages("q", [], [])
    roles = [m["role"] for m in result[1:]]
    assert roles == ["user"]


def test_history_trimmed_to_last_10() -> None:
    history = [{"role": "user", "content": f"msg{i}"} for i in range(15)]
    result = build_rag_messages("q", [], history)
    history_messages = [m for m in result[1:] if m["content"] != "q"]
    assert len(history_messages) == 10
    assert history_messages[0]["content"] == "msg5"


@pytest.mark.parametrize("role", ["system", "tool", "function"])
def test_invalid_history_roles_excluded(role: str) -> None:
    history = [{"role": role, "content": "ignored"}]
    result = build_rag_messages("q", [], history)
    roles = [m["role"] for m in result[1:]]
    assert role not in roles


def test_valid_history_roles_preserved() -> None:
    history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    result = build_rag_messages("q", [], history)
    assert result[1] == {"role": "user", "content": "hello"}
    assert result[2] == {"role": "assistant", "content": "hi"}


def test_contexts_appended_as_user_message() -> None:
    result = build_rag_messages("q", ["ctx1"], [])
    context_msg = result[-2]
    assert context_msg["role"] == "user"
    assert "ctx1" in context_msg["content"]


def test_multiple_contexts_joined_with_blank_line() -> None:
    result = build_rag_messages("q", ["ctx1", "ctx2"], [])
    context_msg = result[-2]
    assert "ctx1\n\nctx2" in context_msg["content"]


def test_empty_contexts_adds_no_context_message() -> None:
    result = build_rag_messages("q", [], [])
    assert result[-1] == {"role": "user", "content": "q"}
    assert len(result) == 2


def test_final_message_is_question() -> None:
    result = build_rag_messages("my question", ["ctx"], [{"role": "user", "content": "prev"}])
    assert result[-1] == {"role": "user", "content": "my question"}


def test_message_ordering_system_history_context_question() -> None:
    history = [{"role": "user", "content": "prev"}]
    result = build_rag_messages("q", ["ctx"], history)
    assert result[0]["role"] == "system"
    assert result[1] == {"role": "user", "content": "prev"}
    assert "ctx" in result[2]["content"]
    assert result[3] == {"role": "user", "content": "q"}
