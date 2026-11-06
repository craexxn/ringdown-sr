# Seed-/Treiber-Kreuzvergleich auf Manjaro: Ergebnis 001

Prüfstand: 06.11.2026. Das nun vorliegende Originalarchiv bestätigt den zuvor
nur übermittelten Befund: Beide Kreuzläufe reproduzieren die vollständigen
historischen Fronten und Suchmerkmale. Die ursprünglichen Auswahlen entsprechen
Klasse A beziehungsweise D. Zwei gezielt gewählte Entwicklungsfälle liefern
keine allgemeine Erfolgswahrscheinlichkeit.

## Fragestellung und vorab festgelegter Vergleich

Die äußere Staffel und der Transfercheck verwendeten unterschiedliche Seeds.
Der [eingefrorene Plan](seed_driver_crosscheck_plan.md) untersucht in genau zwei
Gegenrichtungen, ob das gespeicherte Ergebnis bei gleichem Seed dem historischen
Treiber folgt. Plancommit `be6fc1bd2339df5b429684dfce8e992073d88506`, SHA-256
`e6e2df830dd2e4254d60bd73a5b9e34678377c9bc1e6a2f81830592e4f85b15e`.
Profil 500/300/5, Datenrollen, Grammatik, ursprüngliche Auswahl und Kriterien
bleiben unverändert; vollständige Vorgaben und Grenzen stehen im Plan.

## Tatsächliche Ausführung und Originalarchiv

- Lauf-ID und Dateiname bestätigt: `seed-driver-crosscheck-manjaro-001`,
  `seed-driver-crosscheck-manjaro-001.tar.gz`, 10.913.312 Bytes.
- Selbst berechneter Archiv-SHA-256:
  `c38f857ccee231ae647bbbcf5186cce275b494c6c54a1092773e7d7ccce11926`.
- Gespeicherter sauberer Adapter-/Orchestrierungsstand:
  [`8096ddb8bb6fd065eb1079c7902a2016334a6e6b`](https://github.com/craexxn/ringdown-sr/commit/8096ddb8bb6fd065eb1079c7902a2016334a6e6b),
  der PR67-Merge; separat gebundene historische Worker `bc4025d` (Transfer)
  und `5215c5e` (Staffel). Alle drei Commits sind Vorfahren des geprüften main.
- Aufgezeichneter Beginn: 05.11.2026, 09:37:51,889832 UTC; Abschluss:
  09:44:30,338140 UTC. Status `completed`,
  `outcome=both_crossovers_reproduced`; beide Zellen vollständig, kein Ausfall.
- Laufzeit-/Bibliotheksmetadaten vor und nach den Suchen entsprechen den
  jeweiligen historischen Referenzen nach der unveränderten Vergleichsregel.
  Haswell und Poollimits 1 sind belegt. Dies ist keine vollständige CPU-/JIT-/
  GC-Hardwareidentität; effektive Optionen und Versionen bleiben im Archiv.

## Selbst ausgeführte lesende Prüfung

1. Archivstruktur, **1.142 Dateien und alle 1.141 Abschlussmanifest-Einträge**
   geprüft; keine Sperr-/temporäre Abschlussdatei. Die eingebetteten Staffel-
   und Transferarchive haben die bereits gebundenen Originalhashes; ihre
   entpackten Referenzdateien stimmen vollständig mit den eingebetteten Bytes
   überein. Kein erneuter Audit sämtlicher 38 historischer Suchzellen.
2. **280 verschiedene Commit-/Quelldateibindungen** einschließlich Plan,
   Orchestrierung, Vorbereitung und beider historischer Worker gegen Git
   geprüft. Requests, Eingabebits und Laufzeitdateien stimmen mit den gebundenen
   Manifesteinträgen überein. Eltern-/Workerherkunft und Adapterbelege wurden
   in den bestehenden Prüfpfaden abgeglichen.
3. Beide frischen Kreuzzellen mit den jeweiligen unveränderten historischen
   Python-Elternverifikatoren erneut geprüft: alle **18 Kandidaten**, native
   Vorhersage-/Verlustnachweise, Python-/MPFR-Nachrechnung, Optionen, Seeds,
   Callbackzähler und Auswahl. Beide vollständigen Diagnosen stimmen mit den
   gespeicherten Diagnosen überein. Ganze Frontsignaturen einschließlich
   Reihenfolge, Bäumen, Konstantenbits, Verlustbits und Vorhersage-/Residual-
   Fingerprints stimmen mit den archivgebundenen Referenzen überein.
4. Vergleiche selbst neu gebildet; Originalbericht und Zusammenfassung
   bytegleich regeneriert. Originalarchiv und entpackte Prüfkopie unverändert.
   Keine neue Suche, kein Fit, kein nativer Julia-Replay und keine Ausführung
   von Archivprogrammen oder serialisierten Suchzuständen.

Der erste lokale Prüfansatz unter dem Orchestrierungscheckout wurde von der
historischen Manifestprüfung zurückgewiesen: Dessen Quellenmenge enthält bereits
das zusätzliche Kreuzvergleichsmodul. Die erfolgreiche Prüfung verwendet deshalb
für jede Zelle den tatsächlich gebundenen historischen Workercheckout. Keine
Prüfregel wurde gelockert; der unvollständige Prüfansatz ist kein Suchausfall.

Getrennter lesender Nachweis: `seed-driver-crosscheck-audit-002.tar.gz`, SHA-256
`ba1339952222b650c9bbdfccafcc8a559f3dbe09b818d8bfd1ab9bdd79844c05`.
Enthalten sind Prüfzusammenfassung, Prüfprogramme samt Hashmanifest und
regenerierter Bericht. Dieses Paket ersetzt das Originalarchiv nicht;
dauerhafte Ablage und unabhängige Zweitkopie sind noch unbestätigt.

## Ergebnisse und Gegenbefund

| Seed / frischer Worker | Kandidaten / ursprünglicher Index (ab 0) | Kurve und ursprüngliche Marker | Schlechtester relativer RMS / Maximalfehler beider Raster |
| --- | --- | --- | --- |
| 20261201 / Transfer | 7 / 6, vollständig gleich zur Staffelreferenz | A; `within_tolerance`, Struktur `recognized`, Parameter `matched` | 4,26417e-12 / 2,25475e-12 |
| 20261210 / Staffel | 11 / 10, vollständig gleich zur Transferreferenz | D; `outside_tolerance`, Struktur `not_supported`, Parameter `not_assessed` | 0,0730325 / 0,0684397 |

Auch effektive Pythonparameter, native Optionen und Fit-Callbackzahlen stimmen
je Gegenrichtung überein. Aus den nachgerechneten Kurvenfehlern folgt unter den
bestehenden A–D-Grenzen: Die sieben Kandidaten des ersten Falls sind D/D/D/A/A/A/A;
alle elf des zweiten Falls sind D. Dies ist eine getrennte lesende Einordnung,
keine Änderung der historischen Marker oder ursprünglichen Auswahl.
Die Klasse-A-Kandidaten einer Front sind keine unabhängigen Sucherfolge.

Der Kreuzversuch gehört nicht zu den 78 Originalauswahlen der R1–R3-Berichte.
Das bestätigte historische Parameterurteil der ersten Auswahl ist keine neue
Parameterbewertung durch einen Familiennachweis. Die Gesamtkennzeichnung
`physical_identification=not_assessed` und der regelmäßige Rasterblindfleck
bleiben erhalten.

## Aufgezeichneter Aufwand

| Seed | Neue Workerzeit (s) | Fit einschließlich JIT/Python-Export (s) | Fit-Callbacks |
| --- | ---: | ---: | ---: |
| 20261201 | 157,478298 | 140,088825 | 12.407.818 |
| 20261210 | 187,957618 | 171,677995 | 17.203.537 |

Gespeicherte Gesamtzeit des Kreuzvergleichs: **398,460268 Sekunden** (rund
6 min 38 s), einschließlich Vorbereitung, Referenzprüfung und Aufräumen bis zur
abschließenden Messstelle. Der Wert ist keine reine Evolutionszeit und enthält
nicht die danach ausgeführten letzten Veröffentlichungsoperationen. Alte
Referenzkosten bleiben separat im Originalbericht. Diese zwei Fälle tragen
keinen allgemeinen Geschwindigkeitsvergleich der Treiber.

## Konsequenz und verbleibende Grenze

Für diese zwei Seeds am rauschfreien Ankersignal unter dem gemeinsamen
Einzelzelladapter folgt das gespeicherte Ergebnis dem Seed. Das stützt die
Untersuchung der Suchrobustheit gemäß [Leitfaden](ringdown_recovery_roadmap.md).
Es beweist weder identische Evolutionsverläufe noch allgemeine
Implementierungskorrektheit, Robustheit oder einen Vorteil globaler Neustarts.
Ein erneuter wissenschaftlicher Kreuzlauf ist dadurch nicht beauftragt.

Die Quellenlücke des früheren übermittelten Befunds ist im beschriebenen Umfang
geschlossen. Originalmetadaten und Prüfsummen belegen gespeicherte Konsistenz,
keine unabhängige Beobachtung der damaligen Geräteausführung. Ablage und Sicherung
stehen weiterhin offen im [Ergebnisindex](results_index.md); historische
Originalbewertungen und die spätere [Endfrontdiagnose](endfront_diagnostic_001.md)
bleiben eigenständige Belege.
