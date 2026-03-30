from __future__ import annotations

from pathlib import Path

from ocw_workbench.commands.factory import command_specs_by_command_id, component_toolbar_groups
from ocw_workbench.library.manager import ComponentLibraryManager
from ocw_workbench.plugins.activation import activate_plugin
from ocw_workbench.services.plugin_service import reset_plugin_service
from ocw_workbench.templates.generator import TemplateGenerator
from ocw_workbench.templates.registry import TemplateRegistry


def test_midicontroller_templates_describe_clear_starting_points() -> None:
    reset_plugin_service()
    activate_plugin("midicontroller")

    templates = {item["template"]["id"]: item["template"] for item in TemplateRegistry().list_templates()}

    assert templates["pad_grid_4x4"]["name"] == "Finger Drum Pad Grid"
    assert "finger-drumming controller" in templates["pad_grid_4x4"]["description"]
    assert templates["fader_strip"]["name"] == "Channel Strip"
    assert templates["display_nav_module"]["category"] == "navigation"


def test_midicontroller_workflow_defaults_prioritize_real_controls() -> None:
    reset_plugin_service()
    activate_plugin("midicontroller")

    project = TemplateGenerator().generate_from_template("encoder_module")
    groups = dict(component_toolbar_groups(active_plugin_id="midicontroller"))
    specs = command_specs_by_command_id()
    components = {item["id"]: item for item in ComponentLibraryManager().list_components()}

    assert all(component["library_ref"] == "generic_ec11_encoder_with_push" for component in project["components"])
    assert groups["OCW Performance Surface"] == ["OCW_PlacePad", "OCW_PlaceRgbButton"]
    assert specs["OCW_PlaceEncoder"].library_ref == "generic_ec11_encoder_with_push"
    assert components["generic_mpc_pad_30mm"]["ui"]["category"] == "Performance Pads"
    assert components["omron_b3f_1000"]["ui"]["label"] == "Utility Button 6 mm"


def test_bike_trailer_templates_support_starter_size_profiles() -> None:
    reset_plugin_service()
    activate_plugin("bike_trailer")

    compact = TemplateGenerator().generate_from_template(
        "trailer_basic",
        overrides={"parameter_preset_id": "compact_city_trailer"},
    )
    cargo = TemplateGenerator().generate_from_template(
        "trailer_box",
        overrides={"parameter_preset_id": "daily_cargo_hauler"},
    )

    assert compact["template"]["name"] == "Starter Flatbed Trailer"
    assert compact["controller"]["width"] == 200.0
    assert next(item for item in compact["components"] if item["id"] == "wheel_right")["x"] == 160.0
    assert cargo["template"]["name"] == "Cargo Box Trailer"
    assert cargo["controller"]["depth"] == 140.0
    assert next(item for item in cargo["components"] if item["id"] == "cargo_box")["y"] == 74.0


def test_bike_trailer_component_and_toolbar_labels_match_build_flow() -> None:
    reset_plugin_service()
    activate_plugin("bike_trailer")

    groups = dict(component_toolbar_groups(active_plugin_id="bike_trailer"))
    specs = command_specs_by_command_id()
    components = {item["id"]: item for item in ComponentLibraryManager().list_components()}

    assert list(groups) == ["OCW Frame Setup", "OCW Rolling Gear", "OCW Cargo Modules"]
    assert specs["OCW_PlaceFrameConnector"].label == "Place Crossbar Connector"
    assert specs["OCW_PlaceCargoBoxModule"].label == "Place Cargo Box Module"
    assert components["bike_trailer.frame_connector_crossbar"]["ui"]["category"] == "Frame Setup"
    assert components["bike_trailer.cargo_box_module_standard"]["ui"]["category"] == "Storage Modules"


def test_domain_quickstart_docs_exist() -> None:
    assert Path("docs/workflows/midicontroller_quickstart.md").exists()
    assert Path("docs/workflows/bike_trailer_quickstart.md").exists()
