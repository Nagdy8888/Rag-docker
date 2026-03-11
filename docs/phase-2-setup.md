# Phase 2 Setup Guide — Basic RAG (Folder Watcher + Vector Retrieval)

This guide adds document ingestion and RAG to the Phase 1 chatbot: the backend watches the `documents/` folder, processes files (chunk + embed + store in pgvector), and the agent retrieves relevant chunks before answering.

---

## Prerequisites

- **Phase 1** must be complete: chat tables in Supabase, backend and frontend running via Docker, `.env` with `OPENAI_API_KEY` and `DATABASE_URI`.
- The same Supabase project and OpenAI key are used.

---

## Step 1: Run the Phase 2 SQL migration

1. In Supabase, open **SQL Editor** → **New query**.
2. Open the file **`supabase_phase2.sql`** from this project and copy its full contents into the editor.
3. Click **Run** (or Ctrl+Enter). You should see “Success. No rows returned.”

This migration:

- Enables the **pgvector** extension.
- Creates the **`files`** table (id, filename, file_type, file_size, chunk_count, status, file_hash, created_at).
- Creates the **`documents`** table (id, content, metadata, embedding vector(1536), file_id, chunk_index, created_at).
- Creates an **IVFFlat** index on `documents.embedding` for approximate nearest-neighbor search.
- Defines the **`match_documents(query_embedding, match_count, filter_file_id)`** function for cosine similarity search.

---

## Step 2: Environment variables

No new required variables. Optional:

- **`DOCUMENTS_PATH`** — Path to the folder to watch (default: `documents`). Inside Docker this is `/app/documents`; the compose file mounts `./documents` to that path.

Ensure `.env` still has:

- `OPENAI_API_KEY` (used for embeddings as well as chat).
- `DATABASE_URI` (same Supabase Postgres URI as Phase 1).

---

## Step 3: Rebuild and run

From the project root:

```bash
docker compose up --build
```

The backend will:

- Start the **documents folder watcher** on startup (watchdog on `documents/`).
- Process any new or modified files in that folder (PDF, DOCX, TXT, CSV, Excel, Markdown).

---

## Step 4: Add documents

1. Create or use the **`documents`** folder in the project root (same as Phase 1).
2. Copy or drop files into **`documents/`**. Supported types:
   - **PDF** (`.pdf`) — text extracted via pypdf
   - **Word** (`.docx`)
   - **Text** (`.txt`, `.md`, `.csv`)
   - **Excel** (`.xlsx`, `.xls`)
3. Max file size: **10 MB** per file.
4. The watcher detects new or changed files and runs the pipeline: **load → chunk (RecursiveCharacterTextSplitter, ~1000 tokens, 200 overlap) → embed (OpenAI text-embedding-3-small) → store** in `documents` and update `files`.

No upload UI: you add files by placing them in the folder (e.g. via file manager or volume mount).

---

## Step 5: Verify in the UI

1. Open [http://localhost:3000](http://localhost:3000).
2. In the sidebar, click **Documents**. You should see:
   - The watched folder path (`documents/`).
   - A **grid of document cards** (after at least one file has been processed): filename, type icon, size, date, chunk count, and status (**Processing** / **Ready** / **Error**).
3. The list **auto-refreshes every 5 seconds**. New files appear as they move from “Processing” to “Ready”.

---

## Step 6: Test RAG in chat

1. Switch back to **Chat** in the sidebar (or click a chat / New Chat).
2. Ask a question that should be answered from your ingested documents (e.g. “What is document X about?” or a specific fact you know is in a file).
3. You should see:
   - A short “Retrieving...” status, then the reply streaming in.
   - Answers that use the content of your documents when relevant.

If the context does not contain relevant information, the model is instructed to say so.

---

## How it works (brief)

- **Watcher** (`watcher.py`): Uses `watchdog` to monitor `documents/`. On create/modify it runs the document pipeline; on delete it removes that file’s chunks from the DB.
- **Document processor** (`document_processor.py`): Loads text from the file, splits with `RecursiveCharacterTextSplitter` (token-aware via tiktoken), embeds with **text-embedding-3-small**, and inserts into `documents` and `files`.
- **Retriever** (`retriever.py`): Embeds the user query and calls the Postgres function **`match_documents`** (cosine similarity) to get top-k chunks.
- **Agent** (`agent.py`): Graph is **retrieve → generate**. The retrieve node gets the last user message, runs the retriever, and puts the concatenated chunks into state as context. The generate node gets the same messages plus a system message containing that context and streams the reply.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| **Documents page empty or “Could not load documents”** | Ensure the Phase 2 SQL migration was run (pgvector, `files`, `documents`, `match_documents`). Check backend logs: `docker compose logs backend`. If `files` doesn’t exist, run `supabase_phase2.sql`. |
| **Documents show status “Error” and 0 chunks** | The app now shows an **error message** under each failed file (e.g. “No text could be extracted”, “Embedding failed: …”). If you don’t see it: run **`supabase_phase2_add_error_message.sql`** in Supabase (adds `error_message` column), then restart the backend. Common causes: **No text extracted** — PDF is image-only or unsupported; try a plain TXT file. **Embedding failed** — check `OPENAI_API_KEY` in `.env` and that the key is valid. **Failed to save chunks** — check backend logs; often a DB/vector format issue. |
| **Documents not showing in app or Supabase** | 1) Open the app → **Documents**. If the list is empty, you’ll see a **diagnostic** (Phase 2 tables missing / no files on disk / files not processed). 2) Or call **GET** [http://localhost:3000/api/documents/status](http://localhost:3000/api/documents/status) (or port 8000 if talking to the backend directly). It returns: `documents_folder`, `files_on_disk`, `phase2_tables_ok`, `db_error`. 3) **If `phase2_tables_ok` is false:** run `supabase_phase2.sql` in Supabase SQL Editor, then `docker compose restart backend`. 4) **If `files_count` is 0:** put supported files (PDF, DOCX, TXT, CSV, etc.) in the project’s `documents/` folder and restart the backend. 5) **If files are on disk but still no rows:** run `docker compose logs backend` and look for “Processed existing file” or errors (e.g. OpenAI key, missing table). |
| **Files stay “Processing” or go “Error”** | Check backend logs for exceptions (e.g. missing pypdf/python-docx/openpyxl, OpenAI errors). Ensure `OPENAI_API_KEY` is set; embeddings use the same key. Check file type and size (max 10 MB). |
| **IVFFlat index creation fails** | Some pgvector versions require at least one row before creating IVFFlat. Add a small `.txt` file, let it process, then run the index creation part of the migration again if needed. |
| **Chat doesn’t use my documents** | Ask a question that clearly relates to the content you added. If retrieval returns no or weak matches, the model may say it doesn’t have relevant information. |
| **Watcher not picking up files** | Ensure the `documents/` folder exists and is mounted (e.g. `./documents:/app/documents` in docker-compose). Restart the backend after adding the migration. |

---

## Next step

After Phase 2 works, you can move on to **Phase 3** (hybrid search, parent-child chunking, multi-query expansion). See `docs/phase-3-setup.md` when available.
