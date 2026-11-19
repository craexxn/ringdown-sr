# Entwicklungsabnahme: Hintergrunddauer und Messraster

Stand 19.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md),
[PR #102](https://github.com/craexxn/ringdown-sr/pull/102).
Die wissenschaftliche 624-Worker-Serie ist **nicht ausgeführt**.
Dieser Bericht trennt die eigene Schätzerdiagnose und den kurzen technischen
Vorlauf von den späteren gepaarten Suchvergleichen.

## Quellen und Umfang

Der [Versuchsplan](noise_followup_plan.md) und die Seedtabelle sind an
`a37bf90fe439619fd263d6c06d868c6ff4ea00e8` gebunden. Beide bleiben unverändert.
Die hier bezeichneten Originalausgaben `noise-followup-estimators-cloud-001`
und `noise-followup-preflight-cloud-001` wurden am sauberen Ausführungscommit
`34ef0094d7ae52cbf56f6b012a76451325348444` erzeugt. Python 3.12.14,
Julia 1.13.1, SymbolicRegression 2.5.1 und PythonCall 0.9.36;
Ein-CPU-/Threadvertrag und Haswell-BLAS-Kern wie im Plan.
Vollständige Quellen-, Paket- und Umgebungsbindungen stehen in den Originalen.

Die Cloud-Python-Installation meldet einen nicht vorhandenen ursprünglichen
Bibliotheksordner. Für die native Prüfung wurde deshalb ihre tatsächlich
vorhandene `libpython3.12.so` über `JULIA_PYTHONCALL_LIB` angegeben.
Die anschließende Umgebungsprüfung besteht mit geladenem PythonCall-Adapter;
keine Änderung der Abhängigkeiten oder des Suchprofils. Dieser lokale
Umgebungshinweis ist keine zusätzliche Manjaro-Voraussetzung.

## Schätzerdiagnose 001

Acht korrelierte und vier weiße Entwicklungsfälle, je zwei Dauern und zwei
vorab festgelegte Verfahren: **48/48 berechnet, kein Schätzausfall, keine
SR-Suche**. Je Fall enthält die lange Reihe 16.777.216 Float64-Werte;
die kurze verwendet exakt deren erste 262.144 Werte. Das sind bei 4096 Hz
4096 beziehungsweise 64 Sekunden gemäß N/fs; die Endpunktspanne ist davon
zu unterscheiden. Separate Validierungs- und Kontrollfenster bleiben erhalten.

Alle Ergebnisse sind einschließlich roher/geschrumpfter Matrizen, Alpha,
Kondition, Kontrollscore und Grafiken gespeichert. Die getrennte lesende
Nachrechnung und ihr neuer Export stimmen mit der ursprünglichen Publikation
überein. Die folgende Tabelle beschreibt den Mittelwert der relativen
Frobeniusabweichung der **geschrumpften** Matrix zur bekannten Kovarianz:

| Rauschen | Verfahren | Fälle | 64 s | 4096 s |
| --- | --- | ---: | ---: | ---: |
| AR(1) | volle Matrix | 8 | 0,1561012 | 0,0201411 |
| AR(1) | Welch/Toeplitz | 8 | 0,0237421 | 0,0027709 |
| weiß | volle Matrix | 4 | 0,0018052 | 0,0078612 |
| weiß | Welch/Toeplitz | 4 | 0,0069186 | 0,0020459 |

Für diese korrelierten Entwicklungsfälle verbessert die längere Grundlage
die Matrixschätzung deutlich. Bei den vier weißen Fällen wird die volle
Matrix nach der unveränderten Holdout-Schrumpfung im Mittel schlechter;
mehr Hintergrund garantiert daher auch hier keinen günstigeren Einzelbefund.
Die Welch-Diagnose ist weder ein zweiter Sucharm noch eine automatische
Methodenwahl. Aus diesen Matrixfehlern folgt keine bereits nachgewiesene
Verbesserung freier SR-Formeln. Der wissenschaftliche Lauf behält den
vorab festgelegten vollen Matrixschätzer.

Der gesamte Diagnoseaufruf benötigt 109,132 s Wandzeit, 98,238 s User- und
10,430 s System-CPU-Zeit. Der gemessene Prozesshöchststand beträgt
308.196 KiB, etwa 301 MiB, einschließlich Vorbereitung und vorheriger Arbeit.
Diese enthaltenen Kosten werden nicht zu den einzelnen Schätzerzeiten addiert.
Für den separaten ursprünglichen Verify-Aufruf wurde keine eigene Prozesszeit
gespeichert; sie bleibt unbekannt.

## Ressourcen-Ergänzung und Schätzerdiagnose 002

Die Ergänzung weist auch je Schätzung den kumulativen Prozesshöchststand sowie
Präfix-, gemeinsame Rohdatei- und Ergebnisdateigrößen ausdrücklich aus.
Das ist keine isolierte RAM-Messung eines einzelnen Verfahrens und keine
Änderung seiner Berechnung. Die Originalausgabe 001 bleibt unverändert.

`noise-followup-estimators-cloud-002` ist am sauberen Commit
`04d9a760fc1e3eb8808fdb0763032b526fc9c568` ausgeführt: **48/48 Schätzungen,
keine Ausfälle, keine SR**, separate lesende Nachrechnung und neuer Export
bestanden. Alle 37 Eingabedatei- und 48 Schätzer-NPZ-Hashes stimmen exakt mit
001 überein. Es sind dieselben zwölf Entwicklungsfälle; sie werden weder als
zusätzliche unabhängige Fälle gezählt noch zu einem größeren Datensatz gepoolt.
Die obige Ergebnistabelle bleibt unverändert.

Die tatsächlich gespeicherten Präfixgrößen sind 2.097.152 und 134.217.728 Bytes;
beide referenzieren je Fall dieselbe 134.217.856 Bytes große NPY-Rohdatei
einschließlich Header. Die tatsächliche Größe jeder Ergebnis-NPZ wird separat
gebunden und beim Replay aus ihren Bytes bestimmt. Pro Schätzung gemessene
Prozesshöchststände liegen zwischen 288.064 und 307.624 KiB; sie enthalten
frühere Arbeit und sind keine isolierten Speichervergleiche der Verfahren.

Der interne Gesamtaufruf benötigt 96,071 s Wandzeit, 87,860 s User- und
8,091 s System-CPU-Zeit, Prozesshöchststand 307.624 KiB. Der äußere Python-
Prozess benötigt einschließlich Start und letzter Nachprüfungen 100,030 s,
90,895 s User- und 8,994 s System-CPU-Zeit. Die getrennte lesende Verifikation
mit Export benötigt 73,721 s, 69,479 s User- und 4,132 s System-CPU-Zeit.
Die unterschiedlichen eingeschlossenen Messbereiche werden nicht addiert.

## Technischer Vorlauf 001

Ein eigener AR(1)-Fall, N=128, beide tatsächlichen Dauern und sechs getrennte
Zehnerworker: **6/6 abgeschlossen**, jeweils mit ursprünglichem ausgewählten
Kandidaten und vollständiger nativer Herkunft. Alle bekannten und geschätzten
Gewichtungen sowie beide Messraster sind geprüft. Die Modellgüte ist hierbei
kein Gate; zehn Iterationen ersetzen keinen wissenschaftlichen Suchlauf.

| Bedingung | Gemessene Fitzeit / s |
| --- | ---: |
| Uniform O | 46,220 |
| Uniform K | 42,632 |
| Uniform E64s | 42,513 |
| Uniform E4096s | 43,646 |
| Jitter O | 40,870 |
| Jitter K | 40,717 |

Der gesamte technische Aufruf benötigt 399,789 s Wandzeit, 374,202 s User-
und 26,214 s System-CPU-Zeit. Die sechs enthaltenen Worker benötigen zusammen
383,626 s, davon 256,599 s Fitzeit; diese verschachtelten Zeiten werden nicht
addiert. Der anschließende getrennte lesende CLI-Verify benötigt 7,002 s.

Technischer Plotexport und Exportverifikation bestehen. 34 Exportdateien
enthalten alle sechs unveränderten Originalformeln, Bäume/Metadaten,
Punkt-CSV und PNG/SVG sowie Index und Abschlussbelege. Der äußere
Plotaufruf benötigt 12,808 s, davon 11,121 s in der gemessenen Plottransaktion;
die getrennte Plotprüfung 1,425 s. Äußere Zeiten enthalten den CLI-/uv-Start.
Die AR(1)-Diagnosegrafik und der technische Jitter-K-Plot wurden zusätzlich
visuell geprüft. Daraus wird keine zusätzliche wissenschaftliche Bewertung
oder Formelwahl abgeleitet.

## Implementierungsprüfung

Gezielte KI-basierte Methoden- und Implementierungsreviews beziehen sich auf
PR102-Head `34ef0094d7ae52cbf56f6b012a76451325348444` gegen die Alias-Basis
`7f52cfb2fe94ad13cda1ff28e11daa261e57bd21`; keine offenen Befunde im
beauftragten Umfang. Die Reviews ersetzen die ausführbaren Prüfungen nicht.

Im [Draft-CI-Lauf 44542925986](https://github.com/craexxn/ringdown-sr/actions/runs/44542925986)
bestehen 4.600 Python-Tests in 591,56 s. Der native Teil ist im Draft
planmäßig übersprungen; das Abschlussgate verweigert daher korrekt eine volle
Freigabe. Lokal bestehen zunächst 4.599 Tests, ein Kostentest setzt
unzulässig eine positive gemessene System-CPU-Zeit voraus. Die Korrektur
verwendet kontrollierte synthetische Kosten und ist damit unabhängig von der
Betriebssystem-Zeitauflösung; die Produktionsgrenzen bleiben unverändert.
Nach der Ergänzung bestehen alle **229 Tests der Folgestudie**, darunter
35 Diagnoseprüfungen für tatsächliche Größen, manipulierte Ressourcenbelege
und späte Quellenänderungen. Ruff, Format und 120 Markdown-Prüfungen bestehen.
Vollständige Ready-CI und endgültiger Freigabestand stehen im PR.

## Archiv und offene Sicherung

Originalarchiv `noise-followup-development-cloud-001.tar.gz`,
1.698.753.038 Bytes; SHA-256:

```text
1f15e7f4c0ab1af8b670d6edf21cf4937f7600b42bef67998de38f0bb9ed43f0
```

Das Archiv enthält 390 Original-/Verify-/Plot-/Logdateien einschließlich
der langen Rauschreihen, der Aufrufkosten und eines zusätzlichen Manifests.
Alle Mitglieder wurden aus dem fertigen Archiv lesend gehasht, mit dem
Manifest verglichen und gegen die unveränderten Quelldateien geprüft.
Packen und Archivprüfung benötigen zusammen 96,169 s; dieser eigene Aufwand
wird nicht als Suchzeit gerechnet. Die Ausführungsquelle bleibt über
`refs/pull/102/head` erreichbar.

Die ergänzte Diagnose 002 besitzt das eigene vollständige Originalarchiv
`noise-followup-diagnostics-cloud-002.tar.gz`, 1.565.250.615 Bytes;
SHA-256:

```text
8206130fdfb58b34f430b4a99b9d90e76c2519fde7b141a96f684fff6f55d97e
```

156 Original-/Verify-/Logdateien plus Manifest, einschließlich aller langen
Eingabereihen und der expliziten Bytevergleichsnotiz. Die fertig gepackten
Mitglieder und unveränderten Quellen sind vollständig gehasht geprüft;
Packen und Prüfung benötigen 85,192 s. Das zusätzliche Manifest verweist
auf den SHA-256 des vorausgehenden Entwicklungsarchivs, ohne es zu ersetzen.
Ausführungscommit 04d9a76 bleibt ebenfalls über den dauerhaften PR102-Ref erreichbar.

Lokale Cloud-Arbeitsablage im Exportordner `ringdown-noise-followup`;
dauerhafte Archivablage und unabhängige hashgeprüfte Zweitkopie sind nicht
bestätigt. Der [Ergebnisindex](results_index.md) führt diesen offenen
Sicherungsstand getrennt von der erfolgreichen technischen Ausführung.
