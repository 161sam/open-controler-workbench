# Workbench Icons

The toolbar and menu commands now use dedicated SVG icons from `resources/icons` instead of relying on `default.svg`.

Main icons introduced or refreshed:

- `create_controller.svg`: create a controller from template or variant
- `import_template.svg`: import template data from an `FCStd` file
- `add_component.svg`: add a component to the current controller
- `apply_layout.svg`: run automatic layout
- `move_component.svg`: arm or drag component movement
- `select_component.svg`: focus component editing and selection
- `component_palette.svg`: open the icon-based component palette
- `validate_constraints.svg`: validate placement and spacing rules
- `toggle_overlay.svg`: toggle overlay visibility
- `constraint_overlay.svg`: toggle issue overlay markers
- `snap_to_grid.svg`: snap selection to the active grid
- `measurements.svg`: toggle measurement guides
- `conflict_lines.svg`: toggle conflict connection lines
- `constraint_labels.svg`: toggle issue labels
- `plugin_manager.svg`: open the plugin manager
- `plugin_enable.svg`, `plugin_disable.svg`, `plugin_reload.svg`: plugin state actions
- `duplicate_selected.svg`, `array_horizontal.svg`, `array_vertical.svg`, `grid_array.svg`: layout pattern actions
- `rotate_cw_90.svg`, `rotate_ccw_90.svg`, `rotate_180.svg`, `mirror_horizontal.svg`, `mirror_vertical.svg`: transform actions
- `align_left.svg`, `align_center_x.svg`, `align_right.svg`, `align_top.svg`, `align_center_y.svg`, `align_bottom.svg`, `distribute_horizontal.svg`, `distribute_vertical.svg`: arrangement actions

Additional icons were added for layout pattern, transform, and alignment commands so the main layout toolbar no longer falls back to the generic default icon.

`default.svg` remains the final fallback for commands without a dedicated icon file.
