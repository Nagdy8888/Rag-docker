"""Streaming response: retrieve context, then stream LLM token-by-token."""

from langchain_core.messages import BaseMessage

from app.agent.llm import get_chat_llm
from app.agent.nodes import get_retrieved_context, _chunk_content_to_str
from app.agent.prompts import build_messages_with_context


async def stream_chat_response(messages: list[BaseMessage]):
    """
    Stream the response token by token: retrieve context, then stream LLM directly.
    Yields: ("status", label), ("token", chunk), ("done", "").
    """
    yield "status", "Retrieving..."
    context = get_retrieved_context(messages)
    yield "status", "Generating..."
    llm = get_chat_llm()
    messages_with_context = build_messages_with_context(messages, context)
    async for chunk in llm.astream(messages_with_context):
        content = _chunk_content_to_str(chunk)
        if content:
            yield "token", content
    yield "done", ""
