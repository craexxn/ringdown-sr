# Methodenplan: Optimiererbudget in der freien Ringdown-Suche

Angenommen und eingefroren am 30.10.2026 nach ausdrücklicher Annahme des
korrigierten Beschlusses. Grundlage ist der überarbeitete Entwurf am Head
`8fe947cfad5787609962955b4ce2d2fbbf113c39` von
[PR #44](https://github.com/craexxn/ringdown-sr/pull/44), übernommen als
`722437ea4e3662bed4ef61bd363503777e44d2fe`. Die Zahlen, Reihenfolge, Kriterien
und Entscheidungsregeln dieses Plans sind verbindlich. Implementierung,
technische Prüfung und einmalige wissenschaftliche Ausführung sind getrennte
Schritte; die Suchserie wird auf Manjaro am geprüften Stand ausgeführt.
Bestehende Pläne und Originalergebnisse bleiben unverändert.

## 1. Evidenz, Frage und begrenzter Anspruch

Verankerter Ergebnisstand in [PR #44](https://github.com/craexxn/ringdown-sr/pull/44):
`ad32d4b5ca8e918511f6ae8cc169a1f34f444965`, Vergleichsbasis auf `main`
`0a70f19e16e173aedf2e071a5f5b09d045ecbf69`. Beim Review den tatsächlichen
aktuellen PR-Head zusätzlich vollständig nennen; späterer Dokumentationsstand
ist vom hier verankerten Audit zu unterscheiden.

Die [Konstantendiagnose](constant_diagnostic_results_manjaro_001.md) zeigt bei
fest vorgegebenem Vierkonstantenbaum und acht deklarierten Starts:

| Profil | Kurvengrenzen bestanden | Parameter `matched` |
| --- | ---: | ---: |
| 20 Iterationen, zwei zusätzliche Neustarts | 0/24 | 0/24 |
| 100 Iterationen, zwei zusätzliche Neustarts | 24/24 | 24/24 |

Bei allen 72 lokalen Paaren stimmen die Schritte 0 bis 20 exakt überein.
Explizite Solver-Abbruchstatus fehlen weiterhin. Der unabhängige Audit prüfte
259 Dateien, 47 Quell-/Pin-/Planhashes und 6.506 Zustände. Er startete keine
Optimierung. Das Originalarchiv hat SHA-256
`346459d953468c81975670577b92aa155a1eaec884cebd462fe61e1ab23d492b`.

Die [vorherige freie Serie](representation_control_results_manjaro_001.md)
fand dagegen unter keinem der drei Profile einen erfolgreichen Kurvenmarker
unter 57 Frontkandidaten. Die Häufigkeitsschalter verbesserten die Trainings-
MSE bei allen drei bekannten Seeds um rund 90–97 %. Dieses Ergebnis bestimmt
noch kein Produktionsprofil und belegt keine Populationsvielfalt.

**Forschungsfrage:** Verbessert die Erhöhung der maximalen lokalen
Optimiereriterationen von 20 auf 100 die freien Originalauswahlen innerhalb des
gemeinsam aktivierten Häufigkeitsprofils bei festgehaltenem nominalem Suchbudget?
Beide Arme verwenden die ursprüngliche Sekundenkoordinate sowie
`use_frequency=True` und `use_frequency_in_tournament=True`. Untersucht wird die
bedingte Budgetwirkung in diesem Profil; Budgetwirkungen im ausgeschalteten
Profil und Wechselwirkungen zwischen Profil und Budget bleiben offen.

Arbeitshypothese: Innerhalb dieses Profils erhöht 100/2 gegenüber 20/2 die Zahl
erfolgreicher Originalauswahlen. Gegenmöglichkeiten sind unveränderte Misserfolge,
lediglich kleinere Fehler unterhalb der Erfolgsschwelle, gemischte Seed-Ergebnisse
oder gute ausschließlich nicht ausgewählte Kandidaten.

Der Vergleich untersucht eine Intervention im gesamten freien Suchprozess.
Er trennt nicht nachträglich lokale Anpassung, Strukturentstehung und
Strukturerhaltung. Die acht privilegierten Starts und der bekannte Ringdown-
baum der Diagnose gelangen nicht in die freien Suchpopulationen.

Dies bleibt Methodenentwicklung an einem bekannten Signal und drei bekannten
Seedkennungen. Weder unabhängige Validierung noch eine Erfolgswahrscheinlichkeit,
Rausch-/Gewichtungsstudie oder physikalische Identifikation werden beansprucht.

## 2. Beschlossenes Design und erwogene Alternativen

**Beschlossenes Design auf Grundlage der Reviewempfehlung:** Zwei Arme mit
beiden Häufigkeitsschaltern aktiviert und ursprünglicher Zeitkoordinate. Damit
liegt zwischen den neuen Armen genau ein deklarierter numerischer Faktor.
Sechs neue Suchen begrenzen den Aufwand und knüpfen an das bisher bessere
Approximationsprofil an. Diese Profilwahl nutzt bekannte Entwicklungsergebnisse
und ist ausdrücklich adaptive Methodenentwicklung, keine unabhängige Validierung.
Die bessere Approximation beweist weder mehr Populationsvielfalt noch künftigen
Rekonstruktionserfolg. Die feste Diagnose privilegiert das ausgeschaltete Profil
nicht: Beim direkt vorgegebenen Baum gab es keine Populationsauswahl, auf die
die Häufigkeitsmechanismen wirken könnten.

| Alternative | Erkenntnisgewinn und Kosten | Grund für Zurückstellung |
| --- | --- | --- |
| Beide Budgetarme mit Häufigkeitsschaltern aus | Ebenfalls sechs Suchen und ein innerhalb des Profils isolierter Budgetfaktor; Anbindung an das ursprüngliche Baselineprofil | Methodisch gültig, für den nächsten Entwicklungsschritt weniger attraktiv als das bereits bessere Approximationsprofil. Die feste Diagnose liefert keinen Grund, das ausgeschaltete Profil zu bevorzugen. |
| Vollständiges 2×2 aus Budget 20/100 und beiden Schaltern aus/an | Zwölf Suchen mit drei Seeds; könnte eine Wechselwirkung beschreiben | Doppelter Suchumfang gegenüber dem beschlossenen Design; für diesen Schritt nicht gewählt. Kein kombiniertes Profil wird still ergänzt. |
| Suchverlauf instrumentieren | Näher an Entstehung, Optimierung und Verwerfung von Strukturen | Zusätzlicher Faktor und Prüfaufwand; ein negativer Budgetvergleich allein identifiziert trotzdem keinen Strukturengpass. |
| Weitere feste Startgitter, Koordinaten oder Solver | Weitere lokale Mechanismen untersuchen | Die aktuelle feste Diagnose war unter 100/2 vollständig erfolgreich. Eine zusätzliche Rastererweiterung beantwortet die Übertragung auf freie Suche nicht. |
| Grammatik einschränken oder breite freie Rekonstruktion pausieren | Aufwand begrenzen beziehungsweise engeren Forschungsanspruch wählen | Weiterhin legitime spätere Entscheidung; nicht automatisch aus einem begrenzten negativen Suchvergleich ableiten. |

Das beschlossene Design erlaubt keine Aussage über die Budgetwirkung bei
ausgeschalteten Schaltern oder über eine Wechselwirkung. Bei Wahl einer
Alternative muss genau ein vollständiger Plan neu festgelegt werden; die
Alternativen sind keine zusätzlichen Ausführungsarme dieses Plans.
Zeitstreckung, Einzelschalter, Templates und weitere Solver bleiben zurückgestellt.

## 3. Datenrollen und alleinige Intervention

Die 128 Trainingswerte und 889 inneren Achtelpunkte werden unverändert aus dem
identitätsgeprüften Archiv `representation-manjaro-001.tar.gz` übernommen,
SHA-256 `a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Der bestehende gesicherte Leser prüft zusätzlich die Arraybits. Archivquellen
werden ausschließlich als Daten behandelt; kein Archivcode wird ausgeführt.

Trainingszeiten `t_j=j/4096 s`, `j=0,...,127`; Fensterdauer `128/4096 s`,
letzte Trainingszeit `127/4096 s`. Bekanntes rauschfreies Signal mit
`A=1`, `f=250 Hz`, `tau=0,008 s`, `phi=0`. Diese Angaben dienen dem
Entwicklungsdesign und der nachgelagerten Diagnose. Jeder freie Suchworker
erhält ausschließlich die ursprüngliche Zeitkoordinate und unveränderte
Beobachtungen, mit `X_units=["s"]`, `y_units="1"`, `covariance=None`.
Keine Diagnosepunkte, Wahrheitsparameter, Referenzbäume oder Startkoeffizienten
werden als Hinweise, Einschränkungen, Initialpopulation oder Auswahlhilfe benutzt.

| Kennung | Optimiereriterationsgrenze | Zusätzliche Neustarts | `use_frequency` | `use_frequency_in_tournament` | Koordinate |
| --- | ---: | ---: | --- | --- | --- |
| `optimizer_20` | 20 | 2 | `True` | `True` | `t`, Sekunden |
| `optimizer_100` | 100 | 2 | `True` | `True` | `t`, Sekunden |

Die Bibliotheksoption `optimizer_iterations` wird auf 20 beziehungsweise 100
abgebildet; im tatsächlichen Julia-Objekt muss das entsprechende
`optimizer_options.iterations` vorliegen. Das ist eine Obergrenze je lokalem
Optimierungsversuch, keine fest zu erzwingende Schrittzahl. Zwei Neustarts sind
bis zu zwei zusätzliche lokale Versuche vom ursprünglichen Konstantenvektor.
Toleranzen und sonstige Abbruchgrenzen bleiben gleich, einschließlich des
bestehenden Limits für Funktionsauswertungen. Fehlende tatsächliche Solver-
Abbruchstatus bleiben `unavailable` und werden nicht aus Callbackzahlen erfunden.

Der vorhandene Backendpfad bleibt erhalten: bei einer reellen Konstante Newton,
bei mehreren Konstanten konfiguriertes BFGS mit Backtracking; ohne optimierbare
Konstanten kein lokaler Fit. Der freie Budgetfaktor betrifft somit auch den
Newton-Sonderpfad. Er darf nicht als ausschließliches BFGS-Experiment bezeichnet
werden. Alle wirksamen Optimiereraufrufer, insbesondere Optimierungsmutation
und Populationsnachbearbeitung, müssen gegen den gepinnten Quellpfad
abgeglichen werden; es darf kein verstecktes anderes Profil benutzt werden.

## 4. Suchbudget, Seeds und feste Reihenfolge

Je Arm drei vollständig frische Prozesse mit den bekannten
Entwicklungsseeds 20261020, 20261021 und 20261022. Die gleichen Kennungen
werden zur Anbindung an den bisherigen Entwicklungsfall verwendet; sie sind
nicht zurückgehalten. Beide Arme werden neu ausgeführt. Historische Kandidaten
oder die privilegierten 48 Fits ersetzen keine der sechs neuen Suchzellen.

| Zelle | Seed | Arm |
| --- | ---: | --- |
| 1 | 20261020 | `optimizer_20` |
| 2 | 20261020 | `optimizer_100` |
| 3 | 20261021 | `optimizer_100` |
| 4 | 20261021 | `optimizer_20` |
| 5 | 20261022 | `optimizer_20` |
| 6 | 20261022 | `optimizer_100` |

Mit drei Paaren ist eine exakt gleiche Anzahl beider Paarreihenfolgen unmöglich.
Die Reihenfolge wechselt vorab; die verbleibende 2:1-Asymmetrie wird dokumentiert.
Es wird keine zeitliche Reihenfolgewirkung aus sechs Läufen geschätzt.

Je Suchzelle unverändert 200 **Suchiterationen**, zwei Populationen mit je
32 Individuen und 50 Zyklen je Suchiteration. Insgesamt sechs Suchen und
1.200 nominale Suchiterationen; diese Summe ist kein Maß gleicher Rechenkosten.
Das bisherige Suchbudget wird übernommen, um einen zweiten numerischen Faktor
zu vermeiden. Die 100 lokalen Iterationen stammen aus der erfolgreichen festen
Diagnose; sie sind kein Nachweis eines optimalen Budgets für beliebige Suchbäume.

Unverändert bleiben Operatoren `+,-,*,/,exp,sin,cos`, Einheitskomplexitäten,
Knotenlimit 20, effektives Tiefenlimit 20 (PySR `maxdepth=None`), Parsimony 0,
Float64, numerische Differentiation, serielles deterministisches Profil,
`dimensionless_constants_only=False`, `warm_start=False`, `guesses=None`,
keine neuen Restriktionen, Tracing-Plugins, Templates oder Zielskalierungen.
Python 3.12.14, Julia 1.13.1, PySR 2.6.0 und SymbolicRegression 2.5.1 bleiben
gepinnt. Haswell sowie `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`,
`MKL_NUM_THREADS=1` und `NUMEXPR_NUM_THREADS=1` gelten nur für diesen
kontrollierten Pfad. Allgemeine Suchdefaults werden nicht geändert.
Diese Ausführungskontrolle belegt keine allgemeine Überlegenheit von Haswell.

Der tatsächliche Backendseed wird mit der bestehenden PySR-Abbildung
`RandomState(seed).randint(0, 2**31-1)` absolut geprüft. RNG-Typ und Initialisierung
müssen dem echten freien Suchpfad entsprechen; der explizite Xoshiro-Wrapper
der festen Diagnose wird nicht in die Suche übernommen. Gleiche Seedkennungen
bedeuten hier weder identische Suchpräfixe noch gleiche Mutations-/Restartvektoren:
veränderte Anpassung kann spätere Populationen und RNG-Verbrauch ändern.
Die 72 identischen lokalen Präfixe aus der festen Diagnose werden nicht als
Eigenschaft der neuen freien Suchen vorausgesetzt.

## 5. Auswahl und getrennte Endpunkte

Alle Pareto-Kandidaten, ihre Reihenfolge und der ursprüngliche Auswahlindex
bleiben erhalten. Auswahl ausschließlich nach minimaler gewöhnlicher Trainings-
MSE, dann minimaler Komplexität; bei weiterem Gleichstand erster Originalindex.
Alle Kandidaten werden anhand des vollständigen unveränderten Baums mit
ursprünglicher binärer Auswertungsreihenfolge nachgerechnet. Widersprüche in
Vorhersage, Residuen oder MSE führen zum Abbruch und niemals zur Ersatzwahl.

**Primärer deskriptiver Endpunkt:** Anzahl der drei Originalauswahlen pro Arm,
die auf Training und Zwischenpunkten jeweils `relative_rms <= 0,001` und
`relative_max <= 0,01` erfüllen. Diese Grenzen bleiben unverändert. Keine
p-Werte, Powerbehauptung, Konfidenzintervalle oder Erfolgswahrscheinlichkeit
werden aus drei bekannten Entwicklungsseeds abgeleitet.

Zusätzlich getrennt berichten:

- Trainings-MSE und beide Fehlermaße auf beiden Rastern aller Originalauswahlen;
  Minima, Mediane, Maxima und endliche Nenner über je drei Zellen.
- Strukturstatus/Erstgrund, Abklingen, Amplitude, rohe und aliasbezogene
  Parameter sowie bisherige Parameterfehler. Grenzen: relative Frequenz `1e-3`,
  relative Abklingzeit `1e-2`, Amplituden- und komplexer Amplitudenfehler `1e-2`.
  Vorzeichen und Phase bleiben erhalten. Bestehende Replay-/Alias-/Verfügbarkeits-
  gates bleiben verbindlich; ein fehlgeschlagenes Replay erzeugt keinen positiven
  Parametermarker. Kurven-, Struktur- und Parametermarker bleiben getrennt.
- Alle Frontkandidaten mit Originalindex und Diagnosen; Zahl guter, aber nicht
  ausgewählter Kandidaten ausdrücklich separat. Die Front ist keine Historie
  aller besuchten Strukturen und ihre Kandidaten sind keine unabhängigen Läufe.
- Für jeden Seed `Delta = optimizer_100 - optimizer_20`: MSE, RMS/Maximalfehler
  beider Raster und vergleichbare Parameterfehler, mit beiden Ausgangswerten
  und Status. Bei fehlenden/unbestimmten Seiten `null` mit Grund statt null Fehler.
- Kompakte Übersicht der drei Erfolgswechsel: bestanden/nicht bestanden unter
  20/2 und 100/2 je Seed sowie die Häufigkeiten beider Wechselrichtungen und
  unveränderter Zustände. Dies erläutert den primären Endpunkt, ohne einen neuen
  einzuführen; `C100 - C20` entspricht Gewinnen minus Verlusten.
- Fit-Callbackzahlen, Gesamtzähler und vorhandener Backend-Evaluationszähler
  getrennt. Die zusätzliche Nullkurvenauswertung nach dem Fit gehört nicht in
  den Fit-Zähler. Zell-/Serienzeiten einschließlich Startup, JIT und Export.
  Aufwand je Seed nebeneinander, ohne ihn mit Anpassungsgüte gleichzusetzen.

`physical_identification` bleibt `not_assessed`. Das Achtelraster hat weiterhin
den bekannten Blindfleck bei `8*fs=32768 Hz`. Gute endliche Rasterreplays belegen
keine physikalische Eindeutigkeit und keine Güte zwischen beliebigen Zeitpunkten.

## 6. Technischer Nachweis vor einer wissenschaftlichen Serie

Dieser Plan verlangt einen eigenen isolierten
Treiber und eine eigene Implementierungsherkunft. Bestehende allgemeine Pfade
und alle drei eingefrorenen Laufzeitpläne bleiben erhalten. Dieser Plan wird vor Konsum durch Commit/SHA-256 gebunden und als
Laufzeitdokument ausdrücklich der vollständigen CI zugeordnet. Der Plan selbst
ist kein Suchbefehl.

Vor der ersten wissenschaftlichen Suche erforderlich:

Die Vorprüfungen laufen in eigenen Prozessen. Wissenschaftliche Suchworker
starten danach frisch und übernehmen keine Referenzbäume oder Vorprüfungszustände.

1. Sechs tatsächliche Optionsobjekte für beide Budgets und alle drei Seeds
   ohne Fit/Suche prüfen. Alle wirksamen Felder und konkreten Plugins schon für
   die erste Zelle absolut gegen native Prototypen des gemeinsam aktivierten
   Häufigkeitsprofils prüfen; beide Schalter müssen in jeder Zelle `True` sein.
   Übergreifend allein die bereits einzeln geprüfte Iterationsgrenze sowie
   Seed und technische Ausgabepfade als geplante Unterschiede behandeln.
   Ein gemeinsamer geprüfter Verlustwrapper muss in beiden Armen gleich sein.
2. Native feste 250-/4346-/33018-Hz-Referenzen und Einheitengegenfälle unter
   beiden Optionsprofilen prüfen; keine Optimierung dieser wissenschaftlichen
   Referenzen. Beide sind ursprüngliche Sekundenkoordinaten, keine Zeitstreckung.
3. Den gemeinsamen numerischen Callback gegen die bisherige Referenz prüfen;
   kleine echte Worker auf einem eigenen technischen Signal für beide Budgets
   und eine 20–100–20-Prozessfolge prüfen. Keine der sechs wissenschaftlichen
   Suchzellen als Integrationstest benutzen. Vorhandene nichtlineare technische
   Konstantenfälle, neue Options-/Seed-/Manipulationsgegenfälle und volle CI.

Die spätere Serie verlangt ein neues exklusives Verzeichnis, sauberen geprüften
Codezustand, manifeste Quell-/Pin-/Plan-/Datenhashes, geprüfte Laufzeitkopien und
Start-/Endaufnahmen der geladenen BLAS-Pools. Quellen, Originalarchiv, Eingaben
und konsumierte Workerdateien werden vor und nach Verbrauch sowie abschließend
gegen zuvor eingefrorene Bytes geprüft. Eine konsistente nachträgliche Neuhashung
ersetzt diese Anker nicht. Verifikationsfehler stoppen ohne Reparatur/Reranking.

Die feste Diagnose war eine gesonderte privilegierte Prüfung. Ihre 144 lokalen
Optimierungen oder ihre Laufzeitgrenze werden nicht als Zahl lokaler Optimierungen
oder Kostenprognose der freien Suche übernommen. Zusätzliche breit angelegte
Suchverlaufsinstrumentierung gehört nicht zu dieser Implementierung.

## 7. Aufwand, Abbruch und Vollständigkeit

Verbindliches organisatorisches Limit: **60 Minuten Gesamtwandzeit** für die
sechs Zellen einschließlich Vorprüfungen, Prozessstarts und Abschlussverifikation.
Dies ist eine organisatorische Obergrenze, keine Laufzeitprognose. Weder
die 435 Sekunden der früheren freien Serie noch die 1.203 Sekunden der festen
Diagnose erlauben eine proportionale Hochrechnung auf dieses Design.
Der Faktor 3,35 bei festen Callbackzahlen und fast gleiche JIT-geprägte Zeiten
liefern ebenfalls keine Kostenformel für eine veränderliche freie Population.

Nach sechs geplanten Zellen endet der Versuch unabhängig vom Ergebnis.
Technische Fehler, Ressourcenabbruch, Tastaturabbruch und SIGTERM sichern
Teilstände und beenden die eigene Worker-Prozessgruppe. Keine Wiederholungen,
Ersatzseeds, Warmstarts, stillen Budgeterhöhungen oder anschließenden Zusatzarme.
Eine gültige schlechte Formel ist ein fachliches Ergebnis, kein technischer Fehler.

Verbindliche konservative Berichtssperre: Gruppenstatistiken und sämtliche
Paardifferenzen werden erst bei sechs vollständig geprüften Zellen und bestandener
Abschlussverifikation freigegeben. Sonst bleiben vollständig verifizierte
Einzelresultate mit Status sichtbar; die Serie ist unvollständig und wird nicht
als abgeschlossener Budgetvergleich interpretiert. Dies ist ausdrücklich strenger
als die frühere Regel für vollständig geprüfte Teilgruppen der Zeitdarstellungskontrolle.

## 8. Verbindliche Interpretations- und Weiterentscheidungen

Die folgenden Gates sind nach dem Review korrigierte Entwicklungsentscheidungen,
keine statistisch hergeleiteten Garantien oder automatische Ausführungsfreigaben.
`C20` und `C100` bezeichnen jeweils die Anzahl bestandener ausgewählter
Kurvenmarker von drei. Zusätzliche Struktur-/Parameterbefunde werden daneben
berichtet; die Zeilen sind Interpretationsregeln und keine automatische Profilwahl.
Voraussetzung für den vergleichenden Befund sind sechs vollständig verifizierte
Zellen und eine bestandene Abschlussverifikation.

| Beobachtung | Zulässiger Befund und weitere Entscheidung |
| --- | --- |
| Versuch unvollständig oder Abschlussverifikation nicht bestanden | Kein abgeschlossener Budgetvergleich. Verifizierte Einzelresultate mit Status erhalten; Ursache und weiteres Vorgehen gesondert beschließen. Gruppenstatistiken und Paardifferenzen bleiben gesperrt. |
| `C100 > C20` | Mehr erfolgreiche Originalauswahlen unter 100/2 in diesen drei Entwicklungsfällen. Erfolgswechsel, Fehler und Aufwand für jeden Seed daneben berichten; keine allgemeine Überlegenheit ableiten. |
| `C100 = C20 = 0` | Keine erfolgreiche Originalauswahl unter beiden Budgets. Kleinere Fehler nur als kontinuierliche Verbesserung berichten. Keine automatische nächste Budgetstufe; Suchverlaufsdiagnose oder Eingrenzung/Pause gesondert entscheiden. |
| `C100 = C20 > 0` | Kein Mehrerfolg am primären Zählendpunkt. Seedzuordnung, Fehler und Aufwand getrennt beurteilen. |
| `C100 < C20` | Weniger erfolgreiche Originalauswahlen unter 100/2. Verbesserungen einzelner Seeds oder einzelner Fehlermaße ändern diesen Gesamtbefund nicht. |

Struktur- und Parameterbefunde werden unabhängig von diesem Zählvergleich
eingeordnet. Nur eine Originalauswahl, die selbst die Kurvengrenzen erfüllt,
erkannt wird und die verbindlichen Parameter-/Replaygates besteht, darf als
entsprechender unterstützter Rekonstruktionsfall bezeichnet werden. Gute Kurven
mit `not_supported`, `mismatched`, `not_assessed` oder unbestimmten Diagnosen
behalten diese Einschränkungen. Ihre Existenz allein belegt keine Verbesserung
gegenüber 20/2. Konkrete Erkenner-/Replayfälle können lesend untersucht werden;
keine Ersatzwahl oder nachträgliche Änderung des Erfolgskriteriums.

Gegenläufige Seed-Ergebnisse bleiben ausdrücklich sichtbar. Gute nicht ausgewählte
Frontkandidaten werden separat ausgewiesen und begründen gegebenenfalls eine
neue Auswahlfrage; sie ersetzen keine Originalauswahl. Historische Abweichungen
werden offengelegt und nicht durch Wiederholungen angeglichen.

Ein guter fester Fit oder eine einzelne freie Entwicklungsformel genügt nicht
als Freigabe einer allgemeinen Rausch-/Gewichtungsstudie. Für den Anspruch freier
Ringdown-Rekonstruktion sind ein eingefrorenes Verfahren und separat geplante,
begrenzte Übertragbarkeitsnachweise erforderlich. Ein engerer Parameterfitanspruch
müsste eigenständig beschlossen und mit dem klassischen Referenzfit verglichen werden.

## 9. Methodenreview und angenommener Beschluss

Ein KI-basiertes Methodenreview wurde am 30.10.2026 für PR #44 übermittelt:

- Geprüfter Head: `7ee5f38067ba0b2161ab3ddaf9775d6aa4fc1fbd`.
- Vergleichsbasis: `0a70f19e16e173aedf2e071a5f5b09d045ecbf69`.
- Ergebnisanker: `ad32d4b5ca8e918511f6ae8cc169a1f34f444965`.
- Übermittelter Umfang: beide PR-Commits mit allen fünf Dokumentationsdateien,
  Grundlagen, relevante unveränderte Aufrufer und gepinnte Backendquellen.
  Selbst ausgeführte Quellen-/Dokumentabgleiche und `git diff --check` wurden
  berichtet. Keine Programme, Tests, Fits, Suchen, CI oder zusätzlichen Agenten.
  Die Originalarchive lagen beim Review nicht vor; numerische Befunde und
  Archivhashes wurden dort nicht erneut unabhängig bestätigt. Die lokal
  installierte PySR-Quelle wurde gelesen; ihr GitHub-Dateiabruf scheiterte.
- **Ein korrigierbarer Befund P2 vor dem Einfrieren:** Die bisherige zweite
  Entscheidungszeile konnte gute Kurven unter 100/2 ohne Vergleichsvorteil als
  Verbesserung bezeichnen, etwa bei `C20=3`, `C100=1`. Abschnitt 8 trennt nun
  den vollständigen Zählvergleich von den Struktur-/Parameterbefunden derselben
  Originalauswahl. Weitere entscheidungsblockierende Befunde wurden im
  geprüften Umfang nicht berichtet.
- **Genau eine Empfehlung:** sechs frische Suchen mit beiden Schaltern an.
  Dies wurde in Frage, Profilen und Begründung des Entwurfs übernommen und
  anschließend ausdrücklich angenommen. Budgets, Seeds, Reihenfolge,
  Ressourcenlimit und strenge Vollständigkeitssperre wurden als begrenzte
  Entwicklungsentscheidungen für angemessen beurteilt. Die optionale Übersicht
  der Erfolgswechsel ist in Abschnitt 5 ergänzt.

Die gezielte Gegenprüfung der überarbeiteten Regeln ist im
[Fortsetzungsstand](representation_implementation_status.md) festgehalten.
Eine weitere vollständige Reviewrunde oder ein erneuter Archivaudit folgt
daraus nicht. Das Review des alten Heads ist kein Reviewnachweis für spätere
Dokumentationsänderungen und keine Ausführungsfreigabe.

**Am 30.10.2026 ausdrücklich angenommener Beschluss:**

> Als nächster Schritt wird genau ein Entwicklungsvergleich mit sechs frischen
> Suchen im gemeinsam aktivierten Häufigkeitsprofil beschlossen: 20/2 gegen
> 100/2, bei unverändertem Suchbudget, den drei bekannten Seeds, der festgelegten
> Reihenfolge und 60 Minuten Gesamtlimit. Originalauswahl, Grenzwerte,
> Verifikationssperre und die korrigierten Entscheidungsregeln werden vor
> Implementierung eingefroren. Nach technischer Prüfung ist eine einmalige
> Ausführung vorgesehen. Dieser Beschluss bestimmt kein Produktionsprofil und
> gibt keine Übertragbarkeits- oder Gewichtungsstudie frei.

Mit der ausdrücklichen Annahme werden Design, Zahlen, Reihenfolge, Kriterien
und Ressourcenlimit hier eingefroren. Danach implementieren, volle technische
CI abwarten und einmalig auf Manjaro ausführen. Die Suchserie wird im Rahmen
der Implementierung nicht in der Cloud gestartet. Ein späterer Implementierungs-PR
wird nicht eigenständig gemergt.

## Quellen und vorhandene Prüfgrenzen

- [Bestehender Suchadapter und explizite Suchparameter](../src/ringdown_sr/symbolic.py),
  [ursprünglicher Kontrollplan](noiseless_control_plan.md) und
  [Darstellungskontrollplan](search_representation_plan.md).
- [Geprüfte feste Diagnose](constant_diagnostic_plan.md),
  [ihr vollständiger Befund](constant_diagnostic_results_manjaro_001.md),
  [frühere freie Ergebnisse](representation_control_results_manjaro_001.md)
  und [Fortsetzungsstand](representation_implementation_status.md).
- [SymbolicRegression 2.5.1, Konstantenoptimierung](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/ConstantOptimization.jl):
  Newton-Sonderpfad, Neustarts und unveränderte Auswahl nach strikter Verbesserung.
  Gelesen wurde auch die tatsächlich installierte gepinnte Quelle; dies ist
  kein neu ausgeführter Backendtest.
- [SymbolicRegression 2.5.1, Populationsnachbearbeitung](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/SingleIteration.jl)
  und [Optimierungsmutation](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/Mutate.jl):
  beide Optimiereraufrufer müssen das deklarierte Profil erhalten.
- [SymbolicRegression 2.5.1, Startformelverarbeitung](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/SearchUtils.jl):
  dieser zusätzliche Aufrufer wird bei `guesses=None` nicht zur Übergabe
  privilegierter Formeln benutzt.
- [PySR 2.6.0, Suchadapter](https://github.com/MilesCranmer/PySR/blob/v2.6.0/pysr/sr.py):
  Backendseed-Abbildung und Optionsübergabe; Projektpins bleiben unverändert.

Für die Vorbereitung dieses Plans wurden Dokumente und Quellen abgeglichen. Es gibt keine
neuen Fits, freien Suchen, unabhängigen Signale oder zusätzlichen numerischen
Prüfergebnisse. Ein bereits dokumentierter Audit wird nicht als neue Wiederholung
behauptet. Das übermittelte Methodenreview und seine Prüfgrenzen stehen in
Abschnitt 9; die anschließende Regelgegenprüfung ist davon getrennt.
