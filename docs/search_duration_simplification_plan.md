# Gemeinsames Suchprofil ohne verlustübernehmende Vereinfachung

Vorbereitung vom 03.11.2026 auf Grundlage des
[Originalarchiv-Audits 002](search_duration_results_manjaro_002.md) und des
Auftrags, eine geprüfte Manjaro-Korrektur samt erneutem Start vorzubereiten.
Dieser Text wird vor Code separat committed und durch Commit/SHA-256 gebunden.
Die Änderung ist im PR gezielt zu prüfen; die Übernahme bleibt ein manueller
Schritt. Frühere Pläne und Originalarchive bleiben unverändert.

## Befund und begrenzte Abhilfe

SymbolicRegression 2.5.1 kann nach algebraischer Vereinfachung den Verlust
des vorherigen Float64-Baums behalten. Beide betroffenen nativen Pfade sind
an einem festen Achtpunkt-Gegenbeispiel nachgewiesen. Der exakte historische
Mutationsweg der gescheiterten fünften Zelle ist aus ihrem Archiv nicht
bewiesen; eine Garantie gegen sämtliche möglichen Backendfehler folgt nicht.

Für den Suchbudgetpfad im neuen Format 3 wird deshalb `should_simplify=false`
verbindlich, in beiden Grammatiken, beiden Budgets und allen Seeds. Dies
unterbindet die automatische Populationsvereinfachung und die native
Simplify-Mutation. Alle Operatoren und erlaubten Formeln bleiben verfügbar;
es gibt keine zusätzliche Grammatikregel, Konstantengrenze oder bekannte
Ringdown-Struktur. Normale Mutation, Kreuzung und lokale Konstantenoptimierung
bleiben erhalten. Ältere Kontrollpfade behalten ihren Standard `true`.

Das ist eine gemeinsame Änderung des Suchalgorithmus, keine rein passive
Verifikation: Suchtrajektorien, Komplexitäten und gefundene Fronten können sich
ändern. Der nächste Vergleich gilt ausdrücklich unter diesem Profil; frühere
Teilzellen dürfen nicht mit ihm zu einem Ergebnis kombiniert werden. Der
200/2000-Faktor und der Grammatikfaktor bleiben untereinander gekreuzt.

Erwogene Alternativen: Ein größerer Verlusttoleranzwert würde einen falschen
Verlust bestätigen und wird verworfen. Nachträgliches Ersetzen gespeicherter
Verluste oder Umwählen der Front wird verworfen. Ein eigener Fork bzw. das
Ersetzen interner Backendmethoden mit Neuberechnung nach jeder Umformung wäre
eine umfangreichere Algorithmusänderung; zunächst wird der vorhandene native
Schalter verwendet. Kein Wechsel der Bibliotheksversionen.

## Unveränderte Verträge

Die [Verifikationsergänzung](search_duration_verification_plan.md) und die
[Tabellenpräzisierung](search_duration_table_loss_note.md) bleiben wirksam:
Originalbaum und -verlust, Kandidatenreihenfolge, Originalauswahl, alle
Vorhersage-, Residuen-, Normalbereichs- und rationalen Reduktionsprüfungen.
Jede verbleibende Inkonsistenz führt zum Abbruch; keine Ersatzwahl,
kein diagnostisches Reranking und keine Freigabe einer Teilserie.

Unverändert bleiben Trainingsdaten und getrennte Diagnose, Sekundenkoordinate,
100/2-Konstantenoptimierer, beide Häufigkeitsschalter, Haswell/Threadlimit 1,
serielle Ausführung, Seedabbildung, beide Grammatiken, 200/2000 Iterationen,
Populationen und Zyklen, Erfolgskriterien und Auswertung. Kein Warmstart und
keine Zusatzsuche. Physikalische Identifikation bleibt `not_assessed`.

Die Änderung wird im tatsächlichen nativen Optionsobjekt absolut geprüft,
schon vor dem ersten Worker und bei jedem Aufruf des bestehenden Guards.
Auch der Elternprozess prüft die konkrete Option und Pythonparameter jeder
Zelle, einschließlich der ersten. Alle anderen Optionsfelder und Plugins
bleiben vollständig gegen das bestehende Profil geprüft.

## Prüfungen und späterer Start

- Fester unabhängiger Float64-Gegenfall für beide alten Vereinfachungspfade;
  geänderte Option verhindert die Umformung und setzt das Mutationsgewicht
  auf null. Beide Grammatiken prüfen, ohne wissenschaftliche Suche/Fit.
- Die tatsächlich gespeicherte Verlustabweichung aus Zelle 5 bleibt als
  Regression abgelehnt; konsistente Replays und die früheren Nähe-null-Fälle
  bleiben akzeptiert. Keine aus dem Archiv geladene ausführbare Serialisierung.
- Falsche/fehlende native Option, manipulierte erste/spätere Zelle, unveränderte
  frühere Profile und Planbindung prüfen. Bestehende vollständige Python-/
  Julia-CI sowie fünf kleine technische K2–A2–K3–A3–K2-Worker bleiben erforderlich.
- Gezieltes KI-basiertes Review dieser gemeinsamen Profiländerung samt
  Grenzen der Ursachenzuordnung vor Merge; keine wissenschaftliche Cloud-Suche.

Nach bestandenen Prüfungen und manueller Übernahme ist `duration-manjaro-003`
vorbereitet: alle 20 Prozesse frisch, gleiche Seeds 20261103–20261107 und
Reihenfolge, 600 Sekunden je Worker, 7200 Sekunden insgesamt einschließlich
Elternarbeit und Finalisierung. Kein Fortsetzen von Zelle 5 und keine Übernahme
der vier früheren Zellen. Die wiederverwendeten Seeds gehören weiterhin zur
adaptiven Entwicklung am bekannten Signal, nicht zu ungesehenen Kontrollen.
Aggregate werden erst nach vollständiger Verifikation aller 20 neuen Zellen
freigegeben. WSL2-Portabilität und CPU-Parallelisierung sind getrennte Arbeiten.
