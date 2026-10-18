# ringdown-sr

Repository zur Masterarbeit über rauschgewichtete symbolische
Regression zur Rekonstruktion kurzer Ringdown-Signale.

## Projektstatus

Dokumentationsstand: 18.10.2026.
Offizieller Bearbeitungsbeginn: 12.10.2026.
Beginn der fachlichen Pilotimplementierung: 15.10.2026.

Auf `main` vorhanden:

- Gleichmäßige Zeitachse und Generator für ein einzelnes gedämpftes
  Sinussignal: `src/ringdown_sr/signals.py`.
- Weißes Gaußrauschen mit explizitem NumPy-Zufallsgenerator:
  `src/ringdown_sr/noise.py`.
- Gewöhnliche MSE sowie kovarianzgewichtete Verluste und Whitening
  über eine Cholesky-Zerlegung: `src/ringdown_sr/losses.py`.
- 121 automatisierte Testfälle für diese Bausteine, einschließlich
  analytischer Referenzfälle und ungültiger Eingaben.
- Festgelegte Python-/Julia-Umgebung und automatische GitHub-Prüfungen.

Die Bausteine ergeben noch keinen vollständigen Rekonstruktionslauf.
Klassischer Referenzfit, korreliertes Rauschen, Kovarianzschätzung und
Regularisierung, PySR-Integration sowie Ergebnisexport stehen noch aus.
Die wissenschaftlichen Hauptversuche und ihre Auswertung haben noch
nicht begonnen.

Details zum aktuellen Stand: [Pilot](docs/pilot.md) und
[Verlustfunktionen](docs/losses.md).

## Entwicklungsumgebung

Die grundlegende Installation und ein allgemeiner PySR-Polynomtest
wurden auf einem Windows-Rechner mit Ubuntu unter WSL2 sowie auf einem
Laptop mit Manjaro Linux geprüft. Als Editor wird Visual Studio Code
verwendet, unter Windows mit WSL-Anbindung.

Gemeldete Versionen:

- Python: 3.12.14
- uv: 0.12.21
- Git: 2.53.0 unter WSL2, 2.55.0 unter Manjaro
- PySR: 2.6.0
- juliacall: 0.9.36
- Julia: 1.13.1
- SymbolicRegression: 2.5.1
- PythonCall: 0.9.36

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
uv sync --locked --dev --python 3.12.14
```

Programme werden aus dem Projektordner mit `uv run` gestartet.
Eine manuelle Aktivierung der virtuellen Umgebung ist nicht nötig.

## Bestehenden Rechner aktualisieren

Im Linux- beziehungsweise WSL-Terminal aus dem Projektordner zuerst
`git status` ausführen. Bei sauberem Arbeitsverzeichnis:

```bash
git switch main
git pull --ff-only
uv sync --locked --dev --python 3.12.14
```

Damit werden die übernommenen Änderungen von `main` und die festgelegten
Python-Abhängigkeiten abgeglichen. Änderungen aus offenen Pull Requests
sind auf deren jeweiligen Branches verfügbar.

## Technische Prüfungen

Die Python-Version ist in `.python-version` festgelegt.

Die folgenden Befehle werden aus dem Projektordner ausgeführt:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_environment.py
```

Das Prüfskript kontrolliert Bibliotheksimporte, Python- und
Julia-Versionen, das aktive Julia-Projekt sowie einen Julia-Rechentest.

Mit `uv run --locked pytest -v` wird jeder Testfall mit seinem Ergebnis
angezeigt. Die automatisierten Tests erzeugen keine Diagramme oder
rekonstruierten Ringdown-Formeln.

Der Workflow `.github/workflows/technical-checks.yml` führt dieselben
Prüfungen bei Pull Requests und Änderungen an `main` auf einem
Ubuntu-Rechner aus.

Prüfnachweise für den dokumentierten Code-Stand:

- Der [GitHub-Durchlauf auf `main` vom 15.10.2026](https://github.com/craexxn/ringdown-sr/actions/runs/38762123899)
  zu Commit `600e95b` ist erfolgreich abgeschlossen: Ruff-Codeprüfung,
  Formatprüfung, Unit-Tests und Python-/Julia-Umgebungscheck.
- Am 18.10.2026 wurden die 121 Unit-Testfälle dieses Code-Stands
  zusätzlich in der Codex-Umgebung erfolgreich ausgeführt.

Bestandene Tests bestätigen die geprüften Formeln und Eingaberandfälle.
Die wissenschaftliche Validierung der Rekonstruktionsmethode benötigt
die noch ausstehenden methodischen Prüfungen und Experimente.

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
Der aktuelle GitHub-Durchlauf bestätigt ihn außerdem auf Ubuntu.
Ein aktueller lokaler Prüfnachweis für diesen Startweg unter WSL2
ist noch nicht dokumentiert; der GitHub-Lauf ersetzt diesen Nachweis nicht.

Der frühere allgemeine PySR-Test rekonstruierte `y = x² + 2x + 1`
auf dem Manjaro-Laptop als `x(x + 2) + 1` mit einem mittleren
quadratischen Fehler von ungefähr `3,94 × 10⁻³³`. Dieser Test ist
eine Installationsprüfung und keine Ringdown-Rekonstruktion.

## Nächste Schritte

1. Einen klassischen Referenzfit mit bekannter Ringdown-Formel ergänzen.
   Parameterdarstellung, Startwerte und Grenzen werden dabei ausdrücklich
   festgelegt und anhand unabhängiger Referenzfälle geprüft.
2. Signal, Rauschen, Fit, Bewertung und Ergebnisexport zu einem kleinen
   reproduzierbaren Durchlauf verbinden. Konfiguration und Zufallsquellen
   werden zusammen mit den Ergebnissen protokolliert.
3. Korreliertes Rauschen mit bekannter Kovarianz und anschließend
   Kovarianzschätzung aus getrennten Hintergrunddaten sowie Regularisierung
   ergänzen und prüfen.
4. Die freie PySR-Formelsuche und die volle Kovarianzgewichtung integrieren.
   Endgültige Verlustnormierung und Komplexitätsgewichtung werden im
   methodischen Review festgelegt.

Diese Schritte bilden die Arbeitsplanung für den Pilot.
Parameterbereiche, SNR-Konvention und Kriterien für die Hauptversuche
werden gesondert begründet und dokumentiert.
