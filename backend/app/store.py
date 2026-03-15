from __future__ import annotations

from threading import Lock

from app.schemas import DocumentRecord


class InMemoryDocumentStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._documents: dict[str, DocumentRecord] = {}

    def save(self, record: DocumentRecord) -> None:
        with self._lock:
            self._documents[record.document_id] = record

    def get(self, document_id: str) -> DocumentRecord | None:
        with self._lock:
            return self._documents.get(document_id)


store = InMemoryDocumentStore()
