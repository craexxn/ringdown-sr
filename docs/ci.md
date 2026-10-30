# CI nach Änderungsumfang

Der Workflow `Technical checks` startet weiterhin bei Pull Requests nach
`main`, bei Pushes nach `main` und bei manuellem Aufruf. Der bestehende
Jobname `technical-checks` bleibt erhalten. Die Auswahl geschieht innerhalb
dieses Jobs; es gibt keinen Workflow-Pfadfilter, der den Statuscheck ganz
ausfallen lässt.

## Schlanker Dokumentationspfad

Wenn alle geänderten Dateien ausschließlich `README.md`, `AGENTS.md` oder
Markdown-Dateien unter `docs/` sind, läuft nur die Vorbereitung mit Checkout
und die Prüfung der Dokumentation. Die Prüfung verwendet die Python-
Standardbibliothek des Ubuntu-Runners. Sie installiert weder die
Projektumgebung noch Julia und startet keine Formelsuche.

Geprüft werden alle versionierten Markdown-Dateien: UTF-8, abschließender
Zeilenumbruch, unerwünschte Leerzeichen am Zeilenende und abgeschlossene
Codeblöcke sowie lokale Dateiziele von Inline- und Referenzlinks. Zwei
Leerzeichen als Markdown-Zeilenumbruch sind zulässig. Beispiele in
Codeblöcken und Inline-Code werden nicht als Links geprüft. CRLF-Dateien
bleiben zulässig. Dies ist eine begrenzte Prüfung, kein vollständiger
Markdown-Parser. Externe Webadressen und Sprungmarken innerhalb von Dateien
werden nicht abgerufen beziehungsweise validiert.

**Ausnahmen:** `docs/noiseless_control_plan.md` und
`docs/search_representation_plan.md` sind als eingefrorene Kontrollpläne
mit festgelegter Prüfsumme an den jeweiligen Code gebunden.
Änderungen daran erhalten trotz Markdown-Endung die volle CI. Weitere
Laufzeitdokumente müssen ebenso ausdrücklich als Ausnahme erfasst werden.

## Vollständiger technischer Pfad

Jede andere geänderte Datei aktiviert alle bisherigen Prüfungen, insbesondere
Code, Tests, Konfigurationen, Lockdateien, Julia-Dateien und CI-Werkzeuge.
Gemischte Änderungen erhalten ebenfalls die volle CI. Bei manuellen
Aufrufen, unbekannten oder erzwungenen Ereignissen, leerem Diff sowie
fehlenden oder nicht vergleichbaren Commits wird vollständig geprüft.

Die bisherigen Prüfbefehle, Versionspins, Rechte, Thread-/Haswell-Vorgaben
und das Zeitlimit von 30 Minuten bleiben erhalten. Auch das bisherige
Cacheverhalten bleibt erhalten. Ein Fehler im ausgewählten Prüfpfad führt
weiterhin zu einem fehlgeschlagenen Job.

## Ermittlung des Diffs

Der Checkout enthält die vollständige Git-Historie. Pull Requests verwenden
einen Drei-Punkt-Vergleich zwischen Basis und Head; Pushes den Vorher-/Nachher-
Vergleich. Git liefert alle Pfade mit NUL-Trennung, ohne API-Seitenlimit.
Bei Pull Requests zählt der gesamte PR-Diff, nicht nur der letzte Commit.
Ein Dokumentationsnachtrag in einem PR mit Codeänderungen erhält daher
weiterhin die vollständige Prüfung.
Umbenennungen werden ausdrücklich als Löschung und Neuanlage betrachtet,
damit auch ein aus dem Code in die Dokumentation verschobener Pfad die
volle CI aktiviert. Metadaten werden als JSON gelesen; Commitkennungen
werden geprüft und nicht als Shellcode eingesetzt.

Die Implementierung liegt in [check_ci.py](../scripts/check_ci.py), die
Gegenprüfungen in [test_ci.py](../tests/test_ci.py). Lokal kann die
Dokumentationsprüfung aus dem Repository so ausgeführt werden:

```bash
uv run --locked python scripts/check_ci.py docs
```

Kleine zusammengehörige Nachbesserungen werden gebündelt. Ein grüner
Dokumentationspfad bedeutet, dass die beschriebenen Dokuprüfungen bestanden
sind; er behauptet keine erneute Python-/Julia-Integration. KI-basierte
Reviews werden gezielt bei Methodenentscheidungen oder konkretem Bedarf
eingesetzt, Nachreviews nur bei notwendigen Gegenprüfungen.
