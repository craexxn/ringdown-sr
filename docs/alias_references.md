# Referenzfälle für Frequenz-Aliasing und Phase

Stand: 23.10.2026. `tests/test_alias_references.py` sichert die in
[Abschnitt 6.1 des Methodenplans](symbolic_regression_method_plan.md#61-rohe-ausdrucksfrequenz-und-aliasdarstellung)
festgelegten Identitäten unabhängig von einer SR-Suche ab.
Die Fälle beziehen sich auf die ausdrücklich vorgegebene Form
`A*exp(-t/tau)*cos(2*pi*nu*t+phi)`, mit vorzeichenbehaftetem `nu`, und
das Raster `t_j=j/fs` mit Zeitursprung null. Sie verwenden `fs=4096 Hz`
und 128 Samples. Die Abklingzeit beträgt im numerischen Vergleich
`tau=0.008 s`.

## Unabhängige Vorgaben

Die Referenztabelle enthält rohe und kanonische Frequenzen sowie Phasen
als explizite Konstanten. Sie ruft keinen zu prüfenden Alias-Algorithmus
zur Bildung ihrer Erwartungswerte auf. Die Phase wird nach `[-pi,pi)`
gelegt. Die vorzeichenbehaftete Restfrequenz liegt in `[-fs/2,fs/2)`;
deshalb erhält der exakte Nyquist-Fall in dieser Konvention die negative
Orientierung.

Für `phi=pi/5` gelten beispielsweise:

| Rohe Frequenz (Hz) | Aliasfrequenz (Hz) | Aliasphase |
| --- | --- | --- |
| 250 | 250 | `pi/5` |
| 4346 | 250 | `pi/5` |
| 3846 | 250 | `-pi/5` |
| -250 | 250 | `-pi/5` |
| -4346 | 250 | `-pi/5` |
| -3846 | 250 | `pi/5` |
| 0 oder 4096 | 0 | `pi/5` |
| 2048, -2048 oder 6144 | 2048 | `-pi/5` |

Weitere Fälle prüfen den Phasenumschlag von `9*pi/4` auf `pi/4`, seine
Kombination mit negativer Orientierung sowie `pi` auf `-pi`. Die beiden
direkten Float64-Nachbarn oberhalb und unterhalb von 2048 Hz werden
ausdrücklich getrennt behandelt. Sie werden nicht durch eine Toleranz
auf die Faltungsgrenze verschoben.

## Aussage der Prüfungen

Die Identitäten werden in zwei getrennten Rechnungen abgesichert:

1. Für jeden Sampleindex werden Argumente in Einheiten voller Umdrehungen
   mit `Fraction` exakt berechnet. Nach Berücksichtigung der in der Tabelle
   vorgegebenen Orientierung muss ihre Differenz eine ganze Zahl sein.
   Rationale Vielfache von `pi` ermöglichen diese Prüfung ohne eine
   Gleitkommaauswertung trigonometrischer Funktionen. Bei den beiden
   Nachbarwerten werden die tatsächlich gespeicherten Binärzahlen exakt
   als Brüche übernommen.
2. Der bestehende Ringdown-Generator wird mit einer direkten Auswertung
   des vorzeichenbehafteten Ausdrucks verglichen. Amplituden `1`, `-2`
   und `1e-21` prüfen auch das Vorzeichen und kleine Größenordnungen.
   Der Generator selbst behält seinen Vertrag nicht negativer Frequenzen;
   negative rohe Frequenzen stehen ausschließlich im Referenzausdruck.

Vor dem numerischen Vergleich werden beide Kurven durch den Betrag der
Amplitude geteilt. Das absolute Fehlerbudget gilt damit in Einheiten
der Signalhöhe. Es beträgt
`16*eps*(1+max(abs(raw_argument),abs(alias_argument),t/tau))` über das
jeweilige Fenster; der relative Toleranzanteil ist null. Der Faktor 16
ist ein konservatives technisches Budget für diese begrenzten Argumente
bei Float64-Multiplikation, Addition und Funktionsauswertung, keine
allgemeine Fehlergarantie für beliebig große Konstanten oder jede
Mathematikbibliothek. Der exakte Periodennachweis bleibt davon getrennt.
Eine fehlende Phasenumkehr wird zusätzlich als deutlicher Gegenfall
bei Amplitude `1` und `1e-21` nachgewiesen.

Die Tests halten die Grenzen der Interpretation ausdrücklich fest:

- Zwischen Samples unterscheiden sich beispielsweise 250 und 4346 Hz.
  Am Mittelpunkt des ersten Abtastintervalls liefern sie bei gleicher
  Phase sogar entgegengesetzte Werte.
- Ein verschobener Zeitursprung benötigt eine zusätzliche Phase. Für
  `t0=1/(4*fs)` und die Frequenzverschiebung um `fs` beträgt sie `pi/2`.
  Die unveränderte Nullursprungsregel scheitert in diesem Gegenbeispiel.
- Bei null und Nyquist wirkt nur `A*cos(phi)` als Amplitudenfaktor
  der gegebenenfalls alternierenden Samples. Unterschiedliche Paare aus
  Amplitude und Phase können dieselbe Kurve liefern.
- Bei Amplitude null liefern unterschiedliche Frequenzen, Abklingzeiten
  und Phasen dieselben Nullsamples.

## Umfang und nächste Umsetzung

Diese Tests bestätigen Referenzidentitäten und die numerische Auswertung
der ausgewählten Paare. Sie erkennen keine Struktur in einem freien
SR-Baum und implementieren keinen allgemeinen Frequenz-/Phasenreduzierer.
`parameter_interpretation=not_attempted` im Schema-3-Piloten bleibt gültig.
Die Suchgrammatik, Kandidatenauswahl, Exporte und bestehenden Ergebnisdateien
werden nicht verändert. Keine Suche oder Anpassung an Signalwahrheit
ist für diese Prüfungen erforderlich.

Vor einem späteren Parameterexport bleiben Strukturerkennung, Behandlung
sehr großer Konstanten und numerisch nicht zuverlässig reduzierbarer
Werte sowie ausdrücklich gekennzeichnete Degenerationszustände umzusetzen.
Insbesondere ist die hier geprüfte Identität für bereits deklarierte
Frequenzen in Hz noch kein Genauigkeitsnachweis einer Umrechnung aus
beliebigen Baumkonstanten `c/(2*pi)`.

Auch eine korrekte Aliasdarstellung identifiziert keine eindeutige
physikalische Frequenz. Die Referenzfälle erklären nicht die verschiedenen
Suchergebnisse auf Manjaro und WSL2. Deren Diagnose bleibt ein separater
Arbeitsschritt anhand der ursprünglichen Laufdaten.

Ausführen:

```bash
uv run --locked pytest -q tests/test_alias_references.py
```
