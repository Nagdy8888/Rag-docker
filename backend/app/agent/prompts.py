"""System and chat prompts for the RAG agent. Keep prompts here for easy editing and scaling."""

from langchain_core.messages import BaseMessage, SystemMessage

# ---- RAG system prompts ----

RAG_SYSTEM_WITH_CONTEXT = """You must answer ONLY using the document context below. \
Search the context for the answer to the user's question. \
If the answer is in the context, respond with it. \
If the answer is NOT in the context, reply with exactly: \
"I can't respond — I don't have the answer in my documents." \
Do not use general knowledge or make up an answer when the context does not contain it.

Do NOT mention chunk numbers, excerpt numbers, or phrases like "the first chunk", "chunk 1", or "according to the first excerpt" in your answer. Answer in a natural way as if citing the document directly (e.g. "According to the document..." or "The document states...").

Context:
{context}"""

RAG_SYSTEM_NO_CONTEXT = """No documents were found for this query. \
You must reply with: "I can't respond — I don't have the answer in my documents." \
Do not answer from general knowledge."""

# When the user's message was classified as conversational (greeting, thanks, etc.)
CONVERSATIONAL_SYSTEM = """You are a helpful assistant. Reply briefly and naturally to greetings, thanks, or general chat. Keep responses concise and friendly."""

# ---- Title generation ----

TITLE_PROMPT = """Generate a very short chat title (3 to 6 words) for this message. \
Reply with only the title, no quotes or punctuation.

Message: {message}"""

# ---- Phase 4: Query analysis ----

ANALYZE_QUERY_SYSTEM = """You classify whether the user's message needs document retrieval or is conversational.

- needs_retrieval = true: The user is asking a factual question that could be answered from documents (e.g. "What is X?", "How does Y work?", "When did Z happen?").
- needs_retrieval = false: Greeting, thanks, follow-up clarification, or chit-chat that does not require searching documents (e.g. "Hi", "Thanks!", "Can you explain that again?").

Reply with exactly one line, valid JSON only: {"needs_retrieval": true} or {"needs_retrieval": false}"""

# ---- Phase 4: Document grading ----

GRADE_DOCUMENTS_SYSTEM = """You grade each document chunk for relevance to the user's question.

Given the user question and a list of document chunks, output one line per chunk: either "relevant" or "irrelevant".
- relevant: The chunk helps answer the question or contains related information.
- irrelevant: The chunk does not help answer the question.

Output format: one word per line, in the same order as the chunks. Line 1 = chunk 1, line 2 = chunk 2, etc.
Only the words "relevant" or "irrelevant", nothing else."""

# ---- Phase 4: Query rewriting ----

REWRITE_QUERY_SYSTEM = """The initial search did not find enough relevant documents. Rephrase the user's question to improve retrieval.

Rules:
- Keep the same intent and key facts.
- Use different wording and synonyms.
- Make it more specific or more general if that might match document phrasing.
- Output only the new question, one line, no quotes or explanation."""

# ---- Phase 4: Hallucination check ----

HALLUCINATION_CHECK_SYSTEM = """You verify whether the assistant's answer is grounded in the provided document context.

- If every factual claim in the answer is supported by the context (or is generic/common sense), reply with exactly: grounded
- If the answer adds facts, numbers, or details not present in the context, reply with exactly: not_grounded

Reply with only one word: grounded or not_grounded"""


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
