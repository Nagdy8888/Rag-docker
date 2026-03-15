-- Phase 4: Source references for chat messages (used by intelligent agent)
-- Run after Phase 1 (supabase_setup.sql). Use Supabase SQL Editor.

-- Store which document chunks were used for each assistant message (filename, page/section, snippet)
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT '[]';

-- Optional: index for filtering messages that have sources (e.g. analytics)
CREATE INDEX IF NOT EXISTS idx_chat_messages_sources ON chat_messages USING GIN(sources) WHERE sources IS NOT NULL AND jsonb_array_length(sources) > 0;
