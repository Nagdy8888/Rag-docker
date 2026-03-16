# Phased Development Plan (Detailed)

This project follows a **strict 4-phase build**. Each phase is standalone and runnable; the next phase extends it.

## Phase 1 — Simple Chatbot

**Goal:** Chat UI, chat history in Supabase, Docker, streaming replies.

**Deliverables:**

- Backend: `config.py`, `database.py`, `schemas.py`, agent (single generate node), `main.py` with `POST /api/chat` (SSE), `GET /api/chats`, `GET /api/chats/{id}`.
- Frontend: React + Vite + TS + Tailwind, `ChatInterface`, `Sidebar`, `InputBar`, `EmptyState`, API client with SSE parsing.
- Infra: `docker-compose.yml`, `.env.example`, `sql/supabase_setup.sql` (chat_sessions, chat_messages).
- Docs: `docs/phase-1-setup.md`.

**No RAG yet** — the agent answers from conversation history only (or refuses if no context).

---

## Phase 2 — Basic RAG

**Goal:** Documents in a folder are ingested (chunk + embed + store); chat uses vector search to answer from docs.

**Deliverables:**

- Backend: `document_processor.py` (load PDF/DOCX/TXT/CSV/Excel/MD, chunk, embed with `text-embedding-3-small`, store), `retriever.py` (vector search via `match_documents`), `watcher.py` (watchdog on `documents/`). Agent: retrieve → generate.
- Frontend: `DocumentsPage`, `DocumentList` (auto-refresh), nav to Chat vs Documents.
- SQL: pgvector, `files`, `documents`, `match_documents()`, IVFFlat index.
- Docs: `docs/phase-2-setup.md`, `docs/concepts/embeddings-and-indexes.md`.

---

## Phase 3 — Advanced Retrieval (Hybrid Search)

**Goal:** Hybrid search (dense + sparse), multi-query expansion, parent-child chunking.

**Deliverables:**

- Backend: `retriever.py` rewritten — multi-query expansion, `hybrid_search()` RPC, RRF merge, parent chunk lookup. `document_processor.py` — parent chunks (2000 tok) → child chunks (500 tok); children in `documents` with `parent_id`.
- SQL: `parent_chunks` table, `parent_id` and `fts` on `documents`, HNSW + GIN indexes, `hybrid_search()`.
- Docs: `docs/phase-3-setup.md`, `docs/concepts/hybrid-search.md`, `chunking-strategies.md`, `multi-query-retrieval.md`.

---

## Phase 4 — Intelligent Agent

**Goal:** 7-node agent: query analysis, expansion, retrieve, grade docs, optional rewrite, generate, hallucination check; source references in UI.

**Deliverables:**

- Backend: Agent nodes — analyze_query, expand_query, hybrid_retrieve, grade_documents, rewrite_query, retrieve_after_rewrite, generate, check_hallucination, increment_hallucination_retry. Stream emits status/sources/done; errors sent as `error` event.
- Frontend: Sources (N) collapsible under assistant messages, `SourceCard`, single-click delete, Documents at top of sidebar, title saved before `done`.
- SQL: `sources` (jsonb) on `chat_messages`.
- Docs: `docs/phase-4-setup.md`, `docs/concepts/document-grading.md`.

---

## Documentation Rules

- **Phase setup guides** (`docs/phase-X-setup.md`): prerequisites, SQL to run, env, Docker, how to verify, troubleshooting.
- **Concept docs** (`docs/concepts/*.md`): theory and design (embeddings, hybrid search, chunking, grading, etc.).
- **This guide** (`docs/guide/`): project overview, architecture, code layout, API, errors, and study curriculum.

Do not skip phases or add later-phase features before completing the current phase.
