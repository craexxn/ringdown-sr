# Ergebnisindex und Archivierungsstand

Stand: 22.11.2026. Zentraler Wegweiser zu den belegten Versuchen und ihren
nachträglichen Bewertungen; [Ablagerichtlinie](results_archiving.md).
Serien sind die Indexeinheit, ihre Zellen/Wiederholungen bleiben im Originalbericht.
Die Aufstellung ist keine Behauptung, dass alle jemals lokal erzeugten Ergebnisse
bereits erfasst oder gesichert seien.

**Archivierung offen:** Dauerhafte Ablage und eine geprüfte zweite Kopie sind
hier noch nicht bestätigt. Lokal verfügbare Arbeitskopien werden nicht als
bereits geprüfte Sicherung gezählt. GitHub-Releases sind optional; ein fehlender
Upload oder Downloadlink verhindert den Abschluss der lokalen Archivierung nicht.

Für den [globalen Neustartvergleich](global_restart_comparison.md) sind
[Abbruch 001](global_restart_results_manjaro_001.md) und der vollständig
abgeschlossene [Lauf 002](global_restart_results_manjaro_002.md) an den gelieferten
Paketen geprüft. Auch der [Iterations-/Zeitbudgetlauf 001](iteration_time_results_manjaro_001.md)
ist abgeschlossen und lesend bestätigt: acht frische Suchen auf `4df7eca`,
mitgelieferte `-call.json`-Aufrufmessung und separater Verify-Export geprüft.
Ausführungscommit und Archiv-SHA-256 sind unten zugeordnet. Für alle Archive
bleiben beide gesicherten Ablageorte und die Prüfung ihrer Kopien nachzutragen.
Technische Fixtures und ein implementierter Laufweg sind keine wissenschaftliche
Ausführung und kein Sicherungsnachweis.

Aktueller Ergebnisstand vom 22.11.2026: Die
[Auswertung und Nachprüfung der Folgestudie](noise_followup_results_manjaro_001.md)
bindet 624 erfolgreiche Einzelworker und 156 erfolgreiche Paketausgaben an
Ausführungscommit `8a1a4a1437f4b01daf1f070b56add248074c5907`.
Originalarchive für Dauer/Messraster und eine Shared-Prüfkopie sind empfangen;
39 lange Rauschdateien sind exakt aus ihren gebundenen Zuständen rekonstruiert.
Berichtsstatistik, Workerzensus, Eingaben, Schätzer und Originalplots sind geprüft;
beide offiziellen Serienreplays sind bestanden; die frischen Exporte sind bytegleich.
Beide primären Intervalle umfassen null; der mittlere Rastereffekt wird von
zwei Uniform-K-Fehlern getragen. Die 48 Schätzerdateien wiederholen bytegleich
dieselben Entwicklungsfälle. [Original- und Übersichtseintrag](#wissenschaftliche-folgestudie-manjaro-001)
trennen Originalarchive, rekonstruierte Nutzdaten, den nur berichteten Hash der
ursprünglichen komprimierten Shared-Bytes und die weiterhin offene Sicherung.

Historischer Planungs-/Implementierungsstand vom 19.11.2026: Die
[Folgestudie zu Hintergrunddauer und Messraster](noise_followup_plan.md)
ist in [PR #102](https://github.com/craexxn/ringdown-sr/pull/102)
implementiert, Planbindung `a37bf90fe439619fd263d6c06d868c6ff4ea00e8`.
Vorgesehen sind 26 frische Fälle und 624 neue Worker (A: 416, B: 208);
die 52 gemeinsamen Uniform-O/K-Pakete aus A erscheinen in B als
Kontrollreferenzen ohne neue Suchkosten. Die [Entwicklungsabnahme](noise_followup_development_001.md)
belegt 48 Kovarianz-/PSD-/ACF-Schätzungen und sechs kurze technische Worker,
jeweils mit separater lesender Prüfung. Noch kein wissenschaftlicher Suchlauf
oder zugehöriges Ergebnisarchiv nachgewiesen. Das separate Entwicklungsarchiv
ist unten eingeordnet; vollständige Ready-CI und Freigabestand stehen im PR.
[Prüfstand](representation_implementation_status.md) und
[Lauf-/Export-/Archivbefehle](noise_followup.md) führen die nächsten Schritte.
Künftige Originalformeln, Plots und vollständige Punkt-CSV sind separat
mit den jeweiligen Originalergebnissen und Kontrollreferenzen zu binden.

Die [unabhängige Bestätigung 001](restart_confirmation_results_manjaro_001.md)
ist auf `c3da991` ausgeführt und am Original vollständig lesend bestätigt:
`confirmation-anchor-manjaro-001`, `confirmation-low-manjaro-001` und
`confirmation-high-manjaro-001`, je 50 abgeschlossene Suchen mit eigener
Aufrufmessung, gemeinsame `restart-confirmation-manjaro-001-verification`.
Der technische Manjaro-Vorlauf mit sechs kleinen Workern und Einzel-/Gesamtprüfungen
ist im selben Originalarchiv enthalten und ebenfalls bestätigt. Keine Ausfälle;
die wissenschaftliche 8/10-Grenze ist beim dritten Signal verfehlt. Archivhash,
Ausführung, Prüfung und weiterhin offene Sicherung sind unten getrennt zugeordnet.

Der [Zeitkoordinatenvergleich 001](time_coordinate_results_manjaro_001.md) ist
auf `91d461c` nach PR83 ausgeführt und vollständig lesend bestätigt: 16
wissenschaftliche Suchen in drei Abschnitten sowie vier technische Vorlaufworker.
Die vorab festgelegte Einordnung ist gemischt; Original und separates Audit
sind unten zugeordnet. Keine neue unabhängige Bestätigung und keine
stillschweigende Übernahme der gedehnten Zeitkoordinate.

Der [Vergleich zweier Neustartpakete 001](restart_budget_results_manjaro_001.md)
ist auf `680af98` nach PR85 am 12.11.2026 ausgeführt und am 13.11.2026 als
Originalarchiv empfangen: 48 wissenschaftliche Suchen, 16 Paketausgaben,
zwölf technische Vorlaufworker. Die vorab festgelegte Einordnung ist gemischt;
Ausführung, lesender Prüfstand und offene Sicherung sind unten getrennt zugeordnet.

Die [erneute Bestätigung 001](restart_budget_confirmation_results_manjaro_001.md)
ist auf `6bc0282` nach vollständiger CI und Übernahme von PR87 am 13./14.11.2026
ausgeführt: drei neue Signaldefinitionen, 180 frische Suchen und 60 Paketausgaben.
Das am 14.11.2026 aus vier Teilen zusammengesetzte Originalarchiv umfasst alle
drei Abschnitte samt benachbarten `-call.json`, technischen Vorlauf und
Gesamtverifikation. R erfüllt mit 10/10, 10/10, 9/10 gemeinsamen Erfolgen die
praktische Grenze; L mit 9/10, 7/10, 7/10 nicht. Wissenschaftliche und technische
Verifikation sind vollständig lesend bestätigt; alle zwölf Verify-Exporte bytegleich. Eingefrorener Plan weiterhin `352b7b5`; keine
Umwidmung der belegten 001-IDs für neue Läufe und kein Sicherungsnachweis aus
der bloßen Verfügbarkeit der Arbeitskopie.

Der [144er-Rauschpilot](noise_pilot_plan.md) ist beschlossen und sein
[Serienlaufweg](noise_pilot.md) mit PR92 übernommen. Der technische
Manjaro-N128-Vorlauf ist am Originalarchiv lesend bestätigt; drei erfolgreiche
Zehnerworker. Auch der [wissenschaftliche Lauf 001](noise_pilot_results_manjaro_001.md)
ist nun vollständig lesend bestätigt: 144 abgeschlossene Suchen, 36 Paketausgaben,
keine Ausfälle. Die beiden [Archiveinträge unten](#wissenschaftlicher-rauschpilot-manjaro-001)
trennen technischen Vorlauf, wissenschaftlichen Befund und weiterhin offene Sicherung.

Die am 16.11.2026 beschlossene [520er-Hintergrundstudie](noise_background_plan.md)
ist mit PR94 als Protokoll übernommen; der [getrennte Laufweg](noise_background.md)
ist nach vollständiger Ready-CI mit PR95 als
`bd42634b888c2dbaa5a92726b9a1f9851c766a48` übernommen. Der neue
[technische Manjaro-Vorlauf](#technischer-hintergrundstudien-vorlauf-vom-16112026)
mit fünf N128-Zehnerworkern, separatem Replay und Plot-/Formelprüfung ist
am Originalarchiv lesend bestätigt. Prüfstände und Ressourcenentscheidung
stehen im [Fortsetzungsstand](representation_implementation_status.md).
Ein danach gemeldeter wissenschaftlicher Ausführungsversuch mit 26
vorbereiteten Eingaben ist nach einem belegten System-Suspend im Fit von
`ar1-01/estimated_64/member-04` durch den Uhrenintegritätswächter gesperrt.
Übermittelte monotone Fitzeit 368,390180243 s, Serienabbruchzeit
4.674,278524944 s; Suspend nicht enthalten, CPU-Messung unvollständig.
Das inzwischen hochgeladene Abbrucharchiv 001 ist wegen der Downloadgrenze
noch nicht selbst geprüft. Für den getrennten Versuch 002 liegt inzwischen
das hashgeprüfte vollständige Archiv mit erfolgreichem repariertem Plotexport
vor. Plot-, Statistik- und Herkunftsaudits sowie die eigene vollständige
Serienverifikation bestehen. Der [Ergebnisbericht](noise_background_results_manjaro_002.md)
ordnet alle 130 Originalausgaben und den begrenzten wissenschaftlichen Befund ein.
Die [wissenschaftlichen Archiveinträge](#wissenschaftliche-hintergrundstudie-manjaro-001-und-002)
trennen diese Belegstände. Kosten und Messgrenzen stehen im Fortsetzungsstand.
Originale unverändert bewahren und lesend prüfen; kein automatischer Neustart
oder Umbuchen als numerischer Fehler. Der Abbruch von 001 und seine Kosten
bleiben nach der getrennten Wiederholung erhalten.
Keine Umwidmung alter Pilotarchive. Spätere wissenschaftliche Plot-/Formel-
Exporte werden mit dem Original und seinen Prüfsummen verknüpft.

Lokales Implementierungsprüfpaket vom 16.11.2026:
`noise-background-local-preflight-002.tar.gz`, SHA-256
`278bebe181fc9bc9f6ed5916f4f82aa76ef4b8511414400ef2ce0ab697eaf3bc`.
Es enthält ausschließlich den technischen N128-Vorlauf auf
`cfa2ff54ae773f4c33a42c6f8847b592a6f568b1`, seine fünf Zehnerworker sowie
separate Plots, unveränderte Originalformeln, Punktdaten und Exportkosten.
Alle 165 Originaldateien blieben bei Replay und Plotexport unverändert;
keine wissenschaftliche Serie oder Manjaro-Abnahme. Das Paket wurde damals
nur im lokalen Arbeitsbereich unter `results/` abgelegt; gemeinsame Archivablage und
unabhängige Zweitkopie sind nicht bestätigt. Der zuvor gesperrte technische
Vorlauf 001 bleibt unverändert im Arbeitsbereich erhalten; sein Befund und
seine Abbruchkosten stehen im Fortsetzungsstand, er ist nicht Teil dieses Pakets.

## Archivablage

Die gemeinsamen Ablagehinweise werden einmal hier gepflegt. Die Dateinamen in
den Tabellen bezeichnen die einzelnen Archive innerhalb dieser Ablage.
Verweise auf diesen Abschnitt sind eine Zuordnung zur vorgesehenen Ablage,
keine Bestätigung, dass die jeweilige Datei dort bereits gesichert ist.

| Kopie | Ablagehinweis | Prüfstand |
| --- | --- | --- |
| Gemeinsamer Archivordner | Noch festzulegen; verständliche Bezeichnung genügt | Noch nicht bestätigt |
| Zweite Kopie auf unabhängigem Datenträger oder im bestehenden Backup | Noch zu benennen | Noch nicht bestätigt |

Nach Prüfung beider Kopien gegen den dokumentierten SHA-256 wird der
Sicherungsstand des jeweiligen Eintrags bestätigt. Optionale Downloadlinks
können nach geprüftem Rückdownload ergänzt werden; hierfür besteht keine Pflicht.

## Leseschlüssel und Quellen

- Laufstatus beschreibt Durchführung/Vollständigkeit; ein negativer
  wissenschaftlicher Befund ist kein technischer Abbruch.
- Ausführungscommit stammt aus den bezeichneten Herkunftsnachweisen. „Nur
  vorgegeben“ oder „nicht belegt“ darf nicht als tatsächlich ausgeführt gelesen
  werden. Bei externen Treibern werden beide Codeanteile genannt.
- Originalbewertung meint die im jeweiligen Ausführungsstand gebundenen Regeln.
  Die aufgeführten `ringdown-sr-*`-Bezeichner sind die Originalberichtformate,
  keine nachträglich vereinheitlichte Bewertungsfassung. Methodische Details
  und damalige Pläne stehen im verlinkten Bericht. **R1–R3** bezeichnen die
  getrennten retrospektiven Bewertungen im Abschnitt unten.
- Berichtscommits ergeben sich aus der Git-Historie der verlinkten Datei.
  Ausführungs-, Dokumentations- und Bewertungscommit werden nicht ausgetauscht.
  Ein baumgleicher Merge oder der heutige `main` ist kein Ersatz für die
  aufgezeichnete Commit-ID. Die bei Anlage des Index verlinkten 25 Commits waren am
  06.11.2026 über die GitHub-API erreichbar; das ersetzt keine dauerhafte
  Ref-Sicherung für Stände außerhalb der main-Historie.
- Die vier großen Ausgangsserien sind bereits maschinenlesbar in
  [supplemental_series.json](../data/supplemental_series.json) gebunden. Diese
  Werte wurden samt vier lokalen Originalarchiven erneut abgeglichen. Bei
  älteren Serien werden die Nachweise der vorhandenen Berichte übernommen;
  damit ist kein pauschaler erneuter Originalarchivaudit behauptet. Am
  06.11.2026 gezielt nachgeprüft wurden der
  [Seed-/Treiber-Kreuzvergleich](seed_driver_crosscheck_results_manjaro_001.md),
  die [beiden frühen rauschfreien Serien](early_control_archive_audit_001.md) und
  der [abgebrochene Neustartlauf 001](global_restart_results_manjaro_001.md).

## Entwicklungsversuche und numerische Kontrollserien

Die Lauf-ID verbindet diese Übersicht mit genau der gleichnamigen Zeile in
„Originalarchive“. WSL2 und Manjaro bleiben getrennte Beobachtungen.

| Lauf-ID / Fragestellung | Tatsächlicher Ausführungsstand | Laufstatus | Originalbewertung / Ergänzung | Ergebnisbeleg |
| --- | --- | --- | --- | --- |
| `noiseless-control-001` — Rauschfreie freie Suche bei drei äußeren Budgets | [`bc80b4f07773ffb6d57a927ef3daaee34f9a7817`](https://github.com/craexxn/ringdown-sr/commit/bc80b4f07773ffb6d57a927ef3daaee34f9a7817) | Abgeschlossen; 9 Zellen und 28 Kandidaten lesend bestätigt, kein Kurvenerfolg | `ringdown-sr-noiseless-control-1`; damalige Originalregeln | [Historischer Bericht](noiseless_control_results_manjaro_001.md), [Quellenaudit](early_control_archive_audit_001.md) |
| `representation-manjaro-001` — Zeitkoordinate und Komplexitätshäufigkeitsschalter | [`4057caaffd9c4de5791ded14431c6e289db75b73`](https://github.com/craexxn/ringdown-sr/commit/4057caaffd9c4de5791ded14431c6e289db75b73) | Abgeschlossen; 9 Zellen, kein Kurvenerfolg | `ringdown-sr-representation-control-1` | [Bericht](representation_control_results_manjaro_001.md) |
| `constant-manjaro-001` — Lokales Optimiererbudget bei festem Ringdown-Baum | [`0a70f19e16e173aedf2e071a5f5b09d045ecbf69`](https://github.com/craexxn/ringdown-sr/commit/0a70f19e16e173aedf2e071a5f5b09d045ecbf69) | Abgeschlossen; 48 Backendaufrufe | `ringdown-sr-constant-diagnostic-1` | [Bericht](constant_diagnostic_results_manjaro_001.md) |
| `free-budget-manjaro-001` — Freie Suche mit lokal 20/2 gegenüber 100/2 | [`8bdc8dbc498be6e8527fa2a857293bf74b42f81f`](https://github.com/craexxn/ringdown-sr/commit/8bdc8dbc498be6e8527fa2a857293bf74b42f81f) | Abgeschlossen; 6 Zellen und 50 Kandidaten lesend bestätigt, kein Kurvenerfolg | `ringdown-sr-free-optimizer-budget-1`; damalige Originalregeln | [Historischer Bericht](free_optimizer_budget_results_manjaro_001.md), [Quellenaudit](early_control_archive_audit_001.md) |
| `trajectory-manjaro-001` — Beobachtete Zwischenbäume und Verlustreplay | [`41ccdd27aaa4ade56b509493089241d6695b9757`](https://github.com/craexxn/ringdown-sr/commit/41ccdd27aaa4ade56b509493089241d6695b9757); [Herkunftsfixture](../tests/fixtures/search_trajectory_replay_cases.json) | Abgebrochen: 2 Zellen fertig, Zelle 3 fehlgeschlagen, 4–6 nicht ausgeführt | `ringdown-sr-search-trajectory-1` | [Bericht](representation_implementation_status.md) |
| `trajectory-manjaro-002` — Frische Suchbeobachtung mit getrennter Replayprüfung | [`f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1`](https://github.com/craexxn/ringdown-sr/commit/f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1) | Abgeschlossen; 6 Zellen, kein Kurvenerfolg | `ringdown-sr-search-trajectory-2` | [Bericht](search_trajectory_results_manjaro_002.md) |
| `grammar-manjaro-001` — Direkte und entfernte trigonometrische Verschachtelung | [`23a21131e6fafcdc748e47098c018a1158f1629b`](https://github.com/craexxn/ringdown-sr/commit/23a21131e6fafcdc748e47098c018a1158f1629b) | Abgeschlossen; 6 Zellen, beide Bedingungen 0/3 | `ringdown-sr-trigonometric-grammar-1` | [Bericht](trigonometric_grammar_results_manjaro_001.md) |
| `duration-manjaro-001` — Äußeres Suchbudget 200/2.000 bei zwei Grammatiken | [`4a9286bfe1aa49db3eda174a3aa14c69f1160e74`](https://github.com/craexxn/ringdown-sr/commit/4a9286bfe1aa49db3eda174a3aa14c69f1160e74) | Abgebrochen: 2 Zellen fertig, Zelle 3 fehlgeschlagen, 4–20 nicht ausgeführt | `ringdown-sr-search-duration-1` | [Bericht](search_duration_results_manjaro_001.md) |
| `duration-manjaro-002` — Äußeres Suchbudget 200/2.000 bei zwei Grammatiken | [`76a740018b4426bc1651a5fed3bf214659a083cf`](https://github.com/craexxn/ringdown-sr/commit/76a740018b4426bc1651a5fed3bf214659a083cf) | Abgebrochen: 4 Zellen fertig, Zelle 5 fehlgeschlagen, 6–20 nicht ausgeführt | `ringdown-sr-search-duration-2` | [Bericht](search_duration_results_manjaro_002.md) |
| `duration-manjaro-003` — Äußeres Suchbudget 200/2.000 bei zwei Grammatiken | [`e501e9d83315289cb4c59716495e93aa25154ecd`](https://github.com/craexxn/ringdown-sr/commit/e501e9d83315289cb4c59716495e93aa25154ecd) | Abgebrochen: 4 Zellen fertig, Zelle 5 fehlgeschlagen, 6–20 nicht ausgeführt | `ringdown-sr-search-duration-3` | [Bericht](search_duration_results_manjaro_003.md) |
| `duration-manjaro-004` — Äußeres Suchbudget 200/2.000 bei zwei Grammatiken | [`79ff670b825efd8ba0e999edb983aec6f7e804ae`](https://github.com/craexxn/ringdown-sr/commit/79ff670b825efd8ba0e999edb983aec6f7e804ae) | Abgeschlossen; 20 Zellen | `ringdown-sr-search-duration-4`; zusätzlich [R1–R3](#nachträgliche-bewertungen) | [Bericht](search_duration_results_manjaro_004.md) |
| `local-optimizer-manjaro-001` — Lokale Iterations- und Neustartbudgets | [`cf04476057b95c1517e1a303f4b48fbd30545a47`](https://github.com/craexxn/ringdown-sr/commit/cf04476057b95c1517e1a303f4b48fbd30545a47) | Abgeschlossen; 20 Zellen | `ringdown-sr-local-optimizer-1`; zusätzlich [R1–R3](#nachträgliche-bewertungen) | [Bericht](local_optimizer_results_manjaro_001.md) |
| `outer-ladder-manjaro-001` — Äußere Staffel 200/500/2.000/5.000 bei lokal 300/5 | [`5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4`](https://github.com/craexxn/ringdown-sr/commit/5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4) | Abgeschlossen; 20 Zellen | `ringdown-sr-outer-search-ladder-1`; zusätzlich [R1–R3](#nachträgliche-bewertungen) | [Bericht](outer_search_ladder_results_manjaro_001.md) |
| `transfer-manjaro-001` — Übertragung des Profils 500/300/5 auf sechs Signale | [`bc4025d13b4954dee779341026d282430521686a`](https://github.com/craexxn/ringdown-sr/commit/bc4025d13b4954dee779341026d282430521686a) | Abgeschlossen; 18 Zellen | `ringdown-sr-transfer-check-1`; zusätzlich [R1–R3](#nachträgliche-bewertungen) | [Bericht](transfer_check_results_manjaro_001.md) |
| `seed-driver-crosscheck-manjaro-001` — Folgt das Ergebnis dem Seed oder historischen Treiber? | Orchestrierung [`8096ddb8bb6fd065eb1079c7902a2016334a6e6b`](https://github.com/craexxn/ringdown-sr/commit/8096ddb8bb6fd065eb1079c7902a2016334a6e6b); historische Worker im Bericht | Abgeschlossen; zwei Zellen, 18 Kandidaten lesend bestätigt | `ringdown-sr-seed-driver-crosscheck-1`; getrennte A–D-Einordnung, kein Import in R1–R3 | [Bericht](seed_driver_crosscheck_results_manjaro_001.md) |
| `global-restarts-manjaro-001` — Globale Neustarts gegenüber längerer Einzelsuche | Orchestrierung [`b547bb3b1753235960cc0654f8cebd747fc1b2f3`](https://github.com/craexxn/ringdown-sr/commit/b547bb3b1753235960cc0654f8cebd747fc1b2f3); historischer Worker `5215c5e` | 19 Zellen fertig, Zelle 20 unterbrochen; Teilkosten und gesperrter Abschluss geprüft | Kein freigegebener Serienvergleich | [Abbruchbericht](global_restart_results_manjaro_001.md) |
| `global-restarts-manjaro-002` — Getrennte vollständige Wiederholung | Orchestrierung [`b547bb3b1753235960cc0654f8cebd747fc1b2f3`](https://github.com/craexxn/ringdown-sr/commit/b547bb3b1753235960cc0654f8cebd747fc1b2f3); historischer Worker `5215c5e` | Abgeschlossen; 20 Zellen, 190 Kandidaten, Original und Verify-Export lesend bestätigt | `ringdown-sr-global-restart-comparison-1`; A: Referenz 1/4, lang 4/4, Pakete 4/4; Familie und Kosten getrennt | [Ergebnisbericht](global_restart_results_manjaro_002.md) |
| `iteration-time-manjaro-001` — 2.000 Iterationen gegenüber 400 Sekunden | [`4df7ecaaaed0a6d235f7db104c6982bdfcabf048`](https://github.com/craexxn/ringdown-sr/commit/4df7ecaaaed0a6d235f7db104c6982bdfcabf048) | Abgeschlossen; 8 frische Zellen, 76 Kandidaten, Aufrufmessung und Verify-Export lesend bestätigt | `ringdown-sr-iteration-time-comparison-1`; I 4/4 A, Z 3/4 A; beide 3/4 A plus Familie | [Ergebnisbericht](iteration_time_results_manjaro_001.md) |
| `restart-confirmation-manjaro-001` — Unabhängige Bestätigung von 4 × 500 gegenüber 1 × 2.000 | [`c3da991f389a4ec55206539ebe02a9648d4474b8`](https://github.com/craexxn/ringdown-sr/commit/c3da991f389a4ec55206539ebe02a9648d4474b8) | Alle 150 wissenschaftlichen Zellen und 1.755 Kandidaten in drei Abschnitten lesend bestätigt; technischer Vorlauf mit 6 Workern separat bestätigt | R: 8/10, 10/10, 4/10 A plus Originalfamilie; I: 4/10, 5/10, 7/10; praktische Grenze verfehlt, keine Ausfälle | [Ergebnisbericht](restart_confirmation_results_manjaro_001.md) |
| `time-coordinate-manjaro-001` — Physische und gedehnte Zeit bei je 1 × 2.000 | [`91d461cf9c08c07b7fdb8ddae5ad4b207135bc67`](https://github.com/craexxn/ringdown-sr/commit/91d461cf9c08c07b7fdb8ddae5ad4b207135bc67) | Alle 16 wissenschaftlichen Zellen und 188 Kandidaten lesend bestätigt; technischer Vorlauf mit 4 Workern separat bestätigt | T/U A: 2/2–2/2, 2/2–1/2, 1/4–3/4; gemeinsame Familienerfolge: 0/2–0/2, 2/2–0/2, 1/4–2/4; gemischt, keine Ausfälle | [Ergebnisbericht](time_coordinate_results_manjaro_001.md) |
| `restart-budget-manjaro-001` — 4 × 1.000 gegen 2 × 2.000 bei lokal 300/5 | [`680af98e4342dc831a6dcc995fe658d4fcbe942f`](https://github.com/craexxn/ringdown-sr/commit/680af98e4342dc831a6dcc995fe658d4fcbe942f) | Alle 48 wissenschaftlichen Suchen abgeschlossen; 538 Kandidaten nachgerechnet, technischer Vorlauf mit 12 Workern und vollständige Verifikation bestätigt | R/L A: 2/2–2/2, 2/2–1/2, 4/4–4/4; gemeinsame Familienerfolge: 2/2–2/2, 2/2–1/2, 2/4–3/4; gemischt, keine Ausfälle | [Ergebnisbericht](restart_budget_results_manjaro_001.md) |
| `restart-budget-confirmation-manjaro-001` — Bestätigung von 4 × 1.000 gegen 2 × 2.000 auf drei neuen Signalen | [`6bc028204ff651ee883eeac4d38bff7c07fb3ded`](https://github.com/craexxn/ringdown-sr/commit/6bc028204ff651ee883eeac4d38bff7c07fb3ded) | Alle 180 wissenschaftlichen Suchen und 60 Paketwahlen vollständig lesend bestätigt; 2.053 Endfrontkandidaten gebunden, technischer Vorlauf mit 12 Workern separat bestätigt | R: 10/10, 10/10, 9/10 A plus Originalfamilie, praktische Grenze erfüllt; L: 9/10, 7/10, 7/10, getrennt verfehlt; keine Ausfälle | [Ergebnisbericht](restart_budget_confirmation_results_manjaro_001.md) |
| `sr-repeatability-wsl2-threads1-001` — Wiederholbarkeit freier Fronten bei Poollimit 1 | Vollständige Ausführungs-/Treiberzuordnung im Bericht nicht ausgewiesen | Vergleichsergebnisse dokumentiert; vollständige Abschlussmetadaten nachtragen | Frontvergleich gemäß Bericht; keine Zusatzbewertung | [Bericht](symbolic_core_results.md) |
| `sr-core-control-wsl2-001` — Feste numerische Kontrollen mit/ohne Haswell | [`6ed493d2e8fb3a845dd921bd99a620feb8b8850a`](https://github.com/craexxn/ringdown-sr/commit/6ed493d2e8fb3a845dd921bd99a620feb8b8850a); externer Treiber [`ac41251c180a9302aace512d8a100186a2636fe9`](https://github.com/craexxn/ringdown-sr/commit/ac41251c180a9302aace512d8a100186a2636fe9) | Abgeschlossen laut geprüftem Archivvergleich | Numerischer Vergleich gemäß [Befund](fixed_numerics_probe.md#übermittelter-haswell-vergleich-vom-26102026); keine Zusatzbewertung | [Bericht](fixed_numerics_probe.md) |
| `sr-free-haswell-wsl2-001` — Freie SR-Suche mit bestätigtem Haswell-Kern | [`6ed493d2e8fb3a845dd921bd99a620feb8b8850a`](https://github.com/craexxn/ringdown-sr/commit/6ed493d2e8fb3a845dd921bd99a620feb8b8850a); externer Treiber [`6b3d156a9daecabc4f42d5b940b065a8dda5bc19`](https://github.com/craexxn/ringdown-sr/commit/6b3d156a9daecabc4f42d5b940b065a8dda5bc19) | Abgeschlossen; zwei freie Wiederholungen je Gerät | Geordneter Front-/Bitvergleich gemäß Bericht; keine Zusatzbewertung | [Bericht](symbolic_core_results.md) |
| `sr-repeatability-manjaro-threads1-001` — Wiederholbarkeit freier Fronten bei Poollimit 1 | Vollständige Ausführungs-/Treiberzuordnung im Bericht nicht ausgewiesen | Vergleichsergebnisse dokumentiert; vollständige Abschlussmetadaten nachtragen | Frontvergleich gemäß Bericht; keine Zusatzbewertung | [Bericht](symbolic_core_results.md) |
| `sr-core-control-manjaro-001` — Feste numerische Kontrollen mit/ohne Haswell | [`6ed493d2e8fb3a845dd921bd99a620feb8b8850a`](https://github.com/craexxn/ringdown-sr/commit/6ed493d2e8fb3a845dd921bd99a620feb8b8850a); externer Treiber [`ac41251c180a9302aace512d8a100186a2636fe9`](https://github.com/craexxn/ringdown-sr/commit/ac41251c180a9302aace512d8a100186a2636fe9) | Abgeschlossen laut geprüftem Archivvergleich | Numerischer Vergleich gemäß [Befund](fixed_numerics_probe.md#übermittelter-haswell-vergleich-vom-26102026); keine Zusatzbewertung | [Bericht](fixed_numerics_probe.md) |
| `sr-free-haswell-manjaro-001` — Freie SR-Suche mit bestätigtem Haswell-Kern | [`6ed493d2e8fb3a845dd921bd99a620feb8b8850a`](https://github.com/craexxn/ringdown-sr/commit/6ed493d2e8fb3a845dd921bd99a620feb8b8850a); externer Treiber [`6b3d156a9daecabc4f42d5b940b065a8dda5bc19`](https://github.com/craexxn/ringdown-sr/commit/6b3d156a9daecabc4f42d5b940b065a8dda5bc19) | Abgeschlossen; zwei freie Wiederholungen je Gerät | Geordneter Front-/Bitvergleich gemäß Bericht; keine Zusatzbewertung | [Bericht](symbolic_core_results.md) |

Beim Kreuzvergleich sind ID, Dateiname und Orchestrierungsstand nun aus dem
Originalarchiv bestätigt. Bei `trajectory-manjaro-001` stammt der Ausführungscommit
zusätzlich aus der archivgebundenen Herkunftsfixture; der spätere Format-2-Commit
wird nicht rückwirkend zugeordnet.

## Originalarchive

Ablagehinweis und Sicherungsstand werden hier gepflegt. Bei einer optionalen
Onlinekopie kann ein geprüfter Downloadlink hinzukommen. Die Hashes bezeichnen
die jeweiligen komprimierten Dateien, nicht GitHubs Quellcodearchive oder
ein inneres Manifest. Sieben TAR-Archive und zwei nachgereichte
ZIP-Pakete wurden am 06.11.2026 selbst gehasht. Die ZIP-Hashes bezeichnen die
jetzt empfangenen Pakete, ohne eine frühere Verpackung zu behaupten; Herkunft
der übrigen Hashes steht je Zeile.

| Lauf-ID | Originalarchiv | SHA-256 / Belegstatus | Ablagehinweis / optionaler Download | Sicherungsstand |
| --- | --- | --- | --- | --- |
| `noiseless-control-001` | `noiseless-control-001.zip` | `03a759608c41913d3e18715dd344ef9e26860b75ebc3fae50191343dae92300b`; empfangenes Paket, Inhalt und Herkunft am 06.11.2026 selbst geprüft; früherer Verpackungshash nicht belegt | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `representation-manjaro-001` | `representation-manjaro-001.tar.gz` | `a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`; Bericht: Originalarchiv geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `constant-manjaro-001` | `constant-manjaro-001.tar.gz` | `346459d953468c81975670577b92aa155a1eaec884cebd462fe61e1ab23d492b`; Bericht: Originalarchiv geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `free-budget-manjaro-001` | `free-budget-manjaro-001.tar.gz` | `77fb34ff6ee139c1f2e0fbbb6acd81d7c1623cd6e8090056f641961e887ad33f`; Originalhash, vollständige Manifeste, Herkunft und Fronten am 06.11.2026 selbst geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `trajectory-manjaro-001` | `trajectory-manjaro-001-incomplete.tar.gz` | `08676ddc21c1820110ae425a68de3c5b954c8bef2022b816ca274c307041c873`; Bericht: Originalarchiv geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `trajectory-manjaro-002` | `trajectory-manjaro-002.tar.gz` | `99999285f6d7a8c50c54280cc36b526e704af01b07a1ccf95f2227e5e8597f55`; Bericht: Originalarchiv geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `grammar-manjaro-001` | `grammar-manjaro-001.tar.gz` | `8d7fc8b09ed9c5091acef5237f5512ddb9fb014598e72ee3d9d4e435f33e3915`; Bericht: Originalarchiv geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `duration-manjaro-001` | `duration-manjaro-001.tar.gz` | `d73e990cf0c8092f841bc402aa247eca0311c963421249b5e60ae2e73c55074a`; Bericht: Originalarchiv geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `duration-manjaro-002` | `duration-manjaro-002.tar.gz` | `147d21ec13844f1500b41fa226c4f8d79a8da7558c65faea8f7a478540b70e14`; Bericht: Originalarchiv geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `duration-manjaro-003` | `duration-manjaro-003.tar.gz` | `c39fb68ba6d98729ae64df83dd50feb332117d2204e2b49e49044cd1ebed5147`; Bericht: Originalarchiv geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `duration-manjaro-004` | `duration-manjaro-004.tar.gz` | `c2d9e330770746030bab9467b682a6b595cac25aa132dbb4decd1c4b03472289`; Dateibytes und aufgezeichnete Herkunft am 06.11.2026 erneut gegen Quellenkatalog geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `local-optimizer-manjaro-001` | `local-optimizer-manjaro-001.tar.gz` | `1ab8c0aa91436c4b169c6c6efa8053e04c47ef57d07915f36ac476483276866d`; Dateibytes und aufgezeichnete Herkunft am 06.11.2026 erneut gegen Quellenkatalog geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `outer-ladder-manjaro-001` | `outer-ladder-manjaro-001.tar.gz` | `ac7e841b79042e216d6aacae2961ffb8395f298bbcc7ecc11f1092c90b3deb40`; Dateibytes und aufgezeichnete Herkunft am 06.11.2026 erneut gegen Quellenkatalog geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `transfer-manjaro-001` | `transfer-manjaro-001.tar.gz` | `e363fe1be629973a460fc6e2188bf680c21b2c5519d331bc7e257968dcaaa139`; Dateibytes und aufgezeichnete Herkunft am 06.11.2026 erneut gegen Quellenkatalog geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `seed-driver-crosscheck-manjaro-001` | `seed-driver-crosscheck-manjaro-001.tar.gz` | `c38f857ccee231ae647bbbcf5186cce275b494c6c54a1092773e7d7ccce11926`; Dateibytes, Manifeste, Herkunft und beide Kreuzzellen am 06.11.2026 selbst geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `global-restarts-manjaro-001` | `global-restarts-manjaro-001.zip` | `73f27a15af2c2102ab5e56d49ad13ece9bb13bbff700a6d6f26a808958a8ca14`; empfangenes Abbruchpaket, Bindungen, Einzelbelege und Sperre am 06.11.2026 selbst geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `global-restarts-manjaro-002` | `global-restarts-manjaro-002.tar.gz` | `115147b81234ab3abafcfe3de7f20ad2a7a31097eff8b455ec24d098fbc357d5`; separat übermittelte SHA-256 und alle Original-/Verify-Bindungen am 06.11.2026 selbst geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `iteration-time-manjaro-001` | `iteration-time-manjaro-001.tar.gz` | `b53f63ad9df07a1067d6909adf436ee9631b45b680ff274d5e7acafc4c9e81d9`; separat übermittelte SHA-256, Original-/Aufruf-/Verify-Bindungen am 06.11.2026 selbst geprüft | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `restart-confirmation-manjaro-001` einschließlich technischem Vorlauf | `restart-confirmation-manjaro-001.tar.gz` | `cc5eec6e2fd0a0407f2371c7d6b7591e84e9c2e2cc850b509ed201ba59003468`; am 12.11.2026 aus drei Teilen bytegenau zusammengesetzt, Hash, Original-/Aufruf-/Verify-Bindungen selbst geprüft | [Gemeinsame Ablage](#archivablage); Arbeitskopie vorhanden | Nicht bestätigt |
| `time-coordinate-manjaro-001` einschließlich technischem Vorlauf | `time-coordinate-manjaro-001.tar.gz` | `0d4a662010ad90ae3119a20154b7a39e839b1fbe61cb0adffdbedf51ee6ab4b9`; 9.658.389 Bytes, 1.212 Originaldateien, Herkunft und vollständige wissenschaftliche/technische Verifikation am 12.11.2026 selbst bestätigt | [Gemeinsame Ablage](#archivablage); geprüfte Arbeitskopie vorhanden | Nicht bestätigt |
| `restart-budget-manjaro-001` einschließlich technischem Vorlauf | `restart-budget-manjaro-001.tar.gz` | `fbddd9b45061c3668c089217c7194ca01942655de5608bdc2df649f1c87614e6`; 27.824.763 Bytes, 3.482 Originaldateien; SHA-256, Herkunft und vollständige Verifikation am 13.11.2026 selbst bestätigt | [Gemeinsame Ablage](#archivablage); geprüfte Arbeitskopie vorhanden | Nicht bestätigt |
| `restart-budget-confirmation-manjaro-001` einschließlich technischem Vorlauf | `restart-budget-confirmation-manjaro-001.tar.gz` | `4217baf42ceece7c451f01d388c0f1b9d76bfb58a2e205d0ac6d67aea2a574b2`; am 14.11.2026 aus vier Teilen bytegenau zusammengesetzt; 98.344.207 Bytes, 11.006 Originaldateien | [Gemeinsame Ablage](#archivablage); geprüfte Arbeitskopie vorhanden | Nicht bestätigt |
| `sr-repeatability-wsl2-threads1-001` | `sr-repeatability-wsl2-threads1-001.tar.gz` | `7f63a075c2a95226d320fa6a6a204481c6038fd3ca6c837f9bcbb7f371bf63d7`; Archivhash aus [gemeinsamem Primärnachweis](symbolic_core_results.md#separat-gesicherte-primärnachweise) | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `sr-core-control-wsl2-001` | `sr-core-control-wsl2-001.tar.gz` | `5826725c95499b498f9bc6c0a9935c4cbf7d97f2f63d14b81aad05c85813d114`; Archivhash aus [gemeinsamem Primärnachweis](symbolic_core_results.md#separat-gesicherte-primärnachweise) | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `sr-free-haswell-wsl2-001` | `sr-free-haswell-wsl2-001.tar.gz` | `1442cbea82b6b80c6de9533ceb5bc2a620e1fb3500ee1524529c36c1f5c98ee3`; Archivhash aus [gemeinsamem Primärnachweis](symbolic_core_results.md#separat-gesicherte-primärnachweise) | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `sr-repeatability-manjaro-threads1-001` | `sr-repeatability-manjaro-threads1-001.tar.gz` | `48ea1cd0efb6599378303ea1d77c42b3193e9361ef5799e2697b8c3fa841341b`; Archivhash aus [gemeinsamem Primärnachweis](symbolic_core_results.md#separat-gesicherte-primärnachweise) | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `sr-core-control-manjaro-001` | `sr-core-control-manjaro-001.tar.gz` | `bd2dff7fda69a4124ca8736eb101c32809e9a770cdfd7b02b2e514a745ba8b4d`; Archivhash aus [gemeinsamem Primärnachweis](symbolic_core_results.md#separat-gesicherte-primärnachweise) | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `sr-free-haswell-manjaro-001` | `sr-free-haswell-manjaro-001.tar.gz` | `37d8b1b4d1cc12c9dd7e487d1763a212283a9a3f92c62cdef70ff6be7bdfa94e`; Archivhash aus [gemeinsamem Primärnachweis](symbolic_core_results.md#separat-gesicherte-primärnachweise) | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |

Bei fehlenden Dateien zuerst die ursprünglichen Geräteablagen prüfen. Neu packen
oder einen Lauf wiederholen ersetzt kein verschwundenes Originalarchiv. Ein neu
erzeugtes Paket braucht einen unterscheidbaren Namen und einen eigenen Hash.

## Frühere Portabilitätsläufe mit offenen Archivangaben

Diese technischen Vorläufer sind im [Portabilitätsbericht](portability.md)
dokumentiert; sie sind keine zusätzliche wissenschaftliche Leistungsstudie.
Für **jeden** folgenden Eintrag fehlen ein belegter `.tar.gz`-Archivname,
Archiv-SHA-256 und ein bestätigter dauerhafter Ablagehinweis; auch die zweite
Kopie ist unbestätigt. Die [gemeinsame Ablage](#archivablage) gilt als vorgesehenes
Ziel. Ein Onlineupload ist optional.
Die Präfixe `manjaro:` und `wsl2:` sind nur Indexqualifizierungen der ursprünglichen
Ordnernamen. Es werden keine neuen Lauf-IDs im Originaldatenbestand erzeugt.

| Qualifizierte Lauf-ID | Fragestellung / Bewertungsfassung | Ausführungscommit laut übermitteltem Nachweis | Laufstatus | Ergebnisbericht |
| --- | --- | --- | --- | --- |
| `manjaro:portability-manjaro-001` | Weißrausch-Referenzfit / Schema 1 | [`3833a126102ce943c5c1ee82a4e5d5f935a06463`](https://github.com/craexxn/ringdown-sr/commit/3833a126102ce943c5c1ee82a4e5d5f935a06463) | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `manjaro:ar1-known-manjaro-001` | AR(1)-Referenzfit gewichtet / Schema 1 | Nicht belegt; eigene Git-Metadaten nicht übermittelt | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `manjaro:ar1-ordinary-manjaro-001` | AR(1)-Referenzfit gewöhnlich / Schema 1 | Nicht belegt; eigene Git-Metadaten nicht übermittelt | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `manjaro:estimated-white-portability-001` | Geschätzte Kovarianz / Schema 2 | [`1fcf9fce5b999c2344b038c0a171b60ffaf7ae73`](https://github.com/craexxn/ringdown-sr/commit/1fcf9fce5b999c2344b038c0a171b60ffaf7ae73) | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `manjaro:estimated-ar1-portability-001` | Geschätzte Kovarianz / Schema 2 | [`1fcf9fce5b999c2344b038c0a171b60ffaf7ae73`](https://github.com/craexxn/ringdown-sr/commit/1fcf9fce5b999c2344b038c0a171b60ffaf7ae73) | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `manjaro:sr-portability-001` | Weiß/AR(1), je drei SR-Arme / Schema 3; keine R1–R3-Bindung | [`6ed493d2e8fb3a845dd921bd99a620feb8b8850a`](https://github.com/craexxn/ringdown-sr/commit/6ed493d2e8fb3a845dd921bd99a620feb8b8850a) | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `wsl2:portability-manjaro-001` | Weißrausch-Referenzfit / Schema 1 | [`fbe9a605dc5d89a9beb1b46f19fece178be4a25f`](https://github.com/craexxn/ringdown-sr/commit/fbe9a605dc5d89a9beb1b46f19fece178be4a25f); `dirty: true`, Gründe im Bericht | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `wsl2:ar1-known-wsl2-002` | AR(1)-Referenzfit gewichtet / Schema 1 | Nicht belegt; eigene Git-Metadaten nicht übermittelt | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `wsl2:ar1-ordinary-wsl2-002` | AR(1)-Referenzfit gewöhnlich / Schema 1 | Nicht belegt; eigene Git-Metadaten nicht übermittelt | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `wsl2:estimated-white-wsl2-001` | Geschätzte Kovarianz / Schema 2 | [`1fcf9fce5b999c2344b038c0a171b60ffaf7ae73`](https://github.com/craexxn/ringdown-sr/commit/1fcf9fce5b999c2344b038c0a171b60ffaf7ae73) | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `wsl2:estimated-ar1-wsl2-001` | Geschätzte Kovarianz / Schema 2 | [`1fcf9fce5b999c2344b038c0a171b60ffaf7ae73`](https://github.com/craexxn/ringdown-sr/commit/1fcf9fce5b999c2344b038c0a171b60ffaf7ae73) | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |
| `wsl2:sr-portability-001` | Weiß/AR(1), je drei SR-Arme / Schema 3; keine R1–R3-Bindung | [`6ed493d2e8fb3a845dd921bd99a620feb8b8850a`](https://github.com/craexxn/ringdown-sr/commit/6ed493d2e8fb3a845dd921bd99a620feb8b8850a) | Abgeschlossen laut übermittelten Nachweisen | [Portabilitätsbericht](portability.md) |

Reine Installationsbeispiele, generische Befehlsbeispiele und CI-Fixtures werden
nicht allein wegen eines vorgeschlagenen Ausgabeordners als tatsächlich
wissenschaftlich ausgeführte Versuche eingetragen. Weitere belegte Läufe können
mit denselben wenigen Indexfeldern ergänzt werden.

## Nachträgliche Bewertungen

R1–R3 betreffen dieselben vier Originalserien `duration-manjaro-004`,
`local-optimizer-manjaro-001`, `outer-ladder-manjaro-001` und
`transfer-manjaro-001`: 78 Originalauswahlen in 18 ursprünglichen Gruppen.
Dies sind **keine neuen SR-Versuche**. Ihre Bewertungscommits ersetzen keine
Ausführungscommits in der oberen Tabelle. Die jeweilige Berichtshistorie
belegt spätere Dokumentationsänderungen.

| Kennung / Bewertungs-ID | Bewertungsfassung | Tatsächlicher Bewertungscommit | Status / Ausgangsdaten | Ergebnisbericht |
| --- | --- | --- | --- | --- |
| Vorstufe R1a: `supplemental-assessment-transfer-001` | `ringdown-sr-supplemental-assessment-1` | [`fee9418071834b1ea42692cb436ecdd8fb6d4fd3`](https://github.com/craexxn/ringdown-sr/commit/fee9418071834b1ea42692cb436ecdd8fb6d4fd3) | Export completed; 18 Transferauswahlen; 60 fehlende Fälle, Korpus incomplete | [Bericht](representation_implementation_status.md) |
| Vorstufe R1b: `supplemental-assessment-transfer-002` | `ringdown-sr-supplemental-assessment-1` | [`a7d615fda122ab59124987729527303090225a13`](https://github.com/craexxn/ringdown-sr/commit/a7d615fda122ab59124987729527303090225a13) | Export completed; 18 Transferauswahlen; 60 fehlende Fälle, Korpus incomplete | [Bericht](representation_implementation_status.md) |
| R1: `supplemental-assessment-all-001` | `ringdown-sr-supplemental-assessment-1` | [`efb2accd4a31ebf4206b40acaf261a3bf04b31ad`](https://github.com/craexxn/ringdown-sr/commit/efb2accd4a31ebf4206b40acaf261a3bf04b31ad) | Export completed; 78 Auswahlen, Korpus complete | [Bericht](supplemental_assessment_results_001.md) |
| R2: `supplemental-structure-all-001` | `ringdown-sr-supplemental-assessment-2` | [`3aceb638f9a648caab4019008cb5beeba336f1a2`](https://github.com/craexxn/ringdown-sr/commit/3aceb638f9a648caab4019008cb5beeba336f1a2) | Export completed; 78 Auswahlen, Korpus complete | [Bericht](supplemental_structure_results_001.md) |
| R3: `supplemental-remainder-all-001` | `ringdown-sr-supplemental-assessment-3` | [`97e02afca0591ba731fdb95f76eea4d8223cea99`](https://github.com/craexxn/ringdown-sr/commit/97e02afca0591ba731fdb95f76eea4d8223cea99) | Export completed; 78 Auswahlen, Korpus complete | [Bericht](supplemental_remainder_results_001.md) |

Die beiden Vorstufen bleiben trotz später vollständigem Korpus als getrennte
Artefakte erhalten. Ihre Angaben stammen aus den vorhandenen archivierten
Bewertungsberichten; technische Veröffentlichung `completed` bedeutete dort
nicht vollständige wissenschaftliche Datenabdeckung.

| Bewertungs-ID | Eigenständiges Bewertungsarchiv | Archiv-SHA-256 | Ablagehinweis / optionaler Download | Sicherungsstand |
| --- | --- | --- | --- | --- |
| `supplemental-assessment-transfer-001` | `supplemental-assessment-transfer-001.tar.gz` | `20a65f0cbbeb060b8c39570b4c9314781aaa554b8eea66cd63cd4d7133f73167` | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `supplemental-assessment-transfer-002` | `supplemental-assessment-transfer-002.tar.gz` | `ab14c720058f2af17a3266bd737e0f7c7a4b56180c7fa4fa8c150d6bf178e1d6` | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `supplemental-assessment-all-001` | `supplemental-assessment-all-001.tar.gz` | `3533d3ef163bdc18fa38f78687f87dfc1e485ecf0156a83ec2893c4656fe7466` | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `supplemental-structure-all-001` | `supplemental-structure-all-001.tar.gz` | `cc52de459a4c250b4e70f9290898f9c0b9011e1182dccfc16dd47f8a40c19356` | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |
| `supplemental-remainder-all-001` | `supplemental-remainder-all-001-review.tar.gz` | `a47e88b11934c5cc3df0b433a0e0d1fffe6be5fb175b1f92def277075fa87155` | [Gemeinsame Ablage](#archivablage) | Nicht bestätigt |

Diese fünf Paket-Hashes und die enthaltenen Ausgabemanifeste wurden am
06.11.2026 lesend geprüft; damit wird keine neue wissenschaftliche Bewertung
behauptet. Das R3-Paket ist ein Reviewpaket mit der vollständigen Bewertung und
weiteren Nachweisen, kein Ersatz für die vier Originalarchive. Zusätzliche
historische Audithilfen wie `constant-audit-001.tar.gz` sind im
[Arbeitsdokument](representation_implementation_status.md) erwähnt; ihr Hash
und ihre aktuelle Verfügbarkeit sind hier nicht belegt. Sie ersetzen ebenfalls
kein Originalarchiv.

## Zusatzdiagnosen und offene Sicherung

### Zusätzliche begrenzte Endfrontdiagnose

Am 06.11.2026 wurden die vier Originalarchive erneut bereitgestellt und anhand
ihrer unveränderten Katalog-SHA-256, Manifeste und Quellenbindungen geprüft.
Die [Endfrontdiagnose](endfront_diagnostic_001.md) bewertet getrennt 738 Kandidaten
aus 78 Fronten, ohne Originalauswahlen zu ersetzen. Softwarestand
`4e42ff74eda62a58202aa706fc42a840eea1226c`; das separate Diagnoseprogramm und
sein Hash sind im Paket enthalten. Keine neue Suche und kein neuer Fit.

| Diagnose-ID | Archiv | SHA-256 | Ablage / Sicherungsstand |
| --- | --- | --- | --- |
| `endfront-diagnostic-003` | `endfront-diagnostic-003-review.tar.gz` | `808da23defbbb2bfe7a58e6fe15783a96725d67f306e00e89fa8e8869bb8902a` | Lokale Arbeitskopie mit Originalen und Diagnose; dauerhafte Ablage und unabhängige zweite Kopie nicht bestätigt |

Die beiden vorherigen unvollständigen technischen Auditversuche blieben
gesperrt; sie sind keine zusätzliche Bewertung. Die erfolgreiche Diagnose
und das Reviewpaket sind getrennt von allen Originalen aufbewahrt.

### Quellenaudit der drei nachgereichten Pakete

Am 06.11.2026 wurden die [beiden frühen Serien](early_control_archive_audit_001.md)
und der [Neustart-Abbruch 001](global_restart_results_manjaro_001.md) lesend
geprüft. Das gesonderte Paket `received-evidence-audit-001.tar.gz`, SHA-256
`f8951618a08a1f9c5cc666981678b1e9f50dc3efd7586cb40e4d6c30806aacb6`, enthält
die drei unveränderten empfangenen Dateien, Auditskripte, Dateimanifeste,
Prüfergebnisse und regenerierte frühe Berichte. Sein eigenes Manifest und der
Rücklesevergleich bestehen. Es liegt nur als lokale Arbeitskopie vor; dauerhafte
Ablage und zweite Kopie bleiben offen. Es ersetzt weder die Originale noch eine
positive Abschlussfreigabe für den abgebrochenen Neustartvergleich.

### Lesende Verifikation von Neustartlauf 002

Der [Ergebnisbericht](global_restart_results_manjaro_002.md) bindet das vollständige
Original und seinen mitgelieferten Verify-Export. Getrennter Audit:
`global-restarts-manjaro-002-audit.tar.gz`, SHA-256
`e88404e068dcdba03798f4cc6fc1562a4a37e7c25847691004f7f0dbc14a5c3d`.
Enthalten sind das unveränderte Originalarchiv, Quellen-/Dateiabgleich,
Auditskripte, die dokumentierte reine Python-Startanpassung, der gesperrte erste
CLI-Versuch, erfolgreiche eigene Verifikation und technische Kontroll-Eignung.
Alle drei Verify-Dateien sind bytegleich zum mitgelieferten Export; Auditmanifest
und Rücklesevergleich bestanden. Der Audit ersetzt keine unabhängige
wissenschaftliche Bestätigung. Original und Audit liegen hier als Arbeitskopien;
gemeinsame Archivablage und unabhängig geprüfte zweite Kopien bleiben offen.

### Lesende Verifikation von Zeitbudgetlauf 001

Der [Ergebnisbericht](iteration_time_results_manjaro_001.md) bindet das vollständige
Original mit Aufrufmessung und mitgeliefertem Verify-Export. Getrennter Audit:
`iteration-time-manjaro-001-audit.tar.gz`, SHA-256
`f7196e562e316fbea3222d06d65f53ccf419865c5e52c9e1bb34abf2b4188f55`.
Originalarchiv, Dateimanifest, Quellenabgleich, Auditskripte, dokumentierte
Python-Startanpassung und erfolgreiche eigene Verifikation enthalten. Alle drei
Verify-Dateien sind bytegleich zum mitgelieferten Export. Eigenes Auditmanifest
und Rücklesevergleich bestanden. Keine neue Suche, kein Fit, kein nativer Replay;
keine unabhängige wissenschaftliche Bestätigung. Original und Audit sind hier
Arbeitskopien, gemeinsame Ablage und unabhängig geprüfte Zweitkopien offen.

### Lesende Verifikation der Neustartbestätigung 001

Prüfung vom 12.11.2026 am exakten sauberen Ausführungscommit `c3da991`:
Originalarchiv aus drei Teilen rekonstruiert, 81.098.904 Bytes und SHA-256
`cc5eec6e2fd0a0407f2371c7d6b7591e84e9c2e2cc850b509ed201ba59003468`
bestätigt. Alle 8.954 Originaldateien vor und nach dem Audit unverändert.
Unveränderter CLI-Gesamtverifikator bestätigt 150 wissenschaftliche Zellen und
1.755 Kandidaten; drei Verify-Dateien bytegleich. Technischer Manjaro-Vorlauf mit
sechs kleinen Workern ebenfalls bestätigt, neun technische Verify-Dateien bytegleich.
Keine neue Suche, kein Fit, keine neue native Formelauswertung.

Getrenntes Audit: `restart-confirmation-audit-001.tar.gz`, 23.338.599 Bytes,
SHA-256 `565ad634c734b2e67929382c067beec84152e211776a2908c9241c5e3511980c`.
29 Dateien: Empfangsmanifest, unabhängige Zusammenfassung, Prüfskripte, eigene
Verify-Exporte, Logs und Auditmanifest. Paket-Rücklesen gegen das eigene Manifest
bestanden. Der fehlgeschlagene erste technische Leseversuch wegen eines lokalen
Julia-Pfadtypos bleibt getrennt vom erfolgreichen zweiten Audit erhalten.
Paketwahl/Kostenaddition und beide Erfolgszahlen direkt nachgerechnet, zwölf
Clopper–Pearson-Intervalle unabhängig über Binomialsummen bestätigt. Das Original
bleibt separat erhalten und wird durch dieses Auditpaket nicht ersetzt.

[Ergebnisbericht](restart_confirmation_results_manjaro_001.md): gemeinsame
Übergangsgrenze verfehlt, keine technische Unvollständigkeit. Die ergänzende
[Kombinationsdiagnose vom 12.11.2026](restart_confirmation_results_manjaro_001.md#nachträgliche-kombination-beider-arme)
zählt aus denselben Originalausgaben 9/10, 10/10 und 7/10 gemeinsame Erfolge;
keine neue Serie und keine geprüfte kombinierte Auswahlmethode. Original und Audit
sind Arbeitskopien; gemeinsame Ablage und unabhängig SHA-256-geprüfte Zweitkopien
beider Pakete bleiben gemäß [Archivregel](results_archiving.md) offen.

### Lesende Verifikation des Zeitkoordinatenvergleichs 001

Prüfung vom 12.11.2026 am exakten sauberen Ausführungscommit `91d461c`,
main nach der vollständig CI-geprüften Übernahme von PR83. Originalarchiv
`time-coordinate-manjaro-001.tar.gz`: 9.658.389 Bytes, SHA-256
`0d4a662010ad90ae3119a20154b7a39e839b1fbe61cb0adffdbedf51ee6ab4b9`.
1.212 Originaldateien, 72.035.452 entpackte Bytes; Original und alle Dateien
vor/nach Audit unverändert. Drei wissenschaftliche Abschnitte anchor/low/high
mit Aufrufmessungen, gemeinsame Verifikation und technischer Manjaro-Vorlauf
mit beiden Fixtures, Aufrufmessungen und Einzel-/Gesamtprüfungen enthalten.

Unveränderter Gesamtverifikator bestätigt 16 wissenschaftliche Zellen;
188 Frontkandidaten zusätzlich lesend nachgerechnet. Die drei wissenschaftlichen
Exportdateien sind bytegleich. Vier technische Vorlaufworker samt beiden
Einzelprüfungen und Gesamtprüfung bestätigt; neun technische Exportdateien
bytegleich. 100 gebundene Quellen einschließlich aller 50 Python-Paketquellen
zusätzlich gegen Git geprüft; keine neuen Suchen/Fits oder Archivprogramme.
Originalauswahl, Paarungen und Pflichtkosten unabhängig aus Workerdateien
nachgezählt; gesonderter Baum-Replay und Fehlernormen bestätigen die Klassen.

[Ergebnisbericht](time_coordinate_results_manjaro_001.md): gemischte
Entwicklungseinordnung, sechs ausgewählte U-Beweise an der physischen
Kompositionsgrenze. Gesamtaufrufe rund 2 h 26 min ohne Abschnittspausen;
Ausfälle null. Vorbereitung des nächsten separat eingefrorenen Budgetvergleichs
mit gemeinsamer ursprünglicher Koordinate T; keine automatische Ausführung.

Getrenntes Auditpaket: `time-coordinate-audit-001.tar.gz`, **2.753.620 Bytes**,
SHA-256 `9a624763548da7331c947e5e2f6b80eff781af59d6fa6206acc9576e45e533e0`.
36 Dateien: Empfangsmanifest, Prüfskripte, unabhängige Zähl-/Front-/Modellnachweise,
eigene zwölf Verify-Exporte, Logs, Abschlussnachweis und Auditmanifest.
Paket-Rücklesen gegen das Manifest bestanden. Der erste lokale Leseversuch wegen
schreibgeschütztem Julia-Cache bleibt als gesperrter Audit erhalten; der zweite
bestand mit unverändertem Verifikator. Das Originalarchiv bleibt separat erhalten.

Original und Audit liegen als geprüfte Arbeitskopien vor. Gemeinsame dauerhafte
Ablage, unabhängige Zweitkopien und SHA-256-Prüfung beider Speicherziele bleiben
ausdrücklich offen. Keine verpflichtende GitHub-Upload-Aufgabe.

### Lesende Verifikation des Neustartpaketvergleichs 001

Original am 13.11.2026 empfangen; tatsächliche wissenschaftliche Ausführung
am 12.11.2026 auf sauberem main `680af98` nach PR85. Archiv
`restart-budget-manjaro-001.tar.gz`: **27.824.763 Bytes**, bestätigte SHA-256
`fbddd9b45061c3668c089217c7194ca01942655de5608bdc2df649f1c87614e6`.
3.482 reguläre Originaldateien, 235.902.915 entpackte Bytes; drei Abschnitte
anchor/low/high mit benachbarten Aufrufmessungen und gemeinsamer Verifikation,
technischer Manjaro-Vorlauf mit zwölf Workern, zwei Fixtures und eigenen
Aufrufmessungen sowie Einzel-/Gesamtprüfungen vollständig enthalten.

Alle fünf Vorbereitungen binden 102 Quellen einschließlich aller 52 Python-
Paketdateien an Git und den sauberen Ausführungsstand. Vollständige offizielle
wissenschaftliche und technische Verifikation bestanden: drei wissenschaftliche
und neun technische Exportdateien bytegleich. Beide technischen Einzelprüfungen
über CLI, Gesamtprüfung über die unveränderte öffentliche Verify-Funktion;
die wissenschaftliche Serien-CLI verlangt genau drei Abschnitte. Unabhängige
Nachzählung bestätigt 48 native Originalauswahlen, 16 Paketwahlen, Seeds,
Iterationstopps und sämtliche Pflichtkosten. Alle 538 Frontkandidaten zusätzlich
mit unveränderten Bewertungsverträgen nachgerechnet; eigener Baum-Replay und
Fehlernormen bestätigen die Kurvenklassen. Keine neuen Fits oder Suchen.

[Ergebnisbericht](restart_budget_results_manjaro_001.md): gemischte
Entwicklungseinordnung trotz vier A-Kurven beider Verfahren auf variant_high.
Zwei hohe Originalausgaben besitzen entfernbare Definitionslücken mit gültiger
Fortsetzung, eine einen winzigen zusätzlichen Modus mit offenem Familiennachweis.
Vollständige wissenschaftliche Abschnittsaufrufe zusammen 17.612,447 s,
4 h 53 min 32 s ohne Pausen, technischen Vorlauf und spätere Verifikation.

Getrenntes Auditpaket: `restart-budget-audit-001.tar.gz`, **8.259.028 Bytes**,
SHA-256 `16f7568f6ed2d56245945d6a24d66b80e02ce3e782e659df74df2ea110e338b2`.
137 Dateien: Empfangsmanifest, Zähl-/Front-/Bindungsskripte und Befunde,
offizielle Prüfkommandos, zwölf eigene Verify-Exporte, Logs beider lokalen
Verifikationsversuche, Abschlussnachweis und Auditmanifest. Paket-Rücklesen
gegen Dateien und Manifest bestanden. Der erste Versuch blieb wegen
schreibgeschütztem Julia-Logcache gesperrt; der zweite bestand mit unverändertem
Verifikator und eng begrenztem Cache-Schreibrecht. Originalarchiv und alle
3.482 Dateien vor/nach der Prüfung unverändert; Original bleibt separat erhalten.

Original und Audit bleiben Arbeitskopien; gemeinsame dauerhafte Ablage,
unabhängige Zweitkopien und SHA-256-Prüfung beider Speicherziele sind weiterhin
offen. Keine verpflichtende GitHub-Upload-Aufgabe.

### Lesende Verifikation der erneuten Bestätigung 001

Am 14.11.2026 aus vier übermittelten Teilen bytegenau zusammengesetzt:
`restart-budget-confirmation-manjaro-001.tar.gz`, **98.344.207 Bytes**,
bestätigte SHA-256
`4217baf42ceece7c451f01d388c0f1b9d76bfb58a2e205d0ac6d67aea2a574b2`.
11.006 reguläre Originaldateien, 806.168.742 entpackte Bytes und 14 Wurzeleinträge.
Tatsächlicher Ausführungsstand ist sauberer main `6bc0282` nach PR87.

Enthalten sind `restart-budget-confirmation-low-manjaro-001`,
`restart-budget-confirmation-mid-manjaro-001` und
`restart-budget-confirmation-high-manjaro-001`, alle drei Aufrufmessungen und
`restart-budget-confirmation-manjaro-001-verification`. Der vollständige
technische Vorlauf `restart-budget-confirmation-technical-001` mit `fixture_a`,
`fixture_b`, ihren beiden Aufrufmessungen und Einzel-/Gesamtverifikationen
bleibt getrennt von den wissenschaftlichen Nennern.

180 native Originalwahlen und 60 verlustbasierte Paketwahlen unabhängig
nachgezählt; alle zwölf marginalen Binomialintervalle und Kosten bestätigt.
Die vollständige eigene wissenschaftliche und technische lesende Verifikation
am unveränderten Ausführungscommit ist bestanden; drei wissenschaftliche und
neun technische Exportdateien sind bytegleich. Alle 11.006 Originaldateien
und der Archivhash sind vor/nach der Prüfung unverändert. Ergebnis und Grenzen stehen im
[Bericht](restart_budget_confirmation_results_manjaro_001.md); keine neuen Fits
oder Suchen.

Getrenntes Auditpaket: `restart-budget-confirmation-audit-001.tar.gz`,
**28.362.063 Bytes**, SHA-256
`87d5862be583c3cfe2b059397b072ed39744efadbd83157a36e7f9c33f2dd8e6`.
44 Dateien: Empfangs-/Originalinventar, Zähl-, Quellen- und begrenzte Formel-
prüfungen samt Skripten, tatsächlicher Verifikationskontext, alle zwölf eigenen
Verify-Exporte, Logs, Abschlussnachweis und Auditmanifest. Alle Paketdateien
nach dem Packen gegen das Manifest zurückgelesen und bestätigt. Das vollständige
Originalarchiv bleibt separat erhalten; es wird durch dieses Audit nicht ersetzt.

Original und separates Audit bleiben geprüfte Arbeitskopien, keine bestätigte
unabhängige Sicherung.
Gemeinsame dauerhafte Ablage, zweite Kopie und SHA-256-Prüfung beider Speicherziele
sind offen. GitHub-Uploads sind optional.

### Offene Sicherungsschritte

- Die namentlich und mit Hash belegten Archive und empfangenen ZIP-Pakete aus
  „Originalarchive“ im gemeinsamen Archivordner und einer zweiten gesicherten
  Kopie erhalten. Bei noch nicht selbst geprüften älteren Dateien die
  tatsächlichen Bytes zuerst mit dem dokumentierten Hash vergleichen.
- Für die noch fehlenden Primärbelege die Priorisierung unten verwenden.
  Das Kreuzversuchsarchiv muss nicht erneut bereitgestellt werden. Sein
  gesonderter lesender Audit `seed-driver-crosscheck-audit-002.tar.gz`, SHA-256
  `ba1339952222b650c9bbdfccafcc8a559f3dbe09b818d8bfd1ab9bdd79844c05`, liegt
  ebenfalls nur als Arbeitskopie vor; gemeinsame Ablage und zweite Kopie offen.
- Die fünf getrennten Bewertungsarchive ebenfalls mit zweiter Kopie erhalten.
  Fehlende Quellenrefs dauerhaft sichern, besonders ursprüngliche
  PR-Heads/Werkzeug- und Bewertungscommits außerhalb der main-Historie.
- Gemeinsame Ablagehinweise ergänzen und beide Archivkopien je Eintrag gegen
  SHA-256 prüfen. Bis zur Bestätigung bleibt der Sicherungsstand offen.
  GitHub-Uploads und Downloadlinks sind optionale Ergänzungen.

### Technische Profilübernahme vom 14.11.2026

`confirmed-profile-technical-003` wurde in der Cloud am sauberen
Ausführungscommit `609bc29745a354b212a8015a378b36800c2979c7` abgeschlossen:
sechs kleine native Worker, neun analytische Gewichtungs-/Optimiererreferenzen,
34 Endfrontkandidaten und separater lesender CLI-Aufruf geprüft. Dies ist die
technische Abnahme des [allgemeinen Profilwegs](symbolic_pilot.md#bestätigtes-r-profil-im-allgemeinen-laufweg-schema-4),
keine wissenschaftliche Ringdown- oder Rauschserie und kein Manjaro-Nachweis.
Implementierungs- und Prüfumfang stehen im
[Fortsetzungsstand](representation_implementation_status.md).

Archiv einschließlich lesendem Prüfprotokoll:
`confirmed-profile-technical-003.tar.gz`, **545.347 Bytes**, SHA-256
`a940ca819cef12ba1c23f5d9ecf57e5d7fcd678ef4fc4693ec7ba7f26479fd08`.
TAR und Prüfsumme sind geprüft. Eine Cloud-Arbeitskopie liegt vor;
gemeinsame dauerhafte Archivablage und unabhängige hashgeprüfte Zweitkopie
sind noch nicht bestätigt. Keine zusätzliche verpflichtende GitHub-Ablage.

Der zusätzliche **Manjaro-Vorlauf `confirmed-profile-technical-manjaro-001`**
wurde am sauberen Ausführungscommit
`8b9c6ef3a17fed03958a24ff36698bd47622eca5` nach Übernahme von PR89 abgeschlossen.
Originalarchiv am 14.11.2026 empfangen und auf demselben Commit selbst lesend
verifiziert: sechs kleine Suchworker und neun analytische Kontrollen bestanden.
194 Dateien des Laufordners bleiben bytegleich; die neue CLI-Ausgabe stimmt
mit dem mitgelieferten separaten Verifikationsprotokoll überein. Dies ist ein
technischer Gerätebeleg, keine wissenschaftliche Ringdown- oder Rauschserie.
Details und Aussagegrenzen im [Fortsetzungsstand](representation_implementation_status.md#technischer-manjaro-nachweis-vom-14112026).

Originalarchiv: `confirmed-profile-technical-manjaro-001.tar.gz`,
**572.274 Bytes**, SHA-256
`73b98b8d153a353a5b596cbffa34f9fa7699a0c6f177cd70aa190654fd1857a2`.
195 reguläre Dateien einschließlich des separaten lesenden Prüfprotokolls,
2.984.681 entpackte Bytes; TAR und SHA-256 selbst geprüft. Die übermittelte
Arbeitskopie liegt vor. Dauerhafte Ablage im gemeinsamen Archivordner sowie
unabhängige hashgeprüfte Zweitkopie sind weiterhin nicht bestätigt; keine
weiteren Laufdateien werden für diesen technischen Nachweis benötigt.

### Technischer Rauschpilot-Vorlauf vom 15.11.2026

`noise-pilot-technical-manjaro-001`, tatsächlich ausgeführt und selbst lesend
geprüft auf `eb663a0bf008f7c8697ef7ec5386b3e11545a19f`. Drei abgeschlossene
N128-Zehnerworker mit gewöhnlicher, bekannter und geschätzter Gewichtung;
keine wissenschaftliche Serie. Vollständiger Aufruf 161,847 s, 103 Originaldateien
nach lesender Verifikation bytegleich. Details und Ressourcenentscheidung im
[Fortsetzungsstand](representation_implementation_status.md#technischer-manjaro-n128-nachweis-vom-15112026).

Originalarchiv: `noise-pilot-technical-manjaro-001.tar.gz`, **1.429.764 Bytes**,
SHA-256 `f56e6b1f87d8971a7d7c3a6c6f08d05ea23f495f20ba2f93a30f9575a0898f40`.
Am 15.11.2026 empfangen; TAR, vollständige Manifeste und SHA-256 geprüft.
103 reguläre Dateien, 4.112.593 entpackte Dateibytes. Übermittelte Arbeitskopie
vorhanden; keine weiteren Laufdateien für die technische Abnahme benötigt.
Das separate historische CLI-Verifikationsprotokoll samt Prüfzeit fehlt;
diese Zeit bleibt unbekannt, die neue eigene lesende Prüfung ist belegt.
Ablage im gemeinsamen Archivordner und unabhängige hashgeprüfte Zweitkopie
weiterhin unbestätigt; [Ablagezuordnung](#archivablage). GitHub-Upload optional.

### Wissenschaftlicher Rauschpilot Manjaro 001

`noise-pilot-manjaro-001`, wissenschaftlich ausgeführt und vollständig lesend
geprüft auf `eb663a0bf008f7c8697ef7ec5386b3e11545a19f`. 144 abgeschlossene
Tausendersuchen, 36 Paketausgaben aus zwölf Dreiervergleichen, keine Ausfälle.
Vollständiger Serienaufruf 47.491,474 s; historische separate Verifikation
96,010 s. Wissenschaftliche Einzelwerte, Kosten und Einordnung im
[Ergebnisbericht](noise_pilot_results_manjaro_001.md).

Originalarchiv `noise-pilot-manjaro-001.tar.gz`: **92.167.501 Bytes**, SHA-256
`86a099ebe193669c945abbb918e8b18dd15b21b6341da44622bc1f6efdc69688`.
Am 16.11.2026 aus vier gelieferten Teilen in Reihenfolge 000–003 bytegetreu
zusammengesetzt; Original-SHA und TAR geprüft. 4.916 reguläre Dateien,
469.279.570 entpackte Dateibytes. Enthält wissenschaftliche Inputs, Serie,
separaten Verify-Export samt Aufrufmessungen sowie den technischen Originalordner;
dessen 103 Dateien sind bytegleich zum bereits geprüften technischen Original.
Alle 4.916 Dateien und Archivbytes nach eigener Prüfung unverändert; vier
neue Verify-Exportdateien bytegleich zum gelieferten Export.

Übermittelte Arbeitskopie vorhanden; für diese abgeschlossene Serie fehlen
keine Laufdateien. Dauerhafte gemeinsame Archivablage und unabhängige
hashgeprüfte Zweitkopie weiterhin unbestätigt; [Ablagezuordnung](#archivablage).
Die vier Transportteile ersetzen keinen Nachweis einer unabhängigen Sicherung.
GitHub-Upload bleibt optional.

### Technischer Hintergrundstudien-Vorlauf vom 16.11.2026

`noise-background-preflight-manjaro-001`, tatsächlich ausgeführt und selbst
lesend geprüft auf `bd42634b888c2dbaa5a92726b9a1f9851c766a48`.
Fünf abgeschlossene N128-Zehnerworker für O/K/E64/E256/E1024 bei lokal 300/5;
keine wissenschaftliche Serie. Gespeicherter vollständiger technischer Aufruf
245,763572306 s, eigener separater CLI-Replay 4,035072807 s. Das ursprüngliche
separate Verifikationslog belegt Erfolg ohne Dauer; diese historische Prüfzeit
bleibt unbekannt. Alle 206 Originaldateien blieben bei der eigenen Prüfung
bytegleich. Ressourcenentscheidung und Messgrenzen im
[Fortsetzungsstand](representation_implementation_status.md#technischer-manjaro-n128-nachweis-vom-16112026).

Originalarchiv: `noise-background-preflight-manjaro-001.tar.gz`,
**5.778.824 Bytes**, SHA-256
`c23b99472a27e3732234d56ba8e16ef8a89807d99c03a52ff14bcb1b26df8ae9`.
Am 16.11.2026 empfangen; SHA-256, TAR, vollständige Manifeste und
Quellenbindung geprüft. 206 reguläre Dateien, 15.596.675 entpackte Dateibytes.
Enthält Geräte-/Testprotokolle, technische Originale und einen separaten
Plotexport aller fünf Arme mit unveränderten vollständigen Originalformeln
und numerischen Punktdaten. Originalkosten des Plotexports 5,110615889 s;
eigene lesende Nachprüfung aller fünf Ausgaben 0,108375014 s. Alle Grafik-,
Formel- und Datenbindungen bestätigt; kein erneuter Fit oder Suchaufruf.

Übermittelte Arbeitskopie vorhanden; für diese technische Abnahme fehlen
keine weiteren Laufdateien. Dauerhafte gemeinsame Archivablage und unabhängige
hashgeprüfte Zweitkopie weiterhin unbestätigt; [Ablagezuordnung](#archivablage).
Die Ressourcenprüfung gibt keinen Anlass zur Änderung eingefrorener Fristen,
belegt aber keine Gesamtlaufzeit oder wissenschaftliche Qualität der 520er-Serie.
Die anschließenden wissenschaftlichen Versuche und ihre noch offenen
Originalprüfungen sind unten getrennt zugeordnet.
Ausführung, lesende Prüfung und Archivierung bleiben getrennt;
GitHub-Upload optional.

### Wissenschaftliche Hintergrundstudie Manjaro 001 und 002

Stand 19.11.2026; gebundener Manjaro-Ausführungsstand
`bd42634b888c2dbaa5a92726b9a1f9851c766a48`, technischer Vorlauf 001 wie oben.
Das Originalarchiv von 002 liegt zur eigenen Prüfung vor; Versuch 001 bleibt
davon getrennt. Lauf-, Fehler- und Kostenbelege stehen im
[Fortsetzungsstand](representation_implementation_status.md), der Fachbefund im
[Ergebnisbericht 002](noise_background_results_manjaro_002.md).

- `noise-background-manjaro-001`: Nach belegtem Suspend gesperrter Versuch,
  kein erfolgreicher wissenschaftlicher Abschluss. Das Originalarchiv
  `noise-background-manjaro-001-aborted.tar.gz` wurde hochgeladen, überschreitet
  aber die 32-MiB-Grenze des verfügbaren Downloads. Nur die zugehörige
  Prüfsummendatei wurde gelesen: erwarteter SHA-256
  `4c10460e4f90820f078c5aad5a9d1e33c8cfd9932a3f04471737287d91ba2f30`.
  Dieser Hash ist **nicht an den Archivbytes bestätigt**; TAR-Inhalt und
  vollständige Teilkosten sind noch ungeprüft. Eine Übertragung in kleineren
  Teilen kann dieselben Originalarchivbytes zugänglich machen.
- `noise-background-manjaro-002`: Das Originalarchiv
  `noise-background-manjaro-002-plots-recovered.tar.gz` ist am 19.11.2026 aus
  19 gelieferten Teilen 000–018 zusammengesetzt; sämtliche Teilprüfsummen und
  der vollständige SHA-256 sind selbst bestätigt:
  `b2a4ace2d9097099822ab524377537dae24d59c7ba59e137de11ae5ba3e4214d`.
  470.474.010 Archivbytes; 18.166 reguläre Dateien, 1.931 Verzeichnisse und
  2.027.757.507 entpackte Dateibytes, keine Links oder unsicheren Einträge.
  Beide vollständigen Elternordner sind enthalten: wissenschaftlicher Lauf 002
  und technischer Vorlauf 001, einschließlich Fehlversuchen und Kostensidecars.
  520 abgeschlossene Suchen, 130 erfolgreiche Pakete, keine Timeouts;
  vollständiger Serienaufruf 182.531,209977 s. Die eigene vollständige
  Serienverifikation besteht in 559,396 s; alle vier Exportdateien sind
  bytegleich zur Manjaro-Verifikation. Auch unabhängige Statistik-, Herkunfts-
  und Plotnachprüfung bestehen. Alle 18.166 Originaldateien bleiben bytegleich.
  Die erfolgreiche Manjaro-Verifikation `verification-002` und der reparierte
  Export `plots-002` sind erhalten, ebenso die fehlgeschlagenen Vorgänger.
  Alle 130 Originalformeln und 265.330 Punktwerte sind bestätigt. Renderercommit
  `7b0417db802eb8d97aea407b2a47f715c2a53bba` ist getrennt vom unveränderten
  Ausführungs-/Verifikationsstand `bd42634` gebunden.
  Der technische Originalordner bleibt in 165 Dateien bytegleich zum früheren
  Vorlaufarchiv; 205/206 Dateien seines Elternordners sind identisch. Nur die
  äußere Monitorzeile `progress.txt` wurde nach damaliger Archivierung auf
  den erfolgreichen Abschluss fortgeschrieben.
  Eine separate portable Galerie mit allen 130 Plots, vollständigen Formeln,
  Punktdaten und sechs Übersichten hat 75.143.741 Bytes und SHA-256
  `c5c367cfb6b0349ca69d129a254eb99d493b0ce2520da852ef2345cc3311ffab`.
  Sie ist eine abgeleitete Ansicht und ersetzt das vollständige Originalarchiv nicht.
  Das separate Nachweispaket `noise-background-manjaro-002-audit.zip` enthält
  die unabhängigen Audits, Skripte, CSV-Werte und den eigenen Verify-Export:
  2.949.645 Bytes, SHA-256
  `56fd715461ac8ab57e0121df2ae88a388f517dc0e749f79b7c665379e33ea860`;
  internes Manifest und ZIP-CRC geprüft.

Die anschließend beauftragte [Kandidatenprüfung](noise_background_candidates_manjaro_002.md)
vom 19.11.2026 ist eine getrennte lesende Diagnose desselben Originalarchivs:
636 gespeicherte Kandidaten aus 48 Workern, sechs auffällige Fall-Arme und
deren gewöhnlich gewichtete Vergleiche. Alle 1.298.076 Punkte, ursprünglichen
Auswahlen, Formeln und Quellen sind unabhängig geprüft; sämtliche 18.166
Originaldateien bleiben vor und nach der Diagnose bytegleich. Keine neuen
Fits, Suchen, Stützstellen oder wissenschaftlichen Auswahlen. Diagnoseumfang
vor neuer Auswertung gebunden in `scope.json`, SHA-256
`941f81c1709731deba065c543b8d6df27c68c47ce076bf369bf320657066b84b`.

- `noise-background-manjaro-002-candidates-gallery-v2.zip`:
  280.357.455 Bytes, SHA-256
  `2b031624e6ef6c764c63aa11621278bf08033169366780da98b03989c618780d`.
  Alle 636 Kandidatenplots, vollständige Originalformeln und Punktdaten,
  zwölf Frontübersichten und zwölf verkleinerte Kontaktbögen; 2.662 Dateien.
  Interne Hashes, ZIP-CRC und lokale Links geprüft. V2 behebt ausschließlich
  Achsenbeschnitt in Frontfiguren; V1 samt Archiv bleibt erhalten.
- `noise-background-manjaro-002-candidates-audit.zip`:
  1.092.966 Bytes, SHA-256
  `3a950150fc2470da8bd8df4f531ff0ee3dfd18d8cc7bbbed2988b2e77e400f0f`.
  Scope, reproduzierbare Auditskripte, Kandidatenmetriken/Formeln, Manifeste,
  unabhängige numerische/visuelle Prüfung und Gesamtintegritätsbelege;
  22 Nutzdateien plus internes Manifest, Hashes und ZIP-CRC geprüft.

Für beide Versuche sind gemeinsame dauerhafte Archivablage und unabhängige
hashgeprüfte Zweitkopie unbestätigt. Transportteile, lokale Arbeitskopien und
die Galerie belegen keine unabhängige Sicherung. Der Abbruch von 001 und seine
Teilkosten werden nicht in die abgeschlossene wissenschaftliche Serie 002 gepoolt.

#### Lesender Methodenvergleich auf Hintergrundserie 002

Der [Selektorpilot vom 19.11.2026](noise_background_selector_pilot_001.md)
ist eine weitere getrennte Entwicklungsauswertung desselben unveränderten
Originalarchivs: 6.985 Kandidaten aus 520 Workern, 130 gemeinsame Pools,
260 gewählte Ausgaben und 530.660 Punkte. Vorabplancommit
`2e538ec92142be4fd2f1d2fdf4883b7af7ce200f`, ursprüngliche wissenschaftliche
Ausführung weiterhin `bd42634b888c2dbaa5a92726b9a1f9851c766a48`;
Auswertungsprogramme sind im Bericht und Nachweispaket durch SHA-256 gebunden.
Die gepoolte PySR-`best`-Regel erhöht in allen zehn Modell-/Armgruppen den
mittleren unregelmäßigen RMSE. Keine neue Suchserie oder Methodenübernahme;
unabhängige numerische und visuelle Gegenprüfungen bestehen, alle 18.166
Originaldateien bleiben erhalten.

- `noise-background-manjaro-002-selector-pilot-audit.zip`:
  6.362.393 Bytes, SHA-256
  `91c729ff71ea6de13717d817dfd487660949f75c09d2e132f891de09bf6a6605`.
  540 Nutzdateien plus Manifest; Scope, Skripte, alle Fronten und gewählten
  Originalkandidaten, Statistiken, Originalmanifest und unabhängige Nachweise.
  Sämtliche Nutzdateihashes und ZIP-CRC geprüft.
- `noise-background-manjaro-002-selector-pilot-gallery.zip`:
  82.658.247 Bytes, SHA-256
  `f4c76a959fc9ead7447cfc31cd4db54a7992f6f1a5868f097de16a56c0d12c5f`.
  961 Dateien mit 130 Paarplots, zehn Gruppenübersichten und zehn Kontaktbögen,
  260 vollständigen Originalformeln und sämtlichen Punktdaten. ZIP-CRC,
  lokale Links, Bilder und Quellenkopien geprüft. Vier Transportteile von
  höchstens 24 MiB wurden mit dem bereitgestellten Helfer zum exakten
  Originalhash zusammengesetzt.

Dauerhafte Archivablage und unabhängige Zweitkopie dieser abgeleiteten Pakete
sind weiterhin unbestätigt. Der negative Befund bleibt Entwicklungsevidenz;
die neue Auswertung ersetzt keine ursprüngliche wissenschaftliche Auswahl.

#### Lesende Aliasdiagnose auf Hintergrundserie 002

Die [Aliasdiagnose vom 19.11.2026](noise_background_alias_diagnostic_001.md)
untersucht alle 260 bereits gewählten Originalbäume und drei vorab festgelegte
konstruierte Gegenbeispiele. Vorabplancommit
`3033bb957ed535f7039efbb18fb53e6d1abb44ad`, Basis
`bb14b5a29163c330f4ba38237ce55419b9fa944f`; ursprüngliche wissenschaftliche
Ausführung weiterhin `bd42634b888c2dbaa5a92726b9a1f9851c766a48`.
Die drei Konstruktionen zeigen nahezu gleiche Trainingswerte bei stark
verschiedenen Zwischenpunktwerten. Sie ersetzen keine Originalauswahl und
begründen keine automatische Normalisierung oder neue wissenschaftliche Serie.

`noise-background-manjaro-002-alias-diagnostic.zip`: **2.872.144 Bytes**,
SHA-256 `1a1e28657a9e4958ee0ba34edfe4934c7b01ce847ee4c5636f767f920e6ded24`.
36 Nutzdateien plus internes Manifest: Scope, getrennte Auditprogramme,
vollständiges Inventar, drei Formel-/Baumpaare, 6.123 Punktzeilen,
HTML-Ansicht, drei PNG-/SVG-Paare und unabhängige numerische/visuelle Nachweise.
ZIP-CRC, sämtliche Nutzdateihashes und unveränderte Quellen geprüft.
Der unabhängige Audit besteht 87.159 Prüfungen und bestätigt alle 18.166
Originaldateien sowie 1.048 vorherige Pilotdateien unverändert.
Keine Fits, Suchen oder neuen wissenschaftlichen Beobachtungen.

Das kompakte Paket ist getrennt vom Originalarchiv bereitgestellt und bleibt eine
retrospektive Mechanismusdiagnose. Gemeinsame dauerhafte Archivablage und
unabhängige hashgeprüfte Zweitkopie bleiben unbestätigt.

### Wissenschaftliche Folgestudie Manjaro 001

- Lauf-ID: `noise-followup-manjaro-001`, Dauer-/Messrasterstudie auf 26
  gemeinsamen Fällen. A 416/416, B 208/208 erfolgreiche Einzelworker;
  zusätzlich 6/6 erfolgreiche technische Worker. 156 erfolgreiche
  Paketausgaben, 52 exakt gebundene Kontrollreferenzen ohne neue Suchkosten.
- Ausführung laut gelieferten Quellenbindungen:
  `8a1a4a1437f4b01daf1f070b56add248074c5907`. Abschluss laut Statusdatei
  am 22.11.2026 um 01:07:08 CET; Einzelstatus jetzt vollständig geprüft,
  ohne Fehler oder Timeout. Gemessene Serienaufrufe zusammen 192.710,002 s.
- Empfangen und am SHA-256 geprüft:
  `noise-followup-manjaro-001-overview.tar.gz`, **11.177.133 Bytes**,
  `911bf9249783848b9ff9c0543c7419fd52e089f8c48190849a5f9eaef086a3f6`.
  Dies ist ein ausgewählter Berichtsexport, kein vollständiges Originalarchiv.
- Eigenständig geprüft: Publikationsmanifeste, Quellenhashes,
  bytegleiche Serien-/Verifikationsexporte, unabhängige Kontraststatistik,
  48 Schätzermatrizen und Rekonstruktion aller 156 gewählten Originalbäume
  auf fingerprintgleichen Rastern. Die Schätzerfälle sind identisch zu
  Cloud-Diagnose 002; keine neue unabhängige Entwicklungsstichprobe.
  Die Nachlieferung ergänzt alle Einzelworker, Eingaberegeneration,
  Originalplots, 26 tatsächliche wissenschaftliche Kovarianzpaare und eine
  begrenzte Diagnose von 333 Kandidaten aus 24 Workern in sechs Problemfällen.
- Nachgereichte **Originalarchive**, vollständig aus 13 bzw. sieben Teilen
  rekonstruiert und am ursprünglichen SHA-256 geprüft:
  `noise-followup-manjaro-001-duration.tar.gz`, **314.610.102 Bytes**, SHA-256
  `bc32f591f5d92418e53a68e6d6f120547f0661e3ab1ec0fb0014cbedcb09ed9a`;
  `noise-followup-manjaro-001-sampling.tar.gz`, **174.969.349 Bytes**, SHA-256
  `d1536eb4d1cce4ea3c812d777c45b796c2e4d7c9c2d41ca83423d02cc443dca7`.
- Nachgereichtes Transportderivat:
  `noise-followup-manjaro-001-shared-review.tar.gz`, **44.494.683 Bytes**, SHA-256
  `5df7a048cab2d59f3be65dc388c0fae68beb1413527ac5cc6ab92ad216c4db45`.
  Alle enthaltenen Originalnutzdateien und der unveränderte Archivbeleg sind
  geprüft. Die 39 ausgelassenen NPY wurden ausschließlich in einer separaten
  Arbeitskopie bitgenau ergänzt; insgesamt 22.152 Originalnutzdateien plus
  drei Archivbelege geprüft. `reconstruction-receipt.json` bindet diesen Vorgang.
- Nicht selbst als komprimierte Datei empfangen:
  `noise-followup-manjaro-001-shared.tar.gz`, berichteter SHA-256
  `897fb84605042cf070893028d9e7368ade47ae50c7f7f5ba6879eceaf9cf01d5`.
  Laut Transferbeleg prüfte der Upload-Helfer dieses Original auf Manjaro; die eigene
  Nutzdatenrekonstruktion bestätigt nicht dessen komprimierte Archivbytes.
- Bericht: [Auswertung, lesende Nachprüfung, Literatur und nächste Schritte](noise_followup_results_manjaro_001.md).
  Keine neuen Fits/Suchen und keine veränderte Originalauswahl.
- Separate Auswertungsexporte vom 22.11.2026, Berichtsfassung
  `1b55a7d1d6f36f3efafc802ae0325fecfcae3110`:
  `noise-followup-manjaro-001-analysis.zip`, **12.992.022 Bytes**, SHA-256
  `84d38ddabcef90d1c3a56a22cde8d58f4b2e74f01a12b0b6a33accfde3d1a7da`;
  Bericht, vier Übersichten, Einzelwerttabellen, Auditbelege/-skripte und
  unverändertes geliefertes Übersichtspaket. Keine vollständigen Roharchive.
  `noise-followup-manjaro-001-gallery.zip`, **53.067.688 Bytes**, SHA-256
  `df545c14b79eff959cc382c57fab6e93167f33a710ee8a239cae7ecda33c7d8c`;
  156 unveränderte Originalformeln/Bäume mit rekonstruierten PNG/SVG/CSV.
  ZIP-CRC, sämtliche Nutzdateihashes und lokale Links geprüft; Galerie auch
  in drei Teilen mit höchstens 24 MiB und geprüftem Zusammenfügehelfer.
  Beide früheren Pakete bleiben unverändert. Ihre Berichtsfassung dokumentiert
  den damaligen eingeschränkten Überblick; die Galerie lässt die damals
  fehlenden verrauschten Beobachtungen ausdrücklich leer.
- Ablage von Überblick, Originalarchiven, Transportderivat und Auswertungen:
  lokale Cloud-Arbeits-/Exportkopie. Die 39 großen NPY liegen zusätzlich in
  der getrennten rekonstruierten Prüfkopie, nicht im empfangenen Derivat.
  Dauerhafte gemeinsame Archivablage und unabhängige geprüfte Zweitkopie **offen**.

### Entwicklungsabnahme der Dauer-/Rasterstudie vom 19.11.2026

- Lauf-IDs: `noise-followup-estimators-cloud-001` und
  `noise-followup-preflight-cloud-001`; zwölf reine Rauschfälle/48 Schätzungen
  sowie sechs N128-Zehnerworker, jeweils vollständig lesend bestätigt.
- `noise-followup-estimators-cloud-002` ergänzt Ressourcenangaben an denselben
  zwölf Entwicklungsfällen; alle 37 Eingabedateien und 48 Schätzerdateien sind
  bytegleich zu 001, keine zusätzlichen unabhängigen Fälle oder Suchworker.
- Ausführungscommit: `34ef0094d7ae52cbf56f6b012a76451325348444`, sauber;
  für Schätzerdiagnose 002 `04d9a760fc1e3eb8808fdb0763032b526fc9c568`, sauber.
  Beide dauerhaft über `refs/pull/102/head` erreichbar.
- Originalarchiv: `noise-followup-development-cloud-001.tar.gz`,
  1.698.753.038 Bytes; SHA-256
  `1f15e7f4c0ab1af8b670d6edf21cf4937f7600b42bef67998de38f0bb9ed43f0`.
- Eigenes Originalarchiv der Ergänzung: `noise-followup-diagnostics-cloud-002.tar.gz`,
  1.565.250.615 Bytes; SHA-256
  `8206130fdfb58b34f430b4a99b9d90e76c2519fde7b141a96f684fff6f55d97e`.
  156 Original-/Verify-/Logdateien plus Manifest; Archiv und Quellen vollständig
  gegen die gebundenen Dateihashes geprüft.
- 390 Original-, Verify-, Plot- und Logdateien plus Manifest; fertiges Archiv
  gegen sämtliche Datei- und Quellenhashes geprüft. Vollständige Originalformeln,
  Punktdaten und sechs technische PNG-/SVG-Paare enthalten.
- Bericht, Kosten, Aussagegrenzen und spätere Ressourcen-Ergänzung:
  [Entwicklungsabnahme](noise_followup_development_001.md).
- Ablage: lokaler Cloud-Exportordner `ringdown-noise-followup`.
  Dauerhafte Archivablage und unabhängige Zweitkopie **offen**.

### Priorisierte fehlende Belege

Ergänzung vom 12.11.2026: Das Bestätigungsarchiv 001 mit allen drei
wissenschaftlichen Abschnitten und technischem Manjaro-Vorlauf liegt vollständig
vor und ist lesend geprüft. Dafür fehlen keine weiteren Laufdateien. Die
älteren technischen Vorläufe in der folgenden Tabelle werden dadurch nicht
rückwirkend belegt; dauerhafte Archivablage und unabhängige Zweitkopien bleiben offen.

Abgleich am 06.11.2026 auf main `4df7eca`: Repository, lokale Worktrees,
bereitgestellte Anhänge und vorhandene Auditablagen geprüft; ergänzend die
zugänglichen Übergaben aus „zzz5_Implementierungspipeline“ und
„1_Schreibarbeit“ lesend abgeglichen. Kein Zugriff auf die privaten Geräteablagen
oder Backups. Die vier großen Originalserien, der Kreuzvergleich, beide frühen
rauschfreien Serien, Neustart-Abbruch 001 und Abschluss 002 sowie Zeitbudgetlauf
001 sind vorhanden und gezielt geprüft; diese Dateien werden nicht erneut angefordert.
Lokale technische Fixtures sind keine Manjaro-Originalserien. Die historischen
R1–R3-Prüfnachweise werden übernommen, ihre Audits nicht pauschal wiederholt.

| Priorität / Bezug | Benötigter Beleg | Zweck und betroffene Aussage |
| --- | --- | --- |
| 1 — `global-restarts-technical-001` auf Manjaro | Abschlussausgabe und vorhandener Prüfbericht einschließlich lesender Verifikation mit Herkunft; nur bei Unklarheit der ganze unveränderte technische Ordner. | Technischen lokalen Erfolg belegen; Startmeldung allein genügt nicht. Keine wissenschaftliche Ergebnisbehauptung und keine neue CI-Archivpflicht. |
| 1 — `iteration-time-prefix-001` und `iteration-time-technical-001` auf Manjaro | Vorhandene Abschlussausgaben bzw. Prüfberichte der technischen Vorläufe. | Ausführung der vorgesehenen Präfix-/Timerkontrollen dokumentieren; das bestandene wissenschaftliche Archiv beweist diese separaten Vorläufe nicht. Kein automatischer Wiederholungsauftrag. |
| 1 — Archivablage und Zweitkopien | Verständliche Bezeichnungen beider Speicherziele, Liste tatsächlich vorhandener Dateien und Ergebnisse der SHA-256-Prüfung beider Kopien mit Prüfdatum. Bei Backup lesenden Wiederherstellungscheck angeben. | Dauerhafte Sicherung; Metadaten genügen, keine erneute Übertragung bereits vorhandener Archive erforderlich. |
| 3 — `sr-repeatability-wsl2-threads1-001`, `sr-repeatability-manjaro-threads1-001` | Zunächst ursprüngliche Berichts-/Herkunftsmetadaten mit vollständigen Ausführungs-/Werkzeugcommits und Abschlussstatus; zugehörige Originalarchive bei fehlenden internen Belegen. Namen/Hashes stehen oben. | Ältere technische Wiederholbarkeitsdokumentation vervollständigen; keine zusätzliche Leistungsstudie. |
| 3 — frühe Portabilitätsläufe | Für die zwölf oben einzeln aufgeführten Geräte-/Lauf-IDs tatsächliche Archivnamen/Hashes bzw. unveränderte Ergebnisordner; besonders die vier AR(1)-Schema-1-Läufe mit fehlender Git-Herkunft. | Ältere technische Übertragungsnachweise, kein Engpass der aktuellen Neustartauswertung. Zuerst vorhandene Metadaten zuordnen; keine Wiederholung der Läufe. |

Nachlieferungen gezielt gegen vorhandene Quellen prüfen. Fehlende historische
Metadaten nicht aus heutigem Code ergänzen; neu gepackte Ordner sind nicht das
frühere Originalarchiv. Entscheidungen und Originalberichte bleiben erhalten;
neue Prüfungen werden mit Datum und Umfang separat ergänzt.
