# Project Overview

**RAG Docker** is a full-stack **Retrieval-Augmented Generation (RAG)** chatbot: you add documents to a folder, the system indexes them with embeddings and full-text search, and the chat answers questions using only those documents.

- **Backend:** Python (FastAPI), LangGraph agent, Supabase/PostgreSQL, hybrid search (vector + full-text).
- **Frontend:** React + TypeScript + Vite, dark UI with chat and Documents page.
- **Run:** Docker Compose (backend + frontend); Supabase holds chats and document chunks.

Built in **4 phases**: simple chat → document RAG → hybrid retrieval → intelligent agent (grading, rewriting, hallucination check, source refs).
