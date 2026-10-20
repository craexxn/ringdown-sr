# ringdown-sr

Repository zur Masterarbeit über rauschgewichtete symbolische
Regression zur Rekonstruktion kurzer Ringdown-Signale.

## Projektstatus

Dokumentationsstand: 20.10.2026.
Offizieller Bearbeitungsbeginn: 12.10.2026.
Beginn der fachlichen Pilotimplementierung: 15.10.2026.

Auf `main` vorhanden:

- Gleichmäßige Zeitachse und Generator für ein einzelnes gedämpftes
  Sinussignal: `src/ringdown_sr/signals.py`.
- Weißes Gaußrauschen mit explizitem NumPy-Zufallsgenerator:
  `src/ringdown_sr/noise.py`.
- Stationäres korreliertes AR(1)-Gaußrauschen mit analytischer Kovarianz
  und gepaarten Beispielen für gewöhnlichen und gewichteten Fit.
- Gewöhnliche MSE sowie kovarianzgewichtete Verluste und Whitening
  über eine Cholesky-Zerlegung: `src/ringdown_sr/losses.py`.
- Klassischer Fit mit bekannter Ringdown-Formel, expliziten Startpunkten
  und optionaler fester Kovarianz: `src/ringdown_sr/reference_fit.py`.
- Konfigurierbarer Kontrolllauf mit TOML-Eingabe, Ergebnisdateien,
  Diagramm und Metadaten: `src/ringdown_sr/pilot.py`.
- 301 automatisierte Testfälle für diese Bausteine, einschließlich
  analytischer Referenzfälle und ungültiger Eingaben.
- Festgelegte Python-/Julia-Umgebung und automatische GitHub-Prüfungen.

Ein vollständiger kleiner Durchlauf mit bekanntem Formansatz ist vorhanden.
Kovarianzschätzung und Regularisierung, PySR-Integration und die
statistische Leistungsbewertung stehen noch aus.
Die wissenschaftlichen Hauptversuche und ihre Auswertung haben noch
nicht begonnen.

Details zum aktuellen Stand: [Pilot](docs/pilot.md),
[Verlustfunktionen](docs/losses.md), [Referenzfit](docs/reference_fit.md),
[konfigurierter Durchlauf](docs/configured_pilot.md) sowie
[korreliertes Rauschen](docs/correlated_noise.md).
Die lokalen Vergleiche auf Manjaro und Ubuntu unter WSL2 sind im
[Portabilitätsprotokoll vom 19.10.2026](docs/portability.md) festgehalten.

## Konfigurierter Durchlauf mit gespeicherten Ergebnissen

Aus dem Projektordner:

```bash
uv run --locked ringdown-sr run configs/pilot_white.toml --output results/pilot-001
code -r results/pilot-001/plot.png
```

Der neue Ausgabeordner enthält Konfiguration, Messwerte als CSV,
Parameter und Fehlerwerte als JSON, ein Diagramm und Metadaten mit Seed,
Zufallszuständen, Softwareversionen, Codezustand und Prüfsummen.
Bestehende Ordner werden abgelehnt; für eine Wiederholung einen neuen
Namen wie `results/pilot-002` verwenden. Lokale Ausgaben unter `results/`
werden nicht versioniert und müssen separat gesichert werden.
Der Kontrolllauf braucht kein Julia/PySR und legt keine Einstellungen
oder Erfolgskriterien für die Hauptversuche fest.

Die gepaarten AR(1)-Beispiele werden genauso gestartet, mit
`configs/pilot_ar1.toml` beziehungsweise `configs/pilot_ar1_ordinary.toml`
und jeweils einem neuen Ausgabeordner. Sie erzeugen dieselben Daten und
verwenden unterschiedliche Fit-Gewichtungen. Zusätzlich wird die bekannte
Modellkovarianz als `covariance.csv` gespeichert. Das ist ein Kontrollvergleich,
kein Nachweis einer Überlegenheit aus einem Einzelversuch.

## Sichtbarer Demolauf

Nach der Einrichtung aus dem Projektordner:

```bash
uv run --locked python scripts/demo_reference_fit.py
```

Der Aufruf zeigt vorgegebene und geschätzte Parameter sowie Fehlerwerte
im Terminal und speichert ein Diagramm im temporären Verzeichnis.
Unter Linux/WSL kann es mit `code -r /tmp/ringdown-reference-fit.png`
geöffnet werden. Ein eigener Pfad ist mit `--output /pfad/diagramm.png`
möglich. Dieser einzelne Demofall verwendet die bekannte Formel und
ersetzt keine wissenschaftliche Bewertung oder freie PySR-Formelsuche.

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

Bisherige Prüfnachweise:

- Der [GitHub-Durchlauf auf `main` vom 15.10.2026](https://github.com/craexxn/ringdown-sr/actions/runs/38762123899)
  zu Commit `600e95b` ist erfolgreich abgeschlossen: Ruff-Codeprüfung,
  Formatprüfung, 121 Unit-Testfälle und Python-/Julia-Umgebungscheck.
  Dieser Nachweis stammt aus dem Stand vor Ergänzung des Referenzfits.
- Am 18.10.2026 wurden einschließlich konfiguriertem Pilot 237 Testfälle
  in der Codex-Umgebung erfolgreich ausgeführt.
- Am 19.10.2026 wurden nach Ergänzung der Build-/Laufzeitdiagnosen und
  weiterer Schutzprüfungen 244 Testfälle in der Codex-Umgebung bestanden.
- Am 19.10.2026 wurden nach Integration des AR(1)-Kontrollfalls 301 Testfälle
  in der Codex-Umgebung bestanden.
- Der Nutzer führte am 19.10.2026 auf Manjaro den weißen Kontrolllauf am
  sauberen Commit `3833a12` erfolgreich aus: 244 Tests bestanden, Diagramm
  geprüft. SHA-256 für Konfiguration, `samples.csv` und `result.json` waren
  mit dem Codex-Referenzlauf identisch. Dieser Nachweis gilt für den damaligen
  weißen Kontrollfall.
- Anschließend wurden auf Manjaro auch beide AR(1)-Beispiele erfolgreich
  ausgeführt, ihre Diagramme geöffnet und identische Eingabedaten und
  Kovarianzen innerhalb des Fit-Paars bestätigt. Die gewichteten Fehlerwerte
  wurden direkt aus den exportierten Residuen und Kovarianzen nachgerechnet.
- Auf Ubuntu unter WSL2 wurden am 19.10.2026 nach Aktualisierung auf
  `fbe9a60` 301 Tests bestanden sowie der weiße Kontrolllauf und beide
  AR(1)-Beispiele erfolgreich ausgeführt und ihre Diagramme geöffnet.
  Die ausgegebenen Kennzahlen stimmen mit Manjaro überein; bei AR(1)
  wurden Eingabegleichheit innerhalb des Paars und gewichtete Fehlerwerte
  erneut geprüft. Die abweichenden Weißrausch-Dateihashes wurden durch
  eine CPU-/OpenBLAS-Diagnose exakt nachgestellt. Umfang, Zahlenwerte
  und Grenzen stehen im [Portabilitätsprotokoll](docs/portability.md).

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

1. Einen begründeten Methodenplan für Kovarianzschätzung aus getrennten
   Hintergrunddaten und Regularisierung ausarbeiten. Schätzer,
   Datentrennung, Regularisierungswahl und Prüfkriterien vor der
   Implementierung kritisch prüfen. Der
   [Methodenplan](docs/covariance_method_plan.md) wurde nach dem ersten
   methodischen Review um gezielte Referenzfälle ergänzt; der Schätzer
   ist noch nicht implementiert.
2. Die geprüften Verfahren ergänzen und anhand unabhängiger Referenzen
   testen.
3. Die freie PySR-Formelsuche und die volle Kovarianzgewichtung integrieren.
   Endgültige Verlustnormierung und Komplexitätsgewichtung werden im
   methodischen Review festgelegt.

Diese Schritte bilden die Arbeitsplanung für den Pilot.
Parameterbereiche, SNR-Konvention und Kriterien für die Hauptversuche
werden gesondert begründet und dokumentiert.
