# Hintergrundstudie: Manjaro 002

Quellenprüfung und Einordnung vom 19.11.2026,
[Leitfadenphase 7](ringdown_recovery_roadmap.md). Die
[vorab beschlossene Hintergrundstaffel](noise_background_plan.md) ist vollständig
ausgeführt: **520 abgeschlossene Suchen, 130 erfolgreiche ursprüngliche
Paketausgaben, 26 Fälle, keine Ausfälle oder Timeouts**. Alle geplanten
Primärwerte und Paarungen sind vorhanden. Erfolgreiche technische Ausführung
besagt dabei noch nicht, dass die gefundenen Formeln wissenschaftlich genügen.

Die Hauptfrage erhält in dieser Serie keinen beobachteten mittleren Vorteil
für E1024 gegenüber O unter AR(1): amplitudennormierter primärer RMSE
**0,04071315 gegenüber 0,02373571**, mittlere gepaarte Differenz
**+0,01697744**, approximatives marginales 95%-Student-t-Intervall
**[−0,01576760; +0,04972247]**. E1024 hat in 7/20 Blöcken den kleineren
Fehler. Einzelne große Zwischenpunktfehler verbreitern das Intervall;
allgemeine Unterlegenheit, Gleichwertigkeit oder ein verlässlicher Gewinner
folgen daraus nicht.

Die geschätzte Kovarianz verbessert sich dagegen bei 64→256→1024
Hintergrundfenstern in **allen 20 AR(1)-Blöcken**, sowohl nach relativem
Frobeniusfehler als auch nach unabhängigem Kontrollscore. Die bessere Matrix
führt hier nicht zu einem entsprechenden mittleren Rekonstruktionsvorteil
der freien symbolischen Suche. Auffällige Originalformeln weisen auf
Abtastaliasing, Nyquist-nahe Anteile und empfindliche Nenner hin. Diese
Diagnosen erklären konkrete Rasterbefunde, ohne ihre Ursache experimentell
zu isolieren.

Die wissenschaftliche Serie benötigte **182.531,209977 s =
50 h 42 min 11,21 s**. Die gelieferten separaten Verifikations- und
reparierten Plotexporte sind abgeschlossen. Die eigene vollständige lesende
Verifikation bestätigt Serie und technischen Vorlauf; ihre vier Exportdateien
sind bytegleich zur gelieferten Verifikation. Herkunft, Zahlen und Darstellung
werden unten mit getrennten Prüfnachweisen geführt. Bei dieser Nachprüfung
wurden keine neuen Fits oder Suchen ausgeführt.

## Original, Protokoll und Quellenbindung

- Originalarchiv `noise-background-manjaro-002-plots-recovered.tar.gz`:
  **470.474.010 Bytes**, aus 19 gelieferten Teilen 000–018 zusammengesetzt;
  alle Teilprüfsummen und die Gesamtprüfsumme stimmen.
- Bestätigter Archiv-SHA-256:
  `b2a4ace2d9097099822ab524377537dae24d59c7ba59e137de11ae5ba3e4214d`.
- **18.166 reguläre Dateien, 1.931 Verzeichnisse, 2.027.757.507 entpackte
  Dateibytes**; keine Links, Spezialdateien, doppelten Namen oder unsicheren Pfade.
- Wissenschaftliche Wurzel `noise-background-manjaro-002`; zweite Wurzel
  `noise-background-preflight-manjaro-001` für den gebundenen technischen Vorlauf.
- Serienbericht `series/completion/assessment_report.json`, SHA-256
  `659f60e8521ba21d012ce3d2202d556e666c1f1cc8b01cf7452cc7f81dc6fdd3`.
- Tatsächlicher sauberer wissenschaftlicher Ausführungsstand und ursprünglicher
  Verifikationsstand: `bd42634b888c2dbaa5a92726b9a1f9851c766a48`.
- Separater reparierter Renderer und Exportlauncher:
  `7b0417db802eb8d97aea407b2a47f715c2a53bba`. Der neuere Renderer ersetzt den
  Ausführungsstand der gespeicherten Suchen nicht.
- Eingefrorener Protokollcommit:
  `0c4b52868d8cc9809f38db02fe066ab540bcfeb3`; Plan-SHA-256
  `d3bb289cf4a2ac75a31f88c34721ca72da348c5af6d9d6a3917d4a6cc90f52f7`.

Im technischen Elternordner sind **205/206 Dateien bytegleich** zum zuvor
geprüften Vorlaufarchiv; insbesondere sind **alle 165 Dateien unter
`technical/` unverändert**. Ausschließlich die äußere Anzeige `progress.txt`
wurde nach damaliger Archivierung von „Prüfungen bestanden; Archivierung läuft“
auf „Abgeschlossen: Tests, Vorlauf, Verifikation, Plots und Archiv geprüft“
fortgeschrieben. Das ist keine Änderung der technischen Originalergebnisse.
Der nach Suspend abgebrochene wissenschaftliche Versuch 001 bleibt ein
separater Lauf und geht nicht als weiterer Block in Versuch 002 ein.

Die eigene Herkunftsprüfung bestätigt 181 unterschiedliche Git-Dateien,
130.000 wiederholte Quellenbindungen und 5.720 vorbereitete Dateibindungen.
Alle 520 Worker verwenden die eingefrorenen Seeds, jeweils einen frischen
Suchaufruf, 1.000 abgeschlossene äußere Runden, lokal 300 Optimiereriterationen
und fünf zusätzliche Neustarts. Kein Checkpointimport oder Ersatzseed.
Die 104 Suchseeds sind innerhalb ihres Blocks über fünf eigenständige
Armaufrufe gepaart; 520 Aufrufe sind somit keine 520 unabhängigen Datenblöcke.

Einheitliche Laufumgebung: Python 3.12.14, Julia 1.13.1, PySR 2.6.0,
SymbolicRegression 2.5.1, Intel i7-1165G7, CPU-Affinität `[0]`, Julia-/GC-/BLAS-
Threads jeweils 1, interaktive Threads 0 und Haswell-BLAS vor und nach dem Fit.
Die größte absolute native Uhrabweichung beträgt 0,009353 s; die größte
Abweichung zwischen UTC-Fitintervall und monotoner Fitdauer 0,406642 s.
Der erste Worker begann am 16.11.2026 um 15:34:29 CET, der letzte endete
am 18.11.2026 um 18:03:49 CET.

## Prüfumfang und getrennte Nachweise

Die folgenden Nachweise betreffen unterschiedliche Ebenen:

- **Gelieferter Abschluss:** Serie und `verification-002/` melden `completed`;
  die Verifikation bindet den oben genannten unveränderten Serienbericht.
  Der erste Verifikationsversuch scheiterte am falschen Vorlaufpfad,
  der erste Plotexport an `TypeError: unhashable type: 'dict'`.
  Beide Abbrüche samt Kosten bleiben erhalten. Der getrennte Export
  `plots-002/` ist vollständig und quellengebunden.
- **Eigene vollständige Herkunftsverifikation am Ausführungscommit:**
  bestanden, Exitcode 0, Originalstand `bd42634b888c2dbaa5a92726b9a1f9851c766a48`,
  ursprüngliche gebundene Umgebung mit Haswell-BLAS und einem Thread.
  Alle vier Exportdateien einschließlich Laufstatus, Abschlussbericht,
  Zusammenfassung und Prüfsummen sind bytegleich zu `verification-002/`.
  Alle 18.166 Originaldateien sind nach abschließender SHA-256-Nachprüfung
  gegenüber dem unveränderten Zustand vor der Auswertung bytegleich.
- **Eigene unabhängige Zahlenprüfung:** alle 130 Ausgaben und 265.330
  gespeicherten Plotpunkte nachgerechnet; direkte CSV-Residuen, Blockstatistik
  und t-Intervalle stimmen bis auf Rundung. Maximale absolute Abweichungen:
  RMSE 1,11×10⁻¹⁶, Primärmaß 5,55×10⁻¹⁷, Intervallgrenzen 2,78×10⁻¹⁷.
  Alle 78 geschätzten Matrizen aus Trainingspräfixen und gespeicherten Alphas
  rekonstruiert; Frobeniusfehler, SVD-Kondition und Kontrollscore mit direktem
  Lösen nachgerechnet. Maximale Scoreabweichung 2,62×10⁻¹².
- **Eigene Plotprüfung:** eingebauter lesender Exportprüfer und unabhängiger
  Abgleich aller 673 Plotdateien einschließlich 670 Nutzdateien bestanden.
  Alle 130 Originalformeln und ausgewählten Bäume sowie 1.758 HOF-Zeilen der
  ausgewählten Worker stimmen mit ihren Quellen überein.
  Alle 248.690 gespeicherten Zwischen-/Irregularvorhersagen sind bitgenau aus
  den Bäumen reproduziert; alle 16.640 nativen Trainingsvorhersagen bleiben
  unverändert. Das Python-Replay der Julia-Trainingswerte weicht bei 1.029
  Werten um höchstens 2,00×10⁻¹³ ab und ersetzt diese Originalwerte nicht.
  Alle 18.110 vom Plotexport konsumierten Originaldateien sind unverändert.
- **Eigene visuelle Prüfung:** alle 130 Originalplots auf sechs ausdrücklich
  verkleinerten Kontaktbögen gesichtet; alle sechs Übersichten und der größte
  Ausreißer zusätzlich in Originalauflösung. Die gespeicherten großen Spitzen
  sind sichtbar und werden nicht abgeschnitten. Das ist keine Prüfung jedes
  Einzelbilds Pixel für Pixel und kein Beweis für alle kontinuierlichen Zeiten.

Die getrennten maschinenlesbaren Nachweise heißen `science-audit.json`,
`science-audit.mechanisms.json`, `cost-provenance-audit.json`,
`plot-audit-builtin.json`, `plot-audit-independent.json` und
`plot-audit-visual.json`; sie gehören zum separaten Auswertungspaket.
`verification-comparison-and-original-integrity.json` belegt den vollständigen
Verifikationsvergleich und die unveränderten Originaldateien.
Die vier `science-audit.*.csv`-Dateien enthalten Einzelwerte, Kontraste,
Matrixdiagnosen und gespeicherte klassische Referenzen. Das Originalarchiv
wird durch diese Auswertung nicht ersetzt.

Das separate Paket `noise-background-manjaro-002-audit.zip` enthält diese
Nachweise, Auditskripte und den vollständigen eigenen Verify-Export:
2.949.645 Bytes, SHA-256
`56fd715461ac8ab57e0121df2ae88a388f517dc0e749f79b7c665379e33ea860`.
Die 34 Nutzdateien sind durch ein internes Manifest gebunden; ZIP-CRC und
alle enthaltenen Hashes sind geprüft. Lokale Pfade in den Auditskripten
bezeichnen die konkrete Prüfablage, keinen portablen wissenschaftlichen Laufplan.

## Primärmaß und Vergleichsbedingungen

O bezeichnet gewöhnliche MSE, K die bekannte wahre Kovarianz und E64/E256/E1024
die geschätzte Kovarianz aus 64/256/1.024 Hintergrundfenstern. Die kleineren
Mengen sind Präfixe desselben Pools; je Block bleiben 128 Validierungs- und
256 unabhängige Kontrollfenster fest. Die Alphas werden ausschließlich anhand
des Validierungsscores gewählt. Kontrollfenster und Signalwahrheit sind keine
Auswahlkriterien.

Signal und Rauschpegel bleiben `confirm_mid`: 128 Trainingszeiten
`t[j]=j/4096 s`, Intervall `[0,127/4096] s`, ungefähr A=11/12,
f=265 Hz, τ=1/150 s, φ=0,25 rad und σ/|A|=0,05. Maßgeblich sind die
exakten Binary64-Werte im eingefrorenen Plan. AR(1) hat ρ=0,65; white
ist die separate Kontrolle. Der marginale Rauschpegel ist kein Detektor-SNR.

Das **prospektiv festgelegte Primärmaß** ist RMSE zur sauberen Wahrheit / |A|
an 1.024 vorab erzeugten unregelmäßigen Zeiten desselben Fensters. Diese
dimensionslose Größe E beträgt beispielsweise 0,02 bei 2 % der Amplitude.
Sie ersetzt den historischen Primärendpunkt des
[vorherigen Piloten](noise_pilot_results_manjaro_001.md) nicht rückwirkend.
Die 889 regulären Zwischenpunkte und 128 Trainingspunkte bleiben sekundär.

Die ursprüngliche Paketauswahl erfolgte armweise ausschließlich nach nativem
Trainingsverlust, Komplexität und Mitgliedsposition. Die nachstehenden
Rasterwerte haben keine Suche oder Auswahl gesteuert. Alle Aussagen beziehen
sich auf dieses Signal, dieses feste Auswerteraster, diese Bedingungen und
den gepaarten Mess-, Hintergrund- und Suchzufall; sie sind keine Aussage über
eine unabhängige Signalpopulation oder alle kontinuierlichen Zeiten.

### Alle ursprünglichen Primärwerte

Unveränderte Paketausgaben, auf neun Dezimalstellen dargestellt. Rohwerte
voller Genauigkeit, Formel, Mitglied und Seed bleiben in den gebundenen
Originaldateien und im Einzelwerte-CSV erhalten. Kein Ausschluss großer Fehler.

#### AR(1)-Rauschen

| Fall | O | K | E64 | E256 | E1024 |
| --- | --- | --- | --- | --- | --- |
| ar1-01 | 0,033858348 | 0,030554204 | 0,038803214 | 0,037679334 | 0,030148799 |
| ar1-02 | 0,018672034 | 0,019359714 | 0,021098132 | 0,026350473 | 0,018180134 |
| ar1-03 | 0,015848226 | 0,015315585 | 0,011245610 | 0,014712527 | 0,011517012 |
| ar1-04 | 0,021074161 | 0,021237172 | 0,028707973 | 0,023947785 | 0,334601450 |
| ar1-05 | 0,025854850 | 0,026484827 | 0,025242861 | 0,020253613 | 0,036626059 |
| ar1-06 | 0,034469002 | 0,031415637 | 0,038901587 | 0,040318547 | 0,032101240 |
| ar1-07 | 0,023731812 | 0,024452213 | 0,034629935 | 0,034129259 | 0,027217577 |
| ar1-08 | 0,029465712 | 0,029701763 | 0,029909251 | 0,028992890 | 0,027751227 |
| ar1-09 | 0,024324632 | 0,026670522 | 0,028982992 | 0,030521957 | 0,026949494 |
| ar1-10 | 0,024689488 | 0,027056155 | 0,019220257 | 0,022353819 | 0,018093776 |
| ar1-11 | 0,020656364 | 0,022145677 | 0,024160542 | 0,019318846 | 0,021320061 |
| ar1-12 | 0,022070803 | 0,025211365 | 0,026369740 | 0,018320146 | 0,024008191 |
| ar1-13 | 0,022012080 | 0,023623931 | 0,027961416 | 0,045908768 | 0,023177317 |
| ar1-14 | 0,023777534 | 0,026228986 | 0,023234916 | 0,026947860 | 0,024983831 |
| ar1-15 | 0,015480181 | 0,012640429 | 0,025853219 | 0,020083371 | 0,017950650 |
| ar1-16 | 0,027990938 | 0,029751340 | 0,027465464 | 0,030638599 | 0,041549050 |
| ar1-17 | 0,026597821 | 0,036263395 | 0,025773276 | 0,029715984 | 0,030167256 |
| ar1-18 | 0,030017984 | 0,511524933 | 0,026040403 | 0,024895133 | 0,026451020 |
| ar1-19 | 0,015508967 | 0,025160760 | 0,026729984 | 0,019173750 | 0,020804366 |
| ar1-20 | 0,018613278 | 0,020267730 | 0,018517457 | 0,023430466 | 0,020664408 |

#### Weißes Rauschen

| Fall | O | K | E64 | E256 | E1024 |
| --- | --- | --- | --- | --- | --- |
| white-01 | 0,018713938 | 0,014629634 | 0,331551200 | 0,021020048 | 0,018233001 |
| white-02 | 0,013274828 | 0,013816936 | 0,012498085 | 0,012149028 | 0,013830101 |
| white-03 | 0,015499542 | 0,315540311 | 0,014566400 | 0,016349379 | 0,014936517 |
| white-04 | 0,017628075 | 0,019226898 | 0,015587007 | 0,017907931 | 0,015803598 |
| white-05 | 0,016154447 | 0,019631307 | 0,011714361 | 0,015437998 | 0,015393895 |
| white-06 | 0,014583541 | 0,238915320 | 0,014890905 | 0,011864691 | 0,014626247 |

### Deskriptive Armstatistik

| Modell | Arm | Verfügbar/geplant | Mittel | Median | Min | Max | Stichproben-SD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ar1 | O | 20/20 | 0,023735711 | 0,023754673 | 0,015480181 | 0,034469002 | 0,005592540 |
| ar1 | K | 20/20 | 0,049253317 | 0,025720175 | 0,012640429 | 0,511524933 | 0,108947514 |
| ar1 | E64 | 20/20 | 0,026442411 | 0,026205071 | 0,011245610 | 0,038901587 | 0,006466363 |
| ar1 | E256 | 20/20 | 0,026884656 | 0,025622803 | 0,014712527 | 0,045908768 | 0,008029389 |
| ar1 | E1024 | 20/20 | 0,040713146 | 0,025717425 | 0,011517012 | 0,334601450 | 0,069519405 |
| white | O | 6/6 | 0,015975729 | 0,015826994 | 0,013274828 | 0,018713938 | 0,001985940 |
| white | K | 6/6 | 0,103626734 | 0,019429102 | 0,013816936 | 0,315540311 | 0,136656660 |
| white | E64 | 6/6 | 0,066801326 | 0,014728653 | 0,011714361 | 0,331551200 | 0,129708903 |
| white | E256 | 6/6 | 0,015788179 | 0,015893689 | 0,011864691 | 0,021020048 | 0,003491147 |
| white | E1024 | 6/6 | 0,015470560 | 0,015165206 | 0,013830101 | 0,018233001 | 0,001512418 |

### Alle acht vorab festgelegten Kontraste je Modell

Negative Differenz bedeutet kleineren Fehler für den erstgenannten Arm.
**E1024−O unter AR(1) ist der primäre Kontrast**, E1024−E64 der wichtigste
sekundäre Kontrast. O und K werden je Block gemeinsam wiederverwendet;
die Kontrastzeilen sind keine zusätzlichen Suchläufe. Alle Paarungen sind
vollständig, jeweils 20/20 unter AR(1) und 6/6 unter white.

| Modell | Kontrast | Mittel | Median | Min | Max | Stichproben-SD |
| --- | --- | --- | --- | --- | --- | --- |
| ar1 | E1024−O | 0,016977435 | 0,001571843 | -0,006595712 | 0,313527288 | 0,069965860 |
| ar1 | E1024−E64 | 0,014270734 | -0,002095761 | -0,008654415 | 0,305893477 | 0,068894138 |
| ar1 | E64−O | 0,002706701 | 0,002965138 | -0,005469231 | 0,011221017 | 0,004976893 |
| ar1 | E256−O | 0,003148946 | 0,003144245 | -0,005601236 | 0,023896688 | 0,006490209 |
| ar1 | E64−K | -0,022810905 | 0,001363799 | -0,485484530 | 0,013212790 | 0,109060205 |
| ar1 | E256−K | -0,022368661 | 0,000803066 | -0,486629799 | 0,022284837 | 0,109509785 |
| ar1 | E1024−K | -0,008540171 | -0,000636115 | -0,485073913 | 0,313364278 | 0,132282373 |
| ar1 | K−O | 0,025517606 | 0,001550582 | -0,003304144 | 0,481506949 | 0,107380349 |
| white | E1024−O | -0,000505169 | -0,000521981 | -0,001824476 | 0,000555272 | 0,000804292 |
| white | E1024−E64 | -0,051330767 | 0,000293354 | -0,313318200 | 0,003679534 | 0,128354802 |
| white | E64−O | 0,050825598 | -0,000854943 | -0,004440085 | 0,312837262 | 0,128369119 |
| white | E256−O | -0,000187549 | -0,000218296 | -0,002718850 | 0,002306109 | 0,001736693 |
| white | E64−K | -0,036825408 | -0,005778418 | -0,300973911 | 0,316921566 | 0,215940971 |
| white | E256−K | -0,087838555 | -0,002930608 | -0,299190932 | 0,006390414 | 0,137721802 |
| white | E1024−K | -0,088156174 | -0,003830356 | -0,300603794 | 0,003603367 | 0,137172754 |
| white | K−O | 0,087651006 | 0,002537842 | -0,004084304 | 0,300040769 | 0,137320528 |

MCSE = SD(Differenz)/√n; das Intervall ist
Mittel ± t(0,975; n−1) × MCSE. Die Intervalle sind **approximative marginale
95%-Präzisionsangaben**. Sie sind bei schiefen Verteilungen mit großen Spitzen
keine exakte Garantie und sichern die 16 Modell-Kontrast-Kombinationen nicht
simultan ab. Sie sind weder Signifikanzfreigabe noch neue Entscheidungsregel.
Die Richtungsspalte zählt negative Paare; es gibt keine exakt gleichen Paare.

| Modell | Kontrast | Paare | MCSE | 95%-Untergrenze | 95%-Obergrenze | Negative Paare |
| --- | --- | --- | --- | --- | --- | --- |
| ar1 | E1024−O | 20/20 | 0,015644842 | -0,015767595 | 0,049722466 | 7/20 |
| ar1 | E1024−E64 | 20/20 | 0,015405198 | -0,017972715 | 0,046514183 | 12/20 |
| ar1 | E64−O | 20/20 | 0,001112867 | 0,000377443 | 0,005035959 | 8/20 |
| ar1 | E256−O | 20/20 | 0,001451255 | 0,000111434 | 0,006186457 | 7/20 |
| ar1 | E64−K | 20/20 | 0,024386603 | -0,073852653 | 0,028230842 | 8/20 |
| ar1 | E256−K | 20/20 | 0,024487132 | -0,073620817 | 0,028883496 | 9/20 |
| ar1 | E1024−K | 20/20 | 0,029579238 | -0,070450227 | 0,053369885 | 12/20 |
| ar1 | K−O | 20/20 | 0,024010976 | -0,024737944 | 0,075773156 | 4/20 |
| white | E1024−O | 6/6 | 0,000328351 | -0,001349221 | 0,000338884 | 4/6 |
| white | E1024−E64 | 6/6 | 0,052400628 | -0,186030870 | 0,083369337 | 2/6 |
| white | E64−O | 6/6 | 0,052406473 | -0,083889530 | 0,185540726 | 4/6 |
| white | E256−O | 6/6 | 0,000709002 | -0,002010097 | 0,001634998 | 3/6 |
| white | E64−K | 6/6 | 0,088157532 | -0,263441559 | 0,189790743 | 5/6 |
| white | E256−K | 6/6 | 0,056224690 | -0,232368723 | 0,056691612 | 5/6 |
| white | E1024−K | 6/6 | 0,056000542 | -0,232110151 | 0,055797802 | 4/6 |
| white | K−O | 6/6 | 0,056060871 | -0,056458051 | 0,231760062 | 1/6 |

Die Hauptdifferenz E1024−O beträgt im Mittel +0,01697744, im Median jedoch
nur +0,00157184. Auch E1024−E64 hat einen positiven Mittelwert (+0,01427073)
bei negativem Median (−0,00209576). Das zeigt die Bedeutung der großen
Einzelabweichung von AR1-04/E1024. E64−O und E256−O besitzen zwar positive
marginale Intervalluntergrenzen; daraus entsteht keine nachträgliche Auswahl
eines „signifikanten“ Kontrasts oder ein allgemeiner Unterlegenheitsnachweis.

Bei white beträgt E1024−O im Mittel −0,00050517 mit Intervall
[−0,00134922; +0,00033888]. Sechs Blöcke sind eine kleine getrennte Kontrolle.
Insbesondere die K- und E64-Mittel werden durch große Zwischenpunktfehler
geprägt. Keine Poolung beider Rauschmodelle, keine Imputation, Winsorisierung
oder Entfernung auffälliger Fälle.

## Matrixqualität und Hintergrundstaffel

Die folgende Tabelle berichtet die 78 Schätzungen vollständig aggregiert;
Alpha ist innerhalb der jeweiligen Modell-Stufen-Kombination konstant.
Frobeniusfehler = ||C_hat−C_true||_F / ||C_true||_F. Der unabhängige Kontrollscore
ist Logdeterminante plus mittlere quadratische Form; angegeben ist dessen
Differenz zum Score von C_true auf denselben Kontrollfenstern. Die Kondition
bezieht sich auf die geschätzte Matrix, nicht auf die Suchfunktion.

| Modell | Arm | Gewähltes Alpha | Mittl. rel. Frobeniusfehler | Mittl. Kondition | Mittl. Kontrollscore minus C_true |
| --- | --- | --- | --- | --- | --- |
| ar1 | E64 | 0,5 (20×) | 0,597416345 | 10,251473488 | 44,128447647 |
| ar1 | E256 | 0,2 (20×) | 0,396411045 | 23,123346111 | 20,943409792 |
| ar1 | E1024 | 0,1 (20×) | 0,219954751 | 22,829557996 | 6,808294119 |
| white | E64 | 1,0 (6×) | 0,010418458 | 1,000000000 | 0,017701435 |
| white | E256 | 1,0 (6×) | 0,009228967 | 1,000000000 | 0,008480875 |
| white | E1024 | 1,0 (6×) | 0,003705962 | 1,000000000 | 0,003321363 |

Unter AR(1) verbessern sich Frobeniusfehler und Kontrollscore bei jeder
Erhöhung 64→256→1024 in allen 20 Blöcken. Die Kondition verbessert sich nicht
monoton; sie ist auch kein alleiniger Qualitätsindikator. Die Beobachtung
stützt die Erklärung „zu wenig Hintergrundtraining ist der alleinige
Engpass“ nicht: Die Schätzung wird klar besser, die freie SR-Rekonstruktion
im Mittel hier nicht. Ein kausal isolierter Such- oder Samplingeffekt ist
damit noch nicht nachgewiesen.

Unter white wählen alle 18 Schätzungen Alpha=1; sie sind somit skalare
Einheitsmatrizen mit Kondition 1. O, K und E besitzen dort bei exakter Lösung
dieselben mathematischen Minimierer, jedoch unterschiedlich skalierte
Zielfunktionen. Numerische Optimierer und endliche stochastische Suchverläufe
müssen deshalb nicht identisch ausfallen. Die unterschiedlichen SR-Ausgaben
sind kein Nachweis eines Nutzens oder Schadens von Korrelationsgewichtung
unter white. Eine optimale Alpha-Wahl oder ausreichende Validierungsmenge
wird durch die konstanten Alphas ebenfalls nicht bewiesen.

## Sekundäre Rasterdiagnosen und Originalformeln

Die Mittel beziehen sich auf 20 beziehungsweise sechs Ausgaben pro Arm.
„Größtes Max“ ist der größte gespeicherte amplitudennormierte Absolutfehler
über alle Ausgaben dieses Modell-Arms; verschiedene Spalten können aus
verschiedenen Blöcken stammen. Regulär sind die 889 vorab festgelegten
Zwischenpunkte. Es wurde kein zusätzliches Raster erzeugt und keine
numerische Spitzensuche ausgeführt.

| Modell | Arm | Mittl. Training-RMSE/\|A\| | Mittl. regulärer RMSE/\|A\| | Größtes Training-Max/\|A\| | Größtes reguläres Max/\|A\| | Größtes unregelmäßiges Max/\|A\| |
| --- | --- | --- | --- | --- | --- | --- |
| ar1 | O | 0,023912551 | 0,023734671 | 0,111727574 | 0,110382728 | 0,111381245 |
| ar1 | K | 0,024080842 | 0,042761025 | 0,114309099 | 8,858002782 | 16,310949046 |
| ar1 | E64 | 0,026599502 | 0,026442182 | 0,141552167 | 0,142299271 | 0,142327545 |
| ar1 | E256 | 0,026984897 | 0,026811774 | 0,165211835 | 0,471888334 | 0,642449708 |
| ar1 | E1024 | 0,025346227 | 0,041317980 | 0,127883118 | 1,776750600 | 1,861500261 |
| white | O | 0,016138800 | 0,015967484 | 0,062124564 | 0,063031013 | 0,063037182 |
| white | K | 0,015864847 | 0,112525551 | 0,062533687 | 1,840120813 | 1,726056091 |
| white | E64 | 0,014324700 | 0,068692306 | 0,068355792 | 1,867137099 | 1,930187664 |
| white | E256 | 0,016105164 | 0,015772528 | 0,102328651 | 0,091990509 | 0,099617594 |
| white | E1024 | 0,015591529 | 0,015464301 | 0,059393254 | 0,059314423 | 0,059351774 |

Die folgenden sechs Originalausgaben zeigen besonders große Unterschiede
zwischen Trainings- und Auswertepunkten. Die Fallauswahl dient der Diagnose
und verändert weder den Nenner noch die ursprüngliche Paketauswahl.
Alle Formeln stehen als vollständiger unveränderter Originaltext; `t` ist
physische Zeit in Sekunden, die Ausgabe hat dieselbe Signaleinheit wie A.
Die numerische Einordnung von Koeffizienten ersetzt keine Formel und keinen
gespeicherten Domain-/Familienbeweis.

### ar1-04 / E1024

Training-RMSE/A 0.024034560; regulär 0.346956137; unregelmäßig 0.334601450.

Die Phase enthält einen konstanten Koeffizienten von 53118,270 rad/s (8454,035 Hz = 2×4096 Hz + 262,035 Hz), zusätzlich einen nichtlinearen Phasenterm. Das ist mit Abtastaliasing vereinbar. Die Originalformel ist als überall definiert bestätigt; der Familiennachweis ist ungeklärt.

Unveränderter Originaltext:

```text
(cos(5.940473929766483 - (((exp(122.30191354295101 * t) * 2.9386242521385464) - -53118.27006769258) * t)) * exp(-135.03627776760692 * t)) / 1.15457182464067
```

### white-01 / E64

Training-RMSE/A 0.015540324; regulär 0.342933885; unregelmäßig 0.331551200.

Der innere Sinus hat 4228,033 Hz = 4096 Hz + 132,033 Hz; der äußere verschachtelte Sinus erzeugt weitere harmonische Anteile. Hohe Frequenz und Aliasstruktur beschreiben einen plausiblen Mechanismus des großen Zwischenpunktfehlers, keinen isolierten Kausalnachweis. Domain definiert, Familie ungeklärt.

Unveränderter Originaltext:

```text
24.820423537229164 * ((-0.9644427726668939 + sin(0.3776976974791814 * (sin((t * 26565.516007289254) + -12.437764023114845) + -12.460720072636207))) * exp(-145.39699314872263 * t))
```

### white-03 / K

Training-RMSE/A 0.015050754; regulär 0.354027898; unregelmäßig 0.315540311.

Der innere Sinus hat 12553,310 Hz = 3×4096 Hz + 265,310 Hz. Die diskrete Aliasnähe zur Signalträgerfrequenz ist in der Originalformel sichtbar. Domain definiert, Familie ungeklärt.

Unveränderter Originaltext:

```text
sin(exp(t * -161.53732296873838) * ((sin((t * -78874.77003967474) - 17.532198018765996) - (t * -10.270908290192056)) / 0.9485291541761623)) - 0.013847622661166948
```

### white-06 / K

Training-RMSE/A 0.012375938; regulär 0.253850298; unregelmäßig 0.238915320.

Das Kosinusprodukt enthält rechnerisch Frequenzanteile von 266,067 Hz und 2046,985 Hz, letzterer nahe Nyquist (2048 Hz). Dessen Anfangsphase liegt nur rund 0,00804 rad neben Quadratur; eine Schwäche des gleichförmigen Trainingsrasters ist damit plausibel. Dies ist eine Diagnose des Originalprodukts, keine vereinfachte Ersatzformel. Domain definiert, Familie ungeklärt.

Unveränderter Originaltext:

```text
((exp(-153.84509721506612 * t) / -0.5252274928335174) * cos((-7266.665398221601 * t) - 16.61947485081251)) * cos(365.0920683335862 - (-5594.918661652619 * t))
```

### ar1-18 / K

Training-RMSE/A 0.023481403; regulär 0.086048172; unregelmäßig 0.511524933.

Der Nenner im Exponenten verschwindet rechnerisch bei ungefähr 0,000662379113 s. Der gespeicherte unregelmäßige Punkt bei 0,000649585412 s zeigt einen Fehler von 16,310949 A. Der gespeicherte Familienstatus ist proven_nonmember, Domain unresolved; diese Status werden nicht aufgewertet.

Unveränderter Originaltext:

```text
sin(exp(-0.6738614982681183 * t) * 2451.677993976513) * exp(t * ((t * -137.58024211952096) / (0.6930790158983643 + (t - 0.693741395011374))))
```

### ar1-17 / K

Training-RMSE/A 0.023814326; regulär 0.298078599; unregelmäßig 0.036263395.

Der Nenner 0,0025019075523771816−t liegt am regulären Zwischenpunkt 0,00250244140625 s nur rund 5,34e−7 s von null entfernt. Dort beträgt der Fehler 8,858003 A; das unregelmäßige Raster erreicht hier nur maximal 0,836123 A. Beide festen Raster bleiben nötig; auch das neue Primärraster kann schmale Auffälligkeiten schwächer abtasten. Familienstatus proven_nonmember, Domain unresolved bleibt erhalten.

Unveränderter Originaltext:

```text
((-1.248017848584053e-5 / (0.0025019075523771816 - t)) + ((-0.007846766347782887 / (-0.007032147891488022 - t)) + -0.23295800028326924)) * cos((t / -0.0005999378981636545) - 0.1874457075958824)
```

Die vier oszillierenden Ausgaben zeigen den grundsätzlichen Unterschied
zwischen kleinem Trainingsfehler und großer Rasterabweichung.
Der auffällige reguläre Punkt von AR1-17/K zeigt außerdem, dass das
unregelmäßige Primärraster schmale Strukturen schwächer treffen kann.
Ein endliches Raster liefert keine Garantie zwischen seinen Punkten.

Die weiteren vorgeplanten Trainingsdiagnosen, gewöhnliche MSE zu den
Beobachtungen und Q_true/N, sind für alle 130 Ausgaben verfügbar und im
Serienbericht unter `assessments[].diagnostics` gebunden. Sie ersetzen die
oben berichtete Rekonstruktion zur sauberen Wahrheit nicht. Aus Q_true/N
wird für die ausgewählten SR-Formeln keine Chi-Quadrat-Aussage mit
behaupteten Freiheitsgraden abgeleitet.

## Strukturstatus und privilegierte klassische Referenzen

Die historische Kurvenklasse lautet **129×D und 1×C**; C betrifft
`ar1-03 / estimated_64`. Die strenge rauschfreie A–D-Skala ist kein
Bestehenskriterium für diesen Rauschversuch.

- Originalfamilie: **115 `unresolved`, 15 `proven_nonmember`**, kein positiver
  Familiennachweis. Ungeklärte Fälle werden nicht als Nichtmitglieder gezählt.
- Domain: **111 `defined_everywhere`, zwei `removable_holes`, 17 `unresolved`**.
  Die entfernbaren Lücken betreffen AR1-06/E1024 und AR1-17/E1024.
- Alle 130 neuen Parametervergleiche bleiben **`not_assessed`**.
  Keine neue Erkennerentwicklung oder nachträgliche Parameterfreigabe.

Endliche gespeicherte Rasterwerte bleiben auch bei ungeklärtem oder negativem
Familienbefund Teil der Fehlerauswertung. Sie behaupten keine überall gültige
Originalfunktion. Eine mögliche stetige Erweiterung beseitigt keine Lücke
aus dem unveränderten Originalbaum.

Alle 130 gespeicherten klassischen Referenzfits sind erfolgreich. Für die
eigene Prüfung wurden ausschließlich ihre vorhandenen kanonischen Parameter
auf den bereits gespeicherten Rastern ausgewertet; keine Fits wurden wiederholt.

| Modell | Arm | Erfolgreiche Referenzfits | Mittl. Training-RMSE/\|A\| | Mittl. primärer RMSE/\|A\| |
| --- | --- | --- | --- | --- |
| ar1 | O | 20 | 0,013926024 | 0,013747554 |
| ar1 | K | 20 | 0,013925046 | 0,013749956 |
| ar1 | E64 | 20 | 0,015907540 | 0,015751138 |
| ar1 | E256 | 20 | 0,016356642 | 0,016203570 |
| ar1 | E1024 | 20 | 0,015119742 | 0,014953777 |
| white | O | 6 | 0,007910992 | 0,007808153 |
| white | K | 6 | 0,007910992 | 0,007808153 |
| white | E64 | 6 | 0,007910992 | 0,007808153 |
| white | E256 | 6 | 0,007910992 | 0,007808153 |
| white | E1024 | 6 | 0,007910992 | 0,007808153 |

Diese Referenzen kennen die wahre Ringdown-Familie. Sie sind eine
**privilegierte Diagnose**, kein gleichberechtigter Methodenvergleich gegen
freie SR. Ihre mittleren Fehler liegen für jeden Arm deutlich niedriger.
Unter AR(1) sind O und K nahezu gleich; E1024 liegt näher bei ihnen als
E64/E256. Unter white stimmen die angezeigten Mittel bis auf Rundung überein.
Die Unterschiede in Vorwissen, Zielfunktion und Suchverfahren erlauben daraus
keinen isolierten Kausalnachweis für einen einzelnen Engpass.

## Tatsächlich gemessene Kosten und Abbrüche

Die nachstehenden Aufrufkosten stammen aus den Original-Sidecars. Die beiden
fehlgeschlagenen Nachbearbeitungsversuche werden mitgezählt; sie sind keine
fehlgeschlagenen wissenschaftlichen Worker. Die Wiederholung unter neuen
Ausgabeordnern verändert die ursprünglichen abgeschlossenen Suchergebnisse nicht.

| Aufruf | Status | Wall time / s |
| --- | --- | --- |
| Vorbereitung | completed | 7,555378 |
| Wissenschaftliche Serie | completed | 182531,209977 |
| Erste Verifikation, falscher Vorlaufpfad | aborted | 2,970853 |
| Separate erfolgreiche Verifikation | completed | 551,677946 |
| Erster Plotexport, dict-Fehler | aborted | 1338,682578 |
| Reparierter Plotexport einschließlich Quellenprüfung | completed | 1399,777612 |

Die Serienzeit enthält 181.721,124096 s Fallaufrufe; darin enthalten sind
180.993,055570 s Workerzeit und darin 172.888,883657 s Fitzeit.
**Diese verschachtelten Kosten werden nicht addiert.** Die Serie umfasst auch
ihre Referenzfits und Abschlussprüfungen. Vorbereitung und spätere
Verifikations-/Plotaufrufe sind getrennte Aufrufe. Die Serien-CPU-Messung ist
vollständig: 181.146,017119 s User und 908,661636 s System, einschließlich
eingesammelter Kindprozesse. Wissenschaftlicher Spitzen-RSS sowie gesonderte
Archivierungs- und Uploadkosten sind im Originalarchiv nicht belegt.

Die eigene lesende Gesamtverifikation vom 19.11.2026 benötigte separat
559,395535 s im gemessenen Verifikationsaufruf, 563,608889 s einschließlich
Python-Start und Imports. User-/System-CPU: 461,524235/98,348063 s;
die CPU-Messung ist vollständig. Der dabei beobachtete Prozess-Spitzen-RSS
von 2.755.048 KiB betrifft ausschließlich diese eigene Verifikation und ist
keine nachträgliche Speichermessung der wissenschaftlichen Serie.

Alle fünf Arme haben 104/104 abgeschlossene Worker, davon 80/80 unter AR(1)
und 24/24 unter white, mit null Ausfällen und Timeouts. Die aggregierte
Workerzeit beträgt 50,275849 h; aufgeschlüsselt:

| Modell | O / h | K / h | E64 / h | E256 / h | E1024 / h |
| --- | --- | --- | --- | --- | --- |
| ar1 | 5,726945 | 7,640173 | 8,016547 | 7,484059 | 7,453862 |
| white | 1,791106 | 2,975152 | 3,167293 | 3,075730 | 2,944983 |

Insgesamt sind 15.953.552.630 Verlustcallbacks während der Fits gezählt.
E1024 benötigt gegenüber O 30,15 % mehr Workerzeit unter AR(1) und 64,42 %
mehr unter white, obwohl 2,48 % beziehungsweise 6,83 % weniger Callbacks
anfallen. Callbackanzahl ist somit kein unmittelbarer Ersatz für Laufzeit.
Die feste Armreihenfolge und derselbe einzelne Rechner begrenzen eine
kausale oder hardwareübergreifende Kosteninterpretation.

Der reparierte Plotexport lief am 19.11.2026 von 07:56:40 bis 08:20:00 CET.
Seine 1.399,777612 s enthalten die Quellenprüfung und bedeuten keine neue
wissenschaftliche Suche. Die ursprünglichen abgebrochenen Ordner
`verification/` und `plots/` bleiben neben `verification-002/` und `plots-002/`
als Teil der nachvollziehbaren Aufrufgeschichte erhalten.

## Vollständige Plots, Formeln, Punktdaten und Sicherungsstand

Im Originalarchiv liegen unter `noise-background-manjaro-002/plots-002/`
alle 130 Einzelausgaben. Ein Dateistamm wie `ar1-18-known_covariance`
enthält PNG und SVG, den vollständigen Text `.formula.txt`, CSV-Punktdaten
und JSON-Metadaten mit Originalbaum, Fall-/Arm-/Mitgliedszuordnung und
Quellenbindung. Die sechs Übersichten heißen je Modell
`ar1` beziehungsweise `white` plus `-errors-contrasts`, `-costs-failures`
und `-covariance`. Sie enthalten alle geplanten Nenner.

Der abgeschlossene Plotbericht hat SHA-256
`59f7511d0bb4a6e70a5dfddee9800bce7488e507e19ef2d2277fcd49a02e2e6b`.
Die zusätzlich bereitgestellte durchsuchbare Galerie `index.html` verbindet
alle 130 Originalplots und vollständigen Formeln mit ihren Punktdaten;
`all-original-formulas.txt` enthält alle Formeln gesammelt. Das portable
Paket `noise-background-manjaro-002-gallery.zip` umfasst **75.143.741 Bytes**,
SHA-256 `c5c367cfb6b0349ca69d129a254eb99d493b0ce2520da852ef2345cc3311ffab`.
Die 673 übernommenen Originaldateien sind bytegleich. Die sechs Kontaktbögen
sind zusätzlich erzeugte Vorschauen und ersetzen die Originalplots nicht.

Originalarchiv und Auswertung bleiben außerhalb von Git; dieser Bericht
und der [Ergebnisindex](results_index.md) halten ihre Identität und Herkunft.
Die Lieferung und Prüfsummenprüfung sind belegt. Ein endgültiger gemeinsamer
Archivpfad und ein davon unabhängiges Backup sind **noch nicht bestätigt**.
Die [Archivierungsrichtlinie](results_archiving.md) bleibt dafür maßgeblich.

## Fachliche Folgerung und abgegrenzter nächster Schritt

Die Hintergrundstaffel verbessert die Matrixschätzung deutlich. Ein
entsprechender mittlerer Vorteil der freien symbolischen Rekonstruktion ist
in dieser Serie nicht beobachtet. Das lenkt die nächste Diagnose auf
Suchvariation und die Diskrepanz zwischen Trainings- und Zwischenpunktverhalten.
Mehr Hintergrundfenster allein sind anhand dieses Befunds keine begründete
Zusicherung besserer SR-Ergebnisse. Auch zusätzliche Validierungsfenster
sind derzeit kein belegter vorrangiger Engpass; die konstanten Alphas
schließen einen solchen Einfluss jedoch nicht grundsätzlich aus.

Die anschließend beauftragte **rein lesende Diagnose der gespeicherten
Endfronten** ist im [Kandidatenbericht](noise_background_candidates_manjaro_002.md)
vom 19.11.2026 dokumentiert. Ihr zuvor abgegrenzter Umfang umfasst alle
636 Kandidaten aus 48 Workern: die sechs oben besprochenen auffälligen
Fall-Arme und die gewöhnliche Gewichtung derselben sechs Fälle. In allen
sechs auffälligen Ausgaben enthält bereits der ursprünglich ausgewählte
Worker Alternativen mit kleineren RMSE und Maximalfehlern auf beiden
Zusatzrastern. Die ursprüngliche Auswahl entspricht korrekt ihrer
Trainingsverlustregel. Die Diagnosezeugen über alle vier Worker haben
3,55–10,47 % höheren Trainingsverlust; sie sind anhand bekannter Wahrheit
nachträglich ausgewählte Beispiele. Sie ersetzen keine Originalausgabe und
belegen keinen verbesserten wissenschaftlichen Erfolg der Serie.

Dieser Befund präzisiert den Anschluss: Das Fehlen weniger auffälliger
Kandidaten im gespeicherten Bestand ist für diese sechs Ausgaben keine
ausreichende Erklärung. Die Auswahl nach Trainingsverlust trennt hier kleine
Trainingsfehler nicht zuverlässig von großen Zwischenpunktfehlern. Welche
praktisch verfügbare Information eine bessere Auswahl ermöglichen könnte,
benötigt eine eigene methodische Planung und unabhängige Prüfung.

Für eine anschließende mehrtägige Rechenserie ist ein kontrollierter
Suchzufallsvergleich auf **festen Beobachtungen und festen Kovarianzen**
fachlich naheliegend: Sind die Zwischenpunktfehler bei denselben Inputs
über frische SR-Seeds stabil oder durch Suchvariation geprägt? Eine
begründete Arm- und Fallauswahl, neue Seeds, Wiederholungszahl, Budget,
Endpunkte und geplante Nenner benötigen zuvor ein separates eingefrorenes
Protokoll. Die tatsächlichen Workerzeiten können dessen Rechenplanung
informieren. Diagnostisch ausgewählte Problemfälle erlauben dabei keine
populationsweite Effektaussage. Wiederholte Suchen quantifizieren
Suchvariation; sie beheben die Blindstellen des Trainingsrasters selbst nicht.

Neue Frequenzgrenzen, Grammatikregeln, Regularisierung, Auswahlkriterien oder
Samplingpunkte wären eigenständige methodische Interventionen. Sie benötigen
eine gesonderte Begründung und Planung. **Hier sind keine neuen Seeds,
Budgets, Schwellenwerte, Methodenänderungen oder Laufaufträge beschlossen.**
