# Ergänzende Ergebnisbewertung: Stufe 1

Stand: 05.11.2026. Die Zusatzbewertung ist retrospektiv. Sie bewertet nur die
ursprünglich ausgewählten Kandidaten aus vier abgeschlossenen Originalserien.
Suchverfahren, Bäume, Seeds, Fronten, Auswahlindizes, alte Erkenner sowie
C-/S-, Parameter- und Aliaswertungen bleiben unverändert. Keine neue Suche,
Optimierung oder Anpassung an Referenzparameter gehört zu diesem Export.

## Beschlossener Versionsvertrag

Bewertungsfassung `ringdown-sr-supplemental-assessment-1`, Einzelbewertungsschema
`ringdown-sr-supplemental-record-1`, maschinenlesbar in
[supplemental_assessment_v1.json](../data/supplemental_assessment_v1.json).
Die inklusive Float64-Grenzsemantik wurde am 05.11.2026 ausdrücklich bestätigt:
dieselben Binary64-Schwellen wie bisher, ohne Anzeigenrundung und ohne zusätzliche
Toleranz. Eine dezimal-exakte Neuinterpretation wurde nicht gewählt, weil sie
Grenzfälle gegenüber dem bestehenden Kurvenkriterium ändern könnte.

| Neue Kurvenklasse | Relativer RMS-Fehler | Relativer Maximalfehler |
| --- | ---: | ---: |
| A | ≤ 0,001 | ≤ 0,01 |
| B | ≤ 0,01 | ≤ 0,02 |
| C | ≤ 0,05 | ≤ 0,10 |
| D | Vier gültige Kennzahlen, aber keine der obigen Klassen erfüllt | |

Beide Grenzen müssen **auf beiden Rastern** erfüllt sein; die beste Klasse gilt.
Die JSON-Fassung hält die Schwellen zusätzlich als exakte Float64-Hexwerte fest.
A entspricht bei denselben gültigen Kennzahlen dem bisherigen Kurvenkriterium C.
Die neue Kurvenklasse C ist kein historischer C-Erfolgszähler.

Die archivierten Originaldiagnosen verwenden je Raster
`relative_rms = ||p-y||₂ / ||y||₂` und
`relative_max = max|p-y| / max|y|`. Training und Zwischenpunkte haben jeweils
ihre eigene Normierung. Keine punktweise Division an Nullstellen, kein zusätzlicher
Faktor √N. Die Kennzahlen werden direkt übernommen und niemals durch eine neue
Berechnung ersetzt. Fehlende Raster oder Werte, negative/nichtendliche Werte,
Bool-Werte und nicht verfügbare untergeordnete Rasterstatus ergeben
`curve.status=not_assessable`, `grade=null` mit Grund. Ein ungültiger Zahlenwert
ist weder D noch ein Nullfehler. Strukturelle Parameterverfügbarkeit entscheidet
nicht über die Verfügbarkeit der Kurvenkennzahlen.

Die 128 Trainings- und 889 Zwischenpunkte beweisen keine Aussage zwischen den
Abtastpunkten. Neue Felder `algebraic_identity`, `domain`, `original_family`,
`continuous_extension`, `remainder` und `new_parameter_match` bleiben in Stufe 1
`not_assessed`. Intervall, Ausschlüsse, exakte Koeffizienten und Resttermregeln
bleiben unbestimmt. Insbesondere wird kein Definitionsbereich vorweg festgelegt.

## Vertrauensanker und Import

Der [Serienkatalog](../data/supplemental_series.json) bindet Originalarchive,
Ausführungscommits, eingefrorene Pläne, vollständige Quellenmengen und geplante
Zellidentitäten. Die Archivanker wurden gegen die Ergebnisdokumente am Commit
`b9636ad92ecd57b24b142f39548a7a713d0934a0` geprüft:

| Serie | Geplant | Ergebnisbeleg | SHA-256 des Originalarchivs |
| --- | ---: | --- | --- |
| duration-manjaro-004 | 20 | [Suchbudget 004](search_duration_results_manjaro_004.md) | `c2d9e330770746030bab9467b682a6b595cac25aa132dbb4decd1c4b03472289` |
| local-optimizer-manjaro-001 | 20 | [Lokales Budget](local_optimizer_results_manjaro_001.md) | `1ab8c0aa91436c4b169c6c6efa8053e04c47ef57d07915f36ac476483276866d` |
| outer-ladder-manjaro-001 | 20 | [Äußere Staffel](outer_search_ladder_results_manjaro_001.md) | `ac7e841b79042e216d6aacae2961ffb8395f298bbcc7ecc11f1092c90b3deb40` |
| transfer-manjaro-001 | 18 | [Transfer](transfer_check_results_manjaro_001.md) | `e363fe1be629973a460fc6e2188bf680c21b2c5519d331bc7e257968dcaaa139` |

Die Zelllisten stammen aus den an ihren ursprünglichen Git-Ständen bestätigten
Planfunktionen, nicht aus der CSV mit gerundeten Kennzahlen. Der Import prüft den
äußeren Archivhash vor dem Lesen, sichere eindeutige TAR-Namen ohne Links/Geräte,
das vollständige Manifest, alle Verbrauchsanker, Abschlussstatus und Provenienz.
JSON-Duplikate, NaN, Infinity und überlaufende Literale wie `1e999` werden verworfen.
Technische Grenzen: 64 MiB komprimiert/pro Datei, 256 MiB insgesamt, 10.000 Member;
numerische NPZ-Dateien höchstens 2 MiB entpackt, ohne Pickle.

Alle historischen Quellen werden gegen Git geprüft. Archivprogramme bleiben
Daten und werden nicht ausgeführt. Ursprüngliche Float64-Datenbits, Signal-/Rasterrolle,
Budget, Seed, Optionen und archivierte Verifikationsnachweise werden gebunden.
`result.json:selected_index`, Diagnoseindex, `source_index`, `is_selected` und der
historische Kandidatenhash müssen übereinstimmen. Alle Kandidaten werden in ihrer
Originalreihenfolge gebunden; bewertet wird ausschließlich die ursprüngliche Auswahl.
Gleiche Formeln in verschiedenen Zellen bleiben getrennte Beobachtungen.

Dies ist eine aufgabenbezogene Importprüfung. Sie behauptet keine neue native
Gesamtnachrechnung aller Kandidaten und keinen identischen Suchverlauf.

## Export und Freigabe

Der Export verlangt einen sauberen, bereits committed Checkout. Er bindet vor der
Anwendung Softwarecommit, Quellenbytes, Serienkatalog, Versionsvertrag sowie
Python-/NumPy-Version; die historische Suchumgebung bleibt getrennt archiviert.
Vollständige Git-Historie beziehungsweise die gebundenen historischen Objekte
müssen lokal vorhanden sein. Der Aufruf benötigt keine Julia-Suche:

```bash
uv run --locked python scripts/export_supplemental_assessment.py \
  --archive transfer-manjaro-001=results/transfer-manjaro-001.tar.gz \
  --output results/supplemental-assessment-001
```

Weitere vorhandene Originalarchive können mit zusätzlichen `--archive SERIES=PATH`
angegeben werden. Nicht angegebene Serien erscheinen ausdrücklich als `missing`.
Ein angegebenes, widersprüchliches Archiv erscheint als `failed`, seine Auswertung
bleibt gesperrt. Es gibt keine Ersatzdaten aus Tabellen. Ein neuer Aufruf benötigt
ein neues Ausgabeziel. Vorhandene Ausgaben, Quellverzeichnisse, Symlinkziele und
Unterverzeichnisse bestehender Originalläufe sind unzulässig. Die Standardfrist
beträgt 300 Sekunden; `--timeout-seconds` darf sie explizit ändern.

Ausgaben:

- `assessment_records.json`: alle 78 geplanten Identitäten; verifizierte Fälle mit
  Originalkandidat, vollständiger unveränderter Auswahldiagnose, Datenbindung und
  getrennten Zusatzfeldern. Fehlende Fälle enthalten keine erfundenen Originalwerte.
- `<serie>-historical-report.json`: bytegleiche Kopie des jeweiligen Originalberichts,
  einschließlich sämtlicher historischer Kennzahlen, Zustände und C-/S-Zählungen.
- `assessment_report.json`: Versionsbindung, Quellenstatus und getrennte Gruppen.
- `assessment_summary.md`: lesbare Übersicht; `assessment_checksums.json` bindet
  sämtliche veröffentlichten Nutz- und Abschlussdateien.

Eine Ausgabe ist nur freigegeben, wenn **kein `ASSESSMENT_LOCKED` existiert**, der
Bericht `status=completed` meldet und das vollständige Manifest mit allen Dateien
übereinstimmt. `completed` bezeichnet den Exportabschluss, keine Freigabe fehlender
Serien: nur Serien mit `verification_status=verified` und
`release=separate_verified_series` sind auswertbar. Fehlende oder ungültige Serien
setzen `corpus_status=incomplete`; eine gemeinsame Erfolgszahl über alle 78
heterogenen Fälle gibt es auch bei vollständigem Korpus nicht.

Quellenbytes werden vor Verbrauch festgehalten und durch die Veröffentlichung
erneut geprüft. Zusammenfassung, Manifest, Nutzdateien und temporärer Erfolgsbericht
werden unmittelbar vor dem abschließenden Umbenennen gegen die vorgesehenen Bytes
verglichen; anschließend wird nochmals geprüft. SIGINT, SIGTERM, Fristablauf sowie
Fehler vor oder nach Veröffentlichung widerrufen die Freigabe. Weitere Signale und
einzelne Schreib-/Löschfehler während des Widerrufs verhindern die übrigen
Aufräumschritte nicht. Gesperrte Fehlerberichte enthalten keine positiven neuen
Aggregate; Teildateien bleiben lediglich Prüfevidenz. Bei dauerhaft unbeschreibbarem
Dateisystem kann kein Programm neue Fehlernachweise garantieren; deshalb sind
Manifest und Sperrmarker zwingende Bestandteile jeder Freigabeprüfung.

Die Gruppierung erhält die ursprünglichen Bedingungen: Suchbudget nach Grammatik
und äußerem Budget; lokaler Vergleich nach lokalem Profil; Staffel nach äußerem
Budget; Transfer getrennt je Signal. Nicht bewertbare Fälle bleiben im geplanten
Nenner (je 5 beziehungsweise 3). Keine neue Auswahl, Deduplizierung oder Nachoptimierung.

## Prüfbasis und nächste Stufen

Die Vorbereitung `assessment-preparation-2026-11-05` wurde als Referenz gelesen;
alle 17 Nutzdatei-Hashes und 29 referenzierten Quelldateien wurden geprüft. Ihre
41 synthetischen Kurvenfälle sind unverändert als
[Referenzfixture](../tests/fixtures/assessment/preparation_curve_cases.json) übernommen.
Zusätzlich prüfen unabhängig formulierte Tests exakte rationale Darstellungen der
Float64-Grenzen und ihre Nachbarn, bekannte Vektornormen, fehlende Zustände,
Auswahl-/Hash-/Rasterwidersprüche sowie Veröffentlichung und Widerruf.
Konkreter Prüf- und Anwendungsstand: [Arbeitsdokument](representation_implementation_status.md).

Beauftragt sind drei aufeinanderfolgende PRs. **Nächste ausstehende Stufe ist
Stufe 2: exakte Strukturprüfung einschließlich Originaldefinitionsbereich und
stetiger Fortsetzung.** Sie beginnt erst nach bestätigter Übernahme von Stufe 1.
Vorher sind insbesondere Intervallkonvention (Vorschlag `[0,127/4096]` s statt
nominalem Aufnahmeende `128/4096` s) und Beweis-/Ressourcengrenzen ausdrücklich zu
klären. Die anschließende Stufe 3 ergänzt eine quantifizierte Zusatzterm-Diagnose;
Zerlegungsregeln und Schrankenverfahren bleiben vor ihrer Umsetzung zu klären.
Kein neuer fachlicher Implementierungsauftrag ist für die Folgestufen erforderlich;
Review-/Übernahmegrenzen gelten weiterhin. Keine zusätzlichen Agenten, kein
eigenständiger Merge und keine neue wissenschaftliche Suche.
