# Architecture at a Glance

```
┌─────────────────┐     /api/*      ┌─────────────────┐     LLM / Embeddings
│  React (Vite)   │ ──────────────► │  FastAPI        │ ──────────────────► OpenAI
│  Port 3000/80   │                 │  Port 8000      │
└────────┬────────┘                 └────────┬────────┘
         │                                   │
         │                                   │ SQLAlchemy
         │                                   ▼
         │                          ┌─────────────────┐
         │                          │  Supabase       │  chat_sessions, chat_messages,
         │                          │  (PostgreSQL)   │  files, documents, parent_chunks
         │                          └─────────────────┘
         │
         │  SSE stream (status, token, sources, done)
         └────────────────────────────────────────────
```

- **Frontend:** SPA; `/api` proxied to backend (nginx in Docker, Vite in dev).
- **Backend:** REST + SSE; LangGraph agent runs analyze → retrieve → grade → generate → hallucination check.
- **DB:** Chats, messages (with sources), files, document chunks (vector + FTS), parent chunks for hybrid search.
