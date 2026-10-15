# Verlustfunktionen: Rechenkerne für den Pilot

## Umfang und offene Entscheidungen

Implementiert werden mathematische Referenzfunktionen für einen
Residualvektor und eine vorgegebene Kovarianzmatrix. Die endgültige
Normierung der Forschungszielfunktion und ihre Abstimmung mit der
Komplexitätsstrafe sind noch nicht festgelegt. Dafür sind beide
Kovarianzquadratik-Werte ausdrücklich zugänglich; es gibt keine
voreingestellte Aufrufvariante eines `CovarianceLoss`-Objekts.

Kovarianzschätzung, Regularisierung und PySR-Integration gehören zu
weiteren Schritten. Dieser Baustein ändert keine Versuchskriterien.

## Definitionen

Die Aufrufer bilden den Residualvektor in derselben Reihenfolge wie die
Zeilen und Spalten der Kovarianzmatrix:

```text
r[k] = y[k] - predicted[k], k = 0, ..., N - 1
```

| Funktion / Methode | Berechnung |
|---|---|
| `mean_squared_error(r)` | `sum(r[k]**2) / N` |
| `CovarianceLoss(C).quadratic_form(r)` | `Q = r.T @ inverse(C) @ r` |
| `CovarianceLoss(C).mean_squared(r)` | `Q / N` |
| `CovarianceLoss(C).whiten(r)` | Lösung `z` von `L @ z = r`, mit `C = L @ L.T` |

Die inverse Matrix in der Definition wird im Code nicht gebildet.
Stattdessen wird die Cholesky-Zerlegung einmal beim Erstellen des Objekts
berechnet. Weitere Kandidaten verwenden denselben Faktor:

```text
C = L @ L.T
L @ z = r
Q = z.T @ z
```

Die gewöhnliche MSE hat die quadrierte Einheit der Signalamplitude.
Hat `C` die Einheit der Amplitude zum Quadrat, sind `Q` und `Q / N`
dimensionslos. Beim bisher normierten Signal ist die Amplitude selbst
dimensionslos. Die Division durch `N` ist keine Schätzung mit korrigierten
Freiheitsgraden `N - p`.

Für `C = I` gilt `Q / N = MSE(r)`. Für weißes Rauschen mit
`C = sigma**2 * I` gilt `Q / N = MSE(r) / sigma**2`.
Diese Beziehung sagt nichts über die Güte eines noch zu entwickelnden
Kovarianzschätzers aus.

## Normierung und Modellvergleich

Bei festem `N` unterscheiden sich `Q` und `Q / N` nur um einen positiven
konstanten Faktor. Die reine Minimierung dieses Terms hat dann dieselben
Minima. Wird eine Komplexitätsstrafe addiert, muss deren Gewicht zur
Verlustskalierung passen. Beispielsweise sind
`Q + lambda_raw * complexity` und
`Q / N + lambda_mean * complexity` nur dann proportional, wenn
`lambda_mean = lambda_raw / N` gilt.

Die Quadratik ist außerdem nur ein Teil einer Gauß-Log-Likelihood:

```text
-2 * log p(r | C) = Q + log(det(C)) + N * log(2*pi)
```

Bei einer für alle Kandidaten festgehaltenen Kovarianz sind die letzten
beiden Terme konstant. Wird die Kovarianz selbst verglichen oder verändert,
ist diese Vereinfachung neu zu prüfen. Dieser Baustein implementiert
weder Logdeterminante noch eine Auswahlregel für Kovarianzmodelle.

## Eingaben und numerische Behandlung

- Residuen sind nicht leere eindimensionale, endliche reelle Arrays.
- Die Kovarianz ist eine nicht leere quadratische, endliche reelle Matrix.
- Symmetrische Einträge müssen nach Umwandlung in `float64` exakt
  übereinstimmen. Es gibt keine absolute Symmetrietoleranz, die kleine
  Kovarianzen der Größenordnung `1e-42` unbemerkt akzeptieren würde.
- Die Matrix muss positiv definit sein. Singuläre und indefinite Matrizen
  werden abgelehnt; es werden weder Jitter noch Pseudoinverse ergänzt.
- Die Kovarianzdimension muss zur Residuenlänge passen.
- Das Objekt hält einen eigenen Cholesky-Faktor. Spätere Änderungen am
  ursprünglich übergebenen Array verändern diesen Faktor nicht.

Bei späterer Kovarianzschätzung wird deren Symmetrie ausdrücklich im
Schätzverfahren behandelt. Das reine Rechenobjekt repariert keine Daten.
Der rauschfreie Grenzfall `sigma = 0` erzeugt eine singuläre Kovarianz
und ist für diese Gewichtung nicht invertierbar.

Für die quadrierte Norm wird vor dem Quadrieren durch `sqrt(N)` geteilt,
wenn der Wert pro Sample verlangt ist. So kann ein darstellbarer
Mittelwert großer Quadrate berechnet werden, ohne erst eine überlaufende
Summe zu bilden. Nicht endliche Transformationen und Verluste werden
als Fehler gemeldet. Kleine, nicht mehr in `float64` darstellbare positive
Quadrate können auf null unterlaufen; der Test bei Amplitude `1e-21`
liegt deutlich innerhalb des darstellbaren Bereichs.

Eine erfolgreiche Cholesky-Zerlegung allein garantiert keine hohe
Genauigkeit für beliebig schlecht konditionierte Matrizen. Die Wahl
einer Regularisierung bleibt ein eigener methodischer Schritt.

## Verwendung

```python
import numpy as np

from ringdown_sr.losses import CovarianceLoss, mean_squared_error

residual = np.array([2.0, 4.0])
weight = CovarianceLoss([[4.0, 2.0], [2.0, 10.0]])

mse = mean_squared_error(residual)  # 10.0
quadratic = weight.quadratic_form(residual)  # 2.0
per_sample = weight.mean_squared(residual)  # 1.0
```

Die Kovarianz wird außerhalb der Kandidatenbewertung festgelegt und das
Objekt für weitere Residualvektoren wiederverwendet.

## Referenzfälle und spätere Integration

Die Tests verwenden Identitäts- und Diagonalmatrizen, eine von Hand
invertierte `2 x 2`-Matrix sowie einen bekannten Cholesky-Faktor. Der
Test mit `C = [[2, 1], [1, 2]]` unterscheidet gleich- und gegenläufige
Residuen mit gleicher gewöhnlicher MSE. Damit werden Nebendiagonalen
tatsächlich geprüft.

Weitere Fälle prüfen gemeinsame Skalierung von Residuen und Kovarianz,
kleine Amplituden, starke Korrelation und abgelehnte ungültige Eingaben.
Für `C = [[1, rho], [rho, 1]]` ist `[1, -1]` ein Eigenvektor zum Eigenwert
`1 - rho`. Deshalb ist dessen Referenzwert `Q = 2 / (1 - rho)` und die
Konditionszahl `(1 + rho) / (1 - rho)`. Die relative Testtoleranz wird
vorab als `10 * eps(float64) * Konditionszahl` definiert.

Bei der späteren Fit- oder PySR-Integration gilt die Transformation für
das gesamte Residuum:

```text
z = inverse(L) @ y - inverse(L) @ predicted
```

Daten und Modellvorhersage werden also zusammen transformiert.
Die volle Kovarianz koppelt verschiedene Samples; ihre Integration muss
diesen Zusammenhang erhalten. Die Python-Funktionen dienen dabei als
Referenz für eine später mögliche Julia-Implementierung.

Technische Referenzen:

- [SciPy: Cholesky-Zerlegung](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.cholesky.html)
- [SciPy: Dreieckssystem lösen](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_triangular.html)
- [SciPy: multivariate Normalverteilung](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.multivariate_normal.html)
