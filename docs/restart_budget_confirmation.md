# Laufweg: Bestätigung zweier Neustartpakete auf neuen Signalen

Stand 13.11.2026, [Leitfadenphase 6](ringdown_recovery_roadmap.md),
[eingefrorener Plan](restart_budget_confirmation_plan.md) und
[Seeds/Eingaben](../data/restart_budget_confirmation_protocol.json).
R: vier frische 1.000er-Suchen als vorläufiger Kandidat; L: zwei frische
2.000er-Suchen als aktive Kontrolle. Beide in ursprünglicher Zeit t, lokal
300 Optimiereriterationen plus fünf zusätzliche lokale Neustarts. Pro Paket
genau eine anhand nativen Trainingsverlusts ausgewählte Originalausgabe.

Drei neue Signaldefinitionen `confirm_low`, `confirm_mid` und `confirm_high`,
je zehn gepaarte Blöcke: **180 Suchaufrufe, 120 verschiedene Seeds und
60 Paketausgaben**. Erste zwei Blockseeds in beiden Armen, jeweils vollständig
frischer Aufruf. Keine historische Wiederverwendung oder Checkpointfortsetzung.
R muss mindestens 8/10 A-Ausgaben mit nachgewiesener gültiger Originalfamilie
auf jedem Signal erreichen; L erhält dieselbe praktische Prüfung separat.
Keine automatische Auswahl des besseren Arms oder Kombination ihrer Ausgaben.

**Noch keine wissenschaftliche Ausführung:** Der Plan ist vor Implementierung
in `352b7b5` eingefroren. Technische Abnahme, vollständige Ready-CI und Übernahme
des Laufwegs stehen noch aus; tatsächliche Nachweise im
[Fortsetzungsstand](representation_implementation_status.md). Die folgenden
001-IDs sind geplante erste Ausgaben. Die wissenschaftlichen Befehle erst nach
vollständig geprüfter Übernahme verwenden, nicht während der Implementierung.

## 1. Eigenen sauberen Ausführungsstand nach Übernahme vorbereiten

Aus dem bestehenden Repository einen eigenen Worktree anlegen:

```bash
git fetch origin &&
git worktree add --detach ../ringdown-budget-confirmation-run origin/main &&
cd ../ringdown-budget-confirmation-run &&
git status --short &&
test -z "$(git status --porcelain)" &&
git rev-parse HEAD &&
uv sync --locked --dev
```

Die Kette stoppt beim ersten Fehler; insbesondere bei einem bereits vorhandenen
Worktree nicht einfach mit dem Vorlauf fortfahren. Eine fremde aktivierte
virtuelle Umgebung zuvor mit `deactivate` verlassen; kein `--active` verwenden.
`git status --short` muss leer sein. Den ausgegebenen vollen Commit für Vorlauf,
alle drei Abschnitte und Verifikation erhalten. Während der Serie keine
Quellenupdates, Änderungen oder parallelen Suchen. Alle weiteren Befehle aus
diesem Worktree ausführen; fremde Julia-/CondaPkg-Sperren nicht löschen.

Ausgabeordner, benachbarte `-call.json` und Archive nicht überschreiben oder
wiederverwenden. Vorhandene Teilstände nach Unterbrechung erhalten. Ein neuer
Lauf benötigt eine dokumentierte Entscheidung und neue IDs, keinen Resume.

## 2. Technischer Vorlauf

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/check_restart_budget_confirmation.py \
  --output results/restart-budget-confirmation-technical-001
```

Erwartete Abschlussmeldung:
`Twelve tiny workers, both package arms and read-only series verification passed.`
Zwölf kleine technische Worker auf zwei künstlichen Achtpunkt-Signalen,
je vier mit einer und zwei mit zwei äußeren Iterationen, insgesamt vier
Paketausgaben. Beide Einzelverifikationen und die gemeinsame lesende Prüfung
müssen bestehen. Ergebnisse: Präfix `restart-budget-confirmation-technical-001`
für die Gesamtprüfung, daneben `-fixture_a`, `-fixture_b`, ihre `-call.json`
und jeweils `-verification`. Das bestätigt die technische Funktionsfähigkeit,
keine wissenschaftliche 8/10-Grenze. Nur nach erfolgreichem Vorlauf fortfahren.

## 3. Alle drei wissenschaftlichen Abschnitte hintereinander

Der folgende Bash-Block führt die drei vorab festgelegten Abschnitte ohne
weitere Eingabe nacheinander aus. Er stoppt bei einem fehlgeschlagenen
Kommando und startet keinen Abschnitt automatisch erneut. Gewöhnliche nach
Protokoll zulässige numerische Ausfälle behandelt der Runner innerhalb der
Serie; Integritätsfehler und Unterbrechungen sperren ihren Abschluss.

```bash
bash <<'BASH'
set -euo pipefail
for task_section in low mid high; do
  test ! -e "results/restart-budget-confirmation-${task_section}-manjaro-001"
  test ! -e "results/restart-budget-confirmation-${task_section}-manjaro-001-call.json"
done
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
uv run --locked python scripts/run_restart_budget_confirmation.py run \
  --signal confirm_low --output results/restart-budget-confirmation-low-manjaro-001
uv run --locked python scripts/run_restart_budget_confirmation.py run \
  --signal confirm_mid --output results/restart-budget-confirmation-mid-manjaro-001
uv run --locked python scripts/run_restart_budget_confirmation.py run \
  --signal confirm_high --output results/restart-budget-confirmation-high-manjaro-001
BASH
```

Das Terminal offen halten und automatischen Ruhezustand des Rechners verhindern.
Die Abfolge kann über Nacht und bis in den nächsten Tag laufen. Grobe Orientierung
aus den bisherigen Abschnittskosten auf demselben Rechner: **18–20 Stunden für
die wissenschaftliche Serie**, technischer Vorlauf und spätere Verifikation
zusätzlich. Neue Signale und Seeds können erheblich abweichen; gleiche Summen
äußerer Iterationen bedeuten keine gleichen Kosten. 1.800 s pro Worker und
115.200 s je Signalabschnitt sind Sicherheitsfristen, keine erwartete Dauer.

Je Abschnitt erwartet: `anchor.npz`, `irregular.npz`, `preparation.json`,
`prepared_bindings.json`, `request-*.json`, 60 `cell-*`-Ordner mit Logs,
`run_state.json`, `completion/assessment_report.json`, Zusammenfassung,
Prüfsummen und benachbarte `-call.json`. Alle Zellen werden vor dem ersten Fit
vorbereitet und gebunden; mehrere Minuten ohne Terminalausgabe sind möglich.

Alle geplanten Mitglieder und Abschnitte bleiben vorgesehen, unabhängig von
guten oder schlechten Zwischenbefunden. Kein vorzeitiges Beenden anhand von
Klasse, Signalwahrheit, Familienprüfung oder Zusatzraster, keine Ersatzseeds.
Nach versehentlichem Abbruch die Originale unverändert behalten und den
Teilstand dokumentieren; nicht löschen und dieselben Befehle erneut starten.

## 4. Fortschritt alle zehn Sekunden

In einem zweiten Terminal in **denselben Worktree** wechseln. Ohne `rg` und
ohne Codeänderung zeigt dieser Befehl Status und Zellzahlen aller Abschnitte:

```bash
watch -n 10 'for task_section in low mid high; do
  task_state="results/restart-budget-confirmation-${task_section}-manjaro-001/run_state.json"
  printf "\n%s: 60 geplante Zellen\n" "$task_section"
  if [ -f "$task_state" ]; then
    grep "^  \"status\"" "$task_state"
    grep "^      \"status\"" "$task_state" | sort | uniq -c
  else
    printf "Noch nicht gestartet\n"
  fi
done'
```

`Strg+C` in diesem separaten Beobachtungsterminal beendet nur `watch`.
Im Suchterminal würde es die Serie abbrechen. Die eingerückten Zellstatus zeigen
den Fortschritt; der übergeordnete Status lautet während der vollständigen
Vorbereitung `preparing` und während des Suchteils `running`. Zellfortschritt
oder 60 fertige Zellen ersetzen keine
erfolgreiche Abschlussveröffentlichung und lesende Gesamtverifikation.

## 5. Nach erfolgreichem Abschluss lesend verifizieren

Nach allen drei Abschnitten, aus demselben sauberen Ausführungscommit:

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_restart_budget_confirmation.py verify-series \
  results/restart-budget-confirmation-low-manjaro-001 \
  results/restart-budget-confirmation-mid-manjaro-001 \
  results/restart-budget-confirmation-high-manjaro-001 \
  --output results/restart-budget-confirmation-manjaro-001-verification
```

Die Verifikation startet keine Fits. Erwartet: 180 geprüfte Zellen,
60 Paketausgaben und vollständige Berichte je Signal samt gemeinsamem Abschluss.
`transition_criterion_met` bezeichnet ausschließlich die praktische R-Grenze;
`L_control_criterion_met` berichtet L getrennt. Technisch erfolgreiche Verifikation
ist auch bei verfehlter wissenschaftlicher Grenze möglich. Drei feste
Innenbereichsfälle liefern keine allgemeine Erfolgswahrscheinlichkeit und
wiederholen nicht die zuvor schwierige Randkombination. Keine gepoolte Quote,
kein nachträglicher Armwechsel, keine zusätzliche Seedrunde bis zum Erfolg.

Fehlende Abschnitte, abweichender Ausführungsstand oder numerische Umgebung,
geänderte Quellen/Inputs und widersprüchliche Workerherkunft sperren den
Abschluss; auch späte Änderungen widerrufen Aggregate. Eine Einzelprüfung mit
`verify QUELLORDNER --output NEUER_PRÜFORDNER` ersetzt die Gesamtentscheidung
nicht. Definitionslücken mit gültiger Fortsetzung und ungeklärte Beweise bleiben
getrennt; neue Parameterübereinstimmung weiterhin `not_assessed`.

## 6. Nach erfolgreicher Verifikation archivieren

Erst nach erfolgreichem Rückgabecode der Gesamtverifikation ausführen.
Der Block nimmt alle drei Ergebnisordner, ihre benachbarten Aufrufmessungen,
Gesamtverifikation und den vollständigen technischen Vorlauf auf:

```bash
bash <<'BASH'
set -euo pipefail
task_archive=restart-budget-confirmation-manjaro-001.tar.gz
test ! -e "results/$task_archive"
test ! -e "results/$task_archive.sha256"
tar -czf "results/$task_archive" -C results \
  restart-budget-confirmation-low-manjaro-001 \
  restart-budget-confirmation-low-manjaro-001-call.json \
  restart-budget-confirmation-mid-manjaro-001 \
  restart-budget-confirmation-mid-manjaro-001-call.json \
  restart-budget-confirmation-high-manjaro-001 \
  restart-budget-confirmation-high-manjaro-001-call.json \
  restart-budget-confirmation-manjaro-001-verification \
  restart-budget-confirmation-technical-001 \
  restart-budget-confirmation-technical-001-fixture_a \
  restart-budget-confirmation-technical-001-fixture_a-call.json \
  restart-budget-confirmation-technical-001-fixture_a-verification \
  restart-budget-confirmation-technical-001-fixture_b \
  restart-budget-confirmation-technical-001-fixture_b-call.json \
  restart-budget-confirmation-technical-001-fixture_b-verification
tar -tzf "results/$task_archive" > /dev/null
cd results
sha256sum "$task_archive" > "$task_archive.sha256"
sha256sum -c "$task_archive.sha256"
BASH
```

Erwartet: Originalarchiv, daneben `.sha256` mit portablem Dateinamen und
erfolgreiche Prüfsummenmeldung. Bereits bestehende Archive unverändert erhalten.
Bei Fehlern auch ein unvollständiges Archiv nicht stillschweigend überschreiben;
Ursache und tatsächliche Artefakte prüfen. Keine großen Archive in Git aufnehmen.

## 7. Gemeinsame Ablage und unabhängige zweite Kopie

Die beiden Platzhalter durch tatsächlich bestehende Ablageordner ersetzen;
die zweite Kopie muss auf einem unabhängigen Datenträger oder im bestehenden
Backup liegen. Der folgende Block überschreibt keine vorhandenen Dateien:

```bash
bash <<'BASH'
set -euo pipefail
task_archive=restart-budget-confirmation-manjaro-001.tar.gz
task_archive_dir='/pfad/zum/gemeinsamen/Archiv'
task_backup_dir='/pfad/auf/unabhaengigem/Datentraeger'
for task_destination in "$task_archive_dir" "$task_backup_dir"; do
  test -d "$task_destination"
  test ! -e "$task_destination/$task_archive"
  test ! -e "$task_destination/$task_archive.sha256"
done
for task_destination in "$task_archive_dir" "$task_backup_dir"; do
  cp -- "results/$task_archive" "results/$task_archive.sha256" "$task_destination/"
  (cd "$task_destination" && sha256sum -c "$task_archive.sha256")
done
BASH
```

Bei bestehender Backup-Lösung stattdessen deren tatsächliche Sicherung und
lesenden Wiederherstellungs-/SHA-256-Check nachweisen. Zwei Verzeichnisse auf
demselben Datenträger sind keine unabhängigen Kopien. Ausführungscommit,
Originalarchivhash, enthaltene IDs, Prüfergebnisse, tatsächliche Ablageorte und
Sicherungsstand im bestehenden [Ergebnisindex](results_index.md) gemäß
[Archivregel](results_archiving.md) nachführen. GitHub-Releases und Uploads
sind optional; die lokalen Sicherungsschritte benötigen keinen Upload.

Die wissenschaftliche Einordnung folgt nach Quellenprüfung. Auch ein positives
R-Ergebnis startet keinen Rauschpilot: Das gewählte Profil muss zuvor bewusst
in den allgemeinen späteren Laufweg übernommen und dort rauschfrei geprüft
werden. Dessen Gewichtung muss Struktursuche und Konstantenoptimierung bestimmen.
