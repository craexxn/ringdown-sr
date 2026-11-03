# Abgebrochener Suchbudgetvergleich: duration-manjaro-001

Stand: 03.11.2026. Das Originalarchiv ist lesend geprüft. Zwei Zellen sind
abgeschlossen, die dritte scheitert nach der Suche beim Verlust-Replay;
17 Zellen wurden nicht gestartet. **Kein abgeschlossener Budget- oder
Grammatikvergleich.** Der gesicherte CSV-Stand von Zelle 3 enthält jedoch zwei
Formeln mit der gesuchten gedämpften Schwingungsform und sehr kleinen Fehlern
auf beiden Rastern. Feste native Replays reproduzieren alle acht CSV-Verluste
bitgenau. Die Ursache des Abbruchs und eine zusätzliche Grenze des bisherigen
Strukturerkenners sind damit gezielt eingegrenzt.

## Herkunft und eigener Prüfumfang

- Originalarchiv: `duration-manjaro-001.tar.gz`, 273.074 Bytes, SHA-256
  `d73e990cf0c8092f841bc402aa247eca0311c963421249b5e60ae2e73c55074a`.
  Im übermittelten Hash fehlte das erste `d`; alle weiteren 63 Zeichen stimmen.
- Ausführungscommit: `4a9286bfe1aa49db3eda174a3aa14c69f1160e74`, sauberer
  Checkout laut Herkunftsmetadaten. PR #54 ist mit unverändertem Laufzeitcode
  als `d4899ba3a858576758b055c3b36bffb010d5c305` übernommen;
  der einzige Dateiunterschied ist ein versehentlich eingefügter URL-Text
  im Fortsetzungsstand, der mit diesem Dokumentationsnachtrag korrigiert wird.
- Eingefrorener [Methodenplan](search_duration_plan.md): Commit
  `194cfb499e8c53b8243d19c4d11d58a006baff95`, SHA-256
  `8906a66930848d733e5b2744d40c5fa9c4051db2b876e200908d74ae9ac0b75d`.
- Ausführung am 03.11.2026 von 12:28:44 bis 12:32:57 UTC
  (13:28:44 bis 13:32:57 Europe/Vienna), insgesamt 252,508 Sekunden.
  Zelle 3: Fit 121,012 Sekunden, Worker 135,704 Sekunden; kein Zeitlimitabbruch.

Geprüft wurden sichere Archivpfade, alle 93 Dateien, 58 ursprüngliche
Dateianker, 65 erfasste Quellen gegen die Git-Bytes des Ausführungscommits,
Planbytes und kopierte Laufzeitquellen. Das Gesamtabschlussmanifest fehlt
erwartungsgemäß. Status `incomplete`, Abschlussverifikation `failed`, keine
Fehler der Abbruchsicherung; Gruppenaggregate, Paardifferenzen und Vergleich
sind gesperrt. Die geplante Reihenfolge aller 20 Zellen stimmt.

128 Trainingswerte und 889 Diagnosepunkte stimmen bitgenau mit den
eingefrorenen Daten und Fingerprints überein. Das frühere Eingangsarchiv
`representation-manjaro-001.tar.gz` lag hier nicht erneut vor; dessen Hash
wurde nicht unabhängig nachgeprüft. Die verfügbaren archivierten Vorprüfungen,
Zellmanifeste, Profile und Parameter wurden gegen die gebundenen Quellen
geprüft. Die unveränderten strengen Zellverifikatoren bestehen für Zellen 1/2
und reproduzieren deren Diagnosen exakt. Alle 14 exportierten Bäume wurden
zusätzlich skalar auf dem Trainingsraster nachgerechnet.

Die acht CSV-Formeln von Zelle 3 wurden mit einem Parser für ausschließlich
Zahlen, `t`, vier Grundrechenarten und `exp/sin/cos` eingelesen. Bei allen 14
vollständigen Exporten der Zellen 1/2 rekonstruiert derselbe Parser exakt die
gesicherten Bäume einschließlich Konstantenbits und Auswertungsreihenfolge.
Alle acht rekonstruierten Bäume von Zelle 3 bestehen die Grammatikprüfung.
Unabhängige skalare und NumPy-Auswertungen auf beiden Rastern sowie Rechnungen
mit 80 Dezimalstellen für die zwei guten Formeln bestätigen den Kurvenbefund.

Zusätzlich wurden alle acht festen CSV-Bäume mit geprüftem Repositorycode
im gepinnten Backend (PySR 2.6.0, Julia 1.13.1, SymbolicRegression 2.5.1)
ohne Suche oder Optimierung ausgewertet. Native Baumrundreise, Komplexitäten,
Grammatikprüfung und Vorhersage-Replay bestehen; alle acht nativen Verluste
stimmen bitgenau mit der CSV überein. Serialisierte Julia-Zustände und
Pickle-Dateien wurden nicht geladen, Archivcode wurde nicht ausgeführt.
Sämtliche Originaldateien sind nach den Prüfungen unverändert.

## Gesicherter Teilstand

Alle drei begonnenen Zellen verwenden Seed 20261103 und unverändert 100/2
für die lokale Konstantenoptimierung. RMS-Werte sind relativ zum Signal auf
dem jeweiligen Raster; die feste Grenze beträgt 0,001, für Maximalfehler 0,01.

| Zelle | Grammatik | Iterationen | Status | Training RMS | Diagnose RMS |
| --- | --- | ---: | --- | ---: | ---: |
| 1 | unrestricted | 200 | completed, Originalauswahl Index 4 | 0,851636 | 0,877301 |
| 2 | no_nested_trig | 200 | completed, Originalauswahl Index 8 | 0,669129 | 0,688406 |
| 3 | no_nested_trig | 2000 | failed, keine veröffentlichte Originalauswahl | — | — |

Die CSV von Zelle 3 enthält acht Zeilen. Zwei davon sind:

```text
Komplexität 11, CSV-Index 6:
sin((t * -1570.7963268129254) + 1.5707963269021925) / exp(t * 124.99999999938294)

Komplexität 13, CSV-Index 7:
sin(((t * -506.561728545318) + 0.506561728553073) * 3.1008981497836676) / exp(t * 124.99999999938294)
```

| Komplexität | Gespeicherte/native MSE | Training RMS | Training Max | Diagnose RMS | Diagnose Max |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 11 | 3,947379855932181e-22 | 7,60106e-11 | 7,93488e-11 | 7,82769e-11 | 8,09420e-11 |
| 13 | 2,4108123730080023e-23 | 1,87846e-11 | 2,13410e-11 | 1,93512e-11 | 2,16265e-11 |

Die vier Kurvenmetriken stammen aus unabhängiger skalarer Auswertung der
CSV-Bäume. Beide Formeln sind algebraisch
`exp(-d*t) * cos(omega*t + phi)` mit Amplitude 1. Aus den vorhandenen
Konstanten, ohne Nachfit, folgen:

| Komplexität | Frequenz / Hz | Zerfallszeit / s | Phase / rad |
| ---: | ---: | ---: | ---: |
| 11 | 250,000000002869 | 0,00800000000003949 | -1,07296e-10 |
| 13 | 250,000000000397 | 0,00800000000003949 | -2,65440e-11 |

Index 7 ist das Minimum der gespeicherten CSV-Verluste. Der Worker scheiterte
aber bereits bei Index 6, vor Abschluss des Baumexports und vor der
Auswahlberechnung. `result.json`, `verification.json`, `search_invocation.json`
und Zellabschlussmanifest fehlen. CSV-Minimum und unabhängig rekonstruierte
Formeln sind deshalb **keine nachträglich verifizierte Originalauswahl**.
Die Prüfung des tatsächlichen Suchaufrufs ist im Worker vorhanden, wurde
für Zelle 3 jedoch nicht abschließend als Artefakt veröffentlicht.

## Numerischer Abbruch und Grenze des Strukturerkenners

In `src/ringdown_sr/symbolic.py` vergleicht der Worker nativen Replayverlust,
Tabellenverlust und unabhängige Python-MSE gemeinsam mit dem gespeicherten
Verlust bei `rtol=1e-10, atol=0`. Für Komplexität 11 wird der übermittelte
Fehler exakt reproduziert:

- Nativer/gespeicherter Verlust: `3.947379855932181e-22`.
- Python-MSE mit der Projektfunktion: `3.947378869909249e-22`.
- Absolute Differenz: `9.860229319433307e-29`; relative Differenz
  `2.4979175248653124e-07`, daher verletzt sie die bisherige skalare Schranke.
- Maximale Differenz der Vorhersagen: `1.1102230246251565e-16`;
  der unveränderte amplitudenbezogene Vorhersagevergleich besteht.
- Berechnet Python die MSE aus den **nativen** Vorhersagen, ergibt sich exakt
  der native Verlust. Der Unterschied entsteht hier in der Baumauswertung,
  nicht in der MSE-Reduktion. Dasselbe gilt für Komplexität 13; auch diese
  würde den bisherigen skalaren Vergleich verletzen.

Nahe null verstärkt die Division durch den winzigen Verlust kleine absolute
Rundungsunterschiede. Für Residuum `r` und Vorhersagedifferenz `delta` gilt in
exakter Arithmetik
`|MSE(r-delta)-MSE(r)| <= 2*RMS(r)*RMS(delta) + RMS(delta)^2`.
Für Komplexität 11 ergibt die beobachtete Vorhersagedifferenz etwa `5,13e-28`
als Schranke und erklärt die Abweichung. Das ist eine Fehleranalyse, noch
keine neue implementierte Akzeptanzregel; deren Herleitung muss zusätzlich
Subtraktions- und Reduktionsrundung sowie Gegenfälle berücksichtigen.

Unabhängig davon akzeptiert `src/ringdown_sr/structure.py` bisher nur Produkte
aus einem `exp`- und einem `cos`-Faktor mit rationalen Skalaren. Die
CSV-Bäume erhalten daher `not_supported / exponential_factor_count` und
Parameterstatus `not_assessed`. Sowohl die reziproke Exponentialschreibweise
als auch `sin` mit Phase liegen außerhalb dieses Erkenners. Die algebraische
Ringdown-Form ist hier nachvollziehbar, wird durch den bisherigen automatischen
Marker aber nicht abgedeckt. Ein mechanisches Lockern der MSE-Toleranz würde
diese zweite Grenze nicht beheben.

## Einordnung und nächster abgegrenzter Schritt

Der Teilstand liefert einen starken Hinweis, dass die freie Suche unter
größerem Budget die gewünschte Form finden kann. Er belegt weder eine
Erfolgsrate noch einen Budgetvorteil über fünf Seeds, einen Grammatikvorteil
oder physikalische Identifikation. Es fehlt insbesondere der unbeschränkte
2000er-Lauf desselben Seeds. Der frühere Grammatikbefund bleibt unverändert;
`physical_identification` bleibt `not_assessed`, ebenso bestehen die bekannten
Aliasgrenzen des Rasters und der Entwicklungscharakter des Signals fort.

Empfohlen ist vor weiteren wissenschaftlichen Suchen eine getrennt gebundene
Verifikationsergänzung: gespeicherten Verlust gegen nativen Replayverlust
weiter streng prüfen, unabhängige Vorhersage- und Residuenprüfung beibehalten
und die Nähe-null-Prüfung mathematisch begründen. Die begrenzte Erweiterung
des Strukturerkenners auf algebraisch äquivalente Sinus-/Exponentialquotienten
ist separat zu spezifizieren und mit Gegenfällen zu prüfen. Originalbaum,
Auswertung, Verlust und Auswahl dürfen dabei nicht umgeschrieben werden.

Dieser Audit implementiert keine dieser Änderungen. Die Serie bleibt
unvollständig; keine automatische Wiederaufnahme, Ersatzwahl, zusätzliche
Budgetstufe oder nachträgliche Freigabe. Ein späterer Ausführungsplan muss den
Umgang mit den bereits gesehenen Seeds und der abgebrochenen Serie ausdrücklich
festlegen. Eingefrorene Pläne und Originalarchive bleiben erhalten.
