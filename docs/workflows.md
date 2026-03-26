
# Workflows

## Workflow 1 – Setup

- Repo klonen
- Plugin installieren
- Workbench starten

## Workflow 2 – Geometry (Python)

- Controller definieren
- Builder nutzen
- Geometrie erzeugen

## Workflow 3 – Schema Import

- YAML laden
- validieren
- Domain erzeugen
- Geometrie bauen

## Workflow 4 – UI (Ziel)

- Projekt erstellen
- Komponenten platzieren
- Constraints prüfen
- Export

## Workflow 5 – Schema Export

- controller.hw.yaml erzeugen

## Workflow 6 – KiCad Übergabe

- Outline
- Positionen
- Rotation
- Keepouts

## Workflow 7 – Validation

- fehlende Daten
- Kollisionen
- Constraints

## Workflow 8 – Import FCStd -> refine -> save

- FCStd Datei wählen
- Top Surface Referenz wählen
- YAML Template importieren
- Template im Create Panel auswählen
- Controller weiter verfeinern und speichern

## Interactive Tool Lifecycle

- Only one view-interactive tool session may be active at a time.
- Tool start follows the same lifecycle: resolve view, register callbacks once, create or update overlay preview metadata, then wait for commit or cancel.
- Tool cleanup is idempotent: callback deregistration, preview metadata removal, overlay refresh, and session reset can run more than once without crashing.
- `ESC`, document close, active document change, unavailable view, and tool switching all flow through the same cancellation path.
- Successful commits clear transient preview state after the model mutation finishes.
- Failed preview updates or failed commits clear transient state and leave no active callbacks behind.
