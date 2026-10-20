# Kovarianzschätzer mit getrennten Hintergrundfenstern

Stand: 20.10.2026. Implementiert ist der reine Schätzer aus dem
[geprüften Methodenplan](covariance_method_plan.md), einschließlich
Referenz- und Fehlerprüfungen. Die Anbindung an den konfigurierbaren
Piloten, Erzeugung getrennter Hintergrundrollen und ihre Exporte folgen
im nächsten Schritt. Die bisherigen TOML-Beispiele sind unverändert.

## Schnittstelle und Annahmen

In `src/ringdown_sr/covariance_estimation.py` stehen:

- `empirical_covariance(background_train, *, mean_mode)` liefert
  `S = B_train.T @ B_train / M_train` ohne Zentrierung.
- `estimate_covariance(background_train, background_validation, *,
  alpha_candidates, kappa_max, mean_mode)` wählt eine regularisierte
  Matrix und liefert alle Kandidatendiagnosen.

`mean_mode="known_zero"` muss ausdrücklich angegeben werden. Es
bezeichnet den bekannten Populationsmittelwert null; ein empirischer
Mittelwert ungleich null wird weder abgezogen noch als Fehler behandelt.
Andere Mittelwertmodelle werden abgelehnt.

Die Eingaben sind endliche reelle zweidimensionale Matrizen mit mindestens
einer Zeile und Spalte. Jede Zeile ist ein vollständiges Rauschfenster;
die beiden Matrizen brauchen dieselbe Spaltenzahl. Unabhängige Zeilen
und Datenrollen, gleiche Rauschverteilung, Abtastung und Reihenfolge der
Samples sind Voraussetzungen des Aufrufers. Die reinen Arrays erlauben
keine Prüfung dieser Annahmen. Korrelation innerhalb eines Fensters ist
zulässig.

Es gibt keinen Zugriff auf Zufallsgeneratoren, Signalparameter, Messdaten,
Fit-Residuen oder bekannte Modellkovarianzen. Der Aufruf verändert weder
seine Eingabematrizen noch den globalen NumPy-Zufallszustand.

## Auswahl und Diagnosen

Die Skala und das Ziel werden ausschließlich aus Training bestimmt:

```text
mu = trace(S) / N
C_alpha = (1-alpha)*S + alpha*mu*I
score(alpha) = logdet(C_alpha)
               + mean_m b_validation[m].T @ inv(C_alpha) @ b_validation[m]
```

Die Inverse ist nur die mathematische Schreibweise; die Implementierung
verwendet eine Cholesky-Zerlegung und Dreieckssysteme. Die Quadratik
wird über die Validierungsfenster gemittelt, nicht durch `N` geteilt.
Der Score enthält den für die Kandidatenauswahl notwendigen
Logdeterminanten-Term; die gemeinsame Konstante `N*log(2*pi)` entfällt.

Das nicht leere Alpha-Raster enthält eindeutige endliche Werte aus
`[0,1]`. Es wird vor der Auswertung sortiert. Das Minimum des vollständigen
Scores gewinnt; exakt gleiche numerische Scores bevorzugen das kleinere
Alpha. Es gibt keine Rasterverfeinerung und keinen Refit mit den
Validierungsdaten.

Jeder Kandidat benötigt positive endliche Eigenwerte, eine Zweinorm-
Kondition `<= kappa_max`, einen endlichen Cholesky-Faktor und einen
endlichen Score. `kappa_max` ist ausdrücklich anzugeben, endlich und
größer als eins. Die Konditionsgrenze ist einschließlich Gleichheit
zugelassen und garantiert allein keine gewünschte Rechengenauigkeit.

Für Alpha null gilt vorher eine strukturelle Prüfung: Bei `n_train < N`
ist `rank(S) <= n_train < N`, daher wird der Kandidat unabhängig von
gerundeten Eigenwerten und der Konditionsgrenze abgelehnt. Eigenwert-,
Cholesky- und Score-Berechnungen werden für ihn nicht ausgeführt. Bei
`n_train >= N` ist Vollrang weiterhin nicht garantiert; dort bleiben die
numerischen Prüfungen erforderlich.

`CovarianceEstimate` enthält:

| Feld | Bedeutung |
| --- | --- |
| `raw_covariance`, `covariance` | Rohe und ausgewählte Matrix in quadrierten Eingabeeinheiten |
| `mu`, `alpha_selected` | Trainingsabhängige mittlere Varianz und gewähltes Alpha |
| `candidates` | Unveränderliches Tupel aller Kandidaten in aufsteigender Alpha-Reihenfolge |
| `n_train`, `n_validation` | Tatsächlich verwendete Fensterzahlen |
| `kappa_max`, `mean_mode` | Verwendete Konditionsgrenze und Mittelwertkonvention |
| `method` | `empirical_identity_shrinkage_holdout_v1` |

Die Ergebnisobjekte sind eingefrorene Dataclasses. Die beiden
Ergebnismatrizen haben unveränderlichen Byte-Speicher; weder spätere
Änderungen der Eingaben noch erneutes Einschalten des Schreibflags
können sie verändern.

Jeder `CovarianceCandidate` dokumentiert Alpha, `reason`, Eigenwerte,
Kondition, `cholesky_success`, Logdeterminante, mittlere
Validierungsquadratik und Score. `eligible` ist nur bei einem erfolgreich
ausgewerteten Kandidaten wahr. `None` bedeutet, dass eine Diagnose nicht
verfügbar war oder noch nicht ausgeführt wurde. Beispielsweise folgt
nach Überschreiten der Konditionsgrenze kein Cholesky- oder Score-Aufruf.
Endliche Teilergebnisse werden unmittelbar gespeichert: Scheitert etwa
die Validierungsquadratik, bleibt die bereits berechnete endliche
Logdeterminante erhalten. Ein unvollständiger Score macht den Kandidaten
weiterhin unzulässig.

Mögliche Ablehnungsgründe sind `structurally_singular`, `not_positive_definite`,
`condition_limit_exceeded`, `condition_not_finite`,
`matrix_diagnostic_failed`, `eigenvalues_out_of_range`, `cholesky_failed`,
`cholesky_nonfinite` und `validation_score_out_of_range`. Es gibt keine
stille Reparatur durch Jitter, Clipping, Pseudoinverse oder zusätzliche
Alpha-Werte.

Wenn kein Kandidat verwendbar ist, enthält `CovarianceEstimationError`
die Kandidaten, rohe Matrix und `mu`, soweit verfügbar. Bereichsfehler
bereits bei der rohen Schätzung liefern einen erklärten Fehler. Die
reine Funktion `empirical_covariance` darf eine Nullmatrix zurückgeben;
der vollständige Schätzer lehnt ihre nicht positive mittlere Varianz ab.
Ungültige Eingabeformen und Werte werden vor der Auswahl abgelehnt.

## Numerische Behandlung

Der Gram-Kern wird nach getrennter Skalierung der Eingabespalten in
einem Dreieck mit BLAS `dsyrk` berechnet und gespiegelt. Die Werte
werden anschließend mit den ursprünglichen Spaltenskalen wieder in
Kovarianzeinheiten gebracht. So müssen weder große Eingabewerte zuerst
quadriert noch sehr unterschiedlich skalierte Spalten gemeinsam normiert
werden. Die Skala `mu` wird ohne potenziell überlaufende Spur-Summe
bestimmt. Es erfolgt keine Normierung auf wahre Varianz oder Korrelation.

Die Diagonale der Schrumpfung wird als Summe nicht negativer Beiträge
berechnet, damit ein kleines explizites `alpha*mu` erhalten bleibt.
Ein Eintrag, der bereits genau der Zielvarianz entspricht, bleibt
unverändert; so erzeugt eine isotrope Matrix auch numerisch identische
Kandidaten. Die Konditionsdiagnose verwendet Eigenwerte der durch `mu`
skalierten Matrix und stellt ihre Kovarianzeinheiten wieder her.
Cholesky und Score verwenden die tatsächlich ausgewählte physische Skala.

Nicht darstellbare positive Trainingsvarianzen und nicht endliche
Zwischenergebnisse werden abgelehnt. Auch die diagnostischen Eigenwerte
müssen in `float64` darstellbar sein; endliche Matrixeinträge allein
garantieren dies nicht. Unterläufe sehr kleiner Beiträge können weiterhin
auftreten. Es gibt keine allgemeine Bitidentitäts- oder Genauigkeitsgarantie
für beliebig schlecht konditionierte Matrizen.

## Kleines handrechenbares Beispiel

Aus dem Projektordner:

```bash
uv run --locked python - <<'PY'
from ringdown_sr.covariance_estimation import estimate_covariance

result = estimate_covariance(
    [[1, 0], [-1, 0], [0, 2], [0, -2]],
    [[1, 0], [0, 2]],
    alpha_candidates=[1, 0.4, 0],
    kappa_max=10,
    mean_mode="known_zero",
)
print("Alpha:", result.alpha_selected)
print("Kovarianz:")
print(result.covariance)
for candidate in result.candidates:
    print(f"Alpha {candidate.alpha}: Score {candidate.score:.9f}")
PY
```

Das Ergebnis ist Alpha `0` mit `diag(0.5,2)`. Die Scores betragen
`2.000000000`, `2.108955288` und `2.446287103`. Es handelt sich um eine
deterministische Referenzrechnung, keine Aussage über ein bevorzugtes
Alpha für verrauschte Ringdown-Daten.

## Prüfumfang und nächste Integration

Die Tests sichern insbesondere die Referenzfälle aus Methoden- und
Implementierungsreview ab: einen nicht verschwindenden Stichprobenmittelwert
ohne Zentrierung, das vollständige Score-Minimum und einen späteren
zulässigen Gewinner bei allen sechs Rasterpermutationen. Eine handinvertierte
volle Matrix mit Validierungszeile `[1,0]` unterscheidet korrektes von
transponiertem Cholesky-Whitening: Die erwartete Quadratik ist `0.5`,
die falsche Orientierung ergäbe `0.4`.

Nicht achsenparallele Trainingsmatrizen mit weniger Zeilen als Spalten
prüfen die strukturelle Ablehnung bei Alpha null auch mit `kappa_max=1e20`.
Bei Training `[[1e-150]]` und Validierung `[[1e150]]` bleibt trotz
überlaufender Quadratik die Logdeterminante `-300*log(10)` erhalten.
Weitere Fälle betreffen Eigenwert-Whitening, Rangmangel, Gleichstände,
inklusive Konditionsgrenze, gemeinsame Skalierung, sehr kleines Alpha,
Bereichsfehler und unveränderliche Ergebnisse.

Zusätzlich wurden die beiden Fehlervarianten nur im Arbeitsspeicher
ausgeführt: Der neue volle Matrixreferenzfall scheitert bei transponiertem
Whitening; alle sechs Rasterpermutationen des späteren Gewinners scheitern
bei der Auswahl des ersten zulässigen Kandidaten. Diese absichtlich
fehlgeschlagenen Prüfungen belegen, dass die ergänzten Referenzen die
beiden im Review nachgewiesenen Testlücken schließen.

Die statistische Kontrolle verwendet für `rho=-0.65,0,0.65` jeweils
`R=2000` unabhängige Schätzungen aus `M=32` Fenstern mit `N=4` und
`sigma=0.1`. Die Mittelwerte der rohen Matrix werden mit den analytischen
Gauß-Standardfehlern aus dem Methodenplan verglichen. Diese Prüfung
betrifft die rohe Schätzung, keine Unverzerrtheit der Schrumpfung und
keine Rekonstruktionsleistung.

Die nächste Integration muss Hintergrundrollen getrennt erzeugen,
deren gemeinsame Rauschverteilung sicherstellen, `C_hat` einmal bestimmen
und für alle Kandidaten eines Fits festhalten. Kontrollfenster und wahre
Kovarianz dürfen die Auswahl nicht beeinflussen. Die bestehende CLI hat
noch keinen Modus für geschätzte Kovarianzen; ein erfolgreicher Unit-Test
ist kein Nachweis einer bereits vorhandenen Pilotintegration.

Technische Referenzen:

- [SciPy: dsyrk](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.blas.dsyrk.html)
- [SciPy: solve_triangular](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_triangular.html)
- [NumPy: eigvalsh](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigvalsh.html)
