from ocf_freecad.domain.component import Component
from ocf_freecad.domain.controller import Controller
from ocf_freecad.generator.controller_builder import ControllerBuilder


class ShapeRecorder:
    def __init__(self) -> None:
        self.calls = []

    def create_surface_prism(self, doc, name, surface, height, x=0, y=0, z=0):
        self.calls.append(
            {
                "doc": doc,
                "name": name,
                "surface": surface.to_dict(),
                "height": height,
                "x": x,
                "y": y,
                "z": z,
            }
        )
        return {"name": name, "surface": surface.to_dict(), "height": height, "z": z}


def test_rectangle_surface_is_default(monkeypatch):
    recorder = ShapeRecorder()
    monkeypatch.setattr("ocf_freecad.generator.controller_builder.shapes.create_surface_prism", recorder.create_surface_prism)
    builder = ControllerBuilder(doc="doc")
    controller = Controller("rect", 120, 80, 30, 3)

    body = builder.build_body(controller)
    top = builder.build_top_plate(controller)

    assert body["surface"]["shape"] == "rectangle"
    assert body["surface"]["width"] == 120
    assert body["surface"]["height"] == 80
    assert top["z"] == 27
    assert recorder.calls[1]["surface"]["shape"] == "rectangle"


def test_rounded_rect_surface_is_used(monkeypatch):
    recorder = ShapeRecorder()
    monkeypatch.setattr("ocf_freecad.generator.controller_builder.shapes.create_surface_prism", recorder.create_surface_prism)
    builder = ControllerBuilder(doc="doc")
    controller = Controller(
        "rounded",
        120,
        80,
        30,
        3,
        surface={"shape": "rounded_rect", "corner_radius": 8},
    )

    builder.build_body(controller)

    assert recorder.calls[0]["surface"]["shape"] == "rounded_rect"
    assert recorder.calls[0]["surface"]["corner_radius"] == 8
    assert recorder.calls[0]["surface"]["width"] == 120
    assert recorder.calls[0]["surface"]["height"] == 80


def test_cutouts_remain_relative_to_controller_coordinates():
    builder = ControllerBuilder(doc=None)
    component = Component(
        id="enc1",
        type="encoder",
        x=40,
        y=30,
        library_ref="alps_ec11e15204a3",
    )

    cutouts = builder.build_cutout_primitives([component])

    assert cutouts[0]["x"] == 40
    assert cutouts[0]["y"] == 30
    assert cutouts[0]["shape"] == "circle"
