
# Executive Summary

Die Open Controller Workbench (OCW) setzt auf eine persistent rechte Seitenleiste (“Dock”) als Hauptsteuerzentrale. Dort finden sich die Kerntasks Create, Layout, Components, Plugins und Constraints. Technisch verwendet die Workbench ein dockbares QDockWidget und viele custom Qt-Panels. Unsere detaillierte Analyse zeigt allerdings erhebliche UX- und Code-Mängel:

    Inkonsistente Icon-Nutzung: Viele Commands nutzen nur das generische default.svg-Icon, was die Toolbar visuell unklar macht. Einige fehlen komplett.
    Veraltete UI-Struktur: Der aktuelle Dock-Workflow ist überladen: doppelte Navigation (großer Stepper oben und Tabs unten), zu viele Panels und Texte, sowie fehlende visuelle Hierarchie. UI-Elemente sind minimalistisch, oft textbasiert und schlecht strukturiert.
    Layout-Instabilität: Im Code fanden wir mehrere Stellen mit fehlerhaften Layout-Parametern: z.B. QLayouts mit Widgets statt mit Layouts (TypeError: addLayout(QWidget)), zu enge Margins und teils fixe Höhen. Die Folge sind abgeschnittene Titel und gequetschte Sections.
    Helper-/Builder-Inkonsistenzen: Es existieren mehrere “Hilfsfunktionen” für UI-Gruppenboxen und Panels (z.B. _group_box), aber deren Nutzung ist lückenhaft. Manche UI-Builder geben Widgets zurück, andere QLayouts, was zu Verwirrung führt.
    Testabdeckung: Bestehende Tests decken einige Qt-Kompatibilitätsfälle ab (etwa test_qt_compat.py), aber prüfen die kritischen UI-Pfade (Panels, ScrollAreas, Direct-Drag) nur unzureichend.

Empfehlungen: Wir empfehlen eine hybride Architektur: Den Dock als primäre und persistente Steuerzentrale beibehalten, wichtige Workflows aber bei Bedarf in fokussierte Task-Panels auslagern. UX- und UI-technisch muss die Dock-Oberfläche entschlackt und systematisch restrukturiert werden. Insbesondere sollte sie auf einen einzigen nahtlosen Flow reduziert werden (z.B. Create → Layout → Components → Validate → Plugins), doppelte UI-Ebenen vermeiden, konsistente Abstände/Typografie einführen und visuelle Hierarchien stärken.

Weiterhin muss der Code stabilisiert: alle Layout-Issues (QScrollArea, QSizePolicy, fixe Höhen) beheben, UI-Builder vereinheitlichen und fehlende Icons ergänzen. Zur Zukunftsfähigkeit sollte die Workbench direkt manipulative Interaktionen unterstützen (Drag/Drop im 3D-View, Klick-zum-Platzieren statt umständliche Formulare). Im Anhang finden sich eine Kategorisierte To-Do-Liste, ein Flowchart für den neuen Dock-Flow und ein Zeitplan für die Interaktionsfeatures (als Mermaid-Diagramme).
1. Code-Review: UI/UX und Layout-Probleme

    Icons & Toolbar: Der Befehlssatz ist grafisch unvollständig. In BaseCommand ist standardmäßig ICON_NAME = "default" definiert, und icon_path(name) nutzt nur "default.svg" bei fehlenden Icons. Viele Commands besitzen daher nur den generischen Platzhalter. Beispiel: CreateComponentCommand oder AddComponentCommand verwenden kein eigenes Icon. Wir empfehlen für jeden wichtigen Befehl ein passendes SVG (z.B. „add_component.svg“, „validate.svg“). Eine Referenz ist die Auto-Layout-Command-Klasse, die ICON_NAME = "apply_layout" setzt, wodurch sie korrekt ein Icon erhält.

    Panels und Dock: Die Workbench-Hauptklasse ProductWorkbenchPanel fügt alle Sub-Panels in ein QTabWidget im Dock ein. Dort werden Tabs Create, Layout, Components, Plugins untereinander dargestellt. Gleichzeitig existieren aber oben Step-Buttons („1 Create, 2 Layout, 3 Validate“, etc.), was die Navigation dupliziert. Dieser Aufbau wirkt überladen. Zudem ist der Dock-Titel uneinheitlich benannt: Im Panel steht „Open Controller Studio“, anderswo „Workbench“. Die Titel-Zeile wird mit Qt-Labels und harten Styles (z.B. font-weight:600) umgesetzt und sollte einheitlich sein.

    Layout-Stabilität: Im Code fanden sich mehrere Fehlerquellen:
        TypeError „addLayout(QWidget)“: In plugin_list.py wurde ein Widget (Row-Widget) fälschlich mit addLayout eingehängt (statt addWidget) – dieser Bug wurde fixiert. Generell müssen QLayouts nur mit anderen Layouts kombiniert werden.
        Fixe Höhen & Margins: Viele Panels setzen FixedHeight oder sparsame contentsMargins. Beispiel: In _group_box() wird lediglich setContentsMargins(4,4,4,4) verwendet, was in aktuellen Screenshots zu abgeschnittenen Titeln führte. Überall dort, wo Text abgeschnitten erscheint (z.B. in Layout- und Components-Panels), muss das Layout-Minimum erhöht werden und setFixedHeight entfernt werden. Mehrwartungsfreundlich ist statt fester Höhen eine geeignete QSizePolicy.Preferred/Expanding zu setzen.

    Widget vs. Layout: Mehrere UI-Helper mischen Widgets und Layouts. Beispiel QFormLayout in Panels fügt Zeilen aus FallbackLabel und Qt-Widgets zusammen. Tests (test_qt_compat.py) wurden ergänzt, um sicherzustellen, dass solche Formulare sicher mit Mixed-Inhalt umgehen können. Wir empfehlen klare Trennung: Verwende addWidget() für Widgets, addLayout() nur für Layout-Objekte. So wird das TypeError-Problem vermieden.

    Helper-/Builder-Konsistenz: Es existieren mehrfach ähnliche „Panel-Builder“-Funktionen. Z.B. _group_box(title, child) (siehe Code oben) wird für Überschriften genutzt. Andere Panels verwenden eigene Hilfen oder schreiben Layout code dupliziert. Ein gemeinsames _group_box mit konsistenten Margins ist gut, muss aber überall eingesetzt werden. Generell sollten wiederkehrende Muster (Statuspanel, Info-Header, Formgruppen) in zentrale Helfer ausgelagert werden.

    Command- und Icon-Einsatz: Neben generischen Default-Icons sind die tatsächlichen Buttons oft textlastig oder mit kryptischen Icons. Beispiel: OpenControllerWorkbench legt in Initialize mehrere Toolbars an, aber viele dieser Buttons fehlen echte Icons oder Beschriftungen. Der Code produziert Toolbars wie „OCW Components“ oder „OCW Layout“ – solche Texte sollten als Tooltips, nicht als Symbole dienen.

    Dock/Task-Panel-Architektur: Die OCW-Dokumentation empfiehlt einen Hybrid-Ansatz: Das Dock bleibt als persistenter Übersichts-/Statusbereich, während aufgabenspezifische Abläufe als Task-Panels ausgelagert werden (z.B. Create Controller oder Plugin Manager als modale Dialoge). Unser Code zeigt bereits Task-Panels für Layout und Constraints, aber deren UI ist rudimentär (Plain-Text-Rendering in ConstraintsTaskPanel). Der Umstieg zu mehr Task-Panels (z.B. ein geführter Create-Flow) sollte sorgfältig erfolgen. Der Dock sollte die ständige „Inspektor“-Funktion behalten (Status, Overlay, Auswahl), wie in der Strategieformulierung betont wird.

Insgesamt ist der Code an vielen Stellen fixbar: Icons ergänzen, Layouts bereinigen, redundante UI-Duplikate entfernen. Die Architekturempfehlung des Teams stimmt überein, allerdings ist die aktuelle Implementierung „noch zu sehr alles auf einmal“.
2. UX-Bewertung

Gutes / Schlechtes: Die Workbench hat das richtige Grundkonzept – ein integriertes UI zur Steuerung des Controller-Designs – aber die Details stören momentan die Nutzererfahrung:

    Workflow-Kohärenz: Gut ist, dass die Hauptschritte (Create, Layout, Components, Plugins) vorhanden sind. Schlechter ist die Doppel-Navigation: Nutzer werden mit Step Buttons oben und Tabs darunter verwirrt. Der Fokus sollte auf einem Fluss liegen.
    Visuelle Klarheit: Die UI wirkt fragmentiert: Viele separate Kästen und Texte teilen den Raum ohne klare Prioritäten. Labels, Inputs und Buttons haben bislang keine durchgängige Typografie (Schriftarten/-größen) oder gleichmäßiges Spacing. Die klare visuelle Kaskade von Titel → Abschnitt → Feld fehlt. Vergleichbar mit etablierten Workbench-Standards (z.B. PartDesign oder Sketcher), wo die Seitenleiste ruhig und strukturiert ist, erscheint unsere Dock-Oberfläche „knallig“ und unruhig.
    Platznutzung: Zu viel Platz wird aktuell für Meta-Infos (Overlay-Status, Vorschau-Text oben) verschwendet, während aktive Felder nach unten gedrängt werden. Scrollbalken tauchen zu schnell auf. Inhalte wirken gequetscht (wie in den Screenshots zu sehen).
    Interaktion: Bislang sind fast alle Aktionen über Formulare und Buttons realisiert. Das ist für einige Fälle nicht ideal: UI-Paradigmen wie „Direct Manipulation“ (komponenten per Drag im 3D verschieben) sind nur rudimentär angedacht (z.B. DragMoveComponentCommand). Das Potenzial für schnelles Interagieren direkt im 3D (Click-to-Place, Drag-to-Move) wird bisher nicht voll ausgeschöpft.

Bewertung: Unter Aspekten von Usability und FreeCAD-Konventionen erfüllt die Workbench die Grundfunktion, aber ist oberflächlich noch nicht “schlüssig” genug. Die doppelte Layer-Navigation verletzt klare Erwartungshaltung. Die UI-Ästhetik ist im Fachbereich “hässlich aber funktional”. Für eine professionelle CAD-Erweiterung sollte sie ruhiger, einheitlicher und erkennbar an FreeCAD angepasst werden.
3. Verbesserungsempfehlungen & Fixes

Basierend auf obiger Analyse ergibt sich ein priorisiertes Maßnahmenportfolio:
Priorität	Maßnahme	Referenz-Code/Ort	Beschreibung
Hoch	Icons ergänzen	BaseCommand (z.B.)	Ersetze den Default-Icon-Fallback. Für jeden Command eine spezifische SVG (z.B. „add_component.svg“, „validate.svg“).
Hoch	UI-Struktur vereinfachen	ocw_workbench/workbench.py	Entferne doppelte Navigation: nutze nur Tabs oder Stepper. Reduziere den großen Header mit Erklärtext.
Hoch	Layout-Stabilität sicherstellen	Allerorts (z.B. Layout-/Constraints-Panel)	Fixe QSizePolicy und contentsMargins. Entferne feste Höhen (setFixedHeight). Stelle QScrollArea.setWidgetResizable(True) sicher.
Mittel	Helper-Konsolidierung	ocw_workbench/workbench.py	Vereinheitliche UI-Builder: Nutze zentrale _group_box-Funktion überall für Abschnittsgroups (siehe Code, L873-881). Einheitliche Margins.
Mittel	Text-/Label-Konsistenz	workbench.py, panels/...	Vereinheitliche Terminologie („Workbench“ statt „Studio“), kürze lange Hilfetexte, verwende prägnante Labels und Tooltips.
Mittel	Task Panels erweitern	docs/ui/TASK_PANEL_STRATEGY.md	Plane Task-Panels für Create Controller und Plugin-Install. Diese sollten schrittweis geführt sein, wie in der Strategie empfohlen.
Niedrig	Direkte 3D-Interaktion	DragMoveComponentCommand	Vollende Funktionen wie start_component_drag_mode, füge Click-to-Place hinzu, teste in der 3D-Ansicht.
Niedrig	UI-Tests erweitern	tests/unit/…	Erstelle Tests für neue Layout-Stabilität (Scrollverhalten), Drag-Modus (Mock).

Tabelleninhalt: Die ersten drei Punkte (Icons, Struktur, Layout) sind kritisch: Sie machen die Oberfläche sofort nutzbarer. Mittelfristig folgen Konsolidierung und Sprachkürzungen. Niedrigere Priorität haben die interaktiven Erweiterungen, da sie auf einem stabileren UI-Grid aufsetzen sollten.
Beispiel-Code-Referenzen

    Icons: In BaseCommand.resources() wird Pixmap: icon_path(self.ICON_NAME) verwendet. Ohne eigenes ICON_NAME fällt icon_path auf default.svg zurück.
    Layout: _group_box() legt z.B. nur 4px Innenrand fest. Das ist zu knapp: Empfohlen wäre z.B. 8–12px. Auch wurde in Panels oft QFormLayout mit Standardabständen genutzt; dort sollten wir setVerticalSpacing(8) setzen.
    Dock-Bau: Der Dock-Titel wird im Code mit create_or_reuse_dock("Open Controller", panel.widget) gesetzt. Hier könnten wir einen aussagekräftigeren Titel oder Icon hinzufügen (z.B. create_or_reuse_dock("Open Controller Workbench", widget)).

Diese Code-Stellen geben genau an, wo anzusetzen ist.
4. Interaction Design: Direkte Manipulation

Die Workbench-Architektur erlaubt bereits erste Schritte Richtung direkter 3D-Interaktion (siehe DragMoveComponentCommand). Für eine schlanke Bedienung empfehlen wir:

    Drag & Drop im View: Komponenten direkt per Maus verschiebbar machen. start_component_drag_mode sollte aktiviert werden, sobald ein Objekt selektiert wird. Anschließend könnte ESC den Abbruch signalisieren (wird schon durch das Info-Fenster unterstützt). Eventuell click-Modus ergänzen, um Objekte mit einem Klick zu setzen.

    Platzieren durch Klick: Anstatt (oder ergänzend zu) Parametern im Panel sollte ein Klick auf eine Position im 3D-Fenster eine Komponente dort platzieren. Das kann über ein modales Kommando realisiert werden, das den Klick im 3D view abfängt (z.B. PlacementCommand in FC).

    Weniger Formulare, mehr Kontext-UI: Reduziere lange Textfelder. Wenn der Nutzer z.B. eine Komponente auswählt, sollte ein Inline-Editor im Panel erscheinen, der nur benötigte Parameter zeigt. Statt „Vielschritt-Dialog“ lieber dynamische Paneele oder On-Cam-Widgets (wie Koordinaten-Feedback in der 3D-View).

Priorisierte Action-Items:

    Drag & Click implementieren: Setze start_component_drag_mode nahtlos mit ESC-Abbruch um, teste im 3D. Dauer: 2-3 Tage.
    Click-to-Place: Füge ein Kommando hinzu, das auf Klick-Events im 3D reagiert, und einen „Abbrechen“-Trigger (eventuell FreeCAD’s ViewObserver). Dauer: 1-2 Wochen.
    Panel-Reduktion: Überarbeite Panels so, dass stattdessen modulare Parameter-Widgets erscheinen. Dauer: 1-2 Wochen nach obigen.

Relevante Code-Bereiche:

    ocw_workbench/workbench.py: Methode start_component_drag_mode (nicht gezeigt hier, aber in code) und ensure_workbench_ui, die den Fokus setzt.
    ocw_workbench/commands/drag_move_component.py und möglicherweise neues PlacementCommand.

5. Vergleich aktuelle vs. empfohlene UI-Komponenten
Komponente	Ist (aktuell)	Soll (Empfehlung)	Begründung
Navigation	Großer Stepper oben + Tabs	Nur ein Set (z.B. kompakte Tabs)	Vermeidet doppelte Steuerung, erleichtert Fokus
Header	Großes Titel- und Info-Panel (Dashboard)	Kleiner Titel, kurze Statuszeile	Mehr Arbeitsraum, klarere Prioritäten
Überschriften	QGroupBox oder Labels ohne Abstand	Einheitliche Section-Header mit sinnvoller Margin (8px)	Verhindert Textkollisionen und konsistente Hierarchie
Panel-Boxen	Viele QGroupBox mit grauen Rahmen	Weniger Boxen, mehr Abstand, ggf. QFrame ohne Strich	Ruhigeres Aussehen, weniger „Box-Trap“
Formlayouts	QFormLayout ohne festen Spacing	QFormLayout mit setVerticalSpacing(8)	Bessere Lesbarkeit, vermeidet optische Enge
Buttons	Unterschiedliche Breiten, Text vs Icon	Einheitliche Größe, primärer vs. sekundärer Stil	Klare Action-Hierarchie
Statuszeile	Langer Overlay-Text im Panel	Kompakter Inline-Status (Textleiste)	Blick auf 3D wichtiger als große Stats-Texte
Icons in Toolbar	Teilweise default.svg-Icons	Passende SVG-Icons, einheitlicher Stil	Erhöht Wiedererkennbarkeit und Professionalität
6. Priorisierter Maßnahmen- und Zeitplan (High/Med/Low)

2026-04-05
2026-04-12
2026-04-19
2026-04-26
2026-05-03
Icons ergänzen             Unittests erweitern        Panel-Struktur vereinfachenLayout-Fehler beheben      Integrationstests          Drag & Drop (3D)           Click-to-Place             Form-Reduktion             UI-PolishUX-FeaturesTestsRoadmap: Open Controller Workbench

Zeitplan in Tagen bei 2QA pro Woche. Hohe Priorität (rot) für UI-Stabilisierung, Medium (blau) für neue UX-Features.
7. Neue Dock-Fluss (Single-Flow) – Flowchart

Create

Layout

Components

Validate

Plugins

Dieser Flowchart zeigt den empfohlenen einen Navigationspfad der Dock-Leiste: Der Nutzer durchläuft konsequent Create → Layout → Components → Validate → Plugins, statt paralleler Schritt-Buttons und Tabs.
8. Akzeptanzkriterien und Testing

    Die überarbeitete UI lädt ohne Fehler und enthält nun aussagekräftige Icons statt Platzhalter.
    Der Dock-Header ist kompakt (nur Titel + Status) und Konsistenz in Texten ist hergestellt.
    Es gibt nur eine Navigator-Ebene (Tabs) ohne redundanten Workflow-Buttons.
    Vertikale Abstände/Margins sind angepasst; es gibt keine abgeschnittenen Texte mehr (Sections vollständig sichtbar).
    Neue Interaktion (Drag & Click) funktioniert fehlerfrei.
    Automatisierte Tests (Unit/Smoke) decken Layout- und Drag-Modi ab (z.B. ein Test test_qt_compat.py für ScrollArea-Verhalten). All Tests sollen ohne Fehler durchlaufen.

Entsprechende Code-Reviews, zitiert aus den lokalen Quellen, haben die Problembereiche bestätigt. Mit den oben genannten Maßnahmen wird die Workbench stabiler, intuitiver und wartungsfreundlicher.
