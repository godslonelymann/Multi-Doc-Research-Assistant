from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.models.document import Document
from app.schemas.chat import SourceChunk
from app.vectorstore.chroma import ChromaVectorStore
from app.vectorstore.embeddings import EmbeddingService


class RetrievalService:
    def __init__(
        self,
        db: Session,
        embeddings: EmbeddingService | None = None,
        vector_store: ChromaVectorStore | None = None,
    ) -> None:
        self.db = db
        self.embeddings = embeddings or EmbeddingService()
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve(self, workspace_id: int, question: str, top_k: int | None = None) -> list[SourceChunk]:
        matches = self._query_workspace_matches(workspace_id=workspace_id, question=question, top_k=top_k)
        return self._matches_to_source_chunks(matches, workspace_id=workspace_id)

    async def retrieve_async(self, workspace_id: int, question: str, top_k: int | None = None) -> list[SourceChunk]:
        matches = await run_in_threadpool(
            self._query_workspace_matches,
            workspace_id=workspace_id,
            question=question,
            top_k=top_k,
        )
        return self._matches_to_source_chunks(matches, workspace_id=workspace_id)

    def retrieve_for_document(
        self,
        workspace_id: int,
        document_id: int,
        query: str,
        top_k: int | None = None,
    ) -> list[SourceChunk]:
        matches = self._query_document_matches(
            workspace_id=workspace_id,
            document_id=document_id,
            query=query,
            top_k=top_k,
        )
        return self._matches_to_source_chunks(matches, workspace_id=workspace_id, document_id=document_id)

    async def retrieve_for_document_async(
        self,
        workspace_id: int,
        document_id: int,
        query: str,
        top_k: int | None = None,
    ) -> list[SourceChunk]:
        matches = await run_in_threadpool(
            self._query_document_matches,
            workspace_id=workspace_id,
            document_id=document_id,
            query=query,
            top_k=top_k,
        )
        return self._matches_to_source_chunks(matches, workspace_id=workspace_id, document_id=document_id)

    def _query_workspace_matches(self, workspace_id: int, question: str, top_k: int | None) -> list[dict]:
        query_embedding = self.embeddings.embed_texts([question])[0]
        return self.vector_store.query_workspace(
            workspace_id=workspace_id,
            query_embedding=query_embedding,
            top_k=top_k or settings.retrieval_top_k,
        )

    def _query_document_matches(
        self,
        workspace_id: int,
        document_id: int,
        query: str,
        top_k: int | None,
    ) -> list[dict]:
        query_embedding = self.embeddings.embed_texts([query])[0]
        return self.vector_store.query_document(
            workspace_id=workspace_id,
            document_id=document_id,
            query_embedding=query_embedding,
            top_k=top_k or settings.retrieval_top_k,
        )

    def _matches_to_source_chunks(
        self,
        matches: list[dict],
        workspace_id: int,
        document_id: int | None = None,
    ) -> list[SourceChunk]:
        source_chunks: list[SourceChunk] = []
        for match in matches:
            metadata = match["metadata"] or {}
            match_document_id = int(metadata.get("document_id", 0))
            document = self.db.get(Document, match_document_id) if match_document_id else None
            if document is None:
                continue
            if document.workspace_id != workspace_id:
                continue
            if document_id is not None and document.id != document_id:
                continue
            if document.upload_status != "completed":
                continue

            document_name = document.original_name if document else metadata.get("source_filename", "Unknown document")
            page_number = self._nullable_positive_int(metadata.get("page_number"))
            chunk_index = int(metadata.get("chunk_index", 0))
            distance = match.get("distance")

            source_chunks.append(
                SourceChunk(
                    vector_id=match["vector_id"],
                    document_id=match_document_id,
                    document_name=document_name,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    text=match["text"],
                    score=self._distance_to_score(distance),
                )
            )

        return source_chunks

    def _nullable_positive_int(self, value: object) -> int | None:
        if value in (None, "", 0):
            return None
        return int(value)

    def _distance_to_score(self, distance: object) -> float | None:
        if distance is None:
            return None
        return 1 / (1 + float(distance))
