# Zusatzbewertung Stufe 3: quantifizierte Reste der Originalauswahlen

Stand: 05.11.2026. Leitfadenphase 1, letzte Bewertungsstufe. Retrospektive,
lesende Anwendung auf vier verifizierte Originalarchive: **78 Originalauswahlen,
18 getrennte ursprüngliche Gruppen, Korpusstatus `complete`.** Keine neue Auswahl,
kein Fit und keine wissenschaftliche Suche.

Anwendungscommit: `97e02afca0591ba731fdb95f76eea4d8223cea99`.
Bewertungsfassung `ringdown-sr-supplemental-assessment-3`, Beweisfassung
`ringdown-sr-remainder-proof-1`. Das geschlossene Zeitfenster stammt aus den
verifizierten Trainingsdaten und beträgt überall exakt `[0,127/4096]` Sekunden.
[Vertrag und Grenzen](supplemental_remainder.md) wurden vor der Anwendung
festgelegt; Originalformeln und Referenzbits stammen ausschließlich aus den
gebundenen Archiven. CSV-Neubewertungen sind keine Entscheidungsgrundlage.

## Befund und Aussagegrenzen

Für 41 Originalauswahlen liegt jeweils genau eine regelbasiert erkannte
Ringdown-Komponente mit bewiesener Restschranke vor. Davon besitzen 40 den
exakten Nullrest. Ein Fall enthält einen nachweislich begrenzten Rest ungleich
null. 37 Auswahlen bleiben ungeklärt: 31 ohne zertifizierte Komponente im
beschlossenen Regelwerk, fünf wegen unvollständigem Originaldomainnachweis,
eine wegen der Analyseschrittgrenze (`transfer-manjaro-001`, `cell-12`).
Diese Zahlen beschreiben den Diagnoseumfang, keine gemeinsame Erfolgsquote.

Alle 78 Originalidentitäten, Auswahlindizes, Kandidaten, historischen Kennzahlen
und Kurvenklassen sind gegenüber der [Stufe-2-Anwendung](supplemental_structure_results_001.md)
unverändert. Ebenso unverändert sind deren getrennte Statusentscheidungen zu
Identität, Originaldomain, Originalfamilie und stetiger Fortsetzung.
Ein Nullrest macht eine Originaldefinitionslücke nicht gültig. Für
`local-optimizer-manjaro-001 / cell-10` und `transfer-manjaro-001 / cell-05`
gilt die Schranke auf dem Originalbereich und zusätzlich für die gesondert
bewiesene stetige Fortsetzung. Neue Parametermatches bleiben `not_assessed`.

### Nicht verschwindender Rest: duration-manjaro-004 / cell-09

Originalseed `20261105`, Bedingung `unrestricted`. Nach Zusammenfassen der
Originalkonstanten und Phasen hat die Formel die Gestalt
`(exp(-gamma*t) + epsilon) * sin(omega_original*t + phase)`.
Der regelbasierte Grundterm ist der gedämpfte Anteil; der Rest ist der
ungedämpfte Sinusanteil mit dem exakten konstanten Koeffizienten `epsilon`.

Die zertifizierte globale Schranke beträgt gerundet `B = 9.3484568e-14`.
Aus den exakten gespeicherten Referenzbits folgen getrennt:

| Referenzraster | Obergrenze RMS-Beitrag | Obergrenze Maximalbeitrag |
| --- | ---: | ---: |
| Training | 3.5765136e-13 | 9.3484568e-14 |
| Zwischenpunkte | 3.6702367e-13 | 9.3949789e-14 |

Diese Werte sind dimensionslose Anteile, keine Prozentangaben. Sie begrenzen
`Original minus Grundterm` im exakten reellen Modell. Weder ein Fehler des
Grundterms gegenüber der Signalwahrheit noch Float64-Auswertungsfehler sind
dadurch begrenzt. Die bisherige Kurvenklasse A und die ungeklärte exakte
Familienzugehörigkeit bleiben bestehen. Es gibt keine neue Schwelle oder
binäre Aussage „vernachlässigbar“.

Alle 41 Schranken konnten bereits auf dem ganzen Intervall bewiesen werden.
Mehrere Grundterme und adaptive Unterteilung treten in diesem Korpus nicht
auf; ihre Prüfung stammt aus den gesonderten Gegenfällen der Testsuite.
Die 37 ungeklärten Befunde sind keine Beweise einer unbeschränkten Restgröße.

## Getrennte ursprüngliche Gruppen

Die Nenner bleiben fünf beziehungsweise drei Originalauswahlen. Komponenten
werden separat gezählt und erzeugen keine zusätzlichen Versuche.

| Serie / Signal / Bedingung / äußeres Budget | Nenner | Restschranke bewiesen | Ungeklärt | Komponenten |
| --- | ---: | ---: | ---: | ---: |
| duration-manjaro-004 / anchor / unrestricted / 200 | 5 | 3 | 2 | 3 |
| duration-manjaro-004 / anchor / no_nested_trig / 200 | 5 | 1 | 4 | 1 |
| duration-manjaro-004 / anchor / no_nested_trig / 2000 | 5 | 3 | 2 | 3 |
| duration-manjaro-004 / anchor / unrestricted / 2000 | 5 | 4 | 1 | 4 |
| local-optimizer-manjaro-001 / anchor / local_100_2 / 200 | 5 | 1 | 4 | 1 |
| local-optimizer-manjaro-001 / anchor / local_300_2 / 200 | 5 | 2 | 3 | 2 |
| local-optimizer-manjaro-001 / anchor / local_300_5 / 200 | 5 | 3 | 2 | 3 |
| local-optimizer-manjaro-001 / anchor / local_100_5 / 200 | 5 | 1 | 4 | 1 |
| outer-ladder-manjaro-001 / anchor / local_300_5 / 200 | 5 | 1 | 4 | 1 |
| outer-ladder-manjaro-001 / anchor / local_300_5 / 500 | 5 | 5 | 0 | 5 |
| outer-ladder-manjaro-001 / anchor / local_300_5 / 5000 | 5 | 5 | 0 | 5 |
| outer-ladder-manjaro-001 / anchor / local_300_5 / 2000 | 5 | 5 | 0 | 5 |
| transfer-manjaro-001 / anchor / local_300_5 / 500 | 3 | 0 | 3 | 0 |
| transfer-manjaro-001 / frequency / local_300_5 / 500 | 3 | 1 | 2 | 1 |
| transfer-manjaro-001 / decay / local_300_5 / 500 | 3 | 1 | 2 | 1 |
| transfer-manjaro-001 / phase / local_300_5 / 500 | 3 | 2 | 1 | 2 |
| transfer-manjaro-001 / amplitude / local_300_5 / 500 | 3 | 1 | 2 | 1 |
| transfer-manjaro-001 / combined / local_300_5 / 500 | 3 | 2 | 1 | 2 |

## Einzelbefunde

Numerische Tabellenanzeigen sind gerundet; exakte rationale Hexwerte,
Koeffizienten, Gültigkeitsbereiche und Beweisschritte stehen unverändert in
`assessment_records.json`. Ein Strich bedeutet keinen bewiesenen Betrag,
nicht einen Nullrest. `no_certified_rule_based_component` benennt eine Grenze
des vereinbarten Erkenners und behauptet keine allgemeine Nichtzerlegbarkeit.

| Serie | Zelle | Seed | Kurve | Reststatus / Grund | Komponenten | B (gerundet) |
| --- | --- | ---: | --- | --- | ---: | ---: |
| duration-manjaro-004 | cell-01 | 20261103 | A | bound_proven | 1 | 0 |
| duration-manjaro-004 | cell-02 | 20261103 | A | bound_proven | 1 | 0 |
| duration-manjaro-004 | cell-03 | 20261103 | A | bound_proven | 1 | 0 |
| duration-manjaro-004 | cell-04 | 20261103 | A | bound_proven | 1 | 0 |
| duration-manjaro-004 | cell-05 | 20261104 | A | no_certified_rule_based_component | 0 | — |
| duration-manjaro-004 | cell-06 | 20261104 | A | bound_proven | 1 | 0 |
| duration-manjaro-004 | cell-07 | 20261104 | A | bound_proven | 1 | 0 |
| duration-manjaro-004 | cell-08 | 20261104 | A | bound_proven | 1 | 0 |
| duration-manjaro-004 | cell-09 | 20261105 | A | bound_proven | 1 | 9.3484568e-14 |
| duration-manjaro-004 | cell-10 | 20261105 | C | original_domain_completeness_unresolved | 0 | — |
| duration-manjaro-004 | cell-11 | 20261105 | D | no_certified_rule_based_component | 0 | — |
| duration-manjaro-004 | cell-12 | 20261105 | A | bound_proven | 1 | 0 |
| duration-manjaro-004 | cell-13 | 20261106 | A | bound_proven | 1 | 0 |
| duration-manjaro-004 | cell-14 | 20261106 | D | no_certified_rule_based_component | 0 | — |
| duration-manjaro-004 | cell-15 | 20261106 | D | no_certified_rule_based_component | 0 | — |
| duration-manjaro-004 | cell-16 | 20261106 | D | no_certified_rule_based_component | 0 | — |
| duration-manjaro-004 | cell-17 | 20261107 | C | no_certified_rule_based_component | 0 | — |
| duration-manjaro-004 | cell-18 | 20261107 | D | original_domain_completeness_unresolved | 0 | — |
| duration-manjaro-004 | cell-19 | 20261107 | C | no_certified_rule_based_component | 0 | — |
| duration-manjaro-004 | cell-20 | 20261107 | A | bound_proven | 1 | 0 |
| local-optimizer-manjaro-001 | cell-01 | 20261120 | C | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-02 | 20261120 | A | bound_proven | 1 | 0 |
| local-optimizer-manjaro-001 | cell-03 | 20261120 | A | bound_proven | 1 | 0 |
| local-optimizer-manjaro-001 | cell-04 | 20261120 | C | original_domain_completeness_unresolved | 0 | — |
| local-optimizer-manjaro-001 | cell-05 | 20261121 | C | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-06 | 20261121 | D | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-07 | 20261121 | C | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-08 | 20261121 | D | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-09 | 20261122 | A | bound_proven | 1 | 0 |
| local-optimizer-manjaro-001 | cell-10 | 20261122 | A | bound_proven | 1 | 0 |
| local-optimizer-manjaro-001 | cell-11 | 20261122 | C | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-12 | 20261122 | D | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-13 | 20261123 | A | bound_proven | 1 | 0 |
| local-optimizer-manjaro-001 | cell-14 | 20261123 | C | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-15 | 20261123 | B | original_domain_completeness_unresolved | 0 | — |
| local-optimizer-manjaro-001 | cell-16 | 20261123 | D | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-17 | 20261124 | A | bound_proven | 1 | 0 |
| local-optimizer-manjaro-001 | cell-18 | 20261124 | A | bound_proven | 1 | 0 |
| local-optimizer-manjaro-001 | cell-19 | 20261124 | C | no_certified_rule_based_component | 0 | — |
| local-optimizer-manjaro-001 | cell-20 | 20261124 | A | no_certified_rule_based_component | 0 | — |
| outer-ladder-manjaro-001 | cell-01 | 20261201 | D | no_certified_rule_based_component | 0 | — |
| outer-ladder-manjaro-001 | cell-02 | 20261201 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-03 | 20261201 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-04 | 20261201 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-05 | 20261202 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-06 | 20261202 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-07 | 20261202 | D | no_certified_rule_based_component | 0 | — |
| outer-ladder-manjaro-001 | cell-08 | 20261202 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-09 | 20261203 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-10 | 20261203 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-11 | 20261203 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-12 | 20261203 | B | no_certified_rule_based_component | 0 | — |
| outer-ladder-manjaro-001 | cell-13 | 20261204 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-14 | 20261204 | D | no_certified_rule_based_component | 0 | — |
| outer-ladder-manjaro-001 | cell-15 | 20261204 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-16 | 20261204 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-17 | 20261205 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-18 | 20261205 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-19 | 20261205 | A | bound_proven | 1 | 0 |
| outer-ladder-manjaro-001 | cell-20 | 20261205 | A | bound_proven | 1 | 0 |
| transfer-manjaro-001 | cell-01 | 20261210 | D | no_certified_rule_based_component | 0 | — |
| transfer-manjaro-001 | cell-02 | 20261210 | C | no_certified_rule_based_component | 0 | — |
| transfer-manjaro-001 | cell-03 | 20261210 | C | original_domain_completeness_unresolved | 0 | — |
| transfer-manjaro-001 | cell-04 | 20261210 | A | bound_proven | 1 | 0 |
| transfer-manjaro-001 | cell-05 | 20261210 | A | bound_proven | 1 | 0 |
| transfer-manjaro-001 | cell-06 | 20261210 | A | bound_proven | 1 | 0 |
| transfer-manjaro-001 | cell-07 | 20261211 | A | bound_proven | 1 | 0 |
| transfer-manjaro-001 | cell-08 | 20261211 | A | bound_proven | 1 | 0 |
| transfer-manjaro-001 | cell-09 | 20261211 | B | no_certified_rule_based_component | 0 | — |
| transfer-manjaro-001 | cell-10 | 20261211 | A | bound_proven | 1 | 0 |
| transfer-manjaro-001 | cell-11 | 20261211 | C | no_certified_rule_based_component | 0 | — |
| transfer-manjaro-001 | cell-12 | 20261211 | C | analysis_step_limit | 0 | — |
| transfer-manjaro-001 | cell-13 | 20261212 | C | no_certified_rule_based_component | 0 | — |
| transfer-manjaro-001 | cell-14 | 20261212 | B | no_certified_rule_based_component | 0 | — |
| transfer-manjaro-001 | cell-15 | 20261212 | D | no_certified_rule_based_component | 0 | — |
| transfer-manjaro-001 | cell-16 | 20261212 | A | bound_proven | 1 | 0 |
| transfer-manjaro-001 | cell-17 | 20261212 | B | no_certified_rule_based_component | 0 | — |
| transfer-manjaro-001 | cell-18 | 20261212 | D | no_certified_rule_based_component | 0 | — |

## Prüfnachweise

Auf dem Anwendungscommit bestanden **2.997 Pythonfälle in 359,89 s**, Ruff,
Format und Dokumentationsprüfung. Die reale Vorbereitungsbindung aller
57 Quellen-/Vertragsdateien wurde ohne Fit oder Suche geprüft. Die neuen
Gegenfälle umfassen Mehrfachmoden, exakte und fast gleiche Frequenzen,
Auslöschung, wachsende und singuläre Reste, beide Intervallränder, ungeklärte
Originaldomain, adaptive vollständige Abdeckung, Budgetende, Referenznormen,
ältere Snapshots, automatische/nachträgliche Ausgaben sowie Quellen- und
Veröffentlichungsmanipulationen. Die vollständige native Stufe-3-CI und der
separate Review von [PR #72](https://github.com/craexxn/ringdown-sr/pull/72)
sind bei diesem Anwendungsnachweis noch ausstehend;
ihren aktuellen Stand führt der [Fortsetzungsstand](representation_implementation_status.md).

Eine separat geschriebene Nachrechnung ohne Aufruf des produktiven Erkenners
oder Schrankenrechners bestätigte anschließend:

- die vier Archivanker, alle Ergebnisprüfsummen, vollständige Freigabe ohne
  Sperrdatei und die unveränderten Originalauswahlen/Statusentscheidungen;
- alle 41 Zerlegungen `f = g0 + r` aus Originalbäumen und exakten Koeffizienten
  mit SymPy 1.14.0;
- alle 41 vollständigen Intervallabdeckungen und Rest-Einschließungen mit
  `mpmath.iv` bei 640 Bit, jeweils innerhalb der veröffentlichten Schranken;
- die Bindung beider Referenzraster jeder Auswahl an Originalbits sowie
  82 getrennte Normierungen mit exakten rationalen Summen und Ungleichungen.

Die CAS-Kontrolle beweist keine Originaldomain durch Kürzung. Diese Nachrechnung
ist kein unabhängiges Vollständigkeitsergebnis für den Erkenner und kein
zusätzlicher nativer Julia-Replay. Die 40 Nullreste verlangen nur triviale
Rest-Einschließungen; die nichttriviale historische Schranke ist oben ausgewiesen.

## Verankerte Archive und Ergebnisartefakte

Ausgabeziel: `results/supplemental-remainder-all-001`. Die vier übernommenen
historischen Serienberichte sind bytegetreue Archivkopien. Gültigkeit verlangt
Manifest, `completed`-Bericht und das Fehlen von `ASSESSMENT_LOCKED` gemeinsam.

| Originalarchiv | SHA-256 |
| --- | --- |
| duration-manjaro-004.tar.gz | `c2d9e330770746030bab9467b682a6b595cac25aa132dbb4decd1c4b03472289` |
| local-optimizer-manjaro-001.tar.gz | `1ab8c0aa91436c4b169c6c6efa8053e04c47ef57d07915f36ac476483276866d` |
| outer-ladder-manjaro-001.tar.gz | `ac7e841b79042e216d6aacae2961ffb8395f298bbcc7ecc11f1092c90b3deb40` |
| transfer-manjaro-001.tar.gz | `e363fe1be629973a460fc6e2188bf680c21b2c5519d331bc7e257968dcaaa139` |

| Ergebnisdatei | SHA-256 |
| --- | --- |
| assessment_checksums.json | `1146994132031e954ac16c9797c19e7b17c8e95ecc006b40bab605ffb47edfd5` |
| assessment_records.json | `081e67eb1689b8e341adb4c22ef6a8ed72031cddb3b1bfeea27ab455e1dc73c2` |
| assessment_report.json | `5dda8f200cc112361b6c131bcb36f46243766610b7847a20a577ef7374b2a3e6` |
| assessment_summary.md | `64fa2b8a0ecda1a015ea61ecc0e6d0e9c1d2ef87e030d9597cdde903950bb473` |
| duration-manjaro-004-historical-report.json | `ba6ff1c5b1e8981898006d33f9f73934edbc234f00460f4283bd33889712ecb1` |
| local-optimizer-manjaro-001-historical-report.json | `a635585b09809eb2be3ec5b9bc006d83da2a0fa5f208822e934c3b82887e1e83` |
| outer-ladder-manjaro-001-historical-report.json | `b8920254f1bbe63619663d70871d992fcb19e016d15330fca8f7657c0653ca77` |
| transfer-manjaro-001-historical-report.json | `365a0e9cc3d6af48c512973b7649f5866c2769bf3c2a63914989d2cf3e78813c` |
