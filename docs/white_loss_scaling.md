# White-Skalierungspilot: Laufweg und Befund

Stand 23.11.2026, Leitfadenphase 7. Der
[Vorabplan](white_loss_scaling_plan.md) ist in Commit
`222b4bc2263e6200bf29b2424c2a5e6bd318bdd2` vor neuen Versuchsbeobachtungen
festgelegt. Branch `codex/white-loss-scaling-pilot` baut auf
[Ergebnis-PR #103](https://github.com/craexxn/ringdown-sr/pull/103) auf,
der am 23.11.2026 nach bestandener
[Dokumentations-CI](https://github.com/craexxn/ringdown-sr/actions/runs/45035553844)
als `3ee6e22e9a78e867dae1923152c8df69d73791aa` übernommen wurde.
Die Umsetzung ist in [PR #104](https://github.com/craexxn/ringdown-sr/pull/104)
als Draft vorbereitet. Der erste wissenschaftliche Pilot auf
`d72202e341a51df0d19a4f86c67dbb1eb900c7b2` unter `white-scaling-cloud-001`
ist nach vollständiger fester Stufe und erster erfolgreicher freier Suche
an einer neuen Elternprüfung abgebrochen. Die unten dokumentierte Korrektur
bereitet `white-scaling-cloud-002` mit unverändertem Plan vor. Eine vollständige
wissenschaftliche Freigabe steht bis zum Abschluss und lesenden Replay aus.
Die anschließende Auswahlprüfung ist implementiert,
aber bis zu ihrem gesonderten Vorabplan technisch gesperrt.

## Technische Nachweise vor dem Pilotstart

146 native Assertions, neun unabhängige arithmetische Referenzrechnungen,
vier frische O/S/K/O-Miniworker und vier feste Starts am gesonderten
Achtpunkt-Signal sind bestanden. Die vorbestimmte O-Wiederholung liefert
dieselbe ursprüngliche Front und Callbackzahl. Ein separater lesender
Verifikationsprozess besteht ebenfalls. Der technische Gesamtlauf benötigt
508,629 s und ist keine wissenschaftliche Laufzeit.

348 gezielte Python-Tests auf dem Ausführungscommit sind bestanden. Der erste
vollständige lokale Lauf auf `13d6344` ergibt 4.641 bestandene Tests und einen
Fehler: Die explizite CI-Schrittliste kannte den neu ergänzten Prüfschritt
noch nicht. Diese Liste ist auf `d72202e` ergänzt; ihre gezielte Nachprüfung
ist bestanden. Keine bisherigen Prüfungen entfernt. Vollständige abschließende
Ready-CI am späteren PR-Head bleibt erforderlich.

Die Draft-CI `45139792797` findet danach einen anderen, älteren Testfehler:
Die Signalregeneration erwartet plattformübergreifend gleiche NumPy-Bytes.
Ein kontrollierter Wechsel von `X86_V4` auf `X86_V3` reproduziert exakt den
CI-Hash; 248 von 6.123 Signalwerten unterscheiden sich um höchstens 1,11e−16,
alle Zeitachsen bleiben bytegleich. Die Korrektur betrifft nur den Test:
eingefrorene Archivhashes, Generator und Protokoll bleiben unverändert;
lokale Wiederholung, exakte Methodendaten und beide Signalfassungen gegen die
ursprüngliche MPFR-Schranke 1e−13 werden geprüft. Je 25 Tests bestehen auf
beiden CPU-Pfaden. Keine Toleranz erweitert und keine historischen Daten ersetzt.

Gezieltes KI-basiertes Review an `13d6344690d3541dd1276a42d34df154071e53df`
gegen `9d63fff65c833b2e2de9ee66c4fcd720177bc6d7`: drei notwendige
Robustheitskorrekturen betreffen nichtendliche Zwischenpunktvorhersagen,
Abbruchkosten und sofortige Speicherung fester Teilresultate. Das Nachreview
an `d72202e341a51df0d19a4f86c67dbb1eb900c7b2` bestätigt die Korrekturen;
sechs gezielte Regressionstests sind bestanden. Dies ersetzt keine
wissenschaftliche Bestätigung.

Die erste native technische Testfassung hatte einen Julia-World-age-Fehler
im Testaufbau; das Vorladen der isolierten Testmodule behebt ihn vor dem
wissenschaftlichen Start. Der laufende Ausführungsstand schreibt während
der Arbeit zunächst einen missverständlichen `aborted`-Vorgabewert ohne
`finished_at`; erst der Abschluss setzt den endgültigen Zustand. Die spätere
Anzeige unterscheidet deshalb einen begonnenen gespeicherten Stand von einem
belegten Abschluss. Die laufenden Quellen und Ergebnisdateien werden dafür
nicht geändert.

## Erhaltener Fehlversuch 001 und gezielte Korrektur

Alle 72 festen Optimierungen und die erste freie Suche sind numerisch
erfolgreich. Die freie Suche erzeugt zwölf ursprüngliche Kandidaten und
erreicht ihre 100 äußeren Iterationen. Erst die zusätzliche Elternprüfung
der Baseline scheitert: Ein Hilfsprüfer für nichtnegative Verlustwerte wurde
auf signierte Signalbeobachtungen angewandt. 63 Werte sind negativ, keiner
subnormal. Die Korrektur prüft deren Betrag; Verlustkern, Optimierer,
rationale Fehlerschranken, Seeds und Vorabplan bleiben unverändert.
44 gezielte Tests einschließlich gemischter Vorzeichen für alle drei Arme
und weiterhin abgelehnter Unterlaufgegenfälle bestehen. Eine unabhängige
lesende Nachrechnung bestätigt alle zwölf Originalkandidaten und die
Baseline; sie ersetzt nicht die fehlende vollständige Serienverifikation.

001 bleibt als abgebrochener Versuch einschließlich aller Teilresultate
erhalten. Serienwandzeit 1.037,583 s; darin 940,210 s feste Worker und
96,409 s erster freier Worker, also keine zusätzlich zu addierenden Kosten.
Der neue vollständige Durchlauf verwendet dieselben zwei Rauschfenster und
Sequentiervorgaben in frischen Prozessen. Wiederholte Daten zählen nicht als
zusätzliche unabhängige Fälle; keine Auswahl günstiger Suchwiederholungen.

Die drei getrennten Verlustpfade sind gewöhnliche MSE (O), dieselbe MSE
multipliziert mit 1/sigma² (S) und der diagonale Kovarianzpfad (K).
Ein eigenes Requestformat und eigene Quellenbindungen lassen historische
Suchprofile und Ergebnisse unverändert. Der feste Strukturvergleich prüft
identische Startwerte und Neustartziehungen; freie Suchen behalten 300/5,
Grammatik und bisherige Trainingsverlust-Auswahl.

## Befehle

In einem sauberen Checkout des später dokumentierten Ausführungscommits:

```bash
uv sync --locked --dev
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
taskset -c "$(python -c 'import os; print(min(os.sched_getaffinity(0)))')" \
  uv run --locked python scripts/check_white_scaling.py \
  --output results/white-scaling-technical-001
```

Danach der im Plan begrenzte Entwicklungsversuch. Neue Ausgabeordner verwenden;
vorhandene Läufe werden nicht überschrieben. Ein einzelner logischer CPU-Kern
und begrenzte Julia-/BLAS-Threads gehören zum gebundenen Laufweg.

```bash
taskset -c "$(python -c 'import os; print(min(os.sched_getaffinity(0)))')" \
  uv run --locked python scripts/run_white_scaling.py run \
  results/white-scaling-001
uv run --locked python scripts/run_white_scaling.py verify \
  results/white-scaling-001
uv run --locked python scripts/run_white_scaling.py export \
  results/white-scaling-001 --output results/white-scaling-plots-001
```

Fortschritt in einem zweiten Terminal, rein lesend:

```bash
watch -n 10 'uv run --locked --no-sync python scripts/run_white_scaling.py status results/white-scaling-001'
```

Diese Anzeige zeigt den gespeicherten Stand; Strg+C beendet nur die Anzeige.
Die lesende Verifikation verlangt denselben gebundenen Ausführungsstand.
Umgebungsvorbereitung und technische Checks sind von der wissenschaftlichen
Serienzeit getrennt. Bestehende globale und historische Prüfungen bleiben
zusätzlich Bestandteil der vollständigen Ready-CI.
