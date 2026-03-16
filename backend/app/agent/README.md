# backend/app/agent

LangGraph-based RAG agent: query routing, retrieval, grading, generation, hallucination check.

## Contents

- **state.py** — Graph state (messages, query, context, sources, etc.).
- **nodes.py** — Agent nodes: analyze_query, expand_query, hybrid_retrieve, grade_documents, rewrite_query, retrieve_after_rewrite, generate, hallucination_check, title.
- **graph.py** — LangGraph graph definition and conditional edges.
- **prompts.py** — System and user prompts for each node.
- **stream.py** — Streams agent steps to the client (SSE); orchestrates node calls.
- **llm.py** — LLM instance (OpenAI) for the agent.
- **title.py** — Generates chat session title from the first user message.

See [../../docs/guide/10-agent-overview.md](../../docs/guide/10-agent-overview.md) and [11-agent-nodes-deep-dive.md](../../docs/guide/11-agent-nodes-deep-dive.md) for details.
