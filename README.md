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

Die fachliche Implementierung und wissenschaftliche Auswertung
haben noch nicht begonnen. Der Polynomtest dient ausschließlich
der technischen Funktionsprüfung.

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

## Technische Prüfung

```bash
uv run python --version
uv run python -c "import numpy, scipy, matplotlib, pandas, sympy; print('Basisbibliotheken geladen.')"
uv run python -c "import pysr; print('PySR:', pysr.__version__)"
uv run python -c "import pysr; from juliacall import Main as jl; print('Julia:', jl.seval('string(VERSION)')); print(jl.seval('1 + 1'))"
```

Der erste PySR-Import kann Julia und Julia-Pakete herunterladen
und vorkompilieren. Dafür wird eine Internetverbindung benötigt.

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

Eigene fachliche Tests und eine automatische GitHub-Testpipeline
sind noch nicht eingerichtet.

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