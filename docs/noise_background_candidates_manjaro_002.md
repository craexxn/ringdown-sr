# Lesende Kandidatenprüfung: Hintergrundserie Manjaro 002

Diagnostischer Nachtrag vom 19.11.2026,
[Leitfadenphase 7](ringdown_recovery_roadmap.md), zum
[vollständig geprüften Lauf 002](noise_background_results_manjaro_002.md).
Die Frage lautet: Enthalten die gespeicherten Endbestände der sechs bereits
berichteten auffälligen Ausgaben Alternativen mit kleineren Fehlern auf den
vorhandenen Zwischenpunktrastern, und in welchen Workern liegen sie?

**Alle sechs auffälligen Fall-Arme enthalten bereits gespeicherte Alternativen,
die auf beiden Zusatzrastern sowohl RMSE als auch Maximalfehler der
Originalauswahl unterschreiten. Solche Alternativen liegen in allen sechs
Fällen auch im ursprünglich ausgewählten Worker.** Der Befund betrifft
vorhandene Kandidaten unter der bisherigen Auswahlregel; er ist keine
nachträgliche Verbesserung des abgeschlossenen Versuchs.

Die unten bezeichneten fokalen Diagnosezeugen haben auf dem unregelmäßigen
Raster RMSE/|A| von 0,00744 bis 0,01808 statt 0,03626 bis 0,51152 bei den
Originalauswahlen. Ihr nativer Trainingsverlust liegt dabei **3,55 bis
10,47 % höher**. Die Regel mit minimalem Trainingsverlust bevorzugte also
andere, auf den Zusatzrastern auffällige Formeln. Auch die vier ursprünglichen
Workerwahlen unterscheiden sich deutlich; eine Wiederholungsstudie könnte
diese Suchvariation untersuchen, würde die Auswahlregel selbst aber nicht ändern.

## Vorab begrenzter Diagnoseumfang

Der Umfang wurde vor der neuen Kandidatenauswertung in `scope.json`
festgeschrieben, SHA-256
`941f81c1709731deba065c543b8d6df27c68c47ce076bf369bf320657066b84b`.
Grundlage sind genau die sechs im bisherigen Ergebnisbericht einzeln
diskutierten auffälligen Ausgaben sowie die gewöhnliche Gewichtung O
derselben sechs Fälle als Vergleich:

| Fall | Auffälliger Arm | Zusätzlicher Vergleich |
| --- | --- | --- |
| ar1-04 | E1024 | O |
| white-01 | E64 | O |
| white-03 | K | O |
| white-06 | K | O |
| ar1-18 | K | O |
| ar1-17 | K | O |

Das Inventar umfasst **636 gespeicherte Kandidatenzeilen aus 48 Workern
und zwölf Fall-Arm-Gruppen**, jeweils alle vier ursprünglichen Worker.
Die Fallauswahl ist nachträglich und diagnostisch. Sie ist weder eine neue
unabhängige Stichprobe noch repräsentativ für alle 130 ursprünglichen Ausgaben.
Alle 636 kanonischen Baumhashes sind verschieden; eine mathematische
Gleichwertigkeitsprüfung dieser Bäume wurde nicht durchgeführt. Kandidatenzahlen
sind keine Zahlen unabhängiger Versuche.

Alle Kandidaten bleiben mit ihrer ursprünglichen vollständigen Formel,
ihrem Binary64-Baum, ihrer Zeilenposition, ihrem Worker und Seed verbunden.
Der Abgleich verwendet `result.json` und die ursprüngliche
`hall_of_fame.csv`. Die gespeicherte Endfront ist nicht der gesamte Suchverlauf.

Für jeden Kandidaten werden ausschließlich die vorhandenen 128 Trainings-,
889 regulären Zwischen- und 1.024 unregelmäßigen Auswertepunkte verwendet.
Die nativen Trainingsvorhersagen bleiben erhalten; auf den beiden Zusatzrastern
wird der unveränderte Baum lesend ausgewertet. Alle 1.298.076 ausgewerteten Punkte sind verfügbar: 81.408 native
Trainingswerte und 1.216.668 zusätzliche Baumvorhersagen. Nichtfinite Werte
wären mit ihrem vollständigen Nenner sichtbar; hier trat keiner auf. Keine neue Stützstelle, Optimierung,
Spitzensuche, Vereinfachung, Anpassung oder symbolische Suche.

## Maße, Vergleich und Bedeutung der Diagnosezeugen

Berichtet werden nativer Trainingsverlust, Komplexität, amplitudennormierter
RMSE zur sauberen Wahrheit und größter amplitudennormierter Absolutfehler
je Raster. `t` bleibt physische Zeit in Sekunden, die Formelwerte haben die
Signaleinheit von A. Alle nachstehenden Rasterfehler sind dimensionslos,
geteilt durch |A|. Native Trainingsverluste werden ausschließlich innerhalb
desselben Fall-Arms verglichen, weil die Gewichtungen unterschiedliche
Zielfunktionen definieren.

Die Originalauswahl bleibt der gespeicherte Kandidat mit minimalem nativem
Trainingsverlust, danach Komplexität und Mitgliedsposition. Zusätzlich werden
rein beschreibend Alternativen gezählt, die gegenüber dieser Auswahl
entweder beide Zusatzraster-RMSE oder alle vier Größen aus beiden RMSE und
beiden Maximalfehlern strikt unterschreiten. Die Zählung trennt den
ausgewählten Worker von den anderen drei Workern. Strikte numerische
Ungleichheiten sind keine Signifikanztests oder neue Bestehensgrenzen.

Als **nachträgliche Diagnosezeugen** werden die Kandidaten mit kleinstem
unregelmäßigem beziehungsweise regulärem RMSE und, falls vorhanden, der
Kandidat mit kleinstem unregelmäßigem RMSE unter den in allen vier Größen
kleineren Alternativen bezeichnet. Bei Gleichstand gelten Trainingsverlust,
Komplexität, Mitgliedsposition und Kandidatenzeile in dieser Reihenfolge.
Diese Zeugen verwenden die bekannte Wahrheit zur Diagnose. Sie ersetzen
keine Originalauswahl und erhöhen keinen wissenschaftlichen Erfolgszähler.

### Originalauswahlen und nachträgliche Diagnosezeugen

`mNN` bezeichnet die Mitgliedsposition 1–4, `cNNN` den **nullbasierten**
Index in `result.json.candidates`. Die Tabellen verwenden den Zeugen mit
kleinstem unregelmäßigem RMSE unter den in allen vier Zusatzrastermaßen
kleineren Alternativen. Der Pfeil bedeutet **Originalauswahl → Diagnosezeuge**,
keine neu ausgeführte Verbesserung. Werte sind zur Lesbarkeit gerundet;
`candidate-metrics.csv` und Kandidaten-JSON erhalten die vollständigen Zahlen.

| Fall / Arm | Original | Zeuge | Regulärer RMSE/\|A\|: Original → Zeuge | Unregelmäßiger RMSE/\|A\|: Original → Zeuge |
| --- | --- | --- | --- | --- |
| ar1-04 / E1024 | m01/c013 | m03/c007 | 0,346956 → 0,018079 | 0,334601 → 0,018082 |
| white-01 / E64 | m02/c010 | m03/c007 | 0,342934 → 0,008693 | 0,331551 → 0,008692 |
| white-03 / K | m04/c012 | m02/c007 | 0,354028 → 0,007449 | 0,315540 → 0,007444 |
| white-06 / K | m01/c011 | m04/c006 | 0,253850 → 0,009088 | 0,238915 → 0,009085 |
| ar1-18 / K | m02/c016 | m04/c010 | 0,086048 → 0,014705 | 0,511525 → 0,014712 |
| ar1-17 / K | m03/c013 | m04/c006 | 0,298079 → 0,015354 | 0,036263 → 0,015356 |
| ar1-04 / O | m02/c014 | m02/c009 | 0,021078 → 0,016372 | 0,021074 → 0,016375 |
| white-01 / O | m01/c012 | m02/c007 | 0,018703 → 0,008693 | 0,018714 → 0,008692 |
| white-03 / O | m02/c010 | m03/c007 | 0,015478 → 0,007791 | 0,015500 → 0,007787 |
| white-06 / O | m03/c012 | m01/c007 | 0,014593 → 0,009088 | 0,014584 → 0,009085 |
| ar1-18 / O | m01/c015 | m02/c006 | 0,030015 → 0,018651 | 0,030018 → 0,018644 |
| ar1-17 / O | m04/c014 | m02/c008 | 0,026617 → 0,018537 | 0,026598 → 0,018539 |

| Fall / Arm | Reguläres Max/\|A\|: Original → Zeuge | Unregelmäßiges Max/\|A\|: Original → Zeuge |
| --- | --- | --- |
| ar1-04 / E1024 | 1,776751 → 0,071555 | 1,861500 → 0,071564 |
| white-01 / E64 | 1,867137 → 0,030051 | 1,930188 → 0,030058 |
| white-03 / K | 1,840121 → 0,023939 | 1,726056 → 0,023942 |
| white-06 / K | 1,006982 → 0,037444 | 0,977952 → 0,037872 |
| ar1-18 / K | 2,431515 → 0,056409 | 16,310949 → 0,058583 |
| ar1-17 / K | 8,858003 → 0,059349 | 0,836123 → 0,061821 |
| ar1-04 / O | 0,090615 → 0,071506 | 0,090536 → 0,071491 |
| white-01 / O | 0,063031 → 0,030051 | 0,063037 → 0,030058 |
| white-03 / O | 0,043895 → 0,028258 | 0,049073 → 0,028258 |
| white-06 / O | 0,051856 → 0,037444 | 0,051860 → 0,037872 |
| ar1-18 / O | 0,092867 → 0,081297 | 0,095473 → 0,083138 |
| ar1-17 / O | 0,107200 → 0,073340 | 0,107185 → 0,074207 |

Bei elf Fall-Armen stimmen der Zeuge nach allen vier Kriterien und die beiden
reinen RMSE-Minima überein. Die Ausnahme ist AR1-18/O: `m03/c009` hat den
kleinsten unregelmäßigen RMSE (0,017897215), aber größere Maximalfehler als
die Originalauswahl. Der gemeinsame Zeuge `m02/c006` erreicht RMSE 0,018643809
und unterschreitet zusätzlich beide Maximalfehler. Daher werden RMSE und
Spitzen getrennt erhalten.

### Nativer Trainingsverlust und Komplexität

ΔL = nativer Verlust des Diagnosezeugen minus Verlust der Originalauswahl;
ΔL/L bezieht sich jeweils auf den ursprünglichen Verlust desselben Fall-Arms.
Die positiven Unterschiede erklären, weshalb diese Zeugen unter der
unveränderten Trainingsregel nicht gewählt wurden. Eine tolerierte
Verlustzunahme oder neue Komplexitätsgrenze wird daraus nicht abgeleitet.

| Fall / Arm | L Original | ΔL Zeuge | ΔL/L Original | Komplexität Original → Zeuge |
| --- | --- | --- | --- | --- |
| ar1-04 / E1024 | 0,735852866 | 0,054766914 | +7,443 % | 20 → 13 |
| white-01 / E64 | 1,072028711 | 0,065609073 | +6,120 % | 20 → 13 |
| white-03 / K | 0,857725439 | 0,057816804 | +6,741 % | 20 → 13 |
| white-06 / K | 0,745083137 | 0,026481196 | +3,554 % | 20 → 13 |
| ar1-18 / K | 0,995586462 | 0,104250331 | +10,471 % | 20 → 16 |
| ar1-17 / K | 1,083849976 | 0,073136393 | +6,748 % | 20 → 13 |
| ar1-04 / O | 0,001529537 | 0,000150485 | +9,839 % | 20 → 13 |
| white-01 / O | 0,002269554 | 0,000110272 | +4,859 % | 20 → 13 |
| white-03 / O | 0,001819668 | 0,000123045 | +6,762 % | 19 → 13 |
| white-06 / O | 0,001529141 | 0,000091680 | +5,996 % | 20 → 13 |
| ar1-18 / O | 0,001797591 | 0,000713330 | +39,683 % | 20 → 11 |
| ar1-17 / O | 0,001844331 | 0,000295961 | +16,047 % | 19 → 13 |

### Vollständige Kandidatenzählungen

Die letzten beiden Spalten geben **ausgewählter Worker / andere drei Worker**
an. Es sind Zeilenzählungen gegenüber einer festen Originalauswahl, keine
unabhängigen Erfolge oder Schätzung von Ausfallwahrscheinlichkeiten.

| Fall / Arm | Alle Kandidaten | Beide RMSE kleiner | Alle vier Maße kleiner | Beide RMSE: gleicher / andere | Vier Maße: gleicher / andere |
| --- | --- | --- | --- | --- | --- |
| ar1-04 / E1024 | 52 | 50 | 50 | 12 / 38 | 12 / 38 |
| white-01 / E64 | 46 | 36 | 34 | 6 / 30 | 6 / 28 |
| white-03 / K | 58 | 50 | 50 | 6 / 44 | 6 / 44 |
| white-06 / K | 45 | 31 | 30 | 7 / 24 | 7 / 23 |
| ar1-18 / K | 62 | 34 | 34 | 8 / 26 | 8 / 26 |
| ar1-17 / K | 52 | 18 | 18 | 4 / 14 | 4 / 14 |
| ar1-04 / O | 57 | 9 | 6 | 4 / 5 | 1 / 5 |
| white-01 / O | 50 | 18 | 16 | 0 / 18 | 0 / 16 |
| white-03 / O | 50 | 11 | 3 | 2 / 9 | 0 / 3 |
| white-06 / O | 49 | 8 | 7 | 1 / 7 | 1 / 6 |
| ar1-18 / O | 57 | 24 | 12 | 6 / 18 | 1 / 11 |
| ar1-17 / O | 58 | 14 | 14 | 6 / 8 | 6 / 8 |

Die gewöhnlichen Vergleichsarme besitzen ebenfalls Alternativen mit kleineren
Rasterfehlern. Bei white-01/O und white-03/O liegen die in allen vier Maßen
kleineren Alternativen ausschließlich in anderen Workern. Die Existenz solcher
Alternativen ist daher keine Besonderheit nur der auffälligen gewichteten Arme.

### Ursprüngliche Auswahl jedes Workers

Jede Zelle enthält **unregelmäßigen / regulären RMSE/|A|** des bereits im
jeweiligen Worker gespeicherten Gewinners. Fett markiert ist der anschließend
ursprünglich gewählte Paketworker. Hier wird kein Kandidat anhand der Wahrheit
neu zum Workergewinner gemacht.

| Fall / Arm | Worker 1 | Worker 2 | Worker 3 | Worker 4 |
| --- | --- | --- | --- | --- |
| ar1-04 / E1024 | **0,334601 / 0,346956** | 0,023657 / 0,023661 | 0,023860 / 0,023867 | 0,023324 / 0,023325 |
| white-01 / E64 | 0,326418 / 0,345056 | **0,331551 / 0,342934** | 0,014812 / 0,014810 | 0,014181 / 0,014180 |
| white-03 / K | 0,336926 / 0,352801 | 0,013154 / 0,013137 | 0,013953 / 0,013933 | **0,315540 / 0,354028** |
| white-06 / K | **0,238915 / 0,253850** | 0,011896 / 0,011891 | 0,333413 / 0,352674 | 0,011923 / 0,011918 |
| ar1-18 / K | 0,024808 / 0,024820 | **0,511525 / 0,086048** | 0,023840 / 0,023832 | 0,027707 / 0,027713 |
| ar1-17 / K | 0,022050 / 0,023613 | 0,031599 / 0,031607 | **0,036263 / 0,298079** | 0,026046 / 0,026072 |
| ar1-04 / O | 0,021650 / 0,021654 | **0,021074 / 0,021078** | 0,024846 / 0,024849 | 0,018547 / 0,018548 |
| white-01 / O | **0,018714 / 0,018703** | 0,013039 / 0,013035 | 0,228834 / 0,243177 | 0,009740 / 0,009738 |
| white-03 / O | 0,018165 / 0,018147 | **0,015500 / 0,015478** | 0,013996 / 0,013982 | 0,014828 / 0,014817 |
| white-06 / O | 0,011687 / 0,011683 | 0,013404 / 0,013412 | **0,014584 / 0,014593** | 0,014380 / 0,014375 |
| ar1-18 / O | **0,030018 / 0,030015** | 0,024993 / 0,024982 | 0,024993 / 0,024982 | 0,025233 / 0,025220 |
| ar1-17 / O | 0,030960 / 0,030965 | 0,025934 / 0,025953 | 0,038733 / 0,038748 | **0,026598 / 0,026617** |

Bei AR1-04/E1024 haben die drei anderen ursprünglichen Workerwahlen
unregelmäßige RMSE um 0,023–0,024; gewählt wurde der Worker mit 0,334601.
Bei white-01/E64, white-03/K und white-06/K unterscheiden sich bereits die
vier Workergewinner stark. AR1-17/K zeigt erneut die Bedeutung beider Raster:
0,036263 unregelmäßig steht 0,298079 regulär gegenüber. Auch white-01/O
enthält mit Worker 3 eine deutlich auffällige ursprüngliche Workerwahl,
obwohl die ursprüngliche Paketausgabe dieses gewöhnlichen Arms unauffälliger ist.

## Vollständige Originalformeln der sechs fokalen Diagnosezeugen

### ar1-04 / E1024 — m03/c007

Suchseed `1149751997`, Komplexität 13;
vollständige Identität `ar1-04--estimated_1024--m03--c007`.
Unveränderter Originaltext, `t` in Sekunden:

```text
exp(t / -0.007355894295831955) / (1.1600605091103315 / cos((-0.0073581726749401355 + t) / -0.0005997497131285459))
```

Die innere Division durch den Kosinus bleibt Teil dieses Originalbaums.
Der kleine Rasterfehler bescheinigt weder eine überall definierte Funktion
noch eine geglättete Ersatzformel oder stetige Erweiterung.

### white-01 / E64 — m03/c007

Suchseed `1803237116`, Komplexität 13;
vollständige Identität `white-01--estimated_64--m03--c007`.
Unveränderter Originaltext, `t` in Sekunden:

```text
(0.8963516814042254 * sin((-1655.6813492218027 * t) - 67.81932836410066)) * exp(-148.4863465046255 * t)
```

### white-03 / K — m02/c007

Suchseed `1544013876`, Komplexität 13;
vollständige Identität `white-03--known_covariance--m02--c007`.
Unveränderter Originaltext, `t` in Sekunden:

```text
cos((t / 0.0006004638485718354) - -0.264139083424147) / (exp(t / 0.0065007741528426075) - -0.07196918360649746)
```

### white-06 / K — m04/c006

Suchseed `695090960`, Komplexität 13;
vollständige Identität `white-06--known_covariance--m04--c006`.
Unveränderter Originaltext, `t` in Sekunden:

```text
-0.951223944126033 * (cos(-66.2175771806646 + (-1671.7565610796664 * t)) * exp(-153.81144174904375 * t))
```

### ar1-18 / K — m04/c010

Suchseed `1927678864`, Komplexität 16;
vollständige Identität `ar1-18--known_covariance--m04--c010`.
Unveränderter Originaltext, `t` in Sekunden:

```text
(exp(0.6873359721422668 * exp(-121.0832535081493 * t)) + -1.0089632846860723) * sin((0.0007836229350493434 - t) / 0.0006048118757697307)
```

### ar1-17 / K — m04/c006

Suchseed `1822901715`, Komplexität 13;
vollständige Identität `ar1-17--known_covariance--m04--c006`.
Unveränderter Originaltext, `t` in Sekunden:

```text
(cos((t * -1663.264813990282) + -129.0180952665811) * -0.8498407560684098) * exp(-135.8017708686615 * t)
```

## Herkunft, Prüfnachweise und Kosten

Ausgangsarchiv: `noise-background-manjaro-002-plots-recovered.tar.gz`,
SHA-256 `b2a4ace2d9097099822ab524377537dae24d59c7ba59e137de11ae5ba3e4214d`.
Ursprünglicher Ausführungscommit:
`bd42634b888c2dbaa5a92726b9a1f9851c766a48`.
Der Serienbericht ist unverändert unter SHA-256
`659f60e8521ba21d012ce3d2202d556e666c1f1cc8b01cf7452cc7f81dc6fdd3` gebunden.
Die dokumentarische Ausgangsfassung ist
`2d19e7eb43944a50dbc4da129111d87a7478f0cf`; sie ersetzt keine Ausführung.

Der Hauptaudit bestätigt alle 636 Kandidatenzeilen einschließlich HOF-Formel,
Baum, Verlust, Komplexität, Worker-/Seedzuordnung und ursprünglicher Auswahl.
Alle 272 konsumierten Originaldateien sind vor und nach diesem Audit bytegleich.
Zehn analytische Kontrollen prüfen Konstanten, Zeitvariable, die sieben
Operatoren und nichtfinite Division. `consumed-sources.json` bindet die
Quellen; `audit-payload-sha256.json` bindet die erzeugten Nutzdateien.

Verwendeter Auditor `audit_candidates.py`, SHA-256
`c7794503a3f6220e5d7476a5f32c8c2262b23ead168529224af6db040f16dcc5`,
Python 3.12.14 und NumPy 2.5.3. Gemessene Auditzeit einschließlich
Kandidatenexport, ohne abschließendes Schreiben von Bericht und Manifest:
**14,911596 s**, CPU User/System 14,352819/0,633441 s,
Prozess-Spitzen-RSS 150.340 KiB. Diese Werte betreffen ausschließlich die
lesende Diagnose und sind keine neuen Suchkosten.

Die unabhängige Gegenprüfung `independent-check.json` besteht ebenfalls.
Sie verwendet den gebundenen kanonischen Baum-Evaluator aus `bd42634` und
skalare `math.hypot`-Residuenstatistik, ohne den Hauptauditor zu importieren.
Alle 1.216.668 Zusatzvorhersagen sind bitgleich; alle 81.408 nativen
Trainingswerte, Originalauswahlen, Zählungen und Zeugen sind unverändert
beziehungsweise bestätigt. Größte absolute RMSE-Abweichung: 5,55×10⁻¹⁷;
die Maximalfehler zum neuen Export stimmen exakt. Der Vergleich mit den
ursprünglichen Serienmaxima weicht um höchstens 4,44×10⁻¹⁶ ab.
272 Originalquellen und 1.913 Nutzdateien sind geprüft; alle konsumierten
Dateien bleiben bytegleich. Prüfkosten ohne abschließendes Berichtsschreiben:
14,374101 s, CPU User/System 12,975916/1,270216 s,
Prozess-Spitzen-RSS 243.396 KiB. Die absoluten/relativen Prüftoleranzen
betragen 2×10⁻¹⁵ beziehungsweise 2×10⁻¹³; die beobachteten Abweichungen
liegen deutlich darunter.

Die vollständige Originalablage mit **18.166 Dateien** ist vor und nach
Kandidatenprüfung und unabhängiger Gegenprüfung gegen das Manifest des
vorherigen Gesamtaudits geprüft und bytegleich. Die Kontrollzeiten betragen
8,553852 s vorher und 5,763004 s nachher. Die Nachweise stehen in
`original-integrity-before.json` und `original-integrity-after.json`;
der gebundene Baseline-Manifesthash lautet
`c78905263585dd77ab18634c64ff8940a428a2a5a15d787a3b7b8f063fe3efa5`.

## Grafische Ausgaben und Sicherung

Die vollständigen Kandidatenmetadaten, Originalformeln und Punktdaten liegen
separat unter `candidates/<Fall>--<Arm>--mNN--cNNN.json`, `.formula.txt`
und `.points.csv`. Alle 636 Formeln und sämtliche 1.298.076 Punktzeilen
bleiben damit nachprüfbar; der Bericht zeigt nur die sechs ausdrücklich
diagnostischen Zeugen zusätzlich im Text.

Die vollständige portable Galerie `gallery-v2/index.html` enthält alle
636 Kandidatenplots, zwölf Fall-Arm-Übersichten als PNG/SVG/CSV, zwölf
verkleinerte Kontaktbögen und sechs direkte Gegenüberstellungen von
Originalauswahl und vorab definiertem Diagnosezeugen. Alle vollständigen
Originalformeln und Punktdateien sind verlinkt. Die 60 Dateien der zwölf
ursprünglichen Ergebnisplots bleiben separat bytegleich enthalten.

Das Paket `noise-background-manjaro-002-candidates-gallery-v2.zip` hat
**280.357.455 Bytes**, SHA-256
`2b031624e6ef6c764c63aa11621278bf08033169366780da98b03989c618780d`.
Es enthält 2.662 Dateien; ZIP-CRC und internes Hashmanifest sind geprüft.
Alle 1.974 Quellenkopien stimmen mit ihren Eingaben überein, 3.990 lokale
Linkvorkommen sind gültig und alle 648 neu erzeugten PNGs dekodierbar.
Die Daten werden ausschließlich an den vorhandenen Stützstellen dargestellt;
Markierungen ohne Verbindungslinien, Glättung oder neue Punkte erhalten
auch die großen Spitzen. Die Kontaktbögen sind ausdrücklich verkleinerte
Vorschauen und ersetzen keine Detailprüfung der vollständigen Bilder.

Der erste Galerieaufbau benötigte 184,131129 s. Bei der visuellen Prüfung
war ein angeschnittenes Y-Achsenlabel in einer Frontübersicht aufgefallen;
V2 korrigiert ausschließlich die Ränder der zwölf Front-PNG/SVG in weiteren
19,692853 s. Alle 636 Kandidatenbilder und numerischen Dateien bleiben
bytegleich, ebenso die Front-CSV; keine erneute numerische Auswertung.
V1 samt Archiv bleibt erhalten. Die beiden gebundenen Generatorfassungen
und getrennten Kosten stehen in den Galerieinventaren. Diese Aufbaukosten
sind keine Suchkosten der wissenschaftlichen Serie.

Die separate visuelle Gegenprüfung in `visual-check.json` besteht: alle zwölf
korrigierten Front-PNGs, sämtliche 636 Kandidaten auf den zwölf Kontaktbögen
sowie sechs fokale Originalauswahlen und ihre sechs Diagnosezeugen als
vollständige PNGs wurden gesichtet. Der Achsenbeschnitt ist behoben; weitere
konkrete Darstellungsfehler wurden nicht gefunden. Die großen Einzelabweichungen
von AR1-18/K und AR1-17/K bleiben vollständig sichtbar. Die Sichtungsdateien
sind an das V2-Manifest gebunden. Es wurde keine Pixel-für-Pixel-Prüfung aller
636 Vollbilder behauptet; SVGs sind gebunden, aber nicht separat gerendert.

Das kompakte Nachweispaket `noise-background-manjaro-002-candidates-audit.zip`
enthält Scope, Skripte, alle Kandidatenmetriken mit vollständigen Formeln,
Quellen-/Exportmanifeste sowie numerische, visuelle und Originalintegritätsbelege:
**1.092.966 Bytes**, SHA-256
`3a950150fc2470da8bd8df4f531ff0ee3dfd18d8cc7bbbed2988b2e77e400f0f`.
Die 22 Nutzdateien sind durch ein internes Manifest gebunden; alle enthaltenen
Hashes und ZIP-CRC sind geprüft. Die großen Punktdateien und Bilder gehören
zur separaten vollständigen Galerie. Beide Pakete ersetzen weder das
Originalarchiv noch die noch unbestätigte unabhängige Sicherung.

## Aussagegrenzen und Folgerung

Die Prüfung beschreibt vorhandene Kandidaten unter einer unveränderten
Auswahlregel. Ein kleiner Fehler auf beiden endlichen Zusatzrastern beweist
weder kontinuierliche Unauffälligkeit noch Zugehörigkeit zur Ringdown-Familie.
Es werden keine neuen Domain-, Struktur- oder Parameterzertifikate vergeben.
Der vollständige wissenschaftliche Bericht mit allen 130 Originalausgaben,
seinen geplanten Nennern und seinen Ergebnissen bleibt unverändert gültig.

Für alle sechs untersuchten auffälligen Ausgaben existierten bereits
Alternativen mit kleineren Fehlern auf beiden Zusatzrastern, auch im
ursprünglich ausgewählten Worker. Die Einordnung sollte deshalb die
**Eignung des Trainingskriteriums für die gewünschte Zwischenpunktqualität**
priorisieren. Der Audit bestätigt die gespeicherte Auswahlregel; er weist
keine abweichende Implementierung dieser Regel nach.

Mehr neue Suchseeds können die Variation und Häufigkeit solcher Ausgaben bei
festen Inputs beschreiben. Sie beheben die beobachtete Diskrepanz zwischen
Trainingsverlust und Rasterqualität nicht von selbst. Aus diesen nachträglich
gewählten sechs Fällen folgt weder eine Häufigkeit für alle 26 Fälle noch ein
Vergleich allgemeiner Such- oder Gewichtungsverfahren. Der zuvor skizzierte
624-Worker-Vergleich wäre gegebenenfalls eine getrennte Suchvariationsdiagnose,
keine bereits begründete Reparatur der Rekonstruktion.

Eine neue Auswahl-, Grammatik-, Frequenz- oder Samplingregel müsste mit
zulässigen Informationen und eigenständiger Begründung entwickelt werden.
Die hier bekannten Wahrheitswerte dienen ausschließlich der Diagnose; eine
an ihnen ausgewählte günstigere Originalformel wäre keine zulässige
nachträgliche Verbesserung der abgeschlossenen Studie. Die einfachere
Komplexität mehrerer Diagnosezeugen begründet ebenfalls keine automatische
Komplexitätsgrenze. Eine methodische Intervention und ihre unabhängige
Prüfung benötigen einen separaten Versuchsplan.

Dieser Nachtrag beschließt keine neuen Seeds, Budgets, Methodenänderungen
oder wissenschaftlichen Laufaufträge. Eine Anschlussstudie benötigt ihr
eigenes vorher festgelegtes Protokoll. Ein unabhängiges Backup des
Originalarchivs und der getrennten Diagnoseartefakte bleibt gesondert
gemäß [Archivierungsrichtlinie](results_archiving.md) nachzuweisen.
