from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentDetail, DocumentListResponse, DocumentUploadResponse
from app.services.document_service import DocumentService

router = APIRouter()


@router.get("", response_model=DocumentListResponse)
def list_documents(workspace_id: int | None = None, db: Session = Depends(get_db)) -> DocumentListResponse:
    documents = DocumentService(db).list_documents(workspace_id=workspace_id)
    return DocumentListResponse(documents=documents)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: Annotated[list[UploadFile], File(...)],
    workspace_id: Annotated[int | None, Form()] = None,
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    try:
        documents = await DocumentService(db).upload_documents(uploads=files, workspace_id=workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return DocumentUploadResponse(documents=documents)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentDetail:
    document = DocumentService(db).get_document(document_id=document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)) -> None:
    deleted = DocumentService(db).delete_document(document_id=document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
