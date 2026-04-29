from app.core.config import settings
from app.utils.text import clean_text


class TextChunker:
    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")

    def chunk_pages(self, pages: list[dict]) -> list[dict]:
        chunks: list[dict] = []
        for page in pages:
            text = clean_text(page.get("text", ""))
            if not text:
                continue
            chunks.extend(self._chunk_text(text=text, page_number=page.get("page_number")))
        return chunks

    def _chunk_text(self, text: str, page_number: int | None) -> list[dict]:
        if len(text) <= self.chunk_size:
            return [{"text": text, "page_number": page_number}]

        chunks: list[dict] = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page_number": page_number})
            if end >= len(text):
                break
            start = end - self.chunk_overlap
        return chunks
