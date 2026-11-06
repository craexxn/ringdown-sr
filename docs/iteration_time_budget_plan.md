# Entwicklungsprotokoll: 2.000 Iterationen gegenüber 400 Sekunden

Vorabfestlegung vom 06.11.2026 zu
[Leitfadenphase 3](ringdown_recovery_roadmap.md). Dieses Dokument und die
[Konfiguration](../data/iteration_time_protocol.json) werden vor Implementierung
gemeinsam versioniert und durch Commit/SHA-256 gebunden. Wissenschaftliche
Ausführung bleibt ein eigener Manjaro-Schritt nach Übernahme der Umsetzung.
Das [PR76-Protokoll](global_restart_comparison_plan.md) bleibt unverändert und
wird separat ausgeführt; dieser Vergleich ersetzt seine 20 Suchen nicht.

## Kenntnisstand und Forschungsfrage

Bei dieser Vorabfestlegung liegen hier keine wissenschaftlichen PR76-Ergebnisse
vor; solche Ergebnisse wurden nicht zur Bewertung geöffnet. Bekannt sind die
historischen vier Serien, deren Neubewertung/Frontdiagnose sowie ausschließlich
technische PR76-Fixtures mit acht Punkten `y=1+t`. PR76 ist noch offen; zwei
externe Reviewbefunde werden vor Übernahme korrigiert und erneut vollständig
geprüft. Der neue Vergleich wird in einem getrennten Worktree vorbereitet.

Untersucht wird: Welche Rekonstruktionsqualität erreichen 2.000 äußere
Iterationen gegenüber 400 Sekunden verstrichener Suchzeit bei ansonsten
gleichem Profil? Ein Zeitlimit verändert zunächst den Haltepunkt. Es beweist
keine bessere Suchmethode und untersucht keine globale Neustartstrategie.
Qualität, reale Kosten und praktische Budgetsteuerung werden getrennt berichtet.

Die [historische äußere Staffel](outer_search_ladder_results_manjaro_001.md)
weist für fünf 2.000er-Läufe zusammen 2.001,72272 Sekunden Fitzeit aus:
Mittelwert 400,344544 Sekunden. Daraus stammen die festen 400 Sekunden.
Wegen anderer Zeitabschnitte, JIT, Rechnerlast und Umgebung ist dies nur eine
ungefähre Kostenangleichung. Vier bekannte Entwicklungsseeds tragen keine
allgemeine Erfolgswahrscheinlichkeits- oder Signifikanzbehauptung.

## Eingaben, Paarung und konstantes Profil

Seeds in fester Reihenfolge: **20261201, 20261210, 20261211, 20261212**.
Je Seed genau eine Ausgabe je Arm, einschließlich fehlgeschlagener Ausgaben:

| Arm | Reguläre Grenze | Herkunft |
| --- | --- | --- |
| I | 2.000 äußere Iterationen, kein Suchzeitlimit | Alle vier PR76-Einzelsuchen oder alle vier frisch |
| Z | 400 Sekunden im unten definierten Backendfenster; Reserve 1.000.000 | Vier frische Einzelsuchen |

Identische PR76-Eingabebits: 128 Trainingswerte `t=j/4096` Sekunden,
Amplitude 1, Frequenz 250 Hz, Abklingzeit 0,008 Sekunden, Phase 0. Die
[NPZ-Datei](../data/transfer_check_inputs.npz) trägt SHA-256
`e4de71bb6aa5cb5e3afc72914466b997adb2ef6438bbe38d7baa421a85bd2628`.
Die vorhandenen Array-Fingerprints binden außerdem die 889 Zwischenpunkte.
Nur Trainingszeiten und Beobachtungen gelangen an die Suche.

Profil wie PR76: lokal 300 Optimiereriterationen und fünf **zusätzliche lokale**
Neustarts; allgemeine Grammatik `+, -, *, /, exp, sin, cos`, beide
Häufigkeitsschalter an, `should_simplify=false`, Float64, gewöhnliche MSE,
zwei Populationen à 32, 50 Zyklen je äußerer Iteration, maxsize/maxdepth 20,
Parsimony 0, unveränderter Newton-/BFGS-Pfad und lokale Funktionsgrenze 10.000.
`warmup_maxsize_by=0.0` muss in den effektiven Optionen nachgewiesen sein.
Keine globalen Neustarts, Warmstarts, Startformeln, Templates, Nachfits oder
Checkpointübernahme. Nicht die allgemeinen Defaults 20/2 mit ausgeschalteten
Häufigkeitsschaltern verwenden.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1 und alle
übrigen unveränderten Sperrdateien binden die Versionen. Der historische
Staffelworker `5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4` bleibt erhalten.
Das Zeitprofil erhält einen eigenen versionierten Worker/Adapter. Seine
beabsichtigten Unterschiede sind Zeitgrenze, äußere Reserve und passive
Messung; tatsächliche Optionsunterschiede müssen vollständig geprüft werden.
Ausführung auf Manjaro, seriell, Haswell und Threads 1 für Julia, BLAS und
relevante Bibliotheken. Eine einzelne erlaubte CPU begrenzt zusätzlich die
gesamte neue Prozessgruppe; CPU-Affinität und native Threadbelege werden erfasst.

## Wiederverwendung vor Sichtung der Kurvenqualität entscheiden

Standardmodus `reuse_pr76`: alle vier 2.000er-Kontrollen aus PR76, Zellen
2, 7, 12, 17. **Vier neue Suchaufrufe**. Keine Teilübernahme, kein Ausschluss
erfolgloser Kontrollen und keine Auswahl anhand von Fronten, Kurven oder
Struktur. Auch gewöhnliche wissenschaftliche Ausfälle bleiben im Kontrollarm.

Die Eignungsprüfung bindet das unveränderte Originalarchiv samt SHA-256 und
vollständigen Integritäts-/Vorbereitungsnachweisen. Sie prüft die tatsächlichen
Orchestrierungs- und Workercommits, alle vier Seeds/Eingaben, effektive Optionen,
native Software-/Bibliotheksversionen, CPU-/Hardwareangaben, Threadbegrenzung,
Auswahlregeln und Definitionen der vorhandenen Kostenfelder. Verzeichnis- und
Ausgabepfade sind keine numerischen Unterschiede; andere Abweichungen werden
nicht stillschweigend normalisiert. Eine erfolgreiche Originalverifikation
ersetzt weder den Abgleich mit der neuen Umgebung noch die Prüfung der
aufgezeichneten Ausfälle. Herkunft, Ausfälle und Integrität müssen nach den
korrigierten PR76-Regeln bestätigt sein.

Fehlende Kontrollarchive sperren die unabhängige Implementierungsarbeit nicht.
Bis zur Prüfung lautet der Status **Wiederverwendung unbestätigt**. Fehlende
CPU-Zeit oder interne Timerwerte in historischen Kontrollen werden ausdrücklich
als nicht beobachtet übernommen; sie dürfen weder als null gelten noch durch
Schätzwerte ergänzt werden. Die vorhandenen Fit-/Workerzeitfelder müssen
interpretierbar und bei vorhandenen Messungen unverändert gebunden sein.

Ist der ganze Kontrollarm technisch/methodisch nicht nachweislich geeignet,
steht ausschließlich `fresh_all` als vorher festgelegter Ersatzmodus bereit:
alle vier I und alle vier Z frisch, **acht neue Suchaufrufe**. Keine automatische
Umschaltung oder Ausführung. Der ausdrücklich gewählte Modus, seine Begründung,
Eignungsprüfung, Quellen, Eingaben, effektiven Optionen und vollständige
Aufrufliste werden vor dem ersten neuen Fit gespeichert und gebunden.

In `reuse_pr76` liegen alle I zeitlich im vorherigen PR76-Lauf; danach Z in
Seedreihenfolge. Getrennte Ausführungszeiträume und Last-/Zeiteffekte bleiben
eine Einschränkung. In `fresh_all` gilt pro Seed **I–Z, Z–I, I–Z, Z–I**.
Kein Austausch einzelner Kontrollen nach Ergebniskenntnis. 400 Sekunden,
Seeds, Regeln und Reihenfolge ändern sich nicht durch PR76-Ergebnisse.

## Tatsächliche Timersemantik und Grenzen

Quellenprüfung der gebundenen Versionen: PySR reicht `timeout_in_seconds` an
native `Options` weiter. SymbolicRegression ruft erst `_warmup_search!`, dann
`_main_search_loop!`, anschließend `_tear_down!` auf. In der Hauptschleife
wird `start_time=time()` gesetzt. `check_for_timeout` vergleicht am Ende jedes
Schleifendurchgangs **`time() - start_time > timeout_in_seconds`**. Die
konkreten geprüften Quellhashes stehen in der Konfiguration.

Das **400-Sekunden-Fenster** beginnt an diesem nativen `start_time` nach
Initialisierung und Aufwärmzyklen. Es endet mit der ersten positiven
Zeitprüfung am Ende eines Hauptschleifendurchgangs. Eine natürliche Erschöpfung
der Reserve wird gesondert ausgewiesen, auch wenn die letzte Zeitprüfung zugleich
positiv ist. Die reguläre Zeitprüfung verwendet die Backend-Wanduhr `time()`;
zusätzliche monotone Abschnittsmessungen dienen der Diagnose und ersetzen sie
nicht. Deutliche Uhrsprünge dürfen nicht als belastbarer Zeitvergleich gelten.

Die Grenze ist kooperativ: laufende Zyklen, lokale Optimierung, Migration und
Frontausgabe werden nicht mitten im Schritt unterbrochen. Im seriellen Backend
kann vor der nächsten Zeitprüfung bereits ein weiterer Populationszyklus
ausgeführt sein. Überschreitungen sind möglich; 400 Sekunden sind keine harte
Obergrenze für Fit oder Worker. Initialisierung/JIT/Aufwärmung vor der
Hauptschleife sowie Abbau/PySR-Export danach liegen außerhalb dieses Fensters.
JIT oder Exportarbeit innerhalb der Schleife verbraucht dagegen Suchzeit.

Getrennt aufzeichnen: native Start-/letzte Prüfzeit und Überschreitung,
Hauptschleifen-/Aufrufabschnitte, tatsächliche Fitzeit (einschließlich JIT und
Python-Export wie bisher), Worker-/Adapterzeit, gemessene Nutzer-/System-CPU-Zeit
und Gesamtwandzeit. Nicht separat beobachtbare reine Kompilierzeit bleibt
`not_observed`; Vor-/Nachabschnitte werden nicht als reine JIT-Messung ausgegeben.
CPU-Zeit ist verbrauchte Prozessorzeit, keine andere Bezeichnung der Wandzeit.

Native verbleibende Populationszyklen erlauben, verarbeitete Zyklen und
vollständige Runden durch beide Populationen gesondert auszuweisen. Nicht in
die Endfront übernommene, schon berechnete Zyklen dürfen nicht als veröffentlichte
äußere Iterationen gelten. Bei historischen Kontrollen ohne solche Messung
bleibt der tatsächliche Zähler nicht beobachtet; das Sollbudget ist kein Zähler.
Zielfunktionsaufrufe stammen unverändert vom nativen Callbackzähler.

Reguläres Zeitende mit gültiger Front und vollständigen Nachweisen ist ein
normaler Abschluss. `iteration_limit`, `regular_timeout`, `iteration_reserve`,
`worker_timeout` und gewöhnlicher Fehler bleiben getrennte Gründe.
**1.800 Sekunden je Worker** sind ausschließlich die äußere Sicherheitsfrist.
Ein harter Sicherheitsabbruch ist kein erfolgreicher Zeitlauf.
**7.200 Sekunden** gelten für den neuen Aufruf einschließlich Vorbereitung,
Kontrollprüfung, neuen Suchen, Nachprüfung und Abschluss. Alte PR76-Zeiten werden
nicht erneut von dieser Frist abgezogen, zählen aber zu den Algorithmuskosten.

Alle Teilstände und Ausfälle erhalten. Keine Ersatzseeds, Wiederholungen,
automatischen Verlängerungen oder Auswahlstopps. Integritätsfehler, Wächterfehler,
Unterbrechungen und Gesamtfrist sperren vollständige positive Aggregate.

## Auswahl, Diagnose und vorher festgelegte Interpretation

Pro Suche bleibt die Originalauswahl: minimaler endlicher nativer
Trainingsverlust, dann Komplexität, dann ursprünglicher Frontindex. Wahrheit,
A–D-Klasse, Struktur und Zusatzraster dienen weder der Auswahl noch dem Stopp.
Nichtendliche Verluste sind nicht auswählbar; Ausfälle bleiben im Nenner vier
je Arm. „Passender Kandidat irgendwo vorhanden“ bleibt eine getrennte Diagnose.

[Kurvenvertrag](supplemental_assessment.md),
[Struktur-/Domainvertrag](supplemental_structure.md) und
[Resttermvertrag](supplemental_remainder.md) einschließlich Ressourcen bleiben
unverändert. A–D und kontinuierliche relative RMS-/Maximalfehler auf Training
und regelmäßigem Zwischenraster, Originalfamilie/-domain, Fortsetzung und
Restnachweise getrennt berichten. Gute Kurven mit ungeklärter Struktur bleiben
sichtbar; ungeklärt bedeutet keine bewiesene Nichtzugehörigkeit. Neue
Parameterübereinstimmungen bleiben `not_assessed`.

Das PR76-Zusatzraster mit 1.024 Punkten, unabhängigem PCG64-Seed 2026110601 und
vorab festgelegter Erzeugungsregel wird beibehalten. Im Wiederverwendungsmodus
die **gespeicherten Punkte und Referenzwerte** aus dem Original übernehmen,
an Hashes und Regel prüfen; keine Ersatzneuerzeugung für fehlende Evidenz.
Im frischen Modus vor der Suche erzeugen/speichern/binden. Kein Zugriff auf den
Such-RNG. Ausschließlich kontinuierliche Fehler, keine neue Schwelle oder
Ausschlüsse. Es reduziert regelmäßige Rasteraliase, ersetzt aber keinen
Domainnachweis und garantiert keine Identifizierbarkeit.

Primär die A-Zahl, separat A plus gültige Originalfamilie. Alle vier Paare mit
Kurven-/Strukturgewinnen, -verlusten, offenen Beweisen und kontinuierlichen
Fehlern zeigen. Keine gepoolte Quote mit anderen historischen Bedingungen.

- Mehr A bei höchstens gleichem vollständig gemessenem Workeraufwand:
  positives Entwicklungssignal für das Zeitprofil.
- Mehr A bei höherem Aufwand: Qualitätsgewinn mit Mehrkosten; kein isolierter
  Vorteil der Zeitgrenze.
- Gleiche A-Zahl: kein nachgewiesener Kurvengewinn; Fehler/Kosten weiter berichten.
- Weniger A: Verschlechterung in diesen Entwicklungsfällen.
- Unvollständige Kosten: keine vollständige Effizienzaussage. Strukturänderungen
  und ungeklärte Nachweise verschwinden in keiner automatischen Gesamtwertung.

Algorithmuskosten summieren alle vier Fälle einschließlich vorhandener
historischer Kosten. Neu ausgeführter Aufwand wird separat ausgewiesen;
unbekannte Kosten bleiben unbekannt. Keine automatische 60-Minuten-Serie,
Budgetstaffel oder breite Optimierung. Spätere Leitfadenphasen einschließlich
gegebenenfalls Zeitnormalisierung, bewusster Profilübernahme, unabhängiger
Bestätigung und Rauschpilot bleiben bestehen; höchstens zwei begründete
Suchinterventionen. Dieser begrenzte Halteregelvergleich eröffnet keine weitere
unbeschränkte Optimierungsschleife.

## Technischer Nachweis und Archivierung

Vor wissenschaftlicher Ausführung: tatsächliches kooperatives Zeitende mit
vollständiger Endfront, getrennte Sicherheits-/Fehlergründe, effektive Optionen,
RNG-Isolation, erlaubte Auswahl, Ausfallnenner/Kosten, Kontrollimport,
Quellenbindung und Widerruf bei späten Änderungen prüfen. Ausschließlich kleine
separate technische Fixtures in Cloud/CI. Deterministische Gegenprüfungen
vergleichen die Suchdynamik bis zu einem festgelegten Schritt, insbesondere
mit hoher Reserve und ohne Größenaufwärmung. Ein zusätzlicher Dynamikunterschied
muss vor Ausführung benannt und minimal behoben werden. Zeitbegrenzte
Wiederholungen versprechen keine bitgleiche Endfront.

Originalarchive unverändert erhalten, gemeinsamer Archivordner plus zweite
gesicherte Kopie auf unabhängigem Datenträger/Backup, SHA-256 beider Kopien
prüfen. Tatsächliche Ablage und Sicherung im [Ergebnisindex](results_index.md)
führen; [Archivrichtlinie](results_archiving.md) gilt. GitHub-Uploads optional,
keine großen Archive in Git. Noch keine Archivablage oder Sicherung bestätigt.
