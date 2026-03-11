# Embeddings and Vector Indexes Explained

This document is a technical deep-dive on how Phase 2 RAG uses **embeddings** and **vector indexes** (pgvector, IVFFlat) for semantic search.

---

## What are embeddings?

**Embeddings** are dense vector representations of text (or other data). A model maps a string to a fixed-length list of numbers (e.g. 1536 floats). Semantically similar texts get vectors that are “close” in the chosen distance measure (e.g. cosine similarity or L2).

- **Why use them:** Keyword search fails when the user phrase doesn’t match the document wording. Embeddings capture meaning, so “annual revenue” and “yearly income” can be close in vector space even though they share no words.
- **Dimensions:** More dimensions usually mean more expressive power but more storage and compute. **OpenAI text-embedding-3-small** uses **1536 dimensions** by default (configurable down for cost/speed).

---

## OpenAI text-embedding-3-small

- **Dimensions:** 1536 (default). You can request fewer (e.g. 256) for smaller indexes and faster search at a small quality trade-off.
- **Cost:** Very low per token; often on the order of tens of thousands of pages per dollar.
- **Max input:** 8192 tokens per request. For long documents we chunk first, then embed each chunk.
- **Usage in this project:** We embed both **document chunks** (at ingest time) and the **user query** (at query time). We compare the query vector to chunk vectors to find the most relevant chunks.

---

## Exact vs. approximate nearest neighbor search

- **Exact (brute-force):** Compare the query vector to every stored vector and return the top-k by distance. Correct but **O(n)** per query; fine for small datasets (e.g. hundreds of vectors).
- **Approximate (ANN):** Use an index (IVFFlat, HNSW) to avoid scanning every vector. **Faster** and scalable, with a small chance of missing the true nearest neighbors.

For large corpora we use **approximate** search; pgvector provides IVFFlat and HNSW for that.

---

## PostgreSQL pgvector

**pgvector** is a Postgres extension that adds a `vector` type and distance operators.

- **Types:** `vector(n)` — e.g. `vector(1536)` for our embeddings.
- **Distance operators:**
  - **Cosine distance:** `<=>` — common for normalized embeddings; we use `1 - (a <=> b)` as similarity.
  - **L2 (Euclidean):** `<->`
  - **Inner product:** `<#>` (for already normalized vectors, related to cosine).

Our **`match_documents`** function uses **cosine** (`<=>`) and returns results ordered by smallest distance (most similar first).

---

## IVFFlat index

**IVFFlat** = “Inverted File with Flat storage.”

- **Idea:** Cluster vectors (e.g. with k-means) into `lists` buckets. At query time, find the nearest cluster(s), then do **exact** search only within those buckets.
- **Parameters:**
  - **lists:** Number of clusters. Rule of thumb: `sqrt(row_count)` to a few times that. Too many lists → small buckets, more list overhead; too few → almost brute-force.
- **Trade-offs:**
  - **Pros:** Build is relatively fast, memory predictable.
  - **Cons:** Quality depends on clustering; not as accurate as HNSW for the same memory.

We create the index with:

```sql
CREATE INDEX idx_documents_embedding ON documents
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

`vector_cosine_ops` tells Postgres to use the cosine distance operator for this index. Tune `lists` as your `documents` table grows (e.g. re-create with a larger value after loading more data).

---

## HNSW (for later phases)

**HNSW** (Hierarchical Navigable Small World) is another index type in pgvector.

- **Idea:** A layered graph where search starts at the top layer and “zooms in” to lower layers. Very fast and often more accurate than IVFFlat for similar memory.
- **Parameters:**
  - **m:** Max edges per node (e.g. 16). Higher → better recall, more memory.
  - **ef_construction:** Size of the dynamic candidate list during build. Higher → better index quality, slower build.
- **When to use:** Phase 3+ may switch to HNSW for better recall and query speed once the retrieval pipeline is more advanced.

---

## Index tuning (rule of thumb)

- **IVFFlat `lists`:** Start with ~100 for small datasets; aim for `lists` on the order of `sqrt(n)` to a few times `sqrt(n)`.
- **HNSW `m`:** 16 is a common default; 24–48 can improve recall at higher memory cost.
- **HNSW `ef_construction`:** 64–200; higher for better quality, slower builds.

Rebuild indexes after large bulk loads if you change parameters.

---

## Summary

- **Embeddings** turn text into vectors so we can do semantic similarity search.
- **text-embedding-3-small** gives 1536-d vectors; we store them in **pgvector** and search with **cosine** distance.
- **IVFFlat** gives scalable approximate search; **HNSW** (in later phases) can give better recall and speed when tuned.

For more on combining vector search with keyword search, see **`docs/concepts/hybrid-search.md`** (Phase 3).
