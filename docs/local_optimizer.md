# Bedienung: lokales Optimiererbudget auf Manjaro

**Abgeschlossen am 04.11.2026:** `local-optimizer-manjaro-001` enthält alle
20 verifizierten Zellen. [Ergebnis und Grenzen](local_optimizer_results_manjaro_001.md)
dokumentieren den unabhängigen Audit. Die folgenden Befehle halten den
abgeschlossenen Laufweg fest; sie geben keine Wiederholung oder zusätzliche
Serie frei. Originalverzeichnis und Archiv erhalten.

Der [angenommene Plan](local_optimizer_plan.md) wurde vor Code am Commit
`e7b457bf8927cdd1b52c51bb3457b54d0c88f066` eingefroren, SHA-256
`793006863a739a973dd3ffcf82c6e665f1a77da7eefee4132555843230df7f47`.
Dies ist ein eigener Entwicklungsvergleich nach dem abgeschlossenen
[Suchbudgetlauf 004](search_duration_results_manjaro_004.md).

## Umfang

20 frische Suchen, ausschließlich unrestricted, jeweils 200 äußere
Suchiterationen. Vier lokale Profile 100/2, 300/2, 100/5 und 300/5 kreuzen
Iterationsgrenze und zusätzliche Neustarts. Fünf vorher festgelegte Seeds
20261120–20261124 und feste Reihenfolge; keine Übernahme alter Zellen.
`should_simplify=false`, beide Häufigkeitsschalter, Daten, übrige Optionen,
Originalauswahl sowie sämtliche Verlust-/Vorhersageprüfungen bleiben gleich.

Die Grenzen bleiben **600 Sekunden je Suchworker und 7.200 Sekunden insgesamt**,
einschließlich Vorprüfungen, Elternnachrechnung und Veröffentlichung. Sie
sind keine Laufzeitprognose. Ein Teilstand erlaubt keine Gruppenwertung und
wird nicht automatisch fortgesetzt oder mit Ersatzseeds ergänzt.

## Vorbereitung nach Prüfung und Merge

Der Ergebnisnachtrag #60 ist als f9f4bae übernommen und die Grundlage des
Implementierungsbranches. Den Implementierungs-PR #61 nach vollständiger
technischer CI übernehmen. Der PR enthält den konkreten, an seinen geprüften
Head gebundenen Vorbereitungsblock mit Baumvergleich zum Merge.
`git switch --detach` vermeidet einen Wechsel auf ein bereits von einem
anderen Worktree belegtes main. Zsh benötigt Anführungszeichen um Git-Ausdrücke
mit `^{tree}`.

Historische Plankommits müssen lokal erreichbar bleiben. Zusätzlich zu main
und dem neuen Implementierungs-PR den Head von #55 holen:

```bash
git fetch origin main
git fetch origin refs/pull/55/head:refs/remotes/origin/pr-55
```

Der neue PR-Head enthält den oben genannten Plancommit. Die aus main erreichbare
Vorhersageplanbindung und der historische Tabellenplan werden lokal geprüft.
Fehlende Historie ist kein Grund, diese Prüfungen auszuschalten.

Im sauberen, geprüften Checkout:

```bash
(
  set -e
  test -z "$(git status --porcelain=v1 --untracked-files=all)"
  export OPENBLAS_CORETYPE=Haswell
  export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
  export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

  env -u VIRTUAL_ENV uv sync --locked --dev --python 3.12.14
  env -u VIRTUAL_ENV uv run --locked --python 3.12.14 \
    python scripts/run_python.py scripts/check_environment.py
  env -u VIRTUAL_ENV uv run --locked --python 3.12.14 \
    pytest -q tests/test_local_optimizer.py tests/test_local_optimizer_driver.py \
    tests/test_duration_verification.py

  printf '%s\n' \
    'a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db  results/representation-manjaro-001.tar.gz' \
    | sha256sum --check --strict
)
```

Das Eingangsarchiv bleibt die ursprüngliche Datenquelle. Das zuletzt erhaltene
duration-Archiv enthält den abgeschlossenen Vergleich und ersetzt sie nicht.
Vorhandene unversionierte Dateien erhalten; bei einem schmutzigen Arbeitsbaum
einen separaten sauberen Checkout verwenden.

## Einmalige wissenschaftliche Serie

Nach erfolgreichen Voraussetzungen im selben geprüften Checkout ausführen.
Ausgabeverzeichnis und Archivname müssen beide neu sein. Der Block archiviert
auch einen Abbruch mit vorhandenem Teilstand und gibt dessen Fehlercode weiter.

```bash
(
  set -e
  test -z "$(git status --porcelain=v1 --untracked-files=all)"
  test ! -e results/local-optimizer-manjaro-001
  test ! -e results/local-optimizer-manjaro-001.tar.gz
  export OPENBLAS_CORETYPE=Haswell
  export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
  export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

  run_status=0
  env -u VIRTUAL_ENV uv run --locked --python 3.12.14 \
    python scripts/run_local_optimizer.py \
    --archive results/representation-manjaro-001.tar.gz \
    --output results/local-optimizer-manjaro-001 --label manjaro \
    || run_status=$?

  if test -d results/local-optimizer-manjaro-001; then
    tar -czf results/local-optimizer-manjaro-001.tar.gz \
      -C results local-optimizer-manjaro-001
    sha256sum results/local-optimizer-manjaro-001.tar.gz
  fi
  exit "$run_status"
)
```

## Artefakte, Auswertung und technische Nachweise

`options.json` enthält alle 20 nativen Seed-/Profilobjekte und Pythonprofile.
`references.json` prüft feste Einheiten-/Aliasfälle und uneingeschränkte Syntax
unter allen vier Profilen, ohne Optimierung. Worker erhalten nur Trainingszeit
und Beobachtung. Pro Zelle bleiben vollständige Originalfront, native Options-
und Pluginfelder, ursprüngliche Auswahl, Verlust-/Vorhersagenachweise sowie
der tatsächliche Suchaufruf mit Budget erhalten. Quellen, Plan und konsumierte
Bytes sind gebunden; die Elternnachrechnung prüft alle Kandidaten.

Erst 20 verifizierte Zellen und erfolgreicher Abschluss geben `summaries`,
`pair_differences` und `comparison` frei. Die vier einfachen Faktoreffekte
und der kombinierte Vergleich zur Baseline bleiben getrennt, insgesamt
25 Seedpaaraufzeichnungen. Positive Struktureinordnung verlangt höheren
Kurvenerfolgszähler und einen neuen 0→1-Erfolg mit Unterstützung genau dieser
Originalauswahl. Gegenläufige Effekte, ungewählte gute Kandidaten, fehlende
Diagnosen und Kosten werden sichtbar; kein automatisches Gewinnerprofil.

Jeder Paarvergleich enthält die ursprünglichen Kosten beider Zellen.
`worker_wall_seconds` umfasst im bestehenden Treiber den gesamten
`run_search_arm`-Aufruf und die anschließende Elternverifikation.
`status.json.total_wall_seconds` beginnt innerhalb dieses Aufrufs unmittelbar
vor der Metadatenerfassung und endet nach dem Workeraufruf sowie dem Lesen
und der Basisprüfung seines Ergebnisses. Es enthält damit auch Metadaten-
und Startvorbereitung im Elternprozess und ist keine reine Prozesslaufzeit.
Fitzeit enthält JIT/Export. Diese Größen werden nicht als reine Optimiererzeit
oder eindeutige Baumzahl ausgegeben.

Die technische CI ergänzt einen festen nativen Abweisungstest und fünf
frische Worker auf separaten acht Punkten y=1+t: alle vier lokalen Profile
mit jeweils zwei äußeren Iterationen, danach eine frische 100/2-Wiederholung.
Beide 100/2-Fronten müssen identisch sein. Die wissenschaftlichen 20 Zellen
werden hier nicht ausgeführt. Frühere Integrationen bleiben erforderlich.

Die Herkunft der bekannten Daten und die adaptive Designwahl begrenzen die
Aussage trotz neuer Seeds. `physical_identification=not_assessed`; der
Alias-Blindfleck bei 8·fs bleibt bestehen. Größere äußere Budgets, neue Signale,
WSL2, Parallelisierung und Bereinigung sind getrennte Folgeschritte.
