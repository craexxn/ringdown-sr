# Ergebnis: begrenzter Signaltransfer bei 500/300/5

Stand: 05.11.2026. Alle **18 frischen Manjaro-Zellen und 198 Originalkandidaten**
sind vollständig archiviert und unabhängig nachgerechnet. Die sechs Gruppen
erreichen jeweils zwischen 0/3 und 2/3 Kurvenerfolgen. **Bereits der frische
bekannte Referenzfall erreicht 0/3**, obwohl die frühere äußere Staffel bei
500 Iterationen mit fünf anderen Seeds 5/5 erreichte. Die frühere Beobachtung
überträgt sich somit nicht auf diese neue Seedgruppe. Das Profil 500/300/5
ist kein belegtes robustes Rekonstruktionsprofil oder allgemeines Optimum.

Die Signalvarianten liefern einzelne erfolgreiche Rekonstruktionen, ohne
belastbaren Nachweis allgemeiner Übertragbarkeit. Drei kurvengenaue
Originalauswahlen bleiben formal ungestützt; eine getrennte nachträgliche
algebraische Diagnose erklärt die Schreibweisen und eine Definitionsgrenze.
Kurvengüte, planmäßige Strukturwertung und Parameterbefund bleiben getrennt.
Keine gemeinsame Erfolgsquote über die sechs unterschiedlichen Signale.

## Herkunft und selbst ausgeführte Nachrechnung

Originalarchiv `transfer-manjaro-001.tar.gz`, übermittelter und selbst
bestätigter SHA-256:
`e363fe1be629973a460fc6e2188bf680c21b2c5519d331bc7e257968dcaaa139`.
Sauberer Ausführungscommit `bc4025d13b4954dee779341026d282430521686a`,
Squash-Merge von [PR #65](https://github.com/craexxn/ringdown-sr/pull/65).
Sein Dateibaum `13a82d69adb6877c22a7d96ffa72a96d5c003b54` entspricht exakt
dem geprüften Head `92b96ecea46191fa879244fb9497db900340afd5`.

Die erfolgreiche [Implementierungs-CI 41893653816](https://github.com/craexxn/ringdown-sr/actions/runs/41893653816)
und das im PR dokumentierte übermittelte KI-basierte Review beziehen sich
auf diesen Head. Die 2.394 Python-Tests und Julia-/Integrationsprüfungen sind
frühere CI-Nachweise; die zusätzlichen 127 Tests, 6.102 Signalwerte und
24 Alias-/Phasengegenfälle sind übermittelte Reviewnachweise. Diese Prüfungen
wurden für den Ergebnisnachtrag nicht als eigene Tests wiederholt.

Der [vor Code eingefrorene Plan](transfer_check_plan.md) bleibt unverändert:
Commit `446afbfea8958f409693c2253f8d9d4950f24e45`, SHA-256
`f29561b8151a2a4e17cd881a8c4576f406f0efd340309ac54fcbbde2faabb6f3`.
Alle Eingangsdaten liegen im Repository; kein früheres Ergebnisarchiv nötig.
Die folgenden Prüfungen wurden für das neue Originalarchiv selbst ausgeführt:

- 493 Originaldateien, 492 Abschlussmanifest-Einträge, 490 ursprüngliche
  Verbrauchsanker und 94 gebundene Quellen geprüft. Quellen gegen
  Ausführungscommit und vertrauenswürdigen Checkout verglichen; Runtimekopien,
  Planbytes, saubere Herkunft, Float64-Datenbits und getrennte Datenrollen stimmen.
- Alle 18 Zellidentitäten und ihre Reihenfolge bestätigt: sechs Signale,
  drei gepaarte Seeds 20261210–20261212, fest 500 äußere Iterationen und
  lokale Optimierung 300/5, unrestricted, `should_simplify=false`.
  Native Optionsbelege, Plugins, Vorprüfungen und genau ein tatsächlicher
  Suchaufruf je Zelle ohne Warmstart stimmen.
- Alle 198 Kandidaten im vorhandenen Elternprüfpfad nachgerechnet:
  Verlust- und Rundungsnachweise, Residuen, Originalauswahl, Kurven-, Struktur-
  und Parameterdiagnosen stimmen. Sämtliche MPFR-Vorhersagereferenzen bei 128 Bit.
- Alle CSV-Ausdrücke mit beschränktem Syntaxparser gegen die Originalbäume,
  Reihenfolge, Komplexitäten und Verluste geprüft. Eine unabhängige skalare
  Baumrekursion bestätigt alle Kurvenmarker auf beiden Rastern:
  201.366 Punktwerte; größte absolute Abweichung einer daraus berechneten
  Kurvenkennzahl gegenüber dem Bericht rund 2,22e-16.
- Alle 198 Originalbäume mit Julia 1.13.1 / SymbolicRegression 2.5.1 nativ
  nachgerechnet: Vorhersagen sowie Original-/Replayverluste bitgleich,
  Baumrundreise, Grammatik und Komplexität bestätigt; null Zielfunktionscallbacks.
- Gruppenstatistiken, fünf Kontraste und alle 15 Seedpaare reproduziert;
  Auswahlregel, C/S, Übergänge, Kostenunterschiede/-verhältnisse und die vier
  positiven Parameterbefunde zusätzlich unabhängig nachgerechnet.
  `report.json` und `summary.md` aus dem geprüften Bericht bytegleich neu erzeugt.

Keine Archivprogramme oder serialisierten Suchzustände ausgeführt; keine
Suche, Optimierung oder Nachfits. Alle Originaldateien blieben unverändert.
Eigene Nachweise liegen unter `/workspace/audits/transfer-manjaro-001/`:
`original_sha256.json`, `audit.json`, `native_replay.json`,
`independent_summary.json`, `algebraic_diagnostic.json` sowie eigene Skripte
und Logs. Die Nachrechnung prüft diesen gespeicherten Lauf und erweitert
die Stichprobe nicht.

## Festgelegte Endpunkte und Signalgruppen

Alle Signale folgen A exp(−t/tau) cos(2πft+phi), ohne Rauschen. 128 Trainingspunkte
bei 4.096 Hz und 889 getrennte innere Achtelpunkte; keine Extrapolationsprüfung.
C zählt die ursprünglichen Auswahlen, deren relativer RMS auf beiden Rastern
≤ 0,001 und relativer Maximalfehler jeweils ≤ 0,01 ist. S verlangt zusätzlich
beim selben Kandidaten erkannte Struktur, passende Parameter und beide Replays.
Die Auswahl erfolgt allein nach nativer Trainings-MSE, dann Komplexität und
ursprünglicher Position; keine diagnostische Neuauswahl.

| Signal | C | S | Gute ungewählte Kandidaten | Median relativer RMS, Zwischenpunkte | Größter relativer RMS, Zwischenpunkte |
| --- | --- | --- | --- | --- | --- |
| anchor | 0/3 | 0/3 | 0 | 0,07303252 | 0,1019851 |
| frequency | 1/3 | 1/3 | 1 | 0,02171667 | 0,03874506 |
| decay | 1/3 | 1/3 | 3 | 0,007761667 | 0,02865651 |
| phase | 2/3 | 1/3 | 6 | 1,659968e-09 | 0,07232215 |
| amplitude | 1/3 | 0/3 | 3 | 0,007134059 | 0,03633361 |
| combined | 2/3 | 1/3 | 3 | 2,604097e-11 | 0,00280142 |

Der bekannte Referenzfall scheitert bei allen drei neuen Seeds auch auf dem
Trainingsraster. Unter seinen ungewählten Kandidaten befindet sich ebenfalls
kein Kurvenerfolg. Der Befund lässt sich deshalb nicht allein durch eine
ungünstige Originalauswahl erklären. Die Zwischenpunkt-RMS-Werte des Referenzfalls
liegen rund 17,5- bis 102-mal über der festen RMS-Grenze.

Die frühere [äußere Staffel](outer_search_ladder_results_manjaro_001.md) nutzte
andere Seeds. Ihr 5/5-Ergebnis und das neue 0/3 sind kein gepaarter
Implementierungsvergleich und kein Nachweis einer Codeverschlechterung.
Die drei aktuellen Wiederholungen je Signal erlauben weder eine belastbare
Erfolgswahrscheinlichkeit noch eine Rangfolge der Signalbedingungen.
Gleiche Seedkennungen bei anderen Daten erzeugen keine identischen Suchverläufe.

S = planmäßig vollständig unterstützt; K = Kurvenerfolg ohne diese formale
Unterstützung; – = Kurvenkriterien nicht erfüllt.

| Seed | anchor | frequency | decay | phase | amplitude | combined |
| --- | --- | --- | --- | --- | --- | --- |
| 20261210 | – | – | – | K | K | S |
| 20261211 | – | – | S | S | – | K |
| 20261212 | – | S | – | – | – | – |

## Alle fünf vorab festgelegten Referenzkontraste

Jede Variante wird mit anchor beim selben Seed verglichen, insgesamt
15 Paaraufzeichnungen. Die anchor-Zellen werden in fünf Kontrasten wiederverwendet;
dies sind keine 15 unabhängigen Wiederholungen. Übergänge stehen in der
Reihenfolge 0→0 / 0→1 / 1→0 / 1→1.

| Variante − anchor | Delta C | Delta S | C-Übergänge | S-Übergänge |
| --- | --- | --- | --- | --- |
| frequency | 1 | 1 | 2 / 1 / 0 / 0 | 2 / 1 / 0 / 0 |
| decay | 1 | 1 | 2 / 1 / 0 / 0 | 2 / 1 / 0 / 0 |
| phase | 2 | 1 | 1 / 2 / 0 / 0 | 2 / 1 / 0 / 0 |
| amplitude | 1 | 0 | 2 / 1 / 0 / 0 | 3 / 0 / 0 / 0 |
| combined | 2 | 1 | 1 / 2 / 0 / 0 | 2 / 1 / 0 / 0 |

Die positiven Differenzen entstehen gegenüber einer Referenzgruppe ohne
Kurvenerfolg. Sie belegen keine allgemeine Erleichterung durch Signaländerung
oder Überlegenheit einer Variante. Alle drei Paare je Kontrast einschließlich
der erfolglosen Vergleiche bleiben erhalten. Weil die anchor-Parameter überall
`not_assessed` sind, bleiben die Parameterdifferenzen aller 15 Paare ebenfalls
`not_assessed`; es gibt keine nachträgliche Ersetzung durch Signalwahrheiten.

## Struktur und Parameter getrennt

Die Originalauswahlen in Zellen 6 (combined), 7 (decay), 8 (phase) und
16 (frequency) erfüllen die vorab festgelegten Struktur- und Parametergates.
Die relativen Fehler beziehen sich jeweils auf die Wahrheit der betreffenden
Signalbedingung; die komplexe Amplitude berücksichtigt Phase und Vorzeichen.

| Zelle | Frequenz relativ | Abklingzeit relativ | Amplitude relativ | Komplexe Amplitude relativ |
| --- | --- | --- | --- | --- |
| 6 | 1,996151e-12 | 3,499429e-11 | 2,089865e-11 | 3,679226e-11 |
| 7 | 1,248281e-12 | 5,13695e-13 | 0 | 0 |
| 8 | 2,090758e-10 | 4,817936e-10 | 0 | 1,985771e-09 |
| 16 | 9,651113e-14 | 3,864964e-12 | 0 | 0 |

Alle anderen ursprünglichen Auswahlen erhalten formal `not_supported` und
Parameterstatus `not_assessed`, nicht `mismatched`. Drei davon sind dennoch
kurvengenau. Ein fehlender Strukturnachweis allein belegt keine falsche
physikalische Struktur. Physikalische Identifikation bleibt überall
`not_assessed`, der 8·fs-Blindfleck des Rasters bleibt bestehen.

## Getrennte nachträgliche algebraische Diagnose

Dieser Zusatz wurde erst nach Sichtung der Ergebnisse vorgenommen. Er
verändert weder Originalauswahl, S-Zählungen, Parameterstatus noch den
Strukturerkenner. Betrachtet werden die reellen Funktionen der Originalbäume;
die maßgebliche Float64-Knotenrundung bleibt davon getrennt.

- **Zelle 4, phase:** `unsupported_affine_operator`. Der Sinus eines konstanten
  Arguments im Exponentialfaktor ist selbst konstant. Zusammenfassen der
  konstanten Faktoren ergibt einen linearen Exponenten und eine affine
  Kosinusphase, also reell eine Ringdown-Form auf ganz R.
- **Zelle 5, amplitude:** `trigonometric_denominator`. Die Form
  `K / (exp(b*t) / cos(omega*t))` ist auf ihrem Definitionsbereich gleich
  `K*exp(-b*t)*cos(omega*t)`. An den Kosinusnullstellen hat der Originalquotient
  jedoch Definitionslücken. Die Ringdown-Form ist dort eine stetige Fortsetzung,
  keine globale Gleichheit der Definitionsbereiche. Auf den gespeicherten
  Rastern werden diese Stellen nicht getroffen; die Originalform bleibt erhalten.
- **Zelle 10, combined:** `nonzero_exponential_intercept`.
  `exp(a-b*t)=exp(a)*exp(-b*t)` verschiebt den konstanten Exponenten in die
  Amplitude. Mit `sin(x)=cos(x-pi/2)` und Vorzeichenumrechnung ergibt sich
  reell eine Ringdown-Form auf ganz R.

Die Koeffizienten wurden ausdrücklich aus den jeweiligen Originalformeln
abgeleitet, ohne Fit oder Wahl anhand der Signalwahrheit. Konstanten gehen mit
ihren exakten gespeicherten Binary64-Werten ein. Die unabhängige Rechnung bei
80 und 120 Dezimalstellen vergleicht alle 1.017 vorhandenen Zeitpunkte für
alle drei Fälle: **6.102 Punktvergleiche**, maximale absolute Abweichung
rund 2,24e-81 beziehungsweise 2,36e-121. Dies behauptet weder eine bitgleiche
Float64-Auswertung nach Umformung noch einen nachträglich bestandenen
formalen Parameter-/Aliasvertrag.

Reelle Form A exp(−t/tau) cos(2πft+phi), bei Zelle 5 mit der genannten
Definitionsbereichseinschränkung:

| Zelle | A | f / Hz | tau / s | phi / rad |
| --- | --- | --- | --- | --- |
| 4 | 1 | 249,9999999997373 | 0,008000000000013715 | 0,7000000000134255 |
| 5 | 0,4000000000003262 | 250,0000000000201 | 0,007999999999985937 | 0 |
| 10 | 0,59999999998998 | 179,999999999839 | 0,01200000000043161 | -0,8999999999853426 |

Die Erkennungsabdeckung und der Umgang mit solchen Definitionslücken müssen
vor Nutzung von S als Strukturstabilitätsmaß im Piloten ausdrücklich festgelegt
werden. Eine automatische Erkennererweiterung folgt daraus nicht.

## Gemessener Aufwand

Aufgezeichnete Gesamtdauer **3.019,784255878 Sekunden = 50 min 19,784 s**.
Zeitstempel: 05.11.2026, 06:12:30,306 bis 07:02:50,003 MEZ (UTC+1).
Alle Worker bleiben unter 900 Sekunden, die gesamte Serie unter 7.200 Sekunden.
Der längste Zellabschnitt einschließlich Elternverifikation dauert rund
193,44 Sekunden.

Zellzeit umfasst Armaufruf und Elternverifikation. Das Feld
`status.json.total_wall_seconds` je Zelle enthält bereits Elternvorbereitung
und Ergebnislesen. Fitzeit enthält JIT/Export. Callbackzahlen sind keine
Anzahl eindeutiger Bäume oder lokaler Optimiererschritte.

| Signal | Summe Zellzeit / s | Median Zellzeit / s | Summe Fitzeit / s | Fit-Callbacks |
| --- | --- | --- | --- | --- |
| anchor | 474,8539 | 148,8773 | 433,7815 | 52038073 |
| frequency | 472,1766 | 164,7716 | 430,2979 | 49092723 |
| decay | 523,0602 | 191,9596 | 480,2271 | 49296994 |
| phase | 526,2075 | 181,0076 | 479,7591 | 47295371 |
| amplitude | 499,2393 | 168,8801 | 451,6559 | 46925537 |
| combined | 500,0735 | 164,9963 | 456,4181 | 49192715 |

## Alle 18 Originalauswahlen

Index bezeichnet die ursprüngliche nullbasierte Kandidatenposition. Kurven-
und Parameterstatus sowie alle ungewählten Kandidaten sind im Originalarchiv
vollständig erhalten. Die Tabelle nennt zusätzlich beide Zwischenpunktfehler;
die oben bestätigte Kurvenwertung umfasst auch das Trainingsraster.

| Zelle | Signal | Seed | Index | Komplexität | Befund | Struktur | Parameter | Zwischenpunkt-RMS | Zwischenpunkt-Maximum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | anchor | 20261210 | 10 | 20 | – | not_supported | not_assessed | 0,07303252 | 0,06678998 |
| 2 | frequency | 20261210 | 11 | 20 | – | not_supported | not_assessed | 0,02171667 | 0,02463042 |
| 3 | decay | 20261210 | 11 | 19 | – | not_supported | not_assessed | 0,02865651 | 0,01132206 |
| 4 | phase | 20261210 | 9 | 20 | K | not_supported | not_assessed | 1,064234e-11 | 1,43037e-11 |
| 5 | amplitude | 20261210 | 9 | 20 | K | not_supported | not_assessed | 1,123635e-12 | 8,086865e-13 |
| 6 | combined | 20261210 | 11 | 17 | S | recognized | matched | 2,604097e-11 | 3,88124e-11 |
| 7 | decay | 20261211 | 7 | 19 | S | recognized | matched | 5,49437e-12 | 2,846445e-12 |
| 8 | phase | 20261211 | 8 | 19 | S | recognized | matched | 1,659968e-09 | 2,08192e-09 |
| 9 | amplitude | 20261211 | 11 | 19 | – | not_supported | not_assessed | 0,007134059 | 0,007003433 |
| 10 | combined | 20261211 | 9 | 15 | K | not_supported | not_assessed | 1,856296e-11 | 1,720546e-11 |
| 11 | anchor | 20261211 | 9 | 20 | – | not_supported | not_assessed | 0,01754328 | 0,01409565 |
| 12 | frequency | 20261211 | 10 | 19 | – | not_supported | not_assessed | 0,03874506 | 0,03357884 |
| 13 | amplitude | 20261212 | 13 | 20 | – | not_supported | not_assessed | 0,03633361 | 0,04288969 |
| 14 | combined | 20261212 | 14 | 19 | – | not_supported | not_assessed | 0,00280142 | 0,003114293 |
| 15 | anchor | 20261212 | 10 | 20 | – | not_supported | not_assessed | 0,1019851 | 0,09565394 |
| 16 | frequency | 20261212 | 5 | 13 | S | recognized | matched | 3,053765e-12 | 1,611322e-12 |
| 17 | decay | 20261212 | 12 | 20 | – | not_supported | not_assessed | 0,007761667 | 0,003453469 |
| 18 | phase | 20261212 | 11 | 20 | – | not_supported | not_assessed | 0,07232215 | 0,06392705 |

Zelle 1 (anchor, Seed 20261210):

```text
(t + -0.032327938147647894) * (sin(55307.73994120644 / (t + 5.924606846153432)) * (((-0.03233176088877967 + t) * (t + -0.032331943958393304)) * 27569.638204793042))
```

Zelle 2 (frequency, Seed 20261210):

```text
(-1.6701420713963648e-5 - ((-4.9264113731692944 - (-4.924612544139764 - ((0.07168330542115146 - t) * t))) * t)) * (-58369.662320166564 * cos(t * 2620.086210115599))
```

Zelle 3 (decay, Seed 20261210):

```text
(-10.711503624882212 * cos(25728.016725066675 / (4.052189581794393 - t))) / (-310.17726325659856 - (319.55183721505387 / sin((63.72769456711343 * t) - 1.475430992846937)))
```

Zelle 4 (phase, Seed 20261210):

```text
exp(-341.3467867480858 * (sin(0.3749182986342456) * t)) * cos(-0.42040898023512885 * (-1.6650453080757823 - ((-162.7538138731857 * (-51.67146021928747 * 0.4442894325452629)) * t)))
```

Zelle 5 (amplitude, Seed 20261210):

```text
sin(0.9483953853084848) * (((-2.7340543945250637e-5 * 1107.6523159947146) / (exp((-16.25683971611636 * -7.689071319089153) * t) / cos(1570.7963267950227 * t))) * -16.25683971611638)
```

Zelle 6 (combined, Seed 20261210):

```text
(sin(((780.5092123897061 * t) * -1.4490198672060979) + -0.6707963268251771) / (-0.8227174396390049 * exp(83.33333333624952 * t))) * 0.4936304637937191
```

Zelle 7 (decay, Seed 20261211):

```text
exp((((-7.771177387005036 / 1.6520844685522942) * 30.54937155862938) * t) / 0.574800114552963) * cos(((407.3814629056144 * 1.7390041753670011) * 2.217266977151587) * t)
```

Zelle 8 (phase, Seed 20261211):

```text
cos(-0.699999998014229 + ((((t + (t / -0.16038528059432916)) / -0.13496681529880344) / -0.2623631958906188) / 0.09411649505592837)) * exp(t / -0.00800000000385435)
```

Zelle 9 (amplitude, Seed 20261211):

```text
sin((cos(1570.8129968876954 * t) * ((((t * 4.934193636637747) + -0.3048674823323682) * t) + 0.005167175722205645)) / (0.012556689133170615 + t))
```

Zelle 10 (combined, Seed 20261211):

```text
-3.891337619305628e-5 * (exp(9.643346881659811 - (83.33333333033605 * t)) * sin(-0.670796326809554 + (t * -1130.9733552913142)))
```

Zelle 11 (anchor, Seed 20261211):

```text
((0.03840994834462296 - t) * sin(1.5728374480427574 - (t * -1570.5382127555124))) * ((-7.610684830662713 / (-0.011065185050330564 - t)) * (0.03840990365196661 - t))
```

Zelle 12 (frequency, Seed 20261211):

```text
-1.4275432457506627 * sin((0.03017475771927912 - t) / (((-0.006443421565755036 - t) / sin(-1.5754291734522698 - (t * 2619.5051409594676))) * -5.956795522378872))
```

Zelle 13 (amplitude, Seed 20261212):

```text
(sin(-1.5770495628080083 - (t * -1571.5974223120302)) * (sin(t * 9.55724113843241) + -0.2869919037800316)) * (1.3324232486722754 - sin(t * 82.99226682036459))
```

Zelle 14 (combined, Seed 20261212):

```text
((-1.2190872833150574 + sin(42.494756526468976 * t)) / ((-106.1102829571593 * t) + -2.0244037323099042)) * cos(-5.382642783058595 + (-1131.0137020847774 * t))
```

Zelle 15 (anchor, Seed 20261212):

```text
(t + -0.024709974860724605) * (((-0.024682315671612942 + t) * ((t + -1.378710995818183) * -1073.4405395224328)) * sin((t + -0.001007813878896793) / -0.0006358181575393038))
```

Zelle 16 (frequency, Seed 20261212):

```text
exp(-124.99999999951689 * t) * cos((-0.7930152105329275 * (-14.774772443737778 * -223.62152515748275)) * t)
```

Zelle 17 (decay, Seed 20261212):

```text
(sin(t * 1.2053785934880652) - 0.03076874447888969) * (cos(1570.764732078166 * t) / (sin(-0.07749209659511044 / (t - 0.04488202870540277)) - 1.0187750428219378))
```

Zelle 18 (phase, Seed 20261212):

```text
(0.03273073956711242 - t) * (((0.03273073903264767 - t) * sin(-24.253509031616648 - (1571.9890443339816 * t))) * (26226.66397802389 * (0.03273073932033876 - t)))
```

## Konsequenz und abgegrenzte Fortsetzung

Die begrenzte Serie ist abgeschlossen. 500/300/5 bleibt der untersuchte
Arbeitsbezug; die neue Seedgruppe rechtfertigt keine Aussage robuster
Wiederfindung oder Übertragbarkeit. Eine automatische Budgeterhöhung oder
Seedergänzung wäre eine neue adaptive Serie und ist nicht vorgesehen.
500/1.000 und der optionale 300/2-Anschluss bleiben zurückgestellt.

Der nächste abgegrenzte Schritt ist gemäß vorgemerkter Route die Prüfung der
vorhandenen Rauschpipeline auf identischen verrauschten Daten: gewöhnliche
MSE, bekannte Kovarianz und aus unabhängigen Hintergrundfenstern geschätzte
Kovarianz, anhand weniger Weißrausch-/AR(1)-Fälle. Technische Konsistenz und
wissenschaftlicher Rekonstruktionserfolg sind dabei getrennt zu bewerten.
Die Pipelineprüfung selbst wurde in diesem Ergebnisnachtrag nicht ausgeführt.

Vor einem wissenschaftlichen Piloten sind Datenrollen, Hintergrundmengen,
Auswahlregel, Seedabhängigkeit und eine praktikable Messregel für
Strukturstabilität verbindlich festzulegen. Danach folgen Pilotauswertung
und konkreter Hauptversuchsplan. Die Hauptstudie selbst ist nicht beauftragt.
Zwischenbewertung am 8./9. November und Pilotabschluss etwa 15. November 2026
bleiben Planungsziele, keine Erfolgsgarantie. Wissenschaftliche Suchen bleiben
auf Manjaro; keine WSL2-/Parallelisierungsarbeit oder größere Umstrukturierung.
