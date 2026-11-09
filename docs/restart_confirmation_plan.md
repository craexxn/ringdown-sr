# Bestätigungsprotokoll: vier globale Neustarts gegenüber einer langen Suche

Vorabfestlegung vom 09.11.2026 zu [Leitfadenphasen 5/6](ringdown_recovery_roadmap.md),
auf main `294f4ab79ee2e9588f9e5021b996bad726187d41` nach Übernahme von PR79.
Dieser Plan, [Konfiguration](../data/restart_confirmation_protocol.json),
[Eingabedatei](../data/restart_confirmation_inputs.npz) und
[Eingabeerzeugung](../scripts/prepare_restart_confirmation_inputs.py) werden vor
Implementierung gemeinsam committed und über SHA-256 gebunden. Keine
wissenschaftliche Suche zur Wahl von Signalen, Seeds oder Grenzwerten.

## Fragestellung und beschlossener Umfang

Die bisherigen vier gezielt gewählten Entwicklungsblöcke ergeben bei 4 × 500
und 1 × 2.000 jeweils 4/4 A, mit 4/4 beziehungsweise 3/4 Familiennachweisen;
der übrige Nachweis ist ungeklärt. Pakete brauchen weniger Verlustaufrufe,
aber mehr Workerzeit. Der getrennte 400-Sekunden-Vergleich verliert einen
A-Erfolg. Diese Befunde begründen den Kandidaten und den Kontrollarm, keine
allgemeine Überlegenheit. Historische Ergebnisse und Regeln bleiben erhalten.

Beschlossen: drei feste rauschfreie Signale, je zehn neue gepaarte Seedblöcke.
R ist das vorab ausgewählte Profil aus vier globalen 500er-Suchen, I die frische
2.000er-Einzelsuche. Jeder Block liefert genau zwei Algorithmusergebnisse.
**150 neue Suchaufrufe, 60 Algorithmusergebnisse**, darunter 30 Paketausgaben.
Die 120-Aufruf-Variante des früheren Leitfadens umfasste nur R; die 30 I-Kontrollen
kommen für den ausdrücklich gewünschten direkten Vergleich hinzu.

Die gemeinsame praktische Übergangsgrenze ist beschlossen: **R erreicht
mindestens 8/10 Ausgaben mit Klasse A und nachgewiesener gültiger Originalfamilie
auf jedem der drei Signale**. Domain und Beweisgrenzen folgen dem bestehenden
Vertrag; bloße Fortsetzungen oder ungeklärte Familiennachweise zählen nicht
als bestätigter gemeinsamer Erfolg, bleiben aber mit ihrer Kurvenklasse sichtbar.
Dies ist eine Projektgrenze zum Rauschpilot, kein Literaturstandard, kein
Nachweis einer wahren Erfolgswahrscheinlichkeit von mindestens 80 % und kein
Überlegenheitskriterium gegenüber I. Keine automatische Pilot-Ausführung.

## Eingaben und Grenzen der Übertragbarkeit

| Kennung | Amplitude A | Frequenz f / Hz | Abklingzeit tau / s | Phase phi / rad |
| --- | ---: | ---: | ---: | ---: |
| anchor | 1 | 250 | 0,008 | 0 |
| variant_low | 0,5 | 210 | 0,010 | −0,5 |
| variant_high | 0,8 | 320 | 0,006 | 0,4 |

Formel A exp(−t/tau) cos(2πft + phi). 128 Trainingszeiten t=j/4096 Sekunden,
j=0,…,127; 889 Zwischenpunkte (j+k/8)/4096, j=0,…,126, k=1,…,7.
Die beiden neuen Kombinationen liegen innerhalb der im Transfercheck betrachteten
Parameterbereiche, unterscheiden sich gemeinsam in Frequenz, Dämpfung, Amplitude
und Phase und sind in dessen versioniertem Fallbestand unbenutzt. Sie wurden
vor neuen Suchen festgelegt, ohne Auswahl nach Rekonstruktionserfolg. Zwei
gezielte Kombinationen bilden keine zufällige Stichprobe des Parameterraums.
Der Anker bleibt ein bekanntes Signal mit neuen Suchseeds.

Die Eingabedatei speichert alle konkreten Float64-Werte einschließlich Diagnose-
und Zusatzraster vor der ersten Suche; Hashes je Rolle stehen in der Konfiguration.
Ankerbits und reguläre Zeitachsen bleiben gegenüber den Transfereingaben erhalten.
6.123 Werte wurden unabhängig mit mpmath bei 100 Dezimalstellen gegen die
analytische Formel geprüft; normierter Maximalfehler kleiner als 1e-13.
Nur Trainingszeiten und Beobachtungen gelangen in den eigentlichen Suchworker.

Zusatzraster unverändert nach der Phase-3-Regel: 1.024 stratifizierte Punkte,
eigener PCG64-Seed 2026110601, offenes Trainingsintervall, Ausschluss exakter
Treffer auf dem 1/32768-Sekunden-Raster, maximal 100 Ziehungen je Stratum.
Die gespeicherten Zeiten sind für alle Signale gleich, Referenzwerte signalspezifisch.
Kein Zugriff auf den Such-RNG. Nur kontinuierliche Fehler, keine neue Schwelle,
keine Auswahl oder Beendigung danach. Kein Identifizierbarkeits- oder Domainbeweis.

## Vollständige Seeds, Paarung und Ausführung

Alle 120 konkreten Suchseeds stehen in der Konfiguration als zehn Viererlisten
je Signal. Erzeugung mit separatem PCG64-Seed 2026110901; positive 31-Bit-Werte,
keine Überschneidung zwischen Blöcken oder Signalen. Die Erzeugung schließt
Duplikate und Zahlen aus seedbezogenen versionierten Zeilen am Bezugscommit aus.
Dieser Abgleich belegt Neuheit gegenüber dem dokumentierten Bestand, nicht
gegenüber unbekannten externen Experimenten. Alle Seeds werden vor dem ersten
Fit an die Vorbereitung gebunden; keine nachträgliche Auswahl oder Ersatzseeds.

Je Block verwendet R alle vier Seeds mit je 500 äußeren Iterationen. I verwendet
den ersten Seed desselben Blocks mit 2.000 Iterationen, frisch ohne Checkpoint.
Der gemeinsame Seed macht die Ausgaben zu einem gepaarten Vergleich; die vier
Paketmitglieder sind keine vier unabhängigen Algorithmusergebnisse.
Ungerade Blöcke: R-Mitglieder 0–3, danach I. Gerade Blöcke: I, danach R-Mitglieder
0–3. Somit fünf Blöcke je Reihenfolge pro Signal. Keine Änderung der Reihenfolge
nach Sichtung von Ergebnissen und keine zusätzliche 500er-Referenzsuche.

Drei getrennte, vollständig vorab festgelegte Signalabschnitte mit je 50 Aufrufen;
empfohlene Reihenfolge anchor, variant_low, variant_high. Alle drei bleiben geplant,
auch wenn ein früher Abschnitt die praktische Grenze verfehlt. Pausen zwischen
Abschnitten sind zulässig. Kein Resume, keine Vermischung von Teilständen und
keine automatische Wiederholung abgebrochener Abschnitte. Ein Abbruch bleibt
mit Teilkosten erhalten und sperrt die Gesamtentscheidung; weiteres Vorgehen
bedarf einer ausdrücklich dokumentierten Entscheidung vor neuer Ausführung.

Profil: lokal **300 Optimiereriterationen plus fünf zusätzliche lokale Neustarts**,
allgemeine Grammatik +, −, *, /, exp, sin, cos; beide Häufigkeitsschalter an,
`should_simplify=false`, `warmup_maxsize_by=0.0`, Float64, gewöhnliche MSE,
zwei Populationen à 32, 50 Zyklen je äußerer Iteration, maxsize/maxdepth 20,
Parsimony 0, unveränderter Newton-/BFGS-Pfad und lokale Funktionsgrenze 10.000.
Keine Templates, Warmstarts, Nachfits, historischen Kontrollübernahmen oder Zeitlimits
als reguläre Halteregel. Der geprüfte PR77-Iterationsworker und seine Messung
werden für beide Arme verwendet; keine Mischung verschiedener Workerzeitdefinitionen.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1 und übrige
Sperrdateien unverändert. Manjaro, serielle Ausführung, eine erlaubte CPU,
`OPENBLAS_CORETYPE=Haswell`, Julia Default-/Interactive-/GC-Threads 1/0/1,
BLAS und relevante Bibliotheken 1. Herkunft, Adapter, effektive Optionen,
Thread-/Hardwarebelege und Aufrufwächter vor und während jedes Fits prüfen.
Alle Abschnitte verwenden denselben sauberen Ausführungscommit und dieselbe
numerische Umgebung/Hardware; Abweichungen sperren die gemeinsame Auswertung.

Sicherheitsfristen: 1.800 Sekunden je Worker, 108.000 Sekunden (30 Stunden)
je Signalabschnitt einschließlich Vorbereitung und Abschluss. Die Abschnittsfrist
deckt 50 Workerfristen plus fünf Stunden für übrige Arbeit ab; sie ist keine
Laufzeitprognose. Für lesende Einzel-/Gesamtverifikation 7.200/21.600 Sekunden.
Aus dem bisherigen Ankerlauf grob 11¼ Stunden für alle 150 Aufrufe hochgerechnet;
andere Signale und Rechnerlast können erheblich abweichen.

## Auswahl, Ausfälle und Kosten unverändert übernehmen

Jede Suche: kleinste endliche native Trainings-MSE, danach Komplexität und
ursprünglicher Frontindex. Paket: unveränderte Mitgliedsausgaben nach nativer
Trainings-MSE, Komplexität und festgelegter Mitgliedsposition 0–3 ordnen.
R liefert genau eine Ausgabe; ohne auswählbares Mitglied ist das Paket ein Ausfall.
Keine Auswahl, vorzeitige Beendigung oder Wiederholung anhand von Wahrheit,
A–D-Klasse, Struktur oder Zusatzraster. „A irgendwo in der Front“ separat diagnostizieren.

Gewöhnliche numerische Fehler und Workerzeitüberschreitungen bleiben mit
Teilstand und bekannten Kosten erhalten; übrige geplante Zellen werden ausgeführt.
Nichtendliche Verluste sind nicht auswählbar. Alle zehn Blöcke je Signal bleiben
im Nenner; fehlerhafte Paketmitglieder bleiben in der Kostenrechnung.
Integritätsfehler, Unterbrechungen und Gesamtfrist sperren die Freigabe.
Unbekannte Kosten bleiben unbekannt und verhindern eine vollständige Kostenaussage.

Kosten je Arm, Signal und Block: sämtliche nativen Verlustcallback-Aufrufe,
Fit-/Worker-/Adapterzeiten, Nutzer-/System-CPU-Zeit sowie separate Aufrufmessung
jedes Abschnitts. R summiert alle vier Mitglieder einschließlich Ausfällen.
Keine historische Wiederverwendung: neue Kosten gleich Algorithmuskosten.
Überlappende Zeitfenster nicht addieren; reine JIT-Zeit bleibt nicht beobachtet.
Die Summe der drei Aufrufzeiten schließt Pausen zwischen Abschnitten aus.
Gleiche Iterationssummen sind keine gleichen Rechenkosten.

## Auswertung, Entscheidung und weitere Arbeit

Pro Signal und Arm A-Zahl, gemeinsame A-/Originalfamilienzahl, Domains,
Fortsetzungen, ungeklärte Nachweise, Restbefunde und Ausfälle getrennt berichten.
Alle zehn Paarungen mit Gewinnen/Verlusten/Gleichständen beider Endpunkte sowie
kontinuierliche RMS-/Maximalfehler auf allen drei Rastern erhalten. Bestehende
Bewertungsverträge und Ressourcen bleiben unverändert; neue physikalische
Parameterübereinstimmungen bleiben `not_assessed`.

Unsicherheit: je Signal/Arm marginales exaktes binomiales 95-%-Intervall
(Clopper–Pearson) der A- und gemeinsamen Erfolgszahl unter der Bernoulliannahme.
Keine simultane Garantie, kein Nachweis von 80 % und keine gepoolte Erfolgsquote
über Signale. Der gepaarte Vergleich bleibt deskriptiv; keine nachträglich
gewählte Signifikanzschwelle oder Umdeutung der 8/10-Grenze als Methodensieg.
Kostenregel aus Phase 3 bleibt deskriptiv: bei gleicher A-Zahl und vollständig
bekannten Kosten weniger Verlustaufrufe, dann weniger Workerzeit bevorzugen;
Familiengewinne/-verluste daneben sichtbar lassen. Kein automatischer Profilwechsel.

Die gemeinsame Entscheidung wird erst nach lesender Verifikation aller drei
unveränderten Abschnitte freigegeben. R muss die beschlossene Grenze auf jedem
Signal erfüllen. Bei Nichterfüllung keine neue offene Optimierungsschleife;
Befunde und Forschungsanspruch gemäß Leitfaden mit der Betreuung einordnen.
Tuning an diesen Fällen würde sie zu Entwicklungsfällen machen und ihre Rolle
als unberührte Bestätigung beenden. Höchstens zwei begründete Suchinterventionen.

Das allgemeine Profil 20/2 mit ausgeschalteten Häufigkeitsschaltern bleibt als
historischer Default sichtbar. Der Bestätigungstreiber bindet ausdrücklich
300/5 für beide Arme. Vor dem Rauschpilot ist dieses Profil im tatsächlich
verwendeten allgemeinen Laufweg bewusst zu übernehmen und rauschfrei zu prüfen;
die Gewichtung muss dort sowohl Struktur- als auch Konstantensuche bestimmen.
Die jetzige rauschfreie Vergleichsserie bestätigt noch keinen gewichteten Laufweg.

## Technischer Prüf- und Archivumfang

Keine wissenschaftliche Serie in CI. Separate technische Signale y=1+t und
y=2−t auf acht Punkten; je ein Block mit zwei kurzen Mitgliedern (zwei Iterationen)
und einer langen Kontrolle (drei Iterationen), insgesamt sechs kleine Worker.
Feste technische Seeds, native Herkunft/Optionen/Aufrufe und anschließende
lesende Einzel-/Gesamtverifikation; keine wissenschaftliche 8/10-Entscheidung
für Fixtures. Python-Gegenprüfungen sichern den vollständigen wissenschaftlichen
150-Aufruf-Plan, Paarung, truthfreie Paketwahl, Ausfälle/Nenner, Quellenbindung,
Signal-/Rasterzuordnung, unvollständige Serien und späte Widerrufe.

Originale unverändert im gemeinsamen Archivordner plus unabhängiger Zweitkopie
sichern, beide SHA-256 prüfen und im bestehenden Ergebnisindex zuordnen.
Je Abschnitt gehören Ergebnisordner und benachbarte `-call.json` zusammen;
Gesamtverifikation separat erhalten. Große Archive nicht in Git, GitHub-Uploads
optional. Vorliegender Plan belegt weder wissenschaftliche Ausführung noch Sicherung.
