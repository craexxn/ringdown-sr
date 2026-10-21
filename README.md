# ringdown-sr

Repository zur Masterarbeit über rauschgewichtete symbolische
Regression zur Rekonstruktion kurzer Ringdown-Signale.

## Projektstatus

Dokumentationsstand: 21.10.2026.
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
- Reiner Kovarianzschätzer aus getrennten Hintergrundfenstern mit
  ausdrücklicher Identitätsschrumpfung und Alpha-Auswahl:
  `src/ringdown_sr/covariance_estimation.py`.
- Drei gekoppelte Referenzfits mit getrennten Hintergrundrollen und
  geschätzter Kovarianz im ausdrücklich versionierten Schema 2:
  `src/ringdown_sr/covariance_pilot.py`.
- 456 automatisierte Testfälle für diese Bausteine, einschließlich
  analytischer Referenzfälle und ungültiger Eingaben.
- Julia-Verlustkern mit expliziter Einheitenprüfung, festem Fenster und
  voller Kovarianz sowie separaten Julia-Tests und Python-Replay.
- Deterministische Prüfung der tatsächlichen Newton-/BFGS-Konstantenanpassung
  im Julia-Backend mit unabhängigen Referenzen und Python-Nachrechnung.
- Festgelegte Python-/Julia-Umgebung und automatische GitHub-Prüfungen.

Ein vollständiger kleiner Durchlauf mit bekanntem Formansatz ist vorhanden.
Die Kovarianzschätzung ist mit Hintergrundrollen, drei Fit-Varianten und
Exporten integriert. Der [Julia-Verlustkern](docs/julia_loss_kernel.md) ist als erster
Baustein der freien Suche ergänzt. Die [Konstantenoptimiererprüfung](docs/constant_optimization.md)
ergänzt die tatsächlichen Backend-Pfade bei fest vorgegebenen Strukturen.
Die freie PySR-Suchanbindung und statistische Leistungsbewertung stehen noch aus.
Die wissenschaftlichen Hauptversuche und ihre Auswertung haben noch
nicht begonnen.

Details zum aktuellen Stand: [Pilot](docs/pilot.md),
[Verlustfunktionen](docs/losses.md), [Referenzfit](docs/reference_fit.md),
[konfigurierter Durchlauf](docs/configured_pilot.md) sowie
[korreliertes Rauschen](docs/correlated_noise.md) und
[Kovarianzschätzer](docs/covariance_estimation.md) und
[Pilot mit geschätzter Kovarianz](docs/estimated_covariance_pilot.md).
Das [Portabilitätsprotokoll](docs/portability.md) enthält die bisherigen
Schema-1-Vergleiche und die neuen Schema-2-Nachweise auf Manjaro und WSL2
am selben sauberen Commit. Auch der gepinnte Julia-Startweg ist lokal
unter WSL2 bestätigt. Der [PySR-Methodenentwurf](docs/symbolic_regression_method_plan.md)
wurde separat geprüft und um die Reviewpunkte präzisiert; seine
weitere Such- und Ergebnisintegration steht noch aus.

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

Schema 2 erzeugt die drei Fits gemeinsam und schätzt die dritte Kovarianz
aus getrennten Hintergrundfenstern. Der AR(1)-Kontrolllauf wird so gestartet:

```bash
uv run --locked ringdown-sr run configs/pilot_estimated_ar1.toml --output results/estimated-ar1-001
code -r results/estimated-ar1-001/plot.png
code -r results/estimated-ar1-001/covariance_plot.png
```

Für weißes Rauschen gibt es `configs/pilot_estimated_white.toml`.
Die Ausgabe enthält zusätzlich Hintergrundfenster, rohe/geschätzte/wahre
Kovarianzen, Alpha-Diagnosen und getrennte RNG-Rollen. Bedienung,
Konfiguration, Kennzahlen und Grenzen beschreibt die
[Schema-2-Dokumentation](docs/estimated_covariance_pilot.md).

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
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_julia_loss.py
```

Der Umgebungscheck kontrolliert Bibliotheksimporte, Python- und
Julia-Versionen, das aktive Julia-Projekt sowie einen Julia-Rechentest.
Der separate Julia-Check führt Verlustkern- und echte Konstantenoptimierer-Tests,
zehn Residualvergleiche mit dem Python-Kern sowie zwölf unabhängige
Optimierer-Nachrechnungen aus. Diese Prüfungen gehören
nicht zur pytest-Anzahl; Details stehen im
[Julia-Verlustkern](docs/julia_loss_kernel.md).

Mit `uv run --locked pytest -v` wird jeder Testfall mit seinem Ergebnis
angezeigt. Integrationstests erzeugen unter anderem temporäre Diagramme
im pytest-Verzeichnis. Für bewusst gespeicherte Ergebnisse und Diagramme
die obigen CLI-Kontrollläufe ausführen. Freie Formelsuche findet dort
noch nicht statt.

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
Am 20.10.2026 wurden nach Ergänzung des reinen Kovarianzschätzers und
den Korrekturen aus dem Implementierungsreview 396 Tests in der
Codex-Umgebung bestanden, davon 95 neue Tests für
Schätzung, Auswahl, Fehlerfälle und die statistische Kontrolle des rohen
Schätzers. Nach der Schema-2-Integration bestanden am selben Tag insgesamt
456 Tests, darunter 60 neue Tests für Schema, Zufallsströme und Integration.
Die Seed-Prüfung lehnt identische Anfangszustände der vier Generatoren
vor Datenerzeugung und Anlegen des Ausgabeordners ab. Beide vollständigen
Schema-2-Beispiele wurden in der Codex-Umgebung erfolgreich ausgeführt und
ihre Diagramme geprüft. Das separate Integrationsreview zu PR #16 fand
eine Seed-Überschneidung; deren Nachbesserung ist mit Commit `1fcf9fc`
übernommen. Am 20.10.2026 bestätigte der Nutzer an diesem sauberen Commit
auf Manjaro 456 bestandene Tests in 33,02 s, beide erfolgreichen
Schema-2-Beispiele und die Diagrammanzeige. Eine zusätzliche Nachrechnung
bestätigte Dateiprüfsummen, Kovarianzen, Kontroll-Scores und Fit-Verluste.
Umfang und Zahlen stehen im [Portabilitätsprotokoll](docs/portability.md).
Unter WSL2 wurden am selben Referenzcommit ebenfalls 456 Tests in 27,19 s
bestanden, beide Beispiele und alle vier Diagramme bestätigt sowie dieselben
Datei-, Kovarianz-, Kontroll-Score- und Verlustprüfungen ausgeführt.
Alpha und ausgegebene Kennzahlen stimmen mit Manjaro überein.
Ein vollständiger rechnerübergreifender Array- oder Bytevergleich ist
damit nicht belegt.
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
Am 20.10.2026 bestätigte der Nutzer den Startweg außerdem lokal unter WSL2:
`Technical environment check passed.`, Python 3.12.14, PySR 2.6.0,
Julia 1.13.1, SymbolicRegression 2.5.1 und PythonCall 0.9.36;
geladen wurde `julia/Project.toml` im Projektordner.
Der separate Nachweis ist im [Portabilitätsprotokoll](docs/portability.md)
dokumentiert und bestätigt keinen bereits implementierten SR-Adapter.

Der frühere allgemeine PySR-Test rekonstruierte `y = x² + 2x + 1`
auf dem Manjaro-Laptop als `x(x + 2) + 1` mit einem mittleren
quadratischen Fehler von ungefähr `3,94 × 10⁻³³`. Dieser Test ist
eine Installationsprüfung und keine Ringdown-Rekonstruktion.

## Nächste Schritte

1. Die [Backend-Konstantenoptimiererprüfung](docs/constant_optimization.md)
   im KI-gestützten Code- und Methodenreview prüfen; den Julia-Kern und
   die Erweiterung lokal auf Manjaro/WSL2 ausführen.
2. Die freie PySR-Schnittstelle und Prozessisolation ergänzen und prüfen;
   Alias-/Phasenfälle und eindeutig bezeichneten Score-Export umsetzen.
3. Danach versionierte Konfiguration und Exporte integrieren und den
   neuen SR-Adapter separat reviewen und auf beiden Rechnern prüfen.
   Die wissenschaftliche Formelauswahl wird gesondert festgelegt.

Diese Schritte bilden die Arbeitsplanung für den Pilot.
Parameterbereiche, SNR-Konvention und Kriterien für die Hauptversuche
werden gesondert begründet und dokumentiert.
