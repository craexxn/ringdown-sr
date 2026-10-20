# Pilot mit geschätzter Kovarianz und drei gekoppelten Fits

Stand: 20.10.2026. Schema 2 verbindet den
[geprüften Schätzer](covariance_estimation.md) mit der Datenerzeugung,
drei klassischen Referenzfits, Diagnosen und Ergebnisexport gemäß
[Methodenplan](covariance_method_plan.md). Die bisherigen
[Schema-1-Kontrollfälle](configured_pilot.md) behalten ihre Bedeutung.
Die freie PySR-Suche ist noch nicht angebunden.

## Start

Im Projektordner unter Manjaro oder Ubuntu/WSL2:

```bash
uv run --locked ringdown-sr run configs/pilot_estimated_ar1.toml --output results/estimated-ar1-001
code -r results/estimated-ar1-001/plot.png
code -r results/estimated-ar1-001/covariance_plot.png
```

Für weißes Rauschen `configs/pilot_estimated_white.toml` und einen anderen
neuen Ausgabeordner verwenden. Jeder Aufruf erzeugt dieselben drei Varianten:

| Kennung in `result.json` | Fit-Zielfunktion und Information |
| --- | --- |
| `ordinary` | Gewöhnliche Quadratsumme, ohne Kovarianz |
| `known_covariance` | Gewichtung mit analytischem `C_true`; privilegierter Kontrollfit mit bekanntem Rauschmodell |
| `estimated_covariance` | Gewichtung mit einmal aus Hintergrunddaten bestimmtem `C_hat` |

Alle drei Fits erhalten dieselben Zeitpunkte, Messdaten, Grenzen,
Startpunkte und Budgets. `C_hat` bleibt über alle Starts und numerischen
Kandidaten des Fits fest. Der Schätzer wird einmal aufgerufen, vor den
Fits und ohne Zugriff auf Signalwahrheit, Messdaten oder wahre Kovarianz.
Es gibt keinen Refit und keinen Ersatzfit bei gescheiterter Schätzung.

## Explizite Konfiguration: Schema 2

`schema_version = 2` verlangt dieselben Tabellen `sampling`, `signal` und
`noise` wie Schema 1. `noise.seed` bezeichnet weiterhin ausschließlich das
Messrauschen. Seine Varianz muss hier strikt positiv und endlich in
`float64` darstellbar sein, weil der bekannte Kontrollfit sie benötigt.
Es gibt keine SNR-Normierung.

| Tabelle | Erforderliche Felder |
| --- | --- |
| `fit` | `weighting = "compare_covariances"`; dieselben expliziten Frequenz-/Abklingzeitgrenzen, Startpunkte und `max_nfev` wie bisher |
| `background` | Ganzzahlige `n_train`, `n_validation`, `n_check`, jeweils mindestens 1; `bit_generator = "PCG64"`; ganzzahliger nicht negativer `seed`; `stream_scheme = "seedsequence_role_v1"` |
| `covariance_estimation` | `mean_mode = "known_zero"`; nicht leeres, eindeutiges endliches `alpha_candidates`-Raster in `[0,1]`; endliches `kappa_max > 1` |

Unbekannte, fehlende und falsch typisierte Felder werden vor Anlegen des
Ausgabeordners abgelehnt. Schema-2-Felder werden in Schema 1 nicht akzeptiert;
`compare_covariances` ist ausschließlich in Schema 2 zulässig. Der bisherige
Schema-1-Modus `known_covariance` bedeutet weiterhin die wahre Modellmatrix.

Die Kontrollbeispiele behalten `N=128`, `fs=4096 Hz`, Signalvorgaben,
Fit-Grenzen und Starts der bisherigen Beispiele bei. Das ergibt `N/fs`
von 31,25 ms; damit wird keine Dauer der Hauptversuche festgelegt.
Hinzu kommen 64 Trainings-, 128 Validierungs- und 256 Kontrollfenster,
das Raster `[0,0.001,0.01,0.05,0.1,0.2,0.5,1]` und `kappa_max=1e8`.
Bei `64 < 128` wird Alpha null strukturell abgelehnt. Diese Mengen sind
technische Kontrollvorgaben, kein begründetes Budget für Detektordaten.

## Datenrollen und Zufallsableitung

Alle Fenster und das Messrauschen verwenden dieselbe konfigurierte
Rauschfamilie, marginale Standardabweichung und gegebenenfalls AR(1)-Korrelation.
Samplezahl, Abtastrate und Reihenfolge stimmen überein. Jede Hintergrundzeile
ist ein unabhängig erzeugtes vollständiges Fenster. Bei AR(1) erhält jede
Zeile einen eigenen stationären Anfangswert; es werden keine Abschnitte
einer einzigen zusammenhängenden Folge als unabhängig ausgegeben.

| Rolle | Zweck | Fester `spawn_key` |
| --- | --- | --- |
| `train` | `S = B_train.T @ B_train / M_train`, Ziel `mu*I` | `(0,)` |
| `validation` | Alpha-Auswahl durch Logdeterminante plus mittlere Quadratik | `(1,)` |
| `check` | Nachträglicher Score auf eingefrorenem `C_hat` und `C_true` | `(2,)` |

Jede Rolle verwendet `Generator(PCG64(SeedSequence(background.seed,
spawn_key=(role_id,), pool_size=4)))`. Die Wurzel ist in den Beispielen
`20261019`. Rollen werden direkt über feste Schlüssel abgeleitet;
eine andere Fensterzahl verschiebt keine anderen Ströme.
Das Messrauschen verwendet wie bisher `Generator(PCG64(noise.seed))` mit
Seed 42. Der globale NumPy-Zufallszustand wird nicht verwendet.

Vor dem Anlegen des Ausgabeordners und vor jeder Datenerzeugung werden
die vier tatsächlichen Generatoren gemeinsam initialisiert. Der Pilot
vergleicht ihre vollständigen PCG64-Anfangszustände in allen sechs Paaren.
Bei Gleichheit wird die Konfiguration mit den betroffenen Rollennamen
abgelehnt (CLI-Code `2`); es werden keine Daten oder Laufdateien erzeugt.
Bei erfolgreicher Prüfung werden genau diese unbenutzten Generatoren für
Messrauschen und Hintergrund weiterverwendet.

Damit wird insbesondere die im Implementierungsreview nachgewiesene
Überschneidung bei `background.seed=20261019` und
`noise.seed=20261019 + 2**128` mit dem Validierungszweig ausgeschlossen;
der entsprechende Fall mit `2*2**128` kollidiert mit dem Kontrollzweig.
Seeds werden weiterhin nicht pauschal auf eine feste Bitbreite begrenzt.
Die Ableitung und die gültigen Beispielseeds bleiben unverändert.
Verschiedene Anfangszustände sind allein kein allgemeiner Beweis
statistischer Unabhängigkeit. Die
[NumPy-Dokumentation zur parallelen Zufallserzeugung](https://numpy.org/doc/stable/reference/random/parallel.html)
beschreibt die Voraussetzungen und Überschneidungsrisiken beim Kombinieren
verschiedener Seed-Ableitungen.

Das AR(1)-Modell führt pro Fenster einen Aufruf
`standard_normal(N, dtype=float64)` und die vorhandene stationäre
Transformation aus. Weißes Rauschen verwendet `normal(0,sigma,N)`.
Die Metadaten enthalten Ableitung, Modell, Abtastung, erwartete und
erfolgreich abgeschlossene Fensteraufrufe sowie Zustände vor und nach
der Erzeugung. Bei einer gescheiterten Transformation kann der Zustand
bereits fortgeschritten sein, obwohl das Fenster nicht als abgeschlossen
gezählt wird. Gespeichert werden dann nur vollständig erzeugte Zeilen;
unbegonnene Rollen behalten `state_before = null`.

## Dateien und Diagnosen

Konfiguration, `result.json` und `metadata.json` tragen Schema-Version 2.
Die vorhandenen Regeln für neue Ausgabeordner, UTC-Zeitstempel, Umgebung,
Codezustand und SHA-256-Prüfsummen gelten weiter. CSV verwendet 17
signifikante Stellen, JSON ausschließlich endliche Zahlen oder `null`.

| Datei | Inhalt |
| --- | --- |
| `config.toml`, `resolved_config.json` | Original und vollständig geprüfte Konfiguration |
| `samples.csv` | Gemeinsame Spalten `time_s`, `signal`, `noise`, `observed`; je erfolgreichem Fit zusätzlich `prediction_<Kennung>`, `residual_<Kennung>` |
| `background_train.csv`, `background_validation.csv`, `background_check.csv` | Matrizen ohne Kopfzeile; Zeilen sind Fenster, Spalten die gemeinsamen Samplepositionen |
| `covariance_true.csv` | Analytische Modellmatrix, auch bei weißem Rauschen |
| `covariance_raw.csv`, `covariance_estimated.csv` | Aus Training bestimmte rohe Matrix und ausgewähltes, eingefrorenes `C_hat` |
| `result.json` | Schätzer- und Kandidatendiagnosen; drei Fit-Ergebnisse mit sämtlichen Startdiagnosen; Fehlerwerte und nachgelagerte Kontrolle |
| `metadata.json` | Abschlussstatus, Herkunft, Software, RNG-Rollen und Dateiprüfsummen |
| `plot.png` | Messdaten, Wahrheit, drei Fits und Residuen |
| `covariance_plot.png` | Wahre, rohe und regularisierte Matrix mit gemeinsamer Farbskala |

Zeitspalten sind in Sekunden, Amplituden dimensionslos und Kovarianzen
in quadrierten Amplitudeneinheiten. Zeile/Spalte `i` der Matrix gehört zu
`time_s[i]`. Unveränderte Zeilenreihenfolge und tatsächlich exportierte
Fenster erlauben das Nachrechnen von `S`, `mu`, Kandidaten und Auswahl.

Unter `fits.<Kennung>.metrics` stehen:

- `ordinary_mse`: mittlere Residuenquadrate der Messdaten.
- `mse_to_clean_signal`: mittlere quadratische Abweichung zur Signalwahrheit.
- `q_used_per_sample`: `Q_used/N` mit der jeweiligen Fit-Kovarianz;
  beim gewöhnlichen Fit `null`, da keine Kovarianz eingesetzt wird.
- `q_true_per_sample`: `Q_true/N` mit derselben wahren Matrix für alle Fits.

Die Metriken betreffen die angepassten Samples (`fitted_samples_only`),
keine unabhängige Rekonstruktionsbewertung. `Q_used/N` unterschiedlicher
Kovarianzen ist kein gemeinsamer Leistungsmaßstab. Die nachträgliche
Wahrheitsdiagnose ändert keine Start- oder Alpha-Auswahl.

`diagnostics.relative_frobenius_error` ist `||C_hat-C_true||_F/||C_true||_F`.
`diagnostics.background_check` enthält jeweils Logdeterminante, über
Kontrollfenster gemittelte Quadratik und deren Summe für `C_true` und
`C_hat`. Dieser Score wird nicht durch `N` geteilt und beeinflusst die
Auswahl nicht. Ein kleinerer Validierungs-Score ist keine unabhängige
Bewertung. Auch die Kontrollmenge darf nach Einsicht nicht wiederholt
zur Entwicklung verwendet und weiterhin als unangetastet bezeichnet werden.

## Fehler und Prüfnachweis

Die CLI liefert `0` nur nach vollständiger Berechnung und Export.
`generation_failed`, `estimation_failed`, `fit_failed` und
`evaluation_failed` werden mit Code `1` und erhaltenen Eingaben/Diagnosen
gespeichert. Die drei Fit-Einträge haben eigene Statuswerte; ein einzelner
Fehler macht den Vergleich insgesamt unvollständig. Bei Schätzfehlern
bleiben alle Fits `not_run`. Fehler bei Eingabe oder Export liefern Code `2`;
nach einem unvollständigen Export bleibt die Metadatei `running`.
Vorhandene Ordner werden weder fortgesetzt noch überschrieben.

Am 20.10.2026 bestanden in der Codex-Umgebung 456 Tests, darunter 60 neue
Tests für Schema, Zufallsströme und Integration. Diese prüfen insbesondere Datentrennung,
einmalige Schätzung und feste Matrixübergabe, RNG-Ableitung und -Wiederholung,
stationäre Anfangswerte, Rekonstruktion der Auswahl aus CSV sowie Scores
und Quadratik mit unabhängigen direkten Gleichungslösern. Veränderte
Kontrollwerte, Signalwahrheit und Messrausch-Seeds beeinflussen die Schätzung
nicht. Änderungen einer Hintergrundmenge verschieben keine anderen Rollen.
Fehlerpfade erhalten vorhandene Ergebnisse und endliche Teildiagnosen.
Sieben zusätzliche RNG-Testfälle sichern die Seed-Nachbesserung ab:
Kollisionen mit Validierungs- und Kontrollzweig für beide Rauscharten,
die Ablehnung vor Ausgabeordner und Datenerzeugung, gültige große Seeds
sowie eine absichtlich doppelt belegte Hintergrundrolle.

Beide vollständigen Beispiele wurden am selben Tag in der Codex-Umgebung
erfolgreich ausgeführt; die Diagramme wurden geöffnet und geprüft:

| Einzelner Kontrollfall | Gewähltes Alpha | Relativer Frobeniusfehler |
| --- | ---: | ---: |
| Weißes Rauschen | 1 | 0.008444132406 |
| AR(1), `rho=0.65` | 0.5 | 0.609306218453 |

Dies sind Entwicklungsprüfungen am damaligen Arbeitsstand, keine
Leistungsstudie oder Portabilitätsbestätigung des neuen Schemas.
Die beiden bisherigen AR(1)-Fits reproduzieren die bisherigen Kontrollwerte.
Beim geschätzten AR(1)-Fit beträgt die Frequenz ungefähr `250.10931 Hz`,
die Abklingzeit `0.0081485932 s` und `Q_true/N = 0.60895906`.
Ein Verbesserungskriterium gegenüber den anderen Fits wurde nicht verlangt.
Nach Ergänzung der Seed-Prüfung wurden beide Beispiele wiederholt.
Alle CSV-Dateien, `result.json` und sämtliche RNG-Protokolle waren zum
Stand vor dieser Nachbesserung bytegleich.

Das separate Integrationsreview zu PR #16, Commit `4aae1b0`, bestätigte die
Methodenkonformität und fand einen Seed-Grenzfall mit identischem
Messrausch-/Validierungszustand. Die Prüfung der vier Anfangszustände
wurde in `5c97d64` ergänzt; übernommen wurde PR #16 als `1fcf9fc`.
Die bisherigen Beispielseeds waren von diesem Fehler nicht betroffen.

Am 20.10.2026 bestätigte der Nutzer auf Manjaro am sauberen Commit
`1fcf9fce5b999c2344b038c0a171b60ffaf7ae73` 456 bestandene Tests in 33,02 s,
beide erfolgreichen Beispiele und die Diagrammanzeige. Die zusätzliche
Nachrechnung bestätigte die zwölf Artefaktprüfsummen pro Lauf,
Trainingskovarianz und Schrumpfung, Kontroll-Scores sowie die exportierten
Fit-Verluste. Alpha war 1 für Weißrauschen und 0,5 für AR(1).
Das [Portabilitätsprotokoll](portability.md) dokumentiert die übermittelten
Kennzahlen und den genauen Umfang dieses Nachweises.

Offen bleiben sichtbare Schema-2-Läufe unter WSL2 am selben Referenzcommit.
Vor deren numerischem Vergleich sind passende Toleranzen zu begründen;
Bitidentität wird nicht vorausgesetzt. Der
[PySR-Methodenentwurf](symbolic_regression_method_plan.md) bereitet parallel
den nächsten fachlichen Schritt vor und ist noch separat zu prüfen.
Der lokale Python-/Julia-Umgebungscheck wurde für diese Änderung nicht
erneut ausgeführt; beide Piloten verwenden Julia nicht. Hauptversuche,
Unsicherheitsabdeckung und freie Formelentdeckung folgen separat.
