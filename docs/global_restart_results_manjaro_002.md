# Globaler Neustartvergleich auf Manjaro: Ergebnis 002

Quellenprüfung und Einordnung vom 06.11.2026, [Leitfadenphase 3](ringdown_recovery_roadmap.md).
Alle 20 geplanten Suchaufrufe sind abgeschlossen und lesend nachgeprüft. Die
längere Einzelsuche und die Viererpakete erhöhen die A-Zahl gegenüber der
500er-Referenz von 1/4 auf jeweils 4/4. Die Originalfamilie ist bei drei langen
Ausgaben und allen vier Paketausgaben nachgewiesen. Der vierte lange Fall bleibt
formal ungeklärt; das ist kein Nachweis einer falschen Familie.

| Arm | A / geplant | A und gültige Originalfamilie | Verlustcallback-Aufrufe | Summierte Workerzeit |
| --- | ---: | ---: | ---: | ---: |
| Referenz: 1 × 500 | 1/4 | 1/4 | 64.445.891 | 721,065268 s |
| Lange Einzelsuche: 1 × 2.000 | 4/4 | 3/4 | 256.294.609 | 2.317,925009 s |
| Globale Neustarts: 4 × 500 | 4/4 | 4/4 | 235.178.451 | 2.645,587779 s |

Nach der vorab festgelegten Anschlussregel ist `restarts` der bevorzugte
Entwicklungsarm: gleiche verbesserte A-Zahl, aber 8,24 % weniger Verlustaufrufe
als die langen Suchen. Seine Workerzeit liegt zugleich 14,14 % höher. Ein
Laufzeitvorteil oder eine allgemeine Überlegenheit ist damit nicht belegt.
Vier gezielt gewählte bekannte Entwicklungsblöcke liefern keine allgemeine
Erfolgswahrscheinlichkeit und keine unabhängige wissenschaftliche Bestätigung.

## Original, Herkunft und unverändertes Design

- Originaldatei: `global-restarts-manjaro-002.tar.gz`, 6.108.115 Bytes.
- Selbst berechnete SHA-256, identisch zur separat übermittelten Prüfsumme:
  `115147b81234ab3abafcfe3de7f20ad2a7a31097eff8b455ec24d098fbc357d5`.
- Tatsächlicher sauberer Orchestrierungsstand:
  `b547bb3b1753235960cc0654f8cebd747fc1b2f3`, PR76-Merge.
- Historischer Worker:
  `5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4`.
- [Protokoll](global_restart_comparison_plan.md) und
  [Konfiguration](../data/global_restart_protocol.json): gebundener Commit
  `b00fc4a0a5a5a90e7d72f45d2b27788d1fd1585a`. Vollständige Seeds, Auswahl,
  Bewertungsverträge und Ressourcenregeln bleiben unverändert.
- Gespeicherte Zeitstempel: Beginn 06.11.2026 12:15:22,366806 UTC,
  Berichtabschluss 13:45:29,425269 UTC.

128 feste rauschfreie Trainingswerte und 889 Zwischenpunkte; lokal 300
Optimiereriterationen mit fünf zusätzlichen lokalen Neustarts, allgemeine
Grammatik, beide Häufigkeitsschalter an, `should_simplify=false`. Die effektiven
Optionen und gespeicherten Bibliotheks-/Herkunftsbelege wurden geprüft. Die
1.024 unregelmäßigen Diagnosepunkte mit eigenem RNG waren vor der Suche gebunden.
Sie beeinflussen weder Auswahl noch Stopp und erhalten keinen Bestehensmarker.
Das gemeinsame regelmäßige Raster der alten Punkte hat weiterhin theoretische
Frequenz-Aliase; das Zusatzraster ersetzt keinen Definitionsbeweis.

20 frische Aufrufe, keine historische Kontrollübernahme. Pro Block gehört die
500er-Referenz zugleich zum Viererpaket. Der 2.000er-Lauf ist eine frische Suche,
keine Checkpointfortsetzung. Der [Abbruchlauf 001](global_restart_results_manjaro_001.md)
bleibt getrennt; seine Zellen werden weder übernommen noch zusätzlich als
unabhängige Erfolge gezählt. Seine bekannten Teilkosten bleiben zusätzlicher
Entwicklungsaufwand, unbekannte Gesamtkosten bleiben offen.

## Auswahlen und sämtliche paarweisen Kontraste

| Block / Startseed | Referenz | Lange Suche | Gewähltes Paketmitglied |
| --- | --- | --- | --- |
| 1 / 20261201 | Zelle 1: A, Familie nachgewiesen | Zelle 2: A, Familie nachgewiesen | Zelle 1, Seed 20261201: A, Familie nachgewiesen |
| 2 / 20261210 | Zelle 6: D, Familie ungeklärt | Zelle 7: A, Familie nachgewiesen | Zelle 9, Seed 20261232: A, Familie nachgewiesen |
| 3 / 20261211 | Zelle 11: C, Familie ungeklärt | Zelle 12: A, Familie ungeklärt | Zelle 13, Seed 20261241: A, Familie nachgewiesen |
| 4 / 20261212 | Zelle 16: D, Familie ungeklärt | Zelle 17: A, Familie nachgewiesen | Zelle 19, Seed 20261252: A, Familie nachgewiesen |

Die Paketwahl wurde separat nachgerechnet: native Trainings-MSE, Komplexität,
vorab festgelegte Mitgliedsposition. Originalfrontindex und Originalauswahl
jedes Mitglieds bleiben erhalten. Kurvenklasse, Familie und Zusatzraster wurden
nicht als Auswahlkriterien verwendet. Jedes Paket liefert genau eine Ausgabe.

| Kontrast, jeweils vier Blockpaare | A-Gewinne / Verluste / Gleichstände | Gewinne / Verluste / Gleichstände bei A plus nachgewiesener Originalfamilie |
| --- | --- | --- |
| Lange Suche gegenüber Referenz | 3 / 0 / 1 | 2 / 0 / 2 |
| Neustartpaket gegenüber Referenz | 3 / 0 / 1 | 3 / 0 / 1 |
| Neustartpaket gegenüber langer Suche | 0 / 0 / 4 | 1 / 0 / 3 |

Der zusätzliche positive Familiennachweis im dritten Block bleibt ein eigener
Endpunkt. Bei Zelle 12 sind Originaldomain und Kurvenklasse bestätigt; die
Familienprüfung endet mit `trigonometric_product_not_supported`, die Restprüfung
mit `no_certified_rule_based_component`. Beide bleiben `unresolved`. Es wurde
kein Erkenner erweitert und kein ungeklärter Befund als Gegenbeweis umgedeutet.
Alle 20 Originalauswahlen sind auf dem geschlossenen Prüfintervall überall
definiert. Neue physikalische Parameterübereinstimmung bleibt `not_assessed`.

Zusätzliche Frontdiagnose: 190 gespeicherte Kandidaten; die 20 Originalauswahlen
verteilen sich auf 12 A, 3 B, 3 C und 2 D. In keiner der acht Nicht-A-Fronten
liegt ein anderer A-Kandidat vor. Diese Kandidatenzahlen sind keine zusätzlichen
unabhängigen Versuche. Die Endfronten bilden nicht die gesamte Evolution ab.

## Kontinuierliche Fehler

Relative RMS-/Maximalfehler, sechs signifikante Stellen; volle Präzision und
sämtliche Kandidaten verbleiben im Originalbericht. `reference`, `long` und
`restarts` bezeichnen die drei obigen Arme. Kein zusätzlicher Grenzwert und
kein Ausschluss anhand des unregelmäßigen Rasters.

| Block | Arm / Zelle | Klasse / Originalfamilie | Training RMS / Max | Zwischenpunkte RMS / Max | Zusatzraster RMS / Max |
| --- | --- | --- | --- | --- | --- |
| 1 | reference / 1 | A / proven_member | 4.13902e-12 / 2.23965e-12 | 4.26417e-12 / 2.25475e-12 | 4.26528e-12 / 2.25359e-12 |
| 1 | long / 2 | A / proven_member | 3.10777e-13 / 1.67255e-13 | 3.20002e-13 / 1.68643e-13 | 3.19956e-13 / 1.68449e-13 |
| 1 | restarts / 1 | A / proven_member | 4.13902e-12 / 2.23965e-12 | 4.26417e-12 / 2.25475e-12 | 4.26528e-12 / 2.25359e-12 |
| 2 | reference / 6 | D / unresolved | 0.07291 / 0.0684397 | 0.0730325 / 0.06679 | 0.07305 / 0.0668642 |
| 2 | long / 7 | A / proven_member | 1.01349e-12 / 5.47229e-13 | 1.04424e-12 / 5.52225e-13 | 1.04451e-12 / 5.51947e-13 |
| 2 | restarts / 9 | A / proven_member | 8.27305e-13 / 4.4717e-13 | 8.52152e-13 / 4.49085e-13 | 8.52045e-13 / 4.49529e-13 |
| 3 | reference / 11 | C / unresolved | 0.0174404 / 0.0147314 | 0.0175433 / 0.0140957 | 0.0175492 / 0.0141242 |
| 3 | long / 12 | A / unresolved | 0.000727037 / 0.000778295 | 0.000717215 / 0.000712872 | 0.000717976 / 0.000715799 |
| 3 | restarts / 13 | A / proven_member | 1.06872e-11 / 6.86579e-12 | 1.10094e-11 / 6.96199e-12 | 1.10188e-11 / 6.9621e-12 |
| 4 | reference / 16 | D / unresolved | 0.101886 / 0.0974626 | 0.101985 / 0.0956539 | 0.101991 / 0.0957355 |
| 4 | long / 17 | A / proven_member | 3.45721e-14 / 1.84158e-14 | 3.56872e-14 / 1.89015e-14 | 3.56598e-14 / 1.89571e-14 |
| 4 | restarts / 19 | A / proven_member | 3.03367e-12 / 2.44245e-12 | 3.12549e-12 / 2.49373e-12 | 3.12751e-12 / 2.49389e-12 |

## Kosten und Vollständigkeit

Alle 20 Zellen sind `completed`; keine fehlgeschlagenen, abgebrochenen oder
nicht ausgeführten Zellen innerhalb von 002. Alle vier Fälle je Arm bleiben
im Nenner. Die Kosten der vier Referenzen zählen sowohl zum Referenzalgorithmus
als auch zu ihren Paketen, zum real ausgeführten Gesamtaufwand aber nur einmal.
Die drei Armkosten dürfen deshalb nicht als reale Serienkosten addiert werden.

| Aufgezeichneter Aufwand | Wert |
| --- | ---: |
| 20 reale neue Suchaufrufe | 491.473.060 Fit-Callback-Aufrufe |
| Summierte Workerzeit | 4.963,512788 s |
| Summierte Bridge-Aufrufe (`adapter_call_wall_seconds`) | 5.002,122463 s |
| `total_wall_seconds` bis zum Aufbau des Abschlussberichts | 5.407,155744 s, rund 90,1 Minuten |
| Wiederverwendete historische Kosten | 0 |

Workerzeit bezeichnet hier das historische Feld `verified.json:worker_wall_seconds`;
Bridgezeit umfasst einen weiteren Aufrufbereich. Diese überlappenden Zeitfelder
werden nicht addiert. `total_wall_seconds` wird vor der abschließenden
Dateiveröffentlichung erfasst, ist also keine vollständige Aufrufmessung bis
Prozessende. Eine solche separate `-call.json` gibt es in PR76 nicht. Native
Verlustaufrufe sind keine verschiedenen Formeln und keine reine CPU-Zeit.
Reine JIT-Zeit, CPU-Verbrauch und vollständige historische Julia-/GC-Threadbindung
sind nicht nachträglich messbar. Laufzeiten sind beobachtete Wandzeiten dieser
Manjaro-Serie; die feste Reihenfolge gleicht zeitliche Lasttrends nicht aus.

## Tatsächlich durchgeführte Quellenprüfung

972 Dateien: 969 im Originalergebnis, drei im mitgelieferten Verify-Export.
Vollständiges Rohmanifest mit 965 Einträgen, beide Abschlussmanifeste,
363 Vorbereitungsbindungen, Inventar von 66 Orchestrierungsquellen und insgesamt
154 verschiedene Git-Commit-/Dateibindungen geprüft. Keine Sperre im Original
oder mitgelieferten Verify-Export. Beide sind `completed`; der Verify-Export
bindet den Originalbericht und meldet 20 geprüfte Zellen bei `search_calls=0`.

Die eigene Python-/MPFR-Nachrechnung am tatsächlichen PR76-Stand prüft alle
20 historischen Workerbelege und 190 Kandidaten, Eingabebits, Zusatzraster,
Originalauswahl, Kurven-/Struktur-/Restbefunde, Kosten, Kontraste und
Anschlussregel. Die drei Dateien des neu erzeugten Verifikationsexports sind
bytegleich zum mitgelieferten Export. Originalarchive und entpackte Dateien
blieben bis zum abschließenden Hashvergleich unverändert.

Der unveränderte CLI-Aufruf war hier vor der ersten Zellprüfung gescheitert:
sein Launcher wollte auch für `verify` die fehlende Julia-Installation
vorbereiten; der Netzzugriff war nicht verfügbar. Dieser Versuch bleibt gesperrt
erhalten und wird nicht als bestanden ausgegeben. Für den erfolgreichen eigenen
Audit wurde ausschließlich dieser Startschritt durch einen Python-Aufruf der
unveränderten historischen `verify`-Bridge ersetzt. Quellenbindungen,
Verifikationsregeln und Veröffentlichungsprüfungen blieben aktiv. Suchaufrufe
waren gesperrt; keine neue Suche, kein Fit und kein nativer Replay. Auditskript,
Startanpassung, Fehlernachweis und Verifikation sind im getrennten
[Auditpaket](results_index.md#zusatzdiagnosen-und-offene-sicherung) erhalten.

## Konsequenz und nächster abgegrenzter Schritt

Die eingefrorene Regel schlägt bei vier A-Ausgaben die bewusste Profilübernahme
und anschließend unabhängige Bestätigung vor. Dies ist ein Entwicklungssignal,
keine automatische Profilumstellung oder Freigabe des Rauschpiloten. Eine weitere
offene Suchoptimierung oder Zeitnormalisierung ist durch diesen Befund nicht
begründet. Der bereits vorher festgelegte begrenzte Halteregelvergleich aus PR77
bleibt ein separater Versuch mit unverändertem Protokoll.

Dessen technische Kontroll-Eignungsfunktion wurde auf dem nun geprüften Archiv
lesend ausgeführt: `eligible=false` für den gesamten Arm. In allen vier Zellen
2/7/12/17 fehlen die erforderlichen tatsächlichen CPU-/Julia-/GC-Threadbelege.
Die ausdrücklich vorbereitete Wahl `fresh_all` mit acht neuen Suchen bleibt
damit technisch begründet und unabhängig von diesen Kurvenergebnissen.
Ein Startbefehl belegt noch keine Ausführung dieses nächsten Versuchs.

Nach dem begrenzten Budgetvergleich Profil und Kostenregel bewusst festlegen,
das Profil in den allgemeinen Laufweg übernehmen und eine unberührte Bestätigung
vorab protokollieren. Vor dem Rauschpilot müssen allgemeiner Laufweg und
Spezialtreiber übereinstimmen; die Gewichtung muss weiterhin Struktursuche und
Konstantenoptimierung bestimmen. 8/10 je Signal bleiben ein noch festzulegender
praktischer Vorschlag, kein Literaturstandard. Archivablage und unabhängig
geprüfte zweite Kopie sind weiterhin im [Index](results_index.md) offen.
