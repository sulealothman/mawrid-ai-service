class PromptBuilder:

    @staticmethod
    def build_title_prompt(user_message: str):
        from app.prompts.title_prompt import TITLE_SYSTEM_PROMPT

        return [
            {"role": "system", "content": TITLE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
    
    @staticmethod
    def build_title_from_history(history: list[dict]):

        from app.prompts.title_prompt import TITLE_SYSTEM_PROMPT

        messages = [
            {"role": "system", "content": TITLE_SYSTEM_PROMPT},
        ]

        for m in history[:10]:
            if m.get("role") in ("user"):
                messages.append({
                    "role": m["role"],
                    "content": m["content"],
                })

        return messages