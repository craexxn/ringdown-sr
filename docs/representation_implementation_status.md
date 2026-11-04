# Fortsetzungsstand: Ringdown-Kontrollpfade

Stand: 04.11.2026. PR #59 ist als
`79ff670b825efd8ba0e999edb983aec6f7e804ae` übernommen; der Dateibaum entspricht
dem geprüften Head `401ca5d79eff5a96b98bc99b89ecabd982c429e7`.
[Suchbudgetlauf 004](search_duration_results_manjaro_004.md) ist vollständig
abgeschlossen und unabhängig nachgerechnet. Wissenschaftliche Ausführung
bleibt auf Manjaro. Keine zusätzlichen Agenten.

## Aktuell: vollständiger Suchbudgetvergleich 004

- **Einstieg:** sauberer eigener Branch `codex/duration-manjaro-004-audit`
  ab `79ff670`, ein Worktree, kein offener PR beim Einstieg. Andere Branches,
  einschließlich zurückgestellter WSL2-Arbeit, erhalten.
- **Originalarchiv:** SHA-256
  `c2d9e330770746030bab9467b682a6b595cac25aa132dbb4decd1c4b03472289` bestätigt;
  523 Dateien, 522 Abschlussmanifest-Einträge, 520 ursprüngliche Verbrauchsanker
  und 72 Quellen geprüft. Eingangsarchiv 001 nicht erneut vorhanden; alle
  eingefrorenen Datenkopien und Bindungen geprüft. Keine Archivquellen oder
  serialisierten Zustände ausgeführt, keine wissenschaftlichen Fits/Suchen.
- **Selbst nachgerechnet:** alle 20 Zellen und 193 Kandidaten durch den
  tatsächlichen Elternprüfpfad, sämtliche Diagnosen, Originalauswahlen,
  Gruppenwerte und 20 Paardifferenzen reproduziert. Alle neuen Referenznachweise
  bei 128 Bit. Unabhängige skalare Kurvenmarker identisch. Zusätzlich alle
  193 Originalbäume nativ nachgerechnet: Vorhersagen/Verluste bitgleich,
  Grammatik, Komplexität und Baumrundreise bestätigt; null Zielfunktionscallbacks.
  Originaldateien unverändert. Eigene Nachweise unter
  `/workspace/audits/duration-manjaro-004/` in `audit.json`, `native_replay.json`
  und `original_sha256.json` samt eigenen Skripten/Logs.
- **Befund:** K200 → K2000: 3/5 → 4/5, neuer unterstützter Erfolg bei Seed
  20261107; planmäßig `supported_structure_gain`. A200 → A2000: 2/5 → 3/5,
  neuer Kurvenerfolg bei Seed 20261106 ohne Erkennerunterstützung;
  `approximation_gain_only`. Unterstützte K-Auswahlen insgesamt weiter 2/5.
  Deutlicher Zwischenpunkt-Gegenfall bei K/20261106, deshalb kein pauschaler
  Schluss aus sinkender Trainings-MSE. Physikalische Identifikation und
  allgemeine Übertragbarkeit bleiben offen; adaptive Entwicklung.
- **Aufwand:** 2.576,5844 Sekunden aufgezeichnete Gesamtdauer; alle Worker unter
  600 Sekunden, Serie unter 7.200 Sekunden. K/A-Iterations-, Profil- und
  Auswahlregeln unverändert. Neue Referenzkontrolle beendet die drei früheren
  Teilserien nicht rückwirkend; erste vier frische Fronten identisch zu 003.
- **Arbeitsstand:** ausschließlich Ergebnis-/Statusdokumentation im neuen
  Ergebnis-PR. Maßgeblicher Head und Dokumentations-CI stehen dort; keine
  Codeänderung oder erneute volle technische Suite für diesen Textnachtrag.
  Die vollständige Implementierungs-CI 41785241800 und das übermittelte
  KI-basierte Review von #59 betreffen den unveränderten Ausführungsstand.
- **Nächster abgegrenzter Schritt:** gesonderten Übertragbarkeitsplan anhand
  dieses Befunds festlegen, keine automatische weitere Budget-/Seedserie.
  Die vereinbarte Erinnerung an eine kurze Bereinigungsbestandsaufnahme wird
  jetzt ausgelöst: funktionierenden Stand und Originalarchiv erhalten, danach
  kleine getrennte Änderungen für konkrete Wartungsprobleme. Noch keine
  Bereinigung implementiert; numerische Abläufe und historische Lesbarkeit
  bleiben erhalten. Der Schwerpunkt bleibt auf wissenschaftlichen Folgetests.

## Grundlage: Implementierung der Vorhersageprüfung


- **Grundlage:** übermitteltes KI-basiertes Methodenreview zu PR #58,
  Head `836f6c0d8e560a6c9900e1a38385cd7137822c96`, Basis
  `4c49723e08f6deb9eb086922c1be546819f3408f`, ohne korrekturbedürftige Befunde.
  Laut Review 61 numerische Assertions, sechs native und acht Python-
  Nachrechnungen bestanden; CI 41781938938 eingesehen. Die Originalarchive
  fehlten im separaten Review. Diese Prüfungen sind übermittelte Nachweise.
- **Planbindung:** SHA-256
  `2a215b6f178c085cad6611070124e09e929f35917eba66723f4522c1fe81393c`,
  zur Laufzeit an den tatsächlichen Merge-Commit `9bff8a2` gebunden.
  Ursprünglicher Plancommit vor Code `68cbe10`; frühere Planbytes unverändert.
- **Umsetzung:** Originalbaum mit rationalen Grundoperationen und RN64,
  gerichtete MPFR-Bereiche mit einem Nachbarschritt für exp/sin/cos,
  unveränderte Präzisionsleiter und rationale Breitenentscheidung. Neue
  gepinnte Abhängigkeit gmpy2 2.2.2. Referenzarbeit direkt in Worker und
  Elternprozess, ohne zusätzlichen Prozess, Suchzustand oder Cache.
  Tatsächliche Bibliotheksversionen werden protokolliert; lokale Kontexte
  ändern die Float64-Suchumgebung nicht. Vollständige unabhängige Nachrechnung
  aller Belege einschließlich ungewählter Kandidaten.
- **Erhalten:** native und tabellarische Verluste, eigene Reduktionsschranken,
  Originalauswahl, Datenrollen, Parameter-/Aliasreplays, Strukturerkenner,
  Optionen einschließlich `should_simplify=false` und Zeitgrenzen 600/7200.
  Keine wissenschaftliche Cloud-Suche, kein WSL2- oder Parallelisierungsschritt.
- **Originaldatenbezug:** Archiv 003 erneut gegen den bekannten SHA und alle
  143 ursprünglichen Dateihashes bestätigt. Fixture enthält 34 originale
  Kandidaten sowie zehn ausdrücklich nachträgliche CSV-Rekonstruktionen;
  kein Archivcode und keine serialisierten Suchzustände ausgeführt. Alle
  44 Vorhersagereferenzen bestehen hier bereits bei 128 Bit. Die vier alten
  Abweisungsfälle sind abgedeckt; das ist kein vollständiger Serienbefund.
- **Selbst ausgeführte technische Nachweise:** 183 gezielte Python-Tests
  bestanden. Der feste native Lauf
  `results/prediction-reference-development-003.json` bestätigt alle 44 Bäume,
  deren unveränderte nativen Vorhersagen/Verluste und die neue Kontrolle;
  zusätzlich 152 unabhängige gerichtete MPFR-/Knotenfolge-Assertions.
  Referenzarbeit für 44 Bäume hier 1,35 Sekunden, fester Gesamttest nach
  Runtime-Start 18,31 Sekunden; keine Laufzeitgarantie für neue Suchfronten.
  Referenz: gmpy2 2.2.2 / MPFR 4.2.1 / GMP 6.3.0; Gegenrechnung:
  Julia 1.13.1 / MPFR 4.2.2. Null Zielfunktionscallbacks, keine Suche/Fits.
  Ruff, Format, Dokumentation und unveränderte frühere Planbytes bestätigt.
- **Abgeschlossener Prüf-/Übergabestand:** vollständige technische CI
  41785241800 am Head `401ca5d` bestanden, einschließlich 2.075 Python-Tests,
  festem 44-Baum-Nachweis und allen Integrationen. Übermitteltes KI-basiertes
  Implementierungsreview desselben Heads ohne korrekturbedürftige Befunde:
  laut Review 104 fokussierte Python-Tests und 1.012 separat mit Decimal/Taylor
  geprüfte Modellwerte bestanden; Originalarchive fehlten dort. Befund und
  Aussagegrenzen stehen in [PR #59](https://github.com/craexxn/ringdown-sr/pull/59).
  Danach manueller Squash-Merge und frischer Manjaro-Lauf 004; Ergebnis oben.
- **Vormerkung nach vollständiger Manjaro-Verifikation:** bei der gemeinsamen
  Auswertung ausdrücklich an eine kurze Bestandsaufnahme für gezielte
  Bereinigungen erinnern. Zuerst funktionierenden Code und Originalergebnisse
  sichern; nur konkrete Wartungsprobleme, kleine getrennte Änderungen mit
  Regressionen. Numerische Reihenfolge, Suchverhalten, eingefrorene Pläne und
  historische Lesbarkeit erhalten. Kein großes Refactoring; reine technische
  Testerfolge lösen die Vormerkung noch nicht aus.

## Grundlage: Vorhersageabweichung in Lauf 003

- **Abgeglichener Einstieg:** sauberer eigener Branch
  `codex/duration-manjaro-003-audit` auf
  `e501e9d83315289cb4c59716495e93aa25154ecd`, ein Worktree, `origin/main`
  identisch, keine offenen PRs beim Einstieg. PR #56 ist tatsächlich gemergt;
  sein Codebaum entspricht dem geprüften Head `be887730d9f57c5fbede914240b57a3724e5eb6d`.
  Andere Branches einschließlich aufgeschobener WSL2-Arbeit bleiben erhalten.
- **Selbst ausgeführter Originalaudit:** SHA-256 bestätigt, 143 Dateien
  erfasst, 96 Verbrauchsanker und 69 Quellen geprüft. Alle vier abgeschlossenen
  Zellen mit 34 Kandidaten, Originalauswahlen und Diagnosen erneut verifiziert.
  Die zehn CSV-Bäume der fünften Zelle nativ ohne Suche/Fit nachgerechnet:
  sämtliche gespeicherten Verluste bitgenau, alle separat geprüften Verlust-
  und Reduktionsbedingungen bestanden; vier Vorhersagevergleiche scheitern.
- **Ursache des ersten Abbruchs:** CSV-Index 5, Messpunkt 18 exakt reproduziert.
  Benachbarte Float64-Ergebnisse der inneren `exp`-Operation werden durch
  Division mit einer großen Konstante im Sinusargument verstärkt. 81 Teilbäume
  nativ/NumPy/hochpräzise ausgewertet; erste verursachende Operation zusätzlich
  mit 100 und 200 Dezimalstellen geprüft. Kein Archivcode und keine
  serialisierten Zustände ausgeführt; Originaldateien unverändert.
- **Ergebnisgrenze:** alle vier abgeschlossenen Originalauswahlen bestehen die
  Kurvenkriterien, nur eine die bestehende Struktur-/Parameterdiagnose.
  Der vollständige Vergleich bleibt gesperrt; aus CSV-Replays der gescheiterten
  Zelle wird keine nachträgliche Originalauswahl oder positive Verifikation.
- **Arbeitsstand:** ausschließlich Audit-/Statusdokumentation; keine Änderung
  an Laufzeitcode, eingefrorenen Plänen, Toleranzen oder Suchkonfiguration.
  Lokale Auditbelege unter `/workspace/audits/duration-manjaro-003/`:
  `audit.json`, `native_replay.json`, `separate_loss_checks.json`, `trace.json`
  und `rounding_case.json`. Quellskripte dort sind eigene Auditwerkzeuge,
  kein ausgeführter Archivcode. Dokumentationsprüfung und PR-Stand stehen
  im zugehörigen PR; keine vollständige Testsuite für diese reine Textänderung.
- **Nächster abgegrenzter Schritt:** die im Befund vorgeschlagene baumabhängige
  Vorhersageprüfung methodisch präzisieren, unabhängig begründen und vor Code
  versionieren. Alle vier betroffenen CSV-Bäume und echte Fehlerfälle müssen
  abgedeckt werden. Keine pauschale Toleranzerhöhung und noch kein Neustart.
  Eine Erweiterung des Strukturerkenners bleibt eine getrennte Entscheidung.

## Historisch: inkonsistenter nativer Verlust in Lauf 002

- **Abgeglichener Einstieg:** sauberer Branch `codex/duration-manjaro-002-audit`
  auf `76a740018b4426bc1651a5fed3bf214659a083cf`, ein Worktree, `origin/main`
  identisch, keine offenen PRs. Andere Branches erhalten. Die aufgeschobene
  WSL2-Datenportabilität bleibt ausschließlich im lokalen Branch
  `codex/frozen-archive-inputs` bei `c5f1c5c`; nicht Teil dieser Änderung.
- **Originalaudit:** Archivhash bestätigt, 143 Dateien, 96 Verbrauchsanker,
  68 Quellen und alle vier abgeschlossenen Zellverifikationen geprüft.
  Die letzten zwei Originalauswahlen bestehen Kurven-/Parameterdiagnose;
  Gesamtvergleich weiter gesperrt. Sieben feste native CSV-Replays ohne
  Suche/Fit: sechs gespeicherte Verluste bitgenau, der siebte reproduziert
  exakt den gemeldeten Abstand `0.03399585286266448` zu
  `0.03399585394761332`. Keine serialisierten Zustände ausgeführt.
- **Begründung:** Ein unabhängiger Achtpunktfall beweist in beiden nativen
  Vereinfachungspfaden veraltete Verluste. Ohne Mutationshistorie bleibt die
  alleinige Ursachenzuordnung für den Archivfall offen. Die strenge
  Verlustprüfung ist korrekt und bleibt unverändert.
- **Plan vor Code:** [gemeinsames Profil ohne automatische Vereinfachung](search_duration_simplification_plan.md),
  Commit `f13d7687ddd06d5c68fbbf7ae5baa67639d74ca3`, SHA-256
  `46fb2510957a4ee37d3f61e59291b8a5081db9ff64e7bd36a62aad0073901a0d`.
  Format 3 setzt nur im Suchbudgetpfad `should_simplify=false`; alle früheren
  nativen Aufrufer behalten `true`. Optionen werden nativ und im Elternprozess
  absolut geprüft, einschließlich erster Zelle. Frühere Planbytes bleiben gebunden.
- **Selbst ausgeführte Prüfungen:** alle 1.929 Python-Tests, Ruff, Format und
  Dokumentationsprüfung bestanden. `results/duration-simplification-technical-003.json`
  bestätigt die drei festen nativen Replayfälle, 180 native Assertions und
  zusätzliche Callback-Guard-Prüfungen ohne Suche/Fit. Die vollständige lokale
  Integration `results/duration-simplification-integration-001` bestand:
  zehn native Profile, 20 Pythonprofile, feste Referenzen und fünf frische
  K2–A2–K3–A3–K2-Worker am Achtpunkt-Signal; wiederholte Front identisch.
  Maßgeblicher Head, vollständige CI und gezieltes KI-basiertes Review werden
  im PR festgehalten. Kein Merge und kein wissenschaftlicher Lauf hier.
- **Nächster Schritt:** nach Prüfung und manuellem Merge vollständige frische
  Serie `duration-manjaro-003`, unveränderte 20-Zellen-Anordnung, alle Seeds
  und Budgets, 600/7200 Sekunden. Keine Übernahme alter Teilzellen, kein
  Warmstart und keine rückwirkende Umwertung. [Startweg](search_duration.md).
- **Nachgetragener Reviewstand:** übermittelter KI-basierter Befund zu Head
  `be887730d9f57c5fbede914240b57a3724e5eb6d` gegen `76a740018b4426bc1651a5fed3bf214659a083cf`
  ohne korrekturbedürftige Befunde; im [PR #56](https://github.com/craexxn/ringdown-sr/pull/56)
  dokumentiert. Die separate Reviewprüfung hatte keinen Zugriff auf die
  Originalarchive. Der anschließende Manjaro-Lauf 003 ist oben eingeordnet.

## Historisch: Versionierte Verlust- und Strukturverifikation


- **Abgeglichener Einstieg:** eigener sauberer Branch `codex/duration-abort-audit`
  bei `6dccd469fdb9f1688f54755b3c6c48e4f105e14d`, ein Worktree, andere Branches
  erhalten. `main` weiterhin `d4899ba`; nur PR #55 offen und als Entwurf.
  Die Fortsetzung erweitert diesen PR um die begründete Korrektur; kein Merge.
- **Plan vor Implementierung:** [Verifikationsergänzung](search_duration_verification_plan.md),
  Commit `2a0b50926cd2983d0cd6cc1307ccc28d0a2822fa`, SHA-256
  `b6f7cef2227eeacccf8156d02e8899e6fc83b7bd1f29735c1a402922a9d83062`.
  Der ursprüngliche Suchbudgetplan wird zusätzlich weiter auf seine alten
  Bytes geprüft; frühere Pläne und Archive unverändert.
- **Implementierung:** Suchbudget-/Profilformat 2 aktiviert allein den neuen
  gewöhnlichen MSE-Nachweis. Exakte rationale Quadratsummen und hergeleitete
  Reduktionsschranken prüfen jeden Verlust gegen eigene Residuen; nativer
  Verlustvergleich und Vorhersageprüfung bleiben bestehen. Der Elternprozess
  berechnet alle Kandidatennachweise neu. Auswahl bleibt nach nativer MSE.
- **Strukturdiagnose:** optionaler Erkenner für genau einen Sinus/Kosinus im
  Zähler und einen Exponentialfaktor im Zähler oder Nenner. Exakte rationale
  Radiant-/Pi-Anteile, begrenzte Pi-Konversion, rohe und Alias-Replays bleiben
  getrennte Gates. Ältere Aufrufer behalten den bisherigen Standard.
- **Prüfungen am ersten Implementierungsstand ab32fcf:** alle 1.907 Python-Tests,
  Ruff und Formatprüfung bestanden lokal; darunter 53 neue numerische/strukturelle Gegenprüfungen und alle 31
  Suchbudget-Treibertests. Die beiden CSV-Formeln
  erfüllen Kurven- und Parameterdiagnose ohne Nachfit oder Baumänderung.
  Vollständige Python-/Julia-CI und neue feste native Regressionstests sind
  erforderlich; aktueller Head und abgeschlossene Prüfnachweise stehen in
  [PR #55](https://github.com/craexxn/ringdown-sr/pull/55). Ein erster lokaler
  nativer Prüflauf bestand die fachlichen Assertions, brach aber wegen während
  des Laufs geänderter Quellen an der abschließenden Quellenbindung ab;
  er ist kein vollständiger Prüfnachweis. Die vollständige Wiederholung mit
  unveränderten Quellen bestand: `results/duration-replay-technical-002.json`,
  beide nativen Verluste und Vorhersagen bitgenau bestätigt, beide neue
  Verlust- und Parameterdiagnosen bestanden, null Such-/Fitaufrufe.
- **Technische Tabellenpräzisierung:** Die anschließende vollständige lokale
  Integration bestand K2/A2, scheiterte aber in K3 an einem zusätzlichen
  CSV-Rundungseffekt. Gepinntes Pandas liest `0.008261169598036541` als
  `0.0082611695980365`. [Befund und Präzisierung](search_duration_table_loss_note.md)
  wurden vor der Korrektur als `fee62058992c84a9930aa765233ebdc095c54cb1`
  eingefroren; der Hash ist zusätzlich im Laufzeitpfad gebunden. Die Tabellen-
  kontrolle bleibt beim alten relativen Vertrag; echte native und Python-
  Verluste müssen unverändert die strengere Residuenprüfung bestehen.
  Der konkrete CSV-Fall und ein falscher Tabellenwert sind eigene Tests.
  Der fehlgeschlagene technische Lauf bleibt erhalten. Vollständige Integration
  und CI müssen am korrigierten Head erneut bestehen; aktuelle Nachweise in #55.
- **Regressionsdaten korrigiert:** CI 41682098788 am Head `78f3e94` fand sechs
  fehlgeschlagene Skalierungsfälle unter sonst 1.902 bestandenen Python-Tests.
  Die neuen Tests kombinierten gespeicherte native Vorhersagen/Verluste mit
  erneut generierten Beobachtungen. Die CI-Referenz-MSE dieser Kombination
  unterscheidet sich nachweislich von jener der Original-Eingabebits.
  Die Fixture bindet deshalb nun Trainingszeiten, Beobachtungen und beide
  Replays als zusammengehörige Float64-Vektoren. Der feste native Test nutzt
  dieselben ursprünglichen Eingaben; Laufzeitprüfung und Toleranzen unverändert.
  Die parallel laufende lokale Integration 002 wurde für diese Testkorrektur
  unterbrochen und liefert keinen vollständigen Abschlussnachweis.
- **Gezieltes KI-basiertes Review und P3-Korrektur:** Übermittelter Befund zu
  `70791db19755a31e4f6d689c5bc8882930138705` gegen
  `d4899ba3a858576758b055c3b36bffb010d5c305`: Verlustprüfung und Phasen-/Alias-
  umrechnung grundsätzlich methodentreu; ein Randfall der Normalbereichssperre.
  Der Gegenfall wurde selbst reproduziert: 128 Residuen `2**-511`, normale
  Referenz-MSE `2**-1022`, aber ein akzeptierter subnormaler nativer Verlust
  `nextafter(2**-1022, 0)`. `_reduction` prüft nun auch jeden zu bestätigenden
  Verlust selbst auf null oder Normalbereich. Die getrennte CSV-Regel und
  die eingefrorenen Pläne bleiben unverändert. Acht zusätzliche Grenzfälle
  decken gemeldete und neu berechnete Verluste sowie die erlaubte Grenze
  und CSV-Ausnahme ab; sechs davon scheiterten am alten Code. Nach Korrektur
  bestanden alle 116 gezielten Verlust-, Struktur-, Plan- und Treibertests
  sowie Ruff/Format. Der bisherige vollständige CI-Nachweis mit 1.908 Tests
  gehört zu `70791db`; neuer Head und seine vollständige CI stehen in
  [PR #55](https://github.com/craexxn/ringdown-sr/pull/55). Eine erneute
  Methodenreviewrunde ist für diesen begrenzten Befund nicht erforderlich.
- **Nächster wissenschaftlicher Schritt vorbereitet:** nach vollständiger
  technischer Prüfung und Merge `duration-manjaro-002`, alle 20 Prozesse neu,
  gleiche vorab festgelegte Seeds, Reihenfolge, Budgets und Abbruchgrenzen.
  Keine Übernahme der ersten zwei Zellen; bereits gesehene Seeds ausdrücklich
  als adaptive Entwicklungsprüfung einordnen. Befehle in der
  [Bedienung](search_duration.md). Hier keine wissenschaftliche Ausführung.

## Historisch: Audit des abgebrochenen Suchbudgetvergleichs

- **Arbeitsstand:** sauberer Einstieg auf `codex/search-duration-preparation`
  bei `4a9286bfe1aa49db3eda174a3aa14c69f1160e74`, ein Worktree, andere Branches
  erhalten. Remote geprüft, keine offenen PRs beim Einstieg. Neuer
  Dokumentationsbranch `codex/duration-abort-audit` auf `main`
  `d4899ba3a858576758b055c3b36bffb010d5c305`; keine Laufzeitänderungen.
- **Befund:** [Originalarchiv-Audit und numerische Nachrechnung](search_duration_results_manjaro_001.md).
  Archivhash `d73e990cf0c8092f841bc402aa247eca0311c963421249b5e60ae2e73c55074a`;
  im übermittelten Text fehlte das erste Zeichen. Zwei Zellen vollständig,
  dritte bei `no_nested_trig`, Seed 20261103, 2000 Iterationen nach beendetem
  Fit gescheitert. 17 Zellen nicht gestartet; alle Aggregate gesperrt.
- **Eigener Nachweis:** 93 Dateien, 58 ursprüngliche Dateianker und 65 Quellen
  geprüft; beide abgeschlossenen Zellverifikationen exakt reproduziert.
  Alle acht CSV-Bäume von Zelle 3 nativ ohne Suche/Fit nachgerechnet, sämtliche
  gespeicherten Verluste bitgenau reproduziert. Python-/Julia-Vorhersagen der
  zwei guten Formeln unterscheiden sich höchstens um `1,11e-16`; der rein
  relative Vergleich ihrer nahezu verschwindenden MSE löst den Abbruch aus.
  Beide Formeln liegen auf beiden Rastern klar innerhalb der Kurvengrenzen.
- **Zweite Grenze:** Der Erkenner unterstützt bisher `exp * cos`, nicht
  `sin / exp`; damit weiterhin `not_supported / not_assessed`. Algebraische
  Parameter und Kurvenbefund sind dokumentiert, keine rückwirkende Änderung
  der Originalmarker oder nachträglich veröffentlichte Auswahl.
- **Nächster Schritt:** mathematisch begründete, separat gebundene
  Verifikationsergänzung und eng begrenzte Strukturdiagnose vor weiteren
  wissenschaftlichen Suchen. Umgang mit bereits gesehenen Seeds vor Ausführung
  festlegen. Keine automatische Wiederaufnahme, keine Ersatzwahl und kein
  abgeschlossener Budget-/Grammatikvergleich. Originale und Pläne unverändert.
- **Dokumentationskorrektur:** versehentlich beim Konfliktlösen in #54
  eingefügten URL-Text im historischen Nachweis entfernt. Passende Prüfung:
  schlanke Dokumentations-CI; keine neue Suche, Optimierung oder Voll-CI
  für diesen reinen Dokumentationsnachtrag.

## Historisch: Vorbereitung des Suchbudgetvergleichs

- **Beschluss:** 200/2.000 äußere Suchiterationen, beide Grammatiken, fünf neue
  Seeds und 20 frische Prozesse. Zwei Stunden Gesamtgrenze ausdrücklich
  gewählt; 600 Sekunden je Worker. Lokale Konstantenoptimierung bleibt 100/2.
  Die [Literaturauswertung](search_duration_literature.md) liefert Gründe und
  Ressourcenbeispiele, keine optimale Ringdown-Laufzeit.
- **Plan vor Code eingefroren:** [Methodenplan](search_duration_plan.md),
  Commit `194cfb499e8c53b8243d19c4d11d58a006baff95`, SHA-256
  `8906a66930848d733e5b2744d40c5fa9c4051db2b876e200908d74ae9ac0b75d`.
  Alle sieben bisherigen Pläne und Originalbefunde bleiben erhalten.
- **Arbeitsbasis:** Branch `codex/search-duration-preparation` auf dem
  Ergebnis-Head `e6472bba72b672642987d3ffd55c3bd59694ac05` von PR #53.
  Dieser Ergebnisnachtrag ist enthalten; `main` blieb beim Einstieg `23a2113`.
- **Umsetzung:** isolierter neuer Treiber verwendet die bestehende strenge
  Prüfung und Abbruchsicherung. Zusätzlich Prüfung des tatsächlichen
  `equation_search`-Budgets; keine Änderung der numerischen Zielfunktion.
  Vier Gruppen und sämtliche Seedpaare; Freigabe erst nach allen 20 Zellen.
  Ein positiver Strukturbefund muss zu einem neuen 0→1-Erfolg derselben hohen
  Originalauswahl gehören. Bedienung: [Suchbudgetvergleich](search_duration.md).
- **Vorhandener technischer Nachweis:** Am Implementierungs-Head
  `98f60210f19ec344ba1724a51f399f6581791cf8` bestand die vollständige
  [CI 41616411175](https://github.com/craexxn/ringdown-sr/actions/runs/41616411175):
  1.846 Python-Tests und sämtliche nativen Integrationen. Run, Schritte und
  Logs wurden selbst geprüft; der temporäre Mergebaum war exakt dateigleich.
  Lokal bestanden 46 gezielte Tests und die neue native Integration mit zehn
  Optionsprofilen, 20 Pythonprofilen, sechs Referenzen, 28 Grammatikfällen und
  fünf kleinen Suchworkern. Die wiederholte K2-Front war identisch.
- **Übermitteltes KI-basiertes Review zu PR #54:** Head
  `98f60210f19ec344ba1724a51f399f6581791cf8`, Vergleichsbasis
  `23a21131e6fafcdc748e47098c018a1158f1629b`; alle 18 geänderten Dateien,
  einschließlich Ergebnisnachtrag #53, und relevante Aufrufer geprüft.
  Im geprüften Umfang methodentreu, kein gefundener Laufzeitfehler; ein P2
  im Test der Abschlussveröffentlichung. Dessen Injektion griff schon beim
  gesperrten Startbericht. Eigene Reproduktion bestätigt: Der alte Test bestand
  mit null Workern, obwohl jeder Aufruf von `finalize()` zum Testfehler geführt
  hätte. Die im Review genannten weiteren acht Gegenprüfungen und 30 skalaren
  Formelmetriken sind übermittelte Nachweise und wurden hier nicht wiederholt.
- **Gezielte P2-Korrektur:** Nur der Test und Statusdokumentation geändert.
  Die Injektion greift erst nach dem positiven Rename mit `completed / passed`.
  Sie verlangt 20 durchlaufene Mock-Worker, 20 abgeschlossene Zellen,
  freigegebene Aggregate und ein vorhandenes Abschlussmanifest vor dem Fehler.
  Danach müssen die Aggregate gesperrt und das Manifest entfernt sein.
  Alle drei Fälle bestehen: `OSError`, `KeyboardInterrupt` und eine simuliert
  überschrittene Zeitgrenze, die das echte `clock.check()` nach dem Rename
  abfängt. Zusätzliche reine Testmutationen ohne Widerruf beziehungsweise mit
  zurückbleibendem Manifest werden jeweils in allen drei Fällen erkannt.
  Keine Änderung an Laufzeitcode, Daten, Pins oder eingefrorenen Plänen.
- **Aktueller Prüfstatus:** Die gezielte Gegenprüfung erledigt den P2-Befund;
  eine weitere Methodenreviewrunde ist laut übermitteltem Review nicht nötig.
  Der genaue Korrektur-Head und die automatisch für Teständerungen gestartete
  vollständige CI stehen in [PR #54](https://github.com/craexxn/ringdown-sr/pull/54).
  Die frühere erfolgreiche CI ist kein Nachweis für den neuen Head.
  Keine wissenschaftlichen 200-/2.000-Suchen hier.
- **Nächster Schritt:** vollständige CI des Korrekturstands vor Merge und
  einmaliger Manjaro-Serie abschließen. Weitere Tests erst aus den
  wissenschaftlichen Ergebnissen begründen, keine automatische Budgetleiter.

## Historisch: Abgeschlossener Grammatikvergleich und Ergebnisnachtrag

- **Einstieg selbst abgeglichen:** sauberer Branch
  `codex/trigonometric-grammar-preparation` bei
  `b4c363ada9d3c35f46ec0eec36687dda82c5fe0e`, ein Worktree, weitere lokale
  Branches erhalten. Remote-Fetch erfolgreich, keine offenen PRs beim Einstieg.
  `main` steht bei `23a21131e6fafcdc748e47098c018a1158f1629b`; gleicher
  Dateibaum wie der geprüfte Implementierungs-Head. Kein eigenständiger Merge.
  Neuer Ergebnisbranch `codex/grammar-results-manjaro-001` auf dieser Basis.
- **Ausführung:** `grammar-manjaro-001` am sauberen Commit `23a2113`,
  sechs frische Zellen in festgelegter Reihenfolge. Aufgezeichnet am 03.11.2026
  von 09:10:15 bis 09:16:26 UTC; insgesamt 371,287 Sekunden.
  Originalarchiv-SHA-256 selbst bestätigt:
  `8d7fc8b09ed9c5091acef5237f5512ddb9fb014598e72ee3d9d4e435f33e3915`.
- **Eigener lesender Audit:** 165 Dateien, 164 Gesamtmanifesthashes,
  sämtliche Zellprüfsummen, 162 eingefrorene Dateianker und 59 Quellen gegen
  den Ausführungscommit geprüft. Planbytes, Eingabebits und Trainingsrollen
  stimmen. Alle sechs vorhandenen Zellverifikatoren, gespeicherten nativen
  Options-/Syntax-/BLAS-Nachweise, Referenzdiagnosen und Aggregate bestehen.
  Unabhängiger skalarer Replay aller 51 Bäume bestätigt beide Raster,
  Vorhersagen, Residuen, MSE, Originalauswahl und Grammatikregel. Keine neue
  Julia-Ausführung; serialisierte Zustände/Pickles nicht geladen.
- **Ergebnis:** beide Arme 0/3 erfolgreiche Originalauswahlen, kein
  kurvenguter ungewählter Kandidat. Alle 51 Strukturdiagnosen `not_supported`,
  Parameter und physikalische Identifikation `not_assessed`. A verbessert
  den ersten Seed, erhöht aber MSE/RMS beim zweiten und dritten. Die
  [Detailauswertung](trigonometric_grammar_results_manjaro_001.md) enthält
  Originalformeln, vollständige Fehler, Nenner, Unterschiede und Aufwand.
  Kein Wechsel zur eingeschränkten Grammatik, keine weitere Restriktionsstufe.
- **Prüfgrenzen:** das frühere Eingangsarchiv wurde hier nicht erneut gehasht;
  die im neuen Archiv gespeicherten Arrays wurden direkt gegen die
  eingefrorenen Bits geprüft. 15 veröffentlichte historische 100/2-Metriken
  stimmen exakt mit den frischen K-Auswahlen überein; der vollständige frühere
  Budgetarchiv-Audit bleibt offen. Der Alias-Blindfleck bei `8*fs` bleibt
  bestehen, `trajectory-manjaro-001` bleibt `incomplete / failed`.
- **Arbeitsstand:** ausschließlich neuer Ergebnisbericht, README und dieses
  bestehende Arbeitsdokument. Code, Pins, Auswahl und alle sieben
  eingefrorenen Laufzeitpläne unverändert. Die erfolgreiche vollständige
  [Implementierungs-CI](https://github.com/craexxn/ringdown-sr/actions/runs/41600969196)
  und das übermittelte KI-basierte Review aus #52 bleiben vorhandene
  Nachweise; keine routinemäßige Wiederholung. Der Ergebnis-PR hält den
  vollständigen Dokumentations-Head und dessen schlanke Prüfungen fest.
  Lokale Audithilfen und Nachrechnungen:
  `/workspace/audits/grammar-manjaro-001/`; Originale unverändert erhalten.
- **Nächster abgegrenzter Schritt:** das weitere methodische Vorgehen anhand
  der abgeschlossenen Befunde ausdrücklich neu abwägen. Keine Wiederholung,
  zusätzlichen Seeds, Budgets, Nachfits oder automatische Methodenänderung.
  Freie Formelfindung bleibt Forschungsziel; Auswahlverfahren,
  Übertragbarkeit und Hauptversuche zur Hintergrundlänge/Kovarianzgewichtung
  bleiben eigenständige offene Entscheidungen.

## Historisch: Angenommener Grammatikvergleich vor Manjaro-Ausführung

- Erneuter Einstieg: sauberer Checkout `codex/free-form-methods-literature`
  bei `114bb24dd983c0316c89379bc9477bed5835655a`, ein Worktree; weitere lokale
  Branches erhalten. Remote-Branches vollständig abgefragt, einzig PR #51
  offen und als Entwurf konfliktfrei. `main` unverändert bei
  `2d9ed90043628f0c3b2f948634b1bdcd769bc886`. Kein Merge ausgeführt.
- Veröffentlichungsbranch `codex/trigonometric-grammar-preparation` auf dem Literatur-Head.
  Die neue Arbeit baut auf PR #51 auf; solange dieser offen bleibt, enthält ein
  Vergleich gegen `main` auch die Literaturdokumentation. Keine Umschreibung
  vorhandener Commits oder fremder Arbeit.
  Der erste Push wurde wegen der Commit-E-Mail-Privatsphäre abgewiesen.
  Der lokale Vorbereitungsbranch `codex/trigonometric-grammar-control` bleibt
  erhalten; die Veröffentlichung verwendet eine öffentliche GitHub-Noreply-
  Identität und einen neuen Plancommit bei identischen Planbytes.
- **Angenommen:** Der zuvor bedingte Vergleich ist ausdrücklich beauftragt;
  die wissenschaftliche Ausführung bleibt auf Manjaro. Hier vollständig
  vorbereiten. [Verbindlicher Plan](trigonometric_grammar_plan.md), Commit
  `5de1a4a0bbb8282ac77f06e21f0314acaa99eade`, SHA-256
  `e8fe21344cedc93196d77e83918eb989907fe75e7cfa7219ee17d22661be70b5`.
  Genau sechs Zellen, bekannte Seeds mit wechselnder Paarreihenfolge, 100/2,
  beide Häufigkeitsschalter und ein zusätzlicher Syntaxprior im A-Arm.
- **Implementiert:** Eigener Profil-/Worker-/Treiberpfad mit nativer absoluter
  Optionsprüfung, vier vollständigen Verschachtelungspaaren, Kontrolle aller
  exportierten A-Bäume und bisherigen Verlust-/Auswahl-/Replaygates.
  Quellen und Datenrollen sind manifestiert; Abbruch- und Berichtssperren
  einschließlich Widerruf unvollständiger Abschlüsse bleiben erhalten.
  Allgemeine Suchdefaults, Pins und die sechs bisherigen Laufzeitpläne
  bleiben unverändert. Der neue Plan ist zusätzlich der vollen CI zugeordnet.
- **Prüfumfang:** Python-Gegenfälle für Profile, manipulierte Artefakte,
  Auswahl-/Strukturgates, Zeitgrenzen und Abbrüche; native Options-/Syntax-/
  Aliasreferenzen und eine technische K–A–K-Folge auf `y=1+t`. Die sechs
  wissenschaftlichen Zellen sind keine Tests. Konkrete Ergebnisse und
  Abschlusszustand werden am vollständigen Head im Implementierungs-PR gesichert.
  Keine zusätzlichen Agenten oder routinemäßige Reviewrunde.
- **Umgebung selbst abgeglichen:** Cloud läuft, Richtlinien aktuell und
  durchgesetzt, keine konfigurierten Geheimnisse/VPN-Verbindungen. Vorhandene
  Python-/Julia-Umgebung und beschreibbare Cachepfade verwendet. Git-Fetch mit
  Netzwerkfreigabe funktioniert über den bestehenden Proxy; keine Änderung
  von Pins, Proxy oder TLS. Haswell/Threadlimit 1 nur für den Kontrollpfad.
- **Nächster Schritt:** Nach vollständiger technischer Prüfung genau eine
  Manjaro-Serie am dokumentierten sauberen Commit gemäß
  [Bedienung](trigonometric_grammar.md), anschließend Originalarchiv sichern
  und Ergebnisse gegen die eingefrorenen Regeln auswerten. Keine automatische
  Wiederholung, Ersatzwahl, Budgeterhöhung oder Hauptversuchsfreigabe.
  Der frühere Budgetarchiv-Audit bleibt offen; frühere numerische Nachweise
  wurden hier nicht wiederholt. `trajectory-manjaro-001` bleibt `incomplete / failed`.

## Historisch: Literaturabwägung nach abgeschlossenen Pilotkontrollen

- Einstieg in dieser Cloudinstanz: sauberer Branch `work` bei
  `f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1`, ein Worktree. Der weitere
  lokale Branch `codex/cloud-environment-setup` blieb erhalten. Remote-Branches
  vollständig über die GitHub-Schnittstelle abgefragt; keine offenen PRs.
- PR #50 ist laut selbst gelesenen GitHub-Metadaten am 03.11.2026 um
  08:21 Uhr Europe/Vienna als `2d9ed90043628f0c3b2f948634b1bdcd769bc886`
  übernommen. Der Remotevergleich dieses Commits gegen `main` ist identisch.
  Geprüfter Ergebnis-Head bleibt `1c3f65f0d625c24d2cefe7c9c105c3e85ca7c56a`,
  damalige Basis `d97c95ddff7facf9d5fc766834855697478c49b6`.
  Kein Merge durch diesen Arbeitsschritt.
- Neuer Dokumentationsbranch `codex/free-form-methods-literature` ab `2d9ed90`.
  Der Shell-Aufruf `git fetch origin` scheiterte an der Verbindung zum
  konfigurierten Proxy; der Remoteabgleich erfolgte über den verfügbaren
  GitHub-Konnektor. Keine Umgehung von Proxy oder TLS.
- **Selbst gelesen/geprüft:** Arbeitsregeln, README, aktuelle Befund- und
  Methodenpläne; Original-Exposé, insbesondere PDF-Seiten 2–3; die in der
  [Literaturabwägung](free_form_method_assessment.md) benannten Primärtextabschnitte
  und versionsgebundenen Backendquellen. Persönliche PDF-Angaben werden nicht
  ins Repository übernommen. Kein vollständiger Zugriff auf andere Chats
  und keine Reproduktion der Literaturimplementierungen behauptet.
- **Übernommen geprüft:** Die dokumentierten früheren Archivnachrechnungen
  und CI-Ergebnisse bleiben Nachweise ihrer jeweiligen Arbeitsschritte.
  Hier keine erneute unabhängige numerische Nachrechnung. Das frühere lokale
  Auditverzeichnis `/workspace/audits/trajectory-manjaro-002/` ist in dieser
  Instanz nicht vorhanden; sein Fortbestand wird nicht vorausgesetzt.
- **Ausgearbeitet, nicht angenommen:** Vorwissensbilanz, neun Literaturquellen
  mit Zugriffsgrenzen, vier Optionen und ein bedingter Vorschlag für genau eine
  Grammatikablation. Das Verbot trigonometrischer Nachfahren erzwingt keine
  Ringdown-Form, ist aber ein zusätzlicher Prior; auch Verschlechterung ist
  durch verwandte GP-Befunde plausibel. Pause bleibt die begründete Alternative.
- **Arbeitsumfang:** Neues fachliches Abwägungsdokument; README und dieses
  bestehende Fortsetzungsdokument nachgeführt. Keine neue Projektchronik,
  keine zusätzlichen Agenten oder routinemäßige Reviewrunde. Kein Code,
  Test, Pin, Konfiguration oder eingefrorener Laufzeitplan verändert.
  Die vorhandene `.venv` und beschreibbare UV-Cacheumgebung sind für die
  schlanke Dokumentationsprüfung geprüft; Julia wurde nicht gestartet.
- **Selbst ausgeführte Prüfungen:** `uv run --locked python scripts/check_ci.py
  docs` erfolgreich für 49 Markdown-Dateien einschließlich des neuen
  Abwägungsdokuments; geprüft werden Format und lokale Dateiziele, keine
  externen HTTP-Ziele. `git diff --cached --check` ohne Befund. Der Diff
  umfasst ausschließlich die drei genannten Dokumente; die sechs zur Laufzeit
  gebundenen Pläne bleiben unverändert. Keine technische Testsuite wiederholt.
  Der gesicherte Head und der entfernte CI-Status werden im zugehörigen
  Literatur-PR festgehalten.
- **Nächster abgegrenzter Schritt:** Über den Vorschlag entscheiden; erst bei
  Annahme einen eigenen verbindlichen Methodenplan und danach einen technisch
  geprüften Pfad erarbeiten. Keine automatische Implementierung, zusätzliche
  Budgetstufe, Instrumentierung, Ersatzwahl oder Suchserie. Hauptversuche,
  wissenschaftliche Formelauswahl und früherer Budgetarchiv-Audit bleiben offen.

## Historisch: Originalarchiv der zweiten Suchbeobachtung geprüft

- Einstieg: ein sauberer Worktree auf `codex/trajectory-manjaro-handoff` bei
  `ff25de891b4266bcdf419ad6a7cba3ebe1808dfc`. Remote-Branches, Worktrees und
  offene PRs geprüft; PR #49 inzwischen als
  `d97c95ddff7facf9d5fc766834855697478c49b6` übernommen, keine offenen PRs.
  Neuer Ergebnisbranch `codex/trajectory-results-manjaro-002` auf dieser Basis.
- Originalarchiv `trajectory-manjaro-002.tar.gz`, SHA-256 selbst bestätigt:
  `99999285f6d7a8c50c54280cc36b526e704af01b07a1ccf95f2227e5e8597f55`.
  Ausführung auf Manjaro am festgelegten sauberen Commit
  `f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1`, Gesamtzeit 426,986 Sekunden.
  Sechs Zellen, drei bitgenaue Originalpaarvergleiche und Abschlussprüfung
  bestanden. Format 2, beide gebundenen Pläne und alle Budgets unverändert.
- **Selbst geprüft:** 175 Gesamtprüfsummen, 173 eingefrorene Dateianker,
  alle Zellmanifeste, 58 Quellen gegen Git, Originaleingaben, sechs native
  Options-/Pluginberichte, zwölf gespeicherte native Vorprüfungsfälle sowie
  Seeds und Haswell-/Threadnachweise. Alle sechs Zellen mit bestehenden
  Python-Verifikatoren erneut ausgewertet; sämtliche Diagnosen und
  Klassifikationen exakt reproduziert. Abschließend alle Dateien erneut geprüft.
- **Unabhängig nachgerechnet:** 54 exportierte Frontkandidaten auf beiden
  Rastern, 12.450 gespeicherte native Vorhersage-/MSE-Paare und sämtliche
  62.384 Rohpositionen. Eine erkannte Produktform zusätzlich analytisch
  geprüft. Keine neue Julia-Ausführung, Optimierung oder Suche im Audit.
  Originalartefakte blieben unverändert. Vollständige Implementierungs-CI
  als vorhandener Nachweis übernommen, nicht wiederholt.
- **Befund:** Kein erfolgreicher Frontkandidat und kein erfolgreiches
  verifiziertes beobachtetes Vorkommen. 58.629 Positionen verifiziert,
  157 numerisch ungeklärt, 3.598 nicht beurteilt. Eine erkannte
  Exponential-Kosinus-Form bei Seed 20261021 wächst und passt schlecht;
  Parameterstatus `not_assessed / not_decaying`. Keine Kausalaussage über
  Strukturentstehung, Verlust oder isolierte Optimiererprobleme.
- Der [Ergebnisbericht](search_trajectory_results_manjaro_002.md) hält
  Nenner, Quellen, Ereignisposition, Fehler, Aufwand und Aussagegrenzen fest.
  Die 15 früher dokumentierten Fehlerwerte der historischen 100/2-Auswahlen
  stimmen exakt überein; der vollständige freie Budgetarchiv-Audit bleibt offen.
- **Arbeitsstand:** Ergebnisbericht, README, dieses Arbeitsdokument und
  Bedienungsstatus werden gemeinsam dokumentiert. Kein wissenschaftlicher
  Code, Test, Pin, Konfiguration oder Laufzeitplan geändert. Head, sauberer
  Abschlusszustand und Dokumentations-CI werden im Ergebnis-PR festgehalten.
  Lokale Auditwerkzeuge und Auswertungen liegen unter
  `/workspace/audits/trajectory-manjaro-002/`; sie gehören nicht zum
  wissenschaftlichen Ausführungsstand.
- **Nächster abgegrenzter Schritt:** Literatur zu freier struktureller Suche,
  Konstantenanpassung und Komplexitäts-/Auswahlkriterien gegen diesen Befund
  und das Exposé abwägen. Recherche und neue Methodenentscheidung stehen aus.
  Keine Wiederholung der Serie oder zusätzliche Instrumentierung beschlossen.

## Historisch: Abgeglichener Stand und Manjaro-Übergabe vor Ausführung

- Beim Einstieg am 03.11.2026 Remote-Branches, offene PRs, lokalen Checkout und
  Worktrees geprüft: keine offenen PRs, ein sauberer Worktree auf
  `codex/trajectory-replay-verification` bei
  `27d10fe0148b18e76483ede9d5979c3afac40d89`. `origin/main` steht auf
  `f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1`, dem Merge von PR #48 am
  02.11.2026 um 21:22 Uhr Europe/Vienna. Beide besitzen denselben Git-Tree
  `2fb41c6a24731cc65ca1a231db6e26204314d87b`; der Dateivergleich ist ohne
  Unterschiede. Kein zweiter Implementierungsstand wurde begonnen.
- Die Übergabe zwischen den Unterhaltungen ist nachvollzogen:
  „2_Implementierungspipeline“ enthält die fünf zuletzt auslesbaren Austausche
  zum Originalteilarchiv, nativen Manjaro-Replay und zur Erstellung von PR #48.
  „3_Implementierungspipeline“ enthält die anschließende CI-Korrektur,
  den erfolgreichen Abschluss und den Exposé-Abgleich und wird fortgeführt.
  Die ältere ChatGPT-Gesamthistorie ließ sich aus der Cloud nicht vollständig
  durchblättern. Der aktuelle Übergang wurde zusätzlich gegen PR #47, PR #48
  und das Repository geprüft; kein vollständiger Audit aller früheren Chats.
- **Vollständige CI bestanden:**
  [Lauf 41437880627](https://github.com/craexxn/ringdown-sr/actions/runs/41437880627)
  am PR-Head `27d10fe`; 1.646 Python-Tests, 295 Julia-Prüfungen und sämtliche
  nativen und technischen Integrationen einschließlich Aus/an/aus sowie beider
  abschließenden Haswell-Suchen. Status, Schritte und Logs wurden am 02.11.
  selbst kontrolliert, Workflow- und Jobstatus am 03.11. erneut lesend bestätigt.
  Keine Testwiederholung beim Standabgleich. Der CI-Mergecommit
  `0e08b5c0b1fd2fcba056753f094ebbebc172f72c`, PR-Head und tatsächlicher Merge
  besitzen denselben Dateibaum. Das technische Joblimit von 45 Minuten ändert
  weder Suchbudgets noch wissenschaftliche Zeitgrenzen.
- **KI-basiertes Review übernommen:** Keine korrekturbedürftigen Befunde im
  beauftragten Umfang am Implementierungshead
  `2d9b028ac33ea7c9433eacf8140844cacdb206d0` gegen
  `41ccdd27aaa4ade56b509493089241d6695b9757`; 14 zusätzliche Prüfungen im
  übermittelten Review. Diese wurden hier nicht wiederholt. Der Nachtrag
  `27d10fe` änderte ausschließlich CI-Zeitlimit und Dokumentation.
  Kein weiteres Code-Nachreview ohne relevante Änderungen oder Fehlerhinweise.
- **Festgelegter Ausführungsstand:**
  `f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1`, neuer Ausgabeordner
  `results/trajectory-manjaro-002`. Die Fortsetzungsvereinbarung nach Merge und
  Standabgleich umfasst genau den bisherigen Sechszellenplan mit Format 2,
  keine Zusatzarme, Ersatzseeds oder automatische Wiederholung. Das alte
  `trajectory-manjaro-001` und sein Teilarchiv bleiben unverändert. Der
  [Startweg](search_trajectory.md) bindet den Commit und schützt bestehende
  Ergebnisse. Der Dokumentationsnachtrag muss für diesen Lauf nicht erst
  übernommen werden; er ändert den Ausführungsstand nicht.
- **Planbindung unverändert:**
  `search_trajectory_plan.md` hat SHA-256
  `fcc52e4099f197df676adc10c3163fc78e87d2a2d4661488b9ce929512da37f3`,
  `search_trajectory_replay_policy.md` hat SHA-256
  `e65a52ffd7292599e3d70957414977ede792bad6a64cebbe0e59c080ef241842`.
- **Aktuelle Dokumentationsarbeit:** Branch `codex/trajectory-manjaro-handoff`
  auf Basis `f3c0cb4`. README, dieses bestehende Arbeitsdokument und
  Bedienungsanleitung sind gemeinsam nachgeführt. Wissenschaftlicher Code,
  Tests, Konfigurationen, Pins und Laufzeitpläne bleiben unverändert.
  Lokal bestanden: Dokumentations-/Linkprüfung für 47 Markdown-Dateien,
  `git diff --check` und Syntaxprüfung aller drei Befehlsblöcke mit Bash und zsh.
  Ausschließlich die drei vorgesehenen Dokumente geändert; alle sechs
  Laufzeitpläne bytegleich zum Ausführungscommit. Keine wissenschaftlichen
  Befehle ausgeführt. Veröffentlichten Dokumentationshead, abschließenden
  Checkoutzustand und schlanken CI-Nachweis im zugehörigen PR bestimmen.
  Ältere Nachweise unten
  bleiben historisch erhalten; dortige Aussagen zu fehlender Julia-Umgebung,
  offenem Review oder ausstehender CI beschreiben ihren damaligen Stand.

### Exposé und nächste abgegrenzte Schritte

Das bereitgestellte Exposé vom 29.09.2026 wurde gelesen, insbesondere Seiten
2–3. Verbindlicher Forschungsanspruch bleibt eine freie Formelsuche und der
Einfluss der Länge separater Hintergrunddaten zur Kovarianzschätzung auf
Genauigkeit und Strukturstabilität. Die eigene Verlustfunktion hält die Matrix
während Suche und Konstantenanpassung fest; der klassische Fit mit bekannter
Ringdown-Form bleibt eine Referenz mit stärkerem Vorwissen. Ein zuvor diskutierter
Wechsel zu bekannten Formeln als Hauptpfad wurde nicht beschlossen oder umgesetzt.

Die Pilotkontrollen ersetzen die Hauptversuchsplanung nicht. Noch abzugleichen
sind die Exposé-Signalfälle 200 Hz/4 ms und 250 Hz/6 ms bei 25 ms Fensterdauer
gegenüber dem bisherigen Entwicklungsfall 250 Hz/8 ms bei 31,25 ms sowie
Hintergrundlängen und Datenabhängigkeiten, der Übergang vom allgemeinen
Matrixschätzer aus unabhängigen Fenstern zur vorgesehenen Hintergrundauswertung,
gleiche Rechenzeitbudgets und die endgültige Formelauswahl. Der relative L2-Fehler
ist im Exposé Hauptkriterium; Strukturstabilität wird zusätzlich ausgewertet.
Die strengeren Kurvengrenzen der eingefrorenen Entwicklungsdiagnosen bleiben
für diese Diagnosen unverändert. Hauptversuche und LIGO-Hanford-Auswertung
sind damit nicht freigegeben.

Reihenfolge: den vereinbarten Manjaro-Lauf am geprüften Stand einmal ausführen,
danach Originalartefakte einschließlich eines eventuellen Abbruchs archivieren,
Prüfsumme sichern und Ergebnisse prüfen. Erst anschließend gezielte
Weiterentwicklung und verwandte Literatur gegen Exposé und Befund abwägen;
kein automatischer Wechsel zu einem anderen SR-Verfahren. Der vollständige
Originalarchiv-Audit des früheren freien Budgetvergleichs bleibt gesondert offen.

## Historisch: Getrennte Beobachtungsreplays vor CI-Abschluss

- Nachtrag vom 02.11.2026 im vorhandenen Cloud-Checkout: Arbeitsstand sauber,
  ein Worktree; bestehenden Remote-Branch `codex/trajectory-replay-verification`
  auf `2d9b028ac33ea7c9433eacf8140844cacdb206d0` geladen. PR #48 ist der einzige
  offene PR; Basis unverändert `41ccdd27aaa4ade56b509493089241d6695b9757`.
  Der zuvor lokale Stand von PR #45 bleibt als eigener Branch erhalten.
- Übermitteltes KI-basiertes Review dieses Heads gegen diese Basis: keine
  korrekturbedürftigen Code- oder Methodenbefunde in allen 18 geänderten Dateien
  und relevanten Aufrufern. Vierzehn zusätzliche Gegenprüfungen berichtet,
  einschließlich rationaler MSE-Nachrechnung der fünf Fälle. Kein neuer
  Originalarchivaudit; Fallauszüge ersetzen den Herkunftsnachweis nicht.
- CI [41425713993](https://github.com/craexxn/ringdown-sr/actions/runs/41425713993)
  hier anhand Status, Schritten und Logs kontrolliert: sämtliche Schritte vor
  der letzten Haswell-Prüfung erfolgreich, insgesamt aber `cancelled`.
  Jobstart 10:04:05 UTC, Abbruch 10:35:15 UTC bei 30 Minuten Joblimit;
  die erste Haswell-Wiederholung war verifiziert, die zweite bereits gestartet.
  Ein vollständiger erfolgreicher Pflichtnachweis fehlt damit weiterhin.
- Begrenzte CI-Korrektur: ausschließlich Joblimit von 30 auf 45 Minuten erhöhen
  und den Status dokumentieren. Kein Prüfschritt, Suchbudget, wissenschaftliches
  Zeitlimit, Versionspin oder Laufzeitplan wird geändert. Der neue Head benötigt
  einen vollständig erfolgreichen CI-Lauf; das Review der Implementierung bleibt
  ausdrücklich an `2d9b028` gebunden. Kein weiterer Code-Review ohne relevante
  Änderung oder neuen Fehlerhinweis erforderlich.
- Nächster Schritt: gebündelten CI-Korrekturcommit im bestehenden PR sichern
  und den vollständigen Lauf einschließlich zweier letzter Haswell-Suchen
  kontrollieren. Aktuellen Head und CI-Nachweis im PR bestimmen. Nicht mergen;
  ein frischer wissenschaftlicher Sechszellenlauf bleibt gesondert zu entscheiden.
- Lokal für diesen CI-Nachtrag geprüft: 45 CI-Auswahltests, Dokumentations-
  und Linkprüfung für 47 Markdown-Dateien sowie `git diff --check` bestanden.
  Die beiden Planprüfsummen stimmen unverändert. Der wissenschaftliche Code,
  Tests, Julia-Dateien und Pins bleiben gegenüber dem Reviewhead unverändert.

Die folgenden Implementierungsnachweise beschreiben den zuvor geprüften Stand:

- Basis: `41ccdd27aaa4ade56b509493089241d6695b9757`, Dateibaum
  `04ade5ae24d3823d92ffaf7a595d58671203f8d6`; beim Einstieg keine offenen PRs.
  Arbeitsbranch: `codex/trajectory-replay-verification`.
  Eigener baumgleicher lokaler Checkout; ältere Arbeitsstände bleiben erhalten.
  Die lokale Snapshotgeschichte wird nicht auf die Remote-Geschichte gepusht.
- PR #47 bestand am Head `4798315586b873e6c9e5d561cc8a8b5f532a8e09`
  die [vollständige CI](https://github.com/craexxn/ringdown-sr/actions/runs/41410153617):
  1.572 Python-Tests und 295 Julia-Prüfungen einschließlich nativer
  Beobachterintegration. Der Mergebaum stimmt überein. Das übermittelte
  KI-basierte Implementierungsreview fand im geprüften Umfang keine Befunde.
- Originalteilarchiv `trajectory-manjaro-001-incomplete.tar.gz`, SHA-256
  `08676ddc21c1820110ae425a68de3c5b954c8bef2022b816ca274c307041c873`,
  unabhängig geprüft: 67 Workerprüfsummen, 57 Quellhashes, 56 eingefrorene
  Artefakthashes; alle 97 extrahierten Dateien unverändert.
  Zellen 1/2 und ihr Originalpaarvergleich bestehen; Zelle 3 scheitert
  bei fünf Zwischenmitgliedern, Zellen 4–6 bleiben nicht ausgeführt
  (`planned`). Die acht Endfrontkandidaten von Zelle 3 bestehen die
  bisherigen strengen Replays.
- Der übermittelte native Bericht `trajectory-loss-replay-001.json`
  bindet das korrigierte separate Skript
  `fa6eaa23de632fd4fa0e1fb84159e7996af52ed69cec93d2ee4ca156c3b99a61`.
  Alle fünf Datensätze, 14 konsumierte Hashes und die MSE aus jeweils
  128 nativen Vorhersagebits sind unabhängig nachgerechnet.
  Zwei Fälle zeigen Julia-/NumPy-Abweichungen (auf Manjaro maximal 2,2315 %);
  drei gespeicherte Verluste passen zu keinem aktuellen Replay.
  Die Ursache dieser drei Unterschiede bleibt offen; keine konkrete
  Vereinfachung ist anhand der Aufnahmen belegt. Details in
  [PR #47](https://github.com/craexxn/ringdown-sr/pull/47).
- Die [gebundene Ergänzung](search_trajectory_replay_policy.md) konkretisiert
  harte Fehler, numerisch ungeklärte Mitglieder, positive Gates und
  Serienvollständigkeit. Der ursprüngliche Plan bleibt unverändert.
  Die Umsetzung ergänzt getrennte native Replays nach dem Fit, genaue
  Dateibindungen und sichtbare Nenner; Suche und Originalauswahl bleiben gleich.
- Die fünf Originalfälle werden als kompakte Testdaten mit Herkunft und
  Float64-Bits aufgenommen. Analytische Kontrollen und Manipulationsfälle
  prüfen positive Gates und die weiterhin harten Integritätsfehler.
  Vollständige technische CI und gezieltes KI-basiertes Review der
  Status-/Abschlussregeln sind am fertigen PR-Head nachzuweisen.
- Kein neuer wissenschaftlicher Suchlauf und keine Wiederaufnahme.
  Der ursprüngliche Teilstand bleibt `incomplete / failed`.
  Ein frischer Sechszellenlauf ist erst nach bestandenem Prüfstand, Merge
  und gesonderter Freigabe vorgesehen.
- Lokal Python 3.12.14 verfügbar; Julia hier nicht vorhanden. Native
  Nachweise der Korrektur werden über die technische CI geführt.
- Gebündelte lokale Prüfung: 226 Tests bestanden (89 Kern-, 28 Worker-,
  43 Treiber-, 21 Originalfall- und 45 CI-Auswahltests), Ruff und Formatprüfung
  bestanden; alle 47 Markdown-Dateien mit gültigen lokalen Dateizielen.
  Die gezielte KI-basierte Codeprüfung der Status- und Abschlussregeln fand
  bisher keine korrekturbedürftigen Befunde; Bindung an den veröffentlichten
  Head und native CI-Nachweise folgen im PR. Die Gesamtsuite wird in der
  Linux-CI ausgeführt; keine wiederholte vollständige Windows-Suite.

Die freie Budgetserie bleibt als abgeschlossen übermittelt; ihr
[Befund](free_optimizer_budget_results_manjaro_001.md) und die Grenzen des
fehlenden Originalarchivaudits bleiben erhalten. Die folgenden Abschnitte
sind historische Arbeits- und Prüfnachweise.

## Historisch: Umsetzung der ursprünglichen Suchbeobachtung


- PR #46 ist übernommen. Remote-`main` beim Einstieg:
  `930e3d064d68233368a8c3decfc3115fe62a42c5`, Dateibaum
  `393acb29553c33b0b2a41588ac78f27bba7a5612`; keine offenen PRs.
  Lokaler sauberer Snapshot ist vollständig baumgleich. Seine lokale
  Commitgeschichte ist weiterhin keine Nachbildung der Remote-Geschichte.
- Arbeitsbranch: `codex/search-trajectory-control`.
  Vorherige Checkouts und Arbeitsstände bleiben erhalten.
- Angenommen am 02.11.2026: sechs Zellen, maximal 60 Minuten insgesamt,
  600 Sekunden je Worker und 256 MiB je beobachteter Zelle.
  Der [eingefrorene Plan](search_trajectory_plan.md) liegt unter
  `fbfbc3781f80968f978b388e32bfc8375d6f8725`, SHA-256
  `fcc52e4099f197df676adc10c3163fc78e87d2a2d4661488b9ce929512da37f3`.
  Er übernimmt die korrigierte Interpretationsregel aus PR #46.
- Implementiert: passiver nativer Beobachter, getrennter Worker und Serientreiber,
  Prüfung und nachgelagerte Auswertung der Aufnahmen sowie gezielte technische
  Gegenfälle. Die bisherigen Suchpfade und vier eingefrorenen Pläne bleiben
  unverändert. Die neue Planbindung ist in der vollen CI erfasst.
  [Bedienung und Artefakte](search_trajectory.md) beschreiben die spätere
  Manjaro-Ausführung und die getrennten Aufwands-/Beobachtungsnachweise.
- Gezielt lokal bestanden: 68 Auswertungstests, 29 Treibertests,
  elf Worker-Grenztests und 44 Tests der CI-Zuordnung. Ruff und
  Formatprüfung über den gesamten Stand und Dokumentationsprüfung für
  46 Markdown-Dateien bestanden.
- Vollständiger erster Windows-Lauf (`a460701`): 1.451 bestanden, 105 fehlgeschlagen,
  einer übersprungen. Sämtliche Fehler betreffen unveränderte Prüfpfade:
  100 fehlende Unix-Signal-/Timerfunktionen, fünf fehlende Symlink-Rechte.
  Alle 105 Fehler im unveränderten Ausgangsbaum separat reproduziert
  (7 bestanden, dieselben 105 fehlgeschlagen). Den verbindlichen Linux-CI-Nachweis
  hält [PR #47](https://github.com/craexxn/ringdown-sr/pull/47) mit exaktem Bezugsstand fest. Die Windows-Suite ist damit
  ausdrücklich nicht als vollständig bestanden ausgewiesen.
- Lokale Python-Ausführung mit 3.12.14 ist verfügbar. Julia ist lokal derzeit
  nicht auffindbar; native Options-, Zustands- und aus/an/aus-Prüfungen müssen
  deshalb über die vollständige technische CI nachgewiesen werden.
- Die erste CI zu `a460701` bestand 1.557 Python-Tests und die Julia-Umgebungs-/Startprüfungen.
  Die neue Optionsprüfung wies die vom Backend vorangestellte Beobachterposition
  zurück. Die korrigierte Übergabe liefert nun die drei unveränderten Basisplugins
  ausdrücklich vor dem Beobachter; die absolute Reihenfolgeprüfung bleibt bestehen.
  Außerdem ist der native Modulpfad einer technischen Fixture korrigiert und die
  getrennte Verlaufsauswertung auch für Baumformen ergänzt. Der abschließende
  native Nachweis ist im PR zu prüfen.
- Keine wissenschaftliche Beobachtungsserie ausgeführt. Implementierung,
  Prüfnachweise und verbleibende Punkte werden im zugehörigen PR mit exaktem
  Head dokumentiert; erst danach einmalige Manjaro-Ausführung.

Die folgenden Abschnitte halten die vorherigen Beschluss- und Prüfnachweise fest.

## Historisch: Budgetergebnis und begrenzter Beobachtungsentwurf

- Remote-`main` beim Einstieg:
  `8bdc8dbc498be6e8527fa2a857293bf74b42f81f`, PR #45 übernommen;
  keine offenen PRs vor diesem Dokumentationsauftrag.
- Geprüfter PR-Head `4e29ae44d8e481eb96af128f06e8db7666fff934` und Merge
  haben denselben Git-Tree `ab0e06f36d4cdb2ccf5c27ec53e9bc8b5ebbe099`.
  Die [vollständige CI](https://github.com/craexxn/ringdown-sr/actions/runs/41190324974)
  ist erfolgreich; Run- und Jobstatus mit sämtlichen technischen Schritten
  hier lesend bestätigt. Der PR dokumentiert 1463 Python-Tests und den
  Abschluss des übermittelten gezielten KI-basierten Nachreviews ohne
  verbleibende Befunde zur Widerrufs-/Abbruchsicherung.
  Keine neue Wiederholung dieser Tests oder dieses Reviews.
- Auf Manjaro sind sechs Zellen `completed` und Abschlussverifikation
  `passed` übermittelt. Archivname `free-budget-manjaro-001.tar.gz`,
  übermittelte SHA-256
  `77fb34ff6ee139c1f2e0fbbb6acd81d7c1623cd6e8090056f641961e887ad33f`.
  Das Originalarchiv lag diesem Auswertungsschritt nicht vor:
  keine unabhängig bestätigte Archivprüfsumme, Manifestprüfung oder
  archivierte Git-/Backendherkunft behaupten.
- Eigene Nachrechnung der sechs geposteten Anzeigeformeln:
  128 Trainings- und 889 Diagnosepunkte, alle 30 MSE/RMS/Max-Werte bis
  auf Float64-Rundung reproduziert. Vollständige Zahlen, Formeln,
  Aufwandsangaben und Prüfgrenzen stehen ausschließlich im Ergebnisdokument.
- Ergebnis: kleinere MSE/RMS unter 100/2 bei 3/3 Seeds, aber
  `C20=C100=0`, auch keine kurvenguten ungewählten Kandidaten.
  Der größere Maximalfehler bei Seed 20261021 bleibt sichtbar.
  Keine allgemeine Überlegenheit, keine nachträgliche Auswahl und kein
  Nachweis eines einzelnen Struktur-/Optimiererengpasses.
- Arbeitsbranch: `codex/free-budget-results-and-trajectory-plan`,
  Basis der oben genannte Merge. Genau vier Dokumentationsdateien:
  Ergebnis, neuer Entwurf, README und dieses Fortsetzungsdokument.
  Den veröffentlichten Head über den zugehörigen PR bestimmen.
- Lokaler Einstieg: ältere Windows-Checkouts und Worktrees geprüft;
  ein älterer Arbeitsbranch enthält noch unvollständige Änderungen.
  Diese bleiben unangetastet. Für diesen Auftrag separater Dateibaum
  mit allen 144 Repositorydateien aufgebaut und gegen den tatsächlichen
  Git-Tree des aktuellen `main` vollständig abgeglichen.
  Die lokale Snapshot-Historie ist keine Nachbildung der Remote-Historie;
  der veröffentlichte Dokumentationscommit basiert direkt auf `8bdc8db`.
- Beim ersten Dokumentationsabschluss war die lokale Ausführungsumgebung
  nicht mehr verfügbar. Die [schlanke CI am Head `aa04a9c`](https://github.com/craexxn/ringdown-sr/actions/runs/41399099106)
  bestand mit 44 Markdown-Dateien und korrekt ausgelassenen technischen
  Schritten; der getestete Mergebaum entspricht dem Head.
  Beim Einstieg zur Reviewkorrektur ist die Windows-Ausführungsumgebung
  wieder verfügbar. Frühere lokale Arbeitsstände bleiben erhalten.
- Neuer Methodenentwurf: sechs frische 100/2-Läufe aus/an gepaart,
  nur feste zurückgegebene Populationen und globale Hall of Fame beobachten.
  Backend-Hook quellengeprüft; keine vollständige Vorschlags-/Verwerfungshistorie.
  Das übermittelte Methodenreview bestätigt auch die Plugin-Durchleitung
  im PySR-2.6.0-Quellcode. Die tatsächliche technische Nichtbeeinflussung
  muss vor Ausführung nachgewiesen werden; alle vorgeschlagenen Grenzen
  sind weiterhin ausdrücklich anzunehmen.
- Übermitteltes KI-basiertes Methodenreview zu PR #46:
  Head `aa04a9c49de331c878669907b1bc6a246918d704`,
  Basis `8bdc8dbc498be6e8527fa2a857293bf74b42f81f`.
  Vier Dokumentationsänderungen, Arbeitsregeln und relevante Backendquellen
  geprüft; ein P2 zur Interpretation fehlender Frontzugehörigkeit, keine
  weiteren korrekturbedürftigen Befunde berichtet. Unabhängige Nachrechnung
  der sechs Anzeigeformeln, 30 Fehlerwerte und des Filtergegenfalls sowie
  CI-/Quellenprüfungen sind als Reviewnachweise übermittelt.
  Kein Audit des weiterhin fehlenden neuen Originalarchivs.
- Korrektur: Frontzugehörigkeit und zeitliches Auftreten werden getrennt.
  Späteres Fehlen verlangt entsprechende vergleichbare Populations- oder
  Hall-of-Fame-Aufnahmen. Backend-Filterregel selbst quellengeprüft und
  synthetischen Gegenfall gezielt nachgerechnet; keine neue Suche, kein
  Fit oder nativer Beobachtertest. Details stehen in Abschnitt 7 des Entwurfs.
  Der vollständige Korrekturcommit und seine Prüfnachweise werden im PR
  festgehalten. Keine erneute vollständige Methodenrunde.

Nächster abgegrenzter Schritt: über den korrigierten Entwurf entscheiden,
einschließlich sechs Zellen und der Grenzen von 60 Minuten insgesamt,
600 Sekunden je Worker und 256 MiB Beobachtungsdateien je beobachteter Zelle.
Annahme und anschließende Umsetzung oder Eingrenzung/Pause bleiben offen.
Noch keine Beobachterimplementierung oder neue wissenschaftliche Serie;
kein eigenständiger Merge.

Die vier eingefrorenen Laufzeitpläne, Quellen, Pins und Originalergebnisse
bleiben unverändert. Der neue Entwurf wird von keinem Laufzeitpfad konsumiert
und benötigt derzeit nur den schlanken Dokumentations-CI-Pfad.
Die Prüfungen dieses Dokumentationsheads werden im PR mit exaktem Commit
festgehalten; kein zusätzlicher Statuscommit nur für den CI-Abschluss.

## Historisch: Budgetvergleich vor abschließendem CI-/Reviewabschluss


### Widerrufssicherung nach gezieltem Nachreview zu PR #45 (31.10.2026)

Erneuter Einstieg am 31.10.2026: sauberer Checkout und Remote-Head
`b16ab10a216804500728a18bd913a5c243db2036`, weiterhin
`codex/free-optimizer-budget`, ein Worktree. PR #45 ist offen und der einzige
offene PR; aktuelles `main` und PR-Basis unverändert
`722437ea4e3662bed4ef61bd363503777e44d2fe`. Keine parallelen Änderungen
übernommen. Gepinnter Python 3.12.14 und die tatsächlich vorhandene
Python-Bibliothek erneut bestätigt; gespeicherter Cloud-Startweg beibehalten.

- **Übermitteltes KI-basiertes Nachreview:** Head `b16ab10` wie oben,
  gezielte Basis `592a5fbca6ca0f3e8414183c227c7585ca7ea943`, PR-Basis wie oben.
  Alle fünf Korrekturdateien, Regeln und relevante unveränderte Aufrufer geprüft;
  31 gezielte Tests und zwei zusätzliche Fehlergegenprüfungen berichtet.
  P2 im geprüften Umfang behoben; verbleibender P1: Ein Fehler bereits beim
  Entfernen von `report.json` verhindert weitere Widerrufe und den gesperrten
  Ersatzbericht. Dann kann das vollständig positive Paket zurückbleiben.
  Kein neuer nativer Fachtest, Archivaudit oder wissenschaftlicher Suchlauf.
- **Vorherigen CI-Nachweis hier selbst verifiziert:** Jobstatus und Logs der
  vollständigen [CI 41122598284](https://github.com/craexxn/ringdown-sr/actions/runs/41122598284)
  erfolgreich; 1.451 Python-Tests in 113,41 Sekunden, native Umgebung/Starttests
  und sämtliche Integrationen einschließlich dreier technischer 20–100–20-Worker.
  Dieser Nachweis gehört zu `b16ab10`, nicht zur nachfolgenden Korrektur.
  Zusätzlich bestanden am damaligen Head lokal alle 1.451 Python-Tests in
  94,98 Sekunden; im PR dokumentiert, hier keine erneute Ausführung dieses Stands.
- **Selbst reproduziert:** beide Reviewfälle am unveränderten Head mit
  simulierten Workern: Fehler direkt nach positivem Berichtsrename und danach
  einmaliger `OSError` beziehungsweise `KeyboardInterrupt` beim Entfernen des
  Berichts. Beide Gegenfälle lassen dort erwartungswidrig das positive Paket
  zurück. Die Reproduktionen wurden vor der Korrektur ausgeführt.
- **Implementiert:** jeden Widerruf getrennt absichern, Fehler mit Operation
  im Abbruchbericht erhalten und sämtliche übrigen Schritte weiter versuchen.
  Gesamtmanifest zuerst entfernen; nur fehlgeschlagene Löschungen einmal
  zusätzlich versuchen. Danach gesperrte Berichtsausgabe und bei deren Fehler
  separater JSON-Versuch; auch dessen letzter Löschfallback ist abgesichert.
  Temporäre Handler und eine vorübergehende Signalmaske stellen weitere SIGINT-/SIGTERM-
  Unterbrechungen während der Sicherung zurück und werden danach wiederhergestellt.
  Dies wiederholt keine Suche oder Verifikation. Zeitlimit, Abschlussanker und
  eingefrorener Methodenplan unverändert.
- **Lokal geprüft:** 175 gezielte Tests bestanden (132 Kontroll- und 43
  CI-Auswahlfälle), darunter zwölf neue Fälle: sechs einmalige Löschfehler nach
  Veröffentlichung, vier wiederholte Lösch-/Persistenz-/Fallbackfehler sowie
  echte Prozesssignale und Python-Signalauslieferung bei wiederholtem Abbruch.
  Sperren, Erhalt der Zellartefakte und Wiederherstellung des Signalzustands
  geprüft. Zusätzlich bestanden alle 1.463 Python-Tests in 92,91 Sekunden;
  dieser vollständige Lauf prüft die Wechselwirkungen mit anderen Tests.
  Ruff, Formatprüfung für 122 Pythondateien, Dokumentations-/Linkprüfung
  für 42 Markdown-Dateien und Diffprüfung bestanden; alle vier Planprüfsummen
  unverändert.
- **Fortsetzbarer Stand:** neuer zusammenhängender Korrekturcommit im bestehenden
  Branch mit Treiber, Gegenfällen, Bedienung, README und dieser Datei. Head nach
  Commit/Push über `git rev-parse HEAD` und PR #45 bestimmen; lokale Änderungen
  vor Fortsetzung erneut prüfen. Der aktuelle CI-Nachweis gehört zum jeweiligen
  Head im PR; ein bestandenes Nachreview dieser Korrektur wird nicht behauptet.

Damals nächster abgegrenzter Schritt: vollständige technische CI des neuen Korrekturheads
prüfen und gezieltes KI-basiertes Nachreview ausschließlich der Widerrufs- und
Abbruchsicherung. Nicht eigenständig mergen; keine wissenschaftliche Cloud-Serie.

### Historisch: Korrektur nach erstem Implementierungsreview zu PR #45

Erneuter Einstieg am 30.10.2026: sauberer Checkout auf
`592a5fbca6ca0f3e8414183c227c7585ca7ea943`, Branch
`codex/free-optimizer-budget`, ein Worktree, lokaler/Remote-Head identisch.
PR #45 ist der einzige offene PR; Basis und aktuelles `main` weiterhin
`722437ea4e3662bed4ef61bd363503777e44d2fe`. Keine parallele Fortsetzung
übernommen. Der folgende übermittelte Befund bezieht sich auf diesen Head
und diese Basis, nicht auf den nun geänderten Stand.

- **Übermitteltes KI-basiertes Review:** alle 18 PR-Dateien und relevante
  unveränderte Abhängigkeiten geprüft; 135 gezielte Tests und vier separate
  Fehlergegenprüfungen ausgeführt. CI [41109750849](https://github.com/craexxn/ringdown-sr/actions/runs/41109750849)
  mit 1.423 Python-Tests und nativen Integrationen über GitHub verifiziert.
  Temporärer CI-Mergecommit `a3ff9cf29d9a2049f108b96f6d374958ce9ae423`
  hat denselben Dateibaum wie der geprüfte PR-Head. Keine neuen nativen Tests,
  wissenschaftlichen Suchen/Fits oder Archivaudits im Review berichtet.
- **P1:** Positive Berichte konnten nach einer unterbrochenen Zusammenfassung,
  fehlgeschlagenem Gesamtmanifest oder spät konsistent neugehashten Zellartefakten
  zurückbleiben. **P2:** Während letzter Prüfoperationen überschrittene
  Gesamtwandzeit konnte trotzdem zur Freigabe führen. Die übrige Methodentreue
  wurde im geprüften Umfang bestätigt. Gezieltes Nachreview dieser zwei
  Korrekturen erforderlich; keine vollständige zusätzliche Reviewrunde.
- **Hier selbst reproduziert:** vier neue Gegenfälle am tatsächlichen Treiber
  mit simulierten Workern schlagen am unveränderten Reviewstand erwartungsgemäß
  fehl: Tastaturabbruch der letzten Zusammenfassung, Schreibfehler des
  Gesamtmanifests, späte Änderung samt Zellneuhashung und Zeitüberschreitung
  während des letzten Verzeichnisdurchlaufs. Keine Suche oder Optimierung.
- **Korrektur implementiert:** gesamte Abschlussphase im Fehlerpfad; Berichte
  und Manifest zunächst vorbereiten, alle konsumierten Bytes auch bei der
  Manifestbildung gegen die ursprünglichen Anker prüfen. Weitere Paketdateien
  beim ersten Abschlusslesen einfrieren; Zellmanifeste im Gesamtmanifest erhalten.
  Positiver `report.json` als letzter atomarer Veröffentlichungsschritt nach
  erneuter Integritäts-/Zeitprüfung. Bei Fehler oder Unterbrechung werden
  positive Abschlussdateien entfernt, Aggregate gesperrt und Einzelartefakte
  erhalten; fehlgeschlagene Abbruchsicherung erzeugt keinen Ersatz-Erfolg.
- **Zeitbegrenzung implementiert:** unverändert 3.600 Sekunden; Prüfungen
  vor/nach Dateioperationen und während blockweiser Hashbildung, zusätzlich
  POSIX-Wandzeittimer für blockierende Elternprozessarbeit. Abschließende
  Zeitprüfung auch nach dem Berichtsrename; Zeitüberschreitung widerruft die
  Freigabe. Fremden aktiven Timer ablehnen, eigenen Timer/Signalzustand
  anschließend wiederherstellen. Nach einem Abbruch nur Teilstandssicherung.
- **Lokal geprüft:** 163 gezielte Tests bestanden (120 Kontroll- und 43
  CI-Auswahlfälle), darunter 28 neue Gegenfälle: die vier Reproduktionen,
  Fehler vor/nach allen drei Veröffentlichungen, Zeitüberschreitungen in acht
  Abschlussphasen, echter Timerabbruch blockierender Elternprozessarbeit und
  Erhalt eines fremden Timers. Zusätzliche Fälle prüfen spätere Zelländerung
  samt konsistenter Zell-/Gesamtneuhashung und wiederholtes Scheitern der
  Abbruchzusammenfassung. Ruff, Formatprüfung für 122 Pythondateien,
  Dokumentations-/Linkprüfung für 42 Markdown-Dateien und Diffprüfung bestanden.
  Alle vier eingefrorenen
  Planprüfsummen unverändert; keine Pins, Budgets, Seeds oder Kriterien geändert.
- **Fortsetzbarer Stand:** Treiber, Gegenfälle, Bedienungsdokumentation, README
  und dieses Dokument bilden einen zusammenhängenden Korrekturcommit im
  bestehenden Branch. Den gesicherten Head nach Commit/Push mit
  `git rev-parse HEAD` und PR #45 bestimmen;
  vor Fortsetzung lokale Änderungen erneut prüfen. Der grüne CI-Nachweis
  `41109750849` gehört ausschließlich zum vorherigen Head, nicht zur Korrektur.

Damals nächster abgegrenzter Schritt: vollständige technische CI am Korrekturhead im
bestehenden PR #45 prüfen und ein gezieltes
Nachreview der Finalisierung/Zeitbegrenzung durchführen lassen. Nicht mergen;
keine wissenschaftliche Cloud-Serie. Erst nach diesen Prüfungen folgt der
gesonderte Manjaro-Start am freigegebenen Stand.

### Historischer Implementierungs- und Prüfnachweis vor dem Review

Der korrigierte Beschluss aus PR #44 ist ausdrücklich angenommen. PR #44 wurde
nach Prüfung des Heads `8fe947cfad5787609962955b4ce2d2fbbf113c39` und der grünen
Dokumentations-CI [41105409445](https://github.com/craexxn/ringdown-sr/actions/runs/41105409445)
als `722437ea4e3662bed4ef61bd363503777e44d2fe` gemergt. Sauberer Einstieg, ein
Worktree und keine parallele Fortsetzung; eigener Implementierungsbranch
`codex/free-optimizer-budget` ab diesem Merge.

- **Beschlossen und eingefroren:** [Methodenplan](free_optimizer_budget_plan.md),
  Commit `bb4862034b49b89dcc37d8341814e42aa02989c5`, SHA-256
  `b63e66461e3a380f9e8ca5c127e8c5f99cd2a0d574be7be1603f18f56292907b`.
  Sechs freie Suchen, beide Schalter an, 20/2 gegen 100/2, drei bekannte Seeds,
  feste Reihenfolge, je 200 Suchiterationen und 60 Minuten einschließlich
  Vorprüfungen/Abschlussverifikation. Originalauswahl, Grenzen, korrigierte
  Entscheidungsregeln und vollständige Berichtssperre sind verbindlich.
- **Implementiert:** `free_optimizer_budget.py`, eigener nativer Guard
  `FreeOptimizerBudget.jl`, isolierter Worker, Treiber und Options-/Referenzprüfer.
  Bestehender numerischer Callback und allgemeine Suchdefaults erhalten.
  Sämtliche Optionen/Plugins/Seeds einschließlich erster Zelle werden absolut
  geprüft, dann gegen echte Prototypen verglichen. Optimierertoleranzen und
  Callback bleiben unverändert; Newton- und BFGS-Pfade werden nicht ersetzt.
- Alle Kandidaten, Reihenfolge und Originalindex bleiben erhalten; Vorhersagen,
  Residuen und MSE jedes Kandidaten werden geprüft. Getrennte Such-/physikalische
  Diagnosen und bestehende Replaygates; gleiche erfolgreiche Originalauswahl
  für unterstützte Rekonstruktion erforderlich. `physical_identification` bleibt
  `not_assessed`; der Achtelraster-Blindfleck bleibt dokumentiert.
- Quellen, Pins, Plan, Daten und konsumierte Kopien werden vor Verbrauch und
  abschließend gegen eingefrorene Bytes geprüft. SIGTERM, Tastaturabbruch,
  Zeitlimit und Workerfehler erhalten Teilstände und stoppen die Prozessgruppe.
  Gruppen, Paardifferenzen und Erfolgswechsel bleiben bis zu sechs vollständigen
  Zellen und bestandener Abschlussprüfung gesperrt.
- **Hier ausgeführt:** Python-/Julia-Umgebungscheck einschließlich PythonCall-
  Bindung bestanden: Python 3.12.14, Julia 1.13.1, PySR 2.6.0,
  SymbolicRegression 2.5.1. Pythonbibliothek aus dem Projektinterpreter ermittelt
  und vorhanden; Cachepfade beschreibbar. Gespeicherte lokale Startdatei genutzt,
  Proxy/TLS unverändert, Haswell nur für die Kontrollbefehle.
- Sechs echte native Optionsobjekte ohne Fit/Suche geprüft; sechs feste
  250-/4346-/33018-Hz-Referenzbäume, Einheiten- und falsche Seed-/Budgetfälle
  unter beiden Budgets bestanden. Quellenabgleich der gepinnten Backendaufrufer
  bestätigt dieselben Optimierereinstellungen auch im Ein-Konstanten-Newtonpfad.
- **Technische Integration bestanden:** drei frische Worker auf einem separaten
  Achtpunkt-Signal `y=1+t`, je zwei Suchiterationen, 20–100–20; ursprüngliche
  20er-Fronten exakt identisch. Tatsächlich geladene BLAS-Pools vor/nach jedem
  Fit mit Haswell und Limit 1 geprüft. Lokale Artefakte:
  `results/free-budget-technical-dev-002/`. Dies ist kein wissenschaftlicher
  Kontrolllauf und keine Leistungsvalidierung.
- Erster technischer Anlauf unter `results/free-budget-technical-dev-001/`
  bleibt erhalten: nach erfolgreich exportiertem ersten Worker lehnte der
  neue Python-Verifier das zusätzliche bestehende RNG-Statusfeld fälschlich ab.
  Vergleich auf die beiden absolut geprüften Seedfelder korrigiert; vollständige
  RNG-Aufnahme bleibt erhalten, kein vollständiger RNG-Checkpoint behauptet.
- Am Implementierungscheckpoint `a92c77d8e1c74d1bafd5232490c712378d7f0acc`
  bestanden alle 1.419 Python-Tests in 90,61 Sekunden; zuvor 88 neue fokussierte
  Fälle und zusammen mit CI-Auswahlfällen 131 Tests. Ruff, Format- und
  Dokumentationsprüfung bestanden.
- Anschließend den Abgleich der Laufzeitkopien vor dem ersten Vorprüfungsstart
  ergänzt: bereits beim Kopieren an ursprüngliche Quellhashes binden und vor
  jedem Verbrauch alle Laufzeitdateien erneut gegen diese Anker prüfen.
  Vier neue Gegenfälle weisen die Ablehnung veränderter Kopien vor jedem
  Codeaufruf nach. Danach 135 gezielte Tests bestanden (92 neue Kontrollfälle
  und 43 CI-Auswahlfälle); die vollständige CI prüft den abschließenden Stand. Gegenfälle umfassen die
  Reviewregel, erste/spätere Zellfehler, Profile/Plugins/Optionen, Originalindex,
  Residuen/MSE, späte konsistent neugehashte Manipulation, Abbruch und Prozess-
  gruppenstopp. Alle vier Laufzeitpläne sind der vollständigen CI zugeordnet.
- Zusätzliche Quellprüfung gesichert in
  `9c64051201ab5b1cd80c70cee55be58012a3a590`. [PR #45](https://github.com/craexxn/ringdown-sr/pull/45)
  ist geöffnet, Vergleichsbasis `722437ea4e3662bed4ef61bd363503777e44d2fe`.
  Aktuellen vollständigen CI-Nachweis samt Head im PR prüfen; der PR-Text hält
  das abschließende Prüfergebnis fest. [Bedienung](free_optimizer_budget.md)
  ergänzt. Nach Push des Dokumentationsabschlusses ist der Checkout sauber;
  vor Fortsetzung Commit und lokale Änderungen mit `git status --short --branch`
  und `git rev-parse HEAD` erneut bestimmen.

Damals nächster abgegrenzter Schritt: vollständige Integrations-CI am finalen PR-Head
prüfen und den Nachweis im PR ergänzen; anschließend kann PR #45 übernommen
werden. Nicht selbstständig mergen. Die sechs wissenschaftlichen Suchen werden im Rahmen
aller technischen Prüfungen nicht in der Cloud gestartet; einmalige Manjaro-
Ausführung erst am technisch geprüften Stand. Kein Produktionsprofil und keine
Übertragbarkeits-/Gewichtungsstudie freigegeben.

## Historisch: freier Budgetvergleich nach übermitteltem Methodenreview

Der [überarbeitete Entwurf](free_optimizer_budget_plan_draft.md) liegt weiterhin
im bestehenden Ergebnisbranch `codex/constant-diagnostic-results` und
[PR #44](https://github.com/craexxn/ringdown-sr/pull/44). Das gemeinsame KI-basierte
Methodenreview ist übermittelt, sein Beschlussvorschlag noch nicht angenommen.

- Einstieg erneut geprüft: sauberer Checkout, ein Worktree, lokaler und aktueller
  Remote-Head `7ee5f38067ba0b2161ab3ddaf9775d6aa4fc1fbd`; PR #44 weiterhin
  offen, keine weiteren offenen PRs. `main` unverändert auf
  `0a70f19e16e173aedf2e071a5f5b09d045ecbf69`. Ergebnisanker `ad32d4b`;
  den nach dieser Korrektur aktuellen Head mit `git rev-parse HEAD` oder im PR
  bestimmen. Historische Remote-Branches wurden geladen, nicht übernommen.
- Übermitteltes Review: geprüfter Head `7ee5f38`, vollständige Vergleichsbasis
  und Ergebnisanker wie oben; beide PR-Commits mit allen fünf Dokumentations-
  dateien, Grundlagen und relevanten unveränderten Aufrufern/Backendquellen.
  Quellen-/Dokumentprüfung und `git diff --check` berichtet; keine numerische
  Ausführung. Archive fehlten dort, daher keine erneute unabhängige Bestätigung
  der Archivhashes oder Zahlen. Details im Entwurf, Abschnitt 9.
- Ein Befund P2: Gute 100/2-Kurven allein belegen keinen Vergleichsvorteil.
  Die Entscheidungstabelle trennt nun vollständig `C100 > C20`, Gleichstand
  ohne/mit Erfolg und `C100 < C20`; unvollständige oder abschließend nicht
  verifizierte Serien bleiben davor gesperrt. Struktur-/Parameterbefunde folgen
  unabhängig und müssen dieselbe erfolgreiche Originalauswahl betreffen.
- Empfohlenes Profil im Entwurf übernommen: beide Häufigkeitsschalter in beiden
  Armen an, ursprüngliche Sekundenkoordinate; sechs frische Suchen, drei bekannte
  Entwicklungsseeds, je 200 Suchiterationen, Vergleich 20/2 gegen 100/2. Dies ist
  adaptive Methodenentwicklung am bekannten besseren Approximationsprofil,
  keine neue Validierung. Die feste Diagnose ohne Populationsauswahl privilegiert
  das ausgeschaltete Profil nicht. Dieses und ein 2×2 bleiben Alternativen.
- Unverändert vorgeschlagen: Reihenfolge 20–100 / 100–20 / 20–100, 60 Minuten
  Gesamtlimit einschließlich Vorprüfungen und Abschlussprüfung, Originalauswahl,
  Grenzen, sechs vollständig verifizierte Zellen vor Gruppen/Paardifferenzen.
  Eine Übersicht der Erfolgswechsel ergänzt die bestehenden drei Seed-Paare;
  kein neuer Endpunkt. Keine Behauptung gleicher freier Suchpfade oder Kosten.
- Gezielt gegen die neue Regel abgeglichen: `C20=3, C100=1` mit guter, aber
  nicht unterstützter 100/2-Kurve bleibt weniger Erfolg; `3=3` bleibt Gleichstand;
  `0=0` bleibt ohne erfolgreiche Auswahl, auch bei kleineren Fehlern. Gemischte
  Seed-Wechsel bei `1→2` erlauben einen Mehrerfolg mit sichtbarem Verlust;
  gegensinnige Wechsel bei `1→1` bleiben ohne Mehrerfolg. Gute ungewählte Bäume
  oder Parameter eines anderen Baums erzeugen keinen unterstützten Originalfall.
  Unvollständigkeit oder späte Verifikationsfehler sperren sämtliche Gruppen
  und Paardifferenzen unabhängig von guten Einzelresultaten.
- Keine neue Optimierung, freie Suche, Julia-Ausführung oder Archivaudit. Keine
  zweite vollständige Reviewrunde: die Gegenfälle betreffen gezielt den P2-Befund.
  Alle drei eingefrorenen Laufzeitpläne und konsumierten Quellen bleiben erhalten;
  der neue Entwurf wird noch nicht zur Laufzeit konsumiert.
- Prüfungen der Korrektur: Dokumentations-/Linkprüfung für 40 Markdown-Dateien,
  `git diff --check`, unveränderte drei Planprüfsummen und explizite Zuordnung
  zur Dokumentations-CI. Der frühere grüne Lauf
  [41075733824](https://github.com/craexxn/ringdown-sr/actions/runs/41075733824)
  gehört ausschließlich zu `7ee5f38`; den Nachweis der Korrektur am aktuellen
  PR-Head prüfen. Dieser Zwischenstand ändert ausschließlich README, Entwurf
  und Fortsetzungsdatei; keine weiteren lokalen Arbeiten beim Einstieg vorhanden.

Nächster abgegrenzter Schritt: den Beschlussentwurf in Abschnitt 9 ausdrücklich
annehmen oder ändern. Erst nach Annahme diesen Plan einfrieren und den getrennten
Kontrollpfad mit vollständiger CI implementieren; anschließend einmalige
Manjaro-Ausführung am geprüften Stand. Ein Dokumentationsmerge allein beschließt
oder startet keine Suchserie. Weitere Übertragbarkeits-/Gewichtungsstudien und
ein Produktionsprofil sind damit nicht freigegeben.

## Aktueller Stand nach der Konstantendiagnose

- Beim Einstieg sauberer Checkout auf Implementierungshead `9202d20`, ein
  Worktree, keine offenen PRs. Remote-Branches und aktuelles `main` geprüft:
  `0a70f19e16e173aedf2e071a5f5b09d045ecbf69`, Merge von PR #42. Gegenüber dem
  CI-geprüften Implementierungshead nur zusätzliche Sprachregeln in `AGENTS.md`.
- Neuer Ergebnisbranch `codex/constant-diagnostic-results` ab diesem Merge;
  den aktuellen Dokumentationshead mit `git rev-parse HEAD` bestimmen.
  Dieser Nachtrag ändert ausschließlich Dokumentation und keine Laufzeiteingabe.
- Übermitteltes Originalarchiv `constant-manjaro-001.tar.gz`, 2.418.382 Bytes,
  tatsächliche SHA-256 vor Entpacken bestätigt:
  `346459d953468c81975670577b92aa155a1eaec884cebd462fe61e1ab23d492b`.
- Archivierter Ausführungsstand `0a70f19`, Git sauber, alle 48 Aufrufe
  abgeschlossen, Abschlussprüfung bestanden; etwa 20 Minuten Gesamtwandzeit.
- Selbst ausgeführter lesender Audit: alle 259 Dateien mit 258 Manifesthashes,
  47 Quell-/Pin-/Planhashes gegen den Ausführungscommit, 50 Workermanifeste,
  68 Optionsfelder je Snapshot einschließlich konkreter Plugins, Seeds,
  Restartvektoren und gespeicherte BLAS-Aufnahmen geprüft. Daten und Original-
  auswahl erhalten; beide Fehlergitter und sämtliche Paardifferenzen nachgerechnet.
- Zusätzlich eigener Whitelist-Bauminterpreter, Residuen-MSE mit `math.fsum`,
  direkte Parameterfehler und 6.506 Zustandsreplays. Alle 72 Anfangsverläufe
  bis Schritt 20 exakt identisch; alle 48 Rückgaben entsprechen den ursprünglich
  gewählten beobachteten Schlussminima. Originaldateien abschließend unverändert.
- Ergebnis: 20/2 besteht 0/24 Kurven- und Parameterprüfungen, 100/2 besteht
  24/24. Größter Zwischenpunkte-RMS unter 100/2 etwa `2,46e-8`.
  Physikalische Identifikation bleibt `not_assessed`; kein Nachweis freier Suche.
- Keine Julia-Ausführung, Fits oder Optimierungen im Audit. Gespeicherte native
  Options-/RNG-/BLAS-Nachweise sind von den neuen Python-Nachrechnungen getrennt.
  Die anfangs nicht verfügbare Umgebung wurde wieder erreichbar; für diesen
  Audit nur der gesperrte Pythonweg verwendet. Keine neue Umgebungsvalidierung
  durch Julia und keine erneute numerische CI behauptet.
- Reproduktionshilfen lokal unter `results/constant-audit-001/`: `audit.py`,
  `audit.json`, Diagramm als PNG/SVG; separat gesichertes Originalarchiv.
  Vollständige Zahlen und Prüfgrenzen im verlinkten Befund. Reine Dokumentation
  erhält schlanke CI; der aktuelle Nachweis gehört zum Ergebnis-PR.
- Lokal bestanden: Dokumentations-/Linkprüfung für 39 Markdown-Dateien,
  `git diff --check`, explizite Dokumentations-CI-Zuordnung und erneute Prüfung
  unveränderter konsumierter Quellen sowie aller 259 Originaldateien.
  Auditpaket zusätzlich unter `results/constant-audit-001.tar.gz` gesichert.

Der darauf aufbauende, weiterhin nicht beschlossene Planentwurf ist oben
verlinkt. Die folgenden historischen Implementierungsstände und Prüfnachweise
bleiben davon getrennt; ein neuer Lauf ist nicht freigegeben.

## Vorheriger Fortsetzungsstand nach der freien Kontrollserie

### Angenommene Diagnose A: implementierter Kontrollpfad

Der Nutzer hat den Reviewvorschlag am 30.10.2026 ausdrücklich angenommen und
seine Umsetzung beauftragt. PR #41 ist inzwischen als `978738c38e36e7bcb82c83acb5ba85db6df078f0`
gemergt; Remote-Branches, offene PRs, sauberer Checkout und ein Worktree geprüft.
Neuer Branch `codex/ringdown-constant-diagnostic` ab diesem Merge, kein weiterer
Implementierungsbranch oder offener PR beim Einstieg.

Der [neue eingefrorene Plan](constant_diagnostic_plan.md) übernimmt Option A:
48 Backendaufrufe, acht Starts, drei Seeds, 20/2 gegen 100/2, 60 Minuten.
Die wissenschaftliche Serie bleibt für den geprüften Manjaro-Stand vorgesehen.
Plan und erster Diagnoseentwurf sind in `f568902` remote gesichert;
den aktuellen Head mit `git rev-parse HEAD` bestimmen. Python-/Julia-Umgebung erneut
erfolgreich geprüft: Python 3.12.14, Julia 1.13.1, PySR 2.6.0,
SymbolicRegression 2.5.1 und PythonCall 0.9.36, Interpreter und Erweiterung.
Beschreibbare Cachepfade und tatsächlich vorhandene Python-Bibliothek bestätigt.

Implementiert: isolierter Launcher, absolute Options-/Plugin-/Seed- und
Xoshiro-Prüfung, zehn vorgeschaltete Kontrollen, 48 feste Aufrufe, binäre
Eingabeherkunft aus dem fest gehashten Archiv, beobachtender Callback, getrennte
Fit-/Gesamtzähler und vollständiger Export. Paarunterschiede erhalten beide
Parameterstatus; nicht beurteilbare Parameter werden nicht differenziert.
Abschlussabweichungen sperren sämtliche Gruppen-/Paaraussagen; Teilstände bleiben
erhalten. [Bedienung und Manjaro-Befehl](constant_diagnostic.md).

Lokale Prüfnachweise:

- Vollständiger Pythonlauf: 1.328 Tests bestanden. Danach ausschließlich
  Paarbericht und Prozesswandzeit ergänzt und fokussierte Tests erneut geprüft.
- `results/constant-technical-003.json`: zehn reine Kontrollen, vier direkte
  Optimierungen am eigenen Achtpunkt-Fixture und zwei echte isolierte technische
  Worker bestanden. Unabhängiger Export-/Residuen-/MSE-Replay und alle 68
  effektiven Felder pro Worker geprüft. Mit/ohne Beobachtung gleiche Parameter,
  Verluste, Callbackzahlen und RNG-Zustände für beide Budgets.
- Nach diesem nativen Lauf nur Paarbericht/Prozesswandzeit und Dokumentation
  ergänzt; der native Pfad blieb gleich. Der vollständige CI-Lauf am endgültigen
  PR-Head prüft auch den aktuellen Quellenstand dieses technischen Checks.
- Ruff, Formatierung, Dokumentations-/Link- und Diffprüfung bestanden.
  Alter und neuer eingefrorener Kontrollplan unverändert; der neue Diagnoseplan
  ist ausdrücklich als Laufzeitdokument mit voller CI erfasst.
- Originalarchiv mit dem neuen Leser identitätsgeprüft und ohne Extraktion
  gelesen: 128 Trainings- und 889 Diagnosedaten, 48 geplante Anfragen.
- Abschließende Codeprüfung: auch `SIGTERM` in die kontrollierte Beendigung
  der eigenen Prozessgruppe und Teilstandssicherung einbezogen; eigener
  Gegenfall einschließlich gesperrter Zusammenfassungen im Abbruchbericht.
  Danach 83 fokussierte Tests, Ruff, Format-, Dokumentations- und Diffprüfung
  bestanden. Diese notwendige Abbruchkorrektur erfordert volle CI am neuen Head.
- Die [erste vollständige CI](https://github.com/craexxn/ringdown-sr/actions/runs/41060066819)
  bestand am Vorhead `32feb9d5174fed4e5c86ea3ba519256d6de48cb4`, einschließlich
  des neuen nativen Diagnosechecks und aller bestehenden Integrationen.
  Sie ist kein Nachweis für die nachträgliche SIGTERM-Korrektur; der aktuelle
  CI-Nachweis wird in [PR #42](https://github.com/craexxn/ringdown-sr/pull/42) geführt.

Keine der 48 wissenschaftlichen Zellen oder freie Suchen im Rahmen dieser
Diagnoseimplementierung ausgeführt. Die vollständige technische CI kann die
bisherigen kleinen freien CI-Kontrollen ausführen; diese sind keine neue
wissenschaftliche Serie. Nächster Schritt: Implementierungs-PR mit voller CI
abschließen, danach auf geprüftem Stand die Manjaro-Diagnose ausführen.

### Gesicherter vorheriger Ergebnisstand

- Beim Einstieg `main` auf `97672ed` (übernommener Dokumentationsnachtrag
  aus PR #40), keine offenen PRs und sauberer lokaler Checkout. Neuer
  Ergebnisbranch `codex/representation-control-results`, Basis `97672ed`.
  Der genaue Dokumentationshead ergibt sich aus `git rev-parse HEAD`.
- Ausführungscommit weiterhin `4057caaffd9c4de5791ded14431c6e289db75b73`;
  im Originalarchiv mit sauberem Git-Zustand protokolliert. Keine Änderung
  der wissenschaftlichen Vorgaben oder der 41 konsumierten Quelldateien.
- Vom Nutzer übermitteltes Originalarchiv `representation-manjaro-001.tar.gz`,
  SHA-256 selbst bestätigt:
  `a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
- Archiv vollständig gelesen: 219 Dateien, davon 218 im Artefaktmanifest;
  sämtliche Datei-, Quell-, Worker-, Eingabe- und Planprüfsummen bestätigt.
  Alle neun Zellen `completed`, Abschlussprüfung `passed`.
- 57 Kandidaten mit sämtlichen Originalindizes, Vorhersagen, Residuen und
  MSE nachgerechnet; beide Raster zusätzlich mit unabhängig geschriebenem
  Bauminterpreter und `math.fsum` ausgewertet. Vorprüfungsobjekte, konkrete
  Pluginfelder, Seeds und Haswell-Aufnahmen erneut abgeglichen. Gruppen-
  statistiken und sechs Seed-Paare reproduziert. Keine Originaldatei verändert.
- Ergebnis: Häufigkeitsschalter verbessern die Trainings-MSE bei 3/3 Seeds
  um rund 90–97 %; Zeitstreckung hilft beim Training bei 2/3 Seeds und kann
  auf Zwischenpunkten deutliche Spitzenfehler erzeugen. Alle 57 Kandidaten
  verfehlen die Kurvengrenzen; alle Strukturen `not_supported`, Parameter
  `not_assessed`. Der komplette Auditumfang und alle Zahlen stehen im Befund.
- In diesem Auswertungsschritt keine neue Suche, kein Fit und kein Julia-Lauf.
  Die hier abgeglichenen nativen Backendnachweise sind archivierte Aufnahmen.
  Ergebnisnachtrag ausschließlich als Dokumentation; vollständige CI und
  Review werden ohne Codeänderung nicht erneut ausgeführt.


## Historischer Entscheidungsstand nach übermitteltem Review

Auf Nutzerauftrag ist die [Entscheidungsgrundlage samt vollständigem
Review-Prompt](representation_next_step_review.md) im bestehenden Ergebnisbranch
und PR #41 ergänzt. Gesicherter Ergebnisstand vor dieser Ergänzung:
`73e1c6748fb6683b99336d81271f332e60034d9f`; Vergleichsbasis
`97672ed9b14b81ca90663dc178072b515ee252bc`.

Der Nutzer hat das KI-basierte Methodenreview zu PR #41 übermittelt:
gelesener Head `1c816e5e40b16a0fd03b268df24cf869d6a33a57`, Vergleichsbasis
`97672ed9b14b81ca90663dc178072b515ee252bc`. Der vollständige Befund steht
mit Herkunft und Prüfgrenzen in der bestehenden
[Entscheidungsgrundlage](representation_next_step_review.md#übermittelter-ki-basierter-reviewbefund).
Er empfiehlt Option A und berichtet keine entscheidungsblockierende
Unstimmigkeit in der beschriebenen Optimiererlücke.

Vorgeschlagen sind eine feste Vierkonstantenstruktur, acht Starts, drei
RNG-Initialisierungen, 20/2 und 100/2 sowie 60 Minuten Gesamtwandzeit:
48 Backendaufrufe, höchstens 144 lokale Optimierungen, freies Suchbudget null.
Die konkreten Starts, Kontrollen, Auswertung und Weiterentscheidungen stehen im
übermittelten Entwurf. Diese Zahlen und Diagnoseprivilegien sind noch nicht
vom Nutzer beschlossen; es gibt weder eine neue Implementierung noch Ergebnisse.

Prüfgrenze des übermittelten Reviews: Quellen und dokumentierte Zahlen gelesen;
kein eigener Originalarchiv-Audit, keine Tests, Fits, Optimierungen oder Suchen.
Diese Aussagen sind übermittelte Nachweise und wurden bei der Übernahme nicht
neu ausgeführt. Der vorherige eigene Archivaudit bleibt davon getrennt.

Beim Einstieg zu diesem Nachtrag: sauberer Checkout und ein Worktree auf
`codex/representation-control-results` am gelesenen Head; Remote-Branches und
PRs abgeglichen, PR #41 weiterhin offen, `main` unverändert auf `97672ed`.
Die [Dokumentations-CI des gelesenen Heads](https://github.com/craexxn/ringdown-sr/actions/runs/41054721398)
bestand. Dieser Nachtrag aktualisiert ausschließlich README, Entscheidungs-
und Fortsetzungsdokument; seinen genauen Head mit `git rev-parse HEAD` bestimmen.
Lokal bestanden: Dokumentations-/Linkprüfung für 36 Markdown-Dateien und
`git diff --check`; Wortlaut des Zitats gegen die Eingabe abgeglichen,
schlanken CI-Umfang und beide unveränderten Planprüfsummen bestätigt.
Der neue CI-Status gehört zum neuen Head in PR #41.

Nächster abgegrenzter Schritt: Nutzerentscheidung über den konkreten Vorschlag.
Bei Annahme einen eigenen eingefrorenen Methodenplan und einen technisch
geprüften Diagnosepfad erarbeiten. Keine automatische weitere Reviewrunde,
keine neuen numerischen Läufe und kein eigenständiger Merge.

## Vorheriger Fortsetzungsstand nach Merge und Review

- PR #39 ist auf `main` übernommen, Mergecommit und fester Ausführungsstand:
  `4057caaffd9c4de5791ded14431c6e289db75b73`.
- Geprüfter PR-Head: `cfe44bfb84baef9238f52609ba1030eaa4416ed7`;
  Vergleichsbasis: `909942d3f3910ea20df1703dd12421abe4867a4e`.
  PR-Metadaten und Remote-Branches erneut gelesen. Beim Einstieg keine
  offenen PRs, sauberer lokaler Checkout und ein Worktree.
- Dateibaum des Mergecommits und des geprüften Heads identisch:
  Git-Tree `c85720ff579f75ee6af3849b593ad0dfdf371f7d`.
  Die [vollständige CI](https://github.com/craexxn/ringdown-sr/actions/runs/41038219843)
  ist am PR-Head erfolgreich abgeschlossen; GitHub-Status erneut abgefragt.
  1.288 Python-Tests, 295 Julia-Prüfungen, Residuen-/Optimierer-Replays,
  native Profil-/Koordinaten-/Aliasprüfung und bestehende Integrationen
  bestanden. Keine vollständige Wiederholung zur Statuspflege.
- Dokumentationsnachtrag auf `codex/representation-manjaro-handoff`, Basis
  der oben genannte Mergecommit. Exakten Dokumentationshead beim Fortsetzen
  mit `git rev-parse HEAD` bestimmen. Dieser Nachtrag verändert keinen Code,
  Laufzeitplan oder konsumierten Suchinput. Die wissenschaftliche Ausführung
  verwendet weiterhin den festgelegten Mergecommit.

### Übermittelter KI-basierter Reviewbefund

Der Nutzer hat ein gezieltes KI-basiertes Review zu PR #39 am oben genannten
Head gegen die oben genannte Basis übermittelt. Ergebnis: **keine
korrekturbedürftigen Befunde zur beauftragten Methodentreue**; keine zusätzliche
gezielte Gegenprüfung erforderlich. Geprüft wurden alle 19 geänderten Dateien
und relevante unveränderte Aufrufer/Abhängigkeiten nach Repositoryregeln:
Zeitumrechnung und vollständige Baumauswertung, Originalauswahl, absolute
Seed-/Pluginprüfung ab der ersten Zelle sowie die Auswertungssperre.

Als selbst ausgeführte Prüfungen des Reviews wurden übermittelt:

- 210 gezielte Python-Tests und der gepinnte Python-/Julia-Umgebungscheck.
- Neun echte Optionsobjekte mit je 68 Feldern und neun native Referenzfälle
  einschließlich Einheiten-, Alias- und falscher-Seed-Gegenprüfung.
- 18 unabhängige Frequenz-/Vorzeichen-/Phasenfälle sowie zwei zusätzliche
  Gegenprüfungen zu Originalindex und später Manipulation.
- Ruff, Format-, Dokumentations- und Diffprüfungen sowie Planprüfsummen.

Diese Reviewprüfungen wurden in diesem Fortsetzungsschritt übernommen und
nicht erneut ausgeführt. Der Reviewbefund ist kein Ergebnis wissenschaftlicher
Kontrollsuchen. Insbesondere entspricht die Auswertbarkeit vollständig
geprüfter anderer Gruppen/Paare nach einem zelllokalen Abbruch bei bestandener
Abschlussprüfung dem eingefrorenen Plan.


## Historischer Implementierungseinstieg und verbindliche Grundlage

- Repository `craexxn/ringdown-sr`, Branch `codex/representation-control`.
- Einstieg dieses Cloudauftrags auf geprüftem Remote-Head
  `9c18af2ca6b761eb0ed2e0d8375aaab1dfe484e4`; keine offenen PRs,
  sauberer Checkout, ein Worktree. Gegenüber `0cf7ff1` nur Statusnachtrag.
- `main` auf `909942d3f3910ea20df1703dd12421abe4867a4e` geprüft und
  integriert: ausschließlich organisatorische Änderungen aus PR #38.
  Die volle CI-Ausnahme für beide Laufzeitpläne bleibt erhalten.
- Basis des Methodenplans: `311f87d2df9e47d3e326f24709b8085569f7b5f3`
  (PR #37). [Plan](search_representation_plan.md), unveränderter SHA-256:
  `16cfe818c312fb5bb0a6c594505ad76ba41e41bd7f4a37decc245677c6b8ad86`.
  Auch der alte Plan und seine Prüfsumme bleiben unverändert.
- Veröffentlichter fachlicher Head vor diesem abschließenden
  Dokumentationscheckpoint: `b4db89d6baa8c8c0e914f82f9b46727cc49b2b4f`.
  Arbeitsverzeichnis sauber; Code und Zwischenstände sind remote gesichert.
- Die ursprünglichen lokalen Commits bleiben unter
  `codex/representation-control-local-checkpoints-20261030` erhalten.
  GitHub hatte ihre Pushes wegen der voreingestellten privaten Commit-E-Mail
  abgelehnt. Inhaltsgleiche eigene Commits wurden mit der bereits im Repository
  verwendeten GitHub-Noreply-Adresse veröffentlicht: `2345cb2` entspricht
  `cbc95ca`, `27bc91a` entspricht `d9c3c62`, `b4d60fd` entspricht `b4db89d`.
  Identische Git-Bäume geprüft. Remote-Update von `9c18af2` erfolgte als
  Fast-forward; kein Force-Push und keine Änderung bestehender Remotecommits.


## Implementiert

- Diagnosekern `representation_control.py`: neun feste Zellen,
  schreibgeschützte Koordinaten, getrennte Such-/physikalische Diagnose,
  Replays, Bedingungsstatistik und Differenzen zur frischen Baseline je Seed.
- Begrenzte Profile, absolute Pluginfeldprüfung und native Guard um den
  bestehenden numerischen Callback; allgemeine Suchpfade unverändert.
- `run_representation_control.py`: isolierter Launcher, Options- und
  Referenzvorprüfung, Manifest-/Quell-/Daten-/Workerverifikation, alle
  Kandidaten/Originalauswahl, sichere Teilberichte und abschließende Sperre
  sämtlicher Zusammenfassungen/Differenzen bei Verifikationsfehlern.
- Manifest prüft auch Profil-/Verifikationsdateien, native Quellen und
  Laufzeitkopien. `_candidate` erhält Suchzeiten und `FS/alpha`.
  Fit-Callbackzahlen bleiben vom Gesamtzähler einschließlich der zusätzlichen
  Nullkurvenauswertung getrennt.
- 75 neue Treiberfälle mit konsistent neu gehashten Fälschungen bereits in
  der ersten Zelle, Abbruch-/Teilständen und späten Dateimanipulationen.
- Echte Backend-Referenzprüfung für 250, 4346 und 33018 Hz in allen drei
  Bedingungen; Einheiten und native Seed-Guard. Keine Fit-/Suchaufrufe.
- Technischer Integrationseinstieg: drei frische Profilworker an `y=1+t`,
  je zwei Iterationen. Dieses gesonderte Prüfprogramm ändert nicht das
  wissenschaftliche Budget. In vollständige CI eingebunden.
- [Bedienungsdokumentation](representation_control.md) einschließlich
  späterer Manjaro-Befehle und lokalem Cloud-Startprofil.

## In dieser Cloudinstanz selbst ausgeführt

- Gesperrte Installation und Umgebungscheck: Python 3.12.14, PySR 2.6.0,
  Julia 1.13.1, SymbolicRegression 2.5.1, PythonCall 0.9.36;
  Interpreterbindung und geladene Erweiterung bestätigt.
- Beschreibbare Cache-/Depotpfade geprüft. Nicht versionierte lokale Startdatei
  `/workspace/ringdown-cloud-env.sh` setzt die vorgegebenen sechs Variablen
  und `JULIA_PYTHONCALL_LIB`, ermittelt aus dem tatsächlichen gepinnten
  Projektinterpreter mit Existenzprüfung. Jeder Projektbefehl lädt sie.
  Haswell/Threadlimit 1 nur für die vorgesehenen Kontrollen.
- 86 ursprüngliche fokussierte Tests bestanden; danach 48 Pluginfälle
  ergänzt, insgesamt 134 fokussierte Fälle bestanden am Checkpoint `2345cb2`.
- Optionsvorprüfung: neun echte Objekte, null Callbackaufrufe, kein Fit.
  Callbackdarstellung und konkrete Plugins sowie 29 gemeinsame absolute
  Verträge bestätigt. Geladene NumPy-/SciPy-/Julia-Pools: Haswell, Limit 1.
  Lokales Artefakt `results/representation-options-001.json`.
- Neun echte feste Referenzfälle bestanden: native Verlustauswertung,
  unabhängige Residuen-MSE, 11 Knoten, Parameter-/Aliasrückrechnung und
  Einheiten. Lokales Artefakt `results/representation-references-001.json`.
- Erster vollständiger Python-Lauf des Treiberentwurfs: **1287 Tests bestanden**
  in 85,59 s. Davon 75 neue Treiberfälle. Keine Julia-Tests in dieser Zahl.
- Technischer Integrationsversuch `results/representation-integration-001`:
  Vorprüfungen bestanden, erster Profilworker ausgeführt und exportiert;
  anschließender vollständiger Optionsvergleich hat korrekt gestoppt.
  Die nackten Julia-Optionsprototypen hatten drei andere Defaults als PySR:
  `input_stream`, `should_simplify`, `define_helper_functions`.
  Gepinnte Quelle PySR 2.6.0 `sr.py`, Konstruktor und Optionsübergabe, geprüft.
  Nur die Prototypen wurden an die unveränderte PySR-Suche angepasst:
  `devnull`, `true`, `false`. Kein Feld wurde aus der Prüfung entfernt.
  Der begründete Folgelauf
  `results/representation-integration-002` am sauberen lokalen Commit
  `27bc91a` ist **vollständig bestanden**: neun Optionsobjekte, neun native
  Referenzfälle und alle drei frischen technischen Profilworker; sämtliche
  68 Optionsfelder entsprechen der Vorprüfung (Ausgabepfad separat).
- Zwei gleichzeitige Starts mit fremder aktiver CondaPkg-Sperre bestanden;
  die Sperre blieb unverändert, keine Conda-Umgebung entstand.
- Abschließend Einzelstatus für beide Seiten jeder Fehlerdifferenz ergänzt.
  Ein endlicher Wert mit unbestimmter Diagnose bleibt unauswertbar;
  zugehöriger Gegenfall ergänzt. 210 fokussierte Tests bestanden.
  Ruff, Formatierung, lokale Links und `git diff --check` bestanden.

## Historisch: nächste Schritte vor Annahme des freien Budgetplans

1. Den unabhängig nachgerechneten [Diagnosebefund](constant_diagnostic_results_manjaro_001.md)
   als abgeschlossenen Entwicklungsbefund sichern und beurteilen.
2. Den neuen [Entwurf](free_optimizer_budget_plan_draft.md) gemeinsam mit diesem
   Befund einmalig methodisch prüfen; Reviewhead, Basis und Umfang nennen.
3. Erst danach genau ein Design und alle Zahlen/Gates beschließen und einfrieren.
   Keine automatische Implementierung, Budgeterhöhung oder weitere Suchserie;
   kein eigenständiger Merge.

Der Plan und beide Laufzeitplanprüfsummen sind unverändert. Keine zusätzlichen
wissenschaftlichen Suchen in der Cloud und keine automatische Wiederholung.
Der Alias-Blindfleck bei `8*fs` bleibt ausdrücklich bestehen.

## Historische Nachweise

Der gesonderte Diagnose-/CI-Kern `91f95e2` war mit 64 Tests geprüft.
Vor dem früheren Umgebungsausfall bestanden 86 fokussierte Pythonfälle,
aber nicht für den exakten wiederhergestellten Head `0cf7ff1`.
Die damaligen Aussagen zur nicht erreichbaren Umgebung in `0cf7ff1` und
`9c18af2` beschrieben die jeweiligen Sicherungszeitpunkte; die aktuelle
Cloudbereitschaft wurde oben neu geprüft. Die früher übermittelten
Cloudnachweise am fremden Stand `60798c8` sind keine Prüfnachweise für
diesen Implementierungsbranch und werden nicht übernommen.
