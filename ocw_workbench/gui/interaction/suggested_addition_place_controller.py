from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ocw_workbench.gui.interaction.lifecycle import ViewEventCallbackRegistry
from ocw_workbench.gui.interaction.view_event_helpers import (
    extract_position,
    get_active_view,
    get_view_point,
    is_escape_event,
    is_left_click_down,
    is_mouse_move,
)
from ocw_workbench.gui.interaction.view_place_controller import map_view_point_to_controller_xy
from ocw_workbench.gui.interaction.view_place_preview import load_preview_state
from ocw_workbench.gui.overlay.renderer import OverlayRenderer
from ocw_workbench.freecad_api.gui import clear_interaction_cursor, set_interaction_cursor
from ocw_workbench.gui.panels._common import log_exception, log_to_console
from ocw_workbench.services.controller_service import ControllerService
from ocw_workbench.services.interaction_service import InteractionService


@dataclass
class SuggestedAdditionPlacementState:
    addition_id: str
    command_id: str
    label: str
    base_components: list[dict[str, Any]]
    preview_components: list[dict[str, Any]]
    anchor_x: float
    anchor_y: float
    target_zone_id: str | None = None

    @property
    def is_active(self) -> bool:
        return bool(self.base_components)


class SuggestedAdditionPlaceController:
    def __init__(
        self,
        controller_service: ControllerService | None = None,
        interaction_service: InteractionService | None = None,
        overlay_renderer: OverlayRenderer | None = None,
        on_status: Any | None = None,
        on_finished: Any | None = None,
        on_committed: Any | None = None,
        view_callbacks: ViewEventCallbackRegistry | None = None,
    ) -> None:
        self.controller_service = controller_service or ControllerService()
        self.interaction_service = interaction_service or InteractionService(self.controller_service)
        self.overlay_renderer = overlay_renderer or OverlayRenderer()
        self.on_status = on_status
        self.on_finished = on_finished
        self.on_committed = on_committed
        self._view_callbacks = view_callbacks or ViewEventCallbackRegistry()
        self.doc: Any | None = None
        self.view: Any | None = None
        self.session: SuggestedAdditionPlacementState | None = None

    def start(self, doc: Any, addition_id: str) -> bool:
        view = self._active_view(doc)
        if view is None:
            self._publish_status("Could not start guided placement because no active 3D view is available.")
            return False
        addition, components = self._resolve_addition(doc, addition_id)
        if not components:
            self._publish_status("Could not start guided placement because the suggested addition has no preview.")
            return False
        anchor_x, anchor_y = _components_anchor(components)
        self.cancel(reason="switch", publish_status=False)
        self.doc = doc
        self.view = view
        self.session = SuggestedAdditionPlacementState(
            addition_id=addition_id,
            command_id=str(addition.get("command_id") or ""),
            label=str(addition.get("label") or addition_id.replace("_", " ").title()),
            base_components=components,
            preview_components=components,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            target_zone_id=str(addition.get("target_zone_id") or "") or None,
        )
        self.interaction_service.begin_interaction(doc, "suggested_addition")
        if not self._view_callbacks.attach(view, self.handle_view_event):
            self.cancel(reason="error", publish_status=False)
            self._publish_status("Interaction error")
            return False
        set_interaction_cursor(view, "place")
        self.interaction_service.add_suggested_addition_preview(
            doc,
            addition_id=self.session.addition_id,
            label=self.session.label,
            components=self.session.base_components,
            target_zone_id=self.session.target_zone_id,
        )
        self.overlay_renderer.refresh(doc)
        self._publish_status(f"Click in the 3D view to place '{self.session.label}'. Press ESC to cancel.")
        return self._view_callbacks.is_registered

    def cancel(self, reason: str = "cancel", publish_status: bool = True) -> None:
        doc = self.doc
        view = self.view
        self._view_callbacks.detach()
        if doc is not None:
            try:
                self.interaction_service.end_interaction(doc)
            except Exception as exc:
                log_exception("Failed to clear suggested addition interaction state", exc)
            try:
                self.interaction_service.clear_component_preview(doc)
            except Exception as exc:
                log_exception("Failed to clear suggested addition preview", exc)
            try:
                self.overlay_renderer.refresh(doc)
            except Exception as exc:
                log_exception("Failed to refresh overlay during suggested addition cleanup", exc)
        self.doc = None
        self.view = None
        self.session = None
        clear_interaction_cursor(view)
        self._notify_finished()
        if publish_status:
            self._publish_status(self._status_for_reason(reason))

    def commit(self) -> dict[str, Any]:
        if self.doc is None or self.session is None:
            raise ValueError("No active suggested addition placement to commit")
        preview = load_preview_state(self.doc)
        if preview is None or not isinstance(preview.get("components"), list):
            raise ValueError("No suggested addition preview available")
        validation = preview.get("validation", {})
        if isinstance(validation, dict) and not bool(validation.get("commit_allowed", True)):
            raise ValueError("Preview position is invalid")
        components = [dict(item) for item in preview.get("components", []) if isinstance(item, dict)]
        label = self.session.label
        try:
            state = self.controller_service.add_components(
                self.doc,
                components,
                primary_id=str(components[0]["id"]) if components else None,
                transaction_name=f"OCW Place Suggested {self.session.addition_id}",
            )
        except Exception as exc:
            self._handle_interaction_error(exc)
            raise
        self._notify_committed(state)
        self.cancel(reason="committed", publish_status=False)
        self._publish_status(f"Placed '{label}'.")
        return state

    def update_preview_from_screen(self, screen_x: float, screen_y: float) -> dict[str, Any] | None:
        if self.doc is None or self.session is None:
            return None
        if not self._ensure_view_binding():
            return None
        point = get_view_point(self.view, screen_x, screen_y)
        if point is None:
            return None
        state = self.controller_service.get_state(self.doc)
        settings = self.interaction_service.get_settings(self.doc)
        x, y = map_view_point_to_controller_xy(
            point,
            controller_width=float(state["controller"]["width"]),
            controller_depth=float(state["controller"]["depth"]),
            snap_enabled=bool(settings.get("snap_enabled", True)),
            grid_mm=float(settings.get("grid_mm", 1.0)),
        )
        translated = _translate_components(
            self.session.base_components,
            target_x=x,
            target_y=y,
            anchor_x=self.session.anchor_x,
            anchor_y=self.session.anchor_y,
        )
        self.session.preview_components = translated
        payload = self.interaction_service.add_suggested_addition_preview(
            self.doc,
            addition_id=self.session.addition_id,
            label=self.session.label,
            components=translated,
            target_zone_id=self.session.target_zone_id,
            grid_mm=float(settings.get("grid_mm", 1.0)),
            snap_enabled=bool(settings.get("snap_enabled", True)),
        )
        self.overlay_renderer.refresh(self.doc)
        return payload

    def handle_view_event(self, info: Any) -> None:
        if self.doc is None or self.session is None:
            return
        try:
            if not self._ensure_view_binding():
                return
            payload = info if isinstance(info, dict) else {}
            event_type = str(payload.get("Type") or payload.get("type") or "")
            if is_escape_event(event_type, payload):
                self.cancel()
                return
            position = extract_position(payload)
            if position is not None and is_mouse_move(event_type, payload):
                self.update_preview_from_screen(float(position[0]), float(position[1]))
                return
            if position is not None and is_left_click_down(event_type, payload):
                preview = self.update_preview_from_screen(float(position[0]), float(position[1]))
                if preview is not None and bool(preview.get("validation", {}).get("commit_allowed", True)):
                    self.commit()
        except Exception as exc:
            self._handle_interaction_error(exc)

    def _resolve_addition(self, doc: Any, addition_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        context = self.controller_service.get_ui_context(doc)
        layout = context.get("layout_intelligence", {}) if isinstance(context, dict) else {}
        additions = layout.get("suggested_additions", []) if isinstance(layout, dict) else []
        addition = next(
            (
                item
                for item in additions
                if isinstance(item, dict) and str(item.get("id") or "") == addition_id
            ),
            None,
        )
        if addition is None:
            raise ValueError(f"Unknown suggested addition: {addition_id}")
        components = self.controller_service.build_suggested_addition(doc, addition_id)
        return addition, components

    def _active_view(self, doc: Any) -> Any | None:
        return get_active_view(doc)

    def _ensure_view_binding(self) -> bool:
        if self.doc is None:
            return False
        view = self._active_view(self.doc)
        if view is None and self.view is not None:
            view = self.view
        if view is None:
            self.cancel(reason="view_unavailable")
            return False
        self.view = view
        if not self._view_callbacks.attach(view, self.handle_view_event):
            self.cancel(reason="error")
            return False
        set_interaction_cursor(view, "place")
        return True

    def _publish_status(self, message: str) -> None:
        log_to_console(message)
        if self.on_status is not None:
            self.on_status(message)

    def _handle_interaction_error(self, exc: Exception) -> None:
        log_exception("Suggested addition placement failed", exc)
        self.cancel(reason="error")

    def _notify_finished(self) -> None:
        if self.on_finished is not None:
            try:
                self.on_finished(self)
            except Exception as exc:
                log_exception("Suggested addition placement finish callback failed", exc)

    def _notify_committed(self, state: dict[str, Any]) -> None:
        if self.on_committed is not None:
            try:
                self.on_committed(state)
            except Exception as exc:
                log_exception("Suggested addition placement commit callback failed", exc)

    def _status_for_reason(self, reason: str) -> str:
        return {
            "cancel": "Guided placement cancelled.",
            "switch": "Guided placement cancelled.",
            "view_unavailable": "Guided placement cancelled because the 3D view is unavailable.",
            "error": "Interaction error",
            "committed": "Guided placement completed.",
        }.get(reason, "Guided placement cancelled.")


def _components_anchor(components: list[dict[str, Any]]) -> tuple[float, float]:
    if not components:
        return (0.0, 0.0)
    xs = [float(component.get("x", 0.0) or 0.0) for component in components if isinstance(component, dict)]
    ys = [float(component.get("y", 0.0) or 0.0) for component in components if isinstance(component, dict)]
    if not xs or not ys:
        return (0.0, 0.0)
    return ((min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5)


def _translate_components(
    components: list[dict[str, Any]],
    *,
    target_x: float,
    target_y: float,
    anchor_x: float,
    anchor_y: float,
) -> list[dict[str, Any]]:
    delta_x = float(target_x) - float(anchor_x)
    delta_y = float(target_y) - float(anchor_y)
    translated: list[dict[str, Any]] = []
    for component in components:
        if not isinstance(component, dict):
            continue
        item = dict(component)
        item["x"] = float(component.get("x", 0.0) or 0.0) + delta_x
        item["y"] = float(component.get("y", 0.0) or 0.0) + delta_y
        translated.append(item)
    return translated
