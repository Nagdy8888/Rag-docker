-- Phase 3: Hybrid search, parent-child chunking, HNSW + GIN indexes
-- Run after Phase 2 (supabase_phase2.sql). Use Supabase SQL Editor.

-- Allow more memory for index builds (HNSW/GIN need > default maintenance_work_mem)
SET maintenance_work_mem = '128MB';

-- Ensure files has file_hash (if Phase 2 was run without it)
ALTER TABLE files ADD COLUMN IF NOT EXISTS file_hash TEXT;

-- ========== Parent chunks table (larger context for generation) ==========
CREATE TABLE IF NOT EXISTS parent_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}',
  file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_parent_chunks_file_id ON parent_chunks(file_id);

-- ========== Extend documents for hybrid search and parent-child ==========
-- parent_id: NULL = Phase 2 flat chunk; set = Phase 3 child of a parent_chunk
ALTER TABLE documents ADD COLUMN IF NOT EXISTS parent_id UUID REFERENCES parent_chunks(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_documents_parent_id ON documents(parent_id);

-- Full-text search vector (English) for sparse search
ALTER TABLE documents ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
CREATE INDEX IF NOT EXISTS idx_documents_fts ON documents USING GIN(fts);

-- GIN index on metadata for filtering
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN(metadata);

-- ========== Replace IVFFlat with HNSW (better recall/speed for hybrid) ==========
DROP INDEX IF EXISTS idx_documents_embedding;
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- ========== Hybrid search: dense + sparse, RRF, return parent content ==========
CREATE OR REPLACE FUNCTION hybrid_search(
  query_embedding vector(1536),
  query_text text,
  match_count int DEFAULT 5,
  filter_file_id uuid DEFAULT NULL,
  rrf_k float DEFAULT 60.0
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  file_id uuid,
  chunk_index int
)
LANGUAGE sql STABLE
AS $$
  WITH
  dense AS (
    SELECT d.id, d.parent_id, ROW_NUMBER() OVER (ORDER BY d.embedding <=> query_embedding) AS rn
    FROM documents d
    WHERE (filter_file_id IS NULL OR d.file_id = filter_file_id)
    LIMIT 200
  ),
  sparse AS (
    SELECT d.id, d.parent_id, ROW_NUMBER() OVER (ORDER BY ts_rank(d.fts, plainto_tsquery('english', trim(query_text))) DESC) AS rn
    FROM documents d
    WHERE (query_text IS NOT NULL AND trim(query_text) <> '')
      AND d.fts @@ plainto_tsquery('english', trim(query_text))
      AND (filter_file_id IS NULL OR d.file_id = filter_file_id)
    LIMIT 200
  ),
  rrf AS (
    SELECT COALESCE(d.parent_id, d.id) AS pid, (1.0 / (rrf_k + d.rn)) AS score
    FROM dense d
    UNION ALL
    SELECT COALESCE(s.parent_id, s.id), (1.0 / (rrf_k + s.rn))
    FROM sparse s
  ),
  parent_scores AS (
    SELECT pid, SUM(score) AS total
    FROM rrf
    GROUP BY pid
    ORDER BY total DESC
    LIMIT match_count
  )
  SELECT
    ps.pid AS id,
    COALESCE(p.content, d.content) AS content,
    COALESCE(p.metadata, d.metadata) AS metadata,
    COALESCE(p.file_id, d.file_id) AS file_id,
    COALESCE(p.chunk_index, d.chunk_index) AS chunk_index
  FROM parent_scores ps
  LEFT JOIN parent_chunks p ON p.id = ps.pid
  LEFT JOIN documents d ON d.id = ps.pid;
$$;

-- Optional: set ef_search for HNSW at query time (run before heavy searches if needed)
-- SET hnsw.ef_search = 40;
