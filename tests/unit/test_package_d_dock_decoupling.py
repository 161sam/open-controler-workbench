from __future__ import annotations

import sys
import types


def _make_fake_freecad(doc=None):
    fake_app = types.ModuleType("FreeCAD")
    fake_app.ActiveDocument = doc or object()
    fake_app.newDocument = lambda name="Controller": doc or object()
    return fake_app


def _install_mocks(fake_app, fake_wb, fake_runtime):
    orig_app = sys.modules.get("FreeCAD")
    orig_wb = sys.modules.get("ocw_workbench.workbench")
    orig_runtime = sys.modules.get("ocw_workbench.gui.runtime")
    sys.modules["FreeCAD"] = fake_app
    sys.modules["ocw_workbench.workbench"] = fake_wb
    sys.modules["ocw_workbench.gui.runtime"] = fake_runtime
    return orig_app, orig_wb, orig_runtime


def _restore_mocks(orig_app, orig_wb, orig_runtime):
    if orig_app is None:
        sys.modules.pop("FreeCAD", None)
    else:
        sys.modules["FreeCAD"] = orig_app
    if orig_wb is None:
        sys.modules.pop("ocw_workbench.workbench", None)
    else:
        sys.modules["ocw_workbench.workbench"] = orig_wb
    if orig_runtime is None:
        sys.modules.pop("ocw_workbench.gui.runtime", None)
    else:
        sys.modules["ocw_workbench.gui.runtime"] = orig_runtime


class FakeDocument:
    Objects: list[object] = []

    def recompute(self) -> None:
        pass


def test_reload_plugins_uses_direct_helper_without_workbench() -> None:
    doc = FakeDocument()
    ensure_called: list[bool] = []
    reload_calls: list[object] = []
    info_calls: list[tuple[str, str]] = []

    fake_app = _make_fake_freecad(doc)
    fake_wb = types.ModuleType("ocw_workbench.workbench")
    fake_wb.ensure_workbench_ui = lambda *a, **kw: ensure_called.append(True)
    fake_wb.reload_plugins_direct = lambda current_doc: reload_calls.append(current_doc) or [{"id": "demo"}]
    fake_runtime = types.ModuleType("ocw_workbench.gui.runtime")
    fake_runtime.icon_path = lambda name="default": f"/tmp/{name}.svg"
    fake_runtime.show_info = lambda title, message: None
    fake_runtime.show_error = lambda title, exc: (_ for _ in ()).throw(AssertionError(f"Unexpected error: {title}: {exc}"))

    orig_app, orig_wb, orig_runtime = _install_mocks(fake_app, fake_wb, fake_runtime)
    try:
        import ocw_workbench.commands.reload_plugins as reload_plugins_module

        reload_plugins_module.show_info = lambda title, message: info_calls.append((title, message))
        reload_plugins_module.show_error = lambda title, exc: (_ for _ in ()).throw(
            AssertionError(f"Unexpected error: {title}: {exc}")
        )

        reload_plugins_module.ReloadPluginsCommand().Activated()
    finally:
        _restore_mocks(orig_app, orig_wb, orig_runtime)

    assert not ensure_called
    assert reload_calls == [doc]
    assert info_calls == [("Reload Plugins", "Discovered 1 plugins.")]


def test_import_template_followup_refreshes_open_workbench_without_ensuring_dock(monkeypatch) -> None:
    doc = FakeDocument()
    ensure_called: list[bool] = []
    refresh_calls: list[object] = []
    dialogs: list[tuple[str, object]] = []
    status_calls: list[tuple[str, str]] = []

    fake_app = _make_fake_freecad(doc)
    fake_wb = types.ModuleType("ocw_workbench.workbench")
    fake_wb.ensure_workbench_ui = lambda *a, **kw: ensure_called.append(True)
    fake_wb._refresh_create_panel_if_open = lambda current_doc: refresh_calls.append(current_doc)
    fake_wb._ACTIVE_WORKBENCH = types.SimpleNamespace(doc=doc, set_status=lambda message, level="info": status_calls.append((message, level)))
    fake_runtime = types.ModuleType("ocw_workbench.gui.runtime")
    fake_runtime.icon_path = lambda name="default": f"/tmp/{name}.svg"
    fake_runtime.show_error = lambda title, exc: (_ for _ in ()).throw(AssertionError(f"Unexpected error: {title}: {exc}"))
    fake_runtime.open_dialog = lambda title, panel, **kwargs: None

    class FakeImportPanel:
        def __init__(self, on_imported=None, **kwargs) -> None:
            self.on_imported = on_imported

    inspector_calls: list[dict[str, object]] = []

    class FakeTemplateInspectorPanel:
        def __init__(self, path, on_saved=None, on_status=None, **kwargs) -> None:
            inspector_calls.append({"path": path, "on_saved": on_saved, "on_status": on_status})

    orig_app, orig_wb, orig_runtime = _install_mocks(fake_app, fake_wb, fake_runtime)
    try:
        monkeypatch.setattr(
            "ocw_workbench.gui.panels.import_template_from_fcstd_panel.ImportTemplateFromFCStdPanel",
            FakeImportPanel,
        )
        monkeypatch.setattr(
            "ocw_workbench.gui.panels.template_inspector_panel.TemplateInspectorPanel",
            FakeTemplateInspectorPanel,
        )
        import ocw_workbench.commands.import_template_from_fcstd as import_module

        import_module.open_dialog = lambda title, panel, **kwargs: dialogs.append((title, panel))
        import_module.show_error = lambda title, exc: (_ for _ in ()).throw(
            AssertionError(f"Unexpected error: {title}: {exc}")
        )

        import_module.ImportTemplateFromFCStdCommand().Activated()
        assert dialogs and dialogs[0][0] == "Import Template from FCStd"
        import_panel = dialogs[0][1]
        import_panel.on_imported("/tmp/demo.fcstd")
    finally:
        _restore_mocks(orig_app, orig_wb, orig_runtime)

    assert not ensure_called
    assert refresh_calls == [doc]
    assert len(inspector_calls) == 1
    assert inspector_calls[0]["path"] == "/tmp/demo.fcstd"
    assert inspector_calls[0]["on_status"] is fake_wb._ACTIVE_WORKBENCH.set_status
    inspector_calls[0]["on_saved"]("/tmp/saved-template.yaml")
    assert refresh_calls == [doc, doc]


def test_legacy_place_and_drag_helpers_use_direct_tools_without_opening_dock() -> None:
    import ocw_workbench.workbench as workbench_module

    doc = FakeDocument()
    dock_calls: list[tuple[object, str]] = []
    place_calls: list[tuple[object, str]] = []
    drag_calls: list[object] = []

    original_app = workbench_module.App
    original_open = workbench_module.open_workbench_dock
    original_place = workbench_module.start_place_mode_direct
    original_drag = workbench_module.start_component_drag_mode_direct
    try:
        workbench_module.App = _make_fake_freecad(doc)
        workbench_module.open_workbench_dock = lambda current_doc=None, focus="create": dock_calls.append((current_doc, focus)) or object()
        workbench_module.start_place_mode_direct = lambda current_doc, template_id: place_calls.append((current_doc, template_id)) or True
        workbench_module.start_component_drag_mode_direct = lambda current_doc: drag_calls.append(current_doc) or True

        assert workbench_module.start_component_place_mode(doc, "generic_mpc_pad_30mm") is True
        assert workbench_module.start_component_drag_mode(doc) is True
    finally:
        workbench_module.App = original_app
        workbench_module.open_workbench_dock = original_open
        workbench_module.start_place_mode_direct = original_place
        workbench_module.start_component_drag_mode_direct = original_drag

    assert dock_calls == []
    assert place_calls == [(doc, "generic_mpc_pad_30mm")]
    assert drag_calls == [doc]
