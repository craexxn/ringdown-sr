# Lokales Optimiererbudget bei freier, uneingeschränkter Suche

Angenommener Entwicklungsvergleich vom 04.11.2026; vor Implementierung
eingefroren. Die Zustimmung umfasst Vorbereitung und technische Prüfung hier
und die anschließende einmalige wissenschaftliche Serie auf Manjaro.

## Anlass und begrenzte Frage

Die [feste Konstantendiagnose](constant_diagnostic_results_manjaro_001.md)
erreichte unter 20/2 keinen, unter 100/2 alle 24 Kurvenerfolge. Die gewählten
100er-Verläufe benötigten 42–89 Schritte. Der spätere
[freie Vergleich](free_optimizer_budget_results_manjaro_001.md) meldete
64–80 % kleinere Trainings-MSE, aber weiterhin 0/3 Kurvenerfolge je Profil.
Dieser zweite Befund beruht auf nachgerechneten Berichtsauszügen, keinem
vollständigen Originalarchivaudit. Daraus folgt kein Nachweis, dass 100
heute der Engpass ist oder eine weitere Erhöhung denselben Gewinn bringt.

Im vollständig geprüften [Suchbudgetlauf 004](search_duration_results_manjaro_004.md)
erreichte unrestricted 3/5 beziehungsweise 4/5 Kurvenerfolge bei 200/2.000
äußeren Iterationen; die eingeschränkte Grammatik erreichte 2/5 und 3/5.
Ein neuer unrestricted-Erfolg besitzt eine unterstützte Ringdown-Struktur.
Ein anderer Seed gelingt bei 2.000 nur mit eingeschränkter Grammatik.
Die Beschränkung wird für diesen Folgeschritt zurückgestellt, ohne eine
allgemeine Unterlegenheit aus fünf adaptiven Seeds abzuleiten.

Frage: Verbessern mehr lokale Schritte, mehr zusätzliche Konstantenstarts
oder ihre Kombination die ursprüngliche Auswahl bei fest 200 äußeren
Suchiterationen? 300 und fünf Neustarts sind vorab gewählte Teststufen,
keine Literaturwerte für ein Optimum. Die äußere Staffel 200–5.000 und
Übertragbarkeit auf neue Signale bleiben getrennte spätere Entscheidungen.

## Faktoren und gemeinsame Einstellungen

| Profilkennung | Maximale lokale Iterationen | Zusätzliche Neustarts |
| --- | ---: | ---: |
| local_100_2 | 100 | 2 |
| local_300_2 | 300 | 2 |
| local_100_5 | 100 | 5 |
| local_300_5 | 300 | 5 |

Dies ist ein 2×2-Vergleich zweier ausdrücklich variierter Faktoren, kein
Einzelfaktorexperiment. Alle vier Gruppen verwenden ausschließlich
unrestricted (`nested_constraints=None`) und `should_simplify=false`.
Andere Profile und frühere eingefrorene Pläne bleiben erhalten.

Je Zelle exakt ein frischer equation_search-Aufruf mit 200 Iterationen,
zwei Populationen à 32 Individuen, 50 Zyklen, Komplexitäts-/Tiefenlimit 20,
beiden Häufigkeitsschaltern an, Sekundenkoordinate, Float64 und gewöhnlicher
MSE. Operatoren +, −, ×, ÷, exp, sin und cos sowie Originalauswahl bleiben
wie im Ausführungsstand 79ff670 von #59. Alle weiteren Einstellungen,
Plugins und Optimierertoleranzen einschließlich 10.000 Funktionsaufrufen
je lokalem Versuch bleiben gleich. Keine Warmstarts, Startformeln,
Rauschgewichtung, Nachfits oder zusätzlichen Suchaufrufe.

`optimizer_iterations` ist eine Obergrenze je lokalem Versuch. Der gepinnte
SymbolicRegression-2.5.1-Pfad optimiert zuerst vom ursprünglichen
Konstantenvektor; zwei/fünf Neustarts ergänzen zwei/fünf gestörte Starts,
insgesamt drei/sechs Versuche. Nichtnullkonstanten werden für jeden Neustart
mit 1+0,5·Normal(0,1) multipliziert, Nullkonstanten durch Normal(0,1) ersetzt.
Dies sind keine gleichmäßig global verteilten Starts. Bei einer reellen
Konstante bleibt der Newton-Sonderpfad, sonst BFGS mit Backtracking und
numerischer Differentiation. Ohne optimierbare Konstanten kein lokaler Fit.
Früheres Stoppen bleibt möglich; fehlende Solver-Abbruchstatus werden nicht
aus Callbackzahlen erfunden.

Mehr Neustarts ändern RNG-Verbrauch und anschließende Suchtrajektorien.
Gleiche Seedkennungen bedeuten daher keine identischen Strukturpfade.
Auch zusätzliche lokale Schritte können Fronten und Selektion verändern.
Der Vergleich misst die Wirkung des gesamten jeweiligen Suchprofils.

## Fünf neue Seeds, 20 frische Zellen

Vorab festgelegt: 20261120, 20261121, 20261122, 20261123, 20261124.
Diese Kennungen wurden bei Planerstellung im Projekt nicht wissenschaftlich
ausgeführt. Ihre PySR-Abbildung auf native Seeds wird absolut geprüft.
Das bekannte Signal und die adaptive Wahl des Designs bleiben Entwicklung,
auch mit neuen Seedkennungen. Keine unabhängige Leistungsvalidierung.

Mit B=local_100_2, I=local_300_2, R=local_100_5, X=local_300_5 gilt:

| Seed | Reihenfolge |
| --- | --- |
| 20261120 | B, I, X, R |
| 20261121 | I, R, B, X |
| 20261122 | R, X, I, B |
| 20261123 | X, B, R, I |
| 20261124 | B, I, X, R |

Die ersten vier Blöcke gleichen Positionen und sämtliche zwölf gerichteten
Nachbarschaftspaare innerhalb der Blöcke aus. Der fünfte wiederholt die
erste Folge; bei fünf Blöcken ist vollständiger Positionsausgleich unmöglich.
Zellen werden sequenziell in frischen Prozessen ausgeführt. Kein Fortsetzen
alter Suchzustände, Übernehmen historischer Kontrollzellen, Ersatzseed oder
automatischer Wiederholungsversuch.

## Daten, Kontrolle und Auswahl

Eingang bleibt `representation-manjaro-001.tar.gz`, SHA-256
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
128 originale Trainingswerte bei t=j/4096, bekanntes rauschfreies Signal
A=1, f=250 Hz, tau=0,008 s, phi=0. Nur Zeit und Beobachtung gelangen an
den Worker. 889 innere Achtelpunkte und Wahrheit bleiben beim getrennten
Referenz-/Diagnosepfad. Keine Änderung der eingefrorenen Datenbits.

Ein neuer gemeinsamer nativer Wrapper delegiert unverändert an die bestehende
numerische Zielfunktion. Alle 20 Seed-/Profilkombinationen werden vorab mit
echten nativen Optionsobjekten geprüft. Beim tatsächlichen Callback und im
Elternprozess werden beide Budgetfelder, Seed, uneingeschränkte Grammatik,
abgeschaltete Vereinfachung, alle übrigen Optionen und konkreten Plugins
absolut geprüft, auch für die erste Zelle. Nur einzeln bestätigte variable
Felder dürfen für den anschließenden gemeinsamen Optionsvergleich normalisiert
werden. Der tatsächliche äußere Aufruf wird unverändert durchgereicht und
auf sein angefordertes Budget, frischen Zustand und einen Aufruf geprüft.

Alle Originalkandidaten, Reihenfolge, native Verluste, Tabellenwerte,
Vorhersagen und Residuen bleiben erhalten. Auswahl ist weiterhin minimale
native Trainings-MSE, dann Komplexität, dann erste Originalposition bei
Gleichstand. Die [gebundene Vorhersageprüfung](search_duration_prediction_plan.md),
getrennte [Verlustverifikation](search_duration_verification_plan.md) samt
[CSV-Präzisierung](search_duration_table_loss_note.md) und Parameter-/Aliasreplays
gelten unverändert. Der Elternprozess berechnet Nachweise aller Kandidaten
erneut. Kein Ersatz eines abgewiesenen Kandidaten, keine Lockerung,
Strukturerweiterung oder diagnostische Neuauswahl.

## Endpunkte und vorab bestimmte Kontraste

Primär ist je Gruppe C die Anzahl erfolgreicher Originalauswahlen unter fünf
Seeds. Erfolg verlangt bei derselben Auswahl auf Trainings- und Diagnosegitter
relative_rms ≤ 0,001 und relative_max ≤ 0,01. Anerkannte Struktur, Parameter
und beide Replays bleiben getrennte, nachgelagerte Nachweise.

Vier einfache Faktoreffekte werden mit jeweils fünf Seedpaaren berichtet:

- Lokale Schritte: I−B bei zwei Neustarts und X−R bei fünf Neustarts.
- Neustarts: R−B bei 100 Schritten und X−I bei 300 Schritten.

Zusätzlich wird X−B mit fünf Paaren als kombinierte Profiländerung berichtet;
dieser Kontrast identifiziert keinen isolierten Faktor. Insgesamt 25
Paaraufzeichnungen, ohne sie als unabhängige Wiederholungen zu zählen.
Die drei Vergleiche I/B, R/B und X/B zur frischen Baseline werden gemeinsam
sichtbar. Keine nachträgliche Auswahl nur eines günstigen Kontrasts.

Jeder Kontrast enthält C links/rechts, Differenz, alle vier Erfolgswechsel,
Status und kontinuierliche Fehler beider Raster, endliche Nenner und Kosten.
Nur bei höherem C und mindestens einem neuen 0→1-Kurvenerfolg mit unterstützter
Struktur, passenden Parametern und bestandenen Replays derselben höheren
Originalauswahl gilt `supported_structure_gain`. Höheres C ohne diesen neuen
Strukturnachweis heißt `approximation_gain_only`; sonst
`hypothesis_not_supported`. Ungewählte gute Kandidaten zählen separat und
erzeugen keinen positiven Auswahlbefund. Unbestimmte Diagnosen bleiben gesperrt.

Zählinteraktion: (C_X−C_R)−(C_I−C_B). Gegenläufige einfache Effekte dürfen
nicht durch gepoolte Erfolgsquoten verdeckt werden. Eine positive Interaktion
beweist bei fünf Seeds keine allgemeine Synergie. Keine Signifikanz- oder
Überlegenheitsbehauptung und kein automatisch ausgewähltes Gewinnerprofil.
Eine Folgeentscheidung berücksichtigt sämtliche Kontraste, Strukturbelege
und Aufwand; sie benötigt einen eigenen festgelegten Vergleich. Ein Vorteil
bei 200 äußeren Iterationen muss bei größerem Suchbudget bestätigt werden.

Pro Gruppe alle fünf Originalauswahlen mit Formel, Komplexität, Fehlern,
Struktur-/Parameterstatus sowie Minimum/Median/Maximum verfügbarer Metriken
mit Nenner. Aufwand: Workerwandzeit, Fitzeit einschließlich JIT/Export,
Callbackzahlen und verfügbare Backendzähler. Verschiedene Zähler sind nicht
gleichbedeutend mit eindeutigen Bäumen oder lokalen Schritten. Größere
Iterationsgrenzen sind keine Laufzeitgarantie; Kosten dürfen nicht allein
aus dem Produkt Iterationen×Versuche abgeleitet werden.

`physical_identification=not_assessed`. Der bekannte Alias-Blindfleck des
Achtelrasters bei 8·fs=32768 Hz bleibt dokumentiert. Ein kleinerer Trainingsfehler
allein genügt nicht; der Gegenfall aus Lauf 004 bleibt maßgebliche Warnung
vor dieser Schlussfolgerung. Übertragbarkeit, Rauschen und Hauptversuche offen.

## Grenzen, Artefakte und technische Prüfung

Bestehende organisatorische Grenzen bleiben 600 Sekunden je Suchworker und
7.200 Sekunden insgesamt, einschließlich Vorprüfung, Elternarbeit und
Finalisierung. Es sind Abbruchgrenzen, keine Laufzeitprognosen. Ein Abbruch
beendet eigene Prozessgruppen und erhält den Teilstand; Gruppenaggregate,
Paardifferenzen und Entscheidungen bleiben bis zu 20 verifizierten Zellen
und erfolgreicher Abschlussprüfung null. Keine Hochrechnung aus Teilserien.
Ursprüngliche Verbrauchsanker bleiben maßgeblich gegenüber späterer Neuhashung.
Positive Veröffentlichung erfolgt zuletzt; Abschlussfehler widerrufen sie
und entfernen das Abschlussmanifest.

Neues versioniertes Serienformat, gebundene Planbytes/Commit/SHA,
Trainings-/Diagnosedateien getrennt, runtime-Quellkopien, Vorprüfungen,
vollständige Zellartefakte, Bericht und Abschlussmanifest. Historische
Lesbarkeit und Originalarchive bleiben erhalten. Keine allgemeine Bereinigung
im Implementierungsschritt; die vorgemerkte kleine Bestandsaufnahme bleibt offen.

Technische Prüfungen umfassen Design/Planbindung, alle nativen Profilfelder
und falsche Optionen, echte Callbackabweisung vor numerischem Eintritt,
alle vier Profile an separaten Achtpunktdaten y=1+t mit zwei äußeren
Iterationen und frischer Baselinewiederholung, unveränderte Delegation,
vollständige Elternkontrolle einschließlich ungewählter Kandidaten, sämtliche
Erfolgsrichtungen, gegenläufige Effekte, Zeitlimits und Veröffentlichungsausfälle.
Diese winzigen technischen Suchen sind keine wissenschaftlichen Zellen.
Die bestehende vollständige technische CI bleibt erforderlich. Keine
wissenschaftliche Suche oder Fit am Ringdown in dieser Cloud.
