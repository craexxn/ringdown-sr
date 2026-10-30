# Fortsetzungsstand: Zeitdarstellungs-Kontrolle

Stand: 30.10.2026. Implementierung, gezieltes Review und die geplante
Manjaro-Kontrollserie sind abgeschlossen. Das vollständige Originalarchiv
wurde hier unabhängig nachgerechnet; der neue Entwicklungsbefund steht im
[Ergebnisprotokoll](representation_control_results_manjaro_001.md).

## Aktueller Fortsetzungsstand nach der Kontrollserie

### Angenommene Diagnose A: implementierter Kontrollpfad

Der Nutzer hat den Reviewvorschlag am 30.10.2026 ausdrücklich angenommen und
seine Umsetzung beauftragt. PR #41 ist inzwischen als `978738c38e36e7bcb82c83acb5ba85db6df078f0`
gemergt; Remote-Branches, offene PRs, sauberer Checkout und ein Worktree geprüft.
Neuer Branch `codex/ringdown-constant-diagnostic` ab diesem Merge, kein weiterer
Implementierungsbranch oder offener PR beim Einstieg.

Der [neue eingefrorene Plan](constant_diagnostic_plan.md) übernimmt Option A:
48 Backendaufrufe, acht Starts, drei Seeds, 20/2 gegen 100/2, 60 Minuten.
Die wissenschaftliche Serie bleibt für den geprüften Manjaro-Stand vorgesehen.
Plan und erster Diagnoseentwurf sind in `f568902` remote gesichert;
den aktuellen Head mit `git rev-parse HEAD` bestimmen. Python-/Julia-Umgebung erneut
erfolgreich geprüft: Python 3.12.14, Julia 1.13.1, PySR 2.6.0,
SymbolicRegression 2.5.1 und PythonCall 0.9.36, Interpreter und Erweiterung.
Beschreibbare Cachepfade und tatsächlich vorhandene Python-Bibliothek bestätigt.

Implementiert: isolierter Launcher, absolute Options-/Plugin-/Seed- und
Xoshiro-Prüfung, zehn vorgeschaltete Kontrollen, 48 feste Aufrufe, binäre
Eingabeherkunft aus dem fest gehashten Archiv, beobachtender Callback, getrennte
Fit-/Gesamtzähler und vollständiger Export. Paarunterschiede erhalten beide
Parameterstatus; nicht beurteilbare Parameter werden nicht differenziert.
Abschlussabweichungen sperren sämtliche Gruppen-/Paaraussagen; Teilstände bleiben
erhalten. [Bedienung und Manjaro-Befehl](constant_diagnostic.md).

Lokale Prüfnachweise:

- Vollständiger Pythonlauf: 1.328 Tests bestanden. Danach ausschließlich
  Paarbericht und Prozesswandzeit ergänzt und fokussierte Tests erneut geprüft.
- `results/constant-technical-003.json`: zehn reine Kontrollen, vier direkte
  Optimierungen am eigenen Achtpunkt-Fixture und zwei echte isolierte technische
  Worker bestanden. Unabhängiger Export-/Residuen-/MSE-Replay und alle 68
  effektiven Felder pro Worker geprüft. Mit/ohne Beobachtung gleiche Parameter,
  Verluste, Callbackzahlen und RNG-Zustände für beide Budgets.
- Nach diesem nativen Lauf nur Paarbericht/Prozesswandzeit und Dokumentation
  ergänzt; der native Pfad blieb gleich. Der vollständige CI-Lauf am endgültigen
  PR-Head prüft auch den aktuellen Quellenstand dieses technischen Checks.
- Ruff, Formatierung, Dokumentations-/Link- und Diffprüfung bestanden.
  Alter und neuer eingefrorener Kontrollplan unverändert; der neue Diagnoseplan
  ist ausdrücklich als Laufzeitdokument mit voller CI erfasst.
- Originalarchiv mit dem neuen Leser identitätsgeprüft und ohne Extraktion
  gelesen: 128 Trainings- und 889 Diagnosedaten, 48 geplante Anfragen.

Keine der 48 wissenschaftlichen Zellen oder freie Suchen im Rahmen dieser
Diagnoseimplementierung ausgeführt. Die vollständige technische CI kann die
bisherigen kleinen freien CI-Kontrollen ausführen; diese sind keine neue
wissenschaftliche Serie. Nächster Schritt: Implementierungs-PR mit voller CI
abschließen, danach auf geprüftem Stand die Manjaro-Diagnose ausführen.

### Gesicherter vorheriger Ergebnisstand

- Beim Einstieg `main` auf `97672ed` (übernommener Dokumentationsnachtrag
  aus PR #40), keine offenen PRs und sauberer lokaler Checkout. Neuer
  Ergebnisbranch `codex/representation-control-results`, Basis `97672ed`.
  Der genaue Dokumentationshead ergibt sich aus `git rev-parse HEAD`.
- Ausführungscommit weiterhin `4057caaffd9c4de5791ded14431c6e289db75b73`;
  im Originalarchiv mit sauberem Git-Zustand protokolliert. Keine Änderung
  der wissenschaftlichen Vorgaben oder der 41 konsumierten Quelldateien.
- Vom Nutzer übermitteltes Originalarchiv `representation-manjaro-001.tar.gz`,
  SHA-256 selbst bestätigt:
  `a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
- Archiv vollständig gelesen: 219 Dateien, davon 218 im Artefaktmanifest;
  sämtliche Datei-, Quell-, Worker-, Eingabe- und Planprüfsummen bestätigt.
  Alle neun Zellen `completed`, Abschlussprüfung `passed`.
- 57 Kandidaten mit sämtlichen Originalindizes, Vorhersagen, Residuen und
  MSE nachgerechnet; beide Raster zusätzlich mit unabhängig geschriebenem
  Bauminterpreter und `math.fsum` ausgewertet. Vorprüfungsobjekte, konkrete
  Pluginfelder, Seeds und Haswell-Aufnahmen erneut abgeglichen. Gruppen-
  statistiken und sechs Seed-Paare reproduziert. Keine Originaldatei verändert.
- Ergebnis: Häufigkeitsschalter verbessern die Trainings-MSE bei 3/3 Seeds
  um rund 90–97 %; Zeitstreckung hilft beim Training bei 2/3 Seeds und kann
  auf Zwischenpunkten deutliche Spitzenfehler erzeugen. Alle 57 Kandidaten
  verfehlen die Kurvengrenzen; alle Strukturen `not_supported`, Parameter
  `not_assessed`. Der komplette Auditumfang und alle Zahlen stehen im Befund.
- In diesem Auswertungsschritt keine neue Suche, kein Fit und kein Julia-Lauf.
  Die hier abgeglichenen nativen Backendnachweise sind archivierte Aufnahmen.
  Ergebnisnachtrag ausschließlich als Dokumentation; vollständige CI und
  Review werden ohne Codeänderung nicht erneut ausgeführt.


## Historischer Entscheidungsstand nach übermitteltem Review

Auf Nutzerauftrag ist die [Entscheidungsgrundlage samt vollständigem
Review-Prompt](representation_next_step_review.md) im bestehenden Ergebnisbranch
und PR #41 ergänzt. Gesicherter Ergebnisstand vor dieser Ergänzung:
`73e1c6748fb6683b99336d81271f332e60034d9f`; Vergleichsbasis
`97672ed9b14b81ca90663dc178072b515ee252bc`.

Der Nutzer hat das KI-basierte Methodenreview zu PR #41 übermittelt:
gelesener Head `1c816e5e40b16a0fd03b268df24cf869d6a33a57`, Vergleichsbasis
`97672ed9b14b81ca90663dc178072b515ee252bc`. Der vollständige Befund steht
mit Herkunft und Prüfgrenzen in der bestehenden
[Entscheidungsgrundlage](representation_next_step_review.md#übermittelter-ki-basierter-reviewbefund).
Er empfiehlt Option A und berichtet keine entscheidungsblockierende
Unstimmigkeit in der beschriebenen Optimiererlücke.

Vorgeschlagen sind eine feste Vierkonstantenstruktur, acht Starts, drei
RNG-Initialisierungen, 20/2 und 100/2 sowie 60 Minuten Gesamtwandzeit:
48 Backendaufrufe, höchstens 144 lokale Optimierungen, freies Suchbudget null.
Die konkreten Starts, Kontrollen, Auswertung und Weiterentscheidungen stehen im
übermittelten Entwurf. Diese Zahlen und Diagnoseprivilegien sind noch nicht
vom Nutzer beschlossen; es gibt weder eine neue Implementierung noch Ergebnisse.

Prüfgrenze des übermittelten Reviews: Quellen und dokumentierte Zahlen gelesen;
kein eigener Originalarchiv-Audit, keine Tests, Fits, Optimierungen oder Suchen.
Diese Aussagen sind übermittelte Nachweise und wurden bei der Übernahme nicht
neu ausgeführt. Der vorherige eigene Archivaudit bleibt davon getrennt.

Beim Einstieg zu diesem Nachtrag: sauberer Checkout und ein Worktree auf
`codex/representation-control-results` am gelesenen Head; Remote-Branches und
PRs abgeglichen, PR #41 weiterhin offen, `main` unverändert auf `97672ed`.
Die [Dokumentations-CI des gelesenen Heads](https://github.com/craexxn/ringdown-sr/actions/runs/41054721398)
bestand. Dieser Nachtrag aktualisiert ausschließlich README, Entscheidungs-
und Fortsetzungsdokument; seinen genauen Head mit `git rev-parse HEAD` bestimmen.
Lokal bestanden: Dokumentations-/Linkprüfung für 36 Markdown-Dateien und
`git diff --check`; Wortlaut des Zitats gegen die Eingabe abgeglichen,
schlanken CI-Umfang und beide unveränderten Planprüfsummen bestätigt.
Der neue CI-Status gehört zum neuen Head in PR #41.

Nächster abgegrenzter Schritt: Nutzerentscheidung über den konkreten Vorschlag.
Bei Annahme einen eigenen eingefrorenen Methodenplan und einen technisch
geprüften Diagnosepfad erarbeiten. Keine automatische weitere Reviewrunde,
keine neuen numerischen Läufe und kein eigenständiger Merge.

## Vorheriger Fortsetzungsstand nach Merge und Review

- PR #39 ist auf `main` übernommen, Mergecommit und fester Ausführungsstand:
  `4057caaffd9c4de5791ded14431c6e289db75b73`.
- Geprüfter PR-Head: `cfe44bfb84baef9238f52609ba1030eaa4416ed7`;
  Vergleichsbasis: `909942d3f3910ea20df1703dd12421abe4867a4e`.
  PR-Metadaten und Remote-Branches erneut gelesen. Beim Einstieg keine
  offenen PRs, sauberer lokaler Checkout und ein Worktree.
- Dateibaum des Mergecommits und des geprüften Heads identisch:
  Git-Tree `c85720ff579f75ee6af3849b593ad0dfdf371f7d`.
  Die [vollständige CI](https://github.com/craexxn/ringdown-sr/actions/runs/41038219843)
  ist am PR-Head erfolgreich abgeschlossen; GitHub-Status erneut abgefragt.
  1.288 Python-Tests, 295 Julia-Prüfungen, Residuen-/Optimierer-Replays,
  native Profil-/Koordinaten-/Aliasprüfung und bestehende Integrationen
  bestanden. Keine vollständige Wiederholung zur Statuspflege.
- Dokumentationsnachtrag auf `codex/representation-manjaro-handoff`, Basis
  der oben genannte Mergecommit. Exakten Dokumentationshead beim Fortsetzen
  mit `git rev-parse HEAD` bestimmen. Dieser Nachtrag verändert keinen Code,
  Laufzeitplan oder konsumierten Suchinput. Die wissenschaftliche Ausführung
  verwendet weiterhin den festgelegten Mergecommit.

### Übermittelter KI-basierter Reviewbefund

Der Nutzer hat ein gezieltes KI-basiertes Review zu PR #39 am oben genannten
Head gegen die oben genannte Basis übermittelt. Ergebnis: **keine
korrekturbedürftigen Befunde zur beauftragten Methodentreue**; keine zusätzliche
gezielte Gegenprüfung erforderlich. Geprüft wurden alle 19 geänderten Dateien
und relevante unveränderte Aufrufer/Abhängigkeiten nach Repositoryregeln:
Zeitumrechnung und vollständige Baumauswertung, Originalauswahl, absolute
Seed-/Pluginprüfung ab der ersten Zelle sowie die Auswertungssperre.

Als selbst ausgeführte Prüfungen des Reviews wurden übermittelt:

- 210 gezielte Python-Tests und der gepinnte Python-/Julia-Umgebungscheck.
- Neun echte Optionsobjekte mit je 68 Feldern und neun native Referenzfälle
  einschließlich Einheiten-, Alias- und falscher-Seed-Gegenprüfung.
- 18 unabhängige Frequenz-/Vorzeichen-/Phasenfälle sowie zwei zusätzliche
  Gegenprüfungen zu Originalindex und später Manipulation.
- Ruff, Format-, Dokumentations- und Diffprüfungen sowie Planprüfsummen.

Diese Reviewprüfungen wurden in diesem Fortsetzungsschritt übernommen und
nicht erneut ausgeführt. Der Reviewbefund ist kein Ergebnis wissenschaftlicher
Kontrollsuchen. Insbesondere entspricht die Auswertbarkeit vollständig
geprüfter anderer Gruppen/Paare nach einem zelllokalen Abbruch bei bestandener
Abschlussprüfung dem eingefrorenen Plan.


## Historischer Implementierungseinstieg und verbindliche Grundlage

- Repository `craexxn/ringdown-sr`, Branch `codex/representation-control`.
- Einstieg dieses Cloudauftrags auf geprüftem Remote-Head
  `9c18af2ca6b761eb0ed2e0d8375aaab1dfe484e4`; keine offenen PRs,
  sauberer Checkout, ein Worktree. Gegenüber `0cf7ff1` nur Statusnachtrag.
- `main` auf `909942d3f3910ea20df1703dd12421abe4867a4e` geprüft und
  integriert: ausschließlich organisatorische Änderungen aus PR #38.
  Die volle CI-Ausnahme für beide Laufzeitpläne bleibt erhalten.
- Basis des Methodenplans: `311f87d2df9e47d3e326f24709b8085569f7b5f3`
  (PR #37). [Plan](search_representation_plan.md), unveränderter SHA-256:
  `16cfe818c312fb5bb0a6c594505ad76ba41e41bd7f4a37decc245677c6b8ad86`.
  Auch der alte Plan und seine Prüfsumme bleiben unverändert.
- Veröffentlichter fachlicher Head vor diesem abschließenden
  Dokumentationscheckpoint: `b4db89d6baa8c8c0e914f82f9b46727cc49b2b4f`.
  Arbeitsverzeichnis sauber; Code und Zwischenstände sind remote gesichert.
- Die ursprünglichen lokalen Commits bleiben unter
  `codex/representation-control-local-checkpoints-20261030` erhalten.
  GitHub hatte ihre Pushes wegen der voreingestellten privaten Commit-E-Mail
  abgelehnt. Inhaltsgleiche eigene Commits wurden mit der bereits im Repository
  verwendeten GitHub-Noreply-Adresse veröffentlicht: `2345cb2` entspricht
  `cbc95ca`, `27bc91a` entspricht `d9c3c62`, `b4d60fd` entspricht `b4db89d`.
  Identische Git-Bäume geprüft. Remote-Update von `9c18af2` erfolgte als
  Fast-forward; kein Force-Push und keine Änderung bestehender Remotecommits.


## Implementiert

- Diagnosekern `representation_control.py`: neun feste Zellen,
  schreibgeschützte Koordinaten, getrennte Such-/physikalische Diagnose,
  Replays, Bedingungsstatistik und Differenzen zur frischen Baseline je Seed.
- Begrenzte Profile, absolute Pluginfeldprüfung und native Guard um den
  bestehenden numerischen Callback; allgemeine Suchpfade unverändert.
- `run_representation_control.py`: isolierter Launcher, Options- und
  Referenzvorprüfung, Manifest-/Quell-/Daten-/Workerverifikation, alle
  Kandidaten/Originalauswahl, sichere Teilberichte und abschließende Sperre
  sämtlicher Zusammenfassungen/Differenzen bei Verifikationsfehlern.
- Manifest prüft auch Profil-/Verifikationsdateien, native Quellen und
  Laufzeitkopien. `_candidate` erhält Suchzeiten und `FS/alpha`.
  Fit-Callbackzahlen bleiben vom Gesamtzähler einschließlich der zusätzlichen
  Nullkurvenauswertung getrennt.
- 75 neue Treiberfälle mit konsistent neu gehashten Fälschungen bereits in
  der ersten Zelle, Abbruch-/Teilständen und späten Dateimanipulationen.
- Echte Backend-Referenzprüfung für 250, 4346 und 33018 Hz in allen drei
  Bedingungen; Einheiten und native Seed-Guard. Keine Fit-/Suchaufrufe.
- Technischer Integrationseinstieg: drei frische Profilworker an `y=1+t`,
  je zwei Iterationen. Dieses gesonderte Prüfprogramm ändert nicht das
  wissenschaftliche Budget. In vollständige CI eingebunden.
- [Bedienungsdokumentation](representation_control.md) einschließlich
  späterer Manjaro-Befehle und lokalem Cloud-Startprofil.

## In dieser Cloudinstanz selbst ausgeführt

- Gesperrte Installation und Umgebungscheck: Python 3.12.14, PySR 2.6.0,
  Julia 1.13.1, SymbolicRegression 2.5.1, PythonCall 0.9.36;
  Interpreterbindung und geladene Erweiterung bestätigt.
- Beschreibbare Cache-/Depotpfade geprüft. Nicht versionierte lokale Startdatei
  `/workspace/ringdown-cloud-env.sh` setzt die vorgegebenen sechs Variablen
  und `JULIA_PYTHONCALL_LIB`, ermittelt aus dem tatsächlichen gepinnten
  Projektinterpreter mit Existenzprüfung. Jeder Projektbefehl lädt sie.
  Haswell/Threadlimit 1 nur für die vorgesehenen Kontrollen.
- 86 ursprüngliche fokussierte Tests bestanden; danach 48 Pluginfälle
  ergänzt, insgesamt 134 fokussierte Fälle bestanden am Checkpoint `2345cb2`.
- Optionsvorprüfung: neun echte Objekte, null Callbackaufrufe, kein Fit.
  Callbackdarstellung und konkrete Plugins sowie 29 gemeinsame absolute
  Verträge bestätigt. Geladene NumPy-/SciPy-/Julia-Pools: Haswell, Limit 1.
  Lokales Artefakt `results/representation-options-001.json`.
- Neun echte feste Referenzfälle bestanden: native Verlustauswertung,
  unabhängige Residuen-MSE, 11 Knoten, Parameter-/Aliasrückrechnung und
  Einheiten. Lokales Artefakt `results/representation-references-001.json`.
- Erster vollständiger Python-Lauf des Treiberentwurfs: **1287 Tests bestanden**
  in 85,59 s. Davon 75 neue Treiberfälle. Keine Julia-Tests in dieser Zahl.
- Technischer Integrationsversuch `results/representation-integration-001`:
  Vorprüfungen bestanden, erster Profilworker ausgeführt und exportiert;
  anschließender vollständiger Optionsvergleich hat korrekt gestoppt.
  Die nackten Julia-Optionsprototypen hatten drei andere Defaults als PySR:
  `input_stream`, `should_simplify`, `define_helper_functions`.
  Gepinnte Quelle PySR 2.6.0 `sr.py`, Konstruktor und Optionsübergabe, geprüft.
  Nur die Prototypen wurden an die unveränderte PySR-Suche angepasst:
  `devnull`, `true`, `false`. Kein Feld wurde aus der Prüfung entfernt.
  Der begründete Folgelauf
  `results/representation-integration-002` am sauberen lokalen Commit
  `27bc91a` ist **vollständig bestanden**: neun Optionsobjekte, neun native
  Referenzfälle und alle drei frischen technischen Profilworker; sämtliche
  68 Optionsfelder entsprechen der Vorprüfung (Ausgabepfad separat).
- Zwei gleichzeitige Starts mit fremder aktiver CondaPkg-Sperre bestanden;
  die Sperre blieb unverändert, keine Conda-Umgebung entstand.
- Abschließend Einzelstatus für beide Seiten jeder Fehlerdifferenz ergänzt.
  Ein endlicher Wert mit unbestimmter Diagnose bleibt unauswertbar;
  zugehöriger Gegenfall ergänzt. 210 fokussierte Tests bestanden.
  Ruff, Formatierung, lokale Links und `git diff --check` bestanden.

## Offen und nächster abgegrenzter Schritt

1. Implementierungs-PR der angenommenen Diagnose A vollständig technisch prüfen;
   Head, Basis und CI-Nachweis dort festhalten. Kein eigenständiger Merge.
2. Nach Prüfung die 48 Aufrufe einmalig auf Manjaro gemäß dem neuen Plan
   ausführen und das vollständige Ergebnisarchiv zur Nachrechnung sichern.
3. Erst anhand dieses Befunds über die nächste Forschungsetappe entscheiden.
   Keine routinemäßige weitere Reviewrunde oder automatische Budgeterweiterung.

Der Plan und beide Laufzeitplanprüfsummen sind unverändert. Keine zusätzlichen
wissenschaftlichen Suchen in der Cloud und keine automatische Wiederholung.
Der Alias-Blindfleck bei `8*fs` bleibt ausdrücklich bestehen.

## Historische Nachweise

Der gesonderte Diagnose-/CI-Kern `91f95e2` war mit 64 Tests geprüft.
Vor dem früheren Umgebungsausfall bestanden 86 fokussierte Pythonfälle,
aber nicht für den exakten wiederhergestellten Head `0cf7ff1`.
Die damaligen Aussagen zur nicht erreichbaren Umgebung in `0cf7ff1` und
`9c18af2` beschrieben die jeweiligen Sicherungszeitpunkte; die aktuelle
Cloudbereitschaft wurde oben neu geprüft. Die früher übermittelten
Cloudnachweise am fremden Stand `60798c8` sind keine Prüfnachweise für
diesen Implementierungsbranch und werden nicht übernommen.
