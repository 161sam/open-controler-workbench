
# Architecture

## Rolle des Repos

FreeCAD-basierte Design-Schicht für Controller-Hardware.

Keine Runtime. Kein OCF Framework-Core.

## Architekturprinzipien

- UI ≠ Logik
- Schema-first
- FreeCAD nur Adapter
- Zwischenrepräsentationen testbar halten

## Layer

### 1. UI / Workbench
- workbench.py
- commands/

### 2. Domain
- controller.py
- component.py

### 3. Schema
- loader.py
- validator.py

### 4. Generator
- controller_builder.py
- mechanical_resolver.py

### 5. Geometry
- primitives.py
- freecad_api/shapes.py

The geometry pipeline is staged through `ControllerBuilder` plans:
surface resolution, body plan, top plate plan, cutout primitive collection, and boolean planning.

### 6. Layout
- grid.py
- placement.py
- strategies.py
- zone_layout.py

### 7. Services
- controller_service.py
- controller_state_service.py
- document_sync_service.py
- layout_service.py
- constraint_service.py

`ControllerService` is a compatibility facade.
State mutations live in `ControllerStateService`.
FreeCAD document rebuild and visual refresh live in `DocumentSyncService`.

### 7a. Project State
- freecad_api/model.py
- freecad_api/state.py

Project state is persisted on the `OCW_Controller` document object.
`ProjectJson` is the primary source of truth for controller projects.
Legacy document metadata and `OCW_State` containers are migration inputs only.
Interactive preview state is not persisted in `ProjectJson`.
Preview tools store transient payloads in document metadata under `OCWDragPreview`.
Committed state lives in `ProjectJson`; preview state lives only in metadata and drives overlay-only ghosts.

Parameterized projects persist their roundtrip linkage in project state:

- `meta.template_id` points to the source template
- `meta.variant_id` points to the source variant when a variant created the project
- `meta.parameters.values` stores the current project-scoped editable parameter values
- `meta.parameters.sources` stores where each current value came from
- `meta.parameters.preset_id` stores the active template preset, if one is selected
- `meta.overrides` stays as compatibility payload and legacy fallback source, not as the primary editable parameter store

This keeps parameter editing project-scoped while still allowing a reopened document to be re-resolved through the normal template or variant pipeline.

Generated document geometry is owned by the `OCW_Generated` group.
Regular cleanup and rebuild paths operate on group membership instead of global name scans.
Keepout helper geometry is overlay-driven by default and is only materialized as document objects in explicit debug mode.
The document tree uses `OCW_Controller` as the visible project root.
`OCW_Controller` only claims `OCW_Generated` as a tree child.
`OCW_Overlay` remains a separate visual helper object instead of being implicitly nested under the controller root.

### 8. Export
- exporters/
- ocw_kicad/

## Datenfluss

Schema → Domain → Resolver → Geometry → FreeCAD → Export

### Parameter Resolution Flow

Parameterized templates follow a strict value-resolution path before layout or builder work starts:

- template parameter defaults
- optional template preset values
- project or runtime overrides
- direct parameter bindings into controller, layout, zones, or components
- `${parameters.<id>}` substitution in template fields

The important boundary is:

State → template or variant resolver → resolved template data → layout engine / builder / sync

UI panels only edit staged parameter values or store them in project state.
They do not push ad-hoc geometry values directly into builder code.

For reopened documents the roundtrip is:

- load `ProjectJson`
- recover template or variant linkage plus saved project parameters
- rebuild the parameter UI model from registry-resolved schema
- apply edited project values back through the resolver
- regenerate controller state and geometry through the normal sync path

Legacy documents without explicit `meta.parameters` can still fall back to legacy overrides when available, but the UI marks that state clearly instead of silently assuming a fully modern parameter roundtrip.

## Zielarchitektur

- Schema-driven Design
- Library-driven Komponenten
- reproduzierbare Layouts

See also:

- `docs/ARCHITECTURE_FREECAD_WORKBENCH.md`
