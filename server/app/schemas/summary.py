from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.chat import Citation, SourceChunk


class SummaryGenerateRequest(BaseModel):
    workspace_id: int
    topic: str | None = Field(default=None, max_length=255)
    top_k: int | None = Field(default=None, ge=1, le=20)


class SummaryKeyPoint(BaseModel):
    point: str
    citations: list[Citation] = Field(default_factory=list)


class SummaryRead(BaseModel):
    id: int
    workspace_id: int
    topic: str
    summary: str
    key_points: list[SummaryKeyPoint] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    source_chunks: list[SourceChunk] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}
