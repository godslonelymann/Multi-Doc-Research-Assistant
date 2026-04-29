import json
import math
import sqlite3
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings


class ChromaVectorStore:
    def __init__(
        self,
        persist_dir: str | None = None,
        collection_name: str | None = None,
        provider: str | None = None,
        session_factory=None,
        database_embeddings=None,
    ) -> None:
        self.provider = provider or settings.vector_store_provider
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name
        self.session_factory = session_factory
        self.database_embeddings = database_embeddings
        self._client = None
        self._collection = None

    def is_configured(self) -> bool:
        return bool(self.persist_dir)

    @property
    def client(self):
        if self._client is None:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(name=self.collection_name)
        return self._collection

    def add_chunks(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        if not ids:
            return
        if self.provider == "database":
            return
        if self.provider == "sqlite":
            self._sqlite_add_chunks(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)
            return
        self.collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    def delete_document_vectors(self, document_id: int) -> None:
        if self.provider == "database":
            return
        if self.provider == "sqlite":
            self._sqlite_delete_document_vectors(document_id=document_id)
            return
        self.collection.delete(where={"document_id": document_id})

    def query_workspace(
        self,
        workspace_id: int,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict]:
        if self.provider == "database":
            return self._database_query(
                workspace_id=workspace_id,
                document_id=None,
                query_embedding=query_embedding,
                top_k=top_k,
            )
        if self.provider == "sqlite":
            return self._sqlite_query(
                workspace_id=workspace_id,
                document_id=None,
                query_embedding=query_embedding,
                top_k=top_k,
            )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"workspace_id": workspace_id},
            include=["documents", "metadatas", "distances"],
        )

        return self._normalize_query_results(results)

    def query_document(
        self,
        workspace_id: int,
        document_id: int,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict]:
        if self.provider == "database":
            return self._database_query(
                workspace_id=workspace_id,
                document_id=document_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )
        if self.provider == "sqlite":
            return self._sqlite_query(
                workspace_id=workspace_id,
                document_id=document_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"$and": [{"workspace_id": workspace_id}, {"document_id": document_id}]},
            include=["documents", "metadatas", "distances"],
        )
        return self._normalize_query_results(results)

    def _normalize_query_results(self, results: dict) -> list[dict]:
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        matches: list[dict] = []
        for index, vector_id in enumerate(ids):
            matches.append(
                {
                    "vector_id": vector_id,
                    "text": documents[index],
                    "metadata": metadatas[index],
                    "distance": distances[index],
                }
            )
        return matches

    def _database_query(
        self,
        workspace_id: int,
        document_id: int | None,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict]:
        from app.models.document import Document
        from app.models.document_chunk import DocumentChunk
        from app.vectorstore.embeddings import EmbeddingService

        statement = (
            select(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.workspace_id == workspace_id)
            .where(Document.upload_status == "completed")
        )
        if document_id is not None:
            statement = statement.where(Document.id == document_id)

        if self.session_factory is None:
            from app.db.session import SessionLocal

            session_factory = SessionLocal
        else:
            session_factory = self.session_factory

        with session_factory() as session:
            rows = session.execute(statement).all()

        if not rows:
            return []

        texts = [chunk.content for chunk, _document in rows]
        embedding_service = self.database_embeddings or EmbeddingService()
        embeddings = embedding_service.embed_texts(texts)

        matches = []
        for (chunk, document), embedding in zip(rows, embeddings, strict=True):
            similarity = self._cosine_similarity(query_embedding, embedding)
            matches.append(
                {
                    "vector_id": chunk.vector_id or f"doc-{document.id}-chunk-{chunk.chunk_index}",
                    "text": chunk.content,
                    "metadata": {
                        "document_id": document.id,
                        "workspace_id": document.workspace_id or 0,
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number or 0,
                        "source_filename": chunk.source_filename or document.original_name,
                        "file_type": document.file_type,
                    },
                    "distance": 1 - similarity,
                }
            )

        return sorted(matches, key=lambda match: match["distance"])[:top_k]

    @property
    def sqlite_path(self) -> Path:
        return Path(self.persist_dir) / f"{self.collection_name}.sqlite3"

    def _sqlite_connect(self) -> sqlite3.Connection:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.sqlite_path)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS vector_chunks (
                id TEXT PRIMARY KEY,
                workspace_id INTEGER NOT NULL,
                document_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                embedding TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_vector_chunks_workspace ON vector_chunks (workspace_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_vector_chunks_document ON vector_chunks (document_id)")
        return connection

    def _sqlite_add_chunks(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        rows = []
        for vector_id, text, embedding, metadata in zip(ids, texts, embeddings, metadatas, strict=True):
            rows.append(
                (
                    vector_id,
                    int(metadata["workspace_id"]),
                    int(metadata["document_id"]),
                    text,
                    json.dumps(embedding),
                    json.dumps(metadata),
                )
            )

        with self._sqlite_connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO vector_chunks
                    (id, workspace_id, document_id, text, embedding, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def _sqlite_delete_document_vectors(self, document_id: int) -> None:
        with self._sqlite_connect() as connection:
            connection.execute("DELETE FROM vector_chunks WHERE document_id = ?", (document_id,))

    def _sqlite_query(
        self,
        workspace_id: int,
        document_id: int | None,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict]:
        query = "SELECT id, text, embedding, metadata FROM vector_chunks WHERE workspace_id = ?"
        params: list[int] = [workspace_id]
        if document_id is not None:
            query += " AND document_id = ?"
            params.append(document_id)

        with self._sqlite_connect() as connection:
            rows = connection.execute(query, params).fetchall()

        matches = []
        for vector_id, text, embedding_json, metadata_json in rows:
            embedding = json.loads(embedding_json)
            similarity = self._cosine_similarity(query_embedding, embedding)
            matches.append(
                {
                    "vector_id": vector_id,
                    "text": text,
                    "metadata": json.loads(metadata_json),
                    "distance": 1 - similarity,
                }
            )

        return sorted(matches, key=lambda match: match["distance"])[:top_k]

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))
        left_magnitude = math.sqrt(sum(value * value for value in left))
        right_magnitude = math.sqrt(sum(value * value for value in right))
        if left_magnitude == 0 or right_magnitude == 0:
            return 0.0
        return dot_product / (left_magnitude * right_magnitude)
