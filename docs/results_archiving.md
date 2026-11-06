# Archivierung wissenschaftlicher Versuchsergebnisse

Stand: 06.11.2026. Ergänzung der bestehenden Ergebnis- und
[Reproduzierbarkeitskonventionen](reproducibility_decisions.md), technisch
zu [Leitfadenphase 1](ringdown_recovery_roadmap.md). Der
[Ergebnisindex](results_index.md) ist der zentrale Wegweiser; die einzelnen
Berichte und Originalmetadaten bleiben die Detailquellen.

## Ablage und Unveränderlichkeit

- Vollständige Originalarchive (`.tar.gz`) werden als angehängte Dateien eines
  **privaten GitHub-Releases im privaten Repository** abgelegt. Releases erben
  die Repository-Sichtbarkeit; ein Release in einem öffentlichen Repository
  ist kein privates Archiv. Diese Regel ändert keine Sichtbarkeit.
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
  Laufstatus, wissenschaftlicher Befund und Uploadstatus sind getrennte Angaben.
  Ein vorhandenes Release macht einen abgebrochenen Versuch nicht vollständig.
- Eine zusätzliche vollständige Kopie wird außerhalb von GitHub aufbewahrt,
  beispielsweise auf einem gesicherten lokalen Datenträger. Vor Löschen lokaler
  Arbeitskopien müssen Release-Download und externe Kopie am Archivhash geprüft
  sein. Solange dies nicht bestätigt ist, bleibt die Sicherung offen.
- Actions-Artefakte und CI-Logs haben Aufbewahrungsfristen und sind keine
  alleinige Archivlösung. Für einen Versuch benötigte Nachweise werden mit
  dessen Archiv bzw. einem eindeutig zugeordneten Nachweispaket erhalten.

## Vorhandene Metadaten nutzen

Den gesamten ursprünglichen Ergebnisordner einschließlich vorhandener
Konfiguration, Seeds/Zufallszustände, Softwareversionen, Eltern- und
Workerherkunft, Originalformeln und -ergebnisse, Eingabedaten, Manifeste,
Prüfsummen sowie Fehler-/Abbruchnachweise bewahren. Bei Teilständen fehlende
Abschlussdateien als fehlend belassen; keine erfolgreiche Freigabe nachbauen.
Vorhandene Felder bleiben an ihrem bisherigen Ort. Keine zweite Liste aller
Seeds, Optionen, Kandidaten oder Umgebungsversionen im Index führen.

Der Index hält pro Lauf nur Identität/Fragestellung, tatsächlichen
Ausführungscommit, Laufstatus, Archivname/Downloadlink/SHA-256, Ergebnisbericht
und Bewertungszuordnung fest. Bei bereits gebundenen Serien bleibt der
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

Die zugehörigen Git-Quellen müssen dauerhaft erreichbar bleiben. Für ein
einzelnes Lauf-Release den tatsächlichen Ausführungscommit mit einem stabilen
Tag binden. Bei Sammel-Releases sowie zusätzlichen Werkzeug-/Bewertungscommits
jeden benötigten Stand über vorhandene dauerhafte Refs oder zusätzliche Tags
erhalten. Ein Release-Tag allein bezeichnet nicht automatisch alle ausgeführten
Quellen. Tags nicht verschieben; ursprüngliche Commits nicht durch einen bloß
baumgleichen späteren Merge ersetzen. Vorhandene archivierte Quellen und ihre
Hashbindungen zusätzlich bewahren. Fehlende Stände vor Archivierungsabschluss
wiederbeschaffen und prüfen, nicht aus aktuellem Code rekonstruieren.

## Upload und Abschluss

1. Vorhandenes Originalarchiv und dessen SHA-256 verwenden; etwa mit
   `sha256sum ARCHIV.tar.gz` abgleichen. Vorhandene Archive nicht neu packen,
   nur um sie hochzuladen.
2. **GitHub → Releases → Release erstellen oder bearbeiten → Dateien anhängen**.
   Im privaten Repository ein passend bezeichnetes Release mit dauerhaftem
   Quellbezug wählen und das Originalarchiv hochladen. GitHubs automatisch
   erzeugtes Quellcodearchiv ist kein Versuchsergebnisarchiv.
3. Die angehängte Datei wieder herunterladen und SHA-256 vergleichen. Erst
   danach den echten Asset-Downloadlink im Index ergänzen und den Uploadstatus
   auf geprüft setzen. Ein vorab konstruierter Link ist kein Uploadnachweis.
4. Externe Kopie prüfen und den bisherigen offenen Sicherungsvermerk im Index
   aktualisieren. Bereits enthaltene Metadaten nicht nochmals abschreiben.

Eine beschlossene Richtlinie und ein vollständiger Index bedeuten nicht, dass
Uploads und Sicherungen bereits abgeschlossen sind. Der aktuelle offene Stand
steht im [Ergebnisindex](results_index.md).
