# Interaction Priority Model

GeneratorWorkbench uses a strict visual and behavioral priority order for 3D interaction.

## Layers

The current interaction layers are:

1. active tool
2. active inline edit
3. handle hover
4. selection
5. passive overlay

Snapping and axis-lock feedback are subordinate to the currently active tool and are treated as contextual feedback, not as primary control layers.

## Priority Rules

### 1. Active Tool

Placement and drag tools have highest priority.

- inline handles are hidden
- selection remains visible but is not the primary affordance
- preview and snap feedback belong to the active tool

### 2. Active Inline Edit

Inline edit becomes dominant only when no placement or drag tool is active.

- selected component remains highlighted
- active handle is visually stronger than passive handles
- `ESC` cancels the current inline edit session

### 3. Handle Hover

Handle hover is only available when:

- exactly one component is selected
- no external active tool is running
- no conflicting placement or drag interaction is active

### 4. Selection

Selection is the default idle interaction layer.

- it keeps the selected component visually anchored
- it enables inline handles when allowed
- it never overrides an active tool

### 5. Passive Overlay

Surface, zones, keepouts, cutouts, and diagnostic overlays remain visible but visually subordinate.

## Handle Visibility Rules

Handles are shown only when:

- exactly one component is selected
- no placement tool is active
- no drag tool is active
- no higher-priority interaction is blocking them

Handles are hidden when:

- selection is empty
- multiple components are selected
- an external active tool is running
- the document changes or closes

## Visual Hierarchy

The visual order is:

1. active handle
2. hovered handle
3. placement / move preview
4. selected component
5. snap and axis guides
6. passive overlay geometry

This keeps the user focus on the currently editable target instead of on secondary diagnostics.

## Cursor Rules

- `place`: active placement
- `drag_ready` / `drag_active`: drag interaction
- `edit_ready` / `edit_active`: inline edit
- `pick`: idle selection

Cursor changes are only used when the interaction affordance actually changes.
