from pathlib import Path


def extract_pdf_text(path: Path) -> list[dict]:
    import fitz

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
