"""Phase 4 streaming: run graph step-by-step, emit status per node and stream tokens from generate."""

import json
from langchain_core.messages import BaseMessage, AIMessage

from app.agent.llm import get_chat_llm
from app.agent.nodes import (
    analyze_query_node,
    expand_query_node,
    hybrid_retrieve_node,
    grade_documents_node,
    rewrite_query_node,
    retrieve_with_query_variant_node,
    check_hallucination_node,
    increment_hallucination_retry_node,
    generate_node_streaming,
    MIN_RELEVANT_DOCS,
    MAX_REWRITE_COUNT,
    MAX_HALLUCINATION_RETRY,
)

STATUS_LABELS = {
    "analyze_query": "Analyzing question...",
    "expand_query": "Expanding query...",
    "hybrid_retrieve": "Searching documents...",
    "grade_documents": "Grading relevance...",
    "rewrite_query": "Rewriting query...",
    "retrieve_after_rewrite": "Searching documents...",
    "generate": "Generating answer...",
    "check_hallucination": "Verifying answer...",
    "increment_hallucination_retry": "Verifying answer...",
}


def _merge(state: dict, update: dict) -> dict:
    out = dict(state)
    for k, v in update.items():
        if v is not None:
            out[k] = v
    return out


async def stream_chat_response(messages: list[BaseMessage]):
    """
    Run Phase 4 graph step-by-step; emit status before each node and stream tokens from generate.
    Yields: ("status", label), ("token", chunk), ("sources", json_list), ("done", "").
    """
    llm = get_chat_llm()
    state = {
        "messages": list(messages),
        "context": "",
        "query_analysis": None,
        "query_variants": [],
        "retrieved_docs": [],
        "graded_docs": [],
        "rewrite_count": 0,
        "hallucination_retry_count": 0,
        "hallucination_verdict": "grounded",
        "sources": [],
    }

    # --- analyze_query ---
    yield "status", STATUS_LABELS["analyze_query"]
    state = _merge(state, analyze_query_node(state, llm))

    needs_retrieval = (state.get("query_analysis") or {}).get("needs_retrieval", True)

    if not needs_retrieval:
        # Conversational path: go straight to generate -> check_hallucination
        yield "status", STATUS_LABELS["generate"]
        full_content = ""
        async for token in generate_node_streaming(state, llm):
            full_content += token
            yield "token", token
        state["messages"] = state["messages"] + [AIMessage(content=full_content)]
        state["sources"] = []
        yield "status", STATUS_LABELS["check_hallucination"]
        state = _merge(state, check_hallucination_node(state, llm))
        yield "sources", json.dumps(state.get("sources") or [])
        yield "done", ""
        return

    # --- Retrieval path: expand -> hybrid_retrieve -> grade -> (generate | rewrite -> retrieve -> grade) -> generate -> check [-> retry] ---
    yield "status", STATUS_LABELS["expand_query"]
    state = _merge(state, expand_query_node(state, llm))
    yield "status", STATUS_LABELS["hybrid_retrieve"]
    state = _merge(state, hybrid_retrieve_node(state))
    yield "status", STATUS_LABELS["grade_documents"]
    state = _merge(state, grade_documents_node(state))

    while True:
        graded = state.get("graded_docs") or []
        rewrite_count = state.get("rewrite_count") or 0
        if len(graded) >= MIN_RELEVANT_DOCS or rewrite_count >= MAX_REWRITE_COUNT:
            break
        yield "status", STATUS_LABELS["rewrite_query"]
        state = _merge(state, rewrite_query_node(state, llm))
        yield "status", STATUS_LABELS["retrieve_after_rewrite"]
        state = _merge(state, retrieve_with_query_variant_node(state))
        yield "status", STATUS_LABELS["grade_documents"]
        state = _merge(state, grade_documents_node(state))

    # Generate (streaming)
    yield "status", STATUS_LABELS["generate"]
    full_content = ""
    async for token in generate_node_streaming(state, llm):
        full_content += token
        yield "token", token
    state["messages"] = state["messages"] + [AIMessage(content=full_content)]

    # Hallucination check (with optional retry)
    while True:
        yield "status", STATUS_LABELS["check_hallucination"]
        state = _merge(state, check_hallucination_node(state, llm))
        verdict = (state.get("hallucination_verdict") or "grounded").strip().lower()
        retry = state.get("hallucination_retry_count") or 0
        if verdict == "grounded":
            break
        if "not_grounded" in verdict and retry < MAX_HALLUCINATION_RETRY:
            state = _merge(state, increment_hallucination_retry_node(state))
            yield "status", STATUS_LABELS["generate"]
            full_content = ""
            async for token in generate_node_streaming(state, llm):
                full_content += token
                yield "token", token
            state["messages"] = state["messages"][:-1] + [AIMessage(content=full_content)]
        else:
            break

    yield "sources", json.dumps(state.get("sources") or [])
    yield "done", ""
