from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ocw_workbench.gui.interaction.hit_test import hit_test_components
from ocw_workbench.gui.interaction.view_place_controller import map_view_point_to_controller_xy
from ocw_workbench.gui.interaction.view_place_preview import load_preview_state
from ocw_workbench.gui.overlay.renderer import OverlayRenderer
from ocw_workbench.gui.panels._common import log_to_console
from ocw_workbench.services.controller_service import ControllerService
from ocw_workbench.services.interaction_service import InteractionService


@dataclass
class DragMoveSession:
    component_id: str
    original_x: float
    original_y: float
    original_rotation: float
    previous_selection: str | None
    dragging: bool = False


class ViewDragController:
    def __init__(
        self,
        controller_service: ControllerService | None = None,
        interaction_service: InteractionService | None = None,
        overlay_renderer: OverlayRenderer | None = None,
        on_status: Any | None = None,
    ) -> None:
        self.controller_service = controller_service or ControllerService()
        self.interaction_service = interaction_service or InteractionService(self.controller_service)
        self.overlay_renderer = overlay_renderer or OverlayRenderer()
        self.on_status = on_status
        self.doc: Any | None = None
        self.view: Any | None = None
        self.armed = False
        self.session: DragMoveSession | None = None
        self._callback_handles: list[tuple[str, Any]] = []

    def start(self, doc: Any) -> bool:
        view = self._active_view(doc)
        if view is None:
            self._publish_status("Could not start drag mode because no active 3D view is available.")
            return False
        self.cancel()
        self.doc = doc
        self.view = view
        self.armed = True
        self._register_callbacks(view)
        self._publish_status("Drag: click component and drag, ESC cancel.")
        return True

    def cancel(self) -> None:
        doc = self.doc
        session = self.session
        if doc is not None:
            self.interaction_service.clear_component_preview(doc)
            if session is not None:
                self.controller_service.select_component(doc, session.previous_selection)
            self.overlay_renderer.refresh(doc)
        self._remove_callbacks()
        self.doc = None
        self.view = None
        self.armed = False
        self.session = None

    def handle_view_event(self, info: Any) -> None:
        if self.doc is None:
            return
        payload = info if isinstance(info, dict) else {}
        event_type = str(payload.get("Type") or payload.get("type") or "")
        if self._is_escape_event(event_type, payload):
            self.cancel()
            self._publish_status("Drag cancelled.")
            return
        position = self._extract_position(payload)
        if position is None:
            return
        screen_x = float(position[0])
        screen_y = float(position[1])
        if self._is_left_click_down(event_type, payload):
            self._begin_drag(screen_x, screen_y)
            return
        if self.session is not None and self.session.dragging and self._is_mouse_move(event_type, payload):
            self.update_preview_from_screen(screen_x, screen_y)
            return
        if self.session is not None and self.session.dragging and self._is_left_click_up(event_type, payload):
            self.update_preview_from_screen(screen_x, screen_y)
            self.commit()

    def _begin_drag(self, screen_x: float, screen_y: float) -> bool:
        if self.doc is None or self.view is None:
            return False
        point = self._view_point(self.view, screen_x, screen_y)
        if point is None:
            return False
        overlay = getattr(self.doc, "OCWOverlayState", None)
        if not isinstance(overlay, dict):
            overlay = self.overlay_renderer.refresh(self.doc)
        component_id = hit_test_components(list(overlay.get("items", [])), x=float(point[0]), y=float(point[1]))
        if component_id is None:
            return False
        component = self.controller_service.get_component(self.doc, component_id)
        previous_selection = self.controller_service.get_ui_context(self.doc).get("selection")
        self.controller_service.select_component(self.doc, component_id)
        self.session = DragMoveSession(
            component_id=component_id,
            original_x=float(component["x"]),
            original_y=float(component["y"]),
            original_rotation=float(component.get("rotation", 0.0) or 0.0),
            previous_selection=previous_selection,
            dragging=True,
        )
        self.interaction_service.move_component_preview(
            self.doc,
            component_id=component_id,
            target_x=float(component["x"]),
            target_y=float(component["y"]),
            rotation=float(component.get("rotation", 0.0) or 0.0),
            grid_mm=float(self.interaction_service.get_settings(self.doc).get("grid_mm", 1.0)),
            snap_enabled=bool(self.interaction_service.get_settings(self.doc).get("snap_enabled", True)),
        )
        self.overlay_renderer.refresh(self.doc)
        self._publish_status(f"Dragging {component_id}... release to commit, ESC to cancel.")
        return True

    def update_preview_from_screen(self, screen_x: float, screen_y: float) -> dict[str, Any] | None:
        if self.doc is None or self.view is None or self.session is None:
            return None
        point = self._view_point(self.view, screen_x, screen_y)
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
        payload = self.interaction_service.move_component_preview(
            self.doc,
            component_id=self.session.component_id,
            target_x=x,
            target_y=y,
            rotation=self.session.original_rotation,
            grid_mm=float(settings.get("grid_mm", 1.0)),
            snap_enabled=bool(settings.get("snap_enabled", True)),
        )
        self.overlay_renderer.refresh(self.doc)
        return payload

    def commit(self) -> dict[str, Any]:
        if self.doc is None or self.session is None:
            raise ValueError("No active drag session to commit")
        preview = load_preview_state(self.doc)
        if preview is None:
            raise ValueError("No drag preview position available")
        component_id = self.session.component_id
        state = self.controller_service.move_component(
            self.doc,
            component_id=component_id,
            x=float(preview["x"]),
            y=float(preview["y"]),
            rotation=self.session.original_rotation,
        )
        self.cancel()
        self._publish_status(f"Moved {component_id} to {preview['x']:.2f}, {preview['y']:.2f} mm.")
        return state

    def _active_view(self, doc: Any) -> Any | None:
        try:
            import FreeCADGui as Gui
        except ImportError:
            return None
        gui_doc = None
        doc_name = getattr(doc, "Name", None)
        if isinstance(doc_name, str) and hasattr(Gui, "getDocument"):
            try:
                gui_doc = Gui.getDocument(doc_name)
            except Exception:
                gui_doc = None
        if gui_doc is None:
            gui_doc = getattr(Gui, "ActiveDocument", None)
        if gui_doc is None or not hasattr(gui_doc, "activeView"):
            return None
        try:
            return gui_doc.activeView()
        except Exception:
            return None

    def _register_callbacks(self, view: Any) -> None:
        callback_types = ("SoMouseButtonEvent", "SoLocation2Event", "SoKeyboardEvent")
        if hasattr(view, "addEventCallback"):
            for event_type in callback_types:
                try:
                    handle = view.addEventCallback(event_type, self.handle_view_event)
                except Exception:
                    continue
                self._callback_handles.append((event_type, handle))
        if not self._callback_handles and hasattr(view, "addEventCallback"):
            try:
                handle = view.addEventCallback("SoEvent", self.handle_view_event)
                self._callback_handles.append(("SoEvent", handle))
            except Exception:
                pass

    def _remove_callbacks(self) -> None:
        view = self.view
        if view is not None and hasattr(view, "removeEventCallback"):
            for event_type, handle in self._callback_handles:
                try:
                    view.removeEventCallback(event_type, handle)
                except Exception:
                    continue
        self._callback_handles = []

    def _view_point(self, view: Any, screen_x: float, screen_y: float) -> tuple[float, float, float] | None:
        if not hasattr(view, "getPoint"):
            return None
        try:
            point = view.getPoint(int(round(screen_x)), int(round(screen_y)))
        except Exception:
            return None
        if isinstance(point, (list, tuple)) and len(point) >= 3:
            return (float(point[0]), float(point[1]), float(point[2]))
        if hasattr(point, "__iter__"):
            values = list(point)
            if len(values) >= 3:
                return (float(values[0]), float(values[1]), float(values[2]))
        return None

    def _extract_position(self, payload: dict[str, Any]) -> tuple[float, float] | None:
        for key in ("Position", "position", "pos"):
            value = payload.get(key)
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                return (float(value[0]), float(value[1]))
        return None

    def _is_mouse_move(self, event_type: str, payload: dict[str, Any]) -> bool:
        state = str(payload.get("State") or payload.get("state") or "")
        return event_type in {"SoLocation2Event", "SoEvent"} and state.lower() != "down"

    def _is_left_click_down(self, event_type: str, payload: dict[str, Any]) -> bool:
        if event_type not in {"SoMouseButtonEvent", "SoEvent"}:
            return False
        button = str(payload.get("Button") or payload.get("button") or "").upper()
        state = str(payload.get("State") or payload.get("state") or "").upper()
        return button in {"BUTTON1", "LEFT"} and state == "DOWN"

    def _is_left_click_up(self, event_type: str, payload: dict[str, Any]) -> bool:
        if event_type not in {"SoMouseButtonEvent", "SoEvent"}:
            return False
        button = str(payload.get("Button") or payload.get("button") or "").upper()
        state = str(payload.get("State") or payload.get("state") or "").upper()
        return button in {"BUTTON1", "LEFT"} and state == "UP"

    def _is_escape_event(self, event_type: str, payload: dict[str, Any]) -> bool:
        if event_type not in {"SoKeyboardEvent", "SoEvent"}:
            return False
        key = str(payload.get("Key") or payload.get("key") or payload.get("Printable") or "").upper()
        state = str(payload.get("State") or payload.get("state") or "").upper()
        return key in {"ESCAPE", "ESC"} and state in {"DOWN", ""}

    def _publish_status(self, message: str) -> None:
        log_to_console(message)
        if self.on_status is not None:
            self.on_status(message)
