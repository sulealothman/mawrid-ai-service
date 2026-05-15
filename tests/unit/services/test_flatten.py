from __future__ import annotations

import pytest

from app.services.flatten import flatten_any, flatten_to_text


def test_primitive_root_uses_dollar_key() -> None:
    assert flatten_any(42) == [("$", "42")]


def test_empty_dict_returns_no_pairs() -> None:
    assert flatten_any({}) == []


def test_empty_list_returns_no_pairs() -> None:
    assert flatten_any([]) == []


def test_nested_dict_uses_dot_notation() -> None:
    result = flatten_any({"a": {"b": 1}})
    assert result == [("a.b", "1")]


def test_list_items_use_bracket_index_notation() -> None:
    result = flatten_any(["x", "y"])
    assert result == [("[0]", "x"), ("[1]", "y")]


def test_mixed_dict_list_nesting_key_paths() -> None:
    result = flatten_any({"items": [{"name": "foo"}]})
    assert result == [("items[0].name", "foo")]


def test_flatten_to_text_returns_newline_separated_lines() -> None:
    result = flatten_to_text({"a": 1, "b": 2})
    assert result == "a: 1\nb: 2"


def test_max_depth_returns_marker() -> None:
    deep = {"a": {"b": {"c": "val"}}}
    result = flatten_any(deep, max_depth=1)
    keys = [k for k, _ in result]
    values = [v for _, v in result]
    assert any(v == "[max_depth_reached]" for v in values)
    assert all(k != "a.b.c" for k in keys)


def test_max_items_appends_truncated_marker() -> None:
    obj = {str(i): i for i in range(10)}
    result = flatten_any(obj, max_items=3)
    keys = [k for k, _ in result]
    values = [v for _, v in result]
    assert "$" in keys
    assert any("[items_truncated" in v for v in values)


def test_max_list_items_limits_traversal_and_adds_marker() -> None:
    lst = list(range(5))
    result = flatten_any(lst, max_list_items=2)
    indexed = [(k, v) for k, v in result if k.startswith("[")]
    truncation = [(k, v) for k, v in result if "[list_truncated" in v]
    assert len(indexed) == 2
    assert len(truncation) == 1


def test_long_value_is_truncated() -> None:
    long_str = "x" * 6000
    result = flatten_any({"key": long_str}, max_value_length=5000)
    assert len(result) == 1
    _, v = result[0]
    assert "[truncated" in v
    assert len(v) < 6000


def test_circular_reference_does_not_recurse_infinitely() -> None:
    obj: dict = {}
    obj["self"] = obj
    result = flatten_any(obj)
    values = [v for _, v in result]
    assert any("[circular_reference]" in v for v in values)


@pytest.mark.parametrize("value,expected", [
    ("مرحبا", "مرحبا"),
    ("日本語", "日本語"),
    ("ñoño", "ñoño"),
])
def test_non_ascii_values_handled_correctly(value: str, expected: str) -> None:
    result = flatten_any({"k": value})
    assert result == [("k", expected)]
