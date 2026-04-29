from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workspace import WorkspaceCreate, WorkspaceDetail, WorkspaceListResponse, WorkspaceRead
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: WorkspaceCreate, db: Session = Depends(get_db)) -> WorkspaceRead:
    return WorkspaceService(db).create_workspace(payload)


@router.get("", response_model=WorkspaceListResponse)
def list_workspaces(db: Session = Depends(get_db)) -> WorkspaceListResponse:
    workspaces = WorkspaceService(db).list_workspaces()
    return WorkspaceListResponse(workspaces=workspaces)


@router.get("/{workspace_id}", response_model=WorkspaceDetail)
def get_workspace(workspace_id: int, db: Session = Depends(get_db)) -> WorkspaceDetail:
    workspace = WorkspaceService(db).get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace
