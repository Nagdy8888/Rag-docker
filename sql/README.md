# sql

SQL migrations and Supabase setup for the RAG app.

## Files

- **supabase_setup.sql** — Initial Supabase/Postgres setup (extensions, base schema).
- **supabase_phase2.sql** — Phase 2: documents, chunks, embeddings, full-text.
- **supabase_phase2_add_error_message.sql** — Error message column (e.g. for chat messages).
- **supabase_phase3.sql** — Phase 3: parent_chunks, parent_id, hybrid search helpers.
- **supabase_phase4.sql** — Phase 4: sources, feedback, or other schema for the intelligent agent.

Run in order when setting up a new Supabase project. See [../docs/guide/18-supabase-and-migrations.md](../docs/guide/18-supabase-and-migrations.md) for details.
