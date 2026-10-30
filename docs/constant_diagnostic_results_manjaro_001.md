# Ringdown-Konstantendiagnose auf Manjaro: Ergebnis 001

Ausführung und unabhängige Nachrechnung vom 30.10.2026. Die 48 geplanten
Backendaufrufe sind abgeschlossen; die archivierte Abschlussprüfung ist
bestanden. Das übermittelte Originalarchiv wurde vollständig nachgerechnet.

**Befund:** Unter 20 Iterationen mit zwei zusätzlichen Neustarts besteht keiner
der 24 ausgewählten Fits die festen Kurvengrenzen; unter 100 Iterationen mit
denselben Neustarts bestehen alle 24. Das gilt für wahrheitsnahe und entfernte
Starts. Parameterbefunde wechseln durchgehend von `mismatched` zu `matched`.
Die vorgegebene Struktur und das deklarierte Startgitter bleiben privilegierte
Diagnosebedingungen; freie Strukturentdeckung und Übertragbarkeit sind offen.

## Quelle, Stand und Umfang

- Originalarchiv `constant-manjaro-001.tar.gz`, 2.418.382 Bytes. Tatsächliche
  SHA-256 vor dem Entpacken gegen die übermittelte Prüfsumme bestätigt:
  `346459d953468c81975670577b92aa155a1eaec884cebd462fe61e1ab23d492b`.
- Aufgezeichneter sauberer Ausführungscommit:
  `0a70f19e16e173aedf2e071a5f5b09d045ecbf69`, Merge von
  [PR #42](https://github.com/craexxn/ringdown-sr/pull/42).
  Die konsumierten Quellen entsprechen dem technisch geprüften PR-Head
  `9202d20374c7a075c1328cadb221ac3185ec698a`; zusätzlich sind Sprachregeln
  in `AGENTS.md` übernommen. [Vollständige CI am Implementierungshead](https://github.com/craexxn/ringdown-sr/actions/runs/41062609710).
- 311 Archiveinträge, davon 259 reguläre Dateien; 258 Dateien im abschließenden
  Prüfsummenmanifest, das Manifest selbst als 259. Datei erhalten.
- Serienstatus `completed`, 48 Aufrufe `completed`, `final_verification=passed`.
  Zehn feste Kontrollen, 144 beobachtete lokale Optimierungen, 24 Paare.
- Aufgezeichnete Zeit: 13:55:28 bis 14:15:32 UTC, entsprechend 14:55:28 bis
  15:15:32 Europe/Vienna; 1.203,061 Sekunden Gesamtwandzeit, etwa 20 Minuten.
- Die archivierten Python-/Paketaufnahmen melden Python 3.12.14, PySR 2.6.0
  und JuliaCall 0.9.36. Julia 1.13.1 und SymbolicRegression 2.5.1 werden durch
  die geprüften Pins und den versionsprüfenden Workerstart verlangt; sie wurden
  für diesen lesenden Audit nicht neu gestartet. Vor-/Nachaufnahmen der
  geladenen NumPy-, SciPy- und Julia-BLAS-Pools bestätigen Haswell und Limit 1.

Prüfsummen und Metadaten belegen Paketkonsistenz; sie sind keine externe
Authentifizierung von Gerät, tatsächlicher Ausführung oder Zufallszuständen.
Archivierte native Nachweise und hier neu ausgeführte Nachrechnungen bleiben
getrennte Belegarten.

## Eingefrorene Vorgaben

Der [angenommene Methodenplan](constant_diagnostic_plan.md) ist unverändert,
SHA-256 `5d546f1804da17239bfae33c1d3f3732f46582dc6cf96a4c3b850dda5be9861b`.
Die beiden älteren Kontrollpläne bleiben ebenfalls unverändert.

Ein Baum `A * (exp(b*t) * cos(c*t + phi))`, 13 Knoten und vier freie Konstanten.
Acht deklarierte Starts L1–L4 beziehungsweise R1–R4, drei bekannte Seedkennungen
20261020/21/22, 20 beziehungsweise 100 Iterationen, je zwei zusätzliche
Neustarts. Frische Prozesse, Xoshiro mit festgelegter PySR-Seedabbildung,
abwechselnde Reihenfolge innerhalb der Paare. Float64, Sekunden, gewöhnliche
MSE, BFGS mit Backtracking und numerischer Differentiation. Beide
Häufigkeitsschalter aus; freies Suchbudget null.

Die unveränderten 128 Trainingswerte und 889 inneren Achtelpunkte stammen
binär aus dem bereits geprüften Originalarchiv der
[Zeitdarstellungskontrolle](representation_control_results_manjaro_001.md).
Diagnosepunkte und Wahrheit werden ausschließlich nachgelagert verwendet.
Die Auswahl bleibt die ursprüngliche Backendwahl anhand des Trainingsverlusts.
Auf beiden Rastern gelten weiterhin `relative_rms <= 0,001` und
`relative_max <= 0,01`.

## Gruppenbefund

Alle Nenner betragen zwölf. RMS und Maximalfehler beziehen sich in dieser
Tabelle auf die Zwischenpunkte; die positiven Kurvenmarker verlangen beide Raster.

| Startgruppe | Iterationen | Kurvenmarker bestanden | Parameter `matched` | Median Trainings-MSE | Median relativer RMS | Median relativer Maximalfehler |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Wahrheitsnah | 20 | 0/12 | 0/12 | 0.000140378356 | 0.0439739607 | 0.0293339366 |
| Wahrheitsnah | 100 | 12/12 | 12/12 | 7.03028837e-19 | 3.21894217e-09 | 2.13055252e-09 |
| Entfernt | 20 | 0/12 | 0/12 | 0.0613990875 | 0.95337134 | 0.912831414 |
| Entfernt | 100 | 12/12 | 12/12 | 1.48872318e-18 | 4.46187521e-09 | 4.39836385e-09 |

Unter 100/2 liegt die Trainings-MSE zwischen `4,8783e-20` und `3,9808e-17`.
Der größte relative Zwischenpunkte-RMS beträgt `2,4593e-8`, der größte relative
Maximalfehler `2,7924e-8`. Sämtliche 24 Paardifferenzen der Trainings-MSE
(100 minus 20) sind negativ; ebenso sämtliche RMS-/Maximalfehlerdifferenzen
beider Raster. Es erfolgt keine Auswahl günstiger Seeds.

Alle 48 rohen und aliasbezogenen Parameterreplays bestehen. Unter 100/2 beträgt
der größte relative Frequenzfehler `2,2101e-9`, der größte relative
Abklingzeitfehler `2,1649e-8`. Fünf Rückgabebäume haben negative Amplitude und
Phase nahe π; diese äquivalente Darstellung bleibt im Original erhalten.
Der komplexe Amplitudenvergleich berücksichtigt das Vorzeichen korrekt.
`physical_identification` bleibt in allen 48 Fällen `not_assessed`.

## Alle 24 Paare

Je Zeile sind beide ursprünglichen Ergebnisse erhalten. Die Fehler sind
relative RMS-Werte auf Zwischenpunkten; vollständige Bäume, rohe Parameter,
Replays, Gradienten und alle Fehlerdifferenzen stehen im Originalarchiv.

| Start | Seed | MSE 20/2 | MSE 100/2 | RMS 20/2 | RMS 100/2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| L1 | 20261020 | 0.000247895921 | 3.98079805e-17 | 0.0619504106 | 2.45929282e-08 |
| L1 | 20261021 | 0.000247895921 | 1.00313901e-19 | 0.0619504106 | 1.24818399e-09 |
| L1 | 20261022 | 0.000225441045 | 2.33169713e-19 | 0.0589618938 | 1.9030123e-09 |
| L2 | 20261020 | 0.000227456213 | 4.13636461e-19 | 0.0592075863 | 2.53150116e-09 |
| L2 | 20261021 | 0.000227456213 | 4.13636461e-19 | 0.0592075863 | 2.53150116e-09 |
| L2 | 20261022 | 0.000227456213 | 4.13636461e-19 | 0.0592075863 | 2.53150116e-09 |
| L3 | 20261020 | 3.91005246e-06 | 9.933011e-18 | 0.00756053658 | 1.23984626e-08 |
| L3 | 20261021 | 3.91005246e-06 | 9.933011e-18 | 0.00756053658 | 1.23984626e-08 |
| L3 | 20261022 | 3.91005246e-06 | 9.92421213e-19 | 0.00756053658 | 3.90638317e-09 |
| L4 | 20261020 | 5.53156676e-05 | 4.87828784e-20 | 0.0289860275 | 8.58692579e-10 |
| L4 | 20261021 | 5.53156676e-05 | 9.31915579e-18 | 0.0289860275 | 1.13682226e-08 |
| L4 | 20261022 | 5.53156676e-05 | 3.28807833e-17 | 0.0289860275 | 2.215953e-08 |
| R1 | 20261020 | 0.0511212035 | 9.86341913e-18 | 0.886473068 | 1.22429712e-08 |
| R1 | 20261021 | 0.014663583 | 2.16640017e-18 | 0.474954564 | 5.54938297e-09 |
| R1 | 20261022 | 0.0243733938 | 9.93786211e-20 | 0.597872207 | 1.24253827e-09 |
| R2 | 20261020 | 0.0645824311 | 8.40492295e-20 | 0.976486276 | 1.13259522e-09 |
| R2 | 20261021 | 0.0199842687 | 6.08721757e-18 | 0.556893804 | 9.61444648e-09 |
| R2 | 20261022 | 0.00785466849 | 8.11046194e-19 | 0.347329607 | 3.37436745e-09 |
| R3 | 20261020 | 0.0627681296 | 2.6687045e-17 | 0.962546223 | 2.03208309e-08 |
| R3 | 20261021 | 0.0627681296 | 2.08861382e-17 | 0.962546223 | 1.80012446e-08 |
| R3 | 20261022 | 0.0600300454 | 3.04044581e-18 | 0.944196456 | 6.86762881e-09 |
| R4 | 20261020 | 0.0668711962 | 1.41386323e-19 | 0.990214857 | 1.47079799e-09 |
| R4 | 20261021 | 0.0668711962 | 1.41386323e-19 | 0.990214857 | 1.47079799e-09 |
| R4 | 20261022 | 0.0660931652 | 1.41386323e-19 | 0.985533108 | 1.47079799e-09 |

## Beobachtete Optimiererverläufe und Aufwand

Für alle 72 gepaarten lokalen Optimierungen stimmen die Zustände der Schritte
0 bis 20 exakt überein: Parameter, Verlust und numerischer Gradient. Unter 20/2
endet jede lokale Zustandsfolge nach Schritt 20. Unter 100/2 werden dieselben
Anfangsverläufe fortgesetzt. Die gewählten Schlusszustände liegen dort bei
beobachteten Schritten 42 bis 89; sieben andere lokale Verläufe reichen bis 100.

Die ursprünglichen Rückgabebäume stimmen in allen 48 Fällen mit dem vom
Backend gewählten Minimum der beobachteten lokalen Schlusszustände überein.
Diese Prüfung ersetzt oder verändert keine Auswahl. Ein expliziter
Konvergenz-/Abbruchstatus wird vom Backendpfad nicht zurückgegeben und bleibt
`unavailable`. Beobachtete Schritte sind kein nachträglich erzeugtes Solverflag.

| Profil | Fit-Callbackaufrufe | Backend-Evaluationszähler | Native Optimiererzeit | Workerwandzeit |
| --- | ---: | ---: | ---: | ---: |
| 20/2 | 13733 | 1541 | 222.420 s | 584.304 s |
| 100/2 | 46044 | 5996 | 222.615 s | 589.514 s |

Die Callbackzahlen steigen etwa um Faktor 3,35. Die aufgezeichneten nativen
Zeiten sind dagegen fast gleich. JIT und Prozess-/Exportkosten sind enthalten
beziehungsweise gesondert in der Workerwandzeit sichtbar; diese einzelne Serie
ist kein replizierter Laufzeitbenchmark. Iterationen, Backend-Evaluationszähler
und tatsächliche Callbackzahlen sind verschiedene Größen. Die Gesamtzähler
enthalten zusätzlich je Aufruf zwei Auswertungen außerhalb der Optimierung.
Keine Zahl beschreibt die Anzahl verschiedener freier Suchbäume.

## Selbst ausgeführter lesender Audit

- Archivhash vor Entpacken bestätigt; Einträge auf reguläre Dateien/Verzeichnisse,
  sichere relative Namen, Duplikate und Umfang geprüft. Keine Archivquelle importiert.
- Alle 258 Manifestprüfsummen mit vollständiger Dateiabdeckung bestätigt;
  alle 47 konsumierten Quell-/Pin-/Planhashes gegen den sauberen Ausführungscommit
  und den vertrauenswürdigen Checkout verglichen. Laufzeitkopien bytegleich.
- Sämtliche 50 Workermanifeste, Trainingsdaten und Anfragen, die festgelegte
  Reihenfolge, Seeds, Xoshiro-Zustände und Restartvektoren nachgeprüft.
- Alle 68 Optionsfelder und konkreten Pluginfelder pro Snapshot geprüft.
  Zusätzlich absolute Sollprüfung gegen die bereits unabhängig auditierte
  native Baselinevorprüfung des ursprünglichen Eingabearchivs. Erlaubte
  Wrapper-/Iterationsunterschiede und sämtliche Optimierereinstellungen explizit geprüft.
- Zehn feste Referenzen einschließlich Einheiten- und Aliasfälle sowie 100
  gespeicherte Vor-/Nachaufnahmen der tatsächlich geladenen BLAS-Pools geprüft.
- Alle 48 Rückgabebäume mit eigenem NumPy-Whitelistinterpreter ausgewertet;
  native Residuen bitweise und MSE mit `math.fsum` nachgerechnet. Beide
  Kurvenraster, Parameterfehler und alle Gruppen-/Paardifferenzen reproduziert.
  Die bestehenden Diagnosen zusätzlich mit dem vertrauenswürdigen Erkenner
  reproduziert; dies ist keine neue unabhängige allgemeine Strukturerkennung.
- Alle 6.506 beobachteten Zustände aus 144 lokalen Optimierungen anhand ihrer
  vier Konstanten nachgerechnet. Die größte Differenz der unabhängig
  berechneten RMS-Residuen zum archivierten Zustandsverlust beträgt `5,5512e-17`;
  sie liegt innerhalb der expliziten Float64-Rundungsgrenze des Audits.
- Die 72 identischen Anfangsverläufe und die ursprünglichen 48 Auswahlen
  unabhängig kontrolliert. Alle 259 Originaldateihashes abschließend unverändert.

Der Audit startet weder Julia noch Fit, Optimierung oder freie Suche. Native
Objekte werden aus den gespeicherten strukturierten Aufnahmen geprüft; ihre
Konstruktion wird hier nicht wiederholt. Neue technische CI oder ein weiteres
Implementierungsreview sind für diesen reinen Ergebnisnachtrag nicht erforderlich.

Lokale, nicht versionierte Auditdateien: `results/constant-audit-001/audit.py`,
`audit.json` sowie `diagnostic_rms.png` und `diagnostic_rms.svg` im selben Ordner.
Das Originalarchiv bleibt separat unter `results/constant-manjaro-001.tar.gz`
gesichert. Eingefrorene Vorgaben und wissenschaftliche Originaldateien wurden
nicht geändert.

## Methodische Einordnung und nächste Entscheidung

**Belegt:** Das größere Optimiererbudget verbessert die Anpassung für sämtliche
24 deklarierten Start-/Seedpaare und erreicht die festen Kurven- und Parameter-
ziele. Der Backendpfad kann diesen nichtlinearen Ringdown bei gegebener
Struktur anpassen. Das Profil 20/2 reicht für diese konkreten Fälle nicht aus.

**Offen:** Welche Strukturen und Konstantenstarts die freie Suche tatsächlich
erzeugt, optimiert und erhält. Der Befund identifiziert keinen allgemeinen
Optimiererdefekt und erklärt die historische Suchstagnation nicht vollständig.
Die acht bekannten Starts, drei Entwicklungsseeds und das eine bekannte Signal
sind keine unabhängige Leistungsvalidierung oder Einzugsgebietsschätzung.

Eine begrenzte freie Budgetintervention ist jetzt als nächste Prüfidee begründet.
Dafür sind Suchprofil, Vergleichsbedingungen, Seeds, Suchbudget, Aufwand und
Entscheidungsregeln vorab in einem eigenen Methodenplan festzulegen. Weder das
Produktionsprofil noch ein neuer Lauf sind durch diesen Befund automatisch
freigegeben. Ein Gewichtungs-/Rauschvergleich benötigt weiterhin ein geeignetes
Gate für den ausdrücklich gewählten Forschungsanspruch. Der Alias-Blindfleck
bei `8*fs` bleibt ausdrücklich bestehen.
