from __future__ import annotations

from ocw_workbench.commands.factory import (
    build_plugin_commands,
    command_specs_by_command_id,
    component_toolbar_command_ids,
    component_toolbar_groups,
    iter_plugin_command_specs,
)


def test_plugin_command_specs_include_pad_and_encoder() -> None:
    specs = {spec.component: spec for spec in iter_plugin_command_specs()}

    assert "pad" in specs
    assert "encoder" in specs
    assert specs["pad"].command_id == "OCW_PlacePad"
    assert specs["encoder"].command_id == "OCW_PlaceEncoder"


def test_component_toolbar_groups_are_plugin_driven() -> None:
    groups = dict(component_toolbar_groups(active_plugin_id="midicontroller"))

    assert list(groups) == [
        "OCW Performance Surface",
        "OCW Mixing",
        "OCW Navigation & Feedback",
        "OCW Buttons & Utility",
    ]
    assert groups["OCW Performance Surface"] == ["OCW_PlacePad", "OCW_PlaceRgbButton"]
    assert groups["OCW Navigation & Feedback"] == ["OCW_PlaceDisplay", "OCW_PlaceEncoder"]


def test_command_spec_lookup_exposes_command_metadata() -> None:
    specs = command_specs_by_command_id()

    assert specs["OCW_PlacePad"].icon == "pad.svg"
    assert specs["OCW_PlacePad"].category == "Performance Surface"
    assert "Place Performance Pad" in specs["OCW_PlacePad"].tooltip
    assert "OCW_PlaceEncoder" in component_toolbar_command_ids()


def test_build_plugin_commands_creates_freecad_place_commands() -> None:
    commands = build_plugin_commands()

    assert "OCW_PlacePad" in commands
    assert "OCW_PlaceEncoder" in commands
    assert commands["OCW_PlacePad"].component_type == "pad"
    assert commands["OCW_PlaceEncoder"].component_type == "encoder"
