# Pilot: erster Implementierungsschritt

## Ziel und Stand

Dieser Schritt implementiert eine gleichmäßige Zeitachse und einen
deterministischen Generator für ein einzelnes gedämpftes Sinussignal.
Die Tests prüfen seine mathematische Umsetzung anhand einfacher
Referenzfälle. Rauscherzeugung, Kovarianzschätzung, Verlustfunktionen,
Referenzfit, PySR-Suche und Ergebnisexport folgen in weiteren Schritten.

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
