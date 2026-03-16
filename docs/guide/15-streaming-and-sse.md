# Streaming and SSE (Detailed)

The chat API streams the assistant reply using **Server-Sent Events (SSE)**. The frontend consumes the stream and updates the UI in real time (status, tokens, then sources and done).

## Backend Flow

1. **POST /api/chat** receives `session_id` and `content`.  
2. Loads message history for the session, appends the new user message, saves the user message to the DB.  
3. Builds `history` (list of LangChain HumanMessage/AIMessage).  
4. Calls **stream_chat_response(history)** (async generator).  
5. **event_generator()** iterates over stream_chat_response:  
   - For each `(event_type, event_content)` it yields an SSE event: `event: message`, `data: JSON.stringify({ type, content })`.  
   - When `event_type === "sources"` it first saves the assistant message and updates the session title (if new session), then yields the events (so the client sees the title after refetch).  
   - On exception it yields `type: "error"` with the message and then `type: "done"`.  
6. Uses **EventSourceResponse** (sse-starlette) with headers: Cache-Control no-store, X-Accel-Buffering no, Connection keep-alive.

## stream_chat_response (stream.py)

- Runs the Phase 4 flow **manually** (no compiled graph): analyze → [conversational path or retrieval path] → generate (streaming) → hallucination check (optional retry).  
- **Yields:** ("status", label), ("token", chunk), ("sources", json.dumps(sources)), ("done", "").  
- Status labels: "Analyzing question...", "Expanding query...", "Searching documents...", "Grading relevance...", "Rewriting query...", "Generating answer...", "Verifying answer...".  
- Tokens come from **generate_node_streaming**: it builds messages with context (or conversational prompt), then `async for chunk in llm.astream(messages_with_context)` and yields each content piece.

## Frontend Consumption (api/client.ts)

- **streamChat(sessionId, content, callbacks)** does fetch with POST body, then reads `res.body` with a ReadableStream reader.  
- Decodes chunks to text, splits by newline, parses lines starting with `data: `.  
- JSON in data must have `type` and `content`.  
- **onStatus(content)** for type "status".  
- **onToken(content)** for type "token".  
- **onSources(parsed)** for type "sources" (content is JSON string of sources array).  
- **onError(new Error(content))** for type "error".  
- **onDone()** for type "done".  
- After loop, calls onDone() again for safety.  
- On fetch or read error, calls onError.

## ChatInterface Behavior

- On send: appends user message, sets streaming status, clears streaming content and sources.  
- Passes **onToken**: append to streaming content (and clear status when first token arrives).  
- Passes **onSources**: store in ref and state for the upcoming assistant message.  
- Passes **onDone**: build assistant message with collected content and sources from ref, append to messages, clear streaming state, call onSessionTitleChange (refetch sessions).  
- Passes **onError**: clear streaming state and set error message.  
- Display: while streaming, a single “assistant” bubble shows streaming content + cursor; when done, that message is added to the list with optional Sources section.

## Timeouts

- **Nginx** (frontend container): proxy_read_timeout and proxy_send_timeout 86400s for long streams.  
- **Vite** (dev): proxy timeout 300000 ms (5 min) for /api so Phase 4’s many LLM calls don’t get cut off.
