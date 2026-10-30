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

Initialer Sicherungspunkt: Plan und Merge sind geprüft; die fachliche
Implementierung beginnt. Noch kein Implementierungs-PR geöffnet.
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

Die vorhandenen `noiseless_control.py`, `run_noiseless_control.py`,
`symbolic.py`, `parameters.py` und deren Tests lesen. Danach den reinen
Diagnosekern mit unabhängigen Referenzen implementieren und testen.
Die Integration des tatsächlichen Julia-Backends ist noch offen.

## Prüfungen dieses Sicherungspunkts

Planhash und Merge geprüft. Noch keine neuen Implementierungstests und
keine neuen Suchläufe ausgeführt. Der volle CI-Nachweis aus PR #36 und die
schlanke Doku-CI aus PR #37 gehören zur jeweiligen Grundlage.
