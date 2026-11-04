# Bedienung: äußere Suchbudgets bei festem 300/5-Profil

**Status vom 04.11.2026:** Die 20 Manjaro-Zellen sind vollständig ausgeführt
und unabhängig nachgerechnet. [Ergebnis und Grenzen](outer_search_ladder_results_manjaro_001.md)
halten die Nachrechnung aller 164 Originalkandidaten, die fünf Kontraste und
den Aufwand fest.
Die Befehle unten beschreiben den abgeschlossenen Laufweg und geben keine
automatische Wiederholung frei. Der optionale 300/2-Anschluss bleibt separat
festzulegen.

Die [angenommene Methodenfestlegung](outer_search_ladder_plan.md) wurde vor
Implementierung am Commit `e1ea601286042aadcc5b5291ae72d114c7846dbf` eingefroren,
SHA-256 `95aca0069d6b8a6ad0305d5722c558e4bbea1c23e7f3b70630d2eb33e816fa35`.
Grundlage ist der [abgeschlossene lokale Vergleich](local_optimizer_results_manjaro_001.md).

## Umfang und Auswertung

20 frische Manjaro-Zellen: fünf neue gepaarte Seeds 20261201–20261205,
äußere Iterationen 200, 500, 2.000 und 5.000, durchgehend lokale Optimierung
300/5 und unrestricted. Die 200er-Kontrollen sind ebenfalls frisch.
`should_simplify=false`, weitere Optionen, Datenrollen, Originalauswahl und
alle numerischen Nachweise bleiben erhalten. Keine Warmstarts, Nachfits
oder Wiederverwendung historischer Zellen.

Grenzen: **1.800 Sekunden je Worker und 14.400 Sekunden insgesamt**,
einschließlich Vorprüfungen, Elternnachrechnung und Veröffentlichung.
Dies sind Abbruchgrenzen, keine Laufzeitprognose. Fehler sperren sämtliche
Aggregate; Teilstände werden weder automatisch fortgesetzt noch ergänzt.

Kurvenerfolge C und vollständig unterstützte Originalauswahlen S werden
getrennt gezählt. Fünf festgelegte Kontraste liefern 25 Seedpaaraufzeichnungen
mit beiden Erfolgswechseln, Fehlern und Kosten. Ein neu unterstützter Seed
bei gleichzeitigem Verlust eines anderen erhöht S nicht. Es gibt kein
automatisch gewähltes Gewinnerbudget. Ungewählte gute Kandidaten bleiben
separat; Erkennungsgrenzen und der Blindfleck bei 8·fs bleiben dokumentiert.

## Vorbereitung nach technischer Prüfung und Merge

Der Implementierungs-PR enthält den vollständigen Vorbereitungsblock mit
dem abschließend geprüften Head und einem Dateibaumvergleich zu main.
Der Ergebnisnachtrag #62 ist als `6d15014` und Implementierungs-PR #63 nach
vollständiger CI als `5215c5e` übernommen. Historische Plancommits durch
Fetch der PR-Heads erhalten;
fehlende Historie darf nicht durch abgeschaltete Prüfungen ersetzt werden.
`git switch --detach` vermeidet einen bereits belegten main-Worktree.
Git-Ausdrücke mit `^{tree}` für Zsh stets in Anführungszeichen setzen.

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
    pytest -q tests/test_outer_search_ladder.py \
    tests/test_outer_search_ladder_driver.py tests/test_duration_verification.py
  printf '%s\n' \
    'a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db  results/representation-manjaro-001.tar.gz' \
    | sha256sum --check --strict
)
```

Eingang bleibt die ursprüngliche gebundene Datenquelle. Das lokale
Optimiererarchiv enthält Ergebnisse und ersetzt dieses Eingangsarchiv nicht.
Bei unversionierten Dateien nichts löschen; nötigenfalls einen separaten
sauberen Checkout verwenden. Eine weitere lokale Vollintegration ist bei
vollständiger CI desselben Dateibaums nicht erforderlich.

## Einmalige wissenschaftliche Serie

Nach erfüllten Voraussetzungen im selben Checkout ausführen. Verzeichnis
und Archiv müssen neu sein. Der Block sichert auch vorhandene Teilstände
nach Abbruch und gibt den ursprünglichen Fehlercode zurück.

```bash
(
  set -e
  test -z "$(git status --porcelain=v1 --untracked-files=all)"
  test ! -e results/outer-ladder-manjaro-001
  test ! -e results/outer-ladder-manjaro-001.tar.gz
  export OPENBLAS_CORETYPE=Haswell
  export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
  export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

  run_status=0
  env -u VIRTUAL_ENV uv run --locked --python 3.12.14 \
    python scripts/run_outer_search_ladder.py \
    --archive results/representation-manjaro-001.tar.gz \
    --output results/outer-ladder-manjaro-001 --label manjaro \
    || run_status=$?

  if test -d results/outer-ladder-manjaro-001; then
    tar -czf results/outer-ladder-manjaro-001.tar.gz \
      -C results outer-ladder-manjaro-001
    sha256sum results/outer-ladder-manjaro-001.tar.gz
  fi
  exit "$run_status"
)
```

## Nachweise und vorgemerkte Fortsetzung

Eigener versionierter Treiber; bestehende Verlust-, MPFR- und Elternprüfpfade
sowie der native 300/5-Wrapper werden wiederverwendet. Fünf native Seedoptionen
und alle 20 Python-Suchprofile werden vorab absolut geprüft. Drei feste
Einheiten-/Aliasfälle, die allgemeine Syntax sowie falscher Seed und falsches
100/2-Profil werden ohne Suche geprüft. Der tatsächliche Suchaufruf muss das
angeforderte äußere Budget genau einmal ohne Warmstart durchreichen.

Die technische Integration verwendet eigene acht Punkte y=1+t und fünf
frische 300/5-Worker mit äußeren Budgets 2, 3, 4, 5 und erneut 2. Die beiden
Kontrollfronten müssen identisch sein. Keine wissenschaftlichen Zellen in
der Cloud. Quellen, Plan, ursprüngliche Verbrauchsanker und vollständige
Fronten bleiben erhalten; eine positive Veröffentlichung ist widerrufsgesichert.

`worker_wall_seconds` umfasst Armaufruf und Elternverifikation.
`status.json.total_wall_seconds` enthält bereits Elternvorbereitung und
Ergebnislesen. Fitzeit enthält JIT/Export. Kostenverhältnisse sind beschreibend;
Callbacks sind keine eindeutigen Bäume oder lokalen Optimiererschritte.

**Optionaler Anschlussvergleich, noch nicht beauftragt:** Nach Auswertung
gegebenenfalls dieselbe äußere Staffel mit lokal **300/2** wiederholen,
mit denselben Seedkennungen, Daten und Auswahlregeln und frischen Läufen.
Die Vormerkung 300/2 ersetzt die zwischenzeitliche Idee 100/2: So bleibt die
lokale Iterationsgrenze 300 gleich und allein die Zahl zusätzlicher Neustarts
wird verglichen. Die hierfür weiteren 20 Zellen, ihre Ausführungsreihenfolge
und ihr eigenes Zeitbudget sind vorab separat festzulegen. Keine automatische
Anschlussserie; das jetzige Budget gilt ausschließlich für 300/5.

Die Pilotroute nach Abschluss der Budgettests bleibt erhalten: Übertragbarkeit,
Rauschpipeline, kompaktes gebundenes Pilotdesign, Auswertung und Hauptversuchsplan.
Keine Hauptstudie, WSL2-/Parallelisierungsarbeit oder größere Bereinigung in
diesem Schritt. 10.000 Iterationen bleiben eine spätere Option bei positivem
Trend; keine automatische Erweiterung bei ausbleibendem Strukturgewinn.
