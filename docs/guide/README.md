# RAG Docker — Project Guide & Curriculum

This folder contains **22 markdown files** to understand, run, and study the project. Use them as an overview first, then as a detailed curriculum.

---

## Short overviews (read first)

| File | Description |
|------|-------------|
| **00-project-overview.md** | What the project is, one page. |
| **01-architecture-at-a-glance.md** | High-level diagram and components. |
| **02-tech-stack.md** | Technologies used. |
| **03-quick-start.md** | Run and verify in a few steps. |
| **04-common-issues-and-fixes.md** | Frequent problems and quick fixes. |

**RAG methods in one place:** [../rag-methods-overview.md](../rag-methods-overview.md) — overview and summary of all RAG techniques used (chunking, hybrid, RRF, grading, rewriting, hallucination check, etc.).

---

## Detailed curriculum (study in order)

| File | Description |
|------|-------------|
| **05-phased-development-plan.md** | The 4 phases and what each delivers. |
| **06-backend-structure.md** | Backend folders, modules, entry points. |
| **07-frontend-structure.md** | Frontend components, API client, data flow. |
| **08-database-schema.md** | All tables, columns, relationships, migrations. |
| **09-docker-and-deployment.md** | docker-compose, Dockerfiles, nginx, .env. |
| **10-agent-overview.md** | LangGraph agent, state, high-level flow. |
| **11-agent-nodes-deep-dive.md** | Each node (analyze, grade, generate, etc.). |
| **12-retrieval-pipeline.md** | Hybrid search, RRF, parent-child, tuning. |
| **13-document-processing.md** | How files become chunks and embeddings. |
| **14-api-reference.md** | All endpoints, request/response, streaming. |
| **15-streaming-and-sse.md** | How chat streaming works end-to-end. |
| **16-errors-and-solutions.md** | Errors encountered and their fixes. |
| **17-frontend-state-and-ux.md** | App/Sidebar/ChatInterface state and UX. |
| **18-supabase-and-migrations.md** | Supabase setup and SQL migration order. |
| **19-testing-and-verification.md** | How to verify each phase manually. |
| **20-glossary-and-file-index.md** | Terms and where to find what in the repo. |
| **21-design-decisions-and-tradeoffs.md** | Why we made key design choices. |

---

## Related docs (outside this folder)

- **RAG methods overview:** `../rag-methods-overview.md` — summary of all RAG methods used in the project
- **Setup (per phase):** `../phase-1-setup.md` … `../phase-4-setup.md`
- **Concepts (theory):** `../concepts/embeddings-and-indexes.md`, `hybrid-search.md`, `chunking-strategies.md`, `multi-query-retrieval.md`, `document-grading.md`
- **Advanced plan concepts (Phases 5–7):** `../concepts/advanced-rag-plan-concepts.md` — reranking, HyDE, RAGAS, caching, guardrails, multimodal, citations, etc.
