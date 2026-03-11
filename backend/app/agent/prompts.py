"""System and chat prompts for the RAG agent. Keep prompts here for easy editing and scaling."""

from langchain_core.messages import BaseMessage, SystemMessage

# ---- RAG system prompts ----

RAG_SYSTEM_WITH_CONTEXT = """You must answer ONLY using the document context below. \
Search the context for the answer to the user's question. \
If the answer is in the context, respond with it. \
If the answer is NOT in the context, reply with exactly: \
"I can't respond — I don't have the answer in my documents." \
Do not use general knowledge or make up an answer when the context does not contain it.

Context:
{context}"""

RAG_SYSTEM_NO_CONTEXT = """No documents were found for this query. \
You must reply with: "I can't respond — I don't have the answer in my documents." \
Do not answer from general knowledge."""

# ---- Title generation ----

TITLE_PROMPT = """Generate a very short chat title (3 to 6 words) for this message. \
Reply with only the title, no quotes or punctuation.

Message: {message}"""


def build_system_message(context: str) -> str:
    """Return the system prompt text for the given context (empty = no context)."""
    if context and context.strip():
        return RAG_SYSTEM_WITH_CONTEXT.format(context=context.strip())
    return RAG_SYSTEM_NO_CONTEXT


def build_messages_with_context(messages: list[BaseMessage], context: str) -> list[BaseMessage]:
    """Build message list with system prompt: answer only from context; if not found, refuse."""
    system_text = build_system_message(context)
    system = SystemMessage(content=system_text)
    return [system] + list(messages)
