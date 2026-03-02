from typing import Literal

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    rows: int
    columns: int
    column_names: list[str]
    preview: list[dict]


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AnalyzeRequest(BaseModel):
    file_id: str
    question: str = Field(min_length=1, max_length=2000)
    conversation_history: list[ConversationMessage] = []


class AnalyzeResponse(BaseModel):
    answer: str
    charts: list[str] = []
    summary: str | None = None
    insights: list[str] = []
    tool_calls_made: list[str] = []
    tokens_used: int | None = None


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
