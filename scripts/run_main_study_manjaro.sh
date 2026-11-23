#!/usr/bin/env bash
# Execute one fresh two-section study with a sleep inhibitor and one CPU.
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
  printf 'Aufruf: bash scripts/run_main_study_manjaro.sh results/NEUE-LAUF-ID\n' >&2
  exit 2
fi

task_root=$1
task_commit=$(git rev-parse HEAD)
test -z "$(git status --porcelain)"
test -f scripts/check_main_study.py
test -f scripts/run_main_study.py
test -f .venv/bin/python
command -v systemd-inhibit >/dev/null
command -v taskset >/dev/null
command -v uv >/dev/null
unset VIRTUAL_ENV
task_cpu=$(uv run --locked --no-sync python -c 'import os; print(min(os.sched_getaffinity(0)))')

systemd-inhibit --what=sleep:idle:handle-lid-switch --mode=block \
  --who=ringdown-sr --why='Hauptserie ohne Suspend und Uhrsprung' \
  --no-ask-password taskset -c "$task_cpu" bash -s -- "$task_root" "$task_commit" <<'RUN'
set -Eeuo pipefail
task_root=$1
task_commit=$2
task_phase='Vorbereitung'
test "$(git rev-parse HEAD)" = "$task_commit"
test -z "$(git status --porcelain)"
if [[ -e "$task_root" || -L "$task_root" ]]; then
  printf 'Laufordner bereits vorhanden; nichts ueberschrieben: %s\n' "$task_root" >&2
  exit 1
fi
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export MPLBACKEND=Agg PYTHONUNBUFFERED=1
mkdir -p -- "$task_root"

stage() {
  task_phase=$1
  task_status=${2:-running}
  printf '\n[%s] %s\n' "$(date '+%d.%m.%Y %H:%M:%S %Z')" "$task_phase"
  uv run --locked --no-sync python - "$task_root" "$task_phase" "$task_commit" "$task_status" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
root = Path(sys.argv[1])
record = {
    "phase": sys.argv[2],
    "status": sys.argv[4],
    "software_commit": sys.argv[3],
    "updated_at_utc": datetime.now(timezone.utc).isoformat(),
}
temporary = root / "workflow_state.json.tmp"
with temporary.open("w", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
os.replace(temporary, root / "workflow_state.json")
PY
}

failed() {
  task_exit=$1
  task_line=$2
  trap - ERR INT TERM
  set +e
  printf 'Abbruch bei %s in Zeile %s. Dateien erhalten; kein automatischer Neustart.\n' "$task_phase" "$task_line" >&2
  stage "$task_phase" aborted
  exit "$task_exit"
}
trap 'failed "$?" "$LINENO"' ERR
trap 'failed 130 "$LINENO"' INT
trap 'failed 143 "$LINENO"' TERM

stage 'Technischer Vorlauf: acht N103-Zehnerworker'
uv run --locked --no-sync python scripts/check_main_study.py --output "$task_root/technical"
uv run --locked --no-sync python scripts/check_main_study.py --verify "$task_root/technical"
uv run --locked --no-sync python scripts/run_main_study.py technical-plots \
  --technical "$task_root/technical" --export "$task_root/technical-plots"
uv run --locked --no-sync python scripts/run_main_study.py verify-plots \
  --export "$task_root/technical-plots"

stage 'Alle 80 wissenschaftlichen Eingaben vor der ersten Suche binden'
uv run --locked --no-sync python scripts/run_main_study.py prepare --output "$task_root/inputs"
uv run --locked --no-sync python scripts/run_main_study.py verify-inputs --inputs "$task_root/inputs"
stage 'Gemeinsame Eingaben und technische Belege archivieren'
uv run --locked --no-sync python scripts/run_main_study.py archive --root "$task_root" --part shared

stage 'Signal 200 Hz / 4 ms: 40 Faelle, 640 geplante Worker'
uv run --locked --no-sync python scripts/run_main_study.py run \
  --inputs "$task_root/inputs" --technical "$task_root/technical" \
  --signal signal_200_4ms --output "$task_root/signal_200_4ms"
stage 'Signal 200: getrennte lesende Verifikation'
uv run --locked --no-sync python scripts/run_main_study.py verify \
  --inputs "$task_root/inputs" --technical "$task_root/technical" \
  --signal signal_200_4ms --output "$task_root/signal_200_4ms" --export "$task_root/verification-200"
stage 'Signal 200: Originalformeln, Plots und vollstaendige Punktdaten'
uv run --locked --no-sync python scripts/run_main_study.py plots \
  --inputs "$task_root/inputs" --technical "$task_root/technical" \
  --series-200 "$task_root/signal_200_4ms" --export "$task_root/plots-200"
uv run --locked --no-sync python scripts/run_main_study.py verify-plots --export "$task_root/plots-200"
uv run --locked --no-sync python scripts/run_main_study.py archive --root "$task_root" --part signal_200_4ms

stage 'Signal 250 Hz / 6 ms: 40 Faelle, weitere 640 Worker'
uv run --locked --no-sync python scripts/run_main_study.py run \
  --inputs "$task_root/inputs" --technical "$task_root/technical" \
  --signal signal_250_6ms --previous "$task_root/signal_200_4ms" --output "$task_root/signal_250_6ms"
stage 'Signal 250: getrennte lesende Verifikation'
uv run --locked --no-sync python scripts/run_main_study.py verify \
  --inputs "$task_root/inputs" --technical "$task_root/technical" \
  --signal signal_250_6ms --previous "$task_root/signal_200_4ms" \
  --output "$task_root/signal_250_6ms" --export "$task_root/verification-250"
stage 'Gesamte Hauptserie: Originalformeln, Plots und vollstaendige Punktdaten'
uv run --locked --no-sync python scripts/run_main_study.py plots \
  --inputs "$task_root/inputs" --technical "$task_root/technical" \
  --series-200 "$task_root/signal_200_4ms" --series-250 "$task_root/signal_250_6ms" \
  --export "$task_root/plots-all"
uv run --locked --no-sync python scripts/run_main_study.py verify-plots --export "$task_root/plots-all"
uv run --locked --no-sync python scripts/run_main_study.py archive --root "$task_root" --part signal_250_6ms
test "$(git rev-parse HEAD)" = "$task_commit"
test -z "$(git status --porcelain)"
stage 'Abgeschlossen: Hauptserie, lesende Verifikation, Plots und Archivbytes geprueft' completed
RUN
