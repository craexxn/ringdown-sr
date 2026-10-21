# Tatsächliche Konstantenoptimierung im Julia-Backend

Stand: 21.10.2026. Zweiter abgegrenzter Baustein des
[Methodenplans](symbolic_regression_method_plan.md), nach dem
[Julia-Verlustkern](julia_loss_kernel.md).

`julia/test/constant_optimization.jl` prüft die tatsächliche Funktion
`SymbolicRegression.optimize_constants` mit `FixedWindowLoss` und dem
gepinnten SymbolicRegression 2.5.1 / Optim 2.2.2. Es werden feste Bäume mit
freien Konstanten angepasst. Die Struktur der Formel wird dabei vorgegeben;
eine freie PySR-Suche oder eine neue Produktionsschnittstelle ist damit
noch nicht implementiert.

## Aufruf und beobachteter Optimierer

Jeder Referenzlauf erstellt einen vollständigen Float64-Datensatz mit Zeit
in Sekunden und dimensionsloser Ausgabe sowie ein frisches `PopMember` aus
einer Kopie des Startbaums. Derselbe vollständige Callback bewertet sowohl
die Startwerte als auch die Konstantenänderungen im Backend.

Eingestellt sind `optimizer_algorithm=BFGS` mit Backtracking,
`autodiff_backend=nothing`, `batching=false`, 100 Optimiereriterationen und
keine zufälligen Neustarts. Die festen Startpunkte werden einzeln geprüft.
Dies sind Prüfbudgets; das vorgeschlagene Suchbudget aus dem Methodenplan
wird dadurch nicht geändert. Ein explizites lokales `Xoshiro` wird an den
Backend-Aufruf übergeben. Es werden keine Zufallsdaten erzeugt.

SymbolicRegression überschreibt bei genau einer reellen Konstanten die
eingestellte Methode durch Newton. Bei zwei Konstanten verwendet es BFGS.
Der Optim-Callback beobachtet den tatsächlichen Zustandsdatentyp
`NewtonState` beziehungsweise `BFGSState` und kopiert Parameter und
Gradientennorm. Jeder Referenzlauf muss den erwarteten Zustand und
mindestens einen Anpassungsschritt zeigen. Die Pfadprüfung beruht somit
auf den tatsächlich ausgeführten Optimierer-Callbacks.

Bei `autodiff_backend=nothing` übergibt das Backend nur die Zielfunktion
an Optim. Dessen gepinnter Standard verwendet zentrale finite Differenzen;
Newton benötigt zusätzlich eine numerische Hesse-Matrix. Die Prüfung
liefert keine selbst berechneten Gradienten an den Backend-Optimierer.

## Unabhängige Referenzen

Für `h(t)=theta`, `t=[0,1]`, `y=[1,3]` und
`C=[[4,2],[2,10]]` gelten:

| Gewichtung | Erwartetes theta | Minimaler Verlust | Starts |
| --- | --- | --- | --- |
| Volle Kovarianz | 7/5 | 1/5 | -1 und 5 |
| Nur Diagonale von C | 11/7 | 1/7 | -1 und 5 |
| Gewöhnliche MSE | 2 | 1 | -1 und 5 |

Für `h(t)=a+b*t`, `t=[0,1,2]`, `y=[0,1,0]` und

```text
C = [[2,1,0],
     [1,2,0],
     [0,0,1]]
```

gelten die bereits im Methodenreview hergeleiteten Parameter:

| Gewichtung | a | b | Minimaler Verlust |
| --- | --- | --- | --- |
| Volle Kovarianz | 0 | 1/7 | 4/21 |
| Nur Diagonale von C | 4/11 | -1/11 | 4/33 |
| Gewöhnliche MSE | 1/3 | 0 | 2/9 |

Jede Gewichtung wird von `(1,-1)` und `(-1,1)` gestartet. Insgesamt entstehen
zwölf Referenzläufe. Die Nebendiagonalkopplung verändert beide Minima
gegenüber den Diagonal- und MSE-Kontrollen. Die Tests verlangen die
Anpassung der Konstanten, einen gesunkenen Verlust und Übereinstimmung
des gespeicherten Verlusts mit einer erneuten Baumauswertung.

## Vorab festgelegte Toleranzen

- Optim-Abbruchvorgabe: Unendlichnorm des numerischen Gradienten höchstens
  `1e-8`; die letzte beobachtete Gradientennorm wird zusätzlich geprüft.
- Parametervergleich: `atol=1e-6`, `rtol=0`.
- Vergleich mit dem analytischen Minimalverlust: `atol=1e-11`, `rtol=0`.
- Numerischer Replay bei denselben optimierten Parametern: wesentlich
  engere Rundungsschranken, siehe unten.

Alle Referenzverluste sind strikt konvexe Quadrate. Für die linearen Fälle
gilt `H=2*X.T*C^-1*X/N`; beim Konstantenmodell besteht X nur aus Einsen.
Der kleinste Eigenwert aller hier verwendeten Hesse-Matrizen ist größer
als 0,26. Bei exaktem Gradienten würde die Abbruchschranke den Parameterfehler
in Zweinorm auf weniger als `6e-8` begrenzen. Die Parameterprüfung lässt
zusätzlich die numerische Differentiation zu. Der größte Eigenwert ist
kleiner als 4,78; bei komponentenweisem Fehler `1e-6` liegt der quadratische
Verlustüberschuss unter `4,8e-12`. Die Verlustschranke `1e-11` berücksichtigt
dies und Float64-Rundung. Diese Grenzen gelten für diese Kontrollfälle,
nicht als allgemeine Zusicherung für beliebige symbolische Ausdrücke.

## Kontexttrennung, Einheiten und Fehler

- Ein gewichteter Kontext A, ein gewöhnlicher Kontext B und erneut A
  werden im selben Julia-Prozess optimiert. A behält Faktor und Daten;
  der übergebene Startbaum bleibt erhalten. Dies prüft Kontexttrennung
  innerhalb eines Prozesses. Die geplante Unterprozessisolation der
  späteren SR-Arme ist weiterhin offen.
- Ein bereits exakt passender Konstantenbaum behält Verlust null,
  einschließlich des tatsächlichen Newton-Pfads.
- Der tatsächliche Backend-`Evaluator` erhält einen dimensionswidrigen
  Baum `a+t` bei dimensionslos geforderter Ausgabe. Er liefert auch bei
  Einheitenstrafe null und geänderten Konstanten `Inf`, sowohl ohne als
  auch mit Regularisierungsflag. Nicht endliche Konstanten bleiben
  unzulässig; ein falsches Fenster erzeugt weiterhin einen Eingabefehler.
  Dies ist eine Prüfung des Optimierer-Evaluators, keine Behauptung einer
  erfolgreichen Optimierung einer überall unendlichen Zielfunktion.

Der vom Backend zurückgegebene Evaluationszähler wird auf positive Werte
geprüft. Er wird nicht als vollständiger Aufwand einschließlich aller
numerischen Ableitungsaufrufe oder als Konvergenzstatus ausgegeben.

## Python-Nachrechnung und Ausführen

`scripts/check_julia_loss.py` führt auch diese Julia-Tests aus. Anschließend
werden alle zwölf optimierten Referenzen unabhängig in NumPy geprüft:

```text
beta = solve(X.T @ solve(C, X), X.T @ solve(C, y))
r = y - X @ beta
loss = r.T @ solve(C, r) / N
```

Die gewöhnliche MSE verwendet dafür `C=I`. Diese kleinen direkten
Normalgleichungen dienen ausschließlich der unabhängigen Kontrolle;
sie ersetzen nicht den Backend-Optimierer und sind keine Vorgabe für
das spätere allgemeine numerische Verfahren.

Zusätzlich werden Julia-Vorhersagen aus den optimierten Konstanten in
Python rekonstruiert und ihr tatsächlicher Verlust unabhängig nachgerechnet.
Dafür gelten `rtol=64*eps(float64)*cond(C)`, `atol=0` beim Verlust und
jeweils `32*eps(float64)` beim relativen und absoluten Vorhersagevergleich
dieser Referenzdaten mit Größenordnung eins.

```bash
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_julia_loss.py
```

Der vorhandene GitHub-Prüfschritt führt denselben Befehl aus. Die Julia-
und Replay-Prüfungen werden getrennt von den Python-pytest-Fällen gezählt.
Neue Abhängigkeiten oder Änderungen an Lockdateien sind nicht erforderlich.

## Grenzen und nächste Schritte

Der Nachweis betrifft die Konstantenanpassung fest vorgegebener Strukturen
im echten Julia-Backend. `PySRRegressor.fit`, die Schnittstelle für eine
freie Suche, Prozessisolation, Alias-/Score-Export und Ergebnisintegration
stehen weiter aus. Ebenso offen sind neue Manjaro-/WSL2-Nutzerprüfungen
dieses Bausteins und die wissenschaftliche Leistungsbewertung.

Versionsgebundene Primärquellen:

- [SymbolicRegression 2.5.1: ConstantOptimization.jl](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/ConstantOptimization.jl)
- [Optim 2.2.2: Optimierung und Callback](https://github.com/JuliaNLSolvers/Optim.jl/blob/v2.2.2/src/multivariate/optimize/optimize.jl)
- [Optim 2.2.2: Standard für numerische Differentiation](https://github.com/JuliaNLSolvers/Optim.jl/blob/v2.2.2/src/multivariate/optimize/interface.jl)
