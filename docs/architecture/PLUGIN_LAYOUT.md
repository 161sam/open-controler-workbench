# Plugin Layout

## Purpose

This layout separates plugin runtime infrastructure from actual plugins.

## Runtime Side

`ocw_workbench/plugins/` now contains only:

- loader and manifest parsing
- activation and lifecycle helpers
- registry and plugin context
- internal technical plugins such as `default_exporters`

It is not the home for domain data packs or integration plugins.

## Top-Level Plugin Root

`plugins/` is now the single runtime root for actual plugins:

- domain plugins such as `plugin_midicontroller` and `plugin_bike_trailer`
- dependency or integration plugins such as `ocw_kicad`
- optional data packs such as `basic_components_pack`, `basic_templates_pack`, and `basic_variants_pack`
- optional exporter plugins such as `export_jlcpcb`, `export_svg_panel`, `export_eurorack`, and `export_mouser`

## ocw_kicad

`ocw_kicad` is now modeled as a top-level integration plugin under `plugins/ocw_kicad/`.

The legacy root package `ocw_kicad/` remains only as a compatibility bridge for existing imports and `ocw_kicad_plugin.py`.

## Why external Was Removed

`ocw_workbench/plugins/external/` created an unnecessary second plugin root.

That split made runtime scanning, release packaging, and plugin ownership harder to reason about. Using one top-level `plugins/` root makes dependency plugins, data packs, exporters, and domain plugins behave consistently.
