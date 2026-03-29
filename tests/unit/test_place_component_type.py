from __future__ import annotations

import sys
import types

import pytest

from ocw_workbench.commands.place_component_type import (
    PlaceComponentTypeCommand,
    component_toolbar_command_ids,
    iter_component_type_command_specs,
    _TYPE_DEFAULTS,
    _TYPE_ICONS,
    _TYPE_LABELS,
)
from ocw_workbench.gui.interaction.view_place_preview import load_preview_state
from ocw_workbench.services.controller_service import ControllerService
from ocw_workbench.services.interaction_service import InteractionService

_ALL_TYPES = ("button", "encoder", "fader", "pad", "display", "rgb_button")


# ---------------------------------------------------------------------------
# Registry completeness
# ---------------------------------------------------------------------------

def test_all_types_have_defaults() -> None:
    for ctype in _ALL_TYPES:
        assert ctype in _TYPE_DEFAULTS, f"No default for {ctype}"
        assert _TYPE_DEFAULTS[ctype], f"Empty default for {ctype}"


def test_all_types_have_icons() -> None:
    for ctype in _ALL_TYPES:
        assert ctype in _TYPE_ICONS, f"No icon for {ctype}"
        assert _TYPE_ICONS[ctype].endswith(".svg"), f"Icon not svg for {ctype}"


def test_all_types_have_labels() -> None:
    for ctype in _ALL_TYPES:
        assert ctype in _TYPE_LABELS, f"No label for {ctype}"
        assert _TYPE_LABELS[ctype], f"Empty label for {ctype}"


# ---------------------------------------------------------------------------
# Command construction
# ---------------------------------------------------------------------------

def test_command_stores_type_and_default_ref() -> None:
    cmd = PlaceComponentTypeCommand("button")
    assert cmd.component_type == "button"
    assert cmd.default_library_ref == _TYPE_DEFAULTS["button"]


def test_command_unknown_type_falls_back_to_type_string() -> None:
    cmd = PlaceComponentTypeCommand("mystery_widget")
    assert cmd.default_library_ref == "mystery_widget"


def test_component_toolbar_command_ids_follow_spec_order() -> None:
    assert component_toolbar_command_ids() == [spec.command_id for spec in iter_component_type_command_specs()]


# ---------------------------------------------------------------------------
# GetResources
# ---------------------------------------------------------------------------

def test_get_resources_has_required_keys() -> None:
    for ctype in _ALL_TYPES:
        cmd = PlaceComponentTypeCommand(ctype)
        res = cmd.GetResources()
        assert "MenuText" in res
        assert "ToolTip" in res
        assert "Pixmap" in res


def test_get_resources_menu_text_contains_label() -> None:
    for ctype in _ALL_TYPES:
        cmd = PlaceComponentTypeCommand(ctype)
        res = cmd.GetResources()
        label = _TYPE_LABELS[ctype]
        assert label in res["MenuText"], f"{ctype}: label '{label}' not in '{res['MenuText']}'"


def test_get_resources_tooltip_references_label() -> None:
    for ctype in _ALL_TYPES:
        cmd = PlaceComponentTypeCommand(ctype)
        res = cmd.GetResources()
        label = _TYPE_LABELS[ctype]
        assert label in res["ToolTip"], f"{ctype}: label '{label}' not in '{res['ToolTip']}'"


# ---------------------------------------------------------------------------
# IsActive: no dock required — only _has_controller()
# ---------------------------------------------------------------------------

def test_is_active_false_without_controller(monkeypatch) -> None:
    cmd = PlaceComponentTypeCommand("button")
    monkeypatch.setattr(cmd, "_has_controller", lambda: False)
    assert cmd.IsActive() is False


def test_is_active_true_with_controller(monkeypatch) -> None:
    cmd = PlaceComponentTypeCommand("encoder")
    monkeypatch.setattr(cmd, "_has_controller", lambda: True)
    assert cmd.IsActive() is True


# ---------------------------------------------------------------------------
# Activated: calls start_place_mode_direct with correct template_id
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_freecad_env():
    """Inject fake FreeCAD and ocw_workbench.workbench into sys.modules."""
    fake_doc = object()

    fake_app = types.ModuleType("FreeCAD")
    fake_app.ActiveDocument = fake_doc

    fake_wb = types.ModuleType("ocw_workbench.workbench")
    calls: list[tuple] = []

    def fake_start(doc, template_id):
        calls.append((doc, template_id))
        return True

    fake_wb.start_place_mode_direct = fake_start

    orig_app = sys.modules.get("FreeCAD")
    orig_wb = sys.modules.get("ocw_workbench.workbench")
    sys.modules["FreeCAD"] = fake_app
    sys.modules["ocw_workbench.workbench"] = fake_wb

    yield fake_doc, calls

    # Restore
    if orig_app is None:
        sys.modules.pop("FreeCAD", None)
    else:
        sys.modules["FreeCAD"] = orig_app
    if orig_wb is None:
        sys.modules.pop("ocw_workbench.workbench", None)
    else:
        sys.modules["ocw_workbench.workbench"] = orig_wb


def test_activated_calls_start_place_mode_direct(fake_freecad_env) -> None:
    fake_doc, calls = fake_freecad_env
    cmd = PlaceComponentTypeCommand("fader")
    cmd.Activated()
    assert len(calls) == 1
    assert calls[0][0] is fake_doc
    assert calls[0][1] == _TYPE_DEFAULTS["fader"]


def test_activated_uses_correct_default_per_type(fake_freecad_env) -> None:
    _, calls = fake_freecad_env
    for ctype in _ALL_TYPES:
        calls.clear()
        cmd = PlaceComponentTypeCommand(ctype)
        cmd.Activated()
        assert calls, f"No call for {ctype}"
        assert calls[0][1] == _TYPE_DEFAULTS[ctype], f"{ctype}: wrong template_id"


def test_activated_does_not_call_ensure_workbench_ui(fake_freecad_env) -> None:
    ensure_called: list[bool] = []
    fake_doc, _ = fake_freecad_env
    sys.modules["ocw_workbench.workbench"].ensure_workbench_ui = (  # type: ignore[attr-defined]
        lambda *a, **kw: ensure_called.append(True)
    )

    cmd = PlaceComponentTypeCommand("pad")
    cmd.Activated()
    assert not ensure_called, "ensure_workbench_ui must NOT be called by PlaceComponentTypeCommand"


def test_activated_sets_active_template_before_start(fake_freecad_env, monkeypatch) -> None:
    fake_doc, calls = fake_freecad_env
    template_calls: list[tuple[object, str]] = []

    class FakeInteractionService:
        def __init__(self, controller_service=None) -> None:
            pass

        def set_active_component_template(self, doc, template_id):
            template_calls.append((doc, template_id))
            return {"active_component_template_id": template_id}

    monkeypatch.setattr(
        "ocw_workbench.commands.place_component_type.InteractionService",
        FakeInteractionService,
    )

    cmd = PlaceComponentTypeCommand("display")
    cmd.Activated()

    assert template_calls == [(fake_doc, _TYPE_DEFAULTS["display"])]
    assert calls == [(fake_doc, _TYPE_DEFAULTS["display"])]


def test_activated_reports_start_failure_without_silence(fake_freecad_env, monkeypatch) -> None:
    _, calls = fake_freecad_env
    errors: list[tuple[str, str]] = []

    sys.modules["ocw_workbench.workbench"].start_place_mode_direct = (  # type: ignore[attr-defined]
        lambda doc, template_id: calls.append((doc, template_id)) or False
    )
    monkeypatch.setattr(
        "ocw_workbench.commands.place_component_type.show_error",
        lambda title, exc: errors.append((title, str(exc))),
    )

    cmd = PlaceComponentTypeCommand("button")
    cmd.Activated()

    assert calls and calls[0][1] == _TYPE_DEFAULTS["button"]
    assert errors == [("Place Button", "Could not start 3D placement mode")]


class FakeInteractiveDocument:
    def __init__(self, name: str = "Controller") -> None:
        self.Name = name
        self.Objects = []
        self.transactions: list[tuple[str, object | None]] = []

    def recompute(self) -> None:
        pass

    def openTransaction(self, label: str) -> None:
        self.transactions.append(("open", label))

    def commitTransaction(self) -> None:
        self.transactions.append(("commit", None))

    def abortTransaction(self) -> None:
        self.transactions.append(("abort", None))


class FakeView:
    def __init__(self) -> None:
        self.callbacks = []

    def addEventCallback(self, event_type, callback):
        handle = (event_type, callback, len(self.callbacks))
        self.callbacks.append(handle)
        return handle

    def removeEventCallback(self, event_type, handle):
        self.callbacks = [item for item in self.callbacks if item != handle]

    def getPoint(self, x, y):
        return (float(x), float(y), 0.0)


@pytest.fixture()
def live_type_command_env(monkeypatch):
    from ocw_workbench import workbench as workbench_module
    import ocw_workbench.commands.place_component_type as command_module

    doc = FakeInteractiveDocument()
    controller_service = ControllerService()
    controller_service.create_controller(doc, {"id": "demo", "width": 100.0, "depth": 80.0, "height": 30.0})
    view = FakeView()
    fake_app = types.ModuleType("FreeCAD")
    fake_app.ActiveDocument = doc
    previous_app = sys.modules.get("FreeCAD")
    sys.modules["FreeCAD"] = fake_app

    monkeypatch.setattr(
        "ocw_workbench.gui.interaction.view_place_controller.get_active_view",
        lambda current_doc: view if current_doc is doc else None,
    )
    monkeypatch.setattr(command_module, "show_info", lambda title, message: None)
    monkeypatch.setattr(command_module, "show_error", lambda title, exc: (_ for _ in ()).throw(exc))
    monkeypatch.setattr(workbench_module, "_ACTIVE_WORKBENCH", None)
    monkeypatch.setattr(workbench_module, "_STANDALONE_PLACE_CONTROLLER", None)
    monkeypatch.setattr(workbench_module, "_STANDALONE_DRAG_CONTROLLER", None)

    yield doc, view, workbench_module, controller_service

    workbench_module._cancel_standalone_direct_interactions(reason="cancel", publish_status=False)
    if previous_app is None:
        sys.modules.pop("FreeCAD", None)
    else:
        sys.modules["FreeCAD"] = previous_app


def test_type_command_starts_direct_placement_and_commit_selects_new_component(live_type_command_env) -> None:
    doc, _view, workbench_module, controller_service = live_type_command_env

    PlaceComponentTypeCommand("encoder").Activated()

    controller = workbench_module._STANDALONE_PLACE_CONTROLLER
    settings = InteractionService(controller_service).get_settings(doc)

    assert controller is not None
    assert settings["active_interaction"] == "place"
    assert settings["active_component_template_id"] == _TYPE_DEFAULTS["encoder"]

    preview = controller.update_preview_from_screen(28.0, 24.0)
    assert preview is not None
    controller.commit()

    state = controller_service.get_state(doc)
    selection = controller_service.get_ui_context(doc)["selection"]

    assert len(state["components"]) == 1
    assert state["components"][0]["library_ref"] == _TYPE_DEFAULTS["encoder"]
    assert selection == state["components"][0]["id"]
    assert InteractionService(controller_service).get_settings(doc)["active_interaction"] == "place"


def test_type_command_cancel_clears_preview_and_leaves_no_zombie_mode(live_type_command_env) -> None:
    doc, view, workbench_module, controller_service = live_type_command_env

    PlaceComponentTypeCommand("pad").Activated()

    controller = workbench_module._STANDALONE_PLACE_CONTROLLER
    assert controller is not None
    controller.update_preview_from_screen(12.0, 18.0)
    assert load_preview_state(doc) is not None

    controller.handle_view_event({"Type": "SoKeyboardEvent", "State": "DOWN", "Key": "ESCAPE"})

    settings = InteractionService(controller_service).get_settings(doc)
    assert load_preview_state(doc) is None
    assert settings["active_interaction"] is None
    assert workbench_module._STANDALONE_PLACE_CONTROLLER is None
    assert len(view.callbacks) == 0
