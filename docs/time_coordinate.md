# Laufweg: begrenzter Zeitkoordinatenvergleich

Stand 12.11.2026, [Leitfadenphase 4](ringdown_recovery_roadmap.md),
[eingefrorener Plan](time_coordinate_plan.md) und
[Seeds/Eingaben](../data/time_coordinate_protocol.json).
16 frische Suchen: zwei gepaarte Blöcke auf anchor, zwei auf variant_low und
vier auf variant_high. T verwendet t, U die gedehnte Zeit u=32t; beide bei
1 × 2.000 und lokal 300 Optimiereriterationen plus fünf zusätzliche Neustarts.
Implementierung und technische Prüfbelege im
[Fortsetzungsstand](representation_implementation_status.md) sind von der
noch nicht ausgeführten wissenschaftlichen Serie getrennt.

Die drei Signale sind jetzt bekannte Entwicklungsfälle. Die ursprüngliche
negative Bestätigung aus PR82 bleibt erhalten. Dieser Lauf hat keine 8/10-Grenze
und entscheidet weder über einen Rauschpilot noch über physikalische Parameter.
Der spätere Vergleich 4 × 1.000 gegen 2 × 2.000 erhält nach diesem Befund einen
eigenen eingefrorenen Plan; seine Suchen sind hier nicht enthalten.

## Sauberen Ausführungsstand vorbereiten

Nach Übernahme der vollständig technisch geprüften Implementierung auf Manjaro:

```bash
git switch main
git pull --ff-only
git status --short
git rev-parse HEAD
uv sync --locked --dev
```

Eine fremde aktivierte virtuelle Umgebung zuvor mit `deactivate` verlassen.
Kein `--active` verwenden. `git status --short` muss leer sein; Commit und
gesperrte Umgebung für alle Abschnitte und die Verifikation erhalten. Während
der Serie keine Quellen verändern, Updates oder parallele Suchen starten.
Fremde Julia-/CondaPkg-Sperren nicht löschen. Bei später geändertem main einen
eigenen Worktree auf dem gespeicherten Ausführungscommit verwenden.

Alle Befehle aus diesem Checkout ausführen. Vorhandene Ausgabeordner und
benachbarte `-call.json` niemals löschen oder wiederverwenden. Die IDs 001
gelten für eine erste Ausführung, nicht als Auftrag zum Wiederholen eines Abbruchs.

## Technischer Vorlauf

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/check_time_coordinate.py \
  --output results/time-coordinate-technical-001
```

Erwartet: `Four tiny workers, both signals and read-only series verification passed.`
Dies sind vier kleine technische Suchen auf zwei künstlichen Achtpunkt-Signalen,
keine wissenschaftlichen Entwicklungsfälle. Beide Einzelprüfungen und die
gemeinsame Prüfung bleiben als eigene Artefakte erhalten.

## Wissenschaftliche Abschnitte

Alle drei Abschnitte und sämtliche vorab geplanten Zellen gehören zur Serie,
auch bei schwachen Zwischenbefunden. Zwischen Abschnitten sind Pausen zulässig.
Ein Abbruch bleibt mit Teilkosten erhalten; kein Resume und kein automatischer
Neustart. Eine neue Ausführung benötigt eine dokumentierte Entscheidung und neue ID.

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_time_coordinate.py run \
  --signal anchor --output results/time-coordinate-anchor-manjaro-001
```

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_time_coordinate.py run \
  --signal variant_low --output results/time-coordinate-low-manjaro-001
```

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_time_coordinate.py run \
  --signal variant_high --output results/time-coordinate-high-manjaro-001
```

Erwartet je Abschnitt: `anchor.npz`, `irregular.npz`, `search-T.npz`, `search-U.npz`,
`preparation.json`, `prepared_bindings.json`, `request-*.json`, `cell-*` samt Logs,
`run_state.json`, `completion/assessment_report.json`, Zusammenfassung und
Prüfsummen sowie die benachbarte `-call.json`. Die zwei Suchkoordinatendateien
werden vor allen Fits gespeichert und gebunden. Vier, vier und acht Zellaufrufe
sind geplant; die Vorbereitung kann mehrere Minuten ohne Terminalausgabe dauern.

Aus den bisherigen 2.000er-Workerzeiten ergeben sich für 16 gleich teure Suchen
grob 2½ Stunden plus Vorbereitung und Auswertung. Das ist eine Orientierung:
die geänderte Koordinate kann Kosten und Suchverlauf verändern. Die sechs Stunden
Gesamtfrist je Abschnitt und 1.800 Sekunden pro Worker sind Sicherheitsgrenzen.

Einfacher lesender Fortschritt im zweiten Terminal, ohne `rg` und ohne Codeänderung:

```bash
watch -n 5 'grep -nE "\"number\"|\"status\"" results/time-coordinate-high-manjaro-001/run_state.json'
```

Den Abschnittspfad anpassen. Eine wachsende Logdatei allein bestätigt noch keinen
erfolgreichen Abschluss; maßgeblich bleiben gespeicherter Abschluss und Verifikation.

## Nach erfolgreichem Abschluss lesend verifizieren

Nach allen drei Abschnitten, vom exakt gleichen sauberen Ausführungscommit:

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_time_coordinate.py verify-series \
  results/time-coordinate-anchor-manjaro-001 \
  results/time-coordinate-low-manjaro-001 \
  results/time-coordinate-high-manjaro-001 \
  --output results/time-coordinate-manjaro-001-verification
```

Die Verifikation startet keine Fits. Erwartet sind 16 geprüfte Zellen und eine
beschreibende Entwicklungseinordnung nach dem eingefrorenen Plan. Fehlende oder
veränderte Quellen, Eingaben, Workerbelege, Abschnitte oder uneinheitliche
Umgebungen sperren den Abschluss. Die Einzelprüfung ist mit `verify QUELLORDNER
--output NEUER_PRÜFORDNER` möglich; sie ersetzt keine Gesamtentscheidung.

Originalkandidat q und physisches Modell q(32t) bleiben getrennt. Klasse und
Beweise beziehen sich auf die ursprüngliche physische Zeit. Die Variablensubstitution
kann einen längeren Baum erzeugen: Überschreitet die Komposition die unveränderte
20-Knoten-Prüfgrenze, bleiben Struktur, Domain und Rest ausdrücklich ungeklärt;
physische Kurvenfehler werden weiter berichtet. Diese Fälle werden gesondert
gezählt und sind kein Beleg eines Suchfehlers. Sie können den gemeinsamen
Familienendpunkt von U stärker begrenzen. Keine Erweiterung der Beweisregeln
und keine stillschweigende Parameterbewertung.

## Nach erfolgreicher Verifikation archivieren

```bash
tar -czf results/time-coordinate-manjaro-001.tar.gz -C results \
  time-coordinate-anchor-manjaro-001 time-coordinate-anchor-manjaro-001-call.json \
  time-coordinate-low-manjaro-001 time-coordinate-low-manjaro-001-call.json \
  time-coordinate-high-manjaro-001 time-coordinate-high-manjaro-001-call.json \
  time-coordinate-manjaro-001-verification \
  time-coordinate-technical-001 \
  time-coordinate-technical-001-fixture_a \
  time-coordinate-technical-001-fixture_a-call.json \
  time-coordinate-technical-001-fixture_a-verification \
  time-coordinate-technical-001-fixture_b \
  time-coordinate-technical-001-fixture_b-call.json \
  time-coordinate-technical-001-fixture_b-verification
sha256sum results/time-coordinate-manjaro-001.tar.gz
tar -tzf results/time-coordinate-manjaro-001.tar.gz > /dev/null
```

Nur tatsächliche IDs packen und beide Rückgabecodes prüfen. Originalarchiv
unverändert im gemeinsamen Archivordner sowie auf unabhängigem Datenträger oder
im bestehenden Backup erhalten; Kopien gegen die ausgegebene SHA-256 prüfen.
Ausführungscommit, Ergebnis, Hash, Ablage und Sicherungsstand im bestehenden
[Ergebnisindex](results_index.md) gemäß [Archivregel](results_archiving.md)
nachführen. Große Archive nicht in Git aufnehmen; GitHub-Uploads sind optional.
