from __future__ import annotations

from typing import Any

from ocw_workbench.freecad_api.metadata import clear_document_data, get_document_data, set_document_data

PREVIEW_METADATA_KEY = "OCWDragPreview"


def serialize_preview_state(
    *,
    x: float,
    y: float,
    rotation: float = 0.0,
    mode: str = "place",
    template_id: str | None = None,
    component_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "x": float(x),
        "y": float(y),
        "rotation": float(rotation),
        "mode": str(mode or "place"),
    }
    if template_id is not None:
        payload["template_id"] = str(template_id)
    if component_id is not None:
        payload["component_id"] = str(component_id)
    return payload


def load_preview_state(doc: Any) -> dict[str, Any] | None:
    payload = get_document_data(doc, PREVIEW_METADATA_KEY)
    if not isinstance(payload, dict):
        return None
    template_id = payload.get("template_id")
    component_id = payload.get("component_id")
    if not isinstance(template_id, str) and not isinstance(component_id, str):
        return None
    try:
        return serialize_preview_state(
            x=float(payload.get("x", 0.0)),
            y=float(payload.get("y", 0.0)),
            rotation=float(payload.get("rotation", 0.0)),
            mode=str(payload.get("mode") or "place"),
            template_id=template_id if isinstance(template_id, str) and template_id else None,
            component_id=component_id if isinstance(component_id, str) and component_id else None,
        )
    except Exception:
        return None


def store_preview_state(
    doc: Any,
    template_id: str | None = None,
    *,
    x: float,
    y: float,
    rotation: float = 0.0,
    mode: str = "place",
    component_id: str | None = None,
) -> dict[str, Any]:
    payload = serialize_preview_state(
        x=x,
        y=y,
        rotation=rotation,
        mode=mode,
        template_id=template_id,
        component_id=component_id,
    )
    set_document_data(doc, PREVIEW_METADATA_KEY, payload)
    return payload


def clear_preview_state(doc: Any) -> None:
    clear_document_data(doc, PREVIEW_METADATA_KEY)
