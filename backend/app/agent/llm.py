"""LLM instance for the agent."""

from langchain_openai import ChatOpenAI

from app.config import get_settings


def get_chat_llm() -> ChatOpenAI:
    """Return the chat LLM instance."""
    settings = get_settings()
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=0.7,
    )
