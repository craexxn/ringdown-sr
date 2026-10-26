# Zwei lokale Wiederholungen mit eingefrorenen SR-Eingaben

Ursprünglicher Ablauf: 23.10.2026; ergänzter Prüfstand: 26.10.2026.
Das Skript `scripts/repeat_symbolic_arm.py` führt einen
vorhandenen erfolgreichen SR-Arm zweimal über den bestehenden Suchadapter
aus. Jeder Lauf erhält einen eigenen neuen Workerprozess und Ausgabeordner.
Es gibt keine neue Datenerzeugung oder Kovarianzschätzung und keine Änderung
von Seed, Budget, Suchgrammatik oder Threadlimits.

Ziel ist eine erste Prüfung lokaler Wiederholbarkeit. Die ursprünglichen
Manjaro-/WSL2-Snapshots enthielten bereits geringfügig unterschiedliche
Messdaten. Sie isolieren deshalb keinen reinen Rechnerwechsel bei bitgleichen
Eingaben. Auch bei zwei identischen lokalen Wiederholungen wäre eine
rechnerübergreifend identische Suche noch nicht belegt. Inzwischen wurden
identische Eingaben und die optionale Haswell-Kontrolle auf beiden Geräten
geprüft: Der [gemeinsame Befund](symbolic_core_results.md) dokumentiert vier
übereinstimmende freie Fronten und die Grenzen dieses einzelnen Kontrollfalls.

## Ausführung am bisherigen Referenzcheckout

Zunächst wird der gewöhnliche Weißrauscharm verwendet. Der Quellordner muss
die vollständige ursprüngliche Armausgabe enthalten, einschließlich
`inputs.npz`, `request.json`, Metadaten, Ergebnissen und Prüfmanifest.
Das kleine Portabilitäts-Diagnosepaket allein reicht dafür nicht aus.

Im bisherigen Worktree am Referenzcommit `6ed493d` kann nur das neue Skript
außerhalb des Checkouts bereitgestellt werden. Der Projektstand bleibt
dadurch erhalten. Aus diesem Projektordner im WSL-Terminal:

```bash
git fetch origin &&
repetition_script=$(mktemp "${TMPDIR:-/tmp}/ringdown-repeat-XXXXXX.py") &&
git show origin/codex/symbolic-repeatability-check:scripts/repeat_symbolic_arm.py > "$repetition_script" &&
env -u VIRTUAL_ENV uv run --locked python "$repetition_script" \
  results/sr-portability-001/white/symbolic/ordinary \
  --label wsl2 \
  --output results/sr-repeatability-wsl2-001
```

Ein neuer Ausgabeordner ist erforderlich. Existierende Ausgaben werden
abgelehnt; bei einer weiteren Wiederholung einen neuen Namen wählen.
Die beiden Suchen werden nacheinander gestartet. Gegenüber dem bisherigen
Arm wird dessen vollständiges Budget übernommen, kein verkürztes Testbudget.
Während der Ausführung den Checkout und die Umgebung unverändert lassen.

Für die Weitergabe des Ergebnisses nach erfolgreichem Abschluss:

```bash
tar -czf results/sr-repeatability-wsl2-001.tar.gz \
  -C results sr-repeatability-wsl2-001
```

## Kontrollen und gespeicherte Daten

Vor der ersten Suche werden die tatsächlich konsumierten Quelldateien gegen
das vorhandene Prüfmanifest geprüft. Der alte Status muss erfolgreich sein,
Auftragsformat und Budget müssen passen. Die expliziten Suchvorgaben des
aktuellen Adapters müssen mit den gespeicherten PySR-Parametern übereinstimmen.
Weitere von PySR aufgezeichnete Standardparameter bleiben erhalten und werden
nach jedem Lauf ebenfalls gegen den ursprünglichen Parametersatz geprüft.
Nur `output_directory` ist als unvermeidbarer operativer Pfadunterschied
ausgenommen. Der Auftragsinhalt selbst bleibt vollständig gleich.

Zeitachse, Messdaten und gegebenenfalls Kovarianz werden aus genau den
geprüften NPZ-Bytes einmalig geladen, auf endliche Float64-Werte geprüft und
als schreibgeschützte Arrays an den Adapter übergeben. Der Adapter arbeitet
mit eigenen Kopien. Vor jedem Lauf und nach beiden Läufen wird zusätzlich
geprüft, dass die konsumierten Originaldateien unverändert geblieben sind.
Die tatsächlich geschriebenen Armeingaben werden über Form und Hash der
Little-Endian-Float64-Bitmuster mit dem eingefrorenen Eingang verglichen.
Auch positive und negative Null bleiben dabei unterscheidbar.

| Ausgabe | Inhalt |
| --- | --- |
| `source/` | Unveränderte Bytes der konsumierten ursprünglichen Eingabe-, Auftrags-, Ergebnis- und Metadatendateien samt ursprünglichem Manifest und Status |
| `driver.py` | Exakte Kopie des ausgeführten Wiederholungsskripts |
| `run-1/`, `run-2/` | Vollständige neue Suchausgaben des bestehenden Adapters einschließlich Eingaben, Ergebnissen, Workerlogs, Metadaten und Prüfsummen |
| `report.json` | Herkunft und Umgebung des Treibers, Skript-/Quelldateihashes, Budget, Arrayfingerprints, Fortschritt und abschließender Vergleich |

`source/` ist eine Sicherung der konsumierten Dateien, keine vollständige
Kopie aller ursprünglichen Suchartefakte. Dessen unverändertes Manifest kann
weitere Originaldateien nennen, die für diesen Test nicht kopiert werden.
Die ursprünglichen vollständigen Ergebnisordner deshalb weiterhin behalten.

Der Bericht wird vor dem ersten Workerstart geschrieben und nach jedem Lauf
ergänzt. Bei Fehlern oder Abbruch bleiben Bericht und vorhandene Teilresultate
erhalten. Das Format lautet `ringdown-sr-arm-repeatability-1`.

## Bedeutung des Vergleichs

Die vollständigen geordneten Fronten werden über exakte Baumdarstellung,
Komplexität, hexadezimale Float64-Verluste sowie Vorhersage-/Residualbits
verglichen. Eine identische Auswahl oder Kandidatenanzahl allein genügt
nicht. Zeitangaben, Laufzeiten und Anzeigetexte gehören nicht zur Frontsignatur.
Ausgabeordner werden nur für den Parameter-/Backendoptionsvergleich ausgenommen;
sonstige Felder bleiben erhalten. Backendoptionen werden anhand ihrer Namen
verglichen, nicht anhand der Reihenfolge der exportierten Felder.

Wichtige Felder unter `comparison`:

- `front_bitwise_equal`: beide vollständigen Frontsignaturen stimmen überein.
- `selected_index_equal`, `selected_prediction_bitwise_equal`: getrennte
  Angaben zur Auswahl und ihrer Kurve.
- `rng_records_equal`: dokumentierte Seeds/RNG-Angaben stimmen überein;
  dies ist weiterhin kein vollständiger Julia-RNG-Checkpoint.
- `code_records_equal`: Herkunft und Quellaufnahmen beider neuer Worker
  stimmen überein. Die vollständigen Numerikumgebungen stehen separat in
  deren Metadaten; gleiche Paketversionen sind keine identische Umgebung.
- `source_matches_first_signature`, `source_matches_second_signature`:
  gesonderter Vergleich mit der ursprünglichen Suche. Zwei neue Läufe
  können miteinander übereinstimmen und beide vom ursprünglichen abweichen.

Ein abgeschlossener Vergleich erhält `status=completed`, auch wenn eine
Übereinstimmung `false` lautet. Das ist ein beschreibender Befund, kein
Ausführungsfehler. Ein gescheiterter Worker oder eine verletzte Eingabe-/
Auftragskontrolle führt zu `status=failed` und einem Fehlerabbruch.

Aus zwei gleichen Fronten folgt weder allgemeine Deterministik noch
wissenschaftliche Rekonstruktionsleistung. Bei unterschiedlichen Fronten
werden nicht automatisch Threading oder Gleitkommaabweichungen als Ursache
festgelegt. Ein späterer Rechnervergleich benötigt dieselben eingefrorenen
Eingaben auf beiden Rechnern. Änderungen der Threadlimits wären eine
gesonderte Intervention, die hier noch nicht stattfindet.

## Prüfungen des Treibers

```bash
uv run --locked pytest -q tests/test_repeat_symbolic_arm.py
```

Diese Tests verwenden kontrollierte Workerantworten und prüfen unter anderem
unveränderte Eingangsdaten und Budgets, volle Kovarianzübergabe, winzige
Bitunterschiede, bewahrte Nullvorzeichen, Pfad-/Zeitunterschiede sowie
Prüfsummen-, Abbruch- und Fehlerfälle. Sie führen keine neuen freien Suchen
aus und sind kein Nachweis tatsächlicher lokaler Wiederholbarkeit. Dieser
Nachweis erfordert die beiden oben beschriebenen echten Läufe.

## Kontrollierte freie Suche mit gemeinsamem BLAS-Kern

Stand: 26.10.2026. Die [festen Diagnosen](fixed_numerics_probe.md) stimmen
unter gemeinsamem Haswell-Kern zwischen Manjaro und WSL2 bytegleich überein.
Nun wird ausschließlich der eingefrorene gewöhnliche Weißrausch-Arm zweimal
pro Rechner frei gesucht. Operatoren, Einheitenprüfung, Verlustfunktion,
Seed und vollständiges gespeichertes Suchbudget bleiben erhalten.
Die Rolle der exakten Wiederholbarkeit und die offene Entscheidung zum
späteren Forschungsprofil stehen im
[Entscheidungsvermerk](reproducibility_decisions.md).

Der optionale Aufruf ist:

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked --python 3.12.14 python "$repeat_tools/repeat_symbolic_arm.py" \
  results/sr-core-control-wsl2-001/haswell/source \
  --label wsl2 --require-openblas-core Haswell \
  --output results/sr-free-haswell-wsl2-001
```

Für den sauberen bisherigen Referenzcheckout `6ed493d` werden vorher genau
zwei Dateien aus demselben konkret festgehaltenen Werkzeugcommit in einen
neuen temporären Ordner `$repeat_tools` gestellt:
`scripts/repeat_symbolic_arm.py` und `scripts/probe_symbolic_numerics.py`.
Beide liegen dort nebeneinander. Der zweite Treiber stellt ausschließlich
seine bereits geprüften Umgebungs-/Poolprüfungen bereit; seine feste
Diagnosesuite wird nicht gestartet. Das Referenzcheckout wird nicht geändert.

Die Rechner verwenden folgende Pfade und neue Ergebnisnamen:

| Rechner | Eingabe relativ zum bisherigen Prüfprojekt | Ausgabe relativ zum Prüfprojekt |
| --- | --- | --- |
| WSL2 | `results/sr-core-control-wsl2-001/haswell/source` | `results/sr-free-haswell-wsl2-001` |
| Manjaro | `results/sr-core-control-manjaro-001/haswell/source` | `results/sr-free-haswell-manjaro-001` |

Diese `source/`-Ordner enthalten dieselben neun ursprünglichen Quelldateien,
keine neuen Haswell-Messdaten. Ihre Bitgleichheit zwischen den Geräten ist
im festen Kernvergleich bestätigt. Alle vorherigen vollständigen Ergebnisse
und Archive bleiben erhalten. Für weitere Versuche neue Ausgabe- und
Archivnamen verwenden; vorhandene Ausgaben werden nicht überschrieben.

### Wirkungskontrolle im tatsächlichen Suchworker

Vor dem ersten Worker prüft der Elternprozess die gesetzten Variablen sowie
die geladenen Python-BLAS-Pools. Der vorhandene Adapter startet weiterhin
einen frischen Prozess über seinen gepinnten Launcher und dieselbe
Prozessgruppen-/Abbruchbehandlung. Ausschließlich dessen Einstieg wird auf
die gesicherte Diagnosekopie `driver.py --worker` umgeleitet.

Dieser Einstieg ruft die bestehende `symbolic.worker`-Funktion unverändert
auf. Für die Dauer dieses Workeraufrufs wird ausschließlich die vorhandene
Python-Funktion `_environment_snapshot` beobachtend umschlossen. Sie liefert
dieselbe Umgebungsaufnahme an den Adapter zurück. Die tatsächlichen
Grenzen `before_fit` und `after_search` müssen besucht werden: geladenes
Julia, NumPy und SciPy müssen jeweils OpenBLAS/Haswell melden und alle
erfassten BLAS-/OpenMP-Pools Limit 1. Die Kontrolle setzt keine Limits zur
Laufzeit, zieht keine Zufallszahlen und verändert weder Modelle noch
Optimierer. Bei einer unpassenden Aufnahme vor `fit` beginnt die Suche nicht;
bei einem späteren Fehler bleiben Ergebnis und Fehlernachweise erhalten.
Der Umschlag der Snapshot-Funktion wird in jedem Fall wieder aufgehoben.

Die Aufnahmen und Ergebnisse der Kernprüfung stehen in
`run-N/blas_control.json`. Diese Datei wird vom bestehenden Worker mit
seinen übrigen Artefakten gehasht. Nach Rückkehr prüft der Elternprozess
die Kontrollprüfsumme, die aufgezeichneten tatsächlich geladenen Pools und
ihre Übereinstimmung mit den regulären Suchmetadaten erneut. Die Hashes
beider Diagnosequelldateien und unveränderte Code-/Adapterherkunft werden
ebenfalls kontrolliert. Nach einer erfolgreichen Suche erscheint:

```text
Verified OpenBLAS: Haswell for NumPy, SciPy and Julia; pool limits 1.
```

Der übergeordnete Bericht ergänzt `required_openblas_core`,
`control_initial`, `control_final`, `tool_source_sha256` und die beiden
Worker-Kontrollen. Neben `driver.py` wird die tatsächlich verwendete
Kontrollquelle `probe_symbolic_numerics.py` gesichert. Das zusätzliche
Wurzelmanifest `checksums.json` enthält alle erzeugten Dateien außer sich
selbst, auch bei einem Fehler nach Anlegen des Versuchs. Vorprüfungen
falscher Variablen oder Eingaben können schon vor dem Ausgabeordner abbrechen.

Der bisherige unkontrollierte Aufruf ohne das neue Argument bleibt erhalten
und benötigt keine weitere nebenliegende Datei. Es werden keine globalen
Umgebungsvariablen, Projektabhängigkeiten oder Pilotvorgaben geändert.

### Bewertung und technischer Nachweis

`status=completed` verlangt vollständig ausgeführte Suchen und bestandene
Integritäts-/Kernprüfungen. Es verlangt ausdrücklich keine identischen
Fronten. Der bisherige vollständige Signaturvergleich und die getrennten
Vergleiche zu den ursprünglichen, automatisch optimierten Läufen bleiben
erhalten. Zwei lokale Wiederholungen können mit sich selbst übereinstimmen
und von der ursprünglichen Quelle abweichen.

Die CI führt den kontrollierten Aufruf mit zwei echten frischen Julia-
Suchworkern auf dem bereits erzeugten kleinen Weißrausch-Kontrollarm aus.
Das prüft den tatsächlichen Aufrufpfad, die Wirkungskontrolle und Exporte.
Es ersetzt nicht die beiden Rechnerläufe mit dem unveränderten vollständigen
Budget. Die zusätzlichen Python-Tests prüfen insbesondere Ablehnung vor
der Suche, erhaltene Fehlernachweise, beidseitige Snapshot-Grenzen und die
Unabhängigkeit des Abschlussstatus von exakter Frontgleichheit.

Die beiden vollständigen Rechnerläufe sind inzwischen ausgeführt und an
ihren übermittelten Artefakten nachgerechnet. Ihre sieben Kandidaten pro
Lauf und vollständigen Fronten stimmen in allen vier Wiederholungen
überein. [Befund und Reviewumfang](symbolic_core_results.md) unterscheiden
diesen Nachweis vom kleinen CI-Aufruf und den vorherigen nativen Paketen.
