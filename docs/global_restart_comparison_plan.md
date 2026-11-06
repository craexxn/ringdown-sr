# Globale Neustarts gegenüber längerer Einzelsuche

Eingefrorenes Entwicklungsprotokoll vom 06.11.2026 zu
[Leitfadenphase 3](ringdown_recovery_roadmap.md). Plan und maschinenlesbare
Konfiguration werden vor Implementierung gemeinsam committed und durch SHA-256
gebunden. Die wissenschaftliche Ausführung ist ein separater Manjaro-Schritt.

## Begründung und Grenzen

Die [begrenzte Frontdiagnose](endfront_diagnostic_001.md) fand in keiner der
35 Nicht-A-Fronten eine alternative A-Kurve, insbesondere nicht in den drei
frischen Transfer-Referenzen. Ein konkreter vorrangiger technischer Fehler wurde
im geprüften Umfang nicht gefunden. Deshalb wird die bereits vorgesehene
Suchintervention untersucht. Ein Vorteil globaler Neustarts ist eine Hypothese;
Literatur und bisherige Befunde beweisen ihn nicht. Die vier bekannten, gezielt
gewählten Entwicklungsfälle liefern keine allgemeine Erfolgswahrscheinlichkeit.

## Eingaben, Profil und Ausführung

Alle Zellen verwenden dieselben 128 Ankerwerte `t=j/4096` Sekunden,
`A=1`, `f=250 Hz`, `tau=0,008 s`, `phi=0` aus den unveränderten
[Transfereingaben](../data/transfer_check_inputs.npz). Datei-SHA-256:
`e4de71bb6aa5cb5e3afc72914466b997adb2ef6438bbe38d7baa421a85bd2628`.
Die vier bereits verifizierten Array-Fingerprints des vorhandenen
Einzelzellenadapters binden Training und 889 Zwischenpunkte zusätzlich.
Nur Trainingszeiten und Beobachtungen gelangen an die Suche.

Der unveränderte Worker der äußeren Staffel auf
`5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4` wird über den bestehenden
Einzelzellenadapter aufgerufen. Sein Profil bleibt: allgemeine Grammatik
`+, -, *, /, exp, sin, cos`, `should_simplify=false`, beide Häufigkeitsschalter
an, Float64, gewöhnliche MSE, zwei Populationen à 32, 50 Zyklen je Iteration,
maxsize/maxdepth 20, Parsimony 0, seriell/deterministisch, Haswell, Threadlimit 1.
Lokales Profil 300/5: 300 Optimiereriterationen und fünf **zusätzliche lokale**
Neustarts; unveränderter Newton-/BFGS-Pfad und 10.000 lokale Funktionsaufrufe.
Vier **globale** Neustarts sind dagegen vier vollständig neue SR-Suchen.
Keine Warmstarts, Templates, Startformeln, Nachfits oder Checkpointübernahme.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0 und SymbolicRegression 2.5.1 sowie
alle übrigen Versionen bleiben über die unveränderten Sperrdateien gebunden.
Aktueller Orchestrierungscommit und historischer Workercommit werden getrennt
aufgezeichnet. Vor der ersten Suche müssen alle Eingaben, Plan-/Quellenhashes,
Versionen, effektiven Python-Parameter, nativen Optionen und Referenzprüfungen
gespeichert und geprüft sein. Abweichende Umgebungen innerhalb der Serie
führen zum Integritätsabbruch, nicht zu einer nachträglichen neuen Gruppe.

## Vollständige Seeds und Reihenfolge

| Block | Referenzseed | Drei zusätzliche Seeds |
| --- | --- | --- |
| 1 | 20261201 | 20261221, 20261222, 20261223 |
| 2 | 20261210 | 20261231, 20261232, 20261233 |
| 3 | 20261211 | 20261241, 20261242, 20261243 |
| 4 | 20261212 | 20261251, 20261252, 20261253 |

Keine Seedüberschneidung zwischen Blöcken. Pro Block fünf frische Aufrufe:
Referenz 500, lange Einzelsuche 2.000 mit demselben Referenzseed, danach die
drei zusätzlichen Seeds mit jeweils 500. Blöcke in Tabellenreihenfolge,
alle Worker seriell. Diese Reihenfolge behauptet keinen vollständigen
Ausgleich von Aufwärm- oder Zeittrends; Zeiten werden einzeln berichtet.
Die vier 500er-Suchen bilden gemeinsam das Neustartpaket. Die Referenz ist
zugleich dessen erstes Mitglied: **20 reale Aufrufe, keine 24**.
Der frische 2.000er-Lauf ist keine Fortsetzung des historischen 500er-Laufs.

Historische Referenzen werden in diesem Protokoll nicht übernommen. Ihre
Archive sind geprüft, die Gleichheit mit der noch ausstehenden konkreten
Manjaro-Umgebung ist aber nicht vorab belegt. Die 16-Aufruf-Alternative des
Leitfadens würde ein eigenes, vorher festgeschriebenes Wiederverwendungsprotokoll
mit vollständiger Optionen-/Versions-/Kostenbindung benötigen. Kein Umschalten
nach Sichtung neuer Ergebnisse.

## Ressourcen, Ausfälle und Auswahl

Grenzen: 1.800 Sekunden je Suchworker, entsprechend der bestehenden äußeren
Staffel; 43.200 Sekunden für Vorbereitung, 20 Aufrufe, Nachrechnung und
Abschluss zusammen. Abbruchgrenzen sind keine Laufzeitprognose.
Keine vorzeitige Beendigung anhand von Wahrheit, Klasse, Struktur oder Raster.
Kein Neustarten fehlgeschlagener Zellen, keine Ersatzseeds und keine automatische
Verlängerung. Alle 20 geplanten Zellen und alle vier Blöcke bleiben sichtbar.

Ein gewöhnlicher Workerfehler oder Zeitablauf wird mit Teilstand, Fehlerstatus
und tatsächlich verfügbarer Kosteninformation erhalten; die übrigen geplanten
Zellen werden weiterbearbeitet. Nichtendliche native Trainingsverluste sind
keine auswählbaren Ergebnisse. Unbekannte Kosten bleiben unbekannt, niemals
null. Ein Signal, Gesamtfristablauf, Quellenänderung oder fehlgeschlagener
Integritätsnachweis sperrt den Gesamtabschluss. Nicht ausgeführte Zellen bleiben
als solche erhalten; keine positiven Aggregate aus einer abgebrochenen Serie.

Die Originalauswahl jeder Suche bleibt minimale endliche native Trainings-MSE,
danach Komplexität, danach ursprünglicher Frontindex. Innerhalb des Viererpakets
werden die unveränderten Ausgaben erfolgreicher Mitglieder nach nativer
Trainings-MSE, dann Komplexität, dann vorab festgelegter Mitgliedsposition
0, 1, 2, 3 geordnet. Ein Paket liefert **genau eine** Ausgabe oder den Status
fehlgeschlagen, wenn keine auswählbare Ausgabe vorliegt. Fehlerhafte Mitglieder
bleiben im Paket und Kostennenner. Kein Ersatz durch einen diagnostisch besseren
Kandidaten. „Passender Kandidat irgendwo vorhanden“ wird getrennt ausgewiesen.

## Unregelmäßiges Zusatzraster

Vor der ersten Suche werden 1.024 Punkte im offenen Trainingsintervall erzeugt:
`t_j=(j+u_j)/1024 * (127/4096)`, `j=0,…,1023`, mit unabhängigem
`numpy.random.Generator(PCG64(2026110601))` und `u_j` gleichverteilt in `(0,1)`.
Treffer auf dem regelmäßigen 1/32768-Sekunden-Raster werden verworfen und für
denselben Stratum neu gezogen; höchstens 100 Versuche pro Punkt, sonst Abbruch.
Konkrete Float64-Punkte und zugehörige Referenzwerte werden vor Suchbeginn
gespeichert, per Hash gebunden und unverändert zur Nachrechnung verwendet.
Kein Zugriff auf den globalen NumPy-/Python-Zufallszustand oder Such-RNG.

Training und bisherige Zwischenpunkte liegen zusammen auf einem regelmäßigen
Raster von 1/32768 Sekunden und besitzen theoretische Frequenz-Aliase.
Das Zusatzraster reduziert diesen Blindfleck. Es ersetzt keinen Domainbeweis
und garantiert keine allgemeine Identifizierbarkeit. Ausschließlich zusätzliche
kontinuierliche relative RMS-/Maximalfehler, einschließlich nicht verfügbarer
Werte, berichten. Keine neue Bestehensgrenze, kein Ausschluss, keine Auswahl
und kein Stopp aufgrund dieses Rasters. Historische A–D-Regeln bleiben gleich.

## Endpunkte, Kosten und Anschlussentscheidung

Je Block drei Ausgaben: Referenz, lange Einzelsuche, Neustartpaket. Je Arm
Nenner vier einschließlich Ausfällen. Bestehende A–D-Kurvenklasse, gültige
Originalfamilie, Originaldomain, Fortsetzungen und quantifizierter Rest werden
getrennt nach den unveränderten Verträgen bewertet. A-Zahl ist der primäre
deskriptive Kurvenendpunkt; A plus gültige Originalfamilie ein getrennter
Strukturendpunkt. Ungeklärte Beweise werden nicht als widerlegt umgedeutet.
Neue physikalische Parameterübereinstimmung bleibt `not_assessed`.

Alle drei paarweisen Kontraste mit vier Blockpaaren, sämtliche Gewinne und
Verluste sowie kontinuierliche Fehler beider alten Raster und des Zusatzrasters
berichten. Keine gepoolte Erfolgsrate über historische Serien, keine
Signifikanz- oder allgemeine Wahrscheinlichkeitsaussage.

Kosten: reale Workerzeit, Zeit jedes Adapteraufrufs, gesamte verstrichene Zeit
und native Zielfunktionsaufrufe während des Fits. Je Algorithmusarm die Summe
seiner Mitglieder, bei Neustarts also alle vier, einschließlich Ausfällen.
Die gemeinsame Referenz zählt zum Aufwand beider verglichenen Algorithmen,
im real neu ausgeführten Gesamtaufwand jedoch nur einmal. Hier sind historische
Kosten null und zusätzlicher Aufwand gleich realem Gesamtaufwand. Nominale
Iterationssummen sind keine Kostengleichheit. Vor-/Nachprüfungen und JIT-Anteile
bleiben in den gemessenen Zeiten erkennbar; unbekannte Kosten verhindern eine
vollständige Kostenaussage und werden nicht durch Schätzwerte ersetzt.

Vorab festgelegte Anschlussregel: Bei Integritätsfehlern zuerst deren Ursache
klären. Bei vollständiger Serie einen Anstieg der A-Zahl gegenüber der Referenz
als Entwicklungssignal berichten, zusätzlich Strukturgewinne/-verluste und
reale Mehrkosten. Bei Gleichstand der A-Zahl ist kein Kurvengewinn belegt.
Zwischen gleich guten verbesserten Armen nur bei vollständig gemessenen Kosten
weniger Zielfunktionsaufrufe, dann weniger summierte Workerzeit bevorzugen;
sonst bleibt die Profilentscheidung offen. Keine Entscheidung anhand des
Zusatzrasters. Das ist eine praktische Entwicklungsregel, kein Literaturstandard.

Ein verbesserter Arm mit vier A-Ausgaben wird zur bewussten Profilübernahme und
unabhängigen Bestätigung vorgeschlagen; offene formale Fragen separat erhalten.
Ohne solchen Befund kommt höchstens die bereits vorgesehene Zeitnormalisierung
als zweite begründete Suchintervention infrage. Kein automatischer Anschlusslauf.
Höchstens zwei Interventionen, danach unabhängige Bestätigung und Entscheidung
über den Rauschpilot. Die dort diskutierten 8/10 je Signal bleiben eine noch
festzulegende praktische Grenze. Vor dem Pilot müssen allgemeiner Laufweg und
Spezialprofil übereinstimmen; Gewichtung muss Struktur- und Konstantensuche
weiterhin gemeinsam bestimmen.

## Technische Prüfung und Archivierung

Technische Integration ausschließlich auf acht separaten Punkten `y=1+t`,
Seed 73 und äußeren Budgets 2, 3, erneut 2. Dieselben Profil-/Suchaufrufwächter,
Vorhersage-/Verlustreplays und Quellenbindungen wie wissenschaftlich; kein
Ankersignal und keine wissenschaftliche Serie in CI. Wiederholte technische
Front bitgleich, lesende Nachrechnung aller gespeicherten Ergebnisse.
Python-Gegenfälle prüfen insbesondere deterministische Paketauswahl unabhängig
von Wahrheit, Ausfallnenner, Raster-RNG, geplante Aufrufzahl, Quellenänderung und
späte Unterbrechung der Veröffentlichung. Vollständige Ready-CI bleibt nötig.

Originalfronten, Fehler und vollständige Nachweise unverändert erhalten;
separater lesender Bewertungs-/Verifikationsexport. Gesamtes Ergebnisarchiv im
gemeinsamen Archivordner und eine geprüfte zweite Kopie auf unabhängigem
Datenträger/Backup gemäß [Archivregel](results_archiving.md), SHA-256 und
tatsächlichen Ausführungscommit im [Ergebnisindex](results_index.md) zuordnen.
GitHub-Upload optional. Dieses Protokoll belegt weder eine Ausführung noch
bereits vorhandene Archivkopien.
