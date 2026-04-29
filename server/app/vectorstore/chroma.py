from app.core.config import settings


class ChromaVectorStore:
    def __init__(self, persist_dir: str | None = None, collection_name: str | None = None) -> None:
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name
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
        self.collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    def delete_document_vectors(self, document_id: int) -> None:
        self.collection.delete(where={"document_id": document_id})

    def query_workspace(
        self,
        workspace_id: int,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict]:
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
