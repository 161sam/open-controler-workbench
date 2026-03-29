from __future__ import annotations

import types

from ocw_workbench.freecad_api import gui as freecad_gui


class _FakeSelection:
    def __init__(self) -> None:
        self.cleared = 0
        self.added: list[tuple[str, str]] = []

    def clearSelection(self) -> None:
        self.cleared += 1

    def addSelection(self, doc_name: str, object_name: str) -> None:
        self.added.append((doc_name, object_name))


class _FakeObject:
    def __init__(self, name: str, component_id: str | None = None) -> None:
        self.Name = name
        self.OCWComponentId = component_id


def test_sync_selection_clears_and_selects_matching_component(monkeypatch) -> None:
    selection = _FakeSelection()
    monkeypatch.setattr(freecad_gui, "Gui", types.SimpleNamespace(Selection=selection))
    doc = types.SimpleNamespace(
        Name="Controller",
        Objects=[
            _FakeObject("OCW_btn1", "btn1"),
            _FakeObject("OCW_btn2", "btn2"),
        ],
    )

    assert freecad_gui.sync_selection(doc, "btn2") is True
    assert selection.cleared == 1
    assert selection.added == [("Controller", "OCW_btn2")]


def test_sync_selection_clears_when_selection_is_none(monkeypatch) -> None:
    selection = _FakeSelection()
    monkeypatch.setattr(freecad_gui, "Gui", types.SimpleNamespace(Selection=selection))
    doc = types.SimpleNamespace(Name="Controller", Objects=[_FakeObject("OCW_btn1", "btn1")])

    assert freecad_gui.sync_selection(doc, None) is True
    assert selection.cleared == 1
    assert selection.added == []
