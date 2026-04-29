from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate


class WorkspaceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_workspace(self, payload: WorkspaceCreate) -> Workspace:
        workspace = Workspace(name=payload.name, description=payload.description)
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def list_workspaces(self) -> list[Workspace]:
        statement = select(Workspace).order_by(Workspace.created_at.desc())
        return list(self.db.scalars(statement).all())

    def get_workspace(self, workspace_id: int) -> Workspace | None:
        statement = (
            select(Workspace)
            .options(selectinload(Workspace.documents))
            .where(Workspace.id == workspace_id)
        )
        return self.db.scalar(statement)
