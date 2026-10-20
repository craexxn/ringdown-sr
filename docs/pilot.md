# Pilot: synthetisches Signal und weißes Rauschen

## Ziel und Stand

Implementiert sind eine gleichmäßige Zeitachse, ein deterministischer
Generator für ein einzelnes gedämpftes Sinussignal und weißes Gaußrauschen
mit explizitem Zufallsgenerator. Die Tests prüfen die mathematische
Umsetzung und grundlegende Rauscheigenschaften anhand analytischer
Referenzen. Hinzu kommen die gewöhnliche MSE und Rechenkerne für eine
vorgegebene volle Kovarianzmatrix; Definitionen und offene
Normierungsfragen stehen in [Verlustfunktionen](losses.md).
Ein [klassischer Referenzfit](reference_fit.md) passt die bekannte
Ringdown-Formel an und kann eine vorgegebene volle Kovarianz berücksichtigen.
Ein ausführbarer Demolauf stellt Messdaten, Signal und Fit gemeinsam dar.
Ein [konfigurierbarer Durchlauf mit Ergebnisexport](configured_pilot.md)
verbindet diese Bausteine und speichert Daten, Ergebnisse, Diagramm und
Metadaten. [Stationäres AR(1)-Rauschen](correlated_noise.md) ergänzt einen
korrelierten Kontrollfall mit bekannter voller Kovarianz.
[Kovarianzschätzung mit Regularisierung](covariance_estimation.md) und
ihre [Schema-2-Integration](estimated_covariance_pilot.md) sind inzwischen
vorhanden. Die freie PySR-Suche folgt nach Prüfung ihres
[Methodenentwurfs](symbolic_regression_method_plan.md).

## Signaldefinition und Einheiten

Das zunächst unterstützte Signal lautet:

```text
s(t) = A * exp(-t / tau) * cos(2 * pi * f * t + phi), t >= 0
```

| Größe | Bedeutung | Einheit / zulässige Werte |
|---|---|---|
| `t` / `time_s` | Zeit relativ zum Signalbeginn | Sekunden, endlich, nicht negativ |
| `A` / `amplitude` | Amplitudenfaktor | dimensionslos, endlich, auch null oder negativ |
| `f` / `frequency_hz` | Frequenz | Hertz, endlich, nicht negativ |
| `tau` / `decay_time_s` | Abklingzeit | Sekunden, endlich, strikt positiv |
| `phi` / `phase_rad` | Anfangsphase | Radiant, endlich |

Es gilt `alpha = 1 / tau` für die alternative Abklingrate und
`omega = 2 * pi * f` für die Kreisfrequenz. In Exponentialfunktion und
Kosinus sind die Argumente dimensionslos. Zeit null ist der Beginn des
modellierten Ausschnitts. Die Funktion modelliert keine Verschmelzung,
keinen Übergang davor und keine zusätzlichen Moden.

Die Parameter haben keine astrophysikalischen Standardwerte. Ein
negatives `A` ist mathematisch durch eine Phasenverschiebung um `pi`
darstellbar; diese Redundanz wird bei späteren Fit-Grenzen berücksichtigt.
Frequenz null bleibt als analytischer Grenz- und Testfall zulässig.

## Abtastung

Für eine ausdrücklich gewählte Samplezahl `N` und Abtastrate `fs` gilt:

```text
t[k] = k / fs, k = 0, ..., N - 1
Fensterdauer: T = N / fs
Letzter Abtastzeitpunkt: (N - 1) / fs
```

Das Fenster wird als `[0, T)` verstanden; sein rechter Rand ist kein
zusätzlicher Messpunkt. Die Zeitachse wird aus ganzzahligen Indizes
gebildet und hat den Datentyp `float64`.

Die im Pilot vorgesehenen 25, 50 und 100 ms sind vorläufige Zielgrößen.
Bei 4096 Hz ergeben sie rechnerisch 102,4, 204,8 und 409,6 Samples.
Die API nimmt deshalb eine Samplezahl entgegen und trifft keine
stillschweigende Rundungsentscheidung. Für spätere Versuche werden
Zieldauer, gewählte Samplezahl und tatsächliche Fensterdauer gemeinsam
protokolliert. Die Rundungsregel wird beim Aufbau der Versuchskonfiguration
ausdrücklich festgelegt.

`ringdown_signal` kann auch andere eindimensionale, reelle und nicht
negative Zeitpunkte auswerten. Diese müssen nicht gleichmäßig sein.
Die Prüfung einer geeigneten Abtastrate für gewählte Signalparameter
gehört zur späteren kombinierten Datenerzeugung.

## Verwendung

```python
from ringdown_sr.signals import ringdown_signal, sample_times

time_s = sample_times(n_samples=128, sample_rate_hz=4096.0)
signal = ringdown_signal(
    time_s,
    amplitude=1.0,
    frequency_hz=250.0,
    decay_time_s=0.008,
    phase_rad=0.0,
)
```

Diese Beispielwerte dienen der Funktionsdemonstration und legen keine
Parameterbereiche für die Forschungsexperimente fest.

## Weißes Gaußrauschen

`gaussian_white_noise` erzeugt unabhängige Zufallswerte mit:

```text
epsilon[k] ~ N(0, sigma^2)
E[epsilon[k]] = 0
Cov(epsilon[i], epsilon[j]) = sigma^2, wenn i = j, sonst 0
y[k] = s(t[k]) + epsilon[k]
```

`standard_deviation` ist `sigma`, nicht die Varianz. Die Einheit entspricht
der Signalamplitude; beim bisher normierten Signal ist sie dimensionslos.
Der Wert muss endlich und nicht negativ sein. `sigma = 0` liefert den
rauschfreien Referenzfall.

Die Definition bezieht sich auf die Verteilung. Der Mittelwert und die
Standardabweichung einer endlichen Realisierung schwanken. Die erzeugten
Werte werden deshalb weder nachträglich zentriert noch auf exakt
vorgegebene Stichprobenmomente normiert. Gerade bei kurzen Fenstern
wären dies zusätzliche Eingriffe in die Rauschstatistik.

```python
import numpy as np

from ringdown_sr.noise import gaussian_white_noise

rng = np.random.Generator(np.random.PCG64(42))
noise = gaussian_white_noise(
    len(signal),
    standard_deviation=0.1,
    rng=rng,
)
observed = signal + noise
```

Der Aufrufer verwaltet Generator und Seed. Zwei frisch erzeugte
Generatoren mit gleichem Seed reproduzieren bei gleicher Umgebung und
gleicher Aufruffolge dieselben Werte. Ein wiederverwendeter Generator
wird weitergeschaltet; sein nächster Aufruf erzeugt eine weitere
Realisierung. Der globale NumPy-Zufallszustand bleibt unberührt.

Im Beispiel und in den Tests ist der Algorithmus ausdrücklich `PCG64`.
Die Funktion akzeptiert einen NumPy-`Generator`; für spätere Experimente
werden Algorithmus, Seed, NumPy-Version und Aufruffolge protokolliert.
Ein Seed allein garantiert keine identischen Gleitkommazufallszahlen
über unterschiedliche NumPy-Builds oder Rechner hinweg. Details stehen
in der [NumPy-Kompatibilitätsrichtlinie](https://numpy.org/doc/stable/reference/random/compatibility.html).

Dieses Rauschen ist ein einfacher Kontrollfall. Es bildet noch keine
Detektorcharakteristik ab und legt weder eine SNR-Konvention noch die
Rauschpegel der Hauptversuche fest.

## Prüfungen

Aus dem Projektordner:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
```

Die Signalgenerator-Tests importieren NumPy, aber kein PySR und kein
JuliaCall. Der vorhandene technische Python-/Julia-Umgebungscheck bleibt
als eigenständige Prüfung bestehen.

Für das Rauschen prüfen feste Testseeds die Wiederholbarkeit, das
Fortschalten des Generatorzustands und die Trennung vom globalen
Zufallszustand. Statistiktests mit 200.000 Werten vergleichen Mittelwert,
Varianz, den Anteil innerhalb einer Standardabweichung und ausgewählte
Kovarianzen bei Zeitversatz mit analytisch begründeten Referenzen.
Die Toleranzen entsprechen jeweils sechs Standardfehlern unter dem
angenommenen unabhängigen Normalmodell. Sie sind vorab aus der
Stichprobengröße abgeleitet und werden nicht an beobachtete Werte angepasst.
Diese Prüfungen sind Kontrollfälle und kein vollständiger Nachweis aller
Verteilungseigenschaften. Die große Teststichprobe legt keine Länge für
die späteren Ringdown-Fenster fest.

Die Referenzfälle beruhen auf `cos(0) = 1`,
`cos(pi/2) = 0`, `cos(pi) = -1` und dem Faktor `2**(-t)` für
`tau = 1 / ln(2)`. Erwartungswerte werden separat angegeben und nicht
durch einen zweiten Aufruf des Generators berechnet.

Die relativen Toleranzen berücksichtigen Rundungen bei `float64`.
Nur an analytischen Nullstellen wird bei Amplituden der Größenordnung
eins eine absolute Toleranz von `1e-15` verwendet. Beim Test mit Amplitude
`1e-21` ist die absolute Toleranz null: Ein irrtümliches Nullsignal darf
diesen Test nicht bestehen.

Bestandene Tests belegen die geprüften Formeln und Eingaberandfälle.
Die wissenschaftliche Eignung der späteren Methode wird erst durch
die weiteren methodischen Prüfungen und Experimente untersucht.
