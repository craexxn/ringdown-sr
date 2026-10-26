# Feste SR-Bäume und Konstantenoptimierung vergleichen

Stand: 26.10.2026. Ausgangspunkt waren lokal wiederholbare, zwischen
Manjaro und WSL2 aber unterschiedliche freie Fronten bei denselben
eingefrorenen WSL2-Eingaben. BLAS-/OpenMP-Poollimits 1 allein änderten
diese Fronten auf keinem der beiden Rechner. Deshalb wurden feste Bäume
und anschließend ein gemeinsamer OpenBLAS-Kern untersucht. Die festen
Ergebnisse stehen unten; die nachfolgende freie Haswell-Suche liefert
inzwischen dieselbe vollständige Front auf beiden Rechnern. Deren
[begrenzter Befund](symbolic_core_results.md) erklärt nicht pauschal
sämtliche historischen Schema-3-Ergebnisse.

`scripts/probe_symbolic_numerics.py` untersucht deshalb feste Bäume und
ihre tatsächliche Konstantenoptimierung außerhalb der freien Suchgeschichte.
Es ist ein Diagnosewerkzeug für den gewöhnlichen Weißrausch-Arm, keine
Änderung des Piloten, seiner Zielfunktion oder seiner wissenschaftlichen
Auswahlregeln. Es erzeugt keine neuen Daten und startet keine freie Suche.

Die am 25.10.2026 übermittelten und gemeinsam nachgerechneten festen
Diagnosepakete bestätigen lokal jeweils zwei identische Wiederholungen.
Alle acht Ausgangsvorhersagen und -verluste sowie alle vier Newton-
Optimiererverläufe stimmen zwischen den Rechnern bitgenau überein.
Drei von vier BFGS-Fällen enthalten unterschiedliche Zwischenzustände;
bei zwei Fällen bleibt eine Konstante um eine Float64-Abstandsstufe
verschieden. Die acht Endverluste sind jeweils bitgleich. Alle 64
Ausgangs-/Endauswertungen wurden unabhängig nachgerechnet; der maximale
Verlustabstand zur exakt rational berechneten Quadratsumme der gespeicherten
Residuen beträgt drei ULP. Das belegt keine Ursache der früheren
verschiedenen freien Fronten.

Die NumPy-/SciPy-/Julia-OpenBLAS-Kerne waren trotz Poollimit 1 unterschiedlich:
WSL2 meldete Haswell/Haswell/Zen, Manjaro dreimal SkylakeX. Das separate
Skalarprodukt unterscheidet sich teilweise schon bei bitgleichen Residuen.
Dies begründet die folgende gezielte Kontrolle der Kernwahl.

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

## Optionale Kontrolle mit gemeinsamem OpenBLAS-Kern

Für die nächste Intervention wird vor dem Start aller Python-/Julia-Prozesse
`OPENBLAS_CORETYPE=Haswell` gesetzt, zusammen mit den vier Threadlimits 1.
Die [offizielle OpenBLAS-Anleitung](https://github.com/OpenMathLib/OpenBLAS/blob/develop/USAGE.md)
beschreibt diese Kernwahl für `DYNAMIC_ARCH`-Builds. Die beiden untersuchten
CPUs unterstützen den gemeinsamen Haswell-Befehlssatz; die geladenen
Bibliotheken müssen den Kern tatsächlich anbieten und auswählen.

Das zusätzliche Argument `--require-openblas-core Haswell` aktiviert eine
strikte Wirkungskontrolle. Die Kernvariable wird vom Treiber aufgezeichnet,
jedoch nicht nachträglich im laufenden Prozess geändert. Der Elternprozess
prüft die bereits geladenen Python-BLAS-Bibliotheken. Jeder frische Worker
prüft nach dem Julia-Import vor dem ersten Optimierungsfall und nach dem
letzten Fall alle geladenen BLAS-Pools. Erforderlich sind verifizierte
NumPy-, SciPy- und Julia-Bibliotheken, ausschließlich OpenBLAS mit gemeldetem
Kern `Haswell`, sowie Limit 1 für alle erfassten BLAS-/OpenMP-Pools.
Fehlende Diagnosen, eine fehlende Julia-Bibliothek, ein anderer Kern oder
ein anderes Limit brechen den Kontrolllauf mit erhaltenen Metadaten ab.
Der Elternprozess prüft zusätzlich die gespeicherten Workeraufnahmen.

Die acht Fälle, Starts und der eingebettete Julia-Code der tatsächlichen
Optimierung bleiben unverändert. Dessen SHA-256 ist weiterhin
`8481613c28f91e01772f7c30686ba17f0746d4c77e580bfb1af2e597ce4d33df`.
Ein Regressionstest sichert diese Übereinstimmung mit den beiden
ursprünglichen festen Diagnosepaketen ab. Neu sind ausschließlich die
optionalen Kontrollprüfungen und Herkunftsfelder im Python-Treiber.

Auf jedem Rechner werden mit genau demselben neuen Werkzeugcommit zwei
Teilversuche gestartet, jeweils wieder mit zwei frischen Workern:

1. `baseline/`: `OPENBLAS_CORETYPE` ausdrücklich nicht gesetzt;
   bisherige automatische Kernwahl, vier Threadlimits 1.
2. `haswell/`: `OPENBLAS_CORETYPE=Haswell` und
   `--require-openblas-core Haswell`; dieselben Threadlimits 1.

Die neue Baseline kontrolliert zugleich den aktualisierten Treiber gegen
die vorhandenen festen Diagnoseergebnisse. Als Quelle dient jeweils
`results/sr-fixed-numerics-RECHNER-001/source`, also dieselbe bereits
gesicherte Armausgabe. Beide neuen Teilversuche werden gemeinsam unter
`results/sr-core-control-RECHNER-001/` gespeichert und in ein Archiv
`sr-core-control-RECHNER-001.tar.gz` im Home-Verzeichnis gepackt.
Neue Ausgabeordner und ein neuer Archivname sind erforderlich.

Nach jedem kontrollierten Worker erscheint bei bestandener Kernprüfung:

```text
Verified OpenBLAS: Haswell for NumPy, SciPy and Julia; pool limits 1.
```

`report.json.required_openblas_core` und
`openblas_coretype_environment` in den Herkunftsaufnahmen nennen die
Vorgabe. `blas_control` enthält den bestätigten Status und die tatsächlich
gemeldeten Bibliotheken. Ohne Kontrollargument lautet der Status
`not_requested`; dies ist die Baseline, kein bestätigter gemeinsamer Kern.
Die Ergebnisdateien und alle numerischen Werte behalten ihr bisheriges
Format. Die CI führt neben der Baseline auch den neuen wirkungsgeprüften
Haswell-Durchlauf aus.

Gleiche BLAS-Kernnamen vereinheitlichen weder alle Maschinenbefehle noch
Julia-CPU-/GC-Einstellungen, Systembibliotheken oder Builds. Die
Intervention prüft deshalb nur den Einfluss dieser konkret bestätigten
Kernwahl. Ein möglicher Effekt ist zunächst an den festen Diagnosen zu
beurteilen; eine Erklärung der ursprünglichen freien Suchfronten benötigt
gegebenenfalls deren anschließende kontrollierte Wiederholung.

## Übermittelter Haswell-Vergleich vom 26.10.2026

Beide übermittelten Archive `sr-core-control-manjaro-001.tar.gz` und
`sr-core-control-wsl2-001.tar.gz` wurden gemeinsam unabhängig nachgerechnet.
Alle vier Bedingungen liefen am protokollierten sauberen Referenzcommit
`6ed493d` mit Treiber `ac41251` und identischen Quellen und Eingangsdaten.
Die neuen Basis-Ergebnisdateien reproduzieren jeweils die alten Dateien.
Unter Haswell sind die vollständigen numerischen Ergebnisdateien beider
Rechner für alle acht Fälle bytegleich, einschließlich der gespeicherten
Optimiererzustände. Ohne die gemeinsame Kernwahl bleiben zehn von 88
Zuständen eines Workerpaars verschieden; zwei Endkonstanten unterscheiden
sich um je eine Float64-Abstandsstufe. Die acht Endverluste sind schon
ohne die gemeinsame Kernwahl bitgleich.

Die Nachrechnung bestätigt 80 Paket-Prüfsummen, 32 übereinstimmende
Herkunftsaufnahmen und 128 unabhängige Vorhersage-/Verlust-Replays. Die
maximale Abweichung des produktiven Verlusts von der aus gespeicherten
Float64-Residuen exakt rational berechneten Referenz beträgt drei ULP.
Es wurden für diese Auswertung keine neuen Julia-Suchen gestartet.

Damit ist die Kernwahl als Einflussfaktor für diese festen Fälle belegt.
Die ursprüngliche freie Suchgeschichte wurde dabei nicht nachgestellt.
Die inzwischen ausgeführte [freie Haswell-Kontrolle](symbolic_core_results.md)
ergänzt den festen Befund; ihr
[Ablauf](symbolic_repeatability.md#kontrollierte-freie-suche-mit-gemeinsamem-blas-kern)
ist separat beschrieben. Die methodische Reichweite dieser Vorgabe und
die offene Entscheidung zum späteren Forschungsprofil stehen im
[Entscheidungsvermerk](reproducibility_decisions.md).
