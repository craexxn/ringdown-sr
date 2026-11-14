# Protokoll: erster begrenzter Rauschpilot mit 144 Suchen

Stand 14.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md).
**Beschlossen am 14.11.2026: 144 Suchaufrufe**, vor Implementierung getrennt
versioniert. Die Umfangsentscheidung ist abgeschlossen; die Alternativen unten
bleiben als Begründung erhalten. Wissenschaftliche Ausführung ist ein separater
Schritt nach technischer Abnahme, kein Bestandteil der Protokollübernahme.
Technische Basis ist PR89-Merge `8b9c6ef3a17fed03958a24ff36698bd47622eca5`;
die geprüfte Manjaro-Dokumentation in PR90 hat Head
`4e1fa18461b2b32fc2f8c39e77fd7c51b06c868a` und ist mit PR90 als
`3aa02bcfadc536adb1a4dd2477176dd4c211d8e3` übernommen. Dieser Plan bleibt
vor Implementierung eigenständig gebunden. Keine Änderung historischer Protokolle, Originalauswahlen oder
Bewertungsregeln.

## Fragestellung und begrenzte Aussage

Untersucht wird die Rekonstruktion eines festen bekannten Ringdown-Signals
unter weißem beziehungsweise korreliertem Gaußrauschen mit festem Pegel. Drei
Suchverfahren unterscheiden sich allein durch gewöhnliche MSE, bekannte
wahre Kovarianz und aus unabhängigen Hintergrunddaten geschätzte Kovarianz.
Primärer Vergleich ist geschätzte Gewichtung gegen gewöhnliche MSE; die
bekannte Kovarianz ist ein privilegierter Kontrollarm. Ein Vorteil geschätzter
Gewichtung ist eine Hypothese, keine Voraussetzung für einen gültigen Lauf.

Dies ist ein explorativer Pilot für die folgende Hauptversuchsplanung,
keine neue unabhängige Bestätigung des Suchprofils, kein Nachweis allgemeiner
Rauschrobustheit und keine Aussage über reale Detektordaten. Ein Pegel erlaubt
keine Aussage über eine Pegelabhängigkeit. Das bekannte Signal wird bewusst
weiterverwendet; damit werden Signalvariation und Rauschwirkung zunächst getrennt.

## Umfang und abgewogene Optionen

| Variante | Feste Signale | Rauschmodelle | Blöcke je Signal/Modell | SR-Aufrufe | Paketausgaben |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kleiner Machbarkeitseinstieg | 1 | 2 | 3 | 72 | 18 |
| **Beschlossen** | **1** | **2** | **6** | **144** | **36** |
| Breiterer Signalvergleich | 2 | 2 | 6 | 288 | 72 |

Jeder Block umfasst drei Gewichtungsarme mit jeweils vier neuen Suchen.
Die 144er-Variante liefert zwölf unabhängige Dreiervergleiche und 144.000
geplante äußere Iterationen. Die zwölf Suchmitglieder eines Blocks sind keine
zwölf unabhängigen Rauschrealisierungen. Die kleinere Alternative mit nur
Blöcken 1–3 wurde wegen der geringeren Replikation nicht gewählt. Die größere
Alternative mit zusätzlichem `confirm_high` wurde für diesen begrenzten ersten
Pilot zurückgestellt. Sie ist kein automatischer Anschlussauftrag.
Die folgenden konkreten Vorgaben beschreiben ausschließlich die beschlossene
144er-Variante.

Die Zahl sechs ist eine begrenzte Ressourcenentscheidung, keine Powerrechnung
oder Literaturvorgabe. Schon die maximal mögliche Monte-Carlo-Standardabweichung
einer binären Erfolgsrate beträgt bei sechs unabhängigen Blöcken rund 20,4
Prozentpunkte, bei drei rund 28,9. Deshalb kein neuer Erfolgsquotennachweis,
kein Signifikanztest als Freigabekriterium und keine Übertragung der früheren
rauschfreien 8/10-Grenze. Weniger Bedingungen mit mehr Wiederholungen haben hier
Vorrang vor zwei Pegeln mit jeweils nur drei Blöcken [1, 2].

## Festes Signal, Zeitfenster und Pegel

Verwendet wird `confirm_mid` aus der
[rauschfreien Bestätigung](restart_budget_confirmation_plan.md): A=11/12,
f=265 Hz, tau=1/150 s, phi=1/4 rad. Die Auswahl folgt der mittleren
Frequenzposition der vorab festgelegten Bestätigungssignale, nicht künftigen
Rauschergebnissen. Diese Kombination ist hinsichtlich der anderen Parameter
nicht der Mittelpunkt des gesamten Parameterkastens.

Maßgeblich sind die unveränderten gespeicherten Binary64-Parameter:

| Parameter | Hexwert |
| --- | --- |
| A | `0x1.d555555555555p-1` |
| f / Hz | `0x1.0900000000000p+8` |
| tau / s | `0x1.b4e81b4e81b4fp-8` |
| phi / rad | `0x1.0000000000000p-2` |

128 Trainingspunkte `t[j]=j/4096 s`, j=0,…,127. Das geschlossene Prüfintervall
ist [0,127/4096] s. Physische Zeit t, keine Zeitnormalisierung. Die saubere
Wahrheit bleibt A exp(−t/tau) cos(2 pi f t+phi), mit mathematischem pi und den
exakten Werten der gespeicherten Parameter. Alle Referenzwerte vor der Suche
unabhängig hochpräzise gegenrechnen wie in der Bestätigung; keine neue Toleranz.

Ein festes marginales Verhältnis **sigma/A=0,05** wird als erster
Pegel gewählt. Berechnung: Binary64-Multiplikation des gespeicherten A mit
Binary64 `0.05`; konkretes sigma ist `0x1.7777777777778p-5`, ungefähr
0,04583333333333334. Der tatsächlich realisierte Rauschvektor wird weder
zentriert noch auf eine gewünschte empirische Varianz nachskaliert.

- **white:** unabhängige normalverteilte Samples mit Mittelwert null und
  Varianz sigma²; `C_true=sigma² I`.
- **ar1:** stationäres Gauß-AR(1) mit rho=0,65 und derselben marginalen Varianz;
  `C_true[i,j]=sigma² rho**abs(i-j)`. Jedes Fenster erhält einen eigenen
  stationären Anfangswert nach dem bestehenden Erzeugungsvertrag.

Gleiche marginale Varianz bedeutet nicht gleiche Detektierbarkeit bei
unterschiedlicher Korrelation. Dieses Verhältnis heißt ausdrücklich nicht
Detektor-SNR. SRBench verwendet dagegen sigma/RMS(s) [2]; für unser festes
Signal entspricht der gewählte Pegel ungefähr 0,212696 in jener Konvention.
Die Abweichung ist benannt, keine Gleichsetzung verschiedener Rauschdefinitionen.
Ein späterer stärkerer Pegel benötigt einen eigenen vorab festgelegten Auftrag.

Im weißen Kontrollfall sind wahre GLS und MSE mathematisch proportional.
Deshalb wird dort kein Vorteil wahrer Gewichtung verlangt. Rundung,
Backendnormalisierung und Suchdynamik können trotz proportionaler mathematischer
Verluste unterschiedliche Formeln erzeugen. Der Kontrollarm mit wahrer Kovarianz
ist auch unter AR(1) keine garantierte obere Leistungsgrenze einer stochastischen SR.

## Hintergrund und unveränderter Schätzer

Pro Block werden **64 Trainings-, 128 Validierungs- und 256 Kontrollfenster**
mit jeweils 128 Samples unabhängig erzeugt. Alle vier Rauschrollen einschließlich
des Messrauschens haben dieselbe Verteilung und Abtastung, aber getrennte
Generatorzustände. Keine überlappenden Ausschnitte als unabhängige Fenster zählen.

Diese bisherigen technischen Mengen werden hier bewusst als **ein einziges
datenarmes Pilotszenario** übernommen: M_train/N=0,5. Die rohe Matrix ist
damit strukturell singulär; die vorhandene Regularisierung ist inhaltlicher
Teil des untersuchten Verfahrens. Die Mengen sind weder optimal noch durch
die Literatur als ausreichend für eine Hauptstudie begründet [3]. Eine
Hintergrundstaffel gehört in einen späteren Plan.

Der [bestehende Kovarianzvertrag](covariance_method_plan.md) bleibt erhalten:
bekannter Nullmittelwert, `S=B_train.T @ B_train / M_train`,
`mu=trace(S)/N`, `C_alpha=(1-alpha)S+alpha*mu*I`.
Alpha-Raster `[0,0.001,0.01,0.05,0.1,0.2,0.5,1]`, `kappa_max=1e8`;
Alpha null wird bei M_train<N strukturell verworfen. Auswahl ausschließlich
über den vorhandenen Gaußscore auf den Validierungsfenstern, einschließlich
Logdeterminante und deterministischer Gleichstandsregel. Kein Refit,
Jitter, Clipping, Pseudoinverse oder Ersatz durch die wahre Kovarianz.
Kontrollfenster, Messdaten, Residuen und Signalwahrheit bestimmen Alpha nicht.

## Zufallsquellen, vollständige Seeds und Reihenfolge

Jeder Block erhält neue Messrausch- und Hintergrundwurzeln sowie vier neue
Suchseeds. Innerhalb des Blocks werden dieselben Beobachtungen und derselbe
Viererseedblock zwischen den drei Armen gepaart. Jeder Suchaufruf bleibt ein
frischer Prozess. Zwischen Rauschmodellen und Blöcken werden weder Innovationen
noch Hintergrundfenster geteilt. Unterschiede der Modelle sind daher kein
gepaarter Vergleich desselben Rauschvektors.

PCG64 für Messrauschen und Hintergrund; Hintergrundrollen mit dem bestehenden
`seedsequence_role_v1`, Rollenkennungen train=0, validation=1, check=2,
`pool_size=4`. Vollständige Anfangs-/Endzustände und konkrete Arrays speichern;
auch tatsächlich gleiche Anfangszustände ausschließen. Verschiedene Seedzahlen
allein sind kein empirischer Unabhängigkeitsnachweis [4].

Die folgende Tabelle ist vor Suchausführung erzeugt. Seedgenerator PCG64,
Wurzel `2026111409`, `integers(1,2**31)`; Reihenfolge Block aufsteigend, je
Block white dann ar1, je Zeile Messrauschen, Hintergrund, vier Suchseeds.
Alle 72 Zahlen sind verschieden. Ausgeschlossen wurden 1.766 positive
31-Bit-Dezimaltokens aus UTF-8-Dateien unter data/docs/src/scripts/tests am
Bezugscommit `4e1fa18461b2b32fc2f8c39e77fd7c51b06c868a`, gefunden durch
`(?<![A-Za-z0-9_])\d+(?![A-Za-z0-9_])`. Die aufsteigend sortierte,
zeilenweise dezimale Ausschlussliste einschließlich letzter LF hat SHA-256
`a6a653c98dd9fedf63626e30f57c148685952eefaa7062795d6cffa74c05021a`.
Generator- und Rasterseed sind ebenfalls neu und für die Tabelle gesperrt.

| Block | Modell | Messrauschen | Hintergrund | Vier Suchseeds |
| ---: | --- | ---: | ---: | --- |
| 1 | white | 566695175 | 415413690 | 1734708527, 1539770707, 1622328068, 1225308221 |
| 1 | ar1 | 495067099 | 1676223713 | 1494771928, 1678574396, 2096825714, 1211174835 |
| 2 | white | 1566182586 | 809849776 | 596152422, 614436374, 1180778442, 1006610954 |
| 2 | ar1 | 1777518894 | 1064722274 | 486821846, 99725564, 814485586, 575382670 |
| 3 | white | 796396672 | 2142819059 | 1618513868, 674176212, 552276091, 1316430785 |
| 3 | ar1 | 522170952 | 878189361 | 1459026218, 1799747039, 521508560, 716632464 |
| 4 | white | 541435809 | 2074815860 | 1886273123, 2057732517, 1527388407, 569076422 |
| 4 | ar1 | 1101297837 | 576312512 | 62189220, 883512557, 1060488681, 848276631 |
| 5 | white | 1972424494 | 232958399 | 512201544, 377696954, 1835826724, 670096281 |
| 5 | ar1 | 630298913 | 490261955 | 750060073, 1366925241, 1786922412, 652748693 |
| 6 | white | 714889379 | 2129723798 | 314569512, 604072557, 732549740, 515882677 |
| 6 | ar1 | 197369405 | 1481384320 | 1719232956, 1051201175, 1449253553, 459990396 |

Ausführungsreihenfolge: Block 1–6, bei ungeraden Blöcken white vor ar1,
bei geraden ar1 vor white. Je Fall bleibt die vorhandene Armreihenfolge
ordinary, known_covariance, estimated_covariance; Mitglieder 1–4. Die feste
Armposition ist eine Grenze von Laufzeitvergleichen. Kosten sind deskriptiv;
keine zusätzliche Orchestratorvariante allein für eine balancierte Reihenfolge.
Alle Fälle werden vorab geplant; keine Änderung wegen Zwischenresultaten.

## Suchprofil, Auswahl und Ausfälle

Unverändert `r4x1000-local300x5-v1`: vier neue Suchen je Arm, je 1.000 äußere
Iterationen; 300 lokale Optimiereriterationen und fünf zusätzliche lokale
Neustarts. Beide Häufigkeitsschalter an, ursprüngliches t, allgemeine Grammatik,
`should_simplify=false` und alle übrigen geprüften Optionen aus PR89.
Ein gemeinsamer sauberer Ausführungscommit und dieselbe numerische Umgebung
gelten für alle Abschnitte: Python 3.12.14, Julia 1.13.1, PySR 2.6.0,
SymbolicRegression 2.5.1, Haswell-BLAS, eine CPU, Julia-/GC-/BLAS-Threads wie
im bestätigten Profil. Tatsächliche Workerbelege bleiben zwingend.

Die feste volle Matrix wirkt auf Struktursuche und Konstantenoptimierung.
Jedes Paket wählt eine unveränderte Originalausgabe nach endlichem nativem
Trainingsverlust, Komplexität und Mitgliedsposition. Keine Auswahl zwischen
verschiedenen Verlustskalen. Sauberes Signal, Klasse, Strukturprüfung,
klassische Referenzfits und Zusatzraster dürfen weder Auswahl noch Abbruch
beeinflussen. Vorhandene klassische Fits sind nur getrennte Kontrollen.

Alle vier Mitglieder und sämtliche bekannten Kosten bleiben im Paket, auch
bei zulässigen numerischen Fehlern oder Timeouts. Ohne endliche zulässige
Originalausgabe hat das Paket einen Ausfall und keinen Signalfehlerwert.
Nicht endliche Diagnosewerte werden mit Grund als fehlend ausgegeben,
nicht als null und nicht durch Entfernen des Falls ersetzt. Herkunftsfehler,
Aufrufwächter, Unterbrechungen, unbekannte Fehler und späte Quellenänderungen
sperren den Gesamtabschluss. Ein Integritätsabbruch ist kein normaler Ausfall.

Kovarianz-/Datenvorbereitungsfehler und gegebenenfalls nicht ausgeführte Arme
bleiben im geplanten Nenner mit Grund und Teilkosten. Bei gültigen gemeinsamen
Daten und Gewichtungsmatrizen werden alle drei SR-Arme auch bei einem zulässigen
numerischen Ausfall eines rein diagnostischen klassischen Referenzfits
ausgeführt; dessen Ausfall wird separat berichtet. Scheitert ausschließlich
die geschätzte Kovarianz numerisch, erhält dieser Arm vier `not_run`-Mitglieder
und einen Paketausfall; gewöhnlicher und bekannter Arm bleiben ausführbar.
Fehlen gültige gemeinsame Beobachtungsdaten, werden alle betroffenen Mitglieder
als `not_run` geführt. Integritätsfehler sperren weiterhin die gesamte Serie.
Diese Regeln müssen in der Serienanbindung ausdrücklich implementiert werden;
der heutige allgemeine Referenzschritt stoppt bereits bei Referenzstatus ungleich
`success` und unterscheidet diese Fälle noch nicht für den Serienauftrag.

## Vorab gespeicherte Diagnosepunkte und Endpunkte

Neben den Trainingspunkten werden die bisherigen 889 regulären Zwischenpunkte
und **1.024 neue unregelmäßige Punkte** auf demselben geschlossenen Intervall
vorab gespeichert. Je ein Punkt pro gleich breitem offenen Stratum, eigener
PCG64-Seed `2026111410`; exakte Treffer auf dem gemeinsamen regelmäßigen
1/32768-Sekunden-Raster ablehnen, maximal 100 Ziehungen pro Stratum. Scheitert
die Erzeugung, vor der Suche abbrechen. Derselbe Rastervektor gilt für alle
Blöcke und Arme. RNG und Werte sind vom Suchzufall getrennt.

**Primärmaß:** amplitudennormierter RMSE zur sauberen Wahrheit an den
128 Trainingszeiten, `E_A=sqrt(mean((prediction-signal)**2))/abs(A)`.
Dies ist Rekonstruktionsfehler nach Anpassung desselben Beobachtungsfensters,
keine unabhängige Generalisierungsbewertung. Der Nenner ist die feste
generierende Amplitude, keine nachträglich geschätzte Normierung.

Primärer Kontrast bei verfügbaren Fehlerwerten beider betroffener Arme:
`Delta=E_A(estimated_covariance)-E_A(ordinary)`; negative Werte bedeuten dort
kleineren Fehler mit geschätzter Gewichtung. Sekundär dieselben Differenzen
für known gegen ordinary sowie estimated gegen known. Kein gemeinsamer
Trainingsverlustvergleich der Arme. Ein Ausfall des jeweils dritten Arms
entfernt eine vorhandene Paarung nicht; alle Ausfallnenner bleiben separat erhalten.

Weitere vorab bestimmte Diagnosen:

- RMSE und Maximalfehler geteilt durch A auf Zwischen- und unregelmäßigem
  Raster; kontinuierlich, ohne neue Bestehensschwelle. Diese Punkte reduzieren
  Rasterblindstellen, beweisen weder Domain-Gültigkeit noch allgemeine Identifizierbarkeit.
- Gemeinsame MSE zum verrauschten Beobachtungsvektor und `Q_true/N`, ausschließlich
  nach Auswahl. Keine Chi-Quadrat-Freiheitsgrad- oder Konfidenzbehauptung für
  die frei ausgewählten SR-Modelle.
- Unveränderte A–D-Einordnung und bestehende Originalfamilien-/Domain-/Restterm-
  Verträge für die 36 ausgewählten Originalausgaben, soweit jeweils anwendbar.
  Ungeklärte Nachweise bleiben ungeklärt; keine Nachbearbeitung oder neue
  Erkennerentwicklung für günstigere Zahlen. Die Klassen sind beschreibend,
  keine Rauschpilot-Erfolgsgrenze.
- Physikalische Parameterübereinstimmung bleibt **`not_assessed`**. Der
  Familiennachweis ersetzt keine neue Parameterregel. Klassische bekannte
  Ringdown-Referenzfits werden getrennt ausgewiesen.
- Hintergrund-Kontrollscore, Alpha, Matrixabweichung zur bekannten Kovarianz,
  Konditionierung, Ausfälle, Laufzeiten und Verlustcallbacks.

Je Rauschmodell alle sechs Einzelwerte und gepaarten Differenzen, dazu
Anzahl verfügbar/geplant, Mittelwert, Median, Min/Max und Stichproben-SD
berichten. Ausfallanteile verwenden stets sechs geplante Pakete je Arm.
Bei vollständigen sechs Paaren kann `SD(Delta)/sqrt(6)` als geschätzter
Monte-Carlo-Standardfehler ergänzt werden, ausdrücklich unsicher bei kleinem n.
Bei fehlenden Paaren keine solche Präzisionsangabe für den vollständigen
Verfahrensvergleich; verfügbare Differenzen nur mit ihrem bedingten Nenner.
Keine Poolung über die beiden Rauschmodelle, kein Bootstrap-/p-Wert als
Freigabekriterium und keine automatische Wahl des vermeintlich besten Arms [1].

## Rechenkosten und technischer Vorlauf

Die historische rauschfreie Bestätigung benötigte für 120 ungewichtete
1.000er-Worker 33.331,876 s, im Mittel 277,766 s. Rein arithmetisch entsprechen
72/144/288 solchen Aufrufen 5,56/11,11/22,22 Stunden Workeraufwand.
**Dies ist keine Laufzeitprognose für den Rauschpilot.** Zwei Drittel seiner
Arme verwenden volle Kovarianzen; deren Dreieckslösung pro Callback und
Vorbereitung, Diagnosen und Verifikation erzeugen zusätzliche Kosten.
Der bestätigte neue Manjaro-Vorlauf mit zwei Datenpunkten und einer äußeren
Iteration liefert keinen Nachweis für 128 Punkte und 1.000 Iterationen.

Vor einer wissenschaftlichen Serie ist deshalb ein separat gespeicherter
technischer N=128-Vorlauf erforderlich: dieselbe Signal-/Samplingdefinition,
AR(1), derselbe Pegel und Hintergrundumfang, aber eigene technische Seeds,
drei einzelne Worker mit je **zehn äußeren Iterationen**, lokal unverändert
300/5. Er prüft Datenfluss, vollständige Kovarianz, Replay und Ressourcen;
Kurvenklasse, Familie und Signalfehler sind keine Abnahmekriterien und werden
nicht zur Auswahl des wissenschaftlichen Plans verwendet. Technische Wurzeln:
Messrauschen `2026111411`, Hintergrund `2026111412`, Suchseed `2026111413`
gemeinsam in den drei getrennten Workern. Diese Werte sind außerhalb der
historischen Ausschlussliste und der wissenschaftlichen Tabelle; konkrete
Eingaben und Zustände werden vor dem Vorlauf gebunden. Keine Hochrechnung als garantierte
1.000er-Laufzeit, da JIT und Suchkosten nicht linear sein müssen.

Aktuelle Betriebsfristen bleiben zunächst 1.800 s je wissenschaftlichem Worker,
7.800 s je Paket und 25.200 s je Dreiervergleich. Der technische Vorlauf erhält
höchstens 600 s je Worker und eine eigene vollständige Aufrufmessung.
Sollten Fristen nach dessen Ressourcenbefund geändert werden müssen, geschieht
dies mit begründetem dokumentiertem Beschluss **vor** der wissenschaftlichen
Ausführung; keine nachträgliche Rettung bestimmter wissenschaftlicher Fälle.

Aufzeichnen: vollständige Wall-/CPU-Zeit jedes Abschnitts einschließlich
Vorbereitung und Abschluss, Member-/Fitzeiten, Verlustcallbacks und getrennte
lesende Prüfkosten. Unbekannte Kosten bleiben unbekannt. Enthaltene Zeiten
nicht nochmals addieren; Einrichtung und technische Vorläufe separat ausweisen.

## Anschlussregel und Startvoraussetzungen

1. Fehlende Integrität oder unvollständige Bindung: kein freigegebener
   Gesamtbefund; Ursache klären, Originale und Teilkosten erhalten.
2. Belegte numerische Ausfälle, Timeouts oder nicht auswertbare Originalausgaben:
   vollständig berichten und vor einer Vergrößerung gezielt diagnostizieren.
   Keine automatischen Ersatzseeds, Wiederholungen oder Budgetänderungen.
3. Bei vollständig auswertbarem Pilot: alle Verteilungen und Kosten bilden
   die Grundlage eines **gesonderten** Hauptstudienplans zu Hintergrundmenge
   und Gewichtung. Relevante Effektgröße, gewünschte Präzision und neue
   unabhängige Fälle werden dort vorab festgelegt. Ein fehlender Vorteil der
   geschätzten Gewichtung ist ein wissenschaftlich zulässiger Befund.

Weder positiver Pilot noch die sechs Wiederholungen geben automatisch die
Hauptstudie frei. Es folgt keine neue Suchbudget-, Grammatik- oder
Zeitkoordinatenoptimierung. Die frühere Bestätigung und ihre Grenzen bleiben bestehen.

**Noch nicht implementiert:** Der allgemeine Schema-4-Laufweg kann einzelne
Dreiervergleiche ausführen und lesend prüfen. Seine bisherige Auswertung gilt
nur für Trainingssamples; der bestehende Zusatzbewertungsimport akzeptiert
Schema 3. Die Anbindung des Zusatzrasters und der bestehenden Bewertungsverträge
an Schema 4, gemeinsame Vorbereitung aller zwölf Fälle, Bindung der Teilabschnitte,
vollständige Aufrufmessung und Serienabschluss fehlen noch. Kein bloßes Ausführen
der Beispiel-TOML ersetzt diese Arbeiten.

Auch der technische Zehn-Iterationen-Vorlauf ist ein erst noch getrennt zu
bindender und zu versionierender Modus: Der heutige technische PR89-Worker
akzeptiert genau eine äußere Iteration, der wissenschaftliche genau 1.000.
Die bestehenden Ein-Iterations-Prüfungen und ihre Archivformate bleiben
unverändert; kein bestehender Aufruf wird stillschweigend umgedeutet.

Vor dem ersten wissenschaftlichen Suchaufruf müssen vorliegen:

- der beschlossene Umfang und sein getrennt versionierter endgültiger Protokollcommit;
- konkrete vollständige Eingaben, Hintergrundmatrizen, ausgewählte Kovarianzen,
  Referenzwerte und Raster mit SHA-256, soweit erzeugbar; andernfalls vorab
  gebundene zulässige Vorbereitungsfehler samt betroffenen `not_run`-Armen.
  Quellen-/Versionsbindung gilt auch für diese Ausfälle;
- geprüfter Implementierungs-PR einschließlich Fehler-/Abbruchgrenzen und
  separatem lesendem Serienverifikator, vollständige erforderliche CI;
- erfolgreicher begrenzter technischer Manjaro-Vorlauf auf dem Ausführungsstand;
- konkreter Manjaro-Laufauftrag mit neuen IDs, Befehlen, erwarteten Artefakten
  sowie lesender Verifikation und anschließender Archivierung.

Die wissenschaftlichen Daten dürfen vorab deterministisch erzeugt und auf
ihre Bindung geprüft werden. Es gibt dabei keine freien Suchen oder Fits zur
Auswahl günstiger Signale, Seeds oder Kovarianzen. Originalarchive unverändert
gemäß [Archivregel](results_archiving.md) erhalten; Ablage und unabhängige
hashgeprüfte Zweitkopie im bestehenden [Ergebnisindex](results_index.md) führen.
Ein Plan und eine bereitgestellte Arbeitskopie belegen keine ausgeführte Serie
oder abgeschlossene Sicherung.

## Literaturbezug und Grenzen

Am 14.11.2026 für diesen Entwurf erneut inhaltlich geprüft. Die Quellen
begründen Bausteine; konkrete Signale, sechs Blöcke, Pegel und Datenmengen
sind ausdrücklich begrenzte Projektentscheidungen.

1. Morris, White und Crowther (2019), *Using simulation studies to evaluate
   statistical methods*, [DOI 10.1002/sim.8086](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/).
   ADEMP, gepaarte Vergleiche, Monte-Carlo-Unsicherheit und transparente
   Ausfälle. Keine universelle Mindestzahl von Wiederholungen.
2. La Cava et al. (2021), *Contemporary Symbolic Regression Methods and their
   Relative Performance*, [Volltext](https://pmc.ncbi.nlm.nih.gov/articles/PMC11074949/).
   Numerische Genauigkeit und symbolische Wiederfindung trennen; Appendix A.4
   definiert Rauschpegel relativ zum RMS des Signals. Zufällige Datenaufteilung
   und nachträgliche Simplifizierung werden hier nicht übernommen.
3. Ledoit und Wolf (2004), *A well-conditioned estimator for large-dimensional
   covariance matrices*, DOI 10.1016/S0047-259X(03)00096-4,
   [Originalarbeit](https://perso.ens-lyon.fr/patrick.flandrin/LedoitWolf_JMA2004.pdf).
   Dimension, Zahl unabhängiger Vektoren und Schrumpfung; keine Optimalitätsgarantie
   unserer Holdout-Alpha-Auswahl oder der Mengen 64/128/256.
4. NumPy, [Parallel random number generation](https://numpy.org/doc/stable/reference/random/parallel.html).
   Dokumentierte Ableitung getrennter RNG-Zustände; keine Garantie allgemeiner
   statistischer Unabhängigkeit oder geräteübergreifender Float64-Identität.
5. Imai Aldeia et al. (2025), *Call for Action: Towards the Next Generation of
   Symbolic Regression Benchmark*, [arXiv:2505.03977v1](https://arxiv.org/html/2505.03977v1).
   Feste Seeds, Ressourcenberichte und begrenzte Konfigurationsentwicklung.
   Die dortigen 30 Wiederholungen und Aggregationsregeln sind keine Vorgabe
   für diesen Pilot und ersetzen unsere ursprüngliche Paketwahl nicht.
