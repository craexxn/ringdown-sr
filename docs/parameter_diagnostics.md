# Parameter- und Aliasdiagnose mit numerischer Nachrechnung

Stand: 23.10.2026. `parameters.py` und `aliasing.py` setzen Schritt 2 des
[geprüften Methodenplans](parameter_interpretation_plan.md) um. Sie lesen
einen einzelnen exportierten Baum und seine Zeiten. Es gibt keinen neuen
Suchlauf, Fit oder Verlustvergleich. Die bestehende Auswahl, Eingaben und
Ergebnisdateien bleiben unverändert. Der vollständige lesende Diagnoseexport
für Schema-3-Läufe ist als [Schritt 3](parameter_export.md) separat umgesetzt.

## Schnittstelle für einen Baum

```python
from ringdown_sr.parameters import analyze_tree

report = analyze_tree(tree, time_s, sample_rate_hz=4096)
```

`tree` folgt dem Vertrag des [Strukturerkenners](structure_recognition.md).
`time_s` ist ein endlicher, nicht leerer eindimensionaler reeller Vektor.
Die Abtastrate muss als endlicher positiver reeller Skalar vorliegen;
boolesche Werte sind ausgeschlossen. Die Zeitachse wird kopiert. Der Baum
wird weder umgebaut noch verändert. Ungültige Bäume werfen
`InvalidTreeError`, gültige nicht unterstützte Strukturen bleiben als
`not_supported` dokumentiert. Ungültige Zeitwerte erzeugen `ValueError`;
ungültige Typen der Abtastrate `TypeError`, ungültige Werte `ValueError`.

Das Ergebnis ist ein neuer JSON-kompatibler In-Memory-Datensatz im Format
`ringdown-sr-parameter-analysis-1`, keine geschriebene Datei:

| Feld | Bedeutung |
| --- | --- |
| `structure` | Unveränderte Bedeutung des eigenständigen Strukturergebnisses einschließlich exakter rationaler Koeffizienten; dessen `not_attempted`-Felder beschreiben nur Stufe 1 |
| `raw_parameters` | Vorzeichenbehaftetes `A`, `b`, `c`, rationale Radiantphase `d`, rohe Frequenzen und gegebenenfalls Abklingzeit als getrennte numerische Felder |
| `raw_replay` | Vergleich der kanonischen rohen Form mit dem unveränderten Float64-Originalbaum |
| `alias` | Abgesicherte Alias-/Phasenreduktion oder Grund, weshalb sie nicht vorgenommen beziehungsweise nicht bestimmt wurde |
| `alias_replay` | Gesonderter Vergleich der numerischen Aliasform mit dem Originalbaum auf denselben gespeicherten Zeiten |
| `identifiability` | Exaktes `A=0`, DC-/Nyquist-Kennzeichnung und ausdrücklich `physical_identification=not_assessed` |

Numerische Felder haben `value`, `status`, `reason`. `available` bestätigt
die abgesicherte Float64-Darstellung des jeweiligen mathematischen Werts.
Es bestätigt weder den Replay noch physikalische Identifikation.
`numerical_unresolved` enthält `value=null` und einen konkreten Grund.
Bei `b>=0` ist die Abklingzeit `not_applicable` mit `undamped` oder `growing`.
Für `b<0` gilt exakt `tau=-1/b`. Das Amplitudenvorzeichen bleibt erhalten.

Die rohe vorzeichenbehaftete Frequenz lautet `c/(2*pi)`, ihr Betrag steht
separat daneben. Beide verwenden mathematisches π. Beispielsweise ergibt
die Grundform `2*exp(-125*t)*cos(512*t+0.25)` die Abklingzeit `0.008 s`
und rohe Frequenz `256/pi Hz`. Diese Frequenz ist keine automatisch
identifizierte erzeugende Frequenz.

## Exakte Eingaben und begrenzte Intervallentscheidung

`aliasing.py` verwendet ausschließlich die Standardbibliothek. Die
Referenzschnittstelle verlangt `int` oder `Fraction`, keine implizit
interpretierten Floats. Ein gespeicherter Float64-Wert wird ausdrücklich
mit `Fraction.from_float(value)` übergeben. Es muss genau eine Frequenzart
vorliegen: `frequency_hz` oder `angular_frequency_per_s`.

```python
from fractions import Fraction
from ringdown_sr.aliasing import Phase, reduce_alias

reference = reduce_alias(
    sample_rate_hz=4096,
    frequency_hz=4346,
    phase=Phase("pi_multiple", Fraction(1, 5)),
)
```

Dieses analytische Beispiel liefert `250 Hz`, Orientierung `+1` und exakt
`pi/5` als Aliasphase. `Phase("radian_rational", Fraction.from_float(d))`
bedeutet dagegen einen rationalen Radiantwert. Die Baumroute verwendet
ausschließlich rationale Radiantphasen aus der Koeffizientenextraktion.
`Phase("pi_multiple", 1)` ist mathematisch exakt π; `float(pi)` ist es
nicht. Eingabeart und exakte Brüche werden protokolliert.

Die Reduktion verwendet `k=floor(nu/fs+1/2)`, `q=nu-k*fs` und
`s=-1` für negatives `q`, sonst `+1`. Ausgegeben werden `abs(q)` und
die auf `[-pi,pi)` reduzierte Phase `s*d`. Bei ausdrücklich deklarierten
π-Vielfachen wird π im Reduktionsquotienten symbolisch gekürzt.

Rationale π-Einschlüsse entstehen aus der Machin-Identität und
alternierenden `atan`-Reihen. Je Reihe werden 16, danach gegebenenfalls
32 und höchstens 64 Terme ausgewertet. Ganzzahlige Quotienten und
Vorzeichen müssen für das gesamte Intervall eindeutig sein. Ein
Float64-Wert wird nur akzeptiert, wenn das gesamte Intervall strikt in
seiner exakten Rundungszelle liegt. Berührte Halbierungsgrenzen dürfen
konservativ unbestimmt bleiben. Nichtnullwerte, die auf null runden,
werden nicht als exakte Nullwerte ausgegeben.

Das Ergebnisformat `ringdown-sr-alias-reduction-1` bewahrt Frequenz- und
Phaseneingabe, rationale Abtastrate, verwendetes Reihenbudget,
Frequenz-/Phasenquotienten `k`/`m` als Dezimalzeichenfolgen, Orientierung
und exakte Aliasphase als `radian_part + pi_multiple*pi`. Verlässlich
bestimmte Teilfelder bleiben bei einem später nicht bestimmbaren Feld
erhalten. Die Gesamtverfügbarkeit erfordert beide numerischen Aliasfelder
und eine bestimmte Randklassifikation.

Ein nachweislich innerer Frequenzwert muss auch nach der Float64-Rundung
strikt zwischen null und der exakten rationalen Nyquistgrenze `fs/2` liegen.
Rundet er auf null, an die Nyquistgrenze oder darüber hinaus, bleibt er
`null` mit `boundary_rounding`. Dies gilt auch, wenn `fs/2` selbst nicht als
Float64 darstellbar ist. Beispiel:
`c=2*float(pi)*2048` liegt mathematisch knapp unter Nyquist. Die rohe
Hz-Ausgabe darf korrekt auf `2048` runden; die Aliasdiagnose kennzeichnet
ihn dennoch als inneren Wert und gibt keinen falschen exakten Nyquistwert
aus. Große rationale Winkel können das Reihenbudget erschöpfen. Dann
lautet der Status `numerical_unresolved`, ohne Float64-Modulo-Fallback.

## Raster, Replay und Aussagegrenzen

Die Aliasdiagnose gilt nur für den Nullursprung `t[j]=j/fs`. Die vorhandenen
Float64-Zeiten müssen exakt mit `sample_times(N, fs)` übereinstimmen;
es gibt keine Toleranz zum Anpassen fremder Achsen. Eine verschobene oder
unregelmäßige Achse behält den rohen Replay, erhält aber keine Aliasdiagnose.

Der Originalbaum wird in seiner ursprünglichen binären Reihenfolge mit
`evaluate_tree` ausgewertet. Getrennt werden
`A*exp(b*t)*cos(c*t+d)` und, wenn verfügbar,
`A*exp(b*t)*cos(2*float(pi)*f_alias*t+d_alias)` verglichen.
Die gemeinsame Skala ist `max(maxabs(original),maxabs(replay))` ohne
absolute Untergrenze. Danach gelten `rtol=1e-12`, `atol=1e-14` in normierten
Einheiten mit dem Originalbaum als relativer Referenz. Beide exakt nullen
Vorhersagen bestehen. Nicht endliche Vorhersagen und abweichende Kurven
werden als fehlgeschlagener Replay bezeichnet; nicht verfügbare
Koeffizienten beziehungsweise Aliasfelder als `not_attempted`.

Skala, maximaler normierter Unterschied und Toleranzen werden bei endlichen
Vergleichen gespeichert. Ein Vorzeichenfehler bei `1e-21` scheitert ebenso
wie bei Amplitude eins. Ein gleicher Verlust genügt nicht. Mathematisch
gleiche rationale Reduktionen mit unterschiedlicher Float64-Klammerung
können deshalb erkannt sein und trotzdem einen fehlgeschlagenen Replay haben.

Exaktes `A=0` und unterlaufende Nichtnullamplituden bleiben unterscheidbar.
Bei DC oder Nyquist sind Amplitude und Phase nicht getrennt identifizierbar;
bei `A=0` sind auch Frequenz und Abklingzeit aus der Nullkurve nicht
identifizierbar. `degeneracy=none` schließt nur diese beiden exakten
Frequenzrandfälle aus. Es beweist keine vollständige Identifizierbarkeit,
insbesondere nicht bei kurzen Fenstern oder gegenüber der
Amplitudenvorzeichen-/Phasenmehrdeutigkeit. Bestandene Replays betreffen
ausschließlich die angegebenen Samples. Sie belegen weder Gleichheit
zwischen Samples noch Rekonstruktionsleistung oder Generalisierung.

## Prüfungen

```bash
uv run --locked pytest -q tests/test_aliasing.py tests/test_parameters.py
```

Die bestehenden unabhängigen Hz-/π-Referenzen bleiben unverändert.
Zusätzliche Fälle prüfen rationale Machin-Tangensrechnung, einschließende
Reihen, Rundungszellen, π und seine Float64-Nachbarn beider Vorzeichen und
Orientierungen, Winkel-Nyquist, Budgeterschöpfung, Unter-/Überlauf,
Auswertungsreihenfolge und kleine Signale. Die Module starten weder
PySR noch Julia. Neue freie Suchen gehören nicht zu diesem Prüfumfang.
