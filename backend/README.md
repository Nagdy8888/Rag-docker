# RAG Chat Backend

Python FastAPI backend for the RAG chatbot. Uses LangGraph for the agent and **direct PostgreSQL** (Supabase connection URI) for storage via SQLAlchemy + psycopg2.

## Run with Docker

From the project root:

```bash
docker compose up backend
```

Or with frontend:

```bash
docker compose up --build
```

API docs: http://localhost:8000/docs (when backend is running)

## Agent (LangGraph)

The chat agent is a LangGraph graph with a single node:

- **State:** `messages` (list of LangChain messages).
- **Node:** `generate` — calls the OpenAI chat model with the current messages and returns the new assistant message.
- **Flow:** `__start__` → `generate` → `__end__`.

Streaming uses `graph.astream_events()` so tokens are streamed from the LLM through the graph to the client.
