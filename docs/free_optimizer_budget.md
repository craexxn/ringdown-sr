# Freier Optimiererbudgetvergleich

Der [angenommene Methodenplan](free_optimizer_budget_plan.md) ist am Commit
`bb4862034b49b89dcc37d8341814e42aa02989c5` eingefroren, SHA-256
`b63e66461e3a380f9e8ca5c127e8c5f99cd2a0d574be7be1603f18f56292907b`.
Dieser Kontrollpfad vergleicht sechs frische freie Suchen mit 20 beziehungsweise
100 maximalen lokalen Optimiereriterationen und zwei zusätzlichen Neustarts.
Beide Häufigkeitsschalter bleiben in beiden Armen aktiviert. Originalzeiten
bleiben Sekunden; es gibt keine Zeitstreckung, Templates oder Wahrheitsstarts.

Der Versuch ist adaptive Methodenentwicklung an demselben bekannten Signal
und denselben drei Entwicklungsseeds. Er bestimmt kein Produktionsprofil und
ist kein Übertragbarkeitsnachweis. Ein positives Ergebnis wird ausschließlich
für die ursprüngliche Auswahl berichtet; Frontkandidaten ersetzen sie nicht.

## Technische Prüfung

Im Projektordner, mit den unveränderten Pins und dem dokumentierten
[Python-/Julia-Startweg](julia_startup.md):

```bash
env -u VIRTUAL_ENV uv run --locked ruff check .
env -u VIRTUAL_ENV uv run --locked ruff format --check .
env -u VIRTUAL_ENV uv run --locked pytest -q
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/check_free_optimizer_integration.py --output results/free-budget-technical-001
```

Der letzte Befehl startet Options- und feste Referenzprüfungen sowie drei
frische Worker mit zwei Suchiterationen auf einem eigenen Achtpunkt-Signal
`y=1+t`, in der Reihenfolge 20–100–20. Beide 20er-Fronten müssen identisch sein.
Dies sind technische Suchen; keine der sechs wissenschaftlichen Zellen wird
ausgeführt. Der vollständige CI-Umfang bleibt zusätzlich verbindlich.

Eine gesonderte Optionsvorprüfung ohne Fit/Suche ist möglich:

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_python.py scripts/check_free_optimizer_backend.py --mode options --output results/free-budget-options-001.json
```

`--mode references` prüft stattdessen feste 250-/4346-/33018-Hz-Bäume unter
beiden Budgets sowie Einheiten- und Seed-/Budgetgegenfälle ohne Optimierung.
Beide Vorprüfungen laufen auch vor der wissenschaftlichen Serie in eigenen
Prozessen. Neue Worker übernehmen daraus keine Bäume, Datenkontexte oder RNG-Zustände.

## Einmalige Manjaro-Serie nach technischer Freigabe

Erst am sauberen, technisch geprüften Implementierungsstand ausführen.
`git status --short` muss leer sein; `git rev-parse HEAD` mit dem freigegebenen
Commit abgleichen. Bestehende Ausgaben werden nicht überschrieben. Der interne
Profilworker ist kein eigenständiger Suchbefehl aus `scripts/`; er erwartet
eine verifizierte Laufzeitkopie mit benachbartem `driver.py` und Manifest.

Eingabe ist das frühere Originalarchiv der Darstellungskontrolle, ausschließlich
als Datenquelle; keine archivierten Python-/Julia-Dateien werden ausgeführt:

```bash
sha256sum results/representation-manjaro-001.tar.gz
```

Erwartet: `a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Der Treiber prüft diesen Hash und die Arraybits selbst erneut. Nur Trainingszeiten
und Beobachtungen gehen in die freien Suchworker; Wahrheit und Diagnosepunkte
werden ausschließlich danach verwendet.

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_free_optimizer_budget.py --archive results/representation-manjaro-001.tar.gz --output results/free-budget-manjaro-001 --label manjaro
tar -czf results/free-budget-manjaro-001.tar.gz -C results free-budget-manjaro-001
sha256sum results/free-budget-manjaro-001.tar.gz
```

Das Gesamtlimit von 60 Minuten umfasst serienbezogene Vorprüfungen, Starts
und Abschlussverifikation. Der Befehl darf nach einem Abbruch nicht mit einem
Ersatzseed oder automatisch größerem Budget wiederholt werden. Teilstände
einschließlich Logs bleiben erhalten und können mit denselben Archivbefehlen
gesichert werden. Über einen erneuten Versuch ist gesondert zu entscheiden.
Haswell/Threadlimit 1 gilt für diesen Kontrollpfad, nicht als allgemeiner Standard.

## Verifikation und Ergebnisdateien

- `plan.md`, `training.npz`, `diagnostic.npz`, `runtime/`: eingefrorener Plan,
  binäre Datenrollen und geprüfte Laufzeitkopien. Quellen, Pins und konsumierte
  Dateien sind vollständig mit Hashes verankert. Vor dem Verbrauch eingefrorene
  Bytes werden nach dem Worker und abschließend erneut geprüft; nachträgliche
  konsistente Neuhashung ersetzt diese Anker nicht.
- `options.json` und `references.json` mit Logs: sechs echte native Optionsobjekte
  beziehungsweise feste Referenzen. Sämtliche Optionsfelder einschließlich
  konkreter Plugins werden absolut und gegen den jeweils passenden Prototyp
  geprüft; erst danach dürfen Seed, Ausgabepfad und Iterationsgrenze variieren.
  Die Optimierertoleranzen bleiben gleich, ebenso der uninstrumentierte Callback
  in den Optimierereinstellungen. Newton bei einer Konstante und BFGS bei mehreren
  Konstanten behalten den bestehenden Backendpfad.
- `cell-01/` bis `cell-06/`: ursprüngliche Requests, Profile, Manifeste, alle
  Kandidaten samt Reihenfolge, Originalindex, Vorhersagen, Residuen, MSE,
  Backend-/Plugin-/RNG-Nachweise sowie geladene BLAS-Pools vor/nach dem Fit.
  Jeder Kandidat wird nachgerechnet; ein Widerspruch stoppt ohne Neuauswahl.
- `report.json`: getrennte Such-/physikalische Diagnosen, beide Fehlergitter,
  Replay-/Parameterstatus, Originalauswahlen und vollständiger Abbruchzustand.
  Fit-Callbackzahlen und Gesamtzahlen bleiben getrennt; die zusätzliche
  Nullkurve nach dem Fit erhöht nur den Gesamtzähler. Nicht exportierte RNG-
  oder Solverzustände werden nicht aus Zählern rekonstruiert.
- `summary.md`: kurze Übersicht der Zellen und des vergleichenden Kurvenbefunds.
  Gruppenstatistiken mit endlichen Nennern, Seed-Differenzen und Erfolgswechsel
  werden erst nach sechs vollständig geprüften Zellen und bestandener
  Abschlussverifikation freigegeben. Sonst bleiben alle Aggregate `null`.
- `checksums.json`: abschließendes Dateimanifest zur Paketkonsistenz. Es ist
  keine externe Authentifizierung von Gerät oder Ausführung.

`C100 > C20` bedeutet mehr, `C100 < C20` weniger erfolgreiche Originalauswahlen
in diesen drei Entwicklungsfällen. Gleichstand und Nullerfolg bleiben getrennt.
Struktur-/Parameterunterstützung muss dieselbe kurvengute Originalauswahl
betreffen und alle Replaygates bestehen. Gegenläufige Seeds, gute ungewählte
Kandidaten und historische Abweichungen bleiben sichtbar. Gleiche Seeds
garantieren keine gleichen freien Suchpfade, Restartvektoren oder Kosten.

`physical_identification` bleibt `not_assessed`; das Achtelraster behält den
Alias-Blindfleck bei `8*fs=32768 Hz`. Die Weiterentscheidungen stehen verbindlich
im Plan. Vor Übertragbarkeits-/Gewichtungsstudien ist ein eigenes Design nötig.
