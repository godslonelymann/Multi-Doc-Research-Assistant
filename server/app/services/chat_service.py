from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.document import Document
from app.models.workspace import Workspace
from app.schemas.chat import ChatAskRequest, ChatAskResponse, ChatMessagesResponse
from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService


class ChatService:
    def __init__(
        self,
        db: Session,
        retrieval_service: RetrievalService | None = None,
        llm_service: LLMService | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.db = db
        self.retrieval_service = retrieval_service or RetrievalService(db)
        self.llm_service = llm_service or LLMService()
        self.context_builder = context_builder or ContextBuilder()

    async def ask(self, payload: ChatAskRequest) -> ChatAskResponse:
        workspace = self.db.get(Workspace, payload.workspace_id)
        if workspace is None:
            raise LookupError(f"Workspace {payload.workspace_id} was not found")

        session = self._get_or_create_session(payload)
        if hasattr(self.retrieval_service, "retrieve_async"):
            source_chunks = await self.retrieval_service.retrieve_async(
                workspace_id=payload.workspace_id,
                question=payload.question,
                top_k=payload.top_k,
            )
        else:
            source_chunks = self.retrieval_service.retrieve(
                workspace_id=payload.workspace_id,
                question=payload.question,
                top_k=payload.top_k,
            )
        _, citations = self.context_builder.build(source_chunks)
        answer = await self.llm_service.answer_question(question=payload.question, source_chunks=source_chunks)
        uploaded_document_count = self._count_documents(payload.workspace_id)
        ready_document_count = self._count_documents(payload.workspace_id, upload_status="completed")
        used_document_names = sorted({chunk.document_name for chunk in source_chunks})

        self.db.add(ChatMessage(session_id=session.id, role="user", content=payload.question))
        self.db.add(
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content=answer,
                citations=[citation.model_dump() for citation in citations],
                source_chunks=[chunk.model_dump() for chunk in source_chunks],
            )
        )
        session.updated_at = datetime.utcnow()
        self.db.commit()

        return ChatAskResponse(
            session_id=session.id,
            answer=answer,
            citations=citations,
            source_chunks=source_chunks,
            document_names=used_document_names,
            page_numbers=sorted({chunk.page_number for chunk in source_chunks if chunk.page_number is not None}),
            uploaded_document_count=uploaded_document_count,
            ready_document_count=ready_document_count,
            used_document_count=len(used_document_names),
            evidence_count=len(source_chunks),
        )

    def get_session(self, session_id: int) -> ChatSession | None:
        statement = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        return self.db.scalar(statement)

    def get_messages(self, session_id: int) -> ChatMessagesResponse | None:
        session = self.db.get(ChatSession, session_id)
        if session is None:
            return None
        statement = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
        messages = list(self.db.scalars(statement).all())
        return ChatMessagesResponse(messages=messages)

    def _get_or_create_session(self, payload: ChatAskRequest) -> ChatSession:
        if payload.session_id is not None:
            session = self.db.get(ChatSession, payload.session_id)
            if session is None:
                raise LookupError(f"Chat session {payload.session_id} was not found")
            if session.workspace_id != payload.workspace_id:
                raise ValueError("Chat session does not belong to the selected workspace")
            return session

        session = ChatSession(
            workspace_id=payload.workspace_id,
            title=payload.question.strip()[:120],
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def _count_documents(self, workspace_id: int, upload_status: str | None = None) -> int:
        statement = select(Document).where(Document.workspace_id == workspace_id)
        if upload_status is not None:
            statement = statement.where(Document.upload_status == upload_status)
        return len(list(self.db.scalars(statement).all()))
