# Freie SR-Suche unter gemeinsamem OpenBLAS-Kern

Prüfstand: 26.10.2026. Beide vom Nutzer übermittelten Haswell-Archive wurden
gemeinsam an ihren tatsächlichen Dateibytes ausgewertet und unabhängig in
Python nachgerechnet. Die Originalarchive werden separat gesichert; sie
sind nicht Bestandteil dieses Repositorys. Ein eigener Zugriff auf die
beiden Rechner oder eine erneute Julia-Suche fand bei der Auswertung nicht
statt. Pickle- und Julia-Serialisate wurden nur gehasht, nicht geladen.

## Beobachtetes Ergebnis

Alle vier freien Suchläufe liefern dieselbe vollständige geordnete Front:

| Rechner | Wiederholung | Kandidaten | Gewählte Komplexität | Gewöhnlicher Trainingsverlust |
| --- | ---: | ---: | ---: | ---: |
| WSL2 | 1 | 7 | 12 | 0.054937397171508001 |
| WSL2 | 2 | 7 | 12 | 0.054937397171508001 |
| Manjaro | 1 | 7 | 12 | 0.054937397171508001 |
| Manjaro | 2 | 7 | 12 | 0.054937397171508001 |

Die binären Bäume einschließlich Float64-Konstanten, Komplexitäten,
Verluste und sämtliche Vorhersage-/Residualbits sind gleich. Die ganze
Front wurde verglichen, nicht nur ihre Länge oder das gewählte Ergebnis.
Alle übrigen Inhalte von `result.json` stimmen nach Ausnehmen ausschließlich
von `timing_seconds` ebenfalls exakt überein. Die gesamten Archive und
Dateibytes sind wegen Laufzeiten, Zeitstempeln und Rechnerpfaden nicht
bytegleich. Diese Unterschiede wurden nicht mit Frontunterschieden vermischt.

Die gemeinsame Front hat folgende Komplexitäten und gewöhnlichen Verluste:

| Komplexität | Trainingsverlust |
| ---: | ---: |
| 1 | 0.07559806001305705 |
| 3 | 0.07556551820292692 |
| 4 | 0.07554387133030697 |
| 5 | 0.06473638511734567 |
| 7 | 0.06473615963153709 |
| 8 | 0.06002434399962005 |
| 12 | 0.054937397171508 |

Gewählt wird weiterhin der minimale Trainingsverlust, bei Gleichstand die
kleinere Komplexität. Der gespeicherte nullbasierte Auswahlindex ist `6`.
Diese technische Auswahl ist keine unabhängige wissenschaftliche
Formelauswahl und kein Nachweis physikalischer Ringdown-Identifikation.

## Bedingungen und Herkunft

| Merkmal | Festgehaltene Vorgabe |
| --- | --- |
| Sauber protokolliertes Prüfprojekt | `6ed493d2e8fb3a845dd921bd99a620feb8b8850a` |
| Ausgeführte Diagnosewerkzeuge | Commit `6b3d156a9daecabc4f42d5b940b065a8dda5bc19` aus PR #30 |
| SR-Arm | Gewöhnlicher Weißrauscharm; keine Kovarianzgewichtung |
| Daten | Dieselben neun Quelldateien; je 128 eingefrorene Float64-Zeit- und Messwerte |
| Python-/Backend-Seed | `20261020` / `465951028` |
| Suchbudget | 10 Iterationen, 2 Populationen, Populationsgröße 32, 50 Zyklen je Iteration |
| Kernkontrolle | NumPy, SciPy und Julia tatsächlich jeweils OpenBLAS/Haswell |
| Poolvorgaben | `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` jeweils `1` |
| Software | Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1, PySR 2.6.0, Julia 1.13.1, SymbolicRegression 2.5.1 |

Der externe Werkzeugcommit ist vom Commit des installierten Prüfprojekts
zu unterscheiden. Die tatsächlich ausgeführten beiden Diagnosequellen
stimmen byteweise mit dem Werkzeugcommit überein. Ihr Einstieg verwendet
weiterhin die vorhandene Suche und die bestehenden Julia-Adapter des
Prüfprojekts. Die Wirkungskontrolle umschließt die vorhandenen
Umgebungsaufnahmen; sie verändert weder Operatoren, Einheitenregeln,
Größenlimit und Verlust noch Seeds oder nominelles Budget. Sämtliche
aufgezeichneten PySR-Parameter und Backendoptionen stimmen bis auf
`output_directory` mit den ursprünglichen Vorgaben überein.

Die Kontrollaufnahmen bestätigen die geladenen NumPy-, SciPy- und
Julia-Pools unmittelbar vor `fit` und nach dem Ergebnisexport. Die
Kontrolldateien sind gehasht und stimmen mit den regulären Suchmetadaten
überein. Eine gesetzte Umgebungsvariable allein wurde nicht als Nachweis
akzeptiert. Poolaufnahmen nennen konfigurierte Limits zu diesen Zeitpunkten,
keine kontinuierlich gemessene Zahl aktiver Threads.

Die gleichen Seeds sind dokumentierte Startvorgaben, keine vollständigen
Julia-RNG-Checkpoints. Auch der gemeinsame Kernname vereinheitlicht nicht
sämtliche CPU-, JIT-, GC- und Systembibliothekseigenschaften.

## Verhältnis zu den vorherigen Diagnosen

Die früheren Thread-Kontrollläufe hatten bereits dieselben eingefrorenen
WSL2-Eingaben und Poollimits 1 verwendet. Ihre Eingaben, Herkunft, Seeds,
Budgets und Suchvorgaben wurden erneut gegen die neuen Pakete geprüft:

| Kernwahl | WSL2: Kandidaten / gewählte Komplexität / MSE | Manjaro: Kandidaten / gewählte Komplexität / MSE |
| --- | --- | --- |
| Bisher automatisch | 7 / 12 / 0.054937397171508 | 11 / 20 / 0.06217788927127304 |
| Jetzt bestätigt Haswell | 7 / 12 / 0.054937397171508 | 7 / 12 / 0.054937397171508 |

Zuvor meldete WSL2 Haswell/Haswell/Zen für NumPy/SciPy/Julia, Manjaro
dreimal SkylakeX. Die alleinige Einführung der Poollimits 1 hatte die
beiden Fronten nicht vereinheitlicht. Unter Haswell stimmt die neue
Manjaro-Front nun mit der unveränderten WSL2-Front überein.

`source_matches_first_signature=true` auf Manjaro bezieht sich auf die
gemeinsam eingefrorene ursprüngliche WSL2-Armausgabe. Es behauptet keine
Gleichheit mit dem früheren nativen Manjaro-Lauf mit elf Kandidaten.

Die [gepaarten festen Kontrollen](fixed_numerics_probe.md#übermittelter-haswell-vergleich-vom-26102026)
lieferten unter einem gemeinsamen Werkzeugstand frische Basis- und
Haswell-Läufe auf beiden Rechnern. Die Basis-Ergebnisdateien reproduzierten
jeweils die vorherigen festen Ergebnisse; unter Haswell wurden alle acht
festen Fälle einschließlich ihrer gespeicherten Optimiererzustände bytegleich.

**Grenze des freien Vergleichs:** Seine nativen Gegenbefunde stammen aus
den früheren Wiederholungspaketen mit dem damaligen Diagnosetreiber.
Die neuen freien Pakete enthalten Haswell-Läufe; eine frische gepaarte
freie Baseline mit demselben umschlossenen Einstieg wurde nicht ausgeführt.
Der erste intern abweichende Schritt der ursprünglichen freien Suche ist
nicht vollständig aufgezeichnet. Es wird deshalb weder eine einzelne
BLAS-Operation als alleinige Ursache benannt noch eine Erklärung sämtlicher
sechs historischer Schema-3-Arme behauptet.

Der beobachtete Befund bleibt: Unter der bestätigten gemeinsamen Kernwahl
sind die vollständigen freien Fronten dieses eingefrorenen Arms auf den
beiden Geräten gleich. Zusammen mit den gepaarten festen Kontrollen grenzt
dies den numerischen Einfluss konkret ein.

## Umfang der unabhängigen Nachrechnung

Die Auswertung hat die Berichtsfelder neu aus den Artefakten abgeleitet:

- 98 Prüfsummenvergleiche für alle durch die äußeren Manifeste erfassten Dateien.
- Zusätzlich 60 Vergleiche gegen die vier inneren Worker-Manifeste und
  14 Vergleiche für die sieben konsumierten Originaldateien je Paket.
  Diese Zählungen überlappen; sie sind keine Zahl verschiedener Dateien.
- 12 Herkunftsmomentaufnahmen mit identischem protokolliertem sauberem
  Referenzcommit und gleichen Projekt-, Python-Quell- und Adapter-Prüfsummen;
  die zugehörigen weiteren Eltern-/Worker-Angaben stimmen ebenfalls überein.
- 40 einzelne Worker-Poolbeobachtungen vor und nach den Suchen sowie
  gesondert die Elternprozess-Kontrollen.
- Neuaufbau der Frontsignaturen aus Bäumen, Komplexitäten, hexadezimalen
  Float64-Verlusten und Hashes der Vorhersage-/Residualbits.
- 28 unabhängige Kandidaten-Replays: sieben Kandidaten in vier Läufen.
  Operatorzuordnung, ursprüngliche binäre Reihenfolge und Knotenanzahl
  wurden separat geprüft. Die Knotenanzahl stimmt mit der Komplexität überein.
- 56 erneut geprüfte innere Dateiprüfsummen der vier früheren nativen
  Thread-Kontrollläufe sowie deren Eingaben, Herkunft und Suchvorgaben.

Die eigene skalare Python-Auswertung liefert maximal
`1.1102230246251565e-16` Abweichung von den gespeicherten Julia-Vorhersagen,
normiert auf die gemeinsame maximale Amplitude ohne feste Untergrenze.
Bei den Komplexitäten 8 und 12 bleibt eine minimale Differenz zwischen
dieser eigenen Auswertung und Julia. Die eigene Nachrechnung ist damit
nicht durchgängig bitgleich; die gespeicherten Ergebnisse der vier
Suchläufe sind hingegen untereinander bitgleich.

Die gespeicherten Residuen sind bitgleich mit `observed - prediction`.
Für die unabhängige Verlustreferenz wurden ihre exakten rationalen
Float64-Werte quadriert, summiert und durch 128 geteilt. Nach abschließender
Rundung der Referenz auf Float64 liegt der produktive Verlust höchstens
zwei ULP entfernt, relativ maximal `4.287491839739502e-16`. Julia-Reimport-
und Python-Verluste sowie die Rechnung mit eigenen skalaren Vorhersagen
bestehen die Kontrolle ebenfalls.

Die Vorhersageprüfung verwendet `rtol=1e-12` und normiertes `atol=1e-14`.
Für die Verlustnachrechnung gilt `rtol=64*eps(Float64)`, `atol=0`.
Dies sind numerische Konsistenzprüfungen. Die exakte Gleichheit zwischen
den Geräten wurde davon getrennt an den Float64-Darstellungen geprüft;
statistische Erfolgsschwellen werden damit nicht festgelegt.

## Separat gesicherte Primärnachweise

| Archiv | SHA-256 |
| --- | --- |
| `sr-free-haswell-wsl2-001.tar.gz` | `1442cbea82b6b80c6de9533ceb5bc2a620e1fb3500ee1524529c36c1f5c98ee3` |
| `sr-free-haswell-manjaro-001.tar.gz` | `37d8b1b4d1cc12c9dd7e487d1763a212283a9a3f92c62cdef70ff6be7bdfa94e` |
| `sr-core-control-wsl2-001.tar.gz` | `5826725c95499b498f9bc6c0a9935c4cbf7d97f2f63d14b81aad05c85813d114` |
| `sr-core-control-manjaro-001.tar.gz` | `bd2dff7fda69a4124ca8736eb101c32809e9a770cdfd7b02b2e514a745ba8b4d` |
| `sr-repeatability-wsl2-threads1-001.tar.gz` | `7f63a075c2a95226d320fa6a6a204481c6038fd3ca6c837f9bcbb7f371bf63d7` |
| `sr-repeatability-manjaro-threads1-001.tar.gz` | `48ea1cd0efb6599378303ea1d77c42b3193e9361ef5799e2697b8c3fa841341b` |

Die tatsächlichen Werkzeug-SHA-256 sind
`e12fe20a6f0cd4f900eb20ee49c40b8c0abdeaf833ba34e3026f46b7091e9728`
für `driver.py` und
`de06bb96e45b69df3b1c749f926f1be4426580127c43e8eec017f8c4ce891066`
für `probe_symbolic_numerics.py`.

Eine ausführliche Auswertung liegt separat als
`SR_Freie_Suche_Haswell_Manjaro_WSL2_2026-10-26.md` vor. Die obigen Angaben
dokumentieren die ausgeführten Prüfungen; diese Dokumentation startet
selbst keine neuen Suchen oder vollständigen Tests.

## Methodische Einordnung und Reviewumfang

Geprüft ist ein gewöhnlicher Weißrauscharm mit einer Datenrealisierung,
einem Suchseed und einem Budget auf zwei Geräten. AR(1), die beiden
Kovarianzgewichtungen, weitere Seeds und weitere Plattformen wurden in
dieser freien Intervention nicht untersucht. Wissenschaftliche
Leistungsbewertung, Generalisierung und Parameteridentifikation bleiben offen.

Die Frage, ob exakte Ergebnisgleichheit erforderlich ist und ob die
Kernvorgabe das Modell einschränkt, ist im
[Entscheidungsvermerk](reproducibility_decisions.md) festgehalten. Haswell
bleibt eine explizite Diagnosevorgabe. Das spätere numerische Referenzprofil
und Robustheitskontrollen werden vor einer Leistungsstudie festgelegt;
der mathematische Suchraum wird durch diesen Befund nicht geändert.

Das anschließende Review soll insbesondere prüfen:

1. Unveränderte Daten, Seeds, Suchvorgaben und Verlustfunktion sowie die
   tatsächliche Kernkontrolle vor und nach der freien Suche.
2. Trennung exakter Ergebnisgleichheit von toleranzbasierten eigenen Replays,
   Laufzeitunterschieden und bloß gleich gerundeten Terminalwerten.
3. Herkunft der nativen Gegenbefunde, unterschiedliche Diagnosetreiber und
   die oben ausdrücklich begrenzte kausale Aussage.
4. Reichweite eines einzelnen Arms und Seeds sowie die weiterhin offene
   Entscheidung zum späteren Forschungsprofil.

Für eine eigene Nachrechnung des freien Haswell-Befunds benötigt das Review
die beiden `sr-free-haswell-...`-Archive. Für den gepaarten festen Vergleich
und den historischen nativen Vergleich zusätzlich die jeweils benannten
Archivpaare. Ohne Einsicht in diese Dateien sind diese Teile übermittelte
Nachweise; eine neue unabhängige Artefaktprüfung darf dann nicht behauptet
werden. Die Prüfung des Diagnosecodes ist davon getrennt möglich.
