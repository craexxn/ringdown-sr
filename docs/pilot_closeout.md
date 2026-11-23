# Pilotabschluss: Rekonstruktion, Auswahl und Strukturgrenzen

Stand 23.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md).
Die begrenzte lesende Schlussprüfung ist abgeschlossen. Sie ergänzt die
bereits geprüften Pilotserien und beendet deren offene Entwicklungsrunde.
Der nächste Schritt ist die Umsetzung des [Hauptversuchsprotokolls](main_study_protocol.md),
keine weitere Suche nach einem günstigen Pilotresultat. Die Hauptserie selbst
ist noch nicht implementiert oder ausgeführt.

## Was der Pilot trägt und was offenbleibt

| Gegenstand | Belegter Befund | Konsequenz für die Hauptversuche |
| --- | --- | --- |
| Freie rauschfreie Rekonstruktion | Das bestätigte R-Profil erreicht die zuvor festgelegte praktische Grenze auf drei neuen Innenbereichsfällen. | Das feste Profil ist eine begründete Ausgangsbasis, keine allgemeine Erfolgsgarantie unter Rauschen. |
| Hintergrunddauer | In der Folgestudie verbessert 4096 s gegenüber 64 s die Kovarianzschätzung in allen 20 AR(1)-Fällen, aber nur acht ausgewählte Formeln; das primäre Intervall umfasst null. | Dauerwirkung an neuen Signalbedingungen messen, ohne einen positiven Effekt zur Startbedingung zu machen. |
| Verlustskalierung | Feste Endkurven bleiben praktisch gleich; freie Suchpfade und Formeln ändern sich. | Keine allgemeine Verlustumstellung aus zwei Rauschfenstern. |
| Auswahl zusätzlicher Beobachtungen | Bessere Gruppenmittel und nun auch zusätzliche Familiennachweise sind belegt; der isolierte Rastervergleich bleibt gemischt. | Zusatzbeobachtungen sind Entwicklungsinformation und kein verfügbarer Einzelevent-Standard. |
| Formelstruktur und Domain | Viele Familienfragen bleiben ungeklärt; auch neu ausgewählte Formeln können Definitionslücken besitzen. | Kurvenfehler, Familiennachweis und Domain getrennt berichten. |

Detailquellen bleiben die [R-Bestätigung](restart_budget_confirmation_results_manjaro_001.md),
die [Folgestudie](noise_followup_results_manjaro_001.md) und der
[Skalierungs-/Auswahlbericht](white_loss_scaling.md). Historische negative
Befunde und Abbrüche bleiben erhalten. Ein fehlender allgemeiner Vorteil
gewichteter SR oder längerer Hintergrunddaten ist ein zulässiges Ergebnis
der Hauptfrage und kein Anlass für unbegrenztes Nachoptimieren.

## Umfang der lesenden Schlussprüfung

`pilot-structure-closeout-001` bewertet genau die 468 bereits ausgewählten
Originalausgaben aus 156 Paketen: 26 bekannte Entwicklungsfälle, sechs Arme
und drei Auswahlregeln (Original, Same-grid, Off-grid). Keine Fits, Suchen,
Neuauswahl, Kürzung oder Konstantenanpassung. Die übrigen Kandidaten werden
nicht neu klassifiziert. Auch die 93 Ausgaben des gesonderten Skalierungslaufs
sind keine zusätzlichen Fälle dieser Prüfung.

Verwendet wird der unveränderte Beweiser `ringdown-sr-structure-proof-1`
auf Quellencommit `aef40517334da106a6d6582963e720525056fbb0`, gemäß
[Stufe 2](supplemental_structure.md). Die vorhandenen mathematischen
Ressourcengrenzen bleiben erhalten; Run und Replay erhalten jeweils 300 s.
Das geschlossene Intervall stammt für jeden Arm aus seiner archivgebundenen
Zeitachse. Uniform- und Jitterachsen haben hier beide exakt `[0,127/4096] s`,
obwohl ihre inneren Messzeiten verschieden sind. Daraus folgt kein anderer
Intervallvertrag für spätere Messfenster.

Vor der ersten neuen Klassifikation sind externer Arbeitsplan, unveränderte
Quellen, Adapter und technische Referenzen durch Hashes gebunden. Dies ist
eine retrospektive Bewertung bekannter Entwicklungsdaten, keine unabhängige
Bestätigung oder vorab festgelegte neue Hauptstudie. Wahrheit, Verluste und
Kurvennoten gehen nicht in den Familien-/Domainbeweis ein.

## Familien- und Domainbefund

Die folgenden Summen sind **deskriptive Ausgabenzahlen**, keine gepoolten
unabhängigen Erfolgsquoten. Die sechs Arme teilen dieselben 20 AR(1)- und
sechs White-Fälle. Je Auswahlregel sind alle 156 Ausgaben erfasst.

| Originalfamilie | Original | Same-grid | Off-grid |
| --- | ---: | ---: | ---: |
| Mitgliedschaft nachgewiesen | 0 | 48 | 41 |
| Nichtmitgliedschaft nachgewiesen | 9 | 6 | 3 |
| Ungeklärt | 147 | 102 | 112 |

Bei den Originalauswahlen bedeutet die Null insbesondere **nicht**, dass
alle 156 Formeln als Nichtmitglieder widerlegt wären. Der begrenzte Beweiser
lässt 147 Fragen offen. Ein positiver Familienbeweis weist wiederum keine
richtige Frequenz, Dämpfung oder physikalische Identifikation nach.
Neue Parameterübereinstimmungen und quantifizierte Restterme bleiben
ausdrücklich `not_assessed`.

| Nachgewiesene Mitglieder je Modell/Arm | Original | Same-grid | Off-grid |
| --- | ---: | ---: | ---: |
| AR(1), O, je 20 Fälle | 0 | 5 | 6 |
| AR(1), K | 0 | 4 | 4 |
| AR(1), E64s | 0 | 6 | 5 |
| AR(1), E4096s | 0 | 4 | 3 |
| AR(1), Jitter-O | 0 | 6 | 6 |
| AR(1), Jitter-K | 0 | 4 | 3 |
| White, O, je sechs Fälle | 0 | 4 | 2 |
| White, K | 0 | 3 | 1 |
| White, E64s | 0 | 4 | 1 |
| White, E4096s | 0 | 4 | 2 |
| White, Jitter-O | 0 | 2 | 4 |
| White, Jitter-K | 0 | 2 | 4 |

Same-grid zu Off-grid behält 28 nachgewiesene Mitglieder; 20 zuvor belegte
Mitglieder wechseln zu ungeklärten Ausgaben. Umgekehrt wechseln zwölf
ungeklärte und eine belegte Nichtmitglied-Ausgabe zu nachgewiesenen Mitgliedern.
Das sind Änderungen der **ausgewählten Formel**, keine wechselnden Beweise
derselben Formel. Identische Bäume auf identischen Intervallen haben identische
Befunde. Die zusätzliche Beobachtung hilft hier also auch, vorhandene
Familienmitglieder auszuwählen; das neue Raster liefert keine einheitlich
größere Zahl solcher Nachweise.

| Originaldomain, je 156 Ausgaben | Original | Same-grid | Off-grid |
| --- | ---: | ---: | ---: |
| Überall definiert | 144 | 150 | 153 |
| Nicht behebbare Singularitäten | 0 | 1 | 1 |
| Behebbare Lücken | 1 | 3 | 1 |
| Ungeklärt | 11 | 2 | 1 |

Domain- und Familienbefunde beantworten verschiedene Fragen. Eine ungeklärte
Domainkategorie kann bereits einzelne belegte Ausschlusspunkte enthalten,
ohne dass die Gesamtheit oder Art aller Lücken geklärt wäre. Eine symbolisch
stetige Fortsetzung verändert die Definitionsmenge des Originals nicht.

Ein konkreter Gegenfall ist `ar1-05 / known_covariance`: Same-grid und Off-grid
wählen beide `member-02/candidate-010`, mit unveränderter Originalformel
(t in Sekunden, Ausgabe dimensionslos):

```text
(cos(-2.8523978226084927 + (1664.5416749427188 * t)) * (exp(t / -0.0045592856414944025) + -0.010136869613754011)) / ((t * 47.85235512840305) + -1.0123746409780605)
```

Der gespeicherte Beweis weist eine nicht behebbare Singularität bei ungefähr
0,02115621348754 s innerhalb des Intervalls nach. Endliche Fehlerwerte auf
gespeicherten Prüfpunkten beseitigen diese Singularität nicht. Daraus wird
hier kein nachträglicher Domainfilter für die Auswahl eingeführt; ein solcher
Filter wäre eine eigene vorab festzulegende Methode. Alle unveränderten
Originalformeln, Kurven und Punktdaten sind in der zugeordneten Galerie enthalten.

## Prüfnachweise, Kosten und erhaltener Fehlversuch

18 technische Prüfungen bestehen vor der Anwendung: zehn unabhängig
hergeleitete mathematische Referenzen und acht Adapter-/Bindungsgegenfälle.
Der Run umfasst 375 unterschiedliche Beweisaufrufe und 93 Treffer eines
exakten Baum-/Intervall-/Quellcaches. Alle 468 Ausgaben zählen weiterhin.

Der erste separate Replay rechnet alle 468 Fälle ohne Cache nach, scheitert
aber an einem Python-Vergleich gespeicherter JSON-Listen mit nativen Tupeln
im Präzisionsfeld. Die kanonischen JSON-Datensätze sind bereits identisch.
Der gesperrte Replay samt vollständigen Teilständen und gemessenen Kosten
bleibt erhalten; sein Status wird nicht nachträglich auf Erfolg gesetzt.

Ein separater Verifier in neuer Datei vergleicht kanonische JSON-Repräsentationen.
Vier gezielte Gegenprüfungen zeigen, dass Änderungen von Status, Beweis,
Zahlen, Präzision oder Feldern weiterhin abgelehnt werden. Der neue Replay
`verification-002` bestätigt alle 468 Datensätze ohne Cache bytegleich.
Ein unabhängiger Evidenz-/Zensusaudit prüft die ursprünglichen Kandidaten,
Intervalle, sämtliche Gruppenzahlen, Statusübergänge und Verifierbindungen.
Er wiederholt keine mathematische Klassifikation und ersetzt keinen
allgemeinen Vollständigkeitsbeweis des begrenzten Erkenners.

| Aufruf | Zustand | Wandzeit | gemessene CPU User/System |
| --- | --- | ---: | ---: |
| Strukturprüfung | abgeschlossen | 8,714 s | 5,220 / 3,189 s |
| Erster Replay | abgebrochen, erhalten | 3,333 s | 2,600 / 0,852 s, unvollständige CPU-Messung |
| Separater Replay 002 | abgeschlossen | 8,195 s | 6,436 / 1,741 s |

Die drei Aufrufe benötigen zusammen 20,241 s Wandzeit. Technische Tests,
unabhängige Audits, Galerie und Archivierung sind darin nicht enthalten.
CPU-Scope ist `self_plus_reaped_children`; verschachtelte Zeiten werden nicht
zusätzlich aufsummiert. Originale Eingaben und Ausgaben bleiben unverändert.

Gebundene Kernbelege:

- Plan-SHA-256: `7323c8d9c52cd887169e9f3a7f5b1e0159b5113a97bb8c1226e3cd762d08f9c8`.
- Ursprünglicher Adapter: `536586093a9ee2010c798cb6e6b8bb8f0c6ed52ccdc90cfbb1d94fbac30a0020`.
- Runreport: `bb3169ac3ea5700771da52766694eaedaf573f45dae47f718d4b0a70df4a6411`.
- Vollständige Records: `f95bd778e5143f7e5d2612a579392ac9ad18c706cda5d4a36f73bd5b143962e0`.
- Replay-002-Report: `7fcde834a78ea772df7cbe0dd020aa47f2bc02da6cd46dc0d44ab7d8190fe627`.
- Unabhängiger Audit: `1a7d28ee868653eb2418307172a52a8c61d3ae86f5b7c325a7f973dbed5825c6`.

Werkzeuge, technische Referenzen, beide Replayversuche, Statusprojektion und
Auditbelege gehören zum getrennten Nachweisarchiv. Archivrollen, vollständige
Hashes der Darstellung und tatsächlicher Sicherungsstand stehen im
[Ergebnisindex](results_index.md). Ein lokales Archiv ist keine bestätigte
unabhängige Zweitkopie.

## Beschluss für den Übergang zur Hauptserie

Die bisherige Pilotentwicklung ist fachlich abgeschlossen. Die nun bekannten
Grenzen werden zu Messgrößen und Aussagegrenzen der Hauptserie; ein positiver
Kovarianzeffekt, perfekte Formelrekonstruktion oder eine weitere Skalierungsrunde
sind keine zusätzlichen Abschlussbedingungen.

Am 23.11.2026 ist das **feste Suchprofil R4×1000, lokal 300/5, mit zusätzlich
gemessenen Rechenkosten** beschlossen. Gleiche Iterationen sind keine gleiche
Rechenzeit. Trainingsverlust-Auswahl, Grammatik und Komplexitätsgrenze bleiben
als Hauptvorschlag erhalten; die Wahrheit dient ausschließlich der Bewertung.

Der [konkrete Hauptentwurf](main_study_protocol.md) schlägt zwei Exposé-Signale,
64/4096 s Hintergrund, O/K/E64/E4096 und 80 unabhängige Blöcke vor: 320 Pakete,
1280 Suchworker. Der relative L2-Fehler wird ausdrücklich von den alten
RMSE/A-Endpunkten getrennt. Signal-/Rasterdetails, unabhängige Seeds,
Beurteilung des Definitionsbereichs, Ausfälle, Kosten und vollständige
Ausgaben werden vor dem ersten Hauptlauf gebunden. Die Fallzahl ist
budgetbegrenzt und garantiert keine bestimmte statistische Präzision.

Noch nötig sind die endgültige Plan-/Seedbindung, die getrennte technische
Serienanbindung und deren begrenzter Integrationsvorlauf. Dies ist eine
konkrete Implementierungsaufgabe, keine neue offene Pilotoptimierung.
LIGO-Hanford folgt als gesondert zu planende Anwendung. Die historische
Exposé-Zuordnung und die aktuellen Literaturgrenzen sind im Hauptprotokoll
ausdrücklich dokumentiert.
