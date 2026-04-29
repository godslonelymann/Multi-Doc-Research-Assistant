# Phase 1 Ingestion

This phase provides the runnable application skeleton plus backend document ingestion.

Included:

- FastAPI app bootstrap
- SQLite SQLAlchemy configuration
- Workspace APIs
- Multi-file PDF/TXT upload
- Local file storage
- PDF text extraction with PyMuPDF
- Text cleaning and chunking
- Embedding generation with sentence-transformers
- ChromaDB vector storage
- SQLite document, chunk, workspace, and processing job metadata
- Document list/detail/delete APIs
- AI provider abstraction placeholder
- React + Vite app bootstrap
- React Router page placeholders
- Tailwind CSS setup

Added in Phase 2:

- Retrieval
- LLM calls
- Citation synthesis

Not included yet:

- Conflict detection
- Report generation
