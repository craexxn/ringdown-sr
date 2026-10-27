# Lesender Parameter-Diagnoseexport für gespeicherte Läufe

Stand: 27.10.2026. Schritt 3 des
[Methodenplans](parameter_interpretation_plan.md) ist als nachgelagerter Export
umgesetzt. Er liest einen vollständigen erfolgreichen Schema-3-Lauf und schreibt
ein neues Paket im Format `ringdown-sr-parameter-diagnostics-1`.
Es werden keine Suche, Datenerzeugung, Fits oder neue Verlustauswahl ausgeführt.
Neue Pilotläufe erhalten dadurch keine automatische Parameterinterpretation.

## Aufruf

```bash
uv run --locked python scripts/export_parameter_diagnostics.py results/sr-white-001 --output results/parameters-white-001
```

Die Quelle ist ein einzelner Schema-3-Lauf mit allen drei erfolgreichen Armen.
Für ein vorhandenes Paar unter `white/` und `ar1/` sind zwei getrennte
Aufrufe erforderlich. Der ausdrücklich angegebene Ausgabeordner darf noch
nicht existieren. Quelle und Ausgabe dürfen sich auch über aufgelöste Pfade
nicht überschneiden. Es gibt kein Überschreiben oder Fortsetzen einer Ausgabe.

Die Python-Schnittstelle lautet:

```python
from ringdown_sr.parameter_export import export_parameter_diagnostics

output = export_parameter_diagnostics(source_directory, output_directory)
```

## Paket und Zuordnung

| Datei/Feld | Inhalt |
| --- | --- |
| `diagnostics.json` | Vollständige Diagnose, Quellbezüge und getrennte Herkunft |
| `metadata.json` | Zuletzt geschriebener Abschlussmarker mit Format, Status und SHA-256 der Diagnose |
| `source.file_sha256` | SHA-256 aller konsumierten Quelldateien einschließlich der ursprünglichen Abschlussmetadaten |
| `source.recorded_metadata` / `recorded_initial_metadata` | Unveränderte ursprüngliche Pilotmetadaten |
| `source.recorded_reference_metadata` | Gespeicherte Herkunft der ursprünglichen Referenzstufe |
| `source.sampling`, `time_samples` und `time_fingerprint` | Erklärte Abtastung und tatsächlich verwendete Float64-Zeiten; Fingerprint über Little-Endian-Float64-Bits samt Form |
| `arms.<name>.source_result_file` / `source_result_sha256` | Eindeutiger Quellbezug des Arms |
| `selected_index` und `source_selection` | Gespeicherter Index und unveränderte Auswahlzusammenfassung |
| `candidates[*].source_index` / `is_selected` | Ursprüngliche Reihenfolge und Markierung des ausgewählten Kandidaten |
| `source_candidate` | Vollständiger ursprünglicher Kandidat einschließlich Originalbaum, Konstanten, Verlust, Komplexität, Anzeigetext und Vorhersage |
| `saved_prediction_replay` | Separate Nachrechnung des Originalbaums gegen die gespeicherte Vorhersage |
| `analysis` | Unverändertes Ergebnis der [Parameter-/Aliasdiagnose](parameter_diagnostics.md) |
| `recorded_metadata` / `recorded_initial_metadata` je Arm | Originale Suchmetadaten, einschließlich der aufgezeichneten Umgebung und Quellherkunft |
| `exporter` | Aktuelle Diagnosezeit, Codeherkunft und Diagnoseumgebung; ausdrücklich keine neu erfasste Suchumgebung |

Alle Kandidaten werden exportiert, auch `not_supported`.
Die Ausgabe sortiert, entfernt oder bewertet keine Kandidaten neu.
Sie übernimmt den gespeicherten Auswahlindex nach Prüfung seiner Zuordnung
zur Pilotzusammenfassung. Eine erneute Bestimmung des Minimums gehört nicht zum
Export. Das ursprüngliche `parameter_interpretation=not_attempted` bleibt
sowohl in der Quelle als auch in der übernommenen Auswahlzusammenfassung erhalten.
Die getrennte Diagnose heißt weiterhin `diagnostics_only`.

## Eingabeprüfung und Schutz der Quelle

Die vollständigen Pilot- und Referenzstufen sowie alle drei Sucharme müssen
erfolgreich abgeschlossen sein. Quelle und aufgelöste Artefaktpfade werden
lesend geöffnet. Konsumierte Dateien werden gegen die ursprünglichen
Pilotprüfsummen und workerinterne Dateien zusätzlich gegen deren Manifest
geprüft. Anfängliche und abschließende Pilot-/Workerherkunft müssen zusammenpassen.
Request und gespeichertes Suchbudget müssen übereinstimmen.

Zeitvektoren müssen endlich und Float64 sein, zur gespeicherten Samplezahl
passen und zwischen gemeinsamem Eingang und jedem Arm bitgleich sein.
Es wird keine Achse neu erzeugt oder zurechtgerückt. Eine fremde Achse kann
deshalb weiterhin eine rohe Diagnose, aber keine Nullursprungs-Aliasdiagnose
erhalten. Für die Parameterrechnung werden ausschließlich Originalbaum,
gespeicherte Zeiten und erklärte Abtastrate übergeben. Sauberes Signal,
wahre Parameter, Messziel, Hintergrundfenster und Kovarianzwerte werden dafür
nicht geladen oder berechnet.

Jeder vollständige Baum wird mit dem vorhandenen begrenzten Vertrag validiert.
Komplexität und Knotenzahl müssen zusammenpassen. Der Originalbaum wird auf
seinen gespeicherten Zeiten gegen die gespeicherte Vorhersage nachgerechnet,
mit der bestehenden gemeinsamen Amplitudenskala ohne Untergrenze und
`rtol=1e-12`, normiertem `atol=1e-14`.
Ungültige Bäume, widersprüchliche Indizes und beschädigte Quellen sind Fehler,
keine gewöhnlichen nicht unterstützten Strukturen.
JSON mit doppelten Schlüsseln oder nicht endlichen Zahlen wird abgelehnt.

Die konsumierten Dateien werden unmittelbar vor der Ausgabe erneut geprüft.
Erst nach erfolgreicher Eingabeprüfung, Diagnose und JSON-Serialisierung wird
der neue Ausgabeordner exklusiv angelegt. Bei einem Schreibfehler kann ein
unvollständiger Ausgabeordner zurückbleiben; ohne abschließende Metadaten
gilt er nicht als erfolgreiches Paket. Originaldateien werden nicht verändert.

## Aussagegrenzen

Prüfsummen belegen Konsistenz mit den konsumierten Metadaten, keine externe
Authentizität. Die ursprüngliche `metadata.json` ist dabei ein gesondert
gehashter Vertrauensanker. Unbenutzte Artefakte werden nicht vollständig
nachgerechnet oder durch diese Integritätsprüfung als geprüft ausgewiesen.

Der gespeicherte Vorhersage-Replay und die beiden Replays der Parameterdiagnose
haben verschiedene Aufgaben. Ein fehlgeschlagener roher oder Alias-Replay
bleibt als Diagnosezustand erhalten; er ändert die ursprüngliche Auswahl nicht.
Numerisch verfügbare Parameter bedeuten weder eindeutige physikalische
Identifikation noch Rekonstruktionsleistung. Die Ausgabe bewertet keine
Verluste, SNR-Studien, Generalisierung oder Rechnerunabhängigkeit neu.
Der Haswell-Befund und die CPU-native Wahl bleiben davon unberührt.

## Prüfungen

```bash
uv run --locked pytest -q tests/test_parameter_export.py
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Die Exporttests verwenden unabhängig vorgegebene gespeicherte Artefakte.
Sie prüfen vollständige Kandidatenzuordnung einschließlich nicht unterstützter
Auswahl, exakte Referenzparameter, unveränderte Quellbytes und Zufallszustände,
unabhängige Workerprüfsummen, Eingabe-/Pfadfehler, Änderungen während des Exports
und getrennte Umgebungen. Ein frischer Prozess verbietet PySR-/JuliaCall-Imports
und führt den tatsächlichen Kommandozeilenexport aus.
Die vorhandene CI exportiert außerdem beide ohnehin erzeugten Schema-3-Kontrollen.

