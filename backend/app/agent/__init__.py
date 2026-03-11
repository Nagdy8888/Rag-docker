"""
RAG agent package: state, prompts, nodes, graph, streaming, title.
Import from here to keep the same API as before refactor.
"""

from app.agent.state import AgentState
from app.agent.prompts import (
    build_messages_with_context,
    build_system_message,
    RAG_SYSTEM_WITH_CONTEXT,
    RAG_SYSTEM_NO_CONTEXT,
    TITLE_PROMPT,
)
from app.agent.llm import get_chat_llm
from app.agent.nodes import (
    get_retrieved_context,
    retrieve_node,
    generate_node,
    _chunk_content_to_str,
)
from app.agent.graph import create_chat_graph
from app.agent.stream import stream_chat_response
from app.agent.title import generate_title

__all__ = [
    "AgentState",
    "build_messages_with_context",
    "build_system_message",
    "RAG_SYSTEM_WITH_CONTEXT",
    "RAG_SYSTEM_NO_CONTEXT",
    "TITLE_PROMPT",
    "get_chat_llm",
    "get_retrieved_context",
    "retrieve_node",
    "generate_node",
    "_chunk_content_to_str",
    "create_chat_graph",
    "stream_chat_response",
    "generate_title",
]
