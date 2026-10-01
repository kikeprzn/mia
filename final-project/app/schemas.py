"""Request and response bodies for the API.

Every field a client sends is validated here, before any handler runs.
"""

from __future__ import annotations
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class QueryRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"question": "¿Qué materiales de fabricación tiene el agitador RT-RTG?", "top_k": 3}
            ]
        },
    )

    question: Question
    top_k: int = Field(3, ge=1, le=10)
    source: str | None = Field(None, max_length=255)

    @field_validator("source")
    @classmethod
    def blank_source_is_none(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class Citation(BaseModel):
    n: int  # the [n] used in the answer
    id: str
    title: str
    source: str
    page: int
    text: str
    score: float
    cited: bool


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    abstained: bool


class IngestResponse(BaseModel):
    documents: int
    chunks: int
    skipped: list[str]  # files that produced no chunks, with the reason
