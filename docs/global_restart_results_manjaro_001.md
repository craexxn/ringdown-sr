# Globaler Neustartvergleich auf Manjaro: Abbruch von Lauf 001

Dokumentationsstand: 06.11.2026, [Leitfadenphase 3](ringdown_recovery_roadmap.md).
Der Aufruf mit Ausgabe-ID `global-restarts-manjaro-001` wurde begonnen und
laut übermitteltem Terminalausschnitt versehentlich durch Strg+C unterbrochen.
Ein vollständiger wissenschaftlicher Abschluss ist nicht belegt. Der zunächst
nur besprochene Gesamtlauf `global-restarts-manjaro-002` wurde inzwischen mit
eigenem Start- und Fortschrittsauszug gemeldet; ein Abschluss liegt noch nicht vor.

## Plan, Herkunft und belegte Beobachtung

Es gilt das unveränderte [eingefrorene Protokoll](global_restart_comparison_plan.md)
mit [Konfiguration](../data/global_restart_protocol.json), Plancommit
`b00fc4a0a5a5a90e7d72f45d2b27788d1fd1585a`: vier Entwicklungsblöcke, insgesamt
20 frische Suchen, Vergleich 1 × 500, frische 1 × 2.000 und 4 × 500 bei lokal
300/5. Seeds, Datenrollen, Auswahl, Endpunkte und Ausfallregeln stehen dort;
sie werden durch diesen Abbruchbericht nicht geändert.

Quelle ist die im Chat „6_Implementierungspipeline“ übermittelte Start- und
Abbruchmeldung, am 06.11.2026 dokumentarisch abgeglichen. Originalergebnisordner,
Archiv und lokale vollständige Logs lagen hier nicht vor. Der übermittelte
wissenschaftliche Aufruf war:

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
`b547bb3b1753235960cc0654f8cebd747fc1b2f3`; die tatsächliche Orchestrierungsherkunft
bleibt ohne Originalmetadaten unbestätigt. Die kurze Worktree-Meldung bezeichnet
den historischen Worker, nicht den Orchestrierungscommit. Ebenso beweisen
angeforderte Umgebungsvariablen nicht die tatsächlich geladenen Bibliotheken.

## Status und Kosten

| Gegenstand | Belegt / weiterhin offen |
| --- | --- |
| Wissenschaftlicher Lauf `global-restarts-manjaro-001` | Start und SIGINT-Abbruch übermittelt; kein abgeschlossener Vergleich |
| Teilstand | Zahl fertiger, fehlgeschlagener oder noch nicht ausgeführter Zellen und Abbruchzelle unbekannt; aus dem Traceback nicht ableitbar |
| Abschluss und Sperre | Laut Vertrag muss der Signalabbruch die Freigabe sperren; tatsächlicher Inhalt von `completion/`, `run_state.json` und Sperrdatei hier nicht geprüft |
| Verbrauchter Aufwand | Reale Gesamt-, Worker-/Fitzeiten und Zielfunktionsaufrufe nicht übermittelt; unbekannt, nicht null |
| Vollständige Wiederholung `global-restarts-manjaro-002` | Start und Zwischenstand übermittelt: Zellen 1–2 `completed`, 3 `running`, 4–20 `planned`; kein Serienabschluss oder Archiv belegt |
| Technischer Manjaro-Vorlauf `global-restarts-technical-001` | Separater Aufruf mit `check_global_restarts.py` und Startmeldung übermittelt; erfolgreicher Abschluss und lesende Verifikation noch nicht belegt |

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
Ohne Originalordner bleiben Zellstand, tatsächlich ausgeführter Commit, Kosten
und Archivhash offen. Abschluss und Herkunft von 002 sowie der technische Vorlauf
benötigen jeweils eigene Belege. Kein neuer Suchlauf wurde für diesen Bericht
gestartet, keine Primärdaten neu bewertet und kein Teilstand verändert.
