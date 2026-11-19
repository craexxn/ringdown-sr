# Protokoll: Hintergrunddauer und Abtastungsgeometrie

Beschluss vom 19.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md),
auf Grundlage der [Aliasdiagnose](noise_background_alias_diagnostic_001.md).
Die gemeinsame Testfolge umfasst eine Schätzer-Vorprüfung ohne SR und zwei
gekoppelte wissenschaftliche Blöcke mit **624 neuen Suchworkern**. Dieser
Vertrag und seine Seeddatei werden vor neuen Studienbeobachtungen und Suchen
versioniert und durch Commit und SHA-256 gebunden. Historische Protokolle,
Originalformeln und Auswahlen bleiben unverändert. Die bekannten Signale
bleiben Entwicklungswissen; dies ist keine unabhängige Bestätigung des Profils.

## Fragen, Inventar und Bedingungen

26 frische Fälle: 20 AR(1)- und sechs weiße Kontrollfälle. Jeder der sechs
Arme erhält vier frische Worker mit denselben vier Suchseeds seines Falls.

| Block | Condition-ID | Gewichtung und Messraster | Neue Worker |
| --- | --- | --- | ---: |
| A: `duration` | `ordinary` | Uniform, gewöhnliche MSE | 104 |
| A | `known_covariance` | Uniform, bekannte wahre Kovarianz K | 104 |
| A | `estimated_64s` | Uniform, volle Matrix aus 64 s Hintergrund | 104 |
| A | `estimated_4096s` | Uniform, volle Matrix aus 4096 s Hintergrund | 104 |
| B: `sampling` | `jitter_ordinary` | Ungleichmäßig, gewöhnliche MSE | 104 |
| B | `jitter_known_covariance` | Ungleichmäßig, bekannte wahre Kovarianz K | 104 |

Block A hat 104 Pakete/416 Worker, Block B 52 neue Pakete/208 Worker.
B referenziert die vorab gemeinsamen 52 Uniform-O/K-Pakete aus A anhand
ihrer Eingabe-, Ergebnis- und Quellenbindungen. Keine Übernahme aus Serie 002,
keine zusätzliche Suche oder erneute Kostenanrechnung für diese Kontrollen.
Es bleiben 26 gemeinsame Fallblöcke, keine zwei unabhängigen Stichproben.

Primär unter AR(1): in A der gepaarte Rekonstruktionsfehler
`estimated_4096s - estimated_64s`, in B
`jitter_known_covariance - known_covariance`. Negative Differenzen bedeuten
kleinere Fehler. Sekundär A: beide geschätzten Arme gegen O und K sowie K-O;
B: Jitter-O gegen Uniform-O sowie K-O innerhalb beider Raster. White wird
vollständig, aber getrennt ausgewertet. Keine automatische Armwahl,
nachträgliche Priorisierung günstiger Kontraste oder neue Bestehensgrenze.

## Signal und Messraster

Unverändert `confirm_mid`, physische Zeit t in Sekunden, N=128,
geschlossenes Fenster [0,127/4096] s, marginales sigma/A=0,05.

```text
s(t) = A * exp(-t/tau) * cos(2*pi*f*t + phi)
A     = 0x1.d555555555555p-1
f/Hz  = 0x1.0900000000000p+8
tau/s = 0x1.b4e81b4e81b4fp-8
phi   = 0x1.0000000000000p-2
sigma = 0x1.7777777777778p-5
```

Mathematisches pi und unabhängige hochpräzise Referenzprüfung wie im
Hintergrundplan; keine Zentrierung oder nachträgliche Pegelanpassung.
Sigma/A ist kein Detektor-SNR; K ist privilegierte Kenntnis und keine
Garantie eines SR-Leistungshöchstwerts.

Uniform gilt `t_j=j/4096`, j=0,...,127. Für die 126 inneren Jitterpunkte
werden einmal `u_j=Generator(PCG64(2026111902)).uniform(-0.25,0.25,126)`
gezogen und `t'_j=(j+u_j)/4096` gesetzt. Endpunkte bleiben exakt gleich.
Strikte Ordnung, Mindestabstand `0.5/4096`, keine gleichen inneren Punkte
und keine inneren Uniformtreffer prüfen. Bei unerwartetem Treffer abbrechen,
keine alternative Achse suchen. Dieselbe Achse gilt für alle Fälle.
Die Regel benutzt weder Signalfrequenz noch Ergebnisse oder saubere Kurven.

Messrauschen wird einmal auf der sortierten eindeutigen Vereinigung beider
Achsen (254 Zeiten) erzeugt, dann auf beide Achsen eingeschränkt. Gemeinsame
Endpunkte erhalten bitgleiche Rauschwerte. Bei White: ein unabhängiger
Normalwert je eindeutiger Unionzeit. Bei korreliertem Rauschen gilt als
**neue kontinuierliche Modellannahme**

```text
C(t_i,t_j) = sigma^2 * exp(-lambda * abs(t_i-t_j))
lambda = -4096 * log(0.65)
y_0 = sigma*z_0
a_i = exp(-lambda * (t_i-t_(i-1)))
y_i = a_i*y_(i-1) + sigma*sqrt(1-a_i^2)*z_i
```

Unabhängige Standardnormalinnovationen und stationärer Anfang. Numerisch
stabile äquivalente Auswertung von `1-a_i^2` ist zulässig und quellengebunden.
Auf der Uniformachse ergibt sich in reeller Arithmetik das bisherige AR(1)
mit rho=0,65; die Fortsetzung ist nicht eindeutig aus diesem Modell ableitbar.
Kovarianzmatrizen werden für die jeweilige Achse gebunden. Neue echte
Messwerte werden erzeugt; keine Interpolation. Ein Effekt betrifft Geometrie
und Rauschkorrelation, beweist keine allgemeine Aliasfreiheit und ist kein
unmittelbarer Befund an Detektordaten.

## Hintergrunddauer und fester Schätzer

Pro Fall eine getrennte stationäre Rauschreihe auf dem Uniformraster:
16.777.216 Float64-Samples für 4096 s; die ersten 262.144 Samples für 64 s.
Die Dauer bezeichnet hier N/fs; der Abstand vom ersten zum letzten Sample
ist jeweils um 1/fs kürzer. White ist unabhängig je Sample, AR(1) behält
seinen Zustand über sämtliche Chunk- und Fenstergrenzen. Keine Filterung,
Zentrierung oder Nachskalierung.

Feste Chunks mit 65.536 Samples, stationärer Start, feste sequentielle
Reduktionsreihenfolge. Nichtüberlappende 128er-Vektoren liefern 2048 bzw.
131072 Trainingszeilen. Diese Zeilen sind bei AR(1) **nicht unabhängig**.
Das ist eine neue Stream-/Methodenkennung; der historische Vertrag für
unabhängige Hintergrundfenster wird nicht umgedeutet.

Die mathematische Schätzregel bleibt: bekannter Nullmittelwert,
`S=B.T@B/M`, `mu=trace(S)/128`, `C_alpha=(1-alpha)*S+alpha*mu*I`.
Streaming-Akkumulation wird gegen eine unabhängige dichte Rechnung geprüft;
Rundungsunterschiede zur historischen Reduktionsreihenfolge sind getrennt
von einer Methodenänderung zu behandeln. Eine 128-MiB-Reihe wird fallweise
gespeichert/geprüft, der kurze Hintergrund nur als Präfix referenziert.

128 unabhängige Validierungsfenster und 256 unabhängige Kontrollfenster,
jeweils uniforme 128er-Fenster bei fs=4096 mit stationärem Anfang, werden
aus separaten Rollen erzeugt. Sie sind von
Training und Messrauschen unabhängig und werden zwischen Dauerarmen geteilt.
Alpha-Raster `[0,0.001,0.01,0.05,0.1,0.2,0.5,1]`, `kappa_max=1e8`;
SPD/Cholesky/Kondition wie bisher. Alpha nur durch Logdeterminante plus
mittlere Validierungsquadratik bestimmen; exakte Gleichstände bevorzugen
kleineres Alpha. Keine Verwendung von Wahrheit, Kontrollfenstern oder
SR-Residuen zur Wahl. Kein Refit, Clipping, Zusatzjitter, Pseudoinverse
oder Ersatz durch K. Validierungsumfang und Alpha-Raster bleiben mögliche
Begrenzungen. M ist keine Zahl unabhängiger Trainingsreplikationen.

## Separate Schätzer-Vorprüfung

Acht AR(1)- und vier weiße Entwicklungsfälle mit eigenen Seeds, keine SR.
Jeweils dieselben 64/4096-s-Präfixbedingungen mit zwei festen Schätzern:
volle Matrix wie oben sowie eine Welch-/ACF-/Toeplitz-Diagnose.

Welch: fs=4096, 8192 Samples pro Segment, periodisches Hannfenster,
4096 Samples Überlappung, `detrend=False`, `scaling='density'`, einseitige
PSD, arithmetisches Mittel aller vollständigen Segmente. Segmentweise
Berechnung ohne vollständige FFT der langen Aufnahme. Rücktransformation:

```text
p_two = P_one.copy()
p_two[1:-1] /= 2
acf = fs * irfft(p_two, n=8192)
raw_covariance[i,j] = acf[abs(i-j)]
```

Die ersten 128 Lags bilden die Toeplitzmatrix. Keine Lag-Entfensterung,
Korrektur auf das wahre sigma oder nachträgliche Fensterwahl. Dieselbe
Holdout-Schrumpfung und SPD-/Konditionsprüfung; die Segmentanzahl ist keine
Rangobergrenze dieser Toeplitzmatrix. Die Fensterung kann ACF-Bias erzeugen.
Diese Variante ist eine feste synthetische Diagnose, keine Reproduktion der
Detektordatenstudie von Wang und Shao [1] und kein zweiter SR-Schätzer.

Alle 48 geplanten Schätzungen einschließlich Ausfällen berichten: rohe und
geschrumpfte Kovarianz, Alpha/Kondition, relative Frobeniusabweichung zu K,
Gauß-Score auf unabhängigen Kontrollfenstern, Laufzeit, RAM und Dateigröße.
Numerische Referenzfälle prüfen PSD-Normierung, lineare/periodische
Operationen, Streaming-Präfix und Kovarianzformel getrennt. Kein Gewinner
wird automatisch in die wissenschaftliche Suchserie übernommen. Das Gate
fordert technische Integrität und vollständige Rechenschaft, keinen
günstigen wissenschaftlichen Effekt. Unklassifizierte Fehler blockieren.

## Seeds, Rollen und Reihenfolge

Verbindliche Tabelle: [noise_followup_seeds.json](../data/noise_followup_seeds.json).
Bezugscommit `7f52cfb2fe94ad13cda1ff28e11daa261e57bd21`, NumPy 2.5.3,
Tabellengenerator PCG64(2026111901), `integers(1,2**31)`. Historischer Ausschluss:
3463 positive 31-Bit-Dezimaltokens aus 392 UTF-8-Blobs unter data/docs/src/scripts/tests;
Regex `(?<![A-Za-z0-9_])\d+(?![A-Za-z0-9_])`. Sortierte Werte jeweils LF:
SHA-256 `9317f94a40ac64e46f70791a18ee6bcf27ec9fe06470402e854b0025ea8f520a`.
Historische, reservierte und schon akzeptierte Zahlen werden verworfen.

Reserviert: 2026111901 Tabelle, 2026111902 Akquisition, 2026111903 Bewertung,
2026111904 technisches Messrauschen, 2026111905 technischer Hintergrund,
2026111906 technische Suche. Alle sechs sind im Bezugsbestand neu.
Zuerst 20 AR(1)- und sechs White-Zeilen mit Mess-/Hintergrundwurzel und
vier Suchseeds; danach acht AR(1)- und vier White-Diagnosezeilen mit je zwei
Datenwurzeln. 180 akzeptierte Zahlen bei 180 Ziehungen, keine Verwerfung.
Die sechs technischen Bedingungen verwenden denselben technischen Suchseed.

Messrauschen: PCG64 direkt aus Messseed. Hintergrundrollen:
`SeedSequence(background_seed,spawn_key=(role,),pool_size=4)`, train=0,
validation=1, check=2. Konkrete Zustände vor/nach Ziehung und Arrays speichern.
159 neue tatsächliche Anfangszustände einschließlich technischer Datenrollen,
beider Achsen und Tabellengenerator sind verschieden; verschiedene Zustände
sind kein empirischer Unabhängigkeitsnachweis. Die Tabelle erzeugt selbst
keine Beobachtungen, Hintergrundwerte oder Rasterpunkte. Julia-Suchzufall
ist getrennt im nativen Herkunftsnachweis zu prüfen.

Ausführung pro Block: ar1-01, white-01,...,ar1-06,white-06,ar1-07,...,ar1-20;
innerhalb jedes Falls Bedingungen in Tabellenreihenfolge, Mitglieder 1–4.
Vor der ersten wissenschaftlichen Suche sämtliche 26 Fälle, beide Achsen,
geplanten Kontrollidentitäten, Rollen, geschätzten Matrizen und Quellen binden.
Die tatsächlichen Kontroll-Ergebnishashes werden nach Abschluss von A
gebunden, bevor B startet.
Keine Auswahl günstiger Fälle und keine Anpassung nach Zwischenergebnissen.

## Suchprofil, Bewertung und Ausfälle

Unverändert `r4x1000-local300x5-v1`: vier mal 1000 äußere Iterationen,
lokal 300/fünf zusätzliche Neustarts, allgemeine Grammatik und bisherige
effektive Optionen. Eine feste Matrix wirkt in Struktur- und Konstantensuche.
Originalauswahl nach endlichem nativem Verlust, Komplexität und Mitglied;
kein `best`, keine Aliasnormalisierung, kein Frequenzprior. Ein gemeinsamer
sauberer Ausführungscommit, gesperrte Abhängigkeiten und bestätigter
Ein-CPU-/Threadvertrag wie im ursprünglichen Hintergrundlauf.

Primärer Endpunkt ist RMSE/A gegen das saubere Signal an 1024 gemeinsam
gebundenen unregelmäßigen Zeiten. Je ein Punkt aus jedem offenen gleichen
Stratum von [0,127/4096], PCG64(2026111903), Treffer auf dem alten
1/32768-Raster oder einer Jittermesszeit zurückweisen; maximal 100 Ziehungen
pro Stratum. Erzeugungsfehler stoppt vor Suchen. Die 889 regulären
Zwischenpunkte bleiben gemeinsame sekundäre Diagnose. Wahrheitswerte mit
unabhängiger hochpräziser Referenz prüfen. Keine Bewertungszeit beeinflusst
Suche, Auswahl, Alpha oder Stopp. Trainingsmetriken sind rasterspezifisch.

Je Modell und Kontrast alle Einzelwerte, Mittel/Median/Min/Max/SD, verfügbare
und geplante Nenner berichten. Bei vollständigen Paaren marginale approximative
95%-t-Intervalle und MCSE wie im Hintergrundplan; bei fehlenden Paaren nur
bedingte deskriptive Werte, kein vollständiger Präzisionsnachweis. Keine
Imputation, Ausreißerentfernung, adaptive Fallzahl oder Ersatzseeds. Zwei
Hauptfragen, keine simultane Fehlerkontrolle und keine Überlegenheitsgarantie.
Zusätzlich Maximalfehler/A, native Trainingswerte, MSE zu Beobachtungen,
Q_true/N, Kovarianzdiagnosen, Ausfälle und tatsächliche Kosten. Endliche Raster
beweisen keine kontinuierliche Güte. Neue Familien-/Domain-/Parameterbeweise
und klassische bekannte-Familie-Fits sind in dieser Studie nicht vorgesehen
und bleiben ausdrücklich `not_assessed`; historische Ergebnisse bleiben gültig.

Zulässige numerische Suchfehler/Timeouts gemäß bestätigtem Paket behandeln;
ohne gültige Originalausgabe bleibt ein Paket ausgefallen. Ungültige
Schätzmatrizen als `not_run` für genau ihren Arm samt Grund führen, keine
Ersatzmatrix. Herkunftswidersprüche, Unterbrechung, unbekannte Fehler und
späte Quellenänderungen sperren/widerrufen die Veröffentlichung.

## Betriebsgrenzen, Fortsetzung und Ergebnisdarstellung

Äußere Fristen: Worker 1800 s/Paket 7800 s wie bisher; A-Fall 33000 s,
B-Fall 17400 s; je Block `26*Fallfrist+14400` s. Vorbereitung, Diagnostik,
technischer Gesamtaufruf und vollständige lesende Blockverifikation jeweils
14400 s; technische Worker jeweils 600 s, N128 mit zehn Iterationen.
Diese Grenzen gelten einschließlich Abschluss; keine nachträgliche Lockerung
zur Rettung eines Ergebnisses. Der 23.11. morgens ist nur ein weiches
Planungsziel, keine zusätzliche wissenschaftliche Abbruchregel.

Separate technische Abnahme: ein eigener AR(1)-Fall, beide echten Dauern,
beide Achsen und sechs getrennte N128-Zehnerworker, ursprüngliches lokales
Profil. Vollständige native Herkunft, Eingabebindung und lesender Replay;
Signalqualität kein Gate. Wissenschaftliche Suchen finden nicht in CI statt.

Je Fall begrenzter RAM, gestreamte Hashes und Regeneration; keine 26 langen
Reihen oder deren NPZ-Bytekopien gleichzeitig halten. Abgeschlossene Fälle
werden bei Fortsetzung vollständig gegen Plan, Inputs, Software, Umgebung
und Ergebnisse erneut geprüft. Vorhandene unvollständige Fälle blockieren;
kein stilles Überschreiben oder automatischer Retry. Bewusste Pause nur an
Fallgrenzen. Fortsetzungsaufrufe und deren Kosten separat unveränderlich
erhalten. Bereits bezahlte Kontrollreferenzen nicht erneut als Suchkosten zählen.

Rein lesende Fortschrittsanzeige mit Block, Fall, Bedingung, vier Mitgliedern,
gespeichertem Zustand und Zeitbasis. Prozessabschluss ist kein Erfolgsnachweis.
Nach A dessen Verifikation, sämtliche Plots und Archiv sichern; danach B
mit eindeutig gebundenen A-Kontrollen. Gemeinsame große Eingaben separat
archivieren, nicht stillschweigend weglassen oder mehrfach zählen.

Alle bis zu 156 Originalpakete mit PNG/SVG, vollständigen unveränderten
Formeltexten/Bäumen, Identität/Seeds/Quellenhashes und exakten Plot-CSV zeigen;
auch Ausfälle und nichtendliche Werte. Keine Glättung, versteckte Spitzen oder
Ersatzformeln. Gruppenübersichten mit Einzelwerten, gepaarten Kontrasten,
Grenzen, Ausfällen und Kosten. Plots sind ein eigener gebundener lesender Export.
Originalarchive plus unabhängige hashgeprüfte Zweitkopie gemäß
[Archivregel](results_archiving.md); tatsächliche Sicherung im Ergebnisindex.

Die historische Projektion beträgt 38,93 h für A und 18,13 h für B,
zusammen 57,06 Worker-Stunden, ohne neue Vorbereitung/Prüfung/Sicherung.
Sie approximiert beide Dauerarme durch alte E1024-Suchkosten; neue Raster
können Suchzeiten ändern. 20+6 Fälle sind eine Ressourcenentscheidung,
keine Powerberechnung. Keine nachträgliche Fallzahlanpassung an den Kalender.

## Quelle

1. Wang und Shao (2024), *Comparison between time-domain and frequency-domain
   Bayesian inferences to inspiral-merger-ringdown gravitational-wave signals*,
   [Phys. Rev. D 109, 043027](https://link.aps.org/accepted/10.1103/PhysRevD.109.043027).
   Der dortige 64/4092-s-Vergleich begründet die Dauerfrage; er ist kein
   Nachweis besserer freier SR-Formeln. Weitere Einordnung im Aliasbericht.
