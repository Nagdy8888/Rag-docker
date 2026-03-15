"""Agent state schema for the RAG graph (Phase 4: 7-node intelligent agent)."""

from typing import Annotated, TypedDict, Any

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State for the chat agent: messages, RAG context, and Phase 4 routing/grading."""

    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    # Query analysis: does the user need retrieval or is it conversational?
    query_analysis: dict[str, Any]  # {"needs_retrieval": bool}
    # Multi-query expansion (Phase 3)
    query_variants: list[str]
    # Retrieved and graded docs (Phase 4)
    retrieved_docs: list[Document]
    graded_docs: list[Document]  # only relevant ones after grading
    rewrite_count: int  # how many times we rewrote the query (max 1)
    hallucination_retry_count: int  # how many times we re-generated (max 1)
    hallucination_verdict: str  # "grounded" | "not_grounded" (set by check_hallucination node)
    # Source references for the frontend (filename, page/chunk, snippet)
    sources: list[dict[str, Any]]
