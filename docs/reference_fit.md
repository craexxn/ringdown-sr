# Klassischer Referenzfit für eine bekannte Ringdown-Formel

## Umfang

`fit_ringdown` in `src/ringdown_sr/reference_fit.py` passt genau eine
gedämpfte Schwingung ohne Offset, zusätzlichen Modus oder verschobenen
Signalbeginn an. Der Formansatz ist bekannt; dies ist der klassische
Vergleich und keine freie Formelentdeckung durch PySR.

Dieser Baustein liefert Parameter, Vorhersage, Residuen, Fehlerwerte und
Diagnosen aller Startpunkte. Ein vollständiger Versuchslauf mit
Konfigurationsdatei, Metadaten und dauerhaftem Ergebnisexport folgt separat.

## Parameterdarstellung und Berechnung

Das vorhandene Signalmodell wird äquivalent geschrieben als:

```text
s(t) = exp(-t/tau) * (a*cos(2*pi*f*t) + b*sin(2*pi*f*t))
a = A*cos(phi), b = -A*sin(phi)
A = hypot(a, b), phi = atan2(-b, a)
```

Für jedes Paar `(f, tau)` werden die zwei linearen Koeffizienten mit
`numpy.linalg.lstsq` bestimmt. Nur Frequenz und Abklingzeit werden mit
`scipy.optimize.least_squares` nichtlinear gesucht. Dies ist eine einfache
separable Least-Squares-Anpassung nach dem Prinzip der Variable Projection;
die Software aus der unten genannten Veröffentlichung wird nicht verwendet.
Der reduzierte Residualvektor wird numerisch differenziert.

Die zurückgegebene Amplitude ist nicht negativ, die Phase liegt in
`[-pi, pi)`. Ein negatives Generator-`A` erscheint deshalb als positive
Amplitude mit entsprechend verschobener Phase. Die linearen Koeffizienten
haben keine zusätzlichen Amplitudengrenzen. Bei Amplitude null ist eine
Phase nicht identifizierbar.

Ohne Kovarianz wird die gewöhnliche Quadratsumme minimiert. Mit einer
festen positiv definiten Kovarianz `C = L @ L.T` werden Daten **und beide
Basisspalten** transformiert:

```text
b_data = solve(L, observed)
B = solve(L, H(f, tau))
c = argmin ||B @ c - b_data||^2
```

Es wird keine inverse Kovarianz gebildet. Die Cholesky-Zerlegung wird
einmal pro Fit berechnet. Eine geschätzte Kovarianz wird weder angepasst
noch regularisiert. Anforderungen an `C` stehen in [Verlustfunktionen](losses.md).

## Startpunkte, Grenzen und numerische Skalierung

- `time_s` beginnt bei null, ist streng aufsteigend und gleichmäßig
  abgetastet. Mindestens fünf Werte werden verlangt. Die Gleichmäßigkeit
  wird relativ mit `64 * eps(float64)` und absoluter Toleranz null geprüft.
- `observed` ist ein endlicher reeller Vektor gleicher Länge. Ein
  vollständig nullwertiger Vektor wird abgelehnt, da er keine Frequenz
  oder Abklingzeit festlegt. Nichtnull-Rauschen allein kann weiterhin
  einen numerischen Fit ergeben und ist kein Nachweis eines Signals.
- Frequenzgrenzen sind endlich und liegen strikt zwischen null und der
  Nyquist-Frequenz. Die Abklingzeit hat endliche strikt positive Grenzen.
  Nullfrequenz und Nyquist werden wegen der degenerierenden
  Sinus-/Kosinusdarstellung ausgeschlossen. Der allgemeine Signalgenerator
  unterstützt weiterhin seine separat dokumentierten Grenzfälle.
- `initial_points` enthält ausdrücklich alle Paare `(frequency_hz,
  decay_time_s)`. Jedes liegt strikt innerhalb der Grenzen. Es werden keine
  zusätzlichen Startpunkte erzeugt oder wahre Parameter entgegengenommen.
- Jeder Start erhält einen eigenen lokalen Suchlauf. Aus numerisch
  verwendbaren konvergierten Läufen wird der mit dem kleinsten intern
  skalierten Fehler gewählt; bei Gleichstand der frühere Start.
- Optimiert werden dimensionslose Koordinaten `f * T_span` und
  `log(tau / T_span)`, wobei `T_span = time_s[-1]`. Dieser Abstand zwischen
  erstem und letztem Sample ist nicht die Fensterdauer `N/fs`.
- Die Daten werden durch ihre maximale absolute Amplitude geteilt.
  Nach optionalem Whitening werden Ziel und Designmatrix gemeinsam durch
  den maximalen Absolutwert des transformierten Ziels geteilt. Das sind
  konstante positive Skalierungen pro Datensatz, keine Zentrierung oder
  Änderung der relativen Kovarianzgewichtung. So kann auch eine Amplitude
  von `1e-21` numerisch sinnvoll angepasst werden.
- Solver: TRF, lineare Least-Squares-Verlustfunktion, Dreipunktdifferenzen,
  `x_scale="jac"` und `ftol = xtol = gtol = 1e-10`.
  `max_nfev` ist ausdrücklich änderbar und beträgt standardmäßig 1000
  pro Start. SciPys `nfev` zählt zusätzliche Aufrufe für numerische
  Jacobi-Matrizen nicht mit und ist deshalb kein vollständiger Aufrufzähler.

Numerisch rangdefiziente Basismatrizen und nicht darstellbare
Zwischenergebnisse werden als fehlgeschlagener Start protokolliert.
Es gibt keine stillschweigende Pseudolösung für zwei nicht unabhängige
Basisspalten. Für die Rangentscheidung verwendet `lstsq` seinen
dokumentierten Grenzwert `eps * max(N, 2)` relativ zum größten Singulärwert.
Sind keine verwendbaren konvergierten Starts vorhanden, enthält
`ReferenceFitError.attempts` die einzelnen Diagnosen. Das ist ein
Fehlerergebnis und kein erfolgreicher Fit.

## Ergebnisse und ihre Grenzen

`ReferenceFit` enthält die kanonischen vier Parameter sowie schreibgeschützte
Arrays `prediction` und `residual`, mit `residual = observed - prediction`.
`ordinary_mse` wird immer ausgegeben, `covariance_mean_squared` nur bei
vorgegebenem `C`. Die Bedeutung von `Q/N` und die offene Normierungsfrage
stehen in [Verlustfunktionen](losses.md).

`attempts` dokumentiert Startwerte, SciPy-Konvergenz, numerische
Verwendbarkeit, Status, `nfev`, Meldung und `scaled_mse`. Letzteres ist
ein interner Vergleichswert innerhalb eines Fits und wegen seiner
datensatzabhängigen Skalierung kein Vergleichsmaß zwischen Versuchen.
`selected_start_index` zählt ab null. `active_mask` bezeichnet für
`(f, tau)` eine untere Grenze mit `-1`, eine obere mit `1` und keine
erkannte aktive Grenze mit `0`. Diese TRF-Diagnose ist toleranzabhängig.

`nonlinear_jacobian_rank` ist der numerische Rang der reduzierten
Jacobi-Matrix mit zwei Spalten. Er ist eine lokale Diagnose und weder
ein globaler Eindeutigkeitsnachweis noch eine Unsicherheitsschätzung.
Auch ein konvergierter Mehrfachstart garantiert kein globales Minimum.
Randlösungen, schwache Signale, kurze Fenster und schlechte Konditionierung
müssen bei späteren Versuchen gesondert betrachtet werden.

Die Skalierung verändert den Minimierer einer reinen Quadratsumme nicht.
Sie legt keine endgültige Forschungszielfunktion mit Komplexitätsstrafe
fest. Der Fit liefert auch keine Konfidenzintervalle oder automatische
Entscheidung, ob ein Ringdown vorhanden ist.

## Tests und sichtbarer Demolauf

Die Rückgewinnungstests verwenden die unabhängig berechnete Folge
`2**(-k) * [1, 1, -1, -1, ...]`. Sie entspricht `f = fs/4`,
`tau = 1/(fs*log(2))`, `a = b = 1`. Die Rückgewinnungsstarts enthalten
diese Frequenz und Abklingzeit nicht. Weitere Fälle prüfen negative und
sehr kleine Amplituden, Zeitskalierung, konstante Kovarianzgewichte,
Mehrfachstarts, erschöpfte Suchbudgets und aktive Grenzen.

Für eine volle `5 x 5`-Kovarianz mit führendem Block `[[2, 1], [1, 2]]`
und sonstiger Einheitsmatrix werden lineare Normalgleichungen von Hand
gelöst. Die Referenzkoeffizienten sind `a = 4608/5203`, `b = -544/5203`
und die minimale Quadratik ist `Q = 306/5203`. Sehr schmale nichtlineare
Grenzen von relativ `1e-9` nähern dabei die bekannte feste Basis an;
die relative Testtoleranz `2e-7` berücksichtigt deren kleine Änderung.
Dieser Test prüft die volle Gewichtung, kein verrauschtes Rückgewinnungsziel.

Der ausführbare Demolauf erzeugt ein bekanntes Signal, fügt weißes
Rauschen hinzu, führt den Fit aus und speichert ein Diagramm:

```bash
uv run --locked python scripts/demo_reference_fit.py
```

Standardmäßig liegt die PNG-Datei im temporären Verzeichnis des Rechners.
Unter Linux/WSL kann sie beispielsweise in VS Code geöffnet werden:

```bash
code -r /tmp/ringdown-reference-fit.png
```

Mit `--output /pfad/diagramm.png` lässt sich der Speicherort wählen.
Die Vorgaben sind ausschließlich ein Demofall: 128 Samples bei 4096 Hz,
Amplitude 1, Frequenz 250 Hz, Abklingzeit 8 ms, Phase 0, Rauschstandardabweichung
0,1 und PCG64-Seed 42. Grenzen und Startpunkte sind im Skript ausdrücklich
angegeben. Wahre Parameter werden nur zur Erzeugung und späteren
Darstellung des Beispiels verwendet. Die MSE zur bekannten Testkurve
beeinflusst weder Fit noch Auswahl eines Startpunkts.
Diese Werte definieren kein SNR-Raster oder Abnahmekriterium der Hauptversuche.

Referenzen zur Methode und Software:

- [O'Leary und Rust: Variable Projection for Nonlinear Least Squares Problems, Autorenfassung](https://www.cs.umd.edu/~oleary/software/varpro/varpro.pdf)
- [SciPy: least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)
- [NumPy: lstsq](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html)
