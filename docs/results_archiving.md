# Archivierung wissenschaftlicher Versuchsergebnisse

Stand: 06.11.2026. Ergänzung der bestehenden Ergebnis- und
[Reproduzierbarkeitskonventionen](reproducibility_decisions.md), technisch
zu [Leitfadenphase 1](ringdown_recovery_roadmap.md). Der
[Ergebnisindex](results_index.md) ist der zentrale Wegweiser; die einzelnen
Berichte und Originalmetadaten bleiben die Detailquellen. Die vereinfachte
Ablage wurde am 06.11.2026 beschlossen: vorhandene Archivordner und Backups
nutzen; GitHub-Releases sind eine optionale zusätzliche Ablage.

## Ablage und Unveränderlichkeit

- Vollständige Originalarchive (`.tar.gz`) in einem gemeinsamen Archivordner
  aufbewahren und eine **zweite gesicherte Kopie auf einem unabhängigen
  Datenträger oder im bestehenden Backup** erhalten. Ein weiterer Ordner auf
  derselben ungesicherten Platte genügt dafür nicht. Die tatsächlichen
  Ablageorte werden einmal im [Ergebnisindex](results_index.md#archivablage)
  bezeichnet; persönliche Rechnerpfade sind dafür nicht erforderlich.
- GitHub-Releases können zusätzlich genutzt werden; Uploads, Downloadlinks
  und eigene Releases pro Versuch sind keine Voraussetzung für eine
  abgeschlossene Archivierung. Bestehende Archive unverändert behalten, weil
  die Bewertungsimporte ihre konkreten SHA-256-Werte binden.
- Große Ergebnisarchive gehören nicht regulär in die Git-Historie.
  `results/` bleibt gemäß [.gitignore](../.gitignore) die lokale, nicht
  versionierte Ausgabeablage. Ein lokaler Ordner ist keine bestätigte Sicherung.
- Jedes Archiv hat einen eindeutigen Namen und den SHA-256 seiner tatsächlichen
  Dateibytes. Vorhandene Lauf-IDs und Archivnamen weiterverwenden. Bei mehreren
  Geräten gleichnamige Läufe im Index mit Gerätepräfix unterscheiden, ohne die
  ursprünglichen Metadaten umzubenennen.
- Originalarchive werden weder überschrieben noch unter gleichem Namen ersetzt.
  Wiederholungen erhalten eine neue Lauf-ID. Korrekturen, neu gepackte Archive,
  Audits und nachträgliche Bewertungen erhalten unterscheidbare Einträge oder
  Artefaktnamen mit Verweis auf die Ausgangslauf-ID und deren Archivhash.
  Frühere Fassungen und Befunde bleiben verfügbar.
- Auch erfolglose und abgebrochene Versuche samt Teilständen bleiben im Index.
  Laufstatus, wissenschaftlicher Befund und Sicherungsstand sind getrennte
  Angaben. Ein technischer Abbruch bleibt auch nach vollständiger Sicherung
  ein Abbruch.
- Archivkopie und zweite Kopie müssen am dokumentierten SHA-256 geprüft sein,
  bevor entbehrliche Arbeitskopien gelöscht werden. Bei einem bestehenden
  Backup die Datei aus der Sicherung lesend wiederherstellen und prüfen.
  Solange die Ablage und beide Kopien nicht bestätigt sind, bleibt die
  Sicherung offen. Ein bloßer Ablagehinweis oder geplanter Backupauftrag
  belegt noch keine vorhandene Kopie.
- Actions-Artefakte und CI-Logs haben Aufbewahrungsfristen und sind keine
  alleinige Archivlösung. Für einen Versuch benötigte Nachweise werden mit
  dessen Archiv bzw. einem eindeutig zugeordneten Nachweispaket erhalten.
  Eine dauerhafte Archivierung jedes gewöhnlichen CI-Laufs ist nicht verlangt.

## Vorhandene Metadaten nutzen

Den gesamten ursprünglichen Ergebnisordner einschließlich vorhandener
Konfiguration, Seeds/Zufallszustände, Softwareversionen, Eltern- und
Workerherkunft, Originalformeln und -ergebnisse, Eingabedaten, Manifeste,
Prüfsummen sowie Fehler-/Abbruchnachweise bewahren. Bei Teilständen fehlende
Abschlussdateien als fehlend belassen; keine erfolgreiche Freigabe nachbauen.
Vorhandene Felder bleiben an ihrem bisherigen Ort. Keine zweite Liste aller
Seeds, Optionen, Kandidaten oder Umgebungsversionen im Index führen.

Ein besprochener Wiederholungsaufruf wird erst mit Ausführungsbeleg als gestartet
geführt. Bei einem Abbruch Ursache und belegbaren Zellstand im Ergebnisbericht
festhalten, gemessene verbrauchte Kosten erhalten und fehlende Messungen als
unbekannt kennzeichnen. Eine vollständige Wiederholung erhält eine eigene ID;
Teilstände werden weder hineinkopiert noch als zusätzliche unabhängige Erfolge
gezählt. Technische Vorläufe bleiben von wissenschaftlichen Serien getrennt.

Ist nur der unveränderte Ergebnisordner erhalten, zuerst seine vorhandenen
Manifeste und Herkunft prüfen. Ein daraus neu erzeugtes Paket erhält eigenen
Namen, Packdatum und SHA-256 mit Verweis auf den ursprünglichen Lauf. Es ist
keine Rekonstruktion der verlorenen Originalarchivbytes oder ihres Hashes.

Der Index hält pro Lauf nur Identität/Fragestellung, tatsächlichen
Ausführungscommit, Laufstatus, Archivname/SHA-256, Ablagehinweis,
Sicherungsstand, Ergebnisbericht und Bewertungszuordnung fest. Ein optionaler
Downloadlink ergänzt den Ablagehinweis. Bei bereits gebundenen Serien bleibt der
[bestehende Quellenkatalog](../data/supplemental_series.json) die maschinenlesbare
Quelle; der Index ist sein lesender Wegweiser, kein zweites Laufregister im Code.
Fehlendes ausdrücklich als fehlend oder ungeprüft kennzeichnen. Ein bloß
vorgegebener Commit ist kein belegter Ausführungscommit.

Ausführung, Dokumentation und Neubewertung haben getrennte Commitrollen:

- Ausführung: aus den gespeicherten Herkunftsdaten; bei externen Treibern
  Prüfprojekt und Werkzeugcommit getrennt nennen. Ein schmutziger Stand wird
  samt bereits vorhandenen Änderungsnachweisen erhalten und nicht als sauber
  ausgegeben.
- Dokumentation: durch die Git-Historie des verlinkten Berichts nachvollziehbar;
  sie ersetzt weder Ausführungs- noch Bewertungscommit. Keine manuelle zweite
  Chronik der Berichtsänderungen pflegen.
- Neubewertung: eigene Ausgabe, Bewertungsfassung und Bewertungscommit; Verweis
  auf unveränderte Originalarchive. Sie ersetzt keine Originalauswahl und keine
  zum Ausführungszeitpunkt festgelegte Bewertung.

Die zugehörigen Git-Quellen müssen dauerhaft erreichbar bleiben. Alle benötigten
Ausführungs-, Werkzeug- und Bewertungscommits über vorhandene dauerhafte Refs
oder zusätzliche stabile Tags erhalten; dafür ist kein Release erforderlich.
Tags nicht verschieben; ursprüngliche Commits nicht durch einen bloß baumgleichen
späteren Merge ersetzen. Vorhandene archivierte Quellen und ihre Hashbindungen
zusätzlich bewahren. Fehlende Stände vor Archivierungsabschluss wiederbeschaffen
und prüfen, nicht aus aktuellem Code rekonstruieren.

## Ablage und Abschluss

1. Vorhandenes Originalarchiv und dessen SHA-256 verwenden; etwa mit
   `sha256sum ARCHIV.tar.gz` abgleichen. Vorhandene Archive nicht neu packen.
2. Die unveränderte Datei im gemeinsamen Archivordner und auf dem zweiten
   Sicherungsziel ablegen. Beide Kopien am selben SHA-256 prüfen.
3. Gemeinsame Ablagehinweise im Index ergänzen und den Sicherungsstand der
   tatsächlich geprüften Einträge bestätigen. Vorhandene Metadaten nicht
   nochmals abschreiben. Ein fehlender Downloadlink ist dabei kein offener
   Pflichtschritt.

Neue Archive werden nach einem Versuch oder einer Neubewertung gesichert;
es ist kein zusätzlicher Kalenderturnus oder neues Sicherungssystem vorgeschrieben.

## Optionale GitHub-Ablage

Über **GitHub → Releases → Release erstellen oder bearbeiten → Dateien anhängen**
können Archive zusätzlich bereitgestellt werden. Ein Sammel-Release darf weitere
eindeutig benannte Dateien aufnehmen; bestehende Dateien und Tags bleiben
unverändert. Releases erben die Repository-Sichtbarkeit: Nach einer Umstellung
auf öffentlich sind auch vorhandene veröffentlichte Releases und ihre Anhänge
öffentlich zugänglich. Eine private Zusatzablage benötigt dann ein separates
privates Ziel oder das bestehende Backup. Vor einer öffentlichen Bereitstellung
den konkreten Archivinhalt einschließlich Metadaten prüfen; keine automatischen
Uploads aus der Sichtbarkeitsänderung ableiten. Die
[Veröffentlichungsprüfung](publication_review.md) hält den geprüften Umfang fest.

Nach einem Upload den Rückdownload gegen SHA-256 prüfen und erst dann den echten
Downloadlink samt geprüftem Uploadstatus ergänzen. Ein Release-Tag bezeichnet
nicht automatisch die Ausführungscommits seiner Archive. GitHubs automatisch
erzeugtes Quellcodearchiv ersetzt kein Versuchsergebnisarchiv. Die zwei oben
beschriebenen Archivkopien bleiben unabhängig vom optionalen Upload erhalten.

Eine beschlossene Richtlinie und ein vollständiger Index bedeuten nicht, dass
die Sicherungen bereits abgeschlossen sind. Der aktuelle offene Stand
steht im [Ergebnisindex](results_index.md).
