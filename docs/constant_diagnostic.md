# Bedienung der begrenzten Konstantendiagnose

Der [angenommene und eingefrorene Plan](constant_diagnostic_plan.md) legt
48 Backendaufrufe und eine Stunde Gesamtwandzeit fest. Vorgegebener Baum und
wahrheitsnahe Starts sind privilegierte Methodenentwicklung. Die Diagnose
liefert keinen Nachweis freier Strukturentdeckung oder physikalischer Eindeutigkeit.

## Technische Prüfung und wissenschaftliche Ausführung

`check_constant_diagnostic.py` führt zehn reine Referenz-/Einheiten-/Aliasprüfungen
sowie vier direkte und zwei isolierte Optimierungen eines gesonderten
Achtpunkt-Signals aus. Sie prüfen unter anderem unveränderte Ergebnisse und
RNG-Endzustände bei eingeschalteter Beobachtung sowie den realen Export und
Elternprozess-Verifier. Keine der 48 wissenschaftlichen Zellen wird hierbei
optimiert. Diese Prüfung gehört zur vollständigen CI.

Die wissenschaftliche Serie erst auf Manjaro am sauber ausgecheckten, geprüften
Implementierungscommit ausführen. Den Commit nach Merge beziehungsweise Prüfung
explizit festhalten. Das Originalarchiv der abgeschlossenen Kontrollserie muss
lokal vorliegen; nur die beiden NPZ-Eingabedateien werden lesend daraus übernommen.
Der Launcher prüft zuerst den festen Archivhash und die bekannten Arraybits.
Dateien aus dem Archiv werden nicht als Code geladen.

Aus dem Projektordner, zsh-kompatibel, bei möglicherweise fremdem Virtualenv:

```bash
sha256sum results/representation-manjaro-001.tar.gz
git status --short --branch
git rev-parse HEAD
env -u VIRTUAL_ENV uv sync --locked --dev
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_constant_diagnostic.py --archive results/representation-manjaro-001.tar.gz --output results/constant-manjaro-001
```

Erwarteter Archivhash:
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
`results/constant-manjaro-001` muss neu sein; vorhandene Verzeichnisse werden
abgelehnt. Der Prozess startet Julia ausschließlich über `scripts/run_python.py`.
Haswell und Threadlimit 1 werden für die wirklich geladenen Bibliotheken vor
und nach jedem Worker geprüft. Diese Einstellungen sind auf diesen Pfad begrenzt.
Proxy und TLS-Prüfung bleiben erhalten. Cloud-Startdetails stehen im
[Fortsetzungsstand](representation_implementation_status.md).

## Artefakte und Abbruch

- `plan.md`, `diagnostic.npz`: eingefrorener Plan und binär gesicherte Datenrollen.
  Jeder Worker erhält ausschließlich Trainingszeiten und Beobachtungen.
- `runtime/`: überprüfte Kopien des Workers und der vier nativen Dateien.
- `controls-20/`, `controls-100/`: je fünf reine Kontrollen sowie native
  Options-/Plugin- und absolute Xoshiro-Referenzen; keine Optimierung.
- `call-01/` bis `call-48/`: Anfrage, Trainingsdaten, Manifest, Prozesslog und
  vollständiger Export. Start-/Rückgabebaum behalten die explizite Phase.
- `report.json`: Einzelbefunde, Status, Provenienz und bei vollständigem,
  abschließend geprüftem Lauf die 24 Differenzen 100 minus 20 und L/R-Zähler.
- `checksums.json`: abschließende Dateiprüfsummen des erhaltenen Teil-/Vollstands.

Die finale Verifikation vergleicht Quellen, Originalarchiv und die vor dem
Konsum beziehungsweise direkt nach Verifikation eingefrorenen Dateihashes.
Ein konsistent neu gehashtes, später verändertes Artefakt wird dadurch nicht
akzeptiert. Jeder technische Fehler sperrt alle Gruppen- und Paaraussagen.
Teilstände und Einzelresultate bleiben lesbar. Es gibt keine automatische
Fortsetzung, Ersatzstarts oder Wiederholungen.

Die Optimiererbeobachtung kopiert Zustandswerte und liefert immer `false`;
die RNG-Hülle delegiert jede normale Vektorziehung genau einmal. Die nativen
Optionen werden vollständig gegen den bestehenden Baselineprototyp geprüft,
einschließlich aller Optimierereinstellungen und konkreten Pluginfelder.
Die vorgesehenen Wrapper und beim zweiten Profil die Iterationszahl sind die
einzigen Ausnahmen. Je Paar müssen Anfangs-/Endzustand und wirkliche Restart-
vektoren den absoluten Vorprüfungsreferenzen entsprechen.

`fit_callback_count` zählt ausschließlich den eigentlichen Backendaufruf;
`total_callback_count` enthält zusätzlich die PopMember-Erstauswertung und den
abschließenden Verlustreplay. Der Backend-Evaluationszähler bleibt gesondert.
`optimization_seconds` misst den nativen Optimiereraufruf; Serienwandzeit enthält
auch Starts, JIT, Export und Prüfungen und ist kein reproduzierter Benchmark.

Der Backendpfad exportiert keine abschließenden lokalen Optim-Resultate.
Deshalb bleiben Konvergenz-/Abbruchstatus `unavailable`. Beobachtete Schritte,
Gradienten und Verluste werden gespeichert; daraus wird kein bestätigtes
Iterationslimit erfunden. Nichtendliche Beobachtungswerte behalten ihre
Float64-Hexdarstellung. Schlechte Fits sind fachliche Ergebnisse.
Parameterbefunde verwenden die bisherigen Replays; physikalische Identifikation
bleibt `not_assessed`, einschließlich des bekannten Blindflecks bei `8*fs`.
