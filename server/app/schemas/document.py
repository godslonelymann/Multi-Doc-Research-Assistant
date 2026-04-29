from datetime import datetime

from pydantic import BaseModel, Field


class DocumentChunkRead(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    page_number: int | None = None
    source_filename: str
    text_preview: str
    vector_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProcessingJobRead(BaseModel):
    id: int
    document_id: int
    status: str
    message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: int
    workspace_id: int | None = None
    filename: str
    original_name: str
    file_type: str
    upload_status: str
    chunk_count: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentRead):
    chunks: list[DocumentChunkRead] = Field(default_factory=list)
    jobs: list[ProcessingJobRead] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    documents: list[DocumentRead]


class DocumentUploadResponse(BaseModel):
    documents: list[DocumentRead]
