# Laufweg: globale Neustarts und längere Einzelsuche

Stand: 06.11.2026, [Leitfadenphase 3](ringdown_recovery_roadmap.md).
Das [Protokoll](global_restart_comparison_plan.md) und die
[Konfiguration](../data/global_restart_protocol.json) wurden vor Implementierung
in `b00fc4a0a5a5a90e7d72f45d2b27788d1fd1585a` eingefroren. Umsetzung in
[PR #76](https://github.com/craexxn/ringdown-sr/pull/76), zunächst Draft;
technischer Prüfstand im [Fortsetzungsstand](representation_implementation_status.md).
Noch keine wissenschaftliche Ausführung, keine Erfolgs- oder Kostenbehauptung.

## Voraussetzungen und Vorbereitung

Nach ausdrücklich freigegebener Übernahme des Implementierungs-PRs auf Manjaro
im sauberen Repository arbeiten. Vorher erfolgreiche vollständige Ready-CI und
deren Head/Basis abgleichen. Die folgenden Befehle sind der separate
wissenschaftliche Ausführungsschritt; sie werden nicht in GitHub Actions gestartet.

```bash
git switch main
git pull --ff-only
git status --short
git rev-parse HEAD
git cat-file -e 5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4^{commit}
git cat-file -e b00fc4a0a5a5a90e7d72f45d2b27788d1fd1585a^{commit}
uv sync --locked --dev --python 3.12.14
uv run --locked python scripts/run_python.py scripts/check_environment.py
```

`git status --short` muss leer sein. Der tatsächliche Commit wird gespeichert;
ein vorgesehener Commit ersetzt keine Herkunft. In einem flachen Klon fehlende
Historie zuvor mit dem üblichen authentifizierten Git-Zugriff holen. Keine
fremden Worktrees oder aktiven Julia-/CondaPkg-Sperren entfernen. Der Lauf
erstellt einen eigenen temporären Worktree des unveränderten Staffelworkers.
Abhängigkeitssperrdateien müssen zwischen ihm und dem aktuellen Projekt gleich
sein. System-, Bibliotheks-, Architektur- und Threadoptionen werden geprüft.

## Wissenschaftlicher Aufruf

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_global_restarts.py run \
  --output results/global-restarts-manjaro-001
```

Nur auf Manjaro zulässig. Der neue Ausgabeordner darf nicht existieren;
keine Überschreibung und kein Resume. Vier Blöcke, 20 geplante frische Suchen,
1.800 Sekunden je Worker, insgesamt 43.200 Sekunden einschließlich Vor-/Nachlauf.
Alle Seed-/Optionsprüfungen und das Zusatzraster werden vor dem ersten Fit
gespeichert. Jeder 500er-Referenzlauf ist zugleich Mitglied 0 seines Viererpakets.
Kein vorzeitiger Stopp aufgrund guter Ergebnisse und keine automatische
Ersatzsuche. Abbruchgrenzen sind keine Laufzeitprognose.

Erwartete Artefakte:

- `preparation.json`, `prepared_bindings.json`: Protokoll, Quellen, tatsächlicher
  Commit, Versionen und vollständige vorab gebundene Eingaben/Optionen.
- `anchor.npz`, `irregular.npz`: konkrete Trainings-/Zwischen- und Zusatzpunkte;
  das Zusatzraster ist ausschließlich diagnostisch.
- `request-01.json` bis `request-20.json`, `cell-01/` bis `cell-20/`:
  Originalfronten, native Optionen, RNG-Nachweise, Replays, Laufzeiten,
  Funktionsaufrufe, Protokolle und gegebenenfalls Fehler-/Teilstände.
- `run_state.json`: alle geplanten Zellen einschließlich Ausfällen/Abbrüchen.
- `completion/assessment_report.json`, `assessment_summary.md`,
  `assessment_checksums.json`, `raw_checksums.json`: abschließend freigegebene
  Auswertung und vollständige Bindung aller Rohdateien.

Ein vollständiger Abschluss verlangt `status=completed` im Abschlussbericht,
passende Prüfsummen und **keine** Datei `completion/ASSESSMENT_LOCKED`.
`run_state.json` oder ein einzelner erfolgreicher Worker genügt nicht.
Gewöhnliche Fitfehler zählen zum geplanten Umfang; unbekannte Kosten bleiben
unbekannt. Integritätsfehler, Signal oder Gesamtfrist sperren die Freigabe.
Teilausgaben bewahren und Ursache prüfen; keinen Erfolgsmarker von Hand setzen.

Die Fehlerklassifikation akzeptiert ausschließlich erkennbare numerische oder
Ressourcenfehler (Python: `FloatingPointError`, `OverflowError`,
`ZeroDivisionError`, `MemoryError`; direkt gemeldete native Julia-Fehler:
`DomainError`, `OverflowError`, `OutOfMemoryError`, `InexactError`). Unbekannte
Fitfehler werden konservativ als Gesamtabbruch behandelt; die Phase `fit` allein
ist kein Beleg für einen gewöhnlichen Suchausfall. Aufrufwächter, Unterbrechungen
und Signalbeendigungen dürfen keine vollständige Auswertung freigeben. Bei
Ausfällen werden Eltern- und tatsächlich aufgezeichnete Worker-Herkunft sowie
Adapterquellen an die Vorbereitung gebunden. Ab Fitbeginn sind beide Workerbelege
erforderlich; bei früherem Sicherheitsabbruch darf noch nicht erzeugte Evidenz
fehlen, vorhandene Widersprüche bleiben in jeder Phase unzulässig.

## Anschließend ausschließlich lesend verifizieren

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_global_restarts.py verify \
  results/global-restarts-manjaro-001 \
  --output results/global-restarts-manjaro-001-verification
```

Der getrennte Export prüft Rohinventar, Vorbereitung, eingefrorene Punkte,
Originalauswahl, Quellenbindungen, gespeicherte native Nachweise und alle aktuellen
Bewertungen. Vorhersagen und Verlustnachweise werden mit den vorhandenen
Python-/MPFR-Regeln nachgerechnet; es entstehen keine neuen nativen Vorhersagen.
Er startet keine Suche und verändert das Originalverzeichnis nicht.
Die gebundenen Quellbytes müssen mit dem Ausführungsstand übereinstimmen;
bei später geänderter Software den gespeicherten Ausführungscommit in einem
separaten sauberen Worktree verwenden. Verifikation hat eine eigene Sperrdatei,
Prüfsummen und einen Abschlussbericht mit `search_calls=0`.

```bash
tar -czf results/global-restarts-manjaro-001.tar.gz \
  -C results global-restarts-manjaro-001 global-restarts-manjaro-001-verification
sha256sum results/global-restarts-manjaro-001.tar.gz
```

Vor dem Packen darf dieser Archivname noch nicht existieren. Ein bestehendes
Originalarchiv niemals ersetzen. Danach unveränderte Datei im gemeinsamen
Archivordner und auf dem unabhängigen Sicherungsziel ablegen, beide Kopien am
SHA-256 prüfen und tatsächlichen Commit, Abschluss, Archivhash und Sicherung
im [Ergebnisindex](results_index.md) ergänzen. Releases/Uploads sind optional.

## Technische Integration

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/check_global_restarts.py \
  --output results/global-restarts-technical-001
```

Ausschließlich acht Punkte `y=1+t`, Seed 73, äußere Budgets 2, 3, erneut 2.
Dieselbe Vorbereitung, Quellenbindung, Freigabe und lesende Nachprüfung; die
wiederholte Front muss gleich sein. Kein wissenschaftlicher Probelauf und
kein Ersatz für die vollständigen übrigen technischen Checks.
