# Chunking Strategies Explained

This document explains why we **chunk** documents for RAG and how **parent-child chunking** (Phase 3) improves retrieval and generation.

---

## Why chunking matters

- **Embedding models** have a maximum input length (e.g. 8192 tokens). A long document cannot be embedded as one block.
- **Retrieval** returns the “best” pieces of the corpus. If we stored whole documents, we’d often retrieve huge, only partially relevant blocks. **Chunking** lets us retrieve small, focused pieces.
- **Generation** needs enough context to answer, but not so much that the model gets lost. Chunk size trades off **precision** (small chunks = precise matches) vs **context** (large chunks = more surrounding text).

So we need a strategy: how big should chunks be, and how do we split?

---

## Naive vs. recursive character splitting

- **Naive:** Split by fixed character count (e.g. every 500 chars). Simple but can cut sentences or paragraphs in the middle and break meaning.
- **Recursive character splitting:** Try to split on “natural” boundaries first (e.g. `\n\n`, then `\n`, then `. `, then ` `), and only break in the middle of a word as a last resort. This keeps sentences and paragraphs intact when possible.

We use **RecursiveCharacterTextSplitter** (LangChain) with a **token-based** size (via tiktoken) so chunk sizes are consistent with model limits.

---

## Token-based vs. character-based size

- **Character-based:** e.g. chunk_size=1000 characters. Inconsistent with how models count length; a 1000-char chunk might be 200 or 400 tokens depending on language and vocabulary.
- **Token-based:** We use **tiktoken** (e.g. cl100k_base) to count tokens and set chunk_size in “token units”. So we say “~1000 tokens” and the splitter respects that. This aligns with embedding and LLM limits.

---

## Parent-child chunking: the problem it solves

- **Small chunks (e.g. 500 tokens):** Good for **search** — we get precise matches. But we send many small fragments to the LLM, which can feel choppy and lose narrative flow.
- **Large chunks (e.g. 2000 tokens):** Good for **context** — the LLM sees a coherent block. But search is less precise; the whole block might rank high because of one sentence, and we waste context on irrelevant parts.

**Parent-child chunking** separates the two concerns:

1. **Parents:** Larger chunks (e.g. 2000 tokens, 200 overlap). Stored in `parent_chunks`. **Not embedded.** Used only for **what we send to the LLM**.
2. **Children:** Smaller chunks (e.g. 500 tokens, 50 overlap). Stored in `documents` with `parent_id`. **Embedded** and full-text indexed. Used **only for search**.

At query time:

- We search over **children** (dense + sparse).
- We score and rank by child.
- We then **look up the parent** for each top child and return **parent content** to the LLM.

So: **search** is done on precise, small pieces; **generation** sees the larger, coherent parent. Best of both.

---

## How the pipeline uses it

1. **Ingest:**  
   - Split file into **parents** (2000 tokens, 200 overlap).  
   - Insert each parent into `parent_chunks`, get `parent_id`.  
   - For each parent, split its text into **children** (500 tokens, 50 overlap).  
   - Embed each child, insert into `documents` with `parent_id` and build `fts` (full-text) in the DB.

2. **Search:**  
   - Run hybrid search on `documents` (children).  
   - RRF and ranking are over child rows.  
   - For each top child we have `parent_id`; we aggregate/choose by parent and return **parent** content (or legacy document content when `parent_id` is null).

3. **Generate:**  
   - The agent receives a concatenation of **parent** contents, so the model gets larger, contiguous context instead of many tiny fragments.

---

## Chunk size and overlap tuning

- **Parent size:** 2000 tokens gives a few paragraphs of context. Increase if your answers need longer narrative; decrease if you want to force more focused retrieval.
- **Parent overlap:** 200 tokens avoids hard boundaries between parents and reduces the chance we cut a thought in half.
- **Child size:** 500 tokens is a good default for precise matching. Smaller (e.g. 256) = more precise but more chunks and more embedding cost; larger (e.g. 800) = less precision, fewer chunks.
- **Child overlap:** 50 tokens keeps a bit of continuity between children within the same parent.

These are in `document_processor.py` as `parent_splitter` and `child_splitter` parameters.

---

## Diagram (conceptual)

```
File
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│  Parent splitter (2000 tok, 200 overlap)                │
└─────────────────────────────────────────────────────────┘
  │
  ▼
Parent 1 ──► parent_chunks ──► id = p1
  │
  ▼ Child splitter (500 tok, 50 overlap)
  ├── Child 1.1 ──► documents (embedding, fts, parent_id=p1)
  ├── Child 1.2 ──► documents (embedding, fts, parent_id=p1)
  └── Child 1.3 ──► documents (embedding, fts, parent_id=p1)

Parent 2 ──► parent_chunks ──► id = p2
  │
  ▼
  ├── Child 2.1 ──► documents (parent_id=p2)
  └── ...

Query ──► search children (dense + sparse) ──► top children
       ──► resolve to parents ──► return parent content to LLM
```

---

## Summary

- Chunking is needed for embedding limits and for precise retrieval.
- **Parent-child** = small chunks for **search**, large chunks for **generation**.
- We store parents in `parent_chunks`, children in `documents` with `parent_id`; hybrid search runs on children and returns parent content to the agent.
