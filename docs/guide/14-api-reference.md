# API Reference (Detailed)

Base path: **/api** (proxied from frontend). All responses JSON unless noted.

---

## Chats

### GET /api/chats

- **Response:** List of chat sessions (newest first).  
- **Shape:** `[{ id, title, created_at, updated_at }]`.

### GET /api/chats/{session_id}

- **Response:** One session with messages.  
- **Shape:** `{ id, title, created_at, updated_at, messages: [{ id, session_id, role, content, created_at, sources? }] }`.  
- **404** if session not found.

### POST /api/chats

- **Body:** None.  
- **Response:** New session: `{ id, title, created_at, updated_at }`.  
- **500** if insert fails.

### DELETE /api/chats/{session_id}

- **Response:** 204 No Content.  
- Deletes session and all its messages (CASCADE).

---

## Chat Stream

### POST /api/chat

- **Body:** `{ "session_id": "uuid", "content": "user message" }`.  
- **Response:** SSE stream (`Content-Type: text/event-stream`).  
- **Events:** Each event has `event: message` and `data` = JSON string: `{ "type": "status"|"token"|"sources"|"error"|"done", "content": "..." }`.  
  - **status** — Current step label (e.g. "Analyzing question...", "Grading relevance...").  
  - **token** — One piece of assistant text (streaming).  
  - **sources** — JSON array of `{ filename, chunk_index?, snippet? }` (content is the stringified array).  
  - **error** — Error message if an exception occurred.  
  - **done** — Stream end (content empty).  
- **400** if content empty; **404** if session not found.  
- User message is persisted before streaming; assistant message (and optional sources) are saved when sources event is processed (or in finally on error). New-session title is updated when sources are saved.

---

## Documents

### GET /api/documents

- **Response:** List of processed files: `[{ id, filename, file_type, file_size, chunk_count, status, error_message?, created_at }]`.

### GET /api/documents/status

- **Response:** `{ documents_folder, folder_exists, files_on_disk, files_count, phase2_tables_ok, db_error? }` (diagnostic).

### POST /api/documents/upload

- **Body:** multipart/form-data with `files` (one or more).  
- **Response:** `{ results: [{ filename, success, file_id?, status?, error? }] }`.  
- Files are written to the documents folder and processed (same pipeline as watcher). Max size and allowed extensions enforced.

### GET /api/documents/test-retrieval?q=...

- **Query:** `q` = search string.  
- **Response:** `{ query, chunk_count, previews[] }` or `{ query, chunk_count, error, previews }`.  
- For quick retrieval tests.
