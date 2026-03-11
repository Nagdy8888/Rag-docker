# Phase 1 Setup Guide — Simple Chatbot

This guide walks you through getting the Phase 1 chatbot running: Supabase for chat storage, OpenAI for the LLM, optional LangSmith for tracing, Docker for running the app, and the React web UI.

---

## Prerequisites

- **Docker** and **Docker Compose** installed.
- **Supabase** account: [supabase.com](https://supabase.com).
- **OpenAI** API key: [platform.openai.com](https://platform.openai.com/api-keys).
- (Optional) **LangSmith** account for tracing: [smith.langchain.com](https://smith.langchain.com).

---

## Step 1: Create a Supabase project

1. Go to [app.supabase.com](https://app.supabase.com) and sign in.
2. Click **New project**.
3. Choose your organization, set a **Project name** and **Database password** (save the password).
4. Pick a region and click **Create new project**. Wait until the project is ready.

---

## Step 2: Get your database connection URI

1. In the project dashboard, open **Settings** (gear icon) → **Database**.
2. Under **Connection string**, choose **URI**.
3. Copy the connection string. It looks like:
   ```text
   postgresql://postgres.PROJECT_REF:YOUR_PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres
   ```
4. Add `?sslmode=require` at the end if it’s not already there (required for Supabase).
5. If your password contains special characters (e.g. `@`, `#`), they must be URL-encoded (e.g. `@` → `%40`). Some clients give you an already-encoded URI.
6. This value is your `DATABASE_URI` for the backend.

---

## Step 3: Run the SQL migration (chat tables)

1. In Supabase, open **SQL Editor**.
2. Click **New query**.
3. Open the file `sql/supabase_setup.sql` from this project and copy its full contents into the editor.
4. Click **Run** (or press Ctrl+Enter).  
   You should see “Success. No rows returned.”  
   This creates:
   - `chat_sessions` (id, title, created_at, updated_at)
   - `chat_messages` (id, session_id, role, content, created_at)
   - Indexes and a trigger that updates `chat_sessions.updated_at` when a message is inserted.

---

## Step 4: Get your OpenAI API key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys).
2. Create an API key and copy it. This is `OPENAI_API_KEY`.

---

## Step 5: (Optional) Get LangSmith API key

1. Sign up at [smith.langchain.com](https://smith.langchain.com).
2. Create a project (e.g. `rag-agent`).
3. Open **Settings** → **API Keys**, create a key and copy it. This is `LANGCHAIN_API_KEY`.

---

## Step 6: Configure environment variables

1. In the project root (same folder as `docker-compose.yml`), copy the example env file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and set:
   - `OPENAI_API_KEY` — your OpenAI key (required).
   - `DATABASE_URI` — your Supabase Postgres connection URI (required). From Supabase: **Settings → Database → Connection string → URI**, then add `?sslmode=require` if missing. Use the pooled URI (e.g. `postgresql://postgres.xxx:password@...pooler.supabase.com:5432/postgres?sslmode=require`).
   - For LangSmith (optional): set `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, and `LANGCHAIN_PROJECT`.

---

## Step 7: Create the documents folder (for Docker)

From the project root:

```bash
mkdir -p documents
```

The backend container mounts `./documents`; the folder can stay empty for Phase 1.

---

## Step 8: Build and run with Docker

From the project root:

```bash
docker compose up --build
```

- First run will build the backend (Python) and frontend (Node → Nginx) images, then start both services.
- Backend: [http://localhost:8000](http://localhost:8000).
- Frontend: [http://localhost:3000](http://localhost:3000). Use this in the browser; it proxies `/api` to the backend.

---

## Step 9: Verify the phase works

1. Open [http://localhost:3000](http://localhost:3000) in your browser.
2. Click **New Chat** in the sidebar. A new session should appear.
3. Type a message (e.g. “Hello, what can you do?”) and press Enter or click Send.
4. You should see:
   - A “Thinking...” (or status) indicator, then the reply streaming in token-by-token.
   - The sidebar title updating to an auto-generated title after the first exchange.
5. Refresh the page: the same chat and messages should still be there (loaded from Supabase).
6. (Optional) If LangSmith is configured, open your LangSmith project and confirm that runs/traces appear for the chat request.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| **Frontend shows “Request failed” or CORS** | Ensure you use the app via [http://localhost:3000](http://localhost:3000) so `/api` is proxied to the backend. Do not call the backend on port 8000 from the browser if the frontend is on another origin without CORS configured. |
| **Backend: “Invalid API key” or 401** | Check `OPENAI_API_KEY` in `.env` and that the key is valid and has credits. |
| **Backend: Supabase connection / 500** | Verify `DATABASE_URI` in `.env`. Use the URI from **Settings → Database → Connection string (URI)**. Ensure `?sslmode=require` is at the end. Ensure the SQL from `sql/supabase_setup.sql` was run successfully. |
| **No messages or sessions** | In Supabase **Table Editor**, confirm `chat_sessions` and `chat_messages` exist and that inserts appear when you send messages. |
| **Streaming stops mid-reply** | Check backend logs (`docker compose logs backend`) for errors. Ensure no proxy or firewall is closing long-lived SSE connections. |
| **Trigger error when running SQL** | In Postgres 11+, use `EXECUTE FUNCTION` in the trigger (as in `sql/supabase_setup.sql`). If your Supabase Postgres is older, replace with `EXECUTE PROCEDURE`. |

---

## Next step

After Phase 1 works, you can move on to **Phase 2** (folder watcher, document ingestion, and basic RAG retrieval). See `docs/phase-2-setup.md` when it’s available.
