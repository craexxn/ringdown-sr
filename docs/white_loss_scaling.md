# White-Skalierungspilot: Laufweg und Befund

Stand 23.11.2026, Leitfadenphase 7. Der
[Vorabplan](white_loss_scaling_plan.md) ist in Commit
`222b4bc2263e6200bf29b2424c2a5e6bd318bdd2` vor neuen Versuchsbeobachtungen
festgelegt. Branch `codex/white-loss-scaling-pilot` baut auf dem offenen
[Ergebnis-PR #103](https://github.com/craexxn/ringdown-sr/pull/103) auf.
Die Umsetzung ist in Entwicklung; wissenschaftliche Ergebnisse stehen aus.

Die drei getrennten Verlustpfade sind gewöhnliche MSE (O), dieselbe MSE
multipliziert mit 1/sigma² (S) und der diagonale Kovarianzpfad (K).
Ein eigenes Requestformat und eigene Quellenbindungen lassen historische
Suchprofile und Ergebnisse unverändert. Der feste Strukturvergleich prüft
identische Startwerte und Neustartziehungen; freie Suchen behalten 300/5,
Grammatik und bisherige Trainingsverlust-Auswahl.

## Befehle

In einem sauberen Checkout des später dokumentierten Ausführungscommits:

```bash
uv sync --locked --dev
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
taskset -c "$(python -c 'import os; print(min(os.sched_getaffinity(0)))')" \
  uv run --locked python scripts/check_white_scaling.py \
  --output results/white-scaling-technical-001
```

Danach der im Plan begrenzte Entwicklungsversuch. Neue Ausgabeordner verwenden;
vorhandene Läufe werden nicht überschrieben. Ein einzelner logischer CPU-Kern
und begrenzte Julia-/BLAS-Threads gehören zum gebundenen Laufweg.

```bash
taskset -c "$(python -c 'import os; print(min(os.sched_getaffinity(0)))')" \
  uv run --locked python scripts/run_white_scaling.py run \
  results/white-scaling-001
uv run --locked python scripts/run_white_scaling.py verify \
  results/white-scaling-001
uv run --locked python scripts/run_white_scaling.py export \
  results/white-scaling-001 --output results/white-scaling-plots-001
```

Fortschritt in einem zweiten Terminal, rein lesend:

```bash
watch -n 10 'uv run --locked --no-sync python scripts/run_white_scaling.py status results/white-scaling-001'
```

Diese Anzeige zeigt den gespeicherten Stand; Strg+C beendet nur die Anzeige.
Die lesende Verifikation verlangt denselben gebundenen Ausführungsstand.
Umgebungsvorbereitung und technische Checks sind von der wissenschaftlichen
Serienzeit getrennt. Bestehende globale und historische Prüfungen bleiben
zusätzlich Bestandteil der vollständigen Ready-CI.
