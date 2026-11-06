# Frühe rauschfreie Serien: ergänzende Quellenprüfung

Lesender Abgleich vom 06.11.2026, [Leitfadenphase 1](ringdown_recovery_roadmap.md).
Die nachgereichten Pakete schließen die bisherige Quellenlücke der
[rauschfreien Kontrollserie](noiseless_control_results_manjaro_001.md) und des
[freien Optimiererbudgetvergleichs](free_optimizer_budget_results_manjaro_001.md).
Diese historischen Berichte und ihre eingefrorenen Pläne bleiben unverändert.
Die damaligen Aussagen über fehlende Originaldateien beschreiben ihren damaligen
Prüfstand; der folgende Nachweis ergänzt sie, ohne Ergebnisse neu auszuwählen.

## Pakete und tatsächliche Herkunft

| Serie | Empfangene Datei / SHA-256 | Archivgebundener Ausführungscommit |
| --- | --- | --- |
| Rauschfreie Kontrolle | `noiseless-control-001.zip`; `03a759608c41913d3e18715dd344ef9e26860b75ebc3fae50191343dae92300b` | `bc80b4f07773ffb6d57a927ef3daaee34f9a7817` |
| Freier Budgetvergleich | `free-budget-manjaro-001.tar.gz`; `77fb34ff6ee139c1f2e0fbbb6acd81d7c1623cd6e8090056f641961e887ad33f` | `8bdc8dbc498be6e8527fa2a857293bf74b42f81f` |

Beide Hashes wurden selbst berechnet. Der Free-Budget-Hash entspricht genau dem
früher übermittelten Originalhash. Der ZIP-Hash identifiziert das jetzt empfangene
Paket; eine frühere Verpackung oder deren Hash wird damit nicht nachgewiesen.
Die gespeicherte Herkunft belegt jeweils einen sauberen Checkout des genannten
Commits. Git-Dateibytes, Pythonquellen und Abhängigkeitspins stimmen mit den
gebundenen Metadaten überein. Die Manjaro-/Haswell-Umgebungsbelege wurden lesend
geprüft; gespeicherte Konsistenz ist kein externer Authentizitätsnachweis.

## Tatsächlich ausgeführte Prüfung

| Umfang | Rauschfreie Kontrolle | Freier Budgetvergleich |
| --- | ---: | ---: |
| Dateien / Einträge des vollständigen Abschlussmanifests | 172 / 171 | 158 / 157 |
| Im Bericht gebundene Quelldateien | 30 | 50 |
| Gegen Git geprüfte unterschiedliche Commit-/Dateibindungen einschließlich Plan | 33 | 51 |
| Vollständig geprüfte Zellen / gespeicherte Frontkandidaten | 9 / 28 | 6 / 50 |
| Gespeicherter Abschluss | `completed` | `completed`, `final_verification=passed` |

Verwendet wurden die Python-Elternverifikatoren der tatsächlichen historischen
Ausführungscommits, mit gesperrtem Such-/Workeraufruf. Geprüft wurden vollständige
Manifeste, Eingaberollen und Float64-Bits, Quellen und tatsächliche
Worker-/Adapterherkunft, gespeicherte Bibliotheksschnappschüsse, effektive
Optionen, native Optionsbelege, Originalauswahl, Exportbäume, Vorhersagen,
Trainingsverluste und die vollständigen damaligen Kandidatendiagnosen.
Beim Budgetvergleich kamen die gespeicherten Vorbereitungs- und Referenzbelege
hinzu. Fehlende historische Git-Objekte wurden nachgeladen, keine Bindung
gelockert. Beide Plankopien stimmen mit ihrem eingefrorenen Commit/Hash überein.

Alle Kandidatendiagnosen stimmen mit den gespeicherten Berichten überein.
`report.json` und `summary.md` wurden für beide Serien in getrennten
Auditverzeichnissen bytegleich regeneriert. Empfangene Dateien und entpackte
Originale blieben unverändert. Keine neue Suche, kein Fit, kein Julia-/PySR-Start
und kein neuer nativer Replay; insbesondere wurden weder Pickles noch archivierte
Programme ausgeführt. Die historischen Bewertungsregeln wurden unverändert
verwendet, keine nachträgliche R1–R3-Anwendung vorgenommen.

## Bestätigte Befunde und Kosten

Die rauschfreie Serie hat neun erfolglose Originalauswahlen, je 0/3 bei
10, 50 und 200 äußeren Iterationen. Alle 28 Frontkandidaten verfehlen die
damaligen Kurvengrenzen. Im freien Budgetvergleich bleiben beide lokalen Profile
20/2 und 100/2 bei 0/3; auch alle 50 Frontkandidaten verfehlen die Kurvengrenzen.
Die Parameterstatus bleiben `not_assessed`. Diese Zahlen beschreiben zwei
gezielte Entwicklungsserien, keine gepoolte allgemeine Erfolgswahrscheinlichkeit.

| Aufgezeichneter Aufwand | Rauschfreie Kontrolle | Freier Budgetvergleich |
| --- | ---: | ---: |
| Summe Fit einschließlich JIT und Python-Exporten | 266,866817 s | 198,383718 s |
| Summe Worker-Vorbereitung | 51,396626 s | 47,591349 s |
| Summe vom Elternprozess gemessener Workerzeiten | Nicht separat aufgezeichnet | 267,665210 s |
| Verlustcallback-Aufrufe während Fit | 1.881.687 | 3.369.138 |
| Monotone Serienzeit | Nicht aufgezeichnet | 292,774208 s bis zum Beginn der abschließenden Veröffentlichung |

Callbackwerte stammen aus den manifestgebundenen `result.json`-Dateien; sie
wurden nicht nativ neu gemessen. Der zusätzliche Backend-Evaluationszähler
bleibt jeweils unavailable. Zeiten sind überlappende Messbereiche und werden
nicht addiert; Callback-Aufrufe zählen keine verschiedenen Formeln. Bei der
rauschfreien Serie stehen UTC-Start/Ende 28.10.2026 11:02:01,364268 bis
11:08:09,715429, beim Budgetvergleich 02.11.2026 05:35:13,135190 bis
05:40:05,803379 im Bericht. Diese Zeitstempel ersetzen keine monotone Gesamtmessung.

Der negative Kurvenbefund ist damit an Primärdateien bestätigt. Daraus folgt
kein erneuter Laufauftrag und keine Änderung der späteren Suchinterventionen.
Ein Strukturtest allein würde diese großen Kurvenfehler nicht beheben.
Das gemeinsame Auditpaket und die weiterhin offenen Sicherungen stehen im
[Ergebnisindex](results_index.md#zusatzdiagnosen-und-offene-sicherung).
