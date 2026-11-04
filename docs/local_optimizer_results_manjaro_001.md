# Ergebnis: lokaler Optimiererbudgetvergleich auf Manjaro

Stand: 04.11.2026. Die 20 frischen unrestricted-Suchen mit jeweils 200 äußeren
Iterationen sind abgeschlossen und unabhängig nachgerechnet. Die vier lokalen
Profile erreichen 1/5, 2/5, 2/5 und 3/5 Kurvenerfolge. 300/5 liefert in dieser
Serie die meisten erfolgreichen Originalauswahlen bei rund 32 % mehr summierter
Zellzeit als 100/2. Alle vier Profile erreichen jedoch jeweils nur eine nach
der bestehenden Regel vollständig unterstützte Rekonstruktion. 300/5 verliert
außerdem den einzigen Kurvenerfolg der Baseline. Das begründet einen Kandidaten
für einen Folgeversuch, kein allgemein überlegenes oder optimales Suchprofil.

## Herkunft und selbst ausgeführte Nachrechnung

Originalarchiv `local-optimizer-manjaro-001.tar.gz`, SHA-256
`1ab8c0aa91436c4b169c6c6efa8053e04c47ef57d07915f36ac476483276866d`.
Sauberer Ausführungscommit `cf04476057b95c1517e1a303f4b48fbd30545a47`,
Squash-Merge von [PR #61](https://github.com/craexxn/ringdown-sr/pull/61).
Sein Dateibaum entspricht dem geprüften Head
`3fe7e7a181ba5b8d00ecbc81fe00bf62e49c2ce7`.
Die vollständige [CI 41817419054](https://github.com/craexxn/ringdown-sr/actions/runs/41817419054)
bestand vor der wissenschaftlichen Ausführung: 2.186 Python-Tests,
272 native Assertions und sämtliche technischen Integrationen.
Das übermittelte KI-basierte Implementierungsreview am vorherigen Head c2228a9
bestätigte die Methodentreue. Sein P3-Hinweis zum Umfang der Zeitmessung wurde
in 3fe7e7a ausschließlich in der Bedienung korrigiert.

Der vor Code eingefrorene [Methodenplan](local_optimizer_plan.md) ist unverändert:
Commit `e7b457bf8927cdd1b52c51bb3457b54d0c88f066`, SHA-256
`793006863a739a973dd3ffcf82c6e665f1a77da7eefee4132555843230df7f47`.
Selbst ausgeführter lesender Audit:

- Archivhash, 545 Originaldateien, 544 Abschlussmanifest-Einträge,
  542 ursprüngliche Verbrauchsanker und 80 gebundene Quellen geprüft.
  Quellen gegen Ausführungscommit und vertrauenswürdigen Checkout verglichen;
  Planbytes, Runtimekopien, Herkunft, Datenbits und getrennte Datenrollen stimmen.
- Alle 20 vorab bestimmten Zellidentitäten, Reihenfolgen und Budgets bestätigt:
  fünf neue Seeds, vier lokale Profile, 200 äußere Iterationen, unrestricted,
  `should_simplify=false`, unveränderte übrige Optionen und konkrete Plugins.
  Vorprüfungen, native Optionsnachweise und tatsächliche Suchaufrufbelege geprüft.
- Alle 183 Originalkandidaten durch den bestehenden Elternprüfpfad nachgerechnet:
  Rundungsreferenzen, Verluste, Residuen, Originalauswahl und Diagnosen stimmen.
  Sämtliche Vorhersagereferenzen benötigen 128 Bit. Alle Gruppenstatistiken,
  25 Paaraufzeichnungen und fünf Kontraste vollständig reproduziert.
- Alle CSV-Formeln mit beschränkter Syntaxauswertung gegen die ursprünglichen
  Bäume, Reihenfolgen, Komplexitäten und Verluste geprüft. Unabhängige skalare
  Baumrekursion mit `math`, `math.fsum` und `math.hypot` bestätigt die Kurvenmarker
  sämtlicher 183 Kandidaten auf beiden Rastern. Auswahlregel, Erfolgswechsel,
  Strukturgewinnregel, Zählinteraktion und Kostenzuordnung zusätzlich unabhängig
  von den Aggregationshelfern nachgerechnet.
- Alle 183 Originalbäume mit Julia 1.13.1 / SymbolicRegression 2.5.1 nativ erneut
  ausgewertet: Baumrundreise, Grammatik und Komplexität stimmen;
  Vorhersagebits und native Original-/Replayverluste sind vollständig identisch.
  Null Zielfunktionscallbacks, keine neue Suche, kein Fit und keine Optimierung.

Kein Archivcode und keine serialisierten Suchzustände ausgeführt. Alle
Originaldateien blieben unverändert. Eigene Nachweise liegen unter
`/workspace/audits/local-optimizer-manjaro-001/`: `original_sha256.json`,
`audit.json`, `native_replay.json`, `independent_summary.json` und eigene
Auditskripte/Logs. Das ursprüngliche Eingangsarchiv
`representation-manjaro-001.tar.gz` lag hier nicht erneut vor; die enthaltenen
Datenkopien, ihre eingefrorenen Bits und die gebundene Eingangshashangabe wurden
geprüft. Der neue Audit ersetzt keine unabhängige Leistungsvalidierung.

## Vorab festgelegte Endpunkte

B = 100/2, I = 300/2, R = 100/5, X = 300/5. Die zweite Zahl bezeichnet
zusätzliche Neustarts, also insgesamt drei beziehungsweise sechs lokale
Versuche. Alle Profile verwenden dasselbe äußere Budget von 200 Iterationen.
Kurvenerfolg verlangt bei derselben Originalauswahl auf Training und den
889 inneren Achtelpunkten jeweils relativen RMS ≤ 0,001 und relativen
Maximalfehler ≤ 0,01. Unterstützte Rekonstruktion verlangt zusätzlich erkannte
Struktur, passende Parameter sowie bestandenen Parameter- und Aliasreplay.

| Profil | Kurvenerfolge | Unterstützte Rekonstruktionen | Gute ungewählte Kandidaten | Median relativer RMS auf Zwischenpunkten |
| --- | ---: | ---: | ---: | ---: |
| 100/2 | 1/5 | 1/5 | 1 | 0,0222305 |
| 300/2 | 2/5 | 1/5 | 5 | 0,0413870 |
| 100/5 | 2/5 | 1/5 | 2 | 0,00566910 |
| 300/5 | 3/5 | 1/5 | 8 | 4,92279e-9 |

Gute ungewählte Kandidaten werden weder als erfolgreiche Originalauswahl
gezählt noch nachträglich ausgewählt. Die 25 Paare sind fünf Kontraste derselben
20 Zellen und keine 25 unabhängigen Wiederholungen.

In der folgenden Tabelle bedeutet S: Kurvenerfolg mit vollständiger Unterstützung,
K: Kurvenerfolg ohne diese Unterstützung, –: Kurvenkriterien nicht erfüllt.

| Seed | 100/2 | 300/2 | 100/5 | 300/5 |
| --- | --- | --- | --- | --- |
| 20261120 | – | K | – | K |
| 20261121 | – | – | – | – |
| 20261122 | – | – | S | K |
| 20261123 | – | – | – | S |
| 20261124 | S | S | K | – |

## Alle fünf Kontraste

Erfolgswechsel beziehen sich auf den Kurvenendpunkt. Ein positiver Strukturgewinn
verlangt vorab ein höheres C und mindestens einen neuen 0→1-Kurvenerfolg mit
vollständiger Unterstützung derselben höheren Originalauswahl.

| Kontrast | C vorher → nachher | 0→0 | 0→1 | 1→0 | 1→1 | Neuer unterstützter Seed | Einordnung |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 300/2 gegenüber 100/2 | 1 → 2 | 3 | 1 | 0 | 1 | keiner | approximation_gain_only |
| 300/5 gegenüber 100/5 | 2 → 3 | 1 | 2 | 1 | 1 | 20261123 | supported_structure_gain |
| 100/5 gegenüber 100/2 | 1 → 2 | 3 | 1 | 0 | 1 | 20261122 | supported_structure_gain |
| 300/5 gegenüber 300/2 | 2 → 3 | 1 | 2 | 1 | 1 | 20261123 | supported_structure_gain |
| 300/5 gegenüber 100/2 | 1 → 3 | 1 | 3 | 1 | 0 | 20261123 | supported_structure_gain |

Die Zählinteraktion ist (3−2)−(2−1)=0. Daraus folgt weder Unabhängigkeit der
Faktoren noch ein allgemeiner Synergiebefund. Die Regelbezeichnung
`supported_structure_gain` behauptet hier ausdrücklich keine Steigerung der
Gesamtzahl unterstützter Rekonstruktionen: Diese bleibt in jeder Gruppe 1/5.
Der positive Befund entsteht an anderen Seeds. Die unterstützten Parameter
liegen jeweils nahe f=250 Hz und tau=0,008 s; physikalische Identifikation
bleibt `not_assessed`.

300/5 gewinnt gegenüber 100/2 die Seeds 20261120, 20261122 und 20261123,
verliert aber 20261124. Bei 20261121 steigt der relative Zwischenpunkt-RMS
von 0,0410111 auf 0,737745. 300/2 erhöht zwar die Erfolgszahl, verschlechtert
aber den Median des Zwischenpunkt-RMS gegenüber 100/2. Mehr lokales Budget
verbessert damit weder jeden Seed noch jede kontinuierliche Kennzahl.

Vier erfolgreiche Originalauswahlen bleiben unter der gebundenen
Strukturerkennung ungestützt: Zelle 2 (`exponential_factor_count`),
Zellen 3 und 20 (`unsupported_affine_operator`) und Zelle 10
(`trigonometric_denominator`). Das ist eine Grenze des festgelegten Nachweispfads,
kein Beweis einer mathematisch falschen Struktur. Insbesondere werden die
Originalbäume nicht nachträglich vereinfacht oder durch einen erweiterten
Erkenner neu bewertet. Für die spätere Messregel zur Strukturstabilität bleibt
diese Unterscheidung relevant.

## Gemessener Aufwand

Die Serie benötigte **1.315,952 s = 21 min 55,952 s**. Die Zellzeiten summieren
sich auf 1.280,518 s; weitere 35,434 s entfallen auf die übrige Serienarbeit.
Alle Zellen liegen weit innerhalb der unveränderten 600-/7.200-Sekunden-Grenzen.

| Profil | Summe Zellzeit inklusive Elternverifikation [s] | Median Zellzeit [s] | Summe Fitzeit inklusive JIT/Export [s] | Callbacks während Fit | Zellzeit gegenüber 100/2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100/2 | 281,232 | 56,561 | 211,613 | 8.107.668 | Referenz |
| 300/2 | 296,060 | 59,285 | 227,511 | 11.950.747 | +5,3 % |
| 100/5 | 332,081 | 68,023 | 263,311 | 16.707.271 | +18,1 % |
| 300/5 | 371,146 | 76,063 | 302,589 | 23.447.840 | +32,0 % |

`worker_wall_seconds` enthält den Armaufruf und die Elternverifikation.
`status.json.total_wall_seconds` enthält bereits Metadaten-/Startvorbereitung
und Ergebnislesen im Elternprozess; keine der beiden Größen ist reine
Workerprozesszeit. Callbackzahlen sind keine Anzahl eindeutiger Bäume oder
lokaler Optimiererschritte. Der separate Backend-Evaluationszähler ist nicht
verfügbar. Kostenverhältnisse gelten für diese Serie bei 200 äußeren Iterationen
und werden nicht auf 5.000 oder 10.000 hochgerechnet.

## Einordnung und begrenzte Fortsetzung

**Empfehlung, noch kein neuer Ausführungsplan:** 300/5 ist wegen des primären
Kurvenendpunkts und des beobachteten Mehraufwands der vorrangige Kandidat für
das Arbeitsprofil des nächsten äußeren Budgetvergleichs. 100/5 bleibt eine
günstigere Alternative mit einem neuen unterstützten Erfolg gegenüber der
Baseline. Eine allgemeine Überlegenheit von 300/5 oder die Notwendigkeit von
300 lokalen Schritten ist nicht belegt. Der Vorteil wurde nur bei 200 äußeren
Iterationen untersucht; seine Übertragung auf größere Suchbudgets ist offen.

Die vorgemerkte äußere Staffel **200, 500, 2.000 und 5.000** bleibt ein separat
vor Ausführung festzulegender Folgeschritt. **10.000** bleibt eine spätere Option
bei positivem Trend auf beiden Rastern unter Berücksichtigung von Struktur
und Aufwand. Profile, neue Seeds, Kontraste und Zeitbudget müssen vorab gebunden
werden; dieses Ergebnis startet keine weiteren Suchen und erweitert kein Budget.
Die vorab gestellte lokale Frage ist mit dieser abgeschlossenen Serie beantwortet;
kein weiterer breiter lokaler Budgetvergleich wird hier vorgeschlagen.

Fünf frische Seeds am weiterhin bekannten, adaptiv untersuchten Signal sind
keine unabhängige Leistungsvalidierung. Die frühere 100/2-Gruppe aus
[Suchbudgetlauf 004](search_duration_results_manjaro_004.md) verwendete andere
Seeds; ihre 3/5 bei 200 Iterationen sind kein gepaarter Vergleich zu den jetzigen
1/5. Frühere Kontrollzellen werden nicht eingemischt. Die allgemeine Grammatik
bleibt festgehalten; keine Aussage allgemeiner Überlegenheit gegenüber
`no_nested_trig`. Der Alias-Blindfleck bei 8·fs=32768 Hz bleibt bestehen.

Nach Abschluss und Auswertung der Budgettests bleibt die in #61 festgehaltene
Pilotroute maßgeblich: begrenzter Transfercheck mit neuen Signalparametern,
vorhandene Rauschpipeline erproben, kompaktes Pilotdesign binden, Pilot auswerten
und Hauptversuchsplan vorbereiten. 2.048 äußere Iterationen sind ein Planungswert
für die Hauptstudie, keine zwingende Transfervorgabe. Getrennte Hintergrund-
Datenrollen und während Suche/Optimierung feste Kovarianzen bleiben erforderlich;
ein Vorteil der Kovarianzgewichtung ist kein notwendiges Erfolgskriterium.
Zwischenbewertung am 8./9. November und Pilotabschluss etwa am 15. November sind
Planungsziele. Keine automatische Umfangserhöhung bei fortbestehenden Problemen.
WSL2, Parallelisierung und große Umstrukturierung bleiben zurückgestellt.

## Alle ursprünglichen Auswahlen

Auswahlindizes sind nullbasiert. T bezeichnet relativen Trainings-RMS, Z den
relativen RMS auf Zwischenpunkten, Zmax deren relativen Maximalfehler.
Die folgenden Werte sind gerundet; vollständige Originalzahlen und sämtliche
Kandidaten stehen im unveränderten Archiv.

| Zelle | Seed | Profil | Index | Komplexität | T | Z | Zmax | Kurve / Unterstützung |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 20261120 | 100/2 | 9 | 19 | 0.0223991 | 0.0222305 | 0.0237144 | nein / nein |
| 2 | 20261120 | 300/2 | 6 | 18 | 1.41706e-11 | 1.45942e-11 | 7.67345e-12 | ja / nein |
| 3 | 20261120 | 300/5 | 5 | 17 | 1.03398e-12 | 1.06494e-12 | 5.60885e-13 | ja / nein |
| 4 | 20261120 | 100/5 | 10 | 20 | 0.0412768 | 0.0414467 | 0.0345592 | nein / nein |
| 5 | 20261121 | 300/2 | 10 | 17 | 0.0411019 | 0.041387 | 0.0323721 | nein / nein |
| 6 | 20261121 | 100/5 | 10 | 19 | 0.399012 | 0.288676 | 0.869365 | nein / nein |
| 7 | 20261121 | 100/2 | 11 | 20 | 0.0406924 | 0.0410111 | 0.031443 | nein / nein |
| 8 | 20261121 | 300/5 | 8 | 20 | 0.716102 | 0.737745 | 0.638326 | nein / nein |
| 9 | 20261122 | 100/5 | 6 | 13 | 1.30195e-11 | 1.34073e-11 | 6.59198e-12 | ja / ja |
| 10 | 20261122 | 300/5 | 7 | 14 | 4.77918e-09 | 4.92279e-09 | 2.60147e-09 | ja / nein |
| 11 | 20261122 | 300/2 | 8 | 16 | 0.04522 | 0.045806 | 0.0295597 | nein / nein |
| 12 | 20261122 | 100/2 | 10 | 18 | 0.709644 | 0.707413 | 0.735783 | nein / nein |
| 13 | 20261123 | 300/5 | 6 | 15 | 8.69939e-12 | 8.96237e-12 | 4.73954e-12 | ja / ja |
| 14 | 20261123 | 100/2 | 11 | 20 | 0.0104598 | 0.0105759 | 0.00664475 | nein / nein |
| 15 | 20261123 | 100/5 | 11 | 20 | 0.00560633 | 0.0056691 | 0.00384124 | nein / nein |
| 16 | 20261123 | 300/2 | 9 | 20 | 0.0733753 | 0.0736844 | 0.0658652 | nein / nein |
| 17 | 20261124 | 100/2 | 4 | 13 | 9.38501e-12 | 9.66588e-12 | 5.08971e-12 | ja / ja |
| 18 | 20261124 | 300/2 | 6 | 13 | 1.966e-10 | 2.02525e-10 | 1.07052e-10 | ja / ja |
| 19 | 20261124 | 300/5 | 9 | 19 | 0.0490154 | 0.0483423 | 0.0562777 | nein / nein |
| 20 | 20261124 | 100/5 | 7 | 19 | 3.58356e-05 | 3.65834e-05 | 2.38599e-05 | ja / nein |

### Originale Formelausdrücke

Unveränderte Anzeigeausdrücke in Zellreihenfolge; keine vereinfachten Ersatzformeln.

Zelle 1:

```text
(cos(t * 1570.7826617382946) * (sin((-9.865218312785665 * t) - 1.3722594905934091) - -1.0061048753220558)) * ((-1223.0936092285303 * t) - -37.896179219237595)
```

Zelle 2:

```text
(cos(-1570.796326792418 * t) * exp(t / (-270.74794595725854 * -1640.8779478989845))) * exp((-225.43997181985395 * t) / 1.8035197420940638)
```

Zelle 3:

```text
exp((-126.76806095959226 * t) * (cos(-0.16142857006882058 * 1.2498738847425459e-5) * exp(-0.014045387792967583))) * cos(t * 1570.7963267950652)
```

Zelle 4:

```text
((-1.5912114971624447 * sin(-1.5756456006331365 - (-15.704640790021068 * (t / -0.010001504537448809)))) * 2.9788702652365004) / (-18.17236131538904 - (-0.6773372303875047 / (0.029776874706650372 - t)))
```

Zelle 5:

```text
sin(sin((0.01300046566216634 - t) / 0.0006367867822415266) * -0.2627416023862081) / ((-0.0074825307762585915 - t) / (0.02978566573614323 - t))
```

Zelle 6:

```text
exp(-132.27590528219517 * t) * sin(t * (1692.5562010773363 * exp(0.942921311228787 * exp(311.1274061626771 * (t / -0.6771610149770795)))))
```

Zelle 7:

```text
((sin((0.0009985683563124286 - t) / -0.0006367858941095948) - -0.0052420454008553045) / ((-0.00743651209502232 - t) / (-0.9795849440085868 - (-32.849531084914844 * t)))) / -126.85829649704596
```

Zelle 8:

```text
sin(exp((exp((((-3.9421637840569965 * (-7.59541995074298 * -12.497964306772234)) * 75.62534023132396) * t) * t) * 14.47687466768375) + -4.725458533051321) * -0.0002667619855096016)
```

Zelle 9:

```text
sin((t * -1570.796326792161) - -1.5707963267857068) / exp((t * 3.6022969912084495) * 34.700081727431936)
```

Zelle 10:

```text
sin(1.5707808369236733) / (exp(t / 0.007999999955923492) / cos((t / -0.024962062475488763) / -0.025503492478114214))
```

Zelle 11:

```text
sin(-1.5747636620017775 + (1571.3330584031241 * t)) / ((((-20132.884497661547 * t) + -68.04259108280095) * t) + -1.032491192458249)
```

Zelle 12:

```text
(-0.2629135688177732 * sin(exp(t / 2.0984045371527698) * ((-8.49974402686537 + 369.07611342828454) * -9.135122956685567))) / exp(t / 2.0984045371527698)
```

Zelle 13:

```text
cos(t * 1570.7963267949874) * exp(t / (2657.645643805103 / ((3098.2252751436026 * 1365.5874016016696) / -12.735775856277076)))
```

Zelle 14:

```text
sin(-1434.1375100089588 + (t * -1570.759995905783)) / (-0.9927045449497872 + ((-0.36383192121593677 + (t * (t * -2585.4594515951903))) * (t / 0.002484475970172381)))
```

Zelle 15:

```text
cos((-1560.7615122176326 - 10.025057454751883) * t) / ((-246.74888181996553 * t) + ((0.037234955592496066 - (-12.472260806663256 * t)) / (0.03708320939750035 - t)))
```

Zelle 16:

```text
((0.03228319128395612 - t) * (0.03228319128395612 - t)) * (((2176.7656208748735 * cos(-1570.7740249407746 * t)) * (0.032283191248036344 - t)) * 12.742187258454983)
```

Zelle 17:

```text
cos((t * (-0.8256071942164938 * 88.46971092166628)) * 21.505611706472497) / exp(125.00000000072762 * t)
```

Zelle 18:

```text
cos(t / ((0.09668690282903111 * -0.10043180981792588) * 0.06556033821453228)) * exp(t / -0.008000000002100221)
```

Zelle 19:

```text
cos(51.92189876190828 * t) * ((0.9426683406684165 - ((83.2326130739356 - (2195.614926328921 * t)) * t)) * cos(1570.8141180491095 * t))
```

Zelle 20:

```text
sin((exp((t * -0.10721881698226382) * t) * -3378.7828807516876) * exp(t * 0.4648966729340116)) * exp(t * -125.0001320795795)
```
