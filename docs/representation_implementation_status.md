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

Schritt 1 ist implementiert und lokal geprüft:

- `src/ringdown_sr/representation_control.py`: feste neun Zellen,
  schreibgeschützte Koordinaten, getrennte Such-/physikalische Diagnosen,
  physikalische Replays, Bedingungenübersichten und Seed-Differenzen.
- `tests/test_representation_control.py`: 23 Referenz-/Fehlerfälle.
- Der neue Plan ist zusätzlich als eingefrorenes Dokument in der vollen
  CI-Ausnahme erfasst; der entsprechende CI-Gegenfall ist ergänzt.
- Noch kein Implementierungs-PR geöffnet. Worker, Treiber und die
  tatsächliche Julia-Profilprüfung sind noch nicht implementiert.

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

## Nächster konkreter Schritt

Schritt 2: einen eng begrenzten Worker-Wrapper und eine technische
Options-/Pluginprüfung ohne Fit implementieren. Bestandspfade der Suche
sollen ihre unveränderten Vorgaben behalten. Anschließend den separaten
Treiber analog zu `scripts/run_noiseless_control.py` anbinden.

Bereits im gepinnten Backendquellcode verifiziert:

- `SymbolicRegression 2.5.1`, `src/Options.jl`, erzeugt Defaultplugins aus
  den beiden Häufigkeitsschaltern.
- `src/plugins/AdaptiveParsimony.jl`:
  `default_adaptive_parsimony_plugin` liefert bei `False/False` kein Plugin,
  bei `True/True` einen `AdaptiveParsimonyPlugin` mit `tournament=true`
  und `mutation_acceptance=true`. Weitere Defaultplugins müssen gleich bleiben.
- Es genügt daher nicht, nur die exportierten Boolfelder zu prüfen oder
  das komplette Pluginfeld ungeprüft aus einer Signatur auszublenden.
  Tatsächliche Objekte/Felder sind vorab und nach jedem Worker zu verifizieren.

Der bestehende Worker nimmt nur `format` und `budget` in `request.json`
an. Eine mögliche Integration ist ein eigener kontrollierter Wrapper mit
strengem Profilmanifest; keine frei übergebenen Optionsüberschreibungen.
Die vorhandenen Seed-, Verlust-, Manifest- und Haswell-Prüfungen müssen
auch im neuen Pfad erhalten bleiben.

## Prüfungen dieses Sicherungspunkts

64 fokussierte Python-Tests bestanden: 23 für den neuen Diagnosekern und
41 für die CI-Auswahl. Ruff bestanden. Geprüft sind unter anderem beide
Alias-Gegenfälle einschließlich eines zusätzlichen Zwischenzeitpunkts,
Vorzeichen/Phase, nicht unterstützte gute Kurven, fehlgeschlagene Replays,
Über-/Unterlauf, fehlende Seedpaare und gesperrte Zusammenfassungen.

Validierung unter Windows mit vorhandener gesperrter Python-3.12.14-Umgebung,
lokalem Quellpfad und `uv`; keine Abhängigkeit oder Lockdatei geändert.
Eine frische Offline-Installation war mangels SciPy-Wheel im Cache nicht
möglich. Noch kein lokaler Julia-Lauf und keine neuen Entwicklungs-Suchen.
Die vollständige Integrations-CI steht für den späteren Implementierungs-PR
aus. Der volle Nachweis aus PR #36 gehört nur zur unveränderten Grundlage.
