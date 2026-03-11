"""Hybrid retrieval: dense + sparse search, multi-query expansion, RRF, parent chunk lookup."""

import logging
from collections import defaultdict

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from sqlalchemy import text

from app.config import get_settings
from app.database import get_connection

logger = logging.getLogger(__name__)

# RRF constant (higher = less weight on rank position)
RRF_K = 60.0


def get_embeddings() -> OpenAIEmbeddings:
    """Return OpenAI embeddings model (text-embedding-3-small)."""
    return OpenAIEmbeddings(model="text-embedding-3-small")


def _expand_queries(query: str, num_variants: int = 3) -> list[str]:
    """
    Use LLM to generate alternative phrasings for multi-query retrieval.
    Returns up to num_variants strings (includes original if possible).
    """
    query = (query or "").strip()
    if not query:
        return []
    variants = [query]
    if num_variants <= 1:
        return variants
    try:
        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.3,
        )
        msg = llm.invoke(
            [
                SystemMessage(
                    content="You are a search query expander. Given a user question, output exactly "
                    "2 additional alternative phrasings of the same question. Put one phrasing per line. "
                    "Output only the 2 lines, no numbering or extra text. Keep each line concise."
                ),
                HumanMessage(content=query),
            ]
        )
        content = getattr(msg, "content", None) or ""
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and line not in variants:
                variants.append(line)
            if len(variants) >= num_variants:
                break
    except Exception as e:
        logger.warning("Query expansion failed, using original only: %s", e)
    return variants[:num_variants]


def hybrid_search_sql(
    query_embedding: list[float],
    query_text: str,
    top_k: int = 5,
    file_id: str | None = None,
    rrf_k: float = RRF_K,
) -> list[Document]:
    """
    Run hybrid_search() RPC: dense + sparse, RRF, return parent (or document) content.
    """
    emb_str = "[" + ",".join(map(str, query_embedding)) + "]"
    with get_connection() as conn:
        r = conn.execute(
            text(
                "SELECT id, content, metadata, file_id, chunk_index FROM hybrid_search("
                "CAST(:query_embedding AS vector), :query_text, :match_count, :filter_file_id, :rrf_k)"
            ),
            {
                "query_embedding": emb_str,
                "query_text": (query_text or "").strip() or None,
                "match_count": top_k,
                "filter_file_id": file_id,
                "rrf_k": rrf_k,
            },
        )
        rows = r.fetchall()

    docs = []
    for row in rows:
        row_dict = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
        content = row_dict.get("content") or ""
        metadata = row_dict.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        if row_dict.get("file_id") is not None:
            metadata["file_id"] = str(row_dict["file_id"])
        docs.append(Document(page_content=content, metadata=metadata))
    return docs


def _rrf_merge(doc_lists: list[list[Document]], k: float = RRF_K, top_k: int = 5) -> list[Document]:
    """
    Merge multiple ranked lists of documents using Reciprocal Rank Fusion.
    Deduplicates by (content slice or id in metadata). Returns top_k docs.
    """
    # Use first 200 chars of content + file_id as dedupe key (hybrid_search returns parent content, no stable id in Document)
    def key(d: Document) -> tuple:
        meta = d.metadata or {}
        return (d.page_content[:200] if d.page_content else "", meta.get("file_id"))

    scores: dict[tuple, float] = defaultdict(float)
    doc_by_key: dict[tuple, Document] = {}
    for doc_list in doc_lists:
        for rank, doc in enumerate(doc_list, start=1):
            key_ = key(doc)
            scores[key_] += 1.0 / (k + rank)
            if key_ not in doc_by_key:
                doc_by_key[key_] = doc

    sorted_keys = sorted(scores.keys(), key=lambda x: -scores[x])
    return [doc_by_key[k] for k in sorted_keys[:top_k]]


def retrieve(
    query: str,
    top_k: int = 5,
    file_id: str | None = None,
    use_multi_query: bool = True,
) -> list[Document]:
    """
    Hybrid retrieve with optional multi-query expansion: embed + hybrid_search per variant,
    then RRF merge and return top_k documents (parent-level content).
    """
    query = (query or "").strip()
    if not query:
        return []

    embeddings = get_embeddings()
    if use_multi_query:
        queries = _expand_queries(query, num_variants=3)
    else:
        queries = [query]

    # Fetch more per query so RRF has enough candidates
    per_query_k = max(top_k * 2, 10) if len(queries) > 1 else top_k
    doc_lists: list[list[Document]] = []
    for q in queries:
        try:
            vector = embeddings.embed_query(q)
            docs = hybrid_search_sql(
                query_embedding=vector,
                query_text=q,
                top_k=per_query_k,
                file_id=file_id,
            )
            if docs:
                doc_lists.append(docs)
        except Exception as e:
            logger.warning("Hybrid search failed for query %r: %s", q[:50], e)

    if not doc_lists:
        return []
    if len(doc_lists) == 1:
        return doc_lists[0][:top_k]
    return _rrf_merge(doc_lists, k=RRF_K, top_k=top_k)
