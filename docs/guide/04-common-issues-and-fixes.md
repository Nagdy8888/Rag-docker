# Common Issues and Fixes (Short)

| Issue | Fix |
|-------|-----|
| **Network error** when asking a question | Backend may have thrown; check logs. Stream now sends `error` event; frontend shows message. Increase Vite proxy timeout if in dev (`vite.config.ts`). |
| **New chat title not updating** | Title is saved when `sources` event is sent (before `done`). Ensure Phase 4 stream and DB are in use. |
| **Delete chat does nothing** | Delete is one-click now; if it fails, check network/backend and toast error. |
| **Documents button missing** | It’s at the top of the sidebar (Documents, then New Chat). Ensure `onNavigateToDocuments` is passed in `App.tsx`. |
| **"grade_documents_node() missing 1 required argument: 'llm'"** | In `stream.py`, call `grade_documents_node(state, llm)` (both arguments). |
| **Chunks/sources column missing** | Run `sql/supabase_phase4.sql` in Supabase. |
| **Chat list empty or slow** | First load after Docker start can be slow (cold start). Auto-select first chat is enabled. |
| **First chunk mentioned in answer** | RAG prompt tells model not to cite chunk numbers; ensure latest `prompts.py` is deployed. |

Detailed errors and solutions: see `16-errors-and-solutions.md`.
