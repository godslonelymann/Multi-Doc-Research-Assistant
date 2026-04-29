# Vercel Deployment

This repository is Vercel-ready in two modes:

1. Deploy the repo root as one Vercel project. The React app is served as static files and FastAPI is served under `/api`.
2. Deploy `client/` and `server/` as two separate Vercel projects.

## One Project From Repo Root

Import the repository in Vercel and keep the root directory as the repository root.

The repository pins Vercel's Python runtime to 3.12 with `.python-version` and `pyproject.toml`.

Vercel uses the root `vercel.json`:

- builds `client/` with Vite using `npm --prefix client ci && npm --prefix client run build`
- exposes FastAPI from `api/index.py`
- routes `/api/*` to FastAPI
- routes all other paths to the React app

Set these environment variables in Vercel:

```env
GROQ_API_KEY=your_groq_key
CLIENT_ORIGIN=https://your-project.vercel.app
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
```

You can also set `POSTGRES_URL` instead of `DATABASE_URL`. The app uses `POSTGRES_URL` when `DATABASE_URL` is left at the local default, which matches Vercel Postgres/Neon-style integrations.

Optional production overrides:

```env
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.2
GROQ_TIMEOUT_SECONDS=60
VECTOR_STORE_PROVIDER=database
EMBEDDING_PROVIDER=hashing
EMBEDDING_MODEL=local-hashing-384
RETAIN_UPLOAD_FILES=false
MAX_UPLOAD_SIZE_MB=4
VITE_MAX_UPLOAD_SIZE_MB=4
```

Do not set `VITE_API_BASE_URL` for the one-project setup. The frontend defaults to `/api` in production.

Deploy:

```bash
vercel
vercel --prod
```

## Separate Frontend And Backend Projects

### Backend

Import the repo in Vercel and set the project root directory to `server`.

Set environment variables:

```env
GROQ_API_KEY=your_groq_key
CLIENT_ORIGIN=https://your-frontend.vercel.app
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
```

Deploy from the CLI if preferred:

```bash
cd server
vercel
vercel --prod
```

### Frontend

Import the repo in Vercel and set the project root directory to `client`.

Set environment variables:

```env
VITE_API_BASE_URL=https://your-backend.vercel.app
```

Deploy from the CLI if preferred:

```bash
cd client
vercel
vercel --prod
```

## Persistence

Vercel Functions have a read-only deployment filesystem and only `/tmp` is writable at runtime. This project falls back to `/tmp` automatically on Vercel so it can deploy and run without extra services, but `/tmp` is not durable storage.

For durable Vercel usage, configure hosted Postgres through `DATABASE_URL` or `POSTGRES_URL`. The app will then persist:

- workspaces
- document metadata
- parsed document chunks used for retrieval
- chat sessions and messages
- summaries and reports

On Vercel, `RETAIN_UPLOAD_FILES` defaults to `false`. Uploaded PDFs/TXT files are written to `/tmp` only long enough to parse them, then the app keeps the parsed chunks in the database. If you need original-file downloads later, add Vercel Blob, S3, or Cloudflare R2 and store those object keys on each document.

The Vercel runtime also defaults `VECTOR_STORE_PROVIDER=database` and `EMBEDDING_PROVIDER=hashing`. Local development keeps `VECTOR_STORE_PROVIDER=chroma` and `EMBEDDING_PROVIDER=sentence_transformers` unless you override them.

## Upload Size On Vercel

Vercel Functions reject request bodies larger than 4.5 MB with `413 FUNCTION_PAYLOAD_TOO_LARGE`. This app uses direct multipart uploads to FastAPI, so deployed uploads should stay under about 4 MB total per request after multipart overhead.

For larger PDFs, add browser direct uploads to Vercel Blob, S3, or Cloudflare R2, then pass the stored object URL/key to a backend ingestion endpoint. Server-side `MAX_UPLOAD_SIZE_MB=50` is only realistic for local development or non-Vercel hosts that allow larger request bodies.
