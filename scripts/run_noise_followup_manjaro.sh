#!/usr/bin/env bash
# Run one fresh, fully ordered local study while holding a sleep inhibitor.
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
  printf 'Aufruf: bash scripts/run_noise_followup_manjaro.sh results/NEUE-LAUF-ID\n' >&2
  exit 2
fi

task_root=$1
task_commit=$(git rev-parse HEAD)
test -z "$(git status --porcelain)"
test -f scripts/run_noise_followup.py
test -f scripts/check_noise_followup.py
test -f .venv/bin/python
command -v systemd-inhibit >/dev/null
command -v uv >/dev/null

systemd-inhibit --what=sleep:idle:handle-lid-switch --mode=block \
  --who=ringdown-sr --why='Rauschdauer- und Rasterstudie ohne Suspend' \
  --no-ask-password bash -s -- "$task_root" "$task_commit" <<'RUN'
set -Eeuo pipefail
task_root=$1
task_commit=$2
task_phase='Vorbereitung'
trap 'printf "Abbruch bei %s in Zeile %s. Dateien erhalten; kein automatischer Neustart.\n" "$task_phase" "$LINENO" >&2' ERR
test "$(git rev-parse HEAD)" = "$task_commit"
test -z "$(git status --porcelain)"
if [[ -e "$task_root" || -L "$task_root" ]]; then
  printf 'Laufordner bereits vorhanden; nichts ueberschrieben: %s\n' "$task_root" >&2
  exit 1
fi
unset VIRTUAL_ENV
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
value = {
    "phase": sys.argv[2],
    "status": "completed" if sys.argv[2] == "Abgeschlossen" else sys.argv[4],
    "software_commit": sys.argv[3],
    "updated_at_utc": datetime.now(timezone.utc).isoformat(),
}
temporary = root / "workflow_state.json.tmp"
with temporary.open("w", encoding="utf-8") as stream:
    json.dump(value, stream, indent=2)
    stream.write("\n")
os.replace(temporary, root / "workflow_state.json")
PY
}

failed() {
  task_exit=$1
  task_line=$2
  trap - ERR
  set +e
  printf 'Abbruch bei %s in Zeile %s. Dateien erhalten; kein automatischer Neustart.\n' "$task_phase" "$task_line" >&2
  stage "$task_phase" aborted
  exit "$task_exit"
}
trap 'failed "$?" "$LINENO"' ERR

stage 'Technischer Vorlauf: sechs N128-Zehnerworker'
uv run --locked --no-sync python scripts/check_noise_followup.py \
  --output "$task_root/technical"
uv run --locked --no-sync python scripts/check_noise_followup.py \
  --verify "$task_root/technical"
uv run --locked --no-sync python scripts/run_noise_followup.py technical-plots \
  --technical "$task_root/technical" --export "$task_root/technical-plots"

stage 'Getrennte Schaetzer-Vorpruefung ohne SR-Suchen'
uv run --locked --no-sync python scripts/run_noise_followup.py estimator-check \
  --output "$task_root/estimators"
uv run --locked --no-sync python scripts/run_noise_followup.py estimator-verify \
  --output "$task_root/estimators"

stage 'Alle wissenschaftlichen Eingaben vor der Suche binden'
uv run --locked --no-sync python scripts/run_noise_followup.py prepare \
  --output "$task_root/inputs"
uv run --locked --no-sync python scripts/run_noise_followup.py verify-inputs \
  --inputs "$task_root/inputs"
stage 'Gemeinsame Eingaben und Vorpruefungen einmal archivieren'
uv run --locked --no-sync python scripts/run_noise_followup.py archive \
  --root "$task_root" --part shared

stage 'Block A: Hintergrunddauer, 416 geplante Worker'
uv run --locked --no-sync python scripts/run_noise_followup.py run \
  --block duration --inputs "$task_root/inputs" \
  --technical "$task_root/technical" --estimators "$task_root/estimators" \
  --output "$task_root/duration"
stage 'Block A: vollstaendig lesend verifizieren'
uv run --locked --no-sync python scripts/run_noise_followup.py verify \
  --block duration --inputs "$task_root/inputs" \
  --technical "$task_root/technical" --estimators "$task_root/estimators" \
  --output "$task_root/duration" --export "$task_root/verification-duration"
stage 'Block A: Originalformeln, Punktdaten und Plots'
uv run --locked --no-sync python scripts/run_noise_followup.py plots \
  --block duration --inputs "$task_root/inputs" \
  --technical "$task_root/technical" --estimators "$task_root/estimators" \
  --output "$task_root/duration" --export "$task_root/plots-duration"
uv run --locked --no-sync python scripts/run_noise_followup.py verify-plots \
  --export "$task_root/plots-duration"
stage 'Block A: eigenes Archiv mit Bindung an gemeinsame Eingaben'
uv run --locked --no-sync python scripts/run_noise_followup.py archive \
  --root "$task_root" --part duration

stage 'Block B: Messraster, 208 neue Worker und gemeinsame Kontrollen'
uv run --locked --no-sync python scripts/run_noise_followup.py run \
  --block sampling --inputs "$task_root/inputs" \
  --technical "$task_root/technical" --estimators "$task_root/estimators" \
  --duration "$task_root/duration" --output "$task_root/sampling"
stage 'Block B: vollstaendig lesend verifizieren'
uv run --locked --no-sync python scripts/run_noise_followup.py verify \
  --block sampling --inputs "$task_root/inputs" \
  --technical "$task_root/technical" --estimators "$task_root/estimators" \
  --duration "$task_root/duration" --output "$task_root/sampling" \
  --export "$task_root/verification-sampling"
stage 'Block B: Originalformeln, Punktdaten und Plots'
uv run --locked --no-sync python scripts/run_noise_followup.py plots \
  --block sampling --inputs "$task_root/inputs" \
  --technical "$task_root/technical" --estimators "$task_root/estimators" \
  --duration "$task_root/duration" --output "$task_root/sampling" \
  --export "$task_root/plots-sampling"
uv run --locked --no-sync python scripts/run_noise_followup.py verify-plots \
  --export "$task_root/plots-sampling"
stage 'Block B: eigenes Archiv mit gebundenen Kontrollreferenzen'
uv run --locked --no-sync python scripts/run_noise_followup.py archive \
  --root "$task_root" --part sampling

stage 'Alle drei Archivpruefsummen kontrollieren'
(
  cd -- "$task_root/archives"
  sha256sum -c -- ./*.tar.gz.sha256
)
test "$(git rev-parse HEAD)" = "$task_commit"
test -z "$(git status --porcelain)"
stage 'Abgeschlossen'
printf '\nBeide Bloecke verifiziert; Plots, Formeln, Punktdaten und drei Archive vorhanden.\n'
printf 'Archive: %s/archives\n' "$task_root"
RUN
