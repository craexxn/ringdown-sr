# Entwicklungsprotokoll: physische und normierte Zeitkoordinate

**Beschlossen am 12.11.2026, vor Implementierung getrennt versioniert.**
Bezugsstand `94e15c5bb782028e3ac3d89252185e2d2e03d655`, main nach PR82.
Dieses Arbeitspaket konkretisiert die bedingt vorgesehene zweite
Suchintervention aus [Leitfadenphase 4](ringdown_recovery_roadmap.md), keine neue
Roadmap. [Konfiguration](../data/time_coordinate_protocol.json),
[Eingaben](../data/time_coordinate_inputs.npz) und
[Erzeugung](../scripts/prepare_time_coordinate_inputs.py) gehören zum selben
vor Implementierung versionierten und anschließend über SHA-256 gebundenen Protokollstand.

## Fragestellung und begrenzter Umfang

Die [Bestätigungsserie](restart_confirmation_results_manjaro_001.md) erreicht
die beschlossene Grenze nicht auf jedem Signal. Globale Neustarts und lange
Einzelsuchen zeigen unterschiedliche Stärken; weder zusätzliche Iterationen
noch ein Wechsel der Zeitkoordinate sind dadurch bereits als Verbesserung
nachgewiesen. Der frühere Zeitstreckungsversuch unter lokal 20/2 und
ausgeschalteten Häufigkeitsschaltern beantwortet die Frage unter 300/5 nicht.

Die Literatur begründet den begrenzten Test, nicht seinen Erfolg:
[Kommenda et al. (2020), Abschnitt 3](https://link.springer.com/article/10.1007/s10710-019-09371-3)
zeigen bei einer sinusförmigen Referenz, dass lokale Konstantenoptimierung selbst
bei passender Struktur vom Startbereich abhängt. Das belegt keinen Defekt unseres
300/5-Profils und keinen Vorteil dieser Skalierung.
[PySRs Hinweise zur Abstimmung](https://raw.githubusercontent.com/astroautomata/PySR/master/docs/src/tuning.md)
erläutern, dass längere Suchen nach scheinbaren Plateaus neue Lösungen finden
können; daraus folgt keine allgemeine Überlegenheit eines Budgets oder von Neustarts.

Geprüft wird ausschließlich: **Verbessert die feste Zeitkoordinate u=32t
die Rekonstruktion gegenüber Sekunden t bei frischen 2.000er-Einzelsuchen
unter demselben Profil 300/5?** Der dimensionslose Faktor 32 folgt aus dem
festen Referenzintervall 1 s geteilt durch das nominale Messfenster
128/4096 s = 1/32 s, nicht aus Frequenz oder Abklingzeit der Signalwahrheit.
u ist eine gedehnte Zeit in Sekunden: u=(t/(1/32 s))·1 s. Der unveränderte
Worker deklariert `variable_names=["t"]`, `X_units=["s"]`, `y_units="1"`;
diese Schnittstelle bleibt für beide Arme korrekt. Die numerische Normierung
ändert keine Einheitenmetadaten und führt keine zusätzliche Dimensionsregel ein.

Acht neue gepaarte Entwicklungsblöcke, somit **16 frische Suchen und
16 Algorithmusergebnisse**: zwei Blöcke für anchor, zwei für variant_low,
vier für variant_high. Das bislang schwächere Signal erhält bewusst mehr
Entwicklungsfälle. Diese ungleiche, gezielte Auswahl erlaubt keine gepoolte
Erfolgsquote oder allgemeine Erfolgswahrscheinlichkeit. Beide Arme sind
jeweils 1 × 2.000; es gibt hier weder Viererpakete noch historische Übernahmen.

Die drei Signaldefinitionen werden damit künftig als bekannte Entwicklungsfälle
behandelt. Die ursprüngliche Bestätigung und ihre verfehlte Grenze bleiben
unverändert erhalten. Neue Seeds allein machen diesen Anschlussversuch nicht
zu einer unabhängigen Bestätigung. Kein Rauschpilot und keine Änderung der
ursprünglichen 8/10-Regel sind Bestandteil dieses Plans.

## Unveränderte physische Eingaben und getrennte Koordinaten

Die ursprüngliche Datei `data/restart_confirmation_inputs.npz` wird am
Bezugscommit gelesen und anhand ihres ursprünglichen Protokollhashes
`02d03ebf37be51613b4e6303a2806dcb308fc344c544e82ff0dfd0d82000c8f2` geprüft.
Alle darin gespeicherten physischen Zeiten und Referenzwerte werden bitgleich
übernommen, ohne erneute Signalerzeugung. Damit bleiben auch die bereits
unabhängig nachgerechneten Signalwerte erhalten; der neue Generator belegt
deren Übernahme, wiederholt aber nicht die ursprüngliche MPFR-Nachrechnung.

| Signal | A | f / Hz | tau / s | phi / rad | Blöcke |
| --- | ---: | ---: | ---: | ---: | ---: |
| anchor | 1 | 250 | 0,008 | 0 | 2 |
| variant_low | 0,5 | 210 | 0,010 | −0,5 | 2 |
| variant_high | 0,8 | 320 | 0,006 | 0,4 | 4 |

Je Signal: 128 Trainingspunkte t=j/4096, j=0,…,127; 889 bisherige
Zwischenpunkte; dieselben 1.024 gespeicherten unregelmäßigen Zusatzpunkte.
Das geschlossene physische Prüfintervall bleibt [0,127/4096] s.
Die normierten Trainingsendpunkte sind [0,127/128] s in der Suchkoordinate u.

Die neue Eingabedatei enthält die ursprünglichen Rollen sowie zusätzlich
`time_u`, `diagnostic_time_u` und `irregular_time_u`. Sie entstehen durch
`ldexp(t,5)`. Für alle 2.041 Zeitwerte prüft der Generator mit exakten rationalen
Zahlen, dass u exakt 32t ist; die Rückabbildung erhält sämtliche Float64-Bits.
Das Zusatzraster wird nicht neu gezogen. Seine ursprüngliche Erzeugungsregel
(PCG64-Seed 2026110601, 1.024 Strata, Ausschluss des 1/32768-Sekunden-Rasters)
bleibt durch Quellen- und Rollenhashes gebunden. Keine Nutzung eines Such-RNG.

Jede Vorbereitung speichert und bindet die physischen Eingaben, die tatsächlich
an den jeweiligen Worker übergebenen Koordinaten und die Zuordnung T/U vor der
ersten Suche. Der unveränderte Worker erhält ausschließlich seine Trainings-
koordinaten und dieselben Beobachtungen. Ein historischer Feldname `time_s` im
internen Workerformat bezeichnet im U-Arm numerisch u; eine explizite gebundene
Koordinatenrolle muss die gedehnte Zeit von der ursprünglichen physischen Zeit trennen.
Diagnosepunkte und Signalwahrheit dürfen weder Auswahl noch Suchende beeinflussen.

## Vollständige Paarung und feste Ausführung

| Signal | Block | gemeinsamer Suchseed T/U | Reihenfolge |
| --- | ---: | ---: | --- |
| anchor | 1 | 1151764945 | T, U |
| anchor | 2 | 855357527 | U, T |
| variant_low | 1 | 1429331782 | T, U |
| variant_low | 2 | 608579426 | U, T |
| variant_high | 1 | 1356550349 | T, U |
| variant_high | 2 | 409431025 | U, T |
| variant_high | 3 | 1625947320 | T, U |
| variant_high | 4 | 827273765 | U, T |

Die acht verschiedenen positiven 31-Bit-Seeds stammen aus einem eigenen
PCG64 mit Seed 2026111201. Der Generator verwirft Duplikate sowie alle positiven
31-Bit-Zahlentokens in versionierten Textdateien unter data/docs/src/scripts/tests
am Bezugscommit. Das erfasst auch Seedlisten, deren Werte in separaten JSON-Zeilen
stehen. Ausschlussmenge, Hash und Commit stehen in der Konfiguration; unbekannte
externe Versuche sind davon nicht erfasst. Der Abgleich erfolgt auf dem oben
genannten main nach PR82. Keine nachträglichen Ersatzseeds.

Gleicher Seed und gleiche Signalwerte bilden die Paarung; unterschiedliche
Koordinaten können den gesamten Suchverlauf ändern. Beide Suchen starten frisch,
ohne Checkpoint, Warmstart, Frontübernahme oder Nachfit. Wechselnde Reihenfolge
verteilt Reihenfolgeeffekte, beseitigt sie aber nicht.

Drei getrennte Abschnitte in der Reihenfolge anchor, variant_low, variant_high,
mit vier, vier und acht Suchaufrufen. Alle Abschnitte bleiben geplant, auch wenn
ein früher Abschnitt schlechte Ergebnisse liefert. Pausen zwischen Abschnitten
sind zulässig. Kein Resume und keine Vermischung von Teilständen. Ein Abbruch
bleibt mit Teilkosten erhalten, sperrt die Gesamtentscheidung und erfordert
eine ausdrücklich dokumentierte Entscheidung vor einer neuen Ausführung.

## Suchprofil und numerische Umgebung

Lokal **300 Optimiereriterationen plus fünf zusätzliche lokale Neustarts**;
Häufigkeitsschalter `use_frequency` und `use_frequency_in_tournament` an;
allgemeine Grammatik +, −, *, /, exp, sin, cos;
`should_simplify=false`, `warmup_maxsize_by=0.0`, Float64, gewöhnliche native MSE,
zwei Populationen à 32, 50 Zyklen pro äußerer Iteration, maxsize/maxdepth 20,
Parsimony 0, unveränderter Newton-/BFGS-Pfad und lokale Funktionsgrenze 10.000.
Alle übrigen effektiven Optionen entsprechen dem geprüften PR77-Iterationsworker.
Keine Templates, Grammatikeinschränkung, Populationsvariation oder zusätzliche
Optimierung. Nur die Zeitkoordinate unterscheidet die beiden Arme.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1 und übrige
Sperrdateien unverändert. Manjaro, seriell auf einer erlaubten CPU,
`OPENBLAS_CORETYPE=Haswell`, Julia Default-/Interactive-/GC-Threads 1/0/1,
BLAS und relevante Bibliotheken mit einem Thread. Eltern-/Workerherkunft,
Adapter, tatsächlich geladene Quellen, effektive Optionen, CPU-/Threadbelege
und Aufrufwächter vor und während der Fits prüfen. Alle Abschnitte brauchen
denselben sauberen Ausführungscommit und dieselbe numerische Umgebung/Hardware.

Sicherheitsfristen: 1.800 Sekunden pro Worker und 21.600 Sekunden (sechs Stunden)
pro Signalabschnitt einschließlich Vorbereitung und Abschluss. Die größte
Sektion enthält acht Workerfristen plus zwei Stunden übrige Arbeit; die Grenze
ist keine Laufzeitprognose. Einzelverifikation 7.200 Sekunden, Gesamtverifikation
21.600 Sekunden. 2.000 Iterationen sind die reguläre Halteregel; ein Sicherheits-
timeout ist ein Ausfall, kein erfolgreicher Zeitbudgetarm.

## Originalauswahl, physische Diagnose und Kosten

Jede Suche liefert genau die ursprüngliche Auswahl: kleinste endliche native
Trainings-MSE, danach ursprüngliche Baumkomplexität und ursprünglicher Frontindex.
Keine Auswahl anhand von A–D-Klassen, Signalwahrheit, Struktur oder Zusatzraster;
keine beste Ausgabe über T/U. Nichtendliche Verluste sind nicht auswählbar.
„Passender Kandidat irgendwo in der gespeicherten Endfront“ separat diagnostizieren;
die Front ist kein Protokoll der gesamten Evolution.

Der unveränderte native Baum q, seine Vorhersagen, Originalkomplexität, MSE,
Quellenhashes und Auswahlindizes bleiben erhalten. Für U wird ein zusätzliches
physisches Modell durch reine Variablensubstitution q(32t) gebildet, für T q(t).
Keine Koeffizientenumformung, Vereinfachung oder lokale Optimierung. Original-
und abgeleiteter Baum erhalten getrennte Hashes und eine explizite Transformations-
bindung. Die zusätzliche Komplexität der Komposition verändert keine Auswahl.

Workerreplay prüft q(u) in Suchkoordinaten. Physische Kurven-/Struktur-/Restterm-
diagnose prüft die exakt gebundene Komposition auf dem ursprünglichen physischen
Intervall. Ihre Auswertung gegen q(32t) und q(u) auf den zugehörigen Punkten
muss übereinstimmen. Definitionslücken und Zusatzterme werden dabei räumlich
korrekt zurückgebunden. Bestehende Beweisgrenzen und Ressourcen gelten weiter;
eine bei diesen Grenzen ungeklärte Formel bleibt ungeklärt. Familienzugehörigkeit
und neue Parameterübereinstimmung bleiben getrennt, Letztere `not_assessed`.

Gewöhnliche numerische Suchfehler und Workerzeitüberschreitungen bleiben als
Ausfälle erhalten; übrige geplante Zellen werden ausgeführt. Integritätsfehler,
Wächterfehler, unbekannte Fehler, Unterbrechungen oder Gesamtfrist sperren die
Freigabe. Ein Timeout darf einen protokollierten Integritätsfehler nicht verdecken.
Herkunftsprüfungen gelten auch für fehlgeschlagene Worker. Alle 2/2/4 Paarungen
bleiben in den jeweiligen Signalnennern; keine automatische Wiederholung.

Pro Suche, Paar, Arm und Signal native Verlustcallback-Aufrufe, Fit-/Worker-/
Adapterzeiten und Nutzer-/System-CPU-Zeit berichten. Separate Abschnittsaufruf-
messung einschließlich Vorbereitung und Abschluss erhalten; überlappende Zeiten
nicht addieren. Keine historischen Kosten: neuer Aufwand entspricht dem Aufwand
aller hier ausgeführten Suchen. Fehlende Kosten bleiben unbekannt, nicht null.
JIT-Zeit ist ohne separate Beobachtung nicht isoliert bestimmbar. Gleiche
Iterationen sind auch zwischen Koordinaten kein Nachweis gleicher Rechenkosten.

## Endpunkte und begrenzte Entwicklungsentscheidung

Je Signal und Arm A-Zahl, gemeinsame Zahl **A mit nachgewiesener gültiger
Originalfamilie**, Domain-/Fortsetzungs-/ungeklärte Befunde, Ausfälle und Kosten
berichten. Alle Paarungen einschließlich Gewinne, Verluste und Gleichstände
beider Endpunkte erhalten. Auf Training, Zwischenpunkten und Zusatzraster
kontinuierliche relative RMS-/Maximalfehler zeigen. Historische A–D-Regeln
bleiben unverändert; das Zusatzraster erhält keinen neuen Bestehensmarker.

Erst alle drei unveränderten, lesend verifizierten Abschnitte erlauben eine
gemeinsame Entwicklungsentscheidung. Vorab festgelegte beschreibende Einordnung:

1. **U als Entwicklungskandidat:** Auf keinem Signal sind A-Zahl oder gemeinsame
   A-/Familienzahl kleiner als bei T, und mindestens eine gemeinsame Erfolgszahl
   ist größer. Das stützt die Untersuchung von U im separaten Anschlussvergleich,
   belegt weder allgemeine Überlegenheit noch eine Übergangsgrenze zum Pilot.
2. **T gestützt:** Dasselbe Richtungskriterium gilt mit vertauschten Armen.
3. **Zahlen unverändert:** Beide Endpunkte sind auf allen Signalen gleich.
   Vollständig bekannte Verlustaufrufe und Workerzeiten beschreibend vergleichen;
   ein reiner Kostenvorteil entscheidet die wissenschaftliche Frage nicht allein.
4. **Gemischt/offen:** Alle übrigen vollständigen Ergebnisse, insbesondere
   widersprüchliche Gewinne/Verluste zwischen Signalen oder Endpunkten. Keine
   nachträgliche Poolingregel, kein automatischer Profilwechsel und keine
   zusätzlichen Seeds bis zu einem gewünschten Ergebnis.

Diese qualitative Richtungsregel enthält kein neues 8/10- oder Prozentkriterium.
Kleine Fallzahlen erlauben keine belastbare Überlegenheitsbehauptung. Kosten und
kontinuierliche Fehler bleiben auch bei einer gerichteten Einordnung sichtbar;
die Regel setzt keine Wirkung auf jedem einzelnen gepaarten Seed voraus.

Anschließend ist ein **separat eingefrorener Budgetvergleich 4 × 1.000 gegen
2 × 2.000** vorgesehen. Beide Pakete erhalten je 4.000 äußere Iterationen,
aber nicht zwangsläufig gleiche Kosten; jedes Paket muss eine native verlust-
basierte Ausgabe liefern. Zuvor die verwendete Koordinate aus diesem Befund
ausdrücklich dokumentieren, bei gemischtem Befund die offene Abwägung begründen.
Dieser spätere Plan braucht eigene neue Seeds, Paarung, Auswahl-/Ausfall-/
Kostenregeln und einen getrennten Laufauftrag; seine Suchläufe sind hier nicht
enthalten. Kein ungeprüfter Sprung zu 4 × 2.000 oder breiter Parameteroptimierung.

## Technische Prüfung, Umsetzung und Sicherung

Eigener schmaler Laufweg mit vorhandenen Adaptern, Bewertungen und Veröffentlichungs-
grenzen. Historische Worker und Ausgaben bleiben unverändert. Kleine technische
Fixtures prüfen beide Koordinaten und die lesende Gesamtverifikation; keine
wissenschaftlichen 2.000er-Suchen in GitHub Actions. Python-Gegenprüfungen:
vollständiger 16-Aufruf-Plan, disjunkte Seedblöcke, falsche/doppelte/inverse
Skalierung, Signal-/Rasterverwechslung, Originalkomplexität und unveränderte
Auswahl, physische Domainlücken, getrennte Modellhashes, Ausfälle/Nenner,
unbekannte Kosten, Herkunftsfehler, Unterbrechung und späte Widerrufe.

Vor wissenschaftlicher Ausführung vollständige Ready-CI und angemessener
methodischer/technischer Review. Startbereite Manjaro-Befehle erst mit dem
geprüften Runner bereitstellen. Je Abschnitt Ergebnisordner und benachbarte
`-call.json` zusammen erhalten; lesende Gesamtverifikation separat bewahren.
Originalarchive unverändert im gemeinsamen Archivordner plus unabhängiger
Zweitkopie, beide SHA-256-geprüft; Zuordnung und Sicherungsstand im bestehenden
[Ergebnisindex](results_index.md) gemäß [Archivrichtlinie](results_archiving.md).
GitHub-Uploads optional; keine großen Archive in Git. Dieser Plan belegt
weder technische Implementierung noch wissenschaftliche Ausführung oder Sicherung.
