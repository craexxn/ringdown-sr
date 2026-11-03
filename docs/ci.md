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

**Ausnahmen:** `docs/noiseless_control_plan.md`,
`docs/search_representation_plan.md`, `docs/constant_diagnostic_plan.md`,
`docs/free_optimizer_budget_plan.md`, `docs/search_trajectory_plan.md`,
`docs/search_trajectory_replay_policy.md`, `docs/trigonometric_grammar_plan.md`
`docs/search_duration_plan.md` und `docs/search_duration_verification_plan.md`
sind als eingefrorene Kontrollpläne
mit festgelegter Prüfsumme an den jeweiligen Code gebunden.
Änderungen daran erhalten trotz Markdown-Endung die volle CI. Weitere
Laufzeitdokumente müssen ebenso ausdrücklich als Ausnahme erfasst werden.

Der vollständige Pfad prüft zusätzlich die feste Konstantendiagnose mit
`scripts/check_constant_diagnostic.py`: zehn reine Referenzkontrollen,
unverändertes Optimiererverhalten mit/ohne Beobachtung an einem eigenen
Achtpunkt-Signal und zwei frische Worker samt Export und Verifikation.
Die beschlossene wissenschaftliche Serie mit 48 Aufrufen ist kein CI-Test.

Der freie Budgetvergleich ergänzt
`scripts/check_free_optimizer_integration.py`: sechs echte Optionsobjekte ohne
Fit, feste 250-/4346-/33018-Hz-Bäume unter beiden Budgets, Einheiten- und
Seed-/Budgetgegenfälle sowie drei frische 20–100–20-Worker mit je zwei
Suchiterationen auf einem eigenen Achtpunkt-Signal `y=1+t`. Der wiederholte
20er-Lauf muss dieselbe ursprüngliche Front liefern. Haswell/Threadlimit 1
gilt nur für diesen Kontrollschritt. Keine der sechs wissenschaftlichen
Suchzellen wird in der CI ausgeführt.

## Vollständiger technischer Pfad

Der Suchbudgetvergleich ergänzt `scripts/check_search_duration_integration.py`:
zehn native Optionsobjekte, 20 Pythonprofile und unveränderte feste Referenzen,
danach fünf frische K2–A2–K3–A3–K2-Worker am separaten Achtpunkt-Signal `y=1+t`.
Die tatsächlich durchgereichten Suchbudgets werden geprüft und beide K2-Fronten
müssen übereinstimmen. Die 20 wissenschaftlichen 200-/2.000-Zellen laufen
ausschließlich später auf Manjaro. Python-Gegenfälle prüfen insbesondere
Budgetbindung, vollständige Paare und gesperrte Teilserienauswertung.
Format 2 ergänzt `scripts/check_duration_replay.py`: zwei fest vorliegende
CSV-Bäume nativ auswerten, Verluste/Vorhersagen vergleichen, neue Verlust- und
Strukturdiagnose prüfen; keine Suche oder Optimierung. Python-Gegenfälle
prüfen die rationale Reduktionsschranke, Unter-/Überlauf, verlorene oder
veränderte Nachweise, Sinus-/Quotientenformen und exakte gemischte Phasen.

Der Grammatikvergleich ergänzt `scripts/check_trigonometric_grammar_integration.py`:
sechs native Optionsobjekte, feste Ringdown-/Aliasreferenzen und 28 explizite
Syntaxgegenfälle unter beiden Profilen, anschließend drei frische K–A–K-Worker
mit zwei Suchiterationen am Achtpunkt-Signal `y=1+t`. Alle vier direkten und
entfernten trigonometrischen Paare werden geprüft; die ursprünglichen
Kontrollfronten müssen übereinstimmen. Jeder exportierte A-Kandidat muss die
Regel erfüllen. Haswell/Threadlimit 1 gilt nur für diesen Kontrollpfad.
Die sechs wissenschaftlichen Zellen werden ausschließlich später auf Manjaro
ausgeführt. Fehler-, Manipulations- und Veröffentlichungstests gehören zum
Python-Testlauf; die bisherigen technischen CI-Schritte bleiben erhalten.

Die begrenzte Suchbeobachtung ergänzt
`scripts/check_search_trajectory_integration.py`: echte Optionsobjekte und
PySR-Plugin-Durchleitung ohne Fit, technische Aufnahmekontrollen einschließlich
RNG-/Zustandsschutz und drei frische aus/an/aus-Worker mit jeweils zwei
Suchiterationen auf einem eigenen linearen Achtpunkt-Signal. Die Originalfronten,
Auswahlen und Fit-Callbackzahlen müssen übereinstimmen; der beobachtete Lauf
muss alle vier erwarteten Populationsrückgaben exportieren. Die sechs
wissenschaftlichen 200-Iterations-Zellen bleiben außerhalb der CI.
Haswell und Threadlimit 1 gelten nur für diesen technischen Kontrollschritt.

Die Verifikationsergänzung prüft außerdem getrennte native Trainingsreplays
der beobachteten Bäume und deren Dateibindungen, numerische Konsistenz und
Vollständigkeit. Die fünf geprüften Manjaro-Gegenfälle sind als feste
Testdaten enthalten; gespeicherte Vorhersagebits dienen plattformneutralen
Vergleichen. Sie verlangen keine neue wissenschaftliche Suche und keine
bitweise Gleichheit großer trigonometrischer Ausdrücke zwischen Rechnern.

Jede andere geänderte Datei aktiviert alle bisherigen Prüfungen, insbesondere
Code, Tests, Konfigurationen, Lockdateien, Julia-Dateien und CI-Werkzeuge.
Gemischte Änderungen erhalten ebenfalls die volle CI. Bei manuellen
Aufrufen, unbekannten oder erzwungenen Ereignissen, leerem Diff sowie
fehlenden oder nicht vergleichbaren Commits wird vollständig geprüft.

Die bisherigen Prüfbefehle, Versionspins, Rechte, Thread-/Haswell-Vorgaben
und das Cacheverhalten bleiben erhalten. Der technische CI-Job erhält
45 Minuten Gesamtzeit. Lauf
[41425713993](https://github.com/craexxn/ringdown-sr/actions/runs/41425713993)
am Head `2d9b028` wurde bei bisher 30 Minuten Joblimit nach rund 31 Minuten
in der zweiten abschließenden Haswell-Wiederholung abgebrochen; alle vorherigen
Schritte waren erfolgreich. Die erweiterte native Prüffolge erhält damit
Laufzeitreserve, ohne Prüfungen auszulassen oder deren Budgets zu verändern.
Die Grenzen der wissenschaftlichen Serien und ihrer Worker bleiben unverändert.
Ein Fehler im ausgewählten Prüfpfad führt
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

Die vollständige CI führt außerdem
`check_representation_integration.py` mit dem begrenzten Haswell-Profil aus.
Zuerst prüft sie neun echte Optionsobjekte ohne Callback/Fit sowie neun feste
Koordinaten-/Aliasreferenzen ohne Suche. Anschließend prüft sie drei frische
Profilworker mit jeweils zwei Iterationen am technischen linearen Signal
`y=1+t`. Dieses gesonderte technische Budget ändert keine Vorgabe der
wissenschaftlichen Neun-Zellen-Serie und liefert keinen Rekonstruktionsbefund.
Die Fehler-Injektionstests des Treibers gehören zum regulären pytest-Lauf.
