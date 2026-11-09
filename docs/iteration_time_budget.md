# Laufweg: 2.000 Iterationen gegenüber 400 Sekunden

Leitfadenphase 3; das [eingefrorene Protokoll](iteration_time_budget_plan.md)
und die [Konfiguration](../data/iteration_time_protocol.json) gelten unverändert.
Vier bekannte Entwicklungsseeds, keine allgemeine Erfolgswahrscheinlichkeit.
Der [PR76-Neustartvergleich](global_restart_comparison.md) bleibt ein separater
wissenschaftlicher Versuch. Abgleich vom 06.11.2026: Der
[Lauf 001](iteration_time_results_manjaro_001.md) ist mit acht frischen Suchen
auf `4df7ecaaaed0a6d235f7db104c6982bdfcabf048` abgeschlossen und lesend bestätigt,
einschließlich Aufrufmessung und Verify-Export. I erreicht 4/4 A, Z 3/4 A;
beide 3/4 A mit Familiennachweis. Trotz geringerer Gesamtkosten ist dies nach
der eingefrorenen Regel eine Verschlechterung dieser Entwicklungsfälle.
Die folgenden Befehle dokumentieren den ausgeführten Manjaro-Laufweg; sie
geben keine Wiederholung oder Überschreibung von 001 frei und sind keine CI-Aufgabe.

## Voraussetzungen und Kontrollimport

Ein sauberer Checkout des übernommenen Implementierungsstands, alle Git-Referenzen
und die gesperrten Python-/Julia-Versionen sind erforderlich. Im Ausführungscheckout
während Run und Verify keine Quellen ändern, keinen Branch wechseln und nicht
gleichzeitig andere Suchaufträge starten. Der Laufweg führt alle neuen Suchen
seriell aus, bindet die Prozessgruppe an eine erlaubte CPU und setzt vor dem
Julia-Import `JULIA_NUM_THREADS=1,0`, `PYTHON_JULIACALL_THREADS=1,0` sowie
`JULIA_NUM_GC_THREADS=1`. Die tatsächlich beobachteten Default-/Interactive-/GC-
und BLAS-Threadzahlen müssen 1/0/1/1 betragen. Hardware, Affinität und
Threadumgebung werden vor und während jedes Fits gespeichert.
Die Hardwarebindung enthält auch die tatsächlichen CPU-Modellnamen aus
`/proc/cpuinfo`; Julias Architekturbezeichnung allein genügt dafür nicht.

```bash
git status --short
git rev-parse HEAD
uv sync --locked --dev
```

Standard ist `reuse_pr76`: vier neue Z-Suchen, alle vier historischen I-Kontrollen
einschließlich ihrer Ausfälle. Originalarchiv und separat gesicherte SHA-256
bereitstellen. Die dokumentierte PR76-Tar-Datei darf das Originalverzeichnis
und seinen separaten Verifikationsordner enthalten. Links, doppelte/unsichere
Pfade und Größenüberschreitungen werden abgelehnt; Pickle-/Julia-Zustände werden
nicht geladen. Der Import nutzt ausschließlich den korrigierten, geprüften
PR76-Verifikator `66ec4238f39edbbc2a71bb4e984571e41531e7ab`. Der tatsächliche
Ausführungscommit muss dessen Dateibaum besitzen; ein beliebiger späterer
Workerstand wird nicht stillschweigend akzeptiert. Fehlende Git-Objekte gezielt
nachladen; keine aufgezeichneten Hashes oder Commits ersetzen.

```bash
uv run --locked python scripts/run_iteration_time.py audit-controls \
  --archive /pfad/zum/gemeinsamen-archiv/global-restarts-manjaro-002.tar.gz \
  --archive-sha256 ORIGINAL_SHA256 \
  --output results/time-controls-audit-001
```

Dieser Befehl startet keine Suche. Er prüft das gesamte Original mit dem
PR76-Verifikator und danach die technische Eignung der Zellen 2/7/12/17.
`eligible=false` ist ein abgeschlossener negativer Eignungsbefund, keine
Freigabe einer Ersatzserie. Die Gründe bleiben im JSON-Bericht erhalten.

**Konkrete Quellenlücke:** PR76 zeichnet die tatsächlichen Julia-/GC-Threadzahlen
und die native CPU-/Affinitätsbindung nicht in der erforderlichen Form auf.
Serielle Struktursuche und BLAS=1 beweisen diese Größen nicht; PySR setzt ohne
ausdrückliche Vorgabe Julia-Threads auf `auto` und aktiviert zusätzliche
GC-Threads. Ein unverändertes PR76-Archiv ohne solche Originalbelege wird deshalb
nicht als wiederverwendbar freigegeben. Nachträglich ergänzte Behauptungen oder
Messungen auf dem heutigen Rechner ersetzen keine historischen Workerbelege.
Abgleich vom 06.11.2026: Das [wissenschaftliche Archiv von Lauf 002](global_restart_results_manjaro_002.md)
ist inzwischen vollständig lesend geprüft. Die bestehende Eignungsfunktion
meldet für den ganzen Arm `eligible=false`: In allen vier Kontrollzellen
2/7/12/17 fehlen die tatsächlichen CPU-/Julia-/GC-Threadbelege. Damit ist der
vorbereitete Ersatzmodus `fresh_all` technisch begründet, unabhängig von der
Kurvenqualität. Diese Lücke ändert weder PR76 noch sein eingefrorenes Protokoll.

## Wissenschaftliche Ausführung

Zuerst den technischen Prüfschritt am Ende dieser Anleitung ausführen.
Danach genau einen Modus ausdrücklich wählen und begründen. Keine automatische
Umschaltung, Wiederholung, Verlängerung oder Ersetzung einzelner Seeds.

Nur bei vollständig bestätigter Wiederverwendung:

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_iteration_time.py run \
  --mode reuse_pr76 --reason 'Gesamter PR76-Kontrollarm technisch bestätigt' \
  --archive /pfad/zum/gemeinsamen-archiv/global-restarts-manjaro-002.tar.gz \
  --archive-sha256 ORIGINAL_SHA256 \
  --output results/iteration-time-manjaro-001
```

Ist die Wiederverwendung des gesamten Arms nicht nachweisbar, ist ausschließlich
der ausdrücklich gewählte Ersatzmodus vorgesehen. Er benötigt acht neue Suchen:
pro Seed I–Z, Z–I, I–Z, Z–I. Die Begründung muss den tatsächlichen technischen
Grund nennen; ein vorliegender Auditbericht bleibt erhalten.

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_iteration_time.py run \
  --mode fresh_all --reason 'Historische tatsächliche Julia-/GC-Threadbindung nicht nachgewiesen' \
  --output results/iteration-time-manjaro-001
```

Der Modus wird mit Begründung, Quellen, vollständiger Aufrufliste, Eingaben und
konkretem Diagnosegitter vor dem ersten Fit gebunden. Alle Zellen werden zuerst
vorbereitet; Umgebung und native Optionen müssen übereinstimmen. Es gelten
1.800 Sekunden Sicherheitsfrist je Worker und zwei Stunden für den neuen
Gesamtaufruf einschließlich Vorbereitung und Bewertung. Historische Kosten
zählen zum Algorithmusaufwand, verbrauchen diese neue Frist aber nicht erneut.
Zeitüberschreitungen oder Integritätsfehler führen nicht zu automatischen
Ersatzaufrufen. Teilstände bleiben erhalten; gesperrte Abschlüsse besitzen keine
gültige vollständige Auswertung.

400 Sekunden betreffen die native Hauptschleife nach den Aufwärmzyklen.
Der Abbruch ist kooperativ und kann die Grenze überschreiten. Fitzeit umfasst
zusätzliche Initialisierung/JIT und Export; Workerzeit zusätzlich Prozessstart
und Elternprozessarbeit. JIT wird nicht als isoliert gemessene Größe ausgegeben.
`iteration_limit`, `regular_timeout`, `iteration_reserve`, `worker_timeout`
und erlaubte numerische Fitfehler bleiben getrennt. Unbekannte Fehler,
Aufrufwächter und Unterbrechungen sperren den Gesamtabschluss.
Der Abgleich mit einer monotonen Uhr beginnt vor Eintritt in die native
Hauptschleife; er erfasst auch Sprünge vor der ersten Zeitprüfung. Eine Abweichung
über einer Sekunde sperrt die Freigabe. Reine JIT-Zeit wird nicht aus der
Differenz zweier ungleicher Messfenster geschätzt.

## Artefakte und lesende Verifikation

- `preparation.json`, `prepared_bindings.json`, `request-*.json`: Modus,
  Protokoll, vollständige Quellen und Vorbereitungsbindung.
- `anchor.npz`, `irregular.npz`: tatsächliche Eingabebits und 1.024 diagnostische
  Punkte; beim Import wird die originale NPZ-Datei unverändert übernommen.
- `cell-*/worker/`: Originalfront, Originalauswahl, Metadaten, tatsächlicher
  Aufruf, Optionen, Verlust-/Vorhersagebelege sowie native Timer-/Threadbelege.
- `cell-*/worker_resources.json`: gemessene Nutzer-/System-CPU-Zeit und
  Prozesswandzeit des gestarteten Workers einschließlich gewarteter Nachkommen.
- `run_state.json`: alle geplanten Fälle und verbleibende Teilstände.
- Die benachbarte Datei `iteration-time-manjaro-001-call.json`: tatsächlich
  gemessene Wand-/Nutzer-/System-CPU-Zeit des neuen Aufrufs einschließlich
  Vorbereitung, Worker, Nachprüfung und Veröffentlichung. Nur das abschließende
  Schreiben dieser Messdatei und die letzten Integritätsprüfungen liegen danach.
  `prepublication_wall_seconds` im Hauptbericht endet früher und ist getrennt.
- `completion/`: Bericht, lesbare Zusammenfassung und vollständige Prüfsummen;
  `ASSESSMENT_LOCKED` sperrt die Freigabe bei Fehlern oder Unterbrechungen.

Der primäre Workeraufwand verwendet in beiden Armen das bestehende
`worker/status.json:total_wall_seconds`: Elternvorbereitung, Workerstart/-warten
und Ergebnislesen, ohne nachfolgende Adapterdiagnose. Die zusätzlich gemessene
Prozesswandzeit hat einen engeren Umfang und ersetzt diese Vergleichsgröße
nicht. Fehlende historische CPU-/Iterations-/Timerwerte bleiben unbekannt.
Kosten der alten Kontrollen, neuer Suchen und des gesamten Algorithmus stehen
getrennt im Bericht. Alle vier Fälle je Arm bleiben im Nenner; keine gemeinsamen
Erfolgsquoten mit anderen historischen Serien.

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_iteration_time.py verify \
  results/iteration-time-manjaro-001 \
  --output results/iteration-time-manjaro-001-verification
```

Bei einem mit Kontrollarchiv ausgeführten Run zusätzlich dieselben
`--archive`-/`--archive-sha256`-Argumente angeben. Verify benötigt den exakten
sauberen Ausführungscheckout und die gebundene Python-Umgebung. Er prüft
Originalinventar, vorbereitete Quellen, gespeicherte native Nachweise,
Fehlerherkunft, Kosten und Bewertungsregeln mit Python-/MPFR-Nachrechnung.
Keine Suche, kein Fit und keine neue native Vorhersage. Verschobene
Originalverzeichnisse sind zulässig; deren gespeicherte Eingaben werden gelesen.
Die benachbarte `-call.json`-Datei dabei mitnehmen. Verify bindet ihren Hash,
ihren Berichtsbezug und den aufgezeichneten Messumfang in seinen eigenen Export.

Originalauswahl ausschließlich nach endlichem nativen Trainingsverlust,
Komplexität und Originalfrontindex. Zusatzraster und Strukturdiagnose steuern
weder Auswahl noch Stopp. Historische A–D-Regeln bleiben erhalten, ungeklärte
Strukturen sind kein Gegenbeweis, neue Parametermatches `not_assessed`.

## Technischer Manjaro-Vorlauf und Archivierung

Die technischen Aufrufe nutzen acht separate Punkte `y=1+t`: vier Worker
für Iterationsende, kurze reguläre Zeitgrenze, Reserveende und wiederholten
Iterationslauf; anschließend lesende Verifikation. Drei weitere frische
Prozesse vergleichen den tatsächlichen Suchverlauf bis zu vier festen
Populationsschritten unter historischem Profil, neuem Iterationsprofil und
hoher Zeitprofilreserve. Sie versprechen keine bitgleichen zeitbegrenzten Endfronten.

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/check_time_budget_dynamics.py \
  --output results/iteration-time-prefix-001
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/check_iteration_time.py \
  --output results/iteration-time-technical-001
```

Nach dem wissenschaftlichen Run und erfolgreicher Verify-Prüfung:

```bash
tar -czf results/iteration-time-manjaro-001.tar.gz \
  -C results iteration-time-manjaro-001 iteration-time-manjaro-001-call.json \
  iteration-time-manjaro-001-verification
sha256sum results/iteration-time-manjaro-001.tar.gz
```

Unveränderte Originalarchive im gemeinsamen Archivordner erhalten, unabhängige
zweite Kopie auf anderem Datenträger oder im bestehenden Backup sichern und
beide Kopien anhand SHA-256 prüfen. Tatsächliche Orte, Prüfsummen und
Sicherungsnachweise im [Ergebnisindex](results_index.md) ergänzen.
GitHub-Releases bleiben optional; große Archive gehören nicht regulär in Git.
