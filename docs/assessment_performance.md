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

## Umsetzung

1. Je Prüfzeitpunkt ein begrenztes Archivlesen gemeinsam für Inhaltsbindung
   und Dateiprüfung verwenden. Bei einem neuen Prüfzeitpunkt frisch lesen.
   Die letzte Archivprüfung bleibt hinter den zuvor registrierten Prüfungen
   wie HEAD, auch nach Entfernen der Sperrdatei.
2. Unveränderliche Git-Dateien exportlokal zwischenspeichern; vor dem nächsten
   Export neu anlegen. Der Cache gehört ausdrücklich zur Verbrauchsprüfung
   (`Consumption`), ohne globalen Zustand; vor einer Suche wird der
   Vorbereitungscache geleert. Arbeitsbaum und HEAD weiterhin frisch prüfen.
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
Kein eigenständiger Merge.

## Nachher-Messung und Ergebnisgleichheit

Implementierungsstand `dde3b07f3a59df78f9baeb449811ca3af5ba08dc`, Vergleich gegen
obige Basis, gleiche Originalquellen und Profiler. Ein Zwischenstand
`4a62cb19467c93ed7e5ea0ec2295e73e27910a0b` lieferte dieselben Aufrufzahlen;
anschließend wurde der Cache ausdrücklich an `Consumption` gebunden.

| Messgröße | Vorher | Zwischenstand | Letzter Codestand |
| --- | ---: | ---: | ---: |
| Historischer Export, Profiler-Gesamtdauer | 10,274 s | 10,176 s | 11,633 s |
| Historischer verifizierter Import | 6,281 s | 6,053 s | 7,220 s |
| Historische Bewertung (78 Auswahlen) | 2,089 s | 2,088 s | 2,432 s |
| Historische Veröffentlichung einschließlich Endprüfungen | 0,073 s | 0,072 s | 0,074 s |
| Historische Git-Dateiprozesse | 413 | 388 | 388 |
| Historische Archivlesevorgänge | 72 | 38 | 38 |
| Historische Fingerprintberechnungen | 718 | 328 | 328 |
| Historische Verbrauchsprüfungen / Zeitbudgetprüfungen | 10 / 3.868 | 10 / 3.868 | 10 / 3.868 |
| Gespeicherter Schema-3-Export, Profiler-Gesamtdauer | 0,386 s | 0,406 s | 0,472 s |
| Schema-3-Git-Dateiprozesse | 116 | 114 | 114 |
| Schema-3-Verbrauchsprüfungen / Zeitbudgetprüfungen | 5 / 115 | 5 / 115 | 5 / 115 |

Die Exportmessungen belegen **keinen Zeitgewinn**; der letzte Lauf war langsamer.
Aus diesen einzelnen profilierten Messungen lässt sich weder eine garantierte
Beschleunigung noch die Ursache der Zeitunterschiede ableiten. Belegt sind die
reduzierten Lese- und Rechenwiederholungen. Beim gespeicherten Schema-3-Fall
unterscheidet sich der Vorbereitungscommit vom Exportcommit; der zulässige
Git-Cache kann deshalb nur wenige Zugriffe zusammenlegen.

Die **gleichen 77 Testfälle** bestanden nach der Fixture-Umstellung in
**33,79 s statt 77,90 s**, rund 57 % kürzer. Dieser Vergleich stammt vom
Zwischenstand; die nachfolgende Änderung betrifft nur die explizite Cachebindung.
Die 337 gezielten Fälle einschließlich aller neuen Gegenprüfungen bestanden
am letzten Codestand in 34,28 s. Die abschließende Gesamtsuite und der aktuelle
CI-Stand werden im [Fortsetzungsstand](representation_implementation_status.md)
gepflegt. Eine Einsparung bei nativen CI-Läufen ist damit nicht behauptet.

Alle vier vollständigen Originalarchive wurden am letzten Codestand erneut
verifiziert: 78 Auswahlen, 18 ursprüngliche Gruppen, Korpus `complete`.
Einzelsätze, Zusammenfassung und vier mitgelieferte Originalberichte sind
bytegleich zur Basis. Dasselbe gilt für drei Bewertungen, Zusammenfassung und
Originalresultat des gespeicherten technischen Schema-3-Laufs. Die Berichte
unterscheiden sich ausschließlich in Exportcommit und Quellhashes;
Methodenvertrag und Laufzeitumgebung bleiben identisch. Beide vollständigen
Ausgabemanifeste wurden unabhängig nachgehasht und die Freigaben kontrolliert.

SHA-256 der unveränderten `assessment_records.json`:

- Historisch: `081e67eb1689b8e341adb4c22ef6a8ed72031cddb3b1bfeea27ab455e1dc73c2`.
- Schema 3: `4e03f8b0747ea5a92aeb97859a783a965f598e5b67fc89ee5df480ddf9f061e8`.

Die 14 neuen Fälle prüfen Cachetrennung nach Erfolg/Fehler, bewegliche Refs,
Commit-/Pfadtrennung, fehlgeschlagene Git-Lesevorgänge, frische Archivbytes,
Symlink- und Größenänderungen, alle fünf Veröffentlichungszeitpunkte und
Änderungen in einer vorangehenden Abschlussprüfung nach Entfernen der Sperre.
Ein Fall bestätigt identische Bewertungen bei genau einer Auswertung je
Raster und Originalauswahl. Die gemeinsame Testvorlage wird nach der Suite
auf unveränderte Bytes geprüft; jeder Fehlerfall erhält private Dateikopien.
Automatische Ausführung, reale Herkunftsbindung, Altversionsübernahme und
positive Integration behalten ihre vollständige Vorbereitung.

Die gezielte KI-basierte Eigenprüfung umfasste insbesondere die Reihenfolge
der letzten Archivprüfung, die Lebensdauer des Caches, die unveränderte
vollständige Quellenmenge sowie Vorhersage- und Fixture-Isolation. Sie ersetzt
weder das separate PR-Review noch die vollständige native CI.

Die Rohprofile, Zähler, Vergleichsprogramme, Ausgaben und Testlogs liegen im
zur Reviewübergabe bereitgestellten Nachweispaket. Es enthält auch die vier
Originalarchive zur unabhängigen lesenden Wiederholung; Paketprogramme werden
nicht durch den Export ausgeführt. Reproduzierbare Testauswahl:

```bash
uv run --locked pytest -q --durations=40 \
  tests/test_future_assessment.py tests/test_future_assessment_review.py \
  tests/test_structure_assessment.py tests/test_remainder_assessment.py
uv run --locked pytest -q tests/test_assessment_performance.py
```

Für Exportprofile einen sauberen Checkout des jeweiligen genannten Commits
und neue, getrennte Ausgabeziele verwenden. Archivanker und originale
Bewertungsdaten bleiben verbindlich; gerundete Tabellen sind kein Ersatz.
