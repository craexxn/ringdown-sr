# Laufzeitoptimierung der abgeschlossenen Zusatzbewertung

Stand: 06.11.2026. Technischer Folgeauftrag zu Leitfadenphase 1 nach Übernahme
aller drei Bewertungsstufen. Ausgangsbasis ist
`de33d52aede3903a9745305b52f35c467e0d3b9f` (PR #72), baumgleich zum
geprüften Head `9d4268e162444c141f89cc2b855f8bae56021400`.
Aktueller Branch, PR und Fortsetzung stehen im
[bestehenden Arbeitsdokument](representation_implementation_status.md).

## Umfang und unveränderte Regeln

Optimiert werden Quellenzugriffe, wiederholte Bindungsvergleiche und die
Testvorbereitung. Die drei Bewertungsstufen, ihre Versionskompatibilität,
Beweisgrenzen, Gruppennenner und Originalauswahl bleiben erhalten.
Keine neuen wissenschaftlichen Fits oder Suchreihen, keine veränderten
Kurvengrenzen, kein neues Analysebudget und keine neue Erfolgsaussage.

Jeder bisherige Prüfzeitpunkt bleibt bestehen: Einlesen vor der Anwendung,
Prüfung nach Import, Übergänge zwischen Serien sowie sämtliche Prüfungen
während Veröffentlichung, einschließlich nach Entfernen der Sperrdatei.
Zwischen diesen Zeitpunkten dürfen veränderliche Dateien nicht aus einem
Cache bedient werden. Symlink-/Größenprüfungen und Widerruf bleiben erhalten.
Ein Cache für Git-Dateien darf ausschließlich vollständige unveränderliche
Commit-IDs und sichere Pfade innerhalb genau eines Exports verwenden;
bewegliche Refs, Fehler oder Folgeexporte dürfen keinen alten Treffer erhalten.

## Ausgangsmessung

Messung im selben Cloud-Worktree mit Python 3.12.14 und eingefrorenen
Abhängigkeiten. Historisch werden alle vier vollständigen Originalarchive
lesend exportiert. Der zweite Fall verwendet einen vollständigen Schema-3-Lauf
mit drei festen Python-Testworkern und der kleinen technischen Referenzanpassung;
keine native symbolische Suche. Der gespeicherte Lauf wird anschließend nur gelesen.

Die Exportmessungen verwenden `cProfile` und passive Aufrufzähler. Zeitangaben
enthalten dessen Zusatzaufwand; Unterfunktionen sind einschließlich ihrer
Aufruferarbeit gemessen und dürfen nicht einfach addiert werden. Es handelt
sich um Entwicklungsbenchmarks, nicht um garantierte Laufzeiten oder CI-Kosten.

| Messgröße | Historischer Export (78 Auswahlen) | Gespeicherter Schema-3-Export |
| --- | ---: | ---: |
| Gesamtdauer mit Profiler | 10,274 s | 0,386 s |
| Git-Prozesse zum Lesen von Dateien | 413 | 116 |
| Archivlesevorgänge | 72 | nicht anwendbar |
| Davon begrenztes Lesen / zusätzliche Dateilesung | 42 / 30 | nicht anwendbar |
| Verifizierter historischer Import | 6,281 s | nicht anwendbar |
| Bewertung der 78 Auswahlen | 2,089 s | nicht anwendbar |
| Veröffentlichung einschließlich Endprüfungen | 0,073 s | siehe Profil |

Die gezielte Ausgangssuite aus `test_future_assessment.py`,
`test_future_assessment_review.py`, `test_structure_assessment.py` und
`test_remainder_assessment.py` bestand mit 77 Fällen in 77,90 s. Viele reine
Fehlerfälle benötigen jeweils rund 1,1 s zur Vorbereitung desselben gültigen
Quellenpakets. Die einmalige Erzeugung des separat profilierten Testlaufs
benötigte 1,528 s; sie ist nicht in der lesenden Exportzeit enthalten.

## Daraus abgeleitete Umsetzung

1. Je Prüfzeitpunkt ein begrenztes Archivlesen gemeinsam für Inhaltsbindung
   und Dateiprüfung verwenden. Bei einem neuen Prüfzeitpunkt frisch lesen.
2. Unveränderliche Git-Dateien exportlokal zwischenspeichern; vor dem nächsten
   Export verwerfen. Arbeitsbaum und HEAD weiterhin an den alten Stellen prüfen.
3. Kanonische gemeinsame Quellenbindungen und Fingerprints aus bereits
   verifizierten Daten einmal vorbereiten. Originalvorhersagen für Replay und
   Kurvenbewertung derselben Auswahl wiederverwenden.
4. Für reine Fehlerprüfungen einmal vollständig erzeugte Testquellen jeweils
   in ein eigenes temporäres Verzeichnis kopieren. Automatische Ausführung,
   Vorbereitungszeitpunkt und vollständige Integration weiter separat prüfen.

## Abnahme

Vorher/Nachher-Messungen mit denselben Quellen und Profilierungsbedingungen;
alle 78 Einzelsätze und Gruppenausgaben unverändert, ausgenommen erwartete
Softwareherkunft. Für gespeicherte Schema-3-Läufe ebenfalls identische
Auswahl, Kennzahlen, Beweisspuren und Grenzentscheidungen. Gegenprüfungen für
Änderungen zwischen Prüfzeitpunkten, nach allen Freigabeschritten, Cache-Grenzen
und isolierte Testkopien. Vor Ready passende lokale Gesamtsuite und gezielte
KI-basierte Implementierungsprüfung; danach volle serielle CI und Review.
Kein eigenständiger Merge. Noch kein Nachher-Nachweis auf diesem Planstand.
