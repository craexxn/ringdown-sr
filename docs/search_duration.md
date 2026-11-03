# Bedienung: Vergleich des äußeren Suchbudgets

Der [Methodenplan](search_duration_plan.md) wurde vor Implementierung am Commit
`194cfb499e8c53b8243d19c4d11d58a006baff95` eingefroren, SHA-256
`8906a66930848d733e5b2744d40c5fa9c4051db2b876e200908d74ae9ac0b75d`.
Die [Literaturgrundlage](search_duration_literature.md) begründet die
Budgetprüfung, keinen optimalen Iterationswert oder garantierten Erfolg.

20 frische Suchen kreuzen K/A mit 200/2.000 Suchiterationen bei fünf neuen,
vorab festgelegten Seeds. Konstantenoptimierung 100/2, Populationen, Daten,
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
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_search_duration.py --archive results/representation-manjaro-001.tar.gz --output results/duration-manjaro-001 --label manjaro
```

Das Ausgabeverzeichnis muss neu sein. **600 Sekunden je Worker, insgesamt
7.200 Sekunden einschließlich Vorprüfungen und Abschlussverifikation.**
Die Gesamtgrenze ist keine Laufzeitprognose. Fehler oder Zeitüberschreitung
beenden die eigenen Prozessgruppen; Teilstände bleiben erhalten. Keine
automatischen Wiederholungen, Ersatzseeds oder Verlängerungen. Ein bestehender
fremder Timer wird nicht überschrieben. Dieser Pfad ist für Linux vorgesehen.

Nach Abschluss oder Abbruch unverändert sichern:

```bash
tar -czf results/duration-manjaro-001.tar.gz -C results duration-manjaro-001
sha256sum results/duration-manjaro-001.tar.gz
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

Fünf neue Seeds am bekannten Signal sind keine allgemeine Leistungsvalidierung.
Physikalische Identifikation bleibt `not_assessed`; der Alias-Blindfleck bei
`8*fs` bleibt bestehen. Weitere Tests werden erst anhand der neuen Ergebnisse
begründet und vor Ausführung festgelegt.
