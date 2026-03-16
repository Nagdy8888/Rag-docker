# Glossary and File Index (Detailed)

## Glossary

- **RAG** — Retrieval-Augmented Generation: augmenting an LLM with retrieved documents so it answers from context.  
- **Embedding** — A vector (list of numbers) representing text; used for similarity search (e.g. OpenAI text-embedding-3-small, 1536 dimensions).  
- **Dense search** — Vector similarity search (e.g. cosine distance on embeddings).  
- **Sparse search** — Keyword/full-text search (e.g. PostgreSQL tsvector/tsquery, GIN index).  
- **Hybrid search** — Combining dense and sparse search (e.g. RRF).  
- **RRF** — Reciprocal Rank Fusion: merge ranked lists with score 1/(k+rank) per list, then sort by sum.  
- **Parent-child chunking** — Large “parent” chunks for context; smaller “child” chunks for search; return parent content for generation.  
- **Document grading** — LLM labels each retrieved chunk as relevant or irrelevant; only relevant chunks form the context.  
- **Query rewriting** — Rephrasing the user question to improve retrieval when the first run returns too few relevant chunks.  
- **Hallucination check** — LLM verifies whether the assistant reply is grounded in the provided context.  
- **SSE** — Server-Sent Events: one-way stream of text events (event type + data).  
- **Session** — One chat (chat_sessions row) with many messages (chat_messages).  
- **Sources** — List of { filename, chunk_index, snippet } attached to an assistant message (Phase 4).

## File Index (Where to Find What)

| Topic | Location |
|-------|----------|
| App entry, layout, view state | frontend/src/App.tsx |
| Chat UI, messages, streaming, sources | frontend/src/components/ChatInterface.tsx |
| Sidebar, Documents, New Chat, delete | frontend/src/components/Sidebar.tsx |
| API client, streamChat, listChats, etc. | frontend/src/api/client.ts |
| Types (ChatMessage, SourceRef, etc.) | frontend/src/types/index.ts |
| FastAPI app, routes, SSE stream | backend/app/main.py |
| DB connection, sessions, messages, files | backend/app/database.py |
| Pydantic request/response models | backend/app/schemas.py |
| Env settings | backend/app/config.py |
| Document load, chunk, embed, store | backend/app/document_processor.py |
| Hybrid search, RRF, multi-query | backend/app/retriever.py |
| Folder watcher | backend/app/watcher.py |
| Agent state schema | backend/app/agent/state.py |
| System and node prompts | backend/app/agent/prompts.py |
| LLM instance | backend/app/agent/llm.py |
| All agent nodes | backend/app/agent/nodes.py |
| Graph definition (batch) | backend/app/agent/graph.py |
| Streaming flow (step-by-step) | backend/app/agent/stream.py |
| Title generation | backend/app/agent/title.py |
| Phase 1–4 SQL | sql/supabase_setup.sql, sql/supabase_phase2.sql, sql/supabase_phase3.sql, sql/supabase_phase4.sql |
| Phase setup guides | docs/phase-1-setup.md … docs/phase-4-setup.md |
| Concept deep-dives | docs/concepts/embeddings-and-indexes.md, hybrid-search.md, chunking-strategies.md, multi-query-retrieval.md, document-grading.md |
| This guide (overview + curriculum) | docs/guide/00-*.md … 20-*.md |

## Reading Order for Studying the Repo

1. **00–04** — Overview, architecture, stack, quick start, common issues.  
2. **05** — Phased plan.  
3. **06–07** — Backend and frontend structure.  
4. **08–09** — Database and Docker.  
5. **10–11** — Agent and nodes.  
6. **12–13** — Retrieval and document processing.  
7. **14–15** — API and streaming.  
8. **16** — Errors and solutions.  
9. **17–19** — Frontend state, Supabase, verification.  
10. **20** — Glossary and file index.  
11. **docs/concepts/** — When you want theory (embeddings, hybrid search, chunking, grading).  
12. **docs/phase-X-setup.md** — When you need step-by-step setup for a phase.
