# Verlustskalierung und gezielte Formelauswahl: Laufweg und Befund

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
an einer neuen Elternprüfung abgebrochen. Der getrennte Lauf
`white-scaling-cloud-002` auf `5ae263a5cddd65417aa5d5466646218168d074e7`
ist mit unverändertem Plan vollständig abgeschlossen und lesend geprüft:
72 feste Optimierungen, 18 freie Kurzsuchen und drei exakt reproduzierte
Wiederholungen. Die Verlustskalierung verändert Suchpfade und freie Ergebnisse,
begründet bei zwei Rauschfenstern aber keine allgemeine Methodenrangfolge.
Die anschließende [Auswahlprüfung](offgrid_selection_plan.md) ist nach diesem
Befund gesondert in `6f41817cd0102d7a204a4e28cb5b3a77fc74271f` vorab festgelegt.

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

## Abgeschlossene feste Stufe und numerischer Mechanismus

Der getrennte Lauf 002 auf `5ae263a5cddd65417aa5d5466646218168d074e7`
hat alle 72 festen Optimierungen abgeschlossen. Die unabhängige skalare
Nachrechnung bestätigt gegenüber 001 bitgleiche Eingaben, Originalbäume,
Vorhersagen, Residuen, Parametertraces, Callbackzahlen und Zufallszustände.
Das sind dieselben zwei Rauschfenster, keine zusätzliche Stichprobe.
Die feste Stufe allein begründet keine allgemeine Aussage über freie
Formelfindung; die abgeschlossene freie Stufe steht getrennt unten.

Die drei getrennten Verlustpfade sind gewöhnliche MSE (O), dieselbe MSE
multipliziert mit 1/sigma² (S) und der diagonale Kovarianzpfad (K).
Ein eigenes Requestformat und eigene Quellenbindungen lassen historische
Suchprofile und Ergebnisse unverändert. Der feste Strukturvergleich prüft
identische Startwerte und Neustartziehungen; freie Suchen behalten 300/5,
Grammatik und bisherige Trainingsverlust-Auswahl.

Alle 432 tatsächlichen Startzustände der lokalen Optimierungen stimmen mit
den vorgeschriebenen Start-/Neustartwerten überein. Bei je 24 gepaarten
Vergleichen unterscheiden sich die Parameterpfade ab dem ersten Update;
die Endvorhersagen bleiben praktisch gleich:

| Vergleich | Paare | Größtes absolutes Delta der abschließenden MSE | Größte Vorhersagedifferenz/A auf dem unregelmäßigen Prüfraster |
| --- | --- | --- | --- |
| S gegen O | 24 | 6,46e−17 | 3,19e−8 |
| K gegen S | 24 | 1,73e−18 | 1,58e−9 |

Die feste bekannte Familie erreicht über alle Starts und Suchseeds etwa
1,2801 % bzw. 1,5231 % RMSE/A in den beiden Rauschfenstern. Die vorgegebene
Familie ist privilegiertes Entwicklungswissen, keine frei wiederentdeckte
Struktur und kein Argument für ihre Knotenzahl als allgemeine Suchgrenze.
Die Callbacksummen O/S/K sind 116.613 / 98.844 / 99.327; die gemessenen
Einzelzeiten enthalten Erstkompilierung und begründen keine allgemeine
Geschwindigkeitsrangfolge.

Die gepinnten Quellen von SymbolicRegression 2.5.1 und Optim 2.2.2 erklären,
warum mathematisch äquivalente Verlustskalierungen verschiedene Pfade erlauben.
Der evolutionäre Kostenwert verwendet
`loss / max(baseline_loss, 0.01) + complexity * parsimony`; die Baseline
wird ebenfalls mit dem jeweiligen Verlust berechnet. Oberhalb der Untergrenze
kürzt sich ein gemeinsamer positiver Faktor mathematisch heraus. Die lokale
Konstantenoptimierung erhält dagegen den rohen Verlust: BFGS beginnt mit der
Einheitsmatrix als inverser Hesse-Näherung und einer Backtracking-Liniensuche.
Damit sind bereits die ersten Schritte nicht allgemein skalierungsinvariant.
Die unveränderte absolute Gradientenschranke `g_abstol=1e-8` entspricht zudem
verschiedenen Schranken in MSE-Einheiten. Sie ist eine mögliche weitere
Einflussstelle, aber kein nachgewiesener Abbruchgrund eines konkreten Fits:
Der native Aufrufer verwirft die lokalen Optim-Ergebnisobjekte.

Der Befund weist somit Pfadabhängigkeit nach, keine praktische Verbesserung
der festen Endkurven und keinen Fehler des diagonalen Kovarianzkerns.
Rundung, diskrete Auswahl und andere lokale Optimierer bei einzelnen freien
Bäumen müssen getrennt berücksichtigt werden. Insbesondere ist Newton für einen einzelnen skalaren Parameter
nicht durch den BFGS-Feststrukturvergleich abgedeckt.

Diese Trennung von evolutionärer Suche, Konstantenoptimierung und Auswahl
entspricht [Cranmer (2023)](https://arxiv.org/abs/2305.01582).
[Keijzers (2003) „linear scaling“](https://groups.csail.mit.edu/EVO-DesignOpt/groupWebSite/uploads/Site/keijzer-improving-symbolic-regression-interval-arithmetic-linear-scaling-eurogp-2003.pdf)
bezeichnet einen affinen Ausgabefit und ist nicht mit unserem positiven
Verlustfaktor gleichzusetzen. Die tatsächlich gelesenen Paketquellen und
ihre Hashes bleiben im Nachweispaket erhalten.

## Vollständige freie Stufe und begründeter Anschluss

Mittlerer sauberer RMSE/A auf den 1024 unregelmäßigen Prüfpunkten, je Fenster
über die drei vorbestimmten Suchseeds; die drei Prozesswiederholungen sind
aus diesen Mitteln ausgeschlossen:

| Rauschfenster | O: MSE | S: skalierte MSE | K: diagonaler Kovarianzpfad |
| --- | ---: | ---: | ---: |
| 1 | 13,2005 % | 3,9093 % | 12,7062 % |
| 2 | 9,1395 % | 2,6180 % | 12,9692 % |

S hat in fünf von sechs gepaarten Suchaufrufen kleineren unregelmäßigen RMSE
als O; ein Unterschied beträgt dabei lediglich 0,000925 Prozentpunkte.
K verbessert diesen Endpunkt in einem von sechs Paaren gegenüber S,
die Trainings-MSE in keinem. In beiden Kontrasten ändern sich alle sechs
ursprünglichen Fronten und ausgewählten Bäume. Sämtliche drei vorbestimmten
Wiederholungen reproduzieren Front, Auswahl und Callbackzahl exakt.
Die gewöhnlichen Baselines betragen 0,0489228 und 0,0444343; die Untergrenze
0,01 ist in allen Armen inaktiv. Sie erklärt diese Unterschiede somit nicht.
Gleiche Anfangsseeds belegen keine identischen späteren Zufallszüge oder
Populationen nach divergierender Suche. Zwei unabhängige Rauschfenster und
100 äußere Iterationen erlauben weder eine universelle Rangfolge noch einen
gesicherten Langbudgetvorteil von S. Historische Verlustprofile bleiben erhalten.

Der Originalbaum `white-02-seed-2026112312-covariance` enthält den linearen Term
`sin(90.90624942174962*((t*(0.7944755598450789+300.73558476534595))+23.104196569256864))`.
Seine Frequenz ist 4362,590873 Hz, der Alias auf dem 4096-Hz-Raster
266,590873 Hz. Die exakte Rasteridentität betrifft diesen Term; bei direkter
Float64-Nachrechnung beträgt die maximale Abweichung 5,07e−13. Auf den
unregelmäßigen Prüfpunkten beträgt der RMS-Unterschied der beiden Sinusterme
0,98235. Die vollständige Originalformel wird weder ersetzt noch vereinfacht.
Ihr sauberer unregelmäßiger RMSE beträgt 29,3185 % A.

Ein anderer konkreter Gegenvergleich ist Fenster 1, Seed 2026112313:
O mit nur 15 Knoten erreicht 23,3085 % A, S mit 17 Knoten 1,4234 % A.
Zusammen mit den bereits gespeicherten besseren Alternativen der Folgestudie
begründet das eine gezielte Auswahlprüfung mit zusätzlicher Messinformation;
eine pauschale niedrigere Komplexitätsgrenze folgt daraus nicht.
[VanderPlas (2018)](https://arxiv.org/abs/1703.09824) erklärt die Rolle des
spektralen Fensters und die Grenzen bloßer Unterteilungen desselben Uniformrasters.
Ungleichmäßige Messzeiten garantieren gleichwohl keine richtige Formel.

Der gesonderte Anschlussplan vergleicht alle 156 ursprünglichen Pakete mit
Originalauswahl, 128 neuen verrauschten Werten auf dem bisherigen Raster und
128 auf einem neuen unregelmäßigen Raster. Primär ist Off-grid minus Same-grid,
getrennt nach sechs Armen und zwei Rauschmodellen. Originalbäume, Konstanten,
Suchbudgets und Komplexitätsgrenze bleiben unverändert. Wahrheit bleibt aus
der Auswahl-API ausgeschlossen. Diese zusätzliche synthetische Beobachtung
ist Entwicklungsinformation und lässt sich nicht nachträglich aus einem
einzelnen realen GW-Ereignis erzeugen.

## Abschlussbelege und Kosten von Lauf 002

Der separate gebundene Verifier besteht. Die unabhängige Nachrechnung bestätigt
39 erfolgreiche Prozesse, alle Originalfronten, die vollständigen Zellmengen,
die Kosten und 1132 unveränderte Quelldateien. Audit-SHA-256:
`c9a2ddf6872a35eb2014956daf018db40d8d18f63e65b3b2b5d714528246b84e`;
Originalmanifest-SHA-256:
`255223ba1bc8c653b75e9399a49e4ac83c86548f619ec58b9532965d87d9b3b3`.
Der separate Formelbeleg bindet die genannten Alias-/Komplexitätsgegenbeispiele.

Ein späteres KI-basiertes Integrationsreview an `f6cfced` gegen `3ee6e22`
findet zwei Lücken im neuen Laufweg: einige ungeprüfte Kostenfelder und fehlende
Quellenbindung während des Plotexports. Die wissenschaftliche Ausführung auf
5ae bleibt unverändert. Ein unabhängiger Kosten-/Bestandsaudit und ein externer
Exportguard ergänzen diese konkreten Prüfungen rein lesend. Der Guard bindet
alle 93 ursprünglichen Formelobjekte, alle 93 PNGs und sämtliche Punktdaten;
284 Nutzdateien werden erst nach vollständiger Prüfung veröffentlicht.
Sein SHA-256 lautet
`4105e1adb4f24bc2f0aa4066e669ab32fd806c71bb3fda4b078aa27eed6c47af`.
Die korrigierte Implementierung für künftige Läufe prüft zusätzlich
verschachtelte Zeiten und erhält Primärfehler sowie bekannte CPU-Teilkosten
auch bei einem sekundären Schreibfehler. Ältere Kostenschemata werden nicht
nachträglich umgeschrieben oder als neue Messung ausgegeben.

Serienwandzeit: **2729,867 s = 45 min 29,867 s**, nach Vorbereitung der Eingaben.
Darin enthalten sind 786,739 s feste und 1934,688 s freie Worker;
verschachtelte Zeiten nicht addieren. Gemessene CPU der beendeten Worker:
2586,746 s User und 119,587 s System (`RUSAGE_CHILDREN`). Die vollständige
Serien-CPU einschließlich Treiber wurde in dieser Ausführungsfassung nicht
gemessen. Der vorherige Abbruch 001 und technische Vorlauf bleiben separat
mit ihren Kosten und Archiven im [Ergebnisindex](results_index.md) erhalten.

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
