# CI nach Änderungsumfang

Der Workflow `Technical checks` startet bei Pull Requests einschließlich
gestapelter Entwicklungsbranches, bei Pushes nach `main` und bei manuellem Aufruf. Der bestehende
Jobname `technical-checks` bleibt als verbindlicher Abschluss erhalten.
`prepare` ermittelt den Umfang und führt Dokumentations-, Ruff-, Format- und
Python-Prüfungen aus. Erst nach dessen Erfolg starten drei native Jobs auf
getrennten Ubuntu-24.04-Runnern. Es gibt keinen Workflow-Pfadfilter, der den
Statuscheck ganz ausfallen lässt.

## Parallele technische Prüfungen

| Job | Prüfungen |
| --- | --- |
| `prepare` | Umfang, Dokumentation, bei vollem Umfang historische Referenzen, uv/Sync, Ruff, Format und pytest |
| `native-a` | Julia-Starts, Verlustkern, Schema-3-Pilot, feste Konstantendiagnose, Verlust-/Vorhersagereplays, Suchbudget und sämtliche fünf Pilot-Folgeprüfungen |
| `native-b` | Suchbeobachtung, freie PySR-Suche, Repräsentation, freier Optimierer und Grammatik |
| `native-c` | lokaler Optimierer einschließlich nativem Guard, äußere Staffel, Transfer und historische Kreuzprüfung |
| `technical-checks` | verbindliche Vollständigkeitsprüfung aller vier Vorgänger |

Alle 30 bisherigen Schritte bleiben enthalten. Checkout läuft in fünf Jobs,
uv/Sync in vier Jobs und der Python-/Julia-Umgebungscheck auf jedem nativen
Runner. Die übrigen Fachprüfungen laufen jeweils genau einmal, innerhalb
jedes Blocks in ihrer bisherigen Reihenfolge. Der ursprüngliche Befehlsstand
von #67 dc7f4a2 ist als
[Prüfinventar](../tests/fixtures/ci_steps_before_parallel.json) gebunden;
Tests vergleichen Befehle einschließlich Argumenten, Launcher, env-Präfixen
und Fehlerausgabe. Es gibt keine Matrix, neuen Caches oder Abhängigkeiten.
Haswell-/Threadvorgaben bleiben ausschließlich an den bisherigen Befehlen.

Der Schema-3-Pilot erzeugt seine Daten frisch in `native-a`. Beide festen
Numerikproben, Parameterexport, Diagnoseexport/-vergleich und die beiden
abschließenden freien Haswell-Suchen lesen diese Daten im selben Job.
Die Haswell-Suchwiederholung liest den ursprünglichen Pilotarm, nicht den
Output der Numerikprobe. Zwischen Jobs werden keine Ergebnisdateien übertragen.
Aus/an/aus, 20–100–20, K–A–K und die übrigen Wiederholungsfolgen bleiben
ungeteilte Aufrufe mit frischen Unterprozessen. Wissenschaftliche Suchbudgets
und Originalarchive gehören nicht zu dieser CI-Umstellung.

Stufe 1 der Zusatzbewertung erweitert den bestehenden Schema-3-Prüfaufruf um
die prospektive Anbindung: Beide vorhandenen Kontrollläufe speichern ihre
Bewertungsgrundlage vor der Suche und veröffentlichen anschließend die drei
Originalauswahlen getrennt. Eine unabhängige Norm-/Klassenkontrolle prüft die
Zusatzdateien. Es kommen keine zusätzlichen Suchläufe, Jobs oder Budgets hinzu.

Jeder Job checkt ausdrücklich `${{ github.sha }}` aus und protokolliert Commit
und Dateibaum. Bei PR-Ereignissen ist dies der getestete Mergecommit. Volle
Historie und `persist-credentials: false` bleiben erhalten. Vor pytest und
auf jedem nativen Runner werden zusätzlich die dauerhaften PR-Head-Refs
55/61/63/65/67 abgerufen. Der lesende Actions-Token wird nur dem einzelnen
Fetch über dessen Prozessumgebung übergeben; er wird weder protokolliert
noch in Gitkonfiguration oder historische Worktrees geschrieben.
[Historische Bindungen](../scripts/ci_historical_refs.json) prüfen acht
Commits, ihre Abstammung und feste Dateihashes. Fehlende Refs/Commits oder
abweichende Dateien stoppen vor den Tests; HEAD muss unverändert bleiben.
Die bisherigen inhaltlichen Bindungsprüfungen der Programme bleiben bestehen.

`technical-checks` nennt alle vier Vorgänger in `needs` und läuft mit
`always()` auch nach Fehlern. Eine Standardbibliotheksprüfung liest die
Ergebnisse als JSON aus einer Umgebungsvariablen; es wird kein Ergebnis als
Shellcode ausgewertet. Nur diese beiden Fälle bestehen:

- `prepare=success`, exakt `full=true`, alle drei nativen Jobs `success`.
- `prepare=success`, exakt `full=false`, alle drei nativen Jobs `skipped`.

Fehler, Abbrüche, fehlende Jobs/Ergebnisse, ungültige Scope-Ausgabe und
unerwartete Skips sperren den Abschluss. Auch drei erfolgreiche native Jobs
ersetzen keine gültige Scope-Ausgabe. Alle vollen Bedingungen lauten
`full != 'false'`; fehlender Scope wählt niemals den Prosaweg. Ein normal
erkannter unklarer Diff liefert dagegen regulär `full=true`. Ein tatsächlicher
Scope-Prozessfehler lässt `prepare` scheitern. Workflowabbruch wird zusätzlich
über `cancelled()` geprüft. Die bisherige Cancellation-Gruppe und
`cancel-in-progress: true` bleiben erhalten; kein Pflichtschritt nutzt
`continue-on-error`.

Die bereitgestellte Zeitbasis
[41988145093](https://github.com/craexxn/ringdown-sr/actions/runs/41988145093)
betrug 39:48 Jobzeit beziehungsweise 41:23 von Run-Anlage bis Jobabschluss.
Die Vorbereitung schätzt etwa 18–20 Minuten für die Aufteilung, ohne gesicherte
Queue-/JIT-Kosten; dies ist keine Zusage. Drei frische Julia-Umgebungen erhöhen
voraussichtlich die summierte Runnerzeit. Der Implementierungs-PR hält die
tatsächlich gemessenen Jobzeiten, Schedulinggrenzen, Summe und geprüften
Commit/Dateibaum fest. Einzelmessungen belegen keine stabile Beschleunigung;
Jobzeiten sind keine Abrechnungsminuten.

## Schlanker Dokumentationspfad

Wenn alle geänderten Dateien ausschließlich `README.md`, `AGENTS.md` oder
Markdown-Dateien unter `docs/` sind, läuft nur die Vorbereitung mit Checkout
und die Prüfung der Dokumentation sowie der Abschlussjob mit den drei
erwarteten Skips. Zusätzliche historische Fetches entfallen. Die Prüfung verwendet die Python-
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
`docs/search_duration_plan.md`, `docs/search_duration_verification_plan.md`
`docs/search_duration_table_loss_note.md`
`docs/search_duration_simplification_plan.md`
`docs/search_duration_prediction_plan.md`, `docs/local_optimizer_plan.md`
`docs/outer_search_ladder_plan.md`, `docs/transfer_check_plan.md` und
`docs/seed_driver_crosscheck_plan.md`
sind als eingefrorene Kontrollpläne
mit festgelegter Prüfsumme an den jeweiligen Code gebunden.
Änderungen daran erhalten trotz Markdown-Endung die volle CI. Weitere
Laufzeitdokumente müssen ebenso ausdrücklich als Ausnahme erfasst werden.

Auch `docs/supplemental_assessment.md` erhält die volle CI: Der lesende
Bewertungsexport bindet diesen Versionsvertrag an seinen Softwarestand.
Die bestehenden Prüfjobs und wissenschaftlichen Budgets bleiben erhalten.

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
Seit Format 2 prüft `scripts/check_duration_replay.py` zwei fest vorliegende
CSV-Bäume nativ auswerten, Verluste/Vorhersagen vergleichen, neue Verlust- und
Strukturdiagnose prüfen; keine Suche oder Optimierung. Python-Gegenfälle
prüfen die rationale Reduktionsschranke, Unter-/Überlauf, verlorene oder
veränderte Nachweise, Sinus-/Quotientenformen und exakte gemischte Phasen.

Format 3 ergänzt denselben Prüfschritt um den weiterhin abgelehnten
inkonsistenten Verlust aus `duration-manjaro-002` und unabhängige feste native
Gegenfälle für beide Vereinfachungspfade. Die neue gemeinsame Option
`should_simplify=false` unterdrückt diese Umformungen und die Simplify-Mutation;
alle übrigen nativen Optionsfelder und die bisherigen Defaults werden geprüft.
Die fünf technischen Suchbudgetworker laufen mit dem neuen gemeinsamen Profil.

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
und das Cacheverhalten bleiben erhalten. Jeder Job behält zunächst die
bisherige Reserve von 75 Minuten. Die parallele Aufteilung verkürzt keine
Prüfung und verändert keine fachliche Laufgrenze.
Die bisherigen Schritte bleiben erhalten;
die zusätzliche Reserve erweitert keine wissenschaftliche Laufgrenze. Lauf
[41425713993](https://github.com/craexxn/ringdown-sr/actions/runs/41425713993)
am Head `2d9b028` wurde bei bisher 30 Minuten Joblimit nach rund 31 Minuten
in der zweiten abschließenden Haswell-Wiederholung abgebrochen; alle vorherigen
Schritte waren erfolgreich. Die erweiterte native Prüffolge erhält damit
Laufzeitreserve, ohne Prüfungen auszulassen oder deren Budgets zu verändern.
Die Grenzen der wissenschaftlichen Serien und ihrer Worker bleiben unverändert.
Ein Fehler im ausgewählten Prüfpfad führt
weiterhin zu einem fehlgeschlagenen Job.

Der lokale Optimiererbudgetvergleich ergänzt `check_local_optimizer_native.py`
mit 272 nativen Assertions am festen Achtpunkt-Signal, ohne Optimierung/Suche.
`check_local_optimizer_integration.py` prüft alle 20 echten Seed-/Profiloptionen,
zwölf feste Ringdown-/Aliasfälle und alle vier lokalen Profile plus frische
Baselinewiederholung mit jeweils zwei äußeren Iterationen an acht Punkten y=1+t.
Falsche lokale Iterationen, Neustarts und gemeinsame Optionen müssen vor der
numerischen Zielfunktion scheitern. Die identische wiederholte Front prüft
Prozessisolation. Keine der 20 wissenschaftlichen Zellen wird ausgeführt.

Die äußere Staffel ergänzt `check_outer_search_ladder_integration.py`:
fünf echte native Seedoptionen bei fest 300/5, 20 Python-Suchprofile, drei
feste Ringdown-/Aliasreferenzen und 14 Syntaxfälle. Falscher Seed und falsches
100/2-Profil scheitern vor dem numerischen Callback. Danach fünf frische
300/5-Worker mit äußeren Budgets 2, 3, 4, 5 und erneut 2 am separaten
Achtpunkt-Signal y=1+t. Der echte Suchaufruf muss das jeweilige Budget
unverändert übernehmen; die wiederholten Kontrollfronten müssen identisch sein.
Python-Gegenfälle prüfen getrennte Kurven-/Strukturzahlen, alle Kontraste,
Kosten, vollständige Verifikation und Widerruf positiver Berichte.
Keine wissenschaftliche 200-/500-/2.000-/5.000-Zelle in der CI.

Der Transfercheck ergänzt `check_transfer_check_integration.py`: drei native
Seedoptionen, 18 feste Python-Suchprofile und unveränderte Alias-/Syntaxreferenzen.
Drei frische 300/5-Worker laufen mit je zwei äußeren Iterationen auf eigenen
acht Punkten y=1+t, y=0.4+2t und erneut y=1+t. Die wiederholte Front muss
identisch bleiben. Python-Gegenfälle prüfen die Signaldatenzuordnung,
relative Amplituden-/Phasenparameter, Datenrollen, alle 18 abgeschlossenen
Zellen, 15 Paare und die Widerrufssicherung nach positiver Veröffentlichung.
Alle 6.102 eingefrorenen Eingabewerte werden zusätzlich gegen eine unabhängige
Hochpräzisionsformel geprüft. Kein wissenschaftlicher Transferlauf in der CI.

Der Seed-/Treiber-Kreuzvergleich ergänzt `check_seed_driver_crosscheck.py`:
isolierte historische Worktrees bei 5215c5e und bc4025d, je eine native
Seedvorprüfung und unveränderte feste Referenzen, danach je ein frischer
Miniworker auf acht Punkten y=1+t mit Seed 73 und zwei äußeren Iterationen.
Beide vollständigen Fronten, Optionen, Fit-Callbackzahlen und Diagnosemarker
müssen übereinstimmen. Python-Gegenfälle prüfen Archiv-/Datenbindung,
Umgebungsabweichungen, feste Requests, Reihenfolge und gesperrte Teilbefunde.
Die zwei wissenschaftlichen 500-Iterations-Kreuzvergleichszellen bleiben
ausschließlich für den ursprünglichen Manjaro-Rechner vorgesehen.

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

Format 4 ergänzt `scripts/check_prediction_reference.py`: alle 34 vollständigen
Originalkandidaten und zehn ausdrücklich nachträglichen CSV-Rekonstruktionen
von Lauf 003 werden nativ und mit der neuen Referenz nachgerechnet. Es werden
keine serialisierten Suchzustände oder Archivquellen ausgeführt. Hinzu kommen
unabhängige gerichtete Julia-MPFR-Vergleiche und native FMA-/Knotenfolgegenfälle;
kein Fit und keine Suche. Die Python-Tests decken Intervallbreite, Nachbarbudget,
Halbwegsrundung, Unter-/Überlauf, Extrema, unabhängige Elternnachrechnung und
Abbruch während tatsächlicher Referenzarbeit ab. Die bestehenden kleinen
Integrationen bleiben erforderlich und nutzen im Suchbudgetpfad Format 4.
