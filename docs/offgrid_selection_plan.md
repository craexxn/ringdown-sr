# Auswahl gespeicherter Formeln mit zusätzlicher verrauschter Messinformation

Vorab festgelegt am 23.11.2026, Leitfadenphase 7, nach vollständigem Abschluss
und lesender Nachprüfung des [Skalierungspiloten](white_loss_scaling.md),
vor der ersten neuen wissenschaftlichen Kandidatenbewertung. Dieser Plan wird
gesondert versioniert und vor Ausführung durch seinen SHA-256 im Laufweg gebunden.
Technische Referenzfälle verwendeten ausschließlich kleinere künstliche Raster;
die reservierten wissenschaftlichen Validierungsdaten wurden nicht ausgewertet.

## Frage, Begründung und Abgrenzung

Die [Folgestudie](noise_followup_results_manjaro_001.md) und ihre lesende
Kandidatendiagnose zeigen bessere bereits gespeicherte Alternativen sowie
große Zwischenpunktfehler trotz kleiner Trainingsverluste. Eine kleinere
Komplexitätsgrenze ist daraus nicht begründet: In einem Problemfall haben
die schlechte und eine gute Alternative beide 20 Knoten. Der früher geprüfte
pauschale `best`-Selektor verschlechtert die Gruppenmittel; auch eine bloße
Wiederholung des alten Verbots verschachtelter Trigonometrie ist nicht der
nächste begründete Schritt.

Der inzwischen vollständig geprüfte Skalierungspilot `white-scaling-cloud-002`
auf `5ae263a5cddd65417aa5d5466646218168d074e7` bestätigt bei 72 festen
Optimierungen unterschiedliche Pfade, aber praktisch gleiche Endkurven.
In den 18 freien Kurzsuchen ändern sich alle sechs gepaarten Fronten sowohl
zwischen O/S als auch S/K; die Baseline-Untergrenze ist überall inaktiv.
S erreicht über jeweils drei Suchseeds mittleren unregelmäßigen RMSE/A von
3,9093 % und 2,6180 %, O 13,2005 % und 9,1395 %, K 12,7062 % und 12,9692 %.
S ist in fünf von sechs Paaren besser als O, K in einem von sechs besser als S.
Alle drei vorbestimmten Wiederholungen reproduzieren ihre Originalfronten.
Nur zwei unabhängige Rauschfenster und kurze Suchbudgets begründen keine
allgemeine Verlustumstellung. Ein schlechter O-Baum hat nur 15 Knoten,
während gute S-Bäume 17–20 Knoten besitzen; ein K-Baum enthält weiterhin
einen linearen Sinusterm oberhalb der Raster-Nyquistfrequenz. Eine pauschale
Komplexitätsreduktion beseitigt diese Mehrdeutigkeit nicht gezielt.

Dieser geprüfte Ausgangsstand ist gebunden durch Manifest-SHA-256
`255223ba1bc8c653b75e9399a49e4ac83c86548f619ec58b9532965d87d9b3b3`
und unabhängigen Abschlussaudit-SHA-256
`c9a2ddf6872a35eb2014956daf018db40d8d18f63e65b3b2b5d714528246b84e`.
Der separate offizielle Verifier und der nachgelagerte geschützte Export
aller 93 Originalausgaben sind bestanden. Die bekannten Grenzen der alten
Kosten-/Exportprüfung sind im separat gebundenen Abschlussaudit und Exportguard
ergänzt; die wissenschaftlichen Originaldateien bleiben unverändert.

Die einzelne Intervention ist deshalb eine **neue Auswahlregel anhand einer
zusätzlichen verrauschten Beobachtung**. Die gespeicherten Originalbäume und
Konstanten bleiben unverändert. Keine neue Suche, keine Konstantenoptimierung,
keine neue Grammatik, kein anderer Komplexitätsdeckel und keine Änderung
der ursprünglichen Verlustfunktion. Die bekannte Wahrheit darf nur der
Datenerzeugung und abschließenden Bewertung dienen, nicht der Auswahl.

Das ist eine zusätzliche synthetische Beobachtung desselben Signals, keine
Interpolation vorhandener Messwerte. Eine solche unabhängige Wiederholung
lässt sich nicht nachträglich aus einem einzelnen realen GW-Ereignis erzeugen.
Ein günstiges Ergebnis wäre eine Entwicklungsdiagnose zum Nutzen zusätzlicher
Messinformation, keine unmittelbar verfügbare Methode für vorhandene reale
Ringdowns und keine unabhängige Bestätigung auf neuen Signalbedingungen.

## Vollständiger Bestand und drei festgelegte Auswahlen

Alle 156 eindeutigen erfolgreichen Pakete der Manjaro-Folgestudie werden
berücksichtigt: 26 Fälle × sechs Sucharme, je alle gespeicherten Kandidaten
der vier Originalworker. 52 Uniform-Referenzen aus Serie B werden nicht
nochmals gezählt. Fälle in der Reihenfolge `ar1-01` bis `ar1-20`, dann
`white-01` bis `white-06`; Arme O, K, E64s, E4096s, Jitter-O und Jitter-K.
Keine Auswahl auf die sechs zuvor bekannten Problemfälle beschränkt.

1. **Original:** bestehende Auswahl nach minimalem nativem Trainingsverlust
   reproduzieren, einschließlich Komplexitäts- und stabiler Indexbindung.
2. **Same-grid:** 128 zusätzliche verrauschte Beobachtungen auf der jeweiligen
   ursprünglichen Uniform- bzw. Jitterachse; aus demselben Kandidatenpool
   minimale endliche Validierungs-MSE wählen.
3. **Off-grid:** 128 zusätzliche verrauschte Beobachtungen auf einer neuen
   gemeinsamen unregelmäßigen Achse; dieselbe MSE-Auswahl aus demselben Pool.

Bei Gleichstand: kleinere ursprüngliche Komplexität, danach stabile
Kandidaten-ID (`member-NN/candidate-NNN`). Nichtendliche oder nicht im
Float64-Bereich darstellbare MSE macht einen Kandidaten auf diesem Raster
unzulässig. Wenn alle Kandidaten unzulässig sind, wird Enthaltung ausgegeben;
keine Ersatzformel. Die reine Auswahl-API erhält nur ID, Originalbaum,
Komplexität, Zeitpunkte und verrauschte Beobachtungen.

Der Vergleich Off-grid gegen Same-grid hält Zahl neuer Beobachtungen,
Auswahlmetrik und Kandidatenpool gleich. Gegenüber Original ändern sich
zusätzliche Realisierung und bei gewichteten Sucharmen auch die Auswahlmetrik
zu MSE. Dieser zweite Vergleich darf nicht als isolierter Rastereffekt gelten.

## Neue Beobachtungen vor jeder Kandidatenbewertung

Eine gemeinsame neue Achse mit 128 Strata im offenen Intervall
(0, 127/4096) s: `t_i = (i + u_i) / 128 * (127/4096)`, i = 0,...,127,
`u_i` aus privatem PCG64, Seed **2026112401**. Bei exakter Kollision mit
Training, Jittertraining oder einem der beiden Bewertungsraster Abbruch,
kein Ersatzseed und keine nachträgliche Verschiebung.

Pro Fall genau eine neue unabhängige Rauschrealisierung auf der sortierten
Vereinigung von Uniform-, Jitter- und neuer Off-grid-Achse. Private PCG64-Seeds
**2026112501 bis 2026112526** in der oben festgelegten Fallreihenfolge.
Gemeinsame Zeiten erhalten bitgleiche neue Beobachtungen. Weiß: unabhängige
Normalwerte je eindeutiger Zeit. AR(1): bestehende stationäre OU-Fortsetzung
mit sigma wie in der ursprünglichen Studie und rho = 0,65 bei 4096 Hz;
Korrelation bei Abstand dt ist `rho ** (4096 * abs(dt))`.
Der Generator speichert Zufallszustände, Zeiten, Rauschen und neue Werte
und prüft das Signal unabhängig mit hoher Präzision.

Diese Realisierung ist unabhängig vom jeweiligen Training, zwischen
Auswahlarmen aber kontrolliert gekoppelt. Signalparameter bleiben die
bekannte Entwicklungsbedingung A = 11/12, f = 265 Hz, tau = 1/150 s,
phi = 0,25, sigma/A = 0,05. Eine Realisierung pro Fall, keine Wiederholungen
nach Sichtung und keine Zusammenfassung von Sucharmen als unabhängige Fälle.

Für einen festen Kandidaten g und unabhängiges mittelwertfreies Rauschen
mit marginaler Varianz sigma² gilt auch bei OU-Korrelation:
`E[MSE(y,g) | g,t] = MSE(s,g) + sigma²`. Das motiviert die gemeinsame MSE
ohne Wahrheitszugriff. Der kleinste Validierungsscore unter vielen Kandidaten
ist trotzdem optimistisch und dient nicht als Qualitätsendpunkt.

## Vorab festgelegte Auswertung

**Primärer Kontrast:** Off-grid minus Same-grid, getrennt nach sechs
ursprünglichen Sucharmen und beiden Rauschmodellen. **Primärer Endpunkt:**
RMSE/A auf den bereits gebundenen 1024 unregelmäßigen Bewertungszeiten.
Negative Differenz bedeutet kleinere Abweichung von der sauberen Wahrheit.
Einheiten als Anteil A bzw. Prozentpunkte bei Darstellung in Prozent A.

Sekundär: Maximalfehler/A auf denselben Zeiten, RMS und Maximum auf den 889
regelmäßigen Zwischenpunkten sowie beide neuen Auswahlen gegen Original.
Pro Gruppe n = 20 AR(1) bzw. n = 6 White; Mittel, Median, empirische SD,
MCSE des gepaarten Mittels und Zahl besserer/gleicher/schlechterer Auswahlen
ausgeben. Geplante und tatsächlich auswertbare Paare sowie Enthaltungen und
nichtendliche Bewertungsfälle getrennt nennen. Keine Mittelung über 156
vermeintlich unabhängige Datenfälle, keine gemeinsame Erfolgsquote und kein
Signifikanz-, Äquivalenz- oder automatisches Übernahmegate.

Alle bisherigen Fälle und Bewertungsresultate gehören zum Entwicklungswissen.
Die neue Validierungsrealisierung wurde noch nicht betrachtet, aber die
Methodenwahl ist durch frühere Befunde motiviert. Die Gruppenauswertung ist
deskriptiv; eine spätere Bestätigung verlangt neue Signalbedingungen und
ein vorab begründetes Effekt-/Präzisionsziel.

Vollständiger Export aller 156 Pakete × drei Auswahlen einschließlich
Enthaltungen: unveränderte Formeln/Bäume, Herkunft, Punktdaten, alle
Kandidatenscores und Plots. Extreme Werte sichtbar skaliert kennzeichnen,
keine Achsenkappen oder geglätteten Ersatzkurven. Endliche Rasterprüfungen
beweisen keine kontinuierliche Domainfreiheit zwischen beliebigen Punkten.

## Quellen-, Kosten- und Abschlussbindung

Die Originaldateien werden ausschließlich gelesen. Drei SHA-256-Anker der
Originalinventare (nicht der komprimierten Archive):

- Shared: `e938851c3f5ffeec0bcd8505ed5f38835df8a14865e0aa5f5b34759dece1299a`
- Duration: `2af1c2e46aae4526e0c272729033ad90939c21fa41e395044108cc56aff77c22`
- Sampling: `94bf6f7ac6ce7dfd45a6dcc240abf9fa2f44855aae7d63e407adea2f9a27c0e1`

Jede konsumierte Datei zusätzlich gegen Inventar und Workerbelege prüfen;
ursprünglicher wissenschaftlicher Ausführungscommit bleibt
`8a1a4a1437f4b01daf1f070b56add248074c5907`. Neue Quellen, Planhash, Eingaben
und Exporte separat binden. Vier Stunden Laufgrenze. `<output>-call.json`
misst Wandzeit und CPU des neuen Aufrufs einschließlich Fehlerpfad; diesen
Geschwisterbeleg mit archivieren. Keine neuen SR-Kosten vorgeben.

Eine separate lesende Verifikation verlangt vollständigen Abschluss,
unveränderte Originalquellen, reproduzierte neue Eingaben und Auswahlen,
passende Metriken sowie alle Ausgabehashes. Danach getrennte Archivierung
mit Ergebnisindex. Fehler und Teilresultate bleiben erhalten.

## Literatur und verworfene Alternativen

- [VanderPlas (2018)](https://arxiv.org/abs/1703.09824): neue Messzeiten ändern
  das spektrale Fenster; weitere Werte auf demselben Uniformraster lösen
  exakte Aliase nicht. Ungleichmäßigkeit garantiert keine richtige Frequenz.
- [Cranmer (2023)](https://arxiv.org/abs/2305.01582): evolutionäre Strukturwahl,
  lokale Konstantenoptimierung und Ergebnisauswahl sind getrennte Schritte.
- [Morris, White und Crowther (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/):
  Datengenerierung, Methoden, Endpunkte und Monte-Carlo-Unsicherheit vorab trennen.
- [Keijzer (2003), Originalartikel](https://groups.csail.mit.edu/EVO-DesignOpt/groupWebSite/uploads/Site/keijzer-improving-symbolic-regression-interval-arithmetic-linear-scaling-eurogp-2003.pdf):
  Intervallprüfung kann zwischen Messpunkten verborgene Singularitäten adressieren.
  Seine „linear scaling“ ist ein affiner Ausgabefit, nicht der Faktor vor
  unserer Verlustfunktion.
- [Kronberger et al. (2022)](https://arxiv.org/pdf/2103.15624): erfüllte
  Formconstraints garantieren keine besseren Train-/Testfehler; konservative
  Intervallregeln können zulässige Modelle verwerfen. Daher hier keine
  pauschale Verschärfung der Grammatik oder Komplexitätsgrenze.
