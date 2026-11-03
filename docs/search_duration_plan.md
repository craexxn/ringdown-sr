# Methodenplan: Größeres äußeres Suchbudget bei zwei Grammatiken

Angenommen am 03.11.2026: Suchaufwand erhöhen und erst anhand der Ergebnisse
über weitere Tests entscheiden. Die Gesamtgrenze von zwei Stunden wurde
ausdrücklich gewählt. Vorbereitung und technische Prüfung erfolgen hier;
die einmalige wissenschaftliche Serie bleibt für Manjaro vorgesehen.
Dieser neue Plan wird vor Implementierung durch Commit und SHA-256 gebunden.
Alle sieben bisherigen Laufzeitpläne und Originalbefunde bleiben unverändert.

## 1. Begründung und begrenzte Fragestellung

Grundlage sind der [Originalarchiv-Audit](trigonometric_grammar_results_manjaro_001.md)
am Dokumentations-Head `e6472bba72b672642987d3ffd55c3bd59694ac05` und die
[gezielte Literaturauswertung](search_duration_literature.md). Der bisherige
Vergleich bleibt C_K = C_A = 0/3. Ein besserer Einzelkandidat ist eine gute
Approximation mit abweichender Amplitudenhülle, kein positiver Strukturbeleg.

Neue Frage: Verbessert ein zehnfaches äußeres Suchbudget bei unverändertem
100/2-Profil die Originalauswahlen innerhalb der jeweiligen Grammatik?
Der Grammatikunterschied wird bei beiden Budgets getrennt betrachtet.
Es gibt keine vorab behauptete Richtung der Wechselwirkung und kein Poolen
zu einer allgemeinen Erfolgswahrscheinlichkeit. Budgetänderung und Grammatik
sind zwei ausdrücklich gekreuzte Faktoren, keine behauptete Ein-Faktor-Studie.

Die Literatur liefert Ressourcenbeispiele und Gründe für eine Budgetprüfung,
aber keinen optimalen Wert für diesen Ringdown. 200/2.000 Iterationen und fünf
Seeds sind ein abgegrenzter Entwicklungsumfang. Beide Referenzbudgets werden
frisch ausgeführt; alte Läufe ersetzen keine Zelle. Neue Seeds machen das
bekannte Entwicklungsdatum nicht zu einer unabhängigen Leistungsvalidierung.

## 2. Daten und unveränderte Verfahren

Die gleichen 128 Trainingswerte und 889 inneren Achtelpunkte stammen aus
`representation-manjaro-001.tar.gz`, SHA-256
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Der Leser prüft Archividentität und Float64-Bits; kein Archivcode wird geladen.
Training `t_j=j/4096 s`, `j=0,...,127`; bekanntes Signal A=1, f=250 Hz,
tau=0,008 s, phi=0. Freie Worker erhalten nur Trainingszeiten und Beobachtungen,
`X_units=["s"]`, `y_units="1"`, `covariance=None`. Wahrheit, Diagnosepunkte
und Referenzbäume dürfen weder Suche noch Konstantenfit oder Auswahl erreichen.

K ist unbeschränkt (`nested_constraints=None`). A verbietet weiterhin alle
vier direkten/entfernten `sin/cos`-Nachfahrenpaare; Geschwister sind erlaubt.
K bleibt Referenz, A bleibt untersuchte Alternative. Kein Produktbaum,
Exponentialfaktor, Frequenzwert oder Vorzeichen wird vorgegeben.

Alle Zellen verwenden `+,-,*,/,exp,sin,cos`, Einheitskomplexitäten, maxsize und
effektives maxdepth 20, Parsimony 0, beide Häufigkeitsschalter True,
zwei Populationen zu 32, 50 Zyklen je Iteration. Konstantenoptimierung
100 Schritte und zwei zusätzliche Neustarts, bisheriger Newton-Sonderfall
und BFGS/Backtracking, Toleranzen und lokale Auswertungsgrenzen unverändert.
Float64, Sekunden, seriell/deterministisch, warm_start=False, guesses=None,
dimensionless_constants_only=False, Größenaufwärmung 0. Keine Templates,
neuen Tracing-Plugins, Skalierungen, Solver oder Änderungen allgemeiner Defaults.

Pins: Python 3.12.14, Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1.
Haswell und Threadlimit 1 für OpenBLAS/OMP/MKL/NumExpr nur für diesen Pfad.
Proxy, TLS und Pins bleiben unverändert. Keine parallelen wissenschaftlichen
Worker; Hardware-/Umgebungsdaten und geladene Pools werden aufgezeichnet.

## 3. Umfang, Reihenfolge und Ressourcen

Vier Bedingungen: K200, A200, K2000, A2000. Seeds 20261103, 20261104,
20261105, 20261106 und 20261107 sind vor allen neuen Suchen festgelegt.
Jede Zelle ist ein frischer Prozess ohne Wiederaufnahme eines kurzen Laufs.
Gemeinsame Seeds garantieren weder gleiche Mutationen noch gleiche RNG-Präfixe
zwischen Grammatiken/Budgets. Verdeckte Zustandsidentität wird nicht behauptet.

| Seed | Zellen | Reihenfolge |
| --- | --- | --- |
| 20261103 | 1–4 | K200, A200, A2000, K2000 |
| 20261104 | 5–8 | A200, K2000, K200, A2000 |
| 20261105 | 9–12 | K2000, A2000, A200, K200 |
| 20261106 | 13–16 | A2000, K200, K2000, A200 |
| 20261107 | 17–20 | K200, A200, A2000, K2000 |

Die ersten vier Blöcke gleichen Positionen und unmittelbar aufeinanderfolgende
Bedingungen aus; der fünfte wiederholt den ersten. Die verbleibende
2:1-Positionsasymmetrie ist ausdrücklich Teil des Designs.

Genau 20 frische Zellen. **600 Sekunden je Suchworker**, **7.200 Sekunden
insgesamt** einschließlich Vorprüfungen, Elternarbeit, Export und Finalisierung.
Nominale Budgets sind 200 beziehungsweise 2.000 äußere Suchiterationen;
Callbacks zählen keine unabhängigen Formeln. Tatsächliche Zell-/Fitzeiten,
Setup und bestehende Callbackzahlen getrennt berichten. Kein gemessener
Laufzeitfaktor wird vorausgesetzt; technische CI zählt nicht zum Serienbudget.

Fehler, Ressourcenabbruch, SIGINT oder SIGTERM stoppen die eigenen
Workerprozessgruppen und erhalten Teilstände. Keine automatische Wiederholung,
Ersatzseeds, Verlängerung, Wiederaufnahme oder Auswahl eines Teilvergleichs.
Eine gültige schlechte Formel bleibt ein Ergebnis. Bei unvollständiger Serie
bleiben alle Gruppenaggregate, Paardifferenzen und Gesamtentscheidungen gesperrt.

## 4. Auswahl, Endpunkte und Berichte

Unveränderte Auswahl: kleinste gewöhnliche Trainings-MSE, dann Komplexität,
dann erster Originalindex. Vollständige Fronten mit Reihenfolge, Auswahlindex,
Originalbäumen, Vorhersagen und Residuen erhalten; kein Reranking oder Nachfit.
Baum-/Vorhersage-/Residuen-/MSE-Widersprüche stoppen die Serie.
Alle exportierten A-Kandidaten werden zusätzlich gegen die Grammatik geprüft.

Primär je Grammatik die Zahl C_g,200 und C_g,2000 der fünf Originalauswahlen,
die auf Training und Achtelraster jeweils RMS ≤ 0,001 und Max ≤ 0,01 erreichen.
Budgetdifferenz Delta_g = C_g,2000 - C_g,200 getrennt für K und A.
Zusätzlich C_A,b - C_K,b je Budget und die deskriptive Differenz
Delta_A - Delta_K berichten; keine Signifikanz- oder Überlegenheitsbehauptung.

Für jeden gepaarten Seed beide Ausgangswerte und 2.000-minus-200-Differenzen
aller Fehler-/MSE-Werte je Grammatik; A-minus-K je Budget. Vier Gruppen mit
Minima/Medianen/Maxima und endlichen/geplanten Nennern. Alle vier
Erfolgswechsel zählen, Parameter-/Strukturstatus getrennt; Unverfügbares
bleibt null mit Grund. Alle 20 Originalformeln, Komplexitäten und Kosten zeigen.
Gute ungewählte Kandidaten separat zählen, nie als Auswahlerfolg verwenden.

Parametergrenzen bleiben Frequenz 1e-3, Abklingzeit 1e-2, Amplitude/komplexe
Amplitude 1e-2 samt bisherigen Struktur-, Abkling-, Alias- und Replaygates.
`not_supported` ist kein algebraischer Unmöglichkeitsbeweis;
`physical_identification` bleibt `not_assessed`. Der Blindfleck bei `8*fs`
bleibt bestehen. Keine neuen Diagnosepunkte zur nachträglichen Auswahl.

## 5. Technische Voraussetzung und Herkunft

Isolierter neuer Serienpfad mit manifestierten Quellen, Plan- und Eingabebits;
numerische Zielgröße und native Grammatikprüfung werden unverändert delegiert.
Zehn native Optionsobjekte (fünf Seeds je Grammatik) absolut prüfen. Die
Iterationszahl ist kein Feld dieser nativen Optionsobjekte: zusätzlich alle
20 Pythonprofile prüfen und den tatsächlichen PySR-Aufruf von `equation_search`
an der Python/Julia-Grenze auf genau das angeforderte Budget prüfen und sichern.
Der transparente Aufrufprüfer verändert weder Argumente noch Ergebnisse
und erzeugt keine Suchhistorie. Warmstart, fremde Gewichte oder zweiter Aufruf
sind dort ausgeschlossen. Kein Referenzzustand gelangt an freie Worker.

Native Syntax-/Einheiten-/Seed-/Pluginprüfungen und feste 250-/4346-/33018-Hz-
Referenzen bleiben erhalten. Technische Integration ausschließlich auf dem
separaten Achtpunkt-Signal `y=1+t`: beide Grammatiken bei zwei und drei
Suchiterationen sowie wiederholte unbeschränkte Zweierkontrolle. Deren Front
muss identisch bleiben; die durchgereichten Budgets müssen absolut stimmen.
Keine wissenschaftliche 200-/2.000-Zelle als technischer Test.

Fehler- und Gegenfalltests müssen falsche Budgets/Profile/Seeds bereits in
der ersten Zelle, geänderte Quellen/verbrauchte Dateien, Ersatzwahl,
unvollständige 20-Zellen-Auswertungen, Zeitüberschreitung bei Elternarbeit
und fehlerhafte Abschlussveröffentlichung abfangen. Vor/nach Verbrauch und
abschließend gegen ursprüngliche Anker prüfen; spätere Neuhashung ersetzt
sie nicht. Positive Berichte zuletzt veröffentlichen und bei Abschlussfehlern
widerrufen. Vollständige technische CI am dokumentierten sauberen Stand
vor einmaliger Manjaro-Ausführung; kein eigenständiger Merge.

## 6. Entscheidungsregel und mögliche Folgetests

Voraussetzung ist eine vollständig verifizierte Serie. Budgetwirkung innerhalb
jeder Grammatik getrennt einordnen:

| Ergebnis | Folgerung |
| --- | --- |
| Delta_g > 0 und mindestens ein 0→1-Wechsel mit unterstützter abklingender Struktur und bestandenem Parameterreplay derselben hohen Originalauswahl | Positives Entwicklungssignal für höheres Budget in dieser Grammatik; getrennten Übertragbarkeitsplan erwägen. |
| Delta_g > 0 ohne diesen Strukturnachweis | Mehr erfolgreiche Kurvenapproximationen; freier Strukturanspruch offen. |
| Delta_g ≤ 0, auch bei kleineren Einzel-/Medianfehlern | Kein Mehrerfolg am primären Endpunkt; kontinuierliche Änderungen deskriptiv sichern. |
| Beide Grammatiken ohne Erfolg | Budgetstufe nicht als Lösung bestätigt; anhand der exportierten Strukturen gezielte Diagnose von Darstellung oder Konstantenstarts erwägen. |
| Unvollständig/Verifikation fehlgeschlagen | Kein abgeschlossener Vergleich; Teilstand und Ursache sichern. |

Ein Strukturbeleg eines bereits bei 200 erfolgreichen Seeds begründet nicht
den erforderlichen neuen 0→1-Strukturgewinn. Gegensätzliche Budgetwirkungen
bleiben sichtbar; weder günstigste Grammatik noch bester Seed werden gepoolt.
Auch fünf neue Seeds am bekannten Signal sind keine Hauptversuchsfreigabe.

Der Auftrag umfasst diese Budgetprüfung und die anschließende begründete
Einordnung weiterer Tests. Er startet keine automatische Folge von Budgets,
Restriktionen, Nachfits oder Backendwechseln. Konkrete Folgetests benötigen
eine aus den Ergebnissen abgeleitete, vor Ausführung festgelegte Fragestellung.
Der bisherige Grammatikbefund bleibt unverändert negativ; freie Formelfindung
und die spätere Hintergrund-/Kovarianzfrage des Exposés bleiben Forschungsziele.
