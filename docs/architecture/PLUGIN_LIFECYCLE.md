# Plugin Lifecycle

## Rule

Each GeneratorWorkbench document is bound to exactly one domain plugin.

The binding is stored in project state metadata:

- `meta.plugin_id`
- `meta.plugin_version`
- `meta.document_type`

The same values are mirrored onto the persisted controller object for inspection and recovery.

## New Document

When a document enters the workbench lifecycle:

1. the active domain plugin is resolved
2. the document is bound to that plugin
3. default controller state is bootstrapped only if the document is still empty

An empty bootstrap document may still switch plugins before any template, variant, parameters, or components are applied.

## Existing Document

When an existing document is opened or activated:

1. plugin binding is read from project state metadata
2. the matching domain plugin is activated
3. strict plugin-aware registries reload against that plugin

If metadata is missing, the lifecycle tries to infer the plugin from persisted template, variant, or component references. Legacy unbound projects fall back to `midicontroller` only when a meaningful persisted state exists and no better inference is possible.

## Plugin Switch Rules

- Empty or bootstrap-only document: plugin switch allowed
- Bound document with meaningful project content: plugin switch rejected
- Re-activating the already bound plugin: always allowed

## Error Cases

- Unknown plugin id in document: activation fails with a clear error
- Bound document requested with a different plugin: rejected
- Missing plugin root in strict mode: adapter raises immediately
- Missing metadata on legacy documents: inferred when possible, otherwise legacy default is applied

## Core Lifecycle API

Primary helpers:

- `bind_document_to_plugin(...)`
- `get_document_plugin_id(...)`
- `activate_plugin_for_document(...)`
- `can_switch_plugin_for_document(...)`

These helpers are intentionally small. Document binding stays coupled to the existing persisted project state instead of introducing a second persistence model.
