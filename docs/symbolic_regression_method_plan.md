# Methodenentwurf: freie PySR-Suche mit fester Kovarianz

Stand: 20.10.2026. **Vorschlag für das methodische Review, noch keine
Implementierungsfreigabe oder wissenschaftliche Leistungsvalidierung.**
Alle neuen Such- und Auswahlvorgaben dieses Dokuments sind Vorschläge für
einen begrenzten technischen Pilot. Sie legen weder die Hauptversuche noch
deren Erfolgskriterien fest. Änderungen an Forschungsentscheidungen werden
nach dem Review ausdrücklich dokumentiert.

## 1. Ausgangspunkt und Ziel

Die [Schema-2-Pipeline](estimated_covariance_pilot.md) erzeugt Messdaten,
trennt drei Hintergrundrollen, schätzt einmalig eine Kovarianz und führt
drei klassische Fits mit bekannter Ringdown-Form aus. Schätzer und
Integration wurden separat geprüft; die Seed-Nachbesserung ist auf `main`.
Der [Manjaro-Nachweis](portability.md) gilt für Commit
`1fcf9fce5b999c2344b038c0a171b60ffaf7ae73`; sein WSL2-Gegenstück fehlt.

Die nächste Erweiterung soll Ausdrücke aus Operatoren und freien Konstanten
suchen, statt die vollständige Ringdown-Form vorzugeben. PySR und sein
evolutionäres Julia-Backend sind hierfür bereits installiert [1]. Es wird
kein vortrainiertes neuronales Netz benötigt. Für den ersten technischen
Adapter sind CPU-Ausführung und die vorhandenen Abhängigkeiten vorgesehen.

Zunächst soll die korrekte Übergabe der vollen Kovarianz an Suche,
Konstantenoptimierung und Export nachgewiesen werden. Ein kurzer Suchlauf
muss dafür nicht die wahre Ringdown-Form entdecken. Kleine Trainingsfehler
beweisen weder Formelidentifikation noch Überlegenheit oder Generalisierung.

## 2. Datenrollen und Vergleichsbedingungen

Die Rollen von Schema 2 bleiben erhalten:

| Rolle | Zulässiger Einfluss |
| --- | --- |
| Hintergrundtraining | Bestimmt `S`, `mu` und die Schrumpfungskandidaten |
| Hintergrundvalidierung | Wählt Alpha; danach bleibt `C_hat` fest |
| Hintergrundkontrolle | Nachgelagerte Kovarianzdiagnose; keine Such- oder Formelauswahl |
| Messdaten `t, y` | Eingaben der Formelsuche und Konstantenanpassung |
| Sauberes Signal und wahre Parameter | Ausschließlich nachgelagerte Diagnose |
| Analytisches `C_true` | Gewichtung des ausdrücklich privilegierten Kontrollarms und gemeinsame nachgelagerte Quadratik |

Auch die bisherigen Annahmen gleicher Rauschverteilung und Abtastung sowie
die Prüfung der vier NumPy-Anfangszustände gelten weiter. Die zusätzliche
Suchzufälligkeit wird getrennt protokolliert; sie erzeugt keine neuen
Hintergrunddaten und verändert deren Generatoren nicht.

Vorgeschlagen sind drei SR-Arme: gewöhnliche MSE, `C_true` und `C_hat`.
Sie erhalten dieselben Messdaten, Operatoren, Komplexitätsgrenzen,
Suchseed und nominellen Suchbudgets. Jeder Arm startet frisch; keine
Population oder gefundene Formel wandert zwischen den Armen.
Gleiche Seeds garantieren bei unterschiedlichen Zielfunktionen keine
identischen nachfolgenden Suchkandidaten.

Die klassischen Fits bleiben eine zusätzliche Referenz mit privilegiert
bekannter Funktionsform. Ihre Frequenz-/Abklingzeitgrenzen und Startpunkte
gehen nicht automatisch in die freie Suche ein. Gleiche Rechenbudgets
zwischen klassischem Fit und SR werden damit nicht behauptet.

Die angepassten Samples bleiben Entwicklungsdaten. Für spätere Auswahl von
Grammatik, Komplexitätsgewicht oder einer endgültigen Formel ist ein eigener
Versuchsplan mit unabhängigen Signal-/Rauschrealisierungen erforderlich.
Die Hintergrundkontrolle ist dafür kein Ersatz. Ein zufälliger Split der
zeitlich korrelierten Samples schafft keine unabhängigen Fenster. Nach
wiederholter Einsicht ist auch eine Kontrollmenge keine unangetastete
Abschlussbewertung mehr.

## 3. Zielfunktion und vollständiges Whitening

Für jeden Kandidaten `h` und jeden festgelegten Arm gilt in unveränderter
Sample-Reihenfolge:

```text
r = y - h(t)
ordinary:       ell = ||r||_2^2 / N
weighted:      C = L @ L.T, L unteres Dreieck
               L @ z = r
               ell = ||z||_2^2 / N = Q / N
```

Vorschlag für diesen Adapter ist ausdrücklich `Q/N`, passend zu den
vorhandenen Diagnosen. Beide gewichteten Arme verwenden ihre jeweilige
Matrix über die gesamte Suche, einschließlich Konstantenoptimierung.
Es gibt keinen Refit aus aktuellen Residuen, Jitter oder Pseudoinverse.
Der Cholesky-Faktor wird einmal pro Arm berechnet und als eigene, während
der Suche unveränderte Kopie gehalten. Eine volle Inverse wird nicht gebildet.
Für Normen wird wie im Python-Rechenkern vor dem Quadrieren durch `sqrt(N)`
geteilt und ein gegen Zwischenüberlauf geschützter Normalgorithmus verwendet.

PySR erhält weiterhin die ursprünglichen Zeitpunkte. `L^-1 @ h(t)` ist im
Allgemeinen nicht `h(L^-1 @ t)`; ein Whitening der Zeitmerkmale würde eine
andere Modellklasse erzeugen. Auch `||solve(C,r)||^2` wäre falsch, weil es
`C^-2` statt `C^-1` verwendet. Punktweise skalare Gewichte können die
Nebendiagonalen einer vollen Matrix nicht abbilden.

Für festes `C` ist `log(det(C))` für alle Formelkandidaten konstant. Deshalb
gehört dieser Term nicht in die vorgeschlagene SR-Verlustfunktion. Bei der
Auswahl unterschiedlicher Kovarianzen bleibt der vollständige Gauß-Score
des bestehenden Schätzers einschließlich Logdeterminante erforderlich.
`Q_used/N` verschiedener Matrizen ist kein gemeinsamer Leistungsmaßstab.
Die gewöhnliche MSE trägt quadrierte Amplitudeneinheiten, die mit einer
physikalisch skalierten Kovarianz gebildete Quadratik ist dimensionslos.

## 4. PySR-Schnittstelle und Kontextisolation

Maßgeblich sind die festgelegten Versionen **PySR 2.6.0,
SymbolicRegression 2.5.1, Julia 1.13.1 und PythonCall 0.9.36**.
Die folgenden Schnittstellen wurden im versionsgebundenen Quellcode geprüft,
nicht durch einen neuen Julia-Lauf bestätigt [2–5].

`loss_function` erlaubt eine vollständige Julia-Zielfunktion mit
Baumauswertung und Zugriff auf den gesamten Datensatz [2, 3].
`elementwise_loss` oder das normale `weights`-Argument allein reichen für
volle Kovarianz nicht aus. Vorgeschlagen ist ein eigener vollständiger
Callback für jeden der drei Arme; auch der gewöhnliche Arm durchläuft
dieselben Eingabe-, Einheiten- und Exportprüfungen.

Vertrag des späteren Callbacks:

1. Prüfen, dass genau das vollständige Fenster in vereinbarter Reihenfolge
   vorliegt. `batching=False` wird ausdrücklich gesetzt; kein automatisches
   Batching, Denoising, Feature-Selecting oder Umsortieren der Samples.
2. Dimensionsprüfung aus Abschnitt 6 auf dem unveränderten Baum ausführen.
3. Den Baum an allen ursprünglichen Zeitpunkten auswerten; eine unvollständige,
   komplexe oder nicht endliche Vorhersage macht den Kandidaten unzulässig.
4. Das vollständige Residuum bilden, gegebenenfalls das untere Dreieckssystem
   lösen und den endlichen, nicht negativen Verlust pro Sample zurückgeben.

Ein für diesen Kandidaten undefinierter Ausdruck, etwa Division durch null
oder Exponentialüberlauf, erhält `Inf`. Fehlerhafte Eingaben, eine ungültige
Kovarianz oder ein falscher Callback-Vertrag werden dagegen als Fehler
gemeldet; sie dürfen nicht unbemerkt alle Kandidaten zu `Inf` machen.
Ausnahmen werden nicht pauschal verschluckt. Der exakte Verlust null bleibt
null; es wird kein Epsilon zur physikalischen Zielfunktion addiert.

Der Backend-Quellcode führt auch die Konstantenoptimierung über `eval_loss`
und damit über die eigene Zielfunktion [4]. Für den ersten Adapter wird
`autodiff_backend=None` vorgeschlagen. Damit ruft der Backend-Code den
Optimierer ohne eigene AD-Gradienten auf; die numerische Differentiation
muss für diesen Callback geprüft werden. Bei einer einzigen Konstanten
wählt das Backend Newton, auch wenn `optimizer_algorithm="BFGS"` eingestellt
ist [4]. Die Beschriftung „immer BFGS“ wäre deshalb falsch.

Vorschlag zur Isolation: jeder SR-Arm läuft in einem neuen Python-/Julia-
Unterprozess über `scripts/run_python.py` und die gesperrte Julia-Umgebung.
Der Prozess erhält nur Zeitachse, Messdaten, seine optionale Kovarianz und
Suchvorgaben, nicht Signalwahrheit oder Hintergrundkontrolle. Es gibt
keinen zwischen Armen überschriebenen globalen Faktor. Das genaue Binden
des Julia-Callbacks und die Datenübergabe sind Implementierungsaufgaben;
sie müssen vor dem ersten Ringdown-Suchlauf mit kleinen Referenzen bestehen.

## 5. Verlustskalierung, Suchdruck und Formelauswahl

Bei festem `N` besitzen `Q` und `Q/N` dieselben reinen Minima. Bei einer
ausdrücklichen additiven Komplexitätsstrafe sind dagegen nur

```text
Q + lambda_raw * K
Q/N + (lambda_raw/N) * K
```

proportional. Bei `C -> c*C` mit `c>0` sinkt die Quadratik um den Faktor
`c`; das Gewicht einer solchen Strafe muss entsprechend angepasst werden.
Bei einer gemeinsamen Einheitenänderung `r -> a*r`, `C -> a^2*C` bleibt
die Quadratik unverändert. Dies rechtfertigt keine datenabhängige
Amplitudennormierung oder SNR-Definition ohne eigenen Methodenbeschluss.

**PySR-`parsimony` ist nicht unmittelbar dieses `lambda`.** Backend 2.5.1
bildet den internen Kandidaten-Cost als `ell / normalization + parsimony*K`.
`normalization` ist die verwendbare Baseline, falls sie mindestens `0.01`
beträgt, sonst `0.01` [3]. Zusätzlich können Häufigkeitsmechanismen den
Suchdruck verändern. Daher garantiert eine gemeinsame Skalierung von
Verlusten auch bei gleichen reinen Minima keinen identischen Suchverlauf.
Die effektive Baseline und Normalisierung gehören in den Export.

Vorschlag für den ersten technischen Adapter: `parsimony=0`,
`use_frequency=False` und `use_frequency_in_tournament=False`, ein
ausdrückliches Größenlimit und Export der gefundenen nicht dominierten
Kandidaten. Das schaltet die genannten Komplexitätsgewichte ab, macht die
evolutionäre Suche aber nicht zu einer unbeschränkten Optimierung.
Knotenlimit, Mutationen, Vereinfachung und Budgets prägen sie weiterhin.
Eine spätere wissenschaftliche Komplexitätsstrafe bleibt offen.

PySRs `model_selection="best"` ist keine neutrale Voreinstellung: Die
Python-Auswahl verwendet einen Faktor `1.5` zum kleinsten Verlust und
danach den Score [2]. Für eine ausdrücklich als solche bezeichnete
technische Beispielkurve wird stattdessen `model_selection="accuracy"`
vorgeschlagen: kleinster Trainingsverlust, keine unabhängige Modellauswahl.
`loss_scale="log"` bleibt explizit, passend zu nicht negativen Verlusten.
Der bibliothekseigene Score ist weder unser Verlust noch ein nachgewiesenes
wissenschaftliches Auswahlkriterium. Nullverluste und Gleichstände werden
gesondert geprüft und nachvollziehbar gekennzeichnet.

Der Export enthält die von der Suche gefundenen Pareto-Kandidaten nach
Komplexität und Trainingsverlust [5]. Diese Front ist nicht der vollständige
Raum aller möglichen Formeln. Eine Display-Auswahl verwirft die anderen
Kandidaten nicht. Keine Wahl anhand des sauberen Signals, wahrer Parameter
oder des nachgelagerten Kontroll-Scores.

## 6. Grammatik, Einheiten und Zeitvariable

Vorschlag für die erste Grammatik:

| Bestandteil | Vorschlag und Bedeutung |
| --- | --- |
| Eingabe | Eine Variable `t` in Sekunden; Ausgabe bisher dimensionslos |
| Binäre Operatoren | `+`, `-`, `*`, `/` |
| Unäre Operatoren | `exp`, `sin`, `cos` |
| Konstanten | Frei optimierte reelle `float64`-Werte; dimensionsbehaftete Konstanten zulässig |
| Komplexität `K` | Jeder Operator, jede Variablenverwendung und jede Konstante zählt 1 |
| Begrenzung | `maxsize=20`, `maxdepth=None`; keine zusätzlichen Argument- oder Verschachtelungsgrenzen |
| Vorwissen | Kein Ringdown-Template, keine wahre Formel als `guesses`, keine aus wahren Parametern gebildeten Merkmale |

Auch diese Operatorwahl ist Vorwissen. Mit dieser Zählung hat beispielsweise
`A*exp(b*t)*cos(c*t+d)` 13 Knoten. Der Suchraum enthält damit die Zielstruktur,
erzwingt aber weder ihre Entdeckung noch physikalisch sinnvolle Parameter.
`b` und `c` haben die Einheit `1/s`, `A` und `d` sind dimensionslos.
Nur falls ein gefundener Ausdruck tatsächlich in eine entsprechende
Form überführt und identifiziert wurde, dürfen etwa `tau=-1/b` für `b<0`
oder `f=abs(c)/(2*pi)` berichtet werden. Allgemeine Ausdrücke haben keine
automatisch definierten Ringdown-Parameter.

Vorschlag: zunächst physikalische Sekunden mit `X_units=["s"]` und einer
ausdrücklich dimensionslosen Ausgabe (`y_units="1"`) übergeben;
`dimensionless_constants_only=False`, damit inverse Zeitkonstanten möglich
sind [2, 6]. Die konkrete Akzeptanz dieser Einheitendarstellung wird vorab
im gepinnten Backend getestet. Eine Skalierung `u=t/t_ref` ist eine mögliche
spätere Alternative bei numerischen Problemen. Sie erfordert einen aus
Abtastung oder Konfiguration begründeten, protokollierten Referenzwert und
eine explizite Rücktransformation; `t_ref` darf nicht aus der Signalwahrheit
gewählt werden. Dimensionslose Merkmale verlieren außerdem einen Teil der
Prüfwirkung einer physikalischen Einheitenanalyse.

**Eine eigene vollständige Verlustfunktion umgeht in Backend 2.5.1 die
automatische Dimensionsregularisierung.** Diese liegt nur im Standardpfad
`_eval_loss` [3]. Der Callback muss deshalb den versionsgebundenen Prüfer
`violates_dimensional_constraints` ausdrücklich aufrufen und unzulässige
Bäume mit `Inf` ausschließen; allein `dimensional_constraint_penalty`
einzustellen genügt nicht. Derselbe Check gilt auch bei der
Konstantenoptimierung und beim Reimport exportierter Kandidaten.
Ein Zugriff auf dieses interne Backend-Modul ist eine versionsabhängige
Schnittstelle und wird durch einen gezielten Integrationstest abgesichert.

Die Backend-Prüfung arbeitet mit möglichen Einheiten freier Konstanten
und ist keine vollständige physikalische Identifikation [6]. Eine Formel
mit zulässigen Dimensionen kann wissenschaftlich falsch sein. Beispiele
für die Prüfung sind `exp(b*t)` mit inverser Zeitkonstante gegenüber
`exp(t)` sowie `h(t)=t` bei dimensionslos geforderter Ausgabe. Beim Export
wird zwischen zulässiger Dimensionsprüfung und einer tatsächlich
rekonstruierten Zuordnung der Konstanteneinheiten unterschieden.

## 7. Konkreter Vorschlag für einen technischen Suchlauf

Diese kleinen Vorgaben sollen zunächst Laufzeit, Adapter und Exporte
prüfen. Sie begründen keine ausreichende Suchintensität für die Forschung.

| Einstellung | Vorgeschlagener Wert |
| --- | --- |
| Basisfälle | Bestehende weiße und AR(1)-Schema-2-Daten; jeweils drei SR-Arme |
| Numerik | `precision=64`, `turbo=False`, `bumper=False` |
| Zufall und Parallelität | `random_state=20261020`, `deterministic=True`, `parallelism="serial"` |
| Populationen | `populations=2`, `population_size=32` |
| Suchbudget | `niterations=10`, `ncycles_per_iteration=50` |
| Konstantenoptimierung | `optimizer_algorithm="BFGS"`, `optimizer_iterations=20`, `optimizer_nrestarts=2`, `autodiff_backend=None`; Ein-Konstanten-Sonderfall aus Abschnitt 4 |
| Frischer Start | `warm_start=False`, `guesses=None` |
| Datenbehandlung | `batching=False`, `denoise=False`, `select_k_features=None` |
| Zusätzliche Abbrüche | `early_stop_condition=None`, `timeout_in_seconds=None`, `max_evals=None` |
| Komplexität und Auswahl | Explizit die Vorschläge aus Abschnitten 5 und 6 |

Die Kombination aus festem Seed, deterministischer Einstellung und serieller
Suche erfüllt die entsprechende PySR-Vorgabe [2]. Sie garantiert keine
Bitidentität über Rechner, Julia-/BLAS-Builds oder geänderte Versionen.
Eine verfügbare Laufzeitgrenze darf später nicht stillschweigend das
Vergleichsbudget ersetzen. Abbruch oder Prozessfehler werden als solcher
gespeichert, nicht als bestandener vollständiger Vergleich.

Gleiche Iterationsvorgaben bedeuten weder gleiche Zahl tatsächlicher
Verlustaufrufe noch gleiche Laufzeit. Zu protokollieren sind effektive
Optionen, verfügbare Evaluationszähler und getrennt die Laufzeiten von
Prozessstart/Vorkompilierung und Suche. Eine Behauptung gleicher
Rechenkosten erfordert zusätzliche Festlegungen. Nicht explizit geänderte
Bibliotheksvorgaben werden über vollständige effektive Optionen und
Versionsbindung nachvollziehbar, statt als Forschungsauswahl ausgegeben.

## 8. Unabhängige Referenzen und Abnahmekriterien

Die Implementierung soll zunächst deterministische Kern- und Adaptertests
erhalten. Ein zufälliger Suchtreffer ersetzt keinen dieser Nachweise.

| Fall | Unabhängig erwartetes Ergebnis und erkannter Fehler |
| --- | --- |
| Orientierung | `C=[[5/2,3/2],[3/2,9/2]]`, `r=[1,0]`: `det(C)=9`, `Q=1/2`, `Q/N=1/4`; falsches `L^-T` liefert `Q=2/5` |
| Volle Kopplung | `C=[[2,1],[1,2]]`, `r=[1,1]` bzw. `[1,-1]`: beide MSE 1, aber `Q/N=1/3` bzw. 1; diagonale Gewichte reichen nicht |
| Konstantenanpassung | `h(t)=theta`, `y=[1,3]`, `C=[[4,2],[2,10]]`: `theta=(1.T C^-1 y)/(1.T C^-1 1)=7/5`; gewöhnliches Mittel ist 2. Der tatsächlich verwendete Konstantenoptimierer muss das gewichtete Minimum liefern |
| Zeitachse | `L=[[1,0],[1,1]]`, `t=[0,1]`, `h=exp`: `L^-1 h(t)=[1,e-1]`, aber `h(L^-1 t)=[1,e]`; Zeit-Whitening ist ein anderer Ansatz |
| Identität und Skalierung | `C=I` reproduziert gewöhnliche MSE; gemeinsame Skalierung `r->a*r`, `C->a^2*C` erhält den Verlust, einschließlich `a=1e-21` |
| Vorzeitiger Überlauf | Ein noch darstellbarer Mittelwert großer Quadrate darf nicht durch eine vorher überlaufende Quadratsumme unzulässig werden; Normierung wie im Python-Referenzkern |
| Einheiten im Custom Loss | Zulässige und unzulässige Bäume aus Abschnitt 6 auch während Konstantenanpassung unterscheiden; ein gesetzter Einheitenparameter allein ist kein Prüfnachweis |
| Kandidatenfehler | Ungültige Division, Überlauf, falsche Länge und nicht endliche Ausgabe: Kandidatenfehler und Eingabefehler gemäß Abschnitt 4 unterscheiden; keine stillen Ersatzdaten |
| Exakter Treffer | Verlust null bleibt null; Auswahl, Score-Diagnose und Export bleiben verwendbar |
| Kontexttrennung | Mit unveränderten Eingaben Arm A, Arm B mit anderer Kovarianz und erneut A ausführen: A behält seinen eigenen Faktor; kein Cache- oder Warm-Start-Übertrag |
| Vollständiges Fenster | Nebendiagonalreferenz auch durch die echte PySR-Schnittstelle prüfen; Callback sieht alle N Samples in richtiger Reihenfolge, auch bei Optimierung |
| Export und Auswahl | Vorgegebene Kandidaten mit unterschiedlichen Komplexitäten/Verlusten prüfen Auswahl und Pareto-Export; ein späterer Kandidat muss einen früheren verdrängen können |

Für kleine Matrizen werden die exakten rationalen Werte und direkte
Gleichungslösungen als Referenz verwendet, nicht nur der produktive
Whitening-Pfad. Vergleichstoleranzen berücksichtigen Maschinenpräzision,
Matrixkondition und Algorithmus; bei Optimierer-Konvergenz zusätzlich
dokumentierte Abbruchtoleranzen. Sie werden vor der Prüfung festgelegt.
Exakt symbolisch nachgerechnete Werte bestätigen die Referenzen, noch
nicht den künftigen Julia-Adapter.

Ein kurzer stochastischer Integrationstest darf anschließend endliche
Kandidaten, vollständige Artefakte und den Replay ihrer Verluste prüfen.
Die Entdeckung der wahren Ringdown-Form innerhalb des winzigen Budgets ist
kein technisches Abnahmekriterium. Für eine Leistungsstudie fehlen noch
Mehrfachstarts, Parameter-/Rauschbereiche und vorab begründete Erfolgsmaße.

## 9. Ausgaben und gestufte Umsetzung nach dem Review

Die bestehenden Schema-1-/Schema-2-Ergebnisse bleiben interpretierbar.
Für SR wird vor der Integration ein ausdrücklich versioniertes neues
Konfigurations- und Ergebnisformat vorgeschlagen, statt die Bedeutung
vorhandener Fit-Felder stillschweigend zu ändern.

Zusätzlich zu Eingaben, Kovarianzen und bisherigen Provenienzdaten braucht
ein SR-Lauf pro Arm mindestens:

- Status, effektive Optionen, Suchseed und gegebenenfalls verfügbare
  Julia-RNG-Zustände; keine Behauptung vollständiger Zustandsrekonstruktion
  allein aus einem Python-Seed.
- Gefundene Pareto-Kandidaten mit Komplexität, rohem Trainingsverlust,
  Baseline/Normalisierung und ausdrücklich benanntem Bibliotheks-Score.
- Reproduzierbare Baumbeschreibung mit Operatoren, Variablen und Konstanten
  in voller `float64`-Genauigkeit sowie lesbare Formel und Einheitenstatus.
  Eine verkürzte Terminalformel reicht nicht zum Wiederherstellen.
- Vorhersagen/Residuen der technischen Beispielkurve und Replay ihrer
  Verluste in Python und Julia; eine SymPy-Vereinfachung ersetzt nicht die
  ursprüngliche numerische Auswertungsreihenfolge.
- Gemeinsame nachgelagerte Diagnosen wie gewöhnliche MSE, Fehler zur
  Signalwahrheit und `Q_true/N`, weiterhin `fitted_samples_only`.

Alle genutzten Eingaben, Optionen, Callback-Quellen und Ergebnisse werden
wie bisher mit Prüfsummen und Versionen dokumentiert. Ausgabeordner bleiben
exklusiv; Teilergebnisse und Prozessfehler werden erhalten. Ein einzelner
erfolgreicher Arm macht einen unvollständigen Vergleich nicht erfolgreich.

Vorgeschlagene Reihenfolge nach dem methodischen Review:

1. Julia-Verlustkern und Einheitenprüfung isoliert gegen Abschnitt 8 prüfen.
2. Gepinnte PySR-Schnittstelle, Kontextisolation und echte
   Konstantenoptimierung mit kleinen deterministischen Fällen prüfen.
3. Versionierte Konfiguration und Exporte an vorhandene Daten anschließen;
   die kleinen weißen/AR(1)-Kontrollläufe ausführen und unabhängig nachrechnen.
4. Code-/Wissenschaftsreview und danach neue Manjaro-/WSL2-Kontrollen;
   die bestehende offene WSL2-Prüfung von Schema 2 bleibt separat vermerkt.

## 10. Konkreter Auftrag an das methodische Review

| Entscheidung / Risiko | Zu prüfen oder ausdrücklich zu entscheiden |
| --- | --- |
| Verlust und Vergleich | `Q/N` für diesen Adapter; kein Logdet im Formelsuchverlust bei festem C; getrennte Diagnosen der drei Arme |
| Komplexität | Technisch zunächst keine zusätzliche Strafe, Knotenlimit und gesamte gefundene Front; spätere wissenschaftliche Auswahlregel bleibt offen |
| Suchraum | Vorgeschlagene Operatoren, Knotenmaß und Limit 20; Zielstruktur darstellbar, keine versteckte Vorgabe der vollständigen Formel |
| Einheiten / Zeit | Sekunden und dimensionsbehaftete Konstanten zunächst beibehalten? Expliziter Prüfer im Custom Loss; Grenzen der Wildcard-Einheitenanalyse |
| Optimierung | Tatsächlicher Custom-Loss-Pfad einschließlich Newton-Sonderfall, numerischer Differentiation und unzulässiger Kandidaten |
| Datenrollen | Keine Auswahl anhand von Wahrheit oder Hintergrundkontrolle; unabhängige spätere Signalbewertung gesondert planen |
| Vergleichsbudget | Technischer Vorschlag aus Abschnitt 7; Hauptversuchsbudgets und Zahl unabhängiger Suchstarts noch nicht begründet |
| Schnittstelle / Export | Prozessisolation, vollständige Reihenfolge, voller Faktor, Präzision, Replay und Fehlerstatus ausreichend abgesichert? |

Das Review soll zunächst diese Vorschläge und Gegenbeispiele beurteilen.
Es soll keine nicht durchgeführte PySR-Integration oder Leistungsstudie
bestätigen. Endgültige SNR-Konvention, Datenbudgets, Generalisierung,
Identifikationskriterien und statistische Vergleiche gehören in einen
anschließenden Versuchsplan.

## Quellen und Prüfumfang dieses Entwurfs

[1] Miles Cranmer (2023): *Interpretable Machine Learning for Science with
PySR and SymbolicRegression.jl*, [arXiv:2305.01582v3](https://arxiv.org/abs/2305.01582v3).
Einordnung des Verfahrens; kein Beleg für unsere konkrete Gewichtung.

[2] [PySR 2.6.0: `pysr/sr.py`](https://github.com/astroautomata/PySR/blob/v2.6.0/pysr/sr.py),
insbesondere Parameter, `_run`, `fit` und `idx_model_selection`.
Die installierte Python-Quelle wurde ohne Initialisierung von Julia gelesen.

[3] [SymbolicRegression 2.5.1: `src/LossFunctions.jl`](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/LossFunctions.jl),
insbesondere `eval_loss`, `_eval_loss`, `loss_to_cost` und
`dimensional_regularization`.

[4] [SymbolicRegression 2.5.1: `src/ConstantOptimization.jl`](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/ConstantOptimization.jl),
insbesondere `optimize_constants`, `EvaluatorContext` und `Evaluator`.

[5] [SymbolicRegression 2.5.1: `src/HallOfFame.jl`](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/HallOfFame.jl),
insbesondere `calculate_pareto_frontier` und `format_hall_of_fame`.

[6] [SymbolicRegression 2.5.1: `src/DimensionalAnalysis.jl`](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/DimensionalAnalysis.jl),
insbesondere `violates_dimensional_constraints` und `WildcardQuantity`.

Für diesen Dokumentationsentwurf wurden Quellen und handrechenbare
Referenzen geprüft. Es wurden keine SR-Suchläufe, Julia-Adaptertests oder
neuen statistischen Experimente durchgeführt. Der vorhandene
Manjaro-Prüfnachweis betrifft Schema 2 mit klassischen Fits.
