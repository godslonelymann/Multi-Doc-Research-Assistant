import math
import re
from hashlib import blake2b


HASHING_EMBEDDING_DIMENSIONS = 384
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


class EmbeddingService:
    def __init__(self, model_name: str | None = None) -> None:
        from app.core.config import settings

        self.provider = settings.embedding_provider
        self.model_name = model_name or settings.embedding_model
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if self.provider == "hashing":
            return [self._embed_with_hashing(text) for text in texts]

        if self.provider != "sentence_transformers":
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    def _normalize(self, vector: list[float]) -> list[float]:
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]

    def _embed_with_hashing(self, text: str) -> list[float]:
        vector = [0.0] * HASHING_EMBEDDING_DIMENSIONS
        tokens = TOKEN_PATTERN.findall(text.lower())

        for token in tokens:
            digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], byteorder="big") % HASHING_EMBEDDING_DIMENSIONS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        return self._normalize(vector)
