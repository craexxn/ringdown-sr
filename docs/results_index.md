# Ergebnisindex und Archivierungsstand

Stand: 12.11.2026. Zentraler Wegweiser zu den belegten Versuchen und ihren
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
