# Entscheidungsgrundlage: nächster Schritt nach der rauschfreien Kontrollserie

Stand: 30.10.2026. Vorbereitung eines KI-basierten Methodenreviews.
**Offene Optionen und vorläufige Empfehlung; kein beschlossener Versuchsplan.**
Die abgeschlossene Serie und ihre eingefrorenen Vorgaben bleiben unverändert.

## Was jetzt zu entscheiden ist

Der technische Kontrollpfad funktioniert und die letzte Serie ist vollständig
ausgewertet. Offen ist, welcher nächste Schritt den größten Erkenntnisgewinn
für die Ringdown-Rekonstruktion und das spätere Ziel der Rauschgewichtung bietet:

1. Zuerst eine konkrete Ursache mit vorgegebenen Strukturen untersuchen oder
   direkt einen neuen kontrollierten freien Suchversuch planen?
2. Welche Rolle dürfen die günstigeren Häufigkeitsschalter dabei erhalten:
   Entwicklungskandidat, Vergleichsarm oder bereits festgelegtes Suchprofil?
3. Wie viel Ringdown-Vorwissen ist künftig zulässig? Eine feste Struktur als
   Diagnose und eine dauerhaft eingeschränkte Suchgrammatik haben verschiedene
   Forschungsansprüche und müssen getrennt beschlossen werden.
4. Welche Evidenz wird vor weiteren Signalen, Rauschen und Gewichtungsvergleichen
   verlangt? Wann wird die breite freie Suche stattdessen pausiert oder eingegrenzt?

Eine Erweiterung des Strukturerkenners allein beseitigt den aktuellen Befund
nicht: Bereits die Kurven aller exportierten Kandidaten verfehlen die Grenzen.

## Verbindliche Bezüge und Lesereihenfolge

Repository: `craexxn/ringdown-sr`.

| Rolle | Bezugsstand |
| --- | --- |
| Aktueller Ergebnis-PR | [PR #41](https://github.com/craexxn/ringdown-sr/pull/41), beim Beginn dieser Vorbereitung offen |
| Geprüfter Ergebnisstand vor dieser Reviewvorbereitung | `73e1c6748fb6683b99336d81271f332e60034d9f` |
| Vergleichsbasis dieses Ergebnisstands | `97672ed9b14b81ca90663dc178072b515ee252bc` auf `main`, Merge von PR #40 |
| Wissenschaftlicher Ausführungscommit | `4057caaffd9c4de5791ded14431c6e289db75b73`, Merge von PR #39 |
| Technisch und auf Methodentreue geprüfter Implementierungshead | `cfe44bfb84baef9238f52609ba1030eaa4416ed7`, gleicher Dateibaum wie der Ausführungscommit |
| Basis des Implementierungsreviews | `909942d3f3910ea20df1703dd12421abe4867a4e` |

Der aktuelle PR-Head kann diese reine Dokumentationsvorbereitung zusätzlich
enthalten. Beim Review aktuellen Head und Basis vollständig nennen und die
oben verankerten Ergebnisse von späteren Änderungen unterscheiden.

Pflichtlektüre:

1. [README](../README.md), [AGENTS.md](../AGENTS.md) und
   [Fortsetzungsdatei](representation_implementation_status.md).
2. [Letzte Serie mit Originalarchiv-Audit und allen neun Auswahlen](representation_control_results_manjaro_001.md).
3. [Eingefrorener letzter Methodenplan](search_representation_plan.md), besonders
   Fragestellung, Suchbedingungen, Erfolgskriterien und Grenze des nächsten Schritts.
4. [Bisherige rauschfreie Budgetkontrolle](noiseless_control_results_manjaro_001.md)
   und [ihr eingefrorener Plan](noiseless_control_plan.md). Der ältere Befund
   beruht hier auf übermittelten Auszügen; der neue auf dem vollständigen Archiv.
5. Für die Optimiererfrage: [Konstantenoptimierung](constant_optimization.md),
   [tatsächliche Backendtests](../julia/test/constant_optimization.jl),
   [Ringdown-Verlustreferenz](../julia/test/runtests.jl),
   [aktuelle Suchparameter](../src/ringdown_sr/symbolic.py) und
   [klassischer Referenzfit](reference_fit.md).
6. Für den Forschungsanspruch: [SR-Methodenentwurf](symbolic_regression_method_plan.md),
   [Parameterinterpretation](parameter_interpretation_plan.md) und
   [Wiederholbarkeit/Robustheit](reproducibility_decisions.md).

Historische Statusabsätze älterer Bausteindokumente an README und aktuellem
Code abgleichen; sie ersetzen den heutigen Implementierungsstand nicht.

Originalarchiv: `representation-manjaro-001.tar.gz`, SHA-256
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Wenn es im Reviewchat nicht vorliegt, gilt der Befund als dokumentierte
Auditgrundlage; eine erneute eigene Originalartefaktprüfung darf dann nicht
behauptet werden. Für das Methodenreview ist kein routinemäßiger Wiederholungsaudit nötig.

## Ergebnislage, die das Review erklären muss

Ein bekanntes rauschfreies Signal: `A=1`, `f=250 Hz`, `tau=0,008 s`, `phi=0`;
128 Trainingswerte bei 4096 Hz und 889 innere Achtelpunkte zur Diagnose.
Die drei bereits bekannten Entwicklungsseeds sind 20261020, 20261021 und
20261022. Je Bedingung drei frische Suchen mit 200 Iterationen, zwei Populationen
zu 32 Individuen und 50 Zyklen je Iteration, zyklisch geordnet.

Operatoren `+,-,*,/,exp,sin,cos`, Knotenlimit 20, Float64, serielle deterministische
Ausführung und die bisherigen Einheitenregeln gelten für alle Bedingungen.
Konstantenanpassung: konfiguriertes BFGS mit 20 Iterationen und zwei Neustarts;
der Backend-Sonderpfad für eine einzige Konstante verwendet Newton.

- `baseline`: frische gewöhnliche Suche; beide Häufigkeitsschalter aus.
- `time_stretch`: ausschließlich `u=32*t`, beide Koordinaten Sekunden;
  Schalter aus, vollständige physikalische Vorhersage `q(32*t)`.
- `complexity_frequency`: ursprüngliche Zeit, beide Schalter gemeinsam an.
  Sie betreffen Häufigkeiten von Formelkomplexitäten, nicht die Signalfrequenz.
  Ihre Einzelwirkungen und eine Kombination mit Zeitstreckung wurden nicht untersucht.

Mediane der drei Originalauswahlen je Bedingung; jeweils 3/3 endlich:

| Bedingung | Trainings-MSE | Training relativer RMS | Zwischenpunkte relativer RMS | Zwischenpunkte relativer Maximalfehler |
| --- | --- | --- | --- | --- |
| baseline | 0,0682956796 | 0,999807911 | 1,000107741 | 0,994851497 |
| time_stretch | 0,0388004610 | 0,753595673 | 0,774250129 | 0,994851497 |
| complexity_frequency | 0,00251500024 | 0,191862001 | 0,197413154 | 0,118497837 |

Seedbezogene Kernaussagen:

- Häufigkeitsschalter senken die Trainings-MSE gegenüber der frischen
  Baseline um 89,7 %, 96,3 % und 97,0 %. Auch die berichteten relativen
  RMS-/Maximalfehler beider Raster sinken bei allen drei Seeds.
- Zeitstreckung senkt die Trainings-MSE bei den ersten beiden Seeds um
  36,4 % und 64,3 %. Bei Seed 20261021 steigt gleichzeitig der
  Zwischenpunkte-Maximalfehler auf 1,627406740. Beim dritten Seed bleibt
  die Trainings-MSE gleich; einzelne Fehlerdifferenzen um 1e-12 sind kein
  substanzieller Fortschritt.
- Keiner der 57 Frontkandidaten erfüllt auf beiden Rastern die Vorgaben
  `relative_rms <= 0,001` und `relative_max <= 0,01`.
  Alle Strukturen sind `not_supported`; alle Parameterbefunde und die
  physikalische Identifikation bleiben `not_assessed`.
- Erste Strukturgründe: 52-mal `exponential_factor_count`, fünfmal
  `cosine_factor_count`. Das sind Erkennerbefunde, kein populationsweiter
  Nachweis, wann bestimmte Strukturen erzeugt oder verworfen wurden.

Aufgezeichneter Aufwand, jeweils Summe über drei Zellen:

| Bedingung | Frontkandidaten | Fit-Callbackaufrufe | Fitzeit einschließlich JIT und Python-Exporten |
| --- | --- | --- | --- |
| baseline | 11 | 1.506.775 | 95,891 s |
| time_stretch | 23 | 2.219.722 | 113,614 s |
| complexity_frequency | 23 | 984.908 | 96,553 s |

Diese Zähler enthalten Optimiereraufrufe und zählen keine verschiedenen Bäume.
Gemeinsame Seeds sind keine identischen Suchpräfixe oder Rechenkosten.
Die Fronten enthalten weder alle besuchten Bäume noch einen Verlauf der Populationen.

Die frühere rauschfreie Budgetserie mit 10/50/200 Iterationen hatte 28
Frontkandidaten und ebenfalls keinen bestandenen Kurvenmarker. Beide Serien
sind Entwicklungsbefunde; sie werden nicht zu unabhängigen Wiederholungen gepoolt.

## Gesichert, offen und nicht ableitbar

| Aussage | Einordnung |
| --- | --- |
| Die übermittelten Artefakte, Optionen, Seeds, Originalauswahlen und berichteten Zahlen sind konsistent. | Für die letzte Serie durch den unabhängigen Audit belegt. |
| Eine Referenzstruktur ist innerhalb der Grammatik und des Größenlimits zulässig und hat sehr kleinen Verlust. | Native feste Referenztests bestanden; der spezielle Phase-null-Referenzbaum hat 11 Knoten. |
| Die freie Suche hat eine gute Ringdown-Formel erreicht. | Nicht belegt; alle 57 Kandidaten verfehlen schon die Kurvengrenzen. |
| Die Konstantenoptimierung ist generell defekt oder generell ausreichend. | Beides nicht belegt; siehe konkrete Prüfgrenze unten. |
| Das Profil mit Häufigkeitsschaltern ist auf weiteren Signalen überlegen. | Nicht geprüft. Drei bekannte Seeds an einem bekannten Signal sind keine unabhängige Validierung. |
| Die Ursache ist fehlende Populationsvielfalt oder zu wenig Suchbudget. | Hypothesen; Fronten und Callbackzahlen belegen das nicht. |
| Der Erkenner ist die alleinige Ursache des negativen Befunds. | Erklärt die schon zu großen Kurvenfehler nicht. Seine Unterstützung bleibt trotzdem begrenzt. |
| Physikalische Frequenz und Dämpfung sind aus den gefundenen Formeln identifiziert. | Nicht beurteilt; keine positiven Parameterbefunde. Der Alias-Blindfleck bei `8*fs` bleibt bestehen. |

Konkrete offene Prüfgrenze: Die bestehenden Tests in
`julia/test/constant_optimization.jl` prüfen tatsächliches Newton/BFGS an
konstanten und linearen, in den Parametern konvex-quadratischen Modellen.
Das technische Prüfbudget ist dort 100 Optimiereriterationen ohne zufällige
Neustarts. Die Suchläufe verwenden dagegen 20 Iterationen und zwei Neustarts.
Die festen Ringdown-Verlustreferenzen prüfen Zulässigkeit und Verlust eines
vorgegebenen, bereits passenden Baums; sie optimieren nicht dessen mehrere
nichtlinear gekoppelte Konstanten von anderen Startwerten aus.

Daraus folgt eine offene Frage nach lokaler Anpassung und Einzugsgebieten für
eine Ringdown-Struktur, kein Nachweis eines Optimiererfehlers. Auch ein neuer
positiver Test bei fest vorgegebener Struktur würde noch nicht erklären, ob
und wann die freie Suche diese Struktur erreicht und überlebt.

Der bestehende klassische Referenzfit kennt die Form und verwendet separable
Least Squares mit analytischer Anpassung der linearen Koeffizienten und
nichtlinearer Suche über Frequenz/Abklingzeit. Er ist eine privilegierte
Referenz und kein gleichartiger BFGS- oder freier SR-Lauf.

## Optionen für die nächste Methodenentscheidung

Alle Zeilen sind Vorschläge für das Review; keine davon ist hier freigegeben.

| Option | Welche Frage sie beantworten könnte | Zentrale Grenze / notwendige Festlegung |
| --- | --- | --- |
| A: Begrenzte Diagnose der Konstantenoptimierung an fest vorgegebenen Ringdown-Strukturen | Kann der tatsächlich genutzte Callback-/Optimiererpfad passende Konstanten unter vorher festgelegten Starts und Budgets anpassen? Was ändern Koordinaten oder Parameterdarstellung daran? | Struktur ist privilegiert vorgegeben; Starts, Varianten, Budgets und Bewertungsregeln müssen vorab feststehen. Keine Übertragung wahrer Strukturen/Startwerte in die freie Suche. |
| B: Neuer kontrollierter freier Suchversuch oder gezielte Suchverlaufsdiagnose | Welche vorab benannte Intervention verbessert die freie Rekonstruktion oder grenzt die Strukturentstehung/-verwerfung ein? | Ein klarer Faktor und begrenzter Umfang; mehr Iterationen, Populationen oder Tracing sind neue Bedingungen. Tracing kann Aufwand und Suchbedingung ändern. |
| C: Übertragbarkeit des günstigeren Profils auf weitere Signale/Seeds prüfen | Bleibt die beobachtete Fehlerverbesserung außerhalb des bereits bekannten Falls bestehen? | Bisher kein einziger erfolgreicher Kurvenmarker; Nutzen dieses Schritts gegenüber A/B begründen. Vorab getrennte Entwicklungs- und Validierungsrollen, keine nachträgliche Auswahl günstiger Fälle. |
| D: Forschungsanspruch ausdrücklich eingrenzen, etwa durch eine strukturierte Grammatik oder ein Template | Wird eine kontrollierte, rauschgewichtete Suche innerhalb einer engeren Modellklasse untersucht? | Das ändert den Anspruch freier Formelentdeckung und muss ausdrücklich beschlossen und mit den bekannten klassischen Referenzen abgegrenzt werden. |
| E: Breite freie Rekonstruktion vorerst pausieren oder beenden | Ist ihr zusätzlicher Aufwand für das konkrete Forschungsziel noch gerechtfertigt? Welche vorhandenen Bausteine tragen einen sinnvoll begrenzten weiteren Vergleich? | Einen begrenzten negativen Entwicklungsbefund nicht als allgemeine Unmöglichkeit ausgeben; neue Forschungsfrage und spätere Erfolgskriterien gegebenenfalls getrennt beschließen. |

**Vorläufige Empfehlung zur kritischen Prüfung:** Zuerst den Erkenntnisgewinn
von A gegenüber B bewerten. Die neue Serie zeigt einen Einfluss des Suchprofils,
trennt aber lokale Konstantenanpassung und strukturelle Suche nicht. Eine
kleine vorab begrenzte Diagnose könnte diese Prüfgrenze verkleinern, bevor
weitere freie Suchen geplant werden. Das Review darf diese Reihenfolge
verwerfen, wenn eine Alternative mit klarerem Erkenntnisgewinn begründet ist.
Es wird kein Defekt behauptet und kein neues numerisches Budget festgelegt.

Zusätzlich entscheiden:

- Darf `complexity_frequency` als Kandidat für weitere Entwicklung dienen,
  und welcher Vergleichsarm bleibt erforderlich? Der Befund allein bestimmt
  kein Produktionsprofil.
- Wird Zeitstreckung für weitere freie Suchen vorerst zurückgestellt oder
  nur für eine konkrete Hypothese weiter untersucht? Der Mischbefund der
  freien Suche beweist keine grundsätzliche Untauglichkeit der Koordinate.
- Welche beobachtbaren Ergebnisse führen nach dem nächsten begrenzten Schritt
  zu Fortsetzen, Methodenänderung oder Stopp? Ein gutes festes Strukturfit
  und ein Erfolg freier Suche müssen unterschiedliche Rollen behalten.
- Ist ein anschließender Rausch-/Gewichtungsvergleich schon aussagekräftig,
  und für welchen genau definierten Anspruch? Dafür ein fachliches Gate
  begründen, statt eine allgemeine Pflicht zu fehlerfreier Rekonstruktion
  jeder denkbaren Formel zu behaupten.

## Anforderungen an einen erst noch zu beschließenden nächsten Plan

Das Review soll für genau einen empfohlenen nächsten Schritt einen überprüfbaren
Entwurf liefern: Frage, zu unterscheidende Hypothesen, Kontrollbedingungen,
zulässiges Vorwissen, Datenrollen, numerischer Pfad, Auswertung und Abbruch.

Bei vorgeschlagenen Versuchen sind Anzahl/Starts/Seeds, Such- und
Optimiererbudgets, Wiederholungen, Koordinaten und Änderungen gegenüber dem
Bestand ausdrücklich vorab zu benennen und zu begründen. Wo die Evidenz keine
konkrete Zahl trägt, den Entscheidungsbedarf offenlegen. Keine scheinbar
wissenschaftlich hergeleiteten Zahlen erfinden und keine stille Übernahme
oder Erhöhung des bisherigen Budgets.

Erfolg oder Scheitern muss eine Konsequenz für die folgende Entscheidung
haben; ein unbegrenztes "weiter tunen" ist kein Abbruchkriterium. Aufwand
nur unter Bezug auf die aufgezeichneten Zeiten/Zähler abschätzen, nicht als
proportional zum Iterationsbudget oder hardwareunabhängig zusichern.

Die alten Daten, Pläne, Originalauswahlen und Ergebnisgrenzen bleiben eingefroren.
Neue Kriterien oder engeres Vorwissen dürfen alte Misserfolge nicht nachträglich
als Erfolge umetikettieren. Zusätzliche Bäume in einer Diagnose dürfen nicht
unbemerkt als freie Rekonstruktion verbucht werden. Eine spätere Leistungsstudie
benötigt ein gesondertes Design für unabhängige Signal-/Rauschfälle und Auswahl.

## Kopierbarer Review-Prompt

```text
Führe ein KI-basiertes Methodenreview zur nächsten Entscheidung im Ringdown-SR-Piloten durch. Liefere eine begründete Entscheidungsvorlage; implementiere und starte nichts.

Repository: https://github.com/craexxn/ringdown-sr
Ergebnis-PR: https://github.com/craexxn/ringdown-sr/pull/41
Verankerter Ergebnisstand: 73e1c6748fb6683b99336d81271f332e60034d9f
Vergleichsbasis dieses Ergebnisstands: 97672ed9b14b81ca90663dc178072b515ee252bc
Wissenschaftlicher Ausführungscommit: 4057caaffd9c4de5791ded14431c6e289db75b73
Implementierungsreview: Head cfe44bfb84baef9238f52609ba1030eaa4416ed7 gegen 909942d3f3910ea20df1703dd12421abe4867a4e, ohne korrekturbedürftige Befunde zur Methodentreue. Ausführungscommit und Implementierungshead haben denselben Dateibaum.

Prüfe zuerst den aktuellen Repository-/PR-Stand. Nenne PR, vollständigen gelesenen Head, Basis und Prüfumfang. Falls PR #41 weitergeführt oder gemergt wurde, trenne das von den verankerten Ergebnissen. Lies AGENTS.md und README sowie docs/representation_next_step_review.md als Entscheidungsgrundlage. Dieses Dokument enthält offene Optionen, keinen beschlossenen neuen Versuchsplan.

Pflichtquellen:
- docs/representation_control_results_manjaro_001.md am Ergebnisstand: https://github.com/craexxn/ringdown-sr/blob/73e1c6748fb6683b99336d81271f332e60034d9f/docs/representation_control_results_manjaro_001.md
- docs/search_representation_plan.md, insbesondere Abschnitt 7: https://github.com/craexxn/ringdown-sr/blob/4057caaffd9c4de5791ded14431c6e289db75b73/docs/search_representation_plan.md
- docs/noiseless_control_results_manjaro_001.md und docs/noiseless_control_plan.md für die ältere Budgetkontrolle.
- docs/constant_optimization.md und julia/test/constant_optimization.jl; src/ringdown_sr/symbolic.py; julia/test/runtests.jl; docs/reference_fit.md für tatsächlich abgedeckte Optimierer-/Referenzprüfungen.
- docs/symbolic_regression_method_plan.md, docs/parameter_interpretation_plan.md und docs/reproducibility_decisions.md für Forschungsanspruch, Datenrollen, Aliase und Robustheit.

Letzte Ergebnisse, die du kritisch einordnen sollst:
Ein bekanntes rauschfreies Signal mit A=1, f=250 Hz, tau=0,008 s, phi=0; 128 Trainingswerte bei 4096 Hz, 889 innere Achtelpunkte. Je Bedingung drei frische Läufe mit den bekannten Entwicklungsseeds 20261020/21/22 und 200 Iterationen, zwei Populationen zu 32 Individuen, 50 Zyklen. Operatoren +,-,*,/,exp,sin,cos, Knotenlimit 20, Float64, serial/deterministisch, Haswell/Threadlimit 1, konfigurierte Konstantenanpassung BFGS 20 Iterationen und zwei Neustarts, Newton-Sonderpfad bei einer Konstanten.
Bedingungen: frische Baseline; ausschließlich u=32*t bei weiter Sekunden; ausschließlich beide Komplexitätshäufigkeitsschalter gemeinsam an. Kein kombinierter Arm, keine Templates oder Wahrheitsstartwerte. Die Häufigkeitsschalter erhalten keine physikalische Signalfrequenz.
Mediane (Trainings-MSE / relativer RMS auf Zwischenpunkten): Baseline 0,0682956796 / 1,000107741; Zeitstreckung 0,0388004610 / 0,774250129; Häufigkeitsschalter 0,00251500024 / 0,197413154. Alle Nenner 3/3 endlich.
Häufigkeitsschalter senken die Trainings-MSE je Seed um 89,7 %, 96,3 %, 97,0 % und verbessern alle berichteten RMS-/Maximalfehler gegenüber der jeweiligen Baseline. Zeitstreckung senkt die Trainings-MSE bei zwei Seeds um 36,4 % und 64,3 %, erzeugt aber beim zweiten Seed einen Zwischenpunkte-Maximalfehler von 1,627406740; beim dritten bleibt eine numerisch gleiche Konstante.
Alle neun Zellen completed, Abschlussprüfung passed. Alle 57 Kandidaten außerhalb der festen Grenzen RMS<=0,001 und Max<=0,01 auf beiden Rastern. Alle Strukturen not_supported (52-mal erster Grund exponential_factor_count, fünfmal cosine_factor_count). Parameter und physical_identification not_assessed. 57 Frontkandidaten sind keine 57 unabhängigen Suchläufe.
Vollständiges Originalarchiv unabhängig nachgerechnet: SHA-256 a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db; 218 Manifestdateien, 219 Dateien insgesamt, 41 Quellprüfsummen sowie alle Bäume, Residuen, Auswahlen, Statistiken und Seed-Differenzen bestätigt. Fehlt dir das Originalarchiv, kennzeichne dies; behaupte keinen eigenen Wiederholungsaudit. Ein erneuter vollständiger Audit, eine erneute CI und ein weiteres Implementierungsreview sind nicht der Auftrag.

Entscheidungsfragen:
1. Was belegt dieser Befund für Kurvenapproximation, freie Strukturentdeckung und physikalische Parameter jeweils? Welche Ursachenerklärungen bleiben offen?
2. Welcher nächste Schritt hat den größten Erkenntnisgewinn: A begrenzte Konstantenoptimiererdiagnose mit vorgegebener Ringdown-Struktur; B gezielte freie Such-/Suchverlaufsintervention; C Prüfung der Profilübertragbarkeit; D ausdrücklich eingeschränkte Grammatik/Template; E breite freie Rekonstruktion vorerst pausieren oder beenden? Vergleiche die ernsthaften Alternativen fair und begründe zurückgestellte Optionen.
3. Prüfe besonders die konkrete Prüfgrenze: Bisherige echte Optimierertests nutzen konstante/lineare konvex-quadratische Modelle, 100 Optimiereriterationen und keine zufälligen Neustarts. Die Ringdown-Positivkontrollen bewerten bereits passende vorgegebene Bäume. Das ist noch kein Nachweis der lokalen Anpassung mehrerer nichtlinearer Ringdown-Konstanten unter dem Suchprofil 20/2. Rechtfertigt diese Lücke zuerst eine Diagnose? Sie beweist weder einen Defekt noch, dass ihre Schließung die freie Suche repariert. Prüfe die vorläufige Präferenz für A kritisch und widersprich bei besser begründeter Alternative.
4. Welche Rolle erhalten complexity_frequency und time_stretch im nächsten Schritt? Begründe diese Rolle ohne vorzeitige Profilfreigabe, Populationsvielfaltsbehauptung oder Annahme identischer Mutationsfolgen. Callbackzahlen sind inklusive Optimierung und keine Zahl verschiedener Bäume.
5. Welche Ergebnisse muss der nächste Schritt liefern, um Fortsetzen, Eingrenzen oder Stoppen zu rechtfertigen? Welches Gate ist vor einem Rausch-/Gewichtungsvergleich für den konkret gewünschten Forschungsanspruch sinnvoll?

Erwartete Antwort:
- Kurzes Urteil mit einer priorisierten Empfehlung, Evidenz, zentraler Unsicherheit und den ernsthaften Alternativen.
- Für genau einen empfohlenen nächsten Schritt einen begrenzten Planentwurf: Frage/Hypothesen, Kontrollen, Datenrollen und zulässiges Vorwissen, genaue Änderungen zum Bestand, vorgeschlagene Starts/Seeds und Budgets mit Begründung oder ausdrücklich noch fehlender Festlegung, Kennzahlen/Referenzen, Auswahlregel, Abbruch-/Weiterentscheidung und Aussagegrenzen.
- Kennzeichne Beobachtung, Hypothese, Empfehlung und nötigen Nutzerbeschluss. Trenne entscheidungsblockierende Lücken von optionalen Verbesserungen. Gib bei fachlichen Behauptungen konkrete versionsgebundene Codequellen oder wissenschaftliche Primärquellen an; lege fehlenden Zugriff offen.
- Schließe mit einem kurzen Beschlussentwurf, den der Nutzer annehmen oder ablehnen kann. Erkläre, welche neuen Beobachtungen gegen deine Empfehlung sprechen würden.

Grenzen: Der abgeschlossene Methodenplan ist eingefroren und endet nach diesen neun Zellen. Keine rückwirkende Änderung von Schwellen, Auswahl oder Originalartefakten. Kein neuer Suchlauf, keine Implementierung, kein automatischer größerer oder kombinierter Arm, keine neue Rauschstudie und keine zusätzlichen Agenten. Fest vorgegebene Formeln oder wahrheitsnahe Starts sind privilegierte Diagnosebedingungen und keine freie Formelrekonstruktion. Drei bekannte Entwicklungsseeds sind keine unabhängige Validierung; gleiche nominelle Budgets keine gleichen Rechenkosten; der Achtelraster-Blindfleck bei 8*fs bleibt bestehen. Eine Eingrenzung der Modellklasse oder eine andere Fragestellung muss ausdrücklich als neuer Anspruch beschlossen werden. Sprache Deutsch; Review als KI-basiert bezeichnen, ohne Modellnamen.
```
