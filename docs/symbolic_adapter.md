# Isolierter Adapter für freie PySR-Suchläufe

Stand: 22.10.2026. Dieser Baustein setzt die freie Suchschnittstelle des
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
technischer Arm-Auftrag. Der [Schema-3-Pilot](symbolic_pilot.md) verwendet
drei solcher Aufträge und behält ihre vollständigen Ausgaben bei.

| Datei | Inhalt |
| --- | --- |
| `request.json`, `inputs.npz` | Budget, unveränderte Zeit-/Messwerte und gegebenenfalls Kovarianz; NPZ ohne Python-Pickle |
| `worker.log`, `status.json` | Start-/Suchdiagnosen, Rückgabecode, Status und Gesamtzeit einschließlich Launcher |
| `pysr_parameters.json` | Alle durch `get_params()` zugänglichen Python-Parameter |
| `backend_options.json` | Sämtliche 68 effektiven Julia-Optionsfelder mit Typ und ungekürzter Darstellung; einschließlich aufgelöster Bibliotheksvorgaben |
| `result.json` | Gesamte gefundene Pareto-Front, technische Auswahl, Baseline, Normalisierung, Callback-Zähler und Zeiten |
| `search_state.jls`, `search_options.jls` | Versionsgebundene Julia-Serialisierungen; kein vollständiger RNG-Checkpoint und kein eigenständiges portables Dateiformat |
| `pysr/` | Zusätzlich von PySR erzeugte Dateien; verkürzte Formeln und Pickle sind für unseren Verlust-Replay nicht maßgeblich |
| `metadata_initial.json` | Unveränderliche erste Herkunftsaufnahme vor dem Workerstart: Git-/Quellstand, Lockdatei- und Adapterquell-Prüfsummen, Python-/Numerikumgebung und Elternprozess |
| `metadata.json` | Ergänzte Herkunftsaufnahme mit Worker-Phase, vor `fit` erfasster Herkunft/Umgebung, Julia-/Backend-Version, Worker-Interpreter/PID und gegebenenfalls Fehlerdiagnose |
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
Für den Vorhersagevergleich wird die gemeinsame Skala
`s=max(max(abs(p_python)),max(abs(p_julia)))` verwendet. Für `s>0` werden
**beide Vektoren zuerst durch `s` geteilt** und anschließend mit
`rtol=1e-12, atol=1e-14` verglichen. Der absolute Anteil entspricht damit
`1e-14*s` in den ursprünglichen Amplitudeneinheiten; es gibt keine feste
Untergrenze von 1 oder einer anderen Amplitude. Die Division vor dem Vergleich
vermeidet sowohl den Unterlauf einer winzigen absoluten Toleranz als auch
den Überlauf einer unskalierten Differenz sehr großer Vorhersagen.
Bei `s=0` sind beide Vektoren bereits exakt null. Der Vergleich kontrolliert
die Vektoren relativ zu ihrer gemeinsamen Maximalamplitude, nicht die
relative Genauigkeit jeder einzelnen sehr kleinen Komponente.
Skala und maximale normierte Abweichung werden pro Kandidat unter
`prediction_replay` gespeichert. Die Messwerte und die Zielfunktion werden
durch diese reine Replay-Prüfung nicht skaliert.

Rohe/CSV-/Replay-Verluste werden weiterhin mit `rtol=1e-10, atol=0` verglichen.
Diese konservativen technischen Schranken
lassen kleine Unterschiede elementarer Gleitkommafunktionen zu; sie sind
keine allgemeine Fehlergarantie für beliebig schlecht konditionierte Bäume
oder Kovarianzen. Ein nicht bestandener Replay beendet den Arm als Fehler,
ohne Toleranzen nachträglich anzupassen. Ein exakter Nullverlust erhält kein
Epsilon und muss auch im Verlust-Replay exakt null bleiben.

Die Gegenprobe `y=0`, `C=1e-42*I`, `p=[1e-21,-1e-21]` und `-p` besitzt
zweimal denselben Verlust von ungefähr 1. Die neue Vorhersageprüfung weist
die Vorzeichenumkehr dennoch eindeutig zurück. Gleiche Verluste ersetzen
daher weiterhin keinen gesonderten Vorhersagevergleich.

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

Die erste Herkunftsaufnahme wird **vor dem Launcher-/Workerstart** in
`metadata_initial.json` und zunächst auch in `metadata.json` gespeichert.
Der Worker verändert die erste Datei nicht. In der ergänzten Datei bleiben
`provenance` und `adapter_source_sha256` dieser ersten Aufnahme erhalten.
Noch vor `model.fit` kommen `worker_provenance`,
`worker_adapter_source_sha256`, tatsächliche Julia-Version/Projekt und
die Worker-Umgebung mit Snapshotkennung `before_fit` hinzu. Nach erfolgreichem
Replay ergänzt `environment_after_search` die später geladenen Bibliotheken;
Git-Stand und Python-Quellprüfsummen werden nach `fit` nicht neu zugeordnet.
Die beiden Herkunftsaufnahmen sind zeitlich bezeichnet und machen mögliche
Checkout-Änderungen zwischen Eltern- und Workeraufnahme sichtbar.

Worker-Fehler erhalten `phase=failed`, `failed_during` und eine Diagnose.
Import-, Fit- und Replay-Fehler lassen alle bereits geschriebenen Aufnahmen
erhalten. Stirbt der Worker vor eigener Fehlerbehandlung oder scheitert der
Launcher, bleibt mindestens die erste Aufnahme bestehen. `status.json`
enthält den vom Elternprozess beobachteten Abschluss; die Metadatenphase
bezeichnet die zuletzt protokollierte Workerphase. Auch gescheiterte Läufe
können so ihrem ursprünglichen Code-/Umgebungsstand zugeordnet werden.

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
Zusätzliche Regressionstests weisen die gleich verlustbehaftete
Vorzeichenumkehr bei `1e-21` zurück und prüfen Skalen von `1e-200` bis `1e200`,
exakte Nullvektoren, Subnormalzahlen und große endliche Werte. Gezielte
Import-, Fit- und Replay-Fehler prüfen die erhaltenen Anfangs- und
Laufzeitmetadaten; eine während `fit` simulierte Quelländerung darf die
vorher erfasste Herkunft nicht überschreiben.

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
Eine zusätzliche echte Julia-Auswertung bei Amplitude `1e-21` bestätigt den
korrekten Baum-Replay und den gewichteten Verlust 1; die Vorzeichenumkehr
muss an der normierten Vorhersageprüfung scheitern. In den freien Suchläufen
werden außerdem die unveränderte Anfangsaufnahme, die vor `fit` erfassten
Metadaten und ihre Aufnahme in das Prüfsummenmanifest kontrolliert.

Am ursprünglichen Adapterstand `c129c8c` bestanden am 21.10.2026 in der
nativen Python-3.12.14-Umgebung der Codex-Ausführung 506 Python-Tests,
die vorhandenen 283 Julia-Prüfungen,
zehn Residual-Replays und zwölf Optimierer-Nachrechnungen. Ein zusätzlicher
allgemeiner Polynomlauf mit dem oben angegebenen Standardbudget exportierte
vier Pareto-Kandidaten; alle bestanden Baum-Rückübertragung und Verlust-Replay.
Das ist ein technischer Funktionsnachweis, keine neue Ringdown-Studie.

Nach der Nachbesserung des fachlichen Reviews zu `c129c8c` bestanden lokal
520 Python-Tests, darunter 14 zusätzliche Regressionstests. Die echte
Julia-Auswertung bei Amplitude `1e-21`, alle drei freien A–B–A-Suchen und
die Metadaten-/Prüfsummenkontrollen bestanden ebenfalls. Eine ausschließlich
im Arbeitsspeicher deaktivierte Vorhersageprüfung lässt den neuen
Worker-Gegenprobentest wie erwartet scheitern: Die Regression prüft damit
auch die tatsächliche Einbindung des Vergleichs im Worker.

Diese Nachweise belegen die technische Schnittstelle. Der
[Schema-3-Pilot](symbolic_pilot.md) verbindet sie inzwischen mit denselben
Schema-2-Messdaten, drei Armen und gemeinsamen nachgelagerten Diagnosen.
Die neuen Suchläufe
müssen anschließend auf Manjaro und WSL2 geprüft werden. Statistische
Rekonstruktionsleistung, physikalische Formelidentifikation und die
wissenschaftliche Formelauswahl sind weiterhin offen.
