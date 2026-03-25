from __future__ import annotations

from collections import Counter
from typing import Any

from ocf_freecad.gui.panels._common import (
    FallbackButton,
    FallbackCombo,
    FallbackLabel,
    FallbackText,
    current_text,
    load_qt,
    set_combo_items,
    set_enabled,
    set_label_text,
    set_text,
    text_value,
)
from ocf_freecad.gui.widgets.favorites_list import FavoritesListWidget
from ocf_freecad.gui.widgets.preset_list import PresetListWidget
from ocf_freecad.gui.widgets.recent_list import RecentListWidget
from ocf_freecad.services.controller_service import ControllerService
from ocf_freecad.services.template_service import TemplateService
from ocf_freecad.services.userdata_service import UserDataService
from ocf_freecad.services.variant_service import VariantService


class CreatePanel:
    def __init__(
        self,
        doc: Any,
        controller_service: ControllerService | None = None,
        template_service: TemplateService | None = None,
        variant_service: VariantService | None = None,
        userdata_service: UserDataService | None = None,
        on_created: Any | None = None,
        on_status: Any | None = None,
    ) -> None:
        self.doc = doc
        self.controller_service = controller_service or ControllerService()
        self.template_service = template_service or TemplateService()
        self.variant_service = variant_service or VariantService()
        self.userdata_service = userdata_service or UserDataService(
            template_service=self.template_service,
            variant_service=self.variant_service,
            controller_service=self.controller_service,
        )
        self.on_created = on_created
        self.on_status = on_status
        self._templates: list[dict[str, Any]] = []
        self._variants: list[dict[str, Any]] = []
        self._template_lookup: dict[str, dict[str, Any]] = {}
        self._variant_lookup: dict[str, dict[str, Any]] = {}
        self.form = _build_form()
        self.widget = self.form["widget"]
        self._connect_events()
        self.refresh()

    def refresh(self) -> None:
        context = self.controller_service.get_ui_context(self.doc)
        active_template_id = context.get("template_id")
        active_variant_id = context.get("variant_id")
        previous_template = active_template_id or self.selected_template_id()
        previous_variant = active_variant_id or self.selected_variant_id()
        favorites = self.userdata_service.list_favorites()
        recents = self.userdata_service.list_recents()
        presets = self.userdata_service.list_presets()
        favorite_templates = {entry.reference_id for entry in favorites if entry.type == "template" and entry.reference_id}
        recent_templates = {entry.template_id for entry in recents}
        self._templates = self.template_service.list_templates()
        self._templates = sorted(
            self._templates,
            key=lambda item: (
                0 if item["template"]["id"] in favorite_templates else 1,
                0 if item["template"]["id"] in recent_templates else 1,
                str(item["template"]["name"]).lower(),
            ),
        )
        labels = [_template_label(item, favorite=item["template"]["id"] in favorite_templates) for item in self._templates]
        self._template_lookup = {label: item for label, item in zip(labels, self._templates)}
        set_combo_items(self.form["template"], labels)
        if previous_template:
            self._set_selected_template(previous_template)
        self.refresh_variants(active_variant_id=previous_variant)
        self._refresh_shortcuts()
        self.refresh_preview()
        self._sync_selected_context()
        self._update_actions()

    def refresh_variants(self, active_variant_id: str | None = None) -> None:
        template_id = self.selected_template_id()
        favorites = self.userdata_service.list_favorites()
        favorite_variants = {entry.reference_id for entry in favorites if entry.type == "variant" and entry.reference_id}
        self._variants = self.variant_service.list_variants(template_id=template_id) if template_id else []
        self._variants = sorted(
            self._variants,
            key=lambda item: (
                0 if item["variant"]["id"] in favorite_variants else 1,
                str(item["variant"]["name"]).lower(),
            ),
        )
        labels = ["Template Default"] + [
            _variant_label(item, favorite=item["variant"]["id"] in favorite_variants) for item in self._variants
        ]
        self._variant_lookup = {label: item for label, item in zip(labels[1:], self._variants)}
        set_combo_items(self.form["variant"], labels)
        if active_variant_id:
            self._set_selected_variant(active_variant_id)
        self._set_variant_summary()

    def selected_template_id(self) -> str | None:
        item = self._template_lookup.get(current_text(self.form["template"]))
        if item is None:
            return None
        return item["template"]["id"]

    def selected_variant_id(self) -> str | None:
        label = current_text(self.form["variant"])
        if label in {"", "Template Default"}:
            return None
        item = self._variant_lookup.get(label)
        if item is None:
            return None
        return item["variant"]["id"]

    def refresh_preview(self) -> str:
        preview = self._build_preview()
        set_text(self.form["preview"], preview)
        return preview

    def create_controller(self) -> dict[str, Any]:
        template_id = self.selected_template_id()
        if not template_id:
            raise ValueError("No template selected")
        variant_id = self.selected_variant_id()
        if variant_id:
            state = self.controller_service.create_from_variant(self.doc, variant_id)
            recent_name = f"{self.userdata_service.resolve_template_name(template_id)} / {self.userdata_service.resolve_variant_name(variant_id)}"
            self.userdata_service.record_recent(template_id=template_id, variant_id=variant_id, name=recent_name)
            self._publish_status(f"Created controller from variant '{variant_id}'.")
        else:
            state = self.controller_service.create_from_template(self.doc, template_id)
            recent_name = self.userdata_service.resolve_template_name(template_id)
            self.userdata_service.record_recent(template_id=template_id, variant_id=None, name=recent_name)
            self._publish_status(f"Created controller from template '{template_id}'.")
        self.refresh()
        if self.on_created is not None:
            self.on_created(state)
        return state

    def toggle_template_favorite(self) -> None:
        template_id = self.selected_template_id()
        if template_id is None:
            raise ValueError("No template selected")
        template = self.template_service.get_template(template_id)["template"]
        favorites = self.userdata_service.toggle_favorite("template", template_id, name=str(template["name"]))
        status = "favorite" if any(entry.reference_id == template_id and entry.type == "template" for entry in favorites) else "not favorite"
        self.refresh()
        self._publish_status(f"Template '{template_id}' is now {status}.")

    def toggle_variant_favorite(self) -> None:
        variant_id = self.selected_variant_id()
        if variant_id is None:
            raise ValueError("No variant selected")
        variant = self.variant_service.get_variant(variant_id)["variant"]
        favorites = self.userdata_service.toggle_favorite("variant", variant_id, name=str(variant["name"]))
        status = "favorite" if any(entry.reference_id == variant_id and entry.type == "variant" for entry in favorites) else "not favorite"
        self.refresh()
        self._publish_status(f"Variant '{variant_id}' is now {status}.")

    def load_selected_favorite(self) -> None:
        entry = self.form["favorites_widget"].selected()
        if entry is None:
            raise ValueError("No favorite selected")
        self._apply_selection(template_id=entry["template_id"], variant_id=entry.get("variant_id"))
        self._publish_status("Loaded favorite selection.")

    def load_selected_recent(self) -> None:
        entry = self.form["recents_widget"].selected()
        if entry is None:
            raise ValueError("No recent entry selected")
        self._apply_selection(template_id=entry["template_id"], variant_id=entry.get("variant_id"))
        self._publish_status("Loaded recent selection.")

    def load_selected_preset(self) -> None:
        entry = self.form["presets_widget"].selected()
        if entry is None:
            raise ValueError("No preset selected")
        preset = self.userdata_service.get_preset(entry["preset_id"])
        self._apply_selection(template_id=preset.template_id, variant_id=preset.variant_id)
        self._publish_status(f"Loaded preset '{preset.name}'.")

    def save_current_preset(self) -> None:
        template_id = self.selected_template_id()
        if template_id is None:
            raise ValueError("Select a template before saving a preset")
        name = text_value(self.form["presets_widget"].parts["name"]).strip()
        if not name:
            raise ValueError("Preset name is required")
        preset = self.userdata_service.preset_from_document(
            self.doc,
            name=name,
            template_id=template_id,
            variant_id=self.selected_variant_id(),
        )
        self.refresh()
        self._publish_status(f"Saved preset '{preset.name}'.")

    def handle_template_changed(self, *_args: Any) -> None:
        self.refresh_variants()
        self.refresh_preview()
        self._sync_selected_context()
        self._update_actions()

    def handle_variant_changed(self, *_args: Any) -> None:
        self.refresh_preview()
        self._set_variant_summary()
        self._update_actions()

    def handle_create_clicked(self) -> None:
        try:
            self.create_controller()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_toggle_template_favorite(self) -> None:
        try:
            self.toggle_template_favorite()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_toggle_variant_favorite(self) -> None:
        try:
            self.toggle_variant_favorite()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_load_favorite(self) -> None:
        try:
            self.load_selected_favorite()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_load_recent(self) -> None:
        try:
            self.load_selected_recent()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_load_preset(self) -> None:
        try:
            self.load_selected_preset()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_save_preset(self) -> None:
        try:
            self.save_current_preset()
        except Exception as exc:
            self._publish_status(str(exc))

    def accept(self) -> bool:
        self.create_controller()
        return True

    def _build_preview(self) -> str:
        template_id = self.selected_template_id()
        if not template_id:
            return "Select a template to see the controller preview."
        variant_id = self.selected_variant_id()
        if variant_id:
            project = self.variant_service.generate_from_variant(variant_id)
            title = f"Variant: {variant_id}"
        else:
            project = self.template_service.generate_from_template(template_id)
            title = f"Template: {template_id}"
        counts = Counter(component["type"] for component in project["components"])
        summary = ", ".join(f"{component_type} x{count}" for component_type, count in sorted(counts.items()))
        controller = project["controller"]
        surface = controller.get("surface") or {}
        shape = surface.get("shape") or surface.get("type") or "rectangle"
        width = surface.get("width", controller.get("width", "-"))
        height = surface.get("height", controller.get("depth", "-"))
        return "\n".join(
            [
                title,
                f"Surface: {shape} {width} x {height} mm",
                f"Components: {len(project['components'])}",
                f"Types: {summary or 'none'}",
            ]
        )

    def _set_selected_template(self, template_id: str) -> None:
        for index, item in enumerate(self._templates):
            if item["template"]["id"] == template_id:
                self.form["template"].setCurrentIndex(index)
                return

    def _set_selected_variant(self, variant_id: str) -> None:
        for index, item in enumerate(self._variants, start=1):
            if item["variant"]["id"] == variant_id:
                self.form["variant"].setCurrentIndex(index)
                return
        self.form["variant"].setCurrentIndex(0)

    def _apply_selection(self, template_id: str | None, variant_id: str | None) -> None:
        if template_id:
            self._set_selected_template(template_id)
        self.refresh_variants(active_variant_id=variant_id)
        self.refresh_preview()
        self._sync_selected_context()
        self._update_actions()

    def _sync_selected_context(self) -> None:
        template_id = self.selected_template_id()
        template = next((item["template"] for item in self._templates if item["template"]["id"] == template_id), None)
        if template is None:
            set_label_text(self.form["template_summary"], "Choose a template to start.")
            set_label_text(self.form["favorite_template_status"], "Template favorite: no selection")
            return
        description = template.get("description") or "No template description available."
        is_favorite = self.userdata_service.is_favorite("template", template_id)
        set_label_text(self.form["template_summary"], f"{template['name']}: {description}")
        set_label_text(
            self.form["favorite_template_status"],
            f"Template favorite: {'yes' if is_favorite else 'no'}",
        )

    def _set_variant_summary(self) -> None:
        variant_id = self.selected_variant_id()
        if not variant_id:
            set_label_text(self.form["variant_summary"], "Template defaults are active.")
            set_label_text(self.form["favorite_variant_status"], "Variant favorite: n/a")
            return
        variant = next((item["variant"] for item in self._variants if item["variant"]["id"] == variant_id), None)
        if variant is None:
            set_label_text(self.form["variant_summary"], "Selected variant is not available.")
            set_label_text(self.form["favorite_variant_status"], "Variant favorite: unavailable")
            return
        description = variant.get("description") or "No variant description available."
        is_favorite = self.userdata_service.is_favorite("variant", variant_id)
        set_label_text(self.form["variant_summary"], f"{variant['name']}: {description}")
        set_label_text(
            self.form["favorite_variant_status"],
            f"Variant favorite: {'yes' if is_favorite else 'no'}",
        )

    def _refresh_shortcuts(self) -> None:
        favorites = []
        for entry in self.userdata_service.list_favorites():
            if entry.type == "template" and entry.reference_id:
                favorites.append(
                    {
                        "label": f"Template: {entry.name or entry.reference_id}",
                        "template_id": entry.reference_id,
                        "variant_id": None,
                    }
                )
            elif entry.type == "variant" and entry.reference_id:
                try:
                    variant = self.variant_service.get_variant(entry.reference_id)["variant"]
                    favorites.append(
                        {
                            "label": f"Variant: {entry.name or entry.reference_id}",
                            "template_id": str(variant["template_id"]),
                            "variant_id": entry.reference_id,
                        }
                    )
                except Exception:
                    continue
        recents = [
            {
                "label": entry.name or entry.id,
                "template_id": entry.template_id,
                "variant_id": entry.variant_id,
            }
            for entry in self.userdata_service.list_recents()
        ]
        presets = [
            {
                "label": entry.name,
                "preset_id": entry.id,
            }
            for entry in self.userdata_service.list_presets()
        ]
        self.form["favorites_widget"].set_entries(favorites)
        self.form["recents_widget"].set_entries(recents)
        self.form["presets_widget"].set_entries(presets)

    def _update_actions(self) -> None:
        template_selected = self.selected_template_id() is not None
        variant_selected = self.selected_variant_id() is not None
        set_enabled(self.form["create_button"], template_selected)
        set_enabled(self.form["favorite_template_button"], template_selected)
        set_enabled(self.form["favorite_variant_button"], variant_selected)
        set_enabled(self.form["presets_widget"].parts["save_button"], template_selected)

    def _publish_status(self, message: str) -> None:
        set_label_text(self.form["status"], message)
        if self.on_status is not None:
            self.on_status(message)

    def _connect_events(self) -> None:
        template = self.form["template"]
        variant = self.form["variant"]
        if hasattr(template, "currentIndexChanged"):
            template.currentIndexChanged.connect(self.handle_template_changed)
        if hasattr(variant, "currentIndexChanged"):
            variant.currentIndexChanged.connect(self.handle_variant_changed)
        if hasattr(self.form["create_button"], "clicked"):
            self.form["create_button"].clicked.connect(self.handle_create_clicked)
        if hasattr(self.form["favorite_template_button"], "clicked"):
            self.form["favorite_template_button"].clicked.connect(self.handle_toggle_template_favorite)
        if hasattr(self.form["favorite_variant_button"], "clicked"):
            self.form["favorite_variant_button"].clicked.connect(self.handle_toggle_variant_favorite)
        if hasattr(self.form["favorites_widget"].parts["apply_button"], "clicked"):
            self.form["favorites_widget"].parts["apply_button"].clicked.connect(self.handle_load_favorite)
        if hasattr(self.form["recents_widget"].parts["apply_button"], "clicked"):
            self.form["recents_widget"].parts["apply_button"].clicked.connect(self.handle_load_recent)
        if hasattr(self.form["presets_widget"].parts["load_button"], "clicked"):
            self.form["presets_widget"].parts["load_button"].clicked.connect(self.handle_load_preset)
        if hasattr(self.form["presets_widget"].parts["save_button"], "clicked"):
            self.form["presets_widget"].parts["save_button"].clicked.connect(self.handle_save_preset)


def _build_form() -> dict[str, Any]:
    _qtcore, _qtgui, qtwidgets = load_qt()
    favorites_widget = FavoritesListWidget()
    recents_widget = RecentListWidget()
    presets_widget = PresetListWidget()
    if qtwidgets is None:
        return {
            "widget": object(),
            "favorites_widget": favorites_widget,
            "recents_widget": recents_widget,
            "presets_widget": presets_widget,
            "template": FallbackCombo(),
            "template_summary": FallbackLabel(),
            "favorite_template_status": FallbackLabel(),
            "favorite_template_button": FallbackButton("Toggle Template Favorite"),
            "variant": FallbackCombo(["Template Default"]),
            "variant_summary": FallbackLabel("Template defaults are active."),
            "favorite_variant_status": FallbackLabel(),
            "favorite_variant_button": FallbackButton("Toggle Variant Favorite"),
            "preview": FallbackText(),
            "create_button": FallbackButton("Create Controller"),
            "status": FallbackLabel(),
        }

    widget = qtwidgets.QWidget()
    root = qtwidgets.QVBoxLayout(widget)
    header = qtwidgets.QLabel("Create a controller from a template and optional variant.")
    header.setWordWrap(True)
    shortcuts = qtwidgets.QHBoxLayout()
    shortcuts.addWidget(favorites_widget.widget)
    shortcuts.addWidget(recents_widget.widget)
    form = qtwidgets.QFormLayout()
    template = qtwidgets.QComboBox()
    template_summary = qtwidgets.QLabel()
    template_summary.setWordWrap(True)
    favorite_template_status = qtwidgets.QLabel()
    favorite_template_status.setWordWrap(True)
    favorite_template_button = qtwidgets.QPushButton("Toggle Template Favorite")
    variant = qtwidgets.QComboBox()
    variant_summary = qtwidgets.QLabel()
    variant_summary.setWordWrap(True)
    favorite_variant_status = qtwidgets.QLabel()
    favorite_variant_status.setWordWrap(True)
    favorite_variant_button = qtwidgets.QPushButton("Toggle Variant Favorite")
    preview = qtwidgets.QPlainTextEdit()
    preview.setReadOnly(True)
    create_button = qtwidgets.QPushButton("Create Controller")
    status = qtwidgets.QLabel()
    status.setWordWrap(True)
    form.addRow("Template", template)
    form.addRow("", template_summary)
    form.addRow("", favorite_template_status)
    form.addRow("", favorite_template_button)
    form.addRow("Variant", variant)
    form.addRow("", variant_summary)
    form.addRow("", favorite_variant_status)
    form.addRow("", favorite_variant_button)
    root.addWidget(header)
    root.addLayout(shortcuts)
    root.addLayout(form)
    root.addWidget(preview)
    root.addWidget(presets_widget.widget)
    root.addWidget(create_button)
    root.addWidget(status)
    return {
        "widget": widget,
        "favorites_widget": favorites_widget,
        "recents_widget": recents_widget,
        "presets_widget": presets_widget,
        "template": template,
        "template_summary": template_summary,
        "favorite_template_status": favorite_template_status,
        "favorite_template_button": favorite_template_button,
        "variant": variant,
        "variant_summary": variant_summary,
        "favorite_variant_status": favorite_variant_status,
        "favorite_variant_button": favorite_variant_button,
        "preview": preview,
        "create_button": create_button,
        "status": status,
    }


def _template_label(item: dict[str, Any], favorite: bool = False) -> str:
    template = item["template"]
    prefix = "★ " if favorite else ""
    return f"{prefix}{template['name']} ({template['id']})"


def _variant_label(item: dict[str, Any], favorite: bool = False) -> str:
    variant = item["variant"]
    prefix = "★ " if favorite else ""
    return f"{prefix}{variant['name']} ({variant['id']})"
