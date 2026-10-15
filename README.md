# ringdown-sr

Repository zur Masterarbeit über rauschgewichtete symbolische
Regression zur Rekonstruktion kurzer Ringdown-Signale.

## Projektstatus

Offizieller Bearbeitungsbeginn: 12.10.2026.

Stand der technischen Vorbereitung am 01.10.2026:

- Entwicklungsumgebung eingerichtet.
- Python-Basisbibliotheken erfolgreich importiert.
- Python–Julia-Verbindung geprüft.
- Allgemeiner PySR-Funktionstest mit einer Polynomfunktion erfolgreich.
- Git-Repository eingerichtet und mit GitHub verbunden.

Die fachliche Implementierung des Piloten hat am 15.10.2026 begonnen.
Implementiert sind ein Signalgenerator, weißes Gaußrauschen und
Verlust-Rechenkerne mit analytischen Referenztests.
Die wissenschaftlichen Hauptversuche und ihre Auswertung stehen noch aus.
Der frühere Polynomtest dient ausschließlich der technischen Funktionsprüfung.

Details zum aktuellen Stand: [Pilot](docs/pilot.md) und
[Verlustfunktionen](docs/losses.md).

## Entwicklungsumgebung

Auf einem Windows-Rechner mit Ubuntu unter WSL2 sowie auf einem
Laptop mit Manjaro Linux geprüft.
Als Editor wird Visual Studio Code mit WSL-Anbindung verwendet.

Gemeldete Versionen:

- Python: 3.12.14
- uv: 0.12.21
- Git: 2.53.0
- PySR: 2.6.0
- juliacall: 0.9.36
- Julia: 1.13.1

## Bibliotheken

- NumPy und SciPy: numerische Berechnungen und Optimierung
- Matplotlib: Diagramme
- pandas: tabellarische Auswertung
- SymPy: symbolische Mathematik
- PySR: symbolische Regression mit Julia-Backend

Entwicklungswerkzeuge:

- pytest: automatisierte Tests
- Ruff: Codeprüfung und Formatierung
- ipykernel: Ausführung von Python in Jupyter-Notebooks

## Einrichtung auf einem weiteren Rechner

Voraussetzungen: Git, uv und Zugriff auf das private GitHub-Repository.
Die folgenden Befehle sind für ein Linux- beziehungsweise WSL-Terminal.

```bash
git clone https://github.com/craexxn/ringdown-sr.git
cd ringdown-sr
uv python install 3.12.14
uv sync --locked --python 3.12.14
```

Programme werden aus dem Projektordner mit `uv run` gestartet.
Eine manuelle Aktivierung der virtuellen Umgebung ist nicht nötig.

## Technische Prüfungen

Die Python-Version ist in `.python-version` festgelegt.

Die folgenden Befehle werden aus dem Projektordner ausgeführt:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
uv run --locked python scripts/run_python.py scripts/check_environment.py
```

Das Prüfskript kontrolliert Bibliotheksimporte, Python- und
Julia-Versionen, das aktive Julia-Projekt sowie einen Julia-Rechentest.

Diese Prüfungen wurden am 06.10.2026 auf Manjaro erfolgreich ausgeführt.

Der Workflow `.github/workflows/technical-checks.yml` führt dieselben
Prüfungen bei Pull Requests und Änderungen an `main` auf einem
Ubuntu-Rechner aus. Der technische GitHub-Actions-Workflow wurde am 06.10.2026
erstmals erfolgreich ausgeführt.

## Reproduzierbarkeit

- Python-Abhängigkeiten werden durch `pyproject.toml` und `uv.lock`
  beschrieben und festgelegt. Verwendet wird Python 3.12.14.
- `src/ringdown_sr/juliapkg.json` legt Julia auf Version 1.13.1 fest.
- `julia/Project.toml` und `julia/Manifest.toml` halten die direkten
  und indirekten Julia-Paketversionen fest.
- `scripts/run_python.py` ermittelt das lokale Julia-Programm,
  prüft die Version und stellt die gespeicherte Paketumgebung bereit.
- Die lokale `.venv` wird nicht mit Git versioniert.

Python-Aufrufe mit PySR oder JuliaCall werden über das Startskript
ausgeführt. Beispiel aus dem Projektordner:

```bash
uv run --locked --python 3.12.14 python scripts/run_python.py -c "import pysr; print(pysr.__version__)"
```

Für eine Python-Datei wird anstelle von `-c "..."` deren Pfad angegeben.

Der Startweg wurde am 06.10.2026 auf Manjaro erfolgreich geprüft:
PySR 2.6.0, Julia 1.13.1, SymbolicRegression 2.5.1 und PythonCall 0.9.36.
Die Prüfung dieses neuen Startwegs unter Ubuntu/WSL2 steht noch aus.

## Stand der Prüfungen

Der allgemeine PySR-Test rekonstruierte die Funktion
y = x² + 2x + 1 bis auf einen kleinen numerischen Fehler.

Das bestätigt die technische Funktionsfähigkeit, jedoch keine
wissenschaftliche Validierung der geplanten Ringdown-Methode.

## Technische Prüfung auf dem zweiten Rechner

Am 06.10.2026 wurde die Umgebung auf dem Manjaro-Linux-Laptop
aus dem GitHub-Repository und mit `uv sync --locked`
wiederhergestellt.

Erfolgreich geprüft:

- Python 3.12.14 und Import der Basisbibliotheken.
- PySR 2.6.0 und Julia 1.13.1.
- Julia-Backend SymbolicRegression 2.5.1.
- Allgemeine Formelsuche für y = x² + 2x + 1.

Gefundene Formel: x(x + 2) + 1.
Mittlerer quadratischer Fehler: ungefähr 3,94 × 10⁻³³.

Damit ist die technische Funktionsfähigkeit auf beiden Rechnern
geprüft.
