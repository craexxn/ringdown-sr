# Isolierter Adapter für freie PySR-Suchläufe

Stand: 21.10.2026. Dieser Baustein setzt die freie Suchschnittstelle des
[Methodenplans](symbolic_regression_method_plan.md) für einen einzelnen Arm um.
Der geprüfte [Verlustkern](julia_loss_kernel.md) und die separat geprüfte
[Konstantenoptimierung](constant_optimization.md) werden wiederverwendet.
Die Schema-2-Pipeline und ihre Ergebnisbedeutung bleiben erhalten.

## Aufruf und Umfang

`ringdown_sr.symbolic.run_search_arm` nimmt ausschließlich `time_s`,
`observed`, optional `covariance`, einen neuen Ausgabeordner und ein
`SearchBudget` an. Alle Samples bleiben in ihrer ursprünglichen Reihenfolge.
Zeit ist in Sekunden, die Ausgabe dimensionslos. Die Funktion setzt einen
Repository-Checkout und dessen gesperrten Python-Interpreter voraus.

Ein allgemeines technisches Beispiel aus dem Projektordner:

```bash
uv run --locked --python 3.12.14 python - <<'PY'
import numpy as np
from ringdown_sr.symbolic import run_search_arm

t = np.linspace(0, 1, 16)
run = run_search_arm(t, t*t + 2*t + 1, output="results/sr-polynomial-001")
print("Status:", run.status)
print("Ergebnisse:", run.output_directory)
PY
```

Der Elternprozess importiert dabei weder PySR noch JuliaCall. Er schreibt
nur die übergebenen Arrays und das Budget in den Auftrag und startet einen
neuen Python-/Julia-Prozess über `scripts/run_python.py`. Ein zweiter Arm
bekommt einen neuen Prozess. Der Julia-Adapter lässt in einem Prozess nur
eine einzige Bindung des Kontextes zu. Signalwahrheit, wahre Parameter und
Hintergrundkontrolle gehören nicht zur Schnittstelle.

Ohne Kovarianz gilt gewöhnliche MSE, mit Kovarianz der unveränderte volle
Verlust `Q/N`. Die Kovarianz wird einmal in `FixedWindowLoss` faktorisiert
und während der Suche und Konstantenoptimierung festgehalten. Es gibt keine
zusätzliche Schätzung, Normalisierung der Eingabedaten oder Formvorgabe.

Die Suchvorgaben entsprechen Abschnitt 7 des Methodenplans: freie Operatoren
`+ - * / exp sin cos`, Float64, Knotenlimit 20, Kosten je Knoten 1,
`parsimony=0`, deaktivierte Häufigkeitsgewichte, vollständiges Fenster,
Sekunden und dimensionsbehaftete freie Konstanten. Seed 20261020,
serielle deterministische Suche, zwei Populationen mit je 32 Mitgliedern,
10 Iterationen und 50 Zyklen pro Iteration sind die technischen Standardwerte.
`SearchBudget` erlaubt andere positive Iterations-/Populationsbudgets
und einen Seed im Bereich `0 <= seed < 2**32`. Die Populationsgröße muss
mindestens 16 betragen, passend zur unveränderten Turniergröße 15.
Ein reduziertes Testbudget wird ausdrücklich im Auftrag gespeichert.

Die übrigen Vorgaben bleiben explizit: BFGS mit 20 Optimiereriterationen
und zwei Neustarts, `autodiff_backend=None`, kein Warm-Start oder `guesses`,
kein Batching, Denoising oder Feature-Selecting. Der Backend-Sonderfall Newton
bei einer einzelnen Konstante bleibt bestehen. Der Adapter ist an PySR 2.6.0
und SymbolicRegression 2.5.1 gebunden; der Launcher prüft die Laufzeit-Pins.

## Eigenes Ausgabeformat für einen Sucharm

Das Format heißt `ringdown-sr-search-arm-1`. Es ist ein eigenständiger
technischer Arm-Auftrag, noch kein neues Dreiarm-Pilotschema.

| Datei | Inhalt |
| --- | --- |
| `request.json`, `inputs.npz` | Budget, unveränderte Zeit-/Messwerte und gegebenenfalls Kovarianz; NPZ ohne Python-Pickle |
| `worker.log`, `status.json` | Start-/Suchdiagnosen, Rückgabecode, Status und Gesamtzeit einschließlich Launcher |
| `pysr_parameters.json` | Alle durch `get_params()` zugänglichen Python-Parameter |
| `backend_options.json` | Sämtliche 68 effektiven Julia-Optionsfelder mit Typ und ungekürzter Darstellung; einschließlich aufgelöster Bibliotheksvorgaben |
| `result.json` | Gesamte gefundene Pareto-Front, technische Auswahl, Baseline, Normalisierung, Callback-Zähler und Zeiten |
| `search_state.jls`, `search_options.jls` | Versionsgebundene Julia-Serialisierungen; kein vollständiger RNG-Checkpoint und kein eigenständiges portables Dateiformat |
| `pysr/` | Zusätzlich von PySR erzeugte Dateien; verkürzte Formeln und Pickle sind für unseren Verlust-Replay nicht maßgeblich |
| `metadata.json` | Git-/Quellstand, Lockdatei-Prüfsummen, Software-/Numerikdiagnosen, Julia-/Backend-Version und Worker-Interpreter/PID |
| `RingdownSRLoss.jl`, `RingdownSRSearch.jl` | Tatsächlich verwendete projektspezifische Julia-Quellen |
| `checksums.json` | SHA-256 aller abgeschlossenen Nutzdateien einschließlich PySR-Artefakten; das noch wachsende Log und der anschließend geschriebene Status sind ausgenommen |

Die Front enthält jeden von `calculate_pareto_frontier` zurückgegebenen
Kandidaten, keine vollständige Aufzählung aller untersuchten oder möglichen
Bäume. Für jeden Kandidaten werden der rohe Backend-Verlust, Komplexität,
die Python-Score-Diagnose, Vorhersage/Residuum und ein vollständiger Baum
exportiert. Die technische Beispielkurve ist das Minimum des rohen Verlusts;
bei exakt gleichem Verlust entscheidet die kleinere Komplexität.
Es gibt keine Auswahl anhand unabhängiger Daten oder wissenschaftliche
Formelinterpretation. Insbesondere werden hier keine Ringdown-Frequenzen,
Abklingzeiten oder Aliasparameter aus allgemeinen Ausdrücken abgeleitet.
Die Alias-Konvention bleibt Voraussetzung für einen späteren Parameterexport.

Der Baum hält Arity, Operatorname und versionsgebundenen Operatorindex,
Variable 1 und sämtliche Konstanten als exakte Float64-Hexadezimaldarstellung
fest. Die Reihenfolge der binären Teilausdrücke bleibt erhalten. Vor einem
erfolgreichen Export wird er in Julia neu aufgebaut, erneut auf Einheiten
geprüft und ausgewertet. Python wertet denselben Baum ohne SymPy-Umschreibung
aus. Der Verlust wird zusätzlich mit dem Python-Rechenkern nachgerechnet.
Vorhersagen werden mit `rtol=1e-12, atol=1e-14`, rohe/CSV-/Replay-Verluste
mit `rtol=1e-10, atol=0` verglichen. Diese konservativen technischen Schranken
lassen kleine Unterschiede elementarer Gleitkommafunktionen zu; sie sind
keine allgemeine Fehlergarantie für beliebig schlecht konditionierte Bäume
oder Kovarianzen. Ein nicht bestandener Replay beendet den Arm als Fehler,
ohne Toleranzen nachträglich anzupassen. Ein exakter Nullverlust erhält kein
Epsilon und muss auch im Verlust-Replay exakt null bleiben.

`library_score` bezeichnet ausdrücklich `pysr.sr.calculate_scores` aus
PySR 2.6.0 bei logarithmischer Skala. Nicht endliche Werte werden als `null`
mit Status `positive_infinity`, `negative_infinity` oder `nan` gespeichert.
Die gesamte JSON-Ausgabe verbietet nicht standardkonforme NaN-/Infinity-Zahlen.

Baseline und `cost_normalization` stammen aus dem tatsächlich von PySR
verwendeten Dataset. Der exportierte `backend_seed` ist der von PySR aus dem
Python-Seed abgeleitete Seed. Der Callback-Zähler zählt alle Aufrufe während
`fit`, einschließlich Initialisierung und Konstantenoptimierung; er ist
nicht mit dem internen Evaluationszähler des Backends gleichzusetzen.
Letzteren gibt `equation_search` in diesem Startweg nicht zurück, daher wird
er als nicht verfügbar gekennzeichnet. Die Zeiten unterscheiden Worker-Setup,
`fit` einschließlich JIT und Python-Exports sowie den gesamten Startweg.
Eine reine Suchzeit ohne JIT wird damit nicht behauptet.

Bestehende Ausgabeordner werden abgelehnt. Ein Prozessfehler erhält den Status
`failed`; Eingaben, Log und bereits entstandene Dateien bleiben erhalten.
Ein Abbruch im Elternprozess wird ebenfalls als Fehler protokolliert und
weitergereicht. Auf Linux/WSL beendet der Elternprozess dabei seine eigene
Worker-Prozessgruppe einschließlich Unterprozessen. Laufende Suchprozesse
haben keine zusätzliche Zeitgrenze; die Bootstrap-Fristen des Launchers
gelten weiterhin. Die neue Schnittstelle ist bisher auf Linux-Ausführung
ausgerichtet, native Windows-Ausführung ist nicht geprüft.

## Prüfungen und nächste Integration

```bash
uv run --locked pytest -q
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_symbolic_search.py
```

Die schnelle pytest-Suite prüft Eingaben, festgelegte Suchpolitik,
verlustbasierte Auswahl einschließlich eines späteren besseren Kandidaten,
Score-Endlichkeit, exakte Baumkonstanten/Auswertungsreihenfolge,
Prozessauftrag, exklusive Ausgaben und Fehler-/Abbruchbehandlung.
Ein realer Prozessgruppentest sichert das Beenden eigener Unterprozesse ab.

Das separate Integrationsskript startet echte `PySRRegressor.fit`-Suchen.
Mit `C=[[2.5,1.5],[1.5,4.5]]`, `y=[1,0]` prüft es über den tatsächlich
installierten Callback für den Nullausdruck den handgerechneten Wert `1/4`;
MSE liefert `1/2`. Der Ablauf gewichtet → gewöhnlich → gewichtet erfolgt
in drei neuen Prozessen mit reduziertem, protokolliertem Budget. Alle
gefundenen Kandidaten, Auswahl und Dateiprüfsummen werden nachgerechnet.
Eine zusätzliche feste Formel verwendet alle sieben Operatoren; ihre
AST-Rückübertragung, nicht dezimale Konstanten einschließlich Subnormalzahl
und negativem Nullwert sowie volle Kovarianzquadratik werden unabhängig
kontrolliert. Die tatsächliche Python-Score-Funktion muss beim ersten
Nullverlust Score 0 und beim Übergang auf null einen unendlichen Score liefern.
Die vorhandenen Newton-/BFGS-Referenzprüfungen bleiben ein eigener CI-Schritt.

Lokal bestanden am 21.10.2026 in der nativen Python-3.12.14-Umgebung der
Codex-Ausführung 506 Python-Tests, die vorhandenen 283 Julia-Prüfungen,
zehn Residual-Replays und zwölf Optimierer-Nachrechnungen. Ein zusätzlicher
allgemeiner Polynomlauf mit dem oben angegebenen Standardbudget exportierte
vier Pareto-Kandidaten; alle bestanden Baum-Rückübertragung und Verlust-Replay.
Das ist ein technischer Funktionsnachweis, keine neue Ringdown-Studie.

Diese Nachweise belegen die technische Schnittstelle. Der nächste Schritt
ist ein versionierter vollständiger SR-Pilot mit denselben Schema-2-Messdaten,
drei Armen und gemeinsamen nachgelagerten Diagnosen. Die neuen Suchläufe
müssen anschließend auf Manjaro und WSL2 geprüft werden. Statistische
Rekonstruktionsleistung, physikalische Formelidentifikation und die
wissenschaftliche Formelauswahl sind weiterhin offen.
