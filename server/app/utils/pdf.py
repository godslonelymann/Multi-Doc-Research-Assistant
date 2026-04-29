from pathlib import Path


def extract_pdf_text(path: Path) -> list[dict]:
    try:
        import fitz
    except ImportError:
        return _extract_pdf_text_with_pypdf(path)

    pages: list[dict] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document):
            pages.append(
                {
                    "page_number": page_index + 1,
                    "text": page.get_text("text"),
                }
            )
    return pages


def _extract_pdf_text_with_pypdf(path: Path) -> list[dict]:
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages: list[dict] = []
    for page_index, page in enumerate(reader.pages):
        pages.append(
            {
                "page_number": page_index + 1,
                "text": page.extract_text() or "",
            }
        )
    return pages
