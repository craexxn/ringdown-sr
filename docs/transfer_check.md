# Bedienung: begrenzter Signaltransfer bei 500/300/5

**Stand 04.11.2026:** Vorbereitung des angenommenen
[Transferchecks](transfer_check_plan.md). Keine wissenschaftliche Zelle
auf den neuen Daten ausgeführt. Vor dem einmaligen Manjaro-Lauf müssen
technische Prüfung und manueller Merge abgeschlossen sein.
[PR #65](https://github.com/craexxn/ringdown-sr/pull/65) enthält den Prüfstand
und den konkreten Checkoutblock mit geprüftem Head und Dateibaumvergleich.

## Umfang und Daten

18 frische Zellen: sechs festgelegte Signale mit drei neuen gepaarten Seeds
20261210–20261212. Frischer bekannter Referenzfall, jeweils eine Änderung
von Frequenz, Abklingzeit, Phase und Amplitude sowie ein gemeinsamer Fall.
Überall 500 äußere Iterationen, lokal 300/5, allgemeine Grammatik und
`should_simplify=false`. Keine zusätzliche Budget- oder Grammatikstaffel.

Abbruchgrenzen: **900 Sekunden je Worker, 7.200 Sekunden insgesamt**,
einschließlich Vorprüfung, Elternnachrechnung und Veröffentlichung.
Keine Laufzeitprognose, automatische Fortsetzung oder Ersatzläufe.
Bei einer unvollständigen Serie bleiben sämtliche Aggregate gesperrt.

Die [Eingabedatei](../data/transfer_check_inputs.npz) und das
[Manifest](../data/transfer_check_inputs.json) gehören zum Repository.
**Kein früheres Ergebnisarchiv ist als Eingang erforderlich.** Die Laufzeit
verwendet eingefrorene Float64-Bits statt plattformabhängiger Neugenerierung.
Root-Artefakte `training.npz` und `diagnostic.npz` enthalten je eine gemeinsame
Zeitachse und sechs Datenzeilen in der im Manifest festgelegten Reihenfolge.
Jeder Worker erhält nur seine 128 Trainingszeiten und Beobachtungen.
Zwischenpunkte und Referenzparameter bleiben im Eltern-/Diagnosepfad.

Plan und Daten sind seit Commit `446afbfea8958f409693c2253f8d9d4950f24e45`
vor der Implementierung gebunden; Plan-SHA-256:
`f29561b8151a2a4e17cd881a8c4576f406f0efd340309ac54fcbbde2faabb6f3`.
Der Dateihash des NPZ lautet
`e4de71bb6aa5cb5e3afc72914466b997adb2ef6438bbe38d7baa421a85bd2628`.

## Vorbereitung auf Manjaro

Zuerst den im PR angegebenen geprüften Stand nach Merge auschecken.
Historische Plancommits erhalten: den neuen PR-Head und bei fehlender
Historie die Heads von #55, #61 und #63 in lokalen Remote-Referenzen holen.
`git switch --detach` vermeidet einen bereits belegten main-Worktree.
Git-Ausdrücke mit `^{tree}` für Zsh immer zitieren. Unversionierte Dateien
nicht löschen; bei Bedarf einen getrennten sauberen Checkout verwenden.

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
    pytest -q tests/test_transfer_check.py tests/test_transfer_check_driver.py \
    tests/test_duration_verification.py
  printf '%s\n' \
    'e4de71bb6aa5cb5e3afc72914466b997adb2ef6438bbe38d7baa421a85bd2628  data/transfer_check_inputs.npz' \
    '54f7ddb7b524640e20911ae3fe69334d3fd31d25d9c9fab69d132e1ade9d1773  data/transfer_check_inputs.json' \
    | sha256sum --check --strict
)
```

Nach vollständiger technischer CI desselben Dateibaums ist keine zusätzliche
lokale Vollintegration erforderlich. Der Umgebungscheck bestätigt die
technische Funktionsfähigkeit, keine wissenschaftliche Übertragbarkeit.

## Einmalige Serie und Archivsicherung

Nach erfolgreicher Vorbereitung im selben Checkout ausführen. Der Block
bewahrt vorhandene Teilstände auch bei einem Abbruch und gibt den ursprünglichen
Fehlercode zurück. Ausgabeordner und Archiv müssen neu sein.

```bash
(
  set -e
  test -z "$(git status --porcelain=v1 --untracked-files=all)"
  test ! -e results/transfer-manjaro-001
  test ! -e results/transfer-manjaro-001.tar.gz
  export OPENBLAS_CORETYPE=Haswell
  export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
  export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

  run_status=0
  env -u VIRTUAL_ENV uv run --locked --python 3.12.14 \
    python scripts/run_transfer_check.py \
    --output results/transfer-manjaro-001 --label manjaro \
    || run_status=$?

  if test -d results/transfer-manjaro-001; then
    tar -czf results/transfer-manjaro-001.tar.gz \
      -C results transfer-manjaro-001
    sha256sum results/transfer-manjaro-001.tar.gz
  fi
  exit "$run_status"
)
```

## Auswertung und technische Nachweise

`report.json` enthält sämtliche ursprünglichen Fronten und Auswahlen,
Parameterwahrheiten je Signal, Kurvenfehler auf beiden Rastern und
getrennte Struktur-/Parameterstatus. `summary.md` zeigt alle Originalformeln
sowie C/S je Bedingung mit Nenner drei. Fünf Kontraste gegen die frische
Referenz ergeben 15 Seedpaare; keine gemeinsame Erfolgsquote über die sechs
verschiedenen Signale. Gute ungewählte Kandidaten bleiben separat.

Die komplexe Amplitude wird gegen die jeweilige Referenzphase und -amplitude
normalisiert. Struktur-/Aliasgates, Originalauswahl, native und Python-Verluste,
Normalbereich, MPFR-Vorhersagen und unabhängige Elternprüfung sämtlicher
Kandidaten bleiben erhalten. Nicht erkannte Formen sind kein Beweis falscher
physikalischer Struktur. Der unveränderte Erkenner und der 8·fs-Blindfleck
begrenzen den Befund; physikalische Identifikation bleibt `not_assessed`.

Kosten stehen je Zelle und Signal im Bericht. `worker_wall_seconds` umfasst
Armaufruf und Elternverifikation; `status.json.total_wall_seconds` enthält
auch Elternvorbereitung und Ergebnislesen. Fitzeit enthält JIT/Export.
Callbacks sind keine Anzahl eindeutiger Bäume oder lokaler Optimiererschritte.

Die neue technische Integration prüft drei native Seedoptionen, alle 18
festen Suchprofile, bestehende Alias-/Syntaxreferenzen und drei frische
Miniworker. Diese erhalten ausschließlich eigene acht Punkte mit
`y=1+t`, `y=0.4+2t` und erneut `y=1+t`, je zwei äußere Iterationen.
Die wiederholte ursprüngliche Front muss identisch bleiben. Keine der
wissenschaftlichen 500er-Zellen läuft in der Cloud/CI.

Nach Auswertung folgt ein begründeter nächster Pilotschritt. 500/1.000,
300/2, eine Erkennererweiterung und größere Bereinigung sind keine
automatische Anschlussarbeit. Rauschpipeline, abschließendes Pilotdesign
und Hauptversuchsplan bleiben die vorgemerkte Route; die Hauptstudie selbst
gehört nicht zu diesem Auftrag.
