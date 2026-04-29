from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.chat import Citation, SourceChunk


class ReportGenerateRequest(BaseModel):
    workspace_id: int
    title: str = Field(min_length=1, max_length=255)
    topic: str | None = Field(default=None, max_length=255)
    top_k: int | None = Field(default=None, ge=1, le=30)


class ReportSectionRead(BaseModel):
    id: int | None = None
    order_index: int
    title: str
    content: str
    citations: list[Citation] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ReportRead(BaseModel):
    id: int
    workspace_id: int
    title: str
    topic: str
    introduction: str
    sections: list[ReportSectionRead] = Field(default_factory=list)
    conclusion: str
    citations: list[Citation] = Field(default_factory=list)
    source_chunks: list[SourceChunk] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
