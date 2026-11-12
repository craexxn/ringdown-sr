# Laufweg: vier mittlere gegen zwei längere globale Suchen

Stand 12.11.2026, [Leitfadenphase 4](ringdown_recovery_roadmap.md),
[eingefrorener Plan](restart_budget_plan.md) und
[Seeds/Eingaben](../data/restart_budget_protocol.json).
R: vier frische 1.000er-Suchen; L: zwei frische 2.000er-Suchen. Beide in
ursprünglicher Zeit t, lokal 300 Optimiereriterationen plus fünf zusätzliche
Neustarts. Je Paket genau eine verlustbasiert ausgewählte Ausgabe.

Zwei gepaarte Blöcke auf anchor, zwei auf variant_low, vier auf variant_high:
**48 Suchaufrufe, 32 verschiedene Seeds und 16 Paketausgaben**. Die ersten
beiden Seeds jedes Blocks werden in beiden Armen verwendet; jeder Aufruf
startet vollständig neu. Keine Checkpointfortsetzung oder historische Übernahme.
Gezielter Entwicklungsvergleich, keine erneute unabhängige Bestätigung und
keine 8/10-Grenze. Wissenschaftliche Ausführung ist vom technischen Prüfstand
im [Fortsetzungsstand](representation_implementation_status.md) getrennt.

## Sauberen Ausführungsstand nach Übernahme vorbereiten

Erst nach vollständig geprüfter Übernahme des Laufwegs auf Manjaro:

```bash
git switch main
git pull --ff-only
git status --short
git rev-parse HEAD
uv sync --locked --dev
```

Eine fremde aktivierte virtuelle Umgebung zuvor mit `deactivate` verlassen;
kein `--active` verwenden. `git status --short` muss leer sein. Den ausgegebenen
vollen Commit für alle Abschnitte und die Verifikation erhalten. Während der
Serie keine Quellenupdates oder parallelen Suchen. Bei später geändertem main
einen eigenen Worktree auf dem gespeicherten Ausführungscommit verwenden.
Fremde Julia-/CondaPkg-Sperren nicht löschen.

Alle Befehle aus diesem Checkout ausführen. Ausgabeordner und benachbarte
`-call.json` nicht löschen, überschreiben oder wiederverwenden. Die IDs 001
sind für eine erste Ausführung vorbereitet; sie belegen noch keine Ausführung
und erlauben keinen automatischen Neustart nach Abbruch.

## Technischer Vorlauf

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/check_restart_budget.py \
  --output results/restart-budget-technical-001
```

Erwartet: `Twelve tiny workers, both package arms and read-only series verification passed.`
Zwei künstliche Achtpunkt-Signale, jeweils vier Worker mit einer und zwei Worker
mit zwei äußeren Iterationen. Zwölf kleine technische Suchen und vier Paketausgaben;
Einzel- und Gesamtverifikation bleiben als eigene Artefakte erhalten. Das ist
keine wissenschaftliche Entwicklungsserie.

## Drei wissenschaftliche Abschnitte

Alle geplanten Abschnitte und Mitglieder ausführen, auch nach guten oder
schwachen Zwischenbefunden. Pausen zwischen Abschnitten sind zulässig.
Gewöhnliche numerische Ausfälle bleiben erhalten; keine Ersatzseeds oder
Wiederholungen. Bei Unterbrechung Teilstand behalten, keinen Resume versuchen;
ein neuer Lauf braucht eine dokumentierte Entscheidung und neue ID.

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_budget.py run \
  --signal anchor --output results/restart-budget-anchor-manjaro-001
```

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_budget.py run \
  --signal variant_low --output results/restart-budget-low-manjaro-001
```

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_budget.py run \
  --signal variant_high --output results/restart-budget-high-manjaro-001
```

Erwartet je Abschnitt: `anchor.npz`, `irregular.npz`, `preparation.json`,
`prepared_bindings.json`, `request-*.json`, 12/12/24 `cell-*`-Ordner mit Logs,
`run_state.json`, `completion/assessment_report.json`, Zusammenfassung,
Prüfsummen und benachbarte `-call.json`. Alle Zellen werden vor dem ersten Fit
vorbereitet und gebunden; das kann mehrere Minuten ohne Terminalausgabe dauern.

Grobe Orientierung auf demselben Rechner: **etwa 5–6 Stunden insgesamt**.
Die acht ursprünglichen T-2000er des Zeitkoordinatenversuchs benötigen zusammen
4.411,355 s Workerzeit. Die Übertragung auf 64.000 geplante Iterationen und
48 Starts ergibt mit Vorbereitung/Auswertung grob 5 h 20 min. Das ist eine
Planungsannahme: 1.000er unter diesem Plan sind noch nicht gemessen, neue Seeds
können die Kosten ändern, JIT ist nicht separat beobachtet. Gleiche Iterations-
summen bedeuten keine gleichen Kosten. 1.800 s pro Worker und 50.400 s je
Abschnitt sind Sicherheitsfristen, keine erwartete Dauer.

## Fortschritt alle zehn Sekunden

In einem zweiten Terminal in **denselben Checkout** wechseln. Für die niedrige
Variante, ohne zusätzliches Python-Skript oder `rg`:

```bash
watch -n 10 'grep -nE "\"number\"|\"status\"" results/restart-budget-low-manjaro-001/run_state.json'
```

Für Abschnitt 1 beziehungsweise 3 `low` durch `anchor` beziehungsweise `high`
ersetzen. `Strg+C` in diesem separaten Beobachtungsterminal beendet nur `watch`.
Status- oder Logfortschritt bestätigt noch keinen erfolgreichen Gesamtabschluss.

## Nach Abschluss lesend verifizieren

Nach allen drei Abschnitten, aus demselben sauberen Ausführungscommit:

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_budget.py verify-series \
  results/restart-budget-anchor-manjaro-001 \
  results/restart-budget-low-manjaro-001 \
  results/restart-budget-high-manjaro-001 \
  --output results/restart-budget-manjaro-001-verification
```

Die Verifikation startet keine Fits. Erwartet: 48 geprüfte Zellen, 16
Paketausgaben und eine beschreibende Entwicklungseinordnung nach dem Plan.
Fehlende Abschnitte, abweichender Ausführungsstand, geänderte Quellen/Inputs,
Workerherkunft oder uneinheitliche Umgebungen sperren den Abschluss; auch
späte Änderungen widerrufen Aggregate. Einzelprüfung mit `verify QUELLORDNER
--output NEUER_PRÜFORDNER` ersetzt keine gemeinsame Entscheidung.

Richtungsbefunde `restart_candidate` oder `long_candidate` sind noch keine
Bestätigung und keine automatische Profilübernahme. `unchanged_counts` oder
`mixed` werden ebenso vollständig berichtet; keine zusätzlichen Seeds bis zum
gewünschten Ergebnis. Kosten und offene Beweise getrennt erhalten, neue
Parameterübereinstimmung weiterhin `not_assessed`.

## Nach erfolgreicher Verifikation archivieren

```bash
tar -czf results/restart-budget-manjaro-001.tar.gz -C results \
  restart-budget-anchor-manjaro-001 restart-budget-anchor-manjaro-001-call.json \
  restart-budget-low-manjaro-001 restart-budget-low-manjaro-001-call.json \
  restart-budget-high-manjaro-001 restart-budget-high-manjaro-001-call.json \
  restart-budget-manjaro-001-verification \
  restart-budget-technical-001 \
  restart-budget-technical-001-fixture_a \
  restart-budget-technical-001-fixture_a-call.json \
  restart-budget-technical-001-fixture_a-verification \
  restart-budget-technical-001-fixture_b \
  restart-budget-technical-001-fixture_b-call.json \
  restart-budget-technical-001-fixture_b-verification
sha256sum results/restart-budget-manjaro-001.tar.gz
tar -tzf results/restart-budget-manjaro-001.tar.gz > /dev/null
```

Nur tatsächliche IDs packen und alle Rückgabecodes prüfen. Bereits bestehende
Archive unverändert erhalten. Gemeinsame Archivablage plus unabhängigem
Datenträger oder bestehendem Backup; beide Kopien anhand SHA-256 prüfen.
Ausführungscommit, Originalarchiv, Prüfnachweise und tatsächlichen Sicherungsstand
im [Ergebnisindex](results_index.md) gemäß [Archivregel](results_archiving.md)
nachführen. Keine großen Archive in Git; GitHub-Uploads optional.
