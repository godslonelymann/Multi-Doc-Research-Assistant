# Multi-Document Research Assistant with RAG + Report Generation

A local-first full-stack research assistant for working with multiple PDFs and TXT notes under a shared topic workspace. Users can upload sources, ask questions across all documents, compare selected documents, detect basic conflicts, generate topic summaries, and create structured reports with source citations.

Groq is used for text generation. Local development uses `sentence-transformers` for embeddings by default, ChromaDB stores vectors, and SQLite stores metadata. Vercel deployments use lightweight hashing embeddings and database-backed retrieval so the serverless bundle stays small and parsed document content can persist in hosted Postgres.

This project is intentionally local-first, but it includes Vercel configuration for one-project and split frontend/backend deployments.

## Problem Solved

Single-document chat tools are not enough for research workflows where evidence is spread across papers, notes, reports, and drafts. This app organizes sources by workspace and uses retrieval-augmented generation so answers, summaries, comparisons, conflicts, and reports are grounded in uploaded documents.

## Features

- Workspace/topic management
- Multi-file PDF and TXT upload
- Local file storage for development, temporary upload files on Vercel
- PDF text extraction with PyMuPDF
- Text cleaning and configurable chunking
- Embeddings with local `sentence-transformers` or a built-in serverless fallback
- ChromaDB vector storage locally, database-backed retrieval on Vercel
- SQLite metadata storage locally, hosted Postgres support for deployments
- Groq-powered text generation
- Workspace-scoped multi-document RAG chat
- Source citations with document name, page number, and chunk index where available
- Document comparison with similarities, differences, and conflicts
- Topic-wise summaries with key points and citations
- Structured report generation with sections and citations
- React frontend with workspace, document, chat, compare, summary, and report pages

## Architecture

```text
React + Vite + Tailwind
        |
      Axios
        |
FastAPI API routes
        |
Service layer
        |
Local: SQLite metadata + ChromaDB vectors + local uploaded files
Vercel: hosted SQL metadata/chunks + temporary upload files
        |
local or API embeddings + Groq generation
```

The backend keeps routes thin and puts ingestion, retrieval, chat, comparison, summary, and report logic in services. The frontend uses local component state and Axios service modules.

## Folder Structure

```text
multi-doc-research-assistant/
  client/
    src/
      components/
      hooks/
      lib/
      pages/
      services/
      styles/
    package.json
  server/
    app/
      ai/
        llm/
      api/
      core/
      db/
      models/
      schemas/
      services/
      utils/
      vectorstore/
      main.py
    requirements.txt
    .env.example
  docs/
  README.md
```

## Environment Variables

Backend: `server/.env`

```env
APP_NAME="Multi-Document Research Assistant"
APP_ENV=local
DEBUG=true
DATABASE_URL=sqlite:///./research_assistant.db
# Optional on Vercel/hosted deploys. Used only when DATABASE_URL is left at the local default.
POSTGRES_URL=
CLIENT_ORIGIN=http://localhost:5173

GROQ_API_KEY=
GROQ_BASE_URL=https://api.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.2
GROQ_TIMEOUT_SECONDS=60

CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=research_documents
VECTOR_STORE_PROVIDER=chroma
UPLOAD_DIR=./uploads
RETAIN_UPLOAD_FILES=true
MAX_UPLOAD_SIZE_MB=50
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1200
CHUNK_OVERLAP=200
RETRIEVAL_TOP_K=6
SUMMARY_TOP_K=8
REPORT_TOP_K=12
```

Frontend: `client/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_MAX_UPLOAD_SIZE_MB=50
```

## Groq Setup

1. Create or copy a Groq API key.
2. Put it in `server/.env`:

```env
GROQ_API_KEY=gsk_your_key_here
```

The default model is:

```env
GROQ_MODEL=llama-3.3-70b-versatile
```

Change `GROQ_MODEL` if you want to use another Groq chat model. Groq is used for generation. Local development uses `sentence-transformers` for embeddings by default; Vercel deployments can use the built-in hashing embedding provider to avoid bundling large ML dependencies.

## Local Setup

From a fresh checkout:

```bash
cd multi-doc-research-assistant
```

Backend:

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-local.txt
cp .env.example .env
# edit .env and set GROQ_API_KEY
uvicorn app.main:app --reload
```

The backend starts at:

```text
http://localhost:8000
```

On startup, the backend automatically creates:

- SQLite database tables
- `server/uploads/`
- `server/chroma_db/`

Frontend:

```bash
cd ../client
npm install
cp .env.example .env
npm run dev
```

The frontend starts at:

```text
http://localhost:5173
```

## Vercel Deployment

This repo includes Vercel config for both deployment styles:

- Deploy the repo root as one Vercel project. The frontend is served by Vite static output and the backend is served at `/api`.
- Deploy `client/` and `server/` as separate Vercel projects.

See `DEPLOYMENT.md` for exact settings and environment variables.

Important: Vercel Functions only provide durable code, not durable local runtime storage. For persistence across deployments and function restarts, set `DATABASE_URL` or `POSTGRES_URL` to hosted Postgres. On Vercel, uploaded files are used temporarily for parsing, while document metadata, parsed chunks, summaries, reports, and chat history live in the database. If no hosted database is configured, the app falls back to `/tmp` SQLite and data can disappear.

Vercel Functions also reject request bodies larger than 4.5 MB. The frontend defaults production uploads to 4 MB total per request to avoid raw `413` errors. For larger PDFs on Vercel, add direct browser uploads to Vercel Blob, S3, or Cloudflare R2 and ingest from the stored object.

## API Quick Checks

```bash
curl http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/workspaces \
  -H "Content-Type: application/json" \
  -d '{"name":"Example Research Topic","description":"Papers and notes for one topic"}'
```

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "workspace_id=1" \
  -F "files=@/path/to/paper.pdf" \
  -F "files=@/path/to/notes.txt"
```

```bash
curl -X POST http://localhost:8000/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"workspace_id":1,"question":"What do the sources say about the methodology?","top_k":6}'
```

## Sample Workflow

1. Start the backend and frontend.
2. Open `http://localhost:5173`.
3. Create a workspace for a research topic.
4. Upload multiple PDF or TXT documents into that workspace.
5. Open Chat and ask a question across all workspace documents.
6. Open Compare, select two or more documents, and compare methodology, conclusions, or another topic.
7. Run conflict detection for claims that may disagree.
8. Generate a topic-wise summary.
9. Generate a final structured report with citations.

## Known Limitations

- No authentication or multi-user permissions.
- No migrations; for schema-breaking local changes, delete the local SQLite database and re-ingest documents.
- Groq generation requires a valid `GROQ_API_KEY`.
- Conflict detection is prompt-based and conservative, not a formal entailment system.
- Scanned PDFs without embedded text require OCR, which is not implemented.
- Large documents may take time to embed locally.
- The frontend does not currently list previously generated summaries or reports; it displays newly generated results.

## Future Improvements

- Add Alembic migrations.
- Add OCR for scanned PDFs.
- Add report export to Markdown or PDF.
- Add saved summary/report listing pages.
- Add richer citation navigation to exact source chunks.
- Add reranking for retrieval quality.
- Add background ingestion jobs for large uploads.
