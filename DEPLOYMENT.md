# Vercel Deployment

This repository is Vercel-ready in two modes:

1. Deploy the repo root as one Vercel project. The React app is served as static files and FastAPI is served under `/api`.
2. Deploy `client/` and `server/` as two separate Vercel projects.

## One Project From Repo Root

Import the repository in Vercel and keep the root directory as the repository root.

Vercel uses the root `vercel.json`:

- builds `client/` with Vite using `npm --prefix client ci && npm --prefix client run build`
- exposes FastAPI from `api/index.py`
- routes `/api/*` to FastAPI
- routes all other paths to the React app

Set these environment variables in Vercel:

```env
GROQ_API_KEY=your_groq_key
CLIENT_ORIGIN=https://your-project.vercel.app
```

Optional production overrides:

```env
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.2
GROQ_TIMEOUT_SECONDS=60
VECTOR_STORE_PROVIDER=sqlite
EMBEDDING_PROVIDER=hashing
EMBEDDING_MODEL=local-hashing-384
MAX_UPLOAD_SIZE_MB=50
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

## Persistence Warning

Vercel Functions have a read-only deployment filesystem and only `/tmp` is writable at runtime. This project now falls back to `/tmp` automatically on Vercel so it can deploy and run, but `/tmp` is not durable storage.

For a real production app, replace:

- SQLite with hosted Postgres
- local uploads with Vercel Blob, S3, or Cloudflare R2
- local ChromaDB or the Vercel SQLite fallback with hosted Chroma, Pinecone, Qdrant Cloud, or another managed vector database
- local `sentence-transformers` embeddings with hosted/API embeddings for best retrieval quality. The Vercel config defaults to a lightweight built-in hashing provider so the app can deploy with only `GROQ_API_KEY`.
