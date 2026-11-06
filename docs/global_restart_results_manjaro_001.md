# Globaler Neustartvergleich auf Manjaro: Abbruch von Lauf 001

Dokumentationsstand: 06.11.2026, [Leitfadenphase 3](ringdown_recovery_roadmap.md).
Der Aufruf mit Ausgabe-ID `global-restarts-manjaro-001` wurde begonnen und
laut übermitteltem Terminalausschnitt versehentlich durch Strg+C unterbrochen.
Das am 06.11.2026 nachgereichte ZIP bestätigt 19 fertige Zellen und den Abbruch
der 20. Zelle; die Serienfreigabe ist gesperrt. Der zunächst
nur besprochene Gesamtlauf `global-restarts-manjaro-002` wurde inzwischen mit
eigenem Start- und Fortschrittsauszug gemeldet; ein Abschluss liegt noch nicht vor.

## Plan, Herkunft und belegte Beobachtung

Es gilt das unveränderte [eingefrorene Protokoll](global_restart_comparison_plan.md)
mit [Konfiguration](../data/global_restart_protocol.json), Plancommit
`b00fc4a0a5a5a90e7d72f45d2b27788d1fd1585a`: vier Entwicklungsblöcke, insgesamt
20 frische Suchen, Vergleich 1 × 500, frische 1 × 2.000 und 4 × 500 bei lokal
300/5. Seeds, Datenrollen, Auswahl, Endpunkte und Ausfallregeln stehen dort;
sie werden durch diesen Abbruchbericht nicht geändert.

Erste Quelle war die im Chat „6_Implementierungspipeline“ übermittelte Start-
und Abbruchmeldung. Ergänzend liegt jetzt `global-restarts-manjaro-001.zip` vor,
4.135.809 Bytes, SHA-256
`73f27a15af2c2102ab5e56d49ad13ece9bb13bbff700a6d6f26a808958a8ca14`.
Der selbst berechnete Hash identifiziert das empfangene Paket, kein früheres
Originalarchiv mit anderweitigem Namen/Hash. Der übermittelte Aufruf war:

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_global_restarts.py run \
  --output results/global-restarts-manjaro-001
```

Dies dokumentiert den bereits gemeldeten Aufruf, keinen erneuten Laufauftrag.
Die Umgebung meldete eine abweichende aktive `VIRTUAL_ENV`, die ignoriert wurde,
und `Preparing worktree (detached HEAD 5215c5e)`. Der Traceback endet beim
Warten auf den Bridge-Unterprozess (`call_bridge`, `child.wait`) mit:

```text
^C
InterruptedError: Assessment interrupted by signal 2
```

Das passt zur berichteten manuellen Unterbrechung. Es ist kein Beleg für einen
numerischen Suchfehler oder eine erfolglose Ringdown-Rekonstruktion. Der
empfohlene saubere Ausführungscheckout war der PR76-Merge
`b547bb3b1753235960cc0654f8cebd747fc1b2f3`; dieser ist nun durch die gespeicherte
saubere Orchestrierungsherkunft und ihre Quellenbindungen bestätigt. Die kurze Worktree-Meldung bezeichnet
den historischen Worker, nicht den Orchestrierungscommit. Ebenso beweisen
angeforderte Umgebungsvariablen nicht die tatsächlich geladenen Bibliotheken.

## Status und Kosten

| Gegenstand | Belegt / weiterhin offen |
| --- | --- |
| Wissenschaftlicher Lauf `global-restarts-manjaro-001` | `run_state.status=aborted`, SIGINT; kein abgeschlossener Vergleich |
| Teilstand | 20 vorbereitet; Zellen 1–19 `completed`, Zelle 20 `aborted`, Worker in Phase `fit` durch Signal 15 unterbrochen |
| Abschluss und Sperre | `ASSESSMENT_LOCKED` vorhanden; Fehlerbericht und Abschlussbericht identisch `failed`/`locked`, leere Serien/Gruppen; keine positive Abschlussfreigabe |
| Verbrauchter Aufwand | Für Zellen 1–19 belegt: Bridge 4.298,683095 s, Adapter 4.269,622316 s, Worker 4.265,474093 s, Fit einschließlich JIT/Exporten 3.998,273373 s; 473.929.178 Fit-Callback-Aufrufe. Überlappende Bereiche, nicht addieren. |
| Vollständige Wiederholung `global-restarts-manjaro-002` | Start und Zwischenstand übermittelt: Zellen 1–2 `completed`, 3 `running`, 4–20 `planned`; kein Serienabschluss oder Archiv belegt |
| Technischer Manjaro-Vorlauf `global-restarts-technical-001` | Separater Aufruf mit `check_global_restarts.py` und Startmeldung übermittelt; erfolgreicher Abschluss und lesende Verifikation noch nicht belegt |

Die Teilsummen schließen die Vorbereitung, den angebrochenen Worker 20 und den
abschließenden Abbruch nicht vollständig ein. Für Zelle 20 fehlen `timing.json`,
`outcome.json`, `verified.json` und ein fertiges `result.json`. Gesamtkosten und
Kosten dieser Zelle bleiben unbekannt, nicht null. Vorbereitungsstart ist
06.11.2026 10:49:04,930607 UTC; Dateizeiten werden nicht als Kostenmessung verwendet.

Die im Chat genannte grobe Dauerabschätzung aus historischen 500er-/2.000er-
Laufzeiten ist keine Messung dieser Serie. Sie ersetzt auch keine Abbruchkosten.
Gleichnamige technische Cloud-Ausgaben belegen keinen lokalen Manjaro-Abschluss.

Der zusätzliche Auszug zu 002 vom 06.11.2026 zeigt nach `ps` 21:54 Minuten
verstrichene Prozesszeit sowie das Vorbereitungslog von Zelle 20 und die
Runlogs der ersten drei Zellen. Das ist eine
Momentaufnahme, keine Gesamtserienmessung. Der oberste `run_state`-Status
`preparing` bleibt im PR76-Code während der Suchschleife stehen; die einzelnen
Zellstatus zeigen bereits die laufende Suche. Dateizeiten werden nicht zu
präzisen Fit- oder Suchkosten umgedeutet. Die 20 Zellen von 002 werden unabhängig
von 001 beurteilt; der tatsächliche Quellenstand bleibt bis zur Prüfung seiner
Originalmetadaten offen.

## Lesende Archivprüfung vom 06.11.2026

958 Dateien unverändert gelesen, 363 Vorbereitungsbindungen und die vollständige
Inventarliste von 66 Orchestrierungsquellen geprüft; insgesamt 154 verschiedene
Commit-/Dateibindungen einschließlich historischem Worker und Protokoll gegen
Git abgeglichen. Eingaberollen und Bits des Ankers sowie die 1.024 vorab
festgelegten unregelmäßigen Rasterpunkte stimmen mit dem eingefrorenen Vertrag
überein. Alle 20 vorbereiteten Anfragen, Optionen, Referenz- und Laufzeitdateien
bestehen die historische Bindungsprüfung.

Die gespeicherten Ergebnisse der 19 fertigen Zellen wurden mit dem historischen
Python-Elternverifikator erneut gelesen: Originalauswahl, Herkunft, effektive
Optionen, 179 exportierte Kandidaten und gespeicherte Diagnosen stimmen überein.
Die Worker-/Adapterherkunft und Eingabemanifeste sind auch für Zelle 20 gebunden.
Signal 2 im Elternprozess und Signal 15 im unterbrochenen Worker passen zur
Abbruchbehandlung. Sperre, leere Aggregate und fehlende Erfolgsdateien wurden
eigens geprüft. Das ist keine vollständige Serienverifikation und kein
wissenschaftlicher Armvergleich; kein neuer Bewertungsabschluss wurde erzeugt.
Keine Suche, kein Fit, kein Julia-/PySR-Start und kein nativer Replay.

## Zulässige Konsequenz und benötigte Belege

Den unveränderten Teilstand von 001 einschließlich vorhandener Vorbereitung,
`run_state.json`, `cell-*`, Logs, Abschluss-/Sperrdateien und Manifeste erhalten.
Aus diesem Abbruch werden keine positiven Serienaggregate, Erfolgsquoten oder
Kontrollen für den Zeitbudgetvergleich freigegeben. Einzelne bereits fertige
Zellen dürfen später lesend diagnostiziert werden; sie vervollständigen keinen
anderen Lauf. Ein fehlender Erfolgsmarker wird nicht von Hand ergänzt.

Eine gesondert ausgeführte vollständige Wiederholung verwendet eine neue ID und
behält die vorab festgelegten Regeln; 001 und 002 bleiben getrennt sichtbar.
Bereits verbrauchter Aufwand von 001 gehört zur Entwicklungsdokumentation und
wird, soweit belegt, zusätzlich zum Aufwand der Wiederholung ausgewiesen.
Der Abbruch rechtfertigt keine nachträgliche Seed- oder Ergebnisauswahl.

Priorisierte Nachforderung und Sicherungsstand stehen ausschließlich im
[Ergebnisindex](results_index.md#priorisierte-fehlende-belege).
Zellstand, tatsächlicher Commit, erhaltene Teilkosten und empfangener Pakethash
sind nun belegt; unbekannte Gesamtkosten werden nicht rekonstruiert. Abschluss
und Herkunft von 002 sowie der technische Vorlauf benötigen eigene Belege.
Das Auditpaket und die offenen dauerhaften Sicherungen sind im Index zugeordnet.
Kein neuer Suchlauf wurde gestartet, kein Teilstand verändert und keine
Originalauswahl oder historische Bewertung ersetzt.
