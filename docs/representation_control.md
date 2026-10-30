# Getrennter Kontrollpfad für Zeitdarstellung und Komplexitätshäufigkeiten

Die Implementierung setzt den eingefrorenen
[Methodenplan](search_representation_plan.md) um. Der aktuelle Prüf- und
Fortsetzungsstand steht in [der Fortsetzungsdatei](representation_implementation_status.md).
Geprüfte Software, technische Referenzläufe und wissenschaftliche Ausführung
sind getrennte Stände. Im Implementierungsauftrag wird die Neun-Zellen-Serie
nicht gestartet; sie ist für den Manjaro-Referenzrechner am geprüften Commit
vorgesehen. Kein automatischer Merge und keine automatische Profilwahl.

## Ablauf und Prüfgrenzen

`run_representation_control.py` legt einen neuen exklusiven Ausgabeordner an.
Die drei Bedingungen sind `baseline`, `time_stretch` mit `u=32*t` und
`complexity_frequency` mit beiden Schaltern aktiv. Die neun Zellen, Seeds,
200 Iterationen und zyklische Reihenfolge stammen ausschließlich aus dem
Plan. Es gibt keine CLI-Option für andere Budgets, Seeds oder Kombinationen.

Vor der ersten Zelle starten im gepinnten Launcher zwei getrennte Prüfungen:

- Neun echte Optionsobjekte mit den aus PySR 2.6.0 abgeleiteten Backendseeds;
  kein Fit, kein Callback und keine Optimierung. Alle gemeinsamen Verträge,
  konkrete Pluginfelder und die beiden geplanten Schalterunterschiede werden
  geprüft. Das Pluginfeld bleibt vollständig gespeichert.
- Neun feste Referenzbäume: drei Bedingungen mit 250, 4346 und 33018 Hz.
  Geprüft werden beide Sekundenkoordinaten, Beobachtungsbits, 11 Knoten,
  tatsächliche Backendverluste, unabhängige Residuen-MSE, Einheiten,
  Parameter- und Aliasrückrechnung sowie der Alias-Blindfleck des Achtelrasters
  bei `8*fs`. Ein falscher Backendseed muss vor der Verlustauswertung scheitern.

Jede Suchzelle startet anschließend einen frischen Prozess über den bestehenden
Launcher und Prozessgruppen-Abbruchpfad. An die Suche gehen nur die jeweilige
Zeitkoordinate, unveränderte Beobachtungen, das feste Budget und die eng
begrenzte Profilkennung. Wahrheit, Referenzbäume und Zwischenpunkte werden
nicht als Suchdaten, Startwerte oder Auswahlhilfe übergeben.

Ein Manifest verknüpft Quellen, Laufzeitkopien, Eingabedateien und Profil.
Der Worker prüft es vor und nach der Ausführung. Julia-Verifikationsdatei,
Profilworker, numerischer Callback, Optionen, Plugins und konkrete Seeds
werden zusätzlich gegen die Vorprüfung und die konsumierten Bytes geprüft.
Haswell und Threadlimit 1 werden an den tatsächlich geladenen NumPy-, SciPy-
und Julia-Pools bestätigt. Allgemeine Suchpfade behalten ihre Vorgaben.

Alle exportierten Kandidaten bleiben in Originalreihenfolge erhalten.
Residuen und gewöhnliche Trainings-MSE werden für jeden Kandidaten geprüft;
auch der ursprüngliche Auswahlindex muss der unveränderten Auswahlregel
entsprechen. Widersprüche führen zum Abbruch. Es gibt keine Ersatzwahl.
Suchdiagnosen und physikalische Diagnosen stehen getrennt im Bericht.
Kurven verwenden den vollständigen Baum `q(alpha*t)`; Frequenzen und Raten
werden mit alpha multipliziert, Abklingzeiten durch alpha geteilt.
Fehlende oder fehlgeschlagene Replays verhindern positive Parametermarker.

## Technische Prüfungen

Aus dem sauberen Projektcheckout mit eingerichteter gesperrter Umgebung:

```bash
env -u VIRTUAL_ENV uv run --locked pytest -q
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_python.py scripts/check_representation_backend.py --output results/representation-options-001.json
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_python.py scripts/check_representation_references.py --output results/representation-references-001.json
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/check_representation_integration.py --output results/representation-technical-001
```

Der letzte Befehl umfasst die beiden Vorprüfungen und drei isolierte technische
Worker mit je zwei Iterationen an `y=1+t`. Er führt keine Zelle der
wissenschaftlichen Serie aus. Bei gemeinsamem Ausführen genügt der letzte
Befehl für diese Integration; die Einzelbefehle dienen gezielter Fehlerdiagnose.
Ein direkter Aufruf von `run_representation_worker.py` aus `scripts/` ist
kein Suchbefehl: Er benötigt das Manifest und die benachbarten Laufzeitkopien.

## Spätere wissenschaftliche Ausführung auf Manjaro

Erst am geprüften, vom Nutzer übernommenen Commit, aus dem Projektordner:

```bash
git status --short --branch
git rev-parse HEAD
env -u VIRTUAL_ENV uv sync --locked --dev --python 3.12.14
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_representation_control.py --label manjaro --output results/representation-manjaro-001
```

Vorhandene Ausgabeordner werden abgelehnt. Ein Infrastrukturfehler oder eine
Unterbrechung beendet die Serie; übrige Zellen bleiben `planned`.
Teilstände, Originalexporte und Fehlergründe werden erhalten. Der Treiber
setzt nicht automatisch fort und wiederholt keine Zelle. Über einen neuen
wissenschaftlichen Lauf ist nach Prüfung des Abbruchgrundes ausdrücklich
zu entscheiden; ein neuer Ordner allein ist keine methodische Freigabe.

## Artefakte und Interpretation

- `plan.md`, `training.npz`, `diagnostic.npz` und drei Bedingungsdateien halten
  den Plan, physikalische Daten und abgeleitete Suchkoordinaten fest.
- `runtime/` enthält die überprüften Laufzeitkopien. `preflight.json` und
  `references.json` enthalten die vorangestellten Backendnachweise.
- `cell-01/` bis `cell-09/` entstehen bei Start der jeweiligen Zelle und
  enthalten unveränderte Workerexporte, Manifest, native Verifikation und Logs.
  Alle neun geplanten Zustände stehen von Beginn an in `report.json`.
- `report.json` enthält separate Such-/physikalische Kandidatendiagnosen,
  Originalauswahl, Callbackzahlen während Fit und insgesamt, Zeiten,
  Quellherkunft, Bedingungsstatistik und Differenzen zur frischen Baseline
  desselben Seeds. `summary.md` bietet einen lesbaren Einstieg.
- `metadata.json` hält die abschließenden Artefaktprüfsummen fest.

Quellen, eingefrorene Daten und konsumierte Workerdateien werden abschließend
noch einmal geprüft. Bis dahin bleiben Zusammenfassungen und Seed-Differenzen
gesperrt. Ein Fehler dieser Abschlussprüfung sperrt alle Gruppen, auch wenn
deren Zellen zuvor vollständig waren. Erst bei bestandener Abschlussprüfung
bekommen vollständige Dreiergruppen deskriptive Minima/Mediane/Maxima mit
sichtbaren endlichen Nennern. Fehlende Paarwerte bleiben null mit Grund.
Die Differenz ist Variante minus Baseline; negative Fehlerdifferenzen bedeuten
eine Verbesserung. Callbackzahlen und Zeiten beschreiben Aufwand.

Prüfsummen belegen Konsistenz, keine externe Authentizität. Lokale Ausgaben
unter `results/` sind nicht versioniert und müssen separat gesichert werden.
Kurvengüte, Strukturerkennung und Parameterbefund sind getrennte Aussagen;
`physical_identification` bleibt `not_assessed`. Weder drei Entwicklungsseeds
noch passende Aliasreplays begründen eine Leistungs- oder Identifikationsstudie.

## Cloud-Startprofil

Für die ausgewählte Cloudinstanz gelten beschreibbare Cache-/Depotpfade:

```bash
export UV_CACHE_DIR=/workspace/.cache/uv
export XDG_CACHE_HOME=/workspace/.cache
export MPLCONFIGDIR=/workspace/.cache/matplotlib
export MPLBACKEND=Agg
export JULIA_DEPOT_PATH=/workspace/.cache/julia
export JULIA_NUM_PRECOMPILE_TASKS=2
export JULIA_PYTHONCALL_LIB="$(env -u VIRTUAL_ENV uv run --locked python -c 'import sys, sysconfig; from pathlib import Path; p = Path(sys.base_prefix) / "lib" / sysconfig.get_config_var("LDLIBRARY"); assert p.is_file(), p; print(p)')"
test -f "$JULIA_PYTHONCALL_LIB"
```

Diese Variablen müssen auch in nachfolgenden Befehlen und Kindprozessen
vorliegen. Die Bibliothek wird aus dem tatsächlichen Projektinterpreter
ermittelt; ein alter absoluter Pfad oder `LIBDIR=/install/lib` genügt nicht.
Proxy und TLS-Prüfung bleiben aktiv. Haswell ist ausschließlich Teil der
benannten Kontrollbefehle, kein globales Cloudprofil. Die lokale Startdatei
einer früheren Instanz ist nicht vorauszusetzen.
