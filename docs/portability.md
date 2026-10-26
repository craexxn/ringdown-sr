# Lokaler Portabilitätscheck des Piloten

Prüfstand: 26.10.2026. Der Schema-1-Kontrollvergleich vom 19.10.2026
wurde auf einem Manjaro-Laptop und einem Windows-Rechner mit Ubuntu unter
WSL2 ausgeführt. Für Schema 2 sind inzwischen beide Rechner am selben
Referenzcommit geprüft. Für Schema 3 sind Manjaro und WSL2 einschließlich
der gespeicherten Git-Herkunft am selben Referenzcommit bestätigt. Die
freien SR-Suchergebnisse der ursprünglichen Vollprofile unterscheiden sich
zwischen diesen Rechnern. Die spätere Haswell-Kontrolle bestätigt gleiche
freie Fronten für einen einzelnen eingefrorenen Weißrauscharm; sie ersetzt
nicht die ursprünglichen Vollprofil-Nachweise.
Die historischen Nachweise beruhen auf den vom Nutzer übermittelten
Terminalausgaben und Diagrammbestätigungen sowie ergänzenden Diagnoseläufen
in der Codex-Umgebung. Neuere Diagnosepakete wurden dagegen an ihren
übermittelten Dateibytes geprüft; ihr Umfang ist im jeweiligen späteren
Abschnitt ausgewiesen. Die lokalen Ergebnisdateien wurden nicht in dieses
Repository übernommen und müssen separat gesichert werden.

## Schema 1 vom 19.10.2026: Umfang und Codezustand

Geprüft wurden der konfigurierte Referenzfit mit bekannter Ringdown-Formel,
sein Ergebnisexport und die Anzeige von `plot.png` für drei Kontrollfälle:

| Konfiguration | Rauschmodell | Fit-Gewichtung |
| --- | --- | --- |
| `configs/pilot_white.toml` | Weißes Gaußrauschen | `known_white` |
| `configs/pilot_ar1.toml` | Stationäres AR(1)-Gaußrauschen | `known_covariance` |
| `configs/pilot_ar1_ordinary.toml` | Dasselbe AR(1)-Modell | `ordinary` |

Alle drei Kontrollläufe meldeten auf beiden Rechnern `Status: success`;
die zugehörigen Diagramme wurden geöffnet und vom Nutzer bestätigt.

Die Code- und Testnachweise haben unterschiedlichen Umfang:

- Manjaro, weißer Kontrollfall: sauberer Commit `3833a12`, 244 bestandene
  Tests in 7,74 s. Konfiguration und beide unten genannten Ergebnisdateien
  stimmten bytegenau mit dem Codex-Referenzlauf überein.
- Manjaro, spätere AR(1)-Läufe: erfolgreiche Läufe und Daten-/Fehlervergleich
  wurden bestätigt. Ihr eigener Git-Metadatensatz und ein neuer vollständiger
  Testlauf wurden nicht separat übermittelt; sie werden hier nicht aus dem
  älteren Weißrausch-Nachweis abgeleitet.
- WSL2: Aktualisierung auf `fbe9a605dc5d89a9beb1b46f19fece178be4a25f`
  (`main` nach PR #12), anschließend 301 bestandene Tests in 12,97 s.
  Der übermittelte Git-Metadatensatz des weißen Laufs nennt diesen Commit.
  Für die anschließend gestarteten AR(1)-Läufe wurde kein eigener
  Git-Metadatensatz übermittelt.

Der weiße WSL2-Lauf meldete `dirty: true`: Aufgeführt waren ausschließlich
unversionierte historische Julia-Dateien unter
`docs/environment/julia-2026-10-01/` und erzeugte Dateien unter
`julia/.CondaPkg/`. Änderungen an versionierten Dateien wurden nicht
gemeldet. Der Lauf ist damit kein Nachweis eines vollständig sauberen
Arbeitsverzeichnisses. Diese Dateien wurden für die Prüfung weder gelöscht
noch in den Projektstand aufgenommen.

Im WSL2-Metadatensatz stehen NumPy 2.5.3 und SciPy 1.18.1. Die beiden
geladenen OpenBLAS-Bibliotheken meldeten Versionen `0.3.31.dev` und
`0.3.34.106.0`, jeweils Architektur `Haswell` und zwölf Threads.

Diese Piloten verwenden kein Julia/PySR. Der am 20.10.2026 zusätzlich
übermittelte lokale WSL2-Prüfnachweis des festgelegten Julia-Startwegs ist
eine separate Prüfung; siehe letzter Abschnitt und
[README](../README.md#reproduzierbarkeit).

## Ergebnisordner und beobachtete Kennzahlen

Die im Vergleich verwendeten relativen Verzeichnisse waren:

| Kontrollfall | Manjaro | WSL2 |
| --- | --- | --- |
| Weiß | `results/portability-manjaro-001` | `results/portability-manjaro-001` |
| AR(1), gewichtet | `results/ar1-known-manjaro-001` | `results/ar1-known-wsl2-002` |
| AR(1), gewöhnlich | `results/ar1-ordinary-manjaro-001` | `results/ar1-ordinary-wsl2-002` |

Der Name des weißen WSL2-Ordners wurde vom früheren Befehl übernommen;
er bezeichnet in diesem Fall eine Ausführung unter WSL2. Die Daten wurden
wegen des Ordnernamens nicht verschoben oder neu berechnet.

Die Terminalausgaben auf beiden Rechnern stimmten in allen angezeigten
Stellen überein:

| Kontrollfall | Frequenz in Hz | Abklingzeit in s | Gewöhnliche MSE |
| --- | ---: | ---: | ---: |
| Weiß | 250.08257 | 0.007785405 | 0.006057622 |
| AR(1), gewichtet | 250.62609 | 0.0079656544 | 0.0057284665 |
| AR(1), gewöhnlich | 250.35745 | 0.0079046804 | 0.0057225228 |

Das sind Kontrollfälle mit einem festen Seed, keine Schätzung von
Leistungsunterschieden über viele Rauschrealisierungen. Die Metriken
beziehen sich auf die zur Anpassung verwendeten Samples.

## Daten- und Verlustkontrolle der AR(1)-Paare

Auf jedem Rechner wurden innerhalb des gewichteten/gewöhnlichen Paars
die Spalten `time_s`, `signal`, `noise` und `observed` aus `samples.csv`
sowie die exportierten Kovarianzmatrizen mit exakter Array-Gleichheit
verglichen. Beide Prüfungen bestätigten identische Eingaben innerhalb
des jeweiligen Paars. Ein vollständiger byteweiser AR(1)-Datenvergleich
zwischen den beiden Rechnern wurde damit nicht durchgeführt.

Zusätzlich wurde für beide Fits die Quadratik direkt berechnet:

```text
r = exportierte Residuen = observed - prediction
Q/N = r.T @ solve(C, r) / N
```

Dies kontrolliert den gespeicherten Wert unabhängig vom produktiven
Cholesky-Whitening. Der WSL2-Vergleich mit dem gespeicherten Feld
`metrics.known_covariance_mean_squared` verwendete
`rtol=1e-10, atol=1e-12`. Diese Toleranzen prüfen die numerische Konsistenz
zweier Auswertungswege; sie sind keine Erfolgskriterien der Hauptversuche.
Auf beiden Rechnern wurden folgende Werte bis zur ausgegebenen neunten
Nachkommastelle bestätigt:

| Fit | Nachgerechnetes Q/N |
| --- | ---: |
| Gewichtet | 0.607162556 |
| Gewöhnlich | 0.607430382 |

Beim gewöhnlichen Fit ist dies eine nachgelagerte Diagnose mit derselben
bekannten Kovarianz, kein Optimierungsziel. Die hier kleinere gewöhnliche
MSE des gewöhnlichen Fits und das kleinere Q/N des gewichteten Fits sind
mit den unterschiedlichen Zielfunktionen vereinbar. Sie belegen keine
allgemeine Überlegenheit eines Verfahrens.

## Diagnose der unterschiedlichen Weißrausch-Dateihashes

Die Konfiguration war auf beiden Rechnern bytegleich. Ihre SHA-256 war:

```text
cfe5e1924e25398aa54da07a6a924f7913b017ab4ac442ea4da20ba6f8231f36
```

Die Ergebnisdateien hatten unterschiedliche SHA-256-Prüfsummen:

| Datei | Manjaro / ursprüngliche Codex-Referenz | WSL2 |
| --- | --- | --- |
| `samples.csv` | `98dd727b986cdffe8f02bd7e2ae8e91ad3a7b32b18b03fb383b1d8a3885b2c81` | `054ba13387707cca237280fb991a4d8ed314e4cbaf72f6ace2d6f45a1e61ea76` |
| `result.json` | `7112df3c39947c8df46c16a8c0e4c0c7ac8987329ea2c964eed912a8afbaf176` | `dc59b163a2d629d568e1cae83897dc025da8b235ed4d77240a93fddb660fe22d` |

Der SHA-256-Vergleich jeder als zusammenhängendes Little-Endian-`float64`
gelesenen CSV-Spalte zeigte identische Zeit- und Rauschwerte. Erste
Unterschiede traten im sauberen Signal auf, anschließend in Messdaten,
Vorhersage und Residuen. Ein anderer Dateihash allein hätte die Größe
dieser Unterschiede nicht erkennen lassen.

Ein ergänzender Codex-Diagnoselauf mit denselben Paketversionen stellte
die WSL2-Signalwerte exakt nach, nachdem AVX-512-Rechenpfade deaktiviert
worden waren. Zusammen mit `Haswell` und zwölf OpenBLAS-Threads entstanden
auch `samples.csv` und `result.json` mit exakt den oben übermittelten
WSL2-Dateihashes. Dafür wurden ausschließlich in den Diagnoseprozessen
folgende Umgebungsvariablen gesetzt:

```text
NPY_DISABLE_CPU_FEATURES=X86_V4,AVX512_ICL,AVX512_SPR
OPENBLAS_CORETYPE=Haswell
OPENBLAS_NUM_THREADS=12
```

Diese Einstellungen sind keine neue Projektvorgabe. Die Diagnose zeigt,
dass unterschiedliche numerische Rechenpfade die beobachteten Dateien
reproduzieren können; sie bestimmt nicht den isolierten Anteil jeder
einzelnen Einstellung. NumPy dokumentiert die Auswahl CPU-abhängiger
Rechenpfade und die Möglichkeit, sie für Diagnosen einzuschränken:
[CPU-Dispatch](https://numpy.org/doc/stable/reference/simd/how-it-works.html)
und [Laufzeitdiagnose](https://numpy.org/doc/stable/user/troubleshooting-importerror.html#segfaults-or-crashes).

Zwischen der ursprünglichen Codex-Referenz, deren Dateihashes Manjaro
entsprechen, und dem exakt nachgestellten WSL2-Ergebnis ergaben sich:

| Größe | Absolute Abweichung, gerundet |
| --- | ---: |
| Zeit und Rauschen | 0 |
| Sauberes Signal, maximal über alle Samples | 1.11e-16; sechs Samples betroffen |
| Messdaten, maximal über alle Samples | 5.55e-17 |
| Vorhersage und Residuen, jeweils maximal | 6.04e-13 |
| Geschätzte Amplitude | 6.40e-13 |
| Geschätzte Frequenz | 2.03e-11 Hz |
| Geschätzte Abklingzeit | 9.69e-15 s |
| Geschätzte Phase | 5.48e-13 rad |
| Gewöhnliche MSE | 2.60e-18 |

Es wurde keine Rechenroutine geändert und keine Testtoleranz gelockert,
um die ursprünglichen Hashes zu erzwingen. Der Vergleich dokumentiert
sehr kleine numerische Unterschiede statt allgemeiner rechnerübergreifender
Bitidentität.

## Aussage des Schema-1-Vergleichs

Der technische Portabilitätscheck ist für diese drei Kontrollfälle
abgeschlossen: Ausführung, Export und Diagrammanzeige funktionieren auf
beiden Rechnern; die ausgegebenen Kennzahlen stimmen überein. Die
AR(1)-Eingabegleichheit innerhalb der Vergleichspaare und die erneute
Quadratikberechnung sind bestätigt. Die abweichenden weißen Dateihashes
konnten durch eine gezielte numerische Diagnose nachgestellt werden.

Dieser historische Vergleich deckt keine statistische Leistungsbewertung,
unabhängigen Bewertungsdaten, Kovarianzschätzung/Regularisierung oder freie
PySR-Suche ab. Die inzwischen umgesetzte Schätzung und ihre Pilotintegration
haben einen eigenen Prüfstand; sie werden nicht rückwirkend durch diese
Schema-1-Läufe bestätigt.

## Schema 2 vom 20.10.2026: Manjaro und WSL2 bestätigt

Die [Pilotintegration mit geschätzter Kovarianz](estimated_covariance_pilot.md)
wurde in PR #16 separat geprüft. Das Review zu `4aae1b0` fand eine
deterministische Seed-Überschneidung; die Korrektur `5c97d64` prüft alle
vier Anfangszustände vor der Datenerzeugung. PR #16 wurde als
`1fcf9fce5b999c2344b038c0a171b60ffaf7ae73` übernommen. Die bestehenden
Beispielseeds `42` und `20261019` waren vom Fehler nicht betroffen.

Der Nutzer hat auf dem Manjaro-Laptop an genau diesem übernommenen Commit
folgende Nachweise übermittelt:

- Vollständige Testsuite: **456 bestanden in 33,02 s**.
- Beide CLI-Kontrollläufe melden `Status: success`; Signal-/Fit- und
  Kovarianzdiagramme wurden angezeigt und bestätigt.
- Beide `metadata.json` nennen den vollständigen Commit `1fcf9fce...`,
  `available: true`, `dirty: false` und `changes: []`.
- Eine zusätzliche Nachrechnung bestätigte die unten abgegrenzten
  Datei-, Kovarianz-, Score- und Fitprüfungen für beide Läufe.

Unter Windows mit Ubuntu/WSL2 wurde der Vergleich am selben Referenzcommit
in einem separaten Git-Worktree `ringdown-sr-wsl2-check-1fcf9fc` ausgeführt.
Der Nutzer übermittelte:

- Vollständige Testsuite: **456 bestanden in 27,19 s**.
- Beide CLI-Kontrollläufe mit `Status: success`; alle vier Signal-/Fit-
  beziehungsweise Kovarianzdiagramme wurden angezeigt und bestätigt.
- Für beide Läufe denselben vollständigen Commit `1fcf9fce...`,
  `available: true`, `dirty: false` und `changes: []`.
- Die erfolgreiche zusätzliche Nachrechnung im unten beschriebenen Umfang.

Die ältere aktive virtuelle Umgebung im ursprünglichen Checkout führte
zunächst zu einer uv-Warnung. uv meldete ausdrücklich, diese zu ignorieren,
und verwendete die Umgebung des Prüfordners. Für die Nachrechnung wurde
`VIRTUAL_ENV` nur im gestarteten Prozess entfernt. Die erfolgreichen Läufe
wurden wegen dieser Warnung nicht wiederholt.

Die übermittelten Ergebnisordner sind lokal und werden nicht versioniert:

| Konfiguration | Ergebnisordner auf Manjaro | Ergebnisordner im WSL2-Prüfprojekt | Alpha auf beiden |
| --- | --- | --- | ---: |
| `configs/pilot_estimated_white.toml` | `results/estimated-white-portability-001` | `results/estimated-white-wsl2-001` | 1 |
| `configs/pilot_estimated_ar1.toml` | `results/estimated-ar1-portability-001` | `results/estimated-ar1-wsl2-001` | 0.5 |

Die folgenden Terminalwerte stimmen auf beiden Rechnern in allen
übermittelten Stellen überein. Stellenzahl und Rundung entsprechen den
Ausgaben; die Testlaufzeiten sind keine kontrollierte Geschwindigkeitsstudie:

| Rauschen / Fit | Frequenz in Hz | Abklingzeit in s | Gewöhnliche MSE | Nachgerechnetes `Q_true/N` |
| --- | ---: | ---: | ---: | ---: |
| Weiß / gewöhnlich | 250.08257 | 0.007785405 | 0.006057622 | 0.605762195838 |
| Weiß / wahre Kovarianz | 250.08257 | 0.007785405 | 0.006057622 | 0.605762195838 |
| Weiß / geschätzte Kovarianz | 250.08257 | 0.007785405 | 0.006057622 | 0.605762195838 |
| AR(1) / gewöhnlich | 250.35745 | 0.0079046804 | 0.0057225228 | 0.607430381829 |
| AR(1) / wahre Kovarianz | 250.62609 | 0.0079656544 | 0.0057284665 | 0.607162556032 |
| AR(1) / geschätzte Kovarianz | 250.10931 | 0.0081485932 | 0.0057616639 | 0.608959058286 |

Die zusätzliche Prüfung wurde auf beiden Rechnern an deren lokalen
CSV-/JSON-Dateien ausgeführt und kontrollierte:

1. Erfolgsstatus und alle zwölf gespeicherten Artefaktprüfsummen je Lauf
   gegen die zugehörigen Dateibytes; `metadata.json` hasht sich nicht selbst.
2. `S = B_train.T @ B_train / M_train`, `mu = trace(S)/N` und
   `C_hat = (1-alpha)*S + alpha*mu*I` aus den exportierten Fenstern.
3. Kontroll-Scores für `C_true` und `C_hat` aus `slogdet(C)` und der über
   Kontrollzeilen gemittelten Quadratik mit direktem `solve(C, b)`.
4. `residual = observed - prediction`, gewöhnliche MSE und für jeden Fit
   `Q_true/N` sowie, wo vorhanden, `Q_used/N` mit direktem Gleichungslöser
   statt dem produktiven Cholesky-Whitening.

Für die rohe Matrix galt `rtol=0` und
`atol=8*M_train*eps(float64)*max(diag(S))`; dieselbe absolute Schranke
wurde für die Schrumpfungsrekonstruktion verwendet. Für `mu` galt
`rtol=8*N*eps(float64)`. Die Quadratikvergleiche verwendeten
`rtol=8*N*eps(float64)*cond(C)`, `atol=0`. Dies sind an diese numerischen
Kontrollfälle gebundene Konsistenzprüfungen, keine statistischen
Erfolgsschwellen oder universellen Schranken für alle möglichen Eingaben.

Die Nachrechnung bestätigt die Konsistenz der übermittelten Läufe. Sie
prüfte nicht separat sämtliche Alpha-Validierungsscores, eine vollständige
erneute Selektorausführung oder alle nachgelagerten Wahrheitsdiagnosen.
Die lokalen Dateien selbst und ihre einzelnen Hashwerte wurden nicht
übermittelt. Ein byteweiser oder vollständiger numerischer Vergleich
dieser neuen Schema-2-Artefakte zwischen Rechnern liegt daher nicht vor.

Der technische Kontrollvergleich für diese beiden Schema-2-Konfigurationen
ist damit abgeschlossen: gleicher sauberer Codecommit, erfolgreiche Tests,
Ausführung, Exporte und Diagramme sowie unabhängige lokale Nachrechnungen
auf beiden Rechnern. Der Umfang ist auf diese Kontrollfälle und die
übermittelten Kennzahlen begrenzt; vollständige rechnerübergreifende
Arrayvergleiche oder allgemeine Bitidentität werden nicht behauptet.

Zusätzlich wurde am 20.10.2026 im ursprünglichen WSL2-Projektordner der
gepinnte Python-/Julia-Startweg ausgeführt:

```bash
env -u VIRTUAL_ENV uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_environment.py
```

Der Nutzer meldete `Technical environment check passed.` und das geladene
Projekt `julia/Project.toml` dieses Checkouts mit folgenden Versionen:

| Komponente | Gemeldete Version |
| --- | --- |
| Python | 3.12.14 |
| NumPy | 2.5.3 |
| SciPy | 1.18.1 |
| Matplotlib | 3.11.2 |
| pandas | 3.0.6 |
| SymPy | 1.14.0 |
| PySR | 2.6.0 |
| Julia | 1.13.1 |
| SymbolicRegression | 2.5.1 |
| PythonCall | 0.9.36 |

Dieser Umgebungscheck ist vom Schema-2-Vergleich im separaten Worktree
zu unterscheiden. Er bestätigt die gemeldeten Versionen und den geladenen
Startweg, keinen neuen SR-Adapter; ein eigener Git-Metadatensatz dieses
Umgebungsaufrufs wurde nicht übermittelt. Schema 2 benötigt Julia nicht.

Die Kontrollwerte zeigen insbesondere keine allgemeine Überlegenheit
der geschätzten Gewichtung. Diese Schema-2-Nachweise betreffen klassische
Fits mit bekannter Formel. Die freie PySR-Suche wird im nachfolgenden
Schema-3-Abschnitt gesondert dokumentiert. Eine wissenschaftliche
Leistungsstudie steht weiterhin aus.

## Schema 3 vom 22.10.2026: Manjaro am sauberen Referenzcommit bestätigt

Der Nutzer übermittelte nach dem angeleiteten Vollprofil des
[SR-Piloten](symbolic_pilot.md) folgende Ergebnisse auf Manjaro:

- **559 Python-Tests bestanden in 53,44 s**.
- `Technical environment check passed.` mit korrekter PythonCall-Bindung
  an `.venv/bin/python` des separaten Prüfprojekts, CondaPkg-Backend `Null`
  und geladener PythonCall-Erweiterung.
- Beide vollständigen Audits melden `Schema-3 audit passed`.
- Beide gemeinsamen Diagramme werden laut Nutzer angezeigt.

Der durch gespeicherte Git-Metadaten bestätigte Prüfstand ist Commit
`6ed493d2e8fb3a845dd921bd99a620feb8b8850a` im separaten Worktree
`ringdown-sr-portability-6ed493d`. Der Nutzer führte zusätzlich eine lesende
Herkunftsprüfung an den gespeicherten Metadaten beider Ergebnisordner aus:

- Je Lauf wurden die Elternpipeline, die klassische Referenzstufe und alle
  drei SR-Arme berücksichtigt.
- Für die Arme wurden sowohl `provenance` vor dem Workerstart als auch
  `worker_provenance` vor `fit` geprüft.
- Alle geprüften Git-Aufnahmen nennen `available: true`, denselben
  vollständigen Referenzcommit, `dirty: false` und `changes: []`.

Die gemeldeten Abschlusszeilen lauten jeweils für `white` und `ar1`:
`Commit 6ed493d und sauberer Codezustand aller Stufen bestätigt.`
Dieser Herkunftsnachweis beruht auf der übermittelten Ausführung der
Metadatenprüfung; die Dateien selbst wurden nicht hier eingelesen.

Die Ergebnisordner liegen relativ zum Prüfprojekt unter
`results/sr-portability-001/white` und `results/sr-portability-001/ar1`.
Das vorgegebene Vollprofil verwendet die unveränderten Schema-3-Beispiele
mit 128 Samples und dem Standard-Suchbudget, keinen reduzierten CI-Lauf.
Die folgenden Werte wurden tatsächlich im Terminal gemeldet:

| Rauschen | SR-Arm | Exportierte Kandidaten | `Q_true/N` |
| --- | --- | ---: | ---: |
| Weiß | gewöhnliche MSE | 11 | 5.07768087378 |
| Weiß | wahre Kovarianz | 7 | 6.3972941486 |
| Weiß | geschätzte Kovarianz | 9 | 5.70728782157 |
| AR(1) | gewöhnliche MSE | 5 | 4.93620902355 |
| AR(1) | wahre Kovarianz | 7 | 2.75758997199 |
| AR(1) | geschätzte Kovarianz | 8 | 2.54625560892 |

Gewähltes Alpha: **1** bei Weißrauschen und **0,5** bei AR(1).
Insgesamt wurden **47 Kandidaten** exportiert. Kandidatenzahlen, Alpha und
die ausgegebenen `Q_true/N` stimmen in allen übermittelten Stellen mit dem
bisherigen vollständigen Codex-Kontrolllauf aus dem Implementierungsarbeitsstand
überein. Das bestätigt keine
Identität der Bäume, vollständigen Arrays oder Dateibytes zwischen Rechnern.

Gemeldete Umgebung:

| Komponente | Version |
| --- | --- |
| Python | 3.12.14 |
| NumPy | 2.5.3 |
| SciPy | 1.18.1 |
| Matplotlib | 3.11.2 |
| pandas | 3.0.6 |
| SymPy | 1.14.0 |
| PySR | 2.6.0 |
| Julia | 1.13.1 |
| SymbolicRegression | 2.5.1 |
| PythonCall | 0.9.36 |

Julia wurde zunächst für die eigene `.venv` dieses Prüfprojekts
heruntergeladen und installiert. Die dabei gemeldete Warnung zu mehreren
lokalen Installationsorten bezeichnet keinen fehlgeschlagenen Check;
anschließend wurden die gepinnte Version und der Projektstart erfolgreich
bestätigt.

Die Audit-Erfolgsmeldungen belegen nach übermittelter Ausführung die
projektierten Datei-, Übergabe-, Schrumpfungs-, Kandidaten-, Verlust- und
Kontroll-Score-Prüfungen. Die lokalen Dateien selbst wurden nicht
übermittelt und hier nicht neu geprüft. Eine wissenschaftliche
Leistungsbewertung folgt aus diesen einzelnen angepassten Kontrollfällen
nicht. Für diese beiden Manjaro-Kontrollfälle sind damit Tests, Umgebung,
Ausführung, Audits, Diagrammanzeige und sauberer Referenzcommit durch die
übermittelten Nachweise bestätigt. Der entsprechende Schema-3-Nachweis
unter WSL2 und sein Vergleich mit Manjaro folgen im nächsten Abschnitt.

## Schema 3 vom 22.10.2026: WSL2 bestätigt, SR-Ergebnisse weichen ab

Der Nutzer führte dasselbe angeleitete Vollprofil unter Windows mit
Ubuntu/WSL2 in einem separaten Worktree am Referenzcommit
`6ed493d2e8fb3a845dd921bd99a620feb8b8850a` aus und übermittelte:

- **559 Python-Tests bestanden in 56,97 s**.
- `Technical environment check passed.` mit denselben gemeldeten Versionen
  wie im Manjaro-Umgebungsblock: Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1,
  Matplotlib 3.11.2, pandas 3.0.6, SymPy 1.14.0, PySR 2.6.0, Julia 1.13.1,
  SymbolicRegression 2.5.1 und PythonCall 0.9.36.
- PythonCall verwendet `.venv/bin/python` dieses Prüfprojekts;
  CondaPkg-Backend `Null` und die PythonCall-Erweiterung sind bestätigt.
- Beide vollständigen Audits melden `Schema-3 audit passed`.
- Die zusätzliche lesende Herkunftsprüfung meldet für `white` und `ar1`
  jeweils den Commit `6ed493d` und sauberen Codezustand aller Stufen.
  Sie prüft dieselben Metadatenfelder und Git-Bedingungen wie auf Manjaro,
  einschließlich der Arm-Aufnahme vor Workerstart und der Workeraufnahme
  vor `fit`.
- Beide gemeinsamen Diagramme werden laut Nutzer angezeigt.

Die Ergebnisordner liegen auch hier relativ zum Prüfprojekt unter
`results/sr-portability-001/white` und `results/sr-portability-001/ar1`.
Julia wurde für dessen eigene `.venv` installiert; anschließend bestanden
der Umgebungscheck und die Such-/Auditläufe.

Die Alpha-Auswahl stimmt auf beiden Rechnern überein: **1** bei Weißrauschen
und **0,5** bei AR(1). Die SR-Ergebnisse unterscheiden sich dagegen bereits
in den übermittelten Stellen. Die Kandidatenzahl bezeichnet jeweils die
exportierte Pareto-Front, nicht alle während der Suche untersuchten Bäume:

| Rauschen | SR-Arm | Kandidaten Manjaro | Kandidaten WSL2 | `Q_true/N` Manjaro | `Q_true/N` WSL2 |
| --- | --- | ---: | ---: | ---: | ---: |
| Weiß | gewöhnliche MSE | 11 | 7 | 5.07768087378 | 5.49373971715 |
| Weiß | wahre Kovarianz | 7 | 7 | 6.3972941486 | 5.07985556164 |
| Weiß | geschätzte Kovarianz | 9 | 9 | 5.70728782157 | 4.32241384476 |
| AR(1) | gewöhnliche MSE | 5 | 6 | 4.93620902355 | 3.75865072184 |
| AR(1) | wahre Kovarianz | 7 | 8 | 2.75758997199 | 0.734382443275 |
| AR(1) | geschätzte Kovarianz | 8 | 9 | 2.54625560892 | 3.73673302619 |

Insgesamt wurden auf Manjaro **47**, unter WSL2 **46** Kandidaten exportiert.
Die Testlaufzeiten sind keine kontrollierte Geschwindigkeitsmessung. Auch
die einzelne kleinere Quadratik eines Arms begründet keine allgemeine
Überlegenheit des Verfahrens oder Rechners.

Der technische Ausführungsnachweis ist für diese beiden Konfigurationen
auf beiden Rechnern damit erbracht: gleicher sauberer Codecommit,
gemeldete Versionen, erfolgreiche Tests, Umgebung, Exporte, lokale Audits
und Diagrammanzeige. Die Audits prüfen die interne Konsistenz der jeweils
lokalen Dateien; sie vergleichen keine Arrays, Konstanten, Bäume oder
Dateibytes zwischen Rechnern. Die übereinstimmenden Alpha-Werte beweisen
ebenfalls keine bitgleichen Hintergrundfenster oder Schätzmatrizen.

**Rechnerübergreifend identische SR-Suchergebnisse sind in diesen Läufen
nicht gegeben.** Die Ursache ist mit den vorliegenden Ausgaben nicht
bestimmt. Unterschiede in numerischen Eingaben, CPU-/Build-/BLAS-Umgebung
oder Gleitkommarechnungen sind mögliche Erklärungen, keine hier bestätigte
Diagnose. Für eine Ursachenanalyse müssten unter anderem die gespeicherten
numerischen Eingaben sowie Backend-Seeds, Optionen und Numerikumgebungen
der einzelnen Arme zwischen Rechnern verglichen werden. Auch die
Wiederholbarkeit auf demselben Rechner wurde mit diesen Einzelstarts
nicht gesondert geprüft.

Die Nachweise dieser beiden ursprünglichen Vollprofile wurden vom Nutzer
als Terminalausgaben und Diagrammbestätigungen übermittelt. Ihre vollständigen
lokalen Ergebnisordner wurden damals nicht hier eingelesen und keine
neuen Suchen dafür ausgeführt. Spätere Diagnosepakete werden gesondert
ausgewiesen. Die wissenschaftliche Leistungsbewertung,
unabhängige Generalisierung und Parameteridentifikation bleiben offen.

## Diagnose vom 26.10.2026: gemeinsamer BLAS-Kern für einen freien Arm

Nach Einfrieren derselben WSL2-Eingaben blieb der gewöhnliche Weißrauscharm
auf jedem Gerät lokal wiederholbar, zwischen Geräten jedoch verschieden.
Poollimits 1 allein änderten das nicht. Die folgende feste, gepaarte
Kernkontrolle und zwei neue freie Haswell-Suchen je Gerät sind im
[gemeinsamen Befund](symbolic_core_results.md) dokumentiert.

Am protokollierten sauberen Prüfcommit `6ed493d` mit externem Werkzeugcommit
`6b3d156` liefern alle vier freien Haswell-Läufe dieselbe vollständige
Front mit sieben Kandidaten, gewählter Komplexität 12 und gewöhnlicher
Trainings-MSE `0.054937397171508`. Die eigentlichen Archive wurden diesmal
hier an ihren Dateibytes geprüft; 98 äußere Dateiprüfsummen und 28 eigene
Kandidaten-Replays bestehen. Bäume, Konstanten und Vorhersage-/Residualbits
stimmen überein; die Ergebnisdateien unterscheiden sich bei den Laufzeiten.

Dieser Nachweis betrifft einen gewöhnlichen Weißrauscharm, eine eingefrorene
Datenrealisierung und einen Seed. Er belegt keine neue rechnerübergreifende
Gleichheit aller sechs ursprünglichen Schema-3-Arme. Die nativen freien
Gegenbefunde stammen aus früheren Paketen mit dem damaligen Diagnosetreiber;
eine frische gepaarte freie Baseline mit demselben umschlossenen Einstieg
wurde nicht ausgeführt. Die genaue erste abweichende interne Operation
der früheren freien Suche ist weiterhin nicht nachgestellt.

Haswell bleibt eine explizite Diagnosevorgabe. Exakte Wiederholbarkeit,
wissenschaftliche Robustheit und die offene Festlegung eines späteren
Referenzprofils werden im
[Entscheidungsvermerk](reproducibility_decisions.md) getrennt behandelt.
