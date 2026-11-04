# Audit: zweiter Manjaro-Suchbudgetlauf

Stand: 03.11.2026. Originalarchiv `duration-manjaro-002.tar.gz`, SHA-256
`147d21ec13844f1500b41fa226c4f8d79a8da7558c65faea8f7a478540b70e14`,
sauberer Ausführungscommit `76a740018b4426bc1651a5fed3bf214659a083cf`
(übernommener PR #55). Kein neuer Fit und keine wissenschaftliche Suche im Audit.
Archivcode und serialisierte Julia-/Python-Zustände wurden nicht ausgeführt.

## Herkunft und Teilstand

143 Dateien, alle 96 ursprünglichen Dateianker und 68 gebundenen Quellen
gegen Ausführungscommit und vertrauenswürdigen Checkout geprüft. Die vier
abgeschlossenen Zellen einschließlich aller 29 Kandidaten, ursprünglicher
Auswahl, Verlustnachweise, Optionen und Diagnosen wurden erneut verifiziert.
Zusätzlich wurden ihre CSV-Bäume und skalaren Vorhersagen unabhängig geprüft.
Die ursprünglichen Dateien blieben unverändert. Das frühere Datenarchiv
`representation-manjaro-001.tar.gz` lag hier nicht erneut vor; die enthaltenen
Eingabekopien und ihre Bindungen wurden geprüft.

| Zelle | Grammatik | Iterationen | Auswahlindex | Trainings-MSE | diagnostischer relativer RMS | Kurve / Parameter |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | unrestricted | 200 | 4 | 0,0495528314580966 | 0,877300965009291 | außerhalb / nicht beurteilt |
| 2 | no_nested_trig | 200 | 8 | 0,030589981008770764 | 0,688406203016528 | außerhalb / nicht beurteilt |
| 3 | no_nested_trig | 2000 | 7 | 2,4108123730080023e-23 | 1,9351167413316857e-11 | innerhalb / passend |
| 4 | unrestricted | 2000 | 6 | 1,9463313463296228e-25 | 1,7387961336411802e-12 | innerhalb / passend |

Alle vier Zellen verwenden Seed 20261103. Die beiden hohen Originalauswahlen
bestehen außerdem Struktur-, rohe und Alias-Replaydiagnose. Das ist ein
belegter Teilbefund am bekannten Entwicklungsfall, kein abgeschlossener
Budgetvergleich: Zelle 5 scheiterte, Zellen 6–20 wurden nicht gestartet.
`status=incomplete`, `final_verification=failed`; Gruppenaggregate,
Paardifferenzen und Gesamtentscheidung bleiben gesperrt. Physikalische
Identifikation bleibt `not_assessed`, insbesondere der Blindfleck bei 8·fs.

## Exakt reproduzierter Abbruch

Zelle 5: `no_nested_trig`, Seed 20261104, 200 Iterationen. Der Fit endete nach
40,8254 Sekunden; der Worker scheiterte danach beim Verlust-Replay. Die siebte
CSV-Formel, Komplexität 15, lautet unverändert:

```text
sin((t - 7.391680536538446e8) * -7.631169600584433) * (sin((t - -27188.895031268137) * 207463.99492437518) * 0.2600485957097388)
```

Alle sieben CSV-Bäume wurden über einen Parser mit explizit erlaubten
Syntaxelementen aufgebaut und mit den gepinnten nativen Quellen fest
nachgerechnet. Sechs Verluste stimmen bitgenau. Beim siebten bestätigt die
Nachrechnung exakt den übermittelten Fehler:

- gespeicherter Verlust: `0.03399585286266448`;
- natives Replay: `0.03399585394761332`;
- Python-/skalares Replay: `0.03399585394761333`;
- relativer Abstand gespeichert/nativ: ungefähr `3,19e-8`.

Julia-/Python-Vorhersagen unterscheiden sich höchstens um `2,78e-17`.
Damit ist dies weder der frühere Nähe-null-Fall noch der Pandas-CSV-Fall.
Der gespeicherte Verlust passt nicht zur nachgerechneten Formel. Die strenge
Ablehnung ist korrekt. Es gibt keinen vollständigen `result.json`-Export für
Zelle 5; die CSV-Rekonstruktion ersetzt keinen authentifizierten nativen
Baumexport und liefert keine nachträgliche Originalauswahl. Die frühere
Mutationsgeschichte ist damit nicht eindeutig rekonstruierbar.

## Nachgewiesener Backendfehler und Grenze der Ursachenzuordnung

In SymbolicRegression 2.5.1 übernimmt `SimplifyMutation` nach `simplify_tree!`
und `combine_operators` den Verlust des Elternbaums. Auch
`optimize_and_simplify_population` vereinfacht ohne zwingende Neuberechnung;
`finalize_costs` berechnet bei deaktiviertem Batching nicht neu. Algebraische
Äquivalenz garantiert jedoch keine identische Float64-Auswertung.

Ein unabhängiger Achtpunktfall belegt beide Pfade ohne Suche oder Optimierung:
`t=j/8`, j=0,…,7, `y=1+t`, Baum `((t-1e16)-(-1e16))+1`.
Die ursprüngliche Float64-Vorhersage ist konstant 1; MSE = `0.2734375`.
Die Vereinfachung liefert `t+1`, MSE = 0, behält aber in beiden nativen Pfaden
den alten Verlust `0.2734375`. Mit `should_simplify=false` bleibt im
Populationspfad Baum und Verlust konsistent; die Simplify-Mutation wird durch
die native Gewichtskonditionierung ausgeschaltet.

Quellen des gepinnten Backends:
[Mutate.jl](https://github.com/MilesCranmer/SymbolicRegression.jl/blob/v2.5.1/src/Mutate.jl),
[SingleIteration.jl](https://github.com/MilesCranmer/SymbolicRegression.jl/blob/v2.5.1/src/SingleIteration.jl),
[Population.jl](https://github.com/MilesCranmer/SymbolicRegression.jl/blob/v2.5.1/src/Population.jl).
Die installierten, durch Manifest gepinnten Quellen wurden direkt gelesen.
Das Gegenbeispiel beweist einen passenden Fehlermechanismus, aber ohne
Mutationsprotokoll nicht seine alleinige historische Verursachung in Zelle 5.
Die [vor Implementierung gebundene Abhilfe](search_duration_simplification_plan.md)
vermeidet diesen belegten Pfad; verbleibende Inkonsistenzen müssen weiter
abbrechen. Ein erfolgreicher neuer wissenschaftlicher Lauf wird nicht behauptet.
