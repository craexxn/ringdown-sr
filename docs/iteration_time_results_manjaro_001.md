# Iterations- und Zeitbudgetvergleich auf Manjaro: Ergebnis 001

Quellenprüfung und Einordnung vom 06.11.2026, [Leitfadenphase 3](ringdown_recovery_roadmap.md).
Alle acht geplanten Suchen sind im ausdrücklich gewählten Modus `fresh_all`
abgeschlossen und lesend bestätigt. 2.000 Iterationen erreichen 4/4 A-Kurven,
400 Sekunden native Suchzeit 3/4. Beide Arme erreichen 3/4 Ausgaben mit A und
nachgewiesener Originalfamilie. Der Zeitarm verliert bei Seed 20261211 die
Klasse A, ohne bei einem anderen Seed einen Erfolg hinzuzugewinnen.

| Arm | A / geplant | A und gültige Originalfamilie | Verlustcallback-Aufrufe | Summierte Workerzeit |
| --- | ---: | ---: | ---: | ---: |
| I: 2.000 äußere Iterationen | 4/4 | 3/4 | 256.294.609 | 2.030,234544 s |
| Z: 400 Sekunden native Suchzeit | 3/4 | 3/4 | 222.147.044 | 1.776,309269 s |

Gemäß eingefrorener Regel ist dies `deterioration`: eine Verschlechterung der
A-Zahl dieser Entwicklungsfälle. Z benötigt insgesamt 12,51 % weniger Workerzeit
und 13,32 % weniger Verlustaufrufe, erreicht aber nicht dieselbe Kurvenqualität.
Daraus folgt kein Effizienzgewinn bei gleichwertigem Ergebnis. Vier bekannte
Seeds liefern keine allgemeine Erfolgswahrscheinlichkeit oder unabhängige
wissenschaftliche Bestätigung. Keine Zusammenfassung mit PR76 zu einer Erfolgsquote.

## Original, Herkunft und vorab gebundener Modus

- Original: `iteration-time-manjaro-001.tar.gz`, 2.630.267 Bytes.
- Selbst berechnete SHA-256, identisch zur separat übermittelten Prüfsumme:
  `b53f63ad9df07a1067d6909adf436ee9631b45b680ff274d5e7acafc4c9e81d9`.
- Tatsächlicher sauberer Ausführungsstand:
  `4df7ecaaaed0a6d235f7db104c6982bdfcabf048`, PR78-Merge mit übernommener
  PR77-Implementierung. Heutiger Dokumentationsstand und Ausführungscommit bleiben getrennt.
- [Eingefrorener Plan](iteration_time_budget_plan.md) und
  [Konfiguration](../data/iteration_time_protocol.json), gebundener Commit
  `1aeedcce6a0f6c5683b2c4176161e14ed83ffa6d`; beide Dateien gegen diesen
  Git-Stand und die Ausführungsquellen geprüft.
- Gespeicherter Beginn: 06.11.2026 13:56:32,163170 UTC;
  Berichtabschluss: 15:03:02,792837 UTC.

Vorbereitung und Bericht nennen `fresh_all`; keine wiederverwendete Zelle.
Die gespeicherte Begründung ist die unvollständige tatsächliche Julia-/GC-
Threadbindung im PR76-Format. Die [separate Quellenprüfung von Lauf 002](global_restart_results_manjaro_002.md)
bestätigt diese technische Lücke für alle vier historischen Kontrollen.
`control_eligibility=null` und `archive_sha256=null` im frischen Lauf sind keine
Behauptung einer gelungenen Kontrollübernahme. Alle I- und Z-Suchen sind neu;
der frühere PR76-Aufwand wird nicht als Aufwand dieses Ersatzversuchs gezählt.
Er bleibt separat dokumentierter Entwicklungsaufwand.

Reihenfolge pro Seed: I–Z, Z–I, I–Z, Z–I für 20261201, 20261210, 20261211,
20261212. 128 feste Trainingswerte des rauschfreien 250-Hz-Ankers, 889 reguläre
Zwischenpunkte; lokal 300 Optimiereriterationen und fünf zusätzliche lokale
Neustarts. Allgemeine Grammatik, beide Häufigkeitsschalter an,
`should_simplify=false`, `warmup_maxsize_by=0.0`, zwei Populationen à 32 und
übrige effektive Optionen sind gebunden. Keine globalen Neustarts innerhalb
dieses Versuchs und keine Checkpointfortsetzung. Originalauswahl nach endlichem
nativen Trainingsverlust, Komplexität und ursprünglichem Frontindex nachgerechnet.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0 und SymbolicRegression 2.5.1 bleiben an
die aufgezeichneten Versionen und Sperrdateien gebunden. Tatsächliche native
Belege aller acht Zellen: CPU-Modell Intel Core i7-1165G7, Architektur `tigerlake`,
Affinität `[0]`, Julia Default-/Interactive-/GC-Threads 1/0/1 und BLAS 1.
`OPENBLAS_CORETYPE=Haswell` ist die getrennte BLAS-Vorgabe, keine Behauptung
über das Hardwaremodell. Vorbereitung und Workerbelege stimmen überein.

## Sämtliche Paare und Beweisgrenzen

| Seed | I: Zelle / Klasse / Familie | Z: Zelle / Klasse / Familie | A-Kontrast Z gegenüber I |
| --- | --- | --- | --- |
| 20261201 | 1 / A / nachgewiesen | 2 / A / nachgewiesen | Gleichstand |
| 20261210 | 4 / A / nachgewiesen | 3 / A / nachgewiesen | Gleichstand |
| 20261211 | 5 / A / ungeklärt | 6 / B / ungeklärt | Ein Verlust |
| 20261212 | 8 / A / nachgewiesen | 7 / A / nachgewiesen | Gleichstand |

A: keine Gewinne, ein Verlust, drei Gleichstände. Beim getrennten Endpunkt
A plus nachgewiesene Originalfamilie: keine Gewinne oder Verluste, vier
Gleichstände. Die ungeklärte Familie von I/Z bei Seed 20261211 ist kein
Nachweis einer falschen Familie: I endet mit `trigonometric_product_not_supported`,
Z mit `unsupported_normalized_factor`. Keine Erweiterung des Erkenners zur
Verbesserung dieser Zahlen. Alle acht Originalauswahlen sind auf dem geschlossenen
Prüfintervall überall definiert; physikalische Parameter bleiben `not_assessed`.

76 gespeicherte Frontkandidaten; Originalauswahlen 7 A und 1 B. Auch in der
B-Front von Zelle 6 ist kein anderer A-Kandidat nachgewiesen. Diese Diagnose
ersetzt keine Originalauswahl; Endfronten sind kein vollständiges Evolutionsprotokoll.

## Kontinuierliche Fehler

Relative RMS-/Maximalfehler, sechs signifikante Stellen. Das unregelmäßige
Zusatzraster umfasst 1.024 vorher gebundene Punkte mit getrenntem PCG64-Seed
2026110601. Es beeinflusst weder Such-RNG, Auswahl noch Stopp. Keine neue
Schwelle, kein Bestehensmarker und keine Änderung historischer A–D-Klassen.
Es reduziert regelmäßige Rasteraliase, garantiert aber keine Identifizierbarkeit
und ersetzt keinen Domainnachweis.

| Seed / Arm | Zelle | Klasse / Familie | Training RMS / Max | Zwischenpunkte RMS / Max | Zusatzraster RMS / Max |
| --- | --- | --- | --- | --- | --- |
| 20261201 / I | 1 | A / proven_member | 3.10777e-13 / 1.67255e-13 | 3.20002e-13 / 1.68643e-13 | 3.19956e-13 / 1.68449e-13 |
| 20261201 / Z | 2 | A / proven_member | 3.10777e-13 / 1.67255e-13 | 3.20002e-13 / 1.68643e-13 | 3.19956e-13 / 1.68449e-13 |
| 20261210 / I | 4 | A / proven_member | 1.01349e-12 / 5.47229e-13 | 1.04424e-12 / 5.52225e-13 | 1.04451e-12 / 5.51947e-13 |
| 20261210 / Z | 3 | A / proven_member | 1.01349e-12 / 5.47229e-13 | 1.04424e-12 / 5.52225e-13 | 1.04451e-12 / 5.51947e-13 |
| 20261211 / I | 5 | A / unresolved | 0.000727037 / 0.000778295 | 0.000717215 / 0.000712872 | 0.000717976 / 0.000715799 |
| 20261211 / Z | 6 | B / unresolved | 0.00334085 / 0.00301152 | 0.00334898 / 0.00287906 | 0.00334953 / 0.00288501 |
| 20261212 / I | 8 | A / proven_member | 3.45721e-14 / 1.84158e-14 | 3.56872e-14 / 1.89015e-14 | 3.56598e-14 / 1.89571e-14 |
| 20261212 / Z | 7 | A / proven_member | 3.45721e-14 / 1.84158e-14 | 3.56872e-14 / 1.89015e-14 | 3.56598e-14 / 1.89571e-14 |

## Haltegründe und reale Kosten

Alle acht Zellen sind `completed`, keine Ausfälle oder nicht ausgeführten Fälle;
Nenner vier je Arm. I endet jeweils regulär bei 2.000 vollständig verarbeiteten
äußeren Runden (`iteration_limit`), Z jeweils mit `regular_timeout`. Kein
Reserveende, harter Workerabbruch oder verdeckter numerischer Fehler.

| Seed | Z: vollständige Runden / restliche verarbeitete Populationszyklen | Native Zeit bei letzter Prüfung | Überschreitung von 400 s | Workerzeit I / Z |
| --- | --- | ---: | ---: | ---: |
| 20261201 | 1.815 / 0 | 400,300504 s | 0,300504 s | 509,952517 / 445,096450 s |
| 20261210 | 2.110 / 0 | 400,048221 s | 0,048221 s | 425,109541 / 443,240424 s |
| 20261211 | 1.418 / 0 | 400,089173 s | 0,089173 s | 644,155956 / 444,784629 s |
| 20261212 | 1.950 / 1 | 400,041792 s | 0,041792 s | 451,016531 / 443,187766 s |

Zwei Populationen bilden eine volle Runde. Der einzelne zusätzliche verarbeitete
Zyklus bei Seed 20261212 ist keine volle weitere äußere Runde. Noch ausstehende
Arbeit bleibt `not_observed`; Aufwärmung und solche Arbeit können bereits
Callbackkosten verursachen. Bei Seed 20261210 ist Z teurer als I: 400 Sekunden
sind keine feste Iterationszahl und kein garantiert kleineres Budget je Seed.
Die monotone Gegenmessung weicht in allen acht Zellen um höchstens 0,006511
Sekunden ab, innerhalb der eingefrorenen Ein-Sekunden-Grenze.

| Gemessener Bereich | I | Z | Gesamt der acht neuen Suchen |
| --- | ---: | ---: | ---: |
| Fitzeit | 1.970,643496 s | 1.717,199823 s | 3.687,843318 s |
| Workerzeit | 2.030,234544 s | 1.776,309269 s | 3.806,543813 s |
| Adapteraufruf | 2.037,294395 s | 1.783,313467 s | 3.820,607863 s |
| Nutzer-CPU-Zeit | 2.012,728570 s | 1.760,808261 s | 3.773,536831 s |
| System-CPU-Zeit | 7,172360 s | 6,313741 s | 13,486101 s |
| Verlustcallback-Aufrufe | 256.294.609 | 222.147.044 | 478.441.653 |

Neue Kosten und Algorithmuskosten sind hier identisch; historische Importkosten
sind null, weil nichts importiert wurde. Die überlappenden Zeitbereiche werden
nicht addiert. Primäre Workerzeit ist `worker/status.json:total_wall_seconds`:
Elternvorbereitung, Workerstart/-warten und Ergebnislesen, ohne Adapterdiagnostik.
Sie ist nicht unverändert dieselbe Messgröße wie das historische PR76-Workerfeld.
Daher keine Rangfolge von PR76-Paketen und PR77-Z anhand dieser Zeitwerte bilden.
CPU-Zeit erfasst den Launcher und seine abgewarteten Nachkommen; reine
Kompilierzeit bleibt `not_observed`. Fitzeit umfasst Arbeit außerhalb der nativen
Hauptschleife; ihre Differenz zu 400 Sekunden ist keine isolierte JIT-Messung.

Die benachbarte `iteration-time-manjaro-001-call.json` ist im Originalarchiv
enthalten und bindet den Abschlussbericht. Aufrufmessung: 3.991,202339 Sekunden,
rund 66,5 Minuten; Nutzer-/System-CPU 3.951,250735 / 22,605508 Sekunden.
Gemessener Bereich: Eintritt in `run` bis Rückkehr der Veröffentlichung,
ohne abschließendes Schreiben der Timing-Datei und erneute Schlussprüfungen.
Der Bericht erfasst davor 3.990,757087 Sekunden. Beide Werte liegen unter der
Gesamtfrist von 7.200 Sekunden; die Aufrufmessung ist keine Messung bis zum
letzten Prozessende. Keine Kosten aus anderen Serien darin verstecken.

## Tatsächlich durchgeführte Prüfung und nächster Schritt

469 Dateien: 465 im Ergebnisordner, eine Aufrufmessung und drei Dateien im
mitgelieferten Verify-Export. 461 Rohmanifest-Einträge, Abschlussmanifeste,
163 Vorbereitungsbindungen, 88 Orchestrierungsquellen einschließlich aller
45 Python-Paketquellen und 128 unterschiedliche Git-Commit-/Dateibindungen
geprüft. Original und Verify-Export abgeschlossen, keine Sperre.

Die eigene lesende Python-/MPFR-Verifikation am tatsächlichen Ausführungscommit
bestätigt alle acht Zellen und 76 Kandidaten einschließlich Eingaben, Raster,
Originalauswahl, Kurven-/Familien-/Restbefunden, Timer-/Herkunfts-/Threadbelegen,
Kosten und eingefrorener Vergleichsregel. Alle drei erzeugten Verify-Dateien
sind bytegleich zum mitgelieferten Export; dessen `search_calls=0` und Bindung
an Bericht und Aufrufmessung sind bestätigt. Archiv und alle Originaldateien
blieben bis zum abschließenden Hashvergleich unverändert.

Für diesen Audit wurde nur der Start der Verify-Bridge angepasst: direkte
Python-Ausführung der unveränderten Prüffunktion ohne den hier unnötigen
Julia-Installationsschritt. Quellenbindungen und Veröffentlichungsprüfungen
bleiben aktiv; Suchfunktionen waren gesperrt. Keine Suche, kein Fit, kein
nativer Replay und kein Laden binärer Zustände. Der vollständige unveränderte
CLI-Laufweg wurde damit hier nicht erneut ausgeführt. Skripte, Dateimanifest,
Verifikation und Originalarchiv sind im getrennten [Auditpaket](results_index.md#lesende-verifikation-von-zeitbudgetlauf-001)
erhalten. Technische Manjaro-Vorlaufbelege sind hiervon getrennt.

**Einordnung vom 06.11.2026:** Das 400-Sekunden-Profil wird aufgrund des
A-Verlusts nicht zur Übernahme empfohlen. Kein nachträgliches Hochsetzen des
Budgets und keine neue Optimierungsschleife. Die im getrennten
[Neustartvergleich](global_restart_results_manjaro_002.md) bevorzugten Viererpakete
bleiben der Kandidat für die bewusste Profilübernahme und anschließende
unabhängige Bestätigung. Diese bekannten Entwicklungsseeds ersetzen sie nicht.
Nächster abgegrenzter Schritt ist die Festlegung des Profils im allgemeinen
Laufweg und des Bestätigungsprotokolls vor neuen Suchen, einschließlich
unberührter Fälle, Kosten-/Ausfallregeln und praktischer Entscheidungsgrenze.
8/10 je Signal bleibt ein Vorschlag, kein beschlossener Literaturstandard.
Gewichtung muss Struktur- und Konstantensuche bestimmen. Danach Rauschpilot;
Zeitnormalisierung bleibt nur die bereits bedingte zweite Intervention.

Original und Audit sind Arbeitskopien. Gemeinsame dauerhafte Archivablage und
SHA-256-geprüfte unabhängige Zweitkopien bleiben gemäß [Archivregel](results_archiving.md)
und [Index](results_index.md) nachzuweisen. Keine erneute Ausführung von 001 nötig.
