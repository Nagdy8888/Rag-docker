"""Watchdog-based folder monitor for documents/ — triggers processing on create/modify, removal on delete."""

import logging
import threading
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent
from watchdog.observers import Observer

from app.config import get_settings
from app.document_processor import process_file, remove_file_by_path, SUPPORTED_EXTENSIONS
from app.retriever import get_embeddings

logger = logging.getLogger(__name__)


class DocumentsHandler(FileSystemEventHandler):
    """Handle file create/modify/delete in the watched documents folder."""

    def __init__(self, documents_path: Path):
        self.documents_path = Path(documents_path).resolve()
        self._embeddings = None
        self._seen_hashes: dict[str, str] = {}  # path -> hash, to avoid duplicate work on quick re-saves

    def _get_embeddings(self):
        if self._embeddings is None:
            self._embeddings = get_embeddings()
        return self._embeddings

    def _process(self, src_path: str) -> None:
        path = Path(src_path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return
        try:
            process_file(path, self._get_embeddings())
            logger.info("Processed %s", path.name)
        except Exception as e:
            logger.exception("Processing failed for %s: %s", path, e)

    def on_created(self, event):
        if event.is_directory:
            return
        self._process(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._process(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        try:
            remove_file_by_path(Path(event.src_path))
            logger.info("Removed chunks for deleted file %s", event.src_path)
        except Exception as e:
            logger.exception("Remove failed for %s: %s", event.src_path, e)


_observer: Observer | None = None
_watcher_thread: threading.Thread | None = None


def start_watcher() -> None:
    """Start the documents folder watcher in a background thread."""
    global _observer, _watcher_thread
    settings = get_settings()
    path = Path(settings.documents_path).resolve()
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info("Created documents directory: %s", path)
    handler = DocumentsHandler(path)
    _observer = Observer()
    _observer.schedule(handler, str(path), recursive=False)
    _observer.start()
    logger.info("Watching documents folder: %s", path)
    # Process any files already in the folder (watcher only sees events after start)
    for f in path.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                process_file(f, handler._get_embeddings())
                logger.info("Processed existing file %s", f.name)
            except Exception as e:
                logger.exception("Startup processing failed for %s: %s", f, e)


def stop_watcher() -> None:
    """Stop the watcher (e.g. on app shutdown)."""
    global _observer
    if _observer:
        _observer.stop()
        _observer.join(timeout=5)
        _observer = None
        logger.info("Documents watcher stopped")
