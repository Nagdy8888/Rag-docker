# Database Schema (Detailed)

The project uses **Supabase (PostgreSQL)**. All schema changes are applied via SQL files in `sql/`. Run them in order: Phase 1 → 2 → 3 → 4.

## Phase 1: Chat Only

**File:** `sql/supabase_setup.sql`

- **chat_sessions**  
  - `id` UUID PK, `title` TEXT, `created_at` TIMESTAMPTZ, `updated_at` TIMESTAMPTZ.  
  - Index on `updated_at DESC` for listing.

- **chat_messages**  
  - `id` UUID PK, `session_id` UUID FK → chat_sessions(id) ON DELETE CASCADE, `role` TEXT CHECK (user | assistant), `content` TEXT, `created_at` TIMESTAMPTZ.  
  - Index on `session_id`.  
  - Trigger: on INSERT into chat_messages, update `chat_sessions.updated_at`.

## Phase 2: Documents and Vector Search

**File:** `sql/supabase_phase2.sql`

- **files**  
  - `id` UUID PK, `filename` TEXT, `file_type` TEXT, `file_size` BIGINT, `chunk_count` INT, `status` TEXT, `error_message` TEXT (optional), `created_at` TIMESTAMPTZ.  
  - Tracks each ingested file.

- **documents**  
  - `id` UUID PK, `content` TEXT, `metadata` JSONB, `embedding` vector(1536), `file_id` UUID FK → files(id), `chunk_index` INT, `created_at` TIMESTAMPTZ.  
  - IVFFlat index on `embedding` (Phase 3 replaces with HNSW).  
  - RPC **match_documents(query_embedding, match_count, filter_file_id)** for cosine similarity search.

## Phase 3: Hybrid Search and Parent Chunks

**File:** `sql/supabase_phase3.sql`

- **parent_chunks**  
  - `id` UUID PK, `content` TEXT, `metadata` JSONB, `file_id` UUID FK → files(id), `chunk_index` INT, `created_at` TIMESTAMPTZ.  
  - No embedding; used as the “parent” for child chunks.

- **documents** (additions)  
  - `parent_id` UUID FK → parent_chunks(id) ON DELETE CASCADE. NULL = legacy flat chunk.  
  - `fts` tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED.  
  - GIN index on `fts`, GIN on `metadata`.  
  - IVFFlat replaced by **HNSW** on `embedding` (vector_cosine_ops).

- **hybrid_search(query_embedding, query_text, match_count, filter_file_id, rrf_k)**  
  - CTEs: dense (vector order), sparse (fts rank), RRF by COALESCE(parent_id, id), parent_scores, then JOIN to parent_chunks/documents to return parent (or document) content.  
  - Returns: id, content, metadata, file_id, chunk_index.

## Phase 4: Source References

**File:** `sql/supabase_phase4.sql`

- **chat_messages** (addition)  
  - `sources` JSONB DEFAULT '[]'.  
  - Stores list of `{ filename, chunk_index, snippet }` for assistant messages.  
  - Optional GIN index on `sources` for analytics.

## Relationships Summary

- chat_sessions 1 — N chat_messages (CASCADE delete).
- files 1 — N parent_chunks (CASCADE).
- files 1 — N documents (CASCADE); documents optionally N — 1 parent_chunks via parent_id.
- Chats and document storage are independent (no FK between chat and files/documents).
