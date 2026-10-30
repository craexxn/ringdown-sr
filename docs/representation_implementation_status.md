# Fortsetzungsstand: Zeitdarstellungs-Kontrolle

Stand: 30.10.2026. Diese Datei dokumentiert den Implementierungsfortschritt;
sie ist kein Ergebnisbericht und keine Freigabe für Suchläufe.

## Verbindliche Grundlage

- Repository: `craexxn/ringdown-sr`.
- Basis: Merge von PR #37, Commit `311f87d2df9e47d3e326f24709b8085569f7b5f3`.
- Arbeitsbranch: `codex/representation-control`.
- Freigegebener [Methodenplan](search_representation_plan.md), SHA-256:
  `16cfe818c312fb5bb0a6c594505ad76ba41e41bd7f4a37decc245677c6b8ad86`.
- Der ältere [Kontrollplan](noiseless_control_plan.md) und sein Hash bleiben
  unverändert. Keine neuen Entwicklungs-Suchläufe wurden gestartet.

## Arbeitsstand

Schritt 1 ist implementiert und lokal geprüft. Schritt 2 ist als noch
unvollständig geprüfter Entwurf gesichert; die Ausführungsumgebung wurde
während der Arbeit nicht mehr verfügbar.

- `src/ringdown_sr/representation_control.py`: feste neun Zellen,
  schreibgeschützte Koordinaten, getrennte Such-/physikalische Diagnosen,
  physikalische Replays, Bedingungenübersichten und Seed-Differenzen.
- `tests/test_representation_control.py`: 23 Referenz-/Fehlerfälle.
- Der neue Plan ist zusätzlich als eingefrorenes Dokument in der vollen
  CI-Ausnahme erfasst; der entsprechende CI-Gegenfall ist ergänzt.
- Noch kein Implementierungs-PR geöffnet; keine Suchfreigabe.
- Worker- und Optionsvorprüfung sind als Entwurf angelegt. Der eigentliche
  Kontrolltreiber und die tatsächliche Julia-Ausführung sind noch offen.

Zwischenstände werden auf diesem Branch gesichert, damit Teiländerungen
nicht bei jedem Sicherungspunkt die vollständige CI starten.

## Umsetzung in fortsetzbaren Schritten

1. Reine Koordinaten-/Parameterabbildung, neun feste Zellen, vergleichbare
   Kurvendiagnosen und Differenzen zur frischen Baseline je Seed.
2. Eng begrenzte Suchprofile mit unveränderten Bestandspfaden; tatsächliche
   Backend-/Pluginunterschiede der Häufigkeitsschalter vorab verifizieren.
3. Neuer Treiber mit Quell-/Plan-/Daten-/Workerprüfung, Haswell-Kontrolle,
   unveränderter Auswahl, Teilberichten und Abbruch ohne Ersatzläufe.
4. Referenz- und Fehler-Injektionstests, Einbindung in technische CI sowie
   Bedienungsdokumentation. Neuer Laufzeitplan muss in die volle CI-Ausnahme.
5. Erst nach passenden Prüfungen einen konkreten Implementierungs-PR öffnen.
   Zusammenführung nach `main` erfolgt durch den Nutzer.

## Anforderungen, die beim Fortsetzen erhalten bleiben müssen

- Drei Bedingungen: `baseline`, `time_stretch` mit Faktor 32 und
  `complexity_frequency` mit beiden Schaltern gemeinsam aktiv. Keine Kombination.
- Drei bekannte Entwicklungsseeds, 200 Iterationen je frischer Zelle;
  zyklische Reihenfolge aus dem Plan. Keine Budget-/Toleranzänderung.
- Suche erhält nur jeweilige Zeitkoordinate und unveränderte Beobachtungen.
  Wahrheit, Diagnosepunkte und konstruierte Referenzbäume bleiben außerhalb.
- Sämtliche Kandidaten und Originalauswahl erhalten; Residuen/MSE aller
  Kandidaten prüfen, bevor die gespeicherte Auswahl akzeptiert wird.
- Ursprüngliche Suchdiagnosen getrennt von physikalischen Angaben;
  fehlende/fehlgeschlagene Replays und Umrechnungen verhindern positive Marker.
- Quellen und Daten abschließend erneut prüfen; bei Fehlern sämtliche
  Zusammenfassungen und Seed-Differenzen sperren. Teilstände erhalten.
- KI-basierte Reviews gezielt, keine automatische zusätzliche Nachreviewrunde.

## Gesicherter Entwurf für Schritt 2

- `src/ringdown_sr/representation_profiles.py`: strikt erlaubte Profile,
  unveränderte gewöhnliche Vorgaben mit zwei Häufigkeitsschaltern und einer
  gemeinsamen Verifikationshülle um den bestehenden numerischen Callback.
  Tatsächliche Felder werden erst nach Einzelprüfung für die alten 29
  Backendverträge normalisiert; Originalfelder bleiben unverändert.
- `julia/src/RepresentationProfiles.jl`: genuine Options-Prototypen,
  Pluginaufnahmen und native Prüfung vor der ersten Verlustauswertung.
  Backend-spezialisierte Optionskopien werden erneut geprüft. Die Guard
  konstruiert während der Suche keine Prototypen und verbraucht keinen RNG.
- `scripts/run_representation_worker.py`: verwendet später eine benachbarte
  `driver.py`-Kopie des unveränderten `repeat_symbolic_arm.py`. Direkter
  Aufruf aus `scripts/` ist noch kein unterstützter Suchbefehl.
- `scripts/check_representation_backend.py`: Entwurf für neun echte
  Optionsobjekte ohne Fit/Suche/Optimierung, mit Launcher- und Haswellprüfung.
- `tests/test_representation_profiles.py`: 22 Python-Fälle für
  Profileinschränkungen, alle Seeds, erhaltene Felder und manipulierte Angaben.

Die zusätzliche absolute Prüfung der strukturierten Pluginfelder
(`validate_plugin_records`) wurde zuletzt ergänzt. Für diesen letzten
Zusatz und die über den Connector wiederhergestellten Entwurfsdateien ist
nach dem Umgebungsausfall **noch kein erneuter Test-/Formatlauf erfolgt**.
Die Julia-Datei und der Worker sind insgesamt noch nicht ausgeführt.
Diese Dateien sind ein Arbeitsstand, kein fertig verifizierter Suchpfad.

## Nächster konkreter Schritt

1. Diesen Branch in einer verfügbaren Ausführungsumgebung laden.
2. Ruff/Formatierung und die fokussierten Python-Tests erneut ausführen;
   Tests für die neu ergänzte absolute Pluginfeldprüfung hinzufügen.
3. Die Optionsvorprüfung mit tatsächlichem gepinntem Julia ausführen,
   ohne Fit/Suche. Transitive Optim-/LineSearches-Abhängigkeiten werden
   über `SymbolicRegression.ConstantOptimizationModule` geladen.
4. Neuen Treiber `scripts/run_representation_control.py` implementieren.
   Er muss die drei Runtime-Dateien `driver.py`, Probe und Profilworker
   kopieren, strikt passende Profilmanifeste vor Workerstart schreiben und
   den vorhandenen isolierten Launcher/Prozessabbruchpfad wiederverwenden.
5. Preflight vor den neun Zellen starten; echte Plugins und alle absoluten
   Seed-/Optionsvorgaben je Zelle verifizieren. Zusätzlich zu den alten
   Quelldateien Profil, native Verifikationsdatei und Julia-Kopie gegen das
   Workermanifest und nachträglich gegen ihre konsumierten Bytes prüfen.
6. Residuen/MSE aller Kandidaten und Originalauswahl prüfen. `_candidate`
   muss die Suchzeiten und `FS/alpha` erhalten. Neue Diagnosen verwenden
   physikalische Zeiten mit vollständiger Auswertung `q(alpha*t)`.
7. Vollständige Berichte, Seed-Differenzen, Abbruch-/Fehler-Injektionstests,
   CLI-Dokumentation und vollständige Integrations-CI ergänzen. Erst dann
   einen konkreten Implementierungs-PR öffnen.

Der Profilworker speichert Callbackaufrufe während Fit getrennt vom
Gesamtzähler: Der bisherige Worker führt nach dem Fit eine zusätzliche
Nullkurvenauswertung aus. Dies darf nicht als weitere Fitaktivität erscheinen.

## Bereits geklärte Backendverträge

Gepinnte Quellen: SymbolicRegression 2.5.1, `src/Options.jl` und
`src/plugins/{AdaptiveParsimony,SimulatedAnnealing,AdaptiveMutationWeights}.jl`.

- `False/False`: kein adaptives Parsimony-Plugin.
- `True/True`: zusätzlich `AdaptiveParsimonyPlugin` mit
  `tournament=true`, `mutation_acceptance=true`.
- Beide Fälle behalten `SimulatedAnnealingPlugin` und
  `AdaptiveMutationWeightsPlugin`. Ihre konkreten Felder werden mitgeprüft.
- Das komplette Pluginfeld darf nicht ungeprüft aus Signaturen verschwinden.
  Die tatsächliche Julia-Repräsentation und der gemeinsame Callbackname sind
  vor einer Integration noch anhand des echten Backends zu bestätigen.

## Prüfstand und Einschränkungen

Vor dem Umgebungsausfall bestanden **86 fokussierte Python-Tests**:
23 Diagnosekern-, 22 Profil- und 41 CI-Auswahlfälle. Ruff/Formatierung waren
für den damaligen Python-Stand bereinigt. Die letzte Ergänzung der absoluten
Pluginfeldprüfung und der wiederhergestellte Entwurf wurden nicht nachgetestet.

Der gesonderte erste Codecheckpoint `91f95e2` enthält den mit 64 Tests
geprüften Diagnose-/CI-Kern. Der nachfolgende Sicherungspunkt enthält
zusätzlich den ausdrücklich ungeprüften Restentwurf.

Validierung zuvor unter Windows mit vorhandener gesperrter
Python-3.12.14-Umgebung, lokalem Quellpfad und `uv`; keine Abhängigkeit
oder Lockdatei geändert. Eine frische Offline-Installation war mangels
SciPy-Wheel im Cache nicht möglich. Derzeit ist keine nutzbare native
Ausführungsumgebung verfügbar. Kein lokaler Julia-Lauf und keine neuen
Entwicklungs-Suchen wurden ausgeführt. Die vollständige Integrations-CI
steht für den späteren Implementierungs-PR aus.
