from __future__ import annotations

from ocw_workbench.services.project_parameter_service import ProjectParameterService


def test_project_parameter_service_reads_saved_project_parameter_metadata():
    service = ProjectParameterService()

    model = service.inspect_project_parameters(
        {
            "template_id": "fader_strip",
            "variant_id": None,
            "overrides": {"parameters": {"fader_length": 45}},
            "parameters": {
                "values": {"fader_length": 45, "case_width": 220.0},
                "sources": {"fader_length": "user", "case_width": "user"},
                "preset_id": None,
            },
        }
    )

    assert model["reparameterizable"] is True
    assert model["status"] == "ready"
    assert model["values"]["fader_length"] == 45
    assert model["sources"]["case_width"] == "user"


def test_project_parameter_service_falls_back_to_legacy_overrides():
    service = ProjectParameterService()

    model = service.inspect_project_parameters(
        {
            "template_id": "pad_grid_4x4",
            "variant_id": None,
            "overrides": {
                "parameters": {"pad_count_x": 8, "pad_count_y": 4},
                "parameter_preset_id": "pad_grid_8x2",
            },
            "parameters": {},
        }
    )

    assert model["reparameterizable"] is True
    assert model["status"] == "legacy_fallback"
    assert model["values"]["pad_count_x"] == 8
    assert model["sources"]["pad_count_x"] == "legacy override"
    assert "legacy project overrides" in model["message"]


def test_project_parameter_service_reports_missing_template_source():
    service = ProjectParameterService()

    model = service.inspect_project_parameters(
        {
            "template_id": "missing_template",
            "variant_id": None,
            "overrides": {},
            "parameters": {},
        }
    )

    assert model["reparameterizable"] is False
    assert model["status"] == "missing_source"
    assert "missing_template" in model["message"]
