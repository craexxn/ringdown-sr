# Suchbeobachtung auf Manjaro: trajectory-manjaro-002

Stand: 03.11.2026. Das vollständige Originalarchiv ist lesend geprüft.
Die Serie ist technisch abgeschlossen: sechs Zellen, drei bestandene
Aus/an-Paarvergleiche und Abschlussverifikation. Keine Originalauswahl und
kein numerisch verifiziertes beobachtetes Vorkommen erfüllt die Kurvengrenzen.
Ein beobachteter Baum wird als Exponential-Kosinus-Produkt erkannt; sein
Exponentialfaktor wächst, seine Kurve passt schlecht. Das ist keine
unterstützte abklingende Ringdown-Rekonstruktion.

## 1. Herkunft und Prüfstatus

- Originalarchiv: `trajectory-manjaro-002.tar.gz`, 33.452.109 Bytes.
  SHA-256 selbst bestätigt:
  `99999285f6d7a8c50c54280cc36b526e704af01b07a1ccf95f2227e5e8597f55`.
- Ausführungscommit laut unveränderten Eltern-/Workermetadaten:
  `f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1`, sauberer Checkout, PR #48.
  Der aktuelle Dokumentationsstand beruht auf PR #49,
  `d97c95ddff7facf9d5fc766834855697478c49b6`; die konsumierten Quellen sind
  gegenüber dem Ausführungscommit unverändert.
- Format `ringdown-sr-search-trajectory-2`; ursprünglicher
  [Beobachtungsplan](search_trajectory_plan.md) mit SHA-256
  `fcc52e4099f197df676adc10c3163fc78e87d2a2d4661488b9ce929512da37f3`
  und separate [Replayregel](search_trajectory_replay_policy.md) mit SHA-256
  `e65a52ffd7292599e3d70957414977ede792bad6a64cebbe0e59c080ef241842`.
- Das unveränderte Eingangsarchiv `representation-manjaro-001.tar.gz`
  hat SHA-256
  `a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
  Seine 128 Trainingswerte und 889 Diagnosepunkte stimmen bitgenau mit
  dem neuen Archiv und den eingefrorenen Referenzdaten überein.
- Aufgezeichnete Ausführung am 03.11.2026 von 06:50:55 bis 06:58:02 UTC,
  entsprechend 07:50:55 bis 07:58:02 Europe/Vienna; gemessene Gesamtzeit
  426,986 Sekunden einschließlich der serienbezogenen Vorprüfungen und
  Abschlussphase. Alle Worker bleiben unter 600 Sekunden, die Serie unter
  3600 Sekunden.

Die Prüfung der Archivpfade ergab ausschließlich reguläre Dateien und
Verzeichnisse, keine doppelten Namen oder Pfade außerhalb des Archivwurzelordners.
Das Paket enthält 176 Dateien mit insgesamt 386.336.417 unkomprimierten Bytes.
Alle 175 Einträge des Gesamtmanifests, sämtliche Zellmanifeste und alle 173
eingefrorenen Dateianker stimmen. Die 58 erfassten Quellen wurden zusätzlich
gegen die Git-Bytes des Ausführungscommits geprüft. Auch die tatsächlich
kopierten Python-/Julia-Dateien, beide Pläne, Trainingsrollen und abschließend
erneut sämtliche Archivdateien sind geprüft. Serialisierte Suchzustände und
Pickle-Dateien wurden ausschließlich gehasht, nicht geladen oder ausgeführt.

Die gespeicherten sechs nativen Optionsobjekte einschließlich konkreter
Pluginfelder und die zwölf nativen Vorprüfungsfälle wurden gegen ihre
Verträge geprüft. Seeds, Budgets, Optimierereinstellungen und tatsächliche
Haswell-/Threadlimit-1-Nachweise aller sechs Worker bestehen. Python 3.12.14,
PySR 2.6.0, Julia 1.13.1 und SymbolicRegression 2.5.1 entsprechen den Pins.
Dies ist eine Prüfung der übermittelten Ausführungsnachweise; keine neue
native Optionsprüfung oder Julia-Ausführung während dieses Audits.

Die vorhandenen Python-Verifikatoren wurden auf alle sechs extrahierten
Zellen angewendet. Sämtliche gespeicherten Diagnosen, Beobachtungen,
Statusangaben, Fehlerwerte und Parameterbefunde wurden exakt reproduziert;
nur die neu gemessene Offline-Prüfzeit ist naturgemäß kein Gleichheitsziel.
Alle drei Paarvergleiche wurden erneut geprüft. Sie bestätigen identische
exportierte Originalergebnisse einschließlich Frontreihenfolge, Bäumen,
Auswahlindex, Vorhersagen, Residuen, Verlusten und Callbackzahlen; allein
validierte Zeitangaben sind ausgenommen. Verdeckte Zustände werden damit
nicht als identisch bestätigt.

Zusätzlich erfolgte eine unabhängige Nachrechnung ohne Import der
Projekt-Diagnosefunktionen:

- Skalarer Originalbaum-Replay mit `math.exp/sin/cos` für alle 54
  exportierten Frontkandidaten auf beiden Rastern; Vorhersagen, Trainings-MSE,
  alle vier relativen Kurvenfehler und ursprüngliche Auswahl bestätigt.
- Alle 12.450 verfügbaren nativen Vorhersage-/MSE-Paare aus den gespeicherten
  Float64-Bits mit `math.hypot` nachgerechnet. Größte relative Abweichung
  rund `4,33e-16`, innerhalb der unveränderten Verlusttoleranz `1e-10`.
  Das reproduziert die MSE der gespeicherten nativen Vorhersagen; die
  Originalbäume wurden hier nicht nochmals in Julia ausgewertet.
- Alle 62.384 Rohpositionen erneut gezählt und ihrer Quelle, Ereignisnummer,
  Position, ihren Originalbits und Baumkennungen zugeordnet. Baumformen,
  Erst-/Letztvorkommen und Statusnenner stimmen mit dem Bericht überein.
- Die einzige erkannte Produktform zusätzlich analytisch nachgerechnet;
  siehe Abschnitt 4.

Originaldateien blieben unverändert. Keine Suche, Optimierung, Wiederaufnahme
oder zusätzliche wissenschaftliche Zelle ausgeführt. Die vollständige
[Implementierungs-CI](https://github.com/craexxn/ringdown-sr/actions/runs/41437880627)
wurde als vorhandener Nachweis übernommen, nicht wiederholt. Prüfsummen und
konsistente Metadaten liefern keine externe Authentizitätsgarantie gegen einen
vollständigen Austausch aller Nachweise.

## 2. Originalauswahl und Endfronten

Die Reihenfolge bleibt aus/an für Seed 20261020, an/aus für 20261021 und
aus/an für 20261022. Alle Läufe verwenden 100 lokale Optimiereriterationen,
zwei zusätzliche Neustarts, beide Häufigkeitsschalter und die ursprüngliche
Sekundenkoordinate. Je 200 Suchiterationen, zwei Populationen zu 32 und 50 Zyklen.

| Seed | Zellen | Kandidaten je Front | Originalindex | Trainings-MSE | Training RMS | Training Max | Diagnose RMS | Diagnose Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20261020 | 1 / 2 | 10 | 9 | 0.002035415470878259 | 0.172602 | 0.118713 | 0.177798 | 0.118495 |
| 20261021 | 3 / 4 | 8 | 7 | 0.0005124928763662695 | 0.086609 | 0.123538 | 0.083480 | 0.121104 |
| 20261022 | 5 / 6 | 9 | 8 | 0.000723243966949056 | 0.102887 | 0.098823 | 0.102956 | 0.096949 |

Indizes sind nullbasiert; Fehlerwerte außer MSE sind hier gerundet.
RMS und Max sind relativ zur jeweiligen Wahrheit auf dem jeweiligen Raster.
Die unveränderten Grenzen sind RMS ≤ 0,001 und Max ≤ 0,01 auf beiden Rastern.
Ergebnis: 0/3 erfolgreiche Originalauswahlen je Arm, ebenso kein erfolgreicher
Frontkandidat. Die 54 Exporte sind 27 paarweise identische Kandidatenplätze,
keine 54 unabhängigen Entdeckungen. Keine Endfront enthält einen expliziten
`exp`-Operator; Strukturstatus `not_supported`, Parameterstatus `not_assessed`.

Alle 15 bereits dokumentierten Fehler-/MSE-Werte der drei historischen
100/2-Auswahlen stimmen exakt mit den neuen Auswahlen überein. Dieser
Abgleich betrifft die [veröffentlichten Berichtsauszüge](free_optimizer_budget_results_manjaro_001.md),
nicht das vollständige frühere Budgetarchiv; dessen unabhängiger Audit bleibt offen.

## 3. Was an den Beobachtungspunkten vorkommt

| Seed | Aufnahmen | Mitgliedspositionen | Verifiziert | Numerisch ungeklärt | Nicht beurteilt | Eindeutige Bäume | Baumformen |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20261020 | 400 | 20.798 | 19.647 | 2 | 1.149 | 4.761 | 1.601 |
| 20261021 | 400 | 20.794 | 19.458 | 146 | 1.190 | 4.691 | 1.946 |
| 20261022 | 400 | 20.792 | 19.524 | 9 | 1.259 | 3.790 | 1.486 |
| Summe je Lauf | 1.200 | 62.384 | 58.629 | 157 | 3.598 | 13.242 | 5.033 |

Es sind 38.400 Populationspositionen und 23.984 Hall-of-Fame-Positionen.
Laufübergreifend dedupliziert bleiben 13.214 vollständige Bäume und 4.811
Baumformen. Diese zusätzlichen Nenner ersetzen weder Rohpositionen noch die
drei Entwicklungsseeds; wiederholte Hall-of-Fame-Einträge sind abhängig.

| Seed | Bäume mit explizitem exp | exp-Positionen Population / Hall of Fame | Verifiziert / ungeklärt / nicht beurteilt |
| --- | ---: | ---: | ---: |
| 20261020 | 17 | 7 / 129 | 134 / 0 / 2 |
| 20261021 | 80 | 98 / 498 | 561 / 28 / 7 |
| 20261022 | 45 | 64 / 1 | 60 / 0 / 5 |

Explizite Exponentialoperatoren sind in 142 unterschiedlichen vollständigen
Bäumen und 797 Mitgliedspositionen vorhanden. Das belegt weder eine passende
Hüllkurve noch Ringdown-Struktur. Unter den 58.629 verifizierten Vorkommen
gibt es keinen Kurven- oder Parametererfolg. Auch unter den beobachteten
Bäumen mit durchgehend verifizierten Vorkommen ist der kleinste Trainingsverlust
je Seed derselbe wie bei der Originalauswahl; diese Bäume gehören zur Endfront.
Ein übersehener erfolgreicher beobachteter Kandidat ist damit nicht nachgewiesen.

Die 157 ungeklärten Vorkommen betreffen 56 Bäume innerhalb ihrer jeweiligen
Läufe. 155 Vorkommen widersprechen im Vergleich nativer/Python-Vorhersagen
der strengen skalierten Toleranz, darunter zwei auch im MSE-Vergleich.
Drei widersprechen beim gespeicherten gegenüber dem aktuellen nativen Verlust;
eines davon gehört zugleich zur ersten Gruppe. Die Gründe überlappen.
93 ungeklärte Positionen liegen in der Hall of Fame des zweiten Seeds,
die übrigen 64 in zurückgegebenen Populationen. Alle 3.598 nicht beurteilten
Positionen enthalten nichtendliche gespeicherte Loss-/Costwerte; zusätzliche
Einheiten- oder Replaygründe bleiben sichtbar.

Alle nativen Replaynachweise sind intern konsistent. Die ungeklärten
Mitgliedspositionen bleiben dennoch ungeklärt und ohne positive Marker.
`completed / passed` bestätigt die vollständige Erfassung und regelgemäße
Klassifikation, nicht die numerische Bestätigung sämtlicher Mitglieder.

## 4. Die erkannte Produktform

In Zelle 3, Seed 20261021, Ereignis 205, Populationsposition 11 kommt genau
einmal ein numerisch verifiziertes, vom bestehenden Erkenner erkanntes
Exponential-Kosinus-Produkt vor. Originalbaum in unveränderter Klammerung:

```text
exp(t * 0.2592879446940542) * (cos(t * 1573.4321524908144) * 0.2592879446940542)
```

Baum-SHA-256:
`4489b14acfd2fc4184979c28e898054533b634f31d6f3642db512e12ca805157`.
Komplexität 11; Frequenz etwa 250,419505 Hz, Exponentialrate
`+0.2592879446940542 s⁻¹`, Amplitude `0.2592879446940542`.
Die positive Rate ergibt Wachstum. Eine Abklingzeit ist deshalb
`not_applicable`; der Parameterbefund bleibt `not_assessed / not_decaying`.

Die separat ausgewertete analytische Produktform stimmt auf allen 1017
Abzissen mit dem skalaren Originalbaum überein. Trainings-MSE
`0.0349083241201752`; relative Fehler:

| Raster | RMS | Max |
| --- | ---: | ---: |
| Training | 0.7147998508158401 | 0.7407120553059459 |
| Diagnose | 0.7130248593429227 | 0.739720007023567 |

Der Baum ist in diesen Aufnahmen nicht in der Hall of Fame und nicht in
der Endfront enthalten. Daraus folgt keine nachgewiesene Verlust- oder
Verwerfungsgeschichte: die zurückgegebenen Populationen besitzen keine
übergreifend gesicherte Populationskennung. Auch eine konkrete Entstehung
oder Optimierung dieses Baums ist nicht aufgezeichnet.

## 5. Aufwand und zulässige Folgerung

| Seed | Fit-Callbacks je Arm | Worker aus / an, s | Hook, s | Nativer Replay nach Fit, s |
| --- | ---: | ---: | ---: | ---: |
| 20261020 | 935.848 | 47.295 / 68.245 | 3.803 | 4.649 |
| 20261021 | 808.192 | 51.002 / 71.728 | 5.268 | 4.049 |
| 20261022 | 640.190 | 49.877 / 62.815 | 3.265 | 3.527 |

Der Gesamtcallbackzähler ist jeweils um eins größer. Die Beobachtungsdateien
umfassen je Zelle 29.923.979, 29.612.182 und 25.600.456 Bytes; zusammen
85.136.617 Bytes, innerhalb der Grenzen. Offlineauswertung und nachgelagerte
Einheitenprüfung sind im Bericht separat erfasst. Der große `report.json`
ist kein Bestandteil der auf drei Beobachtungsdateien bezogenen 256-MiB-Grenze.
Zeitdifferenzen umfassen unter anderem JIT und Exporte und sind keine isolierte
Schätzung des reinen Hook-Aufwands.

Der deskriptive Befund ist begrenzt, aber für die nächste Entscheidung nützlich:
Exponentielle Bäume werden an Rückgabepunkten gesehen; eine passende
abklingende Struktur mit erfolgreicher Kurve wurde dort nicht bestätigt.
Die eine erkannte wachsende Produktform zeigt, dass diese allgemeine Form
auftauchen kann. Sie beweist weder einen alleinigen Konstantenoptimierungsengpass
noch, dass zwischen den Aufnahmen nie ein guter Baum existierte. Der begrenzte
Strukturerkenner liefert außerdem keinen algebraischen Unmöglichkeitsbeweis.

Die technische Diagnose ist damit abgeschlossen. Nächster abgegrenzter Schritt
ist die bereits vorgesehene, gezielte Literatur- und Methodenabwägung zur freien
Formelfindung: strukturelle Suchdarstellung und Operatorauswahl, Zusammenspiel
von Struktur- und Konstantensuche sowie Voraussetzungen sinnvoller
Komplexitäts-/Auswahlkriterien. Die bisherigen Kontrollen und dieser Befund
sind dabei als bekannte Entwicklungsdaten zu behandeln. Hier wurde noch keine
Literaturrecherche oder neue Methodenentscheidung durchgeführt.

Keine automatische Wiederholung, Budgeterhöhung, zusätzliche Instrumentierung
oder Umstellung auf vorgegebene Ringdown-Formeln. Ein neuer Versuch benötigt
einen begründeten getrennten Plan. Der bekannte Strukturfit bleibt privilegierte
Referenz, freie Rekonstruktion Forschungsziel gemäß Exposé. Hauptversuche zur
Hintergrundlänge/Kovarianzgewichtung bleiben separat zu planen.
`physical_identification` bleibt `not_assessed`, der Alias-Blindfleck bei `8*fs`
bestehen. Der alte Lauf `trajectory-manjaro-001` bleibt unverändert unvollständig.
