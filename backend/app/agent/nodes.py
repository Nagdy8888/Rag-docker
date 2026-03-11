"""Graph nodes: retrieve and generate. Helpers for context retrieval and chunk parsing."""

import logging
from typing import TYPE_CHECKING

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.retriever import retrieve

if TYPE_CHECKING:
    from app.agent.state import AgentState

logger = logging.getLogger(__name__)

# Number of chunks to retrieve per query
RETRIEVE_TOP_K = 8


def get_retrieved_context(messages: list[BaseMessage]) -> str:
    """Return context string from retrieving on the last user message. Used for streaming and graph."""
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


def retrieve_node(state: "AgentState") -> dict:
    """Fetch relevant document chunks for the last user message. Returns state update with context."""
    messages = state.get("messages") or []
    context = get_retrieved_context(messages)
    return {"context": context}


async def generate_node(state: "AgentState", llm) -> dict:
    """Produce full response from context + messages (used when not streaming). Returns state update."""
    from app.agent.prompts import build_messages_with_context

    context = state.get("context") or ""
    messages = state.get("messages") or []
    messages_with_context = build_messages_with_context(messages, context)
    chunks = []
    async for chunk in llm.astream(messages_with_context):
        chunks.append(chunk)
    content = "".join(_chunk_content_to_str(c) for c in chunks)
    return {"messages": [AIMessage(content=content)]}


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
