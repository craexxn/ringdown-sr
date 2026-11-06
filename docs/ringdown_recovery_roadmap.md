# Leitfaden: wiederholbare Ringdown-Rekonstruktion und Übergang zu Rauschversuchen

Übernommener technischer Begleitauftrag zu Phase 1: Der
[CI-Sparplan](github_actions_savings_plan.md) bündelt lokale Prüfungen vor dem
Ready-Wechsel und führt native Kontrollen seriell aus. Die wissenschaftlichen
Phasen und Kriterien bleiben erhalten; tatsächlicher Prüf- und Übernahmestand
im [Fortsetzungsstand](representation_implementation_status.md).

Version 2, Planungsstand: 06.11.2026, nach Übernahme von PR #73 und #74.
Historische Konkretisierung am selben Tag nach PR #75: Phase 2 abgeschlossen;
[Protokoll](global_restart_comparison_plan.md) für Phase 3 vor Implementierung
eingefroren, [Laufweg](global_restart_comparison.md) in technischer Prüfung.
20 frische Suchaufrufe, vollständige Seeds und unabhängiges Zusatzraster sind
festgelegt. Keine wissenschaftliche Ausführung durch diese Planfortschreibung.
Version 1 wurde mit PR #69 eingeführt. Alle drei Bewertungsstufen sind mit
PR #69, #70 und #72 implementiert, technisch geprüft, übernommen und lesend
auf die 78 Originalauswahlen angewandt. Die [technische Optimierung](assessment_performance.md)
aus PR #73 und die [Archivregel](results_archiving.md) mit
[Ergebnisindex](results_index.md) aus PR #74 sind ebenfalls übernommen.
Sicherungskopien bleiben separat nachzuweisen.

Planergänzung vom 06.11.2026 während der erneuten PR76-Prüfung: der
[begrenzte Budgetvergleich](iteration_time_budget_plan.md) ergänzt Phase 3 um
2.000 Iterationen gegenüber 400 Sekunden im nativen Suchfenster. Vier gepaarte
Seeds, vorab festgelegte Wiederverwendung des gesamten PR76-Kontrollarms oder
vollständig frischer Ersatzmodus; keine zusätzliche offene Optimierungsschleife.
Der PR76-Versuch bleibt ein separater wissenschaftlicher Manjaro-Lauf.

Umsetzungsabgleich vom 06.11.2026: PR #76 ist nach korrigierten Schutzregeln,
gezieltem KI-Nachreview und vollständiger CI als `b547bb3` übernommen.
Der getrennte [Zeitbudgetlaufweg](iteration_time_budget.md) ist mit der
Veröffentlichungsvorbereitung nach vollständiger CI und separatem KI-Review
in PR #77 übernommen (`823732f`). Die Quellenprüfung zeigt
eine konkrete Wiederverwendungslücke: Das bisherige PR76-Format zeichnet die
tatsächlichen Julia-/GC-Threads und native CPU-Affinität nicht vollständig auf.
Serielle Suche und BLAS=1 ersetzen diesen Nachweis nicht. Der Import entscheidet
deshalb konservativ anhand der Originalbelege; ein ungeeigneter Kontrollarm
startet keinen automatischen Ersatzlauf. Das eingefrorene Design mit ausdrücklich
gewähltem `fresh_all` bleibt unverändert, ebenso PR76 und seine Originaldaten.

Dokumentationsabgleich vom 06.11.2026 zu Phase 1 und 3: Der
[Seed-/Treiber-Kreuzvergleich](seed_driver_crosscheck_results_manjaro_001.md)
ist nun am Originalarchiv verifiziert. Für den globalen Neustartvergleich ist
der [Abbruch von 001 und laufende Zwischenstand von 002](global_restart_results_manjaro_001.md)
übermittelt; daraus folgt noch kein wissenschaftlicher Vergleichsbefund.
Fehlende Primärbelege und Sicherungen werden im
[Ergebnisindex](results_index.md#priorisierte-fehlende-belege) priorisiert.
Dies ist Quellen- und Statuspflege, keine Änderung der Versuchspläne.

Die Planungsänderung vom 06.11.2026 zieht das unregelmäßige Zusatzraster in die
Entwicklungsphase vor, präzisiert frische Einzelsuchen gegenüber Fortsetzung
und trennt Gesamtkosten von neuem Aufwand. Zuerst erfolgt die
[begrenzte Endfrontdiagnose](endfront_diagnostic_001.md), anschließend die
Vorbereitung des Suchvergleichs. Wissenschaftliche Ausführung bleibt ein
separater Schritt. Historische Berichte und eingefrorene Protokolle bleiben
unverändert; deren damalige Ausblicke sind kein aktueller Arbeitsauftrag.

Diese Datei hält die vereinbarte Vorgehensrichtung fest. Konkrete Seeds,
Auswahlregeln, Budgets und noch offene methodische Einzelentscheidungen werden
vor Ausführung im jeweiligen Versuchsprotokoll festgelegt. Vorgeschlagene
Zahlen sind unten ausdrücklich gekennzeichnet. Die Roadmap dokumentiert keine
bereits erfolgte Implementierung oder wissenschaftliche Ausführung.

## Rolle und Pflege

- Die [Veröffentlichungsprüfung](publication_review.md) ergänzt die
  organisatorische Quellen- und Archivpflege aus Phase 1. Lizenzierung und
  Repository-Sichtbarkeit ändern weder die wissenschaftlichen Kriterien noch
  die Reihenfolge der Suchversuche; eine öffentliche Umstellung bleibt separat.
- Die [Archivierungsrichtlinie](results_archiving.md) und der
  [Ergebnisindex](results_index.md) ergänzen Phase 1 um die dauerhafte
  Zuordnung vorhandener Versuche, Quellen und Bewertungen. Die Regelung ist
  dokumentiert; Archivablage und zweite gesicherte Kopie bleiben separat
  nachzuweisen. GitHub-Releases sind eine optionale zusätzliche Ablage.
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

Pflegepräzisierung vom 06.11.2026: Nach jedem fachlichen Entscheid oder Versuch
die vorhandenen Quellen zu einer prüfbaren Kette verbinden:

1. Ausgangsproblem, datierte Entscheidung mit Begründung/Alternativen und Status
   im zuständigen Leitfaden- oder Methodenabschnitt festhalten: vorgeschlagen,
   beschlossen, implementiert, ausgeführt oder geprüft.
2. Auf eingefrorenen Plan samt Commit/Hash und vorhandene Konfiguration verweisen;
   Datenrollen, Seeds, Profil, Budget, Auswahl und Kriterien dort erhalten.
3. Im Ergebnisbericht tatsächlichen Ausführungsstand und Umgebung belegen,
   vollständige, fehlgeschlagene, abgebrochene und nicht ausgeführte Fälle sowie
   bekannten Aufwand nennen. Befehlsvorschläge und Schätzungen sind keine Messung.
4. Befunde, Gegenbefunde, Prüfumfang und Aussagegrenzen mit den unveränderten
   Originalen verbinden; technische Prüfung, wissenschaftliche Ausführung und
   retrospektive Bewertung trennen. Zulässige Konsequenz und offene Frage nennen.
5. Im vorhandenen Index Archivhash, Auffindbarkeit und tatsächliche Sicherung
   nachführen; README/Fortsetzungsstand knapp abgleichen. Keine zweite Chronik
   oder manuelle Kopie aller Manifestfelder anlegen.

Frühere Hauptstudienüberlegungen wie 2.048 äußere Iterationen bleiben historisch;
sie sind keine endgültige Budgetfestlegung. Das endgültige Profil und der
Kostenabgleich sind vor den späteren Hauptversuchen separat festzulegen.

## Ziel und Ausgangspunkt

Ziel ist eine wiederholt erfolgreiche freie Rekonstruktion der Ringdown-Familie

\[
g(t)=e^{-\gamma t}\,[a\cos(\omega t)+b\sin(\omega t)],
\qquad \gamma>0,\ \omega>0,\ a^2+b^2>0.
\]

Damit wird eine interpretierbare Grundlage für die Untersuchung von Rauschen,
Hintergrunddatenmenge und Kovarianzgewichtung geschaffen. Ein Fit mit bereits
vorgegebener Ringdown-Struktur bleibt ein privilegiertes Kontrollverfahren.

Der am 05.11.2026 zunächst übermittelte Befund zum
[Seed-/Treiber-Kreuzvergleich](seed_driver_crosscheck_results_manjaro_001.md)
ist seit der lesenden Originalarchivprüfung vom 06.11.2026 im beschriebenen
Umfang bestätigt: Seed 20261201 reproduziert unter dem Transferworker die
Staffelfront mit sieben Kandidaten und A-Auswahl; Seed 20261210 unter dem
Staffelworker die Transferfront mit elf Kandidaten und D-Auswahl. Tatsächlicher
Orchestrierungscommit, Archivhash, Prüfungen und Kosten stehen im Ergebnisbericht.

Für diese zwei gezielt gewählten Seeds am rauschfreien Ankersignal unter dem
gemeinsamen Einzelzelladapter folgt das gespeicherte Ergebnis dem Seed. Das
stützt die Untersuchung der Suchrobustheit und begründet ohne neuen Gegenbefund
keine weitere breite Treiberfehlersuche. Es beweist weder identische Suchverläufe,
allgemeine Implementierungskorrektheit noch eine bestimmte Erfolgswahrscheinlichkeit.
Eine automatische Budgeterhöhung folgt daraus nicht.

Die abgeschlossene [Kurvenbewertung](supplemental_assessment_results_001.md),
[Strukturprüfung](supplemental_structure_results_001.md) und
[Restdiagnose](supplemental_remainder_results_001.md) ändern die Einordnung:

- Die äußere Staffel aus PR #63 erreicht bei 500, 2.000 und 5.000 Iterationen
  jeweils 5/5 Klasse-A-Kurven und gültige Originalmitglieder der Ringdown-Familie.
  Die frühere Strukturzählung 4/5, 3/5, 2/5 beruhte auf Erkennungsgrenzen;
  die historischen Zählungen werden nicht rückwirkend ersetzt.
- Die frischen Referenz-Seeds aus PR #65 bleiben bei 0/3 A-Kurven. Daher hat
  Suchrobustheit Vorrang vor einer vollständigen formalen Entscheidung aller
  ungeklärten Schreibweisen.
- Unter 43 A-Kurven sind 38 gültige Originalmitglieder, zwei passende stetige
  Fortsetzungen bei Originaldefinitionslücken und drei ungeklärte Familienbefunde.
  Das beschreibt den Datenbestand, keine gepoolte Erfolgsquote. Die Restdiagnose
  beweist 41 Schranken, davon 40 Nullreste; diese Zählung ist ein anderer Endpunkt.
- Ein Familiennachweis bewertet neue Parameterübereinstimmungen weiterhin nicht.
  `new_parameter_match` bleibt ohne neuen dokumentierten Vertrag `not_assessed`.

Die Phasennummern sind von den abgeschlossenen drei Bewertungsstufen zu
unterscheiden. [Intervall-/Strukturregeln](supplemental_structure.md) und
[Resttermregeln](supplemental_remainder.md) einschließlich Ressourcen sind
beschlossen. Für zukünftige Läufe gelten weiterhin die gebundenen Datenrollen
und Raster des [Bewertungsvertrags](supplemental_assessment.md).

## Phasenfolge

| Phase | Arbeitspaket | Ergebnis beziehungsweise Entscheidung |
|---|---|---|
| 1 | Bewertung abgeschlossen | Kurve, Struktur, Definitionsbereich und Restdiagnose; neue Parametermatches nicht bewertet |
| 2 | Vorhandene Endfronten diagnostizieren | Erkennungs-, Auswahl-, Konstanten- und Suchprobleme unterscheiden |
| 3 | Globale Neustarts mit längeren Einzelsuchen vergleichen | Eine begründete Suchstrategie auswählen oder unzureichenden Nutzen festhalten |
| 4 | Nur bei Bedarf eine zweite Suchintervention | Zeitkoordinate unter dem aktuellen Profil prüfen |
| 5 | Ausgewähltes Profil in den späteren Laufweg übernehmen | Rauschfreie Kontrollausführung und korrekte gewichtete Optimierung nachweisen |
| 6 | Eingefrorene Konfiguration unabhängig bestätigen | Übergang zum Rauschpilot oder Entscheidung über den Forschungsanspruch |
| 7 | Kleiner Rauschpilot | Technische und methodische Grundlage für die Hauptversuchsplanung |

Die technische Vorbereitung der Rauschpipeline mit bekanntem Strukturfit kann
parallel erfolgen. Die freie SR wird im Rauschpilot nach Phase 6 untersucht.

## 1. Abgeschlossene Bewertungsgrundlage

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

Der [vorab festgelegte Umfang und Befund](endfront_diagnostic_001.md) priorisiert
die drei Transfer-Referenzfälle und begrenzt sich auf die vier großen Serien.
Keine Erkennerentwicklung zur Verbesserung der Erfolgszahlen. Fehlende Archive
bleiben sichtbar; nur vorhandene und gebundene Primärdaten dürfen als neue
Frontbefunde bestätigt werden. Der übermittelte Befund „kein anderer A-Kandidat
in den 15 Nicht-A-Fronten unter 362 Staffel-/Transferkandidaten“ wurde inzwischen
an den Originalarchiven bestätigt. Dasselbe gilt für alle 35 Nicht-A-Fronten
der vier Serien. Die drei Referenzfronten enthalten auch kein nachgewiesenes
Originalmitglied; fehlende Nachweise bleiben ungeklärt. Eine vollständige formale
Entscheidung aller offenen Formeln ist keine Voraussetzung für Phase 3.

## 3. Erster Entwicklungsvergleich: Neustarts gegen längere Suche

Beschlossenes Entwicklungsdesign bei unverändertem lokalem Profil 300/5
(300 Optimiereriterationen und fünf zusätzliche lokale Neustarts):

| Variante | Äußere Suche | Zweck |
|---|---|---|
| Referenz | 1 x 500 | Bisheriges Arbeitsprofil |
| Längerer Lauf | 1 x 2.000 | Nutzen einer frisch gestarteten längeren Einzelsuche |
| Globale Neustarts | 4 x 500 | Nutzen unabhängig begonnener Suchen |

Entwicklungskontrollen: erfolgreicher Seed 20261201 und bisher erfolglose
Anker-Seeds 20261210 bis 20261212. Dies ist eine bewusst ausgewählte Diagnosemenge,
keine Schätzung einer allgemeinen Erfolgsquote. Zusätzliche Seeds und disjunkte
Seed-Blöcke vorab festlegen. Eingeschaltete Häufigkeitsschalter, allgemeine
Grammatik, `should_simplify=false` und alle übrigen verifizierten Einstellungen
bleiben gleich. Vier globale Neustarts bedeuten vier vollständig neue SR-Suchen;
die fünf zusätzlichen lokalen Neustarts betreffen die Konstantenoptimierung.
Ein neuer 2.000er-Lauf mit demselben Seed ist ohne tatsächlich weiterverwendeten
Checkpoint keine Fortsetzung eines historischen 500er-Laufs.

Bei nachweislich identischen Bedingungen kann jeder historische 500er-Lauf
als Referenz und erstes Mitglied seines Neustartpakets verwendet werden.
Dann sind 16 neue Suchaufrufe erforderlich: vier lange und zwölf zusätzliche
kurze Läufe. Andernfalls werden genau 20 frische Suchaufrufe vorbereitet;
jede 500er-Referenz ist zugleich das erste Mitglied ihres Viererpakets.
Die Originalarchive sind geprüft; eine Wiederverwendung benötigt zusätzlich
die identischen tatsächlichen Ausführungsbedingungen des neuen Manjaro-Laufwegs.
Der startbare Standard wird deshalb der frische 20-Aufrufe-Pfad, ohne
stillschweigende Wiederverwendung. Ein späterer 16-Aufrufe-Pfad benötigt vorab
Quellen-, Daten-, Options-, Versions- und Kostenprüfung sowie dieselbe
vorher eingefrorene Paket-/Rasterregel.

Ein Viererpaket liefert ein Algorithmusergebnis. Die Auswahlregel wird vorab
festgelegt: niedrigster endlicher nativer Trainingsverlust, dann kleinste
Komplexität, dann die vorab gespeicherte Mitgliedsreihenfolge. Saubere
Signalwahrheit, Klasse, Strukturdiagnose und Diagnosepunkte dienen weder der
Auswahl noch dem vorzeitigen Beenden. „Passender Kandidat irgendwo vorhanden“
getrennt ausweisen. Ausfälle und nichtendliche Verluste bleiben im Nenner;
ein Paket ohne gültiges Mitglied liefert keine ausgewählte Ausgabe.

Gemeinsame Kurven-/Strukturerfolge, kontinuierliche Fehler und tatsächliche
Kosten vergleichen. Historische Kosten bei Wiederverwendung mitzählen;
gleiche äußere Iterationssummen garantieren keine gleichen Rechenkosten.
Keine Fortsetzung durch zusätzliche Seeds bis zum gewünschten Ergebnis.

Vor Implementierung wird das konkrete Protokoll eingefroren: alle 16 Seeds in
vier disjunkten Blöcken, Eingabebits, Versionen/Optionen, Ausfallbehandlung,
Endpunkte, Laufzeit und Zielfunktionsaufrufe sowie Anschlussentscheidung.
Historische Kosten zählen bei Wiederverwendung zum gesamten Algorithmusaufwand;
aktuell zusätzlicher Aufwand wird separat ausgewiesen. Ein Neustartvorteil
bleibt eine Hypothese, kein aus Literatur oder bisherigen Befunden abgeleitetes
Ergebnis. Wird ein konkreter technischer Fehler oder vorrangiger Engpass
nachgewiesen, wird dieser vor dem wissenschaftlichen Vergleich behandelt.

### Ergänzender begrenzter Halteregelvergleich

Am 06.11.2026 beschlossen: zusätzlich 2.000 äußere Iterationen gegen
400 Sekunden Backend-Suchzeit bei identischem 300/5-Profil vergleichen.
Die Zeit stammt aus ungefähr 400,34 Sekunden historischer mittlerer Fitzeit;
interne Suchzeit und Fit-/Workerzeit sind unterschiedliche Abschnitte, daher
keine exakte Kostenangleichung. Die Reserve 1.000.000 darf keine unbemerkte
Größenaufwärmung oder sonstige Änderung der Suchdynamik bewirken.
Timersemantik, Gegenprüfung und Interpretation stehen im
[eingefrorenen Protokoll](iteration_time_budget_plan.md).

Die vier PR76-Seeds bleiben gepaart. Vor Kenntnis ihrer wissenschaftlichen
Ergebnisse wird Wiederverwendung aller vier 2.000er-Kontrollen als Standard
festgelegt: vier neue Zeitläufe, vorher vollständige technische/methodische
Eignungsprüfung einschließlich Umgebung und Kosten. Fehlt dieser Nachweis,
ist ausschließlich der explizit gewählte Ersatzmodus mit allen vier Kontrollen
frisch zulässig: acht neue Suchen. Keine Mischgruppe oder ergebnisabhängige
Auswahl. Die Modusentscheidung wird vor dem ersten neuen Fit gebunden.

Mehr A bei höchstens gleichem gemessenem Workeraufwand ist ein Entwicklungssignal;
mehr A mit Mehrkosten ein Qualitätsgewinn mit Mehrkosten. Gleichstand belegt
keinen Kurvengewinn, weniger A eine Verschlechterung dieser Entwicklungsfälle.
Paare, Strukturänderungen, offene Beweise und unbekannte Kosten bleiben sichtbar.
Keine allgemeine Erfolgsquote, automatische Budgetstaffel oder neue offene
Suchintervention. PR76 wird separat ausgeführt und nicht ersetzt. Anschließend
bleiben bewusste Profilübernahme, gegebenenfalls Zeitnormalisierung als zweite
Intervention, unabhängige Bestätigung und Rauschpilot in der bestehenden Ordnung.

### Unregelmäßiges Zusatzraster bereits in der Entwicklung

Training und bisherige Zwischenpunkte liegen gemeinsam auf einem regelmäßigen
Raster von `1/32768` Sekunden. Dadurch existieren theoretische Frequenz-Aliase.
Ein unregelmäßiges Raster reduziert diese Blindstellen. Erzeugungsregel,
Punktzahl und eigener RNG-Seed werden vorab festgelegt; konkrete Punkte werden
vor der ersten Suche gespeichert und gehasht. Ein eigener Generator darf den
Zufallszustand der Suche nicht verändern.

Das Zusatzraster dient ausschließlich der Diagnose: kontinuierliche relative
RMS-/Maximalfehler berichten, ohne neue Grenzwerte keinen Bestehensmarker oder
nachträglichen Ausschluss erzeugen. Historische A–D-Klassen bleiben unverändert.
Das Raster ersetzt keinen Definitionsnachweis und garantiert keine allgemeine
Identifizierbarkeit. Familienzugehörigkeit und physikalische Parameter bleiben
getrennt; neue Parameterdiagnosen brauchen zuvor eine dokumentierte Regel.

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

Das bereits in Phase 3 vorab festgelegte unregelmäßige Prüfraster ergänzt die Diagnose gegen
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

- Zielintervall aus tatsächlichen Trainingsendpunkten, Strukturbeweise und
  Ressourcen gemäß bestehenden Verträgen anwenden; diese Regeln sind beschlossen.
- Rolle möglicher Nachbearbeitung im endgültigen Ausgabemodell.
- Zusätzliche Seeds, genaue Auswahl- und Kostenvergleichsregel sowie
  Entscheidung zwischen den Entwicklungsvarianten.
- Unbenutzte Bestätigungssignale und endgültige
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
