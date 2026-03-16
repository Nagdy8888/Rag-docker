# Advanced RAG Plan — Concepts Explained

This document explains the **concepts** introduced in the [Advanced RAG Phases plan](../../.cursor/plans/advanced_rag_phases_d675f94d.plan.md) (Phases 5, 6, and 7). Each section describes what the concept is, why it matters, and how it fits into the pipeline.

---

## Phase 5 — Quality and Measurement

### Cross-Encoder Reranking

**What it is:** After hybrid search returns a set of candidate chunks (e.g. top 20), a **reranker** re-scores each candidate against the **exact query** using a model that considers the query and the chunk **together** (as one input). The top-K after reranking are passed to the next step (e.g. grading).

**Why it helps:**  
- **Bi-encoders** (e.g. embedding models) encode query and document **separately** and compare via similarity. They are fast and good for recall.  
- **Cross-encoders** take the **(query, document)** pair as input and output a single relevance score. They are more accurate but slower, so we use them on a **small** candidate set (e.g. 20) instead of the whole corpus.  
- Studies report ~28% NDCG improvement and ~35% hallucination reduction when adding a reranking step.

**How it fits:** Insert a **rerank** step between **retrieve** and **grade**. Hybrid search returns many candidates; the cross-encoder (e.g. `ms-marco-MiniLM-L-6-v2` or Cohere Rerank API) picks the best subset before the LLM grades them.

---

### HyDE (Hypothetical Document Embeddings)

**What it is:** Instead of embedding the **user question** for dense search, we first ask the LLM to generate a **hypothetical answer** to that question (a short paragraph as if from a document). We then **embed the hypothetical answer** and use that vector to search the corpus.

**Why it helps:**  
- Dense search usually matches **query** to **documents**. Query and document text are in different “styles” (question vs. statement).  
- With HyDE we match **answer-to-answer**: the hypothetical answer is in the same style as real document chunks, so embedding similarity better reflects “this chunk could have been the source of this answer.”  
- This often improves recall and ranking for dense retrieval.

**How it fits:** Before (or as part of) the expand step, add a **HyDE node** that generates a hypothetical answer, embeds it, and uses that embedding for the dense leg of hybrid search. The rest of the pipeline (sparse, RRF, rerank, grade) stays the same.

---

### Conversation Memory (Summarization)

**What it is:** For long chats, the full message history can exceed the context window and dilute the current question. **Conversation memory** keeps the dialogue manageable by **summarizing** older turns into a short “conversation summary” and keeping only the last N messages verbatim.

**Why it helps:**  
- Prevents context overflow and keeps retrieval queries focused on the **current** intent.  
- Reduces token cost and latency when the model no longer needs every past message in full.  
- The summary can be stored (e.g. in `chat_sessions.session_summary`) and loaded at the start of each turn.

**How it fits:** When history length exceeds a threshold (e.g. >10 messages), run a **summarize_history** step before **analyze_query**. The agent then sees “Summary of earlier conversation: …” plus the last N turns, instead of the full raw history.

---

### RAGAS Evaluation Framework

**What it is:** **RAGAS** (Retrieval-Augmented Generation Assessment) is a framework to **measure** RAG quality using LLM-based metrics, without human-labeled “gold” answers for every question. It uses the **question**, **retrieved context**, and **generated answer** to compute:

- **Faithfulness:** Are the claims in the answer supported by the context? (Reduces hallucination.)
- **Answer Relevancy:** Does the answer address the question?
- **Context Precision:** Is the retrieved context focused on what’s needed (few irrelevant chunks)?
- **Context Recall:** Did we retrieve the chunks that would have been needed to produce a good answer? (Requires a reference answer or assumption.)

**Why it helps:**  
- You can’t improve what you don’t measure. RAGAS gives repeatable scores so you can track regressions after pipeline changes.  
- Run as an **offline evaluation script** on a small test set (e.g. `backend/eval/test_set.json`), not in the live app.

**How it fits:** Add `backend/eval/evaluate.py` that loads question–context–answer triples, runs RAGAS (or similar) metrics, and writes scores to a report. Run manually after changing retrieval, grading, or generation.

---

### Configurable Agent Parameters

**What it is:** Moving **hardcoded** values (e.g. `RETRIEVE_TOP_K`, `MIN_RELEVANT_DOCS`, chunk sizes, model names, RRF k) into a central **config** (e.g. `config.py`) and making them overridable via **environment variables**.

**Why it helps:** Different deployments or experiments need different settings without code changes. Sensible defaults keep the app working out of the box.

**How it fits:** Phase 5E in the plan; not a “RAG concept” but a prerequisite for tuning reranker top-K, HyDE, and other Phase 5 features.

---

## Phase 6 — Production Hardening

### Semantic Caching

**What it is:** Before running the full agent (retrieve → grade → generate), check if we have already answered a **very similar** question. We store recent **(query_embedding, response, sources)** in a cache. For a new query we embed it, compare to cache keys (e.g. **cosine similarity**), and if similarity is above a threshold (e.g. 0.92), **return the cached response** without calling the LLM or retriever.

**Why it helps:**  
- Repeated or near-duplicate questions (e.g. “What is X?” and “Can you explain X?”) get **instant** answers and **large cost savings**.  
- Cache can be in-memory or in DB (e.g. a `query_cache` table with pgvector for query embeddings).  
- When documents are re-processed, relevant cache entries should be **invalidated** so answers stay correct.

**How it fits:** At the very start of the request, after input guardrails: **cache check → hit? return cached; miss? run full agent.** Store the new (embedding, response, sources) after a successful run.

---

### Input/Output Guardrails

**What it is:**  
- **Input guardrails:** Before processing the user message, check for **prompt injection** (attempts to override system instructions), **off-topic** queries, or **PII** in the input. If unsafe, **reject** with a polite message and do not run the agent.  
- **Output guardrails:** Before sending the model’s reply, check for **PII leakage**, **toxic** or policy-violating content. **Redact** or **block** and optionally warn.

**Why it helps:**  
- Protects the system from malicious or abusive use and protects user privacy.  
- Implementation can be rule-based (patterns, blocklists), model-based (small classifier or LLM), or a mix.  
- Integrate once at the edges so all requests pass through the same checks.

**How it fits:** **Input:** call `check_input(text)` before `analyze_query`; if not safe, return a fixed response and do not call the agent. **Output:** after `generate`, call `check_output(text)`; if not safe, return a cleaned/blocked version or a generic message.

---

### User Feedback (Thumbs Up/Down)

**What it is:** Let users mark each assistant message as **helpful** (thumbs up) or **not helpful** (thumbs down). Store this in a **feedback** table (e.g. `message_id`, `session_id`, `rating`, `created_at`).

**Why it helps:**  
- Gives a signal of answer quality without running expensive evaluations.  
- Enables **observability** (e.g. feedback ratio on a dashboard) and, long-term, **evaluation test sets** or **fine-tuning data** (e.g. negative feedback → examples to avoid).

**How it fits:** Frontend shows thumbs up/down after each assistant message; `POST /api/feedback` saves the rating. Phase 6C in the plan.

---

### Observability Dashboard

**What it is:** A **stats** view (backend endpoint + frontend page) that shows aggregate metrics: total chats, messages, documents, average response time, **feedback ratio** (up vs. down), **cache hit rate**, and optionally per-request traces (e.g. Langfuse).

**Why it helps:** You can see whether the system is healthy, whether quality is improving (feedback), and whether caching is effective.

**How it fits:** `GET /api/stats` returns counts and ratios; a **Stats** page in the UI displays them. Optional: integrate a tracing provider for detailed request-level observability.

---

### Graceful Error Recovery / Fallback Pipeline

**What it is:** When a step in the agent **fails** (e.g. OpenAI timeout, reranker down), instead of returning a generic error to the user, **fall back** to a simpler but still working path. Examples:  
- If **grade** fails → keep all retrieved docs and continue to generate.  
- If **hallucination check** fails → skip it and return the answer with a note.  
- If **retrieve** fails → generate with a “no context” prompt so the user still gets a response.

**Why it helps:** Improves **availability** and **user experience** when one component is temporarily failing. The answer may be slightly worse but the system stays usable.

**How it fits:** In `stream.py` (or wherever the agent is orchestrated), wrap critical steps in try/except and define fallback behavior (e.g. skip node, use default, or shorten pipeline).

---

## Phase 7 — Advanced Intelligence

### Multimodal RAG (Tables and Images)

**What it is:** Today, PDFs are often treated as **text only**. **Multimodal RAG** also uses **tables** and **images** from documents:  
- **Tables:** Extract with a table-specific library (e.g. `camelot`, `unstructured` with table strategy), store as chunks with metadata `type: "table"`, and optionally embed table text or structure.  
- **Images:** Extract with `unstructured` or similar, optionally generate **descriptions** with a vision model, store as chunks, and optionally embed image vectors.

**Why it helps:** Many documents (reports, manuals) convey critical information in tables and figures. Text-only RAG misses that, so answers can be incomplete or wrong.

**How it fits:** Extend **document_processor** to detect and extract tables and images, create chunks with appropriate metadata, and store them in the same retrieval pipeline (with type-aware handling if needed). Queries that match table or image chunks can then surface that content to the LLM.

---

### Semantic / Contextual Chunking

**What it is:** Instead of **fixed-size** splitting (e.g. every 500 tokens), **semantic chunking** splits at **topic boundaries**: e.g. compute embedding similarity between consecutive sentences and split where similarity **drops** (new topic). Optionally **prepend contextual headers** (document title, section name) to each chunk so embeddings capture “where” the chunk came from.

**Why it helps:**  
- Fixed-size chunks can cut mid-paragraph or mid-topic, mixing unrelated content.  
- Semantic chunks are more coherent, so retrieval returns more self-contained pieces and the LLM gets clearer context.  
- Contextual headers improve retrieval when users ask about “Section 3” or “the intro.”

**How it fits:** Add a new chunking strategy in **document_processor** (e.g. sentence-level embeddings + similarity threshold), and make it configurable alongside existing parent-child. See also [chunking-strategies.md](chunking-strategies.md) for the current approach.

---

### Web Search Fallback

**What it is:** When the **document grader** concludes that **no** retrieved chunks are relevant (even after query rewriting), instead of always saying “I don’t have the answer in my documents,” optionally **search the web** (e.g. Tavily, SerpAPI, Bing) and generate an answer from web results. The UI should **clearly mark** such answers as “from the web” (e.g. different source badge).

**Why it helps:** Users sometimes ask things outside the uploaded corpus. A web fallback keeps the conversation useful while making the source of the answer transparent.

**How it fits:** Add a **web_search_node** that runs only when graded context is empty (and optionally only when a flag or user preference allows). Pass web snippets as context to the generator and tag the response and sources as web-sourced.

---

### Inline Citations

**What it is:** The model is instructed to add **inline references** in the answer (e.g. `[1]`, `[2]`) that point to specific **source chunks**. The frontend **parses** these markers and turns them into **links** that scroll to or highlight the corresponding source card in the “Sources” section.

**Why it helps:** Users can verify which part of which document supports each claim. This increases trust and makes it easier to correct or extend the knowledge base.

**How it fits:** Update the **generate** prompt to request citation markers; ensure **sources** are ordered and numbered consistently. In the frontend, render `[1]` as a clickable element that scrolls to/highlights Source 1.

---

### Domain Embedding Fine-Tuning

**What it is:** Generic embedding models are trained on broad text. **Fine-tuning** trains (or adapts) an embedding model on **your domain**: e.g. query–passage pairs from **user feedback** (thumbs up = relevant pair, thumbs down = irrelevant). Training uses **contrastive loss** so that relevant pairs are close in vector space and irrelevant pairs are far.

**Why it helps:** Domain-specific language (jargon, product names, internal terms) can be underrepresented in general-purpose embeddings. A fine-tuned model improves **retrieval quality** for your corpus.

**How it fits:** A **script** (e.g. `backend/eval/fine_tune_embeddings.py`) collects feedback and optional manual labels, fine-tunes a sentence-transformer (or similar), and exports the model. **Config** allows switching the embedding model so the app can use the fine-tuned one instead of the default.

---

## Summary Table

| Concept | Phase | One-line summary |
|--------|-------|-------------------|
| Cross-encoder reranking | 5 | Re-score top candidates with a (query, doc) model for better precision. |
| HyDE | 5 | Embed a hypothetical answer instead of the question for better dense retrieval. |
| Conversation memory | 5 | Summarize long history to avoid context overflow and keep queries focused. |
| RAGAS evaluation | 5 | LLM-based metrics (faithfulness, relevancy, precision, recall) to measure RAG quality. |
| Configurable params | 5 | Central config + env vars for all agent and retrieval settings. |
| Semantic caching | 6 | Return cached response when the new query is very similar to a past one. |
| Guardrails | 6 | Input/output checks for injection, PII, toxicity before and after the agent. |
| User feedback | 6 | Thumbs up/down per message; store for analytics and future training. |
| Observability | 6 | Stats endpoint + dashboard (counts, latency, feedback ratio, cache hit rate). |
| Error recovery | 6 | Fallback pipeline when a node fails (e.g. skip grade or hallucination check). |
| Multimodal RAG | 7 | Tables and images from PDFs as first-class chunks. |
| Semantic chunking | 7 | Split at topic boundaries; optional contextual headers. |
| Web search fallback | 7 | When docs have no answer, optionally search the web and mark source. |
| Inline citations | 7 | `[1]`-style references in the answer linked to source cards. |
| Embedding fine-tuning | 7 | Adapt embedding model to your domain using feedback/labels. |

---

## Related

- **Plan:** [.cursor/plans/advanced_rag_phases_d675f94d.plan.md](../../.cursor/plans/advanced_rag_phases_d675f94d.plan.md) — full Phase 5–7 scope and implementation notes.  
- **Current RAG methods:** [../rag-methods-overview.md](../rag-methods-overview.md) — overview of what is already implemented (Phases 1–4).  
- **Existing concept docs:** [embeddings-and-indexes.md](embeddings-and-indexes.md), [hybrid-search.md](hybrid-search.md), [chunking-strategies.md](chunking-strategies.md), [document-grading.md](document-grading.md).
