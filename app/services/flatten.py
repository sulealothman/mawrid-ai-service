from __future__ import annotations
from typing import Any
from app.core.config import settings

def flatten_any(
    obj: Any,
    *,
    parent_key: str = "",
    max_depth: int = 25,
    max_items: int = 5000,
    max_list_items: int = 200,
    max_value_length: int = settings.FLATTEN_MAX_VALUE_LENGTH,
) -> list[tuple[str, str]]:

    out: list[tuple[str, str]] = []
    count = 0
    visited: set[int] = set()

    def add(k: str, v: str):
        nonlocal count
        if count >= max_items:
            return

        if len(v) > max_value_length:
            v = v[:max_value_length] + f"...[truncated len={len(v)}]"

        out.append((k, v))
        count += 1

    def walk(x: Any, key: str, depth: int):
        nonlocal count

        if count >= max_items:
            return

        if depth > max_depth:
            add(key or "$", "[max_depth_reached]")
            return

        # circular reference protection
        obj_id = id(x)
        if obj_id in visited:
            add(key or "$", "[circular_reference]")
            return
        visited.add(obj_id)

        if isinstance(x, dict):
            for k, v in x.items():
                nk = f"{key}.{k}" if key else str(k)
                walk(v, nk, depth + 1)
                if count >= max_items:
                    break

        elif isinstance(x, list):
            limit = min(len(x), max_list_items)
            for i in range(limit):
                nk = f"{key}[{i}]" if key else f"[{i}]"
                walk(x[i], nk, depth + 1)
                if count >= max_items:
                    break
            if len(x) > max_list_items:
                add(key or "$", f"[list_truncated total={len(x)} shown={max_list_items}]")

        else:
            add(key or "$", str(x))

    walk(obj, parent_key, 0)

    if count >= max_items:
        out.append(("$", f"[items_truncated max_items={max_items}]"))

    return out


def flatten_to_text(
    obj: Any,
    *,
    max_depth: int = 25,
    max_items: int = 5000,
    max_list_items: int = 200,
) -> str:
    pairs = flatten_any(
        obj,
        max_depth=max_depth,
        max_items=max_items,
        max_list_items=max_list_items,
    )
    return "\n".join(f"{k}: {v}" for k, v in pairs)
