from pathlib import Path

from app.utils.pdf import extract_pdf_text


class DocumentParser:
    def parse(self, path: Path, file_type: str) -> list[dict]:
        if file_type == "pdf":
            return extract_pdf_text(path)
        if file_type == "txt":
            return [{"page_number": None, "text": path.read_text(encoding="utf-8", errors="ignore")}]
        raise ValueError(f"Unsupported file type: {file_type}")
