-- Add error_message to files (run if you already have Phase 2 tables)
-- Use Supabase SQL Editor.

ALTER TABLE files ADD COLUMN IF NOT EXISTS error_message TEXT;
