# Laufweg: unabhängige Bestätigung der Neustartstrategie

Stand: 09.11.2026; [eingefrorenes Protokoll](restart_confirmation_plan.md),
[Konfiguration mit allen Seeds](../data/restart_confirmation_protocol.json),
[zentraler Leitfaden](ringdown_recovery_roadmap.md). 4 × 500 gegen frische
1 × 2.000, lokales Profil 300/5, drei Signale mit je zehn neuen Seedblöcken.
150 Suchaufrufe in drei getrennten Abschnitten. Keine wissenschaftliche
Ausführung durch Implementierung oder CI belegt. Technischer Prüfstand und
Übernahme im [Fortsetzungsstand](representation_implementation_status.md).

## Vorbereitung nach Übernahme der Implementierung

Einen sauberen Manjaro-Checkout des übernommenen, vollständig geprüften Commits
verwenden. Commit vor dem ersten Abschnitt speichern; alle drei Abschnitte und
ihre Verifikation aus exakt diesem Stand und derselben gesperrten Umgebung
starten. Währenddessen keine Quellen ändern, Updates durchführen oder weitere
Suchprozesse parallel starten. Fremde Julia-/CondaPkg-Sperren nicht löschen.

```bash
git switch main
git pull --ff-only
git status --short
git rev-parse HEAD
uv sync --locked --dev
```

`git status --short` muss leer sein. Den ausgegebenen Commit für die gesamte
Serie erhalten; bei einem später veränderten main mit einem eigenen Worktree
auf diesen Commit zurückgehen. Eine fremde aktive virtuelle Umgebung zuvor
mit `deactivate` verlassen, sofern sie aktiviert ist; kein `--active` verwenden,
um versehentlich die Umgebung eines anderen Worktrees zu übernehmen.

Die folgenden Befehle aus diesem Ausführungscheckout starten. `results/` bleibt
lokal und außerhalb der Git-Historie. Bereits vorhandene Ausgabeordner niemals
löschen oder erneut verwenden. Die 001-IDs gelten nur für die erste Ausführung.

## Technischer Vorlauf

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/check_restart_confirmation.py \
  --output results/restart-confirmation-technical-001
```

Erwartet: `Six tiny workers, both signals and read-only series verification passed.`
Dies sind zwei künstliche Achtpunkt-Signale mit sechs winzigen Suchen,
getrennten Einzelverifikationen und gemeinsamer technischer Verifikation.
Keine wissenschaftlichen Anker-/Bestätigungssuchen. Abschlussausgabe und
Prüfbericht erhalten; ein Start allein belegt keinen technischen Erfolg.

## Drei wissenschaftliche Abschnitte

Alle drei Abschnitte sind vorab vorgesehen, auch bei negativen Zwischenbefunden.
Jeder benötigt 50 Suchaufrufe. Aus der bisherigen Ankerserie grob 3¾ Stunden je
Abschnitt und 11¼ Stunden insgesamt hochgerechnet; die neuen Signale, Vorbereitung
und Rechnerlast können andere Laufzeiten verursachen. Die Sicherheitsfrist
von 30 Stunden je Abschnitt ist keine Prognose. Pausen zwischen Abschnitten sind
zulässig; innerhalb eines Abschnitts kein Resume.

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_confirmation.py run \
  --signal anchor --output results/confirmation-anchor-manjaro-001
```

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_confirmation.py run \
  --signal variant_low --output results/confirmation-low-manjaro-001
```

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_confirmation.py run \
  --signal variant_high --output results/confirmation-high-manjaro-001
```

Der Treiber setzt vor Julia-Import die verbindlichen Julia-/GC-Threadgrenzen
und eine einzelne erlaubte CPU. Beide Arme verwenden denselben Iterationsworker
mit tatsächlicher Herkunfts-/Options-/Aufrufprüfung. Alle 50 Zellen werden vor
der ersten Suche vorbereitet. Neue Signale und Seeds sind bereits im
versionierten Protokoll gebunden. Keine Auswahl oder Beendigung anhand von
Wahrheit, A–D, Familiennachweis oder Zusatzraster.

Fortschritt beispielsweise für den ersten Abschnitt, in einem zweiten Terminal
im selben Checkout lesend prüfen:

```bash
grep -nE '"number"|"status"' results/confirmation-anchor-manjaro-001/run_state.json
find results/confirmation-anchor-manjaro-001 -maxdepth 1 -type f \
  -name 'cell-*-*.log' -printf '%TY-%Tm-%Td %TH:%TM:%TS %f\n' |
  sort -r | head -n 8
```

Ein gewöhnlicher erlaubter Fitfehler bleibt im Nenner und Kostenbericht.
Integritätsfehler, Unterbrechungen oder Gesamtfrist sperren den Abschluss.
Bei Abbruch Teilstände und Logs erhalten; keine automatische Neuausführung
oder Übernahme fertiger Zellen in einen neuen Abschnitt.

## Artefakte und lesende Verifikation

Jeder Abschnitt enthält:

- `preparation.json`, `prepared_bindings.json`, `request-*.json`: vollständiger
  Plan, Eingaben und Quellenbindung vor der ersten Suche.
- `anchor.npz`: historische Bezeichnung der vier Eingaberollen; bei den Varianten
  enthält sie die jeweilige neue Signalkurve, was gegen das Protokoll geprüft wird.
  `irregular.npz`: konkretes Zusatzraster mit signalspezifischer Wahrheit.
- `cell-01/` bis `cell-50/`: Originalfronten und -auswahlen, native Optionen,
  Worker-/Adapterherkunft, Timer, tatsächliche Threads, Verlustaufrufe, Kosten
  und gegebenenfalls Fehlerbelege.
- `run_state.json` und `completion/assessment_report.json`, Zusammenfassung,
  Abschluss- und Rohmanifest. Positive Freigabe nur ohne `ASSESSMENT_LOCKED`.
- Benachbarte `*-call.json`: Aufrufmessung bis Rückkehr der Veröffentlichung,
  ohne letztes Schreiben dieser Timing-Datei und erneute Schlussprüfungen.

Nach allen drei erfolgreichen Abschlüssen die gemeinsame lesende Verifikation
starten. Sie prüft alle Originalzellen erneut und verlangt dieselbe Herkunft,
Umgebung und alle drei Signale genau einmal. Kein neuer Fit, keine Suche:

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_confirmation.py verify-series \
  results/confirmation-anchor-manjaro-001 \
  results/confirmation-low-manjaro-001 \
  results/confirmation-high-manjaro-001 \
  --output results/restart-confirmation-manjaro-001-verification
```

Erwartet: `status=completed`, `complete_series=true`, `verified_cells=150`,
`search_calls=0`, keine Sperrdatei. `transition_criterion_met` ist nur dann wahr,
wenn die gewählte Neustartstrategie auf **jedem** Signal mindestens 8/10
A-Ausgaben mit gültigem Originalfamiliennachweis erreicht. Ein falscher Wert
ist ein gültiger negativer wissenschaftlicher Befund, kein technischer Abbruch.
Der Kontrollarm, alle Paarungen, kontinuierlichen Fehler und Kosten bleiben sichtbar.
Keine automatische Freigabe oder Ausführung des Rauschpiloten.

Optional kann ein fertiger Abschnitt bereits während einer Pause einzeln
lesend geprüft werden; das ersetzt die gemeinsame Prüfung nicht:

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_confirmation.py verify \
  results/confirmation-anchor-manjaro-001 \
  --output results/confirmation-anchor-manjaro-001-verification
```

## Nach erfolgreicher Verifikation archivieren

```bash
tar -czf results/restart-confirmation-manjaro-001.tar.gz -C results \
  confirmation-anchor-manjaro-001 confirmation-anchor-manjaro-001-call.json \
  confirmation-low-manjaro-001 confirmation-low-manjaro-001-call.json \
  confirmation-high-manjaro-001 confirmation-high-manjaro-001-call.json \
  restart-confirmation-manjaro-001-verification
sha256sum results/restart-confirmation-manjaro-001.tar.gz
```

Das unveränderte Paket im gemeinsamen Archivordner und auf unabhängigem
Datenträger bzw. im bestehenden Backup sichern. SHA-256 beider Kopien prüfen,
bei Backup lesenden Wiederherstellungscheck durchführen. Ausführungscommit,
Abschlussbefunde, Archivhash und tatsächliche Sicherung im
[Ergebnisindex](results_index.md) nachtragen. Optionale Einzelverifikationen
zusätzlich aufbewahren. Keine großen Archive in Git; GitHub-Uploads sind optional.
