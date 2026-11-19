# Laufweg: Hintergrunddauer und Messraster

Stand 19.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md).
Der [verbindliche Versuchsplan](noise_followup_plan.md) ist vor neuen
Studieneingaben an Commit `a37bf90fe439619fd263d6c06d868c6ff4ea00e8` und
SHA-256 `f762ec7f4311ceea46bd736f3838c111072939d5d853552e3bec537ad86b2773`
gebunden. Die ursprüngliche Hintergrundserie und ihre Archive bleiben erhalten.
Aktuelle Abnahmebelege stehen im
[Fortsetzungsstand](representation_implementation_status.md).
Die folgenden Befehle sind Ausführungsanleitungen, keine bereits erfolgten
wissenschaftlichen Läufe.

## Umfang und Reihenfolge

Die gemeinsame Folge arbeitet ohne interaktive Methodenwahl:

1. Sechs technische N128-Worker mit je zehn Iterationen, lesende Nachrechnung
   und getrennte technische Plots.
2. Eigene Schätzer-Vorprüfung mit acht AR(1)- und vier weißen Fällen,
   64/4096 s und zwei festgelegten Schätzverfahren; keine SR-Suche.
3. Sämtliche 26 wissenschaftlichen Fälle, beide Messraster, Seeds und Matrizen
   vor der ersten wissenschaftlichen Suche speichern und prüfen.
4. Block A `duration`: 416 Worker, Verifikation, Plots und eigenes Archiv.
5. Block B `sampling`: 208 neue Worker plus 52 vorher gebundene O/K-Kontrollpakete
   aus A, Verifikation, Plots und eigenes Archiv.

Insgesamt entstehen 156 neue wissenschaftliche Viererpakete mit 624 Workern.
Die 52 Kontrollreferenzen sind keine zusätzlichen Suchen oder unabhängigen Fälle.
Der Laufweg verwendet keine historischen Ergebnisse als neue Kontrollen.
Die Dauerarme behalten den vollen Matrixschätzer; die Welch-Diagnose wählt
keinen anderen SR-Schätzer. Erfolgs- und Stoppregeln stehen ausschließlich
im eingefrorenen Plan.

Die Projektion aus historischen Suchkosten beträgt ungefähr 57 Stunden.
Vorbereitung, lange Rauschdaten, technische Prüfungen, Verifikation und
Archivierung sind darin nicht gemessen. Der 23.11. morgens ist ein weiches
Planungsziel. Die festen Sicherheitsfristen gelten weiterhin.

## Fester Ausführungscheckout

Erst den durch Review und vollständige Ready-CI geprüften Implementierungsstand
verwenden. Aus dem bestehenden Repository einen neuen Worktree erstellen;
der ausgegebene vollständige Commit muss zum geprüften PR-Stand passen.
Ein vorhandener Ausführungsordner wird nicht ersetzt.

```bash
bash <<'BASH'
set -euo pipefail
git fetch origin codex/noise-duration-sampling-study
task_commit=$(git rev-parse 'origin/codex/noise-duration-sampling-study^{commit}')
git worktree add --detach ../ringdown-noise-followup-run "$task_commit"
cd ../ringdown-noise-followup-run
test "$(git rev-parse HEAD)" = "$task_commit"
test -z "$(git status --porcelain)"
unset VIRTUAL_ENV
uv sync --locked --dev --python 3.12.14
git rev-parse HEAD
BASH
```

Alle folgenden Befehle im neuen Verzeichnis `ringdown-noise-followup-run`
ausführen. Während des gesamten Versuchs keine Commits wechseln, kein
`git pull` und kein erneutes `uv sync`. `--no-sync` erhält die vorbereitete
Umgebung. Vorprüfung, Inputs und Suchpakete müssen denselben sauberen
Ausführungsstand und dieselbe numerische Umgebung binden.
Ein frischer Checkout enthält nach früheren Squash-Merges nicht automatisch
alle eingefrorenen Plancommits. Deshalb gehört der historische Fetch im nächsten
Block zur lokalen Testvorbereitung.

## Tests und technischer Vorlauf

Die vollständige Python-Suite sowie Format- und Dokumentationsprüfungen:
Der erste Schritt lädt die registrierten historischen PR-Refs über den bereits
eingerichteten `origin`-Zugang (Git-Credential-Helper oder SSH). Er benötigt keine
zusätzliche Tokenvariable. Geprüft werden die Commit-Abstammung, sämtliche
Dateihashes aus [ci_historical_refs.json](../scripts/ci_historical_refs.json)
und das unveränderte `HEAD`, entsprechend der historischen Vorbereitung der CI.
Ein fehlender oder abweichender historischer Nachweis stoppt vor den Tests.

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
uv run --locked --no-sync python - <<'PY'
import hashlib
import json
import subprocess
from pathlib import Path

root = Path.cwd()
bindings = json.loads((root / 'scripts/ci_historical_refs.json').read_text())

def git(*args):
    result = subprocess.run(
        ['git', *args], cwd=root, capture_output=True, timeout=180, check=False
    )
    if result.returncode:
        raise SystemExit(f'Historical Git {args[0]} failed (exit {result.returncode}).')
    return result.stdout

before = git('rev-parse', 'HEAD')
refs = sorted({item['durable_remote_ref'] for item in bindings} - {'refs/heads/main'})
targets = {ref: ref.replace('refs/pull/', 'refs/ci-history/') for ref in refs}
git(
    'fetch', '--no-tags', '--no-recurse-submodules', 'origin',
    *(f'{ref}:{targets[ref]}' for ref in refs),
)
for item in bindings:
    commit = item['required_commit']
    git('cat-file', '-e', f'{commit}^{{commit}}')
    ancestor = targets.get(item['durable_remote_ref'], before.decode().strip())
    git('merge-base', '--is-ancestor', commit, ancestor)
    for path, expected in item['files_sha256'].items():
        if hashlib.sha256(git('show', f'{commit}:{path}')).hexdigest() != expected:
            raise SystemExit(f'Historical file mismatch: {commit}:{path}.')
if git('rev-parse', 'HEAD') != before:
    raise SystemExit('Historical preparation changed HEAD.')
print(f'Historical references verified: {len(bindings)} commits; HEAD unchanged.')
PY
uv run --locked --no-sync python scripts/check_ci.py docs
uv run --locked --no-sync ruff check .
uv run --locked --no-sync ruff format --check .
uv run --locked --no-sync pytest -q
BASH
```

Die gesamte native Regressionssuite wird im bestehenden Workflow
`Technical checks` ausgeführt; ihr vollständiger Befehlssatz steht in
[technical-checks.yml](../.github/workflows/technical-checks.yml).
Ein grüner Python-Lauf allein ersetzt diesen Nachweis nicht. Optional mit
bereits eingerichteter GitHub-CLI den vollständigen Workflow auf dem
unveränderten Branchstand auslösen:

```bash
gh workflow run technical-checks.yml --ref codex/noise-duration-sampling-study
gh run list --workflow technical-checks.yml --branch codex/noise-duration-sampling-study --limit 5
```

Die angezeigte Ausführungs-ID anschließend mit `gh run watch ID --exit-status`
beobachten und den getesteten Commit abgleichen. Dies ist keine zusätzliche
Pflichtwiederholung einer bereits vollständig bestandenen unveränderten CI.

Der neue lokale technische Vorlauf lässt sich getrennt ausführen:

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
uv run --locked --no-sync python scripts/check_noise_followup.py \
  --output results/noise-followup-preflight-manjaro-001
uv run --locked --no-sync python scripts/check_noise_followup.py \
  --verify results/noise-followup-preflight-manjaro-001
BASH
```

Sechs kurze erfolgreiche Worker sind ein Funktionsnachweis, keine
wissenschaftliche Erfolgsschwelle oder Laufzeitgarantie. Der gemeinsame
Startblock unten legt einen eigenen vollständigen Vorlauf unter seiner
neuen Lauf-ID an; die getrennten Befehle sind eine alternative technische
Prüfung und werden nicht zusätzlich vor jedem Gesamtlauf verlangt.

## Gemeinsamer unbeaufsichtigter Start

Netzteil anschließen und den Laptop mit offenem Deckel stehen lassen.
Das Skript erwirbt vor Beginn eine Sperre für
`sleep:idle:handle-lid-switch`. Scheitert diese, startet keine ungeschützte
Ersatzvariante. Erzwungener Suspend oder Stromverlust bleiben möglich;
die Uhren- und Integritätsprüfungen bleiben unverändert aktiv.
Das Terminal offen lassen. Die Sperre endet mit dem Skript.

```bash
unset VIRTUAL_ENV
bash scripts/run_noise_followup_manjaro.sh results/noise-followup-manjaro-001
```

Das Skript stoppt bei jedem Fehler, hält bestehende Dateien und startet
keine Ersatzworker. Eine bereits vorhandene Lauf-ID wird abgewiesen.
Alle Schritte werden mit Zeitstempel angezeigt. Der gesamte Ablauf steht
in [run_noise_followup_manjaro.sh](../scripts/run_noise_followup_manjaro.sh).
Er führt zuerst beide Vorprüfungen aus, bindet die gemeinsamen Inputs und
archiviert sie einmal. Danach beendet, verifiziert und archiviert er A,
bevor B beginnt. Originalformeln und sämtliche Punktdaten werden mitexportiert.

Rohtraining benötigt allein 128 MiB je langer Reihe. Wissenschaftliche
Inputs umfassen 26 solche Reihen, die separate Diagnose weitere zwölf und
der technische Vorlauf eine. Archive und Suchartefakte benötigen zusätzlichen
Platz. Fallweise Verarbeitung begrenzt den RAM, ersetzt aber keinen freien
Plattenplatz. Keine Originaleingaben zur Platzersparnis nachträglich löschen.

## Fortschritt in einem zweiten Terminal

In dasselbe Ausführungsverzeichnis wechseln und den folgenden rein lesenden
Monitor starten:

```bash
unset VIRTUAL_ENV
uv run --locked --no-sync python scripts/watch_noise_followup.py \
  --root results/noise-followup-manjaro-001
```

Die Anzeige aktualisiert alle zehn Sekunden Block, Fälle, Bedingungen,
Mitgliedsstatus, gespeicherte Fehler und Zeitbasis. Gemessene Workerzeit wird
getrennt von einer UTC-Differenz seit gespeichertem Start ausgewiesen.
Gespeicherte Aufrufzeiten und CPU-Kosten erscheinen separat mit ihrer
Vollständigkeit. Sie enthalten die Workerzeiten bereits und werden nicht zu
diesen addiert; ein noch laufender Aufruf besitzt noch keinen fertigen Kostenbeleg.
Gespeicherte Zustände können nach einem Abbruch stehen bleiben; weder
Prozessabschluss noch ein Statusbild ist ein wissenschaftlicher Erfolgsnachweis.
Strg+C beendet nur den Monitor. `--once` druckt ein einzelnes Bild, `--all`
auch noch nicht gestartete Fallzeilen und `--json` liefert maschinenlesbare
gespeicherte Zustände. Die Anzeige schreibt keine Dateien.

## Bewusste Pause und begrenzte Fortsetzung

Für einen bewusst aufgeteilten Lauf die Einzel-CLI verwenden. Nach vorhandenen
Vorprüfungen und wissenschaftlicher Vorbereitung kann A beispielsweise nach
zwei **neuen vollständig abgeschlossenen Fällen** anhalten:

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
systemd-inhibit --what=sleep:idle:handle-lid-switch --mode=block \
  --who=ringdown-sr --why='Folgestudie bis zur vollstaendigen Fallgrenze' \
  --no-ask-password uv run --locked --no-sync python scripts/run_noise_followup.py run \
  --block duration --inputs results/noise-followup-manjaro-001/inputs \
  --technical results/noise-followup-manjaro-001/technical \
  --estimators results/noise-followup-manjaro-001/estimators \
  --output results/noise-followup-manjaro-001/duration --max-cases 2
BASH
```

Derselbe Befehl ohne `--max-cases` prüft die vorhandenen vollständigen Fälle
und bearbeitet die noch geplanten Fälle. Alle Fortsetzungsaufrufe und Kosten
bleiben erhalten. Die Schlafsperre im Beispiel schützt auch diese getrennten
Aufrufe; die Sperre des Gesamtskripts gilt nur, solange dieses läuft.

**Ein vorhandener unvollständiger Fall blockiert.** Es gibt keine Fortsetzung
eines abgebrochenen Julia-Workers und kein stilles Löschen, Überschreiben oder
Ersetzen durch neue Seeds. Nicht den gesamten Startblock erneut ausführen:
er verweigert die vorhandene Lauf-ID. Bei einem Fehler zunächst Status,
`metadata.json`, `worker.log`, Aufrufkosten und Originaldateien erhalten.
Ein abgebrochener Fall benötigt eine getrennte Einordnung.

## Lesende Prüfung und Export ohne neue Suche

Beispiel für den vollständig abgeschlossenen Dauerblock; jeder Exportordner
muss neu sein:

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export MPLBACKEND=Agg
task_root=results/noise-followup-manjaro-001
uv run --locked --no-sync python scripts/run_noise_followup.py verify \
  --block duration --inputs "$task_root/inputs" \
  --technical "$task_root/technical" --estimators "$task_root/estimators" \
  --output "$task_root/duration" --export "$task_root/verification-duration-extra"
uv run --locked --no-sync python scripts/run_noise_followup.py plots \
  --block duration --inputs "$task_root/inputs" \
  --technical "$task_root/technical" --estimators "$task_root/estimators" \
  --output "$task_root/duration" --export "$task_root/plots-duration-extra"
BASH
```

Für B `--block sampling`, `--output .../sampling` und zusätzlich
`--duration .../duration` verwenden. Beide Gatepfade bleiben erforderlich.
`verify-inputs`, `estimator-verify`, `verify`, `plots`, `verify-plots` und
`technical-plots` starten keine neuen Fits oder SR-Suchen. Neue technische
Worker startet nur `check_noise_followup.py --output`, wissenschaftliche
Worker nur `run_noise_followup.py run`.

## Archive und Wiederherstellung

Unter `results/noise-followup-manjaro-001/archives/` entstehen drei Teile:

- `noise-followup-manjaro-001-shared.tar.gz`: gemeinsame wissenschaftliche
  Inputs, technische und Schätzervorprüfung sowie technische Plots und Kosten.
- `noise-followup-manjaro-001-duration.tar.gz`: A mit Verifikation, Plots und
  SHA-256-Bindung des gemeinsamen Archivs.
- `noise-followup-manjaro-001-sampling.tar.gz`: B mit Verifikation, Plots sowie
  SHA-256-Bindungen der gemeinsamen Eingaben und des Dauerarchivs.

Jeder Teil besitzt eine `.sha256`-Datei und einen internen
`ARCHIVE-<Teil>.json`-Beleg mit allen Nutzdateihashes. Erstellung liest das
Archiv vollständig zurück und prüft sämtliche Nutzdateibytes; die Quellen
bleiben unverändert. Diese Integritätsprüfung ersetzt keine wissenschaftliche
Verifikation. Die drei Teile sind zusammen der vollständige wissenschaftliche
Bestand; B allein enthält seine großen Eingaben und referenzierten Kontrollen
absichtlich nicht nochmals.

Eine einzelne fehlende Archivstufe lässt sich nach den zugehörigen erfolgreichen
Prüfungen und Exporten separat erzeugen. Beispiel für A; die gemeinsame Stufe
`shared` muss bereits vorhanden sein. Für die anderen Stufen `task_part` auf
`shared` beziehungsweise `sampling` setzen. Die Standardordner des Gesamtskripts
sind erforderlich; ein bestehender Archivteil wird niemals überschrieben.

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
task_root=results/noise-followup-manjaro-001
task_part=duration
uv run --locked --no-sync python scripts/run_noise_followup.py archive \
  --root "$task_root" --part "$task_part"
(
  cd -- "$task_root/archives"
  sha256sum -c -- "noise-followup-manjaro-001-$task_part.tar.gz.sha256"
)
BASH
```

Nach `sha256sum -c` alle drei Archive in denselben **neuen leeren** Zielordner
entpacken. Sie erzeugen denselben Lauf-Elternordner mit getrennten Unterordnern.
Anschließend mit dem unveränderten Ausführungscheckout erneut lesend prüfen.
Originalarchive und eine unabhängige hashgeprüfte Zweitkopie gemäß
[Archivregel](results_archiving.md) aufbewahren. Für erneute Exporte zusätzliche
Archive mit eigener Identität erstellen, keine bereits gebundenen Teile ersetzen.
