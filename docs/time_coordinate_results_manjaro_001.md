# Zeitkoordinatenvergleich auf Manjaro: Ergebnis 001

Quellenprüfung und Einordnung vom 12.11.2026, [Leitfadenphase 4](ringdown_recovery_roadmap.md).
Alle **16 geplanten wissenschaftlichen Suchen** sind abgeschlossen und am
Original lesend bestätigt. Die eingefrorene Richtungsregel ergibt **`mixed`**:
u=32t verbessert die hohe Variante, verschlechtert die niedrige. Kein allgemeiner
Vorteil einer Koordinate und keine automatische Profilübernahme.

| Signal | T: A / geplant | T: A plus Originalfamilie | U: A / geplant | U: A plus Originalfamilie | U: ausgewählte Beweise ressourcenbegrenzt |
| --- | ---: | ---: | ---: | ---: | ---: |
| anchor | 2/2 | 0/2 | 2/2 | 0/2 | 2/2 |
| variant_low | 2/2 | 2/2 | 1/2 | 0/2 | 2/2 |
| variant_high | 1/4 | 1/4 | 3/4 | 2/4 | 2/4 |

T ist die ursprüngliche physische Zeit t, U die gedehnte Zeit u=32t; beide in
Sekunden. Je gepaartem Seed jeweils eine frische Suche mit 2.000 äußeren
Iterationen, lokal 300 Optimiereriterationen plus fünf zusätzliche lokale
Neustarts. 16 Suchen liefern 16 Originalausgaben. Keine Ausfälle, ausgelassenen
Fälle oder historischen Wiederverwendungen; keine Auswahl zwischen T und U.

Die sechs U-Ressourcenbegrenzungen betreffen vier A- und zwei B-Ausgaben.
Sie sind **ungeklärte Familiennachweise**, keine bewiesene Nichtzugehörigkeit
und keine zusätzlichen bestätigten Erfolge. Der Kurvenkontrast ist auch ohne
Familienendpunkt gemischt; der Verlust auf variant_low lässt sich daher nicht
allein mit dieser Beweisgrenze erklären. Die Signale unterscheiden mehrere
Parameter gleichzeitig; keine isolierte Frequenz- oder Dämpfungsursache ableitbar.

## Original und Herkunft

- Original: `time-coordinate-manjaro-001.tar.gz`, **9.658.389 Bytes**.
- Selbst bestätigte SHA-256, identisch zur separat übermittelten Prüfsumme:
  `0d4a662010ad90ae3119a20154b7a39e839b1fbe61cb0adffdbedf51ee6ab4b9`.
- 1.212 reguläre Dateien, 72.035.452 entpackte Dateibytes. Drei wissenschaftliche
  Abschnitte mit benachbarter `-call.json`, gemeinsame Verifikation sowie der
  technische Manjaro-Vorlauf mit vier kleinen Workern und Einzel-/Gesamtprüfungen.
- Tatsächlicher sauberer Ausführungs- und lesender Prüfcommit:
  [`91d461cf9c08c07b7fdb8ddae5ad4b207135bc67`](https://github.com/craexxn/ringdown-sr/commit/91d461cf9c08c07b7fdb8ddae5ad4b207135bc67),
  main nach PR83. Der Dokumentationscommit ersetzt diesen Ausführungsstand nicht.
- [Plan](time_coordinate_plan.md), [Seeds/Eingaben](../data/time_coordinate_protocol.json)
  und Erzeuger vor Implementierung in `a77ee404d5d226544c6643d8500a9415631d9e16`
  eingefroren. Keine nachträgliche Änderung von Seeds, Auswahl, Kosten, Grenzwerten
  oder Beweisressourcen.

| Abschnitt | Beginn UTC | Berichtabschluss UTC | Gemessener vollständiger Aufruf |
| --- | --- | --- | ---: |
| time-coordinate-anchor-manjaro-001 | 12.11.2026 07:51:51 | 12.11.2026 08:28:00 | 2.169,198 s |
| time-coordinate-low-manjaro-001 | 12.11.2026 08:28:01 | 12.11.2026 09:07:32 | 2.371,925 s |
| time-coordinate-high-manjaro-001 | 12.11.2026 09:07:33 | 12.11.2026 10:17:26 | 4.193,693 s |

Die drei gemessenen Abschnittsaufrufe ergeben **8.734,817 s, rund 2 h 26 min**,
ohne Abschnittspausen, technischen Vorlauf und spätere Gesamtverifikation.
Vorbereitung und Veröffentlichung sind enthalten; die abschließende
Aufrufdatei und ihre Nachprüfungen liegen gemäß gespeicherter Messgrenze außerhalb.
Diese Zeit nicht mit den darin enthaltenen Fit-/Workerzeiten addieren.

Gemeinsame numerische Umgebung: Manjaro Linux 6.18.55-1, Intel Core i7-1165G7,
CPU-Affinität `[0]`, Julia Default-/Interactive-/GC-Threads 1/0/1, BLAS ein Thread,
Haswell-Kern; Python 3.12.14, Julia 1.13.1, PySR 2.6.0 und
SymbolicRegression 2.5.1. Gesperrte Pakete, tatsächliche Workerherkunft,
Adapter und effektive Optionen sind lesend gegen die Vorbereitung geprüft.

## Paarungen, Beweisgrenzen und Raster

| Signal | Block | T: Klasse / Originalfamilie | U: Klasse / Originalfamilie |
| --- | ---: | --- | --- |
| anchor | 1 | A / ungeklärt | A / ungeklärt |
| anchor | 2 | A / ungeklärt | A / ungeklärt |
| variant_low | 1 | A / nachgewiesen | A / ungeklärt |
| variant_low | 2 | A / nachgewiesen | B / ungeklärt |
| variant_high | 1 | B / ungeklärt | A / ungeklärt |
| variant_high | 2 | B / ungeklärt | A / nachgewiesen |
| variant_high | 3 | A / nachgewiesen | A / nachgewiesen |
| variant_high | 4 | B / ungeklärt | B / ungeklärt |

Die Originalauswahl bleibt die kleinste endliche native Trainings-MSE, danach
ursprüngliche Komplexität und Frontindex. Physische Komposition, Signalwahrheit,
Klassen, Struktur und Zusatzraster verändern diese Auswahl nicht. Eine Endfront
ist kein vollständiges Protokoll sämtlicher erzeugter Formeln.

Alle **188 Kandidaten in 16 gespeicherten Endfronten** nachgerechnet. In keiner
von fünf Fronten mit Nicht-A-Originalauswahl liegt ein anderer A-Kandidat.
Drei A-Originalauswahlen ohne Familiennachweis besitzen dagegen einen anderen
A-Kandidaten mit nachgewiesener Originalfamilie: anchor/T/Block 2 (Zelle 4),
anchor/U/Block 2 (Zelle 3) und variant_high/U/Block 1 (Zelle 2). Diese Kandidaten
haben jeweils einen höheren nativen Trainingsverlust und wurden nach der
vorgegebenen Regel korrekt nicht ausgewählt. Keine rückwirkende Ersetzung.

15 Frontkandidaten, darunter sechs ausgewählte U-Ausgaben, überschreiten nach
Komposition die 20-Knoten-Grenze. Die sechs ausgewählten Bäume haben 23–28
physische Knoten. T hat keine solche Kompositionsbegrenzung; seine beiden
A-Ankerformeln bleiben wegen `unsupported_normalized_factor` beziehungsweise
`nonaffine_argument` ungeklärt. Von den 16 ausgewählten Formeln sind neun über
dem ganzen Prüfintervall definiert nachgewiesen und sieben ungeklärt: sechs
Kompositionsgrenzen und variant_high/T/Block 2 mit
`denominator_zero_set_unresolved`. Kein neuer Definitionslückennachweis oder
stillschweigende Gleichsetzung von „ungeklärt“ mit „gültig“ oder „ungültig“.

Originalbaum q und physisches Modell q(32t) bleiben getrennt gebunden. Die reine
Variablensubstitution kann den exportierten 20-Knoten-Vertrag überschreiten;
in diesen Fällen bleiben Struktur, Domain und Rest ungeklärt, obwohl die Kurve
weiter bewertet wird. Die Grenze wurde weder erhöht noch durch Vereinfachung
umgangen. Neue Parameterübereinstimmungen bleiben `not_assessed`.

Relative RMS-/Maximalfehler der **ursprünglich ausgewählten** physischen Modelle,
für die Darstellung gerundet; Rohwerte und maßgebliche Binary64-Entscheidungen
bleiben im Originalbericht erhalten. 128 Trainings-, 889 reguläre Zwischen-
und 1.024 vorab gebundene unregelmäßige Punkte je Ausgabe.

| Signal / Block / Arm | Training RMS / Max | Zwischenpunkte RMS / Max | Zusatzraster RMS / Max |
| --- | ---: | ---: | ---: |
| anchor / 1 / T | 4.357e-04 / 4.348e-04 | 4.328e-04 / 4.028e-04 | 4.332e-04 / 4.043e-04 |
| anchor / 1 / U | 4.476e-04 / 3.330e-04 | 4.517e-04 / 3.037e-04 | 4.518e-04 / 3.050e-04 |
| anchor / 2 / T | 1.465e-12 / 9.593e-13 | 1.509e-12 / 9.696e-13 | 1.510e-12 / 9.692e-13 |
| anchor / 2 / U | 3.668e-13 / 1.966e-13 | 3.778e-13 / 1.982e-13 | 3.777e-13 / 1.982e-13 |
| variant_low / 1 / T | 6.196e-12 / 6.742e-12 | 6.293e-12 / 6.775e-12 | 6.295e-12 / 6.774e-12 |
| variant_low / 1 / U | 2.107e-04 / 2.782e-04 | 2.054e-04 / 2.680e-04 | 2.057e-04 / 2.740e-04 |
| variant_low / 2 / T | 1.730e-09 / 1.006e-09 | 1.756e-09 / 1.001e-09 | 1.756e-09 / 1.001e-09 |
| variant_low / 2 / U | 2.008e-03 / 2.194e-03 | 1.960e-03 / 2.117e-03 | 1.962e-03 / 2.162e-03 |
| variant_high / 1 / T | 2.285e-03 / 1.776e-03 | 2.269e-03 / 1.802e-03 | 2.272e-03 / 1.823e-03 |
| variant_high / 1 / U | 1.237e-11 / 1.417e-11 | 1.276e-11 / 1.467e-11 | 1.274e-11 / 1.464e-11 |
| variant_high / 2 / T | 5.137e-03 / 3.393e-03 | 5.197e-03 / 3.481e-03 | 5.200e-03 / 3.495e-03 |
| variant_high / 2 / U | 1.152e-11 / 7.467e-12 | 1.192e-11 / 7.759e-12 | 1.192e-11 / 7.747e-12 |
| variant_high / 3 / T | 1.891e-12 / 1.175e-12 | 1.943e-12 / 1.224e-12 | 1.943e-12 / 1.221e-12 |
| variant_high / 3 / U | 1.238e-12 / 1.557e-12 | 1.219e-12 / 1.644e-12 | 1.216e-12 / 1.642e-12 |
| variant_high / 4 / T | 2.562e-03 / 2.217e-03 | 2.561e-03 / 2.250e-03 | 2.566e-03 / 2.276e-03 |
| variant_high / 4 / U | 1.677e-03 / 1.306e-03 | 1.654e-03 / 1.304e-03 | 1.657e-03 / 1.319e-03 |

Das unregelmäßige Raster ist ausschließlich diagnostisch. Kontinuierliche
Fehler werden ohne neuen Bestehensmarker berichtet; historische A–D-Grenzen
bleiben unverändert. Es ersetzt keinen Definitionsnachweis.

## Beobachtete Kosten

| Signal | Arm | Worker s | Fit s | Adapter s | CPU Nutzer / System s | Verlustcallbacks |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| anchor | T | 1.109,965 | 1.074,061 | 1.114,342 | 1.100,323 / 3,402 | 128.426.400 |
| anchor | U | 944,756 | 906,786 | 948,783 | 936,468 / 3,181 | 110.687.058 |
| variant_low | T | 1.193,056 | 1.157,678 | 1.196,860 | 1.183,872 / 3,359 | 150.129.119 |
| variant_low | U | 1.075,934 | 1.040,341 | 1.079,806 | 1.067,261 / 3,203 | 131.350.728 |
| variant_high | T | 2.108,335 | 2.038,188 | 2.116,242 | 2.091,376 / 6,486 | 270.409.946 |
| variant_high | U | 1.881,674 | 1.811,606 | 1.889,180 | 1.865,809 / 6,378 | 228.622.187 |

U benötigt auf anchor/variant_low/variant_high **14,88 % / 9,82 % / 10,75 %**
weniger Workerzeit und **13,81 % / 12,51 % / 15,45 %** weniger Verlustcallbacks.
Insgesamt 1.019.625.438 beobachtete Verlustcallbacks und 8.313,720 s Workerzeit;
der vollständige Abschnittsaufruf ist oben gesondert ausgewiesen. Einzelworker
benötigen 298,903–738,563 s. Separate JIT-Kosten und ein nativer Gesamtzähler
aller Evaluierungen sind nicht beobachtet; Callback-Aufrufe nicht damit gleichsetzen.

Alle sechs vorgesehenen Kostenfelder sind vorhanden; unbekannte Kosten wurden
nicht als null eingesetzt. Keine historischen Kosten. Die geringeren beobachteten
U-Kosten heben den Kurvenverlust auf der niedrigen Variante nicht auf und ändern
die eingefrorene Richtungsregel nicht. Kleine gezielt gewählte Entwicklungsfälle
ergeben weder eine allgemeine Erfolgsquote noch eine allgemeine Laufzeitgarantie.

## Tatsächlich ausgeführte Prüfung

Der unveränderte CLI-Gesamtverifikator am exakten sauberen Ausführungscommit
bestätigt alle 16 wissenschaftlichen Zellen, Originalauswahlen, physische Replays,
Kurven-/Familien-/Restbefunde, Quellen, Eingaben, Workerbelege, Kosten und die
gemeinsame Umgebung. **Alle drei wissenschaftlichen Exportdateien sind bytegleich**
zum gelieferten Prüfexport. Der technische Vorlauf mit vier kleinen Workern,
beiden Einzelprüfungen und gemeinsamer Verifikation ist ebenfalls bestätigt;
seine neun Exportdateien sind bytegleich. Keine neuen Fits oder Suchen ausgeführt.

Alle 100 gebundenen Quelldateien einschließlich sämtlicher 50 Python-Paketquellen
zusätzlich gegen den Git-Ausführungscommit geprüft. Alle 1.212 Originaldateien
und das Originalarchiv vor/nach der Prüfung unverändert. Ein erster lokaler
Leseversuch scheiterte an Julias schreibgeschütztem Paketcache; mit dem vorhandenen
Cachezugriff bestand die vollständige Prüfung ohne Änderung am Verifikator.
Das war kein Abbruch oder Wiederholungslauf der wissenschaftlichen Serie.

Zusätzliche unabhängige Nachzählung aus Workerdateien bestätigt alle 16
Originalauswahlen, Paarungen, Pflichtkosten und reguläre 2.000er-Abschlüsse.
Alle 188 Frontbewertungen mit unveränderten Kurven-/Struktur-/Restverträgen
kanonisch JSON-identisch nachgerechnet. Ein davon getrennter rekursiver
JSON-Baum-Replay in Float64 und Fehlerdifferenzen/-normen in Long-double-Präzision
bestätigen die Klassen aus Training und Zwischenpunkten sowie die kontinuierlichen
Fehler auf allen drei Rastern; maximale Metrikabweichung geteilt durch
`max(1, |gespeicherter Wert|, |eigener Wert|)` ist `2,22 × 10⁻¹⁶`. Dies ist keine zusätzliche
Familien- oder Parameterbeweisregel. Keine Archivprogramme oder serialisierten
Suchzustände ausgeführt. Skripte, Quellenmanifeste und Exporte im separaten Audit.

Die PR83-Implementierung ist bereits übernommen: vollständige
[CI 43168577591](https://github.com/craexxn/ringdown-sr/actions/runs/43168577591),
3.359 Pythonfälle und alle nativen Blöcke einschließlich vier neuer kleiner
Worker. Der bestätigte CI-Checkout `146dfbb75d93b145f6ea626c2db9317c77627392`
hat denselben Baum `4e2eae4f4b833b0da885ec6e2d8f649a7481db0b` wie der
Ausführungsmerge. Diese technische Abnahme ist vom hier geprüften
wissenschaftlichen Ergebnis getrennt. Für reine Ergebnisdokumentation werden
passende Dokumentationsprüfungen ausgeführt, keine erneuten nativen Suchen.

## Anschlussentscheidung vom 12.11.2026

Für die Vorbereitung des bereits vorgesehenen **4 × 1.000 gegen 2 × 2.000**
bleibt **T die gemeinsame Referenzkoordinate beider Arme auf allen Signalen**.
Begründung: Die Einordnung ist gemischt; ein allgemeiner Koordinatenwechsel
wird durch die eingefrorene Regel nicht gestützt. Mit unverändertem t lässt
sich die Budgetaufteilung gezielt an das bisherige Profil anschließen. Dies
behauptet keine Überlegenheit von T und widerlegt das positive U-Indiz auf der
hohen Variante nicht.

Ein signalabhängiger Wechsel zu U oder die jeweils bessere T-/U-Ausgabe würde
eine neue, nachträglich angepasste Methode bilden. Die geringeren U-Kosten
allein rechtfertigen die Übernahme bei gleichzeitigem Kurvenverlust nicht.
Keine zusätzlichen Koordinatenseeds bis zu einem gewünschten Ergebnis und
keine Erkennerentwicklung zur Verbesserung der Erfolgszahlen.

Der Anschlussvergleich erhält **vor Implementierung und wissenschaftlicher
Ausführung einen eigenen eingefrorenen Plan** mit neuen Seeds, Paarung,
verlustbasierter Paketwahl, genau einer Ausgabe je Paket, Ausfällen, vollständigen
Kosten und Anschlussregel. Lokal 300/5 und übrige Einstellungen bleiben fest;
je 4.000 äußere Iterationen bedeuten nicht gleiche Rechenkosten. Noch kein
startbereiter neuer Laufweg und kein Auftrag zur Wiederholung dieser Serie.

Die ursprüngliche [Bestätigung](restart_confirmation_results_manjaro_001.md)
bleibt negativ. Ihre drei Signale sind inzwischen Entwicklungswissen; eine
spätere unabhängige Bestätigung braucht unberührte Fälle. Höchstens zwei
begründete Suchinterventionen, bewusste Übernahme des gewählten Profils in den
allgemeinen gewichteten Laufweg und anschließende Entscheidung zum Rauschpilot
bleiben bestehen. Die praktische 8/10-Grenze gehört zur früheren Bestätigung,
nicht zu diesem kleinen Entwicklungsvergleich.

Original und separates Auditpaket sind im [Ergebnisindex](results_index.md#lesende-verifikation-des-zeitkoordinatenvergleichs-001)
zugeordnet. Arbeitskopien belegen keine dauerhafte gemeinsame Archivablage oder
unabhängige Zweitkopie. Beide Sicherungsnachweise bleiben gemäß
[Archivierungsrichtlinie](results_archiving.md) offen; GitHub-Uploads sind optional.
