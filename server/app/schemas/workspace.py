from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.document import DocumentRead


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class WorkspaceRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceDetail(WorkspaceRead):
    documents: list[DocumentRead] = Field(default_factory=list)


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceRead]
