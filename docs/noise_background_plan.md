# Protokoll: begrenzte Studie zur Hintergrunddatenmenge

Beschluss vom 16.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md):
**20 neue AR(1)-Blöcke und sechs neue weiße Kontrollblöcke, 520 SR-Suchaufrufe.**
Dieses Protokoll wird vor Implementierung getrennt versioniert. Ausgangsbasis
ist `d1140178b2996c2bbf0bfa7e7ee98ced39dc856a`, der geprüfte PR93-Merge.
Die wissenschaftliche Ausführung folgt erst nach technischer Abnahme in einem
separaten Schritt. Der neue Serienlaufweg ist noch nicht implementiert.

Der [abgeschlossene Rauschpilot](noise_pilot_results_manjaro_001.md) und sein
[eingefrorener Plan](noise_pilot_plan.md) bleiben unverändert. Insbesondere
wird sein primärer Trainingsfehler nicht rückwirkend durch einen Rasterfehler
ersetzt. Dies ist eine gezielte Anschlussstudie, keine neue unabhängige
Bestätigung des Suchprofils und noch keine breite Studie über Signale/Pegel.

## Forschungsfrage und vorab festgelegte Vergleiche

Verbessert geschätzte Kovarianzgewichtung bei mehr unabhängigen Hintergrund-
Trainingsfenstern die Rekonstruktion des bekannten Signals unter AR(1)-Rauschen?
Der Pilot zeigte keinen beobachteten mittleren Vorteil geschätzter Gewichtung;
bei M_train/N=0,5 ist die rohe Kovarianz zwangsläufig singulär. Zugleich zeigten
Originalformeln relevante Zwischenpunktspitzen. Diese Befunde begründen die
Hintergrundstaffel und den **prospektiv** geänderten primären Endpunkt, beweisen
aber weder einen ursächlichen Engpass noch den Nutzen zusätzlicher Daten.

Je frischem Block fünf Pakete, jeweils mit vier neuen 1.000er-Suchen:

| Arm | Gewichtung | Hintergrund-Training |
| --- | --- | ---: |
| O | Gewöhnliche MSE | Nicht verwendet |
| K | Bekannte wahre Kovarianz, privilegierte Kontrolle | Nicht verwendet |
| E64 | Geschätzte Kovarianz | 64 Fenster |
| E256 | Geschätzte Kovarianz | 256 Fenster |
| E1024 | Geschätzte Kovarianz | 1.024 Fenster |

O und K werden **je Block einmal neu berechnet** und in den vorab genannten
Vergleichen gemeinsam verwendet. Keine Übernahme historischer Pilotkontrollen,
keine neue Suche für jede rechnerische Wiederverwendung. Die fünf Ausgaben
sind innerhalb eines Blocks gepaart, keine fünf unabhängigen Wiederholungen.

Primärer Kontrast ist **E1024 minus O unter AR(1)**. Er beantwortet die
praktische Frage nach geschätzter Gewichtung beim größten vorgesehenen
Hintergrundtraining. Wichtigster sekundärer Kontrast ist **E1024 minus E64**;
er beschreibt den Effekt der vergrößerten Trainingsmenge innerhalb derselben
Schätzmethode. Zusätzlich alle drei E-minus-O-, alle drei E-minus-K- und
K-minus-O-Kontraste berichten, insgesamt acht vorab benannte Kontraste.
Der weiße Kontrollfall wird vollständig, aber getrennt ausgewertet.
Kein nachträglicher Wechsel zum günstigsten Kontrast oder zur besten Stufe.

## Feste Bedingungen und verschachtelte Hintergrunddaten

Signal, Fenster, Rauschpegel und Schätzer bleiben die des Piloten:
`confirm_mid`, 128 Samples `t[j]=j/4096 s`, j=0,…,127, physische Zeit t,
geschlossenes Intervall [0,127/4096] s. Keine Zeitnormalisierung.

Die saubere Referenz lautet

\[
s(t)=A\exp(-t/\tau)\cos(2\pi f t+\phi).
\]

Maßgeblich sind die Binary64-Parameter, nicht ihre verkürzte Dezimaldarstellung:

| Parameter | Exakter gespeicherter Hexwert | Einordnung |
| --- | --- | --- |
| A | `0x1.d555555555555p-1` | gerundetes 11/12 |
| f / Hz | `0x1.0900000000000p+8` | 265 |
| tau / s | `0x1.b4e81b4e81b4fp-8` | gerundetes 1/150 |
| phi / rad | `0x1.0000000000000p-2` | 1/4 |
| sigma | `0x1.7777777777778p-5` | Binary64 A × 0,05 |

Mathematisches pi und unabhängige hochpräzise Referenzprüfung wie im Pilot.
Messrauschen weder zentrieren noch nachskalieren. White hat C_true=sigma² I;
stationäres Gauß-AR(1) hat rho=0,65 und
`C_true[i,j]=sigma²*rho**abs(i-j)`. Jede Hintergrundzeile ist ein neues Fenster
mit unabhängigem stationärem Anfangswert, kein überlappender Ausschnitt.
Sigma/A ist kein Detektor-SNR; gleicher marginaler Pegel bedeutet nicht gleiche
Detektierbarkeit. Der bekannte K-Arm garantiert keinen SR-Leistungshöchstwert.

Pro Block einen Pool von **1.024 Trainingsfenstern** sowie getrennt **128
Validierungs- und 256 Kontrollfenster** erzeugen. E64 und E256 erhalten die
ersten 64 beziehungsweise 256 Zeilen desselben Trainingspools; E1024 alle.
So wird innerhalb des Blocks ausschließlich der vorab festgelegte
Trainingsumfang verändert. Das Verhältnis M_train/N ist 0,5 / 2 / 8.
Gemeinsame Validierungs- und Kontrollfenster innerhalb des Blocks; diese beiden
Rollen bleiben vom Trainingspool und vom Messrauschen unabhängig. Die Stufen
sind bewusst korreliert; die unabhängige Auswertungseinheit bleibt der Block.
Die feste Validierungsmenge kann weiterhin die Alpha-Auswahl begrenzen;
diese Studie isoliert keine reine Wirkung einer hypothetisch optimalen Matrix.

Unveränderter [Kovarianzvertrag](covariance_method_plan.md): bekannter
Nullmittelwert, `S_M=B_train[:M].T @ B_train[:M]/M`,
`mu_M=trace(S_M)/128`, `C_alpha=(1-alpha)*S_M+alpha*mu_M*I`.
Alpha-Raster `[0,0.001,0.01,0.05,0.1,0.2,0.5,1]`, `kappa_max=1e8`;
Alpha null bei M<128 strukturell ablehnen. Positive Definitheit und Kondition
prüfen; Alpha ausschließlich durch den bestehenden Gauß-Validierungsscore
(Logdeterminante plus mittlere quadratische Form) auswählen; bei exakt gleichem
Score kleineres Alpha. Keine neue Kovarianzmethode, kein Refit, Jitter,
Clipping, Pseudoinverse oder Ersatz durch C_true. Kontrollfenster, Signalwahrheit,
Messresiduen und Rasterfehler bestimmen Alpha nicht.

## Seeds, Eingabebindung und Ausführungsreihenfolge

Je Block neue Messrausch-/Hintergrundwurzeln und vier neue Suchseeds. Innerhalb
des Blocks sind Beobachtungsvektor und vier Suchseeds über alle fünf Arme
identisch. Jeder der 20 Aufrufe ist ein frischer Worker; identische Seeds
bedeuten bei veränderter Zielfunktion keinen identischen Suchverlauf.
Zwischen Blöcken und Modellen keine geteilten Innovationen oder Hintergründe.

PCG64; Hintergrundrollen über unverändertes `seedsequence_role_v1` mit
train=0, validation=1, check=2 und `pool_size=4`. Den Trainingsstrom einmal
für den vollständigen Pool ziehen, die kleinen Mengen daraus entnehmen;
keine Verschiebung anderer Rollen durch die Trainingsmenge. Alle konkreten
Arrays sowie Anfangs-/Endzustände speichern und gleiche Anfangszustände
rollenübergreifend zurückweisen. Verschiedene Seeds allein beweisen keine
statistische Unabhängigkeit.

Bezugscommit `d1140178b2996c2bbf0bfa7e7ee98ced39dc856a`. Generator: NumPy 2.5.3, `Generator(PCG64(2026111609))`, `integers(1, 2**31)`; zuerst ar1-01 bis ar1-20, danach white-01 bis white-06. Je Zeile Messrauschen, Hintergrundwurzel und vier Suchseeds. Historische, reservierte und bereits akzeptierte Zahlen werden beim Ziehen verworfen.

Ausschluss: **2119** verschiedene positive 31-Bit-Dezimaltokens aus UTF-8-Blobs unter `data/docs/src/scripts/tests` am Bezugscommit; Regex `(?<![A-Za-z0-9_])\d+(?![A-Za-z0-9_])`. Aufsteigend sortierte Dezimalwerte, jeweils LF, einschließlich letzter LF. SHA-256: `76c6bbc7bf1b7f651e7c9cc38a4707c372af0baacdaa15d2570a61a768c66823`.

Alle **156** Zahlen sind verschieden und frei von Überschneidungen mit dieser historischen Ausschlussmenge und den fünf Reservierungen. 156 Generatorziehungen, 0 verworfen. Alle fünf Reservierungen sind im Bezugsbestand neu.

Reserviert: Tabellengenerator `2026111609`, Zusatzraster `2026111610`, technisches Messrauschen `2026111611`, technischer Hintergrund `2026111612`, technische Suche `2026111613`.

| Fall | Messrauschen | Hintergrund | Vier Suchseeds |
| --- | ---: | ---: | --- |
| ar1-01 | 646793876 | 950461961 | 396503743, 667450480, 414882043, 1186887900 |
| ar1-02 | 966005564 | 2131299745 | 224595958, 143460462, 583542165, 1062557763 |
| ar1-03 | 1972632683 | 596718766 | 1464369716, 1317917552, 1865880593, 624569914 |
| ar1-04 | 1650338219 | 1552640662 | 1008562290, 1905374137, 1149751997, 730539992 |
| ar1-05 | 413899298 | 514055703 | 1199221718, 389793444, 1483889227, 932926354 |
| ar1-06 | 1096683654 | 1873929890 | 464176975, 1586673715, 514597075, 2099248160 |
| ar1-07 | 653624123 | 19673332 | 1940945950, 1854345846, 569272474, 2027841777 |
| ar1-08 | 691266039 | 756971811 | 484384071, 1208482622, 2112118114, 659058988 |
| ar1-09 | 741373155 | 2074180037 | 71327655, 1172723461, 873508989, 1967894403 |
| ar1-10 | 1152667351 | 362856872 | 2008397264, 1974146732, 702735018, 1536548225 |
| ar1-11 | 85725611 | 634179035 | 200012446, 1038893210, 1549005214, 1096150590 |
| ar1-12 | 1451052659 | 694866974 | 1761466409, 166853572, 1556594400, 351696746 |
| ar1-13 | 251011455 | 1867190795 | 432510272, 1094408579, 2144670917, 790763179 |
| ar1-14 | 1109200832 | 294890751 | 8825503, 1706784002, 460915138, 40986374 |
| ar1-15 | 790432377 | 1762994460 | 1576026321, 229935957, 1405010561, 1648770210 |
| ar1-16 | 379242070 | 207107888 | 1594960252, 1523618046, 168417674, 20606404 |
| ar1-17 | 1055920531 | 1901945751 | 1301489750, 1261565030, 579531758, 1822901715 |
| ar1-18 | 2133118313 | 1800753884 | 1461571083, 1488595906, 688856225, 1927678864 |
| ar1-19 | 2102872469 | 149230512 | 1217296411, 90968200, 1602463611, 1741087819 |
| ar1-20 | 1600506978 | 1943687657 | 2102622658, 1357013345, 100106180, 1931697111 |
| white-01 | 188052562 | 1431168838 | 1891587003, 1697294631, 1803237116, 1060684896 |
| white-02 | 1501851379 | 1863999801 | 2011719561, 1211536402, 1724950367, 898939138 |
| white-03 | 1740183739 | 1241269774 | 2131104941, 1544013876, 1327216417, 1790832426 |
| white-04 | 607614599 | 546057503 | 1912681404, 805678233, 91075310, 950885165 |
| white-05 | 1507809470 | 776290915 | 1646235952, 81491730, 410527150, 495425711 |
| white-06 | 1849396610 | 142870846 | 1164831031, 1406544, 727495337, 695090960 |

Die tatsächlichen vollständigen PCG64-Anfangszustände wurden vor Datenziehungen verglichen. Hintergrund: `SeedSequence(background_seed, spawn_key=(role_id,), pool_size=4)`, train=0, validation=1, check=2; Messrauschen und Zusatzraster direkt mit ihren Integerseeds. **105/105** wissenschaftliche Daten-/Rasterzustände sind verschieden; einschließlich vier technischer Datenrollen **109/109**. Zusätzlich mit den entsprechenden zwölf historischen Pilotblöcken, deren Raster/technischen Rollen sowie beiden Tabellengeneratoren verglichen: **164/164** Zustände verschieden, keine Kollision.

Verschiedene Anfangszustände sind kein empirischer Unabhängigkeitsnachweis. Suchseeds werden nur als eindeutige Integer geprüft; ihre tatsächliche Julia-RNG-Herkunft ist eine separate Ausführungspflicht. Es wurden keine Mess-/Hintergrundwerte oder Rasterpunkte erzeugt und keine Fits/Suchen ausgeführt.

Reproduktionskontrolle: Derselbe Extraktor am historischen Bezugscommit liefert exakt die damaligen 1.766 Ausschlusswerte, SHA-256 `a6a653c98dd9fedf63626e30f57c148685952eefaa7062795d6cffa74c05021a` und die vollständige ursprüngliche 72er-Seedtabelle.

Ausführen in Blocknummernfolge: zunächst ar1-01, white-01, ar1-02, white-02,
bis ar1-06, white-06, danach ar1-07,…,ar1-20. Je Block fest
O, K, E64, E256, E1024, je Paket Mitglieder 1–4. Diese feste Armposition
begrenzt die Interpretation von Laufzeitunterschieden; Kosten bleiben
deskriptiv. Kein neuer Scheduler allein zur Balancierung. Alle 26 Fälle vorab
planen; keine Änderung nach Zwischenständen.

Vor dem ersten wissenschaftlichen Fit oder Suchaufruf alle 26 Eingabefälle
vorbereiten und lesend verifizieren: konkrete Beobachtungen, Hintergrundpools,
Präfixzuordnung, drei geschätzte Matrizen samt Alpha-Kandidaten, C_true,
Signalreferenzen, Raster und Quellen-/Optionsmanifeste. Zulässige numerische
Vorbereitungsfehler ebenfalls vorab mit Teilständen und betroffenen Armen
binden. Keine Suche günstiger Seeds/Matrizen durch Vorabauswertung.

## Suchprofil, Auswahl und Fehlergrenzen

Unverändert `r4x1000-local300x5-v1`: 4 × 1.000 äußere Iterationen, 300 lokale
Optimiereriterationen und **fünf zusätzliche** lokale Neustarts, beide
Häufigkeitsschalter an, allgemeine Grammatik, `should_simplify=false` und
übrige effektive Optionen des bestätigten Schema-4-Pakets. Die feste Matrix
wirkt sowohl auf Struktursuche als auch auf Konstantenoptimierung.

Ein gemeinsamer sauberer Ausführungscommit und dieselbe numerische Umgebung
für alle Blöcke: Python 3.12.14, Julia 1.13.1, PySR 2.6.0,
SymbolicRegression 2.5.1, gesperrte Python-/Julia-Abhängigkeiten, Haswell-BLAS,
eine CPU, Julia-/GC-/BLAS-Threads 1, interaktive Threads 0. Vor und nach der
Suche tatsächliche Herkunft, Adapterhashes, Umgebung und effektive Optionen
belegen; alle importierten Paketquellen binden. Keine stillschweigende
Aktualisierung zwischen Abschnitten.

Jedes Paket liefert genau **eine unveränderte Originalausgabe** nach endlichem
nativem Trainingsverlust, danach Komplexität und Mitgliedsposition. Die
bestehende Auswahl innerhalb einer Endfront bleibt ebenfalls erhalten.
Trainingsverluste verschiedener Arme haben unterschiedliche Skalen und werden
nicht zur gemeinsamen Armwahl verglichen. Signalwahrheit, Zusatzraster,
Kurvenklasse, Familie, klassische Referenzfits und Plots beeinflussen weder
Auswahl noch Stopp. Kein Neustart wegen ungünstiger Ergebnisse.

Alle 520 geplanten Suchversuche und ihre bekannten Kosten bleiben erhalten.
Gewöhnliche zulässige numerische Suchfehler/Timeouts wie im bestätigten Paket
behandeln. Ohne endliche zulässige Originalausgabe ist das Paket ausgefallen;
kein künstlicher Fehlerwert null. Ein ungültiger E-Schätzer sperrt nur seinen
Arm mit vier expliziten `not_run`-Mitgliedern; gültige andere Arme bleiben
geplant. Fehlende gemeinsame Beobachtungen betreffen alle fünf Arme.
Herkunftswidersprüche, Aufrufwächter, Unterbrechungen, unbekannte Fehler und
späte Quellen-/Archivänderungen sperren beziehungsweise widerrufen die gesamte
Freigabe. Nicht mit gewöhnlichen numerischen Ausfällen vermischen.

Klassische Fits mit bekannter Ringdown-Familie bleiben getrennte privilegierte
Diagnosen nach dem bestehenden Mehrstartvertrag, je verfügbarer Gewichtung.
O/K auch hier nur einmal je Block. Sie sind keine zusätzlichen SR-Suchaufrufe,
keine Ersatzformeln und kein Auswahlkriterium. Ihre numerischen Ausfälle
verhindern gültige SR-Arme nicht; Kosten und Fehler separat erhalten.

## Primärer Endpunkt und Unsicherheit

Vorab **1.024 unregelmäßige Punkte** auf demselben Intervall speichern:
je ein Punkt pro gleich breitem offenen Stratum, separater PCG64-Seed
`2026111610`, exakte Treffer auf dem 1/32768-Sekunden-Raster zurückweisen,
maximal 100 Ziehungen pro Stratum. Derselbe neue Rastervektor für alle Fälle;
seine Erzeugung verändert keinen Suchzufall. Bei Erzeugungsfehler vor Suchen
abbrechen. Die bisherigen 889 regulären Zwischenpunkte ebenfalls erhalten.

Für jede ausgewählte Originalformel lautet der **neue primäre Fehler**

\[
E_{b,a}=\frac{1}{|A|}\sqrt{\frac{1}{1024}
 \sum_{j=1}^{1024}\left[\widehat s_{b,a}(t_j^*)-s(t_j^*)\right]^2},
\qquad \Delta_b=E_{b,E1024}-E_{b,O}.
\]

Negative Delta bedeuten weniger Fehler durch E1024 in diesem Block. Dies ist
eine Bewertung an unbenutzten Zeiten im bekannten Fenster, keine unabhängige
Signalpopulation. Der Rastervektor ist über Blöcke fest: Unsicherheit bezieht
sich auf Messrauschen, Hintergrund und Suchzufall bei diesem Signal und Raster,
nicht auf alle kontinuierlichen Zeiten. Kein endliches Raster ersetzt den
Definitionsnachweis oder garantiert Identifizierbarkeit.

Je Modell alle Einzelwerte und acht gepaarten Kontraste berichten; Mittelwert,
Median, Min/Max und Stichproben-SD der jeweils verfügbaren Werte mit Nenner.
Ein Ausfall eines dritten Arms entfernt keine gültige Paarung. Geplante Nenner
sind **20 AR(1)- beziehungsweise sechs white-Pakete je Arm**, zusätzlich
104/520 geplante Suchversuche je Arm/Serie mit getrennten Modellanteilen.
Fehlende/nichtendliche Fehlerwerte mit Grund erhalten; keine Imputation,
Ausreißerentfernung, Winsorisierung oder zusätzliche Ersatzseeds.

Nur bei vollständigen Paaren eines Kontrasts seine Monte-Carlo-Unsicherheit
für den geplanten Vergleich ergänzen:

\[
\overline\Delta=\frac{1}{n}\sum_b\Delta_b,\quad
\operatorname{MCSE}=\frac{s_\Delta}{\sqrt n},\quad
I_{95}=\overline\Delta\ \pm\ t_{0.975,n-1}\operatorname{MCSE}.
\]

Das Student-t-Intervall ist eine **approximative, marginale** Präzisionsangabe
für den Mittelwert, keine exakte Garantie bei schiefen Verteilungen/Spitzen,
keine simultane Absicherung aller Kontraste und kein Freigabetest. Bei white
ist diese Grenze mit n=6 besonders wesentlich. Rohwerte und Streuung immer
mitzeigen. Bei fehlenden Paaren verfügbare Differenzen nur bedingt deskriptiv;
kein Intervall/MCSE als Aussage über den vollständigen Verfahrensvergleich.
Ausfallraten und Ursachen stets mit geplantem Nenner getrennt berichten.

Kein neues binäres Bestehenskriterium, keine automatische Armwahl und keine
Übertragung von 8/10. Für diese begrenzte deskriptive Studie wird keine
minimale relevante Effektgröße als Entscheidungsschwelle behauptet. Vor einer
späteren Überlegenheits-, Gleichwertigkeits- oder Nichtunterlegenheitsstudie
müssten deren Effekt-/Äquivalenzgrenzen und Powerplanung neu festgelegt werden.

Sekundär: Trainings- und regulärer Raster-RMSE/A, Maximalfehler/A auf allen
Rastern, MSE zu Beobachtungen, Q_true/N, Alpha, Kondition, Matrixabweichung und
Kontrollscore. Keine Chi-Quadrat-Freiheitsgradbehauptung für ausgewählte SR.
A–D-, Originalfamilien-, Domain- und Resttermverträge unverändert und getrennt;
ungeklärte Beweise bleiben ungeklärt. Ein endlicher Rasterfehler bleibt auch
bei ungeklärtem oder negativem Familien-/Domainbefund in der Fehlerauswertung;
er behauptet keine überall gültige Funktion. Neue Parameterübereinstimmungen bleiben
`not_assessed`. Keine Erkennerentwicklung zur Verbesserung dieser Zahlen.

## Ergebnisdarstellung: Plot und Originalformel

Ab diesem Beschluss Ergebnisse stets auch grafisch und mit nachprüfbarer
Formel ausgeben. Dies ist eine Darstellungsregel nach unveränderter Auswahl,
kein zusätzlicher Such- oder Bewertungshebel. Für diese Serie:

- Übersicht je Rauschmodell: alle Blockfehler über O/K/E64/E256/E1024,
  gepaarte Kontraste und deren Unsicherheit mit verfügbarem/geplantem Nenner;
  Matrixdiagnosen, Ausfälle und reale Kosten getrennt darstellen.
- Für **jede** der bis zu 130 Originalpaketausgaben Kurven- und Residuenplot:
  sauberes Referenzsignal, verrauschte Trainingsdaten, gespeicherte native
  Trainingsvorhersage und lesender Replay an den vorab gebundenen Rastern.
  Punkte nach Raster kennzeichnen; Verbindungslinien beweisen keinen Verlauf
  zwischen geprüften Punkten. Keine unbemerkte Glättung, Clipping oder
  logarithmische Achse, die Vorzeichen/Spitzen verdeckt.
- Unveränderten Originalformeltext mit allen gespeicherten Konstanten und
  Originalbaum zuordnen, t in Sekunden und Signalparameter nennen.
  Den Maximalfehler am festen Raster samt Koordinate sichtbar markieren. Lange
  Formeln in einer separaten Textdatei lesbar vollständig erhalten. Eine
  zusätzliche gesetzte Formel muss äquivalent und als Darstellung erkennbar
  sein; keine vereinfachte Ersatzformel als Original ausgeben.
- Lauf, Modell, Block, Arm, Trainingsmenge, ausgewähltes Mitglied/Seed,
  Ausführungs-/Prüfcommit sowie Eingabe-/Ergebnishashes mit CSV/JSON der
  dargestellten Werte binden. PNG plus SVG oder PDF exportieren. Auch
  Ausfälle/nichtendliche Werte sichtbar dokumentieren; nicht nur gute Fälle
  zeigen. Plots in getrenntem Auswerteexport, Originalarchive unverändert.

## Umfang, Aufwand und Ressourcen

26 Blöcke × fünf Pakete × vier Suchen = **520 Suchen**, **130 Paketausgaben**
und **520.000 geplante äußere Iterationen**. Die 104 unterschiedlichen
wissenschaftlichen Suchseeds werden innerhalb ihres Blocks fünfmal verwendet.
Die Fallzahl ist ein begründeter Kompromiss aus Replikation und Aufwand, keine
Literatur-Mindestzahl und keine gesicherte Powerrechnung [1]. AR(1) trägt die
Hauptfrage, white bleibt begrenzte Kontrolle; keine Poolung beider Modelle.

Erwogen wurden 12 AR(1)+6 white (360 Aufrufe) und 30+6 (720). Gewählt wurde
20+6 als mittlere Variante. Aus sechs alten AR(1)-Paaren des unregelmäßigen
E64-minus-O-Fehlers stammt eine SD von 0,00706733. Nur zur Planung ergibt
`1.96*0.00706733/sqrt(20)` rund 0,00310 oder 0,310 Prozentpunkte von A.
Dies ist **keine zugesicherte Intervallhalbbreite**: wenige Pilotpaare,
anderer Hintergrundumfang und mögliche Spitzen begrenzen die Übertragbarkeit.
Die tatsächlich erreichte Präzision wird vollständig berichtet; keine adaptive
Fallzahlerhöhung nach Zwischenständen.

Aus den gemessenen Workerzeiten des Piloten ergibt O+K+3E je Block rechnerisch
1,649 h für AR(1), 2,194 h für white; 20+6 damit **rund 46,14 Worker-Stunden**.
Vorbereitung, Referenzfits, Abschluss, Plots und Verifikation kommen hinzu.
Geänderte Matrizen können Suchkosten ändern; dies ist keine garantierte
Laufzeit oder Reservierung von 46 Stunden. Die 360-/720-Alternativen entsprechen
mit derselben unsicheren Extrapolation rund 32,95/62,63 Worker-Stunden.

Betriebsfristen: 1.800 s je wissenschaftlichem Worker und 7.800 s je Paket
wie bisher; fünfarmiger Block höchstens `5*7800+1800=40800` s einschließlich Abschluss.
Vorbereitung 2.400 s; Gesamtserie höchstens `26*40800+14400` s einschließlich
Abschluss, separate lesende Gesamtverifikation 14.400 s. Das sind äußere
Abbruchgrenzen, keine gewünschten Laufzeiten oder zusätzliche Iterationen.
Fristen gelten auch beim Abschluss; späte Überschreitung widerruft die Freigabe.
Etwaige begründete Änderungen nur vor der wissenschaftlichen Ausführung
versionieren, nicht nachträglich zur Rettung einzelner Fälle.

Wall-/CPU-Zeit vollständiger Aufrufe, Worker-/Fitzeiten, Verlustcallbacks und
lesende Prüfkosten erfassen. Enthaltene Zeiten nicht doppelt addieren;
Vorbereitung, Einrichtung und technische Vorläufe getrennt ausweisen.
Unbekannte Kosten bleiben unbekannt. O/K nur einmal tatsächlich bezahlt und
gezählt; kontrastweise wiederverwendete Kontrollen nicht als neue Läufe zählen.

## Technische Abnahme und nächster Ausführungsschritt

Noch erforderlich, in dieser Reihenfolge:

1. Dieses Protokoll getrennt committen und prüfen; Commit und SHA-256 vor
   Implementierung unveränderlich binden. Frühere Pläne/Berichte nicht ändern.
2. Mit vorhandenen Adaptern, Kovarianz-/Bewertungsverträgen und Archivmechanismen
   die fünfarmige Serie implementieren. Eigenes Format gegenüber dem 144er-Pilot;
   keine stillschweigende Umdeutung alter Archive. Dieses Planungsdokument ab
   seiner Laufzeitverwendung auch in die vollständige CI-Klassifikation aufnehmen.
3. Lokale Tests und gezieltes KI-Review: Präfixbindung, Rollen-/Seedtrennung,
   gemeinsame Kontrollen, Auswahl, vorgeplante Nenner, Fristen, nichtendliche
   Werte, Workerherkunft, unabhängige Metrik-/Intervallnachrechnung sowie späte
   Widerrufe. Grafiken gegen ihre zugrunde liegenden Werte prüfen. Draft-Entwicklung,
   vollständige erforderliche Ready-CI und autorisierte Übernahme.
4. Kleiner separater Manjaro-Vorlauf im neuen N128-Pfad: AR(1), derselbe
   1.024/128/256-Pool und alle fünf Arme, je **ein Worker mit zehn äußeren
   Iterationen**, lokal 300/5. Eigene technische Seeds: Messrauschen
   `2026111611`, Hintergrund `2026111612`, Suche `2026111613` gemeinsam über
   fünf getrennte Worker. Maximal 600 s je Worker, 7.200 s für den vollständigen
   technischen Aufruf samt Vorbereitung/Abschluss. Alle Hintergrundstufen,
   Quellen, Replay und Plotexport lesend prüfen. Signalqualität ist kein
   Abnahmekriterium. Paketwahl/Fehlerfälle zusätzlich mit gezielten Tests prüfen;
   der Ein-Mitglied-Vorlauf ersetzt diese nicht.
5. Erst dann konkreter Manjaro-Laufweg mit neuen IDs, Befehlen für Vorbereitung,
   520er-Serie, Fortschritt, lesende Verifikation, grafische Auswertung und
   Archivierung. Wissenschaftliche Fits/Suchen sind ein separater Schritt;
   keine wissenschaftliche Serie in GitHub Actions.

Nach Ausführung Integrität, Ausfälle, alle Einzelwerte, Kontraste und Kosten
berichten. Bei Ausfällen zuerst begrenzte Ursachenprüfung; keine automatischen
Ersatzläufe. Auch ohne Vorteil oder bei unzureichender Präzision ist die Studie
inhaltlich auswertbar, sofern technisch verifiziert; keinen Sieger erzwingen.
Ein weiterer Pegel, ein neues Signal, mehr Validierungsfenster, eine andere
Kovarianzmethode oder ein geändertes Suchbudget benötigt eine gesonderte,
aus diesen Befunden begründete Planung. Keine automatische Anschlussserie.

Originalarchive im gemeinsamen Archivordner plus unabhängige hashgeprüfte
Zweitkopie nach [Archivregel](results_archiving.md) erhalten. Plots, Formeln,
Plotdaten und getrennte Verifikation eindeutig an das Original binden. Im
[Ergebnisindex](results_index.md) tatsächliche Ausführung, Nachprüfung und
Sicherung getrennt nachtragen; aktuell existiert noch kein Ergebnis dieser Studie.
GitHub-Uploads optional, große Archive nicht in Git aufnehmen.

## Literatur und Aussagegrenzen

Inhaltlich am 16.11.2026 geprüft. Literatur begründet das Designprinzip;
20+6 Blöcke, die drei Mengen, Signal und Pegel sind Projektentscheidungen.

1. Morris, White und Crowther (2019), *Using simulation studies to evaluate
   statistical methods*, DOI 10.1002/sim.8086,
   [Volltext](https://discovery.ucl.ac.uk/id/eprint/10066118/1/2019%20-%20Morris%20-%20simulation%20studies%20tutorial%20-%20stat%20med.pdf).
   ADEMP, unabhängige Replikationen, gepaarte Methodenvergleiche,
   Monte-Carlo-Unsicherheit und transparente Ausfälle; keine universelle Fallzahl.
2. Ledoit und Wolf (2004), *A well-conditioned estimator for large-dimensional
   covariance matrices*, DOI 10.1016/S0047-259X(03)00096-4,
   [Originalarbeit](https://perso.ens-lyon.fr/patrick.flandrin/LedoitWolf_JMA2004.pdf).
   Rangmangel/Instabilität bei großer Dimension relativ zur Hintergrundmenge.
   Ihre analytische Optimalität betrifft einen anderen Schätzer und Verlust;
   kein Nachweis unseres Holdout-Verfahrens oder eines SR-Rekonstruktionsvorteils.
3. La Cava et al. (2021), *Contemporary Symbolic Regression Methods and their
   Relative Performance*,
   [Originalarbeit](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/c0c7c76d30bd3dcaefc96f40275bdc0a-Paper-round1.pdf).
   Vorhersagegenauigkeit und symbolische Wiederfindung trennen. Kein zufälliger
   Trainings-/Testsplit zeitlich korrelierter Samples aus dieser Arbeit übernommen.
4. Imai Aldeia et al. (2025), *Call for Action: Towards the Next Generation of
   Symbolic Regression Benchmark*, [arXiv v1](https://arxiv.org/html/2505.03977v1).
   Feste Seeds und Budgets; ihre 30 Wiederholungen sind kein allgemeines Minimum.
