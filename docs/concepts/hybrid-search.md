# Hybrid Search Explained

This document explains how **hybrid search** combines **dense** (vector) and **sparse** (keyword) search to improve RAG retrieval quality.

---

## What is dense search?

**Dense search** uses **embeddings**: text is turned into a high-dimensional vector (e.g. 1536 dimensions with OpenAI’s model). The query is embedded and compared to stored chunk vectors (e.g. with **cosine similarity**). Chunks whose vectors are “close” to the query vector are considered relevant.

- **Strength:** Captures **meaning**. “Annual revenue” and “yearly income” can be close even with no shared words.
- **Weakness:** Can miss **exact** terms (names, IDs, formulas). If the user asks for “Q3 2024” and the doc says “Q3 2024”, vector similarity might still rank it lower than a chunk that talks about “quarterly results” in general.

---

## What is sparse search?

**Sparse search** uses **keyword** (or bag-of-words) signals. In our setup we use PostgreSQL **full-text search**: the document is turned into a **tsvector** (e.g. `to_tsvector('english', content)`) and the query into a **tsquery** (e.g. `plainto_tsquery('english', query)`). We rank by **ts_rank** and return rows where `fts @@ plainto_tsquery(...)`.

- **Strength:** Matches **exact** phrases and important terms. Great for names, codes, and specific wording.
- **Weakness:** Fails when the user **paraphrases**. “How do I reset my password?” might not match a doc that only says “account recovery”.

---

## Why neither alone is enough

- **Dense only:** Misses precise matches (e.g. “error code 42”, “Section 3.2”).
- **Sparse only:** Misses paraphrased or conceptual questions that don’t share wording with the doc.

**Hybrid** = run both, then combine the rankings so we get both semantic relevance and keyword match.

---

## How hybrid search combines both

We run two searches:

1. **Dense:** Order chunks by embedding distance (e.g. cosine) and assign a **rank** (1, 2, 3, …).
2. **Sparse:** Order chunks by full-text rank and assign a **rank** (1, 2, 3, …).

Then we merge the two ranked lists using **Reciprocal Rank Fusion (RRF)**.

---

## Reciprocal Rank Fusion (RRF)

For each chunk that appears in either list, we compute:

- **score(chunk) = 1/(k + rank_dense) + 1/(k + rank_sparse)**

If a chunk appears in only one list, we treat the other term as 0 (or we only add the term for the list it appears in). We use **k = 60** (a constant that smooths the effect of rank).

- **Formula:** `RRF_score(d) = Σ 1 / (k + rank_i(d))` over all lists where document `d` appears.

Then we sort by this combined score and take the top-k. So:

- Chunks that rank well in **both** dense and sparse get the highest scores.
- Chunks that rank well in only one list still get a non-zero score and can appear in the final list.

A small **worked example:**

- Dense top-3: [A, B, C]  
- Sparse top-3: [B, A, D]  

With k=60:

- A: 1/61 + 1/62 ≈ 0.0324  
- B: 1/61 + 1/61 ≈ 0.0328  
- C: 1/63  
- D: 1/63  

So order becomes B, A, then C/D. B and A are boosted because they appear in both lists.

---

## The SQL implementation (walkthrough)

In `hybrid_search()` we use CTEs:

1. **dense:** `ROW_NUMBER() OVER (ORDER BY embedding <=> query_embedding)` on `documents`, limited (e.g. 200 rows).
2. **sparse:** Same, but `ORDER BY ts_rank(fts, plainto_tsquery('english', query_text)) DESC`, only for rows where `fts @@ plainto_tsquery(...)`.
3. **rrf:** For each row we have `COALESCE(parent_id, id)` (so we group by parent when using parent-child). We add `1/(rrf_k + rn)` per list (dense and sparse).
4. **parent_scores:** `GROUP BY pid, SUM(score)`, then `ORDER BY total DESC LIMIT match_count`.
5. Final **SELECT** joins back to `parent_chunks` or `documents` to return the **content** (parent content when `parent_id` is set, else document content for backward compatibility).

So the “chunk” we rank is the **child** (the row in `documents`); the **content** we return to the LLM is the **parent** (larger context) when available.

---

## Tuning the RRF k constant

- **Larger k (e.g. 60):** Ranks matter less; the difference between rank 1 and rank 10 is smaller. Good when the two lists are on different scales or when we want to avoid one list dominating.
- **Smaller k:** Rank matters more; being first in one list gives a big boost. Good when we want to strongly favor chunks that appear at the top of either list.

We expose `rrf_k` as a parameter in `hybrid_search()` (default 60) so you can tune it without changing code.

---

## Summary

- **Dense** = meaning (embeddings); **sparse** = keywords (full-text).
- **Hybrid** = run both and merge with **RRF** so we get both semantic and lexical relevance.
- The SQL function does dense + sparse, RRF, and parent lookup in one place; the Python retriever adds **multi-query** expansion and another RRF merge across the expanded queries.
