"""Title generation for new chat sessions."""

from langchain_core.messages import BaseMessage, HumanMessage

from app.agent.llm import get_chat_llm
from app.agent.prompts import TITLE_PROMPT


def generate_title(messages: list[BaseMessage]) -> str:
    """Generate a short 3-6 word title for the conversation from the first user message."""
    if not messages:
        return "New Chat"
    llm = get_chat_llm()
    first_user = next((m for m in messages if isinstance(m, HumanMessage)), None)
    if not first_user or not getattr(first_user, "content", None):
        return "New Chat"
    content = first_user.content[:200] if isinstance(first_user.content, str) else str(first_user.content)[:200]
    prompt = TITLE_PROMPT.format(message=content)
    result = llm.invoke([HumanMessage(content=prompt)])
    title = (result.content or "New Chat").strip()[:80]
    return title or "New Chat"
