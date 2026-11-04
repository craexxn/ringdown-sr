# Ergebnis: äußere Iterationsstaffel bei lokalem Profil 300/5

Stand: 04.11.2026. Alle 20 frischen Manjaro-Zellen sind abgeschlossen und
unabhängig nachgerechnet. **500 statt 200 äußere Iterationen erhöhen die
Kurvenerfolge von 1/5 auf 5/5 und die planmäßig unterstützten Originalauswahlen
von 1/5 auf 4/5.** Auch 2.000 und 5.000 erreichen jeweils 5/5 Kurvenerfolge,
bei deutlich höherem Aufwand. Ihre formale Strukturzählung liegt bei 3/5
beziehungsweise 2/5.

Dieser Rückgang belegt keine schlechtere physikalische Rekonstruktion:
Eine getrennte nachträgliche Diagnose zeigt, dass alle sechs kurvengenauen,
formal nicht unterstützten Originalauswahlen reell auf eine Ringdown-Form
zurückgeführt werden können. Der vorhandene Erkenner deckt diese Schreibweisen
nicht ab. Die vorab festgelegten Zählungen und Originalauswahlen bleiben
unverändert. 500 äußere Iterationen bei lokal 300/5 sind damit eine sparsame
Arbeitsgrundlage für die nächste begrenzte Prüfung am neuen Signal,
kein belegtes allgemeines Optimum.

## Herkunft und selbst ausgeführte Nachrechnung

Originalarchiv `outer-ladder-manjaro-001.tar.gz`, selbst berechneter SHA-256:
`ac7e841b79042e216d6aacae2961ffb8395f298bbcc7ecc11f1092c90b3deb40`.
Die übermittelte Zeichenfolge hatte 63 statt 64 Zeichen und entspricht diesem
Hash ab der zweiten Stelle; das führende `a` fehlte. Die vollständige Prüfsumme
bezieht sich auf die tatsächlich hochgeladene Datei.

Sauberer Ausführungscommit `5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4`,
Squash-Merge von [PR #63](https://github.com/craexxn/ringdown-sr/pull/63).
Sein Dateibaum entspricht exakt dem technisch geprüften Head
`a47a273b6531ab4600633390e1b5ece1b4f0dfe2`.
Vor der Ausführung bestand die vollständige
[CI 41833474882](https://github.com/craexxn/ringdown-sr/actions/runs/41833474882):
2.279 Python-Tests, 272 native Optimierer-Assertions, 152 unabhängige/native
Assertions am festen 44-Baum-Nachweis und sämtliche technischen Integrationen.
Dies ist ein früherer Implementierungsnachweis, keine Wiederholung der Suite
für diesen reinen Ergebnisnachtrag.

Der [vor Code eingefrorene Plan](outer_search_ladder_plan.md) bleibt unverändert:
Commit `e1ea601286042aadcc5b5291ae72d114c7846dbf`, SHA-256
`95aca0069d6b8a6ad0305d5722c558e4bbea1c23e7f3b70630d2eb33e816fa35`.
Selbst ausgeführter lesender Audit:

- 545 Originaldateien, 544 Abschlussmanifest-Einträge, 542 ursprüngliche
  Verbrauchsanker und 86 gebundene Quellen geprüft. Quellen gegen
  Ausführungscommit und vertrauenswürdigen Checkout verglichen; Runtimekopien,
  Planbytes, saubere Herkunft, Datenbits und Datenrollen stimmen.
- Alle 20 festgelegten Zellidentitäten, Reihenfolgen und Budgets bestätigt:
  fünf neue gepaarte Seeds 20261201–20261205, vier äußere Budgets,
  fest 300 lokale Iterationen/fünf zusätzliche Neustarts, unrestricted und
  `should_simplify=false`. Native Optionsnachweise, konkrete Plugins,
  Vorprüfungen und tatsächliche Suchaufrufbelege stimmen.
- Alle **164 Originalkandidaten** durch den bestehenden Elternprüfpfad
  nachgerechnet: Verlust- und Rundungsnachweise, Residuen, Originalauswahl und
  Diagnosen stimmen. Alle Vorhersagereferenzen benötigen 128 Bit. Sämtliche
  Gruppenstatistiken, fünf Kontraste und 25 Seedpaaraufzeichnungen reproduziert.
- Sämtliche CSV-Ausdrücke mit beschränkter Syntaxauswertung gegen die
  Originalbäume, Reihenfolge, Komplexitäten und Verluste geprüft. Unabhängige
  skalare Baumrekursion bestätigt alle Kurvenmarker auf beiden Rastern.
  Auswahlregel, C-/S-Zählungen, beide Übergangsmatrizen sowie Zuordnung,
  Differenzen und Verhältnisse der Kosten zusätzlich unabhängig nachgerechnet.
- Alle 164 Originalbäume mit Julia 1.13.1 / SymbolicRegression 2.5.1 erneut
  nativ ausgewertet: Vorhersagen und Original-/Replayverluste sind bitgleich;
  Baumrundreise, Grammatik und Komplexität stimmen. Null Zielfunktionscallbacks,
  keine Suche, kein Fit und keine Optimierung.

Keine Archivprogramme oder serialisierten Suchzustände ausgeführt. Alle
Originaldateien blieben unverändert. Eigene Nachweise liegen unter
`/workspace/audits/outer-ladder-manjaro-001/`: `original_sha256.json`,
`audit.json`, `native_replay.json`, `independent_summary.json`,
`algebraic_diagnostic.json` sowie eigene Auditskripte und Logs.
Das ursprüngliche Eingangsarchiv `representation-manjaro-001.tar.gz` lag hier
nicht erneut vor; die enthaltenen eingefrorenen Datenkopien und Bindungen
wurden geprüft. Fünf Seeds am adaptiv untersuchten bekannten Signal sind
keine unabhängige Leistungsvalidierung.

## Vorab festgelegte Ergebnisse

C zählt Originalauswahlen am bekannten rauschfreien Signal, die auf Training
und den 889 inneren Achtelpunkten
jeweils relativen RMS ≤ 0,001 und relativen Maximalfehler ≤ 0,01 erreichen.
S verlangt zusätzlich beim selben Kandidaten erkannte Struktur, passende
Parameter und beide Replays. Gute ungewählte Kandidaten zählen separat.
Physikalische Identifikation bleibt `not_assessed`; der Blindfleck bei 8·fs
besteht weiter. Die Rasterprüfung innerhalb des Signalfensters ist kein
Nachweis für Extrapolation oder Übertragbarkeit auf andere Signale.

| Äußere Iterationen | C | S | Gute ungewählte Kandidaten | Median relativer RMS, Zwischenpunkte | Größter relativer RMS, Zwischenpunkte |
| --- | ---: | ---: | ---: | ---: | ---: |
| 200 | 1/5 | 1/5 | 3 | 0,0929283 | 0,58573 |
| 500 | 5/5 | 4/5 | 9 | 4,26417e-12 | 7,3001e-11 |
| 2000 | 5/5 | 3/5 | 12 | 1,80219e-12 | 4,87779e-12 |
| 5000 | 5/5 | 2/5 | 15 | 1,12996e-12 | 2,40343e-12 |

Bei 500 liegt selbst der größte Zwischenpunkt-RMS rund sieben Größenordnungen
unter der festgelegten RMS-Grenze. Höhere Budgets verkleinern die bereits sehr
kleinen numerischen Fehler teilweise weiter; daraus folgt kein zusätzlicher
Kurvenerfolg. Kein Budget ab 500 verliert in diesen fünf Seeds einen Kurvenerfolg.

S = planmäßig vollständig unterstützt; K = Kurvenerfolg ohne diese formale
Unterstützung; – = Kurvenkriterien nicht erfüllt.

| Seed | 200 | 500 | 2000 | 5000 |
| --- | --- | --- | --- | --- |
| 20261201 | – | S | K | K |
| 20261202 | – | K | S | K |
| 20261203 | – | S | K | K |
| 20261204 | – | S | S | S |
| 20261205 | S | S | S | S |

Die frühere lokale 300/5-Serie erreichte bei 200 Iterationen 3/5 Kurvenerfolge,
hier sind es 1/5. Es handelt sich um unterschiedliche Seedgruppen; dies ist
kein gepaarter Vorher-/Nachhervergleich der Implementierung.

## Alle fünf festgelegten Kontraste

Jeder Kontrast enthält dieselben fünf Seedpaare. Die 25 Paaraufzeichnungen
sind keine 25 unabhängigen Wiederholungen. Übergänge stehen in der Reihenfolge
0→0 / 0→1 / 1→0 / 1→1; negative Unterschiede bleiben sichtbar.

| Höheres minus niedrigeres Budget | Delta C | Delta S | C-Übergänge | S-Übergänge | Planmäßige Einordnung |
| --- | ---: | ---: | --- | --- | --- |
| 500 − 200 | +4 | +3 | 0 / 4 / 0 / 1 | 1 / 3 / 0 / 1 | `curve_and_supported_count_gain` |
| 2000 − 500 | +0 | -1 | 0 / 0 / 0 / 5 | 0 / 1 / 2 / 2 | `no_count_gain` |
| 5000 − 2000 | +0 | -1 | 0 / 0 / 0 / 5 | 2 / 0 / 1 / 2 | `no_count_gain` |
| 2000 − 200 | +4 | +2 | 0 / 4 / 0 / 1 | 2 / 2 / 0 / 1 | `curve_and_supported_count_gain` |
| 5000 − 200 | +4 | +1 | 0 / 4 / 0 / 1 | 3 / 1 / 0 / 1 | `curve_and_supported_count_gain` |

Von 500 auf 2.000 werden zwei unterstützte Seeds verloren und einer gewonnen;
S sinkt insgesamt um eins. Von 2.000 auf 5.000 geht ein weiterer unterstützter
Seed verloren. Alle betroffenen höheren Originalauswahlen bleiben kurvengenau.
Der folgende Zusatzbefund erklärt die formalen Ablehnungen, ersetzt diese
festgelegte Einordnung aber nicht.

## Nachträgliche Diagnose der sechs Erkennungsgrenzen

Diese begrenzte Untersuchung wurde erst nach Sichtung der Ergebnisse ergänzt.
Sie verändert weder den Erkenner noch S, die Originalauswahl oder einen
archivierten Status. Geprüft werden die reellen Funktionen der unveränderten
Originalbäume, getrennt von deren maßgeblicher Float64-Knotenrundung.

- Zellen 3 und 4 enthalten einen ausschließlich konstanten Kosinusausdruck
  innerhalb des linearen Exponenten. Dieser ist mathematisch ein konstanter
  Faktor; der vorhandene affine Parser weist ihn als
  `unsupported_affine_operator` zurück.
- Zellen 5, 8, 9 und 10 enthalten mehrere Exponentialfaktoren, die über
  `exp(a*t)/exp(b*t) = exp((a-b)*t)` beziehungsweise entsprechende Produkte
  zusammengefasst werden können. Der aktuelle Erkenner meldet
  `exponential_factor_count`. Zellen 9/10 enthalten außerdem einen konstanten
  Exponentialausdruck im Frequenzfaktor.

Beispielsweise hat Zelle 5 die Form
`sin(omega*t + delta) / exp(-47.623790805475*t) / exp(172.62379081423154*t)`.
Reell ergibt das einen einzelnen Exponentialfaktor mit b ≈ −125,00000000875654
pro Sekunde und einen Sinus mit omega ≈ 1570,7963267897142 pro Sekunde.

Für alle sechs Fälle wurden die Koeffizienten ausdrücklich aus den jeweiligen
Originalbäumen abgeleitet, ohne Fit und ohne Wahl anhand der Signalwahrheit.
Konstanten gehen mit ihren exakten gespeicherten Binary64-Werten ein.
Die Identitäten beruhen auf konstanten Faktoren, Exponentialproduktregeln
und `sin(x) = cos(x-pi/2)`. Eine gesonderte Hochpräzisionsrechnung bestätigt
sie an allen 1.017 vorhandenen Zeitpunkten bei 80 und 120 Dezimalstellen:
12.204 Punktvergleiche, maximale absolute Differenz jeweils unter 1e-70
beziehungsweise 1e-110. Das ist keine Behauptung bitgleicher Float64-Auswertung
nach algebraischer Umformung und kein nachträglich bestandener formaler
Parameter-/Aliasvertrag.

Reelle Darstellungsform `exp(b*t)*cos(2*pi*f*t+phi)` mit Amplitude 1;
ein negatives Frequenzvorzeichen wurde zusammen mit der Phase umgerechnet:

| Zelle | Iterationen | Formale Ablehnung | Abgeleitete f / Hz | Abgeleitete tau / s | Abgeleitete phi / rad |
| --- | ---: | --- | ---: | ---: | ---: |
| 3 | 5000 | `unsupported_affine_operator` | 250,0000000000088 | 0,008000000000000135 | 0 |
| 4 | 2000 | `unsupported_affine_operator` | 250,0000000000088 | 0,007999999999999107 | 0 |
| 5 | 500 | `exponential_factor_count` | 249,9999999991752 | 0,00799999999943958 | 3,0696273e-11 |
| 8 | 5000 | `exponential_factor_count` | 250,0000000000684 | 0,008000000000000798 | 0 |
| 9 | 2000 | `exponential_factor_count` | 250,000000000015 | 0,007999999999997783 | 0 |
| 10 | 5000 | `exponential_factor_count` | 250,000000000015 | 0,007999999999997783 | 0 |

Die abgeleiteten Frequenz- und Abklingzeitabweichungen liegen maximal bei rund
3,30e-12 beziehungsweise 7,01e-11 relativ zum bekannten Signal. Dieser Zusatz
spricht für eine begrenzte Abdeckung durch den Erkenner. Er rechtfertigt keine
Änderung von S auf 5/5 und keine Behauptung physikalischer Identifikation.
Vor einer Verwendung als Strukturstabilitätsmaß im Piloten muss die Abdeckung
solcher äquivalenten Schreibweisen gesondert festgelegt und geprüft werden.

## Gemessener Aufwand

Aufgezeichnete Gesamtdauer: **7.418,191988 Sekunden = 2 h 3 min 38,192 s**.
Zeitstempel: 04.11.2026, 13:47:07,995 bis 15:50:46,106 UTC.
Alle Worker bleiben unter 1.800 Sekunden; die Serie bleibt unter 14.400 Sekunden.

Zellzeit umfasst Armaufruf und Elternverifikation. Bereits das separate Feld
`status.json.total_wall_seconds` enthält Elternvorbereitung und Ergebnislesen.
Fitzeit enthält JIT und Export. Callbackzahlen sind keine Anzahl eindeutiger
Bäume oder lokaler Optimierungsschritte.

| Iterationen | Summe Zellzeit / s | Median Zellzeit / s | Summe Fitzeit / s | Fit-Callbacks |
| --- | ---: | ---: | ---: | ---: |
| 200 | 405,052507 | 78,044725 | 333,066972 | 27347093 |
| 500 | 679,400654 | 133,47032 | 608,65647 | 64210280 |
| 2000 | 2070,55842 | 399,71016 | 2001,72272 | 257447352 |
| 5000 | 4237,94014 | 856,3062 | 4167,90145 | 557967265 |

500 kostet rund 1,68-mal so viel summierte Zellzeit wie 200 und gewinnt vier
Kurvenerfolge sowie drei planmäßig unterstützte Auswahlen. Die Gruppen mit
2.000 und 5.000 benötigen beschreibend rund **3,05- bzw. 6,24-mal** die Zellzeit
der 500er-Gruppe. Der längste einzelne Zellabschnitt dauert rund 980,14 Sekunden.
Diese Kosten sind gemessen und nicht aus nominalen Iterationen hochgerechnet.

## Alle 20 Originalauswahlen

Index bezeichnet die ursprüngliche nullbasierte Kandidatenposition.
Die Formelausdrücke unten sind unverändert aus dem Archiv übernommen.
Keine diagnostische Ersatzwahl; vollständige Fronten bleiben im Originalarchiv.

| Zelle | Seed | Iterationen | Index | Komplexität | Kurve | Struktur | Parameter | Zwischenpunkt-RMS |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| 1 | 20261201 | 200 | 6 | 19 | outside_tolerance | not_supported | not_assessed | 0,0935616 |
| 2 | 20261201 | 500 | 6 | 17 | within_tolerance | recognized | matched | 4,26417e-12 |
| 3 | 20261201 | 5000 | 11 | 20 | within_tolerance | not_supported | not_assessed | 3,10491e-13 |
| 4 | 20261201 | 2000 | 8 | 20 | within_tolerance | not_supported | not_assessed | 3,20002e-13 |
| 5 | 20261202 | 500 | 7 | 16 | within_tolerance | not_supported | not_assessed | 5,38721e-11 |
| 6 | 20261202 | 2000 | 6 | 11 | within_tolerance | recognized | matched | 4,87779e-12 |
| 7 | 20261202 | 200 | 9 | 20 | outside_tolerance | not_supported | not_assessed | 0,58573 |
| 8 | 20261202 | 5000 | 5 | 16 | within_tolerance | not_supported | not_assessed | 2,40343e-12 |
| 9 | 20261203 | 2000 | 10 | 19 | within_tolerance | not_supported | not_assessed | 5,63158e-13 |
| 10 | 20261203 | 5000 | 9 | 19 | within_tolerance | not_supported | not_assessed | 5,63158e-13 |
| 11 | 20261203 | 500 | 7 | 15 | within_tolerance | recognized | matched | 1,63341e-12 |
| 12 | 20261203 | 200 | 12 | 20 | outside_tolerance | not_supported | not_assessed | 0,00682095 |
| 13 | 20261204 | 5000 | 5 | 17 | within_tolerance | recognized | matched | 1,80219e-12 |
| 14 | 20261204 | 200 | 10 | 20 | outside_tolerance | not_supported | not_assessed | 0,0929283 |
| 15 | 20261204 | 2000 | 5 | 17 | within_tolerance | recognized | matched | 1,80219e-12 |
| 16 | 20261204 | 500 | 6 | 11 | within_tolerance | recognized | matched | 7,3001e-11 |
| 17 | 20261205 | 200 | 6 | 15 | within_tolerance | recognized | matched | 3,25035e-12 |
| 18 | 20261205 | 500 | 6 | 13 | within_tolerance | recognized | matched | 2,32507e-12 |
| 19 | 20261205 | 5000 | 5 | 11 | within_tolerance | recognized | matched | 1,12996e-12 |
| 20 | 20261205 | 2000 | 5 | 13 | within_tolerance | recognized | matched | 2,32507e-12 |

Zelle 1, Seed 20261201, 200 äußere Iterationen:

```text
((352.54022093889296 * cos((t / -0.34307223864486275) - 3.071207973896114)) + 352.562128200511) * (cos(t / -0.0006365319539557038) + (0.023939609696546932 - 0.014965301701580603))
```

Zelle 2, Seed 20261201, 500 äußere Iterationen:

```text
cos(1.1875872794453841 * (t * 1322.678639273109)) * exp(((t * -673.4465065964314) / (1.3842749687171334 * 4.180108941056976)) / 0.9310716973803297)
```

Zelle 3, Seed 20261201, 5000 äußere Iterationen:

```text
exp((t * ((-1371.975246678472 * cos((0.014998137531816776 * 0.012291254180532297) * 0.012768723270683902)) / 3.1268620419104924)) / 3.5101650876453165) * cos(1570.796326794952 * t)
```

Zelle 4, Seed 20261201, 2000 äußere Iterationen:

```text
cos(1570.796326794952 * t) * exp((cos(0.012291254180532297 * (0.012291254180532297 * -0.015214491333470286)) / 3.5101650876453165) * ((t * -1371.975246678472) / 3.1268620419104924))
```

Zelle 5, Seed 20261202, 500 äußere Iterationen:

```text
(sin((1570.7963267897142 * t) - -1.570796326825593) / exp(-47.623790805475 * t)) / exp(172.62379081423154 * t)
```

Zelle 6, Seed 20261202, 2000 äußere Iterationen:

```text
sin((1570.796326793856 * t) - -1.5707963267973661) / exp(t * 124.99999999962567)
```

Zelle 7, Seed 20261202, 200 äußere Iterationen:

```text
sin((-21.10394571109521 / (exp((t * exp((-8.995720745355463 * -27.784265842924825) * t)) * -83.79088672524912) - -10.8447273498974)) * -64.5868484580443) * 0.6277932387630186
```

Zelle 8, Seed 20261202, 5000 äußere Iterationen:

```text
(cos(t * (1824.0128361217255 * 0.861176136312288)) / exp(t * 166.35386014780246)) * exp(t * 41.35386014781493)
```

Zelle 9, Seed 20261203, 2000 äußere Iterationen:

```text
(cos((-216.7896073476033 * 6.357677540617357) * (exp(0.13074750835081617) * t)) / exp(t * 44.58977868050383)) / exp(t * 80.41022131953082)
```

Zelle 10, Seed 20261203, 5000 äußere Iterationen:

```text
(cos((-216.7896073476033 * 6.357677540617357) * (exp(0.13074750835081617) * t)) / exp(t * 44.58977868050383)) / exp(t * 80.41022131953082)
```

Zelle 11, Seed 20261203, 500 äußere Iterationen:

```text
cos((-11.515375388274606 * -1.1452175519700407) * (-119.11152402481173 * t)) / exp((t * -5.943975260470755) * -21.02969721814339)
```

Zelle 12, Seed 20261203, 200 äußere Iterationen:

```text
(((0.03685782219805042 - t) / (((-0.014954267283285652 - t) * t) + -0.00016196436561146773)) / -228.27535889435313) * cos((-0.003999808944822285 - t) * 1570.803626514396)
```

Zelle 13, Seed 20261204, 5000 äußere Iterationen:

```text
exp((-104.61536121652809 * (-104.61536121652809 * -0.00955882566752567)) * (-0.00955882566752567 * (t * -124.99999999649421))) * cos(1570.7963267945743 * t)
```

Zelle 14, Seed 20261204, 200 äußere Iterationen:

```text
(((1497.0857159535813 * (0.026032482412634506 - t)) * (0.022955781268265654 - t)) - (t * -1.0498413766791563)) * sin(-1573.4776383500982 * (0.0030060658447451944 - t))
```

Zelle 15, Seed 20261204, 2000 äußere Iterationen:

```text
exp(-0.00955882566752567 * ((-104.61536121652809 * ((-104.61536121652809 * -0.00955882566752567) * t)) * -124.99999999649421)) * cos(1570.7963267945743 * t)
```

Zelle 16, Seed 20261204, 500 äußere Iterationen:

```text
exp(-125.00000001021827 * t) * sin(-4.7123889803439125 - (1570.796326806452 * t))
```

Zelle 17, Seed 20261205, 200 äußere Iterationen:

```text
cos(2.8078800752750293 * (-0.2672970348697686 * (t * 2092.8937486241894))) * exp(-15.236900189620274 * (8.203768381030732 * t))
```

Zelle 18, Seed 20261205, 500 äußere Iterationen:

```text
exp(-124.99999999966224 * t) * cos((2.8078800752750293 * (-0.2672970348697686 * t)) * 2092.8937486241894)
```

Zelle 19, Seed 20261205, 5000 äußere Iterationen:

```text
exp(t * -124.99999999990419) * cos((t * 1668.2993522528748) * -0.9415554376817998)
```

Zelle 20, Seed 20261205, 2000 äußere Iterationen:

```text
exp(-124.99999999966224 * t) * cos((2.8078800752750293 * (-0.2672970348697686 * t)) * 2092.8937486241894)
```

## Folgerung und begrenzter nächster Schritt

Für die nächste separat zu bindende Vorbereitung ist **500 äußere Iterationen
bei lokal 300/5** ein begründeter Kandidat: alle fünf Kurven sehr genau,
wesentlich geringerer Aufwand als 2.000/5.000. Ein allgemeines Optimum oder
die Übertragbarkeit auf neue Signalparameter und Rauschen ist damit nicht belegt.
Ein 10.000er-Lauf wird durch diese Ergebnisse nicht begründet.

Der optionale Anschlussvergleich mit 300/2 bleibt vorgemerkt, wurde aber weder
geplant noch gestartet. Er kann den zusätzlichen Aufwand der Neustarts klären;
aus diesem Ergebnis folgt keine automatische Wiederholung der ganzen äußeren
Staffel. Umfang, Reihenfolge und Zeitbudget müssen davor separat festgelegt
werden. Ebenso ist eine Erweiterung des Strukturerkenners ein eigener
Methodenschritt; im Ergebnisnachtrag wurde keine solche Änderung vorgenommen.

Die vereinbarte Pilotroute bleibt erhalten: begrenzter Transfercheck mit neuen
Signalparametern und bislang ungenutzten Seeds, Rauschpipeline, gebundenes
kompaktes Pilotdesign einschließlich Strukturstabilitätsmaß, Pilotauswertung
und Hauptversuchsplan. 8./9. November und etwa 15. November bleiben
Planungsziele. Keine Hauptstudie, größere Umstrukturierung, WSL2-Arbeit oder
Parallelisierung gestartet. Die vorgemerkte kurze Bereinigungsbestandsaufnahme
bleibt auf konkrete Wartungsprobleme begrenzt; numerische Verträge und
historische Originalartefakte werden erhalten.
