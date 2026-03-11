"""FastAPI application - chat endpoints and SSE streaming."""

import json
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from sse_starlette.sse import EventSourceResponse

from app.agent import stream_chat_response, generate_title
from app.schemas import ChatSessionResponse, ChatMessageResponse, ChatSessionWithMessages
from app.database import (
    list_sessions,
    get_session,
    get_messages,
    create_session,
    delete_session,
    insert_message,
    update_session_title,
    list_files,
    get_connection,
)
from sqlalchemy import text
from app.watcher import start_watcher, stop_watcher
from app.config import get_settings
from app.document_processor import (
    process_file,
    SUPPORTED_EXTENSIONS,
    MAX_FILE_BYTES,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start documents watcher on startup, stop on shutdown."""
    start_watcher()
    yield
    stop_watcher()


app = FastAPI(title="RAG Chat API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _session_from_row(row: dict) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=row["id"],
        title=row["title"] or "New Chat",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _message_from_row(row: dict) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=row["id"],
        session_id=row["session_id"],
        role=row["role"],
        content=row["content"] or "",
        created_at=row["created_at"],
    )


@app.get("/api/chats", response_model=list[ChatSessionResponse])
def list_chats():
    """List all chat sessions, newest first."""
    rows = list_sessions()
    return [_session_from_row(row) for row in rows]


@app.get("/api/chats/{session_id}", response_model=ChatSessionWithMessages)
def get_chat(session_id: UUID):
    """Get a chat session with all its messages."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Chat not found")
    msgs = get_messages(session_id)
    return ChatSessionWithMessages(
        **_session_from_row(sess).model_dump(),
        messages=[_message_from_row(m) for m in msgs],
    )


@app.post("/api/chats", response_model=ChatSessionResponse)
def create_chat():
    """Create a new chat session."""
    row = create_session()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create chat")
    return _session_from_row(row)


@app.delete("/api/chats/{session_id}", status_code=204)
def delete_chat(session_id: UUID):
    """Delete a chat session and its messages."""
    delete_session(session_id)
    return None


# --- Documents (Phase 2) ---
class DocumentFileResponse(BaseModel):
    """Processed file metadata for the documents list."""

    id: UUID
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    error_message: str | None = None
    created_at: str  # ISO from DB

    class Config:
        from_attributes = True


def _file_from_row(row: dict) -> DocumentFileResponse:
    return DocumentFileResponse(
        id=row["id"],
        filename=row["filename"] or "",
        file_type=row["file_type"] or "",
        file_size=int(row["file_size"] or 0),
        chunk_count=int(row["chunk_count"] or 0),
        status=row["status"] or "processing",
        error_message=row.get("error_message") or None,
        created_at=row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
    )


@app.get("/api/documents", response_model=list[DocumentFileResponse])
def get_documents():
    """List all processed documents (files) with status and chunk count."""
    try:
        rows = list_files()
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("list_files failed (Phase 2 tables may be missing): %s", e)
        return []
    return [_file_from_row(row) for row in rows]


@app.get("/api/documents/status")
def get_documents_status():
    """
    Diagnostic: folder path, files seen on disk, and whether Phase 2 DB tables exist.
    """
    from pathlib import Path
    from app.config import get_settings
    from app.document_processor import SUPPORTED_EXTENSIONS
    from sqlalchemy import text
    from app.database import get_connection

    path = Path(get_settings().documents_path).resolve()
    files_on_disk = []
    if path.exists():
        for f in path.iterdir():
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                files_on_disk.append(f.name)

    tables_ok = False
    db_error = None
    try:
        with get_connection() as conn:
            conn.execute(text("SELECT 1 FROM files LIMIT 1"))
            tables_ok = True
    except Exception as e:
        db_error = str(e)

    return {
        "documents_folder": str(path),
        "folder_exists": path.exists(),
        "files_on_disk": files_on_disk,
        "files_count": len(files_on_disk),
        "phase2_tables_ok": tables_ok,
        "db_error": db_error,
    }


@app.get("/api/documents/test-retrieval")
def test_retrieval(q: str = "propylene"):
    """
    Test if retrieval works: run a quick search and return chunk count + short preview.
    Use ?q=your_query to try different queries.
    """
    from app.retriever import retrieve
    try:
        docs = retrieve(q, top_k=5)
        previews = [d.page_content[:200] + "..." if len(d.page_content) > 200 else d.page_content for d in docs]
        return {"query": q, "chunk_count": len(docs), "previews": previews}
    except Exception as e:
        return {"query": q, "chunk_count": 0, "error": str(e), "previews": []}


class UploadResultItem(BaseModel):
    """Result for one uploaded file."""
    filename: str
    success: bool
    file_id: str | None = None
    status: str | None = None  # ready | processing | error
    error: str | None = None


class UploadResponse(BaseModel):
    """Response after uploading documents."""
    results: list[UploadResultItem]


@app.post("/api/documents/upload", response_model=UploadResponse)
async def upload_documents(files: list[UploadFile] = File(..., description="Files to upload")):
    """
    Upload documents: save to the documents/ folder and process (chunk, embed, store in Supabase).
    Supported: PDF, DOCX, TXT, CSV, XLSX, XLS, MD. Max 10 MB per file.
    """
    from pathlib import Path
    from langchain_openai import OpenAIEmbeddings

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    docs_path = Path(get_settings().documents_path).resolve()
    docs_path.mkdir(parents=True, exist_ok=True)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    results: list[UploadResultItem] = []

    for upload in files:
        filename = (upload.filename or "").strip() or "unnamed"
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            results.append(UploadResultItem(
                filename=filename,
                success=False,
                error=f"Unsupported type. Use: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            ))
            continue
        dest = docs_path / filename
        try:
            content = await upload.read()
            if len(content) > MAX_FILE_BYTES:
                results.append(UploadResultItem(
                    filename=filename,
                    success=False,
                    error=f"File too large (max {MAX_FILE_BYTES // (1024*1024)} MB)",
                ))
                continue
            dest.write_bytes(content)
        except Exception as e:
            results.append(UploadResultItem(filename=filename, success=False, error=str(e)))
            continue

        try:
            file_id, chunk_count, status = process_file(dest, embeddings)
            error_detail = None
            if status == "error" and file_id:
                try:
                    with get_connection() as conn:
                        r = conn.execute(
                            text("SELECT error_message FROM files WHERE id = :id"),
                            {"id": str(file_id)},
                        )
                        row = r.fetchone()
                        if row and row[0]:
                            error_detail = str(row[0])[:500]
                except Exception:
                    pass
            results.append(UploadResultItem(
                filename=filename,
                success=status == "ready",
                file_id=str(file_id) if file_id else None,
                status=status,
                error=error_detail or (None if status == "ready" else "Processing failed"),
            ))
        except Exception as e:
            results.append(UploadResultItem(filename=filename, success=False, error=str(e)))

    return UploadResponse(results=results)


class ChatSendBody(BaseModel):
    session_id: UUID
    content: str


@app.post("/api/chat")
def chat_stream(body: ChatSendBody = Body(...)):
    """
    Send a message and stream the assistant response via SSE.
    Events: { "type": "status" | "token" | "done", "content": "..." }
    """
    session_id = body.session_id
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content required")

    # Ensure session exists
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Load history
    msgs_list = get_messages(session_id)
    history = [
        HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
        for m in msgs_list
    ]
    history.append(HumanMessage(content=content))

    # Save user message
    insert_message(session_id, "user", content)

    is_new_session = len(history) == 1

    async def event_generator():
        full_reply = []
        try:
            async for event_type, event_content in stream_chat_response(history):
                yield {
                    "event": "message",
                    "data": json.dumps({"type": event_type, "content": event_content}),
                }
                if event_type == "token":
                    full_reply.append(event_content)
        finally:
            reply_text = "".join(full_reply)
            # Save assistant message
            insert_message(session_id, "assistant", reply_text)
            # Session updated_at is set by DB trigger on message insert
            # Background: generate title for new sessions
            if is_new_session and reply_text:
                try:
                    title = generate_title([HumanMessage(content=content), AIMessage(content=reply_text)])
                    update_session_title(session_id, title)
                except Exception:
                    pass

    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
