# Begrenzte Strukturerkennung mit exakten Koeffizienten

Stand: 23.10.2026. `src/ringdown_sr/structure.py` setzt Schritt 1 des
[geprüften Methodenplans](parameter_interpretation_plan.md) um:
Erkennung eines begrenzten Musters und Extraktion seiner rohen Koeffizienten.
Die separate [Parameter-/Aliasdiagnose](parameter_diagnostics.md) ergänzt
inzwischen numerische Nachrechnung, Parameterumrechnung und Aliasreduktion.
Der vollständige lesende Diagnoseexport steht noch aus.

## Schnittstelle und Ergebnis

`recognize_ringdown(tree)` liest einen vollständigen exportierten Baum
und liefert ein unveränderliches `StructureRecognition`-Objekt. Sein
`coefficients`-Feld ist bei erkannter Struktur ein ebenfalls
unveränderliches `RawCoefficients`-Objekt mit `Fraction`-Werten:

| Python-Feld | Symbol und Bedeutung |
| --- | --- |
| `amplitude` | Vorzeichenbehaftetes `A` |
| `exponential_rate_per_s` | `b` im Exponenten `b*t` |
| `angular_frequency_per_s` | Vorzeichenbehaftetes `c` im Argument `c*t+d` |
| `phase_rad` | Rationale Radiantphase `d`, ohne Periodenreduktion |

Für `2*exp(-125*t)*cos(512*t+0.25)` ergeben sich exakt
`A=2`, `b=-125`, `c=512`, `d=1/4`. Die Funktion berechnet daraus weder eine
Frequenz in Hz noch eine Abklingzeit. Ein erkannter Ausdruck ist kein
Nachweis physikalischer Identifikation oder numerischer Gleichwertigkeit.

`to_dict()` erzeugt einen neuen In-Memory-Datensatz im Format
`ringdown-sr-structure-recognition-1`; es schreibt keine Dateien.
Rationale Koeffizienten werden unter `raw_coefficients.A/b/c/d` als
Dezimalzeichenfolgen für Zähler und Nenner gespeichert. Es gibt keine
Float64-Rückkonversion. Dadurch bleiben auch Produkte erhalten, deren
Betrag für Float64 bereits zu klein oder zu groß wäre.

Zustände:

- `structure_status`: `recognized` oder `not_supported` mit `reason`.
- `exponential_status`: bei erkannter Struktur `decaying`, `undamped`
  oder `growing`, bestimmt durch das exakte Vorzeichen von `b`.
- `amplitude_status`: `zero` oder `nonzero`, bestimmt durch das exakte `A`.
  Kleine Amplituden werden nicht auf null gesetzt; negative bleiben negativ.
- `phase_kind`: bei erkannter Struktur ausschließlich `radian_rational`.
  Ein gespeichertes `float(pi)` wird nicht als exaktes π interpretiert.
- `replay_status`, `parameter_interpretation`, `alias_status` bleiben
  ausdrücklich `not_attempted`; `physical_identification` bleibt `not_assessed`.

Bei `not_supported` fehlen Koeffizienten und Formzustände (`null`).
Ein nackter Null- oder Konstantenbaum wird nicht um fehlende Faktoren oder
Parameter ergänzt. Die Zehnerbruchschreibweise `0.1` wird als gespeicherter
Binärwert `3602879701896397/36028797018963968` gelesen, nicht als exakt `1/10`.
Vorzeichen von Float64-Nullen bleiben im ursprünglichen Baum erhalten;
die mathematischen Bruchkoeffizienten unterscheiden diese Vorzeichen nicht.

## Unterstütztes Muster und Vertragsprüfung

Unterstützt wird ein äußeres Produkt aus genau einem `exp(b*t)`, genau
einem `cos(c*t+d)` und rein skalaren rationalen Faktoren. Verschiedene
Reihenfolgen und Klammerungen dieser Produkte sind erlaubt. Der äußere
Vorfaktor kann fehlen. Skalare Faktoren dürfen aus Konstanten und
`+`, `-`, `*`, `/` bestehen, enthalten aber syntaktisch keine Zeitvariable.
Selbst ein äußerer Faktor `(t-t)+2` liegt deshalb außerhalb dieses Musters.

Argumente werden als affine Paare aus Steigung und konstantem Anteil
gelesen. Eine exakt konstante affine Teilrechnung darf als Faktor oder
Nenner innerhalb des Arguments verwendet werden; etwa `t/((t-t)+2)`.
Zwei Faktoren mit nicht verschwindender Steigung, ein zeitabhängiger
Nenner oder ein Nullnenner werden nicht weggekürzt. Der konstante Anteil
des Exponentialarguments muss exakt null sein.

Alle Knoten werden vor der Musterprüfung validiert, auch bei Amplitude
null oder einer schon erkennbar nicht unterstützten äußeren Struktur.
Die aktuelle Exportgrammatik lautet binär `+,-,*,/`, unär `exp,sin,cos`.
Operatorname und Index müssen dazu passen. Das Modul enthält diesen
festen Vertrag ohne Import der Suchlaufzeit; ein Integrationstest bindet
ihn an die tatsächliche Suchkonfiguration.

Die Validierung erwartet die exakt vom Export erzeugten Knotenfelder,
native JSON-Typen, Variablenindex 1 und endliche Konstanten in kanonischer
`float.hex()`-Darstellung. Zusätzliche Felder, fehlende Kinder oder etwa
boolesche Operatorindizes sind Eingabefehler (`InvalidTreeError`).
Der gespeicherte Suchvertrag begrenzt Bäume auf 20 Knoten. Gezählt werden
Knotenvorkommen, keine eindeutigen Python-Objektidentitäten; auch gemeinsam
referenzierte Teilobjekte zählen je Vorkommen. Die Begrenzung verhindert
unbeschränkte Rekursion bei übergroßen oder zyklischen Python-Eingaben.

Gültige, nicht unterstützte Bäume erhalten einen deterministischen Grund:

| Grund | Bedeutung |
| --- | --- |
| `exponential_factor_count` | Im äußeren Produkt ist nicht genau ein Exponentialfaktor vorhanden |
| `cosine_factor_count` | Im äußeren Produkt ist nicht genau ein Kosinusfaktor vorhanden |
| `non_scalar_outer_factor` | Ein weiterer äußerer Faktor ist kein rein skalarer rationaler Ausdruck |
| `nonzero_exponential_intercept` | Der Exponent enthält einen nicht verschwindenden konstanten Anteil |
| `unsupported_affine_operator` | Im Argument tritt ein zusätzlicher unärer Operator auf |
| `non_affine_product` | Im Argument werden zwei affine Ausdrücke mit nicht verschwindender Steigung multipliziert |
| `time_dependent_denominator` | Im Argument hat ein Nenner eine nicht verschwindende Steigung |
| `zero_denominator` | Eine zur Extraktion benötigte Division hat einen exakt verschwindenden Nenner |

Der Grund benennt die erste festgestellte Mustergrenze, nicht sämtliche
Eigenschaften des Baums. Eine äußere Summe oder Division wird deshalb
bereits durch die fehlenden äußeren Faktoren ausgeschlossen. `not_supported`
ist weder eine Aussage über die allgemeine mathematische Äquivalenz noch
eine physikalische Bewertung.

## Reelle Algebra und numerische Grenzen

Die Extraktion verändert den Eingabebaum nicht und nutzt keine Samples,
Signalwahrheit, Fitparameter, Verluste oder Zufallszahlen. Es wird nichts
nachoptimiert. Rationale Koeffizienten beschreiben eine mathematisch reelle
Umformung; sie bewahren die Reihenfolge der Float64-Operationen nicht.
Beispielsweise ergeben die Teilbäume `(1e16 + -1e16)+1` und
`1e16+(-1e16+1)` exakt rational beide 1, bei Float64-Auswertung aber
unterschiedliche Werte. Beide Strukturen dürfen mathematisch erkannt
werden, erhalten dadurch jedoch keinen bestandenen numerischen Replay.
Dieser bleibt eine eigene nachgelagerte Prüfung gemäß Methodenplan.

Die bisherigen Such-/Auswahlregeln, Schemas und Ergebnisdateien werden
nicht angefasst. Das Modul verwendet ausschließlich die Standardbibliothek
und initialisiert weder NumPy noch PySR oder Julia.

## Vorhandenen Kandidaten lesend ansehen

Im Checkout mit dem neuen Modul ausführen und den Dateipfad an einen
vorhandenen Ergebnisordner anpassen. Dies ist eine einzelne In-Memory-
Inspektion, kein vollständiger Herkunfts-/Verlust-Audit oder Diagnoseexport.
Es wird keine neue Suche gestartet:

```bash
uv run --locked python - <<'PY'
import json
from pathlib import Path
from ringdown_sr.structure import recognize_ringdown

path = Path("results/sr-portability-001/white/symbolic/ordinary/result.json")
front = json.loads(path.read_text(encoding="utf-8"))
candidate = front["candidates"][front["selected_index"]]
print(json.dumps(recognize_ringdown(candidate["tree"]).to_dict(), indent=2))
PY
```

Prüfungen des Moduls:

```bash
uv run --locked pytest -q tests/test_structure.py
```
