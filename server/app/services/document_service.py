from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.processing_job import ProcessingJob
from app.models.workspace import Workspace
from app.services.chunking_service import TextChunker
from app.services.document_parser import DocumentParser
from app.services.file_storage_service import FileStorageService
from app.utils.text import text_preview
from app.vectorstore.chroma import ChromaVectorStore
from app.vectorstore.embeddings import EmbeddingService


SUPPORTED_FILE_TYPES = {"pdf", "txt"}


class DocumentService:
    def __init__(
        self,
        db: Session,
        storage: FileStorageService | None = None,
        parser: DocumentParser | None = None,
        chunker: TextChunker | None = None,
        embeddings: EmbeddingService | None = None,
        vector_store: ChromaVectorStore | None = None,
    ) -> None:
        self.db = db
        self.storage = storage or FileStorageService()
        self.parser = parser or DocumentParser()
        self.chunker = chunker or TextChunker()
        self.embeddings = embeddings or EmbeddingService()
        self.vector_store = vector_store or ChromaVectorStore()

    async def upload_documents(self, uploads: list[UploadFile], workspace_id: int | None = None) -> list[Document]:
        if workspace_id is not None and not self.db.get(Workspace, workspace_id):
            raise LookupError(f"Workspace {workspace_id} was not found")

        for upload in uploads:
            self._detect_file_type(upload.filename or "uploaded-document")

        documents: list[Document] = []
        for upload in uploads:
            documents.append(await self._ingest_upload(upload=upload, workspace_id=workspace_id))
        return documents

    def list_documents(self, workspace_id: int | None = None) -> list[Document]:
        statement = select(Document).order_by(Document.created_at.desc())
        if workspace_id is not None:
            statement = statement.where(Document.workspace_id == workspace_id)
        return list(self.db.scalars(statement).all())

    def get_document(self, document_id: int) -> Document | None:
        statement = (
            select(Document)
            .options(selectinload(Document.chunks), selectinload(Document.jobs))
            .where(Document.id == document_id)
        )
        return self.db.scalar(statement)

    def delete_document(self, document_id: int) -> bool:
        document = self.get_document(document_id)
        if document is None:
            return False

        storage_path = Path(document.storage_path)
        try:
            self.db.delete(document)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.vector_store.delete_document_vectors(document_id=document_id)
        if storage_path.exists() and storage_path.is_file():
            storage_path.unlink()
        return True

    async def _ingest_upload(self, upload: UploadFile, workspace_id: int | None) -> Document:
        original_name = upload.filename or "uploaded-document"
        file_type = self._detect_file_type(original_name)
        stored_name, storage_path = await self.storage.save_upload(upload, file_type=file_type)

        document = Document(
            workspace_id=workspace_id,
            filename=stored_name,
            original_name=original_name,
            file_type=file_type,
            upload_status="processing",
            storage_path=str(storage_path),
        )
        self.db.add(document)
        self.db.flush()

        job = ProcessingJob(
            document_id=document.id,
            status="processing",
            message="Document ingestion started.",
            started_at=datetime.utcnow(),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(document)

        vector_ids: list[str] = []
        vectors_added = False

        try:
            parsed_pages = await run_in_threadpool(self.parser.parse, path=storage_path, file_type=file_type)
            chunks = await run_in_threadpool(self.chunker.chunk_pages, parsed_pages)
            if not chunks:
                raise ValueError("No extractable text was found in the uploaded document")

            texts = [chunk["text"] for chunk in chunks]
            vector_ids = [f"doc-{document.id}-chunk-{index}" for index in range(len(chunks))]
            embeddings = await run_in_threadpool(self.embeddings.embed_texts, texts)
            if len(embeddings) != len(chunks):
                raise ValueError("Embedding count did not match generated chunk count")

            metadatas = [
                {
                    "document_id": document.id,
                    "workspace_id": workspace_id or 0,
                    "chunk_index": index,
                    "page_number": chunk.get("page_number") or 0,
                    "source_filename": original_name,
                    "file_type": file_type,
                }
                for index, chunk in enumerate(chunks)
            ]

            await run_in_threadpool(
                self.vector_store.add_chunks,
                ids=vector_ids,
                texts=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            vectors_added = True

            for index, chunk in enumerate(chunks):
                self.db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        page_number=chunk.get("page_number"),
                        source_filename=original_name,
                        text_preview=text_preview(chunk["text"]),
                        content=chunk["text"],
                        vector_id=vector_ids[index],
                    )
                )

            document.upload_status = "completed"
            document.chunk_count = len(chunks)
            document.error_message = None
            document.updated_at = datetime.utcnow()
            job.status = "completed"
            job.message = f"Ingested {len(chunks)} chunks."
            job.completed_at = datetime.utcnow()
            self.db.commit()
            await self._cleanup_upload_file(storage_path)
        except Exception as exc:
            self.db.rollback()
            if vectors_added:
                try:
                    await run_in_threadpool(self.vector_store.delete_document_vectors, document_id=document.id)
                except Exception:
                    pass

            document = self.db.get(Document, document.id)
            job = self.db.get(ProcessingJob, job.id)
            if document is None or job is None:
                raise

            document.upload_status = "failed"
            document.error_message = str(exc)
            document.updated_at = datetime.utcnow()
            job.status = "failed"
            job.message = str(exc)
            job.completed_at = datetime.utcnow()
            self.db.commit()
            await self._cleanup_upload_file(storage_path)

        self.db.refresh(document)
        return document

    async def _cleanup_upload_file(self, storage_path: Path) -> None:
        if settings.retain_upload_files:
            return
        try:
            if storage_path.exists() and storage_path.is_file():
                await run_in_threadpool(storage_path.unlink)
        except OSError:
            pass

    def _detect_file_type(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower().lstrip(".")
        if suffix not in SUPPORTED_FILE_TYPES:
            raise ValueError("Only PDF and TXT uploads are supported")
        return suffix
