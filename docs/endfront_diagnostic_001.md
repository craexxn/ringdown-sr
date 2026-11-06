# Begrenzte Endfrontdiagnose der vier Originalserien

Umfang vor der Diagnose festgelegt am 06.11.2026, zu
[Leitfadenphase 2](ringdown_recovery_roadmap.md). Diese Untersuchung ergänzt
die drei bestehenden Bewertungsberichte; sie verändert keine Originalauswahl,
Erfolgszählung oder eingefrorene Regel. Keine Suche, kein Fit, keine Erweiterung
des Erkenners und keine Erhöhung seiner Beweisbudgets.

## Vorab festgelegter Umfang

Die vier über [supplemental_series.json](../data/supplemental_series.json)
gebundenen Originalserien sind der gesamte Untersuchungsrahmen: 78 Endfronten,
laut historischen Berichten 193 + 183 + 164 + 198 = 738 Kandidaten. Die
Kandidatenzahlen sind vor einer Archivprüfung nur Berichtswerte.

Reihenfolge: zuerst `transfer-manjaro-001` Zellen 01, 11 und 15 (Ankersignal,
Seeds 20261210, 20261211, 20261212); anschließend die übrigen Fronten aus
Transfer und äußerer Staffel, danach Suchdauer und lokaler Optimierer. Damit
wird auch der übermittelte Befund zu 362 Kandidaten aus Staffel/Transfer
gezielt geprüft, soweit die unveränderten Originalarchive vorliegen.

Vor jeder Verarbeitung müssen Archiv-SHA-256, vollständiges Manifest,
Ausführungs-/Planbindung, gespeicherte Daten, Kandidatenbäume und ursprünglicher
Auswahlindex über den vorhandenen verifizierten Import geprüft sein. Die
[Kurvenregeln](supplemental_assessment.md), der [Strukturvertrag](supplemental_structure.md)
und der [Resttermvertrag](supplemental_remainder.md) bleiben verbindlich.
Das geschlossene Intervall stammt aus den Trainingsdaten; hier
`[0,127/4096]` Sekunden. Grenzen je Formel bleiben unverändert. Ein begrenzter
Durchlauf je Kandidat genügt; keine Wiederholungen bis zu einem positiven Beweis.

Je Front getrennt berichten:

- Originalauswahl, Kurvenklasse und getrennte Familien-/Domain-/Restbefunde;
- A-Kandidat mit nachgewiesener gültiger Originalfamilie vorhanden, aber
  ursprünglich nicht ausgewählt; Kandidatenindex und Hash statt Neuauswahl;
- nachgewiesene Originalfamilie, aber keine Klasse A;
- kein entsprechender Kandidat in dieser gespeicherten Endfront nachgewiesen;
- Definitionslücken, passende Fortsetzung, Zusatzterme und ungeklärte Beweise
  mit ihren Gründen; diese Angaben können die vorherigen Kategorien ergänzen.

„Kein Nachweis“ bedeutet weder mathematische Unmöglichkeit noch das Fehlen
einer passenden Formel im gesamten Suchverlauf. Eine Endfront ist kein
vollständiges Evolutionsprotokoll. Familienzugehörigkeit setzt keine neuen
Parametermatches; `new_parameter_match` bleibt `not_assessed`.

## Vorgehen bei fehlenden Originalen

Fehlende Archive werden namentlich und mit dem erwarteten Hash ausgewiesen.
Vorhandene, vollständig gebundene Serien dürfen separat untersucht werden;
fehlende Serien erhalten keinen negativen Frontbefund. Wenn keine Archive
vorliegen, ist nur ein ausdrücklich als solcher bezeichneter Konsistenzabgleich
der versionierten Berichte und Quellenzuordnungen möglich. Berichtstabellen
werden nicht in Originalbäume zurückübersetzt und nicht als Beweisereingaben
verwendet. Übermittelte Endfrontbefunde bleiben unverifiziert.

Ergebnisse und Quellenlücken werden nach diesem vorab festgelegten Umfang
hier ergänzt; [Ergebnisindex](results_index.md) und
[Archivregel](results_archiving.md) bleiben die Quellen für Ablage und Sicherung.
