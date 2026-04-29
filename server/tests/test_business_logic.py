import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import (
    chat_message,
    chat_session,
    document,
    document_chunk,
    processing_job,
    report,
    report_section,
    summary,
    workspace,
)
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.workspace import Workspace
from app.schemas.comparison import CompareRequest
from app.schemas.chat import ChatAskRequest
from app.schemas.summary import SummaryGenerateRequest
from app.services.chat_service import ChatService
from app.services.comparison_service import ComparisonService
from app.services.context_builder import ContextBuilder
from app.services.document_service import DocumentService
from app.services.file_storage_service import FileStorageService
from app.services.retrieval_service import RetrievalService
from app.services.summary_service import SummaryService

_ = (
    chat_message,
    chat_session,
    document,
    document_chunk,
    processing_job,
    report,
    report_section,
    summary,
    workspace,
)


class FakeEmbeddings:
    def __init__(self, vectors=None):
        self.vectors = vectors

    def embed_texts(self, texts):
        if self.vectors is not None:
            return self.vectors
        return [[float(index + 1)] for index, _ in enumerate(texts)]


class FakeVectorStore:
    def __init__(self, workspace_matches=None, document_matches=None):
        self.workspace_matches = workspace_matches or []
        self.document_matches = document_matches or []
        self.added = []
        self.deleted_document_ids = []

    def add_chunks(self, ids, texts, embeddings, metadatas):
        self.added.append(
            {
                "ids": ids,
                "texts": texts,
                "embeddings": embeddings,
                "metadatas": metadatas,
            }
        )

    def delete_document_vectors(self, document_id):
        self.deleted_document_ids.append(document_id)

    def query_workspace(self, workspace_id, query_embedding, top_k):
        return self.workspace_matches[:top_k]

    def query_document(self, workspace_id, document_id, query_embedding, top_k):
        return self.document_matches[:top_k]


class FakeParser:
    def __init__(self, pages):
        self.pages = pages

    def parse(self, path, file_type):
        return self.pages


class FakeUpload:
    def __init__(self, filename, content=b"hello"):
        self.filename = filename
        self.content = content
        self.closed = False
        self.offset = 0

    async def read(self, size=-1):
        if self.offset >= len(self.content):
            return b""
        if size is None or size < 0:
            size = len(self.content) - self.offset
        end = min(self.offset + size, len(self.content))
        chunk = self.content[self.offset:end]
        self.offset = end
        return chunk

    async def close(self):
        self.closed = True


class FakeRetrievalService:
    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(self, workspace_id, question, top_k=None):
        return self.chunks


class FakeLLMService:
    async def answer_question(self, question, source_chunks):
        return "Precise answer [Evidence 1]"

    async def generate(self, prompt):
        return (
            '{"summary":"Grounded summary","key_points":['
            '{"point":"Point one","citations":["Evidence 1"]}'
            "]}"
        )


class BusinessLogicTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def create_workspace(self, name="Workspace"):
        workspace = Workspace(name=name)
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def create_document(self, workspace_id, name, status="completed"):
        document = Document(
            workspace_id=workspace_id,
            filename=f"{name}.txt",
            original_name=f"{name}.txt",
            file_type="txt",
            upload_status=status,
            storage_path=f"/tmp/{name}.txt",
            chunk_count=1 if status == "completed" else 0,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def test_retrieval_filters_cross_workspace_stale_and_not_ready_vectors(self):
        workspace_a = self.create_workspace("A")
        workspace_b = self.create_workspace("B")
        ready_doc = self.create_document(workspace_a.id, "ready")
        other_workspace_doc = self.create_document(workspace_b.id, "other")
        processing_doc = self.create_document(workspace_a.id, "processing", status="processing")

        matches = [
            {
                "vector_id": "ok",
                "text": "workspace A evidence",
                "metadata": {"document_id": ready_doc.id, "page_number": 1, "chunk_index": 0},
                "distance": 0.2,
            },
            {
                "vector_id": "leak",
                "text": "workspace B evidence",
                "metadata": {"document_id": other_workspace_doc.id, "page_number": 1, "chunk_index": 0},
                "distance": 0.1,
            },
            {
                "vector_id": "not-ready",
                "text": "processing evidence",
                "metadata": {"document_id": processing_doc.id, "page_number": 1, "chunk_index": 0},
                "distance": 0.1,
            },
            {
                "vector_id": "stale",
                "text": "deleted evidence",
                "metadata": {"document_id": 999, "page_number": 1, "chunk_index": 0},
                "distance": 0.1,
            },
        ]
        service = RetrievalService(
            self.db,
            embeddings=FakeEmbeddings(),
            vector_store=FakeVectorStore(workspace_matches=matches),
        )

        chunks = service.retrieve(workspace_id=workspace_a.id, question="evidence", top_k=10)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].document_id, ready_doc.id)
        self.assertEqual(chunks[0].text, "workspace A evidence")

    def test_retrieve_for_document_filters_wrong_document_metadata(self):
        workspace = self.create_workspace()
        selected_doc = self.create_document(workspace.id, "selected")
        other_doc = self.create_document(workspace.id, "other")
        matches = [
            {
                "vector_id": "wrong",
                "text": "wrong document",
                "metadata": {"document_id": other_doc.id, "page_number": 1, "chunk_index": 0},
                "distance": 0.1,
            },
            {
                "vector_id": "right",
                "text": "selected document",
                "metadata": {"document_id": selected_doc.id, "page_number": 2, "chunk_index": 1},
                "distance": 0.2,
            },
        ]
        service = RetrievalService(
            self.db,
            embeddings=FakeEmbeddings(),
            vector_store=FakeVectorStore(document_matches=matches),
        )

        chunks = service.retrieve_for_document(
            workspace_id=workspace.id,
            document_id=selected_doc.id,
            query="topic",
            top_k=10,
        )

        self.assertEqual([chunk.vector_id for chunk in chunks], ["right"])

    def test_comparison_requires_completed_documents_in_selected_workspace(self):
        workspace = self.create_workspace()
        completed = self.create_document(workspace.id, "completed")
        processing = self.create_document(workspace.id, "processing", status="processing")
        service = ComparisonService(self.db)

        with self.assertRaisesRegex(ValueError, "Only completed documents"):
            service._load_documents(
                workspace_id=workspace.id,
                document_ids=[completed.id, processing.id],
            )

    def test_delete_document_removes_rows_and_vectors(self):
        workspace = self.create_workspace()
        document = self.create_document(workspace.id, "delete-me")
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            page_number=1,
            source_filename=document.original_name,
            text_preview="preview",
            content="content",
            vector_id="vector-1",
        )
        self.db.add(chunk)
        self.db.commit()
        vector_store = FakeVectorStore()
        service = DocumentService(self.db, vector_store=vector_store)

        deleted = service.delete_document(document.id)

        self.assertTrue(deleted)
        self.assertEqual(vector_store.deleted_document_ids, [document.id])
        self.assertIsNone(self.db.get(Document, document.id))
        chunks = list(self.db.scalars(select(DocumentChunk)).all())
        self.assertEqual(chunks, [])

    async def test_ingest_cleans_vectors_if_database_commit_fails_after_indexing(self):
        workspace = self.create_workspace()
        vector_store = FakeVectorStore()
        with TemporaryDirectory() as tmpdir:
            service = DocumentService(
                self.db,
                parser=FakeParser([{"page_number": 1, "text": "This is enough text to index."}]),
                embeddings=FakeEmbeddings(),
                vector_store=vector_store,
            )
            service.storage.upload_dir = Path(tmpdir)
            original_commit = self.db.commit
            call_count = {"value": 0}

            def commit_side_effect():
                call_count["value"] += 1
                if call_count["value"] == 2:
                    raise RuntimeError("database write failed")
                return original_commit()

            commit_mock = Mock(side_effect=commit_side_effect)
            self.db.commit = commit_mock
            try:
                document = await service.upload_documents([FakeUpload("source.txt")], workspace_id=workspace.id)
            finally:
                self.db.commit = original_commit

        self.assertEqual(document[0].upload_status, "failed")
        self.assertEqual(vector_store.deleted_document_ids, [document[0].id])
        self.assertEqual(self.db.get(Document, document[0].id).chunk_count, 0)

    async def test_storage_rejects_invalid_pdf_signature(self):
        with TemporaryDirectory() as tmpdir:
            storage = FileStorageService(upload_dir=tmpdir)

            with self.assertRaisesRegex(ValueError, "valid PDF signature"):
                await storage.save_upload(FakeUpload("fake.pdf", content=b"not a pdf"), file_type="pdf")

            self.assertEqual(list(Path(tmpdir).iterdir()), [])

    async def test_storage_rejects_files_over_size_limit(self):
        with TemporaryDirectory() as tmpdir:
            storage = FileStorageService(upload_dir=tmpdir)
            storage.max_upload_size_bytes = 3

            with self.assertRaisesRegex(ValueError, "size limit"):
                await storage.save_upload(FakeUpload("large.txt", content=b"abcd"), file_type="txt")

            self.assertEqual(list(Path(tmpdir).iterdir()), [])

    def test_context_builder_preserves_citation_source_mapping(self):
        workspace = self.create_workspace()
        document = self.create_document(workspace.id, "paper")
        service = RetrievalService(
            self.db,
            embeddings=FakeEmbeddings(),
            vector_store=FakeVectorStore(
                workspace_matches=[
                    {
                        "vector_id": "v1",
                        "text": "quoted evidence",
                        "metadata": {"document_id": document.id, "page_number": 3, "chunk_index": 2},
                        "distance": 0.5,
                    }
                ]
            ),
        )
        chunks = service.retrieve(workspace_id=workspace.id, question="topic")

        context, citations = ContextBuilder().build(chunks)

        self.assertIn("[Evidence 1] paper.txt, page 3, chunk 2", context)
        self.assertEqual(citations[0].document_id, document.id)
        self.assertEqual(citations[0].page_number, 3)
        self.assertEqual(citations[0].chunk_index, 2)

    async def test_summary_generation_persists_resolved_citations_and_source_chunks(self):
        workspace = self.create_workspace()
        document = self.create_document(workspace.id, "summary-source")
        source_chunk = RetrievalService(
            self.db,
            embeddings=FakeEmbeddings(),
            vector_store=FakeVectorStore(
                workspace_matches=[
                    {
                        "vector_id": "v1",
                        "text": "summary evidence",
                        "metadata": {"document_id": document.id, "page_number": 4, "chunk_index": 0},
                        "distance": 0.2,
                    }
                ]
            ),
        ).retrieve(workspace_id=workspace.id, question="topic")[0]
        service = SummaryService(
            self.db,
            retrieval_service=FakeRetrievalService([source_chunk]),
            llm_service=FakeLLMService(),
        )

        summary = await service.generate(SummaryGenerateRequest(workspace_id=workspace.id, topic="topic"))

        self.assertEqual(summary.summary, "Grounded summary")
        self.assertEqual(summary.key_points[0]["citations"][0]["document_id"], document.id)
        self.assertEqual(summary.source_chunks[0]["vector_id"], "v1")

    async def test_chat_response_reports_uploaded_ready_used_and_evidence_counts(self):
        workspace = self.create_workspace()
        ready_doc = self.create_document(workspace.id, "ready")
        self.create_document(workspace.id, "processing", status="processing")
        source_chunk = RetrievalService(
            self.db,
            embeddings=FakeEmbeddings(),
            vector_store=FakeVectorStore(
                workspace_matches=[
                    {
                        "vector_id": "v1",
                        "text": "answer evidence",
                        "metadata": {"document_id": ready_doc.id, "page_number": 1, "chunk_index": 0},
                        "distance": 0.1,
                    }
                ]
            ),
        ).retrieve(workspace_id=workspace.id, question="question")[0]
        service = ChatService(
            self.db,
            retrieval_service=FakeRetrievalService([source_chunk]),
            llm_service=FakeLLMService(),
        )

        response = await service.ask(ChatAskRequest(workspace_id=workspace.id, question="question"))

        self.assertEqual(response.uploaded_document_count, 2)
        self.assertEqual(response.ready_document_count, 1)
        self.assertEqual(response.used_document_count, 1)
        self.assertEqual(response.evidence_count, 1)


if __name__ == "__main__":
    unittest.main()
