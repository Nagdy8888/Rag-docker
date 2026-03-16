# backend/app

Core FastAPI application and RAG logic.

## Contents

- **main.py** — FastAPI app, routes (chat, documents, upload, health), SSE streaming.
- **database.py** — SQLAlchemy engine, session, Supabase/Postgres connection.
- **config.py** — App configuration and env-based settings.
- **schemas.py** — Pydantic request/response models.
- **retriever.py** — Hybrid search (dense + sparse), RRF, multi-query expansion, parent-child lookup.
- **document_processor.py** — File parsing, parent-child chunking, embeddings, DB writes.
- **watcher.py** — Optional file watcher for the documents folder.
- **agent/** — LangGraph agent (state, nodes, graph, prompts, streaming).

See [../README.md](../README.md) for how to run the backend. Architecture: [../../docs/guide/06-backend-structure.md](../../docs/guide/06-backend-structure.md).
