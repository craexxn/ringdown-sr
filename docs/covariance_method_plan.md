# Methodenplan: Kovarianzschätzung aus getrennten Hintergrunddaten

Stand: 20.10.2026. **Nach methodischem Review überarbeiteter Plan;
noch keine wissenschaftliche Leistungsvalidierung.** Das Review
zu Commit `897a8ce` bewertete die Verfahrenswahl als tragfähig. Die beiden
Lücken im Prüfplan sowie die zusätzlichen Hinweise sind unten eingearbeitet
und in Abschnitt 10 zugeordnet. Die Kontrollvorgaben legen keine
Einstellungen der Hauptversuche fest.

Teilumsetzung: Der [reine Kovarianzschätzer](covariance_estimation.md) mit
Referenz-, Fehler- und statistischen Funktionstests ist implementiert.
Der Plan beschreibt außerdem die noch ausstehende Erzeugung der
Hintergrundrollen und ihre Anbindung an den konfigurierbaren Piloten.

## 1. Ziel und begrenzter erster Schritt

Der [bisherige Pilot](configured_pilot.md) kann gewöhnliche Fits und Fits
mit bekannter Modellkovarianz vergleichen. Der nächste Schritt soll eine
aus separaten, signalfreien Hintergrunddaten geschätzte Kovarianz während
des gesamten Fits festhalten. Die vorhandenen Definitionen von Residuen,
Einheiten und Cholesky-Whitening aus [Verlustfunktionen](losses.md) und
[Referenzfit](reference_fit.md) bleiben maßgeblich.

Vorschlag für die erste Erweiterung: empirische Kovarianz unabhängiger
synthetischer Rauschfenster mit Schrumpfung zu einer skalierten
Einheitsmatrix. Die Schrumpfungsstärke wird auf weiteren Hintergrundfenstern
gewählt. Das ergibt einen allgemeinen Matrixschätzer als kontrollierbaren
Ausgangspunkt, ohne die AR(1)-Formel in den Schätzer einzubauen.

Die erste Erweiterung betrachtet ausschließlich die bestehenden
mittelwertfreien weißen beziehungsweise stationären AR(1)-Gaußmodelle.
PySR-Integration, echte Detektordaten, unbekannter Mittelwert, Glitches,
Nichtstationarität und statistische Hauptversuche folgen getrennt.
Eine geringe Kovarianzabweichung oder bessere Hintergrundvorhersage
garantiert keine bessere Ringdown-Rekonstruktion.

## 2. Abgewogene Alternativen

| Ansatz | Nutzen | Grund für die vorgeschlagene Einordnung |
| --- | --- | --- |
| Empirische volle Matrix plus skalierte Identität | Positiv semidefiniter Ausgangspunkt, einfache Herleitung, keine vorgegebene AR-Ordnung | Erster Vorschlag; benötigt genügend unabhängige Fenster und nutzt Stationarität noch nicht zur Parameterreduktion |
| Ledoit-Wolf oder OAS | Analytische Wahl einer Schrumpfungsstärke statt separater Auswahlmenge | Sinnvolle spätere Vergleichsverfahren; andere Ableitungs-/Optimalitätskriterien als unser Hintergrund-Score, nicht automatisch dieselbe Methode [1–3] |
| Parametrisches AR(1) aus geschätztem `sigma` und `rho` | Wenige Parameter, effizient bei passendem Modell | Nur strukturierter Kontrollvergleich: setzt die richtige Rauschfamilie voraus und ist deshalb kein allgemeiner Schätzer |
| Autokovarianz-/Toeplitz-Schätzer, gegebenenfalls Tapering oder Spektralschätzer | Nutzt Stationarität; geeignetes Thema für eine lange zusammenhängende Hintergrundzeitreihe | Eigene Entscheidungen zu Zeitabhängigkeit, Lagfenster, positiver Semidefinitheit und Rändern nötig; nicht mit unabhängigen Fensterkopien gleichsetzen [4] |

Die Literatur begründet die Schrumpfungsfamilie [1, 2]. Der nachfolgende
Holdout-Entwurf ist unsere zu prüfende Auswahlregel, nicht die analytische
Ledoit-Wolf- oder OAS-Formel. Aus deren Ergebnissen folgt keine
Optimalitätsgarantie für diesen Pilot. Die unabhängigen Fenster sind eine
explizite Voraussetzung; die Zeitreihenliteratur behandelt davon
verschiedene Beobachtungssituationen [4].

## 3. Datenrollen und zulässige Information

Jede Zeile einer Hintergrundmatrix ist ein vollständiger Rauschvektor
der Länge `N`. Seine Komponenten dürfen zeitlich korreliert sein.
Unabhängigkeit wird zwischen den Zeilen und zwischen den Datenrollen
vorausgesetzt, nicht zwischen den Samples innerhalb eines AR(1)-Fensters.
Im Kontrollfall stammen alle drei Hintergrundrollen und das
Signalrauschen aus derselben Rauschverteilung: gleiche Modellfamilie,
bekannter Nullmittelwert, marginale Rauschstärke und gegebenenfalls
AR(1)-Korrelation. Alle Fenster verwenden dieselbe Samplezahl `N`,
Abtastrate und Sample-Reihenfolge. Unterschiedlich sind ihre unabhängigen
Realisierungen und vorgesehenen Datenrollen, nicht die zugrunde liegende
Verteilung. Diese Übereinstimmung stellt der Orchestrator sicher; die
wahren Rauschparameter bleiben für den Schätzer unzugänglich.

| Datenrolle | Verwendung | Für Auswahl oder Fit gesperrte Information |
| --- | --- | --- |
| `background_train`, Form `(M_train, N)` | Empirische Matrix und Schrumpfungsziel schätzen | Keine Messdaten, Residuen, Signalparameter oder wahre Kovarianz |
| `background_validation`, Form `(M_validation, N)` | Schrumpfungsstärke anhand Hintergrund-Score wählen | Keine Wiederverwendung als Schätz- oder abschließende Prüfmenge |
| `background_check`, Form `(M_check, N)` | Eingefrorenen Schätzer nachträglich kontrollieren | Keine nachträgliche Änderung von Raster, Schätzer oder Auswahlregel |
| `observed = signal + noise_for_signal` | Bekannte Ringdown-Formel fitten | Nicht zur Kovarianzschätzung oder Regularisierungswahl verwenden |
| Signalwahrheit und `C_true` | Datenerzeugung, ausdrücklich gekennzeichneter bekannter Kontrollfit und abschließende Diagnose | Kein Zugriff im Schätzer, Selektor oder im Fit mit geschätzter Kovarianz |

Alle Fit-Varianten eines Vergleichs bekommen dieselben Messdaten, Grenzen,
Startpunkte und Rechenbudgets. Die geschätzte Matrix darf weder pro
Startpunkt noch pro Kandidatenformel geändert werden. Wahre `sigma`- oder
`rho`-Werte gelangen nicht über eine Hilfsschnittstelle in den Schätzer.

Im synthetischen Pilot wird jedes Hintergrundfenster unabhängig erzeugt,
bei AR(1) einschließlich eines eigenen stationären Anfangswerts. Es
werden keine überlappenden Ausschnitte einer einzigen Folge als unabhängig
gezählt. Auch unmittelbar benachbarte, nicht überlappende Abschnitte eines
korrelierten Prozesses sind nicht automatisch unabhängig. Für spätere
Detektordaten sind Stationaritätsbereich, Abstand, zeitliche Trennung und
effektive Hintergrundinformation gesondert zu begründen [4].

Die Hintergrundrollen erhalten feste, dokumentierte `SeedSequence`-
Kindzweige und eigene PCG64-Generatoren [5]. Rollenkennungen und Ableitung
werden versioniert, sodass zusätzliche Diagnosen bestehende Zufallsströme
nicht verschieben. Vorschlag: derselbe Hintergrund-Wurzelwert mit
ausdrücklichem `spawn_key=(role_id,)` für jede feste Rolle. Der bisherige
Messdaten-Aufruf bleibt erhalten;
geänderte Hintergrundmengen dürfen seine Samples nicht verändern.
Unterschiedliche Seeds allein sind kein empirischer Unabhängigkeitsnachweis.

## 4. Mittelwert und empirische Matrix

Der erste Schätzer setzt den **bekannten Populationsmittelwert null** der
synthetischen Modelle voraus. Ein zufällig nicht exakt nullwertiger
Stichprobenmittelwert führt weder zu Zentrierung noch zur Ablehnung.
Für die Trainingszeilen `b_m` gilt:

```text
S = (1/M_train) * sum_m b_m @ b_m.T
  = B_train.T @ B_train / M_train

E[S] = C_true                         bei E[b_m] = 0
v.T @ S @ v = mean_m (v.T @ b_m)^2 >= 0
rank(S) <= min(M_train, N)
```

`S` ist in diesem Umfang eine unverzerrte Kovarianzschätzung; ohne den
bekannten Nullmittelwert wäre sie eine zweite Momentenmatrix. Es wird
kein `M_train - 1` verwendet, weil kein Mittelwert geschätzt wurde.
Bei `M_train < N` ist `S` mathematisch singulär. Vollrang bei größerem
`M_train` ist nicht allein durch die Samplezahl garantiert.
Alpha null muss deshalb bei `M_train < N` schon strukturell abgelehnt
werden, selbst wenn gerundete Eigenwerte und eine Cholesky-Zerlegung
scheinbare positive Definitheit anzeigen.

Insbesondere wird nicht jeder Zeile ihr eigener zeitlicher Mittelwert
abgezogen: Das würde das Modell verändern, den konstanten Vektor
entfernen und eine singuläre Projektion erzeugen. Ein späterer Modus mit
unbekanntem Mittelwert benötigt einen eigenen Plan für dessen Schätzung,
Subtraktion, zusätzliche Unsicherheit und konsistente Fit-Behandlung.
Er wird nicht stillschweigend durch eine Bibliotheksvoreinstellung
aktiviert; zur Zentrierungskonvention siehe auch [2].

Die Matrix hat die quadrierte Signaleinheit. Es erfolgt keine Normierung
auf Korrelation oder auf die wahre Varianz. Im Schätzer wird jeder
symmetrische Eintrag einmal bestimmt und gespiegelt, sodass das Ergebnis
exakt symmetrisch ist. Der bestehende Verlustkern repariert weiterhin
keine asymmetrischen Eingaben.

## 5. Ausdrückliche Regularisierung

Für die ausschließlich aus Trainingsdaten bestimmte Skala gilt:

```text
mu = trace(S) / N
T = mu * I
C_alpha = (1 - alpha) * S + alpha * T, 0 <= alpha <= 1
```

Bei `mu > 0` und `alpha > 0` ist die Matrix mathematisch positiv definit:
`lambda_min(C_alpha) >= alpha*mu`. Das Ziel bewahrt die mittlere Varianz,
schrumpft aber Nebendiagonalen und kann echte Korrelation verzerren.
Bei `alpha = 1` bleibt `mu*I`; der Fit hat dann dieselbe ungewichtete
Zielfunktionsgeometrie bis auf einen positiven Skalenfaktor. Daraus folgt
keine Garantie bitgleicher Optimierungsergebnisse.

Jeder Kandidat benötigt eine erfolgreiche Cholesky-Zerlegung und eine
endliche positive Eigenwertdiagnose. Zusätzlich wird eine ausdrücklich
konfigurierte Grenze `kappa_max > 1` für die Zweinorm-Kondition vorgeschlagen:
`kappa_2 = lambda_max / lambda_min`. Ein Überschreiten macht den Kandidaten
unzulässig und wird protokolliert, statt ihn nachträglich zu verändern.
Der Kontrollwert `1e8` ist ein numerischer Grenzwert, keine universelle
Genauigkeitsgarantie. Die Grenze selbst ist einschließlich ihres
zugelassenen Gleichheitsfalls separat zu prüfen.

Für positiv semidefinites `S`, `mu > 0` und `0 < alpha <= 1` gilt außerdem:

```text
lambda_max(S) <= trace(S) = N*mu
lambda_min(C_alpha) >= alpha*mu
kappa_2(C_alpha) <= ((1-alpha)*N*mu + alpha*mu) / (alpha*mu)
                 = 1 + N*(1-alpha)/alpha
```

Bei `N=128` und dem kleinsten positiven Rasterwert `alpha=0.001` beträgt
diese Schranke `127873`, deutlich weniger als `1e8`. Der normale
Kontrolllauf reizt die Konditionsgrenze mit seinen positiven Alpha-Werten
mathematisch daher nicht aus. Für Alpha null gilt die Schranke nicht;
insbesondere ist die rohe Matrix bei `M_train < N` singulär. Die
explizite Konditionsprüfung bleibt in allen Fällen erforderlich.

Nicht endliche Werte, `mu <= 0`, nicht darstellbare Kovarianzskalen oder
eine vollständig unzulässige Kandidatenmenge ergeben einen erklärten
Schätzfehler. Es gibt keinen automatischen Ersatz durch bekannte
Kovarianz, andere Alpha-Werte, Jitter, Eigenwert-Clipping oder Pseudoinverse.
Die Schrumpfung ist das explizite Verfahren und keine versteckte Reparatur.
Interne Skalierung zur Vermeidung von Über-/Unterlauf muss die Kovarianz
mit ihrer ursprünglichen Einheit wiederherstellen oder klar scheitern.

## 6. Auswahl auf getrennten Hintergrunddaten

Ein endliches vorab konfiguriertes Raster `alpha_candidates` wird einmal
auf `background_validation` bewertet. Für jeden zulässigen Kandidaten:

```text
C_alpha = L_alpha @ L_alpha.T
logdet(C_alpha) = 2 * sum_i log(L_alpha[i, i])

score(alpha) = logdet(C_alpha)
               + mean_m ||solve(L_alpha, b_validation[m])||^2
alpha_selected = argmin score(alpha)
```

Der Score entspricht der doppelten mittleren negativen gaußschen
Log-Dichte ohne den für alle Kandidaten gleichen Term `N*log(2*pi)`.
Er wird als prädiktiver Score eines eingesetzten Gaußmodells verwendet.
Die Logdeterminante ist erforderlich, weil verschiedene Kovarianzen
verglichen werden. Ein ausschließlich kleines `Q` würde große
Varianzannahmen ohne entsprechende Strafe begünstigen. Die offizielle
Referenz [3] zeigt die Auswahl von Schrumpfung anhand einer
Hintergrund-Likelihood; unsere feste Datentrennung ist hier explizit.

Das Raster enthält nur eindeutige endliche Werte im Intervall `[0, 1]`.
Die Auswertung erfolgt aufsteigend nach Alpha; bei exakt gleichem
numerischem Score wird das kleinere Alpha gewählt. Es gibt keine
nachträgliche Rasterverfeinerung anhand der Kontroll- oder Signalergebnisse.
Die Auswahl protokolliert auch unzulässige Kandidaten und deren Gründe.

Nach der Auswahl werden weder `S` noch `mu` aus Trainings- und
Validierungsdaten gemeinsam neu geschätzt. Die ausgewählte Matrix bleibt
für `background_check` und den Signalfit unverändert. Ein späterer Refit
wäre ein eigenes, vorab festzulegendes Verfahren.

Die Auswahlqualität ist selbst zufallsabhängig. Ein kleinerer
Validierungs-Score ist keine unabhängige Leistungsbewertung; dafür ist
`background_check` reserviert. Auch diese Menge darf nach ihrer Einsicht
nicht wiederholt zur Entwicklungsentscheidung verwendet und weiter als
unangetastete Bewertungsmenge bezeichnet werden.

## 7. Fit-Vergleich, Diagnose und Aussagegrenzen

Vorgeschlagen sind drei gekoppelte Kontrollfits:

1. Gewöhnlicher Fit ohne Kovarianzgewichtung.
2. Fit mit bekannter analytischer Modellkovarianz, als privilegierte Referenz.
3. Fit mit der eingefrorenen geschätzten und regularisierten Kovarianz.

Daten und Modell werden im dritten Fit mit demselben Cholesky-Faktor
transformiert. Der Schätzer erhält keine Fit-Residuen. Grenzwerte,
Startpunkte und Abbruchregeln werden gegenüber den anderen Fits nicht
auf die wahren Parameter zugeschnitten.

Zu speichern sind Alpha, Raster-Scores, Ablehnungsgründe, `mu`, Eigenwerte,
Kondition und Cholesky-Status sowie die bestehenden Fit-Diagnosen.
Zusätzliche synthetische Diagnosen dürfen nach dem Einfrieren sein:

- `||C_hat - C_true||_F / ||C_true||_F` als relativer Matrixfehler.
- Hintergrund-Score auf `background_check`, ausdrücklich getrennt vom
  Auswahl-Score; Vergleich verschiedener Kovarianzen stets mit Logdeterminante.
- Gewöhnliche MSE und MSE zum sauberen Signal für alle drei Fits.
- `Q_used/N` mit der jeweiligen Fit-Kovarianz und `Q_true/N` mit derselben
  analytischen Referenzmatrix für alle Varianten, eindeutig getrennt.

`Q_used/N` verschiedener Fits ist bei unterschiedlichen Kovarianzen kein
gemeinsamer Leistungsmaßstab. Die wahre Matrix darf ausschließlich für
den gekennzeichneten bekannten Kontrollfit und Diagnosen verwendet werden.
Keine dieser Diagnosen wählt Alpha, Startpunkte oder Methoden nachträglich.

Die eingesetzte geschätzte Kovarianz ist selbst unsicher. Der Gauß-Score
und der feste GLS-Fit sind ein kontrollierter Plug-in-Ansatz, keine exakte
Marginalisierung dieser Unsicherheit. [6] zeigt unter seinen Voraussetzungen
die Änderung der Inferenz bei geschätzter Kovarianz. Dessen t-Likelihood
oder eine Präzisionskorrektur darf nicht ungeprüft auf unsere durch
Validierung gewählte Schrumpfung übertragen werden.
Insbesondere werden weder `Q/N = 1` noch eine Chi-Quadrat-Verteilung oder
gültige Konfidenzintervalle nach Kovarianzschätzung und Signalanpassung
vorausgesetzt. Unsicherheitsabdeckung erfordert eigene Experimente.

Bei PySR bleiben Verlustnormierung und Komplexitätsstrafe eine spätere
methodische Entscheidung. Eine willkürliche Skalierung von `C_hat` darf
nicht unbemerkt ihr relatives Gewicht verändern.

## 8. Vorschlag für Schnittstellen und Metadaten

Der erste Implementierungsauftrag soll klein bleiben:

- Reiner Schätzer mit Eingaben `background_train`, `background_validation`,
  `alpha_candidates`, `kappa_max` und ausdrücklich `mean_mode="known_zero"`.
  Er hat keinen Zugriff auf Messdaten, Rauschparameter oder Signalwahrheit.
- Unveränderliches Ergebnis mit `S`, ausgewähltem `C_hat`, Alpha, Skala,
  vollständiger Kandidatendiagnose und Methoden-/Mittelwertkonvention.
- Getrennter Orchestrator erzeugt Hintergrund und Messdaten, ruft den
  Schätzer einmal auf und übergibt nur `C_hat` an den bestehenden Fit.
- Ein neues ausdrücklich versioniertes Konfigurationsschema beschreibt
  Hintergrundrollen, Mengen, Zufallsableitung, Raster und Konditionsgrenze.
  Die bisherige Schema-Version 1 und ihre drei Beispiele behalten ihre
  bisherige Bedeutung; neue Felder werden dort nicht stillschweigend erlaubt.

Zu exportieren sind Trainings-, Validierungs- und Kontrollfenster mit
unveränderter Zeilenreihenfolge, rohe und ausgewählte Matrix, Rasterwerte,
Scores und Fehlergründe. Die Matrix für den tatsächlich ausgeführten Fit
muss von `C_true` klar unterscheidbar sein. Metadaten erhalten Rollen,
Anzahlen, bekannte Mittelwertannahme, RNG-Zustände und Ableitung,
Prüfsummen, Methodenkennung, Software-/Codezustand und Einheiten.
Die bestehenden Regeln zu neuen Ausgabeordnern und Fehlerprotokollen gelten.
Ein fehlgeschlagener Schätzer erzeugt keinen erfolgreichen Ersatzfit.

Für diese erste Umsetzung werden keine neuen produktiven Abhängigkeiten
vorgeschlagen: NumPy und SciPy reichen. scikit-learn ist hier eine
Methoden-/Software-Referenz, keine bereits eingeführte Projektabhängigkeit.

## 9. Vorgeschlagene Kontrollen vor Leistungsstudien

Die nachfolgenden Kontrollen berücksichtigen das methodische Review und
beschreiben den geplanten Funktionsnachweis. Die Zahlen gelten nur für
technische Kontrollfälle. Damit wurden noch keine neuen konfigurierten
Kontrollläufe oder stochastischen Forschungsreihen ausgeführt.

### Deterministische Referenzfälle

| Prüfung | Unabhängig begründeter Bezug |
| --- | --- |
| Keine Stichprobenzentrierung | Für `B=[[1,0],[1,2]]` ist der Spaltenmittelwert `[1,1]` und `S=[[1,1],[1,2]]`; eine fehlerhafte Zentrierung vor Division durch `M=2` liefert dagegen `[[0,0],[0,1]]` |
| Divisor und Schrumpfungsbasis | Für `B=[[1,0],[-1,0],[0,2],[0,-2]]` folgt `S=diag(0.5,2)`, `mu=1.25` |
| Schrumpfung | Für dieses `S` und `alpha=0.4` ist `C_alpha=diag(0.8,1.7)` |
| Score | Für Validierungszeilen `[1,1]` und `[-1,-1]` ist der Score `log(1.36) + 1/0.8 + 1/1.7`; Referenz ohne produktives Whitening berechnen |
| Logdeterminante | Für dieselben Zeilen erzielt `I` den Score `2`, `100*I` den Score `2*log(100)+0.02`; eine reine Q-Auswahl würde die größere Matrix bevorzugen |
| Rangmangel | Bei `B=[[1,2],[2,4]]` ist `S=[[2.5,5],[5,10]]`; Alpha null ist unzulässig, positives Alpha macht die Matrix mathematisch positiv definit |
| Struktureller Rangmangel trotz Rundung | Für `B=[[0.7,0.1]]` gilt `M_train=1 < N=2`; Alpha null wird auch mit `kappa_max=1e20` vor numerischen Matrixdiagnosen abgelehnt |
| Whitening-Orientierung | Für `B=[[2,0],[1,3]]` ist `S=[[5,3],[3,9]]/2` und `S^-1=[[9,-3],[-3,5]]/18`; die Validierungszeile `[1,0]` ergibt `Q=1/2` und Score `log(9)+1/2`, transponiertes Whitening ergäbe fälschlich `Q=0.4` |
| Konditionsgrenze einschließlich Gleichheit | Für `S=diag(1,0)` gilt `kappa_2(C_alpha)=2/alpha-1`; mit `kappa_max=3` wird `alpha=0.4` wegen `kappa=4` abgelehnt und `alpha=0.5` mit `kappa=3` zugelassen |
| Exakte Gleichstände | Isotropes `S` erzeugt dasselbe `C_alpha` für alle Alpha-Werte; die definierte Reihenfolge muss die Auswahl eindeutig machen |
| Skalierung | Für gemeinsames `B,V -> c*(B,V)` gilt `C -> c^2*C`, unveränderte Kondition und Alpha-Auswahl; alle Scores verschieben sich um `2*N*log(abs(c))` |
| Fehlerpfade | Nulltrainingsmatrix, falsche Formen, nicht endliche/komplexe Daten, ungültige Raster, unzulässige Kondition und Bereichsfehler werden erklärt abgelehnt |

Der erste Fall hat absichtlich einen nicht verschwindenden empirischen
Mittelwert. Er prüft die bekannte Populationsmittelwert-Konvention und
erkennt das versehentliche Abziehen der Spaltenmittelwerte. Der bisherige
ausgeglichene Fall bleibt als Divisor- und Schrumpfungsreferenz erhalten,
könnte diesen Zentrierungsfehler allein aber nicht erkennen.

**Gesamte Alpha-Auswahl mit eindeutigem Minimum:** Zur vorhandenen Basis
`S=diag(0.5,2)` werden die Validierungszeilen `[1,0]`, `[0,2]` und das
Raster `[0,0.4,1]` verwendet. Mit `kappa_max=10` sind alle drei Kandidaten
zulässig. Die unabhängig berechneten Referenzwerte lauten:

| Alpha | Vollständiger Score, exakt | Score, gerundet | Nur mittlere Quadratik |
| --- | --- | ---: | ---: |
| 0 | `2` | 2.000000 | 2.000000 |
| 0.4 | `log(34/25) + 245/136` | 2.108955 | 1.801471 |
| 1 | `2*log(5/4) + 2` | 2.446287 | 2.000000 |

Der gesamte Selektor muss `alpha_selected=0` und `C_hat=S` zurückgeben,
nicht nur diese Scores berechnen. Mit einer umsortierten Eingabe
`[1,0.4,0]` muss dieselbe Auswahl mit denselben zugeordneten Matrizen und
Scores entstehen. Ohne Logdeterminante würde fälschlich Alpha `0.4`
gewinnen. Das eindeutige Minimum und der separat vorgesehene
Gleichstandstest sichern unterschiedliche Auswahlfälle ab.

**Ein späterer zulässiger Kandidat muss den ersten verdrängen können:**
Bei derselben Trainingsbasis und Validierungszeilen `[1,0]`, `[0,1]`
ergeben sich auf dem Raster `[0,0.4,1]` mit `kappa_max=10`:

| Alpha | Vollständiger Score, exakt | Score, gerundet |
| --- | --- | ---: |
| 0 | `5/4` | 1.250000000 |
| 0.4 | `log(34/25) + 125/136` | 1.226602347 |
| 1 | `2*log(5/4) + 4/5` | 1.246287103 |

Der Selektor muss Alpha `0.4` und `diag(0.8,1.7)` zurückgeben, auch bei
allen umgeordneten Rastereingaben. Dieser Fall erkennt die fehlerhafte
Auswahl des ersten zulässigen Kandidaten, die der vorangehende Fall
mit Gewinner Alpha null allein nicht erkennen kann.

Für die separate Konditionskontrolle kann `S=diag(1,0)` aus den
Trainingszeilen `[1,0]`, `[-1,0]` gewonnen werden. Auf dem Raster
`[0.4,0.5]` muss bei `kappa_max=3` nur Alpha `0.5` zur Score-Auswahl
zugelassen werden; der abgelehnte Kandidat behält seinen dokumentierten
Grund. Eine erfolgreiche Grenzprüfung ersetzt keine Genauigkeitsprüfung
der Quadratik oder des Fits.

Der Skalentest soll vorab festgelegte gut konditionierte Fälle mit
`c=1e-21` und `c=1e21` enthalten. Eindeutige Score-Abstände sind erforderlich,
damit numerisch fast gebundene Minima nicht als Invarianzbeweis dienen.
Die Solver-/Quadratikprüfung verwendet zusätzlich eine unabhängige
Eigenwertdarstellung oder eine von Hand gelöste kleine Matrix. Toleranzen
sind jeweils aus Größenordnung und Kondition zu begründen, nicht nach
Fehlschlägen anzupassen.

### Statistische Kontrolle des rohen Schätzers

Vorgesehen sind `N=4`, `M_train=32`, `R=2000` unabhängige Wiederholungen,
`sigma=0.1` und `rho` aus `[-0.65, 0, 0.65]`. Nur der rohe Schätzer `S`
wird gegen Erwartungswerte geprüft, nicht die verzerrende Schrumpfung.
Für gemeinsam gaußsche, mittelwertfreie Fenster folgt aus den vierten
Momenten und der Unabhängigkeit der Fenster:

```text
Var(S[i,j]) = (C[i,i]*C[j,j] + C[i,j]^2) / M_train
SE(mean_over_R(S[i,j]))
    = sqrt((C[i,i]*C[j,j] + C[i,j]^2) / (M_train*R))
```

Die vorab festgelegte Toleranz beträgt sechs solcher
Standardfehler zuzüglich begründeter Rundungsfehler. Der Test zählt
korrelierte Samples nicht als zusätzliche unabhängige Fenster und
behauptet keine exakte normalverteilte Fehlerschranke. Budget und Toleranz
wurden im Review als ergänzender Funktionstest plausibel bewertet; die
deterministischen Referenzfälle bleiben zusätzlich erforderlich.

### Kleine Integration und nachgelagerte Portabilität

Für den ersten sichtbaren Durchlauf werden die bestehenden Signal-,
Sampling- und Fit-Vorgaben aus den Pilotbeispielen beibehalten. Die
folgenden Werte wurden im Review als technische Kontrollvorgaben
akzeptiert:

| Feld | Technischer Kontrollwert |
| --- | --- |
| Hintergrundmengen | `M_train=64`, `M_validation=128`, `M_check=256` bei `N=128` |
| Alpha-Raster | `[0, 0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1]` |
| Konditionsgrenze | `kappa_max=1e8` |
| Hintergrundzufall | PCG64 mit eigener `SeedSequence`-Wurzel `20261019`; Rollenkennungen `train=0`, `validation=1`, `check=2` |
| Signalrauschen | Bisheriger expliziter PCG64-Aufruf mit Seed 42 bleibt getrennt erhalten |

`M_train < N` prüft gezielt die notwendige Regularisierung; diese Mengen
sind weder ein begründetes Hintergrundbudget für LIGO noch ein Raster der
Hauptversuche. Sie belegen auch keine statistisch stabile Alpha-Auswahl.
Der erste Kontrolllauf darf keine generelle Verbesserung
von Matrixfehler oder Rekonstruktion als Pflicht zum Bestehen verlangen.

Integrationstests müssen nachweisen: gleiche Messdaten in allen drei
Fits; ein einmal bestimmtes festes `C_hat`; nur Trainingsdaten bestimmen
`S` und `mu`; die Auswahl-Scores werten nur Validierungsdaten unter den
aus Trainingsdaten bestimmten Kandidaten aus; Änderungen
an `background_check` oder an Signalwahrheit ändern die Schätzung nicht.
Alle Hintergrundrollen und das Signalrauschen verwenden dieselbe
Rauschverteilung und Abtastung gemäß Abschnitt 3; die Zufallsströme sind
getrennt. Dies ist anhand der aufgelösten Konfiguration und Zuordnung der
Generatoraufrufe zu prüfen, nicht durch eine Forderung nach identischen
empirischen Momenten unabhängiger Stichproben.
Ein anderer Hintergrundumfang verändert die Messdaten nicht. Exporte
stellen die Eingaben und Entscheidung wieder her. Fehlgeschlagene
Schätzung bleibt ein Fehler; die bisherigen Schema-1-Kontrollfälle und
ihre Tests behalten ihre Bedeutung.

Nach Umsetzung sind die vollständigen Tests und ein sichtbarer Lauf
auf Manjaro und WSL2 zu wiederholen. Vergleichsmaß sind dokumentierte
numerische Abweichungen und konsistente Datenrollen; allgemeine
Bitidentität wird gemäß [Portabilitätsprotokoll](portability.md) nicht
vorausgesetzt. Konkrete Fehlertoleranzen sind vor der Prüfung zu begründen.

## 10. Methodisches Review und eingearbeitete Befunde

Das separate Review zu PR #14, Commit `897a8ce`, bewertete den Plan als
fachlich tragfähig. Die volle empirische Matrix mit Identitätsschrumpfung,
bekannter Nullmittelwert, getrennte Hintergrundrollen, Gauß-Score und
Verzicht auf Refit bleiben für den ersten Schritt erhalten. Ledoit-Wolf
und OAS müssen für diesen Implementierungsschritt nicht ergänzt werden.

Die am 20.10.2026 eingearbeiteten konkreten Befunde sind:

| Befund | Änderung | Stelle |
| --- | --- | --- |
| Mittel: bisheriger Nullmittelwert-Fall erkennt Zentrierung nicht | Zusätzliche Trainingsmatrix mit Spaltenmittelwert `[1,1]` und ausdrücklich unterschiedlichem zentriertem Ergebnis | Abschnitt 9, deterministische Referenzfälle |
| Mittel: erwartetes Ergebnis des gesamten Selektors fehlt | Vollständige Score-Tabelle, eindeutige Auswahl Alpha null und dieselbe Erwartung bei umsortiertem Raster | Abschnitt 9, gesamte Alpha-Auswahl |
| Niedrig: normale Kontrollwerte erreichen die Konditionsgrenze nicht | Herleitung der Konditionsschranke und gesonderter Annahme-/Ablehnungsfall mit `kappa_max=3` | Abschnitte 5 und 9 |
| Ergänzung zur Datentrennung | Gleiche Rauschverteilung und Abtastung aller Hintergrundrollen und des Signalrauschens ausdrücklich vorausgesetzt und als Integrationsprüfung festgehalten | Abschnitte 3 und 9 |

Das Review akzeptierte die Kontrollmengen, das Alpha-Raster sowie die
ergänzende statistische Prüfung als technische Funktionstests. Daraus
folgen keine Aussagen zur statistischen Stabilität der Auswahl oder zur
Leistungsfähigkeit der späteren Rekonstruktion. Die Anforderungen an
Genauigkeit, Datenrollen und getrennte wissenschaftliche Bewertung bleiben.

### Prüfauftrag des ursprünglichen Reviews

Das Review soll ein eigenes Urteil anhand der Quellen, des bestehenden
Codes und dieses Entwurfs bilden. Besonders zu beantworten sind:

1. Ist der vorgeschlagene nichtparametrische Fenster-Schätzer für diesen
   ersten Schritt sinnvoll, oder sollte bereits jetzt ein strukturierter
   Toeplitz-/AR-Schätzer beziehungsweise Ledoit-Wolf/OAS hinzukommen?
2. Sind bekannte Nullmittelwertannahme, Divisor, Fenster-Unabhängigkeit
   und spätere Abgrenzung zu zusammenhängenden Detektordaten korrekt?
3. Sind Schrumpfungsziel, Score mit Logdeterminante und Verzicht auf Refit
   konsistent? Ist der Aufwand einer getrennten Auswahlmenge angemessen?
4. Sind Datenrollen, Zufallsableitung und Schnittstellen ausreichend,
   um Signalwissen und Bewertungsdaten aus der Auswahl fernzuhalten?
5. Sind Raster, Hintergrundmengen, Konditionsgrenze sowie statistische
   und numerische Prüfkriterien begründet genug oder zu ändern?
6. Werden geschätzte Kovarianzunsicherheit, unterschiedliche Q-Skalen und
   das Vorwissen des bekannten Kontrollfits ausreichend berücksichtigt?

Die ergänzten Referenzwerte wurden am 20.10.2026 exakt symbolisch
nachgerechnet. Scores wurden zusätzlich numerisch mit dem bestehenden
Verlustkern verglichen, die Auswahlerwartung für alle sechs
Rasterpermutationen geprüft und die Konditionsgrenze einschließlich
Gleichheit unabhängig über Eigenwerte kontrolliert. Das sind Prüfungen
des Plans; ein neuer Schätzer wurde dabei nicht implementiert.
Bei der Implementierung sind die beschriebenen Prüfungen in automatisierte
Tests zu überführen. Die Dokumentationsprüfung validiert noch keine
Schätzimplementierung oder wissenschaftliche Leistungsbewertung.

## Quellen und jeweiliger Geltungsbereich

Alle Quellen wurden am 19.10.2026 eingesehen. Die folgenden Verweise
begründen einzelne Bausteine und Grenzen, nicht den gesamten Pilotplan.

1. Ledoit, O.; Wolf, M. (2004): *A well-conditioned estimator for
   large-dimensional covariance matrices*. Journal of Multivariate Analysis
   88(2), 365–411. DOI: `10.1016/S0047-259X(03)00096-4`.
   [Originalarbeit, Volltext](https://perso.ens-lyon.fr/patrick.flandrin/LedoitWolf_JMA2004.pdf).
   Grundlage für lineare Schrumpfung und die Unterscheidung von
   Schätzdimension und Zahl unabhängiger Vektoren; keine Rechtfertigung
   unserer konkreten Holdout-Mengen oder einer Rekonstruktionsüberlegenheit.
2. scikit-learn: [ShrunkCovariance](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.ShrunkCovariance.html).
   Offizielle Definition der Schrumpfungsfamilie und explizite
   Zentrierungsoption; deren Software-Voreinstellungen werden nicht übernommen.
3. scikit-learn: [Shrinkage covariance estimation: LedoitWolf vs OAS and
   max-likelihood](https://scikit-learn.org/stable/auto_examples/covariance/plot_covariance_estimation.html).
   Offizielles Beispiel zur Auswahl durch Likelihood und zu alternativen
   Schrumpfungsregeln; hieraus folgt kein Optimalitätsbeweis unseres Rasters.
4. Xiao, H.; Wu, W. B. (2012): *Covariance matrix estimation for stationary
   time series*. Annals of Statistics 40(1), 466–493.
   [Originalarbeit](https://arxiv.org/html/1105.4563v2).
   Unterscheidet unabhängige Vektorkopien von einer zeitabhängigen
   Realisierung und untersucht strukturierte Zeitreihenschätzer.
5. NumPy: [Parallel random number generation](https://numpy.org/doc/stable/reference/random/parallel.html).
   Dokumentation der reproduzierbaren Ableitung von Zufallsströmen mit
   `SeedSequence`; kein Versprechen rechnerübergreifend identischer
   Gleitkommaausgaben.
6. Sellentin, E.; Heavens, A. F. (2016): *Parameter inference with estimated
   covariance matrices*. MNRAS: Letters 456(1), L132–L136.
   [Originalarbeit](https://arxiv.org/abs/1511.05969).
   Begründet die gesonderte Betrachtung von Kovarianzunsicherheit in der
   Inferenz; die dortige Likelihood wird nicht auf unseren Schätzer übertragen.
