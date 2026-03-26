from __future__ import annotations

from typing import Any

from ocw_workbench.freecad_api.metadata import clear_document_data, get_document_data, set_document_data

PREVIEW_METADATA_KEY = "OCWDragPreview"


def serialize_preview_state(template_id: str, x: float, y: float, rotation: float = 0.0) -> dict[str, Any]:
    return {
        "template_id": str(template_id),
        "x": float(x),
        "y": float(y),
        "rotation": float(rotation),
    }


def load_preview_state(doc: Any) -> dict[str, Any] | None:
    payload = get_document_data(doc, PREVIEW_METADATA_KEY)
    if not isinstance(payload, dict):
        return None
    template_id = payload.get("template_id")
    if not isinstance(template_id, str) or not template_id:
        return None
    try:
        return serialize_preview_state(
            template_id=template_id,
            x=float(payload.get("x", 0.0)),
            y=float(payload.get("y", 0.0)),
            rotation=float(payload.get("rotation", 0.0)),
        )
    except Exception:
        return None


def store_preview_state(doc: Any, template_id: str, x: float, y: float, rotation: float = 0.0) -> dict[str, Any]:
    payload = serialize_preview_state(template_id=template_id, x=x, y=y, rotation=rotation)
    set_document_data(doc, PREVIEW_METADATA_KEY, payload)
    return payload


def clear_preview_state(doc: Any) -> None:
    clear_document_data(doc, PREVIEW_METADATA_KEY)
