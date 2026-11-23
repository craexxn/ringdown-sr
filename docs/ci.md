# CI nach Änderungsumfang und Entwicklungsstand

Der Workflow `Technical checks` startet bei PR-Ereignissen `opened`, `reopened`,
`synchronize`, `ready_for_review` und `converted_to_draft`, bei Pushes nach `main`
und bei manuellem Aufruf. Es gibt keine Workflow-Pfadfilter. Die Umsetzung folgt
[Abschnitten 4 und 5 des Sparplans](github_actions_savings_plan.md); die dortige
Main-Wiederverwendung bleibt getrennte Folgearbeit.

## Aktuelle Jobfrist nach PR104-Abbruch

Am 23.11.2026 besteht im [Ready-Lauf 45155705726](https://github.com/craexxn/ringdown-sr/actions/runs/45155705726)
auf Head `fd5e7d099a777b5462208a727e1f5a4c45a52d01` die Vorbereitung mit
4.791 Python-Tests, Ruff, Format und 124 Dokumentationsdateien. Der native Job
läuft von 10:34:04 bis 12:34:19 UTC und endet als `cancelled`:
30 von 34 Fachschritten bestehen, der Rauschpilot wird abgebrochen,
Hintergrund-, Folgestudien- und White-Skalierungscheck werden nicht begonnen.
Das Log meldet `The operation was canceled.`; eine gesonderte Abbruchannotation
liegt nicht vor. Die Dauer von 120 min 15 s bei konfigurierten 120 Minuten
spricht stark für die Jobfrist. Der Abschluss verweigert korrekt die Freigabe.

Das letzte abgeschlossene Fachprogramm endet bereits nach 119 min 24 s.
Die vier verbleibenden Blöcke umfassen zusammen 18 frische Suchworker sowie
feste Kontrollen, Verifikationen und Plotexporte. Ausschließlich der serielle
`native`-Job erhält daher **180 Minuten** als begrenzte Reserve, keine
vorhergesagte Laufzeit. `prepare` und Abschluss behalten je 75 Minuten.
Alle Prüfschritte, Workerfristen, Suchbudgets, wissenschaftlichen Programme
und das Vollständigkeitsgate bleiben unverändert. Historische Angaben zu
120 Minuten weiter unten beschreiben den früheren Stand. Der korrigierte
Workflow benötigt eine frische vollständige Ready-CI; der Abbruch und seine
bestandenen Teilschritte sind kein vollständiger Erfolgsnachweis.

## Scope und Ausführungsmodus

`prepare` gibt `full`, `comparison_known` und `mode` aus. `full` beschreibt den
fachlichen Prüfbedarf; ein Draft macht aus Code niemals reine Prosa.
Nur ein erfolgreicher, nichtleerer Git-Vergleich und konsistente Ereignisdaten
ermöglichen einen günstigen Pfad. Fehlende, falsch typisierte oder widersprüchliche
Draft-/Aktions-/Zustandsangaben wählen konservativ die volle Ausführung.

| Ereignis und Umfang | Modus | Tatsächliche Prüfung |
| --- | --- | --- |
| Bekannte reine Prosa, gültiges PR- oder Push-Ereignis | `docs`, `full=false` | Dokumentation |
| Code oder Laufzeitdokument, gültiger Draft-PR | `development`, `full=true` | Dokumentation, Ruff, Format, vollständige Python-Suite |
| Ready-Wechsel oder neuer Push auf einen Ready-PR mit Code | `full`, `full=true` | Schnelle und sämtliche nativen Prüfungen |
| Main-Push mit Code | `full`, `full=true` | Vollständig, ohne Wiederverwendung eines PR-Ergebnisses |
| Manueller Aufruf, unbekannter/erzwungener Vorgang oder unklarer Diff | `full`, `full=true` | Vollständig auf dem gewählten Ref |

Bei reinem Prosaumfang darf auch ein Ready-Ereignis den Dokumentationspfad
verwenden. `comparison_known=false` erlaubt nur `full`. Ein tatsächlicher
Fehler des Scope-Prozesses sperrt bereits `prepare`; eine fehlende Ausgabe
wird niemals als Dokumentationsfreigabe behandelt.

Implementierungs-PRs zunächst als Draft führen, gezieltes KI-basiertes Review
und passende lokale Tests bündeln, danach Ready wählen. Vor weiteren
Entwicklungsiterationen wieder Draft wählen. Ein anderer Zielbranch oder eine
neue Basis erfordert Abgleich und eine neue Ready-Prüfung. Vor Merge Head,
Base und tatsächlich geprüften Mergecommit kontrollieren. Ein Review ohne
Befund ist kein Nachweis bestandener Tests.

## Serielle technische Prüfungen

Der getrennte White-Skalierungspilot ergänzt `check_white_scaling.py`:
native O/S/K-Arithmetik, vollständige Optionsgegenprüfungen, Vergleich der
beobachteten und unbeobachteten lokalen Optimierung sowie vier frische
O/S/K/O-Worker mit je zwei äußeren Iterationen auf acht linearen Messpunkten.
Die O-Wiederholung muss die ursprüngliche Front und Callbackzahl reproduzieren.
Vier feste Starts prüfen zusätzlich den isolierten Fixed-Worker und dessen
lesende Nachrechnung. Python-Gegenfälle prüfen Kosten-/Abschlussbelege,
Quellenänderungen während des Exports und die gesperrte Ausgabe bei Plotfehlern.
Die wissenschaftlichen 72 lokalen Diagnosen und 21 kurzen Suchen sind nicht
Teil der CI. `docs/white_loss_scaling_plan.md` und der spätere
`docs/offgrid_selection_plan.md` gelten als laufzeitrelevante Pläne.

Der historische Regenerationstest unterscheidet unveränderte Archivbytes von
CPU-abhängiger NumPy-Signalarithmetik. Lokale Wiederholung, Methode, Seeds und
Zeitachsen bleiben exakt; archivierte und neu erzeugte Signalwerte müssen
jeweils dieselbe ursprüngliche MPFR-Fehlerschranke erfüllen. Eingefrorene Daten,
Hashes und Generatoren werden dafür nicht verändert.

| Job / Abschnitt | Prüfungen |
| --- | --- |
| `prepare` | Umfang und Modus, Dokumentation; bei vollem Scope historische Referenzen, uv/Sync, Ruff, Format und pytest |
| `native`, Block A | Julia-Starts, Verlustkern, Schema-3-Pilot, feste Konstantendiagnose, Verlust-/Vorhersagereplays, Suchbudget und fünf Pilot-Folgeprüfungen |
| `native`, Block B | Suchbeobachtung, freie PySR-Suche, Repräsentation, freier Optimierer und Grammatik |
| `native`, Block C | lokaler Optimierer einschließlich nativem Guard, äußere Staffel, Transfer und historische Kreuzprüfung |
| `technical-checks` | verbindliche Vollständigkeitsprüfung von `prepare` und `native` |

`native` startet nur nach erfolgreichem `prepare` mit `mode=full`. Die Blöcke
laufen A, B, C, innerhalb jedes Blocks in der bisherigen Reihenfolge. Alle
30 ursprünglichen Schritte des [Prüfinventars](../tests/fixtures/ci_steps_before_parallel.json)
bleiben enthalten; nur wiederholte Runner-Vorbereitung entfällt. Checkout läuft
in drei Jobs, uv/Sync in zwei Jobs, der allgemeine Python-/Julia-Umgebungscheck
einmal im nativen Job. Befehle, Optionen, Budgets, Launcher, env-Präfixe und
Fehlerausgaben sind gegen das unveränderte Inventar gebunden. Kein Cache,
keine Matrix und keine neue Abhängigkeit; Haswell-/Threadvorgaben gelten
weiterhin nur an den bisherigen einzelnen Befehlen.

Alle expliziten Ausgabepfade sind verschieden und überdecken einander nicht.
Der Schema-3-Pilot und seine fünf Folgeprüfungen liegen in Block A zusammen;
Verbraucher folgen ihrem Erzeuger. Die Haswell-Wiederholung liest den
ursprünglichen Pilotarm. Start-/Sperrtest und freie Suchkontrolle behalten ihre
eigenen `TemporaryDirectory`-Verzeichnisse; die historischen Worktrees erhalten
ein eigenes, vom Ausgabepfad abgeleitetes Hilfsverzeichnis. Jeder Fachbefehl
startet weiterhin einen eigenen Python-Prozess, explizite frische Worker und
Wiederholungsfolgen bleiben erhalten. Der nun gemeinsame Runner und seine
Julia-Installation werden im ersten vollständigen Lauf als Integration geprüft.
Keine wissenschaftlichen Serien oder geänderten SR-Suchparameter.

Die vorhandenen Schema-3-Kontrollen speichern die Bewertungsgrundlage vor der
Suche und prüfen anschließend die ergänzende Bewertung ihrer Originalauswahlen.
Die Anbindung erhält keine zusätzlichen Suchläufe oder Budgets.

Jeder Job checkt ausdrücklich `${{ github.sha }}` aus und protokolliert Commit
und Dateibaum. Bei PR-Ereignissen ist dies der Mergecommit. Volle Historie und
`persist-credentials: false` bleiben erhalten. Vor pytest und im nativen Job
werden zusätzlich die dauerhaften PR-Head-Refs 55/61/63/65/67/77/102 abgerufen.
Der lesende Actions-Token bleibt auf die Prozessumgebung dieses Fetchs begrenzt.
[Historische Bindungen](../scripts/ci_historical_refs.json) prüfen zehn Commits,
ihre Abstammung und feste Dateihashes; HEAD muss unverändert bleiben.

## Abschluss, Cancellation und manuelle Läufe

Der Job `technical-checks` hat `needs: [prepare, native]` und `if: always()`.
Er liest Ergebnisse als JSON aus einer Umgebungsvariablen, ohne Shellauswertung.
Nur diese Kombinationen erhalten Erfolg:

- `prepare=success`, `full=true`, `mode=full`, gültiger Vergleichsmarker und
  `native=success`: vollständige technische CI.
- `prepare=success`, `full=false`, `mode=docs`, `comparison_known=true` und
  `native=skipped`: Dokumentationsprüfung.

Development verlangt zwar `full=true`, `comparison_known=true`, erfolgreiche
Vorbereitung und ausdrücklich übersprungenes `native`, beendet den Abschluss
aber bewusst nicht erfolgreich:

> Schnelle Prüfungen bestanden; vollständige technische Prüfung bis Ready
> zurückgestellt. Dieser Stand besitzt noch keine vollständige CI-Freigabe.

Der grüne `prepare` zeigt bestandene schnelle Prüfungen, der rote Abschluss
die zurückgestellte Vollprüfung. Ein echter Vorbereitungsfehler wird gesondert
benannt. Fehlende Modi/Jobs, widersprüchliche Angaben, Abbrüche und unerwartete
Skips sperren weiterhin. Das Gate wird nicht übersprungen; ein GitHub-Skip kann
bei erforderlichen Checks sonst als Erfolg gelten. Kein `continue-on-error`.

Die gemeinsame Concurrency-Gruppe `technical-checks-${{ github.ref }}` und
`cancel-in-progress: true` bleiben erhalten. Draft und Ready desselben PRs
teilen sich die Gruppe; main bleibt getrennt. Ein Draft-Wechsel kann den
bisherigen vollen Lauf abbrechen. Ein Re-run behält den alten Ereigniskontext;
nach Draft-Wechsel deshalb den neuen Lauf nutzen und keinen alten Ready-Lauf
neu starten. Es wird kein Ergebnis auf einen anderen Commit übertragen.

Nur bei `workflow_dispatch` heißt derselbe Abschlussjob sichtbar
`manual-technical-checks`, sonst `technical-checks`. Es gibt keinen zusätzlichen
übersprungenen PR-Abschluss im manuellen Lauf. Ein manueller Branchlauf
berechtigt nicht zur Freigabe eines anderen PR-Mergecommits.

Am 05.11.2026 meldete die gelesene Main-Branchantwort weiterhin `protected:false`
und keine erforderlichen Statuschecks. Eine automatisch erzwungene Merge-Sperre
ist damit nicht belegt. Vollständige Prüfung vor Merge bleibt Arbeitsregel;
Repository-Einstellungen werden mit diesem Auftrag nicht verändert.

## Kosten und Abnahme

Für eine spätere öffentliche Sichtbarkeit gilt: Die hier verwendeten
Standard-Runner `ubuntu-24.04` sind in öffentlichen Repositories kostenlos.
Größere Runner bleiben kostenpflichtig; Speicher hat eigene Regeln gemäß
[GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
Das ändert weder erforderliche Prüfungen noch den seriellen Ablauf. Der
historische Sparplan und seine Messungen bleiben erhalten. Die Prüfung von
Actions-Logs, Fork-Freigaben und tatsächlichem Branchschutz steht im
[Veröffentlichungsbefund](publication_review.md). Dieser Dokumentationsnachtrag
ändert keine Repository-Einstellung oder Workflow-Berechtigung.

Der [Sparplan](github_actions_savings_plan.md) nennt historische Jobzeiten und
rechnerische Einsparungen, keine gemessenen Kosten des neuen Ablaufs. Durch zwei
entfallende allgemeine Umgebungsprüfungen werden neun bis elf Runner-Minuten je
Vollprüfung erwartet; die sichtbare Dauer kann auf etwa 45–65 Minuten steigen.
Die einmalige Draft-/Ready-Abnahme und tatsächliche Jobzeiten stehen im
[Fortsetzungsstand](representation_implementation_status.md) beziehungsweise PR.
Es gibt keinen zusätzlichen Volltest allein zur Kostenmessung. Die nächsten
drei ohnehin anstehenden PRs dienen der Verbrauchsbeobachtung.

## Schlanker Dokumentationspfad

Sind alle geänderten Dateien ausschließlich erlaubte Prosa (`README.md`,
`AGENTS.md` oder Markdown unter `docs/`), installiert `prepare` weder die
Projektumgebung noch Julia. Der native Job wird ausdrücklich übersprungen;
Python aus der Runner-Standardinstallation prüft die Dokumentation.
Eine neue Datei `LICENSE` im Repository-Wurzelverzeichnis fällt nach der
unveränderten Klassifikation in den vollständigen Scope. Dieser Auftrag
erweitert die Ausnahme nicht; sein Prüfstand wird entsprechend als
vollständiger Scope geführt.

Geprüft werden alle versionierten Markdown-Dateien: UTF-8, abschließender
Zeilenumbruch, unerwünschte Leerzeichen und abgeschlossene Codeblöcke sowie
lokale Dateiziele von Inline- und Referenzlinks. Zwei Leerzeichen als
Markdown-Zeilenumbruch und CRLF bleiben zulässig. Codebeispiele werden nicht
als Links geprüft; externe Webadressen und Sprungmarken werden nicht validiert.
Dies ist eine begrenzte Prüfung, kein vollständiger Markdown-Parser.

**Ausnahmen:** `docs/noiseless_control_plan.md`,
`docs/search_representation_plan.md`, `docs/constant_diagnostic_plan.md`,
`docs/free_optimizer_budget_plan.md`, `docs/search_trajectory_plan.md`,
`docs/search_trajectory_replay_policy.md`, `docs/trigonometric_grammar_plan.md`
`docs/search_duration_plan.md`, `docs/search_duration_verification_plan.md`
`docs/search_duration_table_loss_note.md`
`docs/search_duration_simplification_plan.md`
`docs/search_duration_prediction_plan.md`, `docs/local_optimizer_plan.md`
`docs/outer_search_ladder_plan.md`, `docs/transfer_check_plan.md`,
`docs/seed_driver_crosscheck_plan.md`, `docs/global_restart_comparison_plan.md`
sowie `docs/iteration_time_budget_plan.md`, `docs/restart_confirmation_plan.md`
und `docs/time_coordinate_plan.md`, `docs/restart_budget_plan.md`,
`docs/restart_budget_confirmation_plan.md`, `docs/noise_pilot_plan.md`
und `docs/noise_background_plan.md`, `docs/noise_followup_plan.md`
sind als eingefrorene Kontrollpläne
mit festgelegter Prüfsumme an den jeweiligen Code gebunden.
Änderungen daran erhalten trotz Markdown-Endung die volle CI. Weitere
Laufzeitdokumente müssen ebenso ausdrücklich als Ausnahme erfasst werden.

Der Neustartvergleich ergänzt im bestehenden nativen Job
`scripts/check_global_restarts.py`: drei frische technische Worker auf acht
Punkten `y=1+t`, äußere Budgets 2/3/2, danach lesende Prüfung gespeicherter
nativer Nachweise mit Python-/MPFR-Nachrechnung. Bestehende Prüfblöcke bleiben
unverändert. Der wissenschaftliche
20-Aufruf-Laufweg wird nicht in Actions ausgeführt.

Der Zeitbudgetvergleich ergänzt denselben seriellen Job um
`scripts/check_time_budget_dynamics.py` (drei frische technische Präfixe bis
zu vier festen Populationsschritten) und `scripts/check_iteration_time.py`
(vier Worker auf acht Punkten: Iterationsende, 0,01-Sekunden-Zeitende,
Reserveende und wiederholte Iterationskontrolle, danach lesende Verifikation).
Die tatsächlich begrenzte CPU-Affinität und Julia-/GC-/BLAS-Threads werden
geprüft. Bestehende Prüfblöcke bleiben bestehen; keine wissenschaftliche
400-Sekunden-Serie in GitHub Actions.

Die unabhängige Bestätigung ergänzt `scripts/check_restart_confirmation.py`:
zwei getrennte Achtpunkt-Signale `y=1+t` und `y=2−t`, jeweils zwei kurze
Mitglieder mit zwei Iterationen und eine lange Kontrolle mit drei Iterationen.
Sechs frische technische Worker, tatsächliche Thread-/Aufrufbelege sowie
lesende Einzel- und Gesamtverifikation. Die wissenschaftlichen 150 Aufrufe
bleiben ausschließlich ein separater Manjaro-Schritt; bestehende Prüfblöcke
werden nicht ersetzt. Der neue eingefrorene Plan erhält die volle CI.

Der begrenzte Zeitkoordinatenvergleich ergänzt `scripts/check_time_coordinate.py`:
dieselben beiden künstlichen Achtpunkt-Signale, je eine Suche in t und in u=32t,
jeweils nur zwei äußere Iterationen. Vier frische technische Worker mit nativen
Quellen-/Aufrufbelegen, physischer Auswertung und lesender Einzel-/Gesamtprüfung.
Keine wissenschaftliche 16-Aufruf-Serie in Actions; bisherige Prüfblöcke bleiben.

Der Anschlussvergleich der Neustartbudgets ergänzt `scripts/check_restart_budget.py`:
zwei künstliche Achtpunkt-Signale, jeweils vier R-Worker mit einer und zwei
L-Worker mit zwei äußeren Iterationen. Zwölf kleine technische Worker und vier
Paketausgaben prüfen beide Mehrmitgliedsauswahlen, tatsächliche Iterationsenden,
Herkunft, Kosten und lesende Einzel-/Gesamtverifikation. Die wissenschaftlichen
48 Aufrufe sind ein separater Manjaro-Schritt. Alle bisherigen Prüfblöcke bleiben;
keine Änderung der historischen Budgets oder Erweiterung zu wissenschaftlichen
Serien in Actions.

Die neue unabhängige Bestätigung ergänzt
`scripts/check_restart_budget_confirmation.py`: zwei getrennte künstliche
Achtpunkt-Signale, je vier R-Worker mit einer und zwei L-Worker mit zwei äußeren
Iterationen. Zwölf kleine Worker prüfen den neuen gebundenen Laufweg,
Paketwahl, Kosten sowie lesende Einzel-/Gesamtverifikation. Technische Fixtures
geben weder die praktische R-Grenze noch die getrennte L-Kontrollgrenze frei.
Die 180 wissenschaftlichen Suchaufrufe bleiben ein separater Manjaro-Schritt;
alle historischen Prüfblöcke bestehen unverändert fort.

Die Profilübernahme aus Phase 5 ergänzt `scripts/check_confirmed_profile.py`
im bestehenden nativen Job. Der technische Viererpaketweg mit vollständiger
Kovarianz und gewöhnliche/diagonale Kontrollen verwenden sechs frische kleine
Worker. Feste Referenzen prüfen zusätzlich die gewichtete Strukturrangfolge
und Konstantenoptimierung unter lokal 300/5. Die äußeren Budgets sind
ausdrücklich reduziert; wissenschaftliche 1.000er-Suchen oder ein Rauschpilot
werden dadurch nicht in Actions gestartet. Alle bisherigen Prüfblöcke bleiben
erhalten. Die vorhandene 120-Minuten-Frist bleibt zunächst unverändert;
der neue vollständige Lauf muss ihre Eignung bestätigen.

Der begrenzte Rauschpilot ergänzt `scripts/check_noise_pilot.py` mit drei
frischen technischen Workern: gewöhnliche, wahre und geschätzte Gewichtung
auf 128 Punkten mit AR(1)-Rauschen, je zehn äußere Iterationen bei lokal 300/5.
Eigene technische Seeds trennen diese Kontrolle von den wissenschaftlichen
Blöcken. Jeder Worker erhält höchstens 600 Sekunden; der Checker speichert
die technische Konfiguration und die vollständige Aufrufmessung. Anschließend
prüft ein separater `--verify`-Aufruf die vorhandene Ausgabe
`results/ci-noise-pilot-001` lesend. Fehler aus Lauf oder Verifikation sperren
den Job und geben vorhandene Workerlogs aus. Der neu konsumierte eingefrorene
Rauschpilotplan gehört zum vollen CI-Scope. Keine der 144 wissenschaftlichen
Suchen wird in Actions gestartet; sämtliche bisherigen Prüfblöcke bleiben
erhalten. Die Frist des nativen Jobs bleibt zunächst bei 120 Minuten; die
Laufzeit des neuen Vorlaufs muss vor Ready gegen die verbleibende Reserve
geprüft werden. Dies ändert keine wissenschaftliche Workerfrist.

Die Hintergrundstudie ergänzt `scripts/check_noise_background.py`: fünf
frische N128-Worker mit zehn äußeren Iterationen bei lokal 300/5, je einer
für O/K/E64/E256/E1024. Ein gemeinsamer technischer AR(1)-Fall bindet den
1.024er-Trainingspool samt Präfixen und die getrennten 128/256 Fenster.
Nach dem Lauf folgen ein eigener `--verify`-Aufruf und der rein lesende
`run_noise_background.py technical-plots`-Export mit Originalformeln und
zugeordneten Plotdaten. Jeder der drei Schritte sperrt bei einem Fehler den
Job; vorhandene Workerlogs bleiben sichtbar. Die Ausgaben
`results/ci-noise-background-001` und `results/ci-noise-background-plots-001`
sind getrennt. Alle bisherigen Prüfblöcke bleiben erhalten; keine der
520 wissenschaftlichen Suchen wird in Actions gestartet. Der neu konsumierte
Hintergrundplan gehört zum vollen CI-Scope. Die native Jobfrist bleibt
zunächst bei 120 Minuten; ihre Reserve ist anhand des neuen technischen
Laufs vor Ready zu prüfen. Implementierung und Workflowanbindung allein
belegen noch keine erfolgreiche native Prüfung.

Die Dauer-/Messraster-Folgestudie ergänzt `scripts/check_noise_followup.py`:
sechs frische technische N128-Worker mit jeweils zehn äußeren Iterationen
bei lokal 300/5. Vier uniforme Bedingungen O/K/E64s/E4096s und zwei echte
Jitterbedingungen O/K teilen einen eigenen technischen AR(1)-Fall;
die Sekundenangaben bezeichnen kontinuierliche Hintergrunddauer, nicht
die Zahl unabhängiger Fenster. Der Vorlauf prüft den gebundenen neuen
Schätzer- und Rasterweg mit eigenen technischen Seeds. Danach folgen ein
separater `--verify`-Aufruf und `run_noise_followup.py technical-plots` mit
allen sechs Originalformeln und Punktdaten. Fehler in jedem dieser drei
Schritte sperren den Job und geben vorhandene Workerlogs aus. Die Ausgaben
`results/ci-noise-followup-001` und `results/ci-noise-followup-plots-001`
sind getrennt; alle bisherigen Prüfblöcke bleiben erhalten. Keine der
624 wissenschaftlichen Suchen und keine wissenschaftliche Armwahl laufen
in Actions. Der eingefrorene Plan gehört zum vollen CI-Scope; Plan und
Seedtabelle sind zusätzlich an den Vorabcommit aus PR #102 gebunden.
Die native Jobfrist bleibt bei 120 Minuten. Ihre Eignung ist vor Ready
anhand des vollständigen nativen Laufs zu prüfen; die Workflowanbindung
allein belegt keinen erfolgreichen technischen Vorlauf.

Die Frist ausschließlich des seriellen `native`-Jobs wurde mit PR85 auf 90 Minuten
gesetzt. Der damals zuletzt vollständig geprüfte native PR83-Lauf
`43168577591` dauerte laut Joblog 55 min 37 s. Der lokale neue Vorlauf benötigte
bereits 20 min 16 s für seine beiden Abschnittsaufrufe, zuzüglich separater
Einzel-/Gesamtverifikation. Die bisherige 75-Minuten-Frist lässt für die zwölf
zusätzlichen frischen Kontrollworker damit zu wenig Reserve; lokale Zeiten
sind dabei keine Garantie der Actions-Laufzeit.
`prepare` und Abschluss behalten je 75 Minuten; keine Änderung der eingefrorenen
wissenschaftlichen Worker-/Abschnittsfristen und keine ausgelassenen Prüfblöcke.

Erste Einordnung vom 13.11.2026: Der vollständig erfolgreiche native PR85-Lauf
`43213172104` benötigte laut Joblog 64 min 24 s; sein Zwölf-Worker-Budgetblock
davon 11 min 43 s. Für den zusätzlichen gleich großen technischen
Bestätigungsblock blieb die vorhandene 90-Minuten-Frist zunächst bestehen.
Diese Orientierung ist keine Garantie der nächsten Actions-Laufzeit.

Korrektur nach [PR87-Lauf 43380454967](https://github.com/craexxn/ringdown-sr/actions/runs/43380454967):
Der native Job begann um 06:48:11 UTC und wurde um 08:18:23 UTC nach rund
90 Minuten abgebrochen. Alle Blöcke bis einschließlich Zeitkoordinatenprüfung
bestanden; der bisherige Budgetblock wurde nach 15 min 27 s abgebrochen,
der neue Bestätigungsblock nicht begonnen. Im Log steht ausschließlich
`The operation was canceled.`, kein fachlicher Testfehler. Zeitpunkt und
konfigurierte Jobfrist sprechen für das Zeitlimit; eine gesonderte
Abbruchannotation lag bei der Auswertung nicht vor.

28 vergleichbare abgeschlossene Loggruppen benötigten zusammen rund 42 % mehr
Zeit als im PR85-Lauf. Mit dieser beobachteten Verlangsamung liegt die grobe
Orientierung für den vollständigen Umfang einschließlich des neuen Blocks bei
108 Minuten. Deshalb erhält ausschließlich der serielle `native`-Job nun
**120 Minuten**. Die beiden übrigen Jobs behalten je 75 Minuten; alle Prüfschritte,
wissenschaftlichen Fristen und eingefrorenen Protokolle bleiben unverändert.
Der Abschluss verweigert eine Freigabe bei abgebrochenem nativen Job weiterhin.
Der neue Workflowstand benötigt eine frische vollständige Ready-CI;
ein Wiederanlauf des alten Stands würde die alte 90-Minuten-Frist verwenden.

Abschluss am 13.11.2026: Der neue
[Ready-Lauf 43394100165](https://github.com/craexxn/ringdown-sr/actions/runs/43394100165)
auf Head `b17a741` bestand vollständig: 3.656 Pythonfälle und sämtliche nativen
Blöcke einschließlich der zwölf neuen Bestätigungsworker und lesender
Einzel-/Gesamtverifikation. Alle drei Jobs prüften Mergecommit `93d6b3a` mit
Baum `8ddae5be67afd26fa3615a9bb54883d6609d70e7`; der tatsächliche
PR87-Merge `6bc0282` besitzt denselben Baum. Keine wissenschaftliche Serie in CI.

Auch `docs/supplemental_assessment.md` erhält die volle CI: Der lesende
Bewertungsexport bindet diesen Versionsvertrag an seinen Softwarestand.
Dies gilt ebenso für `docs/supplemental_structure.md`, den gebundenen
Stufe-2-Vertrag. Die beiden vorhandenen Schema-3-Kontrollen prüfen zusätzlich
das vor dem ersten Fit gespeicherte Intervall, getrennte Strukturstatus und
die unveränderte Originalauswahl. Keine zusätzlichen Suchläufe oder Jobs.
Auch `docs/supplemental_remainder.md` ist gebundene Laufzeiteingabe. Dieselben
Kontrollen prüfen in Stufe 3 außerdem den vorab gespeicherten Resttermvertrag,
getrennte Komponentendiagnosen und die Hashbindung beider Referenzraster.
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

Jede andere geänderte Datei verlangt vollen fachlichen Prüfumfang, insbesondere
Code, Tests, Konfigurationen, Lockdateien, Julia-Dateien und CI-Werkzeuge.
Gemischte Änderungen behalten ebenfalls `full=true`; im gültigen Draft-Modus
werden die nativen Prüfungen bis Ready zurückgestellt. Bei manuellen
Aufrufen, unbekannten oder erzwungenen Ereignissen, leerem Diff sowie
fehlenden oder nicht vergleichbaren Commits wird vollständig geprüft.

Die bisherigen Prüfbefehle, Versionspins, Rechte, Thread-/Haswell-Vorgaben
und das Cacheverhalten bleiben erhalten. Jeder Job behält zunächst die
bisherige Reserve von 75 Minuten. Die serielle Zusammenlegung verkürzt keine
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
weiterhin vollen fachlichen Scope; nur ein gültiger Draft kann die native
Ausführung bis Ready zurückstellen.
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
