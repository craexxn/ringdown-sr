# Leitfaden: wiederholbare Ringdown-Rekonstruktion und Übergang zu Rauschversuchen

Version 1, Stand: 05.11.2026. Als Dokumentationsergänzung in
[PR #69](https://github.com/craexxn/ringdown-sr/pull/69) übernommen.
Der PR ist übernommen und umfasst ausschließlich **Phase 1, Bewertungsstufe 1**.
Aktuell wird Bewertungsstufe 2 umgesetzt; ihr
[Intervall- und Beweisvertrag](supplemental_structure.md) ist am 05.11.2026
ausdrücklich beschlossen. Prüfung und Übernahme stehen noch aus.
Die Umsetzung und lesende Anwendung gehören zu
[PR #70](https://github.com/craexxn/ringdown-sr/pull/70); die Zusatzterm-Stufe
bleibt ein nachfolgender eigener PR.

Diese Datei hält die vereinbarte Vorgehensrichtung fest. Konkrete Seeds,
Auswahlregeln, Budgets und noch offene methodische Einzelentscheidungen werden
vor Ausführung im jeweiligen Versuchsprotokoll festgelegt. Vorgeschlagene
Zahlen sind unten ausdrücklich gekennzeichnet. Die Roadmap dokumentiert keine
bereits erfolgte Implementierung oder wissenschaftliche Ausführung.

## Rolle und Pflege

- Diese Datei ist die zentrale Quelle für Reihenfolge, Begründung und
  Entscheidungskriterien des weiteren Vorgehens.
- [README](../README.md#projektstatus) bleibt der Einstieg;
  [Fortsetzungsstand](representation_implementation_status.md) führt den
  aktuellen Bearbeitungsstand, Prüfnachweise und nächsten konkreten Schritt.
  Beide verlinken hierher; die Roadmap wird dort nicht vollständig kopiert.
- Jeder fachlich relevante PR nennt seine Phase in diesem Leitfaden und
  aktualisiert den Fortsetzungsstand. Änderungen an der Route werden im
  zuständigen PR begründet; der Fortsetzungsstand verlinkt Entscheidung und Belege.
- Bereits ausgeführte oder eingefrorene Versuchsprotokolle bleiben unverändert.
  Geänderte Regeln gelten als neue Version für zukünftige Versuche;
  retrospektive Neubewertungen werden ausdrücklich so bezeichnet.
- Vor jedem neuen Arbeitspaket aktuellen Repository- und PR-Stand prüfen.
  PR-Nummern sind Verweise auf tatsächliche PRs, keine reservierten Arbeitspakete.

## Ziel und Ausgangspunkt

Ziel ist eine wiederholt erfolgreiche freie Rekonstruktion der Ringdown-Familie

\[
g(t)=e^{-\gamma t}\,[a\cos(\omega t)+b\sin(\omega t)],
\qquad \gamma>0,\ \omega>0,\ a^2+b^2>0.
\]

Damit wird eine interpretierbare Grundlage für die Untersuchung von Rauschen,
Hintergrunddatenmenge und Kovarianzgewichtung geschaffen. Ein Fit mit bereits
vorgegebener Ringdown-Struktur bleibt ein privilegiertes Kontrollverfahren.

Ein am 05.11.2026 übermittelter Nachrechnungsbefund zum
[Seed-/Treiber-Kreuzvergleich](seed_driver_crosscheck.md) berichtet:

| Seed | Kreuzlauf und Übereinstimmung | Originalauswahl |
|---|---|---|
| 20261201 | Transfertreiber reproduziert alle 7 Kandidaten des Staffeltreibers | A, praktisch punktgenau; Ringdown-Struktur nachgewiesen, Parameter passend |
| 20261210 | Staffeltreiber reproduziert alle 11 Kandidaten des Transfertreibers | D; relativer RMS 7,30 %, Maximum 6,84 %; bisher nicht erkannt, Parameter nicht bewertet |

Die Fehlerwerte verwenden jeweils das schlechtere der beiden Raster. Laut
übermitteltem Befund stimmen Originalreihenfolge, Formeln, Vorhersagen, Residuen,
Verlustbits, Auswahlindex, effektive Optionen und Zielfunktionsaufrufzahlen überein.
Berichtet wurden Archivhash-, Prüfsummen- und Quellenprüfung sowie unabhängige
Python-Nachrechnung; kein zusätzlicher nativer Julia-Replay. Das Originalarchiv,
sein SHA-256 und ein versionierter Ergebnisbericht liegen diesem PR nicht vor.
Diese Angaben sind **übermittelte Nachweise**, keine hier erneut ausgeführte
Primärdatenprüfung. Ein konkreter Beleglink bleibt nachzutragen. Die im Entwurf
enthaltene Aussage, keiner der elf Kandidaten erreiche A/B/C, wird ohne die
Einzelkandidatenwerte hier nicht als geprüfter Befund übernommen.

Für diese zwei gezielt gewählten Seeds am rauschfreien Ankersignal unter dem
gemeinsamen Einzelzelladapter folgt das gespeicherte Ergebnis dem Seed. Das
stützt die Untersuchung der Suchrobustheit und begründet ohne neuen Gegenbefund
keine weitere breite Treiberfehlersuche. Es beweist weder identische Suchverläufe,
allgemeine Implementierungskorrektheit noch eine bestimmte Erfolgswahrscheinlichkeit.
Eine automatische Budgeterhöhung folgt daraus nicht.

Zum Dokumentationsstand umfasst PR #69 Stufe 1 der Zusatzbewertung: Kurvenklassen
und ihre Anbindung an historische Auswahlen und zukünftige Schema-3-Läufe.
Exakte Struktur/Definitionsbereich/Fortsetzung sowie Zusatzterm-Diagnose sind
nachfolgende Stufen. Ein Merge von #69 allein schließt die Bewertung nicht ab.
Die beauftragten Bewertungsstufen 2 und 3 folgen jeweils in eigenen PRs nach
bestätigter Übernahme der vorherigen Stufe; ihre offenen Methodenentscheidungen
werden vor der Umsetzung geklärt. Die Phasennummern dieses Leitfadens sind von
diesen drei Bewertungsstufen zu unterscheiden. Für zukünftige simulierte
Schema-3-Läufe gelten die beschlossenen Datenrollen und Raster aus dem
[Bewertungsvertrag](supplemental_assessment.md); neue Endpunkte und Suchversuche
in den folgenden Phasen bleiben vorher festzulegen und gesondert auszuführen.

## Phasenfolge

| Phase | Arbeitspaket | Ergebnis beziehungsweise Entscheidung |
|---|---|---|
| 1 | Bewertung vervollständigen | Getrennte, geprüfte Befunde zu Kurve, Struktur, Definitionsbereich und Parametern |
| 2 | Vorhandene Endfronten diagnostizieren | Erkennungs-, Auswahl-, Konstanten- und Suchprobleme unterscheiden |
| 3 | Globale Neustarts mit längeren Einzelsuchen vergleichen | Eine begründete Suchstrategie auswählen oder unzureichenden Nutzen festhalten |
| 4 | Nur bei Bedarf eine zweite Suchintervention | Zeitkoordinate unter dem aktuellen Profil prüfen |
| 5 | Ausgewähltes Profil in den späteren Laufweg übernehmen | Rauschfreie Kontrollausführung und korrekte gewichtete Optimierung nachweisen |
| 6 | Eingefrorene Konfiguration unabhängig bestätigen | Übergang zum Rauschpilot oder Entscheidung über den Forschungsanspruch |
| 7 | Kleiner Rauschpilot | Technische und methodische Grundlage für die Hauptversuchsplanung |

Die technische Vorbereitung der Rauschpipeline mit bekanntem Strukturfit kann
parallel erfolgen. Die freie SR wird im Rauschpilot nach Phase 6 untersucht.

## 1. Bewertung abschließen

Kurvengüte, Struktur, Originaldefinitionsbereich und Parameterübereinstimmung
bleiben getrennte Angaben. Vorschlag für den gemeinsamen rauschfreien
Erfolgsendpunkt: Kurve A, nachgewiesene Ringdown-Familie und gültiger
Definitionsbereich im vorab festgelegten Zeitfenster. Parameterabweichungen
werden zusätzlich ausgewiesen; etwaige Grenzwerte sind vorher festzulegen.

Die Kurvenskala verwendet jeweils den schlechteren relativen RMS- beziehungsweise
Maximalfehler aus Trainings- und Zwischenpunktraster. Beide Grenzen müssen
erfüllt sein; es gilt die beste erreichte Klasse:

| Klasse | Relativer RMS | Relativer Maximalfehler |
|---|---:|---:|
| A | <= 0,1 % | <= 1 % |
| B | <= 1 % | <= 2 % |
| C | <= 5 % | <= 10 % |
| D | übrige auswertbare Fälle | übrige auswertbare Fälle |

Nicht auswertbare Fälle erhalten einen eigenen Status, keine Klasse D.
Normierung erfolgt über Signalnorm beziehungsweise Spitzenamplitude,
nicht über den einzelnen Signalwert. Die implementierten Bewertungsverträge
sind die maßgebliche Quelle für exakte Grenzen und Rasterdefinitionen.

Für die Struktur gelten die drei Befunde „nachgewiesen passend“,
„nachgewiesen außerhalb der Zielklasse“ und „ungeklärt“. Gleichwertige
Exponential-, Sinus-, Kosinus- und Phasendarstellungen werden berücksichtigt.
Normalisiert wird eine Analysekopie; Definitionsbedingungen bleiben erhalten.
Positive Referenzfälle und Gegenbeispiele prüfen die Regeln.

Stetige Fortsetzung und quantifizierte Restterme bleiben eigene Befunde.
Soll daraus ein nachbearbeitetes Ausgabemodell entstehen, muss das Verfahren
vor der Bestätigung feststehen und anschließend in allen Vergleichsarmen
gleich angewendet werden. Original und bearbeitetes Modell getrennt berichten.

## 2. Vorhandene Kandidatenfronten diagnostizieren

Historische Originalauswahlen bleiben erhalten. Zusätzliche Diagnosen prüfen,
ob eine passende Formel in der Endfront vorhanden, aber nicht erkannt oder
nicht ausgewählt wurde; ob die richtige Familie schlechte Konstanten besitzt;
oder ob geeignete Kandidaten fehlen. Definitionslücken und zusätzliche Terme
werden separat erfasst.

Eine Endfront beschreibt nicht alle während der Evolution erzeugten Formeln.
Ein diagnostisch passender Kandidat ist kein nachträglicher Ersatz für die
ursprünglich ausgewählte Formel.

## 3. Erster Entwicklungsvergleich: Neustarts gegen längere Suche

Vorgeschlagenes Design bei unverändertem lokalem Profil 300/5
(300 Optimiereriterationen und fünf zusätzliche lokale Neustarts):

| Variante | Äußere Suche | Zweck |
|---|---|---|
| Referenz | 1 x 500 | Bisheriges Arbeitsprofil |
| Längerer Lauf | 1 x 2.000 | Nutzen einer fortgesetzten einzelnen Suche |
| Globale Neustarts | 4 x 500 | Nutzen unabhängig begonnener Suchen |

Entwicklungskontrollen: erfolgreicher Seed 20261201 und bisher erfolglose
Anker-Seeds 20261210 bis 20261212. Dies ist eine bewusst ausgewählte Diagnosemenge,
keine Schätzung einer allgemeinen Erfolgsquote. Zusätzliche Seeds und disjunkte
Seed-Blöcke vorab festlegen.

Bei nachweislich identischen Bedingungen kann jeder historische 500er-Lauf
als Referenz und erstes Mitglied seines Neustartpakets verwendet werden.
Dann sind 16 neue Suchaufrufe erforderlich: vier lange und zwölf zusätzliche
kurze Läufe. Andernfalls die Ausführungszahl vorab neu festlegen.

Ein Viererpaket liefert ein Algorithmusergebnis. Die Auswahlregel wird vorab
festgelegt und verwendet nur zulässige Trainingsdaten, Verlust und gegebenenfalls
Komplexität. Saubere Signalwahrheit, Strukturdiagnose und Diagnosepunkte dienen
nicht der Auswahl. „Passender Kandidat irgendwo vorhanden“ getrennt ausweisen.

Gemeinsame Kurven-/Strukturerfolge, kontinuierliche Fehler und tatsächliche
Kosten vergleichen. Historische Kosten bei Wiederverwendung mitzählen;
gleiche äußere Iterationssummen garantieren keine gleichen Rechenkosten.
Keine Fortsetzung durch zusätzliche Seeds bis zum gewünschten Ergebnis.

## 4. Zweite Intervention nur bei Bedarf

Priorität hat die Skalierung der Zeitkoordinate unter dem nun ausgewählten
Suchprofil, beispielsweise u = 32t für das bisherige Zeitfenster. Die Skalierung
wird aus dem Messfenster abgeleitet, nicht aus den wahren Signalparametern.
Einheiten, Auswertung und Rückrechnung der physikalischen Parameter festlegen.

Der frühere Skalierungsversuch mit lokal 20/2 und ausgeschalteten
Häufigkeitsschaltern beantwortet diese Kombination nicht. Dieselben
Entwicklungskontrollen und eine vorher festgelegte Vergleichsregel verwenden.

Vorerst unverändert lassen:

- `should_simplify=false`, bis der bekannte Fehler der Verlustkonsistenz
  durch eine gezielte technische Gegenprüfung beziehungsweise Backendkorrektur
  geklärt ist.
- Allgemeine Grammatik; ein Verbot trigonometrischer Verschachtelungen bleibt
  eine begründungsbedürftige Reserve, kein automatisch folgender Versuch.
- Weitere Populations-, Komplexitäts-, Mutations- und Optimierereinstellungen.

Kein Ringdown-spezifisches Vortraining und kein Template als stillschweigender
Ersatz für freie Formelfindung. Stärkeres Vorwissen wäre eine eigene Methode.

## 5. Suchprofil in den tatsächlichen späteren Laufweg übernehmen

Beim Codeabgleich auf main 46da82ec7bfe24614e0b3fc3203258535343d848 verwendete
`src/ringdown_sr/symbolic.py` im allgemeinen Suchprofil lokal 20/2 und
ausgeschaltete Häufigkeitsschalter. Die jüngsten rauschfreien Spezialversuche
verwendeten 300/5 und eingeschaltete Schalter. Dies ist bei Übernahme erneut
zu prüfen und vor dem Rauschpilot bewusst abzugleichen.

Das ausgewählte Profil einschließlich Zeitkoordinate, Vereinfachung,
Kandidatenauswahl und Nachbearbeitung in den tatsächlich vorgesehenen
Laufweg übertragen. Dort zuerst rauschfrei kontrollieren. Die gewichtete
Zielfunktion muss sowohl die Struktursuche als auch die lokale
Konstantenoptimierung bestimmen; eine Übernahme des Profils darf sie nicht
unbemerkt durch gewöhnliche MSE ersetzen.

## 6. Eingefrorene Bestätigung

Vorschlag: drei vorab bestimmte Signale, davon das Ankersignal und zwei bisher
ungenutzte Parameterkombinationen aus dem vorgesehenen Untersuchungsbereich;
je zehn neue unabhängige Seed-Blöcke. Das ergibt 30 Algorithmusergebnisse,
bei vier globalen Neustarts insgesamt 120 Suchaufrufe.

Vorgeschlagene praktische Grenze zum Rauschpilot: mindestens 8/10 gemeinsame
Kurven-/Strukturerfolge je Signal. Das ist kein Literaturstandard und kein
statistischer Nachweis einer wahren Erfolgswahrscheinlichkeit von mindestens
80 %. Erfolgszahlen, Unsicherheit und alle Fehlschläge berichten; keine
gepoolte Erfolgsquote über unterschiedliche Signale als Ersatz.

Ein vorab festgelegtes unregelmäßiges Prüfraster ergänzt die Diagnose gegen
Blindstellen regelmäßiger Raster. Es beeinflusst weder Kandidatenauswahl noch
nachträglich die historische A-D-Skala und ersetzt keinen Definitionsnachweis.

Nach Tuning an diesen Bestätigungsfällen gelten sie als Entwicklungsfälle.
Sie dürfen anschließend nicht als unberührte unabhängige Bestätigung auftreten.

## 7. Rauschpilot und Hauptversuchsplanung

Zunächst wenige Signale und Rauschbedingungen wählen. Rauschrealisierungen,
Hintergrunddaten und Suchseeds als unterschiedliche Zufallsquellen behandeln.
Mehrere Suchseeds auf einer einzigen Rauschrealisierung belegen keine allgemeine
Rauschrobustheit.

Gewichtungsverfahren anhand derselben Beobachtungsdaten und vorab bestimmten
Seed-Blöcke vergleichen. Kovarianz aus getrennten Hintergrunddaten bestimmen;
Regularisierung nachvollziehbar festlegen. Die resultierende Kovarianz bleibt
innerhalb der gesamten Suche einschließlich Konstantenoptimierung konstant.

Maßgeblich sind Fehler gegen das saubere Referenzsignal, Struktur,
Parameterabweichungen, Ausfälle und Kosten. Unterschiedlich gewichtete
Trainingsverluste sind kein gemeinsamer Qualitätsmaßstab zwischen Verfahren.
A-D bleibt eine beschreibende Skala; rauschfreies A ist unter Rauschen kein
automatisches allgemeines Bestehenskriterium.

Anschließend die Hauptstudie zur Hintergrunddatenmenge und Kovarianzgewichtung
anhand der Pilotergebnisse konkretisieren; den
[Kovarianzplan](covariance_method_plan.md) und
[SR-Methodenplan](symbolic_regression_method_plan.md) berücksichtigen.

## Grenze des Entwicklungszyklus

Höchstens zwei begründete Suchinterventionen, danach eine eingefrorene
Bestätigung und eine Entscheidung. Bei ausreichender Wiederholbarkeit zum
Rauschpilot übergehen. Andernfalls mit der Betreuung den Forschungsanspruch
festlegen: stärkeres Vorwissen als ausdrücklich benannte Variante oder eine
Untersuchung der Grenzen freier SR. Keine unbeschränkte Parametersuche.

## Vor dem jeweiligen Versuch noch festzulegen

- Zielintervall, zulässige Strukturbeweise und Ressourcenbegrenzung der Prüfung.
- Rolle möglicher Nachbearbeitung im endgültigen Ausgabemodell.
- Zusätzliche Seeds, genaue Auswahl- und Kostenvergleichsregel sowie
  Entscheidung zwischen den Entwicklungsvarianten.
- Unbenutzte Bestätigungssignale, unregelmäßiges Prüfraster und endgültige
  Fortsetzungskriterien; 8/10 je Signal ist zunächst ein Arbeitsvorschlag.
- Konkrete Rausch-, Hintergrund- und Gewichtungsbedingungen des kleinen Piloten.

## Literatur und Übertragungsgrenzen

Literaturangaben und ihre Einordnung stammen aus dem bereitgestellten Leitfaden.
In dieser Dokumentationsübernahme wurde keine erneute Literaturprüfung durchgeführt.

- [Cranmer (2023): PySR und SymbolicRegression.jl](https://arxiv.org/html/2305.01582v3).
  Evolutionäre Suche kann sich früh auf ungünstige Formklassen spezialisieren.
  Das motiviert den Suchvergleich, beweist aber keinen Vorteil von 4 x 500.
- [Kommenda et al. (2020): Parameter identification for symbolic regression](https://link.springer.com/article/10.1007/s10710-019-09371-3).
  Nichtlineare Konstantenanpassung kann trotz richtiger Struktur von Startwerten
  und lokalen Optima abhängen; kein Beleg für einen Defekt unseres Optimierers.
- [La Cava et al. (2021): Contemporary Symbolic Regression Methods](https://cavalab.org/assets/papers/La%20Cava%20et%20al.%20-%202021%20-%20Contemporary%20Symbolic%20Regression%20Methods%20and%20their.pdf).
  Numerische Genauigkeit und symbolische Wiederfindung unterscheiden;
  automatische Äquivalenzerkennung besitzt Grenzen. Die dortige Definition
  symbolischer Gleichwertigkeit wird nicht unverändert übernommen.
- [Aldeia et al. (2025): Next Generation of Symbolic Regression Benchmark](https://arxiv.org/html/2505.03977v1).
  Begrenzte Konfigurationsentwicklung, getrennte Bewertung, wiederholte Läufe
  und dokumentierte Rechenressourcen. Die dortigen 30 Wiederholungen sind
  nicht mit unseren zehn je Signal gleichzusetzen. Zufällige Datenaufteilungen
  werden nicht ungeprüft auf korrelierte Zeitreihen übertragen.
- [Tenachi et al. (2023): PhySO](https://arxiv.org/html/2303.03192v2).
  Gedämpfte Oszillatoren sind unter anderen Datenbedingungen und zusätzlichem
  physikalischem Vorwissen symbolisch rekonstruierbar. Das ist keine
  Erfolgsprognose für unseren Aufbau und verlangt kein Ringdown-Vortraining.
