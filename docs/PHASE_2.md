# Phase 2 RAG Q&A

This phase adds workspace-scoped multi-document question answering.

Included:

- ChatSession and ChatMessage models
- Workspace-scoped vector retrieval
- Query embedding with the configured sentence-transformers model
- ChromaDB top-k search scoped by workspace metadata
- Source chunk formatting for LLM context
- Citation metadata with document name, page number, and chunk index
- Groq LLM provider abstraction
- Persisted user and assistant chat messages
- Chat session detail and message list APIs

Not included yet:

- Document comparison
- Report generation
- Conflict detection
- Frontend chat workflow
