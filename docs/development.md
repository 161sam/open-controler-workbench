
# Development Guide

## Setup

```bash
git clone ...
pip install -e .
````

## Struktur

```
domain/
schema/
generator/
geometry/
layout/
services/
commands/
```

## Prinzipien

* keine Logik in Commands
* Domain unabhängig von FreeCAD
* Geometry testbar

## Einstiegspunkte

* init_gui.py
* workbench.py
* controller_builder.py

## Roadmap Dev

1. Schema erweitern
2. Mapping bauen
3. Builder testen
4. GUI erweitern
5. Export stabilisieren

## Tests

* Schema
* Builder
* Resolver
