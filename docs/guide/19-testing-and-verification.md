# Testing and Verification (Detailed)

How to verify that each part of the system works. No automated test suite is described here; this is a manual verification curriculum.

## After Phase 1

1. **Docker:** `docker compose up --build`. Open http://localhost:3000.  
2. **Chat:** Create a new chat; send a message. You should see a reply (from conversation only; no docs).  
3. **Sidebar:** Session appears with an auto-generated title after the first reply.  
4. **Persistence:** Refresh the page; sessions and messages should still be there.  
5. **API:** Open http://localhost:8000/docs; try GET /api/chats and GET /api/chats/{id}.  
6. **Optional:** If LangSmith is configured, check for a trace for the chat request.

## After Phase 2

1. **Documents:** Ensure sql/supabase_phase2.sql has been run.  
2. **Folder:** Add a PDF or TXT to the `documents/` folder (or use upload if implemented).  
3. **Documents page:** Open Documents; the file should appear with status "Ready" and a chunk count.  
4. **Chat:** Ask a question that can be answered from the file content. The reply should use the document and may say "I can't respond..." if the answer isn’t in the context.  
5. **API:** GET /api/documents and GET /api/documents/test-retrieval?q=... to confirm retrieval.

## After Phase 3

1. **SQL:** Run sql/supabase_phase3.sql.  
2. **Re-process:** Remove and re-add a document (or touch it) so it gets parent-child chunking.  
3. **Chat:** Ask a question; retrieval now uses hybrid search (dense + sparse, RRF, parent chunks).  
4. **Quality:** Compare answers for keyword-heavy vs semantic questions; both should be supported.

## After Phase 4

1. **SQL:** Run sql/supabase_phase4.sql.  
2. **Chat:** Ask a factual question; you should see status steps (Analyzing question..., Searching documents..., Grading relevance..., Generating answer..., Verifying answer...).  
3. **Sources:** Below the reply, a "Sources (N)" section should appear; expand to see filename, chunk index, snippet.  
4. **Conversational:** Send "Hi"; the agent should skip retrieval and reply briefly (no Sources).  
5. **Title:** Create a new chat, send one message; the sidebar title should update from "New Chat" to a short phrase.  
6. **Delete:** Delete a chat with one click on the trash icon; it should disappear and a toast confirm.  
7. **Error handling:** If the backend throws (e.g. wrong env), the UI should show the error message instead of "Network error".  
8. **Documents button:** At the top of the sidebar, Documents then New Chat should always be visible.

## Common Checks

- **Backend logs:** `docker compose logs backend` to see Python exceptions and watcher activity.  
- **DB:** In Supabase Table Editor, inspect chat_sessions, chat_messages (including sources), files, documents, parent_chunks.  
- **Network:** Browser DevTools → Network; filter by "chat" or "chats" to see request/response and SSE events.
