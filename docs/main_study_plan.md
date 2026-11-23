# Verbindlicher Hauptversuchsplan: Hintergrunddauer und freie Ringdown-Rekonstruktion

Stand 23.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md).
Dieser Plan setzt den [begründeten Hauptentwurf](main_study_protocol.md)
nach dem [Pilotabschluss](pilot_closeout.md) um. Matrix, Signale, Rauschpegel,
Schätzer, Auswahlregel, Budget, Endpunkte, Seeds und Ausfallregeln sind damit
für die folgende Hauptserie festgelegt. Der Plan und seine Seedtabelle werden
vor wissenschaftlichen Beobachtungen separat versioniert und unveränderlich
an die Laufzeit gebunden. Ein Plancommit ist kein Nachweis ausgeführter Suchen.

Es gilt **4 × 1.000 Suchiterationen, lokal 300/5, mit zusätzlich gemessenen
Kosten**. Ein gleiches verbrauchtes Zeitbudget wird nicht behauptet.
Ein negativer oder unpräziser Dauereffekt ist ein zulässiger wissenschaftlicher
Abschluss. Neue Methoden, Datenpegel, Ersatzseeds oder adaptive Erweiterungen
gehören nicht in diesen Versuch. Historische Laufzeitpläne bleiben unverändert.

## Forschungsfrage und Bezug zum Exposé

Hauptfrage: Wie verändert die Länge **separater signalfreier Hintergrunddaten**
die Rekonstruktionsgenauigkeit und Strukturstabilität frei gesuchter
Ringdownformeln, wenn Kovarianzschätzer, Auswahlregel und Suchprofil feststehen?

Der [dokumentierte Exposé-Abgleich](representation_implementation_status.md#exposé-und-nächste-abgegrenzte-schritte)
nennt freie Formelsuche, relativen L2-Fehler als Hauptkriterium sowie die
Signalbedingungen 200 Hz/4 ms und 250 Hz/6 ms bei 25 ms Fensterdauer.
Das ursprüngliche Exposé-PDF ist im aktuellen Arbeitsbestand nicht erneut
verfügbar. Diese Angaben stammen deshalb aus dem früheren dokumentierten
Abgleich. Insbesondere wird daraus keine wörtlich nachgeprüfte Pflicht zu
identischer Rechenzeit abgeleitet. Die aktuelle Entscheidung lautet:
**festes Suchprofil und tatsächliche Kosten als zusätzlicher Endpunkt**.

Die [Folgestudie](noise_followup_results_manjaro_001.md) zeigt genauere
Kovarianzen ohne einen entsprechend gesicherten allgemeinen SR-Gewinn. Der
[Skalierungs- und Auswahlvergleich](white_loss_scaling.md) zeigt außerdem
Suchpfadabhängigkeit und bessere gespeicherte Alternativen. Er begründet
keine allgemeine Übernahme skalierter MSE, kein neues Messraster und keine
kleinere Komplexitätsgrenze. Zusätzliche unabhängige Signalbeobachtungen der
letzten Auswahlprüfung stehen bei einem einzelnen realen Ereignis nicht
nachträglich zur Verfügung. Sie werden hier nicht als Selektionsinformation
eingeführt.

Die Hauptserie schätzt den Effekt auf zwei festgelegten neuen
Signalbedingungen unter synthetischem stationärem Rauschen. Sie belegt keine
universelle Überlegenheit, keine Robustheit über sämtliche Ringdownparameter
und keine Leistung an LIGO-Daten. Bekannte Pilotfälle, deren Ausgaben oder
günstig ausgewählte Seeds werden nicht als neue Hauptstudienfälle übernommen.

## Konkrete Matrix und unabhängige Einheiten

| Bedingung je Signal | Unabhängige Blöcke | Arme je Block | Paketausgaben | Neue Suchworker |
| --- | ---: | ---: | ---: | ---: |
| AR(1), rho = 0,65 | 30 | 4 | 120 | 480 |
| Weißes Rauschen | 10 | 4 | 40 | 160 |
| Beide Signale zusammen | 80 | 4 | 320 | 1280 |

Jeder Arm besteht aus vier frischen Suchen; diese Neustarts bilden zusammen
**eine** Algorithmusausgabe. Je Signal liegen damit 30 unabhängige AR(1)-
und zehn unabhängige White-Blöcke vor. Die vier Arme, vier Suchseeds und
beiden Hintergrundpräfixe eines Blocks erhöhen diese unabhängige Fallzahl nicht.
Auch die beiden unterschiedlichen festen Signale sind keine zufällige
Stichprobe aus einer Signalpopulation.

Die Fallzahl ist ein begrenzter Ressourcenbeschluss mit mehr Replikation als
in der bisherigen Folgestudie, keine aus sechs White-Fällen abgeleitete Power-
oder Präzisionsgarantie. Die Hauptserie dient der Effektschätzung; eine neue
praktische Bestehensschwelle wird nicht nachträglich aus ihren Ergebnissen
erzeugt. Die Fallzahl bleibt nach dem ersten wissenschaftlichen Aufruf fest.
Es gibt keine Aufstockung bis zum gewünschten Vorzeichen oder Intervall.

| Arm | Gewichtung während Suche und Konstantenanpassung | Rolle |
| --- | --- | --- |
| O | Gewöhnliche MSE | Ungewichtete aktive Referenz |
| K | Wahre Modellkovarianz, Q/N | Privilegierte synthetische Referenz |
| E64 | Geschätzte volle Kovarianz aus 64 s Training, Q/N | Kurzer Hintergrund |
| E4096 | Derselbe Schätzer aus 4096 s Training, Q/N | Langer Hintergrund |

K ist kein praktisch verfügbarer Schätzer und kein garantierter
Leistungshöchstwert der endlichen SR-Suche. Die gleiche unveränderte Matrix
eines Arms bestimmt sämtliche Struktur- und Konstantenschritte. Die Arme
erhalten dieselbe verrauschte Signalbeobachtung und denselben Viererblock
von Suchseeds; unterschiedliche Verluste können trotzdem verschiedene
spätere Zufallszüge und Suchpfade erzeugen.

Eine zusätzliche mittlere Hintergrunddauer oder ein zweiter Schätzer wird
für diese begrenzte Hauptserie nicht ergänzt. Zwei vorab begründete Dauern
beantworten den vorgesehenen Kontrast mit weniger Bedingungen. Eine
monotone Wirkung über alle Hintergrundlängen lässt sich daraus nicht ableiten.

## Signal, Messfenster und Rauschmodell

Festgelegte Signale sind

```text
s(t) = A * exp(-t/tau) * cos(2*pi*f*t + phi)
A = 1, phi = 0 rad
signal_200_4ms: f = 200 Hz, tau = 0.004 s
signal_250_6ms: f = 250 Hz, tau = 0.006 s
```

Amplitude und Phase sind ausdrücklich festgelegte Bedingungen dieses
Hauptplans, keine erneut am Exposé-PDF bestätigten Angaben. Ein gemeinsamer
Pegel sigma/A = 0,05 hält die erste Hauptmatrix klein. Dies ist marginale
Rauschstandardabweichung relativ zur Amplitude und kein Detektor-SNR. Wegen
der verschiedenen Abklingzeiten ist sigma/RMS(s) zwischen Signalen
verschieden; beide Normierungen werden berichtet. Zusätzliche Pegel oder
Glitches gehören nicht nachträglich in diesen Versuch.

Die Abtastrate bleibt **4096 Hz**. Das nominelle Akquisitionsfenster ist
`0 <= t < 0.025 s`; die Messzeiten sind `t[j] = j/4096 s`, j = 0,...,102,
also **103 Punkte**. 25 ms mal 4096 Hz ergeben 102,4 und nicht 128 Samples.
Die letzte Messzeit ist 0,02490234375 s. Die Hauptbewertung einschließlich
Domainprüfung verwendet den ausdrücklich neuen geschlossenen Hauptbereich
`[0,1/40] s` mit exakt rationaler rechter Grenze. Sein letzter Abschnitt von
0,09765625 ms ist nicht durch einen zusätzlichen Messwert beobachtet. Ergebnisse auf dem engeren
Messstützbereich `[0,102/4096] s` werden zusätzlich getrennt berichtet.
Der numerische Diagnosepunkt `float(0.025)` ist auf Binary64 gerundet;
er ersetzt nicht die exakt rationale Grenze des Domainbeweises. Der
Messstützbereich ist exakt rational `[0,102/4096] s`. Die historische
N128-Achse und ihre Intervalle werden nicht umgedeutet.

White besteht aus unabhängigen zentrierten Gaußwerten mit Varianz sigma².
AR(1) verwendet einen stationären Anfang und rho = 0,65 pro 4096-Hz-Schritt;
`C_true[i,j] = sigma² * rho**abs(i-j)`. Training und sämtliche Hintergrundrollen
verwenden dasselbe Rauschmodell und denselben marginalen Pegel. Keine
Zentrierung einzelner Fenster, Filterung, nachträgliche Pegelanpassung,
Jitterachse oder Interpolation zusätzlicher Messwerte. AR(1) ist eine
kontrollierte synthetische Bedingung, kein realistisches vollständiges
Detektorrauschmodell.

Vor Ausführung werden die konkreten Binary64-Parameter und Arrays gespeichert.
Die saubere Referenz wertet die gespeicherten Parameter mit mathematischem pi
aus und wird unabhängig hochpräzise nachgerechnet. Die Wahrheit steht nur
der Datenerzeugung und der anschließenden Bewertung zur Verfügung.

## Hintergrunddaten, Schätzung und zulässige Information

Der Schätzer folgt dem gebundenen Streamverfahren der
[Dauerstudie](noise_followup_plan.md#hintergrunddauer-und-fester-schätzer),
angepasst an N = 103. Pro Block wird eine separate stationäre Reihe von
4096 s beziehungsweise 16.777.216 Samples erzeugt. E64 verwendet genau deren
erste 262.144 Samples. Die Dauern bezeichnen Trainingssamples geteilt durch
fs, nicht den Abstand vom ersten zum letzten Sample. Verschachtelte Präfixe
ermöglichen einen gepaarten Vergleich.

Nichtüberlappende vollständige 103er-Vektoren ergeben 2545 bzw. 162885
Trainingszeilen. Die neun bzw. 61 verbleibenden Samples werden archiviert,
aber nicht mit einem unvollständigen Vektor in die Matrix aufgenommen.
Die kontinuierliche Rauscherzeugung verwendet Chunks von 65536 Samples.
Für die Matrixreduktion werden ausschließlich die vollständigen Vektoren
übergeben; deren Chunklänge ist **65508 = 636 × 103 Samples**. Die
Chunks der Erzeugung und der Matrixreduktion sind verschiedene Verträge.
Der AR(1)-Zustand bleibt über Chunk- und Zeilengrenzen erhalten. Die Zeilen
sind deshalb nicht unabhängig; die Zahl der Zeilen ist keine unabhängige
Stichprobengröße für die abschließende Verfahrensbewertung.

Beibehalten werden der bekannte Nullmittelwert, `S = B.T @ B / M`,
`mu = trace(S)/N`, `C_alpha = (1-alpha)*S + alpha*mu*I`, das Alpha-Raster
`[0,0.001,0.01,0.05,0.1,0.2,0.5,1]` und die Konditionsgrenze `1e8`.
Die Streaming-Reduktionsreihenfolge wird versioniert und gegen eine
unabhängige Rechnung geprüft. Eine erfolgreiche Cholesky-Zerlegung und die
bestehenden SPD-/Konditionsprüfungen sind erforderlich. Ungültige Matrizen
werden nicht mit Jitter, Clipping, Pseudoinverse oder wahrer K ersetzt.

Je Block kommen **128 unabhängige Validierungsfenster** und **256 unabhängige
Kontrollfenster** mit jeweils 103 Punkten aus getrennten RNG-Rollen hinzu.
Ihre stationären Anfangswerte sind unabhängig; sie sind keine benachbarten
Ausschnitte der Trainingsreihe. Beide Dauerarme teilen diese Rollen. Alpha
wird ausschließlich nach Logdeterminante plus mittlerer Validierungsquadratik
gewählt; bei exaktem Gleichstand gewinnt das kleinere Alpha. Kontrolle,
Signalwahrheit und SR-Ergebnisse beeinflussen die Schätzung nicht.

64 und 4096 s bezeichnen somit **Trainingsdauer bei festem Zusatzumfang**,
nicht die gesamte zusätzlich bereitgestellte Rauschinformation. Die Rollen
umfassen zusätzlich 3,21875 s bzw. 6,4375 s Samples/fs an Validierungs- und
Kontrolldaten. Dies sind Sampleumfänge unabhängiger Fenster und keine Behauptung
einer einzigen entsprechend langen zusammenhängenden Aufnahme. Kontrollfenster
zählen zu den Kosten der Auswertung, nicht zum Schätz- oder Suchinput.
Trainings-, Validierungs-, Kontroll- und Messrauschen sowie der Suchzufall
werden als getrennte Quellen gespeichert.

## Festes Suchprofil, Auswahl und Kostenvergleich

Die Entscheidung ist **R: vier frische Suchen mit je 1000 äußeren Iterationen,
lokal 300 Optimiereriterationen und fünf zusätzlichen Neustarts**. Das
bestätigte Profil `r4x1000-local300x5-v1` liefert die fachliche Referenz:
physische Zeit t, Operatoren `+, -, *, /, exp, sin, cos`, maxsize/maxdepth 20,
zwei Populationen à 32, 50 Zyklen, beide Häufigkeitsschalter an,
`should_simplify=false` und die übrigen gebundenen effektiven Optionen.
Die neue Hauptserienanbindung muss ihre vollständige Übereinstimmung mit
diesen Optionen prüfen; neue Eingaben und N = 103 sind explizite Unterschiede.

Das Paket wählt unverändert den endlichen minimalen nativen Trainingsverlust,
danach kleinere Komplexität, Mitgliedsreihenfolge und ursprünglichen
Kandidatenindex. Verglichen wird nur innerhalb desselben Arms. Es gibt
keine gemeinsame Rangliste über unterschiedliche Verlustskalen. Zusätzliche
Signalbeobachtungen, die saubere Wahrheit, Bewertungsraster, Domainstatus,
Familienbeweis oder ein klassischer Referenzfit bestimmen weder Auswahl
noch Stopp. Die bessere nachträgliche Auswahl des Piloten wird deshalb
nicht als bereits bestätigte Hauptmethode übernommen.

Gleiche Iterationszahlen bedeuten **keine gleiche verbrauchte Rechenzeit**.
Die Hauptfrage betrifft dieses feste Algorithmusprofil. Vollständige Wall-
und CPU-Zeiten werden zusätzlich berichtet: Hintergrundvorbereitung und
Schätzung, jede Suche, Paket/Block, lesende Nachprüfung und Veröffentlichung.
Getrennte Messbereiche und enthaltene Zeiten dürfen nicht additiv doppelt
gezählt werden. Soweit erfasst, ergänzen Callbackzahlen und verarbeitete
Zyklen die Kosten. Nicht gemessene Kompilierzeit bleibt unbekannt.

Die Alternative vier mal gemeinsamer Suchzeit ist für diese Hauptserie
zurückgestellt. Sie würde eine neue Halteregel mit anderem Verlauf und
eigenem Zeitfenstervertrag benötigen; der historische
[400-s-Vergleich](iteration_time_results_manjaro_001.md) rechtfertigt ihre
automatische Übernahme nicht. Es folgt daher keine neue Zeitbudgetkalibration
oder weitere Suche nach einem günstigeren Budget. Zeitgleichheit wird weder
aus Ein-CPU-Ausführung noch nachträglich aus ähnlich langen Läufen behauptet.

Alle Arme laufen seriell auf demselben gebundenen Rechner mit einer erlaubten
CPU, bestätigten Julia-/GC-/BLAS-Threads und derselben numerischen Umgebung.
Versionen und tatsächliche Prozessbelege werden gespeichert; gleiche Seeds
allein belegen keine plattformübergreifende Bitgleichheit. Bei einem
Rechner-/Umgebungswechsel entsteht ein getrennt gekennzeichneter Ausführungsblock.

## Bewertung, Primärkontraste und Unsicherheit

Das Hauptkriterium ist der **relative L2-Fehler auf einem vorab gespeicherten
unregelmäßigen Prüfraster**:

```text
E_L2 = sqrt(sum_k (prediction[k]-truth[k])**2 / sum_k truth[k]**2)
```

Die Implementierung bildet die Normen gegen Zwischenüberlauf geschützt und
prüft einen endlichen positiven Referenznenner; die Formel beschreibt die
mathematische Größe, keine Anweisung zu ungeschütztem Quadrieren.

1024 Strata gleicher Breite teilen `[0,0.025] s`; aus jedem offenen Stratum
wird unabhängig ein Punkt gezogen. Derselbe vorab gebundene Vektor gilt für
alle Arme, Blöcke und beide Signale; der RNG ist vom Suchzufall getrennt.
Jeder Hauptpunkt hat dasselbe Gewicht 1/1024; der gemeinsame Faktor kürzt
sich in der angegebenen Normquote heraus.
Exakte Treffer auf Messzeiten werden abgelehnt, höchstens 100 Ziehungen je
Stratum. Ein Erzeugungsfehler stoppt vor wissenschaftlichen Suchen. Endpunkte
werden zusätzlich diagnostiziert, nicht heimlich mit anderen Gewichten in
die Hauptnorm aufgenommen. Ein getrenntes ebenso gebundenes Prüfraster auf
dem engeren Messstützbereich liefert die angekündigte Randdiagnose.

Das ist eine diskrete Norm und zugleich eine festgelegte Quadraturdiagnose,
kein Beweis einer kontinuierlichen L2-Norm oder einer überall gültigen Formel.
Für dasselbe Raster und gleiche Gewichte gilt exakt in reeller Arithmetik:
`E_L2 = (RMSE/A) / (RMS(truth)/A)`. Innerhalb eines Falls bleiben Rangfolgen
gleich; zwischen den beiden Signalen ändert sich der Nenner. Alte RMSE/A-
Tabellen werden nicht umetikettiert. Der neue Hauptbericht enthält zusätzlich
RMSE/A und Maximalfehler/A zur Vergleichbarkeit.

Die **zwei Primärkontraste** sind, getrennt für jedes Signal unter AR(1),
`Delta = E_L2(E4096) - E_L2(E64)`. Negative Werte bedeuten kleineren Fehler
bei längerem Hintergrund. Die Hypothesen und Signalreihenfolge werden nicht
nach Kenntnis der Ergebnisse vertauscht. White-Dauerkontraste, E64/O,
E4096/O, K/O und beide Schätzer/K sind sekundär beziehungsweise Kontrollen.
Es gibt keine nachträgliche Poolung zu einer günstigen Gesamtrangfolge.

Je Kontrast werden alle Einzelpaare, verfügbar/geplant, Mittelwert, Median,
Min/Max und Stichproben-SD der Differenzen berichtet. Bei vollständigen
Paaren ist `MCSE = SD(Delta)/sqrt(n)`. Für die zwei Primärkontraste werden
zweiseitige **97,5%-t-Intervalle** des gepaarten Mittels angegeben, als
Bonferroni-Konstruktion für eine approximative gemeinsame 95%-Abdeckung.
Die endliche n=30-Stichprobe und mögliche schwere Ausreißer begrenzen die
t-Approximation; deren nominelle Deckung ist keine gemessene Garantie.
Sekundärintervalle sind höchstens marginale beschreibende 95%-t-Intervalle
und begründen keine zusätzliche familienweite Überlegenheitsbehauptung.

Die tatsächlichen MCSE und Intervallbreiten zeigen die erreichte Präzision.
Die budgetbegrenzte Fallzahl garantiert keinen vorab bestimmten kleinen
Fehlerbalken. Ein Intervall, das null umfasst, belegt weder Äquivalenz noch
Wirkungslosigkeit. Ein günstiger Mittelwert bei großen Ausreißern wird mit
vollständigen Einzelwerten und Median eingeordnet. Keine Ausreißerentfernung,
kein ergebnisabhängiges Bootstrapverfahren und keine adaptive Fallzahl.

Sekundär werden Originalfamilie und Originaldomain nach bestehenden begrenzten
Beweisverfahren bewertet, mit explizit gebundenem Hauptintervall. Gültig,
nachgewiesen ungültig und ungeklärt bleiben getrennt. Eine ungeklärte Familie
ist kein Nachweis ihrer Nichtzugehörigkeit; eine symbolische Fortsetzung
repariert die Originalausgabe nicht. Familien-/Domainanteile erhalten stets
ihren geplanten Nenner; bei vollständig erfassten Statuswerten einschließlich
`ungeklärt` können marginale Wilson-Intervalle je benanntem Status ergänzt
werden. Erforderlich ist vollständige Statuserfassung, nicht durchgängiger
Beweiserfolg. Solche Anteile sind
keine nachträglich eingeführte Haupt-Bestehensgrenze.

**Strukturstabilität** wird zusätzlich für die ausgewählten Originalbäume
innerhalb jeder Signal-/Rauschmodell-/Armgruppe operationalisiert. Ein
rein syntaktischer Deskriptor ersetzt in der exportierten Baumstruktur jede
numerische Konstante durch denselben Platzhalter und erhält Operatoren,
Zeitvariable, Klammerung und Reihenfolge sämtlicher Kinder. Es erfolgt keine
algebraische Vereinfachung, kommutative Umsortierung oder Aliasreduktion.
Je Gruppe werden alle Deskriptorhäufigkeiten, die Zahl verschiedener
Deskriptoren und der Anteil des häufigsten Deskriptors am geplanten Nenner
berichtet. Fehlende Ausgaben bilden einen eigenen Status und werden nicht
als gemeinsamer Formeltyp gezählt. Unterschiedliche Syntax kann dieselbe
Mathematik ausdrücken; wiederkehrende Syntax beweist umgekehrt weder richtige
Parameter noch physikalische Zugehörigkeit. Deshalb stehen diese Häufigkeiten
neben den getrennten Familien-/Domainbelegen. Die Variation umfasst hier
gemeinsam Messrauschen, Hintergrund und Suchzufall; ihre Varianzbeiträge
lassen sich aus dieser Matrix nicht einzeln identifizieren.

Neue physikalische Parameterübereinstimmungen und quantifizierte Restterme
bleiben **not_assessed**, solange dafür keine eigene vorab begründete Regel
gebunden ist. Ein Familienbeweis allein ist kein Nachweis richtiger Frequenz
oder Dämpfung. Eine spätere diagnostische Aliasdarstellung darf eine reduzierte
Frequenz nicht als die tatsächlich frei gefundene Originalfrequenz ausgeben.
Neue klassische Fits mit bekannter Familie gehören nicht zur
festgelegten Vierarmmatrix. Sie wären privilegierte Zusatzreferenzen mit
separatem Aufwand und keine freie Formelrekonstruktion.

## Ausfälle, Grenzen und vollständige Rechenschaft

Fehlgeschlagene Schätzungen betreffen genau ihren Arm; O und K bleiben bei
gültigen gemeinsamen Beobachtungen ausführbar. Eine ungültige Matrix wird
nicht durch K oder O ersetzt. Ein Paket ohne zulässige endliche Originalausgabe
ist ausgefallen. Sämtliche vorgesehenen Mitglieder bleiben mit Status und
bekannten Kosten im Nenner, auch `not_run`-Mitglieder.

Bei einem nichtendlichen Rasterfehler wird kein künstlicher Zahlenwert
eingesetzt. Für jeden Kontrast werden beide verfügbar, nur E64 verfügbar,
nur E4096 verfügbar und beide fehlend ausgewiesen. Bei fehlenden Paaren sind
die Fehlerdifferenzen unter verfügbaren Paaren nur bedingte Deskription;
kein Intervall wird als vollständiger Verfahrensvergleich ausgegeben.
Ausfallunterschiede werden separat vollständig berichtet. Eine finite
Rasterabweichung bleibt als solche sichtbar, selbst wenn die Originaldomain
eine Lücke enthält; sie wird dann nicht als kontinuierliche Güte interpretiert.

Numerische Ausfälle und harte Workerfristen werden nach dem gebundenen
Fehlervertrag von Herkunftswidersprüchen, unerwarteten Fehlern, Unterbrechung
und geänderten Quellen getrennt. Letztere sperren den vollständigen Abschluss.
Keine automatischen Ersatzseeds, Budgetverlängerungen oder Wiederholung eines
ungünstigen Fits. Ein technischer Neustart erhält eine eigene Lauf-ID und
die verbrauchten Teilkosten bleiben erhalten.

Als Betriebsgrenzen gelten 1800 s je wissenschaftlichem Worker,
7800 s je Viererpaket und 33000 s je Vierarmblock. Für jeden
Signalabschnitt mit 40 Blöcken gilt `40*33000 + 14400` s einschließlich
Abschnittsabschluss; Vorbereitung und lesende Gesamtverifikation erhalten
je 14400 s. Das sind Sicherheitsobergrenzen, keine Laufzeitprognosen. Eine
Friständerung wäre vor wissenschaftlichem Start mit Ressourcenbegründung zu
binden; sie wird nicht nachträglich zur Rettung eines Ergebnisses vorgenommen.

Die beiden Signalabschnitte erhalten unabhängige Abschlussbelege unter einem
vorab gebundenen Gesamtplan. Vorhandene erfolgreiche Abschnitte werden lesend
geprüft und bei späterer Ausführung des noch nicht begonnenen Abschnitts nicht
als neue Suchen gezählt. Innerhalb eines abgebrochenen Abschnitts gibt es
ohne gesondert implementierten und vorab geprüften Fortsetzungsvertrag keine
automatische Übernahme einzelner guter Pakete. Wiederholte Daten sind keine
zusätzlichen unabhängigen Blöcke. Suspend/Uhrsprünge und Integritätsabbrüche
bleiben erhalten; ein Statuszähler ersetzt keinen erfolgreichen Abschluss.

## Seeds, Ablauf und technische Umsetzung vor Start

Die verbindliche Tabelle [main_study_seeds.json](../data/main_study_seeds.json)
enthält 80 Zeilen mit jeweils Messseed, Hintergrundwurzel und vier Suchseeds,
also 480 wissenschaftliche positive 31-Bit-Werte. Ihr SHA-256 ist
`b03b2ec41a868e6875169c5375639c2fbee5c52838063ae479a3dd990a870381`.
Der getrennte [Generator](../scripts/generate_main_study_seeds.py) erzeugt
nur die Seedtabelle, keine Messwerte, Hintergrundreihen oder Bewertungsraster.

Historischer Bezugscommit ist `a0ddad1ad7751ed858a40534a8a2fd41b73be523`.
Aus sämtlichen 471 regulären UTF-8-Blobs dieses Git-Baums werden positive
31-Bit-Dezimaltokens mit `(?<![A-Za-z0-9_])\d+(?![A-Za-z0-9_])`
ausgeschlossen: 4850 verschiedene Zahlen, vollständig sortiert in der
Tabelle erhalten. Die ASCII-Folge jeder sortierten Zahl mit abschließendem LF
hat SHA-256 `0038eb2257b72a62ad41d5034f297bb8338f61018f361bdf8a2bbbc9779b0ac4`.
Nicht als UTF-8 lesbare Blobs sind mit Pfad dokumentiert; sie liefern keine
Dezimaltokens. Anders als der ältere Dauerplan beschränkt dieser Scan sich
nicht auf fünf Unterordner. Die exakte Git-Baumliste ist zusätzlich gebunden.

Reserviert sind 2026112701 für die Tabellenziehung, 2026112702 für das
Hauptprüfraster, 2026112703 für das Stützbereichsraster sowie
2026112704, 2026112705 und 2026112706 für die technischen
Mess-/Hintergrund-/Such-Tabellengeneratoren. Einige Reservierungen stehen
bereits im vorherigen Planungsdokument; sie werden deshalb nicht als im
Bezugsbestand neue Werte behauptet. Keine Reservierung wird als neu
gezogener wissenschaftlicher oder technischer Daten-/Suchseed verwendet.

NumPy 2.5.3, `Generator(PCG64(2026112701)).integers(1,2**31)` liefert
480 akzeptierte wissenschaftliche Seeds bei 480 Ziehungen, ohne Verwerfung.
Historische, reservierte und bereits akzeptierte Werte sind ausgeschlossen.
Die Slots werden in der unten festgelegten Fallreihenfolge gefüllt, je Zeile
Messseed, Hintergrundwurzel und vier Suchseeds. Alle Zustände vor und nach
Ziehung und eventuelle Verwerfungen sind gespeichert.

Danach werden in Reihenfolge Mess-/Hintergrund-/Suchrolle aus ihren drei
reservierten PCG64-Generatoren jeweils zwei weitere zulässige Zahlen gezogen;
der Ausschluss umfasst zusätzlich alle wissenschaftlichen und bereits
angenommenen technischen Zahlen. Sechs technische Seeds werden aus sechs
Ziehungen ohne Verwerfung angenommen. Zwei `technical_cases` enthalten je
einen AR(1)-Fall pro Signal, `block=0`, einen eigenen Messseed und Hintergrundseed
sowie genau einen Suchseed, den die vier technischen Arme dieses Falls teilen:

| Technischer Fall | Messseed | Hintergrundwurzel | Suchseed |
| --- | ---: | ---: | ---: |
| `signal_200_4ms-technical-ar1` | 1429806109 | 862718505 | 159810800 |
| `signal_250_6ms-technical-ar1` | 277587312 | 106026128 | 1270129815 |

Messrauschen verwendet PCG64 direkt aus dem jeweiligen Messseed.
Hintergrundrollen erhalten `SeedSequence(background_seed, spawn_key=(role,),
pool_size=4)` mit train=0, validation=1 und check=2. Mess- und Suchzufall
bleiben getrennt. Die tatsächlichen initialen Zustände aller Datenrollen
und Achsen werden vor Datenbildung auf Kollisionen geprüft und gebunden.
Eindeutige Anfangszustände sind ein technischer Bindungsnachweis, kein
empirischer Unabhängigkeitsbeweis.

Signalreihenfolge: zuerst 200 Hz/4 ms, dann 250 Hz/6 ms. Innerhalb eines
Signals AR1-01, White-01, ..., AR1-10, White-10, danach AR1-11 bis AR1-30.
Die Reihenfolge der vier Arme rotiert vorab nach der Position 0,...,39
in dieser Ausführungsfolge jedes Signals, nicht nach dem wiederholten
modellinternen Blocknummernfeld. Der Versatz ist Position modulo vier über
O/K/E64/E4096, K/E64/E4096/O, E64/E4096/O/K, E4096/O/K/E64.
Mitglieder laufen in ihrer gespeicherten Reihenfolge. Alle Eingaben und
Kovarianzen werden vor dem ersten wissenschaftlichen Fit vorbereitet und
gebunden; erklärte Vorbereitungsfehler erzeugen vorgesehene `not_run`-Arme.

Vor dem ersten Hauptlauf müssen folgende Bindungen und Prüfungen vorliegen:

1. Dieser unveränderte Protokollstand und die vollständige Seedtabelle sind
   vor wissenschaftlichen Beobachtungen in einem eigenen Commit gebunden.
   Der Lauf bindet dessen Commit und beide SHA-256-Werte zusätzlich zur
   konkreten Implementierungsfassung und den erzeugten Eingaben.
2. Neue Serienanbindung für N=103, den expliziten Hauptbereich und relativen
   L2-Endpunkt, ohne die alten N128-Laufwege oder eingefrorenen Pläne umzudeuten.
   Das Artefakt nennt verwendete Ausführungs-, Bewertungs- und Quellenfassungen.
3. Unabhängige Referenzen für neue Datenform, Schätzerpräfixe, L2-Normierung,
   Domainintervall, Auswahl und Ausfall-/Kostenregeln; separater lesender
   Serienverifikator und erforderliche CI. Kein Qualitätsgewinn als Testgate.
4. Ein begrenzter technischer Integrationsvorlauf auf dem Zielrechner:
   beide Signaldefinitionen, vier Arme, je ein frischer Zehn-Iterationen-Worker,
   lokal 300/5, eigene technische Daten und Seeds. Die acht Worker erhalten
   je 600 s, der Gesamtaufruf und sein separater Replay je 14400 s.
   Jeder Fall verwendet beide vollständigen
   Hintergrunddauern. Die Worker prüfen Eingabe-/Quellenbindung, Laufweg,
   Ressourcen und Replay; keine 1000er-Budgetkalibration und keine Auswahl
   nach Kurvenqualität.
5. Konkreter Startauftrag mit neuen Lauf-IDs, vollständigen Befehlen,
   Ressourcenrahmen, lesender Fortschrittsanzeige und Archivpfaden. Ein
   Protokoll oder erfolgreicher Vorlauf ist kein Beleg ausgeführter Hauptsuchen.

Diese Voraussetzungen begrenzen die technische Implementierungs- und
Integrationsaufgabe. Es folgt keine weitere offene Suche nach Grammatik,
Skalierung, Komplexitätsgrenze, Halteregel oder besonders günstigen Seeds.

## Darstellung, Archivierung und spätere Detektordaten

Alle 320 geplanten Paketausgaben einschließlich fehlender Ausgaben werden
dargestellt. Originalformeltexte und Bäume, Einheiten, Fall-/Armzuordnung,
sämtliche geplotteten Punkte, Vergleichsgrafiken mit vollständigem Wertebereich
und Ausfalltabellen bleiben gebunden. Eine logarithmische oder Symlog-
Zusatzansicht ersetzt keine lineare Vollansicht. Wahrheitszugriff dient der
Bewertung, nicht der nachträglichen Auswahl einer besseren Hauptausgabe.

Originalarchive, bekannte Abbruchkosten und unveränderte Quellen werden nach
der [Archivregel](results_archiving.md) erhalten; Berichte und tatsächlicher
Sicherungsstand werden im [Ergebnisindex](results_index.md) nachgeführt.
Unabhängige Zweitkopien sind nur nach Hashprüfung als bestätigt zu bezeichnen.
Große Datensätze werden nicht in die Git-Historie übernommen.

LIGO-Hanford ist eine spätere getrennte Anwendung. Ereignis/GPS-Zeiten,
signalfreier Bereich, Stationaritätsannahmen, Mittelwertbehandlung,
Filterung/Downsampling, konsistente Modell- und Kovarianztransformation sowie
zulässige Auswahl-/Bewertungsinformation sind dafür gesondert festzulegen.
Injektionen in gemessenen Hintergrund erlauben eine bekannte Signalwahrheit;
bei einem beobachteten Ereignis ist der saubere Ringdown nicht bekannt.
Der synthetische relative-L2-Endpunkt darf dort nicht mit einer angenommenen
Modellkurve als tatsächlicher Wahrheit ausgegeben werden.

## Literaturbezug und Aussagegrenzen

- [Morris, White und Crowther (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/):
  Ziele, Datengenerierung, Methoden, Endpunkte und Monte-Carlo-Unsicherheit
  explizit trennen. Die vorliegende Fallzahl ist eine Ressourcenentscheidung,
  keine aus dieser Quelle abgeleitete Powergarantie.
- [Cranmer (2023)](https://arxiv.org/abs/2305.01582): freie Suche, lokale
  Konstantenoptimierung und Ergebnisauswahl sind getrennte Komponenten.
  Ein bekannter Ringdown-Strukturfit ersetzt nicht die freie Suchfrage.
- [VanderPlas (2018)](https://arxiv.org/abs/1703.09824): die Abtastung prägt
  Aliasmehrdeutigkeiten. Zusätzliche Wahrheitsdiagnosepunkte reduzieren
  Rasterblindstellen, liefern der Suche aber keine neuen Messinformationen.
- [Wang und Shao (2024)](https://link.aps.org/accepted/10.1103/PhysRevD.109.043027):
  der Vergleich betrifft 64 und 4092 s aus einer 4096-s-Aufnahme sowie andere
  ACF-/PSD-Verfahren. Die dortigen Ergebnisse begründen keine Garantie eines
  isolierten freien SR-Gewinns durch unsere 4096 s; die unterschiedlichen
  Methoden- und Dauereffekte bleiben getrennt.
- [Siegel, Isi und Farr (2025)](https://arxiv.org/abs/2410.02704):
  Daten, Modell und Kovarianz müssen bei Konditionierung konsistent behandelt
  werden. Hintergrunddauer und Länge des analysierten Signals sind
  verschiedene Größen; der Übergang zu Detektordaten benötigt eigene Regeln.

Die inhaltliche Quellenzuordnung stützt sich auf die vorhandenen
[Literaturnotizen der Folgestudie](noise_followup_results_manjaro_001.md#einordnung-in-bisherige-arbeit-und-literatur)
und den dort dokumentierten Geltungsbereich. Literatur ersetzt keine
vorab gebundene konkrete Hauptstudienentscheidung und keine neuen Ergebnisse.
