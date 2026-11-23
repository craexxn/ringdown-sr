# Laufweg der Hauptserie: Hintergrunddauer und freie Rekonstruktion

Stand 23.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md).
Der [verbindliche Hauptplan](main_study_plan.md) und die vollständige
[Seedtabelle](../data/main_study_seeds.json) sind vor wissenschaftlichen
Beobachtungen in `126b39e311eceeb12102cf09e6da57deb735025b` gebunden.
Plan-SHA-256: `772b26883e5bb871ad64af9d60b2e07b69c786af34790e9c68cfeb6930b5d706`;
Seeds-SHA-256: `b03b2ec41a868e6875169c5375639c2fbee5c52838063ae479a3dd990a870381`.
Der bisherige N128-Pilot und seine Originalarchive bleiben unverändert.

Die technische Anbindung wird derzeit integriert und geprüft. Vollständige
Abnahme, endgültiger Implementierungscommit und CI-Nachweis stehen im
[Fortsetzungsstand](representation_implementation_status.md) beziehungsweise
Implementierungs-PR. Diese Anleitung belegt keine bereits ausgeführten
Hauptsuchen. Ein technischer Cloud-Vorlauf ersetzt keinen Vorlauf auf Manjaro;
der Zielrechnernachweis ist noch offen.

## Umfang, Speicher und Reihenfolge

Je Signal sind 30 AR(1)- und zehn White-Blöcke vorgesehen. Jeder Block
enthält vier Arme mit je vier Suchneustarts: O, wahre Kovarianz K sowie
Schätzung aus 64 beziehungsweise 4096 s. Damit entstehen je Signal
160 Paketausgaben und 640 Suchworker, zusammen **320 Ausgaben und
1280 wissenschaftliche Worker**. Die unabhängige Einheit ist der Block,
nicht jeder Suchneustart. R4×1000, lokal 300/5, bleibt fest.

Die gemeinsame Startfolge führt aus:

1. Acht technische N103-Zehnerworker: zwei eigene AR(1)-Signalfälle,
   je vier Arme, ursprüngliches lokales Profil, getrennte lesende Prüfung
   und technische Originalplots.
2. Alle 80 wissenschaftlichen Fälle, unabhängigen Rollen, vollständigen
   Hintergrundreihen, Kovarianzen und Bewertungsachsen vor der ersten
   Hauptsuche erzeugen und binden; gemeinsames Archiv erstellen.
3. Signal 200 Hz/4 ms vollständig ausführen, lesend nachprüfen, darstellen
   und archivieren.
4. Signal 250 Hz/6 ms anschließend ausführen; den abgeschlossenen ersten
   Abschnitt als Herkunftsvoraussetzung prüfen. Beide Signalabschnitte
   gemeinsam darstellen, den zweiten Abschnitt getrennt archivieren.

Allein die 80 wissenschaftlichen 4096-s-Hintergrundreihen benötigen
`80 × 4096 × 4096 × 8 = 10 GiB` reine Float64-Nutzdaten. Die beiden
technischen Reihen benötigen zusätzlich 256 MiB. Dazu kommen Eingaben,
Suchartefakte, Plots, Punktdaten, Julia/Python und komprimierte Originalarchive.
**Mindestens 30 GiB freien Platz als praktische Reserve einplanen**;
dies ist keine garantierte Obergrenze des gesamten Verzeichnisses.
Rauschreihen werden gestreamt, nicht alle gleichzeitig in RAM geladen.
Originaldateien und Archive bleiben nebeneinander erhalten.

Eine Laufzeitprognose für die neuen Signalbedingungen liegt noch nicht vor.
Die Fristen im Plan sind Sicherheitsgrenzen. Tatsächliche Vorbereitungs-,
Worker-, Paket-, Abschnitts-, Prüf- und Exportkosten werden getrennt erfasst;
enthaltene Zeiten dürfen nicht additiv doppelt gezählt werden.

## Geprüfter Ausführungscheckout

Erst den durch Review und vollständige Ready-CI geprüften Implementierungsstand
verwenden. Der folgende Platzhalter ist durch dessen vollständigen Commit zu
ersetzen; der Plancommit allein enthält noch keinen fertigen Laufweg.
Der Ausführungsordner muss neu sein.

```bash
bash <<'BASH'
set -euo pipefail
task_commit='HIER_VOLLSTAENDIGEN_GEPRUEFTEN_IMPLEMENTIERUNGSCOMMIT_EINTRAGEN'
[[ "$task_commit" =~ ^[0-9a-f]{40}$ ]]
git fetch origin codex/main-study
git cat-file -e "$task_commit^{commit}"
git worktree add --detach ../ringdown-main-study-run "$task_commit"
cd ../ringdown-main-study-run
test "$(git rev-parse HEAD)" = "$task_commit"
test -z "$(git status --porcelain)"
unset VIRTUAL_ENV
uv sync --locked --dev --python 3.12.14
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
uv run --locked --no-sync python scripts/run_python.py scripts/check_environment.py
git rev-parse HEAD
BASH
```

Alle weiteren Befehle laufen in `ringdown-main-study-run`. Während der Serie
bleiben Commit und Umgebung unverändert; keine Aktualisierung mit `git pull`
oder erneutem `uv sync`. `--no-sync` erhält die vorbereitete Umgebung.
Die Umgebungsprüfung bereitet Julia vor dem zeitlich begrenzten Vorlauf vor.

## Tests vor dem technischen Vorlauf

Ein frischer Checkout benötigt die registrierten historischen Git-Belege.
Der folgende lesende Abgleich lädt fehlende dauerhafte PR-Refs über den bereits
eingerichteten Git-Zugang; er verändert weder HEAD noch Arbeitsdateien.
Danach folgen Dokumentation, Ruff, Format und die vollständige Python-Suite.

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
git('fetch', '--no-tags', '--no-recurse-submodules', 'origin',
    *(f'{ref}:{targets[ref]}' for ref in refs))
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

Die vollständige native Regressionssuite einschließlich des neuen achtfachen
Integrationsvorlaufs steht in
[technical-checks.yml](../.github/workflows/technical-checks.yml).
Ein grüner Python-Lauf ersetzt die volle Ready-CI nicht. Ein bereits bestandener
unveränderter CI-Stand wird nicht routinemäßig erneut ausgeführt; lange
CI-Läufe müssen nicht durch fortlaufende Chat-Abfragen überwacht werden.

## Gemeinsamer Start auf Manjaro

**Dieser Befehl startet nach bestandenem Vorlauf auch die vollständige
wissenschaftliche Serie mit 1280 Workern.** Er ist kein bloßer Testbefehl.
Für ausschließlich technische Prüfungen den getrennten Block weiter unten
verwenden.

Netzteil anschließen, Laptop mit offenem Deckel stehen lassen und das Terminal
offen halten. Das Skript bindet eine erlaubte CPU und erwirbt vor Ausführung
die Sperre `sleep:idle:handle-lid-switch`. Schlägt dies fehl, startet keine
ungeschützte Ersatzvariante. Erzwungener Suspend oder Stromverlust bleiben
möglich; die Integritäts- und Uhrenprüfungen bleiben aktiv.

```bash
unset VIRTUAL_ENV
bash scripts/run_main_study_manjaro.sh results/main-study-manjaro-001
```

Das [Startskript](../scripts/run_main_study_manjaro.sh) verwendet die oben
beschriebene feste Reihenfolge. Ein vorhandener Laufordner wird abgewiesen.
Bei Fehler stoppt die Folge; vorhandene Artefakte bleiben erhalten. Es gibt
keine automatischen Ersatzseeds, Workerwiederholungen oder stillen Neustarts.
Eine leere Fortschrittsanzeige vor dem Start ist kein Nachweis laufender Suchen.

## Fortschritt in einem zweiten Terminal

```bash
unset VIRTUAL_ENV
uv run --locked --no-sync python scripts/watch_main_study.py \
  --root results/main-study-manjaro-001
```

Die [Anzeige](../scripts/watch_main_study.py) aktualisiert alle zehn Sekunden
und liest ausschließlich gespeicherte Zustände: Gesamtschritt, je Signal
Fälle `/40`, beendete Prozesse `/640`, Arm-/Mitgliedsstatus, Fehler und bekannte
Zeiten. `--all` zeigt alle Fälle; `--once` genau eine Ansicht; `--json` gibt
jede Ansicht maschinenlesbar aus. `--once --json` liefert genau eine
maschinenlesbare Momentaufnahme. Strg+C beendet nur diese Anzeige.
Ein gespeicherter laufender Stand kann nach Abbruch stehen bleiben; beendete
Prozesse oder `40/40` sind kein Ersatz für erfolgreiche Verifikation.

## Ausschließlich technischer Vorlauf

Dieser alternative Block führt acht Zehn-Iterationen-Worker einschließlich
beider vollständiger Hintergrunddauern aus, danach lesende Verifikation und
gebundene technische Plots. Er erzeugt keine Hauptfälle oder Hauptsuchen.
Der gemeinsame Start führt seinen eigenen Vorlauf aus; ein separater Vorlauf
ist nicht zusätzlich vor jedem neuen Gesamtlauf erforderlich.

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export MPLBACKEND=Agg
task_cpu=$(uv run --locked --no-sync python -c 'import os; print(min(os.sched_getaffinity(0)))')
systemd-inhibit --what=sleep:idle:handle-lid-switch --mode=block \
  --who=ringdown-sr --why='Technischer Hauptserienvorlauf ohne Suspend' \
  --no-ask-password taskset -c "$task_cpu" bash <<'RUN'
set -euo pipefail
uv run --locked --no-sync python scripts/check_main_study.py \
  --output results/main-study-preflight-manjaro-001
uv run --locked --no-sync python scripts/check_main_study.py \
  --verify results/main-study-preflight-manjaro-001
uv run --locked --no-sync python scripts/run_main_study.py technical-plots \
  --technical results/main-study-preflight-manjaro-001 \
  --export results/main-study-preflight-plots-manjaro-001
uv run --locked --no-sync python scripts/run_main_study.py verify-plots \
  --export results/main-study-preflight-plots-manjaro-001
RUN
BASH
```

## Lesender Abschluss und getrennte Abschnitte

Bei erfolgreichem gemeinsamem Start sind diese Schritte bereits ausgeführt.
Für eine ausdrücklich gewünschte zusätzliche lesende Prüfung immer neue
Ausgabeordner wählen. `--output` bezeichnet die vorhandene Serie,
`--export` die **neue** Verifikationsausgabe. Der zweite Signalabschnitt
verlangt zusätzlich `--previous` mit dem unveränderten ersten Abschnitt.

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
uv run --locked --no-sync python scripts/run_main_study.py verify \
  --inputs results/main-study-manjaro-001/inputs \
  --technical results/main-study-manjaro-001/technical \
  --signal signal_200_4ms \
  --output results/main-study-manjaro-001/signal_200_4ms \
  --export results/main-study-manjaro-001/verification-200-extra-001

uv run --locked --no-sync python scripts/run_main_study.py verify \
  --inputs results/main-study-manjaro-001/inputs \
  --technical results/main-study-manjaro-001/technical \
  --signal signal_250_6ms \
  --previous results/main-study-manjaro-001/signal_200_4ms \
  --output results/main-study-manjaro-001/signal_250_6ms \
  --export results/main-study-manjaro-001/verification-250-extra-001
BASH
```

Der Plotexport erhält `--series-200` und für beide Signale zusätzlich
`--series-250`. Die Darstellungen enthalten alle geplanten Ausgaben samt
Ausfällen, unveränderte Originalformeln mit Einheiten, vollständige Punktdaten,
Kurven- und Struktur-/Domainbefunde. Ein einzelner abgeschlossener Abschnitt
wird ausdrücklich als Teilstand dargestellt; fehlende Ausgaben des zweiten
Abschnitts werden nicht als zusätzliche Beobachtungen gewertet.

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export MPLBACKEND=Agg
uv run --locked --no-sync python scripts/run_main_study.py plots \
  --inputs results/main-study-manjaro-001/inputs \
  --technical results/main-study-manjaro-001/technical \
  --series-200 results/main-study-manjaro-001/signal_200_4ms \
  --series-250 results/main-study-manjaro-001/signal_250_6ms \
  --export results/main-study-manjaro-001/plots-extra-001
uv run --locked --no-sync python scripts/run_main_study.py verify-plots \
  --export results/main-study-manjaro-001/plots-extra-001
BASH
```

Der vollständige Abschnitt 200 kann Voraussetzung eines späteren, noch nicht
begonnenen Abschnitts 250 sein. Innerhalb eines abgebrochenen Abschnitts gibt
es keinen geprüften Fortsetzungsvertrag; einzelne fertige Pakete werden nicht
automatisch in einen neuen Lauf übernommen. Keine manuelle Ergänzung von
Erfolgsmarkern und kein Überschreiben bestehender Ausgaben.

## Originalarchive und Abbrüche

Im Unterordner `archives` entstehen drei Pakete mit je eigener SHA-256-Datei:

| Archivteil | Inhalt und Abhängigkeit |
| --- | --- |
| `shared` | Alle wissenschaftlichen Eingaben, technischer Vorlauf, technische Plots und zugeordnete Aufrufkosten |
| `signal_200_4ms` | Erster Abschnitt, Verifikation und Plots; bindet den Hash von `shared` |
| `signal_250_6ms` | Zweiter Abschnitt, Verifikation und gemeinsame Plots; bindet `shared` und den ersten Abschnitt |

`archive --root results/main-study-manjaro-001 --part shared` beziehungsweise
`--part signal_200_4ms` und `--part signal_250_6ms` entsprechen den Schritten
des Startskripts. Vorhandene Archive werden nicht ersetzt. Der Archivierer
liest die gepackten Dateien zurück und prüft ihre Bytes sowie den unveränderten
Quellbestand. Das ist eine Integritätsprüfung; wissenschaftliche Verifikation
bleibt ein eigener Schritt.

Nach einem Abbruch kann der erhaltene Teilbestand einmal getrennt gesichert
werden, ohne Suchen oder Verifikation zu starten:

```bash
uv run --locked --no-sync python scripts/run_main_study.py archive \
  --root results/main-study-manjaro-001 --part partial
```

Ein Teilarchiv bleibt ein Abbruchbeleg. Kostenbelege, Fehler und gesperrte
Ausgaben gehören dazu. Ein Archiv erzeugt keine nachträgliche Erfolgsfreigabe.
Die Originale werden nach der [Archivierungsregel](results_archiving.md)
erhalten und auf einen unabhängigen Datenträger beziehungsweise ins bestehende
Backup kopiert; die zweite Kopie ist erst nach Hashprüfung bestätigt.
Unabhängige Sicherung, spätere Übertragung und Auswertung sind vom lokalen
Laufabschluss zu unterscheiden. Große `shared`-Archive nicht ungeprüft durch
kleine Übersichten ersetzen; deren genaue benötigte Teilmenge wird für eine
spätere Übertragung anhand der Originalmanifeste festgelegt.
