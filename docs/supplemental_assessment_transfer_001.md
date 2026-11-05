# Zusatzbewertung Transfer 001 – Stufe 1

Stand: 05.11.2026. Lesende Anwendung der [Bewertungsfassung 1](supplemental_assessment.md)
auf das vollständige, verifizierte Original `transfer-manjaro-001.tar.gz`.
Implementierung und Versionsvertrag wurden vor Anwendung als
`fee9418071834b1ea42692cb436ecdd8fb6d4fd3` committed. Der abschließende Export
verwendet `a7d615fda122ab59124987729527303090225a13`, einschließlich einer
zusätzlichen Prüfung auf während der Veröffentlichung eingefügte Dateien.
Bewertungsregeln, sämtliche Einzelbewertungen und historischer Serienbericht
sind gegenüber der ersten Anwendung bytegleich; nur die Softwarebindung des
Abschlussberichts und sein Manifest ändern sich.

## Primärdaten und Prüfung

Archiv-SHA-256 vor und nach Verarbeitung:
`e363fe1be629973a460fc6e2188bf680c21b2c5519d331bc7e257968dcaaa139`.
18 ursprüngliche Auswahlen, ursprüngliche Indizes und Kandidatenhashes,
vollständige Manifeste, Quellen-/Datenbindungen und historische Nachweise
wurden lesend geprüft. Archivprogramme wurden nicht ausgeführt.
Keine neue Suche, kein Fit, keine neue native Gesamtaudit-Serie.

Eine separate Prüfung mit exakten rationalen Darstellungen der Float64-Werte
bestätigt alle 18 Noten. Alle Originalkandidaten und Auswahldiagnosen wurden
wertgleich, der vollständige historische Serienbericht bytegleich übernommen.
Für jeden Fall stimmt neue Klasse A genau mit dem alten Kurvenmarker überein.
Manifest und Abschlussstatus sind konsistent; kein Sperrmarker ist vorhanden.

## Getrennte Signalgruppen

| Signal | Geplant | A | B | C | D | Nicht bewertbar |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| anchor | 3 | 0 | 0 | 1 | 2 | 0 |
| frequency | 3 | 1 | 0 | 2 | 0 | 0 |
| decay | 3 | 1 | 1 | 1 | 0 | 0 |
| phase | 3 | 2 | 0 | 0 | 1 | 0 |
| amplitude | 3 | 1 | 1 | 1 | 0 | 0 |
| combined | 3 | 2 | 1 | 0 | 0 | 0 |

Die feinere Skala beschreibt den Abstand zu den bisherigen engen Grenzen.
Sie verbessert keine Formel und beweist weder eine Ringdown-Identität noch
Definitionslückenfreiheit. Die historischen C-/S-Zählungen bleiben unverändert.

## Ursprüngliche Einzelentscheidungen

Kennzahlen sind die unveränderten gespeicherten Float64-Werte in rücklesbarer
Dezimaldarstellung. Der Auswahlindex ist wie in `result.json` nullbasiert.

| Zelle | Seed | Signal | Index | Klasse | RMS Training | Max Training | RMS Diagnose | Max Diagnose |
| ---: | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 20261210 | anchor | 10 | D | 0.07290999064390653 | 0.06843973835452644 | 0.07303252446279813 | 0.06678998395381874 |
| 2 | 20261210 | frequency | 11 | C | 0.022421099508147458 | 0.02514371265890669 | 0.021716670756057585 | 0.024630416152414902 |
| 3 | 20261210 | decay | 11 | C | 0.02745118797988848 | 0.011247039667094616 | 0.028656508124732184 | 0.011322058594596507 |
| 4 | 20261210 | phase | 9 | A | 1.0608867760654603e-11 | 1.4310400087174246e-11 | 1.0642335606726655e-11 | 1.4303697115655434e-11 |
| 5 | 20261210 | amplitude | 9 | A | 1.1087020966781015e-12 | 8.153477892853798e-13 | 1.1236345582236383e-12 | 8.08686451137618e-13 |
| 6 | 20261210 | combined | 11 | A | 2.68833930294515e-11 | 3.912115076413595e-11 | 2.6040966773698423e-11 | 3.881239774102368e-11 |
| 7 | 20261211 | decay | 7 | A | 5.187188515705113e-12 | 2.810592036883719e-12 | 5.494370185018493e-12 | 2.8464453016852274e-12 |
| 8 | 20261211 | phase | 8 | A | 1.6520377380601242e-09 | 2.0752367463350296e-09 | 1.6599677168447133e-09 | 2.081919858731851e-09 |
| 9 | 20261211 | amplitude | 11 | B | 0.006923938873793328 | 0.0064102422765819345 | 0.00713405911606815 | 0.007003432825952505 |
| 10 | 20261211 | combined | 9 | A | 1.8471427765358967e-11 | 1.710531716270225e-11 | 1.856295732064314e-11 | 1.720545927952344e-11 |
| 11 | 20261211 | anchor | 9 | C | 0.017440372953693856 | 0.014731383635450578 | 0.017543284702701733 | 0.014095653499650003 |
| 12 | 20261211 | frequency | 10 | C | 0.0381715628369685 | 0.028783162457256158 | 0.038745060744289364 | 0.033578840086665764 |
| 13 | 20261212 | amplitude | 13 | C | 0.036942679597517646 | 0.044031978951399875 | 0.03633360771774242 | 0.04288969485106975 |
| 14 | 20261212 | combined | 14 | B | 0.0028697495115911874 | 0.0031985706801725424 | 0.0028014195478948305 | 0.003114292516252572 |
| 15 | 20261212 | anchor | 10 | D | 0.10188646952447318 | 0.09746257638959288 | 0.10198506407310036 | 0.09565393912571385 |
| 16 | 20261212 | frequency | 5 | A | 2.964182997057556e-12 | 1.5949463971764999e-12 | 3.0537646769006453e-12 | 1.6113221867897456e-12 |
| 17 | 20261212 | decay | 12 | B | 0.0074719144591342875 | 0.0037223612100434345 | 0.00776166745870147 | 0.0034534694771903972 |
| 18 | 20261212 | phase | 11 | D | 0.07256659184248325 | 0.0685320274099035 | 0.0723221453299417 | 0.06392705217480421 |

## Ausgabebindung und Grenzen

Lokales separates Ausgabeziel: `results/supplemental-assessment-transfer-002`.
Die Ausgabe wird nicht in die historischen Ergebnisverzeichnisse geschrieben.

| Artefakt | SHA-256 |
| --- | --- |
| `assessment_checksums.json` | `71397aef6d89854b5372cac6d475a56f2ecfa8acc55e63f8de4a4b986e436f00` |
| `assessment_report.json` | `81b39a348e7e1a5651ecd3562752a2fc8c688cfb6382921f358b5a812788a9f0` |
| `assessment_records.json` | `e3c9d80c40d92584f64bfbecc48384415f28cd24b9002d78a5b21c3026f0b264` |

Der vollständige geplante Korpus umfasst 78 Auswahlen. Die drei anderen
Originalarchive fehlen hier; ihre 60 Fälle bleiben `missing`/`not_assessable`
in den jeweiligen geplanten Nennern. Deshalb bleibt der Korpus `incomplete`;
nur die Transfer-Serie wird getrennt freigegeben. Keine gemeinsame Erfolgsquote.
Alle neuen Struktur-, Domain-, Fortsetzungs-, Restterm- und Parameterfelder
bleiben `not_assessed`. Neue PR-67-Originalergebnisse gehören nicht zu diesem Korpus.

Übergabe und weiterer Ablauf stehen im
[bestehenden Arbeitsdokument](representation_implementation_status.md).
Nach Review und bestätigter Übernahme folgt Stufe 2 in einem eigenen PR.
