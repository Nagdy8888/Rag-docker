# Backend Structure (Detailed)

The backend is a **FastAPI** app under `backend/`. It uses **direct PostgreSQL** (Supabase connection string), **LangGraph** for the agent, and **OpenAI** for chat and embeddings.

## Directory Layout

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py          # Settings from env (OPENAI_API_KEY, DATABASE_URI, etc.)
│   ├── database.py        # SQLAlchemy engine, get_connection, list_sessions, get_messages, insert_message, etc.
│   ├── main.py            # FastAPI app, routes: /api/chats, /api/chats/{id}, /api/chat (SSE), /api/documents, upload
│   ├── schemas.py         # Pydantic: ChatSessionResponse, ChatMessageResponse, SourceRefResponse, etc.
│   ├── document_processor.py  # Load files (PDF, DOCX, …), parent/child chunking, embed, store in DB
│   ├── retriever.py       # hybrid_search_sql, _expand_queries, _rrf_merge, retrieve()
│   ├── watcher.py         # Watchdog on documents/ folder; on change → process_file
│   └── agent/
│       ├── __init__.py    # Re-exports state, prompts, nodes, graph, stream, title
│       ├── state.py       # AgentState TypedDict (messages, context, query_analysis, graded_docs, sources, …)
│       ├── prompts.py    # RAG_SYSTEM_*, TITLE_PROMPT, ANALYZE_QUERY_*, GRADE_*, REWRITE_*, HALLUCINATION_*
│       ├── llm.py         # get_chat_llm() — ChatOpenAI gpt-4o-mini
│       ├── nodes.py       # analyze_query_node, expand_query_node, hybrid_retrieve_node, grade_documents_node, rewrite_query_node, retrieve_with_query_variant_node, generate_node, check_hallucination_node, generate_node_streaming
│       ├── graph.py       # create_chat_graph() — StateGraph with conditional edges (Phase 4)
│       ├── stream.py      # stream_chat_response() — runs graph step-by-step, yields status/token/sources/done
│       └── title.py       # generate_title() for new chat session
├── requirements.txt
└── Dockerfile
```

## Entry Point

- **`main.py`** defines the FastAPI app, CORS, lifespan (start/stop watcher). Routes mount under `/api` (when behind nginx/Vite proxy the client calls `/api/...`).
- **Chat stream:** `POST /api/chat` builds message history, saves user message, then runs `stream_chat_response(history)` and streams SSE events. On `sources` event it saves assistant message and title; on exception it sends `error` event then `done`.

## Key Modules

- **config:** `get_settings()` returns a settings object with `openai_api_key`, `database_uri`, `documents_path`. Used by LLM, DB, and document processor.
- **database:** Synchronous; uses `get_connection()` as context manager. All chat and file reads/writes go through here. Handles optional `sources` column for Phase 4.
- **agent/stream:** Does not use the compiled LangGraph for streaming; it runs the same nodes in a fixed order and yields status labels and tokens. This keeps streaming simple and ensures we emit status before each step.
- **retriever:** Uses SQLAlchemy `text()` to call Supabase RPC `hybrid_search(...)`. Embeddings via `OpenAIEmbeddings(model="text-embedding-3-small")`.

## Dependencies (requirements.txt)

- fastapi, uvicorn, sse-starlette
- langchain-openai, langchain-core, langgraph
- sqlalchemy, psycopg2-binary
- pydantic, python-dotenv
- pypdf, python-docx, openpyxl, unstructured, tiktoken, watchdog
- langsmith (optional)
