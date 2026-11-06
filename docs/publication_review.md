# Veröffentlichungsprüfung und Lizenzentscheidung

Stand: 06.11.2026. Organisatorischer Folgeauftrag zur Quellen- und Archivpflege
in [Leitfadenphase 1](ringdown_recovery_roadmap.md), getrennt von den laufenden
Suchvorbereitungen in PR #76. Geprüfter Hauptbranch:
`2f9fff00c24a72f644dc42816b6a05aa87e392f0`. Das Repository ist weiterhin privat.
Dieser Befund und die Dateikorrekturen ändern keine GitHub-Einstellung und
erteilen keine Freigabe zur öffentlichen Umstellung.

## Prüfverfahren und Umfang

Die Prüfung umfasst einen vollständigen Abruf der zu diesem Zeitpunkt sichtbaren
Remote-Branches, Tags und PR-Head-Refs, eine musterbasierte Durchsicht ihrer
erreichbaren Gitobjekte und die getrennte Prüfung der GitHub-Oberflächen.
Alle Abrufe und Analysen sind lesend. Lokale Rohdaten der Prüfung liegen außerhalb
des Repositories; persönliche Kontaktwerte oder vermutete Geheimnisse werden
nicht in diesen Bericht kopiert.

| Oberfläche | Selbst geprüfter Umfang |
| --- | --- |
| Git-Refs | 78 Origin-Refs, 76 PR-Head-Refs und ein Tag; 155 Refs im Snapshot |
| Git-Historie | 264 erreichbare Commits, Commit-/Tag-Texte und Metadaten |
| Historische Dateien | 978 unterschiedliche Blobs mit 22.069.114 Bytes; 301 historische Dateipfade |
| Binärdaten | Ein NPZ-Blob mit vier Float64-NPY-Arrays; auch entpackte Mitglieder geprüft |
| PRs und Issues | Alle 76 PR-Beschreibungen, zwei Issuekommentare; keine eigenständigen Issues |
| Reviews | Alle 76 Review-Sammlungen abgefragt; keine Reviews oder Inline-Reviewkommentare vorhanden |
| Releases und Zusatzoberflächen | Keine Releases/Releaseanhänge oder Forks; Wiki, Discussions und Pages deaktiviert |
| Actions-Inventar | 227 Runs, 414 Jobs, sämtliche 227 Artefaktabfragen ohne Artefakte |
| Actions-Logs | 386 abgeschlossene, nicht übersprungene Joblogs angefragt; 367 gelesen, 19 mit HTTP 404 nicht verfügbar |

Weitere 27 Jobs waren übersprungen, ein Job lief beim Inventarabgleich noch.
Die gelesenen Logs umfassen 189.170 Zeilen beziehungsweise 15.741.013 UTF-8-Bytes.
Inventare wurden über alle erforderlichen API-Seiten gelesen. Die einzelne
Artefaktabfrage pro Run war jeweils leer; dort bestand keine weitere Seite.

Die Mustersuche erfasst insbesondere bekannte GitHub-/Cloud-/API-Tokenformate,
private Schlüsselblöcke, Zugangsdaten in URLs und Zuweisungen, unmaskierte
Authentifizierungsheader, Kontakt-E-Mail-Adressen und persönliche Home-Pfade.
Breitere Treffer auf Begriffe wie `token`, `password` und Autorennamen wurden
im Kontext eingeordnet. Testwerte und maskierte GitHub-Header sind keine
nachgewiesenen Zugangsdatenfunde.

Zusätzlich wurde **Gitleaks 8.30.1** mit Standardsatz und vollständiger Redaktion
über die 79 unterschiedlichen Heads dieser 155 Refs ausgeführt: Exit 0,
keine Leaks. Das offizielle Release-Archiv wurde gegen den GitHub-Asset-Digest
und die veröffentlichte SHA-256-Prüfsumme geprüft. Gitleaks erfasste 246 Commits
mit Diffs; die weiteren 18 Commits besitzen in dieser Git-Log-Abfrage keinen
Numstat-Diff. Der ergänzende Blob-/Metadatenscan erfasst alle 264 Commits und
978 Blobs, einschließlich der NPZ-Mitglieder. Diese verschiedenen Zählungen
dürfen nicht als zusätzliche unabhängige Commits addiert werden.

## Konkrete Befunde und Maßnahmen

| Fundstelle | Befund | Maßnahme beziehungsweise Entscheidung |
| --- | --- | --- |
| [README im geprüften Stand, Zeile 450](https://github.com/craexxn/ringdown-sr/blob/2f9fff00c24a72f644dc42816b6a05aa87e392f0/README.md#L450) | Einrichtung setzt ausdrücklich ein privates Repository voraus | Auf Lesezugriff und bedingte Anmeldung für den privaten Stand präzisiert |
| [Archivierungsregel, Zeilen 104–110](https://github.com/craexxn/ringdown-sr/blob/2f9fff00c24a72f644dc42816b6a05aa87e392f0/docs/results_archiving.md#L104) | Releases sind als private Zusatzablage beschrieben | Vererbte Sichtbarkeit und separates privates Sicherungsziel ausdrücklich dokumentiert |
| Repository-Wurzel und erreichbare Historie | Keine bisherige Projektlizenz gefunden | Ausdrücklich gewählte MIT-Lizenz als [LICENSE](../LICENSE) ergänzt |
| [CI-Regeln, Kostenabschnitt](https://github.com/craexxn/ringdown-sr/blob/2f9fff00c24a72f644dc42816b6a05aa87e392f0/docs/ci.md#L121) | Bisherige Kostenabwägung beschreibt private CI | Öffentliche Standard-Runner eingeordnet; historische Messungen und Prüfpflichten erhalten |
| [Beispielcommit aus PR #76](https://github.com/craexxn/ringdown-sr/commit/66ec4238f39edbbc2a71bb4e984571e41531e7ab) | Ausgeschriebener Autorenname in 88 Commits beziehungsweise 176 Autor-/Committerfeldern | Name wird mit öffentlicher Historie sichtbar; derselbe Name wurde ausdrücklich für den Lizenzhinweis gewählt. Keine Historienänderung |
| [Beispiel PR #74](https://github.com/craexxn/ringdown-sr/pull/74) und weitere PR-Beschreibungen | Elf generische `/workspace/`-Pfade, keine persönlichen Home-Pfade | Technische Herkunftshinweise erhalten; kein konkreter Bereinigungsbedarf festgestellt |
| [PR #70](https://github.com/craexxn/ringdown-sr/pull/70), Beschreibungszeile 42 im Snapshot | Historische Aussage zur damaligen privaten Sichtbarkeit | Als damaligen Zustand erhalten; keine Umschreibung historischer Berichte |
| [Main-Branchstatus](https://github.com/craexxn/ringdown-sr/branches) und [bestehender CI-Befund](ci.md) | `protected:false`, keine verpflichtenden Statuschecks beim Abgleich | Einstellungen separat prüfen und `technical-checks` als erforderlichen Abschlusscheck einrichten; hier nicht geändert |

Im geprüften Umfang wurden keine konkreten Zugangsdatenfunde identifiziert.
Die gefundenen E-Mail-Adressen in Gitmetadaten sind GitHub-Noreply- oder
reservierte Automationsadressen; weitere Dateitreffer sind reservierte
Testadressen. Es wurden keine persönlichen Kontakt-E-Mail-Adressen oder
persönlichen Home-Pfade festgestellt. Lokale Git-Konfiguration und außerhalb
von Git gespeicherte Dateien sind nicht Teil der öffentlichen Git-Historie.

Keine getrackten `.env`-Dateien, Schlüsseldateien, wissenschaftlichen
Ergebnisarchive, PDFs oder Bilddateien wurden in den untersuchten historischen
Pfaden gefunden. Die Binärdatei
[transfer_check_inputs.npz](../data/transfer_check_inputs.npz) enthält die
erwarteten synthetischen Eingabearrays; ihr Erzeugungsrezept ist in
[transfer_check_inputs.json](../data/transfer_check_inputs.json) dokumentiert.
Die Prüfung der Dateiinhalte ist keine erneute wissenschaftliche Validierung.

## Lizenzentscheidung

Am 06.11.2026 wurde die **MIT-Lizenz** für eigenen Softwarecode und zugehörige
technische Dokumentation ausdrücklich gewählt. Als öffentliche
Urheberbezeichnung wurde der Name aus den vorhandenen Git-Commits bestimmt:
**Copyright (c) 2026 Gregor Hubmann**. Die kanonischen Bedingungen stehen in
[LICENSE](../LICENSE); die [README](../README.md#lizenz) grenzt den Umfang ab.

MIT erlaubt auch kommerzielle und geschlossene Weiterverwendung unter Erhalt
des Lizenzhinweises. Erwogen wurden Apache-2.0 mit ausdrücklicher Patentlizenz
und GPL-3.0 mit Copyleft bei Weitergabe abgeleiteter Software. Eine zusätzliche
CC-Lizenz wurde nicht eingeführt. Die separat verfasste Masterarbeit wird
dadurch nicht automatisch lizenziert.

Im aktuellen Bestand von 289 getrackten Dateien wurden keine gebündelten
Fremdbibliotheken oder vollständigen externen Publikationen identifiziert.
Gezielte Suchen nach Lizenz-, Copyright- und Übernahmevermerken ergaben keine
konkrete entgegenstehende Fremdlizenz für die eigenen Repository-Inhalte.
Die Julia-Instrumentierung verwendet Backend-APIs, etwa
`SymbolicRegression.optimize_constants` in
[ConstantDiagnostic.jl](../julia/src/ConstantDiagnostic.jl); das ist von einer
Übernahme des Backend-Quellcodes zu unterscheiden.

Die Projektlizenz lizenziert Abhängigkeiten nicht um. Beispielsweise stehen
[PySR 2.6.0](https://github.com/astroautomata/PySR/blob/v2.6.0/LICENSE) und
[SymbolicRegression 2.5.1](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/LICENSE)
unter Apache-2.0; [gmpy2 2.2.2](https://pypi.org/project/gmpy2/2.2.2/)
führt LGPLv3 oder später. Unmarkierte Fremdübernahmen lassen sich durch die
gezielte Suche nicht ausschließen; eine vollständige transitive Lizenzinventur
wurde nicht durchgeführt. Nachnutzung der Abhängigkeiten bleibt an deren
jeweilige Bedingungen gebunden.

## Grenzen und verbleibende Schritte vor einer Umstellung

Dies ist eine muster- und kontextbasierte Veröffentlichungsprüfung, keine
Garantie der Abwesenheit jedes Geheimnisses und keine vollständige Rechteprüfung.
Unbekannte Tokenformate, nicht erreichbare Gitobjekte, gelöschte oder frühere
Versionen von GitHub-Kommentaren und nicht abrufbare Logs sind nicht abgedeckt.
Die 19 mit HTTP 404 antwortenden Joblogs gelten als **nicht geprüft**, nicht als
inhaltlich unbedenklich. Betroffen sind folgende Job-IDs; jede Zeile verlinkt
den zugehörigen Run:

| Run | Nicht abrufbare Job-IDs |
| --- | --- |
| [42196022394](https://github.com/craexxn/ringdown-sr/actions/runs/42196022394) | 127820040081 |
| [42185332349](https://github.com/craexxn/ringdown-sr/actions/runs/42185332349) | 127784797618 |
| [42166460960](https://github.com/craexxn/ringdown-sr/actions/runs/42166460960) | 127724473428 |
| [42101046773](https://github.com/craexxn/ringdown-sr/actions/runs/42101046773) | 127504763223 |
| [42100134546](https://github.com/craexxn/ringdown-sr/actions/runs/42100134546) | 127503812503 |
| [42090691230](https://github.com/craexxn/ringdown-sr/actions/runs/42090691230) | 127468482430 |
| [42083525019](https://github.com/craexxn/ringdown-sr/actions/runs/42083525019) | 127443406368, 127443406425, 127443406445 |
| [42065214478](https://github.com/craexxn/ringdown-sr/actions/runs/42065214478) | 127379111586, 127379111934, 127379112100 |
| [42016769203](https://github.com/craexxn/ringdown-sr/actions/runs/42016769203) | 127212278598, 127212278741, 127212278948 |
| [42016521232](https://github.com/craexxn/ringdown-sr/actions/runs/42016521232) | 127209636681, 127209637348, 127209638103 |
| [41817417246](https://github.com/craexxn/ringdown-sr/actions/runs/41817417246) | 126531604986 |

Beim Inventarabgleich lief außerdem
[Job 127820119244](https://github.com/craexxn/ringdown-sr/actions/runs/42196112043/job/127820119244)
noch; sein späterer Abschluss und nachfolgende Jobs gehören zum Deltaabgleich.

Vor einer tatsächlichen Umstellung:

1. Den Dateivorbereitungs-PR technisch abschließen und ausdrücklich übernehmen.
   Die neue Root-Datei `LICENSE` verlangt nach der unveränderten
   [Scope-Regel](ci.md) die vollständige CI; keine Prüfumgehung durch diesen PR.
2. Seit dem Snapshot neu entstandene Commits, PR-Texte, Logs und Anhänge
   nachprüfen. Insbesondere PR #76 und der eigene Vorbereitungs-PR ändern
   sich weiter. Nicht abrufbare Nachweise bei erneutem Zugriff nachprüfen;
   bleibende Lücken bei der Freigabe ausdrücklich berücksichtigen.
3. Branchschutz, erforderlichen Abschlusscheck und Freigaben für Actions aus
   fremden Forks in den Repository-Einstellungen festlegen. Der aktuelle
   Workflow verwendet `pull_request`, `contents: read`, SHA-gepinnte Actions
   und `persist-credentials: false`; keine selbst gehosteten Runner oder
   Artefaktuploads. Das ist eine Sichtprüfung, kein vollständiger Workflow-Audit.
4. Erst mit gesonderter Freigabe die Sichtbarkeit umstellen und danach Zugriff
   sowie Schutzregeln prüfen. Öffentlich gewordene Kopien und Forks lassen
   sich durch einen späteren Privatwechsel nicht zurückholen.

Es werden weder Releases hochgeladen noch alte Logs, Diskussionen oder
Gitobjekte gelöscht. Ein bloßes Löschen heutiger Dateien würde ältere Versionen
nicht entfernen. Ohne konkreten Befund ist keine Historienbereinigung begründet;
sie würde wissenschaftliche Commit- und Quellenbindungen berühren.

Primärquellen: [Sichtbarkeitsänderungen](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility),
[Lizenzierung](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository),
[Actions-Abrechnung](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
und [Fork-Freigaben](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks).
