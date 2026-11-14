# Bestätigung zweier Neustartpakete auf neuen Signalen: Manjaro 001

Quellenprüfung und Einordnung vom 14.11.2026, [Leitfadenphase 6](ringdown_recovery_roadmap.md).
Der vorab ausgewählte Kandidat **R: 4 × 1.000** erreicht nach vollständiger
lesender Verifikation und unabhängiger Nachzählung **10/10, 10/10 und 9/10 gemeinsame
A-/Originalfamilienerfolge**. Damit erfüllt er auf allen drei neuen Signalen
die praktische Grenze von mindestens 8/10. **L: 2 × 2.000** erreicht 9/10,
7/10 und 7/10 und verfehlt die separat berichtete Kontrollgrenze.
**Die vollständige erneute lesende Verifikation bestätigt den Befund.**
Alle zwölf wissenschaftlichen/technischen Verify-Exportdateien sind bytegleich
zum gelieferten Original; keine neuen Suchen oder Fits.

| Signal | R: A / geplant | R: A plus Originalfamilie | L: A / geplant | L: A plus Originalfamilie |
| --- | ---: | ---: | ---: | ---: |
| confirm_low | 10/10 | 10/10 | 9/10 | 9/10 |
| confirm_mid | 10/10 | 10/10 | 9/10 | 7/10 |
| confirm_high | 10/10 | 9/10 | 8/10 | 7/10 |

180 frische Suchen liefern **60 Paketausgaben** in 30 gepaarten Blöcken.
Alle 120 R-Mitglieder beenden 1.000 und alle 60 L-Mitglieder 2.000 äußere
Iterationen regulär; keine ausgefallenen, ausgelassenen oder wiederverwendeten
Suchen. Jede Paketausgabe wird allein aus den ursprünglichen Mitgliedsausgaben
nach endlicher nativer Trainings-MSE, Originalkomplexität und Mitgliedsposition
gewählt. Keine nachträgliche Auswahl anhand von Klasse, Familie oder Zusatzraster.
Physische Zeit t, lokal 300 Optimiereriterationen plus fünf zusätzliche lokale
Neustarts, allgemeine Grammatik und übrige eingefrorene Einstellungen bleiben erhalten.

Dies ist ein begrenzter positiver Bestätigungsbefund für R auf drei **vorab
festgelegten neuen Innenbereichskombinationen**. Die Signale sind keine zufällige
Stichprobe des gesamten Parameterkastens. Die frühere schwierige Randkombination
wird nicht erneut geprüft; die negative frühere Bestätigung bleibt unverändert.
Keine gepoolte Erfolgsquote, allgemeine Überlegenheitsbehauptung oder automatische
Übernahme in den späteren gewichteten Laufweg.

## Original, Ausführungsstand und Zeitfenster

- Original: `restart-budget-confirmation-manjaro-001.tar.gz`, **98.344.207 Bytes**.
- Selbst bestätigte SHA-256:
  `4217baf42ceece7c451f01d388c0f1b9d76bfb58a2e205d0ac6d67aea2a574b2`.
- 11.006 reguläre Dateien mit 806.168.742 entpackten Dateibytes in 14 Wurzeln:
  drei wissenschaftliche Abschnitte mit benachbarten `-call.json` und gemeinsamer
  Verifikation sowie technischer Manjaro-Vorlauf mit beiden Aufrufmessungen und
  Einzel-/Gesamtverifikation. Keine Ausführung archivierter Programme oder
  Deserialisierung von Suchzuständen für diesen Audit.
- Tatsächlicher sauberer wissenschaftlicher Ausführungsstand:
  [`6bc028204ff651ee883eeac4d38bff7c07fb3ded`](https://github.com/craexxn/ringdown-sr/commit/6bc028204ff651ee883eeac4d38bff7c07fb3ded),
  main nach [PR87](https://github.com/craexxn/ringdown-sr/pull/87).
  Die spätere Ergebnisdokumentation ersetzt diesen Stand nicht.
- [Plan](restart_budget_confirmation_plan.md),
  [Konfiguration/Seeds](../data/restart_budget_confirmation_protocol.json),
  Eingaben und Erzeuger wurden vor Implementierung festgelegt; unveränderte
  öffentliche Commitbindung `352b7b5145ad8c8e735eea887a29744c97825c20`.
  120 verschiedene neue Seeds, je vier pro Block; die ersten zwei in beiden
  Armen, jeweils in einer eigenständigen frischen Suche. Keine Checkpointfortsetzung.

| Abschnitt | Beginn, Europe/Vienna | Berichtabschluss, Europe/Vienna | Gemessener vollständiger Aufruf |
| --- | --- | --- | ---: |
| restart-budget-confirmation-low-manjaro-001 | 13.11.2026 12:02:58 | 13.11.2026 18:30:35 | 23.261,006 s |
| restart-budget-confirmation-mid-manjaro-001 | 13.11.2026 18:30:40 | 14.11.2026 00:36:16 | 21.939,891 s |
| restart-budget-confirmation-high-manjaro-001 | 14.11.2026 00:36:21 | 14.11.2026 07:08:48 | 23.550,058 s |

Die lokale Darstellung in MEZ/UTC+1 folgt den unveränderten UTC-Metadaten.
Die vollständigen Abschnittsaufrufe ergeben zusammen **68.750,956 s,
19 h 05 min 51 s**, ohne Abschnittspausen, technischen Vorlauf und spätere
Verifikation. Vorbereitung und Veröffentlichung sind enthalten; abschließende
Aufrufdatei und Nachprüfungen liegen außerhalb der gespeicherten Messgrenze.
Diese Zeiten nicht mit den darin enthaltenen Fit-/Workerzeiten addieren.

Die geprüfte gemeinsame Umgebung umfasst Manjaro Linux 6.18.55-1,
Intel Core i7-1165G7, CPU-Affinität `[0]`, Julia Default-/Interactive-/GC-Threads
1/0/1, BLAS einen Thread und Haswell-Kern, Python 3.12.14, Julia 1.13.1,
PySR 2.6.0 und SymbolicRegression 2.5.1. Alle fünf Vorbereitungen binden
dieselben 104 Quellen einschließlich aller 54 Python-Paketdateien;
jeder der 192 wissenschaftlichen beziehungsweise technischen Worker bindet
117 Quellen. Quellen, tatsächliche Worker-/Adapterherkunft, Laufzeitdateien
und Eingabemanifeste sind gegen Git und den sauberen Checkout bestätigt.

## Paarvergleich und Unsicherheitsintervalle

Gewinne und Verluste beziehen sich auf R gegenüber L im selben vorab geplanten
Seedblock; ein Gleichstand kann zwei Erfolge oder zwei verfehlte Endpunkte bedeuten.

| Signal | A: Gewinne / Verluste / Gleichstände | A plus Originalfamilie: Gewinne / Verluste / Gleichstände | Blöcke mit zusätzlichem gemeinsamen R-Erfolg |
| --- | ---: | ---: | --- |
| confirm_low | 1 / 0 / 9 | 1 / 0 / 9 | 2 |
| confirm_mid | 1 / 0 / 9 | 3 / 0 / 7 | 1, 3, 10 |
| confirm_high | 2 / 0 / 8 | 2 / 0 / 8 | 9, 10 |

Bei `confirm_high`, Block 2, erreicht R A, sein Familiennachweis bleibt aber
ungeklärt; L ist B. Beide verfehlen dort den gemeinsamen Endpunkt. Die Paarzahlen
sind deskriptiv und ersetzen keine vorab geplante inferenzielle Überlegenheitsprüfung.
Es erfolgt keine nachträgliche Auswahl zwischen beiden Armen und keine Kombination
mit 4 × 500.

Die folgenden **marginalen exakten zweiseitigen 95-%-Clopper–Pearson-Intervalle**
gelten für jeden entsprechenden Zählwert in der Ergebnistabelle, für beide
Endpunkte getrennt. Alle zwölf gespeicherten Intervalle wurden unabhängig durch
Inversion direkter Binomialsummen nachgerechnet.

| Beobachteter Zählwert | 95-%-Intervall |
| --- | --- |
| 10/10 | [69,15 %; 100 %] |
| 9/10 | [55,50 %; 99,75 %] |
| 8/10 | [44,39 %; 97,48 %] |
| 7/10 | [34,75 %; 93,33 %] |

Die Intervalle beschreiben unter der Bernoulliannahme Suchzufall auf dem jeweiligen
festen Signal, keine simultane Garantie für alle Endpunkte und keine Übertragung
auf eine Signalpopulation. Zehn Blöcke sind die pragmatisch eingefrorene Größe,
keine behauptete Powerberechnung. Auch 10/10 oder erfüllte 8/10 belegen keine wahre
Erfolgswahrscheinlichkeit von mindestens 80 %.

## Ausgewählte Formeln ohne gemeinsamen Erfolg

Die folgenden acht Originalausgaben verfehlen A oder den gültigen Originalfamilien-
nachweis. Alle anderen Paketausgaben sind A und als Originalmitglieder nachgewiesen.
Die unveränderten Bewertungsverträge und ein unabhängiger numerischer
Baum-Replay bestätigen die folgenden Gründe und Kurvenklassen.

| Signal / Arm | Block / Zelle | Klasse | Originalfamilie und Grund |
| --- | --- | --- | --- |
| confirm_low / L | 2 / 8 | B | Ungeklärt, nichtaffines trigonometrisches Argument |
| confirm_mid / L | 1 / 6 | B | Ungeklärt, trigonometrische Produktform |
| confirm_mid / L | 3 / 17 | A | Ungeklärt, Sinus einer kleinen exponentiellen Hüllkurve |
| confirm_mid / L | 10 / 55 | A | Ungeklärt, Sinus einer kleinen exponentiellen Hüllkurve |
| confirm_high / R | 2 / 12 | A | Ungeklärt, verschachtelte trigonometrische Form |
| confirm_high / L | 2 / 8 | B | Ungeklärt, verschachtelte trigonometrische Form |
| confirm_high / L | 9 / 53 | C | Familien- und Domainnachweis ungeklärt |
| confirm_high / L | 10 / 55 | A | Original mit 19 entfernbaren Definitionslücken; gültige Fortsetzung |

Bei der letzten Ausgabe ist das Original `proven_nonmember` wegen
`original_domain_gap`; die stetige Fortsetzung ist `proven_member`.
Sie ersetzt kein auf dem ganzen geschlossenen Prüfintervall gültiges Original.
Die drei anderen A-Ausgaben ohne Familiennachweis bleiben `unresolved`;
dies ist kein Beweis der Nichtzugehörigkeit. Kleine Zusatz- oder Hüllterme
werden nicht zu null gesetzt und keine Formeln nachträglich umgeschrieben.
Neue physikalische Parameterübereinstimmung bleibt **`not_assessed`**.

Die gezielte Frontdiagnose umfasst zusätzlich alle **226 Kandidaten in den
18 Mitgliedsfronten der acht Pakete ohne gemeinsamen Erfolg**. In keinem der
vier Nicht-A-Pakete liegt ein anderer A-Kandidat in diesen gespeicherten Fronten.
Für R/high/Block 2 ist auch im ganzen Paket keine gültige Originalfamilie
nachgewiesen. Bei L/mid/Block 3 und 10 sowie L/high/Block 10 liegen andere
A-/Originalfamilienkandidaten in der Front der gewählten Zelle. Ein anderes
gültiges Originalmitglied des Pakets ist bei L/mid/Block 10 und L/high/Block 10
jeweils Zelle 56; sein höherer Trainingsverlust rechtfertigt nach der eingefrorenen
Regel keine Ersetzung der ursprünglichen Paketwahl.

Diese Diagnose bewertet die 60 ausgewählten Paketformeln und die vor Beginn
dieser lesenden Diagnose begrenzt hinzugezogenen Fronten, keine vollständige
Evolutionsgeschichte und keine offene
Erkennerentwicklung. Ungeprüfte andere Fronten werden damit nicht als vollständig
nachgerechnet dargestellt. Bei L/high/Block 9 ist die Domain wegen
`denominator_zero_set_unresolved` ungeklärt; daraus keine bewiesene Lücke ableiten.

## Kontinuierliche Fehler und Zusatzraster

Maximum der relativen RMS- beziehungsweise Maximalfehler über die jeweils zehn
ausgewählten Paketausgaben eines Signals/Arms; beide Maxima können von
verschiedenen Ausgaben stammen. Werte aus den gespeicherten Originalbewertungen,
nur für die Darstellung gerundet. Die vollständigen 60 Metriksätze bleiben
in den Originalberichten und sind unabhängig numerisch nachgerechnet.

| Signal / Arm | Training RMS / Max | Zwischenpunkte RMS / Max | Zusatzraster RMS / Max |
| --- | ---: | ---: | ---: |
| confirm_low / R | 1,971e-10 / 2,028e-10 | 1,977e-10 / 2,032e-10 | 1,978e-10 / 2,031e-10 |
| confirm_low / L | 1,151e-03 / 1,025e-03 | 1,138e-03 / 1,035e-03 | 1,137e-03 / 1,034e-03 |
| confirm_mid / R | 4,862e-12 / 4,379e-12 | 5,032e-12 / 4,350e-12 | 5,038e-12 / 4,359e-12 |
| confirm_mid / L | 7,099e-03 / 5,426e-03 | 7,142e-03 / 4,593e-03 | 7,145e-03 / 4,839e-03 |
| confirm_high / R | 3,749e-04 / 5,215e-04 | 3,607e-04 / 4,886e-04 | 3,609e-04 / 4,967e-04 |
| confirm_high / L | 1,295e-02 / 9,883e-03 | 1,299e-02 / 8,937e-03 | 1,300e-02 / 9,187e-03 |

128 Trainings-, 889 reguläre Zwischen- und 1.024 vorab gebundene unregelmäßige
Punkte je Ausgabe. Das Zusatzraster dient ausschließlich der Diagnose; keine
neue Klasse, kein nachträglicher Ausschluss und kein Ersatz für einen Definitions-
oder Familiennachweis. Ein kleiner Rasterfehler allein belegt weder exakte
Familienzugehörigkeit noch allgemeine Identifizierbarkeit.

## Beobachtete Kosten und Ausfälle

Alle Mitgliederkosten einschließlich der nicht ausgewählten Suchen sind
enthalten. Kein Worker- oder Paketausfall; alle vorgesehenen Kostenfelder bekannt.

| Signal | Arm | Worker s | Fit s | Adapter s | CPU Nutzer / System s | Verlustcallbacks |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| confirm_low | R | 11.338,645 | 10.681,809 | 11.411,390 | 11.234,200 / 43,822 | 1.392.504.028 |
| confirm_low | L | 10.434,667 | 10.106,978 | 10.470,268 | 10.350,862 / 32,413 | 1.377.062.241 |
| confirm_mid | R | 10.541,832 | 9.883,225 | 10.614,208 | 10.441,950 / 43,657 | 1.265.568.664 |
| confirm_mid | L | 9.951,703 | 9.621,302 | 9.988,112 | 9.871,532 / 32,057 | 1.292.531.752 |
| confirm_high | R | 11.451,399 | 10.793,424 | 11.524,786 | 11.346,815 / 44,510 | 1.398.443.834 |
| confirm_high | L | 10.652,240 | 10.323,365 | 10.688,411 | 10.567,708 / 33,525 | 1.399.051.987 |

R benötigt auf low/mid/high **8,66 % / 5,93 % / 7,50 % mehr Workerzeit** als L.
Verlustcallbacks: **1,12 % mehr / 2,09 % weniger / 0,04 % weniger**.
Gleiche 4.000 äußere Iterationen je Paket bedeuten keine gleichen Rechenkosten.
Insgesamt 64.370,486 s Workerzeit und 8.125.162.506 Verlustcallbacks; dies sind
Kosten des ganzen ausgeführten Algorithmus, keine gepoolte Erfolgsquote.
Separate JIT-Zeiten und ein nativer Gesamtzähler aller Evaluierungen wurden
nicht beobachtet; Callback-Aufrufe nicht damit gleichsetzen. Keine historische
Wiederverwendung, daher entspricht der neue Suchaufwand dem gesamten Suchaufwand.
Kosten verändern die eingefrorene praktische Entscheidungsregel nicht.

## Tatsächliche Prüfung

Archivhash, Größe und sichere Extraktion sind bestätigt. Alle 11.006
Originaldateien und das Archiv sind nach der Herkunftsprüfung unverändert.
Der vollständige Quellen-/Bindungsaudit bestätigt alle 192 Worker einschließlich
nativer Originalwahl, Hall-of-Fame-Dateien, Iterationsabschluss, Laufzeitbelegen,
neun Veröffentlichungsmanifesten und fünf vollständigen Aufrufmessungen.
Der wissenschaftliche Bestand enthält 2.053 Endfrontkandidaten:
695/664/694 auf low/mid/high; zusätzlich 35 technische Kandidaten.
Diese Bestands- und Herkunftsprüfung ist von der unten begrenzten zusätzlichen
Formelnachrechnung zu unterscheiden. Die unabhängige
Nachzählung rekonstruiert alle 180 nativen Originalauswahlen und 60 Paketwahlen
aus den Mitgliedsdateien, alle drei Signalnenner, 30 Paarungen und sechs
Kostenfelder. Klassen-/Familienzählungen, Kosten, Intervalle und die gespeicherte
R-/L-Entscheidung stimmen überein. Die konsumierten Originaldateien sind dabei
unverändert; keine Fits oder neuen Suchen.

Die unveränderte vollständige lesende CLI-Gesamtverifikation auf dem sauberen
Ausführungsstand `6bc0282` ist bestanden: 180 geprüfte Zellen, 60 Paketausgaben
und null neue Suchaufrufe. Herkunft, Eingaben, effektive Optionen, Originalauswahlen,
Kosten und Abschlussbindungen sind bestätigt. Alle drei wissenschaftlichen
Exportdateien (Bericht, Zusammenfassung, Prüfsummenmanifest) sind bytegleich
zum Original; `transition_criterion_met=true`, `L_control_criterion_met=false`.
Der Checkout bleibt sauber und alle 11.006 Originaldateien samt Archivhash sind
auch nach sämtlichen eigenen Prüfungen unverändert.

Die gezielte zusätzliche Formelprüfung ist abgeschlossen: alle 60 ausgewählten
Paketformeln und 226 Kandidaten aus den 18 begrenzten Mitgliedsfronten,
nach Abzug von acht überlappenden Auswahleinträgen zusammen 278 getrennt
gebundene Kandidateneinträge, mit unveränderten Kurven-, Domain-, Struktur-
und Resttermverträgen kanonisch JSON-identisch nachgerechnet. Ein unabhängiger
rekursiver Float64-JSON-Baum-Replay mit Differenzen und Normen in Long-double-
Präzision bestätigt Klassen und kontinuierliche Fehler auf allen drei Rastern.
Maximaler Metrikunterschied geteilt durch das Maximum aus eins und den beiden
verglichenen Beträgen: `2,22 × 10⁻¹⁶`. Konsumierte Quellen unverändert;
keine neue Beweisregel und keine Fits.

Der mitgelieferte technische Manjaro-Vorlauf ist getrennt von der wissenschaftlichen
Serie: zwölf kleine Worker, vier Paketausgaben. Beide Einzelverifikationen
über die reguläre CLI und die gemeinsame Prüfung über die unveränderte öffentliche
Funktion `restart_budget_confirmation.verify(..., complete=True)` sind erneut
bestanden, ohne weitere Suchen. Die wissenschaftliche Serien-CLI verlangt drei
Quellen, die technische Prüfung umfasst zwei Fixtures. Die Berichte nennen
85.038/62.355 Verlustcallbacks und
429,015/421,688 s vollständige Abschnittsaufrufe. Technische Entscheidungsschlüssel
bleiben `null`; diese Fixtures liefern keine wissenschaftliche 8/10-Entscheidung.
**Alle neun neu erzeugten technischen Exportdateien sind bytegleich** zum
gelieferten Original. Der Vorlauf fand am 13.11.2026 statt: `fixture_a`
11:48:05–11:55:13, `fixture_b` 11:55:24–12:02:25, jeweils Europe/Vienna.

## Einordnung und nächster abgegrenzter Schritt

Die geplante praktische R-Grenze ist nach vollständiger Quellenprüfung erfüllt;
L verfehlt sie auf zwei Signalen. Die verbleibende R-Lücke liegt beim Nachweis
der Originalfamilie einer A-Kurve, während L zusätzlich vier Nicht-A-Ausgaben
besitzt. Offene Beweise sind kein Auftrag zur nachträglichen Erfolgssteigerung.
Historische negative oder gemischte Ergebnisse bleiben bestehen; andere Seeds,
Signale und Pakete erlauben keine kausale Verbesserungsschätzung gegenüber
4 × 500, 1 × 2.000 oder früheren Entwicklungsserien.

Nach dieser abgeschlossenen Quellenprüfung folgt gemäß Plan die **bewusste Übernahme des
ausgewählten Profils in den tatsächlichen allgemeinen Laufweg** nach Leitfadenphase 5.
Zuerst allgemeines Profil und Spezialtreiber abgleichen und den übertragenen
Pfad rauschfrei prüfen. Die Gewichtung muss sowohl Struktursuche als auch
Konstantenoptimierung bestimmen. Diese ungewichtete Bestätigung beweist den
späteren gewichteten Pfad nicht. Keine neue Budgetstaffel, zusätzliche Seedrunde
oder weitere Suchintervention; der Rauschpilot ist ein danach gesondert
festzulegender und auszuführender Schritt.

Original und Prüfnachweise im bestehenden [Ergebnisindex](results_index.md)
gemäß [Archivregel](results_archiving.md) zuordnen. Gemeinsame dauerhafte Ablage
und unabhängig SHA-256-geprüfte Zweitkopien bleiben nachzuweisen; vorhandene
Arbeitskopien sind kein Sicherungsnachweis. GitHub-Uploads sind optional.
