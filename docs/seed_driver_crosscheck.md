# Seed-/Treiber-Kreuzvergleich auf Manjaro

Stand: 05.11.2026. Implementierung auf `codex/seed-driver-crosscheck`, ausgehend
von main `b9636ad92ecd57b24b142f39548a7a713d0934a0` nach Ergebnis-PR #66.
Die wissenschaftlichen Kreuzvergleichszellen wurden noch nicht ausgeführt.
Der [vorab gebundene Plan](seed_driver_crosscheck_plan.md) wurde vor dem Code
als Commit `be6fc1bd2339df5b429684dfce8e992073d88506` gespeichert;
SHA-256 `e6e2df830dd2e4254d60bd73a5b9e34678377c9bc1e6a2f81830592e4f85b15e`.

## Zweck und feste Zellen

Der frühere 5/5-Erfolg und der spätere anchor-Misserfolg 0/3 verwendeten
verschiedene Seeds. Zwei Gegenrichtungen grenzen ein, ob derselbe Seed
unter dem jeweils anderen historischen Workerpfad dieselben Ergebnisse liefert:

| Zelle | Seed | Gespeicherte Referenz | Frischer historischer Pfad |
| --- | --- | --- | --- |
| 1 | 20261201 | Staffel, Zelle 2: Kurvenerfolg | Transfer bc4025d |
| 2 | 20261210 | Transfer, Zelle 1: kein Kurvenerfolg | Staffel 5215c5e |

Beide bleiben bei 500/300/5, allgemeiner Grammatik, unveränderten Datenbits,
`should_simplify=false` und den bisherigen numerischen Prüfungen. Es gibt
keine weiteren Seeds, Warmstarts, Nachfits oder automatischen Wiederholungen.
Die Originalauswahl und der Strukturerkenner bleiben erhalten.

## Vorbereitung und Ausführung

Erst den überprüften PR-Stand verwenden; kein eigenständiger Merge. Den
Branch-Head auch nach einem Squash-Merge als Remote-Referenz erhalten, damit
der vorangehende Plancommit erreichbar bleibt. Vorhandene Worktrees und
unversionierte Dateien nicht entfernen; bei Bedarf einen neuen Checkout nutzen.
Die vollständige Historie beider ursprünglicher Mergecommits muss vorhanden sein.

Auf **demselben Manjaro-Rechner wie beide Originalserien**, im sauberen Checkout:

```bash
git fetch origin codex/seed-driver-crosscheck
git switch --detach origin/codex/seed-driver-crosscheck
git status --short
git cat-file -e be6fc1bd2339df5b429684dfce8e992073d88506
git cat-file -e 5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4
git cat-file -e bc4025d13b4954dee779341026d282430521686a
env -u VIRTUAL_ENV uv sync --locked --dev --python 3.12.14
```

Beide vollständigen Originalarchive werden benötigt, hier unter `results/`.
Abweichende Aufbewahrungsorte nur in den beiden Archivargumenten anpassen.
Die SHA-256-Werte sind im Plan und im Programm gebunden. Ein nachträglich neu
gepacktes Archiv ist kein Ersatz für das ursprüngliche Paket.

```bash
(
  set -e
  test -z "$(git status --porcelain=v1 --untracked-files=all)"
  test ! -e results/seed-driver-crosscheck-manjaro-001
  test ! -e results/seed-driver-crosscheck-manjaro-001.tar.gz
  export OPENBLAS_CORETYPE=Haswell
  export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
  export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
  run_status=0
  env -u VIRTUAL_ENV uv run --locked --python 3.12.14 \
    python scripts/run_seed_driver_crosscheck.py \
    --outer-archive results/outer-ladder-manjaro-001.tar.gz \
    --transfer-archive results/transfer-manjaro-001.tar.gz \
    --output results/seed-driver-crosscheck-manjaro-001 || run_status=$?
  if test -d results/seed-driver-crosscheck-manjaro-001; then
    tar -C results -czf results/seed-driver-crosscheck-manjaro-001.tar.gz \
      seed-driver-crosscheck-manjaro-001
    sha256sum results/seed-driver-crosscheck-manjaro-001.tar.gz
  fi
  exit "$run_status"
)
```

Der Aufruf bereitet den gepinnten Julia-Interpreter selbst vor. Die Programme
laufen aus isolierten, sauberen detached Worktrees der historischen Commits;
Archivprogramme und gespeicherte Suchzustände werden nicht ausgeführt.
Nur der gemeinsame Einzelzelladapter wählt den festen Seed und orchestriert
Vorprüfung, Worker und unabhängige Elternnachrechnung. Beide nativen Vorprüfungen
und beide Originalnachweise müssen vor der ersten frischen Suche bestehen.

Python-/Paketversionen, Plattformmerkmale, Haswell, tatsächliche Bibliotheksversionen
und Threadlimits müssen zu beiden Originalen passen. Bibliothekspfade und
Snapshotnamen werden aus dem Umgebungsvergleich entfernt; ihre wissenschaftlich
relevanten Merkmale bleiben erhalten. Plattformmetadaten beweisen keine
Hardwareidentität. Bei Abweichungen wird vor der Suche abgebrochen;
keine Umgebungsprüfung abschalten und keinen Ersatzlauf starten.

Grenzen: **900 Sekunden pro Suchworker, 3.600 Sekunden insgesamt**, einschließlich
Vorbereitung, Referenzprüfung, Elternarbeit und Finalisierung. Fehler und
Unterbrechungen erhalten Teilstände mit `outcome=not_assessed`. Nach einem
Abbruch vorhandene Ausgaben archivieren und prüfen; keine automatische Fortsetzung.
Nur selbst angelegte, weiterhin saubere Hilfsworktrees werden ohne Force entfernt.

## Ergebnis lesen

`crosscheck_report.json` und `crosscheck_summary.md` nennen je Richtung die
Gleichheit der ganzen Front, effektiver Pythonparameter, nativer Optionen und
Fit-Callbackzahl. Die Frontsignaturen in `outer-reference.json`,
`transfer-reference.json` und `cell-*/verified.json` enthalten alle Originalbäume,
Konstantenbits, Komplexitäten, Verlustbits, Vorhersage-/Residualfingerprints,
Reihenfolge, Auswahlindex und RNG-Seeds. Originaldateien und sämtliche
Worker-/Elternnachweise bleiben im Paket. Laufzeiten und Kurven-/Struktur-/
Parametermarker stehen separat. `crosscheck_checksums.json` bindet das
vollständige erfolgreich abgeschlossene Paket.

- `both_crossovers_reproduced`: Beide ganzen Fronten und Suchmerkmale gleichen
  den historischen Referenzen. Das stützt Seedabhängigkeit für diese zwei Fälle
  und spricht gegen einen Unterschied dieser Workerpfade als Erklärung.
- `valid_crossovers_differ`: Mindestens ein geprüftes Suchmerkmal unterscheidet
  sich. Die gespeicherten Merkmale zeigen, wo die technische Ursachenanalyse
  ansetzen kann, auch wenn der Kurvenmarker gleich geblieben ist.
- `not_assessed`: Lauf oder Nachweis unvollständig; keine Ursachenzuordnung.

Die gemeinsame Einzelzellsteuerung ersetzt die vollständigen historischen
Serienschleifen. Der Vergleich untersucht deshalb die beiden Workerpfade unter
diesem Adapter. Zwei gezielt gewählte Fälle liefern keine Erfolgswahrscheinlichkeit,
keine Garantie einer Verbesserung und keine Begründung für ein bestimmtes höheres
Budget. `physical_identification=not_assessed` und der 8·fs-Blindfleck bleiben.
Anschließend wird der nächste Schritt anhand des Befunds begründet; Rauschpipeline,
Pilotdesign und Hauptversuchsplan bleiben vorgemerkt.

## Technische Prüfung

`tests/test_seed_driver_crosscheck.py` prüft Archivstruktur, Datenbits,
Umgebungsvergleich, vollständige Fronten, feste Requests, Vorprüfungsreihenfolge,
Zeitgrenzen, Signale und gesperrte Fehlerberichte ohne wissenschaftliche Suche.
`scripts/check_seed_driver_crosscheck.py` startet genau zwei historische
Miniworker auf eigenen acht Punkten t=j/8, y=1+t, Seed 73, zwei äußere
Iterationen. Die vollständigen Fronten, Optionen, Callbackzahlen und Marker
müssen übereinstimmen. Der Schritt gehört zur vollständigen technischen CI.
Der eingefrorene Plan ist ausdrücklich als Laufzeitdokument erfasst.

Lokal bestanden 179 gezielte Pythonfälle einschließlich der bisherigen
Transfer-Treibertests sowie beide historischen Miniworker mit identischen
Fronten, Optionen, Callbackzahlen und Markern. Die neue Referenzprüfung hat
alle elf Kandidaten der festgelegten Transferzelle unverändert bestätigt.
Der vollständige lokale/CI-Prüfnachweis wird im Implementierungs-PR festgehalten.
Das übermittelte Originalarchiv der äußeren Staffel liegt dieser Cloudinstanz
nicht vor; seine Originalprüfung und die wissenschaftliche Gegenüberstellung
bleiben Teil des Manjaro-Aufrufs. Das Transferoriginal wurde separat lesend
gegen den historischen Elternprüfpfad geprüft.
