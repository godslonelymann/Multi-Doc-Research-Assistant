from pydantic import BaseModel, Field

from app.schemas.chat import Citation, SourceChunk


class CompareRequest(BaseModel):
    workspace_id: int
    document_ids: list[int] = Field(min_length=2)
    topic: str | None = Field(default=None, max_length=255)
    top_k_per_document: int | None = Field(default=None, ge=1, le=10)


class ConflictDetectionRequest(BaseModel):
    workspace_id: int
    document_ids: list[int] = Field(min_length=2)
    topic: str | None = Field(default=None, max_length=255)
    top_k_per_document: int | None = Field(default=None, ge=1, le=10)


class ComparisonItem(BaseModel):
    point: str
    citations: list[Citation] = Field(default_factory=list)


class ConflictItem(BaseModel):
    claim_a: str
    citations_a: list[Citation] = Field(default_factory=list)
    claim_b: str
    citations_b: list[Citation] = Field(default_factory=list)
    explanation: str
    confidence: str = "low"


class CompareResponse(BaseModel):
    summary: str
    similarities: list[ComparisonItem] = Field(default_factory=list)
    differences: list[ComparisonItem] = Field(default_factory=list)
    conflicts: list[ConflictItem] = Field(default_factory=list)
    source_chunks: list[SourceChunk] = Field(default_factory=list)
    document_names: list[str] = Field(default_factory=list)


class ConflictDetectionResponse(BaseModel):
    summary: str
    conflicts: list[ConflictItem] = Field(default_factory=list)
    source_chunks: list[SourceChunk] = Field(default_factory=list)
    document_names: list[str] = Field(default_factory=list)
