# Dreiarm-Pilot mit freier symbolischer Regression

Schema-3-Stand: 22.10.2026. Schema 3 verbindet die bestehende
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
separates Modul umgesetzt. Die ebenfalls separate
[Parameter-/Aliasdiagnose](parameter_diagnostics.md) ergänzt Umrechnung
und numerische Nachrechnung. Ihr [lesender Export](parameter_export.md) ist separat umgesetzt;
die bisherigen Pilotdateien bleiben unverändert.

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

## Bestätigtes R-Profil im allgemeinen Laufweg: Schema 4

Beschluss vom 14.11.2026, [Leitfadenphase 5](ringdown_recovery_roadmap.md).
Die [rauschfreie Bestätigung](restart_budget_confirmation_results_manjaro_001.md)
begründet die bewusste Übernahme des R-Profils in den allgemeinen Laufweg.
Sie validiert weder Gewichtungsvergleiche unter Rauschen noch den gesamten
Parameterkasten. Die folgenden Vorgaben betreffen die technische Übernahme;
ein wissenschaftliches Rauschpilotprotokoll ist noch gesondert festzulegen.

### Auftrag und unveränderte Auswahlgrenzen

Schema 4 verwendet die bestehende Schema-2-Datengenerierung mit demselben
binären Eingabeübergang. Es ersetzt die einzelne Schema-3-Suche je Arm durch
vier vollständig neue Worker. Die Schema-1–3-Aufträge, Formate und Defaults
bleiben unverändert. Der neue Auftrag enthält anstelle von `[symbolic_search]`:

```toml
[confirmed_search]
profile = "r4x1000-local300x5-v1"
seeds = [2026111401, 2026111402, 2026111403, 2026111404]
```

Die vier unterschiedlichen Seeds werden vor Beginn gespeichert; derselbe
Block gilt für die drei getrennten Gewichtungsarme. Die Beispielseeds
definieren keine wissenschaftliche Bestätigungsstichprobe. Das Profil legt
1.000 äußere Iterationen, 300 lokale Optimiereriterationen und fünf zusätzliche
lokale Neustarts fest. Vier globale Neustarts sind vier neue SR-Suchen.
Beide Häufigkeitsschalter sind eingeschaltet; allgemeine Grammatik,
`should_simplify=false`, kein Größen-Warmup, ursprüngliches t und die übrigen
gebundenen Einstellungen gelten gemeinsam.

Innerhalb jedes Workers bleibt die native Originalauswahl erhalten.
Das Paket wählt unter diesen vier Originalausgaben nach tatsächlichem
Trainingsverlust, danach Komplexität und schließlich Mitgliedsposition.
Ein Paket liefert genau eine Ausgabe. Keine Auswahl nach Signalwahrheit,
Kurvenklasse, Familie oder zusätzlichen Diagnosepunkten; kein Vergleich
roher Trainingsverluste zwischen unterschiedlichen Gewichtungen.

Alle geplanten Mitglieder einschließlich zulässiger numerischer Ausfälle
und Zeitüberschreitungen bleiben im Paket und in den Kosten. Fehlende
Kostenbelege bedeuten unbekannte Kosten. Unterbrechungen, Herkunftswidersprüche,
Aufrufwächterfehler und unbekannte Fehler verhindern die Freigabe. Ein
Timeout darf einen bereits aufgezeichneten Integritätsfehler nicht verdecken.
Die lesende Prüfung muss dieselben Grenzen wie die Ausführung anwenden.

Die Betriebsgrenzen betragen 1.800 Sekunden je Worker und 7.800 Sekunden
je vollständigem Paket einschließlich Vorbereitung und Abschluss. Sie sind
keine wissenschaftlichen Erfolgsschwellen und keine Laufzeitvorhersage.
Der reduzierte technische Paketcheck erhält 1.200 Sekunden; die reine
Paketverifikation 600 Sekunden. Eine späte Überschreitung darf keine
veröffentlichte Freigabe bestehen lassen.

### Gewichtung und technische Abnahme

Die feste vollständige Kovarianz bleibt im nativen `FixedWindowLoss` gebunden:
für die Bewertung von Strukturen und für sämtliche Konstantenoptimierungen.
Die drei Arme verwenden gewöhnliche MSE, wahres `Q/N` beziehungsweise
geschätztes `Q/N`. Keine Diagonalisierung, Residuenanpassung der Kovarianz oder
nachträgliche Gewichtung erst bei der Paketwahl.

Der historische MSE-Replay des Spezialtreibers ist für Kovarianzverlust
nicht definiert. Im neuen Profil werden deshalb Baumvorhersage und
Residuenreduktion getrennt geprüft. Nahezu exakte Formeln dürfen nicht allein
wegen kleiner zulässiger Vorhersagerundungen im Python-Replay scheitern;
eine pauschale absolute Verlusttoleranz wäre dafür kein ausreichender Nachweis.
Der gewichtete Vertrag prüft die tatsächlich verwendeten nativen und
Python-Choleskyfaktoren über den Rückwärtsfehler `L Lᵀ − C` gegen die originale
Matrix. Jede Weißung wird gegen ihren eigenen Residualvektor über `L z − r`
geprüft; anschließend wird die Reduktion `Σ z²/N` exakt rational nachgerechnet.
Auch die zur Prüfung berechneten Matrixprodukte und Schranken benötigen
Rundungsfehlerhüllen. Die Baumvorhersagen werden separat durch den bestehenden
MPFR-Intervallnachweis gebunden. Native Front-, Reimport- und Tabellenverluste
behalten ihren strikten relativen Abgleich; die Paketwahl verwendet weiterhin
den unveränderten nativen Trainingsverlust.

Für `u=2^-53` und `γ_k=k·u/(1−k·u)` schließt die Nachrechnung den Fehler eines
Skalarprodukts mit `N` Summanden durch `γ_N·|A|·|B| + α_N` ein. Dabei ist
`α_N=N·2^-1075/(1−N·u)` der aus IEEE-Rundung abgeleitete Anteil für allmählichen
Unterlauf. Gerichtete Float64-Schranken um Produkt, Betrag, Subtraktion und
Schrankenrechnung müssen den tatsächlichen Rückwärtsfehler komponentenweise
unter `γ_(2N+2)·|A|·|B| + 2α_N` nachweisen. NumPy-/BLAS-Kontrollen prüfen, dass
subnormale Operanden und Produkte nicht einfach zu null gesetzt werden.
Der Maschinenunterlaufanteil verändert keine Kovarianzeinträge und ist keine
frei gewählte absolute Verlusttoleranz.

Für die anschließend exakt rational überprüfte Quadratsummenreduktion gilt
die bestehende `γ_(N+2)`-Grenze. Nichtverschwindende Quadrate müssen weiterhin
im normalen Float64-Bereich bleiben; Extremskalen können daher ausdrücklich
abgelehnt werden. Die Prüfung ändert weder Kovarianz noch native Auswahl.

Dies ist ein Nachweis kleiner Rückwärtsfehler des numerischen Rechenwegs.
Bei schlecht konditionierter Kovarianz folgt daraus keine enge Vorwärtsschranke
zum mathematisch exakten `rᵀ C⁻¹ r/N` und keine behauptete Übereinstimmung
beliebiger unabhängiger Implementierungen. Diese Grenze darf nicht als
bewiesene Genauigkeit verschleiert werden. Numerische Unter-/Überläufe und
nicht belegbare Schranken verhindern die Freigabe; keine neue Regularisierung,
feste absolute Fehlertoleranz oder stillschweigende Änderung der historischen
Verlustverträge.

Die begrenzte technische Prüfung verwendet saubere, fest gespeicherte
Beobachtungen mit separat gewählter positiv definiter Testkovarianz direkt
über dieselbe allgemeine Paket-API. Sie behauptet kein Rauschen in diesen
Daten und ändert nicht die positive Varianzvorgabe der Schema-2-Erzeugung.
Ein vollständiges kleines Viererpaket sowie gewöhnliche und diagonale
Kontrollen prüfen die neue Route. Analytische Referenzen müssen zeigen,
dass die Nebendiagonalen die Strukturrangfolge und das Konstantenoptimum
tatsächlich beeinflussen. Reduzierte äußere Budgets sind ausdrücklich als
technisch gekennzeichnet; lokal 300/5 und die übrigen Profileinstellungen
bleiben erhalten. Keine bestimmte gefundene Formel oder Kurvenklasse ist
ein technisches Bestehenskriterium.

Implementierung, konkrete Prüfbefehle und tatsächlich ausgeführte Nachweise
werden im [Fortsetzungsstand](representation_implementation_status.md)
nachgeführt. Originalarchive bleiben gemäß [Archivregel](results_archiving.md)
unverändert; technische Nachweise erhalten eigene Ausgaben und Prüfsummen.

### Begrenzter technischer Manjaro-Lauf

Erst nach vollständiger Abnahme des Implementierungsstands aus
[PR #89](https://github.com/craexxn/ringdown-sr/pull/89) starten. Die folgenden
Befehle holen dessen tatsächlichen Head in einen eigenen unveränderlichen
Checkout. Aus dem bisherigen Repository ausführen; vorhandene Arbeitsbäume
oder Ausgabeordner nicht überschreiben:

```bash
bash <<'BASH'
set -euo pipefail
git fetch origin refs/pull/89/head
task_commit=$(git rev-parse FETCH_HEAD)
git worktree add --detach ../ringdown-confirmed-profile-run "$task_commit"
cd ../ringdown-confirmed-profile-run
test -z "$(git status --porcelain)"
env -u VIRTUAL_ENV uv sync --locked --dev --python 3.12.14
git rev-parse HEAD
BASH
```

Danach im neuen Arbeitsbaum den **technischen** Vorlauf starten. Dieser führt
neun feste native Rang-/Optimiererreferenzen und sechs kleine Suchworker aus:
ein vollständiges Viererpaket mit voller Kovarianz, einen diagonalen und einen
ungewichteten Worker. Die Suchdaten sind der feste saubere Zweipunktfall
`t=[0,1]`, `y=[1,0]`; die volle Testkovarianz ist `[[2.5,1.5],[1.5,4.5]]`.
Jeder Suchworker erhält nur eine äußere Iteration bei ansonsten unverändertem
Profil einschließlich lokal 300/5. Das ist eine technische Funktionsprüfung,
keine wissenschaftliche Ringdown-Rekonstruktionsserie.

```bash
cd ../ringdown-confirmed-profile-run
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/check_confirmed_profile.py \
  --output results/confirmed-profile-technical-manjaro-001
```

Erwartete Dateien sind `analytic.json`, das Viererpaket unter `full/` mit
seinen vier `member-*/`-Ordnern, ursprünglichen Eingaben, Vorbereitung,
nativen Fronten, Herkunfts-/Kostenbelegen und freigegebenem `completion/`,
sowie die Einzelkontrollen `diagonal/` und `ordinary/`. Keine bestimmte
gefundene Formel ist Voraussetzung. Einrichtung und JIT gehören zum
technischen Aufwand; die Workerlogs können längere Zeit ohne neue Ausgabe
bleiben. Bei Abbruch bleiben Teilstände erhalten; für eine Wiederholung eine
neue Lauf-ID verwenden.

Nach erfolgreichem Abschluss im selben sauberen Ausführungscheckout separat
**lesend verifizieren und erst danach archivieren**:

```bash
bash <<'BASH'
set -euo pipefail
task_run=confirmed-profile-technical-manjaro-001
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/check_confirmed_profile.py \
  --verify "results/$task_run" | tee "results/$task_run-verification.log"
task_archive="$task_run.tar.gz"
test ! -e "results/$task_archive"
tar -czf "results/$task_archive" -C results \
  "$task_run" "$task_run-verification.log"
tar -tzf "results/$task_archive" > /dev/null
cd results
sha256sum "$task_archive" > "$task_archive.sha256"
sha256sum -c "$task_archive.sha256"
BASH
```

Originalarchiv und SHA-256 im gemeinsamen Archivordner sowie auf dem
unabhängigen Sicherungsziel erhalten; beide Kopien am Hash prüfen und den
bestätigten Ablage-/Sicherungsstand im [Ergebnisindex](results_index.md)
nachführen. GitHub-Uploads bleiben optional.

### Späterer Schema-4-Pilot und lesende Prüfung

[`configs/pilot_confirmed_ar1.toml`](../configs/pilot_confirmed_ar1.toml)
zeigt den allgemeinen Auftragsweg. Seine zwölf vollständigen 1.000er-Suchen
sind **kein freigegebener wissenschaftlicher Rauschversuch**. Signal-, Rausch-,
Hintergrund- und Seedblöcke, Endpunkte und Anschlussregel sind zuvor separat
festzulegen. Dieser Implementierungsschritt startet diesen Auftrag nicht.

Ein später tatsächlich vorhandener Schema-4-Lauf wird über
`uv run --locked ringdown-sr verify-confirmed AUSGABEORDNER` lesend geprüft.
Eine gültige Verifikation liefert Exitcode 0 auch dann, wenn dokumentierte
numerische Ausfälle den Pilotstatus `comparison_failed` ergeben. Der eigentliche
Lauf liefert dafür Exitcode 1; Integritätsfehler sperren die Freigabe. Der
Schema-3-Verifikator und die bisherigen Zusatzbewertungsexporte werden nicht
auf die neuen Mehrmitgliedsdateien umgedeutet. Neue physikalische
Parameterübereinstimmungen bleiben `not_assessed`.
