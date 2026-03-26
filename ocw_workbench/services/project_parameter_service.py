from __future__ import annotations

from copy import deepcopy
from typing import Any

from ocw_workbench.services.template_service import TemplateService
from ocw_workbench.services.variant_service import VariantService
from ocw_workbench.templates.parameters import TemplateParameterResolver


class ProjectParameterService:
    def __init__(
        self,
        template_service: TemplateService | None = None,
        variant_service: VariantService | None = None,
        parameter_resolver: TemplateParameterResolver | None = None,
    ) -> None:
        self.template_service = template_service or TemplateService()
        self.variant_service = variant_service or VariantService()
        self.parameter_resolver = parameter_resolver or TemplateParameterResolver()

    def inspect_project_parameters(self, context: dict[str, Any]) -> dict[str, Any]:
        template_id = str(context.get("template_id") or "").strip() or None
        variant_id = str(context.get("variant_id") or "").strip() or None
        if template_id is None:
            return {
                "status": "unlinked",
                "message": "This document is not linked to a parameterized template.",
                "reparameterizable": False,
                "template_id": None,
                "variant_id": None,
                "template": None,
                "values": {},
                "sources": {},
                "preset_id": None,
                "ui_model": None,
            }

        try:
            template = self.variant_service.resolve_variant(variant_id) if variant_id else self.template_service.resolve_template(template_id)
        except KeyError:
            missing = f"variant '{variant_id}'" if variant_id else f"template '{template_id}'"
            return {
                "status": "missing_source",
                "message": f"The project source {missing} is no longer available. Re-parameterization is unavailable.",
                "reparameterizable": False,
                "template_id": template_id,
                "variant_id": variant_id,
                "template": None,
                "values": {},
                "sources": {},
                "preset_id": None,
                "ui_model": None,
            }

        seeded_values, seeded_sources, preset_id, source_status = self._seed_project_values(context)
        try:
            ui_model = self.parameter_resolver.build_ui_model(
                template,
                values=seeded_values,
                preset_id=preset_id,
            )
        except KeyError:
            ui_model = self.parameter_resolver.build_ui_model(
                template,
                values=seeded_values,
                preset_id=None,
            )
            preset_id = None

        if seeded_sources:
            ui_model["sources"].update(seeded_sources)

        status = "ready" if source_status == "project" else "legacy_fallback"
        message = (
            "Project parameters loaded from saved project metadata."
            if status == "ready"
            else "Loaded parameter values from legacy project overrides. Review and re-save to persist explicit project parameter metadata."
        )
        return {
            "status": status,
            "message": message,
            "reparameterizable": True,
            "template_id": template_id,
            "variant_id": variant_id,
            "template": template,
            "values": deepcopy(ui_model["values"]),
            "sources": deepcopy(ui_model["sources"]),
            "preset_id": ui_model["preset_id"],
            "ui_model": ui_model,
        }

    def _seed_project_values(self, context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str], str | None, str]:
        parameter_meta = context.get("parameters", {}) if isinstance(context.get("parameters"), dict) else {}
        if isinstance(parameter_meta.get("values"), dict) and parameter_meta.get("values"):
            return (
                deepcopy(parameter_meta.get("values", {})),
                deepcopy(parameter_meta.get("sources", {})) if isinstance(parameter_meta.get("sources"), dict) else {},
                str(parameter_meta.get("preset_id")) if parameter_meta.get("preset_id") else None,
                "project",
            )

        overrides = context.get("overrides", {}) if isinstance(context.get("overrides"), dict) else {}
        legacy_values = overrides.get("parameters", {}) if isinstance(overrides.get("parameters"), dict) else {}
        legacy_preset_id = str(overrides.get("parameter_preset_id")) if overrides.get("parameter_preset_id") else None
        if legacy_values or legacy_preset_id:
            return (
                deepcopy(legacy_values),
                {parameter_id: "legacy override" for parameter_id in legacy_values},
                legacy_preset_id,
                "legacy",
            )
        return ({}, {}, None, "project")
