# Task Panel Strategy

## Purpose

This note defines when the Open Controller Workbench should use:

- the persistent right-side dock
- a FreeCAD task panel via `Gui.Control.showDialog(...)`
- a hybrid of both

It is a planning document for incremental migration, not a request for immediate UI replacement.

## Current Architecture

### Dock-based UI

The main Workbench UI lives in the persistent right dock created by `create_or_reuse_dock(...)` in:

- `ocw_workbench/gui/docking.py`
- `ocw_workbench/workbench.py`

The dock hosts a tabbed shell with these panel areas:

- `Create`
- `Layout`
- `Components`
- `Plugins`

The dock also keeps shared status context visible:

- workbench header
- activity/status
- overlay status
- tab navigation

The dock is currently the primary production UI.

### Existing Task Panels

Task panels already exist, but they are narrow and currently closer to legacy or prototype forms:

- `ocw_workbench/gui/taskpanels/layout_taskpanel.py`
- `ocw_workbench/gui/taskpanels/constraints_taskpanel.py`
- `ocw_workbench/gui/taskpanels/library_taskpanel.py`

They are currently used by older commands such as:

- `ocw_workbench/commands/auto_layout.py`
- `ocw_workbench/commands/move_component.py`
- `ocw_workbench/commands/validate_layout.py`

These task panels do not yet reflect the richer dock panels and currently duplicate simplified UI logic.

### Dialog-based UI

Some flows already use dedicated dialogs:

- `Import Template From FCStd`
- `Template Inspector`

These are naturally workflow-driven and already separate from the persistent dock.

## Architectural Reading

### What belongs in the dock

The dock is best for persistent context and quick switching:

- always-visible project context
- selection-aware editing
- repeated small adjustments
- overlay toggles
- status and validation summary
- plugin status overview

The dock should remain the "control tower" of the Workbench.

### What belongs in a task panel

A FreeCAD task panel is strongest when the user is in a guided, temporary, or modal workflow:

- one focused goal
- a clear accept/cancel lifecycle
- temporary attention shift away from the full sidebar
- actions that feel like "do this now, then return"

Task panels fit workflows better than persistent dashboards.

## Candidate Evaluation

### 1. Create Controller

Current state:

- rich dock-based `CreatePanel`
- includes templates, variants, favorites, presets, parameters, preview

Assessment:

- not purely modal
- users often compare templates, adjust parameters, then return later
- benefits from persistent access while working in the document

Recommendation:

- keep the primary Create experience in the dock
- optionally add a future guided task panel only for first-run onboarding or template-based creation wizard

Conclusion:

- `Dock-first`
- task panel only as an optional guided entry flow later

### 2. Auto Layout

Current state:

- dock-based `LayoutPanel` is richer
- `LayoutTaskPanel` exists and is already used by legacy commands

Assessment:

- running Auto Layout is a focused operation
- users may want a compact modal setup when starting a new placement pass
- however overlay toggles and repeated iteration still benefit from dock visibility

Recommendation:

- adopt a hybrid model
- keep the dock as the main iteration surface
- task panel can remain for a compact "run Auto Layout" flow if it is later rebuilt on top of shared panel logic

Conclusion:

- `Hybrid`
- the dock remains canonical

### 3. Constraints / Validation

Current state:

- dock-based constraints panel is now richer and more navigable
- old `ConstraintsTaskPanel` still exists

Assessment:

- validation summary should remain always reachable
- focused issue review is a natural modal flow
- future "jump to issue" and "next issue" behavior would fit a task panel very well

Recommendation:

- use a hybrid model
- keep the dock for summary, overview, and quick checks
- add a future task panel for focused review / issue navigation / step-through validation

Conclusion:

- `Hybrid`
- validation overview in dock, issue-resolution workflow in task panel

### 4. Plugin Management

Current state:

- full plugin UI lives in the dock

Assessment:

- plugin status is useful reference information, but most plugin actions are administrative and episodic
- install/import/export/remote registry actions are not part of the normal controller editing loop
- plugin management behaves more like a management console than persistent editing context

Recommendation:

- move toward a hybrid model
- keep a compact plugin status/entry point in the dock
- move advanced plugin operations to a dedicated management surface
- that management surface could be a task panel or a dedicated dialog; task panel is appropriate if the flow becomes step-based

Conclusion:

- `Hybrid leaning away from dock`

### 5. Add Component / Library Browsing

Current state:

- dock-based Components panel
- separate component palette dock
- legacy `LibraryTaskPanel`

Assessment:

- library browsing is often transient
- placement itself is workflow-driven and attention-heavy
- however selected-component editing belongs in persistent UI

Recommendation:

- keep selected-component editing in dock
- treat library browsing / add-from-library / placement kickoff as a candidate for a compact task panel later
- component palette dock can remain as a quick-access tool

Conclusion:

- `Hybrid`

## Recommended Target Architecture

### Principle

Use the dock for persistent context.
Use task panels for guided workflows.

### Target split

#### Persistent dock

Keep in the dock:

- project summary
- selection-aware component editing
- lightweight layout controls and overlay toggles
- validation summary
- quick plugin overview / entry points

#### Task panels

Use task panels for:

- focused Auto Layout run/setup
- focused Validation review / issue stepping
- future guided Create wizard
- future Add Component / placement flow
- advanced plugin management if it becomes multi-step

## Migration Recommendation

### Preferred strategy

Do not migrate panel-by-panel by copying UI again.

Instead:

1. keep the dock as the canonical surface for now
2. treat existing task panels as provisional
3. when rebuilding a task panel, compose it from shared Workbench UI logic or shared widget builders
4. avoid maintaining two different feature-complete UIs for the same workflow

### Near-term roadmap

#### Phase 1

- keep dock as primary UI
- document the split of responsibilities
- stop expanding legacy task panels independently

#### Phase 2

- rebuild `ConstraintsTaskPanel` as the first serious hybrid candidate
- focus it on issue review, next/previous issue, and jump-to-component
- keep dock constraints panel as summary + quick access

#### Phase 3

- review `LayoutTaskPanel`
- either modernize it as a compact guided "Run Auto Layout" flow
- or retire it if the dock proves sufficient

#### Phase 4

- decide whether plugin administration should remain dock-based, become dialog-based, or become task-panel-based

## Small Technical Preparation Guidelines

Before any migration:

- keep shared strings and layout helpers centralized
- prefer reusable builders over copying Qt form code into task panels
- keep domain logic in services and panels, not in task panel glue
- route task panels through existing service APIs and existing status formatting where possible

## Explicit Decision

### Recommended architecture

- `Dock-only`: not recommended as the long-term answer
- `Task-panel-only`: not recommended because too much persistent context would be lost
- `Hybrid`: recommended

### Short version

The Open Controller Workbench should become:

- a persistent dock for context, editing, and quick control
- plus focused task panels for modal, guided workflows

### First migration candidate

`Constraints / Validation`

This area has the clearest path to a meaningful task panel without weakening the dock.
