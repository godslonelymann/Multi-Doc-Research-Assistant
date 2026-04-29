from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.comparison import (
    CompareRequest,
    CompareResponse,
    ConflictDetectionRequest,
    ConflictDetectionResponse,
)
from app.services.comparison_service import ComparisonService

router = APIRouter()


@router.post("/compare", response_model=CompareResponse)
async def compare_documents(payload: CompareRequest, db: Session = Depends(get_db)) -> CompareResponse:
    try:
        return await ComparisonService(db).compare(payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/conflicts", response_model=ConflictDetectionResponse)
async def detect_conflicts(
    payload: ConflictDetectionRequest,
    db: Session = Depends(get_db),
) -> ConflictDetectionResponse:
    try:
        return await ComparisonService(db).detect_conflicts(payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
