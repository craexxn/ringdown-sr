# Entwurf: Begrenzte Beobachtung der freien Suche

Stand: 02.11.2026. **Vorschlag zur Methodenentscheidung, nicht eingefroren.**
Dieser Text ist kein Laufzeitinput und erteilt keine Freigabe für neue Suchen.
Bestehende vier Laufzeitpläne bleiben unverändert.

## 1. Anlass, Frage und Anspruch

Der [freie Budgetvergleich](free_optimizer_budget_results_manjaro_001.md)
berichtet 0/3 erfolgreiche Originalauswahlen unter 20/2 und 100/2.
100/2 verringert MSE und RMS bei allen drei Entwicklungsseeds, ohne eine
erfolgreiche freie Rekonstruktion zu erreichen. Die sechs Originalauswahlen
enthalten keinen Exponentialfaktor. Der Befund beruht auf übermittelten
Auszügen und eigener Nachrechnung der Anzeigeformeln; ein unabhängiger Audit
des neuen Originalarchivs bleibt offen.

Die Endfront beantwortet nicht, welche Bäume zuvor in Populationen vorkamen.
**Vorgeschlagene Frage:** Welche exponentiellen und vom bestehenden Erkenner
unterstützten Strukturen sind an festen Rückgabepunkten des unveränderten
100/2-Suchprofils sichtbar, wie gut passen diese beobachteten Bäume und welche
von ihnen erscheinen in der endgültigen exportierten Front?

Das ist eine deskriptive Beobachtung an bekannten Entwicklungsdaten.
Sie identifiziert keinen kausalen Engpass und keine Erfolgswahrscheinlichkeit.
Wahrheit oder konstruierte Ringdown-Bäume gelangen weiterhin nicht in die Suche.

## 2. Entscheidungsvorschlag und Alternativen

Vorgeschlagen ist genau eine weitere, begrenzte Diagnose: drei beobachtete
100/2-Läufe, jeweils mit einem frischen unbeobachteten Kontrolllauf.
Beobachtet werden ausschließlich feste Populationsrückgaben; Mutation,
Akzeptanz, Einheitenprüfung und Optimierer werden nicht instrumentiert.

100/2 wird gewählt, weil dieses Profil im abgeschlossenen Vergleich bei
allen drei Seeds kleinere MSE/RMS liefert. Das ist eine adaptive Wahl anhand
bekannter Ergebnisse und keine Festlegung eines Produktionsprofils.
Die Kontrollen sind neue Diagnoseläufe, keine Reparatur oder Wiederholung
des abgeschlossenen Budgetvergleichs. Historische 100er-Ergebnisse werden
daneben berichtet, ersetzen aber keinen aktuellen Kontrolllauf.

| Alternative | Erkenntnisgewinn / Grenze | Vorschlag |
| --- | --- | --- |
| Weitere Budgeterhöhung | Weitere Approximation möglich; erklärt die bisherigen Verläufe nicht | Zurückstellen |
| Vollständige Mutations- und Optimiererhistorie | Feinere Entstehungs-/Verwerfungsfragen; zusätzliche Eingriffe, Datenmenge und Neutralitätsrisiken | Für diesen Schritt zurückstellen |
| Nur Populationsaufnahmen ohne frische Kontrollen | Weniger Rechenaufwand; kein gepaarter Nachweis unveränderter exportierter Suchresultate | Nicht wählen |
| Grammatik oder Modellfamilie einschränken | Stärkerer Strukturprior, möglicherweise enger und planbarer | Legitime Alternative; Forschungsanspruch und Referenzvergleich gesondert beschließen |
| Freie Rekonstruktion vorläufig pausieren | Aufwand begrenzen und vorhandene Befunde ausarbeiten | Legitime Alternative vor oder nach dieser Diagnose |

Das übermittelte KI-basierte Methodenreview empfiehlt diesen begrenzten
Entwurf nach Korrektur der Interpretationsregel in Abschnitt 7.
Vor Implementierung bleibt zu entscheiden, ob der deskriptive Erkenntnisgewinn
den Aufwand rechtfertigt: genau diesen Plan annehmen oder eine Alternative
wählen. Eine Änderung der Fragestellung oder zusätzliche Arme werden nicht
während der Ausführung ergänzt.

## 3. Konkreter Beobachtungspunkt im gepinnten Backend

Gelesene Primärquellen: SymbolicRegression.jl `v2.5.1`,
[Plugin.jl](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/Plugin.jl#L199)
und
[Suchschleife](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/SymbolicRegression.jl#L1154).

Der Hook `on_generation_end!` liefert die zurückgegebene Population und
den Suchzustand. Zu diesem Zeitpunkt sind Vereinfachung und lokale
Konstantenanpassung beendet, die globale Hall of Fame ist aktualisiert;
Migration in die zurückgegebene Population erfolgt anschließend.
Der Name des Hooks rechtfertigt keine Gleichsetzung mit jeder einzelnen Mutation.

Der erste Entwurf verwendet nur diesen Hook. Er sieht weder jeden
Mutationsvorschlag noch einen isolierten Zustand vor/nach jeder
Konstantenoptimierung. `on_mutation_end!` liefert keine Vorschlagsbäume;
das native Tracing ist keine vollständige Sammlung exakter exportierter
Bäume aller verworfenen Vorschläge. Eine Ausweitung auf diese Ebenen wäre
ein anderer Plan.

Aufnahme von:

- allen 32 Mitgliedspositionen der zurückgegebenen Population;
- allen belegten Komplexitätsplätzen 1 bis 20 der globalen Hall of Fame;
- unverändertem Originalbaum mit Operator- und Variablenkennung,
  Float64-Konstantenbits, vorhandenen Loss-/Cost-Werten und deren
  Verfügbarkeitsstatus, bestehendem Komplexitätscache, `birth`, `ref`, `parent`.

Der Hook besitzt kein explizites Argument für Populations- oder
Suchiterationsindex. Daher eigene Datensatz-ID aus Zellnummer,
fortlaufendem `event_index`, Quelle `returned_population` beziehungsweise
`hall_of_fame` und Mitgliedsposition. Keine erfundenen Populationskennungen
oder Abstammungsketten. Backend-Referenzen bleiben zusätzliche Metadaten.

Die Hall of Fame ist ein kumulierter Beststand je Komplexität; wiederholtes
Vorkommen zählt nicht als neue unabhängige Entdeckung. Sie enthält auch
`best_seen`-Einträge aus dem Worker, ohne deren vollständige Vorgeschichte.

## 4. Vorgeschlagene sechs Zellen und Grenzen

Alle sechs Läufe verwenden ursprüngliche Sekundenkoordinaten, 100 maximale
lokale Optimiereriterationen, zwei zusätzliche Neustarts und beide
Häufigkeitsschalter. Je 200 Suchiterationen, zwei Populationen zu 32
Individuen, 50 Zyklen, Knoten-/Tiefenlimit 20, bestehende Operatoren,
Float64 und serielles deterministisches Profil. Pins, Einheitenregeln,
Optimierertoleranzen und numerischer Verlustkern wie im
[Budgetplan](free_optimizer_budget_plan.md).
Haswell und alle vier Threadlimits auf 1 gelten nur für diese Diagnose.

| Zelle | Seed | Beobachtung |
| --- | ---: | --- |
| 1 | 20261020 | aus |
| 2 | 20261020 | an |
| 3 | 20261021 | an |
| 4 | 20261021 | aus |
| 5 | 20261022 | aus |
| 6 | 20261022 | an |

Die 2:1-Asymmetrie der Paarreihenfolge bleibt sichtbar; keine Schätzung
einer Reihenfolgewirkung aus sechs Läufen.
Kontrolle und Beobachtung starten jeweils in einem frischen Prozess.
Keine Warmstarts, Ersatzseeds, Referenzformeln oder Startkoeffizienten.

Vorgeschlagen werden alle 400 eingesammelten Populationsrückgaben pro
beobachtetem Lauf, entsprechend 200 Suchiterationen mal zwei Populationen.
Das sind höchstens 20800 Mitgliedsdatensätze je beobachtetem Lauf,
insgesamt 62400, einschließlich Hall-of-Fame-Wiederholungen.
Keine adaptive Ausdünnung nach Verlust, Struktur oder Erfolg.

Die serielle Backend-Schleife kann zusätzliche Workerarbeit bereits
ausführen, deren Rückgabe vor dem Ende nicht mehr eingesammelt wird.
Die Aufnahmezahl beschreibt ausdrücklich Rückgaben, nicht sämtliche
Dispatches oder alle berechneten Populationen. Hookzahl und Reihenfolge
müssen zunächst am gepinnten technischen Pfad bestätigt werden.
Bei Abweichung den Entwurf korrigieren, bevor wissenschaftliche Läufe
freigegeben werden; nicht still andere Beobachtungspunkte einsetzen.

Vorgeschlagene organisatorische Obergrenzen:

- 60 Minuten für Vorprüfungen, sechs Worker, nachgelagerte Auswertung
  und Abschlussverifikation zusammen;
- höchstens 600 Sekunden je Worker, zusätzlich zum verbleibenden Gesamtlimit;
- höchstens 256 MiB unkomprimierte Beobachtungsdateien je beobachteter Zelle,
  768 MiB insgesamt; laufende Zählung der tatsächlich geschriebenen Bytes.

Die Zeit- und Speichergrenzen sind organisatorische Entscheidungen,
keine aus bisherigen Laufzeiten abgeleiteten Garantien.
Bei Überschreitung oder Schreib-/Verifikationsfehlern stoppen, Teilstände
erhalten und Auswertung als unvollständig kennzeichnen. Keine still
verworfenen Aufnahmen, automatische Wiederholung oder Budgeterhöhung.
Nach genau sechs vollständigen Zellen endet die Diagnose unabhängig
davon, ob interessante Strukturen sichtbar sind.

## 5. Datenrollen und technische Nichtbeeinflussung

Die Trainingsdaten bleiben die identitätsgeprüften 128 Werte des
Originalarchivs `representation-manjaro-001.tar.gz`, SHA-256
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Nur Trainingszeiten und Beobachtungen gelangen in die Suche.
Diagnosepunkte, Wahrheit und Strukturerkenner werden ausschließlich nach
Suchende auf die gespeicherten Bäume angewandt.

Der Beobachter kopiert bestehende Werte in seinen eigenen Zustand beziehungsweise
Export. Keine zusätzlichen Aufrufe von Loss, Konstantenoptimierung,
Vereinfachung, Komplexitätsberechnung mit Cacheänderung oder Zufallszahlengenerator.
Insbesondere keine normalen neuen PopMember-Konstruktionen:
[PopMember.jl](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/PopMember.jl)
erzeugt dabei Referenzen über `rand(Int)`. Kopierpfad und Serializer müssen
nachweislich bestehende Referenzen und numerische Bits erhalten.

Der Beobachter wird als ausdrücklich erlaubtes zusätzliches Plugin hinter
den bestehenden Plugins geführt. Reihenfolge und konkrete Felder aller
bestehenden Plugins bleiben absolut geprüft. Das ganze Pluginfeld darf
nicht aus Verifikationssignaturen entfernt werden. Ein gemeinsamer neuer
Verifikationswrapper muss in Kontroll- und Beobachtungsarm identisch sein;
er delegiert an denselben bisherigen numerischen Callback.

Vor einer wissenschaftlichen Ausführung erforderlich:

1. Durchleitung des eigenen Plugins durch tatsächlich installiertes PySR
   2.6.0 und native Optionsobjekte ohne Fit prüfen. Die Julia-Schnittstelle
   ist quellengeprüft; das übermittelte Methodenreview bestätigt auch die
   vorgesehene Durchleitung im PySR-2.6.0-Quellcode. Der tatsächliche
   technische Nachweis mit dem eigenen Beobachter bleibt erforderlich.
2. Technische Beispielpopulationen einschließlich nichtendlicher Werte:
   Baum-Roundtrip, Konstantenbits, Slots und Backendmetadaten prüfen.
   Hookaufrufe dürfen RNG, Originalpopulation, Caches und bestehende
   Pluginzustände nicht verändern. Keine Wahrheit zur Laufzeitklassifikation.
3. Drei frische technische Worker aus/an/aus mit 100/2 und zwei
   Suchiterationen auf einem eigenen linearen Achtpunkt-Signal.
   Vollständige Originalfronten, Reihenfolge, Auswahl, Vorhersagen,
   Residuen, Verluste und Fit-Callbackzahlen müssen übereinstimmen.
   Hookanzahl und Vollständigkeit der Aufnahmen explizit prüfen.
4. Fehlergegenfälle zu Abbruch, Speicher-/Zeitgrenze, fehlenden oder
   doppelten Ereignissen und späteren Artefaktänderungen; vollständige
   technische CI am Implementierungsstand.

Je wissenschaftlichem Seed anschließend dieselben exportierten
Suchresultate des frischen Kontroll-/Beobachtungspaars vergleichen,
einschließlich exakter Baumkonstanten und Callbackzahlen.
Geplante Unterschiede wie Beobachtungsdateien, Laufzeit und Ausgabepfad
dürfen nur nach Einzelprüfung aus dem Gleichheitsvergleich ausgeschlossen werden.
Nicht vergleichbare und nichtendliche Werte nicht als Gleichheit umdeuten.

Eine Paarabweichung stoppt die Serie und sperrt die vergleichende
Suchverlaufsinterpretation. Auch eine technisch interessante beobachtete
Formel hebt diese Sperre nicht auf. Übereinstimmung belegt Nichtbeeinflussung
nur für die geprüften exportierten Größen und Fälle; sie beweist keine
Identität sämtlicher unbeobachteter Zwischenzustände.
Historische Abweichungen gegenüber dem alten 100er-Lauf gesondert dokumentieren,
nicht durch neue Versuche angleichen.

## 6. Nachgelagerte Auswertung und Erfolgstrennung

Gespeicherte Bäume werden anhand exakter Originalkonstanten und Operatorreihenfolge
identifiziert. Rohaufnahmen und wiederholte Mitgliedspositionen bleiben erhalten;
eine zusätzliche deduplizierte Auswertung darf ihre Nenner nicht ersetzen.
Eine Strukturkennung ohne Konstantenwerte bezeichnet nur eine Baumform.

Für die beobachteten Mitglieder getrennt ausweisen:

- Zahl der Aufnahmen, Mitgliedspositionen und eindeutigen vollständigen Bäume;
  Zeitachse ausschließlich als Ereignisordinal, keine unabhängigen Wiederholungen.
- Explizites Vorkommen eines `exp`-Operators; das allein ist keine
  Ringdown-Strukturerkennung und kein Nachweis einer abklingenden Hüllkurve.
- Bestehende Strukturerkennung, Erstgründe und Parameter-/Replaystatus.
  Vollständige Originalbaumauswertung auf Training und den 889 Diagnosepunkten,
  ursprüngliche Fehlernormalisierung und unveränderte Kurvengrenzen.
- Nachrechnung gespeicherter gewöhnlicher Trainingsverluste, soweit numerisch
  und semantisch auswertbar. Ungültige Einheiten oder nichtendliche Mitglieder
  bleiben mit Status sichtbar und zählen niemals als Erfolge.
  Export-/Verifikationsfehler sind von gültigen schlechten Suchmitgliedern zu trennen.
- Erstes/letztes beobachtetes Auftreten und Anzahl der Aufnahmen je vollständigem
  Baum beziehungsweise gesondert je Baumform, getrennt nach zurückgegebener
  Population und globaler Hall of Fame. Die Zugehörigkeit zur endgültigen
  exportierten Originalfront ist ein eigenes Merkmal ohne zeitliche Aussage.
- Aufwand für Suche, Beobachtung und Offline-Auswertung getrennt. Callbackzahlen
  bleiben keine Zahl eindeutiger Strukturen oder tatsächlicher Optimiererschritte.

Nachbeobachtete Zwischenbäume ersetzen niemals die ursprüngliche Auswahl.
Ein kurvenguter beobachteter Baum wird als solcher beschrieben; unterstützte
Parameter verlangen zusätzlich dieselben bisherigen Struktur-/Replaygates.
Der primäre Rekonstruktionsbefund der endgültigen Originalauswahl bleibt separat.
`physical_identification` bleibt `not_assessed`; Alias-Blindfleck bei `8*fs`
unverändert.

## 7. Interpretations- und Weiterentscheidungen

Vollständige Interpretation erst bei sechs vollständigen Zellen,
drei bestandenen Paarvergleichen, vollständigen Beobachtungsdaten und
bestandener Abschlussverifikation. Sonst nur gekennzeichnete Einzelbefunde.

| Beobachtung | Zulässiger Befund / nächste Entscheidung |
| --- | --- |
| Kein unterstützter Baum an den festen Beobachtungspunkten | In diesen Aufnahmen nicht gesehen; nicht „nie erzeugt“. Keine automatische Ausweitung auf Mutationshistorie. Eingrenzung/Pause oder neuer begründeter Plan entscheiden. |
| Unterstützte Strukturen vorhanden, aber Kurvengrenzen verfehlt | Passende Baumformen sind an Rückgabepunkten vorhanden, ihre beobachteten Konstanten passen unzureichend. Kein isolierter Nachweis eines Optimiererengpasses. |
| Kurvenguter beobachteter Baum nicht in der endgültigen Front enthalten | Beobachtet, aber nicht in der endgültigen Front enthalten. Daraus folgt kein zeitliches Verschwinden aus Population oder Hall of Fame. Keine nachträgliche Ersatzwahl. |
| Gute Frontkandidaten vorhanden, Originalauswahl unzureichend | Separate Auswahlfrage; Kriterien nicht nachträglich umstellen. |
| Erfolgreiche Originalauswahl | Entwicklungsbefund dieses frischen Laufs; keine nachträgliche Änderung des alten Budgetvergleichs und keine Freigabe einer allgemeinen Rauschstudie. |
| Beobachter verändert exportierte Ergebnisse oder Daten fehlen | Nichtbeeinflussung/Vollständigkeit nicht bestätigt; keine vergleichende Suchverlaufsaussage. Technisches Vorgehen gesondert entscheiden. |

Die [Pareto-Filterung des gepinnten Backends](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/HallOfFame.jl#L163)
übernimmt einen vorhandenen Hall-of-Fame-Baum nur, wenn sein Trainingsverlust
strikt kleiner als der jedes vorhandenen einfacheren Baums ist.
Ein einfacherer Baum mit kleinerem oder gleichem Verlust kann ihn daher aus
der Front ausschließen, obwohl er weiterhin seinen Hall-of-Fame-Platz belegt.
Die Filterfunktion verändert diese Belegung nicht.

Gezielter synthetischer, dimensionsloser Gegenfall: Für `y=1+t` besteht
auch `q=t+exp(0.0001*t)` auf den 128 Trainings- und 889 Diagnoseabzissen
beide Kurvengrenzen. Eigene Float64-Nachrechnung ergibt relativ etwa
`1.77e-6` RMS und `3.01e-6` Maximum; die Trainings-MSE beträgt etwa
`3.22e-12`. Der einfachere exakte Baum `1+t` hat Verlust null und
schließt `q` aus der Front aus, ohne dessen Hall-of-Fame-Platz zu leeren.
Das ist eine Gegenprüfung der Interpretationsregel ohne Suche oder Fit,
kein Nachweis eines tatsächlichen Ringdown-Suchverlaufs.

Ein späteres Fehlen muss anhand der entsprechenden Aufnahmen getrennt
für Population und Hall of Fame belegt werden. Dabei muss die betrachtete
Population vergleichbar sein: Fehlen in einer später zurückgegebenen
anderen oder nicht zuordenbaren Population belegt kein Verschwinden aus
der zuvor beobachteten Population oder allen Populationen.
Ohne diese Zuordnung nur das Vorkommen in den jeweiligen Aufnahmen berichten.
Auch ein belegtes Fehlen zu einem späteren Aufnahmezeitpunkt beweist kein
dauerhaftes Verschwinden zwischen oder nach den Aufnahmen.

Mehrere Beobachtungen können gleichzeitig zutreffen und werden gemeinsam
berichtet. Frontzugehörigkeit, beobachtetes zeitliches Auftreten und
Strukturstatus bleiben getrennt. Aus diesen Merkmalen folgt ohne
entsprechende Ereignisdaten keine konkrete Mutations-, Selektions- oder
Optimierungsgeschichte.

## 8. Beschluss- und Prüfstatus

Beauftragt sind Ergebnisdokumentation und Ausarbeitung dieses Vorschlags.
Zahlen, Messpunkte und Grenzen dieses Entwurfs sind noch nicht angenommen.
Noch keine neue Implementierung, kein technischer Beobachtertest und
kein wissenschaftlicher Diagnoselauf.

Übermitteltes KI-basiertes Methodenreview zu
[PR #46](https://github.com/craexxn/ringdown-sr/pull/46):
Head `aa04a9c49de331c878669907b1bc6a246918d704`,
Basis `8bdc8dbc498be6e8527fa2a857293bf74b42f81f`.
Geprüft wurden die vier Dokumentationsänderungen, Arbeitsregeln und
relevanten Backendquellen. Ein P2-Befund zur Gleichsetzung fehlender
Frontzugehörigkeit mit zeitlichem Verschwinden; keine weiteren
korrekturbedürftigen Befunde berichtet. Die Regel ist hier korrigiert
und anhand der Backendquelle sowie des synthetischen Gegenfalls gezielt
gegengeprüft. Eine erneute vollständige Methodenrunde ist nicht erforderlich.
Vollständiger Korrekturcommit und seine Dokumentationsprüfungen stehen im PR.

Nächster Schritt ist der ausdrückliche Beschluss über die sechs Zellen,
die organisatorischen Grenzen und Durchführung oder Alternative.
Erst nach Annahme eingefrorenen Laufzeitplan und getrennten
Implementierungspfad erstellen; anschließend technische Prüfungen und einmalige
Manjaro-Ausführung. Ein bei Umsetzung konsumierter Plan gehört in die volle
CI-Ausnahme; dieser noch nicht konsumierte Entwurf bleibt reine Dokumentation.
