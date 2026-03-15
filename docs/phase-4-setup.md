# Phase 4 Setup Guide — Intelligent Agent (Grading, Rewriting, Hallucination Check)

This guide upgrades the RAG agent from a simple retrieve→generate pipeline to an **intelligent 7-node graph**: query analysis, multi-query expansion, hybrid retrieval, **document grading**, optional **query rewriting**, generation, and **hallucination check**. The frontend shows **source references** below assistant messages.

---

## Prerequisites

- **Phases 1–3** must be complete: chat tables, documents + hybrid search (Phase 2 and 3 SQL run). You should have run `sql/supabase_setup.sql`, `sql/supabase_phase2.sql`, and `sql/supabase_phase3.sql`.
- Same Supabase project, OpenAI key, and (optional) LangSmith for tracing.

---

## Step 1: Run the Phase 4 SQL migration

1. In Supabase, open **SQL Editor** → **New query**.
2. Open **`sql/supabase_phase4.sql`** from this project and copy its full contents into the editor.
3. Click **Run**. You should see “Success. No rows returned.”

This migration:

- Adds a **`sources`** (JSONB) column to `chat_messages` to store which document chunks were used for each assistant reply.
- Optionally creates a GIN index on `sources` for queries that filter by presence of sources.

---

## Step 2: Environment variables

No new required variables. Ensure `.env` has:

- `OPENAI_API_KEY`
- `DATABASE_URI` (Supabase Postgres)

---

## Step 3: Rebuild and run

From the project root:

```bash
docker compose up --build
```

The backend and frontend will use the Phase 4 agent and source references.

---

## Step 4: Verify the intelligent agent

1. **Chat**
   - Ask a **factual question** (e.g. from your documents). You should see status steps such as:
     - “Analyzing question…”
     - “Expanding query…”
     - “Searching documents…”
     - “Grading relevance…”
     - “Generating answer…”
     - “Verifying answer…”
   - Ask a **conversational** message (e.g. “Hi” or “Thanks”). You should see “Analyzing question…” then “Generating answer…” without retrieval steps.
   - Below assistant messages that used documents, a collapsible **“Sources (N)”** section appears; expand it to see filename, chunk, and snippet.

2. **Source references**
   - After a reply that used documents, click **“Sources (N)”** to expand. Each source shows filename, chunk index, and a short snippet with an indigo left border.

3. **LangSmith** (if configured)
   - Traces will show the multi-step agent; you can inspect each node (analyze, expand, retrieve, grade, rewrite, generate, hallucination check).

---

## How the agent works (brief)

- **analyze_query**: Classifies the user message as needing retrieval (factual) or conversational (greeting, thanks, etc.). Conversational messages skip retrieval and use a short friendly reply.
- **expand_query**: Prepares the query for multi-query expansion (the retriever still generates 3 variants internally).
- **hybrid_retrieve**: Calls the Phase 3 hybrid retriever (dense + sparse, RRF, parent chunks).
- **grade_documents**: The LLM grades each retrieved chunk as relevant or irrelevant; only relevant chunks form the context for the answer.
- **rewrite_query** (conditional): If too few chunks are relevant and the rewrite count is below the limit (1), the question is rephrased and retrieval + grading run again.
- **generate**: Produces the answer from the graded context (or a “no documents” / conversational prompt).
- **check_hallucination**: The LLM checks whether the answer is grounded in the context. If “not_grounded”, the agent can retry generation once.

Source references (filename, chunk index, snippet) are built from the **graded** chunks and sent in the stream; the frontend displays them and they are stored in `chat_messages.sources`.

---

## Troubleshooting

| Issue | What to do |
|--------|------------|
| **“column sources does not exist”** | Run `sql/supabase_phase4.sql` in the Supabase SQL Editor. |
| **No “Sources” below messages** | Ensure the Phase 4 migration ran and the backend was rebuilt. Reload the chat; new replies will have sources. |
| **Status stays on “Grading relevance…”** | Check backend logs; grading uses the same OpenAI key. Increase timeout if needed. |
| **Answers still wrong or hallucinated** | Hallucination check runs after generate; at most one retry. Check LangSmith for the “check_hallucination” and “generate” steps. |

---

## Performance notes

- Each user message can trigger several LLM calls: analyze, (expand), (grade), (rewrite), generate, (hallucination check). Expect higher latency and token usage than Phase 2/3.
- Grading and hallucination use `gpt-4o-mini` by default; you can change the model in `app/agent/llm.py` or add a separate grading model in config.
