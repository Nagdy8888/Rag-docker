# Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Framer Motion, Lucide, react-markdown, react-hot-toast |
| **Backend** | Python 3.11, FastAPI, Uvicorn, LangChain/LangGraph, OpenAI (chat + embeddings), SQLAlchemy |
| **Database** | Supabase (PostgreSQL + pgvector); SQL migrations in `sql/` |
| **DevOps** | Docker, Docker Compose; nginx for frontend in prod |
| **Optional** | LangSmith for tracing |

Backend talks to DB via `DATABASE_URI`; no Supabase client SDK for DB (direct Postgres). Documents are stored under `documents/` (Docker volume).
