-- Phase 2: pgvector, files, documents, match_documents
-- Run after Phase 1 (supabase_setup.sql). Use Supabase SQL Editor.

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Files table (one row per ingested file)
CREATE TABLE IF NOT EXISTS files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size BIGINT NOT NULL,
  chunk_count INT NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'error')),
  file_hash TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at DESC);

-- Documents table (chunks with embeddings)
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}',
  embedding vector(1536) NOT NULL,
  file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_file_id ON documents(file_id);

-- IVFFlat index for approximate nearest neighbor (cosine distance)
-- Use after loading initial data; tune lists for your dataset size (rule of thumb: sqrt(row_count))
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- match_documents: cosine similarity search
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  match_count int DEFAULT 5,
  filter_file_id uuid DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  file_id uuid,
  chunk_index int,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    d.id,
    d.content,
    d.metadata,
    d.file_id,
    d.chunk_index,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM documents d
  WHERE (filter_file_id IS NULL OR d.file_id = filter_file_id)
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
$$;
