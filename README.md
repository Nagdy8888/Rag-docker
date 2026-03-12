# RAG Chat — LangGraph + Supabase + Docker

A **RAG (Retrieval-Augmented Generation)** chatbot built in phases: chat with Supabase storage, document ingestion with vector search, and hybrid retrieval (dense + sparse, multi-query, parent-child chunking). The backend uses **FastAPI**, **LangGraph**, and **PostgreSQL (Supabase)** with pgvector; the frontend is **React** (Vite, TypeScript, Tailwind).

---

## Features

- **Chat** — Multiple sessions, streaming responses, auto-generated titles
- **Documents** — Upload PDF, DOCX, TXT, CSV, Excel, Markdown (up to 50 MB); files are chunked, embedded (OpenAI), and stored in Supabase
- **RAG** — Answers from your documents only; hybrid search (vector + full-text), multi-query expansion, parent-child chunking for better context
- **Docker** — Single `docker compose up` to run backend + frontend; `documents/` folder is mounted for storage and watcher

---

## Prerequisites

- **Docker** and **Docker Compose**
- **Supabase** project ([supabase.com](https://supabase.com)) — for Postgres + pgvector
- **OpenAI** API key — for chat and embeddings
- (Optional) **LangSmith** — for tracing

---

## Quick start

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd "Rag docker"
```

Copy `.env.example` to `.env` (or create `.env`) and set:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Required. Used for chat and embeddings. |
| `DATABASE_URI` | Required. Supabase Postgres connection URI (with `?sslmode=require`). |
| `LANGCHAIN_TRACING_V2` | Optional. Set to `true` for LangSmith. |
| `LANGCHAIN_API_KEY` | Optional. LangSmith API key. |
| `LANGCHAIN_PROJECT` | Optional. LangSmith project name (e.g. `rag-agent`). |
| `DOCUMENTS_PATH` | Optional. Folder for documents (default: `documents`). |

### 2. Database migrations

In the **Supabase SQL Editor**, run in order:

1. **Phase 1 (chat):** `sql/supabase_setup.sql` — creates `chat_sessions`, `chat_messages`
2. **Phase 2 (RAG):** `sql/supabase_phase2.sql` — pgvector, `files`, `documents`, `match_documents`
3. **Phase 3 (hybrid):** `sql/supabase_phase3.sql` — `parent_chunks`, `hybrid_search`, HNSW/GIN indexes

Optional: `sql/supabase_phase2_add_error_message.sql` if you need the `error_message` column on `files`.

### 3. Run

```bash
docker compose up --build
```

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (when using port 8000 directly)

Create a chat, upload documents from the **Documents** page, then ask questions — the agent answers using only the ingested docs.

---

## Project structure

```
├── backend/                 # FastAPI + LangGraph
│   ├── app/
│   │   ├── agent/           # LangGraph: state, prompts, nodes, graph, stream, title
│   │   ├── config.py
│   │   ├── database.py      # Sessions, messages, files
│   │   ├── document_processor.py  # Chunk, embed, store (parent-child)
│   │   ├── main.py          # REST + SSE, upload endpoint
│   │   ├── retriever.py     # Hybrid search, multi-query
│   │   └── watcher.py       # Watch documents/ folder
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/      # ChatInterface, Sidebar, DocumentsPage, DocumentList, …
│   │   ├── api/
│   │   └── types/
│   ├── Dockerfile
│   └── nginx.conf           # Proxies /api to backend, client_max_body_size 50M
├── documents/               # Mounted into backend; uploads + watched files
├── docs/                    # Setup guides and concept deep-dives
│   ├── phase-1-setup.md
│   ├── phase-2-setup.md
│   ├── phase-3-setup.md
│   └── concepts/            # hybrid-search, chunking-strategies, multi-query-retrieval, …
├── sql/                     # Supabase migrations (run in order)
│   ├── supabase_setup.sql           # Phase 1
│   ├── supabase_phase2.sql          # Phase 2
│   ├── supabase_phase2_add_error_message.sql
│   └── supabase_phase3.sql          # Phase 3
├── docker-compose.yml
├── .env.example
└── README.md                # This file
```

---

## Storing large documents (Git LFS)

If you plan to keep many large PDFs (or other binaries) in the repo long-term — for example in `documents/` or a dedicated folder — use **Git LFS** so the repo stays small and clones stay fast.

1. **Install Git LFS:** [git-lfs.com](https://git-lfs.com) — then run once on your machine:
   ```bash
   git lfs install
   ```

2. **This repo is already configured:** `.gitattributes` tracks `*.pdf`, `*.docx`, `*.xlsx`, and `*.xls` with LFS. New adds of these types will use LFS automatically.

3. **If you already committed large PDFs before LFS:** migrate them into LFS and rewrite history (do this only if the repo is shared and others are aware):
   ```bash
   git lfs migrate import --include="*.pdf" --everything
   ```
   Then force-push: `git push --force` (coordinate with anyone else who has cloned the repo).

After that, any `git add` of matching files will store them in LFS; on clone/pull, Git LFS will download the real files.

---

## Documentation

- **Setup (step-by-step):**
  - [Phase 1 — Simple Chatbot](docs/phase-1-setup.md)
  - [Phase 2 — Basic RAG](docs/phase-2-setup.md)
  - [Phase 3 — Hybrid Search](docs/phase-3-setup.md)
- **Concepts (deep-dives):**
  - [Embeddings and vector indexes](docs/concepts/embeddings-and-indexes.md)
  - [Hybrid search](docs/concepts/hybrid-search.md)
  - [Chunking strategies](docs/concepts/chunking-strategies.md)
  - [Multi-query retrieval](docs/concepts/multi-query-retrieval.md)

---

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chats` | List chat sessions |
| GET | `/api/chats/{id}` | Get session with messages |
| POST | `/api/chats` | Create session |
| DELETE | `/api/chats/{id}` | Delete session |
| POST | `/api/chat` | Send message (SSE stream) |
| GET | `/api/documents` | List processed documents |
| GET | `/api/documents/status` | Diagnostics (folder, DB) |
| POST | `/api/documents/upload` | Upload files (multipart) |

---

## Troubleshooting

- **502 on first load** — Backend may still be starting; wait a few seconds and refresh.
- **Documents not showing** — Ensure Phase 2 and (for new ingestion) Phase 3 SQL are run; check `GET /api/documents/status`.
- **Upload fails for large files** — Nginx and backend allow 50 MB; see `frontend/nginx.conf` and `MAX_FILE_BYTES` in `document_processor.py`.
- **“Phase 2 tables missing”** — Run `sql/supabase_phase2.sql` in Supabase SQL Editor, then restart backend.

For more, see the phase setup guides and troubleshooting sections in `docs/`.
