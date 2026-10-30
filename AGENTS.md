# Arbeitsregeln für Agenten

## Projektstatus und Umfang

Offizieller Bearbeitungsbeginn der Masterarbeit: 12.10.2026.

Nur die konkret beauftragte Aufgabe bearbeiten. Verbindlicher Einstieg ist
der [Fortsetzungsstand in der README](README.md#projektstatus).

## Einstieg, Zuständigkeiten und Übergaben

- Vor Arbeitsbeginn README und aufgabenrelevante Pläne/Befunde lesen;
  Branch, Commit, lokale Änderungen, weitere Worktrees und Remote-Stand
  einschließlich offener PRs prüfen. Aktive Arbeiten auf anderen Branches
  berücksichtigen. Fehlenden Zugriff benennen; Chat-Zusammenfassungen
  ersetzen diese Prüfung nicht.
- Implementierungschats verantworten beauftragten Code, technische Prüfungen
  und zugehörige Dokumentation. Reviewchats prüfen einen benannten Stand.
  Brainstorming liefert Alternativen und Entscheidungsvorschläge; diese sind
  noch kein Implementierungsauftrag. Schreibchats verwenden belegte Befunde
  und markieren offene Aussagen, statt neue Ergebnisse zu unterstellen.
- An fachlichen Grenzen wechseln, etwa nach Planentscheidung, prüfbarem
  Implementierungsschritt oder Auswertung; nicht erst am Chatlimit.
  Bei längerer Arbeit einen kurzen Fortsetzungsstand am bestehenden
  Arbeitsdokument oder PR pflegen. Keine parallele Projektchronik anlegen.
- Die README hält nur den aktuellen Überblick und verlinkt die Detailquelle.
  Bei Statusänderungen deren Datum und betroffene Statusaussagen abgleichen;
  historische Prüf- und Ausführungsdaten bleiben erhalten. Eingefrorene
  Laufzeitpläne nicht zur Statuspflege verändern.

Eine Übergabe enthält knapp, mit Links statt wiederholten Befundtexten:

```text
Stand/Datum, Aufgabe und zuständiger Chat:
Repository, Branch, HEAD, PR/Basis; lokale Änderungen oder laufende Prozesse:
Gültiger Plan/Entscheidung und vorhandene Artefakte (ggf. Hash/Sicherungsort):
Geplant / implementiert / ausgeführt / CI-geprüft / unabhängig nachgerechnet:
  jeweils Bezugscommit, Befehl/Beleg, Ergebnis und Grenze; Ausstehendes nennen.
Offene Befunde/Entscheidungen; nächster abgegrenzter Schritt:
```

Der übernehmende Chat prüft den aktuellen Stand erneut. Ein übermittelter
lokaler Lauf bleibt als solcher gekennzeichnet, bis seine Primärartefakte
im angegebenen Umfang geprüft wurden.

## Sprache

- Kommunikation, Projektdokumentation, Issues und Pull Requests
  auf Deutsch.
- Code, Bezeichner, Docstrings und technische Code-Kommentare
  auf Englisch.
- Commit-Nachrichten und Branch-Namen auf Englisch.
- Etablierte Fachbegriffe und Bibliotheksnamen nicht künstlich übersetzen.

## Änderungen und Versionsverwaltung

- Bestehende Dateien und Konfigurationen zuerst lesen.
- Änderungen klein, nachvollziehbar und aufgabenbezogen halten.
- Aufgaben in einem eigenen Branch bearbeiten.
- Für Agenten-Branches das Präfix `codex/` verwenden.
- Keine Geheimnisse, Zugangsdaten oder lokale Umgebungen versionieren.
- Keine bestehenden Arbeiten verwerfen oder überschreiben.
- Keine Force-Pushes oder Änderungen der Commit-Historie ohne Auftrag.
- Pull Requests nicht eigenständig in `main` übernehmen.

## Umgebung und Abhängigkeiten

- Python-Befehle im Projekt über `uv run` ausführen.
- Python-Abhängigkeiten über `uv` verwalten.
- `uv.lock` nicht manuell bearbeiten.
- Abhängigkeiten nur ändern, wenn die Aufgabe es erfordert.
- Python- und Julia-Umgebung getrennt berücksichtigen.
- Portable Pfade verwenden; keine persönlichen Rechnerpfade einbauen.

## Wissenschaftliche Sorgfalt

- Fachliche Annahmen, Formeln, Einheiten und Parameter dokumentieren.
- Forschungsfrage, Vergleichsbedingungen und Erfolgskriterien
  nicht eigenmächtig ändern.
- Zufallsquellen und Experimentkonfigurationen nachvollziehbar halten.
- Daten für Entwicklung, Auswahl und abschließende Bewertung
  entsprechend dem festgelegten Versuchsplan trennen.
- Technische Funktionsfähigkeit und wissenschaftliche Validierung
  ausdrücklich unterscheiden.
- Ergebnisse, Laufzeiten und Testerfolge niemals erfinden.
- Wesentliche Entscheidungen im zuständigen Methodenplan oder Befunddokument
  festhalten: Beschluss und Begründung, erwogene/verworfene Alternativen,
  Belege mit Version/Commit sowie Aussagegrenzen und offene Fragen.
  Ideen, beschlossene Vorgaben, Implementierung und Ausführung unterscheiden.
  Externe Fachquellen konkret zitieren; fehlenden Quellenzugriff offenlegen.

## Prüfungen

- Für Änderungen passende Prüfungen auswählen.
- Wissenschaftliche Berechnungen anhand unabhängig begründeter
  Referenzfälle prüfen.
- Fehlgeschlagene Tests nicht durch unbegründet gelockerte
  Toleranzen oder entfernte Prüfungen umgehen.
- Genau berichten, welche Prüfungen tatsächlich ausgeführt wurden.
- Nicht ausgeführte Prüfungen und offene Einschränkungen benennen.
- Vorgeschriebene Checks vollständig durchführen. Zusätzliche oder wiederholte
  Prüfungen durch Änderungen, Fehler oder offene Risiken begründen; nach
  bestandenem unverändertem Prüfstand keine routinemäßigen Wiederholungen.

Verfügbare Prüfbefehle:

- `uv run --locked ruff check .` für statische Codeprüfung.
- `uv run --locked ruff format --check .` für Formatprüfung.
- `uv run --locked python scripts/run_python.py scripts/check_environment.py`
  für die technische Umgebungsprüfung.
- `uv run --locked pytest` für Tests, sobald eigene Tests vorhanden sind.
- `uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_julia_loss.py`
  für Julia-Verlustkern- und Konstantenoptimierer-Tests sowie Python-Replays.
- `uv run --locked --python 3.12.14 python scripts/check_julia_startup.py`
  für gleichzeitige Starts bei fremder aktiver CondaPkg-Sperre.
- `uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_symbolic_search.py`
  für echte freie PySR-Suchen in getrennten Prozessen, Baumexport und Replay.
- `uv run --locked python scripts/check_symbolic_pilot.py --output results/ci-sr-controls-001`
  für beide Schema-3-Kontrollfälle mit reduziertem, gespeichertem CI-Budget.
- `uv run --locked python scripts/check_symbolic_pilot.py --verify results/sr-ar1-001`
  für die unabhängige Nachrechnung eines vorhandenen Schema-3-Ergebnisses.
- `uv run --locked python scripts/diagnose_symbolic_pilot.py export results/sr-portability-001 --label manjaro --output results/diagnostics-manjaro-001`
  für einen lesenden Diagnoseexport bestehender weißer/AR(1)-Läufe; keine Suche.
- `uv run --locked python scripts/diagnose_symbolic_pilot.py compare results/diagnostics-manjaro-001 results/diagnostics-wsl2-001 --output results/diagnostics-comparison-001.json`
  für den beschreibenden Vergleich zweier vorhandener Diagnosepakete.

Der technische Umgebungscheck prüft die Funktionsfähigkeit der
Softwareumgebung. Wissenschaftliche Validierung benötigt fachliche Tests.

Ein Testlauf ohne gefundene Tests ist kein bestandener Testnachweis.

## Abschluss einer Aufgabe

Kurz berichten:
- Was geändert wurde und warum.
- Welche Prüfungen durchgeführt wurden und mit welchem Ergebnis.
- Welche Fragen oder Einschränkungen offenbleiben.

## Julia-Umgebung

- Python-Aufrufe mit PySR oder JuliaCall über
  `uv run --locked --python 3.12.14 python scripts/run_python.py ...`
  ausführen.
- Die Julia-Version in `src/ringdown_sr/juliapkg.json` und
  `julia/Manifest.toml` konsistent halten.
- `julia/Manifest.toml` nicht manuell bearbeiten.
- Der Launcher bindet PythonCall an den aktuellen Python-Interpreter und setzt
  CondaPkg auf `Null`. Fremde oder aktive Sperrdateien nicht löschen.

## CI und Reviews

- Reine Änderungen an `README.md`, `AGENTS.md` und Markdown unter `docs/`
  erhalten schlanke Format- und lokale Linkprüfungen. Dokumente, die zur
  Laufzeit konsumiert werden, benötigen weiterhin die volle CI; aktuell gilt
  dies für `docs/noiseless_control_plan.md`.
- Code-, Test-, Konfigurations-, Abhängigkeits- und CI-Änderungen benötigen
  vor dem Merge die vollständigen technischen Prüfungen. Unklare Änderungen
  werden vollständig geprüft. Die Zuordnung ist in `docs/ci.md` beschrieben.
- Kleine zusammengehörige Nachbesserungen bündeln, um unnötige neue Läufe
  zu vermeiden. Bestehende erforderliche Checks nicht umgehen.
- KI-basierte Reviews gezielt bei wesentlichen Methodenentscheidungen oder
  konkretem Prüfbedarf einsetzen. Nachreviews nur bei notwendigen
  Gegenprüfungen; keine automatische zusätzliche Reviewrunde pro PR.
- Reviewauftrag und Befund nennen PR, vollständigen Head-Commit, Vergleichsbasis
  und Prüfumfang. Konkrete Fehler/wissenschaftliche Risiken mit Fundstelle,
  Auswirkung und notwendiger Korrektur von optionalen Verbesserungen trennen.
  Nach Änderungen benennen, welche offenen Befunde oder betroffenen Annahmen
  erneut geprüft werden müssen; frühere Reviews gelten für ihren Bezugsstand.
- Ein separater KI-Review ersetzt weder unabhängig hergeleitete Referenzfälle
  oder Nachrechnungen noch wissenschaftliche Validierung. Umfang und Grundlage
  einer Nachrechnung getrennt vom Reviewurteil dokumentieren.
- Reviews in Dokumentation und PR-Texten als KI-basiert bezeichnen;
  konkrete Modellnamen sind dafür nicht erforderlich.

## Projekt- und Codex-Einstellungen

Technische Regeln bleiben hier und in den verlinkten Repositorydokumenten.
Projektanweisungen sollen darauf verweisen, statt sie zu kopieren. Als
Ausgangspunkt für Routinearbeit Sol High verwenden; stärkere Einstellungen
gezielt bei schwierigen Methoden- oder Fehlerfragen wählen. Kontext nur
aufgabenbezogen laden und Parallelität nur bei trennbaren Aufgaben einsetzen.
Nicht einsehbare Modell-, Projekt-, Berechtigungs- oder Umgebungseinstellungen
als ungeprüft kennzeichnen und bei Bedarf gezielt anfordern.
