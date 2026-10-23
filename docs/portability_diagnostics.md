# Diagnose bestehender SR-Portabilitätsläufe

Stand: 23.10.2026. Auf Manjaro und WSL2 liefen die Schema-3-Beispiele am
sauberen Referenzcommit `6ed493d` erfolgreich, mit unterschiedlichen
SR-Kandidatenzahlen und Verlusten. Das [Protokoll](portability.md) hält
die übermittelten Nachweise und ihre Grenzen fest. Die Ursache der
Unterschiede ist weiterhin offen.

`scripts/diagnose_symbolic_pilot.py` liest vorhandene Ergebnisse und
erzeugt transportable Diagnosepakete sowie beschreibende Vergleiche.
Es importiert ausschließlich Standardbibliothek und NumPy. Keine Suche,
Julia-Initialisierung oder neue Datenerzeugung wird gestartet. Die
gespeicherten Quelldateien bleiben unverändert.

## Export auf beiden Rechnern

Mit einem Checkout, der das Werkzeug enthält:

```bash
uv run --locked python scripts/diagnose_symbolic_pilot.py export /pfad/zum/pruefprojekt/results/sr-portability-001 --label manjaro --output results/diagnostics-manjaro-001
```

Unter WSL2 entsprechend `--label wsl2 --output results/diagnostics-wsl2-001`
verwenden. Der Eingabeordner enthält `white/` und `ar1/` aus dem damaligen
Vollprofil; er muss nicht neu erzeugt werden. Das Werkzeug akzeptiert nur
abgeschlossene erfolgreiche Schema-3-Läufe. Ausgabeordner müssen neu sein
und außerhalb des Eingabeordners liegen.

Im bisherigen Prüf-Worktree kann das einzelne Skript aus dem neuen Branch
temporär außerhalb des Projekts bereitgestellt werden. Damit bleibt der
Checkout bei `6ed493d`. Im Prüfprojekt zuerst `diagnostic_label=manjaro`
beziehungsweise `diagnostic_label=wsl2` setzen und dann:

```bash
git fetch origin &&
diagnostic_script=$(mktemp "${TMPDIR:-/tmp}/ringdown-diagnostics-XXXXXX.py") &&
git show origin/codex/symbolic-portability-diagnostics:scripts/diagnose_symbolic_pilot.py > "$diagnostic_script" &&
env -u VIRTUAL_ENV uv run --locked python "$diagnostic_script" export results/sr-portability-001 --label "$diagnostic_label" --output "results/diagnostics-$diagnostic_label-001"
```

Der Branch bezeichnet hier die Bereitstellung des Diagnosewerkzeugs,
nicht den Codezustand des ursprünglichen Suchlaufs. Die Datei-Prüfsumme
des tatsächlich ausgeführten Skripts wird im Diagnosebericht gespeichert.

## Inhalt und Zuordnung

| Datei | Inhalt |
| --- | --- |
| `report.json` | Quellen-Prüfsummen, Konfiguration, alte Herkunftsaufnahmen, Zufallsaufzeichnungen, Optionen, Fronten und gemeldete Umgebungen |
| `arrays.npz` | Verlustfreie Float64-Snapshots von gemeinsamen Eingaben, Hintergrundfenstern, tatsächlichen Armeingaben und ausgewählter Vorhersage/Residuum |
| `checksums.json` | SHA-256 der beiden abgeschlossenen Dateien |

Das Berichtsformat heißt `ringdown-sr-portability-diagnostics-1`. Die
Ergebnisarrays werden bei der Snapshot-Bildung ausschließlich in
zusammenhängende Little-Endian-Float64-Darstellung gebracht. Es gibt keine
Amplitudenskalierung oder Präzisionsreduktion. Form, kanonischer Datentyp
und Datenhash werden je Array gespeichert; ein anderer Byte-Order allein
ändert den kanonischen Hash nicht. Verschiedene Vorzeichen von null bleiben
in den Bits sichtbar.

Jede konsumierte Quelldatei wird gegen das vorhandene Wurzelmanifest
`metadata.json.artifact_sha256` geprüft. Für `metadata.json` selbst wird
ihre gelesene Datei-Prüfsumme festgehalten, da sie nicht im eigenen Manifest
steht. Die tatsächlichen Arm-Eingaben werden zusätzlich bitgenau gegen
die gemeinsamen Eingaben geprüft. Dieses Werkzeug ersetzt nicht den
wissenschaftlichen Verlust-Audit: Es rechnet weder alle Verluste noch
die Alpha-Auswahl neu und liest nicht sämtliche übrigen Suchartefakte.
Prüfsummen belegen Konsistenz mit dem vorliegenden Manifest, keine
unabhängige Authentizität der ursprünglich übermittelten Dateien.

`recorded_environment` stammt ausschließlich aus den alten Metadaten.
Die nach der Suche ergänzte Worker-Umgebung bleibt von der Aufnahme vor
`fit` getrennt. Auch die alten Git-/Quellaufnahmen werden nicht durch den
heutigen Checkout ersetzt. Ein ursprünglicher schmutziger Codezustand
wird als solcher erhalten; der Export erklärt ihn nicht nachträglich
für sauber. Unter `exporter` stehen separat Datum, Skript-Prüfsumme sowie
Python-/NumPy-Version des heutigen Exportprozesses. Diese Versionen
beschreiben nicht die ursprüngliche Suchumgebung.

Die numerischen Build-/Threadpool-Aufnahmen sind die damals tatsächlich
gespeicherten Diagnosen. Explizite Julia-CPU-Target-/Build-/BLAS-Konfiguration
und vollständige Julia-RNG-Checkpoints wurden nicht zusätzlich aufgezeichnet.
Die vorhandenen Threadpool-Daten können Informationen zu geladenen
Bibliotheken enthalten, ersetzen aber keine vollständige Julia-Konfiguration.
Fehlende Informationen werden nicht aus dem heutigen Rechner rekonstruiert.

## Vergleich und Einordnung

Wenn beide Pakete auf einem Rechner verfügbar sind:

```bash
uv run --locked python scripts/diagnose_symbolic_pilot.py compare results/diagnostics-manjaro-001 results/diagnostics-wsl2-001 --output results/diagnostics-comparison-001.json
```

Auch der Vergleich ist lesend; seine Ausgabedatei muss neu sein und
außerhalb beider Pakete liegen. Beide Pakete und ihre Arraybeschreibungen
werden vor dem Vergleich auf Konsistenz geprüft.

Der Bericht trennt Formen, Bitgleichheit und numerische Gleichheit. Er
nennt die Zahl unterschiedlicher Float64-Bitmuster und Zahlenwerte,
maximale absolute Abweichung sowie die Abweichung relativ zur gemeinsamen
Maximalamplitude ohne feste Untergrenze. Ein einzelner darstellbarer
Unterschied bei `1e-21` bleibt dadurch erkennbar. Die absolute Differenz
wird direkt berechnet; eine Differenz außerhalb des Float64-Wertebereichs
erhält `null` mit Status `exceeds_float64_range`, während der skalierte
Vergleich endlich bleibt. Sehr kleine normierte Differenzen können bei
extremer Dynamik unterlaufen; Bit- und Wertvergleich bleiben davon getrennt.
Es wird keine wissenschaftliche Toleranzschwelle oder Gleichwertigkeit
der Ergebnisse festgelegt.

Konfiguration, Hintergrund-RNG-Aufzeichnungen, Python-/Backend-Seeds,
Aufträge, Quellaufnahmen, gemeldete Umgebungen und Fronten werden getrennt
verglichen. `output_directory` wird für Python-Parameter und Backendoptionen
gesondert als operativer Pfadunterschied ausgewiesen. Alle anderen Felder
bleiben im Vergleich erhalten. Julia-Backendoptionen sind exportierte
Typ-/Wertdarstellungen: Unterschiedliche Darstellungen sind ein
Prüfhinweis, kein Beweis unterschiedlicher Semantik; gleiche Darstellungen
beweisen keine identische Laufzeitimplementierung. Eine spätere manuelle
Einordnung bleibt erforderlich.

Der Vergleich kann zeigen, ob bereits Eingaben oder dokumentierte Seeds
abweichen, oder ob trotz gleicher gespeicherter Eingaben und Vorgaben
andere Fronten entstanden sind. Keine dieser Beobachtungen allein belegt
eine Ursache. Insbesondere werden weder kleine Gleitkommadifferenzen noch
ein Betriebsystemwechsel automatisch als Erklärung festgelegt.

Die drei Dateien eines Diagnosepakets gemeinsam sichern bzw. übertragen.
Die vollständigen ursprünglichen Ergebnisordner und vorhandenen
Terminalprotokolle zusätzlich behalten; das kleine Paket ersetzt sie nicht.
