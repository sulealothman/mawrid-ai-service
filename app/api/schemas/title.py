from pydantic import BaseModel, Field
from typing import Optional

class TitleGenerationConfig(BaseModel):
    temperature: float = 0.1
    max_tokens: int = 20


class Message(BaseModel):
    role: str
    content: str


class TitleRequest(BaseModel):
    request_id: str
    messages: list[Message]
    generation: TitleGenerationConfig = Field(default_factory=TitleGenerationConfig)


class TitleResponse(BaseModel):
    request_id: str
    title: str
    usage: Optional[dict] = None