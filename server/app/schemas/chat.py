from datetime import datetime

from pydantic import BaseModel, Field


class ChatAskRequest(BaseModel):
    workspace_id: int
    question: str = Field(min_length=1)
    session_id: int | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


class Citation(BaseModel):
    document_id: int
    document_name: str
    page_number: int | None = None
    chunk_index: int
    source_label: str


class SourceChunk(BaseModel):
    vector_id: str
    document_id: int
    document_name: str
    page_number: int | None = None
    chunk_index: int
    text: str
    score: float | None = None


class ChatAskResponse(BaseModel):
    session_id: int
    answer: str
    citations: list[Citation]
    source_chunks: list[SourceChunk]
    document_names: list[str]
    page_numbers: list[int]
    uploaded_document_count: int = 0
    ready_document_count: int = 0
    used_document_count: int = 0
    evidence_count: int = 0


class ChatMessageRead(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations: list | None = None
    source_chunks: list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionRead(BaseModel):
    id: int
    workspace_id: int
    title: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionDetail(ChatSessionRead):
    messages: list[ChatMessageRead] = Field(default_factory=list)


class ChatMessagesResponse(BaseModel):
    messages: list[ChatMessageRead]
