# Feste SR-Bäume und Konstantenoptimierung vergleichen

Stand: 25.10.2026. Die bisherigen Wiederholungen mit denselben eingefrorenen
WSL2-Eingaben liefern auf jedem Rechner lokal bitgleiche Fronten, zwischen
Manjaro und WSL2 jedoch unterschiedliche Fronten. Die übermittelten
BLAS-/OpenMP-Kontrollen mit Limit 1 ändern diese Fronten auf keinem der
beiden Rechner. Das ist ein begrenzter Diagnosebefund; eine Ursache ist
weiterhin nicht nachgewiesen.

`scripts/probe_symbolic_numerics.py` untersucht deshalb feste Bäume und
ihre tatsächliche Konstantenoptimierung außerhalb der freien Suchgeschichte.
Es ist ein Diagnosewerkzeug für den gewöhnlichen Weißrausch-Arm, keine
Änderung des Piloten, seiner Zielfunktion oder seiner wissenschaftlichen
Auswahlregeln. Es erzeugt keine neuen Daten und startet keine freie Suche.

## Fälle und feste Vorgaben

Jeder der zwei frischen Worker bearbeitet dieselben acht Fälle:

| Modell | Anfangswerte | Tatsächlich geprüfter Backend-Pfad |
| --- | --- | --- |
| `sin(t*k)` | die gespeicherten WSL2-/Manjaro-Konstanten, außerdem −0,5 und −1 | Newton, vier Fälle |
| `a + b*t` | (1, −1) und (−1, 1) | BFGS, zwei Fälle |
| `a*sin(t*k)` | (1, −0,5) und (0,5, −1) | BFGS, zwei Fälle |

Die beiden beobachteten Sinuskonstanten sind exakt die Float64-Werte
`-0x1.a9a30ae4d1e60p-2` und `-0x1.a9a30bd659620p-2`. Die ursprüngliche
binäre Reihenfolge `t*k` bleibt erhalten. Diese Werte sind diagnostische
Startpunkte, keine rekonstruierten Anfangswerte historischer Optimierungen.
Insbesondere wird nicht behauptet, dass der erste Unterschied der freien
Suche an diesen Bäumen entstanden ist.

Der Aufruf erfolgt über `SymbolicRegression.optimize_constants` im
gepinnten Backend 2.5.1. Ein beobachtender Callback muss tatsächliche
`NewtonState`- beziehungsweise `BFGSState`-Zustände liefern. Der Callback
kopiert Zustand und Gradient, bricht nicht ab und berechnet keine
zusätzlichen Zielfunktionswerte. Für eine Konstante überschreibt das
Backend die konfigurierte BFGS-Methode durch Newton.

Die verlust- und optimierungsrelevanten Vorgaben entsprechen dem geprüften
Arm: gewöhnlicher vollständiger Verlustkern mit Einheitenprüfung,
Float64, kein Batching, kein Turbo/Bumper, keine automatische
Differentiation, BFGS mit BackTracking, 20 Iterationen und zwei
Zufallsneustarts. Die übrigen Suchmechanismen werden nicht aufgerufen.
Die effektive Optimierer-Konfiguration wird gespeichert. Es gibt keine
nachträgliche Verschärfung von Konvergenzkriterien und keine Anforderung,
dass nichtlineare Fälle ein globales Minimum erreichen.

Vor **jedem Fall** wird ein neuer `Xoshiro(465951028)` erzeugt. Das ist der
bekannte Backend-Seed des untersuchten ursprünglichen Arms, kein
historischer RNG-Checkpoint. Die acht gespeicherten UInt64-Ausgaben vor
und nach der Optimierung sind Zustandsfingerprints, keine vollständigen
Checkpoints. Gleicher Seed und gleicher Start werden auf beiden Rechnern
ausdrücklich vorgeschrieben; frühere Suchverläufe werden nicht nachgespielt.

## Aufruf auf beiden Rechnern

Das Werkzeug wird aus dem neuen Commit temporär außerhalb des sauberen
Prüfprojekts bereitgestellt. Das Prüfprojekt selbst bleibt auf dem
Referenzcommit `6ed493d2e8fb3a845dd921bd99a620feb8b8850a`.
Der konkrete Werkzeugcommit wird für beide Aufrufe festgehalten.
Voraussetzung sind die bereits vorhandenen Thread-Kontrollordner mit
den neun gesicherten Quelldateien unter `source/`.

| Rechner | Prüfprojekt | Eingabe relativ zum Prüfprojekt |
| --- | --- | --- |
| WSL2 | `~/projects/ringdown-sr-portability-6ed493d` | `results/sr-repeatability-wsl2-threads1-001/source` |
| Manjaro | `~/Projects/ringdown-sr-portability-6ed493d` | `results/sr-repeatability-manjaro-threads1-001/source` |

Nach Bereitstellung des Skripts lautet der eigentliche Aufruf unter WSL2:

```bash
env -u VIRTUAL_ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked --python 3.12.14 python "$fixed_probe_script" \
  results/sr-repeatability-wsl2-threads1-001/source \
  --label wsl2 --output results/sr-fixed-numerics-wsl2-001
```

Auf Manjaro entsprechend den Quellordner und beide Rechnerkennungen ändern.
Die Threadvorgaben gelten ausschließlich für diesen Aufruf und seine
Kinder. Das Werkzeug zeichnet die gemeldeten Poollimits auf, ohne sie
zusätzlich zur Laufzeit umzuschalten. Weitere Julia-/GC-Einstellungen
werden erfasst, jedoch nicht verändert. Bestehende Ausgabeordner werden
abgelehnt. Für eine Wiederholung einen neuen Ausgabenamen verwenden.

## Daten und Ergebnisse

Die konsumierten sieben Quelldateien werden gegen das vorhandene
SHA-256-Manifest geprüft. Manifest und Erfolgsmeldung werden zusätzlich
kopiert. Es werden ausschließlich die gehashten NPZ-Bytes geladen,
mit `allow_pickle=False`; akzeptiert werden endliche Float64-Vektoren
`time_s` und `observed` ohne Kovarianz. Kein Zentrieren, Skalieren,
Resampling oder Neuaufbau aus der Pilotkonfiguration findet statt.
Unpassende Optimierervorgaben werden vor dem Anlegen der Ausgabe abgelehnt.

Gespeichert werden:

- `source/`: unveränderte konsumierte Quelldateien und ihre Nachweise.
- `driver.py` und `probe.jl`: tatsächlich ausgeführter Diagnosecode.
- `report.json`: Anfangs-/Endherkunft, Quellen- und Eingabehashes,
  Aufträge und beschreibende lokale Ergebnisidentität.
- `run-1/` und `run-2/`: getrennte Workerlogs, Metadaten und Teil-/Endergebnisse.
- `checksums.json`: SHA-256 aller erhaltenen Dateien, auch nach einem Fehler.

Je Fall werden Ausgangs- und Endbaum, Parameter, Vorhersagen, Residuen,
Verlust und alle Callback-Zustände gespeichert. Zahlen erhalten zusätzlich
ihre exakte Float64-Hexdarstellung; nicht endliche Tracewerte erhalten
`null` mit Status und Hex-/Sonderwertdarstellung. Ein Verlustvergleich
allein ersetzt weder Vorhersage- noch Parametervergleich. Zusätzlich
werden direkte Quadratsumme und BLAS-Dot-Produkt als numerische Diagnosen
gespeichert; sie ersetzen den Verlustkern nicht.

Jeder Ausgangs- und Endbaum wird unabhängig in Python in ursprünglicher
Binärreihenfolge nachgerechnet. Vorhersagen werden an ihrer gemeinsamen
Maximalamplitude ohne feste Untergrenze verglichen (`rtol=1e-12`,
normiertes `atol=1e-14`), Verluste mit `rtol=1e-10`, `atol=0`.
Der Vergleich dieser Replays hat dieselben Grenzen wie der bestehende
Adapter; unterschiedliche Python-/Julia-Bibliotheksauswertungen werden
aufgezeichnet und nicht als Bitidentität ausgegeben.

Vor und nach den Proben werden Code-/Umgebungsaufnahmen bewahrt.
Julia-Version, CPU-Name, CPU-/Julia-/GC-Threadzahlen, CPU-Target und
BLAS-Konfiguration ergänzen die Python-Poolaufnahmen. Veränderungen an
Runtime-Quellen oder an den ursprünglichen Eingabedateien führen zum
Fehlerstatus mit erhaltenen Diagnoseartefakten. Frühere Ergebnisse werden
nicht verändert und keine Pickle-/Julia-Serialisate geladen.

`completed` bedeutet, dass alle Fälle und Replays durchgelaufen sind.
`local_results_bitwise_equal` ist ein getrennter beschreibender Befund,
keine wissenschaftliche Erfolgsschwelle. Ein Unterschied zwischen zwei
Rechnern lokalisiert einen untersuchten numerischen Pfad; er beweist
noch nicht dessen Ursächlichkeit für die historischen freien Fronten.
Übereinstimmung schließt Unterschiede anderer Bäume, Startwerte oder
Suchpfade ebenfalls nicht aus.

## Prüfungen des Werkzeugs

Die Python-Tests prüfen Quellenintegrität, unveränderte Datennutzung,
Startbäume, ausschließliche Ausgabeordner, erhaltene Fehlerdaten,
Nullvorzeichen und skalengerechtes Replay mit kontrollierten Workern.
Sie sind kein Nachweis ausgeführter Julia-Optimierung.

Die CI führt das Werkzeug zusätzlich auf dem bereits erzeugten gewöhnlichen
weißen Schema-3-Kontrollarm aus. Dabei müssen beide echten Worker alle
acht Fälle, tatsächlichen Optimiererpfade und Python-Replays bestehen.
Dieser kleine CI-Lauf ersetzt die folgenden Manjaro-/WSL2-Vergleiche mit
den ursprünglichen 128 Samples nicht.
