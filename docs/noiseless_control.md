# Rauschfreie Entwicklungsdiagnose: Bedienung und Artefakte

Die Implementierung folgt dem separat geprüften
[Methodenplan](noiseless_control_plan.md) aus PR #32. Dessen eingefrorener
Dokumentstand wird durch Commit und SHA-256 identifiziert. Suche, Erkenner,
Parameterdiagnose, Abhängigkeiten und bestehende Ergebnisformate bleiben
unverändert. Implementierungsreview und gezieltes Nachreview zu PR #34
sind abgeschlossen. Die anschließend auf Manjaro ausgeführte erste
[Neun-Zellen-Serie](noiseless_control_results_manjaro_001.md) ist vollständig
übermittelt; sie erreicht die festgelegten Kurvenfehlergrenzen nicht.

## Feste Serie

`scripts/run_noiseless_control.py` führt genau die neun geplanten Zellen aus:
drei Seeds, `niterations=10/50/200`, zyklische Reihenfolge und jeweils ein
frischer gewöhnlicher Suchworker. Es gibt keine frei einstellbaren Budgets,
zusätzlichen Seeds, Kovarianz, Hintergrundfenster, Referenzfits oder Fortsetzung.
Die Zielstruktur wird der Suche nicht vorgegeben. Der ursprüngliche
Auswahlindex wird gegen die Trainingsregel geprüft und unverändert behalten;
auch ein besser interpretierbarer Frontkandidat ersetzt ihn nicht.

Trainingsdaten (`128` Werte, `fs=4096 Hz`) und analytische Referenzwerte auf
`889` Zwischenpunkten entstehen einmalig. Die Suchfunktion erhält ausschließlich
die Trainingszeiten, beobachteten Werte und das jeweilige Suchbudget.
Nur Datenerzeugung und nachgelagerte Diagnose nutzen die Wahrheitsparameter;
Diagnosepunkte und Wahrheitsparameter werden dem Suchworker nicht übergeben.
Die vorhandene [BLAS-Kontrolle](symbolic_repeatability.md) prüft die tatsächlich
geladenen Haswell-Pools mit Limit 1 vor Fit und nach Suche in jedem Worker.
Hinzu kommen anfängliche und abschließende Aufnahmen im Elternprozess.

## Ausführung nach Implementierungsreview

Auf dem vereinbarten Manjaro-Referenzrechner aus dem sauberen Checkout des
geprüften Implementierungscommits. Der Ausgabeordner muss neu sein; `results/`
ist im Repository bereits von Git ausgenommen. Die Umgebungsvariablen müssen
vor dem Python-Start gesetzt sein. Es gibt keinen stillen CPU-native-Fallback.

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_noiseless_control.py --label manjaro --output results/noiseless-control-001
```

Der Elternprozess importiert weder PySR noch JuliaCall. Die neuen Worker
verwenden den vorhandenen gepinnten Julia-Launcher und dessen Behandlung
eigener Prozessgruppen. CPU-native Aufrufe der bestehenden Werkzeuge ändern
sich dadurch nicht. Der Treiber setzt keine globale BLAS-Vorgabe und keine
zusätzliche Zeitgrenze innerhalb der Suchalgorithmen.

## Ausgabe

| Datei bzw. Verzeichnis | Inhalt |
| --- | --- |
| `report.json` | Vollständiger neuer Bericht im Format `ringdown-sr-noiseless-control-1`, alle neun Zellen und deren Zustände |
| `summary.md` | Lesbare Einzelwerttabelle und deskriptive Budgetübersicht |
| `training.npz` | Eingefrorene Trainingszeiten und beobachtete Werte |
| `diagnostic.npz` | Eingefrorene Zwischenzeiten und analytische Referenzwerte |
| `plan.md` | Unveränderte Kopie des geprüften Methodenplans |
| `runtime/` | Kopien der bestehenden kontrollierten Worker-/Prüfwerkzeuge und des neuen Treibers |
| `cell-01/` bis `cell-09/` | Bestehende vollständige Workerexporte mit allen Kandidaten, Originalauswahl, Requests, tatsächlichen Optionen, Laufzeiten, Umgebungen, Zuständen und Logs |
| `metadata.json` | Abschließender Serienstatus und SHA-256-Manifest der gespeicherten Artefakte |

Der Bericht enthält zusätzlich die kanonischen Little-Endian-Float64-
Arrayprüfsummen und Quellenhashes. Alle konsumierten Workerdateien werden
gegen das Workermanifest geprüft, Eingaben und Auswahl validiert sowie
relevante Daten/Quellen abschließend erneut geprüft. Die aktuelle
Diagnoseherkunft bleibt von den originalen Workeraufnahmen getrennt.
Prüfsummen bestätigen gespeicherte Konsistenz, keine externe Authentizität.
Dieses neue Gesamtformat ist kein Schema-3-Parameterexport.

### Prüfung von Seeds, Backendvorgaben und Trainingsverlusten

Jede Zelle wird auch gegen absolute Vorgaben geprüft, einschließlich der ersten
Zelle. Der zusätzliche Vergleich mit der ersten Zelle ersetzt diese Prüfung
nicht. Der Pythonseed muss zum Zellbudget und zu den angeforderten PySR-Parametern
passen. Der tatsächliche Backendseed muss sowohl im Ergebnis als auch in den
exportierten Backendoptionen dem durch PySR 2.6.0 abgeleiteten Seed entsprechen:
`RandomState(python_seed).randint(0, 2**31 - 1)`. Die Nachrechnung nutzt einen
lokalen Generator und verändert keinen globalen NumPy-Zufallszustand.

| Pythonseed | Erwarteter Julia-Backendseed |
| --- | --- |
| `20261020` | `465951028` |
| `20261021` | `1616241070` |
| `20261022` | `651396412` |

Die tatsächlichen Backendfelder werden gegen Größe/Tiefe, Populationszahlen,
Zyklen, Operatorfolge und -anzahl, uneingeschränkte Operatorbedingungen,
Einheitskomplexitäten, Parsimony-/Frequenzmechanismen, Batching, Determinismus,
Turbo/Bumper, BFGS mit 20 Optimiereriterationen und zwei Neustarts,
Verlustcallback/-skala sowie die vorgesehenen leeren Zusatz-/Abbruchbedingungen
geprüft. Fehlende, doppelte oder widersprüchliche relevante Felder werden
abgelehnt. Übrige gepinnte Bibliotheksdefaults bleiben vollständig gespeichert
und werden zusätzlich zwischen Zellen verglichen. Nur der bereits einzeln
geprüfte Backendseed wird aus diesem Vergleich ausgeblendet.

Die Zuordnung folgt den gepinnten Quellen:
[PySR 2.6.0](https://github.com/astroautomata/PySR/blob/v2.6.0/pysr/sr.py),
[SymbolicRegression 2.5.1](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/OptionsStruct.jl),
[DynamicExpressions 2.12.0](https://github.com/astroautomata/DynamicExpressions.jl/blob/v2.12.0/src/OperatorEnum.jl)
und [Optim 2.2.2](https://github.com/JuliaNLSolvers/Optim.jl/blob/v2.2.2/src/types.jl).
Die nötigen Julia-Darstellungen werden eng verglichen bzw. ausgewertet;
es wird kein gespeicherter Ausdruck als Code ausgeführt.

Vor der Auswahlprüfung wird für **jeden** Kandidaten aus den eingefrorenen
Beobachtungen und gespeicherten Vorhersagen das Residuum nachgerechnet.
Gespeicherte Residuen müssen in Form und Float64-Bits übereinstimmen. Die
gewöhnliche MSE wird numerisch abgesichert aus diesem Residuum berechnet und
mit dem gespeicherten Trainingsverlust verglichen (`rtol=1e-10`, `atol=0`,
wie bei den bestehenden Verlust-Replays). Dies sind technische
Konsistenzgrenzen, nicht die Entwicklungsmarkierungen für Kurven oder Parameter.
Erst danach wird die ursprüngliche Auswahl gegen die gespeicherte Trainingsregel
geprüft. Bei Widerspruch wird abgebrochen; Verlust oder Auswahlindex werden
nicht korrigiert. Auch passend neu berechnete Workerprüfsummen ersetzen diese
inhaltlichen Prüfungen nicht. Die Prüfnachweise werden im Bericht erhalten.

## Getrennte Bewertungen und Grenzen

- Kurvenfehler benutzen die Referenznorm ohne Kandidatenmaßstab oder
  Einheitsuntergrenze im Nenner. Nicht endliche bzw. numerisch unbestimmte
  Ergebnisse erhalten `null` und einen Grund. Die Markierung verlangt beide
  im Plan vorgegebenen Grenzen auf beiden Gittern.
- Der bestehende begrenzte Erkenner wird unverändert angewandt. Seine
  Status-/Erstgrundzahlen über alle Frontkandidaten sind eine Abdeckungsangabe;
  Frontkandidaten sind keine unabhängigen Wiederholungen.
- Parameter werden nur bei geeigneter Struktur, verfügbarer nicht degenerierter
  Aliasklasse und bestandenen Replays beurteilt. Die komplexe Amplitude
  berücksichtigt Vorzeichen und Phase. Fehlerwerte, rohe signierte Frequenz,
  Aliasfrequenz und sämtliche ursprünglichen Diagnosestatus bleiben erhalten.
- Auf Zwischenzeiten wird immer der vollständige Originalbaum ausgewertet.
  `250+fs` und `250+8*fs` sind getrennte getestete Gegenfälle: Der zweite
  kann beide Raster und die Aliasklassenprüfung bestehen und außerhalb des
  gemeinsamen Achtelrasters dennoch das Vorzeichen wechseln.

`completed` bezeichnet den technischen Abschluss. Auch eine vollständig
abgeschlossene Serie ohne passende Kurven oder erkannte Strukturen ist ein
zulässiges Ergebnis. `physical_identification` bleibt `not_assessed`.
Entwicklungsmarkierungen sind keine wissenschaftlichen Identifikationsgrenzen.

## Fehler und Abbruch

Bei einem Worker-, Quellen-, Pool- oder Verifikationsfehler stoppt die Serie;
es gibt keine automatische Wiederholung oder Ersatzwahl. Gestartete Zellen
heißen zunächst `running`, danach `completed`, `failed` oder `aborted`.
Nicht gestartete Zellen bleiben `planned`. Suchstatus und Diagnoseinformationen
werden zusätzlich erhalten, soweit verfügbar.

Ctrl+C und SIGTERM im CLI lösen die bestehende Worker-Prozessbehandlung aus
und speichern den unvollständigen Bericht. Ein harter Prozess-/Rechnerabbruch
kann kein abschließendes Manifest garantieren; der letzte `running`-Stand
ist kein Abschlussnachweis. Vorhandene Ordner werden stets abgelehnt.
Ein weiterer Versuch wäre eine neue, ausdrücklich zu dokumentierende Serie.

Nur Budgetgruppen mit allen drei vollständig diagnostizierten Zellen erhalten
Minimum/Median/Maximum; bei fehlenden numerischen Werten wird der endliche
Nenner angegeben. Scheitert die abschließende Quellen-/Numerikprüfung, werden
sämtliche Budgetzusammenfassungen als `not_assessed` gesperrt. Einzelartefakte
und Fehlergründe bleiben erhalten. Drei Starts begründen keine belastbare
Erfolgswahrscheinlichkeit und keinen automatischen Produktionsbudgetentscheid.

## Technische Prüfungen

```bash
uv run --locked pytest -q tests/test_noiseless_control.py
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Die Tests verwenden unabhängige Metrik-/Rasterreferenzen und kontrollierte
Workerdateien. Sie prüfen unter anderem Datenidentität, Auswahl ohne
Neurangierung, beide Alias-Gegenfälle, Vorzeichen/Phase, nicht endliche Werte,
veränderte Optionen, fehlerhafte Prüfsummen, Quellenänderungen und Abbrüche.
Diese Tests starten keine echte Suche und ersetzen kein Implementierungsreview
oder die späteren neun vereinbarten Kontrollläufe.
