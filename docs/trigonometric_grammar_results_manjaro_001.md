# Grammatikvergleich auf Manjaro: grammar-manjaro-001

Stand: 03.11.2026. Das vollständige Originalarchiv ist lesend geprüft und
unabhängig nachgerechnet. Alle sechs Zellen sind abgeschlossen; die
Abschlussverifikation besteht. Trotzdem erreicht keiner der 51 exportierten
Frontkandidaten die Kurvengrenzen. Der primäre Vergleich ergibt
**C_K = 0/3 und C_A = 0/3**. Die Hypothese wird nicht gestützt; gemäß
[eingefrorenem Plan](trigonometric_grammar_plan.md#6-entscheidungsregel)
wird die zusätzliche Einschränkung nicht übernommen. Der Versuch ist beendet.

## 1. Herkunft und Prüfstatus

- Originalarchiv: `grammar-manjaro-001.tar.gz`, 579.226 Bytes.
  SHA-256 selbst bestätigt:
  `8d7fc8b09ed9c5091acef5237f5512ddb9fb014598e72ee3d9d4e435f33e3915`.
- Ausführungscommit laut übereinstimmenden Eltern-/Workermetadaten:
  `23a21131e6fafcdc748e47098c018a1158f1629b`, sauberer Checkout.
  [PR #52](https://github.com/craexxn/ringdown-sr/pull/52) ist damit übernommen;
  der darin enthaltene Literatur-PR #51 ist als ersetzt geschlossen.
  Der Squashcommit und der geprüfte Implementierungs-Head
  `b4c363ada9d3c35f46ec0eec36687dda82c5fe0e` besitzen denselben Git-Tree
  `d7352ed5e34d446374bdf573d6422ac869b18369`.
- Format `ringdown-sr-trigonometric-grammar-1`; Plancommit
  `5de1a4a0bbb8282ac77f06e21f0314acaa99eade`, SHA-256
  `e8fe21344cedc93196d77e83918eb989907fe75e7cfa7219ee17d22661be70b5`.
  Die archivierten Planbytes stimmen mit dem Ausführungscommit überein.
- Aufgezeichnete Ausführung am 03.11.2026 von 09:10:15 bis 09:16:26 UTC;
  Gesamtzeit 371,287 Sekunden einschließlich Vorprüfungen und Abschlussphase.
  Alle sechs Worker bleiben unter 600 Sekunden, die Serie unter 3600 Sekunden.

Die Archivpfade enthalten ausschließlich reguläre Dateien und Verzeichnisse,
keine doppelten Namen oder Pfade außerhalb des Wurzelordners. Das Paket enthält
165 Dateien mit insgesamt 2.705.697 unkomprimierten Bytes. Alle 164 Einträge
des Gesamtmanifests, sämtliche Zellprüfsummen und alle 162 eingefrorenen
Dateianker stimmen. Die 59 erfassten Quellen wurden gegen die Git-Bytes des
Ausführungscommits geprüft; ebenso Projekt-/Pin-Dateien, Python-Herkunft,
Adapterquellen und tatsächlich kopierte Laufzeitdateien.

Die 128 Trainingswerte und 889 inneren Achtelpunkte stimmen bitgenau mit den
eingefrorenen Referenzdaten und den archivierten Fingerprints überein. Jeder
Suchworker enthält ausschließlich Trainingszeiten und Beobachtungen als
Eingabearrays. Das frühere Eingangsarchiv `representation-manjaro-001.tar.gz`
mit gebundenem Hash
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`
lag diesem Audit nicht nochmals vor. Seine Identitätsprüfung gehört zum
ausgeführten Treiber; hier wurden die im neuen Paket enthaltenen Datenbits
direkt geprüft, nicht das frühere Archiv erneut gehasht.

Die vorhandenen Python-Verifikatoren bestehen für alle sechs Zellen.
Sämtliche gespeicherten Zelldiagnosen werden exakt reproduziert; die damals
gemessenen Zeiten werden auf Konsistenz geprüft und nicht neu gemessen.
Auch Gruppenstatistiken, Paardifferenzen und Entscheidung stimmen exakt.
Die gespeicherten sechs nativen Optionsobjekte, 28 Syntaxentscheidungen,
sechs Referenzfälle, konkreten Plugins, Seeds und 100/2-Einstellungen bestehen
ihre Verträge. Die sechs Referenzdiagnosen wurden erneut aus den festgelegten
Bäumen berechnet. Tatsächliche Haswell-/Threadlimit-1-Nachweise vor/nach Fit
und Pins Python 3.12.14, Julia 1.13.1, PySR 2.6.0 und SymbolicRegression 2.5.1
sind konsistent. Dies prüft archivierte native Nachweise; Julia wurde hier
nicht neu ausgeführt.

Zusätzlich erfolgte eine unabhängig formulierte skalare Auswertung mit
`math.exp/sin/cos`, ohne Verwendung des Projekt-Baumauswerters oder seiner
Fehlerfunktionen: alle 51 Originalbäume auf beiden Rastern, gespeicherte
Vorhersagen, Residuen, Trainings-MSE, vier relative Fehler, Komplexitäten,
Grammatikregel und ursprüngliche Auswahl bestätigt. Größte skalierte
Abweichung zu gespeicherten Vorhersagen: `2,15e-16` als aufgerundete Grenze;
größte relative Abweichung der Kurvenmetriken: `1,41e-15`. Unveränderte
Replaytoleranzen eingehalten. Endpunkte, endliche Nenner, Minima/Mediane/Maxima
und Seed-Differenzen wurden zusätzlich aus dieser Rechnung bestätigt.

Alle Originaldateien sind nach dem Audit erneut unverändert bestätigt.
Serialisierte Julia-Zustände und Pickle-Dateien wurden nur gehasht, nicht
geladen. Keine Suche, Optimierung, Wiederaufnahme, Ersatzwahl oder zusätzliche
wissenschaftliche Zelle ausgeführt. Die erfolgreiche
[Implementierungs-CI](https://github.com/craexxn/ringdown-sr/actions/runs/41600969196)
und das in #52 dokumentierte übermittelte KI-basierte Review sind vorhandene
Implementierungsnachweise; sie wurden hier nicht wiederholt. Dieser Audit
ist eine eigene Ergebnisprüfung. Konsistente Hashes und Metadaten sind keine
externe Authentizitätsgarantie gegen einen vollständigen Austausch aller Belege.

## 2. Vergleich und Originalauswahl

K bezeichnet `unrestricted`, A `no_nested_trig`. Beide verwenden ursprüngliche
Sekunden, 100 lokale Optimiereriterationen mit zwei zusätzlichen Neustarts,
beide Häufigkeitsschalter, 200 Suchiterationen, zwei Populationen zu 32 und
50 Zyklen. Die einzige geplante Intervention ist das Verbot sämtlicher
direkter und entfernter trigonometrischer Nachfahren unter `sin/cos` in A.

| Zelle | Seed | Arm | Frontgröße | Originalindex | Komplexität |
| --- | ---: | --- | ---: | ---: | ---: |
| 1 | 20261020 | K | 10 | 9 | 19 |
| 2 | 20261020 | A | 9 | 8 | 17 |
| 3 | 20261021 | A | 8 | 7 | 18 |
| 4 | 20261021 | K | 8 | 7 | 19 |
| 5 | 20261022 | K | 9 | 8 | 16 |
| 6 | 20261022 | A | 7 | 6 | 20 |

Indizes sind nullbasiert. Alle 27 K- und 24 A-Exporte haben Kurvenstatus
`outside_tolerance`, Strukturstatus `not_supported` und Parameterstatus
`not_assessed`. Kein ungewählter Kandidat ist kurvengut. Alle 24 A-Bäume
erfüllen die Grammatikregel; drei K-Kandidaten enthalten verschachtelte
Trigonometrie. Die 51 Kandidaten sind keine 51 unabhängigen Wiederholungen.

| Zelle | Trainings-MSE | Training RMS | Training Max | Diagnose RMS | Diagnose Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.002035415470878259 | 0.1726022643772139 | 0.11871316606369353 | 0.17779847047721714 | 0.11849460042632555 |
| 2 | 0.000039412280919507404 | 0.024017939038265972 | 0.016236442498752158 | 0.024506784539625116 | 0.01635200791191633 |
| 3 | 0.000723246806946773 | 0.102887642412535 | 0.09889590318349817 | 0.10295276558468579 | 0.09703071038041655 |
| 4 | 0.0005124928763662695 | 0.08660916865146916 | 0.12353801751502114 | 0.08347975398578916 | 0.12110438512901311 |
| 5 | 0.000723243966949056 | 0.1028874404061427 | 0.09882281122108816 | 0.10295592136912703 | 0.09694909402421059 |
| 6 | 0.038374818978121165 | 0.7494507926469466 | 0.7300814213504434 | 0.9034133862690139 | 1.340410142222667 |

RMS und Max sind relativ zur jeweiligen Wahrheit auf dem jeweiligen Raster.
Die festen Grenzen verlangen RMS ≤ 0,001 und Max ≤ 0,01 auf beiden Rastern.
Selbst die beste A-Auswahl in Zelle 2 überschreitet die RMS-Grenze auf dem
Diagnoseraster um den Faktor 24,51 und die Maximalgrenze um den Faktor 1,64.

Die 15 Fehler-/MSE-Werte der drei frischen K-Auswahlen stimmen exakt mit den
veröffentlichten 100/2-Auszügen des
[früheren Budgetvergleichs](free_optimizer_budget_results_manjaro_001.md)
überein. Dies ist ein Abgleich der dokumentierten Werte, kein vollständiger
Audit des weiterhin fehlenden früheren Budgetarchivs.

## 3. Seed-Differenzen und Gruppenstatistiken

Differenzen sind A minus K; Werte in den folgenden Tabellen sind gerundet.
Die vollständigen Ausgangswerte stehen oben und unverändert im Originalbericht.

| Seed | Delta MSE | Delta Training RMS | Delta Training Max | Delta Diagnose RMS | Delta Diagnose Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20261020 | -0.00199600319 | -0.148584325 | -0.102476724 | -0.153291686 | -0.102142593 |
| 20261021 | +0.000210753931 | +0.016278474 | -0.024642114 | +0.019473012 | -0.024073675 |
| 20261022 | +0.03765157501 | +0.646563352 | +0.631258610 | +0.800457465 | +1.243461048 |

A senkt die Trainings-MSE beim ersten Seed um 98,06 %. Beim zweiten steigt
sie um 41,12 %, beim dritten auf das 53,06-Fache. Beim zweiten Seed sinken
die Maximalfehler trotz höherer MSE/RMS. Alle drei Erfolgswechsel bleiben
`nicht bestanden -> nicht bestanden`; kleinere Einzelwerte ändern den
primären Zählendpunkt nicht.

| Metrik | Arm | Minimum | Median | Maximum | Endlich/geplant |
| --- | --- | ---: | ---: | ---: | ---: |
| Trainings-MSE | K | 0.000512493 | 0.000723244 | 0.002035415 | 3/3 |
| Trainings-MSE | A | 0.000039412 | 0.000723247 | 0.038374819 | 3/3 |
| Training RMS | K | 0.086609 | 0.102887 | 0.172602 | 3/3 |
| Training RMS | A | 0.024018 | 0.102888 | 0.749451 | 3/3 |
| Training Max | K | 0.098823 | 0.118713 | 0.123538 | 3/3 |
| Training Max | A | 0.016236 | 0.098896 | 0.730081 | 3/3 |
| Diagnose RMS | K | 0.083480 | 0.102956 | 0.177798 | 3/3 |
| Diagnose RMS | A | 0.024507 | 0.102953 | 0.903413 | 3/3 |
| Diagnose Max | K | 0.096949 | 0.118495 | 0.121104 | 3/3 |
| Diagnose Max | A | 0.016352 | 0.097031 | 1.340410 | 3/3 |

Parameterfehler für Frequenz, Abklingzeit, Amplitude und komplexe Amplitude
sind unter beiden Armen `not_assessed / unsupported_structure`: jeweils
0/3 verfügbare Werte, Minima/Mediane/Maxima und Paardifferenzen `null`.
Unterstützte Rekonstruktionen und kurvengute ungewählte Kandidaten: jeweils
0 in beiden Armen. `physical_identification` bleibt `not_assessed`.

## 4. Originalformeln und Strukturgrenzen

Die Anzeigeformeln sind unverändert aus den Exporten übernommen. Die Prüfung
verwendete die ursprünglichen Bäume mit hexadezimalen Float64-Konstanten.

Zelle 1, K, Seed 20261020:

```text
sin(0.1548412379556712 / (((t / 0.020736597872640435) + 0.09476507199059332) / sin((((t / -0.024285952408210423) + 0.028763403261519695) / 0.026247968165630152) + 0.4505552422640563)))
```

Zelle 2, A, Seed 20261020:

```text
sin(-1.7387305557106205 / ((-0.3177011764624364 / (t + -0.031294150428860974)) + -8.928760912133699)) * sin((t + -0.0070000791991127135) / -0.0006366553890765741)
```

Zelle 3, A, Seed 20261021:

```text
(sin((0.008997050886470683 - t) / 0.0006357214395665264) / 0.0013454886381542943) * (((0.04923317600773583 - t) - t) * (0.024629082512441707 - t))
```

Zelle 4, K, Seed 20261021:

```text
((cos(t * 1570.8904367489856) * -29.604967206294102) * cos((0.03464013179096598 - t) * (t * 4318.804181487477))) * (t - 0.029605234026357594)
```

Zelle 5, K, Seed 20261022:

```text
((t - 0.024621361363751842) * sin((t * -1573.0620353248692) - -1.586331578652905)) * ((t - 0.02462136137876959) * 1486.7518054008688)
```

Zelle 6, A, Seed 20261022:

```text
sin((0.00023393292227888007 / (t + (t + (((t * -0.14426166653224837) + t) + -0.0032248117047699366)))) / ((t + 0.0006492948562997201) / -0.019050440546135146))
```

Keine Originalauswahl enthält einen expliziten `exp`-Operator. Drei ungewählte
Kandidaten in Zelle 2, Indizes 1–3, enthalten Exponentialoperatoren: eine
einfache Exponentialfunktion, deren skalierte Variante und eine verschachtelte
Exponentialfunktion. Keiner enthält einen Oszillationsfaktor oder besteht die
Kurvengrenzen. Eine erfolgreiche exponentielle Ringdown-Rekonstruktion ist
damit auch unter den ungewählten Frontkandidaten nicht belegt. Der begrenzte
Strukturerkenner liefert keinen algebraischen Unmöglichkeitsbeweis.

Die K-Auswahlen für die letzten beiden Seeds erfüllen bereits die A-Regel.
Dass A dort schlechtere RMS-Werte erzielt, ist mit einer veränderten
Suchtrajektorie vereinbar; es belegt keinen bestimmten Mutationsmechanismus.
Die Grammatikregel ist kein nachträglicher Filter derselben Kandidatenmenge.

## 5. Aufwand

| Zelle | Arm | Zellzeit, s | Fit einschließlich JIT/Export, s | Fit-Callbacks |
| --- | --- | ---: | ---: | ---: |
| 1 | K | 56.842 | 41.853 | 935848 |
| 2 | A | 58.037 | 42.173 | 867098 |
| 3 | A | 56.443 | 40.542 | 635436 |
| 4 | K | 56.491 | 41.533 | 808192 |
| 5 | K | 55.199 | 40.124 | 640190 |
| 6 | A | 55.692 | 39.655 | 489913 |

Die Zellzeit umfasst Start, Suchworker, Export und nachgelagerte Pythonprüfung;
die direkte Workerzeit wurde zusätzlich gegen das 600-Sekunden-Limit geprüft.
Der Gesamtcallbackzähler ist jeweils um eins größer, wegen der separaten
Nullauswertung nach dem Fit. Ein vollständiger Backendevaluationszähler ist
`unavailable / not returned by equation_search`. Gleiche nominelle Budgets
ergeben keine gleichen Callbackzahlen oder verbrauchten Rechenzeiten.

## 6. Konsequenz und offene Fragen

Der technisch vollständige Vergleich stützt die Hypothese **nicht**.
Die zusätzliche Grammatikregel wird nach dem angenommenen Plan nicht als
neues Suchprofil übernommen. Einzelne bessere Fehlerwerte rechtfertigen
weder eine Ausnahme vom Endpunkt noch eine weitere Restriktionsstufe.
Der negative Befund gilt für diesen bekannten Entwicklungsfall und drei
bekannte Seeds, nicht als allgemeiner Nachweis einer schlechteren Methode.

Der Versuch endet hier. Weitere freie Suchversuche bleiben bis zu einer
neuen begründeten Methodenentscheidung unterbrochen; keine Wiederholung,
Ersatzseeds, Budgeterhöhung, Nachfits oder neue Einschränkungen sind freigegeben.
Das Forschungsziel freier Formelfindung bleibt bestehen. Der bekannte
Strukturfit bleibt privilegierte Referenz; ein Abbruch der Masterarbeit oder
eine Umstellung auf vorgegebene Ringdown-Formeln folgt daraus nicht.

Nächster abgegrenzter Schritt ist die sachliche Neubewertung des weiteren
methodischen Vorgehens anhand der abgeschlossenen Befunde. Wissenschaftliche
Formelauswahl, Übertragbarkeit, Hintergrund-/Kovarianzdesign und der frühere
Budgetarchiv-Audit bleiben offen. Keine Hauptversuchsfreigabe; keine
physikalische Identifikation. Der Alias-Blindfleck bei `8*fs` bleibt bestehen.
Der frühere Teilversuch `trajectory-manjaro-001` bleibt unverändert unvollständig.
