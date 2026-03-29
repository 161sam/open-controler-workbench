# 🧱 GeneratorWorkbench Architektur (FINAL)

## 🎯 Ziel

Die bisherige **Open Controller Workbench (OCW)** wird zu einer generischen Plattform transformiert:

> **GeneratorWorkbench ist eine plugin-basierte FreeCAD-Workbench für template- und component-basierte Konstruktion.**

Der Fokus liegt auf:

* Wiederverwendbarkeit
* klarer Trennung von Core und Domain
* Erweiterbarkeit durch Plugins
* stabiler, konsistenter Workflow

---

# 1. 🔥 Systemübersicht

## 1.1 Core (GeneratorWorkbench)

Der Core ist vollständig **domain-neutral**.

### ❌ Core darf NICHT enthalten

* MIDI-spezifische Logik
* PCB-/KiCad-spezifische Logik
* TopPlate-/Controller-Modelle
* jegliche Domain-spezifischen Annahmen

---

### ✅ Core enthält

* Template Engine (generisch)
* Component System (generisch)
* Placement System (Drag, Move, Select)
* Tree Model (generisch)
* Document Model
* Plugin Runtime
* Dependency Resolver
* Sync Pipeline
* Validation Pipeline (hook-basiert)
* Export Pipeline (hook-basiert)

---

## 1.2 Plugin-Typen

### 🟢 Domain Plugin (GENAU 1 aktiv)

Beispiele:

* `plugin_midicontroller`
* `plugin_bike_trailer`

Definiert:

* Templates
* Component Libraries
* Validatoren
* Exporter
* Tree-Struktur
* Default-Werte
* Commands

---

### 🔵 Dependency Plugin (0–n aktiv)

Beispiele:

* `ocw_kicad`
* `ocw_fasteners`
* zukünftig: CAM, BOM, Simulation

Eigenschaften:

* werden automatisch geladen
* erweitern Funktionalität
* definieren KEINE Hauptdomäne

---

# 2. 🧠 Plugin Activation Model

## Regeln

* ✅ genau **1 Domain Plugin aktiv**
* ✅ Dependencies werden automatisch geladen
* ❌ keine parallelen Domain Plugins
* ❌ keine gemischten Component Libraries

---

## Aktivierung

### Neues Dokument

* Auswahl eines Templates → aktiviert Plugin implizit
* Auswahl eines Plugins → lädt Templates & Libraries

---

### Bestehendes Dokument

Dokument enthält Metadaten:

```yaml
plugin_id: midicontroller
plugin_version: 0.1.0
```

→ Plugin wird automatisch geladen

---

### Plugin-Wechsel

* ❌ nicht erlaubt für bestehende Dokumente
* ✅ nur bei leerem Dokument möglich

---

# 3. 📦 Plugin Manifest (verbindlich)

Jedes Plugin enthält eine Datei:

`plugin.yaml`

---

## Beispiel: MIDI Controller Plugin

```yaml
id: midicontroller
type: domain
name: MIDI Controller
version: 0.2.0

depends_on:
  - ocw_kicad

templates:
  - templates/pad_grid_4x4.yaml
  - templates/fader_strip.yaml

component_libraries:
  - components/buttons.yaml
  - components/encoders.yaml
  - components/displays.yaml

validators:
  - pcb_clearance
  - component_spacing

exporters:
  - kicad_layout

document_type: midicontroller_project

tree:
  groups:
    - controls
    - displays
    - pcb
    - mounting
```

---

## Beispiel: Bike Trailer Plugin

```yaml
id: bike_trailer
type: domain
name: Bike Trailer
version: 0.1.0

depends_on:
  - ocw_fasteners

templates:
  - templates/trailer_basic.yaml
  - templates/trailer_long.yaml

component_libraries:
  - components/wheels.yaml
  - components/hitches.yaml
  - components/frame.yaml

validators:
  - wheel_clearance
  - frame_strength

exporters:
  - cut_list
  - assembly_parts

document_type: bike_trailer_project

tree:
  groups:
    - frame
    - wheels
    - hitch
```

---

# 4. 📄 Dokumentmodell

Jedes Dokument enthält:

```python
plugin_id: str
plugin_version: str
document_type: str
```

---

## Konsequenzen

* Dokumente sind **plugin-gebunden**
* keine Cross-Domain-Kombinationen
* reproduzierbares Verhalten
* stabile Lade-Logik

---

# 5. 🔌 Core ↔ Plugin Schnittstellen (verbindlich)

Der Core kommuniziert ausschließlich über definierte Interfaces.

---

## TemplateProvider

```python
get_templates() -> list[Template]
```

---

## ComponentLibraryProvider

```python
get_components() -> list[ComponentDefinition]
```

---

## ValidatorProvider

```python
validate(document) -> list[ValidationResult]
```

---

## ExporterProvider

```python
export(document, target)
```

---

## CommandProvider

```python
get_commands() -> list[Command]
```

---

## TreeModelProvider

```python
build_tree(document) -> TreeStructure
```

---

# 6. ⚙️ Runtime Flow

## Beim Start

1. Plugin Loader scannt verfügbare Plugins
2. Registry wird aufgebaut

---

## Beim Öffnen eines Dokuments

1. plugin_id wird gelesen
2. Domain Plugin wird geladen
3. Dependencies werden geladen
4. Registry wird aktiviert

---

## Während der Nutzung

* Template-Verarbeitung → Core
* Component Definitions → Plugin
* Placement → Core
* Validation → Plugin Hooks
* Export → Plugin Hooks

---

# 7. 🧪 Refactor Plan

## Phase 1 – Analyse

* Identifikation aller MIDI-spezifischen Komponenten

---

## Phase 2 – Extraction

* Templates → `plugin_midicontroller`
* Components → `plugin_midicontroller`
* Validatoren → `plugin_midicontroller`
* Exporter → `plugin_midicontroller`

---

## Phase 3 – Core Clean

* Entfernung aller Domain-Abhängigkeiten
* Einführung klarer Interfaces

---

## Phase 4 – Plugin Runtime

* Plugin Loader
* Aktivierungslogik
* Dependency Resolver

---

## Phase 5 – Proof Plugin

* Implementierung `plugin_bike_trailer`
* Validierung der generischen Architektur

---

# 8. ❗ Harte Regeln

* Core bleibt domain-neutral
* Domain-Logik gehört ausschließlich in Plugins
* genau ein Domain Plugin aktiv
* Dokumente sind plugin-gebunden
* Plugins definieren Verhalten, nicht der Core

---

# 9. 💥 Ergebnis

Das System ermöglicht:

* mehrere unabhängige Produktdomänen
* Wiederverwendung derselben Workbench
* klare Architektur ohne Vermischung
* einfache Erweiterbarkeit
* stabile und nachvollziehbare Dokumente

---

# 🚀 Perspektive

GeneratorWorkbench ist nicht nur ein Tool, sondern eine Plattform für:

* Hardware-Design
* modulare Konstruktion
* parametrisierte Systeme
* plugin-basierte Engineering-Workflows

---

**Status:** verbindliche Architektur für v0.2+
