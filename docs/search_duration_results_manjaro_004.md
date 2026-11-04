# Ergebnis: vollständiger Manjaro-Suchbudgetvergleich 004

Stand: 04.11.2026. Alle 20 Zellen sind vollständig verifiziert. Ein größeres
äußeres Suchbudget verbessert den primären Kurvenendpunkt in beiden
Grammatiken um einen Erfolg. Ohne Einschränkung erfüllt der neu erfolgreiche
Seed zusätzlich den vorab verlangten Struktur-/Parameterbeleg. Das ist gemäß
[Entscheidungsregel](search_duration_plan.md#6-entscheidungsregel-und-mögliche-folgetests)
ein positives Entwicklungssignal für höheres Budget am bekannten Signal.
Es ist keine allgemeine Leistungsvalidierung oder physikalische Identifikation.

## Herkunft und unabhängig nachgerechneter Umfang

Originalarchiv `duration-manjaro-004.tar.gz`, SHA-256
`c2d9e330770746030bab9467b682a6b595cac25aa132dbb4decd1c4b03472289`.
Sauberer Ausführungscommit `79ff670b825efd8ba0e999edb983aec6f7e804ae`,
Squash-Merge von [PR #59](https://github.com/craexxn/ringdown-sr/pull/59).
Sein Dateibaum entspricht dem geprüften Head
`401ca5d79eff5a96b98bc99b89ecabd982c429e7`.
Das übermittelte KI-basierte Implementierungsreview meldete keine
korrekturbedürftigen Befunde; die vollständige
[CI 41785241800](https://github.com/craexxn/ringdown-sr/actions/runs/41785241800)
bestand vor der wissenschaftlichen Ausführung.

Selbst ausgeführter lesender Audit:

- Archivhash, alle 523 Originaldateien, 522 Einträge des Abschlussmanifests,
  520 ursprüngliche Verbrauchsanker und 72 gebundene Quellen geprüft.
  Quellen gegen Ausführungscommit und vertrauenswürdigen Checkout verglichen;
  Planbytes, Runtimekopien, Vor-/Abschlussherkunft und getrennte Datenbits stimmen.
- Alle 20 festgelegten Zellidentitäten, Seeds, Reihenfolgen und Budgets,
  Python-/native Profile, Grammatik-, Plugin-, Haswell- und Aufrufnachweise
  geprüft. `should_simplify=false`, 100/2-Optimierung und Originalauswahl erhalten.
- Alle 193 Kandidaten durch den tatsächlichen Elternprüfpfad nachgerechnet:
  Rundungsreferenzen, Verluste, Residuen, Auswahlindizes, Kurven- und
  Parameterdiagnosen stimmen. Sämtliche Referenzen benötigen 128 Bit.
  Alle Gruppenstatistiken und 20 Paardifferenzen vollständig reproduziert.
- Alle CSV-Formeln mit einer beschränkten Syntaxauswertung gegen Originalbäume,
  Reihenfolge, Komplexität und native Verluste geprüft. Zusätzlich skalare
  Baumrekursion mit `math`/`math.fsum`/`math.hypot`: dieselben Kurvenmarker auf
  Trainings- und Diagnoseraster für alle 193 Kandidaten. Nahe null wird keine
  unbegründete relative Gleichheit verschiedener MSE-Rechenwege verlangt.
- Alle 193 Originalbäume nativ mit Julia 1.13.1 / SymbolicRegression 2.5.1
  erneut ausgewertet: Baumrundreise, Grammatik und Komplexität bestätigt,
  Vorhersagebits und native Original-/Replayverluste vollständig identisch.
  Null Zielfunktionscallbacks, keine Suche, kein Fit und keine Optimierung.

Kein Archivcode und keine serialisierten Suchzustände ausgeführt; sämtliche
Originaldateien blieben unverändert. Lokale Nachweise liegen unter
`/workspace/audits/duration-manjaro-004/`: `original_sha256.json`, `audit.json`,
`native_replay.json` und zugehörige eigene Auditskripte/Logs. Diese sind eigene
Nachrechnungen; die separate Reviewprüfung von #59 hatte die Originalarchive
nicht vorliegen. Das frühere Eingangsarchiv `representation-manjaro-001.tar.gz`
lag hier nicht erneut vor; die im Lauf enthaltenen Datenkopien und ihre
gefrorenen Bits wurden vollständig geprüft.

Die vier ersten frischen Fronten stimmen mit Lauf 003 in Kandidatenreihenfolge,
Bäumen, Verlusten, Vorhersagen, Residuen und Originalauswahl überein. Das sind
34 erneut gefundene Kandidaten, keine übernommene Fortsetzung. Die wiederholten,
teilweise bereits gesehenen Seeds bleiben adaptive Entwicklung; der gespeicherte
Scope-Text „five new seeds“ ist im Kontext der Neustarts kein Beleg neuer Blinddaten.

## Vorab festgelegte Endpunkte

K = `unrestricted`, A = `no_nested_trig`. Ein Kurvenerfolg erfordert auf
Training und innerem Achtelraster jeweils relativen RMS ≤ 0,001 und relativen
Maximalfehler ≤ 0,01. Unterstützte Rekonstruktion erfordert zusätzlich die
bestehenden Struktur-, Abkling-, Parameter- und Replaygates derselben Auswahl.

| Gruppe | Erfolgreiche Originalauswahlen | Unterstützte Rekonstruktionen | Gute ungewählte Kandidaten |
| --- | ---: | ---: | ---: |
| K200 | 3/5 | 2/5 | 9 |
| K2000 | 4/5 | 2/5 | 14 |
| A200 | 2/5 | 0/5 | 3 |
| A2000 | 3/5 | 1/5 | 7 |

Gute ungewählte Kandidaten zählen nicht als Auswahlerfolge. Die unterstützten
Rekonstruktionen steigen bei K insgesamt nicht an: Sie bleiben 2/5. Die
festgelegte positive Einordnung beruht auf einem **neuen 0→1-Kurvenerfolg mit
Strukturbeleg**, nicht auf einer behaupteten Erhöhung aller Strukturzählwerte.

| Seed | K200 → K2000: Kurve | A200 → A2000: Kurve | Strukturbeleg des neuen hohen Kurvenerfolgs |
| --- | --- | --- | --- |
| 20261103 | 1 → 1 | 1 → 1 | kein neuer Kurvenerfolg |
| 20261104 | 1 → 1 | 1 → 1 | kein neuer Kurvenerfolg |
| 20261105 | 1 → 1 | 0 → 0 | kein neuer Kurvenerfolg |
| 20261106 | 0 → 0 | 0 → 1 | A: nicht unterstützt |
| 20261107 | 0 → 1 | 0 → 0 | K: erkannt, abklingend, Parameter passend |

Daraus folgt Δ_K = +1 mit `supported_structure_gain`, Δ_A = +1 mit
`approximation_gain_only`. In keiner Grammatik gibt es einen 1→0-Kurvenwechsel.
Das schließt Verschlechterungen kontinuierlicher Fehler nicht aus.

A hat bei beiden Budgets einen Kurvenerfolg weniger als K; die deskriptive
Zählinteraktion Δ_A−Δ_K ist null. Bei 2.000 Iterationen gewinnt A gegenüber K
Seed 20261106, verliert aber 20261105 und 20261107. Die Einschränkung ist damit
weder allgemein überlegen noch generell erfolglos. Es gibt keinen Nachweis
einer allgemeinen Überlegenheit einer Grammatik; fünf gepaarte Seeds am
bekannten Signal werden nicht zu einer allgemeinen Erfolgswahrscheinlichkeit
zusammengefasst. Frühere Serien bleiben unter ihren damaligen Bedingungen
unverändert; der frühere 0/3-Befund wird nicht rückwirkend umgewertet.

## Neuer unterstützter Kurvenerfolg und Gegenfall

Bei Seed 20261107 verbessert K2000 die ausgewählte Formel aus Zelle 17 zu
Zelle 20. Ihre unveränderte Originalform lautet:

```text
cos(1570.7963267946689 * t) * exp((0.5244153001345051 - 66.10628457253976) * (t / 0.524654954177711))
```

Die vorhandene Diagnose erhält A=1, f≈249,999999999964 Hz,
τ≈0,007999999999977 s und φ=0; Roh- und Aliasreplay bestehen.
Trainings-MSE: `3,721738579830651e-25`, diagnostischer relativer RMS:
`2,404268765469483e-12`. Das ist der geforderte neue unterstützte Erfolg.

Der neue Kurvenerfolg von A bei Seed 20261106 (Zelle 13) erreicht ebenfalls
sehr kleine Fehler, wird vom vorhandenen Erkenner aber nicht unterstützt.
`not_supported` ist eine Grenze dieses Erkenners, kein Beweis, dass die reelle
Funktion algebraisch keinen Ringdown darstellen könnte. Keine nachträgliche
Vereinfachung, Umklassifizierung oder Erweiterung des Erkenners im Audit.

**Wichtiger Gegenfall: Seed 20261106 ohne Einschränkung, Zellen 14 → 15.**
Die Trainings-MSE sinkt von `4,37413e-4` auf `7,75229e-6`, rund 98,2 Prozent.
Der diagnostische relative RMS steigt dennoch von `0,08036` auf `1,51055`,
der diagnostische Maximalfehler von `0,07147` auf `1,97463`.
Beide Auswahlen scheitern an den Kurvenkriterien. Die hohe Auswahl enthält
einen Kosinusträger mit ungefähr 7.942,00244 Hz, nahe `2*fs−250 Hz`; sein
Trainingsalias liegt bei ungefähr 249,99756 Hz. Dieser konkrete Befund zeigt,
warum kleinere Trainings-MSE allein keine bessere Rekonstruktion zwischen den
Messpunkten belegt. Das Diagnoseraster bleibt ausschließlich Auswertung,
kein nachträgliches Auswahlkriterium.

## Alle Originalauswahlen

Auswahlindizes sind nullbasiert. „Unterstützt“ umfasst die bestehenden
Struktur-/Parametergates. Fehlerwerte beziehen sich auf das Diagnoseraster;
der Kurvenmarker berücksichtigt zusätzlich das Training.

| Zelle | Seed | Gruppe | Index | Komplexität | Trainings-MSE | RMS diagnostisch | Max diagnostisch | Kurve | Unterstützt |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 20261103 | K200 | 8 | 13 | 4.90967e-20 | 8.73336e-10 | 4.61838e-10 | ja | ja |
| 2 | 20261103 | A200 | 8 | 19 | 1.38754e-22 | 4.64192e-11 | 5.24741e-11 | ja | nein |
| 3 | 20261103 | A2000 | 7 | 18 | 2.47404e-24 | 6.1977e-12 | 3.26369e-12 | ja | nein |
| 4 | 20261103 | K2000 | 7 | 15 | 8.45955e-28 | 1.14666e-13 | 6.05627e-14 | ja | nein |
| 5 | 20261104 | A200 | 9 | 19 | 7.44127e-11 | 3.3719e-05 | 2.11128e-05 | ja | nein |
| 6 | 20261104 | K2000 | 9 | 19 | 3.51422e-19 | 2.33654e-09 | 1.22425e-09 | ja | ja |
| 7 | 20261104 | K200 | 10 | 18 | 2.87465e-16 | 6.68227e-08 | 4.57547e-08 | ja | nein |
| 8 | 20261104 | A2000 | 5 | 11 | 1.541e-25 | 1.54727e-12 | 8.17957e-13 | ja | ja |
| 9 | 20261105 | K2000 | 10 | 20 | 6.76394e-27 | 3.23376e-13 | 1.92457e-13 | ja | nein |
| 10 | 20261105 | A2000 | 9 | 19 | 7.8185e-06 | 0.0108361 | 0.00666764 | nein | nein |
| 11 | 20261105 | A200 | 9 | 18 | 0.000776449 | 0.108263 | 0.0749381 | nein | nein |
| 12 | 20261105 | K200 | 7 | 17 | 1.89803e-22 | 5.4279e-11 | 2.85965e-11 | ja | ja |
| 13 | 20261106 | A2000 | 8 | 18 | 3.10561e-24 | 6.94582e-12 | 3.6719e-12 | ja | nein |
| 14 | 20261106 | K200 | 11 | 20 | 0.000437413 | 0.0803616 | 0.0714728 | nein | nein |
| 15 | 20261106 | K2000 | 11 | 19 | 7.75229e-06 | 1.51055 | 1.97463 | nein | nein |
| 16 | 20261106 | A200 | 11 | 20 | 0.000717745 | 0.10289 | 0.0913963 | nein | nein |
| 17 | 20261107 | K200 | 10 | 19 | 1.23051e-05 | 0.012192 | 0.0221694 | nein | nein |
| 18 | 20261107 | A200 | 6 | 14 | 0.0374674 | 0.846736 | 1.11303 | nein | nein |
| 19 | 20261107 | A2000 | 12 | 20 | 3.5583e-05 | 0.0225441 | 0.0258014 | nein | nein |
| 20 | 20261107 | K2000 | 6 | 13 | 3.72174e-25 | 2.40427e-12 | 1.27037e-12 | ja | ja |

## Aufwand

Aufgezeichnete Gesamtdauer: **2.576,5844 Sekunden = 42 Minuten 56,6 Sekunden**.
Alle Worker blieben unter 600 Sekunden, die Gesamtserie unter 7.200 Sekunden.
Die längste Workerzeit betrug 229,76 Sekunden. Die folgenden Fitzeiten umfassen
JIT und Pythonexporte; sie sind keine isolierte reine Optimiererzeit.

| Gruppe | Median Workerzeit (s) | Median Fit einschließlich JIT/Export (s) |
| --- | ---: | ---: |
| K200 | 57.48 | 43.75 |
| K2000 | 202.98 | 189.26 |
| A200 | 56.80 | 42.12 |
| A2000 | 182.42 | 167.92 |

Über die fünf Seeds steigt die aufsummierte Fitzeit bei K um Faktor 4,29,
bei A um Faktor 4,19. Zehnfaches Iterationsbudget bedeutet hier keinen
zehnfachen gemessenen Laufzeitbedarf. Diese Zahlen gelten für diesen Rechner,
diese Serie und das gespeicherte Profil.

## Einordnung und nächster abgegrenzter Schritt

Die Suchbudgethypothese erhält für K ein positives Entwicklungssignal; bei A
ist ein zusätzlicher Approximationserfolg belegt. Die Trainings-MSE sinkt in
allen zehn Budgetpaaren, während der Gegenfall die Grenze dieser Kennzahl
zeigt. Datenrollen und Originalauswahl werden deshalb beibehalten.

Als nächster wissenschaftlicher Schritt ist ein vor Ausführung festgelegter
Übertragbarkeitsvergleich plausibel: 2.000 Iterationen ohne Einschränkung als
Referenzprofil, neue Ringdown-Parameter beziehungsweise bislang ungenutzte
Signale und Seeds. Den Beitrag der Grammatik gegebenenfalls als ausdrücklich
geplanten Vergleich erhalten. Umfang und Erfolgskriterien sind separat zu
beschließen; dieser Audit startet keine weiteren Suchen und gibt noch keinen
Hauptversuch frei. Rauschen/Kovarianz und physikalische Identifikation bleiben
weiterführende Fragen des Exposés; `physical_identification=not_assessed` und
der bekannte Blindfleck bei `8*fs` gelten weiter.

**Vorgemerkte Bereinigung:** Der erste vollständig verifizierte Manjaro-
Suchbudgetlauf liegt jetzt vor. Damit ist die vereinbarte Erinnerung an eine
kurze Bestandsaufnahme fällig. Zuerst den gemergten funktionierenden Stand und
das Originalarchiv erhalten. Danach insbesondere Startweg/Dokumentation und
konkrete Wartungsprobleme prüfen; kleine getrennte Änderungen mit Regressionen,
keine große Umstrukturierung. Dieser Ergebnis-PR enthält keine solche
Bereinigung und verändert keine numerischen Abläufe oder eingefrorenen Pläne.

## Unveränderte Originalformeln

Die Nummern entsprechen den Zellen oben; jede Formel ist die Originalauswahl.

Zelle 1:

```text
exp(t / -0.008000000009977283) * cos((t - (t / -0.0328867249154902)) / 0.019994575725712928)
```

Zelle 2:

```text
sin(-4.712388980450938 - (t * (-1570.7963268522046 - (exp(6.6973862774116135) * -6.074624908528927e-11)))) / exp((t / 0.48117299821573994) / exp(-4.0967853274029915))
```

Zelle 3:

```text
(cos(1570.7963267938976 * t) / exp((-94.35549074627235 / -0.44057063457947815) * (t / 1.1907848543182866))) / exp(-54.85326608196708 * t)
```

Zelle 4:

```text
exp((cos(-1570.7963267948908) / exp(-0.39263073459482656)) * (t * -84.40975729726254)) * cos(t * -1570.7963267948908)
```

Zelle 5:

```text
sin((-3429.0483686960683 / exp((t * t) * 0.10406003014140547)) / exp(-0.45808120610782677 * t)) / exp(125.00023820748076 * t)
```

Zelle 6:

```text
sin((-2.7671188479105857 + (((t / -0.1331995874437985) / -0.20062638129543933) / 0.14875581548189756)) / 0.16014568828336667) / exp((t / 0.033630271745454306) / 0.2378809213034649)
```

Zelle 7:

```text
sin((cos(-0.030009222073968618) + ((t / -0.03001351349826552) + (t / -0.03001351349826552))) / -0.04242220916891194) / exp(t / 0.008000000261752708)
```

Zelle 8:

```text
cos(1.0767229495410593 * (t * -1458.8676942981317)) / exp(t * 124.99999999972752)
```

Zelle 9:

```text
(exp(-124.99999999990357 * t) + (-4.6742283778426116e-14 + -4.6742283778426116e-14)) * sin((-1570.7963267948824 * ((5.89738514924591e-15 * cos(1.1978405976255935)) + t)) - -1.5707963267982192)
```

Zelle 10:

```text
sin(-1.571232596992353 + (-1570.7640717173674 * t)) / (((-16309.840847187283 * t) + (sin(-19.71673725873464 * t) * -819.7932260081283)) + -0.9929180757583871)
```

Zelle 11:

```text
sin((552.2266490109407 / (t + 1.0664332103522876)) / -0.30494828818184677) / ((t + (t + 0.0270167753151191)) / (-0.025415828069594606 + t))
```

Zelle 12:

```text
sin(((2734.4832224352103 - -0.005277635288882934) * (t * -0.5744388125035539)) + (2.2455683956887063 - 0.6747720688984451)) * exp(t * -125.00000000308584)
```

Zelle 13:

```text
cos((t * (-9.708503718116267e-10 - -1570.7963267970426)) + (-9.708503718116267e-10 * (t * exp(0.257469321555762)))) * exp(t * -124.9999999987608)
```

Zelle 14:

```text
((cos(-0.3832222309117765) + sin(t / -0.026218930803700934)) * cos(1570.7710810980707 * t)) * (cos(-5.994762350172354e-8) + sin(t / -0.021598133291131097))
```

Zelle 15:

```text
cos(t * -49901.07304232362) * (sin((((3666.1864443176282 + (t * -48955.146960374936)) * t) + -110.11385228887835) * t) + 0.9882218581433504)
```

Zelle 16:

```text
(1485.2565116819262 * ((t - 0.024628504414133893) * (t - 0.024628391291237936))) * (0.006701935759577351 - sin(((t - -0.9738900327001593) * 32.159560836142134) * 48.899124683599844))
```

Zelle 17:

```text
cos(1570.7688882010425 * t) * sin((4.200294943169606 * (t + -0.042797770330687865)) * ((t + -0.04279783263473992) / (t - -0.005691002168999588)))
```

Zelle 18:

```text
0.8052974286537535 * (0.028631487804933776 + sin(0.0012327614746280309 / (0.0008645651159642985 - ((t * 702.9470562333001) * t))))
```

Zelle 19:

```text
sin(-229618.42878107843 / (12.097957515156514 - t)) * ((57487.50227623483 * (0.0005432975877654539 - ((0.04086031790638435 - t) * t))) * (0.03117680477122909 - t))
```

Zelle 20:

```text
cos(1570.7963267946689 * t) * exp((0.5244153001345051 - 66.10628457253976) * (t / 0.524654954177711))
```
