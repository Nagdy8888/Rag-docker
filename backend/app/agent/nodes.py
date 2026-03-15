"""Graph nodes: Phase 4 intelligent agent (analyze, expand, retrieve, grade, rewrite, generate, hallucination check)."""

import json
import logging
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from app.retriever import retrieve

if TYPE_CHECKING:
    from app.agent.state import AgentState

logger = logging.getLogger(__name__)

RETRIEVE_TOP_K = 8
MIN_RELEVANT_DOCS = 1
MAX_REWRITE_COUNT = 1
MAX_HALLUCINATION_RETRY = 1


def get_retrieved_context(messages: list[BaseMessage]) -> str:
    """Return context string from retrieving on the last user message. Used for streaming fallback and title."""
    last_user = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    query = (getattr(last_user, "content", None) or "").strip()
    if not query:
        return ""
    try:
        docs = retrieve(query, top_k=RETRIEVE_TOP_K)
        context = "\n\n---\n\n".join(d.page_content for d in docs)
        logger.info("Retrieved %s chunks for query (context length %s)", len(docs), len(context))
        return context
    except Exception as e:
        logger.exception("Retrieval failed: %s", e)
        return ""


def _last_user_content(state: "AgentState") -> str:
    messages = state.get("messages") or []
    last_user = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    return (getattr(last_user, "content", None) or "").strip()


def _doc_to_source(doc: Document) -> dict[str, Any]:
    """Build a source dict for frontend: filename, page/chunk_index, snippet."""
    meta = doc.metadata or {}
    filename = meta.get("source") or meta.get("filename") or "document"
    chunk_index = meta.get("chunk_index", 0)
    snippet = (doc.page_content or "")[:300].strip()
    return {"filename": filename, "chunk_index": chunk_index, "snippet": snippet}


# ---------- Phase 4 nodes ----------


def analyze_query_node(state: "AgentState", llm) -> dict:
    """Classify: needs_retrieval or conversational. Returns state update with query_analysis."""
    from app.agent.prompts import ANALYZE_QUERY_SYSTEM

    query = _last_user_content(state)
    if not query:
        return {"query_analysis": {"needs_retrieval": False}}
    try:
        msg = llm.invoke([
            SystemMessage(content=ANALYZE_QUERY_SYSTEM),
            HumanMessage(content=query),
        ])
        raw = (getattr(msg, "content", None) or "").strip()
        # Parse JSON from the response (may be wrapped in markdown)
        if "{" in raw:
            raw = raw[raw.index("{"):]
        if "}" in raw:
            raw = raw[: raw.rindex("}") + 1]
        data = json.loads(raw)
        needs = bool(data.get("needs_retrieval", True))
        return {"query_analysis": {"needs_retrieval": needs}}
    except Exception as e:
        logger.warning("Query analysis failed, assuming needs_retrieval: %s", e)
        return {"query_analysis": {"needs_retrieval": True}}


def expand_query_node(state: "AgentState", llm) -> dict:
    """Multi-query expansion: use last user message as primary; retriever will expand to 3 variants internally."""
    query = _last_user_content(state)
    return {"query_variants": [query] if query else []}


def hybrid_retrieve_node(state: "AgentState") -> dict:
    """Run hybrid retrieval (Phase 3) for the last user message. Returns state update with retrieved_docs."""
    messages = state.get("messages") or []
    query = _last_user_content(state)
    if not query:
        return {"retrieved_docs": [], "context": ""}
    try:
        docs = retrieve(query, top_k=RETRIEVE_TOP_K)
        context = "\n\n---\n\n".join(d.page_content for d in docs)
        logger.info("Retrieved %s chunks for query", len(docs))
        return {"retrieved_docs": docs, "context": context}
    except Exception as e:
        logger.exception("Retrieval failed: %s", e)
        return {"retrieved_docs": [], "context": ""}


def grade_documents_node(state: "AgentState", llm) -> dict:
    """Grade each retrieved doc as relevant/irrelevant. Filter to relevant only, set graded_docs and context."""
    from app.agent.prompts import GRADE_DOCUMENTS_SYSTEM

    query = _last_user_content(state)
    docs = state.get("retrieved_docs") or []
    if not docs:
        return {"graded_docs": [], "context": "", "sources": []}

    # Build prompt: question + numbered chunks
    chunks_text = "\n\n".join(f"[Chunk {i+1}]\n{d.page_content}" for i, d in enumerate(docs))
    prompt = f"User question: {query}\n\nChunks:\n{chunks_text}"

    try:
        msg = llm.invoke([
            SystemMessage(content=GRADE_DOCUMENTS_SYSTEM),
            HumanMessage(content=prompt),
        ])
        raw = (getattr(msg, "content", None) or "").strip().lower()
        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
        graded = []
        for i, doc in enumerate(docs):
            if i < len(lines) and "relevant" in lines[i] and "irrelevant" not in lines[i]:
                graded.append(doc)
    except Exception as e:
        logger.warning("Grading failed, keeping all docs: %s", e)
        graded = list(docs)

    context = "\n\n---\n\n".join(d.page_content for d in graded)
    sources = [_doc_to_source(d) for d in graded]
    return {"graded_docs": graded, "context": context, "sources": sources}


def rewrite_query_node(state: "AgentState", llm) -> dict:
    """Rephrase the user question to improve retrieval. Returns state update with new query in query_variants, increment rewrite_count."""
    from app.agent.prompts import REWRITE_QUERY_SYSTEM

    query = _last_user_content(state)
    rewrite_count = state.get("rewrite_count") or 0
    if not query:
        return {"query_variants": [], "rewrite_count": rewrite_count + 1}
    try:
        msg = llm.invoke([
            SystemMessage(content=REWRITE_QUERY_SYSTEM),
            HumanMessage(content=query),
        ])
        rewritten = (getattr(msg, "content", None) or "").strip()[:500]
        if rewritten:
            return {"query_variants": [rewritten], "rewrite_count": rewrite_count + 1}
    except Exception as e:
        logger.warning("Rewrite failed: %s", e)
    return {"query_variants": [query], "rewrite_count": rewrite_count + 1}


def retrieve_with_query_variant_node(state: "AgentState") -> dict:
    """Retrieve using the first query variant (after rewrite). Same as hybrid_retrieve but uses query_variants."""
    query_variants = state.get("query_variants") or []
    query = query_variants[0] if query_variants else _last_user_content(state)
    if not query:
        return {"retrieved_docs": [], "context": ""}
    try:
        docs = retrieve(query, top_k=RETRIEVE_TOP_K)
        context = "\n\n---\n\n".join(d.page_content for d in docs)
        return {"retrieved_docs": docs, "context": context}
    except Exception as e:
        logger.exception("Retrieve after rewrite failed: %s", e)
        return {"retrieved_docs": [], "context": ""}


async def generate_node(state: "AgentState", llm) -> dict:
    """Produce answer from graded context + messages. Attach sources to state. Returns state update."""
    from app.agent.prompts import build_messages_with_context, build_system_message, CONVERSATIONAL_SYSTEM

    context = state.get("context") or ""
    messages = state.get("messages") or []
    sources = state.get("sources") or []
    query_analysis = state.get("query_analysis") or {}
    is_conversational = query_analysis.get("needs_retrieval") is False

    if is_conversational:
        messages_with_context = [SystemMessage(content=CONVERSATIONAL_SYSTEM)] + list(messages)
    else:
        messages_with_context = build_messages_with_context(messages, context)
    chunks = []
    async for chunk in llm.astream(messages_with_context):
        chunks.append(chunk)
    content = "".join(_chunk_content_to_str(c) for c in chunks)
    return {"messages": [AIMessage(content=content)], "sources": sources}


def check_hallucination_node(state: "AgentState", llm) -> dict:
    """Verify the last assistant message is grounded in context. Returns state update with verdict."""
    from app.agent.prompts import HALLUCINATION_CHECK_SYSTEM

    messages = state.get("messages") or []
    context = state.get("context") or ""
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
    answer = (getattr(last_ai, "content", None) or "").strip()
    if not answer or not context:
        return {"hallucination_verdict": "grounded"}

    prompt = f"Context:\n{context}\n\nAssistant answer:\n{answer}"
    try:
        msg = llm.invoke([
            SystemMessage(content=HALLUCINATION_CHECK_SYSTEM),
            HumanMessage(content=prompt),
        ])
        raw = (getattr(msg, "content", None) or "").strip().lower()
        verdict = "not_grounded" if "not_grounded" in raw else "grounded"
        return {"hallucination_verdict": verdict}
    except Exception as e:
        logger.warning("Hallucination check failed: %s", e)
        return {"hallucination_verdict": "grounded"}


def increment_hallucination_retry_node(state: "AgentState") -> dict:
    """Increment retry count before re-running generate (max 1 retry)."""
    count = state.get("hallucination_retry_count") or 0
    return {"hallucination_retry_count": count + 1}


def retrieve_node(state: "AgentState") -> dict:
    """Legacy: fetch context for last user message (Phase 2 style). Used by non-Phase-4 stream path."""
    messages = state.get("messages") or []
    context = get_retrieved_context(messages)
    return {"context": context}


async def generate_node_streaming(state: "AgentState", llm):
    """
    Stream generate node: yield each token string. Caller collects and uses state['sources'] for references.
    """
    from app.agent.prompts import build_messages_with_context, CONVERSATIONAL_SYSTEM

    context = state.get("context") or ""
    messages = state.get("messages") or []
    query_analysis = state.get("query_analysis") or {}
    is_conversational = query_analysis.get("needs_retrieval") is False

    if is_conversational:
        messages_with_context = [SystemMessage(content=CONVERSATIONAL_SYSTEM)] + list(messages)
    else:
        messages_with_context = build_messages_with_context(messages, context)

    async for chunk in llm.astream(messages_with_context):
        content = _chunk_content_to_str(chunk)
        if content:
            yield content


def _chunk_content_to_str(chunk) -> str:
    """Extract string content from an LLM stream chunk (AIMessageChunk)."""
    content = getattr(chunk, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text" and "text" in part:
                    parts.append(part["text"])
                elif "text" in part:
                    parts.append(part["text"])
            elif hasattr(part, "text"):
                parts.append(part.text)
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content) if content else ""
