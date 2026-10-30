# Entwurf: Optimiererbudget in der freien Ringdown-Suche

Stand: 30.10.2026. **Zur KI-basierten Methodenprüfung; nicht beschlossen,
nicht eingefroren, nicht implementiert und nicht ausgeführt.** Sämtliche neuen
Zahlen und Entscheidungsregeln sind Vorschläge. Die abgeschlossenen Pläne
und Originalergebnisse bleiben eingefroren. Der Auftrag umfasst diesen Entwurf
und die Vorbereitung genau eines gemeinsamen Reviews von Plan und Befund.

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

**Vorgeschlagene Frage:** Verbessert ausschließlich die Erhöhung der maximalen
lokalen Optimiereriterationen von 20 auf 100 die freien Originalauswahlen im
bisherigen Baseline-Suchprofil bei festgehaltenem nominalem Suchbudget?

Der Vergleich untersucht eine Intervention im gesamten freien Suchprozess.
Er trennt nicht nachträglich lokale Anpassung, Strukturentstehung und
Strukturerhaltung. Die acht privilegierten Starts und der bekannte Ringdown-
baum der Diagnose gelangen nicht in die freien Suchpopulationen.

Dies bleibt Methodenentwicklung an einem bekannten Signal und drei bekannten
Seedkennungen. Weder unabhängige Validierung noch eine Erfolgswahrscheinlichkeit,
Rausch-/Gewichtungsstudie oder physikalische Identifikation werden beansprucht.

## 2. Vorzugsentwurf und ernsthafte Alternativen

**Vorzugsentwurf zur kritischen Prüfung:** Zwei Arme auf dem ursprünglichen
Baselineprofil; beide Häufigkeitsschalter aus und ursprüngliche Zeitkoordinate.
Damit liegt zwischen den neuen Armen genau ein deklarierter numerischer Faktor.
Die Konstante-Diagnose verwendete ebenfalls dieses Profil. Sechs neue Suchen
begrenzen den Aufwand; Wechselwirkungen mit Häufigkeitsschaltern bleiben offen.

| Alternative | Erkenntnisgewinn und Kosten | Grund für Zurückstellung im Vorzugsentwurf |
| --- | --- | --- |
| Beide Budgetarme mit `complexity_frequency` an | Ebenfalls sechs Suchen und ein innerhalb des Profils isolierter Budgetfaktor; knüpft an den bislang besten Approximationsarm an | Die feste Diagnose lief ohne diese Populationsmechanismen. Eine Aussage über Budgetwirkung auf dem ursprünglichen Baselineprofil wäre damit nicht möglich. Das Review darf diese Alternative als sinnvoller priorisieren. |
| Vollständiges 2×2 aus Budget 20/100 und beiden Schaltern aus/an | Zwölf Suchen mit drei Seeds; könnte eine Wechselwirkung beschreiben | Doppelter Suchumfang gegenüber dem Vorzugsentwurf; für den nächsten begrenzten Schritt noch nicht gewählt. Kein kombiniertes Profil wird still ergänzt. |
| Suchverlauf instrumentieren | Näher an Entstehung, Optimierung und Verwerfung von Strukturen | Zusätzlicher Faktor und Prüfaufwand; ein negativer Budgetvergleich allein identifiziert trotzdem keinen Strukturengpass. |
| Weitere feste Startgitter, Koordinaten oder Solver | Weitere lokale Mechanismen untersuchen | Die aktuelle feste Diagnose war unter 100/2 vollständig erfolgreich. Eine zusätzliche Rastererweiterung beantwortet die Übertragung auf freie Suche nicht. |
| Grammatik einschränken oder breite freie Rekonstruktion pausieren | Aufwand begrenzen beziehungsweise engeren Forschungsanspruch wählen | Weiterhin legitime spätere Entscheidung; nicht automatisch aus einem begrenzten negativen Suchvergleich ableiten. |

Der Vorzugsentwurf kann das günstigere Häufigkeitsprofil bewusst verfehlen.
Das ist eine wesentliche Grenze und eine ausdrückliche Reviewfrage. Bei Wahl
einer Alternative muss genau ein vollständiger Plan neu festgelegt werden;
die Alternativen sind keine zusätzlichen Ausführungsarme dieses Entwurfs.
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
| `optimizer_20` | 20 | 2 | `False` | `False` | `t`, Sekunden |
| `optimizer_100` | 100 | 2 | `False` | `False` | `t`, Sekunden |

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

Vorschlag: je Arm drei vollständig frische Prozesse mit den bekannten
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
- Fit-Callbackzahlen, Gesamtzähler und vorhandener Backend-Evaluationszähler
  getrennt. Die zusätzliche Nullkurvenauswertung nach dem Fit gehört nicht in
  den Fit-Zähler. Zell-/Serienzeiten einschließlich Startup, JIT und Export.
  Aufwand je Seed nebeneinander, ohne ihn mit Anpassungsgüte gleichzusetzen.

`physical_identification` bleibt `not_assessed`. Das Achtelraster hat weiterhin
den bekannten Blindfleck bei `8*fs=32768 Hz`. Gute endliche Rasterreplays belegen
keine physikalische Eindeutigkeit und keine Güte zwischen beliebigen Zeitpunkten.

## 6. Technischer Nachweis vor einer wissenschaftlichen Serie

Dieser Entwurf verlangt erst nach Methodenbeschluss einen eigenen isolierten
Treiber und eine eigene Implementierungsherkunft. Bestehende allgemeine Pfade
und alle drei eingefrorenen Laufzeitpläne bleiben erhalten. Der spätere
freigegebene Plan wird vor Konsum durch Commit/SHA-256 eingefroren und als
Laufzeitdokument ausdrücklich der vollständigen CI zugeordnet. Dieser heutige
Entwurf wird nicht zur Laufzeit gelesen und ist kein Suchbefehl.

Vor der ersten wissenschaftlichen Suche erforderlich:

Die Vorprüfungen laufen in eigenen Prozessen. Wissenschaftliche Suchworker
starten danach frisch und übernehmen keine Referenzbäume oder Vorprüfungszustände.

1. Sechs tatsächliche Optionsobjekte für beide Budgets und alle drei Seeds
   ohne Fit/Suche prüfen. Alle wirksamen Felder und konkreten Plugins schon für
   die erste Zelle absolut gegen profilgerechte native Prototypen prüfen.
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

Vorgeschlagenes organisatorisches Limit: **60 Minuten Gesamtwandzeit** für die
sechs Zellen einschließlich Vorprüfungen, Prozessstarts und Abschlussverifikation.
Dies ist ein zur Annahme offenes Ressourcenlimit, keine Laufzeitprognose. Weder
die 435 Sekunden der früheren freien Serie noch die 1.203 Sekunden der festen
Diagnose erlauben eine proportionale Hochrechnung auf dieses Design.
Der Faktor 3,35 bei festen Callbackzahlen und fast gleiche JIT-geprägte Zeiten
liefern ebenfalls keine Kostenformel für eine veränderliche freie Population.

Nach sechs geplanten Zellen endet der Versuch unabhängig vom Ergebnis.
Technische Fehler, Ressourcenabbruch, Tastaturabbruch und SIGTERM sichern
Teilstände und beenden die eigene Worker-Prozessgruppe. Keine Wiederholungen,
Ersatzseeds, Warmstarts, stillen Budgeterhöhungen oder anschließenden Zusatzarme.
Eine gültige schlechte Formel ist ein fachliches Ergebnis, kein technischer Fehler.

Vorgeschlagene konservative Berichtssperre: Gruppenstatistiken und sämtliche
Paardifferenzen werden erst bei sechs vollständig geprüften Zellen und bestandener
Abschlussverifikation freigegeben. Sonst bleiben vollständig verifizierte
Einzelresultate mit Status sichtbar; die Serie ist unvollständig und wird nicht
als abgeschlossener Budgetvergleich interpretiert. Dies ist ausdrücklich strenger
als die frühere Regel für vollständig geprüfte Teilgruppen der Zeitdarstellungskontrolle.

## 8. Vorab vorgeschlagene Weiterentscheidungen

Die folgenden Gates sind Entwicklungsentscheidungen zur Prüfung im Review,
keine statistisch hergeleiteten Garantien oder automatische Ausführungsfreigaben.
`C20` und `C100` bezeichnen jeweils die Anzahl bestandener ausgewählter
Kurvenmarker von drei. Zusätzliche Struktur-/Parameterbefunde werden daneben
berichtet; die Zeilen sind Interpretationsregeln und keine automatische Profilwahl.

| Beobachtung im vollständigen Versuch | Konsequenz |
| --- | --- |
| `C100 > C20`; mindestens eine Auswahl unter 100/2 zusätzlich erkannt und parameterkompatibel | Begrenzter positiver Rekonstruktionsbefund für diesen Entwicklungsfall; vor Übertragbarkeitsaussagen eigenes Design mit getrennten Signal-/Seedrollen beschließen |
| Unter 100/2 gute ausgewählte Kurven, aber fehlende Struktur-/Parameterunterstützung | Kurvenverbesserung berichten und die konkreten Erkenner-/Replayfälle lesend untersuchen; keine Ersatzwahl und keine nachträgliche Änderung des Erfolgskriteriums |
| `C20 = C100 = 0`, auch wenn MSE kleiner wird | Weiterhin unzureichende Originalauswahlen; keine nächste Budgetstufe. Zwischen gezieltem Suchverlauf und bewusster Eingrenzung/Pause neu entscheiden; vorhandene gute Frontkandidaten separat ausweisen, Wechselwirkungen mit Häufigkeitsprofilen bleiben offen |
| `C20 = C100 > 0` | Kein Mehrerfolg beim primären Zählendpunkt; Einzelzuordnung zu Seeds, Fehler und Aufwand getrennt beschreiben. Historische Baselineabweichungen offenlegen, keine Wiederholung zur Ergebnisangleichung |
| `C100 < C20`, gegenläufige Seed-Differenzen oder nur nicht ausgewählte gute Frontkandidaten | Alle Fälle erhalten; nur entsprechende Teilbehauptung zulässig, Auswahl-/Suchfragen neu planen, kein bestes Beispiel als Gesamtergebnis |
| Technisch oder zeitlich unvollständig | Kein abgeschlossener Vergleich und keine wissenschaftliche Rangfolge; zunächst Ursache und vertretbaren nächsten Schritt beschließen |

Ein guter fester Fit oder eine einzelne freie Entwicklungsformel genügt nicht
als Freigabe einer allgemeinen Rausch-/Gewichtungsstudie. Für den Anspruch freier
Ringdown-Rekonstruktion sind ein eingefrorenes Verfahren und separat geplante,
begrenzte Übertragbarkeitsnachweise erforderlich. Ein engerer Parameterfitanspruch
müsste eigenständig beschlossen und mit dem klassischen Referenzfit verglichen werden.

## 9. Reviewfragen und noch nötiger Beschluss

Das gemeinsame KI-basierte Methodenreview soll insbesondere klären:

- Hat der Baselinevergleich mit sechs Suchen den größten Erkenntnisgewinn oder
  wäre das gemeinsame Häufigkeitsprofil bei gleichem Umfang sinnvoller? Ist
  ein 2×2-Design seinen doppelten Umfang bereits wert?
- Sind Übernahme von 200 Suchiterationen, bekannten drei Seeds und 100 lokalen
  Iterationen als ausdrücklich begrenzte Entwicklungsentscheidungen gerechtfertigt?
- Ist der primäre Endpunkt an der Originalauswahl passend, und trennen die
  vorgeschlagenen Gates Kurvengüte, Erkennerabdeckung und Parameterdiagnose sauber?
- Sind 60 Minuten und die strikte Vollständigkeitsregel angemessen, ohne
  Ressourcenabbrüche als negative Suchleistung fehlzuinterpretieren?
- Welche konkreten Befunde würden gegen die Budgetintervention und für Such-
  verlaufsdiagnose oder eine bewusste Pause/Eingrenzung sprechen?

Erst nach Review und ausdrücklichem Methodenbeschluss: genau ein Design,
Zahlen, Reihenfolge, Kriterien und Ressourcenlimit einfrieren; danach implementieren,
volle technische CI abwarten und einmalig auf Manjaro ausführen. Ein Merge des
Dokumentationsentwurfs allein beschließt oder startet keinen Versuch.

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

Für diesen Entwurf wurden Dokumente und Quellen abgeglichen. Es gibt keine
neuen Fits, freien Suchen, unabhängigen Signale oder zusätzlichen numerischen
Prüfergebnisse. Ein bereits dokumentierter Audit wird nicht als neue Wiederholung
behauptet. Das hier vorbereitete Methodenreview ist noch nicht ausgeführt.

## Kopierbarer Auftrag für das gemeinsame Methodenreview

```text
Führe ein KI-basiertes Methodenreview von Planentwurf und aktuellem Entwicklungsbefund für den Ringdown-SR-Piloten durch. Prüfe genau den nächsten begrenzten Schritt; implementiere oder starte nichts.

Repository: https://github.com/craexxn/ringdown-sr
PR: https://github.com/craexxn/ringdown-sr/pull/44
Lies den tatsächlich aktuellen PR-Head und die Vergleichsbasis vollständig aus. Der Ergebnisanker vor diesem Entwurf ist ad32d4b5ca8e918511f6ae8cc169a1f34f444965, seine Basis 0a70f19e16e173aedf2e071a5f5b09d045ecbf69. Aktuellen Entwurfshead und Ergebnisanker getrennt benennen. Keine Aussagen über einen ungeprüften späteren Head übertragen.

Verbindlich lesen: AGENTS.md und README im aktuellen Stand; docs/representation_implementation_status.md; docs/free_optimizer_budget_plan_draft.md; docs/constant_diagnostic_results_manjaro_001.md; docs/constant_diagnostic_plan.md; docs/representation_control_results_manjaro_001.md; docs/search_representation_plan.md; relevante Aufrufer in src/ringdown_sr/symbolic.py und im gepinnten SymbolicRegression-Backend 2.5.1.

Evidenz: Bei festem Vierkonstantenbaum bestanden 0/24 Fits unter 20/2 und 24/24 unter 100/2 die unveränderten Kurvengrenzen. Alle 72 lokalen Paare hatten identische Schritte 0 bis 20. Solver-Abbruchstatus bleiben unavailable. Der Audit prüfte 259 Dateien, 47 Quell-/Pin-/Planhashes, 144 lokale Verläufe und 6506 Zustände. Er ist dokumentiert, kein Auftrag zu einem erneuten Originalarchiv-Audit. Wenn das Originalarchiv fehlt, lege diese Prüfgrenze offen. Die frühere freie Serie lieferte keinen erfolgreichen Kandidaten unter 57; Häufigkeitsschalter senkten die Trainings-MSE bei allen drei Entwicklungsseeds um rund 90–97 %.

Vorzugsentwurf: sechs frische freie Suchen, ursprüngliche Sekundenkoordinate, beide Häufigkeitsschalter aus. Je drei bekannte Entwicklungsseeds 20261020/21/22; einziges numerisches Vergleichsmerkmal 20 gegen 100 lokale Optimiereriterationen, je zwei zusätzliche Neustarts. Beide Arme je 200 Suchiterationen, zwei Populationen zu 32 Individuen, 50 Zyklen. Ein Signal, keine Templates/Wahrheitsstarts, ursprüngliche Auswahl und Grenzen, Haswell/Threads 1. Vorgeschlagenes Ressourcenlimit 60 Minuten; keine automatischen Wiederholungen. Alle neuen Zahlen und Gates sind Entwurfsvorschläge, noch kein Methodenbeschluss.

Prüfe kritisch:
1. Trägt die feste Diagnose diese nächste freie Intervention, ohne bereits den historischen Engpass oder einen Optimiererdefekt zu behaupten?
2. Ist die Baseline mit beiden Schaltern aus die beste Wahl? Vergleiche fair mit zwei Budgetarmen bei gemeinsam aktivierten Häufigkeitsschaltern und mit einem vollständigen 2x2 (zwölf Suchen). Begründe Informationsgewinn und Aufwand; übernimm den Vorzugsentwurf nicht ungeprüft. Falls du ihn verwirfst, empfehle genau ein konsistentes alternatives Design, keine Sammlung zusätzlicher Arme.
3. Sind Suchbudget, wiederverwendete Entwicklungsseeds, Reihenfolge und Ressourcenlimit begründet? Gleiche Seeds bedeuten keine identischen freien Suchpfade oder gleichen Rechenkosten. Die 72 identischen Präfixe der festen Diagnose sind keine Anforderung an freie Populationen. Der Budgetfaktor betrifft auch den bestehenden Ein-Konstanten-Newtonpfad.
4. Sind Originalauswahl als primärer Endpunkt, vollständige Frontdiagnosen, getrennte Kurven-/Struktur-/Parametermarker, Statusregeln für Replays und Paardifferenzen sowie strenge Vollständigkeitssperre angemessen und unverfälscht?
5. Sind die vorgeschlagenen Weiter-/Stoppregeln aussagekräftig, einschließlich schlechter ausgewählter und guter nicht ausgewählter Kandidaten, gemischter Ergebnisse und Ressourcenabbruch? Welches Gate folgt vor einer Übertragbarkeits- oder Gewichtungsstudie?

Berichte: PR, vollständigen geprüften Head, Vergleichsbasis und Prüfumfang; ein kurzes Urteil und genau eine Empfehlung. Trenne entscheidungsblockierende Befunde mit Fundstelle/Auswirkung/notwendiger Korrektur von optionalen Verbesserungen. Nenne konkrete versionsgebundene Quellen für technische Behauptungen und kennzeichne fehlenden Zugriff. Liefere bei notwendigen Änderungen präzise ersetzbare Planpassagen und einen kurzen Beschlussentwurf. Trenne Beobachtungen, Hypothesen, Empfehlung und nötige Entscheidungen.

Grenzen: Kein Implementierungsreview als zusätzliche Routine, kein erneuter vollständiger Audit oder CI-Lauf, keine Fits, Suchläufe oder zusätzlichen Agenten. Keine rückwirkende Änderung abgeschlossener Pläne, Auswahl, Grenzwerte oder Originalartefakte. Keine eigenmächtige Freigabe neuer Budgets oder eines Produktionsprofils. physical_identification bleibt not_assessed; der Alias-Blindfleck bei 8*fs bleibt bestehen. Sprache Deutsch; das Review als KI-basiert bezeichnen, ohne Modellnamen.
```
