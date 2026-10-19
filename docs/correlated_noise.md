# Korreliertes Gaußrauschen mit bekannter Kovarianz

## Kontrollmodell und Abgrenzung

Der Pilot unterstützt zusätzlich ein stationäres Gauß-AR(1)-Modell. Es ist
ein einfaches Kontrollmodell für zeitlich korrelierte Samples, keine
Nachbildung eines LIGO-Rauschleistungsdichtespektrums. Der einzelne
Korrelationswert im Beispiel legt keine Einstellung der Hauptversuche fest.
Kovarianzschätzung aus Hintergrunddaten und Regularisierung folgen separat.

Für unabhängige `z[k] ~ N(0, 1)` werden die Samples erzeugt durch:

```text
u[0] = z[0]
u[k] = rho*u[k-1] + sqrt(1-rho^2)*z[k], k >= 1
epsilon[k] = sigma*u[k]

E[epsilon[k]] = 0
Cov(epsilon[i], epsilon[j]) = sigma^2 * rho^abs(i-j)
```

`sigma = standard_deviation` ist die **marginale** Standardabweichung jedes
Rauschsamples, nicht die Innovationsstandardabweichung. Diese beträgt
`sigma*sqrt(1-rho^2)`. Es gilt `-1 < rho < 1`; `rho` ist die dimensionslose
Korrelation benachbarter Samples bei der gewählten Abtastrate. Ein Wechsel
von `fs` bei festem `rho` ändert daher den zeitlichen Korrelationsmaßstab.

Weil der erste Wert bereits Varianz `sigma^2` hat und von den folgenden
Innovationen unabhängig ist, gilt die Stationarität ab dem ersten Sample:
`Var(epsilon[k]) = rho^2*sigma^2 + sigma^2*(1-rho^2) = sigma^2`.
Wiederholtes Einsetzen liefert die angegebene Kovarianz. Die Samples sind
gemeinsam gaußverteilt, weil sie eine lineare Transformation unabhängiger
Normalvariablen sind. Ein Nullstart würde die Anfangsvarianz verfälschen;
hier gibt es weder Nullstart noch Burn-in.

Positive Werte von `rho` erzeugen positive Nachbarkorrelationen, negative
Werte alternierende Vorzeichen der Kovarianz. Bei `rho = 0` entsteht der
weiße Kontrollfall. Bei `sigma = 0` ist das Rauschen identisch null; seine
Kovarianz ist dann nicht positiv definit und darf nicht zum Whitening
verwendet werden. Endliche Realisierungen werden weder zentriert noch
auf exakte Stichprobenmomente normiert. Es wird keine SNR-Normierung
vorgenommen.

Die stationären AR(1)-Beziehungen sind beispielsweise in den
[Berkeley-Vorlesungsnotizen zu AR-Modellen](https://stat153.berkeley.edu/spring-2026/ar-models-notes/)
dargestellt; deren Innovationsvarianz entspricht hier `sigma^2*(1-rho^2)`.

## Implementierung und numerische Grenzen

In `src/ringdown_sr/noise.py` stehen:

- `gaussian_ar1_noise(N, standard_deviation=sigma, correlation=rho, rng=rng)`:
  genau ein Aufruf `rng.standard_normal(N, dtype=np.float64)`, anschließend
  die stationäre Rekursion im normierten Raum und Multiplikation mit `sigma`.
  Der Innovationsfaktor wird als `sqrt((1-rho)*(1+rho))` berechnet.
- `ar1_covariance(N, standard_deviation=sigma, correlation=rho)`:
  analytische Matrix `C[i,j] = sigma^2*rho^abs(i-j)` mit Sample-Reihenfolge
  `0, ..., N-1`. Sie entsteht unabhängig von den gezogenen Werten und
  erfordert keine Kovarianzschätzung oder Cholesky-Erzeugung des Rauschens.

Beide Funktionen prüfen Samplezahl und skalare Parameter. Der Generator
prüft den expliziten NumPy-`Generator`; ungültige Argumente verändern den
Zufallszustand nicht. Überläufe werden als Fehler gemeldet. Für eine
positive Standardabweichung muss die auszugebende Varianz als strikt
positive endliche `float64`-Zahl darstellbar sein. Das betrifft die
Kovarianzfunktion und den konfigurierten AR(1)-Lauf, der die Matrix speichert.
Der reine Rauschgenerator kann kleinere positive Amplituden darstellen,
solange seine Samples selbst im Zahlenbereich liegen.

Mathematisch ist `C` bei `sigma > 0` und `abs(rho) < 1` positiv definit.
Nahe den Korrelationsgrenzen kann sie numerisch schlecht konditioniert
sein. Die vorhandene Cholesky-Prüfung kann dann scheitern; es werden
weder Grenzen verschoben noch Jitter, Pseudoinversen oder Regularisierung
eingeführt. Auch die nachgelagerte Kovarianzdiagnose eines gewöhnlichen
Fits kann in einem solchen Fall als `evaluation_failed` enden.

Die Rekursion benötigt linearen Speicher und lineare Arbeit. Die explizite
Matrix benötigt quadratischen Speicher, der bestehende volle
Kovarianzfit eine dichte Cholesky-Zerlegung. Dies ist für kleine
Kontrollfenster vorgesehen, keine Optimierung für große Zeitreihen.

## Konfiguration und Vergleich

Das Konfigurationsschema bleibt Version 1. Bei `noise.kind = "gaussian_ar1"`
ist zusätzlich `noise.correlation` zwingend erforderlich. Für weißes
Rauschen ist dieses Feld weiterhin unzulässig. Es gibt keinen versteckten
Standardwert für die Korrelation.

```toml
[noise]
kind = "gaussian_ar1"
standard_deviation = 0.1
bit_generator = "PCG64"
seed = 42
correlation = 0.65
```

`fit.weighting = "known_covariance"` verwendet die zum Erzeugungsmodell
gehörige analytische Kovarianz: AR(1) oder `sigma^2*I` bei weißem Rauschen.
`known_white` bleibt als bisheriger Weißrausch-Modus erhalten und wird
für AR(1) ausdrücklich abgelehnt. `ordinary` berücksichtigt im Fit keine
Kovarianz. `sigma = 0` ist nur bei `ordinary` zulässig.

Die Beispiele `configs/pilot_ar1.toml` und
`configs/pilot_ar1_ordinary.toml` unterscheiden sich inhaltlich ausschließlich
in der Fit-Gewichtung. Signal, marginale Rauschstärke, Korrelation, Seed,
Abtastung, Fit-Grenzen und Startwerte sind gleich. Sie erzeugen deshalb
innerhalb derselben Umgebung dieselben Messdaten:

```bash
uv run --locked ringdown-sr run configs/pilot_ar1.toml --output results/ar1-known-001
uv run --locked ringdown-sr run configs/pilot_ar1_ordinary.toml --output results/ar1-ordinary-001
code -r results/ar1-known-001/plot.png
code -r results/ar1-ordinary-001/plot.png
```

Der Referenzfit transformiert Daten und beide Basisfunktionen mit derselben
bekannten Kovarianz; siehe [Referenzfit](reference_fit.md). Die Matrix wird
aus den festgelegten Rauschparametern berechnet, nicht aus Signalwahrheit
oder Fitresiduen. Sie bleibt während eines Fits fest. Der Vergleich besitzt
damit Vorwissen über das Rauschmodell; es handelt sich nicht um eine
Untersuchung geschätzter Kovarianzen.

## Zusätzlicher Export und Auswertung

Bei AR(1) enthält der Lauf zusätzlich `covariance.csv`: eine headerlose
`N x N`-Matrix mit 17 signifikanten Dezimalstellen. Ihre Einheit ist das
Quadrat der Signaleinheit; im normierten Pilot ist sie dimensionslos.
Die Matrix wird auch beim gewöhnlichen Fit und bei einem gescheiterten
Fit gespeichert, sofern ihre Erzeugung erfolgreich war. Ihre Prüfsumme
steht in `metadata.json`. Im Ergebnis kennzeichnet `noise_model`, dass
die Matrix aus dem analytischen stationären Modell stammt und ob sie
im Fit benutzt wurde.

`random.calls` dokumentiert den einzelnen Standardnormalaufruf,
`random.transform` die stationäre AR(1)-Transformation und ihre Parameter.
Seed, Zustände, NumPy-/Buildinformationen und tatsächlich gezogene Samples
bleiben gespeichert. Der bisherige Weißrausch-Aufruf bleibt unverändert;
die neue Modellwahl gibt keine allgemeine rechnerübergreifende
Bitidentitätsgarantie.

Die vorhandenen Felder behalten ihre Bedeutung:

- `ordinary_mse` bewertet immer die ungewichteten Residuen.
- `covariance_mean_squared` enthält `Q/N` nur, wenn im Fit tatsächlich
  eine Kovarianz verwendet wurde; bei `ordinary` ist es `null`.
- Bei AR(1) kommt `known_covariance_mean_squared` hinzu. Dieses diagnostische
  `Q/N` wird mit derselben bekannten Modellkovarianz für **beide** Fits
  ausgewertet. Es verändert weder das Optimierungsziel noch die Startauswahl
  des gewöhnlichen Fits. Bei `sigma = 0` ist die Diagnose `null`.
- `mse_to_clean_signal` vergleicht nachträglich mit dem bekannten Signal;
  es beeinflusst keine Auswahl.

Zur unabhängigen Kontrolle der Quadratik gilt für AR(1):

```text
Q = (r[0]/sigma)^2
    + sum((r[k]-rho*r[k-1])^2 / (sigma^2*(1-rho^2)), k=1,...,N-1)
```

Dies folgt aus der inversen Innovationsdarstellung. Der produktive Fit
nutzt weiterhin die allgemeine Cholesky-Implementierung und keine eigens
für AR(1) vereinfachte Verlustfunktion. `Q/N` ist kein reduziertes
Chi-Quadrat mit geschätzten Freiheitsgraden. Endgültige Normierung und
Komplexitätsstrafe für PySR bleiben offen.

Alle Metriken betreffen die angepassten Samples. Ein einzelner Lauf darf
weder Überlegenheit noch Unverzerrtheit oder Unsicherheitsabdeckung belegen.
Gewichteter und gewöhnlicher Fit optimieren unterschiedliche Kriterien;
eine kleinere gewöhnliche MSE allein ist daher kein fairer Vergleich
beider Optimierungsziele. Mehrfachstarts garantieren weiterhin kein
globales Minimum.

## Prüfungen

Die Tests verbinden mehrere unabhängige Kontrollen:

- Handrechnung mit `sigma=5`, `rho=+/-3/5` und fest eingespeisten
  Standardnormalwerten `[1, 2, -1, 0]`; Referenzsamples, Matrix und
  zurückgewonnene Innovationen werden unabhängig angegeben.
- 20.000 unabhängige Fenster mit je sechs Samples für `rho=-0.65, 0, 0.65`.
  Mittelwert und unzentrierte zweite Momente jeder Position werden gegen
  die stationäre Verteilung geprüft, ausdrücklich auch am ersten Sample.
  Die sechs Standardfehler sind analytisch vorgegeben: nach Division durch
  `sigma` beträgt der Mittelwert-Standardfehler `1/sqrt(M)` und für das
  Produkt der Positionen `i,j` der Standardfehler
  `sqrt((1 + rho^(2*abs(i-j)))/M)` unter dem gemeinsam gaußschen Modell.
  Korrelation innerhalb eines Fensters wird nicht als unabhängige
  Zusatzstichprobe gezählt.
- Exportierte Rauschwerte werden anhand des gespeicherten RNG-Zustands
  und einer separat formulierten analytischen Dreiecksmatrix reproduziert.
  Die gespeicherte volle Quadratik wird gegen die Innovationsformel geprüft.
- Gepaarte Beispiele prüfen identische Eingabedaten und Startbedingungen,
  beide Optimierungsziele und dieselbe nachgelagerte Kovarianzdiagnose.
- Weitere Fälle prüfen `rho=0`, negative Korrelation, kleine Amplituden,
  `sigma=0`, RNG-Fortschaltung, globale Zustandstrennung, ungültige Eingaben,
  Überlauf sowie erhaltene Daten und Kovarianz bei Fit-Abbruch.

Diese Tests belegen die geprüften Kontrollfälle. Sie ersetzen keine
statistische Leistungsstudie oder Validierung gegen Detektordaten.
