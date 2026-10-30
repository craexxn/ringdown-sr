# ringdown-sr

Repository zur Masterarbeit über rauschgewichtete symbolische
Regression zur Rekonstruktion kurzer Ringdown-Signale.

## Projektstatus

Fortsetzungsstand: 30.10.2026; abgeglichener Stand auf `main`: `722437e`
([PR #44](https://github.com/craexxn/ringdown-sr/pull/44));
Ausführungsstand der Konstantendiagnose: `0a70f19`, der freien Kontrollserie: `4057caa`.
Offizieller Bearbeitungsbeginn: 12.10.2026.
Beginn der fachlichen Pilotimplementierung: 15.10.2026.

Dieser Abschnitt ist der kurze Einstieg für neue Chats. Arbeits- und
Übergaberegeln stehen in [AGENTS.md](AGENTS.md); vor Fortsetzung sind lokale
Änderungen, Branches und PRs erneut zu prüfen.

- **Abgeschlossene Methodengrundlage:** Der geprüfte
  [Plan für Zeitdarstellung und Komplexitätshäufigkeiten](docs/search_representation_plan.md)
  ist mit PR #37 übernommen. Er ergänzt den unveränderten
  [rauschfreien Kontrollplan](docs/noiseless_control_plan.md).
- **Implementierung abgeschlossen:** Der getrennte Kontrolltreiber ist mit
  PR #39 übernommen. Die vollständige technische CI am PR-Head `cfe44bf`
  bestand. Ein übermitteltes KI-basiertes Review desselben Heads fand keine
  korrekturbedürftigen Befunde zur beauftragten Methodentreue.
  [Bedienung und Artefakte](docs/representation_control.md) sowie
  [Fortsetzungsstand](docs/representation_implementation_status.md) enthalten
  Bezugscommits, Prüfumfang und Grenzen. Die wissenschaftliche Kontrollserie
  wurde auf Manjaro ausgeführt und ihr vollständiges Originalarchiv hier
  unabhängig nachgerechnet.
- **Neuer Entwicklungsbefund:** Die [Zeitdarstellungs-Kontrollserie auf
  Manjaro](docs/representation_control_results_manjaro_001.md) ist mit neun
  abgeschlossenen Zellen und bestandener Abschlussprüfung archiviert.
  Alle 57 Kandidaten, Originalauswahlen, Fehler und Seed-Differenzen wurden
  nachgerechnet. Die Häufigkeitsschalter senken die Trainings-MSE bei allen
  drei Seeds um rund 90–97 % gegenüber der frischen Baseline. Trotzdem
  erfüllt kein Kandidat die Kurvengrenzen; der Erkenner unterstützt keine
  gefundene Struktur, Parameter und Identifikation bleiben `not_assessed`.
- **Konstantendiagnose abgeschlossen:** Der [angenommene Diagnoseplan](docs/constant_diagnostic_plan.md)
  ist mit PR #42 implementiert und auf Manjaro ausgeführt. Das vollständige
  [Originalarchiv ist unabhängig nachgerechnet](docs/constant_diagnostic_results_manjaro_001.md):
  Unter 20/2 bestehen 0/24, unter 100/2 alle 24 Fits die festen Kurvengrenzen;
  Parameterbefunde wechseln von `mismatched` zu `matched`. Bei allen 72 lokalen
  Paaren sind die ersten 20 Schritte exakt gleich. Das belegt Budgetabhängigkeit
  für die vorgegebene Struktur und das deklarierte Startgitter; freie
  Strukturentdeckung und Übertragbarkeit bleiben offen.
- **Freier Budgetvergleich beschlossen:** Der [eingefrorene Methodenplan](docs/free_optimizer_budget_plan.md)
  sieht sechs frische freie Suchen vor: 20 gegen 100 lokale Optimiereriterationen,
  beide Häufigkeitsschalter an, drei bekannte Entwicklungsseeds, je 200 Suchiterationen
  und 60 Minuten Gesamtlimit. Die korrigierten Entscheidungsregeln trennen den
  Zählvergleich von Struktur-/Parameterbefunden derselben Originalauswahl.
  PR #44 ist übernommen; der getrennte Kontrollpfad wird auf
  `codex/free-optimizer-budget` implementiert. Die lokale technische
  Prozessprüfung ist bestanden; vollständige CI und einmalige Manjaro-Ausführung
  stehen aus. [Bedienung und Artefakte](docs/free_optimizer_budget.md). Dies ist adaptive Methodenentwicklung,
  keine Festlegung eines Produktionsprofils oder allgemeine Leistungsvalidierung.
- **Prüfnachweise:** Die [vollständige CI zu PR #39](https://github.com/craexxn/ringdown-sr/actions/runs/41038219843)
  bestand am Head `cfe44bf`: 1.288 Python-Tests, Julia- und technische
  Integrationsprüfungen. Der Mergecommit hat denselben Dateibaum. Die
  [schlanke CI zu PR #37](https://github.com/craexxn/ringdown-sr/actions/runs/41022224068)
  bestand am Head `e92152a`; sie prüft Dokumentation, keine Numerik.
  Der [Haswell-Befund](docs/symbolic_core_results.md) enthält die unabhängige
  Nachrechnung übermittelter Originalarchive. Der
  [rauschfreie Manjaro-Befund](docs/noiseless_control_results_manjaro_001.md)
  beruht dagegen auf übermittelten Berichtsauszügen; ein unabhängiger Audit
  aller Originalartefakte ist dort ausdrücklich nicht belegt.
  Die [vollständige CI zu PR #42](https://github.com/craexxn/ringdown-sr/actions/runs/41062609710)
  bestand am Head `9202d20`. Der neue Originalarchiv-Audit prüft 48 Fits,
  144 lokale Verläufe und 6.506 Zustände; dabei keine neue Optimierung.
- **Offen:** Ursache der Suchstagnation; wissenschaftliche Formelauswahl,
  numerisches Forschungsprofil und statistischer Versuchsplan vor einer
  Leistungsstudie. Dazu die [offenen Reproduzierbarkeitsentscheidungen](docs/reproducibility_decisions.md)
  und die Grenzen des neuen Methodenplans verwenden. Hauptversuche und
  wissenschaftliche Leistungsvalidierung stehen weiterhin aus.

## Implementierter Pilot auf der abgeglichenen Basis

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
- Automatisierte Python-Tests für diese Bausteine, einschließlich
  analytischer Referenzfälle, ungültiger Eingaben und des Julia-Startwegs.
- Julia-Verlustkern mit expliziter Einheitenprüfung, festem Fenster und
  voller Kovarianz sowie separaten Julia-Tests und Python-Replay.
- Deterministische Prüfung der tatsächlichen Newton-/BFGS-Konstantenanpassung
  im Julia-Backend mit unabhängigen Referenzen und Python-Nachrechnung.
- Festgelegte Python-/Julia-Umgebung und automatische GitHub-Prüfungen.
- Isolierte Laufzeitvorbereitung ohne zusätzliche Conda-Python-Umgebung;
  Prüfung gleichzeitiger Starts bei fremder aktiver CondaPkg-Sperre.
- Isolierter Adapter für einzelne freie PySR-Suchläufe mit vollständigem
  Baumexport, festem Kovarianzkontext und Verlust-Replay aller Pareto-Kandidaten.
- Vollständiger Schema-3-Pilot: drei freie SR-Arme auf denselben binären
  Eingaben, gemeinsame nachgelagerte Diagnosen und klassische Referenzen.
- Unabhängige [Alias-/Phasenreferenzen](docs/alias_references.md) für
  vorgegebene Ausdruckspaare, einschließlich kleiner Amplituden und Randfälle.
- Begrenzter [Strukturerkenner](docs/structure_recognition.md) für exportierte
  Ringdown-Ausdrücke mit exakter rationaler Koeffizientenextraktion.
- Separate [Parameter-/Aliasdiagnose](docs/parameter_diagnostics.md) mit
  rationalen π-Einschlüssen, abgesicherten Rundungsentscheidungen und
  Vorhersagevergleich gegen den unveränderten Originalbaum.

Ein vollständiger kleiner Durchlauf mit bekanntem Formansatz ist vorhanden.
Die Kovarianzschätzung ist mit Hintergrundrollen, drei Fit-Varianten und
Exporten integriert. Der [Julia-Verlustkern](docs/julia_loss_kernel.md) ist als erster
Baustein der freien Suche ergänzt. Die [Konstantenoptimiererprüfung](docs/constant_optimization.md)
ergänzt die tatsächlichen Backend-Pfade bei fest vorgegebenen Strukturen.
Der [freie Suchadapter](docs/symbolic_adapter.md) startet einzelne Arme in
neuen Prozessen. Der [Schema-3-Pilot](docs/symbolic_pilot.md) verbindet sie
mit der bestehenden Datenerzeugung und speichert alle Kandidaten sowie
gemeinsame Diagnosen. Die statistische Leistungsbewertung steht noch aus.
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
am selben sauberen Commit. Für Schema 3 sind auf Manjaro und WSL2 jeweils
559 bestandene Tests, beide vollständigen Audits und Diagrammanzeigen am
sauberen Commit `6ed493d` übermittelt. Zusätzliche Prüfungen bestätigen
die gespeicherte Git-Herkunft aller Stufen. Die freie SR-Suche liefert dabei
unterschiedliche Kandidatenzahlen und Verluste; die Ursache ist noch
nicht bestimmt. Ausführbarkeit und lokale Konsistenz sind bestätigt,
für diese ursprünglichen Vollprofile liegen keine rechnerübergreifend
identischen SR-Ergebnisse vor. Der spätere begrenzte
[Haswell-Vergleich](docs/symbolic_core_results.md) ist davon zu unterscheiden.
Auch der gepinnte Julia-Startweg ist lokal
unter WSL2 bestätigt. Der [PySR-Methodenentwurf](docs/symbolic_regression_method_plan.md)
wurde separat geprüft und um die Reviewpunkte präzisiert. Die freie Suche
ist im Dreiarm-Pilot integriert. Die drei Schritte der
[geplanten Parameterinterpretation](docs/parameter_interpretation_plan.md)
sind als begrenzte Strukturerkennung und separate numerisch abgesicherte
[Parameter-/Aliasdiagnose](docs/parameter_diagnostics.md) umgesetzt.
Der [lesende Export](docs/parameter_export.md) für vollständige gespeicherte Läufe ist ebenfalls umgesetzt;
wissenschaftliche Formelauswahl bleibt eine gesonderte Aufgabe.
Die [erste rauschfreie Kontrollserie auf Manjaro](docs/noiseless_control_results_manjaro_001.md)
ist vollständig übermittelt: Alle neun Zellen wurden abgeschlossen, aber keiner
der 28 exportierten Kandidaten erfüllt die festgelegten Kurvenfehlergrenzen.

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

Schema 3 startet zusätzlich drei freie PySR-Suchen mit demselben kleinen
technischen Budget. Die klassischen Referenzen liegen unter `reference/`:

```bash
uv run --locked ringdown-sr run configs/pilot_sr_ar1.toml --output results/sr-ar1-001
code -r results/sr-ar1-001/plot.png
uv run --locked python scripts/check_symbolic_pilot.py --verify results/sr-ar1-001
```

Das weiße Gegenstück heißt `configs/pilot_sr_white.toml`. Alle drei Arme
erhalten dieselben Samples; ihre Gewichtung unterscheidet sich. Das letzte
Kommando rechnet gespeicherte Verluste und Diagnosen unabhängig nach.
Aufrufe, Dateien, Suchbudget und Grenzen beschreibt die
[Schema-3-Dokumentation](docs/symbolic_pilot.md).

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
uv run --locked --python 3.12.14 python scripts/check_julia_startup.py
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_julia_loss.py
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_symbolic_search.py
uv run --locked python scripts/check_symbolic_pilot.py --output results/ci-sr-controls-001
```

Der Umgebungscheck kontrolliert Bibliotheksimporte, Python- und
Julia-Versionen, das aktive Julia-Projekt sowie einen Julia-Rechentest.
Er prüft außerdem die tatsächliche PythonCall-Interpreterbindung und die
geladene PythonCall-Erweiterung. Der separate
[Startweg-Check](docs/julia_startup.md) prüft zwei gleichzeitige Starts bei
einer fremden aktiven CondaPkg-Sperre.
Der separate Julia-Check führt Verlustkern- und echte Konstantenoptimierer-Tests,
zehn Residualvergleiche mit dem Python-Kern sowie zwölf unabhängige
Optimierer-Nachrechnungen aus. Diese Prüfungen gehören
nicht zur pytest-Anzahl; Details stehen im
[Julia-Verlustkern](docs/julia_loss_kernel.md).

Mit `uv run --locked pytest -v` wird jeder Testfall mit seinem Ergebnis
angezeigt. Integrationstests erzeugen unter anderem temporäre Diagramme
im pytest-Verzeichnis. Für bewusst gespeicherte Ergebnisse und Diagramme
die obigen CLI-Kontrollläufe ausführen. Nur die Schema-3-Konfigurationen
starten dabei freie Formelsuchen.

Der [CI-Workflow](docs/ci.md) führt diese Prüfungen bei Code-, Test-,
Konfigurations-, Abhängigkeits- und CI-Änderungen auf Ubuntu aus.
Reine Dokumentationsänderungen erhalten schlanke Format- und lokale
Linkprüfungen; zur Laufzeit konsumierte Dokumente bleiben ausgenommen.
Manuelle und nicht eindeutig einordenbare Läufe prüfen vollständig.

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
  prüft die Pins und stellt ausschließlich die gespeicherte Paketumgebung
  bereit. PythonCall verwendet die aktuelle Python-Umgebung; CondaPkg
  läuft mit dem Null-Backend. Nur die Vorbereitung hält die
  Installationssperre; Details stehen im [Startweg](docs/julia_startup.md).
- Die lokale `.venv` wird nicht mit Git versioniert.

Die Rolle exakter Wiederholbarkeit gegenüber wissenschaftlicher Robustheit
und die vorläufige gemeinsame BLAS-Kontrolle sind im
[Entscheidungsvermerk](docs/reproducibility_decisions.md) festgehalten.
Der [wirkungsgeprüfte freie Suchlauf](docs/symbolic_repeatability.md#kontrollierte-freie-suche-mit-gemeinsamem-blas-kern)
wurde inzwischen zweimal je Rechner ausgeführt. Unter gemeinsamem Haswell-
Kern stimmen die vollständigen Fronten des eingefrorenen gewöhnlichen
Weißrauscharms auf Manjaro und WSL2 exakt überein. Der
[Befund mit Prüfgrenzen](docs/symbolic_core_results.md) dokumentiert sieben
Kandidaten je Lauf, die Nachrechnung und den historischen nativen Vergleich.
Diese Diagnose legt keine zusätzlichen Formelrestriktionen fest.

Python-Aufrufe mit PySR oder JuliaCall werden über das Startskript
ausgeführt. Beispiel aus dem Projektordner:

```bash
uv run --locked --python 3.12.14 python scripts/run_python.py -c "import pysr; print(pysr.__version__)"
```

Für eine Python-Datei wird anstelle von `-c "..."` deren Pfad angegeben.

Der Startweg wurde am 06.10.2026 auf Manjaro erfolgreich geprüft:
PySR 2.6.0, Julia 1.13.1, SymbolicRegression 2.5.1 und PythonCall 0.9.36.
Die oben verlinkte technische CI zu `600e95b` bestätigte ihn außerdem
auf Ubuntu; eine spätere reine Dokumentations-CI ist kein neuer Startwegnachweis.
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
