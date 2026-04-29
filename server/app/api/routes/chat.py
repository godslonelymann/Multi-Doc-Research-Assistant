from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatAskRequest, ChatAskResponse, ChatMessagesResponse, ChatSessionDetail
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/ask", response_model=ChatAskResponse)
async def ask_question(payload: ChatAskRequest, db: Session = Depends(get_db)) -> ChatAskResponse:
    try:
        return await ChatService(db).ask(payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_chat_session(session_id: int, db: Session = Depends(get_db)) -> ChatSessionDetail:
    session = ChatService(db).get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return session


@router.get("/sessions/{session_id}/messages", response_model=ChatMessagesResponse)
def get_chat_messages(session_id: int, db: Session = Depends(get_db)) -> ChatMessagesResponse:
    response = ChatService(db).get_messages(session_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return response
