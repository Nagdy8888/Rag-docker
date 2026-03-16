# Retrieval Pipeline (Detailed)

Retrieval is implemented in **retriever.py** and uses the **hybrid_search** SQL function in the database. It combines dense (vector) and sparse (full-text) search with **Reciprocal Rank Fusion (RRF)** and returns **parent-level** content when parent-child chunking is used.

## Steps

1. **Query expansion (optional)**
  `_expand_queries(query, num_variants=3)` uses the LLM to generate 2 extra phrasings (plus the original). Used when `retrieve(..., use_multi_query=True)` (default).
2. **Per-query retrieval**
  For each query variant:  
  - Embed the query with `OpenAIEmbeddings(model="text-embedding-3-small")`.  
  - Call `hybrid_search_sql(query_embedding, query_text, top_k=per_query_k, file_id=None, rrf_k=RRF_K)`.  
  - The SQL function runs dense ranking (HNSW on embedding) and sparse ranking (GIN on fts), computes RRF scores by (parent or doc) id, and returns top-k rows with content from parent_chunks (or documents if no parent_id).
3. **RRF merge across variants**
  If multiple variants were used, `_rrf_merge(doc_lists, k=RRF_K, top_k=top_k)` merges the ranked lists using RRF again (dedupe by content slice + file_id), and returns the final top_k documents.
4. **Return**
  List of LangChain `Document` objects with `page_content` (parent or doc content) and `metadata` (e.g. source, file_id, chunk_index).

## hybrid_search_sql

- Takes: query_embedding (list of 1536 floats), query_text, match_count, filter_file_id, rrf_k.  
- Calls DB function `hybrid_search(...)`.  
- Maps rows to Document; metadata includes file_id.  
- Content returned is the **parent** chunk text when parent_id is set, else the document row content (Phase 2 compatibility).

## RRF Formula

Score for an item appearing at rank r in a list: `1 / (k + r)`. k = RRF_K (60). Items from multiple lists (dense and sparse, or multiple queries) have scores summed; then sort by total score descending.

## Parent-Child Behavior

- Search is over **child** rows (documents with parent_id set): they have embeddings and fts.  
- Scores are aggregated by **parent** (COALESCE(parent_id, id)).  
- Returned content is the **parent** chunk (larger context) for better generation quality.  
- Files ingested before Phase 3 have no parent_id; hybrid_search falls back to returning document content.

## Tuning

- RETRIEVE_TOP_K (default 8) in nodes.py.  
- per_query_k in retriever: max(top_k*2, 10) when multiple query variants.  
- RRF_K = 60 in retriever; same rrf_k passed to SQL hybrid_search.  
- HNSW parameters (m, ef_construction) and optional ef_search in SQL.

