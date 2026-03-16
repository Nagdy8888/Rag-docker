# Supabase and Migrations (Detailed)

The project uses **Supabase** only as **PostgreSQL** (and pgvector). Connection is via **connection string** (SQLAlchemy); no Supabase client SDK for database access. Chats and document chunks are stored in the same database.

## Supabase Setup

1. Create a project at [app.supabase.com](https://app.supabase.com).  
2. In **Settings → Database**, copy the **Connection string (URI)**.  
3. Add `?sslmode=require` if not present. URL-encode the password if it contains special characters.  
4. Set **DATABASE_URI** in `.env`.  
5. Run SQL migrations in the **SQL Editor** (New query → paste → Run). Order matters.

## Migration Files (Run in Order)

| File | Purpose |
|------|--------|
| **sql/supabase_setup.sql** | Phase 1: chat_sessions, chat_messages, indexes, trigger for updated_at. |
| **sql/supabase_phase2.sql** | Phase 2: vector extension, files, documents, match_documents(), IVFFlat index. |
| **sql/supabase_phase3.sql** | Phase 3: parent_chunks, parent_id and fts on documents, HNSW + GIN indexes, hybrid_search(). |
| **sql/supabase_phase4.sql** | Phase 4: sources column on chat_messages, optional GIN on sources. |

## Important Details

- **pgvector:** Phase 2 enables the `vector` extension. Embeddings are 1536-dimensional (OpenAI text-embedding-3-small).  
- **CASCADE:** Deleting a chat_session deletes its chat_messages. Deleting a file deletes its documents and parent_chunks.  
- **Triggers:** update_chat_session_updated_at runs after INSERT on chat_messages and sets chat_sessions.updated_at = now().  
- **Generated column:** documents.fts is GENERATED ALWAYS AS (to_tsvector('english', content)) STORED.  
- **RPC:** match_documents and hybrid_search are SQL functions; the backend calls them via raw SQL (e.g. text("SELECT ... FROM hybrid_search(...)")).

## If You Reset the Database

- Run the four SQL files in order.  
- Re-add or re-process documents (watcher will ingest files in documents/ again).  
- Chat history will be empty (new chat_sessions and chat_messages).

## Connection in Code

- **database.py** uses SQLAlchemy create_engine(DATABASE_URI, pool_pre_ping=True, ...). get_connection() yields a connection and commits on exit (or rollback on exception). All reads/writes use this context manager.
