# Entscheidungsgrundlage: nächster Schritt nach der rauschfreien Kontrollserie

Stand: 30.10.2026. KI-basiertes Methodenreview vom Nutzer übermittelt.
**Option A wurde anschließend vom Nutzer angenommen; siehe den
[eigenen Diagnoseplan](constant_diagnostic_plan.md).**
Die abgeschlossene Serie und ihre eingefrorenen Vorgaben bleiben unverändert.

## Aktueller Entscheidungsstand nach dem Review

Der [vollständige übermittelte Befund](#übermittelter-ki-basierter-reviewbefund)
bezieht sich auf PR #41, Head
`1c816e5e40b16a0fd03b268df24cf869d6a33a57`, gegen
`97672ed9b14b81ca90663dc178072b515ee252bc`. Er empfiehlt einmalig
**Option A: Konstantenanpassung einer fest vorgegebenen Ringdown-Struktur**.
Das Review berichtet keine entscheidungsblockierende Unstimmigkeit in der
beschriebenen Optimiererlücke. Ein Defekt oder eine Ursache der historischen
Suchergebnisse ist damit nicht nachgewiesen.

Zur Entscheidung stehen gemeinsam folgende vorgeschlagene Grenzen:

- Ein Baum mit vier freien Konstanten, acht deklarierte Starts und drei
  kontrollierte RNG-Initialisierungen (20261020, 20261021, 20261022).
- 20 beziehungsweise 100 Optimiereriterationen, jeweils zwei zusätzliche
  Neustarts: 48 Backendaufrufe, höchstens 144 lokale Optimierungen.
- 60 Minuten Gesamtwandzeit einschließlich Prozessstarts; feste Kontrollen,
  unveränderte Kurvengrenzen, unabhängige Nachrechnungen und sichere Teilstände.
- Vorgegebene Struktur und wahrheitsnahe Starts sind privilegierte
  Methodenentwicklung. Freies Suchbudget null; keine zusätzlichen Koordinaten,
  Solver, Startgitter oder automatischen Folgeversuche.

Der Nutzer hat am 30.10.2026 nach Übermittlung des Befunds die Umsetzung dieses
Umfangs ausdrücklich beauftragt. Der eigene Diagnoseplan hält diesen Beschluss
fest. Die folgenden Reviewempfehlungen und der Wortlaut dokumentieren weiterhin
ihren damaligen Vorschlagsstand; sie sind keine Ausführungsnachweise.
Ein weiteres Methodenreview ist ohne konkreten neuen Prüfbedarf nicht vorgesehen.

Die folgenden Abschnitte bis einschließlich des kopierbaren Prompts bewahren
die ursprüngliche Entscheidungsgrundlage und den bereits bearbeiteten Auftrag.
Sie lösen keine erneute Reviewrunde aus.

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

## Übermittelter KI-basierter Reviewbefund

Vom Nutzer am 30.10.2026 als `Pasted text.txt` übermittelt; SHA-256 der
unveränderten Eingabedatei:
`7ff8aa29fd9e589d41ffdb3c5f3ce2a578ba8904242b96d08d3e56528539fbaf`.
Der folgende Wortlaut ist als Zitat übernommen. Aussagen in erster Person
beziehen sich auf das übermittelte Review, nicht auf neue Prüfungen bei seiner
Dokumentation. Empfehlungen und Beschlussentwurf sind keine Nutzerfreigabe.
Nur Zitatmarkierungen und Markdown-Zeilenumbrüche sind angepasst.

> [PR #41](https://github.com/craexxn/ringdown-sr/pull/41) — **KI-basiertes Methodenreview**
>
> Gelesener Head: `1c816e5e40b16a0fd03b268df24cf869d6a33a57`
> Vergleichsbasis: `97672ed9b14b81ca90663dc178072b515ee252bc`
> Verankerter Ergebnisstand: `73e1c6748fb6683b99336d81271f332e60034d9f`
>
> PR #41 ist weiterhin offen. Seit dem verankerten Ergebnisstand wurden nur Dokumentationsnachträge ergänzt; Ergebniszahlen, wissenschaftlicher Code und eingefrorene Pläne sind unverändert. Geprüft wurden die Pflichtdokumente, relevante Projektquellen und der versionsgebundene Optimiererpfad.
>
> **Empfehlung: genau ein begrenzter Diagnoseschritt nach Option A — Konstantenanpassung einer fest vorgegebenen Ringdown-Struktur, mit dem bestehenden Profil 20/2 und einer ausschließlich diagnostischen Vergleichsbedingung 100/2.**
>
> Die vorläufige Präferenz für A ist begründet, sofern die Diagnose ausdrücklich eine begrenzte Ausschlussprüfung bleibt. Sie untersucht eine bislang offene Voraussetzung erfolgreicher Suche. Sie beweist weder einen Optimiererdefekt noch erklärt ein positiver Ausgang die Strukturentdeckung.
>
> **Befund und offene Ursachen.** Die dokumentierte Serie zeigt eine erhebliche Verbesserung der Approximation durch die gemeinsam aktivierten Häufigkeitsschalter. Die gerundeten Tabellenwerte ergeben tatsächlich MSE-Senkungen von 89,7 %, 96,3 % und 97,0 %. Dennoch liegt selbst der beste ausgewählte Zwischenpunkte-RMS dieses Arms ungefähr beim **178-Fachen** der Grenze. Die Verbesserung ist somit substanziell, der Abstand zum festgelegten Rekonstruktionsziel ebenfalls.
>
> Daraus folgt:
>
> - **Kurvenapproximation:** verbessert, aber kein exportierter Kandidat erfüllt die Anforderungen.
> - **Freie Strukturentdeckung:** kein erfolgreicher Rekonstruktionsnachweis. `not_supported` beschreibt die Erkennerabdeckung; es belegt nicht, dass geeignete Teilstrukturen während der Suche niemals entstanden.
> - **Physikalische Parameter:** weiterhin nicht beurteilt. Weder kleinere MSE noch passende Einheiten ersetzen Parameterreplays und Identifizierbarkeitsannahmen.
> - **Ursache:** offen bleiben insbesondere Strukturentstehung und -erhaltung, Konstantenstarts, lokale Anpassung, numerische Darstellung und Budgetwirkung. Fronten und Callbackzahlen trennen diese Erklärungen nicht.
>
> Das Originalarchiv mit SHA-256 `a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db` liegt hier nicht vor. Diese Aussagen verwenden den [dokumentierten Audit](https://github.com/craexxn/ringdown-sr/blob/73e1c6748fb6683b99336d81271f332e60034d9f/docs/representation_control_results_manjaro_001.md), keinen von mir wiederholten Originalartefaktaudit.
>
> Die Alternativen bewerte ich folgendermaßen:
>
> | Option | Erkenntnisgewinn | Grenze und Einordnung |
> |---|---|---|
> | **A: Konstantenoptimiererdiagnose** | Trennt bei bekannter Struktur die Anpassungsfähigkeit von deren evolutionärer Entdeckung; erlaubt einen überschaubaren Budgetvergleich. | Privilegierte Struktur und künstliche Starts. Nur unter striktem Endpunkt sinnvoll; **meine Empfehlung**. |
> | **B: Freie Suchintervention oder Verlaufsauswertung** | Liegt näher an der eigentlichen Forschungsfrage. Ein Verlauf könnte Entstehung, Optimierung und Verwerfung geeigneter Strukturen unterscheiden. | Eine weitere reine Budgeterhöhung wäre schwach begründet. Aussagekräftiges Tracing benötigt zusätzliche Instrumentierung und ihre Prüfung. Stärkste Alternative, falls A bereits ausreichend belegt wäre. |
> | **C: Profilübertragbarkeit** | Könnte zeigen, ob die Fehlerverbesserung über den bekannten Fall hinausgeht — auch ohne bestandenen Kurvenmarker eine legitime Frage. | Untersucht primär Übertragbarkeit einer weiterhin unzureichenden Approximation. Für das derzeitige Rekonstruktionsproblem weniger unmittelbar aufschlussreich. |
> | **D: Engere Grammatik oder Template** | Kann den Schwerpunkt schneller auf kontrollierte Rauschgewichtung lenken. | Ändert den Forschungsanspruch. Ein vollständig vorgegebenes Ein-Moden-Template ist zunächst Parameteranpassung; sein zusätzlicher Nutzen gegenüber dem vorhandenen separablen Referenzfit müsste begründet werden. |
> | **E: Breite freie Suche pausieren/beenden** | Begrenzt Aufwand und ermöglicht Konzentration auf bereits tragfähige Bausteine. | Bei engem verbleibendem Zeitbudget durchaus vorrangig. Die bisherigen Ergebnisse rechtfertigen aber keine allgemeine Unmöglichkeitsaussage; eine einzelne begrenzte Prüfung von A ist noch vertretbar. |
>
> **Warum die Optimiererlücke trägt.** Die [bestehenden Backendtests](https://github.com/craexxn/ringdown-sr/blob/4057caaffd9c4de5791ded14431c6e289db75b73/julia/test/constant_optimization.jl#L23) verwenden tatsächlich konstante beziehungsweise lineare Modelle, 100 Iterationen und keine zufälligen Neustarts. Die [Ringdown-Kontrolle](https://github.com/craexxn/ringdown-sr/blob/4057caaffd9c4de5791ded14431c6e289db75b73/julia/test/runtests.jl#L274) bewertet einen bereits passenden Baum.
>
> Im [Backend 2.5.1](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/ConstantOptimization.jl#L202) bedeuten zwei Neustarts zwei zusätzliche lokale Optimierungen. Ihre Startvektoren werden vom ursprünglichen Vektor abgeleitet. Der beste Optimiererwert wird bei strikter Verbesserung übernommen; eine bestätigte Konvergenz wird dabei nicht verlangt. Deshalb müssen **Optimiererstatus, numerische Konsistenz und fachliche Güte getrennt** erfasst werden.
>
> Der stärkste Einwand gegen A bleibt: Gute Ergebnisse an absichtlich vorgegebenen Bäumen können für tatsächlich besuchte Suchbäume wenig repräsentativ sein. Ich begrenze A deshalb auf einen Budgetvergleich und endlich viele Starts. Koordinatenwechsel, alternative Solver und neue Parameterdarstellungen werden nicht zusätzlich untersucht.
>
> **Planentwurf — sämtliche folgenden Zahlen und Entscheidungsregeln sind Vorschläge zur Annahme, keine bereits beschlossenen Vorgaben.**
>
> 1. **Frage und Hypothesen**
>
>    Kann der tatsächliche Mehrkonstantenpfad die bekannte Ringdown-Struktur unter 20/2 von festgelegten abweichenden Starts aus ausreichend anpassen?
>
>    Unterschieden werden:
>
>    - **Budgethypothese:** 20 Iterationen begrenzen die Anpassung; 100 helfen bei ansonsten identischen Bedingungen.
>    - **Startabhängigkeit:** Nahe Starts funktionieren, weiter entfernte scheitern auch mit 100 Iterationen.
>    - **Andere lokale Begrenzung:** Schon nahe Starts bleiben unzureichend, etwa wegen Abbruchverhalten, numerischer Ableitungen oder ungünstiger Parametrisierung.
>    - **Kein nachgewiesener Engpass in diesen Fällen:** Bereits 20/2 liefert gute Anpassungen. Die historische freie Suche ist damit weiterhin nicht erklärt.
>
> 2. **Daten, Struktur und erlaubtes Vorwissen**
>
>    Verwendet werden ausschließlich die unveränderten 128 Trainingswerte der abgeschlossenen Serie. Die 889 Zwischenpunkte bleiben nachgelagerte Diagnosepunkte.
>
>    Ein einziger, unverändert geklammerter Baum wird vorgegeben:
>
>    \[
>    h(t)=A\,[\exp(bt)\,\cos(ct+\phi)].
>    \]
>
>    Er besitzt 13 Knoten und vier optimierbare Konstanten. Insbesondere wird die wahre Phase nicht festgehalten. `b` und `c` sind einzelne Konstanten; die lesbaren Startangaben werden einmalig durch \(b=-1/\tau\), \(c=2\pi f\) umgerechnet.
>
>    Die bekannte Struktur und wahrheitsnahe Starts sind **privilegierte Diagnosebedingungen**. Sie gelangen weder in freie Suchpopulationen noch in die alten Ergebnisse. Die neue Diagnose ist ebenfalls Methodenentwicklung, keine unabhängige Validierung.
>
> 3. **Acht vorab festgelegte Starts**
>
>    Vier bewusst wahrheitsnahe Starts:
>
>    | Start | \(A\) | \(f\) in Hz | \(\tau\) in s | \(\phi\) in rad |
>    |---|---:|---:|---:|---:|
>    | L1 | 0,9 | 247,5 | 0,0072 | −0,1 |
>    | L2 | 1,1 | 252,5 | 0,0088 | +0,1 |
>    | L3 | 0,9 | 252,5 | 0,0088 | −0,1 |
>    | L4 | 1,1 | 247,5 | 0,0072 | +0,1 |
>
>    Hinzu kommen vier weiter entfernte Starts als kartesisches Produkt:
>
>    \[
>    f\in\{4/T,16/T\}=\{128,512\}\,\mathrm{Hz},\qquad
>    \tau\in\{T/8,T/2\},
>    \]
>    mit \(T=128/4096\,\mathrm{s}\), \(A=\max_j|y_j|\) und \(\phi=\pi/2\).
>
>    Diese Auswahl deckt zwei Startbereiche ab; sie schätzt weder das Volumen eines Einzugsgebiets noch eine Erfolgswahrscheinlichkeit. Die Zahlen sind begrenzte Entwicklungsentscheidungen, keine wissenschaftlich hergeleitete optimale Stichprobe.
>
> 4. **Numerischer Pfad und Budget**
>
>    Direkter Aufruf von `SymbolicRegression.optimize_constants` mit dem vorhandenen vollständigen Verlustcallback und Einheitencheck. Float64, Sekunden, gewöhnliche MSE, BFGS mit Backtracking, numerische Differentiation und bisherige Abbruchtoleranzen bleiben erhalten. Keine zusätzliche Frequenz-/Dämpfungsbeschränkung und keine analytische Voranpassung.
>
>    Zwei Bedingungen:
>
>    - **20 Iterationen, zwei Neustarts:** bestehendes Profil.
>    - **100 Iterationen, zwei Neustarts:** ausschließlich diagnostischer Budgetfaktor. Die 100 knüpfen an das vorhandene technische Prüfbudget an; sie sind keine belegte ausreichende Obergrenze.
>
>    Drei kontrollierte RNG-Initialisierungen je Start: die bekannten Seedkennungen 20261020/21/22 mit der bestehenden Backendabbildung. Je Paar werden RNG-Typ, Anfangszustand und tatsächliche Restartvektoren geprüft. Das rekonstruiert **nicht** den fortgeschrittenen Zufallszustand einer historischen freien Suche.
>
>    Insgesamt **8 Starts × 3 Seeds × 2 Budgets = 48 Backendaufrufe**, mit höchstens 144 lokalen Optimierungen. Jeder Aufruf startet frisch; keine Wiederholung bis zum Erfolg. Die Paarreihenfolge wird vorab abwechselnd festgelegt.
>
>    **Freies Suchbudget: null.** Beide Häufigkeitsschalter bleiben für diese isolierte Diagnose aus. Ihre Populationsmechanismen werden hier nicht untersucht. `complexity_frequency` bleibt Entwicklungskandidat für eine spätere freie Untersuchung mit frischer Baseline. `time_stretch` wird in diesem Schritt zurückgestellt; sein Mischbefund beweist keine grundsätzliche Untauglichkeit.
>
> 5. **Kontrollen, Messgrößen und Auswahl**
>
>    Je Budgetprofil fünf reine Kontrollen ohne Optimierung: passender Referenzbaum, optimale Konstante, dimensionswidriges `sin(t)` sowie die Aliasfälle 4346 und 33018 Hz. Damit werden Verlustpfad, Einheiten und bekannte Diagnosegrenzen kontrolliert.
>
>    Für alle 48 Aufrufe werden Startbaum, Restartreihenfolge, Rückgabebaum, Anfangs-/Endverlust, tatsächlicher Optimiererzustand, verfügbare Abbruchinformationen, Callbackzahlen und Zeiten gespeichert. Beobachtende Instrumentierung darf weder RNG noch Optimiererzustand verändern oder Abbruchentscheidungen treffen. Nicht verfügbare Status bleiben ausdrücklich nicht verfügbar.
>
>    Die Auswahl entspricht dem unveränderten Backendverhalten: bester lokaler Trainingsverlust; ohne strikte Verbesserung bleibt der Ausgangsbaum. Keine Auswahl nach Wahrheit oder Zwischenpunkten, kein „bester Seed“ als Gesamtergebnis.
>
>    Ausgewertet werden:
>
>    - unabhängig nachgerechnete Vorhersagen, Residuen und MSE;
>    - RMS-/Maximalfehler auf beiden bestehenden Rastern mit unveränderten Grenzen;
>    - rohe und aliasbezogene Parameter samt bisherigen Replay-Gates;
>    - gepaarte Unterschiede **100 minus 20**, getrennt für nahe und entfernte Starts;
>    - Abbruchursachen und Aufwand, ohne Gleichsetzung von Iterationen und Rechenkosten.
>
>    Eine nachgelagerte analytische Gradientenrechnung kann die numerische Diagnose ergänzen:
>    \[
>    \nabla_\theta L=\frac{2}{N}J^\top(h-y).
>    \]
>    Sie wird dem Optimierer nicht übergeben. Der klassische [separable Referenzfit](https://github.com/craexxn/ringdown-sr/blob/4057caaffd9c4de5791ded14431c6e289db75b73/docs/reference_fit.md) ist keine gleichartige Solverkontrolle und wird diesem begrenzten Versuch nicht als weiterer Fitarm hinzugefügt.
>
> 6. **Abbruch und Konsequenzen**
>
>    Quellen-, Daten-, Options- oder Replayfehler stoppen die Serie; Teilstände bleiben erhalten. Nichtkonvergenz und schlechte Kurven sind dagegen fachliche Ergebnisse und kein Anlass für Ersatzläufe. Nach 48 Aufrufen endet die Diagnose unabhängig vom Ergebnis.
>
>    Als organisatorische Obergrenze schlage ich **60 Minuten Gesamtwandzeit einschließlich Prozessstarts** vor. Das ist ein zu beschließendes Ressourcenlimit, keine Laufzeitprognose. Die dokumentierten 435 Sekunden der früheren Serie erlauben keine proportionale Hochrechnung. Ein Ressourcenabbruch bleibt unvollständig und wird nicht automatisch wiederholt.
>
>    | Beobachtung | Konsequenz für die anschließende Entscheidung |
>    |---|---|
>    | Alle zwölf nahen Fälle bestehen bereits unter 20/2 die Kurvengrenzen | Ein allgemeines lokales Anpassungsversagen ist für diese Fälle nicht gestützt. Als nächstes wäre eine gezielte Strukturverlaufsfrage zu begründen; keine weitere Optimierer-Rastererweiterung. |
>    | 20 erreicht das Iterationslimit; 100 führt dieselben Starts zu guten Kurven | Budgetbegrenzung ist für diese Fälle belegt. Eine spätere freie Budgetintervention wäre begründbar, aber noch nicht freigegeben. |
>    | Nahe Starts funktionieren, entfernte bleiben schlecht | Startabhängigkeit ist belegt. Unbekannt bleibt, welche Starts die freie Suche tatsächlich erzeugt; kein automatischer Schluss „mehr Iterationen“. |
>    | Nahe Starts bleiben auch unter 100 unzureichend oder stoppen früh mit großem Fehler | Keine weitere Budgeteskalation. Breite freie Versuche bleiben ausgesetzt; Parametrisierung oder Forschungsumfang benötigen einen neuen Beschluss. |
>    | Gemischte oder technisch unklare Ergebnisse | Keine eindeutige Ursachenbehauptung und keine automatische Zusatzserie. |
>
>    Die Zwölf-von-zwölf-Regel ist ein vorgeschlagenes konservatives Entwicklungsgate für diese nahe Startmenge, keine statistische Garantie.
>
> **Gate vor einem Rausch-/Gewichtungsvergleich.** Für den Anspruch *freie Ringdown-Rekonstruktion* reicht ein positives Ergebnis von A nicht. Zuerst sollte ein eingefrorenes freies Verfahren auf einer separat geplanten, begrenzten rauschfreien Entwicklungsmenge die erforderliche Kurvengüte zeigen. Danach braucht der Gewichtungsvergleich getrennte Signal-/Rauschfälle, unabhängige Hintergrundrollen und vorab festgelegte gemeinsame Bewertungsmaße. Eine fehlerfreie Rekonstruktion jeder denkbaren Formel ist dafür nicht erforderlich.
>
> Für den ausdrücklich engeren Anspruch *Parameteranpassung innerhalb bekannter Ringdown-Struktur* könnte ein Gewichtungsvergleich früher sinnvoll sein. Dieser Wechsel müsste beschlossen werden; bei vollständig vorgegebener Formel wäre der vorhandene klassische Referenzfit eine wesentliche Vergleichsgrundlage. Der Alias-Blindfleck bei \(8f_s\) bleibt bestehen, `physical_identification` bleibt auch nach guten Rasterreplays `not_assessed`.
>
> **Entscheidungsstand und Prüfgrenzen.** Ich sehe keine entscheidungsblockierende Unstimmigkeit in der beschriebenen Optimiererlücke. Vor einer Ausführung erforderlich sind jedoch der Beschluss über privilegierte Starts, Budgetvergleich und Ressourcenlimit sowie ein eingefrorener, technisch geprüfter Diagnosepfad mit nachgewiesener Eingabeherkunft. Weitere Koordinaten, Solver, Startgitter und Erkennererweiterungen sind optionale spätere Fragen.
>
> Hier wurden Quellen und dokumentierte Zahlen geprüft. Python- und Julia-Installationen sind vorhanden; für dieses Review wurden keine Tests, Fits, Optimierungen oder Suchläufe gestartet und keine zusätzlichen Agenten eingesetzt.
>
> **Beschlussentwurf:** „Wir wählen einmalig Option A im beschriebenen Umfang: eine feste Vierkonstantenstruktur, acht deklarierte Starts, drei kontrollierte RNG-Initialisierungen und die Profile 20/2 sowie 100/2. Wir akzeptieren die Diagnoseprivilegien und die feste Aufwandsgrenze. Die abgeschlossene Serie bleibt unverändert; Folgeversuche benötigen einen neuen Beschluss.“
>
> Gegen diese Empfehlung sprächen bereits vorhandene belastbare Ringdown-Optimierernachweise unter 20/2 mit vergleichbaren Starts, aussagekräftige Suchverläufe mit eindeutig anderem Engpass oder ein verbleibendes Arbeitsbudget, das selbst diese begrenzte Diagnose nicht rechtfertigt. Dann hätten B beziehungsweise ein ausdrücklich beschlossener Wechsel zu D/E Vorrang.
