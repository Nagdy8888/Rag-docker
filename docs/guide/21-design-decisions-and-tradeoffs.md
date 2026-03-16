# Design Decisions and Tradeoffs (Detailed)

A short document explaining why certain choices were made. Useful when maintaining or extending the project.

## Why Stream Outside the Compiled Graph?

The Phase 4 agent is implemented as a **StateGraph** in `graph.py` but the HTTP stream uses **stream.py**, which runs the same nodes manually. Reasons:

- **Control over events:** We need to yield a status label **before** each node runs and stream tokens **during** generate. The compiled graph’s astream_events would require mapping internal events to our SSE format.
- **Simplicity:** A linear async generator is easier to debug and to change (e.g. save message/title on "sources" before "done").
- **Compatibility:** The graph is still there for batch or future use; the streaming path is the main one.

## Why Save Message and Title on "sources" Instead of in finally?

If we save in a `finally` block that runs after the generator exits, the "done" event is already sent. The frontend then refetches sessions before the DB has been updated. By saving when we **receive** the "sources" event (before yielding "done"), we ensure the title and message are committed before the client sees "done" and refetches. So the sidebar shows the new title immediately.

## Why Single-Click Delete?

The previous "click twice to confirm" caused confusion: users clicked once or clicked the row instead of the icon. Single-click delete with a toast is the expected pattern. Accidental deletes are mitigated by the trash icon being secondary (hover) and the toast giving feedback. If needed, a confirmation modal can be added later.

## Why Documents at Top of Sidebar?

The Documents entry was at the bottom of the scrollable list and disappeared when many chats were present. Moving it (and New Chat) to a sticky top block keeps navigation always visible and matches common “nav + list” patterns.

## Why Parent-Child Chunking?

Small chunks improve **search precision** (better matches); large chunks improve **generation context** (fewer fragments). Parent-child gives both: search on children, return parent content to the LLM. Tradeoff: more storage and a more complex pipeline; the gain in answer quality justified it for Phase 3.

## Why Grade Documents?

Retrieval is by similarity, not by “answers this question.” Grading filters out irrelevant chunks and reduces noise and hallucination. Tradeoff: extra LLM call(s) and latency; we accept that for higher quality in Phase 4.

## Why Hallucination Check with Max One Retry?

We want to catch answers that add facts not in the context, but we don’t want long retry loops. One retry is a compromise: we give the model a second chance without risking long or infinite runs.

## Why No Supabase Client SDK for DB?

The app uses **SQLAlchemy + connection string** so we can run arbitrary SQL (including RPCs like hybrid_search) and keep migrations in plain SQL files. The Supabase client is optional for auth or storage; for this project, Postgres + pgvector is the only requirement.

## Why Long Nginx Timeouts for /api?

Phase 4 can run many LLM steps in one request. Without long timeouts, the proxy could close the connection before the stream finishes. 86400s avoids that; in practice most responses finish in minutes.

---

For implementation details, see the other guide documents; for concept deep-dives, see `docs/concepts/`.
