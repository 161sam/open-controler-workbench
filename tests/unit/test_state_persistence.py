from __future__ import annotations

import json

from ocf_freecad.freecad_api.model import CONTROLLER_OBJECT_NAME, GENERATED_GROUP_NAME, get_generated_group
from ocf_freecad.freecad_api.state import (
    STATE_PROPERTY_NAME,
    get_state_container,
    has_persisted_state,
    read_state,
    write_state,
)


class FakeViewObject:
    def __init__(self) -> None:
        self.Visibility = True


class FakeDocumentObject:
    def __init__(self, type_name: str, name: str) -> None:
        self.TypeId = type_name
        self.Name = name
        self.Label = name
        self.PropertiesList: list[str] = []
        self.ViewObject = FakeViewObject()
        self.editor_modes: dict[str, int] = {}
        self.Group: list[FakeDocumentObject] = []

    def addProperty(self, _type_name: str, name: str, _group: str, _doc: str) -> None:
        if name not in self.PropertiesList:
            self.PropertiesList.append(name)
            setattr(self, name, "")

    def setEditorMode(self, name: str, mode: int) -> None:
        self.editor_modes[name] = mode

    def addObject(self, obj) -> None:
        if obj not in self.Group:
            self.Group.append(obj)


class FakeDocument:
    def __init__(self) -> None:
        self.Objects: list[FakeDocumentObject] = []

    def addObject(self, type_name: str, name: str) -> FakeDocumentObject:
        obj = FakeDocumentObject(type_name, name)
        self.Objects.append(obj)
        return obj

    def getObject(self, name: str):
        for obj in self.Objects:
            if obj.Name == name:
                return obj
        return None


def test_write_state_creates_controller_object_with_persistent_properties():
    doc = FakeDocument()

    write_state(
        doc,
        {
            "controller": {
                "id": "demo",
                "width": 180.0,
                "depth": 110.0,
                "height": 32.0,
                "top_thickness": 3.0,
                "wall_thickness": 4.0,
                "bottom_thickness": 5.0,
                "lid_inset": 1.5,
                "inner_clearance": 0.4,
                "surface": {
                    "shape": "rounded_rect",
                    "corner_radius": 8.0,
                },
            },
            "components": [],
            "meta": {
                "template_id": "encoder_module",
                "variant_id": "encoder_compact",
                "selection": "enc1",
            },
        },
    )

    controller = doc.getObject(CONTROLLER_OBJECT_NAME)

    assert controller is not None
    assert controller.ViewObject.Visibility is False
    assert json.loads(controller.ProjectJson)["controller"]["id"] == "demo"
    assert controller.ControllerId == "demo"
    assert controller.TemplateId == "encoder_module"
    assert controller.VariantId == "encoder_compact"
    assert controller.SelectionId == "enc1"
    assert controller.Width == 180.0
    assert controller.Depth == 110.0
    assert controller.WallThickness == 4.0
    assert controller.SurfaceShape == "rounded_rect"
    assert controller.CornerRadius == 8.0


def test_read_state_prefers_controller_object_payload():
    doc = FakeDocument()
    write_state(doc, {"controller": {"id": "persisted"}, "components": [], "meta": {}})

    state = read_state(doc)

    assert state is not None
    assert state["controller"]["id"] == "persisted"
    assert has_persisted_state(doc) is True


def test_read_state_migrates_legacy_state_container_into_controller_object():
    doc = FakeDocument()
    legacy = get_state_container(doc, create=True)
    legacy.StateJson = json.dumps({"controller": {"id": "legacy"}, "components": [], "meta": {}})

    state = read_state(doc)
    controller = doc.getObject(CONTROLLER_OBJECT_NAME)

    assert state is not None
    assert state["controller"]["id"] == "legacy"
    assert controller is not None
    assert json.loads(controller.ProjectJson)["controller"]["id"] == "legacy"
    assert legacy.StateJson


def test_generated_group_reuses_single_group_container():
    doc = FakeDocument()

    first = get_generated_group(doc, create=True)
    second = get_generated_group(doc, create=True)

    assert first is second
    assert first.Name == GENERATED_GROUP_NAME
