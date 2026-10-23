# Dreiarm-Pilot mit freier symbolischer Regression

Stand: 22.10.2026. Schema 3 verbindet die bestehende
[Schema-2-Pipeline](estimated_covariance_pilot.md) mit dem
[Suchadapter](symbolic_adapter.md). Die Budgets und die angezeigte
Beispielkurve sind technische Kontrollvorgaben. Wissenschaftliche
Versuchsplanung und Formelauswahl bleiben gesonderte Aufgaben.

## Start und sichtbare Ergebnisse

Nach `uv sync --locked --dev --python 3.12.14`, aus dem Projektordner:

```bash
uv run --locked ringdown-sr run configs/pilot_sr_white.toml --output results/sr-white-001
uv run --locked ringdown-sr run configs/pilot_sr_ar1.toml --output results/sr-ar1-001
code -r results/sr-white-001/plot.png
code -r results/sr-ar1-001/plot.png
```

Die Elternpipeline importiert kein Julia/PySR. Jeder Sucharm startet einen
eigenen Python-/Julia-Prozess über den gepinnten Launcher. Einrichtung und
JIT können mehrere Minuten dauern. Bestehende Ausgabeordner werden
abgelehnt; Wiederholungen erhalten einen neuen Namen. Ergebnisse unter
`results/` werden nicht versioniert und müssen separat gesichert werden.

Das Terminal zeigt je Arm Anzeigegleichung, gewöhnliche MSE und `Q_true/N`.
Das gemeinsame Diagramm enthält Messwerte, bekanntes synthetisches Signal,
drei SR-Beispielkurven und Residuen. Dargestellt werden ausschließlich
angepasste Samples: Die verbundenen Linien belegen keine Übereinstimmung
zwischen den Samples. Klassische Fits und ihre Diagramme liegen weiterhin
im Unterordner `reference/`.

## Gemeinsame Daten und getrennte Suche

1. Die vollständig validierte Konfiguration wird auf kollidierende
   anfängliche Zufallszustände geprüft, bevor Ausgaben oder Daten entstehen.
2. Eine abgeleitete Schema-2-Konfiguration erhält Signal, Abtastung,
   Rauschen, Hintergrundrollen, Schrumpfung und klassische Fit-Einstellungen
   unverändert. Die bestehende Pipeline erzeugt Daten und schätzt die
   Kovarianz **einmal**.
3. Zusätzlich speichert sie `reference/comparison_inputs.npz`: Zeit,
   sauberes Signal, Rauschen, Messwerte sowie wahre und geschätzte Kovarianz
   als Float64-Arrays. Dieser binäre Übergang vermeidet eine CSV-Rundreise.
   Seine Prüfsumme wird vor der Übergabe kontrolliert.
4. Drei isolierte Suchprozesse bekommen bitgleich dieselben Zeit- und
   Messwerte. Nur die Gewichtung unterscheidet sich: gewöhnliche MSE,
   wahre Kovarianz oder eingefrorene geschätzte Kovarianz.
5. Vor der gemeinsamen Auswertung werden Aufträge, Arrays, Prüfsummen,
   Bäume, Vorhersagen, Residuen und Verluste **aller** exportierten
   Kandidaten sowie ihre verlustbasierte Auswahl kontrolliert.

Der Suchauftrag enthält weder sauberes Signal noch wahre Parameter,
klassische Fit-Ergebnisse oder Hintergrund-Kontrollfenster. Die Grenzen
und Startpunkte unter `[fit]` gelten allein für die klassischen Referenzen.
Zeit in Sekunden, Reihenfolge und vollständiges Fenster bleiben erhalten.

Nur Hintergrundtraining bestimmt rohe Matrix und Schrumpfungsziel;
Validierung wählt Alpha. Kontrollfenster liefern nachgelagerte Diagnosen.
Kein Refit und keine Anpassung der Kovarianz an SR-Residuen. Die gemeinsamen
Messdaten ergeben einen gepaarten Kontrollfall, keine unabhängige Bewertung.

## Konfiguration und Auswahl

Schema 3 übernimmt alle Tabellen aus Schema 2 und verlangt zusätzlich:

```toml
[symbolic_search]
seed = 20261020
niterations = 10
populations = 2
population_size = 32
ncycles_per_iteration = 50
```

Alle Arme erhalten diese fünf Werte identisch. Der Seed liegt zwischen
0 und `2**32-1`; die übrigen Werte sind positive Ganzzahlen, die
Populationsgröße mindestens 16. Unbekannte Felder werden abgelehnt.
Grammatik, Knotenlimit, Einheitenprüfung, Konstantenoptimierung und übrige
Adaptervorgaben bleiben fest wie im [Suchadapter](symbolic_adapter.md).
Es gibt keine Startformel. Gleiche nominelle Budgets und Seeds garantieren
bei verschiedenen Verlusten weder gleiche Suchtrajektorien noch Rechenkosten.

Jeder Arm behält seine gesamte gefundene Pareto-Front. Für die Anzeige
wird das Minimum des rohen Trainingsverlusts gewählt, bei exakt gleichem
Verlust die kleinere Komplexität. **Erst nach dieser eingefrorenen Auswahl**
berechnet die Elternpipeline gemeinsame Diagnosen. Wahrheit und
Hintergrundkontrolle dürfen die Auswahl nicht beeinflussen.

Für `r = observed - prediction` gelten:

| Feld | Bedeutung |
| --- | --- |
| `training_loss` | Roher Armverlust: gewöhnliche MSE oder volles `Q_used/N` |
| `ordinary_mse` | `r.T @ r / N`, gemeinsam in Amplitudenquadrat |
| `q_used_per_sample` | `r.T @ solve(C_used, r) / N`; beim gewöhnlichen Arm `null`, da keine Gewichtungsmatrix verwendet wird |
| `q_true_per_sample` | `r.T @ solve(C_true, r) / N`, gemeinsamer bekannter Maßstab für alle drei Beispielkurven |
| `mse_to_clean_signal` | Fehler zur synthetischen Wahrheit, ausschließlich nach Auswahl |

Rohe Trainingsverluste unterschiedlicher Gewichtungen liegen auf
unterschiedlichen Skalen; zwischen den Armen wird daraus keine Formel
ausgewählt. Alle Kennzahlen tragen `evaluation_scope=fitted_samples_only`,
die gemeinsamen Diagnosen zusätzlich `diagnostic_role=post_selection_only`.
Auch der Fehler zum sauberen Signal ist keine unabhängige
Generalisierungsprüfung nach Anpassung desselben Messfensters.

Allgemeine SR-Ausdrücke erhalten `parameter_interpretation=not_attempted`.
Frequenz, Abklingzeit und physikalische Identifikation werden nicht aus
ihnen abgeleitet. Die [Alias-/Phasenreferenzen](alias_references.md) sind
als unabhängige Prüfungen vorgegebener Ausdruckspaare umgesetzt. Eine
Strukturerkennung mit numerisch abgesicherter Parameterinterpretation
bleibt Voraussetzung für einen späteren Parameterexport.
Der [Methoden- und Abnahmeplan](parameter_interpretation_plan.md) beschreibt
den vorgesehenen begrenzten Erkenner und die nachgelagerte Diagnose;
der [Erkenner mit rohen Koeffizienten](structure_recognition.md) ist als
separates Modul umgesetzt. Numerische Parameter-/Aliasdiagnose und deren
Export stehen noch aus; die bisherigen Pilotdateien bleiben unverändert.

## Dateien, Herkunft und Fehler

| Pfad | Inhalt |
| --- | --- |
| `config.toml`, `resolved_config.json` | Ursprünglicher Schema-3-Auftrag und validierte Werte |
| `reference_config.toml` | Tatsächlich verwendete Schema-2-Konfiguration |
| `reference/` | Klassische Vergleichsausgabe, Hintergrundfenster, RNG-Zustände, Kovarianzen und zusätzlicher binärer Übergang |
| `symbolic/ordinary/`, `symbolic/known_covariance/`, `symbolic/estimated_covariance/` | Einzelne Adapterausgaben mit Eingaben, gesamter Front, Baumexport, Optionen, Logs, Herkunft und Prüfsummen |
| `result.json` | Status jeder Stufe, eingefrorene Anzeigeauswahl und gemeinsame Diagnosen |
| `samples.csv`, `plot.png` | Gemeinsame Samples und erfolgreich geprüfte SR-Kurven/Residuen |
| `metadata_initial.json` | Unveränderliche Herkunfts-/Umgebungsaufnahme vor der Berechnung |
| `metadata.json` | Herkunft mit Abschlussstatus, Laufzeit und rekursiven Prüfsummen; die Datei selbst ist ausgenommen |

Schema 1 und normale Schema-2-Aufrufe ändern ihre Ausgaben nicht. Der
binäre Übergang entsteht ausschließlich für Schema 3.

Scheitert die klassische Vorbereitung, starten keine Sucharme. Scheitert
ein Arm oder sein Eltern-Replay, bleibt er als `failed` erhalten; die
anderen Arme werden weiterhin versucht. Insgesamt gilt dann
`comparison_failed`, CLI-Rückgabecode 1. Ein vollständiger Vergleich
erfordert drei erfolgreiche, geprüfte Arme. Abbrüche erhalten `aborted`,
Exportfehler `export_failed`; beide werden weitergereicht. Metadaten und
Teilresultate bleiben erhalten. Details stehen im Wurzelresultat und in
den einzelnen `worker.log`-Dateien.

Die Anfangsherkunft wird nicht nachträglich einem späteren Checkout
zugeordnet. Jeder Arm ergänzt eigene Aufnahmen vor Workerstart und vor
`fit`, einschließlich tatsächlicher Julia-/Backend-Versionen. Die
Wurzel-Prüfsummen umfassen auch abgeschlossene Logs und Statusdateien.
Ausgaben nicht während eines Laufs bearbeiten.

## Nachrechnung und CI

Vorhandene Ergebnisse ohne neue Suche prüfen:

```bash
uv run --locked python scripts/check_symbolic_pilot.py --verify results/sr-white-001
uv run --locked python scripts/check_symbolic_pilot.py --verify results/sr-ar1-001
```

Der Prüfbefehl kontrolliert Datei-Prüfsummen, gemeinsame Arrays, Bäume,
Residuen und Auswahl. Er rechnet sämtliche Kandidatenverluste mit direkter
Matrixlösung nach. Die wahre Quadratik wird zusätzlich über die
Weißrauschformel beziehungsweise stationäre AR(1)-Innovationen geprüft.
Trainingsmatrix, Schrumpfung, Hintergrund-Kontroll-Scores und Herkunftserhalt
werden ebenfalls geprüft. Für Bäume wird derselbe Python-Interpreter wie
im Adapter verwendet; die unabhängige Verlustprüfung betrifft die direkte
Matrix-/Innovationsrechnung, keinen zweiten AST-Interpreter.

Der Kovarianzvergleich wird durch `s = max(abs(C_reference))` normiert.
Die Referenz entsteht unabhängig aus den gespeicherten Trainingsfenstern
und Alpha. Für eine positiv semidefinite Kovarianz entspricht `s` der
größten Varianz; die geprüfte Referenz muss eine endliche positive Skala
besitzen. Beide Matrizen werden vor dem Vergleich durch `s` geteilt.
`rtol=1e-12, atol=1e-15` gelten damit in normierten Einheiten: Der absolute
Anteil entspricht `1e-15*s` in Amplitudenquadrat, ohne feste Untergrenze.
Der relative Anteil toleriert Rundungsunterschiede der unabhängigen
Matrixprodukte; der normierte absolute Anteil betrifft verschwindende
oder sehr kleine Kopplungseinträge. Das ist keine allgemeine numerische
Fehlergarantie für beliebige Eingaben. Regressionsfälle führen den gesamten
Audit mit weißem und AR(1)-Rauschen bei `(A, sigma)=(1, 0.1)` und
`(1e-21, 1e-22)` aus: Korrekte Matrizen bestehen, nach der Schätzung
verdoppelte Matrizen müssen jeweils scheitern. Nur die teure Suche wird
dabei durch kontrollierte Kandidaten ersetzt.

Beide vollständigen Beispiele mit unveränderten Konfigurationen starten:

```bash
uv run --locked python scripts/check_symbolic_pilot.py --full --output results/sr-controls-001
```

Ohne `--full` gilt das ausdrücklich reduzierte CI-Profil: 32 Samples,
16/20/24 Hintergrundfenster, eine Iteration, eine Population mit 16
Mitgliedern und zwei Zyklen. Die verwendeten Konfigurationen werden
gespeichert. Dieser Check verlangt keine bestimmte Formel oder Güte.
GitHub prüft beide Fälle zusätzlich zu Adapter-, Newton-/BFGS- und
Verlustkerntests.

Die Python-Integrationstests ersetzen ausschließlich die teure Suche durch
einen kontrollierten Export. Datenerzeugung, Schätzung, klassische Fits,
Eltern-Replay, Auswahlprüfung und Diagnosen laufen echt. Gegenproben
prüfen veränderte Artefakte, Fehler, Abbrüche und unveränderte Auswahl bei
geänderter nachgelagerter Signalwahrheit. Echte PySR-Suchen laufen separat.
Diese Prüfungen belegen keine wissenschaftliche Rekonstruktionsleistung.
Auf Manjaro und WSL2 wurden jeweils 559 bestandene Tests, beide vollständigen
Audits und Diagrammanzeigen am Referenzcommit `6ed493d` übermittelt.
Zusätzliche Metadatenprüfungen bestätigen den sauberen Codezustand der
Elternpipeline, Referenzstufe und aller Sucharme. Die SR-Kandidatenzahlen
und Verluste unterscheiden sich zwischen den Rechnern. Die Ursache ist
noch nicht bestimmt; die lokalen Audits belegen keine identischen
Suchergebnisse über Rechner hinweg. Details und Grenzen stehen im
[Portabilitätsprotokoll](portability.md).
