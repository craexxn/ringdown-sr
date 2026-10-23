# Zwei lokale Wiederholungen mit eingefrorenen SR-Eingaben

Stand: 23.10.2026. Das Skript `scripts/repeat_symbolic_arm.py` führt einen
vorhandenen erfolgreichen SR-Arm zweimal über den bestehenden Suchadapter
aus. Jeder Lauf erhält einen eigenen neuen Workerprozess und Ausgabeordner.
Es gibt keine neue Datenerzeugung oder Kovarianzschätzung und keine Änderung
von Seed, Budget, Suchgrammatik oder Threadlimits.

Ziel ist eine erste Prüfung lokaler Wiederholbarkeit. Die ursprünglichen
Manjaro-/WSL2-Snapshots enthielten bereits geringfügig unterschiedliche
Messdaten. Sie isolieren deshalb keinen reinen Rechnerwechsel bei bitgleichen
Eingaben. Auch bei zwei identischen lokalen Wiederholungen wäre eine
rechnerübergreifend identische Suche noch nicht belegt.

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
