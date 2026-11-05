# Umsetzungsplan: GitHub-Actions-Rechenzeit während der Implementierung senken

Stand: 05.11.2026. Zielort: `docs/github_actions_savings_plan.md`.
Status: Abschnitte 4 und 5 zur Umsetzung beauftragt. Der tatsächliche
Implementierungs- und Prüfstand steht im
[Fortsetzungsstand](representation_implementation_status.md).
Main-Wiederverwendung nach Abschnitt 6 bleibt getrennte Folgearbeit;
Repository-Einstellungen und Abrechnung sind nicht Teil dieses Auftrags.

Geprüfte Codebasis: `e09ab286fc853fe2991f070c4d96d9f070b55d9d`.
Vor Umsetzung aktuellen main- und PR-Stand erneut abgleichen.

## 1. Ziel und gewählte Reihenfolge

Das Actions-Kontingent wurde nach Projektangabe innerhalb von drei bis vier
Tagen weitgehend verbraucht. Ziel ist vor allem eine geringere Häufigkeit
teurer Vollprüfungen während der Entwicklung. Die vollständige technische
Prüfung des abschließend zu übernehmenden Codezustands bleibt erhalten.

1. **Nächster Implementierungs-PR:** Draft-PRs erhalten schnelle Prüfungen;
   der Übergang zu Ready startet die vollständige CI. Die drei nativen Blöcke
   laufen dabei wieder seriell in einem gemeinsamen Job. Review und gezielte
   Tests finden vorher in Codex beziehungsweise lokal statt.
2. **Danach als abgegrenzte Erweiterung:** Einen bereits vollständig geprüften
   Merge auf main anhand eines gebundenen Nachweises erkennen und seine
   nativen Prüfungen nicht nochmals ausführen. Bei Unklarheit bleibt die
   vollständige Ausführung erhalten.
3. Erst nach Messung verbleibender Kosten zusätzliches Julia-Caching oder
   einen eigenen Runner untersuchen. Kein gleichzeitiger Umbau aller Mechanismen.

Dies ist ein technisches Arbeitspaket zur Durchführung der
[Rekonstruktions-Roadmap](ringdown_recovery_roadmap.md), keine neue
wissenschaftliche Suchintervention und keine Änderung ihrer Erfolgsregeln.

## 2. Gemessener Ausgangspunkt

Der aktuelle Workflow besitzt fünf Ubuntu-24.04-Jobs: prepare, drei native
Julia-Jobs und den Abschluss technical-checks. Er startet bei PR-Updates,
Pushes nach main und manuellen Aufrufen. Überholte Läufe werden bereits
abgebrochen; reine Prosa besitzt bereits einen günstigen Prüfpfad.

| Erfolgreicher Lauf | Summierte Jobzeit | Aufgerundet je Job, näherungsweise |
|---|---:|---:|
| [PR-Lauf 42065464612](https://github.com/craexxn/ringdown-sr/actions/runs/42065464612) | 57:46 Minuten | 62 Runner-Minuten |
| [Main-Lauf 42057578451](https://github.com/craexxn/ringdown-sr/actions/runs/42057578451) | 70:05 Minuten | 73 Runner-Minuten |

Diese Angaben stammen aus Jobzeitstempeln, nicht aus einer Rechnung.
Parallelisierung verkürzt die Wartezeit, nicht automatisch die Summe der
Runner-Minuten. Die Umgebungsprüfungen allein benötigen in diesen Läufen
summiert 13:11 beziehungsweise 16:14 Minuten. Python-Synchronisierung benötigt
dagegen nur wenige Sekunden je Job. Es gibt derzeit keine Artefakt-Uploads
und keine Abhängigkeits-Caches in diesem Workflow.

Ein Dokumentationscommit innerhalb eines bereits Code enthaltenden PRs
startet aktuell ebenfalls die volle CI, da der gesamte PR-Diff maßgeblich ist.

## 3. Codex-Review und tatsächliche Testausführung

Ein Code-Review untersucht Änderungen, Fehlerfälle und fachliche Risiken.
Codex kann dazu auch Code und Tests ausführen. Die Review-Funktion garantiert
jedoch nicht, dass sämtliche vorgeschriebenen Repository-Tests gelaufen sind.
Ein Review ohne Befund ersetzt keinen dokumentierten vollständigen Testlauf.

CI ist die automatische Ausführung festgelegter Prüfungen. Für dieses Projekt
umfasst sie unter anderem Julia-Startverhalten, Verlustkern, Konstantenoptimierung,
numerische Replays und kleine native SR-Kontrollen. Diese Prüfungen bleiben
Bestandteil der abschließenden Vollprüfung.

Vorgesehener Ablauf:

1. In Codex beziehungsweise lokal implementieren und passende Tests ausführen.
2. Den konkreten Diff einmal gezielt mit Codex prüfen; bei größeren Änderungen
   die wesentlichen Methoden- und Implementierungsrisiken vorgeben.
3. Korrekturen bündeln und die betroffenen Tests erneut ausführen.
4. Erst danach den PR von Draft auf Ready setzen und die vollständige CI starten.
5. Nach bestandener unveränderter Prüfung keine routinemäßigen Wiederholungen.

Reviewaufträge halten Commit, Basis und Prüfumfang fest. Testnachweise nennen
Befehl, Umgebung, geprüften Commit beziehungsweise Dateibaum, Exitstatus und
Ergebnis. Nicht ausgeführte Prüfungen bleiben ausdrücklich offen. Ein lokaler
Testlauf prüft nicht automatisch auch den GitHub-Mergecommit.

Für diesen Ablauf genügt ein gezieltes Review in Codex. Keine zusätzliche
automatische Reviewrunde bei jedem Push einrichten. Codex-Nutzung besitzt
eigene Kontingente. Die OpenAI-Integration ist von einem eigens in GitHub Actions
installierten Review-Workflow zu unterscheiden: Letzterer verbraucht wiederum
Runner-Zeit. Pushes infolge von Korrekturen können weiterhin Actions auslösen.

## 4. Erster Umsetzungs-PR: Draft-Modus und serielle native Prüfung

Den PR in zwei nachvollziehbare Commits gliedern: zunächst Draft-Steuerung,
danach Zusammenlegung der nativen Jobs. Beide während der Bearbeitung im Draft
halten; nach lokalen Gegenprüfungen ein gemeinsamer abschließender Volltest.

### Ereignisse und Arbeitsweise

Die vorhandene Datei `.github/workflows/technical-checks.yml` erweitern:

```yaml
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review, converted_to_draft]
  push:
    branches: [main]
  workflow_dispatch:
```

Neue Implementierungs-PRs werden als Draft erstellt. Auch die erste
Review-/Korrekturrunde erfolgt im Draft. Vor weiteren Entwicklungsiterationen
an einem bereits bereiten PR zuerst wieder auf Draft wechseln.

| Ereignis und Änderungsumfang | Ausführung | Aussage des Abschlusses |
|---|---|---|
| Nachweislich reine Prosa | Bestehende Dokumentationsprüfung | Dokumentationsprüfung bestanden |
| Code oder Laufzeitdokument in einem Draft-PR | Dokumentation, Ruff, Format, Python-Suite | Vollprüfung ausdrücklich zurückgestellt |
| Übergang zu Ready bei vollem Prüfumfang | Gesamte bisherige CI | Vollständig geprüft, sofern alle Pflichtjobs bestanden |
| Neuer Push auf einen Ready-PR | Gesamte bisherige CI | Neuer Stand benötigt eigenen Erfolg |
| Rückkehr zu Draft | Schnelle Prüfungen; älteren Lauf abbrechen | Keine neue Vollfreigabe |
| Push nach main | Im ersten Commit unveränderte bisherige Scope-Regel | Code voll, reine Prosa schlank |
| Manueller Aufruf | Vollständige CI auf dem gewählten Ref | Nur dieser tatsächlich geprüfte Stand |

Ein Wechsel der Zielbranch beziehungsweise eine inzwischen geänderte Basis
darf keinen alten Nachweis ersetzen: PR zurück auf Draft setzen, mit der
aktuellen Zielbasis abgleichen und anschließend eine neue Ready-Prüfung
auslösen. Vor Merge Head, Base und geprüften Mergezustand abgleichen.
Titel- oder Beschreibungskorrekturen allein benötigen keinen Volltest.

### Prüfbedarf und Ausführung getrennt speichern

`scripts/check_ci.py` behält den bisherigen fachlichen Scope `full=true/false`.
Zusätzlich wird `mode=docs|development|full` ausgegeben:

- `docs`: Scope ist nachweislich reine erlaubte Prosa.
- `development`: voller fachlicher Prüfumfang, aber eindeutig gültiges
  `draft: true` bei einem der oben genannten PR-Ereignisse.
- `full`: abschließende Codeprüfung, manueller Aufruf oder sonstiger
  vollständiger Ausführungspfad.

Fehlende, falsch typisierte oder widersprüchliche Metadaten dürfen nie den
Sparpfad wählen. Ein unklarer Diff wählt konservativ die Vollprüfung;
ein tatsächlicher Fehler der Scope-Ermittlung sperrt den Lauf.
Draft bedeutet insbesondere niemals `full=false`.

Die Scope-Ermittlung muss dafür zusätzlich einen strukturierten Befund
`comparison_known=true/false` bereitstellen. Das bisherige `full=true` allein
unterscheidet bekannte Codeänderungen nicht von einem fehlgeschlagenen Vergleich.
Nur ein erfolgreich ermittelter Diff darf den Entwicklungsmodus ermöglichen;
keine Entscheidung anhand eines frei formulierten Meldungstexts treffen.

`prepare` führt bei vollem fachlichem Scope auch im Entwicklungsmodus die
bisherigen Dokumentations-, Ruff-, Format- und Python-Prüfungen aus. Die für
pytest erforderlichen historischen Git-Referenzen bleiben erhalten.
Der zusammengelegte native Job startet nur im gültigen Modus `full` nach
erfolgreicher Vorbereitung. Sämtliche bisherigen fachlichen Befehle, Optionen,
Budgets, Fehlerausgaben und blockinternen Reihenfolgen bleiben erhalten.

### Parallelisierung zurücknehmen

Die bestehenden Jobs `native-a`, `native-b` und `native-c` durch einen Job
`native` ersetzen. Die Blöcke laufen darin in der Reihenfolge A, B, C; innerhalb
jedes Blocks bleibt die bisherige Reihenfolge erhalten.

- Checkout, Aufzeichnung von Commit/Tree, historische Referenzen, uv/Sync und
  die allgemeine Python-/Julia-Umgebungsprüfung nur einmal je nativem Job ausführen.
- Alle fachlichen Prüfungen genau einmal beibehalten. Der Start-/Sperrtest und
  explizit frische Unterprozesse bleiben unverändert. Ein gemeinsamer Runner
  darf nicht zu gemeinsam benutztem wissenschaftlichem Workerzustand führen.
- Die Schema-3-Pilotdaten und sämtliche davon abhängigen Prüfungen verbleiben
  zusammen im bisherigen Block A. Vor Beginn vorhandene Ausgabe-/Temp-Pfade
  auf Kollisionen zwischen den bisherigen Jobs prüfen.
- Die bisherigen Haswell-/Threadvorgaben weiterhin nur an den jeweiligen
  Befehlen setzen. Keine globalen CPU- oder Optimierereinstellungen ändern.
- Der Abschluss benötigt `prepare` und `native`; die Erwartung an drei native
  Ergebnisse wird passend geändert. Full verlangt beide erfolgreich; Docs
  verlangt erfolgreiche Vorbereitung und explizit übersprungenen nativen Job;
  Development bleibt ohne vollständige Freigabe.
- Zunächst das vorhandene Joblimit von 75 Minuten beibehalten und im ersten
  echten Volltest die Laufzeit prüfen. Bei Zeitüberschreitung zuerst den
  verursachenden Schritt untersuchen, keinen Test zur Kostensenkung entfernen.

Das ist ein begrenzter Workflow-Umbau; die SR-Implementierung wird dafür nicht
geändert. Er verändert bewusst die Umgebungsaufteilung. Deshalb Befehlsinventar,
Ausgabepfade und Isolation prüfen, statt eine unveränderte Gesamtwirkung allein
aus identischen Befehlen abzuleiten.

Grobe Erwartung: Zwei von drei bisherigen allgemeinen Umgebungsprüfungen
entfallen. Aus den beobachteten 13 bis 16 summierten Minuten ergäben sich bei
ähnlicher Verteilung etwa neun bis elf eingesparte Runner-Minuten je Volltest.
Das ist keine Messung des seriellen Ablaufs. Die sichtbare Laufzeit könnte
dafür ungefähr 45 bis 65 statt rund 27 Minuten betragen. Maßgeblich ist der
tatsächliche erste Volltest; kein zusätzlicher Vergleichslauf allein für diese
Schätzung nötig.

### Abschluss und sichtbare Zustände

Der bestehende Job `technical-checks` läuft weiterhin mit `always()`.
Für PR-Ereignisse bleibt der Name fest; kein Wechsel des Abschlussnamens
zwischen Draft und Ready und keine zusätzliche Check-Status-API.

Erfolg gibt es nur bei vollständig bestandener Dokumentationsprüfung oder
vollständiger technischer Prüfung. Im Entwicklungsmodus beendet sich der
Abschluss bewusst **nicht erfolgreich**, mit der eindeutigen Meldung:

> Schnelle Prüfungen bestanden; vollständige technische Prüfung bis Ready
> zurückgestellt. Dieser Stand besitzt noch keine vollständige CI-Freigabe.

Der grüne prepare-Job zeigt die erfolgreichen schnellen Prüfungen; der rote
Abschluss bezeichnet die fehlende Vollprüfung, keinen behaupteten Testdefekt.
Scheitert bereits prepare, ist dieser echte Fehler getrennt zu benennen.
Diese einfache Darstellung wird zugunsten einer eindeutigen Sperre gewählt.

Das Abschluss-Gate darf nicht einfach übersprungen werden: GitHub kann einen
übersprungenen erforderlichen Job als erfolgreich behandeln. Fehlender Modus,
fehlende Jobs, Abbrüche, unerwartete Skips und Widersprüche sperren weiterhin.

Die vorhandene gemeinsame Concurrency-Gruppe je PR-Ref bleibt für Draft und
Ready dieselbe; main bleibt getrennt. Kein neuer Gruppenname je Modus.
Ein Draft-Wechsel kann dadurch eine bereits laufende alte Vollprüfung abbrechen.
Ein neu gestarteter Lauf überträgt keine erfolgreiche Prüfung auf einen anderen
Commit. Bei einem Re-run gilt der ursprüngliche Ereigniskontext: Nach einem
Draft-Wechsel deshalb den neuen Lauf verwenden, keinen alten Ready-Lauf neu starten.

Manuelle Läufe sind keine Freigabe eines beliebigen PRs. Ihr Abschluss erhält
den eindeutig abweichenden angezeigten Namen `manual-technical-checks`;
der reguläre PR-Abschluss bleibt `technical-checks`. Es wird kein Ergebnis
zwischen Branch-HEAD und PR-Mergecommit übertragen.
Hierfür denselben Gate-Job verwenden und seinen angezeigten Namen ausschließlich
anhand des Ereignisses zwischen diesen zwei festen Namen wählen. Keinen zweiten,
übersprungenen regulären Abschlussjob im manuellen Lauf erzeugen.

### Betroffene Dateien

| Datei | Änderung |
|---|---|
| `.github/workflows/technical-checks.yml` | Ready-/Draft-Ereignisse, Modusweitergabe, ein serieller nativer Job, eindeutiger manueller Abschluss |
| `scripts/check_ci.py` | Gültige Modi ermitteln; Abschluss für prepare und native vollständig prüfen |
| `tests/test_ci.py` | Ereignis-/Modus-/Gate-Gegenfälle, vollständiges Befehlsinventar und angepasste Jobzuordnung |
| `docs/ci.md` | Neuer Ablauf, Scope gegenüber Modus, vollständiger Prüfbedarf |
| `AGENTS.md` | Draft zuerst, Review und gebündelte Korrekturen vor Ready |
| `docs/representation_implementation_status.md` | Geprüfter Umsetzungsstand und nächster Schritt |
| `README.md` | Kurzer Verweis auf den aktuellen CI-Ablauf |

Das bisherige Befehlsinventar bleibt die Referenz für die fachlichen
Prüfschritte. Tests für geänderte Steuerung gezielt anpassen; keine
unbegründete Lockerung oder Entfernung der Vollständigkeitskontrollen.

## 5. Abnahme des ersten Umsetzungs-PRs

Mit lokalen Ereignis-/Ergebnisfixtures prüfen:

1. Draft-Code führt die schnellen Prüfungen aus, aber keinen nativen Job;
   der vollständige Abschluss kann nicht grün werden.
2. Ready und ein neuer Ready-Push verlangen den vollständigen nativen Job.
3. Reine Prosa bleibt billig; jedes bereits gebundene Laufzeit-Markdown
   einschließlich Bewertungsvertrag behält vollen fachlichen Prüfumfang.
4. Fehlender Modus, ungültiger Draft-Wert und unklarer Scope erlauben keine
   erfolgreiche Sparfreigabe.
5. Fehler, Abbruch, fehlender Job und unerwarteter Skip sperren den Abschluss.
6. Alle bisherigen fachlichen Prüfkommandos, Budgets und blockinternen
   Reihenfolgen bleiben erhalten; nur wiederholte Runner-Vorbereitung entfällt.
7. Manuelle und normale PR-Abschlüsse besitzen eindeutige unterschiedliche Namen.

Danach am Implementierungs-PR einmal den Draft-Pfad, den Ready-Übergang und
die vollständige CI nachweisen. Ereignissteuerung und Cancellation möglichst
mit kurzen Prüfungen beobachten; keine zusätzlichen wissenschaftlichen Suchen.
Der erste main-Lauf bleibt vollständig, weil die Nachweiswiederverwendung
noch nicht implementiert ist. Das Einsparziel rechtfertigt keinen ungeprüften Merge.

Vor Aussagen über eine automatisch erzwungene Merge-Sperre tatsächliche
Repository-Regeln prüfen. Die gelesene Branchantwort meldete `protected:false`;
wir haben damit keinen Nachweis eines aktiven verpflichtenden Statuschecks.
Private Branchschutzfunktionen hängen unter anderem vom GitHub-Tarif ab.
Bis ein wirksamer Schutz nachgewiesen ist, bleibt die Kontrolle vor Merge
eine ausdrückliche Arbeitsregel. Einstellungen nicht stillschweigend ändern.

## 6. Zweiter Schritt: vollständige Main-Doppelprüfung vermeiden

Diese Erweiterung folgt separat, wenn die erste Einsparung nicht genügt.
Bis dahin bleibt der bisherige main-Pfad erhalten. Ein bloß grüner PR oder
eine passende Commitnachricht reicht nicht zum Überspringen der nativen CI.

Ein erfolgreicher vollständiger PR-Lauf veröffentlicht einen kleinen
maschinenlesbaren Nachweis, zum Beispiel `ci-proof.json`, als Actions-Artefakt:
Repository, Workflow-ID, Run-ID und Attempt, Ereignis, PR-Nummer, Head, Base,
tatsächlich ausgecheckter Merge-SHA, dessen Tree-SHA und Prüfvertragsversion.
Er entsteht erst nach allen erfolgreichen Pflichtjobs. Keine Testresultate
oder wissenschaftlichen Daten als wiederverwendbaren Ausführungszustand speichern.

Die main-Vorbereitung darf `mode=reuse` erst wählen, wenn sie Folgendes prüft:

- Der Nachweis stammt vom erwarteten Workflow im selben Repository und vom
  eindeutig zugehörigen erfolgreichen PR-Lauf/Attempt. Die tatsächlich
  erforderlichen Jobs sind erfolgreich; kein Entwicklungs- oder Dokumentationslauf.
- Der PR ist nach main gemergt; der dokumentierte Head gehört zu genau diesem
  Merge. Der Push wird eindeutig einem einzelnen solchen Merge zugeordnet.
- `push.before` entspricht der geprüften Basis. Der aktuelle main-Dateibaum
  entspricht dem tatsächlich getesteten Merge-Dateibaum.
- Die Prüfanweisungen und ihre Version stimmen überein. Alte erfolgreiche
  Läufe mit inzwischen verändertem Prüfvertrag berechtigen nicht zur Wiederverwendung.
- Auch im Nachweis müssen alle ausgeführten Jobs zum gleichen geprüften
  Commit und Dateibaum gehören. Metadaten und Artefakt werden gegengeprüft;
  der Inhalt eines beliebigen JSON-Dokuments genügt nicht als Herkunftsbeleg.

Bei passendem Nachweis führt main die schnellen Prüfungen aus. Der Abschluss
benennt ausdrücklich den wiederverwendeten vollständigen Lauf. Jede Unklarheit
führt automatisch zur vollständigen CI: fehlendes oder abgelaufenes Artefakt,
API-Fehler, anderer Tree/Base/Head, Direktpush, Force-Push, mehrere nicht eindeutig
zuordenbare Merges, unvollständiger oder abgebrochener Lauf.

Neue Berechtigungen minimal halten: lesen von Actions-Metadaten und Nachweisen,
gegebenenfalls PR-Metadaten; keine Schreibrechte für Status, Repositoryinhalt oder
Labels. Kein `pull_request_target`-Workflow zur Ausführung von PR-Code.
Kleine Nachweise mit begrenzter Aufbewahrung genügen, beispielsweise sieben Tage;
nach Ablauf wird regulär vollständig geprüft. Sie sind Optimierungshilfe,
kein dauerhaftes wissenschaftliches Ergebnisarchiv.

Abnahme durch Gegenbeispiele zu jeder Bindung und einen passenden Mergefall.
Nicht erlaubte Wiederverwendung muss nachweislich auf volle Prüfung fallen.
Die einmalige volle Einführungskontrolle und ein tatsächlich passender späterer
Merge reichen zur Integration; keine zusätzliche Serie teurer Schein-PRs planen.

## 7. Erwartete Einsparung und Messung

Rechenbeispiel, keine Messung des neuen Verfahrens: acht veröffentlichte
Entwicklungsstände einschließlich PR-Eröffnung, danach Ready und Merge.
Der alte Workflow prüft die acht Entwicklungsstände und main vollständig;
Ready allein löst dort keinen zusätzlichen Lauf aus. Der neue Workflow prüft
acht Entwicklungsstände schnell und startet zusätzlich die Ready-Vollprüfung.

Angenommen 65 Runner-Minuten für den bisherigen parallelen Volltest,
55 für den seriellen Volltest und sechs für den schnellen Codepfad:

| Ablauf | Modellrechnung | Runner-Minuten |
|---|---|---:|
| Bisher | 9 x 65 | 585 |
| Draft-Modus, noch parallel | 8 x 6 + 2 x 65 | 178 |
| Draft-Modus und seriell | 8 x 6 + 2 x 55 | 158 |
| Zusätzlich gültige Main-Wiederverwendung | 8 x 6 + 55 + 6 | 109 |

Draft-Modus allein entspräche etwa 70 %, zusammen mit serieller Ausführung
etwa 73 % und einschließlich Main-Wiederverwendung etwa 81 % Einsparung.
Ein Zwischenpush wäre etwa 90 % günstiger. Bei wenigen Entwicklungspushes
ist der prozentuale Nutzen geringer; zusätzliche notwendige Vollprüfungen
erhöhen den Verbrauch. Ein Sparmodus garantiert keinen festen Monatsverbrauch.

Die nächsten drei ohnehin anstehenden PRs auswerten: Anzahl und Modus der Läufe,
Summe der Jobzeiten, je Job aufgerundete Minuten, abgebrochene Arbeit,
native Startzahl und Gründe zusätzlicher Vollprüfungen. Diese kurzen Befunde
im bestehenden Fortsetzungsstand führen; keinen neuen Messdienst bauen.

## 8. Reserven, falls der Verbrauch weiterhin zu hoch ist

- **Julia-Vorbereitung gezielt optimieren:** Lockdateien, Julia-/Python-Version,
  Betriebssystem/Architektur und gegebenenfalls CPU-Ziel in Cache-Schlüsseln
  berücksichtigen. Frische Worker und die gezielten Isolationstests erhalten.
  Keine Scientific-Outputs, PythonCall-Pfade oder aktiven Sperren blind übernehmen.
- **Eigener Runner auf Manjaro:** Kann gehostete Rechenminuten weiter reduzieren.
  Separates Arbeitsverzeichnis und gepinnte Umgebung, ausschließlich ausdrücklich
  vertrauenswürdige Repository-Aufträge, keine Kollision mit wissenschaftlichen
  Läufen. Dies ist ein eigener Betriebsentscheid; die hiesige vorübergehende
  Codex-Umgebung ist kein dauerhaft verfügbarer GitHub-Runner.

Keine pauschalen `[skip ci]`-Anweisungen für Codeänderungen, keine kleineren
wissenschaftlichen Budgets oder lockereren Toleranzen zur Kostensenkung.
Reine Prosa-PRs bleiben günstig; ein Prosa-Nachtrag im Code-PR wird im ersten
Schritt nicht automatisch als Ersatz für die vollständige PR-Prüfung behandelt.

## 9. Implementierungsauftrag für den nächsten PR

Nur Abschnitt 4 einschließlich der Abnahme aus Abschnitt 5 umsetzen.
Aktuellen Repository-Stand prüfen, Draft-PR mit den zwei beschriebenen Commits
verwenden, bestehende fachliche Prüfkommandos erhalten. Review und lokale Tests
vor der abschließenden Ready-Prüfung bündeln. Abschnitt 6 als Folgearbeit dokumentieren, nicht
unbemerkt in denselben Umbau aufnehmen. Keine Abrechnungs- oder
Repository-Einstellungen ohne entsprechenden Auftrag verändern.

## Quellen

- [Aktueller untersuchter Workflow](https://github.com/craexxn/ringdown-sr/blob/e09ab286fc853fe2991f070c4d96d9f070b55d9d/.github/workflows/technical-checks.yml)
- [Bestehende CI-Dokumentation](ci.md)
- [GitHub: Workflow-Ereignisse](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)
- [GitHub: übersprungene Jobs und Status](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions)
- [GitHub: Branchschutz und erforderliche Checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [OpenAI: Code Review](https://learn.chatgpt.com/docs/code-review)
- [OpenAI: Codex Cloud](https://help.openai.com/en/articles/20001545-using-codex-cloud)
