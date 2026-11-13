# Bestätigungsprotokoll: vier mittlere gegen zwei längere globale Suchen

**Beschlossen am 13.11.2026, vor Implementierung getrennt versioniert.**
Anschluss an [Leitfadenphasen 4–6](ringdown_recovery_roadmap.md), kein weiterer
Suchhebel. Bezugsstand der Ergebnisdokumentation zu PR86:
`16f2e4533583ca7cced88799ffc3abb8d0052904`, auf der übernommenen PR85-Basis
`680af98e4342dc831a6dcc995fe658d4fcbe942f`. PR86 ist als
`11c844d05703ba200f2d0333ce5a422cfe7d5791` übernommen; der genaue Quellenstand
für Eingaben- und Seed-Ausschlüsse bleibt der oben genannte Ergebniscommit. Dieser Plan,
[Konfiguration und vollständige Seeds](../data/restart_budget_confirmation_protocol.json),
[Eingaben](../data/restart_budget_confirmation_inputs.npz) und
[Erzeuger](../scripts/prepare_restart_budget_confirmation_inputs.py) werden gemeinsam
vor Implementierung eingefroren und später über Commit und SHA-256 gebunden.
Keine wissenschaftlichen Vorversuche zur Auswahl von Signalen, Seeds oder Regeln.

## Fragestellung, Kandidat und feste Ausgabesemantik

Der [Entwicklungsvergleich](restart_budget_results_manjaro_001.md) bleibt gemischt:
4 × 1.000 (R) gewinnt einen gemeinsamen A-/Originalfamilienerfolg auf der niedrigen
Variante, 2 × 2.000 (L) einen auf der hohen. R liefert auf allen betrachteten
Entwicklungsblöcken A-Kurven; L benötigt je Signal weniger Workerzeit. Diese
Beobachtungen begründen R als vorläufigen Kandidaten und L als aktive Kontrolle,
keine allgemeine Überlegenheit von R. Die frühere negative 4 × 500-Bestätigung
und die gemischten Koordinatenbefunde bleiben unverändert.

Geprüft wird die Übertragbarkeit der **unveränderten Verfahren auf drei vorab
festgelegte, bisher nicht benutzte Signaldefinitionen**. R und L bleiben in
physischer Zeit t, beide bei lokal 300/5 und unveränderter allgemeiner Grammatik.
Keine Kombination mit 4 × 500, keine Koordinatenvariation und keine Budgetstaffel.

Maßgeblich ist die tatsächlich ausgewählte **Originalformel**: Klasse A und
nachgewiesene gültige Originalfamilie auf dem ganzen geschlossenen Prüfintervall.
Stetige Fortsetzung ist ein getrennter Befund, kein Erfolg des lückenhaften
Originals. Ein kleiner nicht null gesetzter Zusatzterm wird nicht entfernt.
Ungeklärte Nachweise zählen nicht als bestätigter gemeinsamer Erfolg und nicht
automatisch als Beweis der Nichtzugehörigkeit. Keine neue Nachbearbeitung,
Grammatikbeschränkung, Ringdown-Vorlage oder Änderung der Beweisressourcen.

Die vorab ausgewählte praktische Grenze für R lautet **mindestens 8/10 gemeinsame
A-/Originalfamilienerfolge auf jedem der drei Signale**. Für L wird die Erfüllung
derselben Grenze separat berichtet. L-Erfolge heilen keinen R-Misserfolg;
kein automatischer Wechsel zu L oder zu einem aus beiden Armen ausgewählten Hybrid.
Die Grenze ist eine praktische Projektentscheidung, kein Literaturstandard,
kein Nachweis einer wahren Erfolgswahrscheinlichkeit von mindestens 80 % und
kein statistischer Überlegenheitsnachweis. Historische Ergebnisse werden nicht
nachträglich mit dieser neuen Bestätigung zusammengezählt.

## Neue feste Signale und Grenzen der Übertragbarkeit

Der Parameterkasten folgt dem bisherigen rauschfreien Zielbereich:
Amplitude A in [0,5;1], Frequenz f in [210;320] Hz, Abklingzeit tau in
[0,006;0,010] s und Phase phi in [−0,5;0,4] rad. Jeder Bereich wird in drei
gleich breite Strata geteilt; verwendet werden deren Mittelpunkte mit vorher
festgelegten unterschiedlichen Rangzuordnungen. Ränge 0/1/2 stehen für das
untere/mittlere/obere Stratum. In der untenstehenden Reihenfolge sind die Ränge
für A **0,2,1**, f **0,1,2**, tau **2,0,1**, phi **1,2,0**.

| Kennung und Reihenfolge | A, Designbruch | f / Hz, Designbruch | tau / s, Designbruch | phi / rad, Designbruch |
| --- | ---: | ---: | ---: | ---: |
| confirm_low | 7/12 | 685/3 | 7/750 | −1/20 |
| confirm_mid | 11/12 | 265 | 1/150 | 1/4 |
| confirm_high | 3/4 | 905/3 | 1/125 | −7/20 |

Die Brüche beschreiben die Auswahl. **Maßgebliche Signalparameter sind ihre
einmal gerundeten Binary64-Werte**, vollständig als Dezimal- und Hexwerte in
der Konfiguration gespeichert. Die Wahrheit ist
A exp(−t/tau) cos(2πft+phi) mit den exakten Werten dieser gespeicherten
Binary64-Parameter und mathematischem pi. Kein Nachjustieren der Parameter
anhand gefundenen Formeln oder Sucherfolgen.

Die festen Zuordnungen nutzen alle drei inneren Bereiche jedes Parameters,
ohne sämtliche Parameterränge gleich laufen zu lassen. Drei gemeinsame
Parameterkombinationen erlauben dennoch keine isolierte Kausalaussage über
Frequenz, Dämpfung, Amplitude oder Phase. Sie sind keine zufällige Stichprobe
und keine flächige Bestätigung des ganzen Parameterkastens. Insbesondere wird
die frühere schwierige Randkombination nicht erneut getestet; ihr negativer
Befund wird auch bei Erfolg dieser inneren Fälle nicht aufgehoben.

Der Erzeuger gleicht die vollständigen Parameterkombinationen gegen sämtliche
vollständigen Signaldefinitionen in versionierten JSON-Dateien unter `data/`
am Bezugscommit ab; keine der drei Kombinationen ist dort enthalten. Umfang
und Hash dieser Ausschlussmenge stehen in der Konfiguration. Das bestätigt
Neuheit gegenüber dem dokumentierten Bestand, nicht unbekannten externen Läufen.
Die bisherigen Entwicklungssignale gehen nicht in diesen Bestätigungsnenner ein.

## Konkrete Eingaben, unabhängige Referenz und Zusatzraster

128 Trainingspunkte t=j/4096 Sekunden, j=0,…,127; 889 reguläre Zwischenpunkte
(j+k/8)/4096 mit j=0,…,126 und k=1,…,7. Diese beiden Zeitachsen werden bitgleich
aus der gebundenen bisherigen Eingabe übernommen. Das geschlossene physische
Prüfintervall bleibt [0,127/4096] s. Alle Signalwerte und das unregelmäßige Raster
werden neu erzeugt; keine Übernahme früherer Beobachtungen oder Suchergebnisse.

Alle konkreten Zeiten und Werte werden vor der Suche in der deterministischen
NPZ-Datei gespeichert; Fingerprints für jede Rolle und den ganzen Bytestrom
stehen in der Konfiguration. Die numerische Erzeugung verwendet den per Git und
Hash gebundenen bisherigen `ringdown_signal`-Code. Alle **6.123 Signalwerte**
werden zusätzlich unabhängig mit mpmath bei 100 Dezimalstellen gegen die
analytische Formel auf den exakten gespeicherten Binary64-Zeiten/-Parametern
geprüft; absolute Abweichung geteilt durch A kleiner als 1e-13. Dieser technische
Eingabenachweis sagt nichts über die Wiederfindung durch die Suchverfahren aus.

Das neue Zusatzraster verwendet **1.024 Punkte und einen eigenen PCG64-Seed
2026111302**: je ein Punkt pro gleich breitem Stratum im offenen Intervall
(0,127/4096) s, maximal 100 Ziehungen je Stratum. Exakte Treffer auf dem
regelmäßigen 1/32768-Sekunden-Raster werden verworfen. Der Erzeuger bestätigt
zusätzlich, dass kein neuer Punkt dem früheren unregelmäßigen Raster entspricht.
Alle drei Signale teilen diese neuen Zeiten; Referenzwerte sind signalspezifisch.
Der private Rastergenerator greift nicht auf den Such-RNG oder dessen Zustand zu.

Nur Trainingszeiten und Beobachtungen gehen in die Suche und Trainingszielfunktion
ein. Mitgeladene diagnostische Arrays bleiben der späteren Auswertung vorbehalten;
sie bestimmen weder Auswahl noch Abbruch. Zwischen- und Zusatzpunkte dienen der
Diagnose. Das unregelmäßige Raster reduziert
Blindstellen des gemeinsamen regelmäßigen Trainings-/Zwischenrasters, beweist
weder allgemeine Identifizierbarkeit noch Domain-Gültigkeit. Ausschließlich
kontinuierliche relative RMS-/Maximalfehler berichten; keine neue Schwelle,
Auswahl oder vorzeitige Beendigung danach. Historische A–D-Regeln unverändert.

## Umfang, vollständige Seeds und Paarung

Je Signal **zehn gepaarte Blöcke**, jeweils vier frische 1.000er-Suchen für R und
zwei frische 2.000er-Suchen für L. Je Paket genau eine Ausgabe. Insgesamt
**30 Paarungen, 180 Suchaufrufe und 60 Algorithmusergebnisse**; 240.000 geplante
äußere Iterationen. Beide Pakete eines Blocks haben je 4.000 äußere Iterationen,
was weder gleiche Laufzeit noch gleiche Zahl von Verlustaufrufen garantiert.

Alle **120 verschiedenen positiven 31-Bit-Seeds** stehen in der Konfiguration
als zehn Viererlisten je Signal. Eigener PCG64-Generatorseed 2026111301;
`integers(1,2**31)`, Duplikate sowie sämtliche positiven 31-Bit-Ganzzahltokens
in versioniertem Text unter data/docs/src/scripts/tests am Bezugscommit werden
ausgeschlossen. Numerische JSON-Zeilen werden vollständig berücksichtigt.
Ausschlussumfang, Hash und Quellencommit sind festgehalten. Kein Überlappen
zwischen Blöcken oder Signalen; keine nachträglichen Ersatzseeds.

R verwendet pro Block alle vier Seeds, L die ersten beiden. Alle sechs Aufrufe
sind vollständig neue Suchen; gleiche Seeds sind keine Checkpointfortsetzung,
kein Warmstart und keine Garantie eines gemeinsamen Evolutionspräfixes.
Die beiden gemeinsamen Seeds paaren die Starts. Die vier beziehungsweise zwei
Mitglieder sind keine unabhängigen Algorithmusergebnisse: statistische Einheit
ist die ausgewählte Paketausgabe beziehungsweise das Paar, nicht der einzelne Fit.

Ungerade Blöcke führen alle R-Mitglieder, danach alle L-Mitglieder aus; gerade
Blöcke umgekehrt. Innerhalb eines Arms feste Mitgliedsreihenfolge. Fünf Blöcke
je Reihenfolge pro Signal; keine Anpassung nach Zwischenergebnissen.
Abschnittsreihenfolge: confirm_low, confirm_mid, confirm_high, jeweils 60 Aufrufe.
Alle Abschnitte und Mitglieder bleiben geplant, auch nach frühen Erfolgen oder
Misserfolgen. Eine unbeaufsichtigte Sequenz darf die drei vorgesehenen Abschnitte
nacheinander starten; keine automatische Wiederholung, kein Resume und kein
Überschreiben bestehender Ordner. Pausen zwischen Abschnitten sind zulässig.

## Festes Profil, Umgebung und Sicherheitsfristen

Lokales Profil **300 Optimiereriterationen plus fünf zusätzliche lokale Neustarts**;
globale Neustarts sind davon getrennte vollständige SR-Suchen. Beide
Häufigkeitsschalter an, allgemeine Grammatik +, −, *, /, exp, sin, cos,
`should_simplify=false`, `warmup_maxsize_by=0.0`, Float64 und native gewöhnliche MSE.
Zwei Populationen à 32, 50 Zyklen je äußerer Iteration, maxsize/maxdepth 20,
Parsimony 0, unveränderter Newton-/BFGS-Pfad und lokale Funktionsgrenze 10.000.
Übrige effektive Optionen und nativer Iterationsworker wie im geprüften
Budgetvergleich; kein neuer Optimierer oder zeitbasierter regulärer Suchabbruch.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1 und weitere
Sperrdateien unverändert. Manjaro, seriell auf einer erlaubten CPU,
`OPENBLAS_CORETYPE=Haswell`, Julia Default-/Interactive-/GC-Threads 1/0/1,
BLAS und relevante Bibliotheken ein Thread. Alle drei Abschnitte verwenden
denselben sauberen Ausführungscommit und dieselbe numerische Umgebung/Hardware.
Quellen, Adapter, tatsächliche Workerherkunft, effektive Optionen, CPU-/Thread-
belege und Aufrufwächter bleiben vor und während der Fits gebunden und geprüft.

Sicherheitsfristen: **1.800 Sekunden je Worker, 115.200 Sekunden (32 Stunden)
je Signalabschnitt**, einschließlich Vorbereitung und Abschluss. Die Abschnitts-
frist deckt 60 Workerfristen plus 7.200 Sekunden übrige Arbeit ab. Einzelverifikation
7.200 Sekunden, Gesamtverifikation 21.600 Sekunden. Fristen sind Sicherheitsgrenzen,
keine Laufzeitprognosen. Technische Fixtures verwenden separat die bestehenden
kurzen Grenzen des technischen Laufwegs; keine wissenschaftlichen Budgets in CI.
Die begrenzte Hochrechnung aus dem Entwicklungsbestand ergibt grob 18–20 Stunden
für die ganze wissenschaftliche Serie auf demselben Rechner; neue Signale und
Seeds können erheblich abweichen. Technischer Vorlauf und spätere Verifikation
sind darin keine bereits gemessenen Kosten dieser neuen Serie.

## Auswahl, Ausfälle und Kosten

Die ursprüngliche Workerauswahl bleibt: kleinste endliche native Trainings-MSE,
danach ursprüngliche Baumkomplexität und ursprünglicher Frontindex. Paketwahl
nur zwischen diesen Originalausgaben: native Trainings-MSE, Originalkomplexität,
vorab festgelegter Mitgliedsindex. Ein Paket liefert genau eine Ausgabe.
Keine Auswahl über T/U oder R/L und kein Nachranking aller Frontformeln.
„Passender Kandidat irgendwo vorhanden“ wird getrennt diagnostiziert.

Alle vorgesehenen Mitglieder ausführen, auch wenn eine frühere Ausgabe gut ist.
Nichtendliche Verluste sind nicht auswählbar; ein Paket ohne zulässiges Mitglied
liefert einen Ausfall. Gewöhnliche nach bestehendem Vertrag zulässige numerische
Suchfehler und Worker-Timeouts bleiben als Ausfälle mit bekannten Teilkosten
erhalten. Alle zehn Pakete je Signal/Arm bleiben im Nenner. Kein Abbruch,
Nachfit, Ersatzseed oder Wiederholung anhand von Signalwahrheit, Klasse,
Familienprüfung, Restterm oder Zusatzraster.

Wächter-/Herkunftsfehler, unbekannte Fehler, Unterbrechungen und Gesamtfristen
sperren beziehungsweise widerrufen die Freigabe. Ein Timeout darf einen
aufgezeichneten Integritätsfehler nicht verdecken. Herkunftsbelege gelten auch
für fehlgeschlagene Worker entsprechend der erreichten Phase; vorhandene
Widersprüche sind stets unzulässig. Ein abgebrochener Teilstand bleibt erhalten;
weitere Ausführung benötigt eine dokumentierte Entscheidung und neue Lauf-ID.

Je Mitglied, Paket, Paar, Arm und Signal alle bekannten Verlustcallback-Aufrufe,
Fit-/Worker-/Adapterzeiten sowie Nutzer-/System-CPU-Zeit erhalten. Paketkosten
enthalten sämtliche Mitglieder einschließlich nicht ausgewählter und ausgefallener.
Vollständige Abschnittsaufrufe einschließlich Vorbereitung/Veröffentlichung
separat messen; überlappende Zeitfenster nicht addieren. Keine historische
Wiederverwendung: neuer Aufwand entspricht dem ganzen Algorithmusaufwand.
Unbekannte Kosten bleiben unbekannt, niemals null; JIT-Zeit und native Gesamt-
evaluierungszahlen nicht aus Callback-Zählern ableiten. Kosten sind kein
nachträglicher Gleichstandsentscheid für die praktische Bestätigungsgrenze.

## Auswertung, Unsicherheit und gemeinsame Entscheidung

Je Signal/Arm A-Zahl und gemeinsame A-/Originalfamilienzahl, Domains,
Fortsetzungen, Restbefunde, ungeklärte Nachweise und Ausfälle berichten.
Für alle zehn Paarungen Gewinne, Verluste und Gleichstände beider Endpunkte
sowie vollständige Kosten erhalten. Neue physikalische Parameterübereinstimmung
bleibt `not_assessed`; sie folgt weder aus Klasse A noch aus Familienzugehörigkeit.
Vor einer späteren Parameterdiagnose wäre eine eigene Regel zu dokumentieren.

Je Signal/Arm/Endpunkt marginale exakte zweiseitige 95-%-Binomialintervalle
(Clopper–Pearson) unter der Bernoulliannahme berichten. Sie beschreiben die
Unsicherheit über den Suchzufall auf den jeweiligen festen Signalen; keine
simultane Garantie und keine Übertragung auf eine Signalpopulation. Drei feste
Signale und zehn Blöcke sind eine pragmatische, begrenzte Bestätigung, keine
behauptete Powerberechnung. Kein Pooling über Signale, kein Signifikanztest und
keine Überlegenheitsbehauptung aus den deskriptiven gepaarten Zahlen.

Die praktische R-Entscheidung wird **erst nach lesender Verifikation aller drei
unveränderten Abschnitte** freigegeben: auf jedem Signal mindestens 8/10 gemeinsame
Erfolge. L erhält dieselbe Prüfung getrennt. Weder ein L-Erfolg noch geringere
Kosten ändern eine verfehlte R-Grenze. Keine automatische Auswahl des erfolgreicheren
Arms auf diesen Daten, keine Kombination der besten Ausgaben und keine zusätzliche
Seedrunde bis zum gewünschten Erfolg.

Bei Nichterfüllung den Befund und den erreichbaren Forschungsanspruch gemäß
Leitfaden mit der Betreuung einordnen; kein neuer Suchhebel. Tuning an diesen
Fällen beendet ihre Rolle als unberührte Bestätigung. Bei Erfüllung liegt ein
begrenzter praktischer Befund für R auf diesen neuen Fällen vor; weder allgemeine
Robustheit noch der Rauschpilot sind damit automatisch bestätigt oder gestartet.
Vor dem Rauschpilot gewähltes Profil bewusst in den tatsächlichen allgemeinen
Laufweg übernehmen und rauschfrei prüfen. Die Gewichtung muss dort sowohl
Struktursuche als auch Konstantenoptimierung bestimmen; dieser ungewichtete
Bestätigungsversuch prüft den gewichteten späteren Laufweg nicht.

## Technische Abnahme, Quellen und Sicherung

Vorhandene Adapter, Bewertungen und Archivmechanismen verwenden. Getrennte
technische Fixtures y=1+t und y=2−t auf acht Punkten: je ein Block mit vier
Ein-Iterations- und zwei Zwei-Iterations-Workern, insgesamt zwölf kleine
Suchen und vier Paketausgaben. Reguläres Ende, Herkunft, beide Paketwahlen,
alle Kosten und Einzel-/Gesamtverifikation prüfen; keine wissenschaftliche
8/10-Entscheidung aus Fixtures. Python-Gegenfälle prüfen insbesondere vollständige
180-Aufruf-Planung, feste neue Inputs/Seeds, Grenzen der Haupt-/Kontrollentscheidung,
Ausfälle/Nenner, Paketwahl, Intervalle, Herkunft und späte Widerrufe.
Vollständige Ready-CI und angemessener KI-Review vor Übernahme. Keine
wissenschaftliche Versuchsserie in GitHub Actions.

Die Methodenliteratur motiviert die Trennung von numerischem Fehler und
symbolischer Wiederfindung sowie begrenzte Entwicklung und getrennte Bestätigung:
[Cawley und Talbot (2010)](https://www.jmlr.org/papers/v11/cawley10a.html)
begründen die Trennung von Methodenwahl und Leistungsbewertung bei Auswahlverzerrung;
[La Cava et al. (2021)](https://cavalab.org/assets/papers/La%20Cava%20et%20al.%20-%202021%20-%20Contemporary%20Symbolic%20Regression%20Methods%20and%20their.pdf)
und [Aldeia et al. (2025)](https://arxiv.org/html/2505.03977v1), mit den bestehenden
Übertragungsgrenzen aus dem Leitfaden. Die Literatur belegt weder einen Vorteil
von 4 × 1.000 noch die konkrete Wahl von drei Signalen, zehn Blöcken oder 8/10.
Keine erneute Literaturabnahme wird durch diese Planübernahme behauptet.

Originalarchive unverändert im gemeinsamen Archivordner und auf unabhängigem
Datenträger beziehungsweise vorhandenem Backup erhalten; beide SHA-256 prüfen.
Je Abschnitt Ergebnisordner und benachbarte `-call.json`, technischer Vorlauf
und lesende Gesamtverifikation gemeinsam zuordnen. Tatsächliche Ablage und
Sicherungsnachweise im bestehenden [Ergebnisindex](results_index.md) gemäß
[Archivrichtlinie](results_archiving.md) dokumentieren. Keine großen Archive
in Git; GitHub-Uploads optional. Dieser Plan belegt keine Implementierung,
wissenschaftliche Ausführung oder bereits vorhandene Sicherung.
