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

Bisher auf einem Windows-Rechner mit Ubuntu unter WSL2 geprüft.
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

`pyproject.toml` beschreibt die Abhängigkeiten.
`uv.lock` hält die aufgelösten Python-Paketversionen fest.
Beide Dateien werden mit Git versioniert.

Die lokale Umgebung `.venv` wird nicht versioniert.

Die Julia-Version und Julia-Pakete sind durch `uv.lock` allein
nicht vollständig festgelegt. Ihre explizite Fixierung und die
Prüfung auf einem zweiten Rechner stehen noch aus.

## Stand der Prüfungen

Der allgemeine PySR-Test rekonstruierte die Funktion
y = x² + 2x + 1 bis auf einen kleinen numerischen Fehler.

Das bestätigt die technische Funktionsfähigkeit, jedoch keine
wissenschaftliche Validierung der geplanten Ringdown-Methode.

Eigene fachliche Tests und eine automatische GitHub-Testpipeline
sind noch nicht eingerichtet.