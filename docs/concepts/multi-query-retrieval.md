# Multi-Query Retrieval Explained

This document explains **multi-query expansion**: why we generate several phrasings of the user question and how we merge their results to improve recall.

---

## The vocabulary mismatch problem

Users phrase questions in many ways. The same intent can be expressed as:

- “How do I reset my password?”
- “Forgot password, how to recover account?”
- “Where is the password reset option?”

If we only search with the **exact** user query, we might hit only one of these phrasings in the index. The document might use different words (“account recovery”, “reset credentials”) and still be relevant. A single query can miss good chunks that would match a slightly different wording.

---

## How multi-query expansion works

1. **Expand:** From the user’s question, we generate **multiple query variants** (e.g. 3 total: the original + 2 alternatives). We use an LLM (e.g. gpt-4o-mini) with a short system prompt: “Output 2 additional alternative phrasings of the same question, one per line.”
2. **Search:** For each variant we run the same retrieval pipeline (embed + hybrid search). So we get 3 ranked lists of chunks (or parent contents).
3. **Merge:** We combine the 3 lists with **Reciprocal Rank Fusion (RRF)**. A chunk that appears in multiple lists gets a higher combined score; we deduplicate by content (or a stable key) and take the top-k.

So we cast a wider net: different phrasings can hit different chunks, and RRF ensures that chunks that appear in several result sets rise to the top.

---

## How the LLM generates alternatives

We send the user question to a fast, cheap model with instructions to output **2 extra phrasings** (so we have 3 queries in total including the original). The model is asked to:

- Rephrase the same question.
- Put one phrasing per line.
- Keep each line concise.

We parse the response by splitting on newlines and stripping. If parsing fails or we get fewer than 3, we fall back to using only the original query. So multi-query is an optional improvement; the system still works with a single query.

---

## Deduplication and merging

- **Same chunk from different queries:** The same parent (or document) can appear in the result lists for query 1, 2, and 3. We deduplicate by a key (e.g. content snippet + file_id) so we don’t show the same block twice.
- **RRF:** For each unique chunk we compute  
  `score = 1/(k + rank_1) + 1/(k + rank_2) + 1/(k + rank_3)`  
  (using 0 when the chunk doesn’t appear in a list). We sort by this score and take top-k. Chunks that rank well for **multiple** phrasings get a higher score and are more likely to be in the final set.

This is the same RRF idea as in hybrid search (dense + sparse), but applied **across query variants** instead of across dense vs. sparse.

---

## Examples where it helps

- **Synonyms:** User says “refund”; doc says “return” or “money back”. One variant might be “how to get a return” and match.
- **Question form:** “What is X?” vs “Explain X” vs “Tell me about X”. Different variants can match different sentence structures in the docs.
- **Jargon vs. plain language:** User says “dashboard”; doc says “control panel”. A variant might rephrase to “control panel” and hit the right chunk.

So we get better **recall** (we find more of the relevant chunks) while still ranking by how often and how highly a chunk appears across the variants.

---

## Cost and latency

- **Extra cost:** One small LLM call per user message (e.g. gpt-4o-mini for 2 lines of output). Usually a fraction of the cost of the main answer.
- **Extra latency:** One round-trip for expansion, then 3 retrieval runs (each with embed + hybrid search). We fetch more candidates per query (e.g. top_k * 2) so that after RRF we still have enough for top_k.

If you need to reduce cost or latency, you can disable multi-query (e.g. `retrieve(..., use_multi_query=False)`) and use only the original query.

---

## Summary

- **Multi-query expansion** = generate 3 phrasings (original + 2 from LLM), search with each, merge with RRF.
- It addresses **vocabulary mismatch**: different wordings can retrieve different chunks, and RRF favors chunks that are relevant to multiple phrasings.
- Implemented in `retriever.py` (`_expand_queries` and `retrieve` with `use_multi_query=True`).
