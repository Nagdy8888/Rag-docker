"""Agent state schema for the RAG graph."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the chat agent: messages and RAG context."""

    messages: Annotated[list[BaseMessage], add_messages]
    context: str
