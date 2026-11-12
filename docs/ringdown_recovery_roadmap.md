# Leitfaden: wiederholbare Ringdown-Rekonstruktion und Übergang zu Rauschversuchen

Übernommener technischer Begleitauftrag zu Phase 1: Der
[CI-Sparplan](github_actions_savings_plan.md) bündelt lokale Prüfungen vor dem
Ready-Wechsel und führt native Kontrollen seriell aus. Die wissenschaftlichen
Phasen und Kriterien bleiben erhalten; tatsächlicher Prüf- und Übernahmestand
im [Fortsetzungsstand](representation_implementation_status.md).

Aktueller Ergebnisabgleich vom 12.11.2026: Die
[unabhängige Bestätigung](restart_confirmation_results_manjaro_001.md) aus Phase 6
ist einschließlich technischem Vorlauf auf main `c3da991` ausgeführt und vollständig
lesend geprüft. 150 frische Suchen; R erreicht 8/10, 10/10 und 4/10 gemeinsame
A-/Originalfamilienerfolge, I 4/10, 5/10 und 7/10. Damit ist die vorab beschlossene
8/10-Grenze je Signal verfehlt. Auch die nachträgliche Vereinigung beider Arme
erreicht nur 9/10, 10/10 und 7/10 gemeinsame Erfolge; sie belegt keine vorab
festgelegte kombinierte Auswahlstrategie. PR #82 ist samt dieser Ergänzung
übernommen. Die zweite Intervention ist inzwischen als
[Zeitkoordinatenvergleich](time_coordinate_results_manjaro_001.md) mit 16 frischen
Suchen auf main `91d461c` nach PR83 ausgeführt und vollständig lesend bestätigt.
Der Befund ist gemischt: u=32t verbessert die hohe und verschlechtert die niedrige
Variante. PR84 hat diesen Befund als `fbdb450` übernommen. Der Anschlussvergleich
4 × 1.000 gegen 2 × 2.000 ist inzwischen [vor Implementierung eingefroren](restart_budget_plan.md):
48 frische Suchen, 16 Paketausgaben und t als gemeinsame Referenzkoordinate;
kein Nachweis seiner Überlegenheit, siehe datierte Entscheidung in Phase 4. Ausführung dieses
Anschlussversuchs und spätere Bestätigung bleiben eigene Schritte;
kein unmittelbarer Rauschpilot. Historische
Protokolle, Seeds, Eingaben und Entscheidungsregeln bleiben eingefroren. Profilübernahme in
den allgemeinen gewichteten Laufweg bleibt vor einem späteren Rauschpilot
gesondert zu prüfen. Die folgenden datierten Einordnungen erhalten ihre Historie.

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
ist nun am Originalarchiv verifiziert. Die
[beiden frühen rauschfreien Serien](early_control_archive_audit_001.md) sind
ebenfalls an den nachgereichten Primärdateien bestätigt. Beim globalen Vergleich
ist [Abbruch 001](global_restart_results_manjaro_001.md) mit 19 fertigen Zellen,
unterbrochener Zelle 20, Teilkosten und gesperrter Freigabe geprüft.
Der getrennte [Lauf 002](global_restart_results_manjaro_002.md) ist nun vollständig
lesend bestätigt; ebenso der [Zeitbudgetlauf 001](iteration_time_results_manjaro_001.md)
mit acht frischen Suchen. Ihre getrennten Einordnungen folgen im Phase-3-Abschnitt unten.
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
Zahlen sind unten ausdrücklich gekennzeichnet. Planvorgaben allein belegen keine
Implementierung oder wissenschaftliche Ausführung; datierte Ergebnisabgleiche
verweisen dafür auf die jeweiligen Berichte.

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

### Ergebnis und Anschlussentscheidung vom 06.11.2026

Der [abgeschlossene Lauf 002](global_restart_results_manjaro_002.md) mit 20 frischen
Suchen erreicht 1/4 A bei der Referenz und jeweils 4/4 bei langen Suchen und
Neustartpaketen. A plus gültige Originalfamilie: 1/4, 3/4, 4/4; ein langer
A-Fall bleibt formal ungeklärt, ohne Definitionslücke. Die A-Zahl ist gegenüber
der Referenz verbessert, zwischen den beiden verbesserten Armen gleich.
Die eingefrorene Regel bevorzugt daher die Pakete anhand der vollständig
aufgezeichneten Verlustaufrufe: 8,24 % weniger als lange Suchen. Ihre summierte
Workerzeit ist allerdings 14,14 % höher. Keine allgemeine Erfolgswahrscheinlichkeit,
kein Laufzeitvorteil und keine automatische Profilumstellung ableiten.

Die bewusste Profilübernahme und unabhängige Bestätigung sind damit der
vorgesehene Anschluss. Der bereits separat eingefrorene begrenzte
Halteregelvergleich aus PR77 ist inzwischen ebenfalls abgeschlossen; Befund unten.
Die technische Eignungsprüfung von 002 bestätigt die fehlende historische
CPU-/Julia-/GC-Threadbindung aller vier Kontrollen. Die vorab begründete Wahl
`fresh_all` wurde mit acht frischen Suchen ausgeführt, ohne ergebnisabhängige
Kontrollauswahl oder Mischung mit historischen Zellen.
Zeitnormalisierung bleibt nur die bereits bedingt vorgesehene zweite Intervention;
dieser Befund begründet keine weitere offene Suchoptimierung. Vor dem Rauschpilot
Profil im allgemeinen Laufweg bewusst übernehmen und an unberührten Fällen
bestätigen; die Gewichtung muss Struktur- und Konstantensuche gemeinsam bestimmen.

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

### Ergebnis des Halteregelvergleichs vom 06.11.2026

[Zeitbudgetlauf 001](iteration_time_results_manjaro_001.md): alle acht Suchen
im frischen Modus abgeschlossen und lesend bestätigt. I erreicht 4/4 A,
Z 3/4 A; jeweils 3/4 A plus nachgewiesene Originalfamilie. Ein A-Verlust bei
Seed 20261211, keine A-Gewinne. Familiennachweise bleiben in diesem Paar
ungeklärt; keine Definitionslücke. Die eingefrorene Regel bewertet die
verringerte A-Zahl als Verschlechterung dieser Entwicklungsfälle. Insgesamt
12,51 % weniger Workerzeit und 13,32 % weniger Verlustaufrufe rechtfertigen
daher keine Übernahmeempfehlung für das 400-Sekunden-Profil. Alle Zeitläufe
enden regulär; kein technischer Fehler als Erklärung nachgewiesen.

Historische Planfortschreibung vom 06.11.2026; die spätere Konkretisierung steht
in Phase 6: kein nachträgliches Budgettuning oder weiterer Laufauftrag.
Die Viererpakete aus dem getrennten Neustartvergleich bleiben der Kandidat für
bewusste Profilübernahme und unabhängige Bestätigung. Zuerst Profil und
Bestätigungsprotokoll mit unberührten Fällen, Ausfall-/Kostenregeln und praktischer
Entscheidungsgrenze festlegen. Diese vier bekannten Seeds gelten nicht als
unabhängige Bestätigung. Unterschiedliche Worker-Messbereiche der beiden Serien
verbieten einen unmittelbaren Zeitkostenvergleich zwischen PR76-Paketen und
PR77-Zeitarm; keine gepoolte Erfolgsquote. Die späteren Phasen bleiben bestehen.

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

### Begrenzte Konkretisierung nach PR82, beschlossen am 12.11.2026

Auf die negative Bestätigung folgt der vor Implementierung eingefrorene
[Zeitkoordinatenplan](time_coordinate_plan.md), Umsetzung und Befehle im
[Laufweg](time_coordinate.md). Acht neue gepaarte Entwicklungsblöcke:
zwei anchor, zwei variant_low, vier variant_high. Je Block frische 1 × 2.000 in
t und 1 × 2.000 in u=32t, insgesamt 16 Suchen. Faktor 32 aus dem Messfenster,
beide Zeitkoordinaten in Sekunden; keine Ableitung aus wahren Signalparametern.
300 lokale Optimiereriterationen plus fünf zusätzliche Neustarts, Grammatik,
Häufigkeitsschalter, Vereinfachungsregel und alle übrigen Optionen unverändert.
Keine historischen Übernahmen oder Checkpointfortsetzungen.

Die Literatur und bisherigen Befunde begründen diese Frage, nicht einen Vorteil
der Skalierung. Die eingefrorene Richtungsregel vergleicht beide Endpunkte
pro Signal, lässt widersprüchliche Ergebnisse offen und verändert keine 8/10-Grenze.
Originalauswahl, physische Bewertung q(32t), Kosten und alle Ausfälle erhalten.
Das Zusatzraster bleibt diagnostisch; Parameterübereinstimmung bleibt `not_assessed`.
Bei zu großem physischem Kompositionsbaum greifen weiterhin die bestehenden
Beweisgrenzen; solche ungeklärten Fälle gesondert von Kurvenfehlern zählen.

Anschließend **4 × 1.000 gegen 2 × 2.000** mit derselben ausdrücklich gewählten
Koordinate und lokal 300/5 vergleichen: je 4.000 äußere Iterationen, nicht
notwendig gleiche Kosten. Dies ist ein begrenzter Folgeabgleich der Budgetaufteilung,
kein offener dritter Suchhebel. Zuvor eigene Seeds, Paarung, verlustbasierte
Paketwahl, Ausfall-/Kostenregeln und Anschlussentscheidung einfrieren; keine
automatische Ausführung oder Sprung zu 4 × 2.000. Bei gemischtem Koordinatenbefund
die Entscheidung dafür ausdrücklich begründen.

Die bisherige Bestätigung bleibt als negativer historischer Befund erhalten.
Ihre Signale gelten ab jetzt als Entwicklungswissen; spätere unabhängige
Bestätigung braucht unberührte Fälle. Die Grenze von höchstens zwei begründeten
Suchinterventionen und die anschließende Einordnung mit der Betreuung bleiben
bestehen. Keine weiteren Suchhebel oder Seeds bis zum gewünschten Erfolg anhängen.

### Befund und Anschlussentscheidung vom 12.11.2026

PR83 ist nach vollständiger CI als `91d461c` übernommen. Der
[Zeitkoordinatenlauf 001](time_coordinate_results_manjaro_001.md) ist auf diesem
Stand ausgeführt und vollständig lesend bestätigt: 16 wissenschaftliche Suchen,
vier technische Vorlaufworker separat, keine Ausfälle. Die eingefrorene
Einordnung lautet **gemischt**. T/U erreichen auf anchor je 2/2 A ohne
Familiennachweis, auf variant_low 2/2 gegen 1/2 A (gemeinsam 2/2 gegen 0/2),
auf variant_high 1/4 gegen 3/4 A (gemeinsam 1/4 gegen 2/4).

Bei sechs ausgewählten U-Formeln, darunter vier A-Kurven, überschreitet die
physische Komposition die bestehende 20-Knoten-Grenze. Diese Nachweise bleiben
ungeklärt; kein Suchfehler und kein Beleg einer falschen Familie. Schon die
Kurvenzahlen ohne Familienprüfung widersprechen einem einheitlichen Vorteil.
U benötigt beobachtet je Signal rund 10–15 % weniger Workerzeit; dies hebt
den Kurvenverlust auf der niedrigen Variante nicht auf. Keine gepoolte Erfolgsrate.

Für die Vorbereitung des separat einzufrierenden **4 × 1.000 gegen 2 × 2.000**
bleibt **T auf allen Signalen in beiden Armen die gemeinsame Referenzkoordinate**.
Begründung ist die gezielte Untersuchung der Budgetaufteilung bei fortgeführtem
Profil; kein nachgewiesener Sieg von T. U bleibt ein offener Entwicklungsbefund,
wird aber weder signalabhängig übernommen noch nachträglich mit T kombiniert.
Plan, neue Seeds, Paarung, verlustbasierte Paketwahl, Ausfälle, Kosten und
Anschlussregel vor Implementierung einfrieren. Dieser Ergebnisbefund startet
keine neuen Suchen und verändert weder den eingefrorenen Koordinatenplan noch
die negative unabhängige Bestätigung.

### Eingefrorener Budgetvergleich nach PR84, 12.11.2026

Der [Plan](restart_budget_plan.md) ist zusammen mit Seeds, Eingaben und Erzeuger
in `2cb96a7fef73a05e6c45564292dbce2c3d7f1583` vor Implementierung eingefroren.
R hat vier frische 1.000er-Mitglieder, L zwei frische 2.000er-Mitglieder;
ursprüngliches t und lokal 300/5 bleiben gleich. Zwei anchor-, zwei niedrige und
vier hohe Blöcke ergeben 48 Aufrufe, 16 ausgewählte Paketausgaben und 32 verschiedene
Seeds. Die ersten beiden Seeds jedes Blocks paaren beide Arme, ohne Suchzustände
weiterzugeben. Die stärkere Vertretung der hohen Variante behält den begrenzten
Entwicklungsumfang des Koordinatenversuchs bei; keine allgemeine Erfolgsquote.

Die eingefrorene Richtungsregel vergleicht A-Zahl und gemeinsamen Familienerfolg
je Signal: auf keinem Signal kleiner, mindestens ein gemeinsamer Erfolg größer.
Reiner A-Gewinn ohne gemeinsamen Gewinn und widersprüchliche Richtungen bleiben
gemischt; gleiche Zahlen bleiben gleich. Kosten beschreibend erhalten, kein
nachträglicher Kostengleichstandsentscheid und keine automatische Profilübernahme.
Alle Pakete/Mitglieder einschließlich Ausfällen behalten Nenner und Kosten.
Neue Seeds oder dritte Suchinterventionen bis zum gewünschten Erfolg sind
ausgeschlossen. Nach diesem begrenzten Abgleich folgt die begründete Einordnung
mit der Betreuung vor unabhängiger Bestätigung auf unberührten Fällen.

[Laufweg und Archivbefehle](restart_budget.md) werden technisch geprüft.
Zwölf winzige Kontrollworker prüfen beide Mehrmitgliedspakete; die wissenschaftliche
48-Aufruf-Serie bleibt ein gesonderter Manjaro-Schritt. Keine Änderung älterer
Pläne, Berichte, Bewertungsverträge oder praktischer Bestätigungsgrenzen.

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

Konkretisierung und Beschluss vom 09.11.2026 nach lesender Auswertung beider
Vergleiche und Übernahme von PR79: [Bestätigungsprotokoll](restart_confirmation_plan.md)
mit drei festen Signalen, davon der Anker und zwei bisher ungenutzte Kombinationen;
je zehn neue gepaarte Seedblöcke. Viererpakete mit je 500 Iterationen gegen eine
frische 2.000er-Kontrolle, beide bei lokal 300/5. 30 Paketausgaben plus 30
Kontrollausgaben aus insgesamt 150 Suchaufrufen. Die frühere 120-Aufruf-Variante
betrachtete nur das ausgewählte Profil; 30 lange Kontrollen kommen für den
beschlossenen direkten Vergleich hinzu. Keine erneute offene Budgetoptimierung.

Praktische Grenze für das vorab ausgewählte Neustartprofil beschlossen:
**mindestens 8/10 gemeinsame A-/Originalfamilienerfolge je Signal**.
Offene Familienbeweise sind keine bestätigten gemeinsamen Erfolge und kein
Nachweis der Nichtzugehörigkeit. Die Grenze ist kein Literaturstandard,
kein statistischer Nachweis von mindestens 80 % wahrer Erfolgswahrscheinlichkeit
und kein Überlegenheitskriterium gegenüber der langen Suche. Beide Arme,
Paarungen, Ausfälle, marginale Unsicherheitsintervalle und reale Kosten berichten;
keine gepoolte Erfolgsquote über unterschiedliche Signale.

Drei getrennt ausführbare, vorher vollständig geplante Signalabschnitte mit
je 50 Aufrufen erlauben Pausen. Die gemeinsame Entscheidung erfordert die
lesende Prüfung aller Abschnitte mit gleicher Herkunft und numerischer Umgebung.
Auch nach einem negativen ersten Abschnitt bleiben die weiteren vorgesehen.
Kein Resume oder automatischer Wiederholungsauftrag nach Abbruch. Seeds,
Signale, Reihenfolge, Auswahl, Kosten und Fristen stehen im eingefrorenen Plan;
[Bedienung](restart_confirmation.md), tatsächliche Prüfungen und Ausführung
im [Fortsetzungsstand](representation_implementation_status.md) getrennt führen.

Das unregelmäßige Prüfraster bleibt ausschließlich diagnostisch. Historische
A–D-Regeln, Struktur-/Restverträge und Parameterstatus bleiben erhalten. Tuning
an Bestätigungsfällen würde sie zu Entwicklungsfällen machen. Vor dem Rauschpilot
ist das geprüfte 300/5-Profil im allgemeinen späteren Laufweg ausdrücklich zu
übernehmen; seine Gewichtung muss Struktur- und Konstantensuche bestimmen.
Die jetzige rauschfreie Bestätigung allein belegt diesen gewichteten Pfad nicht.

### Bestätigungsbefund und Planfortschreibung vom 12.11.2026

Die [vollständig geprüfte Serie 001](restart_confirmation_results_manjaro_001.md)
umfasst alle 150 geplanten Suchen und den technischen Manjaro-Vorlauf.
R erzielt auf anchor/variant_low/variant_high 10/10, 10/10, 4/10 A-Ausgaben,
davon 8/10, 10/10, 4/10 mit gültiger Originalfamilie. I erzielt 5/10, 7/10,
7/10 A, davon 4/10, 5/10, 7/10 gemeinsam. Die praktische Grenze ist beim dritten
Signal verfehlt; dort sind alle A-Familien nachgewiesen, sodass offene
Strukturbeweise den A-Verlust nicht erklären. Keine Ausfälle, alle Kosten bekannt.
R benötigt je Signal rund 22–26 % mehr Workerzeit und geringfügig weniger
Verlustaufrufe. Weder allgemeine Überlegenheit noch Laufzeitgewinn bestätigt.

Die am 12.11.2026 ergänzte [Kombinationsdiagnose](restart_confirmation_results_manjaro_001.md#nachträgliche-kombination-beider-arme)
zählt je Block höchstens einen Erfolg aus den beiden Originalausgaben:
9/10, 10/10 und 7/10 A plus Originalfamilie. Bei variant_high ergänzen die
R-Ausgaben keinen I-Erfolg; beide Arme verfehlen A in Block 1, 5 und 7.
Damit schließt auch diese Rückschau die Wiederholbarkeitslücke nicht.
Die Verwendung nachträglicher Klassen-/Familienkenntnis ist keine zulässige
Auswahlregel eines neuen Verfahrens. Eine tatsächliche Kombination benötigte
eine vorab festgelegte Auswahl und die Kosten aller fünf Suchen mit insgesamt
4.000 äußeren Iterationen je Block; sie ist hier nicht bestätigt oder beschlossen.

Die begrenzte Diagnose aller gespeicherten Fronten findet auch in den sechs
Nicht-A-Paketen des dritten Signals keine alternative A-Ausgabe. Das belegt
keine vollständige Evolutionsgeschichte und identifiziert noch keine konkrete
Suchursache. Die drei Signale erlauben keine isolierte Erklärung durch Frequenz
oder einen anderen gleichzeitig veränderten Parameter.

Historische Einordnung vor der oben datierten Konkretisierung von Phase 4:
Gemäß eingefrorenem Plan den Befund und Forschungsanspruch mit der
Betreuung einordnen: Grenzen freier SR oder stärkeres Vorwissen als ausdrücklich
benannte Variante. Die Grenze nicht nachträglich lockern, keinen jeweils besten
Arm als Ersatz auswählen und keine zusätzlichen Seeds bis zum Erfolg anhängen.
Die bereits bedingt vorgesehene Zeitnormalisierung bleibt eine begründungsbedürftige
zweite Intervention, kein automatischer Laufauftrag. Tuning an diesen Fällen
würde sie zu Entwicklungsfällen machen. Der Rauschpilot folgt nicht unmittelbar
auf diese verfehlte Bestätigung; seine Voraussetzungen und die bewusste
Profilübernahme aus Phase 5 bleiben bestehen.

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
- Seeds, Bestätigungssignale, Auswahl-/Kostenregeln und 8/10-Grenze sind
  im Bestätigungsprotokoll vom 09.11.2026 festgelegt; Umsetzung, vollständige
  technische CI, separates Review und Übernahme sind mit PR #80 abgeschlossen.
  Technischer Manjaro-Vorlauf und wissenschaftliche Serie sind inzwischen
  vollständig lesend bestätigt; die praktische Grenze ist verfehlt. Der nächste
  Schritt ist die oben datierte Einordnung, keine automatische Wiederholung.
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
