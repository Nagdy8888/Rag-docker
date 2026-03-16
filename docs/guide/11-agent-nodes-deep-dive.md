# Agent Nodes Deep Dive

Each node is a function that takes **state** (and optionally **llm**) and returns a **state update** (dict merged into state). The streaming layer in `stream.py` calls these nodes in order and merges results with `_merge(state, update)`.

## analyze_query_node(state, llm)

- **Role:** Decide if the user message needs retrieval or is conversational.
- **Input:** state["messages"]; last user message used as query.
- **Process:** LLM with ANALYZE_QUERY_SYSTEM; parse JSON `{"needs_retrieval": true|false}`.
- **Output:** `{"query_analysis": {"needs_retrieval": bool}}`. On parse error, defaults to true.

## expand_query_node(state, llm)

- **Role:** Set query_variants for retrieval (currently just the last user content; multi-query expansion is inside retriever).
- **Output:** `{"query_variants": [query]}`.

## hybrid_retrieve_node(state)

- **Role:** Run hybrid retrieval for the last user message.
- **Process:** Calls `retrieve(_last_user_content(state), top_k=RETRIEVE_TOP_K)` from `retriever.py` (multi-query + hybrid_search + RRF).
- **Output:** `{"retrieved_docs": docs, "context": concatenated content}`.

## grade_documents_node(state, llm)

- **Role:** Filter retrieved docs to relevant only; build context and sources for generate.
- **Process:** Build prompt with question and numbered chunks; LLM returns one line per chunk ("relevant" or "irrelevant"). Filter docs to those marked relevant; concatenate content into context; build sources list from graded docs via `_doc_to_source(doc)` (filename from metadata.source, chunk_index, snippet).
- **Output:** `{"graded_docs": list, "context": str, "sources": list[dict]}`. On grading failure, keeps all docs.

## rewrite_query_node(state, llm)

- **Role:** Rephrase the question when too few docs were relevant (max one rewrite).
- **Process:** LLM with REWRITE_QUERY_SYSTEM; increment rewrite_count.
- **Output:** `{"query_variants": [rewritten], "rewrite_count": rewrite_count + 1}`.

## retrieve_with_query_variant_node(state)

- **Role:** Retrieve again after rewrite using state["query_variants"][0] (or last user message if empty).
- **Process:** Same as hybrid_retrieve but uses query from query_variants.
- **Output:** `{"retrieved_docs", "context"}`.

## generate_node(state, llm) / generate_node_streaming(state, llm)

- **Role:** Produce the assistant reply from context (or conversational prompt).
- **Process:** If query_analysis.needs_retrieval is False, use CONVERSATIONAL_SYSTEM; else build_messages_with_context(messages, context). Stream LLM tokens. generate_node_streaming yields token strings; generate_node collects and returns AIMessage + sources.
- **Output:** `{"messages": [AIMessage(content=...)], "sources": state["sources"]}`.

## check_hallucination_node(state, llm)

- **Role:** Verify the last assistant message is grounded in context.
- **Process:** LLM with HALLUCINATION_CHECK_SYSTEM; prompt = context + last AI answer. Parse "grounded" vs "not_grounded".
- **Output:** `{"hallucination_verdict": "grounded"|"not_grounded"}`.

## increment_hallucination_retry_node(state)

- **Role:** Increment retry count before re-running generate (max 1 retry).
- **Output:** `{"hallucination_retry_count": state["hallucination_retry_count"] + 1}`.

## Constants

- RETRIEVE_TOP_K = 8  
- MIN_RELEVANT_DOCS = 1  
- MAX_REWRITE_COUNT = 1  
- MAX_HALLUCINATION_RETRY = 1  
