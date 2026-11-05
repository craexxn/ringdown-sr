# Ergänzende Ergebnisbewertung: Kurve, Struktur und Zusatzterme

Seit Stufe 3 erzeugen die beschriebenen Befehle Fassung 3. Der
[Resttermvertrag](supplemental_remainder.md) ergänzt alle regelbasiert erkannten
Ringdown-Grundterme mit jeweils eigener exakter Restzerlegung, zertifizierten
Schranken und getrennten Referenznormen. Keine bevorzugte Komponente und keine
zusätzliche Erfolgs- oder Vernachlässigbarkeitsschwelle. Die Diagnose begrenzt
den exakten reellen Rest, nicht einen Float64-Replayfehler.

Fassung-1- und Fassung-2-Snapshots bleiben unverändert lesbar. Ihre Ergänzung
wird ausdrücklich als `retrospective_upgrade_of_stage1_snapshot` bzw.
`retrospective_upgrade_of_stage2_snapshot` für die Restdiagnose ausgewiesen.
Bei neuen Läufen werden auch Resttermvertrag, Ressourcen und Quellen vor dem
ersten Fit gebunden. Suche und Originalauswahl erhalten diese Daten nicht.
Neue Parametermatches bleiben `not_assessed`. Die folgenden Stufenbeschreibungen
dokumentieren außerdem die ursprünglichen Fassungen und ihre Datenrollen.

Seit Stufe 2 erzeugen die unten beschriebenen Befehle die Bewertungsfassung 2:
zusätzlich zur unveränderten Kurvenskala werden Identität, Originaldomain und
stetige Fortsetzung getrennt geprüft. Der
[Strukturvertrag](supplemental_structure.md) bindet das geschlossene Intervall
vom ersten bis zum letzten verifizierten Trainingssample und die beschlossenen
Beweisregeln/Ressourcen. Die früheren Fassung-1-Verträge und Ausgaben bleiben
erhalten; ihre unten dokumentierten `not_assessed`-Felder beschreiben Stufe 1.
Neue Parametermatches und Zusatzterm-Diagnosen bleiben auch in Fassung 2
`not_assessed`. Die vollständige Anwendung und technische Freigabe der neuen
Fassung werden im [Arbeitsdokument](representation_implementation_status.md) geführt.

Stand: 05.11.2026. Stufe 1 ergänzt zukünftige Schema-3-Piloten und erhält den
retrospektiven Import der vier abgeschlossenen Originalserien. Beide Wege bewerten
ausschließlich die bereits ausgewählten Kandidaten und veröffentlichen getrennte Ausgaben.
Suchverfahren, Bäume, Seeds, Fronten, Auswahlindizes, alte Erkenner sowie
C-/S-, Parameter- und Aliaswertungen bleiben unverändert. Keine neue Suche,
Optimierung oder Anpassung an Referenzparameter gehört zu diesem Export.

## Anbindung zukünftiger Schema-3-Läufe

Der Umfang von PR #69 wurde am 05.11.2026 ausdrücklich um zukünftige Ergebnisse
erweitert; der geprüfte Archivexport bleibt erhalten. Für simulierte Schema-3-Läufe
sind folgende Regeln beschlossen:

- Auf **beiden** Bewertungsrastern ist das bekannte **rauschfreie Signal** die
  Referenz. Verrauschte Messwerte bleiben ausschließlich Ziel der bisherigen
  Fitverluste und Auswahl. Die Alternative einer gemischten Referenz (Messwerte
  im Training, sauberes Signal an Zwischenpunkten) wurde nicht gewählt, damit
  die neue Kurvenklasse in beiden Rastern denselben Rekonstruktionsfehler misst.
- Das Diagnoseraster wird vor dem ersten Fit und der ersten Suche festgelegt:
  `t[k,j] = (k+j/8)/fs`, `k=0..N-2`, `j=1..7`, intervallweise geordnet,
  ohne Randextrapolation. Bei 128 Trainingspunkten sind das 889 Zwischenpunkte.
  Dies setzt die bisherige Rasterdichte fort; es ist keine Aussage über einen
  stetigen Definitionsbereich und keine Vorentscheidung für Stufe 2.

Die separate Fassung
[future_assessment_v1.json](../data/future_assessment_v1.json) trägt die Kennung
`ringdown-sr-future-assessment-1`, Schema `ringdown-sr-future-record-1`. Sie verwendet
dieselben vier normierten Fehler und inklusiven Float64-Grenzen wie die unten
beschriebene Archivfassung. Diese bleibt unverändert retrospektiv.

Ein künftiger, gesondert freigegebener Schema-3-Lauf erhält die Zusatzbewertung
mit `--assessment-output`. Beispielsyntax, **keine neue wissenschaftliche
Ausführungsfreigabe**:

```bash
uv run --locked ringdown-sr run configs/pilot_sr_ar1.toml \
  --output results/sr-new-001 \
  --assessment-output results/sr-new-001-assessment
```

Der Checkout muss sauber und committed sein. Beide Verzeichnisse müssen neu,
getrennt und ohne Symlinkpfade sein; projektinterne Ausgaben gehören unter
`results/`, damit die Herkunft aller Worker sauber bleibt. Die Pipeline speichert
`assessment_inputs.npz` (beide Raster und beide sauberen Referenzen) und
`assessment_contract.json` vor dem ersten Referenzfit. Das Anfangsmanifest bindet
ihre Bytes; die automatische Bewertung hält diese Bindung zusätzlich im Speicher
bis zum Ende. Kein Bewertungsraster und keine zusätzliche Wahrheit wird an die
Suchworker übergeben. Seeds, Budgets, Kovarianzen, Originalfronten, Verluste und
Auswahlverfahren bleiben erhalten. Ohne die Option läuft die bisherige Pipeline.

Nach dem unveränderten Lauf erfolgt die lesende Bewertung in einem separaten
Ausgabeordner. Ein späterer Export derselben aufgezeichneten Daten ist möglich:

```bash
uv run --locked ringdown-sr assess results/sr-new-001 \
  --output results/sr-new-001-assessment-002
```

Dieser zweite Aufruf startet keine Suche und keinen Fit. Er benötigt den
aufgezeichneten Vorbereitungssnapshot und dessen Git-Commit lokal; die vier
historischen Originalarchive sind dafür nicht erforderlich. Fehlende Snapshots
älterer Läufe werden **nicht nachträglich erzeugt**. Der zukünftige Pfad unterstützt
derzeit die drei Arme `ordinary`, `known_covariance`, `estimated_covariance` eines
vollständigen Schema-3-Laufs. Historische Spezialtreiber und reale Daten ohne
bekanntes sauberes Signal erhalten damit keine stillschweigende neue Datenrolle.

Der Import prüft vollständiges Dateiinventar und Manifeste, Vorbereitungsversion,
originale Git-Quellen und Herkunft jedes Workers, Konfiguration, Raster-/Signalbits,
Workerinputs, Originalauswahl und Kandidatenbindung. Trainingsvorhersage, Residuum
und Verlust werden an der unveränderten Auswahl nachgerechnet; es gibt keine
erneute Rangbildung. Die Kurvenfehler werden aus dem Originalbaum auf beiden
gespeicherten Rastern berechnet, ohne Vereinfachung, Kürzung oder Schließen von
Definitionslücken. Der Signalnachbau dient ausschließlich der Prüfung der
vorhandenen Referenzbytes, niemals als Ersatz für fehlende Eingaben.

Die vollständige Python-Quellenmenge wird aus dem Git-Baum des
Vorbereitungscommits ermittelt, einschließlich Unterverzeichnissen. Aufgezeichnete
Teilmengen oder zusätzliche Namen sind unzulässig, auch bei konsistent erneuerten
Quellensatz- und Artefakthashes. Vorbereitung und Nachprüfung binden außerdem
Launcher, Python-/Julia-Adapter sowie Python- und Julia-Projektdateien.
Die Elternherkunft und die unmittelbar vor dem Fit erfasste
`worker_provenance` müssen jeweils einen verfügbaren sauberen Git-Stand und
dieselben vollständigen Quellen belegen. Eltern- und
`worker_adapter_source_sha256` sowie die tatsächlich gespeicherten Julia-Kopien
werden gegen die gebundenen Quellen geprüft.

`result.json:rng.python_seed` muss als Integer mit dem konfigurierten Seed
übereinstimmen; `selection` muss `minimum_training_loss_then_complexity` lauten.
Diese Prüfungen übernehmen den vorhandenen Auswahlindex ohne erneute Rangbildung.
Der Bericht bewahrt den verifizierten Originalseed, die aufgezeichnete RNG-Angabe
und die Originalauswahlregel. Fehlende oder widersprüchliche Nachweise sperren die
Bewertung. Ältere vorläufige Schema-3-Pakete ohne vollständige Vorbereitungsbindung
werden nicht nachträglich aufgefüllt; der verankerte historische Archivexport
bleibt davon getrennt und unverändert.

`assessment_records.json` erhält je Arm den Originalkandidaten, die unveränderte
Auswahl samt bisherigen Kennzahlen, die vier neuen Fehler, Kurvenklasse und
ausdrücklich unbewertete Folgestufen. `original-result.json` ist eine bytegleiche
Kopie des ursprünglichen Ergebnisses. Der Bericht bindet vollständige Bedingungen,
Vorbereitungs- und Bewertungssoftware sowie sämtliche Quelldateihashes. Pro Arm
bleibt ein geplanter Fall im Nenner, auch bei `not_assessable`; keine gepoolte
Erfolgsquote über die drei unterschiedlichen Verlustfunktionen.

Nichtendliche Originalbaumwerte oder nicht normierbare Referenzen ergeben
`not_assessable`, keine Klasse D. Quellenwidersprüche, unvollständige Läufe,
fehlende Vorbereitung, Abbruch oder Veröffentlichungsfehler sperren das gesamte
Bewertungspaket ohne positive Aggregate. Der ursprüngliche Laufstatus bleibt
erhalten; der gemeinsame CLI-Aufruf meldet den Bewertungsfehler. Freigabe und
Widerruf verwenden dieselbe unten beschriebene Transaktion wie der Archivexport.
Die Exportfrist von standardmäßig 300 Sekunden beginnt **nach** der Suche;
`assess --timeout-seconds` kann sie ändern. NPZ-Eingaben bleiben auf 2 MiB
entpackte numerische Daten je Datei begrenzt.

Die aufgezeichneten Manifeste belegen interne Konsistenz und Git-Herkunft,
keine externe Signatur oder nachträglich unabhängig beweisbare Aufzeichnungszeit.
Die automatische Anbindung prüft zusätzlich die vor dem Lauf festgehaltenen Bytes.
Die Rasterbewertung ist eine Diagnose am bekannten simulierten Signal und keine
unabhängige wissenschaftliche Validierung oder allgemeine Leistungsbewertung.

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

Beauftragt sind drei aufeinanderfolgende PRs. Stufe 1 ist mit PR #69 und Stufe 2
mit PR #70 übernommen. **Stufe 3 wird jetzt als letzter eigener Bewertungs-PR
umgesetzt.** Die quantifizierte Zusatzterm-Diagnose folgt den am 05.11.2026
bestätigten Mehrfachdiagnosen und begrenzten adaptiven Schranken; der
[Resttermvertrag](supplemental_remainder.md) hält Regeln und Grenzen fest.
Tatsächliche Abnahme und Anwendung stehen im Arbeitsdokument, keine weitere
Bewertungsstufe ist nach Stufe 3 beauftragt.
Kein neuer fachlicher Implementierungsauftrag ist für die Folgestufen erforderlich;
Review-/Übernahmegrenzen gelten weiterhin. Keine zusätzlichen Agenten, kein
eigenständiger Merge und keine neue wissenschaftliche Suche.
