# Folgestudie Manjaro 001: Hintergrunddauer und Messraster

Auswertung vom 22.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md).
Grundlage ist das gelieferte **Übersichtspaket**, nicht das vollständige
Originalarchiv. Die berichteten 624 neuen Suchaufrufe liefern 156 erfolgreiche
Paketausgaben auf 26 gemeinsamen Fällen. Alle vorgesehenen Endpunkte sind
vorhanden. Die eigene Berichts-, Zahlen-, Matrix- und ausgewählte Baumprüfung
wird unten von der noch ausstehenden vollständigen Herkunftsprüfung getrennt.
Es wurden keine Fits oder symbolischen Suchen gestartet und keine Originalwahl
verändert. Der [eingefrorene Plan](noise_followup_plan.md) bleibt unverändert.

## Ergebnis und Bedeutung

**4096 Sekunden Hintergrund liefern hier keinen belegten Vorteil für die
ausgewählte Formel gegenüber 64 Sekunden.** Unter AR(1) steigt der mittlere
primäre RMSE von 2,558 auf 2,782 % der Signalamplitude. Das approximative
marginale 95%-t-Intervall der gepaarten Differenz umfasst beide Richtungen.
Dies belegt weder Gleichwertigkeit noch eine allgemeine Wirkungslosigkeit
längerer Rauschaufnahmen.

**Das verschobene Messraster vermeidet in dieser Serie die beiden großen
Uniform-K-Fehler, ist aber kein allgemein überlegener Ersatz.** Der mittlere
AR(1)-Fehler mit bekannter Kovarianz fällt von 5,477 auf 2,542 %. Fast die
gesamte mittlere Differenz stammt aus zwei Fällen. Auch das zweite primäre
Intervall umfasst null. Die weißen Kontrollen und einzelne schmale Spitzen
sprechen zusätzlich gegen eine pauschale Jitterempfehlung.

Die frühere Trennung bleibt entscheidend: **genauere Rauschbeschreibung,
gute Suche auf den Messpunkten und eine brauchbare Formel zwischen den
Messpunkten sind verschiedene Ziele.** Mehr Hintergrunddauer allein löst
die bereits belegte Frequenzmehrdeutigkeit und empfindliche Ausdrucksformen
nicht. Der nächste Schritt sollte die konkrete Fehlerentstehung eingrenzen,
bevor eine weitere große Suchserie begonnen wird.

## Datenstand, Bindung und Grenzen der eigenen Prüfung

- Geliefert: `noise-followup-manjaro-001-overview.tar.gz`, 11.177.133 Bytes,
  SHA-256 `911bf9249783848b9ff9c0543c7419fd52e089f8c48190849a5f9eaef086a3f6`.
  Prüfsumme stimmt; 92 sichere reguläre Datei-/Verzeichniseinträge mit
  35.803.472 Nutzdateibytes, keine Links oder doppelten Pfade.
- In allen vier Berichten gebundener Ausführungscommit:
  `8a1a4a1437f4b01daf1f070b56add248074c5907`.
  PR #102 wurde als `0f5a29f78c06a4fcdc3dabd5ae7ced6143dff6c8` übernommen;
  der Merge ersetzt den tatsächlichen Ausführungscommit nicht.
- Vorabplancommit `a37bf90fe439619fd263d6c06d868c6ff4ea00e8`, Plan-SHA-256
  `f762ec7f4311ceea46bd736f3838c111072939d5d853552e3bec537ad86b2773`.
  Alle 192 Quellenhashes je Bericht passen zum Ausführungscheckout.
- Sechs Publikationsmanifeste mit insgesamt 66 referenzierten Dateiprüfungen
  bestehen. Serien- und Verifikationsexporte beider Blöcke sind bytegleich.
  Das bestätigt die gelieferten Dateien; die vollständige Verifikation wurde
  hier mangels Originaleingaben und aller Workerdateien nicht erneut ausgeführt.
- A: 104 neue Viererpakete/416 Suchaufrufe. B: 52 neue Viererpakete/208
  Suchaufrufe und 52 exakt identische, hashgebundene O/K-Kontrollpakete aus A.
  Insgesamt 156 neue Pakete; die 208 Assessmentzeilen beider Berichte sind
  keine 208 unabhängigen Ergebnisse. Alle 156 Pakete melden `success`.
  **Die Einzelstatus aller 624 Worker fehlen im Überblick.** Ein erfolgreiches
  Viererpaket schließt klassifizierte Ausfälle einzelner Mitglieder nicht aus.
- Sechs technische Memberrecords melden abgeschlossene N128-Zehnerworker.
  `workflow_state.json` meldet Abschluss am **22.11.2026 um 01:07:08 CET**.
- Eigene unabhängige Zahlenprüfung: 288 Zusammenfassungsfelder und sämtliche
  20 Modell-/Blockkontraste einschließlich Einzelpaardifferenzen, MCSE und
  t-Intervallen stimmen mit den Berichten überein.
- Ausgewählte Originalbäume und Formeltexte sind enthalten. Die eingefrorenen
  Zeitachsen und sauberen Referenzwerte lassen sich deterministisch herstellen
  und gegen ihre übermittelten Fingerprints prüfen. Daraus erzeugte neue
  Formelplots sind ein **Rekonstruktionsreplay ausgewählter Bäume**, keine
  Prüfung der fehlenden Originalplotdateien oder sämtlicher Suchkandidaten.
- Nicht geprüft sind bisher die Bytes der drei Originalarchive, alle
  wissenschaftlichen Rohinputs, sämtliche Worker-/Uhrennachweise, vollständige
  Kandidatenfronten und die ursprünglichen Auswahlentscheidungen. Die drei
  mitgelieferten Archivprüfsummentexte allein schließen diese Lücken nicht.
  Familien-, Parameter- und kontinuierliche Domainnachweise bleiben
  entsprechend dem Studienplan `not_assessed`.

Die aktuellen Berichte sind an SHA-256
`512ce565147daf0b774195677d649258897ec9144f3a8f3ef5fa86488f41e2a1` (A)
und `24429cf5ac1a30f8d49a568f157ad91a790d89e5ee29f78a2a22855a6be01628` (B)
gebunden. Detailnachweise heißen `audit_integrity.json`, `statistics.json`
und `white-scaling.json`; Skripte und vollständige Einzelwerte gehören zum
separaten Auswertungspaket. Originaldateien bleiben erhalten.

## Neue gebundene Darstellung der Originalformeln

Alle 156 Originalbäume und deren Baumhashes wurden aus den Berichten gelesen.
Die 128 uniformen bzw. 128 Jitterzeiten, 889 regulären Zwischenzeiten und
1024 unregelmäßigen Bewertungszeiten samt Wahrheit stimmen exakt mit allen
übermittelten Referenzfingerprints überein. Die nativen Trainingsvorhersagen
bleiben erhalten; die beiden Zusatzraster werden aus den unveränderten
Bäumen neu ausgewertet. **Alle 936 RMS-/Maximalwerte sind bitgenau gleich**
den übermittelten Werten. Die Exporte enthalten 318.396 Punktzeilen,
vollständige Originalformeltexte und Bäume sowie PNG/SVG für alle 156 Ausgaben.
Die fehlenden verrauschten Beobachtungen werden nicht erfunden oder ergänzt.

`plot-reconstruction-audit.json` hält diesen begrenzten Nachweis fest.
`groups-ar1`, `groups-white`, `primary-contrasts` und `selected-spikes` zeigen
sämtliche Gruppen bzw. ausdrücklich nachträglich ausgewählte Diagnosefälle;
jeweils als PNG/SVG/PDF mit zugeordneten CSV-Werten. Gruppenübersichten
verwenden beschriftete logarithmische y-Achsen, damit kleine Werte und große
Spitzen gemeinsam sichtbar bleiben. `gallery/index.html` verknüpft alle
Originalausgaben; die 967 lokalen Galerielinks wurden geprüft. Die Übersichten
und ausgewählte Einzelplots sind visuell geprüft, keine Aussage über jedes
Pixel aller Einzelbilder. Endliche Punktraster sind kein kontinuierlicher
Domainnachweis. Die 52 gemeinsamen Kontrollen erscheinen nicht als neue Fälle.

## Vorab festgelegtes Maß und alle Bedingungen

Primärmaß ist RMSE zur sauberen Wahrheit, geteilt durch die Amplitude A,
auf 1024 vorab gebundenen unregelmäßigen Zeiten. In den folgenden Tabellen
steht `100 * RMSE/A`, also Prozent der Amplitude; Differenzen stehen in
**Prozentpunkten**. Die 889 regulären Zwischenpunkte und die 128 Messpunkte
bleiben sekundäre Diagnosen. Es wird kein großes Ergebnis entfernt.

Alle Arme verwenden dasselbe bekannte Entwicklungssignal `confirm_mid`,
N128, ungefähr 265 Hz, Dämpfungszeit 1/150 s, Rauschpegel sigma/A=0,05
und das unveränderte Profil R4×1000 bei lokal 300/5. O bedeutet gewöhnliche
MSE, K wahre bekannte Kovarianz, E64s/E4096s volle Matrixschätzung aus
zusammenhängendem Hintergrund. Jitter verwendet tatsächlich andere Messzeiten
und Messwerte, mit der vorab festgelegten kontinuierlichen Rauschfortsetzung.
Es verändert auch die Korrelation; ein Unterschied ist kein isolierter
Nachweis ausschließlich eines Geometrieeffekts.

| Bedingung | AR(1), Mittel / Median / größter Fall-RMSE (%) | White, Mittel / Median / größter Fall-RMSE (%) |
| --- | ---: | ---: |
| Uniform O | 2,802 / 2,808 / 4,945 | 1,354 / 1,409 / 1,577 |
| Uniform K | 5,477 / 2,432 / 32,468 | 7,123 / 1,467 / 32,250 |
| Uniform E64s | 2,558 / 2,461 / 3,815 | 1,417 / 1,416 / 1,955 |
| Uniform E4096s | 2,782 / 2,792 / 4,427 | 6,642 / 1,417 / 32,868 |
| Jitter O | 2,628 / 2,756 / 3,481 | 1,928 / 1,918 / 2,409 |
| Jitter K | 2,542 / 2,519 / 3,763 | 1,593 / 1,515 / 1,992 |

Nenner je Bedingung: AR(1) 20/20, White 6/6. Der größte Fall-RMSE ist
nicht der größte punktweise Fehler; wichtige Punktspitzen folgen unten.
Der Vergleich von Armen erfolgt auf gepaarten Fällen, nicht als ungepaarter
Vergleich dieser Mittelwerte. Keine Zusammenfassung von AR(1) und White zu
einer vermeintlichen gemeinsamen Erfolgsquote.

| Primärer AR(1)-Kontrast | Mittlere Differenz (pp) | MCSE (pp) | Approx. marginales 95%-t-Intervall (pp) | Kleinere Fehler |
| --- | ---: | ---: | --- | ---: |
| E4096s minus E64s | +0,22428 | 0,13035 | [−0,04855; +0,49710] | 8/20 |
| Jitter K minus Uniform K | −2,93505 | 2,02820 | [−7,18011; +1,31002] | 12/20 |

Negative Differenzen bedeuten Verbesserung. Es sind zwei vorab benannte
Hauptfragen, keine simultan kontrollierten Intervalle. Starke Schiefe,
einzelne große Fehler und kleine Fallzahlen begrenzen die t-Näherung.
Insbesondere ist ein Intervall über null kein Gleichwertigkeitsnachweis.

## Was die Mittelwerte verdecken

Bei `ar1-12/K` sinkt der Fall-RMSE von 32,468 % auf 2,611 % unter Jitter K;
bei `ar1-14/K` von 31,740 % auf 2,811 %. Die Summe ihrer beiden gepaarten
Differenzen beträgt −58,78545 pp, die Summe aller 20 Paare −58,70096 pp.
Der Median der Paardifferenzen beträgt dagegen nur −0,12438 pp.
Eine ausdrücklich nachträgliche Einflussdiagnose der übrigen 18 Paare
ergäbe +0,00469 pp. **Die Primäranalyse bleibt bei allen 20 Paaren.** Dies
ist keine neue Ausschlussregel und kein nachträglich anderer Hauptendpunkt.

Die beiden Uniform-K-Formeln haben auf den Messpunkten nur etwa 2,31 bzw.
2,49 % RMSE, auf beiden Zusatzrastern aber ungefähr 32 %. Dieser Abstand
ist mit der bisherigen Informations-/Auswahlproblematik vereinbar.
Konkrete affine trigonometrische Komponenten der Originalbäume liefern:

| Originalausgabe | Betrag der Komponentenfrequenz (Hz) | Auf dem Uniformraster gefaltete Frequenz (Hz) |
| --- | ---: | ---: |
| ar1-12 / K | 12.551,588359 | 263,588359 |
| white-05 / K | 3.831,276442 | 264,723558 |
| white-05 / E4096s | 7.927,309853 | 264,690147 |

Dies betrifft exakt affine Phasenteilbäume und ihre Rastermehrdeutigkeit,
nicht die Identität des gesamten verschachtelten Ausdrucks mit einem reinen
265-Hz-Ringdown. Die Originalformeln werden weder gefaltet noch ersetzt.
`ar1-14/K` besitzt eine nichtaffine Phase; hier wird keine einzelne konstante
Frequenz behauptet.

Auch die Jitterbedingung ist nicht durchgehend unproblematisch:
`white-02/Jitter-O` erreicht auf dem unregelmäßigen Raster **42,50 %**
punktweisen Fehler, auf dem regulären Zwischenraster nur 8,61 %.
Die zugehörigen RMSE betragen 2,409 bzw. 1,944 %. Bei
`ar1-03/E4096s` liegt der unregelmäßige Spitzenfehler bei **84,02 %**,
obwohl der Fall-RMSE nur ungefähr 3,34 % beträgt. Verschachtelte
Sinus-/Divisionsstrukturen bleiben damit ein eigener Diagnosegegenstand.
Endliche Raster schließen weitere, noch schmalere Spitzen nicht aus.

Sekundär wird White/Jitter-O in 6/6 Paaren schlechter als Uniform-O:
mittlere Differenz +0,57334 pp, marginales Intervall [+0,26975; +0,87693] pp.
Die kleine Entwicklungsstichprobe und fehlende simultane Kontrolle bleiben
zu beachten. Sie begründet jedenfalls keine universelle Jitterempfehlung.

## Schätzerdiagnose: besseres K ist noch keine bessere SR-Formel

Alle 48 enthaltenen Schätzerdateien sind hashgeprüft und **bytegleich zur
bereits dokumentierten Cloud-Diagnose 002**. Die Manjaro-Ausführung wiederholt
dieselben acht AR(1)- und vier weißen Entwicklungsfälle. Sie ist keine neue
unabhängige Stichprobe und kein Nachweis der Matrixfehler sämtlicher 26
wissenschaftlichen Fälle, deren Eingabedateien im Übersichtspaket fehlen.

| Modell / Schätzer | Mittlerer relativer Frobeniusfehler, 64 s (%) | 4096 s (%) |
| --- | ---: | ---: |
| AR(1), volle Matrix | 15,6101 | 2,0141 |
| AR(1), Welch/Toeplitz | 2,3742 | 0,2771 |
| White, volle Matrix | 0,1805 | 0,7861 |
| White, Welch/Toeplitz | 0,6919 | 0,2046 |

Schrumpfformel, Eigenwerte, Kondition und Matrixfehler wurden unabhängig
nachgerechnet; bei Welch zusätzlich PSD→ACF→Toeplitz. Alpha entspricht
jeweils dem Minimum der gespeicherten zulässigen Scores. Deren quadratische
Bestandteile können ohne Holdout-/Kontrollfenster nicht vollständig neu
berechnet werden. Welch ist in dieser Serie **kein SR-Arm**.

White erklärt die scheinbare Umkehr bei voller Matrix: Der rohe Matrixfehler
sinkt in allen vier Fällen von ungefähr 25,3 auf 3,13 %. Bei 64 s wählt die
Holdout-Regel jedoch immer alpha=1, bei 4096 s zweimal alpha=0,5. Die schlechtere
ausgewählte Schätzung betrifft hier die feste Schrumpfungswahl, nicht allgemein
den Wert längerer Rauschaufnahmen.

Eine zusätzliche billige Kontrollrechnung betrifft White-K: Für einen festen
Kandidaten gilt bei C=sigma² I genau `L_K = MSE / sigma²`. An allen zwölf
gewählten Uniform-/Jitter-K-Ausgaben stimmen berichteter nativer Verlust und
skalierte MSE bis maximal 3,84×10⁻¹⁶ relativ überein; die MSE aus den
übermittelten Residuen weicht höchstens 8,68×10⁻¹⁹ absolut ab. Der Faktor
beträgt 476,03305785123956. **Kein Rechenwiderspruch ist damit sichtbar.**
Gleiche mathematische Kandidatenrangfolge garantiert jedoch keine identischen
endlichen heuristischen Suchverläufe. Deren unterschiedliche Ausgaben
begründen eine separate kleine Skalierungs-/Optimierungskontrolle.

## Tatsächlich belegte Kosten

| Umfang | Gemessene Wandzeit |
| --- | ---: |
| Gesamter Serienaufruf A | 131.848,425 s = 36 h 37 min 28 s |
| Gesamter Serienaufruf B | 60.861,577 s = 16 h 54 min 22 s |
| Beide Serienaufrufe | **192.710,002 s = 53 h 31 min 50 s** |
| Gemeinsame wissenschaftliche Inputvorbereitung | 31,753 s |
| Zusätzlicher Plotaufruf A | 660,175 s |
| Zusätzlicher Plotaufruf B | 943,478 s |
| Technischer Plotaufruf | 8,902 s |

Die Serien enthalten bereits Fall-, Worker- und Fitzeiten. Diese Ebenen
werden nicht addiert; die B-Kontrollen verursachen keine neuen Suchkosten.
Beide Serien-CPU-Messungen sind als vollständig markiert und numerisch mit
ihren enthaltenen Kosten konsistent. Aus diesem Upload unbekannt bleiben
die vollständigen technischen und Schätzeraufrufkosten
(`technical/technical_call.json`, `estimators/call.json` fehlen), separate
Verifikations-/Archivzeiten und eine vollständige Gesamtskriptmessung.
Der Zeitstempel des Abschlussstatus ersetzt diese Messungen nicht.

## Einordnung in bisherige Arbeit und Literatur

Die [Hintergrundserie 002](noise_background_results_manjaro_002.md) zeigte
bereits genauere AR(1)-Matrizen ohne entsprechenden mittleren SR-Vorteil.
Die [Kandidatenprüfung](noise_background_candidates_manjaro_002.md) fand
bessere Zwischenpunktkurven unter gespeicherten Alternativen, während der
[vorab festgelegte pooled-best-Vergleich](noise_background_selector_pilot_001.md)
den mittleren Fehler in allen zehn Gruppen erhöhte. Die
[Aliasdiagnose](noise_background_alias_diagnostic_001.md) belegte danach
konkrete Mehrdeutigkeiten des regelmäßigen Rasters. Die neue Studie ergänzt
diese Kette um frische Fälle, eine tatsächliche Daueränderung und echte
Jittermessungen. Sie rechtfertigt keine Rückkehr zur unverändert negativen
`best`-Regel und keine automatische Gewinnerwahl.

1. **Wang und Shao (2024), Phys. Rev. D 109, 043027:**
   [Originalmanuskript](https://link.aps.org/accepted/10.1103/PhysRevD.109.043027).
   Der Literaturvergleich betrifft 64 und **4092 s** aus einer 4096-s-Aufnahme,
   ACF-/PSD-Verfahren und GW190521-artige Daten. Der reine Dauereffekt auf
   die berichtete SNR ist ungefähr 5 %; die Bayes-Parametervergleiche verwenden
   dagegen alle 4092 s. Daraus folgt kein belegter isolierter Parameter- oder
   freier SR-Gewinn durch die längere Aufnahme. Unsere volle Matrix,
   stationäre Synthetik und freie Ausdruckssuche sind andere Bedingungen.
2. **Welch (1967):**
   [Originalpublikationsseite und Abstract](https://research.ibm.com/publications/the-use-of-fast-fourier-transform-for-the-estimation-of-power-spectra-a-method-based-on-time-averaging-over-short-modified-periodograms).
   Gemittelte modifizierte Periodogramme motivieren die strukturierte
   PSD-/ACF-Schätzung. Dies garantiert weder die Biasfreiheit unserer konkreten
   endlichen ACF noch bessere symbolische Ausgaben.
3. **VanderPlas (2018), Understanding the Lomb–Scargle Periodogram:**
   [Originalmanuskript](https://arxiv.org/pdf/1703.09824).
   Ungleichmäßige Abtastung verändert das Spektralfenster; sie garantiert
   keine allgemeine Aliasfreiheit. Ein Holdout nur auf demselben uniformen
   Raster bricht die exakte Raster-Aliassymmetrie ebenfalls nicht.
4. **Cranmer (2023), Interpretable Machine Learning for Science with PySR:**
   [Originalmanuskript](https://arxiv.org/html/2305.01582v3).
   Evolution, lokale Konstantenoptimierung, Paretofront und endgültige Auswahl
   sind getrennte Bestandteile. Struktur-/Verschachtelungsbeschränkungen sind
   mögliche Interventionen; eine für unsere Daten passende Regel folgt daraus
   noch nicht. Eine konkrete Ursache der Skalierungsabhängigkeit muss an
   unseren gebundenen effektiven Optionen untersucht werden.
5. **Siegel, Isi und Farr (2025), Analyzing black-hole ringdowns II: data conditioning:**
   [Originalmanuskript](https://arxiv.org/html/2410.02704v2).
   Filterung, Downsampling und Signalfenster müssen konsistent auf Daten,
   Modell und Kovarianz bezogen werden. Die dort diskutierte Länge des
   analysierten **Signals** ist von unserer **Rauschhintergrunddauer** zu
   unterscheiden; schmale Detektorlinien fehlen in unserer glatten AR(1)-Synthetik.
6. **Morris, White und Crowther (2019), Using simulation studies to evaluate statistical methods:**
   [Originalartikel](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/).
   Ziele, Datengenerierung, Zielgrößen, Methoden und Leistungsmaße vorab trennen
   und Monte-Carlo-Unsicherheit berichten. Dies stützt eine nächste Fallzahlplanung
   anhand eines vorab gewünschten Präzisionsziels statt weiterer Rechenzeit allein.

## Priorisierte nächste Schritte — Vorschläge, keine neuen Laufaufträge

1. **Originalnachweise vervollständigen und Fehlermechanismen gezielt prüfen.**
   Die drei unveränderten Archive `shared`, `duration`, `sampling` nachreichen
   oder einen geeigneten Übertragungsweg anhand ihrer Größen wählen. Danach
   alle Worker-/Kandidatenbindungen und die Originalauswahl lesend prüfen.
   Die jetzt mögliche Originalbaumgalerie dient zur Eingrenzung; bei auffälligen
   Paketen zusätzlich vorhandene Kandidatenfronten untersuchen. Messziel:
   Suchbestand, Selektor und Ausdrucksmehrdeutigkeit voneinander unterscheiden.
2. **Vor der nächsten Großserie eine kleine White-Skalierungskontrolle planen.**
   Die feste Kandidatenrechnung oben ist bereits bestanden. Ein gesonderter
   technischer Pilot könnte auf identischen Daten/Seeds gewöhnliche MSE,
   analytisch skalierte MSE und den entsprechenden Kovarianzpfad vergleichen.
   Effektive Normierung, Optimierung und Stopps mitprotokollieren. Zuerst eine
   mögliche Abweichungsstelle belegen, nicht vorab einen Backendfehler behaupten.
3. **Danach genau eine begründete Intervention für brauchbarere Formeln testen.**
   Bei bestätigtem Aliasproblem physikalisch begründete Träger-/Strukturgrenzen
   oder zusätzliche echte Messinformation prüfen; bei empfindlichen Nennern
   eine gezielte Domain-/Strukturbegrenzung. Keine Schranke anhand der bekannten
   265-Hz-Wahrheit optimieren. Ein vollständig vorgegebenes Ringdowntemplate
   wäre ein engerer Bekannte-Familie-Fit und entsprechend anders zu bewerten.
   Auswahlregel, Grammatik, Gewichtung und Messraster nicht gleichzeitig ändern.
4. **Welch/Toeplitz als nachrangige, getrennte SR-Frage behandeln.**
   Die Matrixdiagnose ist günstig, die Übertragung auf Formeln aber ungeprüft.
   Bei begründetem Interesse ein eigener kleiner Vergleich bei gleicher
   Hintergrunddauer, gleicher Geometrie und gleichem Suchbudget; keine erneute
   große 64/4096-s-Serie allein in Erwartung automatisch besserer Formeln.
5. **Eine ausgewählte Methode erst auf neuen Signalbedingungen bestätigen.**
   Vorab neue Frequenzen, Dämpfungen, Phasen und Rauschpegel sowie ein relevantes
   Effekt-/Präzisionsziel festlegen. Entwicklungs- und Bestätigungsdaten trennen.
   Erst dann die erforderliche Fallzahl und einen neuen Langlauf planen.

Alle Schritte nach der lesenden Prüfung sind methodische Vorschläge. Es ist
kein neues Protokoll eingefroren, keine zusätzliche wissenschaftliche Suche
autorisiert oder gestartet und keine historische Auswahl ersetzt worden.
Dauerhafte Archivablage und unabhängige Zweitkopie bleiben im
[Ergebnisindex](results_index.md) separat offen.
