# Quick Start

1. **Clone and env**  
   Copy `.env.example` to `.env`. Set `DATABASE_URI` (Supabase connection string with `?sslmode=require`) and `OPENAI_API_KEY`.

2. **Database**  
   In Supabase SQL Editor, run in order: `sql/supabase_setup.sql`, `sql/supabase_phase2.sql`, `sql/supabase_phase3.sql`, `sql/supabase_phase4.sql`.

3. **Run**  
   From repo root: `docker compose up --build`. Open http://localhost:3000 (frontend). API: http://localhost:8000/docs.

4. **Verify**  
   Create a chat, ask a question. Add files to `documents/` (or use Documents page upload); ask about their content and check Sources under the reply.

See `docs/phase-1-setup.md` through `docs/phase-4-setup.md` for step-by-step setup per phase.
