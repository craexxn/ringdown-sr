# Julia-Verlustkern mit expliziter Dimensionsprüfung

Stand: 21.10.2026. Erster ausführbarer Baustein des
[geprüften PySR-Methodenplans](symbolic_regression_method_plan.md).
Die Umsetzung liegt in `julia/src/RingdownSRLoss.jl`. Sie verbindet eine
feste Fensterdefinition, gewöhnliche beziehungsweise kovarianzgewichtete
Residualverluste und eine ausdrückliche Dimensionsprüfung für Kandidaten.

Die Tests prüfen diesen Kern sowie den vollständigen Verlust-Dispatcher
des gepinnten SymbolicRegression-Backends. Die Anbindung an
`PySRRegressor.fit`, freie Suchläufe und neue Ergebnisformate folgen
in eigenen Schritten. Die tatsächliche Newton-/BFGS-Konstantenoptimierung
wird in einer [separaten Erweiterung](constant_optimization.md) geprüft.
Die bekannte lineare Mehrkonstantenreferenz wird hier nur ausgewertet;
ihr Optimum wird noch nicht durch einen Optimierer ermittelt.

## Festes Fenster und Zielfunktion

`FixedWindowLoss(time_s, observed; covariance=nothing)` übernimmt eigene
Float64-Kopien einer endlichen, nicht leeren Zeit- und Messwertfolge.
Die Zeitpunkte sind nicht negativ und werden in Sekunden interpretiert;
die Signalamplitude ist im bisherigen Pilot dimensionslos.
Samplezahl und Reihenfolge bleiben unverändert. Die Funktion sortiert,
zentriert, normiert oder interpoliert keine Daten. Eine gleichmäßige
Abtastung wird vom Rechenkern nicht zusätzlich vorausgesetzt.

Ohne Kovarianz ist der Verlust die gewöhnliche MSE. Mit Kovarianz gilt:

```text
r = observed - prediction
C = L * L', L unteres Dreieck
L * z = r
loss = (norm(z) / sqrt(N))^2 = r' * C^-1 * r / N
```

Der untere Faktor wird einmal beim Erstellen der Instanz berechnet.
Die Matrix muss zur Fensterlänge passen, nach Float64-Konvertierung exakt
symmetrisch sein und eine erfolgreiche Cholesky-Zerlegung erlauben.
Die Eingaben werden nicht symmetrisiert oder regularisiert; es gibt
keinen Jitter, keine Pseudoinverse und keinen Refit aus Residuen.
Der Rechenkern setzt keine zusätzliche Konditionsgrenze. Die
Regularisierung und Zulässigkeit einer geschätzten Matrix bleiben Aufgabe
des vorgeschalteten Schätzers; eine erfolgreiche Zerlegung allein ist
keine Garantie hoher Genauigkeit bei schlechter Kondition.

Die Normberechnung vermeidet eine zuerst gebildete Quadratsumme und teilt
vor dem abschließenden Quadrieren durch `sqrt(N)`. Ein exakt verschwindendes
Residuum liefert Verlust null; es wird kein Epsilon ergänzt.
Die Zeitmerkmale werden nicht mit L transformiert. Es wird weder
`h(L^-1*t)` noch die falsche Quadratik `norm(C^-1*r)^2` berechnet.

## Schnittstellen und Fehlervertrag

| Aufruf | Verhalten |
| --- | --- |
| `residual_loss(objective, residual)` | Numerische MSE beziehungsweise Q/N für einen expliziten Residualvektor; keine Formel- oder Einheiteninterpretation |
| `candidate_loss(objective, tree, options)` | Dimensionsprüfung, Auswertung des Baums an allen ursprünglichen Zeiten, vollständiges Residuum und Verlust |
| `objective(tree, dataset, options)` | Vollständiger Callback mit zusätzlichen Prüfungen des übergebenen Backend-Datensatzes |
| `objective(tree, dataset, options, idx)` | Backend-Schnittstelle für explizite Indizes; nur `idx=nothing` ist zulässig und delegiert an den dreistelligen Callback |
| `n_samples(objective)` | Unveränderte Fensterlänge |

Der vollständige Callback akzeptiert nur einen Float64-Regressionsdatensatz
mit genau einem Zeitmerkmal. Er prüft Samplezahl, vollständige Zeit- und
Messwerte einschließlich Reihenfolge sowie die geparsten Einheiten
Sekunden und dimensionslose Ausgabe gegen das beim Erstellen festgelegte
Fenster. Geänderte, gewichtete oder gebatchte Datensätze werden abgelehnt.
Auch ein Batch mit allen Samples gilt als Batch und wird abgelehnt.
Zusätzlich bietet der Kern den vierstelligen Callback an: Der Backend-Dispatcher
reicht explizite `idx`-Argumente nur an diese Schnittstelle weiter. Jeder Wert
außer `nothing` führt zu `ArgumentError`, auch vollständige, umsortierte oder
leere Indexlisten und Indexbereiche. `idx=nothing` durchläuft unverändert
die vollständige Datensatz- und Kandidatenprüfung. Tests prüfen beide
Batch-Zugänge über den tatsächlichen `SymbolicRegression.eval_loss`-Dispatcher:
explizite Indizes und Indizes aus einem `SubDataset`.
Der spätere PySR-Adapter muss ausdrücklich `batching=False` setzen.

Der Kern unterstützt die getesteten Float64-`Node`-Bäume und normale
`Expression`-Wrapper. Vor den Backend-Aufrufen prüft er Merkmals- und
Operatorindizes, da Teile des Backends ungeprüfte Arrayzugriffe verwenden.

| Fall | Ergebnis |
| --- | --- |
| Ungültige Fenster-/Matrix-/Residualeingabe, etwa boolesche Werte, nicht endliche Daten, falsche Dimension oder singuläre Matrix | `ArgumentError` |
| Fehlerhafter Callback-Datensatz oder unzulässiger Baumvertrag, etwa anderes Zeitmerkmal oder Float32-Baum | Fehler wird weitergegeben; kein Ersatz durch Inf |
| Zulässiger Residualvektor mit numerisch nicht darstellbarem Whitening oder Verlust | `residual_loss` wirft `OverflowError` |
| Dimensionsverletzung, nicht endlicher Kandidat, unvollständige Baumauswertung, nicht endliche Vorhersage oder numerischer Überlauf während Kandidatenbewertung | Kandidat erhält `Inf` |
| Unerwarteter Programmierfehler | Wird weitergegeben; keine pauschale Ausnahmebehandlung |

Während der Kandidatenbewertung werden ausschließlich numerische
`DomainError`- und `OverflowError`-Ausnahmen in `Inf` überführt.
Der Callback prüft seinen Datensatz vorher, sodass falsche Eingaben auch
bei einem bereits unzulässigen Kandidaten sichtbar bleiben.

Jede Instanz hält ihre eigenen Daten und ihren eigenen Faktor; öffentliche
Operationen verändern diese nicht. Die internen Felder sind kein
Mutations-API. Ein Wechsel der Kovarianz verlangt eine neue Instanz.
Die spätere Prozessisolation der SR-Arme ist noch nicht implementiert.

## Einheitenprüfung im eigenen vollständigen Loss

Der interne Backend-Prüfer `violates_dimensional_constraints` wird
ausdrücklich aufgerufen. Das ist erforderlich, weil SymbolicRegression
2.5.1 beim eigenen vollständigen Loss die Dimensionsregularisierung des
Standardpfads umgeht. Tests rufen den echten `eval_loss`-Dispatcher mit
diesem Callback auf und prüfen die Zurückweisung eines numerisch perfekt
passenden, aber dimensionswidrigen Baums auch bei Einheitenstrafe null.

Der feste Datensatz trägt `X_units=["s"]`, `y_units="1"`.
Beispielsweise wird `exp(b*t)` mit einer möglichen inversen Zeiteinheit
der freien Konstante zugelassen, `exp(t)` dagegen ausgeschlossen.
`h(t)=t` ist bei dimensionsloser Ausgabe auch dann unzulässig, wenn die
Messwerte numerisch genau den Zeitwerten entsprechen.
`dimensionless_constants_only=true` verändert diese Zulässigkeit und
wird als Gegenprobe getestet; der Methodenplan sieht False vor.

Die Wildcard-Einheitenanalyse des Backends prüft mögliche Dimensionen
freier Konstanten. Sie beweist keine physikalisch richtige Formel und
liefert keine vollständige eindeutige Konstanteneinheitenzuordnung.
Die verwendeten internen Dataset-/Dimensionsschnittstellen sind an
SymbolicRegression 2.5.1 gebunden.

## Unabhängige Referenzen und Python-Replay

`julia/test/runtests.jl` enthält unter anderem:

- Eine von Hand invertierte volle 2×2-Matrix mit `Q/N=1/4`;
  transponiertes Whitening ergäbe fälschlich `1/5`.
- Gleich- und gegenläufige Residuen mit gleicher MSE, aber
  `Q/N=1/3` beziehungsweise 1 unter derselben vollen Kovarianz.
- Identität, gewöhnliche MSE, gemeinsame Amplituden-/Kovarianzskalierung
  einschließlich `1e-21`, starke Korrelation, einen darstellbaren großen
  Mittelwert und Verlust null.
- Auswertung der linearen Referenz bei `a=0, b=1/7`, `Q/N=4/21`;
  dies ist ausdrücklich kein Nachweis der BFGS-Anpassung.
- Ursprüngliche Zeitachse, gültige/ungültige Dimensionen, zulässige
  gedämpfte Schwingung sowie numerische Kandidatenfehler.
- Den echten vollständigen Backend-Loss-Pfad, Ablehnung veränderter
  und gebatchter Daten sowie expliziter Indizes, unveränderten Verlust bei
  `idx=nothing`, Originaldatenkopien und unabhängige Instanzen.

Die einfachen Matrixreferenzen verwenden relative Schranken von
32 beziehungsweise 64 Maschinenpräzisionen. Für die starke Korrelation
gilt wie beim Python-Referenzkern `10*eps(float64)*cond(C)`.
Kleine Abweichungen direkter Formel- und Baumauswertung werden gesondert
begrenzt. Die Tests verlangen keine zufällige Formelentdeckung.

`scripts/check_julia_loss.py` führt die Julia-Tests im gepinnten Projekt aus
und vergleicht anschließend zehn Residualfälle mit dem vorhandenen
[Python-Rechenkern](losses.md). Diese zusätzliche Sprachvergleichsprüfung
nutzt `rtol=16*N*eps(float64)*cond(C)`, `atol=0`, bei gewöhnlicher MSE
Konditionsfaktor 1. Sie ersetzt nicht die unabhängigen Handreferenzen.
Die Eingaben sind fest vorgegeben; es wird kein Zufallsgenerator verwendet.

## Ausführen und verbleibende Prüfungen

Aus dem Projektordner:

```bash
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_julia_loss.py
```

Der Runner benötigt den vorhandenen Startweg mit gesetztem
`PYTHON_JULIACALL_PROJECT` und prüft das tatsächlich aktive Projekt.
Er meldet Fehler mit einem fehlgeschlagenen Prozess. Julia-Tests und
Python-Replay laufen als eigener Schritt im GitHub-Workflow nach dem
Umgebungscheck. Sie werden nicht stillschweigend in die bisherige
pytest-Anzahl aufgenommen. Der erste Lauf kann vorkompilieren.

Für diese Erweiterung wurden keine Abhängigkeiten oder Lockdateien
geändert. Das KI-gestützte Code- und Methodenreview dieses Kerns ist erfolgt;
die Batch-Abwehr wurde entsprechend ergänzt. Die nächste Erweiterung prüft
die [tatsächlichen Konstantenoptimierer](constant_optimization.md).
Die PySR-Suchanbindung und Prozessisolation stehen weiter aus.
Die bisherigen [Manjaro-/WSL2-Nachweise](portability.md) gelten für den
klassischen Schema-2-Piloten. Lokale Nutzerprüfungen des neuen Julia-Kerns
sind zusätzlich erforderlich; Hauptversuche und Leistungsvalidierung
sind weiter offen.
