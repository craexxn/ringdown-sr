# Lesende Aliasdiagnose auf Hintergrundserie 002

Mechanismusdiagnose vom 19.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md),
auf Grundlage des [negativen Auswahlpiloten](noise_background_selector_pilot_001.md).
**Die drei vorab festgelegten Beispiele zeigen die erwartete Abtastmehrdeutigkeit:**
Original und konstruierter Aliasrepräsentant unterscheiden sich auf den
128 Trainingspunkten höchstens um 1,20 × 10⁻¹⁴, zwischen ihnen aber stark.
Ein kleiner Trainingsverlust oder wenige Baumknoten können diese Mehrdeutigkeit
allein nicht auflösen. Das ist eine mathematische Mechanismusdiagnose und
keine neue Kandidatenauswahl oder wissenschaftlich bestätigte Verbesserung.

Das vollständige Inventar umfasst **260 Originalbäume und 342 trigonometrische
Knoten**. Numerische Auswertung, unabhängige Gegenrechnung, die drei
Plotexporte und deren separate PNG-Sichtung sind abgeschlossen.
Keine Fits, Suchen, neuen wissenschaftlichen Beobachtungen oder Studienseeds.
Die bereits betrachteten Daten bleiben retrospektive Entwicklungsdaten.

## Umfang, Herkunft und reproduzierbare Regeln

`scope.json` wurde vor der neuen Auswertung festgelegt, SHA-256
`a49af2fe6fde886a6f877ee44dcfdf63e31c779adc5d94e1fe76aea62022a12c`;
der Vorabplan wurde als `3033bb957ed535f7039efbb18fb53e6d1abb44ad`
auf Basis `bb14b5a29163c330f4ba38237ce55419b9fa944f` veröffentlicht.
Die ursprüngliche Suche lief auf `bd42634b888c2dbaa5a92726b9a1f9851c766a48`.
Das unveränderte Archiv `noise-background-manjaro-002-plots-recovered.tar.gz`
hat SHA-256 `b2a4ace2d9097099822ab524377537dae24d59c7ba59e137de11ae5ba3e4214d`.
Der vorausgehende Auswahlpilot ist durch Summary-SHA-256
`a6805b42d7f59aae88e1090c3101d0d7c775329a3834f14df243ddbd69f2a09d` gebunden.

Inventarisiert sind alle `sin`-/`cos`-Knoten der 130 historischen
`accuracy`-Ausgaben und der 130 bereits festgelegten `pooled_best`-Ausgaben.
Das vollständige `inventory.json` enthält alle 260 Zuordnungen, unveränderte
Originalformeln und Baumhashes; `inventory.csv` enthält alle 342 Knoten.
Ausgaben und Knoten sind keine unabhängigen Wiederholungen.

Die Affinität einer Phase `a*t+b` wird aus endlichen Binary64-Konstanten
mit exakten rationalen Zahlen (`Fraction`) geprüft. Erlaubt sind Variable 1,
Konstanten, Addition, Subtraktion, Multiplikation mit mindestens einem
exakt konstanten Operanden und Division durch einen exakt konstanten
Nenner ungleich null. Bereits zertifizierte affine Koeffizienten dürfen
sich kompensieren; unbekannte oder nichtlineare Ausdrücke werden nicht
weggekürzt. Andere Operationen erhalten `not_certified`.

| Auswahl | Ausgaben | Trigonometrische Knoten | Affin zertifiziert (davon nichtkonstant) | Ausgaben mit zertifiziertem k ≠ 0 | Ausgaben mit mindestens einer unbekannten Phase |
| --- | --- | --- | --- | --- | --- |
| `accuracy` | 130 | 212 | 104 (99) | 2 | 88 |
| `pooled_best` | 130 | 130 | 125 (125) | 19 | 5 |

Von 342 Knoten sind 229 affin zertifiziert und 113 nicht zertifiziert.
**Die Zahlen 2 und 19 sind keine vergleichbaren globalen Aliasraten:**
Die Erkennbarkeit unterscheidet sich stark. `not_certified` bedeutet weder
nachgewiesene Nichtaffinität noch Aliasfreiheit. Auch ein zertifiziertes
`k=0` schließt andere Mehrdeutigkeiten des gesamten Ausdrucks nicht aus.

## Welche Symmetrie tatsächlich nachgewiesen wird

Alle 128 gespeicherten Zeiten sind exakt `t_j=j/4096`, j=0,…,127:
Abstand 0,000244140625 s, Dauer 127/4096 = 0,031005859375 s,
Nyquist-Grenze 2048 Hz. Für `fs=4096 Hz` gilt in reeller Arithmetik
für ganzzahliges `k` und beide trigonometrischen Funktionen:

```text
sin/cos((a + 2*pi*k*fs)*t_j + b) = sin/cos(a*t_j + b).
```

Die zusätzliche Phase beträgt genau `2*pi*k*j`. Bei definierten äußeren
Operationen bleiben deren Samples und damit jede Verlustfunktion derselben
Residuen mit positiver definiter Kovarianz gleich. In einem festen affinen
Trägertemplate mit freien Frequenz-/Phasenkonstanten genügt deren Austausch
bei unveränderter Baumtopologie; diese Aussage gilt für dieses Template.
Mehr Seeds,
Kovarianzgewichtung oder Knotenzahl allein brechen diese exakte Symmetrie nicht.

Dokumentiert werden `a` in rad/s, `f=a/(2*pi)` in Hz sowie der
vorzeichenbehaftete Hauptrepräsentant `f0` in `[-fs/2,fs/2)` mit
`k=floor(a/(2*pi*fs)+1/2)` und `a0=a-2*pi*fs*k`.
Alle Aliasordnungen stimmen bei MPFR mit 128 und 256 Bit überein.
Ein irrationaler Versatz ist im Allgemeinen nicht als Binary64-Konstante
speicherbar. Die folgende gerundete Konstruktion besitzt daher nur numerisch
nahe Samplewerte; sie ist nicht bitgleich zum Original. Die hochpräzisen
Konsistenzproben sind keine allgemeine Rundungsfehlerschranke.

Eine kleine repräsentative Trägerfrequenz beweist nicht die wahre physikalische
Frequenz. Eine Trägergrenze erfordert zusätzliches Vorwissen und ist zudem
kein Bandlimit der gedämpften endlichen Kurve. Nichtlineare Phasen,
verschachtelte Funktionen, Nennerverstärkung und Definitionslücken bleiben
ungeprüft. Die bisherigen Nenner-/Fortsetzungs- und Familienfragen werden
hierdurch nicht geschlossen; endlich viele Samples identifizieren keine
beliebige freie Ausdrucksklasse global.

## Drei konstruierte Beispiele, vollständig getrennt vom Original

Die Fälle wurden bereits im Auswahlpilot veröffentlicht und vor dieser
Auswertung festgelegt; es wurde kein Ersatzfall oder günstigster Repräsentant
gesucht. Alle drei besitzen genau einen affin zertifizierten trigonometrischen
Knoten und eine unterstützte exponentielle Hülle. Außerhalb des Knotens bleibt
alles erhalten. `a0` wird mit 256 Bit berechnet und auf Binary64 gerundet;
der rationale Achsenabschnitt wird ebenfalls auf Binary64 gerundet.
Die drei Zuordnungen wurden vor der erneuten Wahrheitsauswertung in
`constructed-mappings-before-truth.json` fixiert, SHA-256
`95b759981fb75940f93b5bf09c105ce0c03f4c2bff03dfab441a69a5c1a23b60`.

| Fall/Arm, jeweils `best` | Originalfrequenz / Hz | k | Konstruierter Hauptrepräsentant / Hz |
| --- | --- | --- | --- |
| ar1-10/E1024 | -8462.886328426 | -2 | -270.886328426 |
| white-03/E64 | -7927.283839893 | -2 | 264.716160107 |
| ar1-20/O | -3833.599304969 | -1 | 262.400695031 |

Diese Konstruktionen sind **neue mathematische Diagnoseartefakte** und
ersetzen keine historische Formel oder Auswahl. Insbesondere sind ihre
kleineren Zusatzrasterfehler kein Leistungsergebnis eines neuen Selektors.
`t` steht in Sekunden; Formeln und Konstanten sind vollständig erhalten.
Mitgliedspositionen sind 1-basiert, Kandidatenindizes 0-basiert.

### ar1-10/E1024

Original `ar1-10--estimated_1024--m04--c004`, Seed 1536548225,
Backend-Seed 52365578:

```text
exp(-164.31644975794768 * t) * cos(-53173.88303509549 * t)
```

Ausdrücklich konstruierter Diagnosebaum:

```text
(exp((-164.31644975794768 * t)) * cos((-1702.0289986803161 * t)))
```

### white-03/E64

Original `white-03--estimated_64--m03--c006`, Seed 1327216417,
Backend-Seed 560399111:

```text
exp(t * -158.38063349562285) * sin((t * -49808.59334865933) - -1.8485231790261236)
```

Ausdrücklich konstruierter Diagnosebaum:

```text
(exp((t * -158.38063349562285)) * sin(((1663.2606877558449 * t) + 1.8485231790261236)))
```

### ar1-20/O

Original `ar1-20--ordinary--m03--c006`, Seed 100106180,
Backend-Seed 247892762:

```text
sin((t * -24087.214826597487) - 42.0696900160896) * exp(t * -160.85771122997193)
```

Ausdrücklich konstruierter Diagnosebaum:

```text
(sin(((1648.7121916100996 * t) + -42.0696900160896)) * exp((t * -160.85771122997193)))
```

### Endliche Rastervergleiche

Ausschließlich die vorhandenen 128 Trainings-, 889 regulären Zusatz- und
1024 unregelmäßigen Zusatzpunkte werden ausgewertet. `T` verwendet die
unveränderten nativen Originalvorhersagen, `R` und `I` deren Python-Replay.
Alle Werte sind durch den Betrag der Signalamplitude normiert; die folgenden
Spitzen sind Rastermaxima und keine kontinuierlichen Maximalfehler.
Die drei Paarvergleiche enthalten insgesamt 6.123 vollständige Punktzeilen.

| Fall/Arm | Raster | RMSE Original | RMSE Konstruktion | Maximum Original | Maximum Konstruktion |
| --- | --- | --- | --- | --- | --- |
| ar1-10/E1024 | T | 0.047160644 | 0.047160644 | 0.226768026 | 0.226768026 |
| ar1-10/E1024 | R | 0.354448792 | 0.046902752 | 2.004458467 | 0.228093565 |
| ar1-10/E1024 | I | 0.345732012 | 0.046918382 | 1.995607088 | 0.228064262 |
| white-03/E64 | T | 0.016284257 | 0.016284257 | 0.080194290 | 0.080194290 |
| white-03/E64 | R | 0.357875769 | 0.015454391 | 1.933903120 | 0.076867756 |
| white-03/E64 | I | 0.342382254 | 0.015446163 | 1.974851724 | 0.079306899 |
| ar1-20/O | T | 0.020072829 | 0.020072829 | 0.088864621 | 0.088864621 |
| ar1-20/O | R | 0.355593513 | 0.019695143 | 1.900708319 | 0.089991962 |
| ar1-20/O | I | 0.334678176 | 0.019700689 | 1.878881147 | 0.089957187 |

Die Trainings-RMSE erscheinen nach Rundung gleich; die tatsächlichen
Gleitkommaabweichungen werden separat ausgewiesen. Vorhersagedifferenzen
in der folgenden Tabelle haben die ursprüngliche Signaleinheit, keine
A-Normierung. ΔL bedeutet Konstruktion minus Original-Python-Replay.
E1024 und E64 verwenden die eindeutig gebundene ursprüngliche Kovarianz
und Cholesky-Lösung; O verwendet die mittlere Residuenquadratsumme.

| Fall/Arm | max. Pythonoriginal minus nativ | max. Konstruktion minus Pythonoriginal | Gespeicherter nativer Verlust | ΔL |
| --- | --- | --- | --- | --- |
| ar1-10/E1024 | 5.55112e-17 | 7.88258e-15 | 1.28527936578174 | 2.17604e-14 |
| white-03/E64 | 1.11022e-16 | 1.19349e-14 | 0.9924273501574423 | 4.70735e-14 |
| ar1-20/O | 1.11022e-16 | 7.46625e-15 | 0.00153818750618752 | 2.45030e-17 |

Die Replays der nativen Zielfunktion weichen vom gespeicherten Verlust um
höchstens 2,22 × 10⁻¹⁶ ab. Auf den Zusatzrastern unterscheiden sich die
nahezu trainingsgleichen Formeln dagegen deutlich. Das isoliert in diesen
drei Fällen den Aliasmechanismus, beweist aber weder dessen Anteil an allen
Serienfehlern noch die physikalische Richtigkeit des Hauptrepräsentanten.

## Offset-Gegenproben und eine Akquisitionsoption

Die 16 getrennten analytischen Proben verwenden `k=1,2,3,4` und
`delta=0, 1/2, 1/3, (sqrt(2)-1)/4`, jeweils mit 128 und 256 Bit.
Auf der Vereinigung des Originalrasters und der innerhalb desselben Fensters
verschobenen Punkte bleibt bei gemeinsamer Phase ein Alias erhalten, wenn
`k*delta` ganzzahlig ist. Der Halbschritt erhält k=2 und 4, der Drittelschritt
k=3; der irrationale Offset bricht die untersuchten k=1,…,4 in reeller
Arithmetik. Die numerischen Proben stimmen mit diesen Aussagen überein.
Diese generische Phasensymmetrie schließt zusätzliche Gleichheiten durch
Kosinus-Reflexionen oder degenerierte feste Samples nicht aus.

**Nur das einzige uniforme Raster zu verschieben genügt nicht:** Bei freier
Phase kompensiert `b0=b-2*pi*k*delta` den Versatz für jedes k wieder.
Irrationale Zeitpunkte sind eine mathematische Aussage, keine Garantie über
Binary64-Zeitgeber. Die gedämpften Kosinusbeispiele sind ausdrücklich
analytische Gegenproben, keine neuen verrauschten Studienbeobachtungen;
`toy-offsets.json` bleibt von den Studienmetriken getrennt.

Eine begründete künftige Option ist eine neue synthetische Studie mit
**N=128 uniformen gegenüber tatsächlich ungleichmäßigen Messzeitpunkten**,
gleichen Endpunkten, Suchprofil, Budget, freier Grammatik und unveränderter
`accuracy`-Auswahl. Die Messwerte müssten am jeweiligen Zeitpunkt wirklich
verfügbar sein; Interpolation der bisherigen Samples ersetzt sie nicht.
Ein gemeinsamer zugrunde liegender Prozess auf beiden Zeitachsen könnte
gepaarte Daten ermöglichen, keine zweite unabhängige Aufnahme desselben Signals.

Dafür wäre `C(t_i,t_j)=sigma²*exp(-lambda*abs(t_i-t_j))` mit
`lambda=-4096*log(0.65)` eine explizite neue kontinuierliche
Rauschannahme. Sie stimmt auf dem bisherigen Raster mit AR(1) überein,
folgt daraus aber nicht eindeutig. Ein Effekt beträfe Abtastungsgeometrie
**und** die veränderten Rauschkorrelationen; er wäre kein isolierter Beweis,
dass sämtliche Probleme aliasbedingt sind, und kein unmittelbarer
Detektordatennachweis. Weder ein Frequenzprior nahe der bekannten Wahrheit
noch eine zusätzliche Auswahl-/Normalisierungsregel wird zugleich eingeführt.
Dies ist eine begründete Option, keine beschlossene Langlaufpriorität.

## Einordnung der Frage nach mehr Rauschhintergrund

[Wang und Shao (2024), Phys. Rev. D 109, 043027, Abschnitte III/V](https://link.aps.org/accepted/10.1103/PhysRevD.109.043027)
vergleichen 64 s mit 4092 s aus einer 4096-s-Rohaufnahme. Der zugehörige
Dauereffekt auf SNR beträgt ungefähr 5 % bei TTD2/FD; alle untersuchten
Bayes-Parametervergleiche verwenden dagegen 4092 s. Die Arbeit behandelt
ACF-/PSD-Schätzung im Umfeld von GW190521, keine freie symbolische Regression.
Sie belegt deshalb keinen isolierten SR- oder Parametergewinn durch
Verlängerung von 64 s auf 4092 s.

In unserem [Hintergrundplan](noise_background_plan.md) bedeuten M=64/256/1024
jeweils unabhängige Fenster mit 128 Samples: `M*128/4096` ergibt
2/8/32 s **reines Samplevolumen**, keinen zusammenhängenden Zeitverlauf.
Verwendet werden Stichprobenkovarianz und validierungsgewähltes Shrinkage,
keine Toeplitz-ACF aus einer langen kontinuierlichen Rauschaufnahme.
Eine Übertragung der Literaturdauer ist daher eine eigene Methodenfrage.
Ein günstiger getrennter Dauer-/Schätzervergleich vor der Entscheidung über
lange Suchläufe bleibt ein begründeter Vorschlag; hier wurde keiner ausgeführt.

## Konkreter Vorschlag für das verfügbare Laufzeitfenster

Das Zeitfenster bis zum Morgen des 23.11.2026 ist eine weiche Planungsgrenze;
mehrere aufeinanderfolgende Tests sind möglich. Ein begrenzter gemeinsamer
Vorschlag verwendet **26 frische Fälle: 20 AR(1), sechs weiß**, jeweils vier
Worker je Fall/Arm. Dies ist noch kein eingefrorenes Protokoll oder Laufauftrag.

- **Block A, Hintergrunddauer:** Uniformes N=128-Raster, O, K sowie aus
  64 s und 4096 s Hintergrund geschätzte Gewichtung: 26 × 4 × 4 = **416 Worker**.
  Die Sekunden bezeichnen neue Zeitdauern, nicht die bisherigen Fensterzahlen.
  Vorgesehen sind lange kontinuierliche AR(1)-Reihen und ihr 64-s-Teil.
  Der volle Matrixschätzer mit Shrinkage bleibt methodisch festgelegt;
  Fensterbildung sowie unabhängige Validierungs-/Kontrollrollen sind vorher
  zu definieren. Eine günstige PSD-/ACF-Diagnostik darf keinen nachträglichen
  Gewinner bestimmen, der dann als vorab festgelegte SR-Methode erscheint.
- **Block B, Abtastungsgeometrie:** Gleiches N=128 und gleiche Endpunkte,
  ungleichmäßige Akquisition nur mit O und K: 26 × 2 × 4 = **208 neue Worker**.
  Uniforme O-/K-Ausgaben aus Block A werden vorab als gemeinsame Kontrollen
  gebunden. Freie Grammatik, `accuracy` und Suchbudget bleiben gleich.

Insgesamt wären das **624 neue Worker**, mit einer groben historischen
Laufzeitprojektion von etwa **57,06 Stunden**: Block A 38,93 h, Block B 18,13 h.
Die Quelle `cost-provenance-audit.model-arm.csv` der
[Originalauswertung](noise_background_results_manjaro_002.md) ergibt über
26 Fälle O=7,51805 h, K=10,61532 h und E1024=10,39884 h.
Beide neuen Dauerarme werden allein durch diese bisherigen E1024-Kosten
angenähert. Das ist keine Laufzeit- oder Powergarantie; neue Eingabe-,
Schätz-, Raster- und Verifikationskosten sind nicht gemessen. Prozess-, Zeitachsenunion- und
Seedbindung müssen vor neuen Daten feststehen. Historische Fälle aus Serie
002 werden nicht als frische Kontrollen wiederverwendet; die gekoppelten
Blöcke sind keine unabhängigen Stichproben.

Vor einem Start sind Methodenplan und Umsetzung nötig: fallweise Teilblöcke,
eigene passende Schemas und getrennte Sicherung vollständig abgeschlossener
Teilblöcke. Der vorhandene Serienrunner bietet kein Resume. Zeitdruck darf
weder diese Bindungen noch vollständige Prüfungen überspringen; bis dahin
bleiben Raster, Rollen, Schätzerdetails, Seeds und konkrete Startbefehle offen.

## Prüfungen, Kosten und Artefakte

Der Hauptaudit besteht 3.741 Datenprüfungen; zusätzlich wurden zehn analytische
Rechenprimitive, acht unterstützte und sieben ausdrücklich nicht unterstützte
Phasenfälle, fünf vorgegebene Aliasordnungen und die 16 Offsetproben geprüft.
445 konsumierte Originaldateien und 263 Quellen des Auswahlpiloten bleiben
bytegleich. Python 3.12.14, NumPy 2.5.3, gmpy2 2.2.2 und MPFR 4.2.1;
keine Julia-Ausführung.

Die separate Gegenrechnung besteht 87.159 Prüfungen mit 14 analytischen
Referenzfällen und neun Phasenreflexionsprüfungen. Alle 260 Ausgaben,
342 Knoten und 224 nichtkonstanten Aliasordnungen wurden unabhängig geprüft;
ein rationales pi-Intervall mit Breite kleiner als 2⁻⁵⁹⁰ bestätigt zusätzlich
die eindeutigen Aliasordnungen und die drei gerundeten Frequenzkonstanten.
Alle 12.246 Original-/Konstruktionsreplaywerte der 6.123 CSV-Zeilen sind
bitgleich, alle 384 nativen Trainingswerte erhalten. Größte RMSE-Abweichung
5,55 × 10⁻¹⁷, Rastermaxima und Spitzenzuordnungen identisch; unabhängige
dichte Kovarianzlöser weichen höchstens 2,22 × 10⁻¹⁶ von den Cholesky-Verlusten ab.
Prüftoleranzen sind relativ/absolut 2 × 10⁻¹² / 2 × 10⁻¹⁵ für Metriken
und 2 × 10⁻¹⁰ / 2 × 10⁻¹² für Zielfunktionen, keine allgemeinen
Genauigkeitsgarantien. Alle **18.166 Originaldateien mit 2.027.757.507 Bytes**,
1.048 Nutzdateien des Auswahlpiloten und 21 aktuelle Auditnutzdateien
bleiben unverändert.

Gemessene Hauptlaufzeit 2,969449 s, CPU User 2,898321 s / System 0,779972 s,
Peak-RSS 92.344 KiB. Darin enthalten sind 2,258361 s Konstruktion vor
Wahrheitsbewertung; diese Teilzeit darf nicht addiert werden. Die Zeitgrenze
endet vor abschließendem Bericht-/Manifestschreiben. Plotexport 3,590223 s,
CPU User 3,358459 s / System 0,218937 s, vor Schreiben des Plotberichts.
Separate Gegenrechnung 17,575444 s vor Berichtschreiben, CPU User
9,471803 s / System 5,476617 s, Peak-RSS 202.644 KiB.

Der separate Export enthält `index.html`, drei PNG-/SVG-Paare und unter
`examples/` alle drei JSONs, sechs vollständigen Formeltexte sowie drei
Punkt-CSV mit je 2.041 Zeilen. Native und Python-Originalwerte bleiben
getrennt verfügbar. Alle drei PNGs wurden dekodiert, 27 lokale Linkvorkommen
geprüft und 14 konsumierte Plotquellen unverändert bestätigt. Zusätzlich
wurden alle drei vollständigen PNGs separat visuell gesichtet, ohne konkrete
Darstellungsbefunde; SVGs wurden dabei nicht separat gerendert und die Dauer
der Sichtung nicht gemessen.

Das vollständige Paket `noise-background-manjaro-002-alias-diagnostic.zip`
umfasst 2.872.144 Bytes, 36 Nutzdateien und ein internes Manifest,
SHA-256 `1a1e28657a9e4958ee0ba34edfe4934c7b01ce847ee4c5636f767f920e6ded24`.
ZIP-CRC, alle 36 Nutzdateihashes und unveränderte Paketquellen sind geprüft.
`MANIFEST.sha256.json` hat SHA-256
`5951d409fa7de38c54dafcd79ecf44d5f1b4020d27807c3050260d437dbb3839`.
Nach vollständigem Entpacken öffnet `index.html` die drei Plotpaare mit
Formeln und Punktdaten. Das Paket ersetzt kein Originalarchiv;
eine davon unabhängige Sicherung ist damit noch nicht belegt.

Die Artefakte liegen außerhalb von Git; Zuordnung und Sicherungsstand stehen
im [Ergebnisindex](results_index.md). Wesentliche SHA-256-Bindungen:

| Artefakt | SHA-256 |
| --- | --- |
| `audit_aliases.py` | `aa18ddb97b71030d1c34492e270676df95535d0e79f900206fbfbaac4a6c4ed8` |
| `summary.json` | `6253ca37e61b704b51c61ad361798584003a1974542d008d6206647d5be0b1e0` |
| `inventory.json` | `c5ed176911f66603568b959c1624bb82bcf067180b134f7360c4fa7b40ab0c44` |
| `inventory.csv` | `2fa39eed507bf60b026a2b97e55697b2757e7cdc138fe4f586cfd118a3149970` |
| `audit-payload-sha256.json` | `303ac6fd6a6e512db7d11ecc259fa87001d451a18f2020c64e1854e821522585` |
| `plot-report.json` | `56a2c96b719d3c8a7ef3d6e61036de24cc78c38cc20242a22d238aecc63b88c7` |
| `visual-check.json` | `3cb303835cbfb1b6aadb9f68b9687b36cbd36b7249e1afcdb920cc2615a97b9e` |
| `independent-check.py` | `c8eebfe474235ea07b7dca0107dca8fcab90a4e78e1037b5523312742d5d3d9d` |
| `independent-check.json` | `7a421f47d79608ec94ca7a2173883ec4d39407c50c6921fa4bdd3de534889fc9` |
| Historische `cost-provenance-audit.model-arm.csv` | `690007279ff61b11ff883f7b653695416263128049532007cb2e4a4ea09c876d` |

Der Befund rechtfertigt weder automatische Baseband-Ausgaben noch eine
neue große Suchserie mit `pooled_best`. Historische Protokolle und sämtliche
Originalauswahlen bleiben erhalten.
