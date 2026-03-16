# Errors and Solutions (Detailed)

This document lists errors encountered during development and their fixes. Use it when debugging or when studying the repo.

---

## 1. Network error when asking a question (Phase 4)

**Symptom:** Frontend shows "Network error" and no reply.

**Cause:** Phase 4 runs many LLM steps (analyze, expand, retrieve, grade, generate, hallucination check). Any uncaught exception in the stream (e.g. OpenAI timeout, missing argument) closed the connection without a proper error payload.

**Fix:**  
- In **main.py** event_generator: wrap the `async for stream_chat_response` in try/except; on exception log and yield `{"type": "error", "content": str(e)}` then `{"type": "done", "content": ""}`.  
- In **frontend** api/client.ts: handle `type === "error"` and call `onError(new Error(data.content))`.  
- Optionally increase Vite proxy timeout for /api (e.g. 300000 ms) so long requests in dev don’t get cut off.

---

## 2. grade_documents_node() missing 1 required positional argument: 'llm'

**Symptom:** Backend error when the agent reaches the grading step.

**Cause:** In **stream.py** the node was called as `grade_documents_node(state)` but the function signature is `grade_documents_node(state, llm)`.

**Fix:** In stream.py call `grade_documents_node(state, llm)` in both places (first retrieval path and after rewrite loop).

---

## 3. New chat title not updating in sidebar

**Symptom:** After the first message in a new chat, the sidebar still shows "New Chat".

**Cause:** Title was updated in the `finally` block of the event_generator, which runs **after** the last event ("done") was sent. The frontend received "done", refetched sessions, but the backend hadn’t run finally yet, so the title was still old.

**Fix:** When processing the **sources** event (before yielding "done"), save the assistant message and call generate_title + update_session_title, then yield the events. Use a `message_saved` flag so finally only saves when we never got to sources (e.g. error path).

---

## 4. Delete chat: clicking many times does nothing

**Symptom:** User had to click the trash icon many times; delete seemed not to work.

**Cause:** The UI required a **double-click** to confirm (first click “armed” delete, second click within 2 seconds performed it). Many users clicked once or clicked the row instead of the icon, so the second click never registered on the same item.

**Fix:** Change to **single-click delete**: one click on trash calls deleteChat(id), then onSessionsChange() and if activeId === id then onNewChat(). Show a toast on success or error. Disable the button while the request is in flight to avoid double submit.

---

## 5. Documents button disappeared / hard to find

**Symptom:** Documents entry was at the bottom of the sidebar and scrolled away with many chats.

**Fix:** Move **Documents** to a fixed top section of the sidebar, then **New Chat**, then the scrollable chat list. Use a sticky block (shrink-0) with a border below it.

---

## 6. Answer mentions "the first chunk" or chunk numbers

**Symptom:** Model said things like "According to the first chunk..." or "Chunk 1 states...".

**Cause:** No instruction in the RAG system prompt to avoid citing internal structure.

**Fix:** In **prompts.py** (RAG_SYSTEM_WITH_CONTEXT) add a line: do not mention chunk numbers, excerpt numbers, or phrases like "the first chunk"; answer naturally as if citing the document (e.g. "According to the document...").

---

## 7. SourceCard / TypeScript: 'index' is declared but its value is never read

**Symptom:** Frontend build failed (TS6133).

**Cause:** SourceCard accepted an `index` prop but didn’t use it.

**Fix:** Remove `index` from the SourceCard props and from the call site in ChatInterface.

---

## 8. Chats or documents slow to load after Docker start

**Symptom:** First load of the page or documents feels slow.

**Cause:** Cold start: backend and DB connection pool need to warm up; first request pays the cost.

**Fix:** This is expected. Optional: show a “Connecting…” or skeleton until first response. No code change required; documented in guide.

---

## 9. Column "sources" does not exist (chat_messages)

**Symptom:** Backend or DB error when saving or loading messages with sources.

**Cause:** Phase 4 migration not run.

**Fix:** Run **sql/supabase_phase4.sql** in the Supabase SQL Editor (adds `sources` JSONB to chat_messages).

---

## 10. React hooks: useState after early return

**Symptom:** In ChatInterface, `sourcesOpen` state could cause inconsistent hook order when sessionId was null.

**Cause:** `useState` for sourcesOpen was declared after the early return `if (!sessionId) return ...`, violating the rules of hooks.

**Fix:** Move all hooks (including `const [sourcesOpen, setSourcesOpen] = useState(...)`) to the top of the component, before any return.

---

## 11. Auto-select first chat on load

**Symptom:** After sessions loaded, no chat was selected and the main area showed "Select a chat or create a new one" even when sessions existed.

**Fix:** In App.tsx, in the effect that depends on sessions and activeId: if sessions.length > 0 and activeId is null, set activeId to sessions[0].id. Also keep the existing logic: if activeId is set but not in sessions (e.g. deleted), set activeId to sessions[0] or null.

---

## 12. Stale messages when switching chats or on getChat error

**Symptom:** Switching to another chat or a failed getChat showed the previous chat’s messages.

**Fix:** In ChatInterface, when sessionId is set and we start loading: set messages to [] and clear error. On getChat error, set error and set messages to [].

---

For more quick reference, see **04-common-issues-and-fixes.md**.
