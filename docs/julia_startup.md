# Stabiler Start der festgelegten Python-/Julia-Umgebung

Stand: 21.10.2026. Technische Nachbesserung nach dem Review der
[Backend-Konstantenoptimierung](constant_optimization.md).
Die mathematischen Verfahren, Daten und Optimierervorgaben bleiben unverändert.

## Anlass und Änderung

Der bisherige Start rief `juliapkg.executable()` auf. Diese Funktion löst
auch Julia-Paketabhängigkeiten auf und kompiliert eine automatisch verwaltete
Umgebung. Anschließend wurde zusätzlich das versionierte Projekt unter
`julia/` instanziiert und automatisch vorkompiliert. Dabei konnten
PythonCall/CondaPkg eine weitere Python-Umgebung einrichten oder an deren
Sperre warten. Separate Vorkompilierungen meldeten Python-Bibliotheksfehler,
obwohl die folgenden eingebetteten Prüfungen teilweise bestanden.

`scripts/run_python.py` verwendet jetzt folgenden Ablauf:

1. Python-Version, exakten Julia-Pin und übereinstimmende
   JuliaCall-/PythonCall-Version prüfen.
2. Die Installation mit einer betriebssystemgestützten `FileLock`-Sperre
   im aktuellen Python-Präfix serialisieren.
3. Mit dem versionsgebundenen `juliapkg.find_julia.find_julia` ausschließlich
   das exakt passende Julia-Programm suchen oder installieren. Der frühere
   Standardpfad im Python-Präfix bleibt verwendbar; ein explizites
   `PYTHON_JULIAPKG_EXE` wird weiterhin berücksichtigt und anschließend geprüft.
4. Nur `julia/Project.toml` und `julia/Manifest.toml` mit
   `Pkg.instantiate(allow_autoprecomp=false, julia_version_strict=true)`
   bereitstellen. Es gibt keinen zusätzlichen Aufruf von `Pkg.add`,
   `Pkg.resolve` oder `Pkg.precompile`.
5. Vor dem Experiment kontrollieren, dass die beiden versionierten
   Julia-Dateien byteweise unverändert geblieben sind.
6. Die Installationssperre freigeben und Python mit den übergebenen
   Argumenten starten; seinen Rückgabecode weitergeben.

Für die Startvorgänge werden bestehende Eltern-Umgebungsvariablen kopiert.
Die folgenden Projektvorgaben gelten ausschließlich für die gestarteten
Prozesse und ändern keine globalen Einstellungen:

| Einstellung | Vorgabe |
| --- | --- |
| `PYTHON_JULIACALL_EXE` | Ermitteltes, exakt geprüftes Julia-Programm |
| `PYTHON_JULIACALL_PROJECT` | Absoluter Pfad zum versionierten Julia-Projekt |
| `PYTHON_JULIACALL_STARTUP_FILE` | `no` |
| `JULIA_PYTHONCALL_EXE` | Derselbe Python-Interpreter, der den Launcher ausführt |
| `JULIA_CONDAPKG_BACKEND` | `Null`: vorhandene Python-Umgebung verwenden |
| `JULIA_PKG_PRECOMPILE_AUTO` | `0`: keine automatische Paket-Vorkompilierung bei Paketoperationen |

Die reguläre Julia-Kompilierung beim tatsächlichen Import bleibt aktiv.
Sie erfolgt in der eingebetteten Python-/Julia-Umgebung und nutzt Julias
normalen Cache. CondaPkg bleibt eine transitive Julia-Abhängigkeit; dessen
Hilfsartefakte können beim Paketimport heruntergeladen werden. Das Null-
Backend verwaltet dabei keine zusätzliche Conda-Python-Umgebung.

Die bereits aufgelösten Python-Pakete `juliapkg==0.1.27` und
`filelock==3.32.7` sind nun direkte Abhängigkeiten. Die Suchschnittstelle
ist versionsgebunden. `uv` hat die Lockmetadaten aktualisiert; die
aufgelösten Paketversionen und das Julia-Manifest bleiben unverändert.

## Sperren und Fehlerverhalten

Auf eine belegte eigene Installationssperre wird höchstens 30 Sekunden
gewartet. Danach folgt eine klare Fehlermeldung mit dem Sperrpfad und dem
Hinweis, nach Abschluss des anderen Starts erneut zu versuchen. Die
Paketinstallation mit `Pkg.instantiate` erhält eine Grenze von 600 Sekunden.
Die erstmalige Suche beziehungsweise der Download des Julia-Programms
erfolgen davor über JuliaPkg. Ein laufendes Experiment hält die
Installationssperre nicht und erhält keine zusätzliche Zeitbegrenzung.

Bestehende `.CondaPkg`-Verzeichnisse und fremde Sperrdateien werden nicht
gelöscht. Das Null-Backend nutzt ihre Paketauflösung nicht. Auch eine
fehlgeschlagene Vorbereitung gibt die eigene Installationssperre frei.
Bei geänderten Julia-Metadaten startet kein Experiment; die Meldung fordert
zur Prüfung des Git-Diffs auf. Geänderte Dateien werden nicht zurückgesetzt.

## Prüfungen

Die zwölf neuen pytest-Fälle prüfen unter anderem Versionsabweichungen,
vollständige Argumentübergabe, Rückgabecode, lokale Umgebungsvariablen,
Metadatenänderungen, fehlgeschlagene Installation und begrenztes Warten
auf eine tatsächlich von einem anderen Prozess gehaltene OS-Sperre.

`scripts/check_environment.py` kontrolliert zusätzlich:

- Der Null-Backend-Vertrag ist gesetzt und bei geladenem CondaPkg aktiv.
- PythonCall verwendet denselben tatsächlichen Python-Interpreter.
- `SymbolicRegressionPythonCallExt` ist erfolgreich geladen.

`scripts/check_julia_startup.py` erstellt eine temporäre Kopie der
Umgebungsdateien und Startskripte. Ein separater Julia-Prozess hält dort
eine echte CondaPkg-PID-Sperre. Währenddessen starten zwei Launcher
gleichzeitig und führen den vollständigen Umgebungscheck aus. Beide
müssen erfolgreich sein; die fremde Sperre muss noch aktiv und byteweise
unverändert sein. Zusätzliche CondaPkg-Umgebungsdateien werden abgelehnt.
Der Prüfprozess schließt ausschließlich seine eigene temporäre Sperre.

Aus dem Projektordner:

```bash
uv run --locked pytest -q
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_environment.py
uv run --locked --python 3.12.14 python scripts/check_julia_startup.py
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_julia_loss.py
```

Der letzte Befehl prüft weiterhin die 283 Julia-Referenzen, zehn
Residualvergleiche und zwölf Optimierer-Nachrechnungen. Der GitHub-Workflow
führt alle Schritte aus. Eigene erneute Nutzerprüfungen auf Manjaro und
WSL2 stehen für diesen geänderten Startweg noch aus.

Versionsgebundene Primärquellen:

- [JuliaPkg 0.1.27: Paketauflösung und Vorkompilierung](https://github.com/JuliaPy/pyjuliapkg/blob/v0.1.27/src/juliapkg/deps.py)
- [PythonCall 0.9.36: Konfiguration mit vorhandenem Python](https://github.com/JuliaPy/PythonCall.jl/blob/v0.9.36/docs/src/pythoncall.md#configuration)
- [CondaPkg 0.2.36: Null-Backend und PID-Sperre](https://github.com/JuliaPy/CondaPkg.jl/blob/v0.2.36/src/resolve.jl)
