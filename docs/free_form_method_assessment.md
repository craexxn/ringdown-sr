# Freie Formelfindung: Literatur- und Methodenabwägung

Stand: 03.11.2026. **Entscheidungsgrundlage, kein angenommener Methodenplan.**
Ausgangspunkt sind die abgeschlossenen Pilotkontrollen und das erneut gelesene
Exposé vom 29.09.2026, insbesondere PDF-Seiten 2–3. Ergebnisbasis ist
`2d9ed90043628f0c3b2f948634b1bdcd769bc886`, der bestätigte Merge von
[PR #50](https://github.com/craexxn/ringdown-sr/pull/50).
Repositoryabgleich und aktueller Arbeitsstand stehen ausschließlich im
[bestehenden Fortsetzungsdokument](representation_implementation_status.md).

**Empfehlung:** Wenn eine weitere begrenzte Entwicklung verfolgt werden soll,
zuerst über genau einen allgemeinen Strukturprior entscheiden: keine
trigonometrischen Nachfahren unter `sin` oder `cos`. Dafür unten einen kleinen,
kontrollierten Vergleich vorbereiten. Das erhält freie Kombinationen und
Konstanten, schränkt aber die Grammatik ausdrücklich ein. Die Literatur belegt
keinen erwartbaren Ringdown-Erfolg dieser Änderung; auch Verschlechterung ist
plausibel. Bei fehlender Zustimmung zu diesem Vorwissen oder zum begrenzten
Aufwand ist eine Pause besser begründet als weitere ungerichtete Suchläufe.

Hier wurden Literatur und Quellen gelesen und Vorschläge formuliert. Keine
neue Methode angenommen, eingefroren, implementiert oder ausgeführt; keine
Suche, Optimierung, nachträgliche Ersatzwahl oder Archivaudit-Wiederholung.

## 1. Welche Befunde die Entscheidung tatsächlich tragen

Die folgenden Zahlen sind **übernommene, zuvor geprüfte Ergebnisse** aus den
verlinkten Repositoryberichten. In diesem Arbeitsschritt wurden die Berichte
gelesen, ihre numerischen Prüfungen aber nicht erneut ausgeführt.

| Nachweis | Belastbare Aussage | Nicht daraus ableitbar |
| --- | --- | --- |
| [Zeitdarstellung/Häufigkeiten](representation_control_results_manjaro_001.md): neun Zellen, 57 Frontkandidaten | Gemeinsame Häufigkeitsschalter verbessern die Approximation; `u=32*t` wurde bereits untersucht. Kein Kurvenerfolg. | „Einfach die Zeit normieren“ als noch unversuchte Lösung; garantierte Diversität durch die Schalter. |
| [Konstantendiagnose](constant_diagnostic_results_manjaro_001.md): 0/24 unter 20/2, 24/24 unter 100/2 | Der Backendpfad kann den vorgegebenen Vierkonstantenbaum von diesen acht Starts anpassen. | Freie Strukturentdeckung, allgemeine Einzugsgebiete oder alleiniger Optimiererengpass. |
| [Freier Budgetvergleich](free_optimizer_budget_results_manjaro_001.md): sechs Suchen | 100/2 verbessert MSE/RMS bei drei bekannten Seeds; weiterhin 0/3 erfolgreiche Originalauswahlen je Budget. | Nutzen weiterer Budgetstufen. Der vollständige unabhängige Originalarchiv-Audit bleibt offen. |
| [Suchbeobachtung 002](search_trajectory_results_manjaro_002.md): sechs Zellen, drei bestandene Aus/an-Paare | Kein erfolgreicher Frontkandidat; kein Kurven-/Parametererfolg unter 58.629 verifizierten Positionen. | Vollständige Mutationshistorie, Bestätigung aller 62.384 Positionen oder algebraischer Unmöglichkeitsbeweis. |

157 Positionen bleiben numerisch ungeklärt, 3.598 nicht beurteilt. Die einzige
erkannte Exponential-Kosinus-Produktform wächst statt abzuklingen und passt
schlecht. Ihr Fehlen in Hall of Fame und Endfront belegt keine konkrete
Verwerfungs- oder Verlustgeschichte. Die
[Replayregeln](search_trajectory_replay_policy.md) gelten unverändert.

Eine reine Änderung der Endauswahl ist gegenwärtig nicht als Abhilfe belegt:
In den geprüften Fronten liegt kein erfolgreicher Kandidat bereit. Auch eine
höhere Priorität für `exp` wäre kein aus dem Befund erzwungener Schritt:
142 unterschiedliche Bäume enthalten diesen Operator bereits. Offen bleibt,
wie Darstellung, numerische Anpassung und evolutionäre Suche zusammenwirken.

## 2. Exposé-Konformität und zulässiges Vorwissen

Das Original-PDF ist in diesem Chat verfügbar und wurde direkt gelesen;
die folgenden Anforderungen sind keine bloß übernommene Zusammenfassung:

- Gesucht ist eine explizite Signalformel mit frei zu bestimmender Struktur.
  Der Fit mit bekannter Ringdown-Form bleibt eine privilegierte Referenz.
- Die aus separatem Hintergrund geschätzte Kovarianz bleibt während Suche
  **und** Konstantenanpassung fest. Diagonale, geschätzte volle und im
  synthetischen Fall bekannte volle Kovarianz bilden die Vergleichsarme.
- Für diese Arme müssen Operatoren, Komplexitätsgrenzen, Auswahlprinzip und
  Rechenzeitbudget gleich sein. Test-Reinsignale sind weder Such- noch Auswahlhilfe.
- Relativer L2-Fehler ist Hauptkriterium, Strukturstabilität ein zusätzlicher
  Befund. Pilotgrenzen dürfen daraus nicht nachträglich umdefiniert werden.

„Frei“ bedeutet hier Suche innerhalb einer deklarierten Grammatik. Bereits
`+,-,*,/,exp,sin,cos` und ein Knotenlimit sind Vorwissen. Eine zusätzliche
allgemeine Verschachtelungsregel kann damit vereinbar sein, muss aber als
methodische Einschränkung beschlossen und später für alle Kovarianzarme
gleich verwendet werden. Sie ist weder neutrale Formatierung noch eine
physikalische Gesetzmäßigkeit.

| Vorwissen | Einordnung für dieses Projekt |
| --- | --- |
| Zeit- und Ausgabeeinheit, Abtastrate, Fensterdauer, allgemeine Operatoren | Deklarierbare Mess- und Darstellungsinformation; keine wahre Ringdown-Form. |
| Allgemeine Verschachtelungsregeln oder vorab gewählte Operatorgewichte | Zusätzlicher Strukturprior; Wirkung und ausgeschlossene Formen offenlegen. |
| Fest deklarierte Anzahl/Einheiten freier Parameter | Stärkerer Parameterprior; nicht mit beliebig vielen dimensionsbehafteten Konstanten gleichsetzen. |
| Frequenzschätzung aus Trainingsdaten | Datenabhängige Suchhilfe; eigenes Verfahren, Kosten und Datenrollen festlegen. Kein kostenloser, neutraler Startwert. |
| Wahre Frequenz/Abklingzeit, vorgegebener Produktbaum, Ringdown-Makrooperator, vorab getrennte Hüllkurve und Träger | Zielbezogenes Privileg. Als Referenz/Diagnose ausweisen; ersetzt den freien Hauptpfad nicht. |

Die Hauptversuchsplanung bleibt offen: 200 Hz/4 ms und 250 Hz/6 ms bei
25 ms gegenüber dem bisherigen Entwicklungsfall 250 Hz/8 ms bei 31,25 ms;
Hintergrundlängen, Autokovarianzschätzung und Regularisierung, Datenabhängigkeiten,
Rechenzeitbudget, endgültige Auswahl und unabhängige Bewertung. Das Exposé
verlangt nicht, aus drei bekannten Entwicklungsseeds eine Leistungsstudie zu
machen. Hauptversuche und LIGO-Auswertung werden hier nicht freigegeben.

## 3. Rechercheumfang und Zugriffsstatus

Gezielte Webrecherche am 03.11.2026, keine systematische Vollständigkeitssuche.
Suchachsen unter anderem `symbolic regression damped oscillation`,
`parameter identification symbolic regression nonlinear least squares`,
`symbolic regression nested trigonometric constraints`,
`physical symbolic optimization units` und `priors symbolic regression`.
Direkte Oszillatorbeispiele wurden mit Methodenprimärquellen zu Konstanten,
Grammatik und Auswahl ergänzt. Suchtreffer und Übersichtsartikel dienten nur
zum Auffinden; die folgenden fachlichen Aussagen stützen sich auf Primärtexte.

**Volltext gelesen** bedeutet hier: Die angegebenen fachlichen Abschnitte
wurden im zugänglichen Volltext gelesen, nicht jeder Anhang oder Quellcode
vollständig auditiert. Es wurde keine publizierte Implementierung reproduziert.
Bei S9 lag nur der Abstract vor. Sekundärangaben sind kein Ergebnisnachweis.

### S1: Direkte freie Oszillatorrekonstruktion mit PhySO

Tenachi, Ibata und Diakogiannis (2023), *Deep symbolic regression for physics
guided by units constraints: toward the automated discovery of physical laws*,
[DOI 10.3847/1538-4357/ad014c](https://doi.org/10.3847/1538-4357/ad014c).
[Volltext, arXiv v2](https://arxiv.org/html/2303.03192v2): III.1–III.3,
V.4–V.5, Tabelle 5 und Anhang A/B gelesen.

- **Mechanismus/Problem:** Ein RNN erzeugt Ausdrücke mit Einheitenregeln während
  der Generierung; lokale L-BFGS-Anpassung bestimmt Konstanten. Der gedämpfte
  Oszillator ist ausdrücklich ein synthetischer Testfall. Tabelle 5 berichtet
  bei einer Million Ausdrucksversuchen fünf erfolgreiche vollständige Läufe;
  die dortigen Ablationsvarianten erreichen für diesen Fall keinen Erfolg.
- **Voraussetzungen/Vorwissen:** Operatorbibliothek, Längen-/Verschachtelungspriors
  und fallspezifische freie Konstanten samt Einheiten; der Oszillator besitzt
  drei freie Parameter. Das ist kein bloßes Einschalten unserer Einheitenprüfung.
- **Bezug/Grenze:** Direkter Machbarkeitsbeleg unter anderen Bedingungen,
  kein Nachweis für 128 äquidistante Werte, unsere Konstantenskalen, feste volle
  Rauschkovarianz oder unsere Originalauswahl. Die Ablation isoliert keine
  einzelne für PySR übertragbare Grammatikregel.
- **Prüfidee:** Allgemeine Strukturpriors getrennt beurteilen; vor einem
  Backendwechsel Parameterprivilegien, Verlustpfad und Kosten abgleichen.

### S2: Reale gedämpfte Bewegung mit stärkerem Vorwissen

Shin, Jang und Jo (2024), *Physics Education and Symbolic Regression*,
[DOI 10.3938/NPSM.74.678](https://doi.org/10.3938/NPSM.74.678).
[Verlagsvolltext](https://www.npsm-kps.org/journal/view.html?doi=10.3938/NPSM.74.678):
II, III.2, Tabelle 2 und IV gelesen. Der DOI-Abruf scheiterte zunächst;
die direkte Artikelseite war zugänglich.

- **Mechanismus/Problem:** AI-Feynman und PhySO werden auf experimentelle
  Bewegungsdaten angewandt, darunter ein in Wasser gedämpftes Federpendel.
- **Voraussetzungen/Vorwissen:** Für die Analyse werden 50 Positionen verwendet;
  die AI-Feynman-Darstellung nutzt `omega*t`, `alpha*t` und Phase als
  dimensionslose Eingaben. Die Diskussion beschreibt ausdrücklich die
  vorausgesetzte exponentielle Hüllkurve, konstante Frequenz und darauf
  abgestimmte Funktionsauswahl.
- **Bezug/Grenze:** Thematisch sehr nah, aber kein Nachweis der Rekonstruktion
  allein aus `t,y` ohne diese Hilfen. Normalisierte Fehler und ein
  bekannter Strukturfit sind nicht unsere Kurven- oder Identifikationsgates.
- **Prüfidee:** Eine Vorwissensbilanz gehört vor jeden Verfahrensvergleich.
  Die dortigen Merkmale nicht still in unseren Suchinput übernehmen.

### S3: Konstantenanpassung innerhalb genetischer Suche

Kommenda, Burlacu, Kronberger und Affenzeller (2020; online 2019),
*Parameter identification for symbolic regression using nonlinear least squares*,
[DOI und Volltext 10.1007/s10710-019-09371-3](https://doi.org/10.1007/s10710-019-09371-3).
Abschnitte 1.3, 2 und 3 einschließlich des Sinusbeispiels gelesen.

- **Mechanismus/Problem:** Levenberg–Marquardt mit automatischer Differentiation
  passt Konstanten in GP-Bäumen an; optimierte Werte fließen in die Evolution
  zurück. Zusätzlich wird eine affine Ausgabeskalierung verwendet.
- **Voraussetzungen/Vorwissen:** Differenzierbare Ausdrücke, passende Startwerte,
  zusätzliche lineare Koeffizienten und Rechenaufwand. Im Beispiel
  `sin(theta*x)` erreicht LM das globale Minimum nur aus einem begrenzten
  Startbereich; eine korrekte Baumform genügt nicht.
- **Bezug/Grenze:** Begründet die Kopplung von Strukturfitness und Anpassung
  sowie das Risiko oszillatorischer lokaler Minima. Beweist weder einen
  BFGS-Defekt bei uns noch, dass LM nach 24/24 erfolgreichen festen Fits
  die freie Suche verbessern würde. Das Methodenpaket ist keine isolierte
  Solverablation gegen unseren Callback.
- **Prüfidee:** Falls später ein Solververgleich gewählt wird, denselben
  vollständigen Residuenverlust und gleiche Kosten verwenden; affine
  Skalierung und neue Starts nicht gleichzeitig als versteckte Faktoren ergänzen.

### S4: Grammatikbeschränkung mit einem wichtigen Gegenbefund

Petersen et al. (2021), *Deep symbolic regression: Recovering mathematical
expressions from data via risk-seeking policy gradients*, ICLR,
[stabile Quelle arXiv:1912.04871v4](https://arxiv.org/abs/1912.04871v4).
[Volltext](https://arxiv.org/html/1912.04871v4): 3.1 und Anhänge C/D gelesen.

- **Mechanismus/Problem:** RNN-Sampling mit Maskierung unzulässiger Tokens,
  risikosuchender Lernregel und innerer Konstantenoptimierung auf
  SR-Benchmarks. Eine Regel verbietet trigonometrische Nachfahren unter
  trigonometrischen Operatoren.
- **Voraussetzungen/Vorwissen:** Grammatik-/Längenregeln, ausgewählte Benchmarks
  und lokale BFGS-Starts. Bei Konstantenfällen wurde vorab geprüft, dass die
  richtige Struktur vom gewählten Start nicht in einem schlechten Minimum endet.
- **Bezug/Grenze:** Eine allgemeine Grammatikregel ist formulierbar, ohne
  einen Ringdown-Baum vorzugeben. Aber im GP-Vergleich senkt das nachträglich
  geprüfte **Regelbündel** die Wiedergewinnungsrate von 60,1 auf 32,3 Prozent
  (Anhang C). Das ist weder eine isolierte Wirkung des Trigonometrieverbots
  noch ein PySR-Ergebnis. Weniger erlaubte Bäume können Exploration behindern.
- **Prüfidee:** Eine einzelne Regel nur gegen eine frische unbeschränkte
  Kontrolle vorschlagen; keine Erfolgsgarantie aus DSR auf evolutionäre Suche
  übertragen und kein zusätzlicher RNN-Wechsel im selben Vergleich.

### S5: Der bereits verwendete Suchmechanismus

Cranmer (2023), *Interpretable Machine Learning for Science with PySR and
SymbolicRegression.jl*, [DOI 10.48550/arXiv.2305.01582](https://doi.org/10.48550/arXiv.2305.01582).
[Volltext v3](https://arxiv.org/html/2305.01582v3): 2.1 und Algorithmusdarstellung gelesen.

- **Mechanismus/Problem:** Mehrpopulationsevolution mit Vereinfachung und
  Konstantenanpassung; adaptive Bestrafung häufig vorkommender Komplexitäten
  soll frühe Spezialisierung auf eine Formelklasse erschweren.
- **Voraussetzungen/Vorwissen:** Operatoren, Komplexitätsdefinition, Mutationen
  und Ressourcen bestimmen den tatsächlich explorierten Raum.
- **Bezug/Grenze:** Die gemeinsam aktivierten Häufigkeitsschalter sind eine
  bereits untersuchte Richtung. „Frequency“ meint hier Häufigkeit von
  Komplexitäten, keine Information über 250 Hz. Der Artikel beschreibt keine
  Garantie und ersetzt nicht die Prüfung unserer gepinnten Version.
- **Prüfidee:** Vor einer Änderung genau den noch unbehandelten Faktor
  benennen. Häufigkeitsschalter oder lokale Optimierung nicht als neue Lösung
  erneut vorschlagen, nur weil sie in der Literatur erfolgreich eingesetzt werden.

### S6: Vollständige Struktursuche und MDL haben Bedingungen

Bartlett, Desmond und Ferreira (2023 online; Zeitschriftenband 2024),
*Exhaustive Symbolic Regression*,
[DOI 10.1109/TEVC.2023.3280250](https://doi.org/10.1109/TEVC.2023.3280250).
[Volltext arXiv v2](https://arxiv.org/html/2211.11461v2): II.D, III und V.A–B gelesen.

- **Mechanismus/Problem:** Enumeration bis zu einer festgelegten Komplexität,
  algebraische Deduplikation und numerische Anpassung; MDL verbindet
  Datenbeschreibung, Formelstruktur und Parameterpräzision. Anwendung auf
  kosmologische Daten.
- **Voraussetzungen/Vorwissen:** Endliche Operatorbasis und Größenlimit;
  optimale Rangfolge setzt global gelöste Konstantenprobleme voraus.
  Der untersuchte Ansatz bleibt bei niedriger Komplexität, ungefähr zehn
  Knoten, praktikabel.
- **Bezug/Grenze:** Trennt Kandidatenerzeugung von Bewertung. Unsere explizite
  Vierkonstantenform hat bereits 13 Knoten nach Projektzählung; Zählweisen
  sind vor einem Vergleich abzugleichen. Enumeration beseitigt lokale
  Frequenzminima nicht und begründet keine bezahlbare Vollsuche bis 20 Knoten.
- **Prüfidee:** MDL später als eigenständige Auswahloption spezifizieren;
  gegebenenfalls kleine Teilräume vergleichen, aber keinen globalen
  Ringdown-Erfolg aus niedrigen Enumerationsgrenzen ableiten.

### S7: Strukturprior, Parameterprior und Kovarianzgewichtung

Bartlett, Desmond und Ferreira (2023), *Priors for symbolic regression*,
[DOI 10.1145/3583133.3596327](https://doi.org/10.1145/3583133.3596327).
[Volltext arXiv v2](https://arxiv.org/html/2304.06333v2): 2.1–2.4 und 4 gelesen.

- **Mechanismus/Problem:** Ein aus Gleichungen gelerntes n-Gramm-Modell bewertet
  Operatoranordnungen; Fractional Bayes Factors behandeln Parameterpriors.
  Bayesianische, MDL- und heuristische Auswahl werden verglichen. Der
  Supernovafall verwendet eine veröffentlichte volle Kovarianz.
- **Voraussetzungen/Vorwissen:** Gleichungskorpus, Parametrisierung und
  Näherungen der Evidenz sind Teil der Methode. Gleiche Knotenanzahl bedeutet
  nicht gleiche a-priori-Plausibilität unterschiedlicher Verschachtelungen.
- **Bezug/Grenze:** Begründet eine explizite Vorwissens- und Auswahlbilanz.
  Keine Studie zum Einfluss geschätzter Hintergrundlängen auf kurze
  Ringdowns; die volle Kovarianz stammt dort nicht aus unserem Verfahren.
  Ein auf Zielgleichungen abgestimmter Korpus wäre zusätzliches Vorwissen.
- **Prüfidee:** Vor Hauptversuchen eine Auswahlregel mit festem Kandidatenpool,
  Likelihood und Datenrollen entwerfen. Kein nachträgliches Umranken der
  bisherigen Resultate und keine bevorzugte Kodierung gerade der Ringdown-Form.

### S8: Oszillatordynamik ist eine andere Zielgröße

Brunton, Proctor und Kutz (2016), *Discovering governing equations from data
by sparse identification of nonlinear dynamical systems*,
[DOI und Volltext 10.1073/pnas.1517384113](https://doi.org/10.1073/pnas.1517384113).
Methodendarstellung zu Gleichungen 1–5 gelesen.

- **Mechanismus/Problem:** SINDy bestimmt wenige aktive Terme einer
  Kandidatenbibliothek für die rechte Seite von Bewegungsgleichungen.
  Oszillatoren gehören zu den untersuchten dynamischen Systemen.
- **Voraussetzungen/Vorwissen:** Zustandsvariablen, gemessene/geschätzte
  Ableitungen und eine geeignete Bibliothek, in der die Dynamik dünn besetzt ist.
- **Bezug/Grenze:** Zeigt einen anderen Zugang zu oszillatorischen Daten,
  rekonstruiert aber nicht unmittelbar eine explizite Signalformel aus `t,y`.
  Ableitungen würden zudem das Rausch- und Kovarianzproblem verändern.
- **Prüfidee:** Nur als ausdrücklich anderes Forschungsdesign erwägen.
  Ein erfolgreicher ODE-Fit ist kein Ersatznachweis für unseren Hauptpfad.

### S9: Verwandte Oszillatorvorhersage, nur Abstract geprüft

Quade, Abel, Shafi, Niven und Noack (2016), *Prediction of dynamical systems
by symbolic regression*,
[DOI 10.1103/PhysRevE.94.012214](https://doi.org/10.1103/PhysRevE.94.012214).
[Verlagsabstract](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.94.012214)
und [PubMed](https://pubmed.ncbi.nlm.nih.gov/27575130/) gelesen.
Der Verlagsvolltext verlangte Anmeldung; hier kein Volltextnachweis.

- **Mechanismus/Problem laut Abstract:** Fast Function Extraction und genetische
  Programmierung für die Vorhersage dynamischer Systeme, darunter ein
  harmonischer Oszillator.
- **Voraussetzungen/Vorwissen:** Messdaten als Ausgangspunkt; konkrete
  Merkmalswahl, Operatoren und Konstantenbehandlung sind damit nicht geklärt.
- **Bezug/Grenze:** Verwandte Aufgabenklasse, kein nachgewiesener Erfolg bei
  freier gedämpfter Ringdown-Formelfindung unter unseren Bedingungen.
- **Prüfidee:** Volltextzugang erst bei konkreter Erwägung dieser Verfahren
  vertiefen. Aus dem Abstract wird keine Methodenentscheidung abgeleitet.

## 4. Folgerungen für Darstellung, Optimierung und Auswahl

Die folgenden Folgerungen sind **eigene methodische Bewertungen** der Quellen
und Projektbefunde, keine zusätzlich berichteten Literaturergebnisse.

**Darstellung und Einheiten:** Im aktuellen Pilot sind die elementaren
Operatoren für die Zielstruktur vorhanden. Einheitenzulässigkeit schließt
unpassende Dimensionen aus, erzwingt aber weder Dämpfung noch eine konstante
Trägerfrequenz. Die Wildcard-Einheiten freier Konstanten sind schwächeres
Vorwissen als vorab typisierte Parameter. Numerische Zeitstreckung,
Dimensionslosmachen und Einheitensteuerung während der Baumgenerierung sind
verschiedene Eingriffe. Die bereits geprüfte Streckung `u=32*t` behielt
Sekunden und Einheitenprüfung bei; sie wurde zudem nicht mit den aktivierten
Häufigkeitsschaltern gekreuzt. Die Wechselwirkung ist offen, keine automatische
Einladung zu einem zusätzlichen Arm.

**Konstanten:** Gute Fits bei vorgegebener Struktur schließen ungünstige
Startwerte in der freien Suche nicht aus. Der gelesene gepinnte
[Backendpfad v2.5.1](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/ConstantOptimization.jl#L202)
führt die zusätzlichen Restarts vom ursprünglichen Konstantenvektor aus;
bei Nichtnullwerten sind es relative normalverteilte Störungen, bei Null
additive Normalstarts. Das ist keine globale Mehrskalensuche. Hieraus folgt
aber nicht, dass gerade die beobachtete wachsende Produktform damit hätte
gerettet werden können: Ihr Optimierungsverlauf ist nicht bekannt.

Ein generischer Residuenoptimierer könnte bei festem `C=L L^T` den Vektor
`L^-1 (y-f_theta)` minimieren. Dann muss derselbe vollständige Vektor auch die
Konstantenanpassung treiben; elementweise Gewichte ersetzen volle Kovarianz
nicht. Diese algebraische Anschlussmöglichkeit ist kein implementierter
LM-/AD-Pfad und keine Empfehlung, Solver, Ableitungen, Skalierung und Starts
zugleich umzustellen.

**Komplexität:** Knotenlimit, interne Häufigkeitsmechanismen, explizite
Komplexitätskosten und endgültige Formelauswahl erfüllen unterschiedliche
Aufgaben. Ein billiger `ringdown(...)`-Operator würde Struktur und Zählung
privilegieren. Ein hoher Preis für Division oder verschachtelte Funktionen
wäre ebenfalls ein Prior und benötigt eine eigene Begründung. `exp` lediglich
zu verbilligen ist durch sein beobachtetes Vorkommen nicht hinreichend begründet.

**Auswahl:** Für die rauschfreien Entwicklungskontrollen bleibt die ursprüngliche
Trainingsauswahl samt festen Gates bestehen. Für die spätere Rauschstudie ist
`accuracy` noch kein wissenschaftlich begründetes Auswahlprinzip. MDL kann
eine Option sein, verlangt aber eine festgelegte Kodierung und Likelihood.
Bei festem `C` ist `log(det(C))` innerhalb eines Kandidatenvergleichs konstant;
zwischen unterschiedlichen Kovarianzen gilt das nicht. Beliebig skalierte
`Q/N`-Werte plus derselbe Strafterm ergeben keine automatisch faire MDL-Auswahl.
Singuläre Parameterkrümmungen, Aliase und rauschfreie Grenzfälle brauchen
definierte Behandlung statt blind übernommener Informationskriterien.

Die spätere Formelauswahl muss ohne Test-Reinsignal auskommen. Eine mögliche
Validierungsregel benötigt geeignete getrennte Signal-/Rauschbeispiele;
zufällig getrennte Einzelzeitpunkte einer korrelierten kurzen Kurve sind keine
automatisch unabhängigen Daten. Hintergrundabschnitte zur Kovarianzschätzung
sind ihrerseits keine Validierungsdaten für die Signalkurve. Regeln auf den
bekannten Entwicklungsfällen festlegen, anschließend unabhängig bewerten.

## 5. Wenige abgewogene Optionen

| Option | Hypothese und möglicher Erkenntnisgewinn | Vorwissen, Aufwand und Grenze | Bewertung |
| --- | --- | --- | --- |
| A: Ein allgemeines Verbot trigonometrischer Nachfahren unter `sin/cos` | Ein veränderter Grammatikprior verbessert freie Originalauswahlen, wenn verschachtelte trigonometrische Approximationen einen ungünstigen Suchpfad begünstigen. | Kein Produktbaum vorgegeben; phasenmodulierte Formen werden ausgeschlossen. Relativ kleiner Eingriff über vorhandene Bibliotheksschnittstelle, aber neuer Plan und technische Prüfung erforderlich. Nachträgliche Ablehnung kann die Suche auch verschlechtern; S4 liefert Gegenbelege für ein Regelbündel. | Bevorzugter begrenzter **Entwurf**, sofern dieser Prior akzeptiert wird. Keine behauptete Ursache oder Erfolgsprognose. |
| B: Residuenbasierter LM-Vergleich innerhalb freier Suche | Andere lokale Schritte können bei gleichen Kosten andere Strukturfitness und Endergebnisse ergeben. | Grammatik kann gleich bleiben; Residuen-/Jacobianpfad, volle Gewichtung und numerische Gegenprüfungen sind zusätzlicher Implementierungsaufwand. S3 ändert mehr als nur den Solver; auch LM hat lokale Frequenzminima. | Zurückstellen: 100/2 löst die bisherigen festen Fälle bereits; ein genereller Solverdefekt ist nicht belegt. |
| C: Neuer Backendvergleich, insbesondere PhySO | Einheitengeleitete Generierung und gelerntes Sampling könnten anders explorieren. | Direkter Oszillatorbeleg S1, aber Parameterpriors, Kandidatenauswahl, Export, Kosten und eigener voller Verlust müssten neu angeglichen werden. ESR wäre zusätzlich durch Enumeration und lokale Minima begrenzt. | Für den nächsten Schritt zu viele gleichzeitige Änderungen. Kein Paketwechsel aus einer Demonstration ableiten. |
| D: Freie Entwicklung pausieren und Befunde ausarbeiten | Aufwand begrenzen; negative Pilotbefunde, Vorwissensgrenzen und offene Forschungsfragen nachvollziehbar dokumentieren. | Kein neuer Rechenaufwand; ursprüngliche Hintergrundlängenfrage bleibt unbeantwortet. Bekannter Strukturfit bleibt Referenz. Eine Eingrenzung der Abschlussarbeit bedarf einer ausdrücklichen fachlichen Entscheidung. | Bevorzugte Alternative, falls A nicht tragfähig oder sein Aufwand nicht vertretbar ist. |

Zusätzliche Budgetstufen, neue Beobachter, selektives Nachoptimieren des einen
interessanten Baums und eine Ersatzwahl sind keine Optionen dieses Vorschlags.
Auch ein erweitertes Restart- oder Skalierungsprofil wäre ein eigener Faktor,
nicht eine nebenbei vorgenommene Verbesserung von A.

## 6. Abgegrenzter nächster Schritt als Vorschlag

**Jetzt entscheidbar:** Soll ein kontrollierter Entwurf zu A ausgearbeitet
werden oder die freie Entwicklung vorläufig pausieren? Die Empfehlung zu A
beruht auf einer kleinen, erklärbaren Änderung innerhalb des vorhandenen
Suchpfads. Sie beruht ausdrücklich nicht darauf, dass die Literatur ihren
Nutzen für unseren Pilot schon belegt hätte.

### Hypothese und genau eine Intervention

Vorschlag H: Bei sonst unverändertem 100/2-Häufigkeitsprofil erhöht das Verbot
die Zahl erfolgreicher **Originalauswahlen** gegenüber der frischen Kontrolle.
Die Hypothese betrifft die gesamte Suche unter einer geänderten Grammatik;
sie identifiziert keinen isolierten Entstehungs- oder Verwerfungsmechanismus.

Die Regel betrifft alle vier geordneten Paare aus äußerem und innerem
`sin/cos`, auch wenn arithmetische Knoten dazwischenliegen. `exp`, Division,
freie Konstanten, Phasen und Produkte bleiben grundsätzlich möglich. Beispielsweise
bleiben `a+b*t`, `cos(c*t+d)`, `exp(b*t)` und
`(a+b*t)*cos(c*t+d)` ebenso wie ein Ringdown-Produkt zulässig. Weder
Exponentialfaktor noch Produkt, konstante Frequenz, negative Exponentialrate
oder Zahl der Faktoren werden erzwungen. `sin(a*t+sin(b*t))` wäre ausgeschlossen;
damit wird reale Phasenmodulation als darstellbarer Mechanismus eingeschränkt.
Die Regel betrifft Syntax, keine vollständigen algebraischen Äquivalenzklassen.

Die installierte PySR-2.6.0-Quelle dokumentiert `nested_constraints`; der
gelesene [Backendprüfer v2.5.1](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/CheckConstraints.jl)
prüft Verschachtelungen entlang Baumwegen. Im
[aktuellen Projektadapter](../src/ringdown_sr/symbolic.py) ist die Option
ausdrücklich `None`. Das belegt eine vorhandene Schnittstelle, noch keine
implementierte oder technisch geprüfte Projektvariante. Insbesondere ist die
Prüfung fertiger Mutationsvorschläge nicht DSRs Tokenmaskierung bei der Generierung.

### Kontrollen, Umfang und Aufwand

Als diskussionsfähiger Umfang: zwei Arme mit drei bekannten Entwicklungsseeds,
also **sechs frische Zellen**, keine automatische Wiederholung. Der Kontrollarm
verwendet die bisherige unbeschränkte Grammatik; alte Läufe bleiben daneben
historische Referenzen. Beide Arme ohne Populationsbeobachter, mit identischen
Trainingsbits, ursprünglichen Sekunden, Operatoren, Knoten-/Tiefenlimit 20,
Einheitenprüfung, 100/2 einschließlich Newton-Sonderfall, Häufigkeitsschaltern,
Originalauswahl und nachgelagerten Diagnosegates.

Vorgeschlagene nominale Obergrenzen bleiben 200 Suchiterationen, zwei
Populationen zu 32, 50 Zyklen, 600 Sekunden je Worker und 60 Minuten für
die Serie einschließlich Vorbereitung und Prüfung. Das sind Vorschläge zur
Aufwandsbegrenzung, keine gemessene Laufzeitprognose. Gleiche Obergrenzen
garantieren keine gleiche verbrauchte Rechenzeit: abgelehnte Mutationen,
Konstantenanpassung, JIT und Export können unterschiedlich viel kosten.
Der Vergleich wäre daher zunächst eine **Grammatikablation bei gleichem
nominalem Budget**, keine Überlegenheitsstudie bei exakt gleichem Rechenaufwand.
Das Rechenzeitdesign der späteren Kovarianzstudie bleibt separat zu lösen.

Vor einer Ausführung müssten Datenquelle, Seedliste, Paarreihenfolge, wirksame
Optionsdifferenz und Abbruchbehandlung ausdrücklich festgelegt werden. Die
bereits bekannten Seeds sind keine unabhängige Validierung. Gemeinsame Seeds
erzwingen nach der Intervention weder gleiche Zufallspräfixe noch gleiche
Mutationsfolgen; ein bitgleicher Ergebnisvergleich ist hier kein Abnahmekriterium.

Technische Voraussetzungen wären eine native Optionsprüfung beider Profile,
zulässige und unzulässige Gegenbäume einschließlich entfernter Nachfahren,
unveränderte Verlust-/Export-/Auswahlprüfung sowie die erforderliche vollständige
CI eines späteren Implementierungs-PRs. Diese Prüfungen wurden hier weder
implementiert noch gestartet. Keine zusätzliche Suchhistorieninstrumentierung
vorsehen; vorhandene Laufzeit- und Callbackgrößen reichen zur begrenzten
Endergebnisfrage. Der Entwicklungsaufwand liegt vor allem in den gebundenen
Profil-/Verifikationsverträgen, nicht in der Eingabe eines einzelnen Schalters.

### Endpunkte und Entscheidungsregel

Die bisherigen Kurvengrenzen bleiben auf Trainings- und Diagnoseraster
`relative_rms <= 0.001` und `relative_max <= 0.01`. Zusätzlich getrennt
berichten: Strukturerkennung, Parameterstatus, relative L2/RMS-Fehler als
Zahlenwerte auf beiden Rastern, Maximalfehler, Originalbaum, Komplexität und Aufwand.
Kurvenerfolg allein heißt nicht Strukturwiedergewinnung; `not_supported`
bedeutet bei unserem begrenzten Erkenner nicht algebraisch widerlegt.

Mit `C_A` und `C_K` als Zahlen kurvenguter Originalauswahlen der drei Zellen
je Arm wäre folgende **organisatorische** Regel vorab entscheidbar:

| Ergebnis nach vollständiger technischer Verifikation | Vorgeschlagene Konsequenz |
| --- | --- |
| `C_A > C_K` und mindestens eine erfolgreiche A-Originalauswahl mit unterstützter abklingender Struktur und bestandenem Parameterreplay | Positives Entwicklungssignal; ausschließlich einen getrennten Übertragbarkeitsplan auf neuen Entwicklungsfällen erwägen. Keine Erfolgswahrscheinlichkeit, Identifikation oder Hauptversuchsfreigabe. |
| `C_A > C_K`, aber kein solcher Strukturnachweis | Verbesserte Approximation nach festen Gates, freier Ringdown-Strukturanspruch noch offen. Kein automatischer Erkennerumbau oder Nachfit. |
| `C_A <= C_K`, auch bei kleineren kontinuierlichen Fehlern | Hypothese dieses begrenzten Vergleichs nicht gestützt; A nicht als neues Profil übernehmen. Pause beziehungsweise ausdrücklich neue Abwägung, keine zweite Restriktionsstufe. |
| Nur ungewählte Kandidaten gut oder alle sechs Zellen ohne Erfolg | Kein Ersatz der Originalauswahl. Negative oder begrenzte Befunde vollständig sichern; kein zusätzlicher Seed oder automatischer Neustart. |
| Abbruch, verletzte Quellen-/Profilbindung oder numerisch unbestimmtes Ergebnis | Teilstand und Gründe erhalten; kein positives Gesamturteil und kein Ersatzlauf ohne neuen Beschluss. |

Die Schwelle „mindestens eine“ ist ein bewusst schwaches Entwicklungssignal,
kein statistisch begründetes Erfolgsgate für eine Leistungsstudie. Sie und
der gesamte Umfang oben sind Vorschläge. Eine Methode wird durch diesen
Text weder angenommen noch eingefroren. `physical_identification` bleibt
`not_assessed`; insbesondere behebt die Regel den Alias-Blindfleck bei `8*fs`
nicht. Der alte Lauf `trajectory-manjaro-001` bleibt `incomplete / failed`.

## 7. Offene Entscheidung

Vor einer Umsetzung ist über den allgemeinen Grammatikprior und den begrenzten
Vergleich zu entscheiden. Bei Ablehnung oder fehlendem Arbeitsbudget wird
Option D empfohlen. Der feste Strukturfit darf in beiden Fällen als Referenz
weiter dokumentiert werden; eine Umstellung des Forschungsziels auf diesen Fit
ist kein Bestandteil dieser Literaturabwägung.

Unabhängig davon bleiben spätere wissenschaftliche Auswahl, Hintergrunddesign,
Übertragbarkeit und Bewertungskriterien im Hauptversuchsplan zu klären.
Der offene Audit des früheren freien Budgetarchivs ist weiterhin offen; er
wurde hier nicht als Voraussetzung für eine erneute numerische Prüfung benutzt.
