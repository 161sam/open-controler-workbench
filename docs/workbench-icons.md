# Workbench Icons

The toolbar and menu commands now use dedicated SVG icons from `resources/icons` instead of relying on `default.svg`.

Main icons introduced or refreshed:

- `create_controller.svg`: create a controller from template or variant
- `import_template.svg`: import template data from an `FCStd` file
- `add_component.svg`: add a component to the current controller
- `apply_layout.svg`: run automatic layout
- `validate_constraints.svg`: validate placement and spacing rules
- `toggle_overlay.svg`: toggle overlay visibility
- `snap_to_grid.svg`: snap selection to the active grid
- `measurements.svg`: toggle measurement guides
- `conflict_lines.svg`: toggle conflict connection lines
- `constraint_labels.svg`: toggle issue labels
- `plugin_manager.svg`: open the plugin manager

Additional icons were added for layout pattern, transform, and alignment commands so the main layout toolbar no longer falls back to the generic default icon.

`default.svg` remains the final fallback for commands without a dedicated icon file.
