# Agent Overview (Detailed)

The chat agent is implemented with **LangGraph** (state graph) and runs in two modes: **streaming** (used by the API) and **batch** (compiled graph in `graph.py`, used for non-streaming or future use). The streaming path in `stream.py` does not use the compiled graph; it runs the same nodes manually and yields status/token/sources/done.

## State (AgentState)

Defined in `agent/state.py`. Fields:

- **messages** — list of LangChain messages (history + latest user message).
- **context** — string of concatenated document chunks passed to the generate step.
- **query_analysis** — `{ "needs_retrieval": bool }` from analyze_query.
- **query_variants** — list of strings (e.g. rewritten query for second retrieval).
- **retrieved_docs** — list of Document from hybrid_retrieve.
- **graded_docs** — list of Document kept after grading (relevant only).
- **rewrite_count** — number of rewrite attempts (max 1).
- **hallucination_retry_count** — number of generate retries after not_grounded (max 1).
- **hallucination_verdict** — "grounded" | "not_grounded".
- **sources** — list of `{ filename, chunk_index, snippet }` for the frontend.

## High-Level Flow (Phase 4)

1. **analyze_query** — LLM classifies: needs_retrieval vs conversational.
2. If **conversational**: go to generate (conversational system prompt) → check_hallucination → end.
3. If **needs_retrieval**:  
   - **expand_query** (sets query_variants).  
   - **hybrid_retrieve** (retriever returns parent-level docs).  
   - **grade_documents** (LLM marks each chunk relevant/irrelevant; filter to relevant, build context and sources).  
   - If too few relevant and rewrite_count &lt; 1: **rewrite_query** → **retrieve_after_rewrite** → **grade_documents** again.  
   - **generate** — build messages with graded context (or no-context prompt), stream tokens.  
   - **check_hallucination** — LLM says grounded or not_grounded.  
   - If not_grounded and retry &lt; 1: **increment_hallucination_retry** → **generate** again → **check_hallucination** → end.  
   - Else end.  
4. Emit **sources** (JSON) then **done**.

## Where It Runs

- **Streaming:** `stream_chat_response()` in `stream.py` runs the steps above and yields events. Used by `POST /api/chat` in `main.py`.
- **Graph:** `create_chat_graph()` in `graph.py` builds a StateGraph with the same nodes and conditional edges; compiled graph is available for batch or debugging but is not used by the HTTP stream.

## LLM and Prompts

- Single LLM: `get_chat_llm()` (gpt-4o-mini) used for analyze, grade, rewrite, generate, hallucination check.  
- Prompts live in `prompts.py`: RAG system with context, no-context, conversational, title, analyze, grade, rewrite, hallucination.  
- Generate uses either graded context (RAG prompt) or conversational prompt depending on query_analysis.
