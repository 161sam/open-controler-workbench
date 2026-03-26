from __future__ import annotations

from contextlib import contextmanager
from typing import Any


def create_document(name: str = "Controller") -> Any:
    import FreeCAD as App

    return App.newDocument(name)


def supports_document_transactions(doc: Any) -> bool:
    return callable(getattr(doc, "openTransaction", None))


@contextmanager
def document_transaction(doc: Any, label: str):
    opened = _open_document_transaction(doc, label)
    try:
        yield
    except Exception:
        if opened:
            _abort_document_transaction(doc)
        raise
    else:
        if opened:
            _commit_document_transaction(doc)


def _open_document_transaction(doc: Any, label: str) -> bool:
    opener = getattr(doc, "openTransaction", None)
    if not callable(opener):
        return False
    opener(str(label))
    return True


def _commit_document_transaction(doc: Any) -> None:
    committer = getattr(doc, "commitTransaction", None)
    if callable(committer):
        committer()


def _abort_document_transaction(doc: Any) -> None:
    aborter = getattr(doc, "abortTransaction", None)
    if callable(aborter):
        aborter()
