# Arbeitsregeln für Agenten

## Projektstatus und Umfang

Offizieller Bearbeitungsbeginn der Masterarbeit: 12.10.2026.

Vor diesem Datum sind Aufgaben in diesem Repository auf technische
und organisatorische Vorbereitung beschränkt:
- Entwicklungsumgebung und Installation dokumentieren.
- Git-Arbeitsabläufe und allgemeine Entwicklungsregeln vorbereiten.
- Allgemeine, fachlich unabhängige Installationsprüfungen durchführen.

Keine Ringdown-Implementierung, eigene Kovarianzschätzung,
wissenschaftliche Verlustfunktion oder Forschungsexperimente
vor dem Bearbeitungsbeginn umsetzen.

Auch nach dem Startdatum nur die konkret beauftragte Aufgabe bearbeiten.

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

## Prüfungen

- Für Änderungen passende Prüfungen auswählen.
- Wissenschaftliche Berechnungen anhand unabhängig begründeter
  Referenzfälle prüfen.
- Fehlgeschlagene Tests nicht durch unbegründet gelockerte
  Toleranzen oder entfernte Prüfungen umgehen.
- Genau berichten, welche Prüfungen tatsächlich ausgeführt wurden.
- Nicht ausgeführte Prüfungen und offene Einschränkungen benennen.

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
