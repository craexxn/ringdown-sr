# ringdown-sr

Repository zur Masterarbeit über rauschgewichtete symbolische
Regression zur Rekonstruktion kurzer Ringdown-Signale.

## Projektstatus

Fortsetzungsstand: 06.11.2026; abgeglichener main `16d2f40` nach ausdrücklich
freigegebener Übernahme von [PR #73](https://github.com/craexxn/ringdown-sr/pull/73)
und [PR #74](https://github.com/craexxn/ringdown-sr/pull/74).
Alle drei Bewertungsstufen sind implementiert, geprüft, übernommen und auf
78 Originalauswahlen angewandt: [Kurvenklassen](docs/supplemental_assessment_results_001.md),
[Originalfamilie und Domain](docs/supplemental_structure_results_001.md),
[quantifizierte Restterme](docs/supplemental_remainder_results_001.md).

Die Neubewertung erklärt den früheren Rückgang der Strukturzählung in der
äußeren Staffel als Erkennungsgrenze: 500, 2.000 und 5.000 erreichen jeweils
5/5 A-Kurven mit gültiger Originalfamilie. Die drei frischen Transfer-Referenzen
bleiben bei 0/3; Suchrobustheit hat deshalb Vorrang. Die 38 gültigen Mitglieder,
zwei Fortsetzungen und drei ungeklärten Familienbefunde unter 43 A-Kurven sind
eine Beschreibung des Bestands, keine gepoolte Erfolgsquote. Neue Parameter-
übereinstimmungen bleiben `not_assessed`.

Der [zentrale Leitfaden](docs/ringdown_recovery_roadmap.md) führt nun Phase 2:
[begrenzte Endfrontdiagnose](docs/endfront_diagnostic_001.md), danach Vorbereitung
von 1 × 500, 1 × 2.000 und 4 × 500 bei festem lokalem Profil 300/5.
Das unregelmäßige Zusatzraster begleitet bereits die Entwicklung; es dient
ausschließlich der Diagnose. Wissenschaftliche Suchläufe bleiben ein separater
Ausführungsschritt. Umsetzung und Nachweise stehen im
[Fortsetzungsstand](docs/representation_implementation_status.md).

[CI-Sparplan](docs/github_actions_savings_plan.md),
[technische Optimierung](docs/assessment_performance.md) und
[Archivregel](docs/results_archiving.md) sind übernommen. Der
[Ergebnisindex](docs/results_index.md) führt Zuordnung und offene Sicherung:
gemeinsamer Archivordner plus zweite gesicherte Kopie, Releases optional.
Konkrete Ablageorte und geprüfte Zweitkopien sind weiterhin unbestätigt.
Offizieller Bearbeitungsbeginn: 12.10.2026.
Beginn der fachlichen Pilotimplementierung: 15.10.2026.

### Historische Entwicklungsbefunde

Die folgenden Abschnitte erhalten die ursprünglichen Bewertungen und damaligen
Arbeitspläne. Ihre Ausblicke werden durch den aktuellen Leitfaden oben abgelöst;
sie geben keine erneute wissenschaftliche Ausführung frei.

Der [Manjaro-Suchbudgetlauf 004](docs/search_duration_results_manjaro_004.md)
ist vollständig abgeschlossen und unabhängig nachgerechnet: **20 Zellen,
193 Kandidaten**, alle nativen Vorhersagen und Verluste bitgleich reproduziert.
Die aufgezeichnete Gesamtdauer beträgt rund 43 Minuten.

Ohne Grammatikbeschränkung steigt die Zahl erfolgreicher Originalauswahlen
bei 2.000 statt 200 Iterationen von 3/5 auf 4/5; der neue Erfolg besitzt eine
unterstützte Ringdown-Struktur mit passenden Parametern. Mit Beschränkung
steigt die Zahl von 2/5 auf 3/5, ohne unterstützten Strukturnachweis beim neu
erfolgreichen Seed. Das ist ein positives Entwicklungssignal für das höhere
Budget ohne Einschränkung und ein zusätzlicher Approximationserfolg mit
Einschränkung. Ein Gegenfall zeigt trotz kleinerer Trainings-MSE erheblich
schlechtere Zwischenpunktfehler. Fünf adaptive Seeds am bekannten Signal
begründen keine allgemeine Leistungsvalidierung oder physikalische Identifikation.

Der [lokale Optimiererbudgetvergleich](docs/local_optimizer_results_manjaro_001.md)
ist ebenfalls abgeschlossen: **20 frische Zellen, 183 Kandidaten**, sämtliche
nativen Vorhersagen und Verluste bitgleich nachgerechnet; Gesamtdauer knapp
22 Minuten. Bei fest 200 äußeren Iterationen erreichen 100/2, 300/2, 100/5 und
300/5 jeweils **1/5, 2/5, 2/5 und 3/5 Kurvenerfolge**. Unterstützte
Rekonstruktionen bleiben in allen Gruppen 1/5. 300/5 benötigt rund 32 % mehr
summierte Zellzeit als 100/2 und verliert einen Baselineerfolg.
Es ist ein Kandidat für das nächste Arbeitsprofil, kein belegtes Optimum.

Die [äußere Staffel bei fest 300/5](docs/outer_search_ladder_results_manjaro_001.md)
ist abgeschlossen und unabhängig nachgerechnet: **20 Zellen, 164 Kandidaten**,
alle nativen Vorhersagen und Verluste bitgleich; Gesamtdauer rund 2 h 4 min.
200/500/2.000/5.000 Iterationen erreichen **1/5, 5/5, 5/5 und 5/5 Kurvenerfolge**;
die planmäßige Strukturwertung liegt bei **1/5, 4/5, 3/5 und 2/5**.
Eine getrennte nachträgliche Diagnose führt alle sechs formal nicht erkannten
Kurvenerfolge reell auf Ringdown-Formen zurück. Der Rückgang dieser Wertung
belegt daher keine schlechtere physikalische Struktur; die Originalzählungen
und der Erkenner wurden nicht verändert.

Der [Transfercheck bei 500/300/5](docs/transfer_check_results_manjaro_001.md)
ist auf Manjaro abgeschlossen und unabhängig nachgerechnet: **18 Zellen,
198 Kandidaten**, alle nativen Vorhersagen und Verluste bitgleich;
Gesamtdauer rund 50 Minuten. Je drei neue gepaarte Seeds ergeben für
anchor/frequency/decay/phase/amplitude/combined **C = 0/3, 1/3, 1/3, 2/3,
1/3, 2/3** und **S = 0/3, 1/3, 1/3, 1/3, 0/3, 1/3**.
Bereits der frische bekannte Referenzfall erreicht keinen Kurvenerfolg;
die frühere 5/5-Beobachtung überträgt sich nicht auf diese neue Seedgruppe.
500/300/5 ist damit kein belegtes robustes Rekonstruktionsprofil.
Die fünf Signaländerungen liefern einzelne Erfolge, aber keine allgemeine
Übertragbarkeit oder gemeinsame Erfolgsquote über die sechs Bedingungen.

Drei kurvengenaue Originalauswahlen bleiben formal unerkannt. Eine getrennte
nachträgliche algebraische Diagnose erklärt diese Schreibweisen; bei einem
verschachtelten Quotienten bleiben Definitionslücken an Kosinusnullstellen.
Die planmäßigen S-Zählungen und Parameterstatus bleiben unverändert.
Der [Plan](docs/transfer_check_plan.md) und alle Eingabedaten sind unverändert;
die [Bedienung](docs/transfer_check.md) dokumentiert den abgeschlossenen Laufweg,
keine Wiederholungsfreigabe. Technischer Prüfstand in
[PR #65](https://github.com/craexxn/ringdown-sr/pull/65).

2.000 und 5.000 benötigten am bisherigen Signal rund 3,05-/6,24-mal die summierte
Zellzeit der 500er-Gruppe. Ein allgemeines Optimum oder Übertragbarkeit ist
nicht belegt. Allgemeine Grammatik, `should_simplify=false`, Originalauswahl,
Strukturerkenner und numerische Prüfungen bleiben erhalten. Referenzparameter
werden für jedes Signal passend verglichen; keine Auswahl anhand der Wahrheit.

Weitere 500/1.000-Tests und die optionale Staffel mit **300/2** sind zurückgestellt,
keine automatische Anschlussfreigabe. Auch 10.000 ist derzeit nicht begründet.
Als nächster abgegrenzter Schritt ist ein
[Seed-/Treiber-Kreuzvergleich](docs/seed_driver_crosscheck.md) implementiert:
zwei feste Gegenrichtungen mit historischen Workerpfaden, vollständigem
Frontvergleich und unverändertem 500/300/5-Budget. Ein übermittelter
Nachrechnungsbefund berichtet die Reproduktion beider vollständigen Endfronten;
Primärdaten und ein versionierter Ergebnisbericht liegen hier noch nicht vor.
Die Einordnung und Grenzen stehen im [Leitfaden](docs/ringdown_recovery_roadmap.md).
Nach Abschluss der Zusatzbewertung folgen die dort beschriebenen, vorab
festzulegenden Entwicklungskontrollen und die Prüfung des tatsächlichen
späteren Laufwegs; anschließend Rauschpilot und Hauptversuchsplanung.
Die Seedabhängigkeit und eine praktikable Messregel
für Strukturstabilität müssen im Pilotdesign ausdrücklich berücksichtigt werden.
Wissenschaftliche Ausführung bleibt auf Manjaro; Hauptstudie und
wissenschaftliche Übertragbarkeit bleiben offen.
Die vorgemerkte kurze Bereinigungsbestandsaufnahme bleibt offen; funktionierenden
Code und Originalergebnisse erhalten, anschließend nur konkrete kleine Änderungen.
WSL2, Parallelisierung wissenschaftlicher Läufe und größere Umstrukturierung
bleiben zurückgestellt.

[Ergebnis und Grenzen](docs/search_duration_results_manjaro_004.md),
[Bedienung](docs/search_duration.md),
[Methodenplan](docs/search_duration_plan.md) und
[Prüf-/Fortsetzungsstand](docs/representation_implementation_status.md)
enthalten die Details. Die Startbefehle dokumentieren den abgeschlossenen
Laufweg; sie geben keine automatische Wiederholung frei.

Dieser Abschnitt ist der kurze Einstieg für neue Chats. Arbeits- und
Übergaberegeln stehen in [AGENTS.md](AGENTS.md); vor Fortsetzung sind lokale
Änderungen, Branches und PRs erneut zu prüfen.

- **Abgeschlossene Methodengrundlage:** Der geprüfte
  [Plan für Zeitdarstellung und Komplexitätshäufigkeiten](docs/search_representation_plan.md)
  ist mit PR #37 übernommen. Er ergänzt den unveränderten
  [rauschfreien Kontrollplan](docs/noiseless_control_plan.md).
- **Implementierung abgeschlossen:** Der getrennte Kontrolltreiber ist mit
  PR #39 übernommen. Die vollständige technische CI am PR-Head `cfe44bf`
  bestand. Ein übermitteltes KI-basiertes Review desselben Heads fand keine
  korrekturbedürftigen Befunde zur beauftragten Methodentreue.
  [Bedienung und Artefakte](docs/representation_control.md) sowie
  [Fortsetzungsstand](docs/representation_implementation_status.md) enthalten
  Bezugscommits, Prüfumfang und Grenzen. Die wissenschaftliche Kontrollserie
  wurde auf Manjaro ausgeführt und ihr vollständiges Originalarchiv hier
  unabhängig nachgerechnet.
- **Neuer Entwicklungsbefund:** Die [Zeitdarstellungs-Kontrollserie auf
  Manjaro](docs/representation_control_results_manjaro_001.md) ist mit neun
  abgeschlossenen Zellen und bestandener Abschlussprüfung archiviert.
  Alle 57 Kandidaten, Originalauswahlen, Fehler und Seed-Differenzen wurden
  nachgerechnet. Die Häufigkeitsschalter senken die Trainings-MSE bei allen
  drei Seeds um rund 90–97 % gegenüber der frischen Baseline. Trotzdem
  erfüllt kein Kandidat die Kurvengrenzen; der Erkenner unterstützt keine
  gefundene Struktur, Parameter und Identifikation bleiben `not_assessed`.
- **Konstantendiagnose abgeschlossen:** Der [angenommene Diagnoseplan](docs/constant_diagnostic_plan.md)
  ist mit PR #42 implementiert und auf Manjaro ausgeführt. Das vollständige
  [Originalarchiv ist unabhängig nachgerechnet](docs/constant_diagnostic_results_manjaro_001.md):
  Unter 20/2 bestehen 0/24, unter 100/2 alle 24 Fits die festen Kurvengrenzen;
  Parameterbefunde wechseln von `mismatched` zu `matched`. Bei allen 72 lokalen
  Paaren sind die ersten 20 Schritte exakt gleich. Das belegt Budgetabhängigkeit
  für die vorgegebene Struktur und das deklarierte Startgitter; freie
  Strukturentdeckung und Übertragbarkeit bleiben offen.
- **Freier Budgetvergleich abgeschlossen übermittelt:** PR #45 ist übernommen;
  vollständige technische CI und gezieltes Nachreview der Widerrufssicherung
  sind am baumgleichen Head `4e29ae4` abgeschlossen. Die
  [Manjaro-Auswertung](docs/free_optimizer_budget_results_manjaro_001.md) meldet
  sechs vollständige Zellen und bestandene Abschlussverifikation.
  100/2 senkt die Trainings-MSE bei allen drei bekannten Seeds um rund 64–80 %;
  trotzdem 0/3 erfolgreiche Originalauswahlen unter beiden Budgets und kein
  Kurvenerfolg unter insgesamt 50 Frontkandidaten. Beim Seed 20261021 steigt
  der Maximalfehler. Sechs gepostete Formeln und ihre 30 Fehlerwerte wurden
  unabhängig nachgerechnet; der vollständige Originalarchiv-Audit bleibt offen.
  [Bedienung und Artefakte](docs/free_optimizer_budget.md).
- **Suchbeobachtung und Verifikationskorrektur:** Der
  [eingefrorene Methodenplan](docs/search_trajectory_plan.md)
  umfasst drei beobachtete 100/2-Läufe mit drei frischen Kontrollläufen.
  Feste Populationsaufnahmen beantworten keine vollständige Mutationshistorie.
  Das übermittelte KI-basierte Methodenreview empfiehlt den Entwurf nach
  Korrektur einer Interpretationsregel: fehlende Frontzugehörigkeit belegt
  kein zeitliches Verschwinden. Die Regel ist korrigiert und gezielt
  gegengeprüft. Sechs Zellen und organisatorische Grenzen sind angenommen;
  der getrennte Beobachtungspfad ist mit PR #47 und vollständiger CI übernommen.
  Der erste Manjaro-Lauf blieb bei der Prüfung von Zelle 3 unvollständig.
  Originalarchiv und fünf gezielte native Replays sind geprüft: zwei Fälle
  zeigen Unterschiede der Julia-/NumPy-Baumauswertung, drei einen Unterschied
  zwischen gespeichertem Verlust und beiden aktuellen Replays mit offener Ursache.
  Die [gebundene Verifikationsergänzung](docs/search_trajectory_replay_policy.md)
  trennt diese Nachweise und schließt ungeklärte Mitglieder von positiven
  Markern aus. PR #48 ist übernommen; das übermittelte KI-basierte Review fand
  im geprüften Umfang keine Code- oder Methodenbefunde. Die
  [vollständige CI](https://github.com/craexxn/ringdown-sr/actions/runs/41437880627)
  am Head `27d10fe` bestand mit 1.646 Python-Tests, 295 Julia-Prüfungen und
  sämtlichen Integrationen einschließlich beider letzten Haswell-Suchen.
  Head und Merge `f3c0cb4` haben denselben Dateibaum. Der frühere abgebrochene
  CI-Lauf bleibt ein historischer Teilnachweis; das technische Joblimit beträgt
  inzwischen 45 Minuten. Die frische Serie `trajectory-manjaro-002` ist
  auf Manjaro abgeschlossen und das [Originalarchiv unabhängig geprüft](docs/search_trajectory_results_manjaro_002.md):
  sechs Zellen, drei exakte Aus/an-Paarvergleiche, Abschlussprüfung bestanden.
  Weiterhin kein erfolgreicher Frontkandidat und kein Kurvenerfolg unter den
  verifizierten beobachteten Vorkommen. Unter 62.384 Positionen bleiben 157 numerisch ungeklärt und
  3.598 nicht beurteilt. Eine erkannte Exponential-Kosinus-Form wächst und
  passt schlecht; sie ist keine erfolgreiche Ringdown-Rekonstruktion.
  [Bedienung und Artefakte](docs/search_trajectory.md) sowie der
  [Fortsetzungsstand](docs/representation_implementation_status.md) halten
  Ausführungsstand und verbleibende Nachweise fest.
  Keine automatische weitere Budgetstufe, kein Produktionsprofil und keine
  allgemeine Leistungsvalidierung.
- **Forschungsanspruch bestätigt:** Das bereitgestellte Exposé verlangt freie
  Formelfindung und untersucht den Einfluss der Hintergrundlänge auf Genauigkeit
  und Strukturstabilität bei Kovarianzgewichtung. Der bekannte Strukturfit bleibt
  Referenz. Die [Literatur- und Methodenabwägung](docs/free_form_method_assessment.md)
  ist als Entscheidungsgrundlage ausgearbeitet: neun Primärarbeiten mit
  getrenntem Zugriffsstatus, Vorwissen und Übertragungsgrenzen. Darauf aufbauend
  wurde der [begrenzte Grammatikvergleich](docs/trigonometric_grammar_plan.md)
  am 03.11.2026 angenommen und mit PR #52 übernommen; #51 ist als ersetzt
  geschlossen. Die einmalige Manjaro-Serie ist abgeschlossen und ihr
  [Originalarchiv unabhängig nachgerechnet](docs/trigonometric_grammar_results_manjaro_001.md):
  sechs Zellen, Abschlussverifikation bestanden, **0/3 erfolgreiche
  Originalauswahlen in beiden Armen**, kein Kurvenerfolg unter 51 Frontkandidaten.
  Das Verbot trigonometrischer Nachfahren verbessert einen Seed deutlich,
  verschlechtert die RMS-Werte der anderen beiden und stützt die Hypothese nicht.
  Die zusätzliche Regel wird gemäß Plan nicht übernommen; der Versuch ist
  beendet. Als neuer abgegrenzter Schritt ist der oben verlinkte
  Suchbudgetvergleich unter beiden Grammatiken angenommen. Die [Bedienung](docs/trigonometric_grammar.md)
  dokumentiert den abgeschlossenen Laufweg, keine Wiederholungsfreigabe.
  Freie Formelfindung bleibt Forschungsziel; kein Produktionsprofil oder
  Hauptversuch ist freigegeben. Wissenschaftliche Suchen bleiben auf Manjaro;
  hier Vorbereitung, technische Kontrollen und lesende Audits.
  Die Abgrenzung zwischen Pilot und Hauptversuchen steht im
  [Fortsetzungsstand](docs/representation_implementation_status.md).
- **Prüfnachweise:** Die [vollständige CI zu PR #39](https://github.com/craexxn/ringdown-sr/actions/runs/41038219843)
  bestand am Head `cfe44bf`: 1.288 Python-Tests, Julia- und technische
  Integrationsprüfungen. Der Mergecommit hat denselben Dateibaum. Die
  [schlanke CI zu PR #37](https://github.com/craexxn/ringdown-sr/actions/runs/41022224068)
  bestand am Head `e92152a`; sie prüft Dokumentation, keine Numerik.
  Der [Haswell-Befund](docs/symbolic_core_results.md) enthält die unabhängige
  Nachrechnung übermittelter Originalarchive. Der
  [rauschfreie Manjaro-Befund](docs/noiseless_control_results_manjaro_001.md)
  beruht dagegen auf übermittelten Berichtsauszügen; ein unabhängiger Audit
  aller Originalartefakte ist dort ausdrücklich nicht belegt.
  Die [vollständige CI zu PR #42](https://github.com/craexxn/ringdown-sr/actions/runs/41062609710)
  bestand am Head `9202d20`. Der neue Originalarchiv-Audit prüft 48 Fits,
  144 lokale Verläufe und 6.506 Zustände; dabei keine neue Optimierung.
- **Offen:** Verifikation des neuen freien Rekonstruktionshinweises und Übertragbarkeit;
  wissenschaftliche Formelauswahl,
  numerisches Forschungsprofil und statistischer Versuchsplan vor einer
  Leistungsstudie. Dazu die [offenen Reproduzierbarkeitsentscheidungen](docs/reproducibility_decisions.md)
  und die Grenzen des neuen Methodenplans verwenden. Hauptversuche und
  wissenschaftliche Leistungsvalidierung stehen weiterhin aus.

## Implementierter Pilot auf der abgeglichenen Basis

- Gleichmäßige Zeitachse und Generator für ein einzelnes gedämpftes
  Sinussignal: `src/ringdown_sr/signals.py`.
- Weißes Gaußrauschen mit explizitem NumPy-Zufallsgenerator:
  `src/ringdown_sr/noise.py`.
- Stationäres korreliertes AR(1)-Gaußrauschen mit analytischer Kovarianz
  und gepaarten Beispielen für gewöhnlichen und gewichteten Fit.
- Gewöhnliche MSE sowie kovarianzgewichtete Verluste und Whitening
  über eine Cholesky-Zerlegung: `src/ringdown_sr/losses.py`.
- Klassischer Fit mit bekannter Ringdown-Formel, expliziten Startpunkten
  und optionaler fester Kovarianz: `src/ringdown_sr/reference_fit.py`.
- Konfigurierbarer Kontrolllauf mit TOML-Eingabe, Ergebnisdateien,
  Diagramm und Metadaten: `src/ringdown_sr/pilot.py`.
- Reiner Kovarianzschätzer aus getrennten Hintergrundfenstern mit
  ausdrücklicher Identitätsschrumpfung und Alpha-Auswahl:
  `src/ringdown_sr/covariance_estimation.py`.
- Drei gekoppelte Referenzfits mit getrennten Hintergrundrollen und
  geschätzter Kovarianz im ausdrücklich versionierten Schema 2:
  `src/ringdown_sr/covariance_pilot.py`.
- Automatisierte Python-Tests für diese Bausteine, einschließlich
  analytischer Referenzfälle, ungültiger Eingaben und des Julia-Startwegs.
- Julia-Verlustkern mit expliziter Einheitenprüfung, festem Fenster und
  voller Kovarianz sowie separaten Julia-Tests und Python-Replay.
- Deterministische Prüfung der tatsächlichen Newton-/BFGS-Konstantenanpassung
  im Julia-Backend mit unabhängigen Referenzen und Python-Nachrechnung.
- Festgelegte Python-/Julia-Umgebung und automatische GitHub-Prüfungen.
- Isolierte Laufzeitvorbereitung ohne zusätzliche Conda-Python-Umgebung;
  Prüfung gleichzeitiger Starts bei fremder aktiver CondaPkg-Sperre.
- Isolierter Adapter für einzelne freie PySR-Suchläufe mit vollständigem
  Baumexport, festem Kovarianzkontext und Verlust-Replay aller Pareto-Kandidaten.
- Vollständiger Schema-3-Pilot: drei freie SR-Arme auf denselben binären
  Eingaben, gemeinsame nachgelagerte Diagnosen und klassische Referenzen.
- Unabhängige [Alias-/Phasenreferenzen](docs/alias_references.md) für
  vorgegebene Ausdruckspaare, einschließlich kleiner Amplituden und Randfälle.
- Begrenzter [Strukturerkenner](docs/structure_recognition.md) für exportierte
  Ringdown-Ausdrücke mit exakter rationaler Koeffizientenextraktion.
- Separate [Parameter-/Aliasdiagnose](docs/parameter_diagnostics.md) mit
  rationalen π-Einschlüssen, abgesicherten Rundungsentscheidungen und
  Vorhersagevergleich gegen den unveränderten Originalbaum.

Ein vollständiger kleiner Durchlauf mit bekanntem Formansatz ist vorhanden.
Die Kovarianzschätzung ist mit Hintergrundrollen, drei Fit-Varianten und
Exporten integriert. Der [Julia-Verlustkern](docs/julia_loss_kernel.md) ist als erster
Baustein der freien Suche ergänzt. Die [Konstantenoptimiererprüfung](docs/constant_optimization.md)
ergänzt die tatsächlichen Backend-Pfade bei fest vorgegebenen Strukturen.
Der [freie Suchadapter](docs/symbolic_adapter.md) startet einzelne Arme in
neuen Prozessen. Der [Schema-3-Pilot](docs/symbolic_pilot.md) verbindet sie
mit der bestehenden Datenerzeugung und speichert alle Kandidaten sowie
gemeinsame Diagnosen. Die statistische Leistungsbewertung steht noch aus.
Die wissenschaftlichen Hauptversuche und ihre Auswertung haben noch
nicht begonnen.

Details zum aktuellen Stand: [Pilot](docs/pilot.md),
[Verlustfunktionen](docs/losses.md), [Referenzfit](docs/reference_fit.md),
[konfigurierter Durchlauf](docs/configured_pilot.md) sowie
[korreliertes Rauschen](docs/correlated_noise.md) und
[Kovarianzschätzer](docs/covariance_estimation.md) und
[Pilot mit geschätzter Kovarianz](docs/estimated_covariance_pilot.md).
Das [Portabilitätsprotokoll](docs/portability.md) enthält die bisherigen
Schema-1-Vergleiche und die neuen Schema-2-Nachweise auf Manjaro und WSL2
am selben sauberen Commit. Für Schema 3 sind auf Manjaro und WSL2 jeweils
559 bestandene Tests, beide vollständigen Audits und Diagrammanzeigen am
sauberen Commit `6ed493d` übermittelt. Zusätzliche Prüfungen bestätigen
die gespeicherte Git-Herkunft aller Stufen. Die freie SR-Suche liefert dabei
unterschiedliche Kandidatenzahlen und Verluste; die Ursache ist noch
nicht bestimmt. Ausführbarkeit und lokale Konsistenz sind bestätigt,
für diese ursprünglichen Vollprofile liegen keine rechnerübergreifend
identischen SR-Ergebnisse vor. Der spätere begrenzte
[Haswell-Vergleich](docs/symbolic_core_results.md) ist davon zu unterscheiden.
Auch der gepinnte Julia-Startweg ist lokal
unter WSL2 bestätigt. Der [PySR-Methodenentwurf](docs/symbolic_regression_method_plan.md)
wurde separat geprüft und um die Reviewpunkte präzisiert. Die freie Suche
ist im Dreiarm-Pilot integriert. Die drei Schritte der
[geplanten Parameterinterpretation](docs/parameter_interpretation_plan.md)
sind als begrenzte Strukturerkennung und separate numerisch abgesicherte
[Parameter-/Aliasdiagnose](docs/parameter_diagnostics.md) umgesetzt.
Der [lesende Export](docs/parameter_export.md) für vollständige gespeicherte Läufe ist ebenfalls umgesetzt;
wissenschaftliche Formelauswahl bleibt eine gesonderte Aufgabe.
Die [erste rauschfreie Kontrollserie auf Manjaro](docs/noiseless_control_results_manjaro_001.md)
ist vollständig übermittelt: Alle neun Zellen wurden abgeschlossen, aber keiner
der 28 exportierten Kandidaten erfüllt die festgelegten Kurvenfehlergrenzen.

## Konfigurierter Durchlauf mit gespeicherten Ergebnissen

Aus dem Projektordner:

```bash
uv run --locked ringdown-sr run configs/pilot_white.toml --output results/pilot-001
code -r results/pilot-001/plot.png
```

Der neue Ausgabeordner enthält Konfiguration, Messwerte als CSV,
Parameter und Fehlerwerte als JSON, ein Diagramm und Metadaten mit Seed,
Zufallszuständen, Softwareversionen, Codezustand und Prüfsummen.
Bestehende Ordner werden abgelehnt; für eine Wiederholung einen neuen
Namen wie `results/pilot-002` verwenden. Lokale Ausgaben unter `results/`
werden nicht versioniert und müssen separat gesichert werden.
Der [Ergebnisindex](docs/results_index.md) ordnet die dokumentierten Versuche
ihren Ausführungsständen, Originalarchiven und Bewertungen zu. Die
[Archivierungsrichtlinie](docs/results_archiving.md) regelt einen gemeinsamen
Archivordner und eine zweite gesicherte Kopie. GitHub-Releases sind optional.
Ablageorte und Sicherung sind noch zu bestätigen; die Richtlinie allein ist
keine Sicherung.
Der Kontrolllauf braucht kein Julia/PySR und legt keine Einstellungen
oder Erfolgskriterien für die Hauptversuche fest.

Die gepaarten AR(1)-Beispiele werden genauso gestartet, mit
`configs/pilot_ar1.toml` beziehungsweise `configs/pilot_ar1_ordinary.toml`
und jeweils einem neuen Ausgabeordner. Sie erzeugen dieselben Daten und
verwenden unterschiedliche Fit-Gewichtungen. Zusätzlich wird die bekannte
Modellkovarianz als `covariance.csv` gespeichert. Das ist ein Kontrollvergleich,
kein Nachweis einer Überlegenheit aus einem Einzelversuch.

Schema 2 erzeugt die drei Fits gemeinsam und schätzt die dritte Kovarianz
aus getrennten Hintergrundfenstern. Der AR(1)-Kontrolllauf wird so gestartet:

```bash
uv run --locked ringdown-sr run configs/pilot_estimated_ar1.toml --output results/estimated-ar1-001
code -r results/estimated-ar1-001/plot.png
code -r results/estimated-ar1-001/covariance_plot.png
```

Für weißes Rauschen gibt es `configs/pilot_estimated_white.toml`.
Die Ausgabe enthält zusätzlich Hintergrundfenster, rohe/geschätzte/wahre
Kovarianzen, Alpha-Diagnosen und getrennte RNG-Rollen. Bedienung,
Konfiguration, Kennzahlen und Grenzen beschreibt die
[Schema-2-Dokumentation](docs/estimated_covariance_pilot.md).

Schema 3 startet zusätzlich drei freie PySR-Suchen mit demselben kleinen
technischen Budget. Die klassischen Referenzen liegen unter `reference/`:

```bash
uv run --locked ringdown-sr run configs/pilot_sr_ar1.toml --output results/sr-ar1-001
code -r results/sr-ar1-001/plot.png
uv run --locked python scripts/check_symbolic_pilot.py --verify results/sr-ar1-001
```

Das weiße Gegenstück heißt `configs/pilot_sr_white.toml`. Alle drei Arme
erhalten dieselben Samples; ihre Gewichtung unterscheidet sich. Das letzte
Kommando rechnet gespeicherte Verluste und Diagnosen unabhängig nach.
Aufrufe, Dateien, Suchbudget und Grenzen beschreibt die
[Schema-3-Dokumentation](docs/symbolic_pilot.md).

## Sichtbarer Demolauf

Nach der Einrichtung aus dem Projektordner:

```bash
uv run --locked python scripts/demo_reference_fit.py
```

Der Aufruf zeigt vorgegebene und geschätzte Parameter sowie Fehlerwerte
im Terminal und speichert ein Diagramm im temporären Verzeichnis.
Unter Linux/WSL kann es mit `code -r /tmp/ringdown-reference-fit.png`
geöffnet werden. Ein eigener Pfad ist mit `--output /pfad/diagramm.png`
möglich. Dieser einzelne Demofall verwendet die bekannte Formel und
ersetzt keine wissenschaftliche Bewertung oder freie PySR-Formelsuche.

## Entwicklungsumgebung

Die grundlegende Installation und ein allgemeiner PySR-Polynomtest
wurden auf einem Windows-Rechner mit Ubuntu unter WSL2 sowie auf einem
Laptop mit Manjaro Linux geprüft. Als Editor wird Visual Studio Code
verwendet, unter Windows mit WSL-Anbindung.

Gemeldete Versionen:

- Python: 3.12.14
- uv: 0.12.21
- Git: 2.53.0 unter WSL2, 2.55.0 unter Manjaro
- PySR: 2.6.0
- juliacall: 0.9.36
- Julia: 1.13.1
- SymbolicRegression: 2.5.1
- PythonCall: 0.9.36

## Bibliotheken

- NumPy und SciPy: numerische Berechnungen und Optimierung
- Matplotlib: Diagramme
- pandas: tabellarische Auswertung
- SymPy: symbolische Mathematik
- PySR: symbolische Regression mit Julia-Backend

Entwicklungswerkzeuge:

- pytest: automatisierte Tests
- Ruff: Codeprüfung und Formatierung
- ipykernel: Ausführung von Python in Jupyter-Notebooks

## Einrichtung auf einem weiteren Rechner

Voraussetzungen: Git, uv und Zugriff auf das private GitHub-Repository.
Die folgenden Befehle sind für ein Linux- beziehungsweise WSL-Terminal.

```bash
git clone https://github.com/craexxn/ringdown-sr.git
cd ringdown-sr
uv python install 3.12.14
uv sync --locked --dev --python 3.12.14
```

Programme werden aus dem Projektordner mit `uv run` gestartet.
Eine manuelle Aktivierung der virtuellen Umgebung ist nicht nötig.

## Bestehenden Rechner aktualisieren

Im Linux- beziehungsweise WSL-Terminal aus dem Projektordner zuerst
`git status` ausführen. Bei sauberem Arbeitsverzeichnis:

```bash
git switch main
git pull --ff-only
uv sync --locked --dev --python 3.12.14
```

Damit werden die übernommenen Änderungen von `main` und die festgelegten
Python-Abhängigkeiten abgeglichen. Änderungen aus offenen Pull Requests
sind auf deren jeweiligen Branches verfügbar.

## Technische Prüfungen

Die Python-Version ist in `.python-version` festgelegt.

Die folgenden Befehle werden aus dem Projektordner ausgeführt:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_environment.py
uv run --locked --python 3.12.14 python scripts/check_julia_startup.py
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_julia_loss.py
uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_symbolic_search.py
uv run --locked python scripts/check_symbolic_pilot.py --output results/ci-sr-controls-001
```

Der Umgebungscheck kontrolliert Bibliotheksimporte, Python- und
Julia-Versionen, das aktive Julia-Projekt sowie einen Julia-Rechentest.
Er prüft außerdem die tatsächliche PythonCall-Interpreterbindung und die
geladene PythonCall-Erweiterung. Der separate
[Startweg-Check](docs/julia_startup.md) prüft zwei gleichzeitige Starts bei
einer fremden aktiven CondaPkg-Sperre.
Der separate Julia-Check führt Verlustkern- und echte Konstantenoptimierer-Tests,
zehn Residualvergleiche mit dem Python-Kern sowie zwölf unabhängige
Optimierer-Nachrechnungen aus. Diese Prüfungen gehören
nicht zur pytest-Anzahl; Details stehen im
[Julia-Verlustkern](docs/julia_loss_kernel.md).

Mit `uv run --locked pytest -v` wird jeder Testfall mit seinem Ergebnis
angezeigt. Integrationstests erzeugen unter anderem temporäre Diagramme
im pytest-Verzeichnis. Für bewusst gespeicherte Ergebnisse und Diagramme
die obigen CLI-Kontrollläufe ausführen. Nur die Schema-3-Konfigurationen
starten dabei freie Formelsuchen.

Der [CI-Workflow](docs/ci.md) führt diese Prüfungen bei Code-, Test-,
Konfigurations-, Abhängigkeits- und CI-Änderungen auf Ubuntu aus.
Reine Dokumentationsänderungen erhalten schlanke Format- und lokale
Linkprüfungen; zur Laufzeit konsumierte Dokumente bleiben ausgenommen.
Manuelle und nicht eindeutig einordenbare Läufe prüfen vollständig.

Bisherige Prüfnachweise:

- Der [GitHub-Durchlauf auf `main` vom 15.10.2026](https://github.com/craexxn/ringdown-sr/actions/runs/38762123899)
  zu Commit `600e95b` ist erfolgreich abgeschlossen: Ruff-Codeprüfung,
  Formatprüfung, 121 Unit-Testfälle und Python-/Julia-Umgebungscheck.
  Dieser Nachweis stammt aus dem Stand vor Ergänzung des Referenzfits.
- Am 18.10.2026 wurden einschließlich konfiguriertem Pilot 237 Testfälle
  in der Codex-Umgebung erfolgreich ausgeführt.
- Am 19.10.2026 wurden nach Ergänzung der Build-/Laufzeitdiagnosen und
  weiterer Schutzprüfungen 244 Testfälle in der Codex-Umgebung bestanden.
- Am 19.10.2026 wurden nach Integration des AR(1)-Kontrollfalls 301 Testfälle
  in der Codex-Umgebung bestanden.
- Der Nutzer führte am 19.10.2026 auf Manjaro den weißen Kontrolllauf am
  sauberen Commit `3833a12` erfolgreich aus: 244 Tests bestanden, Diagramm
  geprüft. SHA-256 für Konfiguration, `samples.csv` und `result.json` waren
  mit dem Codex-Referenzlauf identisch. Dieser Nachweis gilt für den damaligen
  weißen Kontrollfall.
- Anschließend wurden auf Manjaro auch beide AR(1)-Beispiele erfolgreich
  ausgeführt, ihre Diagramme geöffnet und identische Eingabedaten und
  Kovarianzen innerhalb des Fit-Paars bestätigt. Die gewichteten Fehlerwerte
  wurden direkt aus den exportierten Residuen und Kovarianzen nachgerechnet.
- Auf Ubuntu unter WSL2 wurden am 19.10.2026 nach Aktualisierung auf
  `fbe9a60` 301 Tests bestanden sowie der weiße Kontrolllauf und beide
  AR(1)-Beispiele erfolgreich ausgeführt und ihre Diagramme geöffnet.
  Die ausgegebenen Kennzahlen stimmen mit Manjaro überein; bei AR(1)
  wurden Eingabegleichheit innerhalb des Paars und gewichtete Fehlerwerte
  erneut geprüft. Die abweichenden Weißrausch-Dateihashes wurden durch
  eine CPU-/OpenBLAS-Diagnose exakt nachgestellt. Umfang, Zahlenwerte
  und Grenzen stehen im [Portabilitätsprotokoll](docs/portability.md).

Bestandene Tests bestätigen die geprüften Formeln und Eingaberandfälle.
Am 20.10.2026 wurden nach Ergänzung des reinen Kovarianzschätzers und
den Korrekturen aus dem Implementierungsreview 396 Tests in der
Codex-Umgebung bestanden, davon 95 neue Tests für
Schätzung, Auswahl, Fehlerfälle und die statistische Kontrolle des rohen
Schätzers. Nach der Schema-2-Integration bestanden am selben Tag insgesamt
456 Tests, darunter 60 neue Tests für Schema, Zufallsströme und Integration.
Die Seed-Prüfung lehnt identische Anfangszustände der vier Generatoren
vor Datenerzeugung und Anlegen des Ausgabeordners ab. Beide vollständigen
Schema-2-Beispiele wurden in der Codex-Umgebung erfolgreich ausgeführt und
ihre Diagramme geprüft. Das separate Integrationsreview zu PR #16 fand
eine Seed-Überschneidung; deren Nachbesserung ist mit Commit `1fcf9fc`
übernommen. Am 20.10.2026 bestätigte der Nutzer an diesem sauberen Commit
auf Manjaro 456 bestandene Tests in 33,02 s, beide erfolgreichen
Schema-2-Beispiele und die Diagrammanzeige. Eine zusätzliche Nachrechnung
bestätigte Dateiprüfsummen, Kovarianzen, Kontroll-Scores und Fit-Verluste.
Umfang und Zahlen stehen im [Portabilitätsprotokoll](docs/portability.md).
Unter WSL2 wurden am selben Referenzcommit ebenfalls 456 Tests in 27,19 s
bestanden, beide Beispiele und alle vier Diagramme bestätigt sowie dieselben
Datei-, Kovarianz-, Kontroll-Score- und Verlustprüfungen ausgeführt.
Alpha und ausgegebene Kennzahlen stimmen mit Manjaro überein.
Ein vollständiger rechnerübergreifender Array- oder Bytevergleich ist
damit nicht belegt.
Die wissenschaftliche Validierung der Rekonstruktionsmethode benötigt
die noch ausstehenden methodischen Prüfungen und Experimente.

## Reproduzierbarkeit

- Python-Abhängigkeiten werden durch `pyproject.toml` und `uv.lock`
  beschrieben und festgelegt. Verwendet wird Python 3.12.14.
- `src/ringdown_sr/juliapkg.json` legt Julia auf Version 1.13.1 fest.
- `julia/Project.toml` und `julia/Manifest.toml` halten die direkten
  und indirekten Julia-Paketversionen fest.
- `scripts/run_python.py` ermittelt das lokale Julia-Programm,
  prüft die Pins und stellt ausschließlich die gespeicherte Paketumgebung
  bereit. PythonCall verwendet die aktuelle Python-Umgebung; CondaPkg
  läuft mit dem Null-Backend. Nur die Vorbereitung hält die
  Installationssperre; Details stehen im [Startweg](docs/julia_startup.md).
- Die lokale `.venv` wird nicht mit Git versioniert.

Die Rolle exakter Wiederholbarkeit gegenüber wissenschaftlicher Robustheit
und die vorläufige gemeinsame BLAS-Kontrolle sind im
[Entscheidungsvermerk](docs/reproducibility_decisions.md) festgehalten.
Der [wirkungsgeprüfte freie Suchlauf](docs/symbolic_repeatability.md#kontrollierte-freie-suche-mit-gemeinsamem-blas-kern)
wurde inzwischen zweimal je Rechner ausgeführt. Unter gemeinsamem Haswell-
Kern stimmen die vollständigen Fronten des eingefrorenen gewöhnlichen
Weißrauscharms auf Manjaro und WSL2 exakt überein. Der
[Befund mit Prüfgrenzen](docs/symbolic_core_results.md) dokumentiert sieben
Kandidaten je Lauf, die Nachrechnung und den historischen nativen Vergleich.
Diese Diagnose legt keine zusätzlichen Formelrestriktionen fest.

Python-Aufrufe mit PySR oder JuliaCall werden über das Startskript
ausgeführt. Beispiel aus dem Projektordner:

```bash
uv run --locked --python 3.12.14 python scripts/run_python.py -c "import pysr; print(pysr.__version__)"
```

Für eine Python-Datei wird anstelle von `-c "..."` deren Pfad angegeben.

Der Startweg wurde am 06.10.2026 auf Manjaro erfolgreich geprüft:
PySR 2.6.0, Julia 1.13.1, SymbolicRegression 2.5.1 und PythonCall 0.9.36.
Die oben verlinkte technische CI zu `600e95b` bestätigte ihn außerdem
auf Ubuntu; eine spätere reine Dokumentations-CI ist kein neuer Startwegnachweis.
Am 20.10.2026 bestätigte der Nutzer den Startweg außerdem lokal unter WSL2:
`Technical environment check passed.`, Python 3.12.14, PySR 2.6.0,
Julia 1.13.1, SymbolicRegression 2.5.1 und PythonCall 0.9.36;
geladen wurde `julia/Project.toml` im Projektordner.
Der separate Nachweis ist im [Portabilitätsprotokoll](docs/portability.md)
dokumentiert und bestätigt keinen bereits implementierten SR-Adapter.

Der frühere allgemeine PySR-Test rekonstruierte `y = x² + 2x + 1`
auf dem Manjaro-Laptop als `x(x + 2) + 1` mit einem mittleren
quadratischen Fehler von ungefähr `3,94 × 10⁻³³`. Dieser Test ist
eine Installationsprüfung und keine Ringdown-Rekonstruktion.
