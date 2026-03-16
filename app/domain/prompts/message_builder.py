from __future__ import annotations

from typing import Dict, List

from app.prompts.rag_prompt import RAG_PROMPT

def build_rag_messages(
    question: str,
    contexts: List[str],
    history: List[Dict[str, str]],
) -> List[Dict[str, str]]:

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": RAG_PROMPT}
    ]

    trimmed_history = history[-10:] if history else []

    for m in trimmed_history:
        if m.get("role") in ("user", "assistant"):
            messages.append(
                {
                    "role": m["role"],
                    "content": m["content"],
                }
            )

    if contexts:
        context_text = "\n\n".join(contexts)

        messages.append(
            {
                "role": "user",
                "content": f"Context:\n{context_text}",
            }
        )

    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    return messages
