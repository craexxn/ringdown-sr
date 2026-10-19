# Konfigurierbarer Pilot mit Ergebnisexport

## Umfang und Start

Ein Aufruf verbindet Zeitachse, eine synthetische gedämpfte Schwingung,
weißes Gaußrauschen, den [klassischen Referenzfit](reference_fit.md) und
die Auswertung auf denselben Samples. Es wird eine einzelne Konfiguration
ausgeführt, kein Parameter-Raster und keine PySR-Suche. Die Vorgaben in
`configs/pilot_white.toml` sind ausschließlich ein technischer Kontrollfall.

Aus dem Projektordner im Linux-/WSL-Terminal:

```bash
uv run --locked ringdown-sr run configs/pilot_white.toml --output results/pilot-001
code -r results/pilot-001/plot.png
```

`--output` ist ausdrücklich erforderlich und bezeichnet einen **neuen**
Ordner. Auch ein vorhandener leerer Ordner, eine Datei oder ein Symlink
werden abgelehnt. Für eine Wiederholung einen anderen Namen wählen:

```bash
uv run --locked ringdown-sr run results/pilot-001/config.toml --output results/pilot-002
```

Relative Konfigurations- und Ausgabepfade beziehen sich auf das aktuelle
Arbeitsverzeichnis. Absolute Pfade funktionieren ebenfalls; persönliche
Pfade sind nicht im Code hinterlegt. Die direkte Python-API ist
`ringdown_sr.pilot.run_pilot(config_path, output_directory)`.
Dieser Aufruf benötigt weder Julia noch den Julia-Launcher.

## Konfiguration: Schema 1

TOML wird mit der Python-Standardbibliothek gelesen. Alle nachfolgenden
Felder sind erforderlich; es gibt keine impliziten wissenschaftlichen
Standardwerte. Unbekannte Felder, fehlende Angaben, doppelte TOML-Schlüssel,
ungültige Datentypen und nicht endliche Zahlen werden abgelehnt.

| Tabelle | Felder und Bedeutung |
|---|---|
| Wurzel | `schema_version = 1` |
| `sampling` | Ganzzahliges `n_samples >= 5`; positives `sample_rate_hz` in Hz |
| `signal` | Dimensionslose vorzeichenbehaftete `amplitude`; `frequency_hz` zwischen null einschließlich und Nyquist ausschließlich; positives `decay_time_s` in Sekunden; `phase_rad` in Radiant |
| `noise` | `kind = "gaussian_white"`; nicht negatives `standard_deviation` in Signaleinheiten; `bit_generator = "PCG64"`; ganzzahliger nicht negativer `seed` |
| `fit` | `weighting`; positive geordnete `frequency_bounds_hz` strikt unter Nyquist; positive geordnete `decay_time_bounds_s`; nicht leere Liste `initial_points` aus `(f, tau)`-Paaren strikt innerhalb der Grenzen; ganzzahliges `max_nfev >= 1` pro Start |

Zulässige Gewichtungen:

- `ordinary`: gewöhnliche Quadratsumme; auch `standard_deviation = 0`
  für einen rauschfreien Kontrollfall zulässig.
- `known_white`: bekannte Modellkovarianz `C = sigma^2 * I`, mit
  `sigma = noise.standard_deviation`. Die Varianz muss als strikt positive
  endliche `float64`-Zahl darstellbar sein. Sie wird **nicht** aus der
  Stichprobe geschätzt. Das ist ein Kontrollfall mit bekanntem Rauschmodell.

Die Signalwahrheit darf außerhalb der Fit-Grenzen liegen, um bewusst einen
unzutreffenden Suchbereich prüfen zu können. Grenzen und Startpunkte werden
nicht aus der Wahrheit abgeleitet oder korrigiert. Der Fit erhält nur
Zeitpunkte, verrauschte Messwerte, Fit-Einstellungen und optional `C`.

Die Samplezahl wird explizit angegeben. Es gilt `T = N/fs`, letzter
Abtastzeitpunkt `(N-1)/fs`. Es wird keine Zieldauer stillschweigend gerundet.
SNR-Konvention, Rauschpegel und Parameterbereiche der Hauptversuche werden
hiermit nicht festgelegt.

## Gespeicherte Dateien

| Datei | Inhalt |
|---|---|
| `config.toml` | Unveränderte Eingabedatei einschließlich Kommentaren |
| `resolved_config.json` | Vollständige geprüfte Konfiguration mit normalisierten Zahlentypen |
| `samples.csv` | `time_s`, `signal`, `noise`, `observed`; nach erfolgreichem Fit zusätzlich `prediction`, `residual` |
| `result.json` | Status, Wahrheit, Abtastung, geschätzte Parameter, sämtliche Startdiagnosen und Fehlerwerte; bei Rechenfehlern Fehlerbeschreibung |
| `metadata.json` | Abschlussstatus, Zeitstempel, Laufzeit, Umgebung, Codezustand, Zufallszustände und SHA-256-Prüfsummen |
| `plot.png` | Signal, Messdaten, Fit und Residuen; nur bei erfolgreichem Rechenlauf |

CSV-Zahlen werden mit 17 signifikanten Dezimalstellen geschrieben, damit
`float64`-Werte mit einem korrekt rundenden Leser wiederhergestellt werden
können. Dezimaltrennzeichen ist der Punkt. Einheiten: Zeit in Sekunden,
übrige CSV-Spalten dimensionslose Amplituden. Im Diagramm wird die Zeit
zur Lesbarkeit in Millisekunden dargestellt. JSON verwendet keine
`NaN`-/`Infinity`-Sonderwerte; ein nicht verfügbarer Wert ist `null`.

`ordinary_mse` und `covariance_mean_squared = Q/N` bewerten die Residuen
`observed - prediction`. `mse_to_clean_signal` ist eine Diagnose gegenüber
der bekannten synthetischen Kurve. Sie beeinflusst weder Fit noch
Startauswahl. Sämtliche Werte beziehen sich auf **die angepassten Samples**;
sie sind keine Bewertung auf unabhängigen Testdaten. `Q/N` ist kein
automatisch um Freiheitsgrade korrigiertes reduziertes Chi-Quadrat.
Bei weißem Rauschen bewirkt die konstante Gewichtung mathematisch denselben
Minimierer wie die gewöhnliche Anpassung; dieser Kontrollfall belegt
keinen Vorteil bei korreliertem Detektorrauschen.

## Metadaten und Wiederholung

Pro Lauf werden gespeichert:

- UTC-Anfang und -Ende sowie verstrichene Zeit einschließlich numerischer
  Berechnung und Ergebnisexport nach Vorbereitung und Ordnerreservierung.
  Dies ist kein isolierter Solver-Benchmark.
- Python-Version und Implementierung, Betriebssystem/Architektur, alle
  installierten Python-Paketversionen sowie ausgewählte Thread-Variablen.
  `julia_used = false` stellt klar, dass installierte PySR-/JuliaCall-Versionen
  in der Paketliste keine Verwendung dieser Verfahren bedeuten.
- Unter `environment.numerical_libraries` die Build-Konfigurationen von
  NumPy und SciPy einschließlich Compiler- und BLAS-/LAPACK-Angaben aus
  `show_config(mode="dicts")`. Buildpfade und dort genannte Python-Versionen
  beschreiben die Erstellung des jeweiligen Pakets; sie sind nicht mit
  der aktuellen Python-Laufzeit gleichzusetzen.
- Ebenfalls dort eine Momentaufnahme der bereits geladenen, von
  `threadpoolctl.threadpool_info()` erkannten nativen Bibliotheken vor der
  Datenerzeugung: unter anderem Bibliothekspfad, Implementierung, Version,
  Threading-Verfahren und eingestellte Threadzahl, soweit der Anbieter sie
  meldet. Die Threadgrenzen werden nur gelesen, nicht geändert. NumPy und
  SciPy können unterschiedliche BLAS-Versionen laden.
  `threadpoolctl` ist bereits in der gesperrten Abhängigkeitskette vorhanden,
  bleibt für diese Diagnose aber optional. Jeder Diagnosebericht kennzeichnet
  `status = "available"` mit seinen `details` oder `status = "unavailable"`
  mit `details = null` und Fehlermeldung. Eine erfolgreich gelesene leere
  Bibliotheksliste bedeutet, dass keine unterstützte Bibliothek erkannt
  wurde; sie beweist nicht, dass keine numerischen Bibliotheken verwendet
  werden. Auch die Momentaufnahme ist keine vollständige Identitätsgarantie
  für spätere Rechenoperationen.
- Git-Commit und geänderte/unversionierte Dateipfade vor Erzeugung des
  Ausgabeordners, sofern das tatsächlich geladene Paket im Repository
  liegt. Ein anderes Repository im aktuellen Arbeitsverzeichnis wird
  nicht zugeschrieben. Ohne Git oder außerhalb eines passenden Checkouts
  sind Commit und Änderungsstatus ausdrücklich unbekannt (`null`).
- SHA-256 für die Python-Dateien des geladenen Pakets und einen gemeinsamen
  Fingerabdruck dieser Liste. Im Quellcheckout zusätzlich Prüfsummen von
  Python-/Julia-Paketdefinitionen, Lockdateien und Versionsvorgaben.
  Ein Commit allein beschreibt bei `dirty = true` nicht den ausgeführten
  Stand: Änderungen müssen zusätzlich gesichert werden; Hashes ersetzen
  keine Sicherung des Quelltexts. Während eines Laufs keine Quelldateien
  bearbeiten.
- Seed, ausdrücklich gewählter `PCG64`, Zufallszustand vor und nach dem
  einzelnen Aufruf `normal(loc=0, scale=sigma, size=N)` und dessen
  Abschlusskennung. Der globale NumPy-Zufallszustand wird nicht benutzt.
- Prüfsummen aller erzeugten Nutzdateien. `metadata.json` ist von seiner
  eigenen Prüfsummenliste ausgenommen. Prüfsummen erkennen Veränderungen;
  sie sind keine digitale Signatur oder wissenschaftliche Validierung.

Konfiguration, NumPy-Build, Rechner und Aufruffolge können die Wiederholung
beeinflussen. Gleiche Seeds allein garantieren keine rechnerübergreifend
identischen Gleitkommawerte; siehe [NumPy-Kompatibilitätsrichtlinie](https://numpy.org/doc/stable/reference/random/compatibility.html).
Auch Solver und BLAS/LAPACK können zwischen Rechnern geringfügig abweichen.
Die gespeicherten Messwerte bleiben daher als konkreter Datennachweis
erhalten. Dieser erste Befehl erzeugt Daten anhand der Konfiguration neu;
ein eigener Modus zum erneuten Fitten importierter CSV-Daten ist noch
nicht implementiert.

Für eine nachvollziehbare Wiederholung auf dem zweiten Rechner:

1. Den protokollierten Commit verwenden und die Umgebung mit
   `uv sync --locked --dev --python 3.12.14` herstellen.
2. Falls der ursprüngliche Stand geändert war, die Änderungen zusätzlich
   wiederherstellen und die Quelltextprüfsummen vergleichen.
3. Die gespeicherte `config.toml` mit neuem `--output` ausführen.
4. Konfiguration, Daten, Umgebungsinformationen und numerische Ergebnisse
   vergleichen. Zeitstempel und Laufzeiten dürfen sich unterscheiden;
   rechnerübergreifende numerische Toleranzen müssen fachlich festgelegt
   werden. Die Aussage „rechnerübergreifend identisch“ wird nicht vorweggenommen.

Lokale Ausgaben unter `results/` werden nicht mit Git versioniert. Sie
müssen separat gesichert werden. Konfigurationen unter `configs/` und
Implementierung gehören ins Repository. Bei anderen Ausgabeorten im
Repository selbst auf den Git-Status achten.

## Fehler und Abschlussstatus

Der Rückgabecode des Kommandozeilenprogramms ist:

| Code | Bedeutung |
|---|---|
| `0` | Berechnung und Export abgeschlossen, `metadata.status = "success"` |
| `1` | Rechenfehler protokolliert: `generation_failed`, `fit_failed` oder `evaluation_failed` |
| `2` | Eingabe-/Dateifehler oder nicht vollständig möglicher Export; Meldung auf stderr |

Ungültige Konfigurationen werden vor Reservierung des Ausgabeordners
abgelehnt. Nach der Reservierung wird zuerst `metadata.json` mit Status
`running` angelegt. Erst nach Berechnung, Dateiexport und Prüfsummen wird
der Abschlussstatus geschrieben; die Metadatendatei wird dabei atomar
ersetzt. Bei Prozessabbruch oder unerwartetem Exportfehler kann ein
unvollständiger Ordner mit `running` zurückbleiben. Einzelne schon
vorhandene Dateien, auch ein `result.json` mit erfolgreicher Berechnung,
belegen dann keinen vollständigen Export. Maßgeblich ist die abschließende
`metadata.json`. Ein Abbruch noch vor ihrer ersten Anlage kann auch einen
leeren reservierten Ordner hinterlassen.

Fit-Abbrüche durch erschöpftes Budget behalten die erzeugten Messdaten
und alle Startdiagnosen. Es werden keine erfolgreichen Parameter erfunden.
Bestehende Ergebnisse werden weder überschrieben noch automatisch
fortgesetzt oder gelöscht. Der nächste Versuch bekommt einen neuen Ordner.

## Prüfungen und offene Arbeit

Integrationstests prüfen unter anderem den vollständigen Export, die
CSV-Rückgewinnung, Prüfsummen, RNG-Zustandswiederholung, geänderte Seeds,
unveränderten globalen Zufallszustand, Fehlerprotokolle, Überschreibschutz
einschließlich eines Symlinks mit fehlendem Ziel und einen Aufruf aus anderem
Arbeitsverzeichnis. Zwei über ein gemeinsames Startsignal synchronisierte
Python-Prozesse prüfen denselben Ausgabeordner: genau ein Lauf darf erfolgreich
abschließen, der andere muss das vorhandene Ziel ablehnen. Anschließend
werden Abschlussstatus, Dateibestand und sämtliche Nutzdatei-Prüfsummen
kontrolliert. Fehlende Build-/Laufzeitdiagnosen werden außerdem als nicht
verfügbare Angaben gespeichert, ohne den Rechenlauf scheitern zu lassen.
Ein rauschfreier Lauf
wird gegen die unabhängig berechnete Folge
`2**(-k) * [1, 1, -1, -1, ...]` geprüft.

Die im Review separat ausgeführten Vergleiche des vollständigen
Referenzfits mit einer direkten Vierparameteroptimierung und symmetrischem
Eigenwert-Whitening sind nun als neun Testfälle für weiße sowie positiv
und negativ korrelierte feste Kovarianzen versioniert. Dies prüft den
Fit-Kern; die konfigurierbare Datenerzeugung unterstützt weiterhin nur
weißes Rauschen. Beide Optimierungen sind lokal, kein globaler Beweis.

Offen bleiben statistische Leistungsbewertung mit mehreren Realisierungen,
unabhängige Bewertungsdaten, Unsicherheiten, korrelierte Datenerzeugung,
Kovarianzschätzung/Regularisierung, PySR-Integration sowie die Begründung
der Hauptversuche. Eine bekannte Modellfamilie hat gegenüber freier
Formelentdeckung zusätzliches Vorwissen; dies muss im Vergleich ausgewiesen
werden.

Referenzen zu den Diagnoseschnittstellen:

- [NumPy: show_config](https://numpy.org/doc/stable/reference/generated/numpy.show_config.html)
- [SciPy: show_config](https://docs.scipy.org/doc/scipy/reference/generated/scipy.show_config.html)
- [threadpoolctl: Runtime Programmatic Introspection](https://github.com/joblib/threadpoolctl#python-runtime-programmatic-introspection)
