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

## Geprüfter Teilstand: versionierte Berichte und Git-Quellen

Der Umfang wurde vor dem Abgleich in `41e730d` committed. Die anschließende
Prüfung auf `4e42ff74eda62a58202aa706fc42a840eea1226c` verwendet den übernommenen
main `16d2f40506e6dae6534f02d76f1cf2f0dfde5dd2`. Die drei Ergebnisberichte und
der Quellenkatalog sind gegenüber main unverändert.

Selbst geprüft wurden alle 78 Einzelauswahlen der drei Berichtstabellen:
Zell-/Seed-/Bedingungs-/Budgetzuordnung gegen den Quellenkatalog, gleiche
Kurvenklassen in allen Stufen und unabhängige Anwendung der Klassengrenzen
auf die gespeicherten rücklesbaren Kennzahlen. Vier Plan-SHA-256 stimmen mit
den gebundenen historischen Git-Dateien überein; alle 50 in den vier Serien
aufgeführten Laufzeitdatei-Verweise sind am jeweiligen Ausführungscommit
vorhanden. Archivhashes in Katalog, Stufe-1-Bericht und Index stimmen überein.
Dies prüft Dokumentkonsistenz und Git-Verfügbarkeit, keine Archivdateibytes,
keinen nativen Replay und keine ursprünglichen vollständigen Quellenmanifeste.

Bestätigt als konsistente Berichtsaussagen:

- 78 Originalauswahlen in 18 getrennten Gruppen; 43 A-Kurven, davon 38 gültige
  Originalmitglieder, zwei passende Fortsetzungen bei Lücken und drei ungeklärte
  Familienbefunde. Keine gepoolte Erfolgsquote.
- Äußere Staffel: bei 500, 2.000 und 5.000 jeweils 5/5 A und gültige
  Originalfamilie. Die ältere Erkennung unterschätzte diese Familienzugehörigkeit.
- 41 Restschranken; weitere 31 Fälle ohne zertifizierte Komponente, fünf mit
  unvollständigem Domainnachweis, ein Ressourcenabbruch. Vollständige formale
  Aufklärung ist keine Voraussetzung für einen begrenzten Suchvergleich.

| Prioritärer Transferfall | Originalindex (nullbasiert) | Klasse | Originalfamilie | Restdiagnose |
| --- | ---: | --- | --- | --- |
| cell-01, Seed 20261210 | 10 | D | ungeklärt | keine zertifizierte Komponente |
| cell-11, Seed 20261211 | 9 | C | ungeklärt | keine zertifizierte Komponente |
| cell-15, Seed 20261212 | 10 | D | ungeklärt | keine zertifizierte Komponente |

Diese Auswahlbefunde beantworten noch nicht, welche anderen Kandidaten in
den drei Fronten vorkommen. Aus dem Tabellenabgleich ergibt sich kein konkreter
technischer Fehler; das ist keine vollständige technische Entlastung.

## Gebundene Originalarchive

Beim Einstieg am 06.11.2026 fehlten im Workspace alle vier Originalarchive.
Anschließend wurden alle vier unveränderten Dateien bereitgestellt und ihre
Dateibytes gegen die folgenden extern gebundenen SHA-256 geprüft:

| Originalarchiv | Erwarteter SHA-256 |
| --- | --- |
| `transfer-manjaro-001.tar.gz` | `e363fe1be629973a460fc6e2188bf680c21b2c5519d331bc7e257968dcaaa139` |
| `outer-ladder-manjaro-001.tar.gz` | `ac7e841b79042e216d6aacae2961ffb8395f298bbcc7ecc11f1092c90b3deb40` |
| `duration-manjaro-004.tar.gz` | `c2d9e330770746030bab9467b682a6b595cac25aa132dbb4decd1c4b03472289` |
| `local-optimizer-manjaro-001.tar.gz` | `1ab8c0aa91436c4b169c6c6efa8053e04c47ef57d07915f36ac476483276866d` |

## Ergebnis der eigenen lesenden Frontprüfung

Am 06.11.2026 wurden alle 78 Fronten mit 738 Kandidaten anhand des eingefrorenen
Umfangs geprüft. Der bestehende Import bindet Archivbytes, vollständige
Manifeste, Daten-/Quellenhashes, Ausführungscommits und originale Auswahlindizes.
Alle 738 Kandidatenidentitäten wurden gegen die gespeicherten Fronten gebunden;
Python-Vorhersagen und baumabhängige Rundungsnachweise stimmen mit den
historischen Nachweisen überein. Alle vier Kurvenfehler je Kandidat sind exakt
gleich den gespeicherten Werten. Struktur-/Domain-/Fortsetzungs- und Restbefunde
verwenden die unveränderten vorhandenen Beweiser. Kein nativer Julia-Replay,
kein Fit und keine Suche; gespeicherte native Nachweise bleiben als solche
gekennzeichnet. Ursprüngliche Auswahl und Bewertungsregeln bleiben erhalten.

| Serie | Fronten | Kandidaten | Auswahl nicht A | Davon mit anderem A-Kandidaten | Fronten mit gültiger Familie, aber Nicht-A-Kandidat |
| --- | ---: | ---: | ---: | ---: | ---: |
| Transfer | 18 | 198 | 11 | 0 | 4 |
| Äußere Staffel | 20 | 164 | 4 | 0 | 1 |
| Suchdauer 004 | 20 | 193 | 8 | 0 | 0 |
| Lokaler Optimierer | 20 | 183 | 12 | 0 | 0 |

Der zuvor nur übermittelte Befund ist damit **eigenständig anhand der Quellen
bestätigt**: Unter 362 Staffel-/Transferkandidaten enthält keine der 15 Fronten
mit ausgewählter Nicht-A-Kurve einen anderen A-Kandidaten. Im gesamten
festgelegten Bestand gilt dies für alle 35 Fronten mit Nicht-A-Auswahl.
Das ist keine Erfolgsquote und keine Aussage über nicht gespeicherte Kandidaten.
Eine Auswahlkorrektur innerhalb dieser Endfronten würde keinen A-Fall gewinnen.

Die drei Transfer-Referenzfronten enthalten 11, 10 und 11 Kandidaten, jeweils
keinen A-Kandidaten und kein nachgewiesenes Originalmitglied. Die Familienstatus
sind 2/9, 3/7 und 6/5 bewiesene Nichtmitglieder/ungeklärte Fälle. In den ersten
beiden Fronten sind alle Originaldomains als vollständig definiert nachgewiesen;
in der dritten sind neun definiert und zwei ungeklärt. Alle Restdiagnosen
dieser drei Fronten bleiben ungeklärt. Fehlender Familiennachweis ist kein
Beweis, dass die Suche niemals eine passende Form erzeugte.

Sieben gültige Familienmitglieder mit Klasse D befinden sich in fünf Fronten,
deren Originalauswahl jeweils bereits A ist: Transfer cell-04 (Indizes 4, 7),
cell-06 (5, 7), cell-08 (4), cell-10 (6) und Staffel cell-09 (6), Indizes nullbasiert.
Zwei davon sind auf dem Trainingsraster nahezu exakt, auf dem Zwischenraster
aber stark abweichend (Transfer 04/7, Staffel 09/6). Dies illustriert die
Trennung zwischen Familie und Kurve; es belegt keinen Fehler der lokalen
Optimierung und keine neue Parameterübereinstimmung.

Die 78 Originalauswahlen behalten ihre bisherigen Klassen und Familienbefunde.
Die beiden A-Auswahlen mit Originaldefinitionslücken und die drei ungeklärten
A-Familienfälle bleiben unverändert. Der bereits bewiesene nicht verschwindende
Rest in duration cell-09 bleibt ein separater Befund; er ersetzt weder die
Familienentscheidung noch die Originalformel.

Ein erster technischer Auditansatz verwendete irrtümlich den allgemeinen
Vorhersagevergleich statt des für diese Archive gebundenen baumabhängigen
Vertrags. Der Ansatz wurde verworfen; keine Toleranz wurde erweitert. Die
korrekte Prüfung verwendet dieselbe Referenzregel wie die historischen Treiber.
Historische Quellhashes werden gegen ihren Ausführungscommit geprüft; die
heutige Quellenbindung wird separat aufgezeichnet. Ein geänderter Hash von
`pilot.py` durch spätere Bewertungsanbindung ersetzt keinen historischen Hash.
Beide unvollständigen Auditversuche bleiben gesperrt und sind keine Nachweise.

Der erfolgreiche Export `endfront-diagnostic-003` ist getrennt von den
Originalarchiven abgelegt; sein vollständiges Manifest wurde unabhängig
nachgehasht, alle vier Eingaben bei Veröffentlichung erneut unverändert geprüft.
Softwarestand: `4e42ff74eda62a58202aa706fc42a840eea1226c`, baumgleicher fachlicher
Code zu main `16d2f40`; zusätzlich nur der vorab eingefrorene Diagnoseumfang.
Der Export enthält das verwendete Diagnoseprogramm, Scope, jeden Kandidaten
mit Beweisspur und je Front getrennte Kategorien. Paketzuordnung und
Sicherungsstand stehen im [Ergebnisindex](results_index.md).

| Erfolgreiches Diagnoseartefakt | SHA-256 |
| --- | --- |
| `assessment_checksums.json` | `aac136903f407d518099407f6477cc6d3a155add443eb4ec4e5083bbba4f141f` |
| `assessment_report.json` | `0a708957857be4baa7ace40d8fe145bce2e93e873e875d3bf14b94a8e167e04c` |
| `endfront_records.json` | `cd21d0e82657578173e67ae3af1678a4fd3cd99a029e4341a90b974232632daa` |

Das Reviewpaket enthält zusätzlich die vier unveränderten Originalarchive.
Es ist eine lokale Arbeitskopie, keine bestätigte zweite Sicherung.

## Konsequenz für den nächsten abgegrenzten Vergleich

Im geprüften Umfang wurde kein neuer technischer Fehler als vorrangiger Engpass
gefunden. Es fehlen A-Kandidaten in den erfolglosen gespeicherten Fronten;
deshalb ist der vorgegebene Vergleich längerer Einzelsuchen mit globalen
Neustarts begründet. Er soll deren Nutzen erst prüfen. Die Untersuchung belegt
weder einen Neustartvorteil noch eine allgemeine Erfolgswahrscheinlichkeit.
Die übrigen Beweisgrenzen werden beibehalten; keine offene Erkennerentwicklung.
