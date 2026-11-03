# Bedienung: Vergleich des äußeren Suchbudgets

Der [Methodenplan](search_duration_plan.md) wurde vor Implementierung am Commit
`194cfb499e8c53b8243d19c4d11d58a006baff95` eingefroren, SHA-256
`8906a66930848d733e5b2744d40c5fa9c4051db2b876e200908d74ae9ac0b75d`.
Die [Literaturgrundlage](search_duration_literature.md) begründet die
Budgetprüfung, keinen optimalen Iterationswert oder garantierten Erfolg.

Der erste Lauf blieb [beim Replay unvollständig](search_duration_results_manjaro_001.md).
Für Format 2 gilt zusätzlich die vor Code eingefrorene
[Verifikationsergänzung](search_duration_verification_plan.md), Commit
`2a0b50926cd2983d0cd6cc1307ccc28d0a2822fa`, SHA-256
`b6f7cef2227eeacccf8156d02e8899e6fc83b7bd1f29735c1a402922a9d83062`.
Die zusätzlich gebundene [Tabellenpräzisierung](search_duration_table_loss_note.md)
trennt Pandas-CSV-Einlesen von nativer Reduktion: Commit
`fee62058992c84a9930aa765233ebdc095c54cb1`, SHA-256
`56c0807127ff208148df9057607c698218bf87b0cdcf73471b58add14485372c`.
Diese Bedienung beschreibt die neue vollständige Serie `duration-manjaro-002`.

20 frische Suchen kreuzen K/A mit 200/2.000 Suchiterationen bei denselben fünf
vorab festgelegten Seeds. Sie sind nach dem Teilstand nicht mehr vollständig
ungesehen. Konstantenoptimierung 100/2, Populationen, Daten,
Originalauswahl und Diagnosegrenzen bleiben gleich. Keine Wiederaufnahme
kurzer Läufe und keine Übernahme früherer Zellen als neue Kontrollen.

## Technische Voraussetzung

Die vollständige technische CI muss am dokumentierten Implementierungs-Head
bestanden sein. Ein späterer Merge ist nur bei bestätigter Baumgleichheit
derselbe geprüfte Dateistand. Kein eigenständiger Merge durch diesen Ablauf.
Lokale technische Integration bei Bedarf:

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/check_search_duration_integration.py --output results/duration-technical-001
```

Sie prüft zehn native Optionsobjekte und 20 Pythonprofile, feste Referenzen
und Grammatikgegenfälle. Fünf frische Worker laufen ausschließlich am separaten
Achtpunkt-Signal `y=1+t`: K2, A2, K3, A3, K2. Der tatsächliche Aufruf an
`equation_search` wird auf das jeweilige Budget geprüft; beide K2-Fronten
müssen identisch sein. Dieser Test führt keine wissenschaftliche Zelle aus.

Zusätzlich prüft die volle CI mit `scripts/check_duration_replay.py` die zwei
vorhandenen CSV-Bäume nativ ohne Suche/Fit. Die Fixture ist ein ausdrücklich
nachträglicher Regressionstest, kein wiederhergestellter Originalbaumexport.

## Versionierte Verifikation

Nur der neue Suchbudgetworker aktiviert `duration_replay.verify_loss_replay`;
der Standardadapter und ältere Kontrollpfade behalten ihre bisherige skalare
Prüfung. Jeder Kandidat erhält einen `loss_replay`-Nachweis. Der Elternprozess
prüft dessen Inhalt erneut einschließlich Tabellenverlust, unabhängiger
Python-MSE und Fehlergrenze. Fehlende oder veränderte Nachweise sperren die
Serie. Die Originalauswahl verwendet weiterhin den gespeicherten nativen
Trainingsverlust, keine korrigierte oder diagnostische MSE.
Der Tabellenwert bleibt als tatsächlich von PySR/Pandas gelesener Wert
erhalten; für ihn gilt der unveränderte Vergleich `rtol=1e-10, atol=0` zum
nativen Verlust. Die Gamma-Schranke prüft echte Reduktionswerte gegen ihre
Residuen, nicht zusätzlich die Rundung des CSV-Parsers.

Die rationale Schranke im gebundenen Plan ist ein Genauigkeitsvertrag einer
direkten Quadratsummenreduktion. Die vorhandene Python-Funktion verwendet
tatsächlich eine skalierte BLAS-Norm, Division durch sqrt(n) und Quadrieren;
sie wird nicht ersetzt. Ihr konkretes Ergebnis wird unabhängig gegen die
exakte rationale Quadratsumme geprüft. Es wird **keine allgemeine
Fehlergarantie für jede BLAS-Implementierung** vorausgesetzt. Überschreitet
ein Ergebnis die Schranke, bleibt es abgelehnt. Der normale Zahlenbereich
gilt auch für Quadrate und unnormalisierte Quadratsumme; Unter-/Überlauf wird
nicht durch einen absoluten Größenboden verdeckt.

Der optionale Strukturerkenner und die Parameterdiagnose tragen Version 2.
Sinusphasen behalten getrennte rationale Radiant- und Pi-Anteile; die
Umrechnung wird durch rationale Pi-Intervalle geprüft. Nur der neue
Suchbudget-Diagnosepfad aktiviert Produkte/Quotienten mit Sinus oder Kosinus.
Ältere Aufrufer nutzen weiterhin den bisherigen Erkenner. Beide numerischen
Parameterreplays, Kurvengrenzen und ursprüngliche Diagnosegates bleiben nötig.

## Einmalige Serie auf Manjaro

Im sauberen Checkout des geprüften Commits mit der bestehenden gepinnten
[Python-/Julia-Umgebung](julia_startup.md) prüfen:

```bash
git status --short
git rev-parse HEAD
sha256sum results/representation-manjaro-001.tar.gz
```

Erwarteter Eingangsarchivhash:
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Das frühere Originalarchiv ist Datenquelle; sein Code wird nicht ausgeführt.
Der Treiber prüft Archivhash und Float64-Bits selbst. Diagnosepunkte und
Wahrheit gelangen nicht an die Suchworker.

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_search_duration.py --archive results/representation-manjaro-001.tar.gz --output results/duration-manjaro-002 --label manjaro
```

Das Ausgabeverzeichnis muss neu sein. **600 Sekunden je Worker, insgesamt
7.200 Sekunden einschließlich Vorprüfungen und Abschlussverifikation.**
Die Gesamtgrenze ist keine Laufzeitprognose. Fehler oder Zeitüberschreitung
beenden die eigenen Prozessgruppen; Teilstände bleiben erhalten. Keine
automatischen Wiederholungen, Ersatzseeds oder Verlängerungen. Ein bestehender
fremder Timer wird nicht überschrieben. Dieser Pfad ist für Linux vorgesehen.

Nach Abschluss oder Abbruch unverändert sichern:

```bash
tar -czf results/duration-manjaro-002.tar.gz -C results duration-manjaro-002
sha256sum results/duration-manjaro-002.tar.gz
```

Bestehende Archive erhalten; gegebenenfalls einen neuen Sicherungsnamen
verwenden. Archivierung allein bedeutet keine bestandene Abschlussprüfung.

## Artefakte und Einordnung

- `plan.md`, getrennte Trainings-/Diagnosedateien und `runtime/` binden Plan,
  Eingaben und konsumierte Quellen. Ursprüngliche Verbrauchsanker bleiben
  gegenüber späterer Neuhashung maßgeblich.
- `options.json` enthält zehn native Seed-/Grammatikprofile und alle 20
  Pythonprofile. `references.json` prüft feste Syntax-/Einheiten-/Aliasfälle.
- `cell-01/` bis `cell-20/` erhalten vollständige Originalfronten, Auswahlindex,
  Bäume, Vorhersagen, Residuen, MSE, native Options-/Plugin-/BLAS-Nachweise.
  `search_invocation.json` bestätigt den einen abgeschlossenen Aufruf mit
  angefordertem Budget ohne Warmstart, Gewichte oder Startformeln.
- `report.json` und `summary.md` zeigen Originalauswahlen und getrennte
  Befunde. Vier Gruppen, 20 Seedpaare, Fehlerwerte mit Verfügbarkeit und
  endlichen Nennern, Erfolgswechsel und Kosten bleiben nachvollziehbar.
- `checksums.json` sichert Paketkonsistenz, keine externe Authentifizierung.
  Positive Berichte werden zuletzt veröffentlicht und bei Abschlussfehlern
  widerrufen.

Erst alle 20 verifizierten Zellen und eine bestandene Abschlussprüfung geben
Gruppenaggregate und Paardifferenzen frei. Bei einem Abbruch bleiben sie `null`;
verifizierte Einzelresultate bleiben sichtbar. Kein Reranking oder Nachfit.

Primär wird innerhalb jeder Grammatik die Erfolgszahl bei 2.000 mit jener
bei 200 verglichen. Mehr Erfolge plus mindestens eine neu erfolgreiche,
strukturell und im Parameterreplay unterstützte Originalauswahl sind ein
positives Entwicklungssignal. Eine bessere Approximation allein bestätigt
keine freie Strukturentdeckung. Die Grammatikunterschiede und ihre
Wechselwirkung mit dem Budget bleiben getrennt sichtbar.

Fünf vorab festgelegte, teilweise bereits gesehene Seeds am bekannten Signal
sind keine allgemeine Leistungsvalidierung.
Physikalische Identifikation bleibt `not_assessed`; der Alias-Blindfleck bei
`8*fs` bleibt bestehen. Weitere Tests werden erst anhand der neuen Ergebnisse
begründet und vor Ausführung festgelegt.
