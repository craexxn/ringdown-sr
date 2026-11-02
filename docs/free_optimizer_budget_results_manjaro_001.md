# Freier Optimiererbudgetvergleich auf Manjaro: Ergebnis 001

Stand der übermittelten Auswertung: 02.11.2026.

**Befund aus den Berichtsauszügen:** Unter 100/2 sinken Trainings-MSE und
relative RMS-Fehler bei allen drei bekannten Entwicklungsseeds. Unter beiden
Budgets bleiben jedoch 0/3 erfolgreiche Originalauswahlen. Auch unter den
ungewählten Frontkandidaten wird kein Kurvenerfolg berichtet. Insgesamt sind
50 Frontkandidaten exportiert; diese sind keine 50 unabhängigen Wiederholungen.

## Herkunft und Prüfgrenze

- Übermittelte Quelle: Terminalauszüge aus `summary.md` und `report.json`
  von `results/free-budget-manjaro-001`, einschließlich aller sechs
  ausgewählten Anzeigeformeln, Strukturgründe, Fehler und Aufwandsangaben.
- Übermittelte SHA-256 von `free-budget-manjaro-001.tar.gz`:
  `77fb34ff6ee139c1f2e0fbbb6acd81d7c1623cd6e8090056f641961e887ad33f`.
  Das Archiv selbst lag für diese Auswertung nicht vor. Diese Prüfsumme wurde
  übernommen, nicht durch eigenes Hashen des Originalarchivs bestätigt.
- Für den Manjaro-Lauf vorgegebener Ausführungsstand:
  `8bdc8dbc498be6e8527fa2a857293bf74b42f81f`, Merge von
  [PR #45](https://github.com/craexxn/ringdown-sr/pull/45).
  Die Git-Herkunft im Ergebnisarchiv ist noch nicht unabhängig abgeglichen.
- Selbst über GitHub bestätigt: Der Merge und der geprüfte PR-Head
  `4e29ae44d8e481eb96af128f06e8db7666fff934` besitzen denselben Git-Tree
  `ab0e06f36d4cdb2ccf5c27ec53e9bc8b5ebbe099`.
  Die [vollständige technische CI des PR-Heads](https://github.com/craexxn/ringdown-sr/actions/runs/41190324974)
  wurde anhand von Run- und Jobstatus einschließlich sämtlicher technischer
  Schritte erfolgreich bestätigt. Keine Wiederholung dieser CI für die Auswertung.
- Übermittelter Serienstatus `completed`, Abschlussverifikation `passed`,
  sechs Zellen `completed`. Das ist die gespeicherte Meldung des Treibers;
  ein unabhängiger Audit aller Manifest-, Options-, Quellen- und Datenanker
  des neuen Originalarchivs wird damit nicht behauptet.
- Selbst nachgerechnet: die sechs geposteten Anzeigeausdrücke auf 128
  Trainings- und 889 Diagnosepunkten. JavaScript-Float64 mit
  `Math.exp/sin/cos/hypot`, unveränderte Klammerung der Ausdrücke;
  Referenz und Fehlernormalisierung aus
  [noiseless_control.py](../src/ringdown_sr/noiseless_control.py) am
  genannten Ausführungsstand. Alle 30 Werte aus Trainings-MSE und
  RMS-/Maximalfehlern beider Raster stimmen mit den Auszügen überein;
  größte absolute Differenz etwa `2.78e-17`.
  Dies prüft die Auszüge, nicht die ursprünglichen binären Exportbäume,
  sämtliche Fronten oder archivierte Residuen.
- Keine neue Suche, Konstantenoptimierung oder Julia-Ausführung in dieser
  Ergebnisauswertung. Ein vollständiger Originalarchiv-Audit bleibt offen.

## Design und Endpunkt

Es gilt der eingefrorene [Methodenplan](free_optimizer_budget_plan.md),
Commit `bb4862034b49b89dcc37d8341814e42aa02989c5`, SHA-256
`b63e66461e3a380f9e8ca5c127e8c5f99cd2a0d574be7be1603f18f56292907b`.

Sechs frische Suchen: 20 beziehungsweise 100 maximale lokale
Optimiereriterationen, jeweils zwei zusätzliche Neustarts, beide
Häufigkeitsschalter aktiviert und ursprüngliche Sekundenkoordinate.
Je Zelle 200 Suchiterationen, zwei Populationen zu 32 Individuen, 50 Zyklen.
Bekanntes rauschfreies Signal mit 128 Trainingswerten und 889 inneren
Achtelpunkten; keine Diagnosepunkte oder Wahrheit als Suchhilfe.

Erfolg verlangt für dieselbe Originalauswahl auf beiden Rastern
`relative_rms <= 0.001` und `relative_max <= 0.01`.
Auswahlindex, Reihenfolge und Grenzwerte bleiben unverändert.

| Zelle | Seed | Lokale Iterationen | Originalindex | Komplexität | Frontgröße | Kurve | Struktur | Parameter |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | 20261020 | 20 | 5 | 13 | 6 | outside_tolerance | not_supported | not_assessed |
| 2 | 20261020 | 100 | 9 | 19 | 10 | outside_tolerance | not_supported | not_assessed |
| 3 | 20261021 | 100 | 7 | 19 | 8 | outside_tolerance | not_supported | not_assessed |
| 4 | 20261021 | 20 | 6 | 19 | 7 | outside_tolerance | not_supported | not_assessed |
| 5 | 20261022 | 20 | 9 | 17 | 10 | outside_tolerance | not_supported | not_assessed |
| 6 | 20261022 | 100 | 8 | 16 | 9 | outside_tolerance | not_supported | not_assessed |

Die drei 20er-Fronten enthalten zusammen 23, die drei 100er-Fronten 27
Kandidaten. Aus 0 erfolgreichen Originalauswahlen und 0 kurvenguten
ungewählten Kandidaten je Budget folgt für die übermittelten Fronten:
0/50 Kurvenerfolge. Die Strukturgründe wurden hier nur für die sechs
Originalauswahlen übermittelt; daraus folgt kein Strukturstatus aller 50 Bäume.

## Kontinuierliche Fehler der Originalauswahlen

| Zelle | Trainings-MSE | Training RMS | Training Max | Diagnose RMS | Diagnose Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.006275840088351765 | 0.3030790294586404 | 0.3250162081748179 | 0.3014591735372102 | 0.3232649781772161 |
| 2 | 0.002035415470878259 | 0.1726022643772139 | 0.11871316606369353 | 0.17779847047721714 | 0.11849460042632555 |
| 3 | 0.0005124928763662695 | 0.08660916865146916 | 0.12353801751502114 | 0.08347975398578916 | 0.12110438512901311 |
| 4 | 0.002515000237397423 | 0.19186200054227323 | 0.10407909810183041 | 0.1974131537584195 | 0.10695860709669903 |
| 5 | 0.002035415472898297 | 0.17260226446286298 | 0.11871586210213114 | 0.1777984714331526 | 0.11849783662612724 |
| 6 | 0.000723243966949056 | 0.1028874404061427 | 0.09882281122108816 | 0.10295592136912703 | 0.09694909402421059 |

RMS und Max sind relativ zur jeweiligen Referenz auf dem jeweiligen Raster.
Alle übermittelten Paarmetriken haben Status `available`, somit jeweils
3/3 endliche Werte je Budget und Metrik. Prozentuale Verbesserungen sind
`100 * (1 - Fehler_100 / Fehler_20)`, keine Erfolgswahrscheinlichkeiten.

| Seed | MSE kleiner um | Diagnose-RMS kleiner um | Delta Diagnose-Max (100 minus 20) |
| --- | ---: | ---: | ---: |
| 20261020 | 67.567442 % | 41.020713 % | -0.20477037775089058 |
| 20261021 | 79.622552 % | 57.713175 % | +0.01414577803231408 |
| 20261022 | 64.467010 % | 42.094035 % | -0.02154874260191665 |

Bei Seed 20261021 steigen trotz kleinerer MSE beide Maximalfehler:
Training von 0.10407909810183041 auf 0.12353801751502114,
Diagnose von 0.10695860709669903 auf 0.12110438512901311.
Alle drei Erfolgswechsel sind `nicht bestanden -> nicht bestanden`.
Der beste Diagnose-RMS entspricht noch etwa dem 83.48-Fachen der festen Grenze.

## Originale Anzeigeformeln und Strukturdiagnosen

Die folgenden Zeichenketten sind aus den Terminalauszügen übernommen.
Algebraische Deutungen ersetzen keine Originalbäume oder Auswahl.

Zelle 1:

```text
cos((t + t) * 789.3585311358653) * (0.6749837918251821 - sin(t * 26.789615391297144))
```

Zelle 2:

```text
sin(0.1548412379556712 / (((t / 0.020736597872640435) + 0.09476507199059332) / sin((((t / -0.024285952408210423) + 0.028763403261519695) / 0.026247968165630152) + 0.4505552422640563)))
```

Zelle 3:

```text
((cos(t * 1570.8904367489856) * -29.604967206294102) * cos((0.03464013179096598 - t) * (t * 4318.804181487477))) * (t - 0.029605234026357594)
```

Zelle 4:

```text
sin((-0.2882236213429937 / (((t / -0.0038454300225987553) - 0.7968165019363348) * 0.401743575670685)) * sin((t / -0.0006349224171177073) - -1.5634075667159821)) * 1.314389796873057
```

Zelle 5:

```text
sin((sin(((t * -1.0497586077106384) + -0.29959075098344556) * 1494.3764123000594) / ((t * -245.91837297946822) + -0.4832584475583017)) / 1.2664393938753389)
```

Zelle 6:

```text
((t - 0.024621361363751842) * sin((t * -1573.0620353248692) - -1.586331578652905)) * ((t - 0.02462136137876959) * 1486.7518054008688)
```

Alle sechs Ausdrücke besitzen keinen expliziten Exponentialfaktor.
Der übermittelte Erstgrund `exponential_factor_count` passt dazu.
`raw_coefficients`, Amplituden-/Exponentialstatus und Phasenart sind
`null`; Replay, Alias und Parameterinterpretation `not_attempted`.
Für diese nicht unterstützten Strukturen wurden keine Parameter-Replays versucht.

Einzelne lineare Phasen liefern Trägerkomponenten nahe 250 Hz:
Zelle 1 etwa 251.260624 Hz, Zelle 3 etwa 250.014978 Hz, Zelle 6 etwa
250.360599 Hz. Das sind rechnerische Komponenten der jeweiligen Ausdrücke,
keine bestätigten physikalischen Frequenzen des Gesamtmodells.
Zelle 1 moduliert mit Konstante minus Sinus; Zelle 3 mit linearem Faktor
und zusätzlichem Kosinus; Zelle 6 mit einem nahezu quadratischen Faktor,
der bei ungefähr 24.62 ms nahezu null wird und anschließend wieder wächst.
Die verschachtelten Sinus-/Quotientenformen der anderen Zellen sind ebenfalls
keine nachgewiesenen exponentiell gedämpften Schwingungen.

Aus den Endfronten folgt weder, dass exponentielle Ausdrücke während der
Suche nie entstanden, noch dass ein bestimmter Optimierungs-, Einheiten-
oder Selektionsmechanismus allein den Misserfolg verursacht hat.

## Aufwand

| Zelle | Fit-Callbacks | Gesamt-Callbacks | Worker s | Fit einschließlich JIT/Export s | Setup s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 301956 | 301957 | 40.656985864000035 | 29.729082869999957 | 7.3954354449999755 |
| 2 | 935848 | 935849 | 46.34881475399993 | 34.879150202999995 | 7.846887161999916 |
| 3 | 808192 | 808193 | 46.18061675399997 | 34.604573594000044 | 8.012144742999908 |
| 4 | 290350 | 290351 | 42.37039250600003 | 30.870241941000018 | 7.918618829000025 |
| 5 | 392602 | 392603 | 43.623986752999826 | 31.9805953959999 | 8.038941659000102 |
| 6 | 640190 | 640191 | 48.48441382499982 | 36.32007373400006 | 8.379321078999965 |

Fit-Callbacks: 984908 unter 20/2, 2384230 unter 100/2; Faktor 2.420764.
Je Seed sind die Faktoren etwa 3.0993, 2.7835 und 1.6306.
Die Summe der Workerzeiten steigt von 126.651365123 auf 141.013845333 s,
also um etwa 11.34 %. Das ist keine gemessene Gesamtserienzeit:
Vorprüfungen und abschließende Elternprozessarbeit fehlen in dieser Summe.

Der zusätzliche Gesamt-Callback je Zelle gehört zur Nullkurvenauswertung
nach dem Fit. Der Backend-Evaluationszähler ist ausdrücklich `unavailable`
mit Grund `not returned by equation_search`. Callbackzahlen zählen weder
eindeutige Suchbäume noch reine Optimiererschritte. JIT/Setup/Export und
geänderte Suchpfade verhindern eine allgemeine Kostenhochrechnung.

## Einordnung und nächste Entscheidung

Der in Abschnitt 8 des Plans definierte Fall `C20 = C100 = 0` ist berichtet.
100/2 verbessert die kontinuierlichen Fehler überwiegend, erzeugt jedoch
keinen Erfolg am primären Endpunkt. Ein engerer Fehler ist kein Anlass,
Grenzen, Originalauswahl oder Erfolgsdefinition nachträglich zu ändern.

Die erfolgreiche [feste Konstantendiagnose](constant_diagnostic_results_manjaro_001.md)
unter 100/2 überträgt sich in diesen freien Entwicklungsfällen nicht auf
erfolgreiche Originalauswahlen. Das ist kein allgemeiner Unmöglichkeitsnachweis
für symbolische Regression und keine Identifikation eines einzelnen Engpasses.

Auf Grundlage dieses Befunds wird der vorliegende Vergleich dokumentarisch
abgeschlossen und ein [begrenzter Beobachtungsplan](search_trajectory_plan_draft.md)
zur Methodenentscheidung vorgelegt. Seine Zahlen und Beobachtungspunkte sind
ein Vorschlag; noch keine Implementierungs- oder Ausführungsfreigabe.
Keine automatische weitere Budgetstufe. Eine Eingrenzung oder Pause des
freien Rekonstruktionsanspruchs bleibt eine explizite Alternative.

`physical_identification` bleibt `not_assessed`; der Blindfleck des
Achtelrasters bei `8*fs=32768 Hz` bleibt bestehen. Übertragbarkeit und eine
Rausch-/Gewichtungsstudie benötigen ein eigenes Design.
