# Docker and Deployment (Detailed)

## docker-compose.yml

Two services:

- **backend**  
  - Build: `./backend` (Dockerfile).  
  - Port: `8000:8000`.  
  - Env: from `.env` (e.g. `OPENAI_API_KEY`, `DATABASE_URI`).  
  - Volume: `./documents:/app/documents` (ingested files and watcher input).  
  - Restart: unless-stopped.

- **frontend**  
  - Build: `./frontend` (multi-stage: Node build → nginx serve).  
  - Port: `3000:80` (container listens 80).  
  - Depends_on: backend.  
  - Restart: unless-stopped.  
  - No volume for static assets (baked into image).

No explicit network: default network allows frontend to reach backend as `http://backend:8000`.

## Backend Dockerfile

- Base: `python:3.11-slim`.  
- WORKDIR `/app`.  
- `pip install -r requirements.txt`.  
- COPY app code.  
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

## Frontend Dockerfile

- Build stage: `node:20-alpine`, copy package.json, `npm ci`, copy source, `npm run build`.  
- Run stage: `nginx:alpine`, copy built output to `/usr/share/nginx/html`, copy `nginx.conf` to `/etc/nginx/conf.d/default.conf`.  
- No custom CMD (nginx default).

## nginx.conf (Frontend Container)

- Listen 80; root `/usr/share/nginx/html`; `try_files` for SPA.  
- `location /api/`: proxy_pass `http://backend:8000`; headers (Host, X-Real-IP, etc.); `proxy_buffering off`; `proxy_read_timeout` and `proxy_send_timeout` 86400s for long-lived SSE.  
- `client_max_body_size 50M` for uploads.

## .env

- **DATABASE_URI** — Supabase Postgres connection string (include `?sslmode=require`).  
- **OPENAI_API_KEY** — Used for chat and embeddings.  
- Optional: **LANGCHAIN_TRACING_V2**, **LANGCHAIN_API_KEY** for LangSmith.

Copy from `.env.example` and fill values. Do not commit `.env`.

## Running

- From repo root: `docker compose up --build`.  
- Frontend: http://localhost:3000.  
- Backend API: http://localhost:8000; docs at http://localhost:8000/docs.  
- First requests after startup can be slower (cold start, DB pool).

## Development Without Docker

- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload` (set `.env`).  
- Frontend: `cd frontend && npm install && npm run dev` (Vite proxies `/api` to backend; proxy timeout 5 min in vite.config.ts).  
- Ensure `documents/` exists if using watcher.
