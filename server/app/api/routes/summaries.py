from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.summary import SummaryGenerateRequest, SummaryRead
from app.services.summary_service import SummaryService

router = APIRouter()


@router.post("/generate", response_model=SummaryRead, status_code=status.HTTP_201_CREATED)
async def generate_summary(payload: SummaryGenerateRequest, db: Session = Depends(get_db)) -> SummaryRead:
    try:
        return await SummaryService(db).generate(payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{summary_id}", response_model=SummaryRead)
def get_summary(summary_id: int, db: Session = Depends(get_db)) -> SummaryRead:
    summary = SummaryService(db).get_summary(summary_id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return summary
