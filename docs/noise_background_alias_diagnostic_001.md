# Lesende Aliasdiagnose auf Hintergrundserie 002

Vorab festgelegte Mechanismusdiagnose vom 19.11.2026,
[Leitfadenphase 7](ringdown_recovery_roadmap.md). Ausgangspunkt ist der
[negative Auswahlpilot](noise_background_selector_pilot_001.md): Eine
Komplexitätsregel bevorzugte auch einfache hochfrequente Formeln mit großen
Zwischenpunktfehlern. Die vorliegende Untersuchung prüft die konkrete
Abtastsymmetrie und begründet eine mögliche Intervention an der Datenerfassung.
Sie entwickelt keine weitere Auswahlregel.

**Stand dieses Vorabplans:** Umfang festgelegt; neue Aliasauswertung und
unabhängige Gegenrechnung noch nicht abgeschlossen. Noch keine neuen
wissenschaftlichen Ergebnisse, keine neue Suchserie und kein Studienprotokoll.
Die bereits untersuchten Daten bleiben retrospektive Entwicklungsdaten.

## Festgelegter Umfang und Herkunft

Der maschinenlesbare Umfang `scope.json` wurde vor der neuen Auswertung
festgelegt, SHA-256
`a49af2fe6fde886a6f877ee44dcfdf63e31c779adc5d94e1fe76aea62022a12c`.
Dokumentationsbasis ist `bb14b5a29163c330f4ba38237ce55419b9fa944f`.
Die ursprüngliche Suche lief auf
`bd42634b888c2dbaa5a92726b9a1f9851c766a48`; ihr unverändertes Archiv
`noise-background-manjaro-002-plots-recovered.tar.gz` hat SHA-256
`b2a4ace2d9097099822ab524377537dae24d59c7ba59e137de11ae5ba3e4214d`.
Der vorausgehende Auswahlpilot ist durch seine Scope-SHA-256
`119040430ace6ad80d788c6289e6fb03e5199e5fada1277e8949b3cf5afbd1ea`
und Summary-SHA-256
`a6805b42d7f59aae88e1090c3101d0d7c775329a3834f14df243ddbd69f2a09d`
gebunden.

Inventarisiert werden sämtliche `sin`-/`cos`-Knoten der **260 bereits
ausgewählten Originalbäume aus 130 Paketen**, jeweils `accuracy` und
`pooled_best`. Das vollständige Inventar erhält Fall, Arm, Auswahl,
Kandidatenidentität, vollständige Originalformel und Baumhash. Es werden
keine weiteren Kandidaten ausgewählt und keine Originaldateien verändert.

Die Affinität einer Phase `a*t+b` wird aus den gespeicherten endlichen
Binary64-Konstanten mit exakten rationalen Zahlen (`Fraction`) geprüft.
Zulässig sind Variable 1, Konstanten, Addition, Subtraktion, Multiplikation
mit mindestens einem exakt konstanten Operanden und Division durch einen
exakt konstanten Nenner ungleich null. Andere Operationen und argumentierte
Kürzungen erhalten `not_certified`. Das bedeutet weder nachgewiesene
Nichtaffinität noch Aliasfreiheit. Insbesondere bleiben nichtlineare Phasen,
verschachtelte Funktionen und Definitionslücken separat ungeprüft.

## Mathematische Aussage und numerische Grenze

Zunächst wird aus den gespeicherten 128 Zeitpunkten geprüft, ob exakt
`t_j=j/4096` für `j=0,...,127` gilt. Für `fs=4096 Hz` ist dann in reeller
Arithmetik, für jedes ganzzahlige `k` und beide trigonometrischen Funktionen:

```text
sin/cos((a + 2*pi*k*fs)*t_j + b) = sin/cos(a*t_j + b).
```

Sind die äußeren Operationen definiert, bleiben damit auch ihre Samplewerte
und jede Verlustfunktion derselben Residuen mit positiver definiter
Kovarianz gleich. Ein Wechsel einer Frequenzkonstante benötigt keine größere
Baumtopologie. Mehr Suchseeds, eine andere Gewichtung derselben Samples oder
die Knotenzahl allein heben diese exakte Mehrdeutigkeit daher nicht auf.

Pro zertifizierter nichtkonstanter Phase werden vorzeichenbehaftetes
`a` in rad/s, `f=a/(2*pi)` in Hz, der Repräsentant `f0` im halboffenen
Intervall `[-fs/2,fs/2)` und `k=floor(a/(2*pi*fs)+1/2)` dokumentiert.
Die Bestimmung von `k` muss bei MPFR-Präzision 128 und 256 Bit übereinstimmen.
Ein mathematisch exakter irrationaler Frequenzversatz ist im Allgemeinen
nicht als Binary64-Konstante darstellbar. Deshalb werden Reellidentität,
gerundete konstruierte Formel und gemessene numerische Abweichung getrennt.
Es wird keine bitgenaue Gleichheit konstruktiver Float64-Replays behauptet.

Ein gebundener Träger liegt nicht deshalb unterhalb einer Schranke, weil
ein Repräsentant dort liegt. Dafür wäre zusätzliche physikalische Information
nötig. Eine abklingende endliche Ringdown-Kurve ist zudem nicht streng
bandbegrenzt; eine Trägergrenze wäre kein Zertifikat des gesamten Spektrums.
Für eine beliebige freie Ausdrucksklasse liefern endlich viele Samples
keinen allgemeinen Identifizierbarkeitsbeweis.

## Drei festgelegte konstruierte Diagnosebeispiele

Die Beispiele stammen bereits aus dem veröffentlichten Auswahlpilot:

| Ausgabe | Rolle im bisherigen Befund |
| --- | --- |
| `ar1-10--estimated_1024--best` | Einfaches AR(1)/E1024-Gegenbeispiel |
| `white-03--estimated_64--best` | Größte weiße Verschlechterung des unregelmäßigen RMSE |
| `ar1-20--ordinary--best` | Gegenbeispiel bei gewöhnlicher Gewichtung |

Jedes Beispiel muss genau einen trigonometrischen Knoten mit zertifizierter
affiner Phase und eine unterstützte exponentielle Hülle besitzen. Andernfalls
wird es als nicht verfügbar ausgewiesen; kein Ersatzbeispiel wird gesucht.
Für den Diagnosebaum bleibt alles außerhalb dieses Knotens unverändert;
seine Phase wird durch `a0*t+b` ersetzt. `a0=a-2*pi*fs*k` wird mit 256 Bit
berechnet und danach auf Binary64 gerundet, ebenso der rationale Achsenabschnitt.

Diese **konstruierten mathematischen Aliasrepräsentanten sind neue
Diagnoseartefakte**. Sie ersetzen weder die Originalformel noch die historische
Auswahl und gelten nicht als nachgewiesen rekonstruierte Wahrheit. Ihre
deterministische Definition erfolgt vor der erneuten Wahrheitsauswertung.
Es gibt keine Optimierung von Frequenzen, Koeffizienten oder Spitzen.

Original und Diagnosebaum werden ausschließlich auf den bestehenden
128 Trainings-, 889 regulären Zusatz- und 1024 unregelmäßigen Zusatzpunkten
verglichen. Native Trainingsvorhersagen bleiben erhalten. Ausgewiesen werden
Python-Replay gegen native Werte, Original gegen Konstruktion auf Trainingspunkten,
RMSE und Maximalfehler gegen die saubere Referenz auf jedem Raster sowie,
bei eindeutig gebundener Kovarianz, die Änderung der ursprünglichen Zielfunktion.
Plots aller drei Paare erhalten vollständige Originalformel und ausdrücklich
konstruierte Formel, Identitäten, Einheiten und vollständige Punkt-CSV.

## Analytische Offset-Gegenproben und Anschlussfrage

Gesonderte analytische Beispiele prüfen `k=1,2,3,4` und die Offsets
`delta=0, 1/2, 1/3, (sqrt(2)-1)/4`. Sie betreffen die Vereinigung von
ursprünglichen und verschobenen Zeitpunkten bei gemeinsamer Phase:
Ein Alias bleibt erhalten, wenn `k*delta` ganzzahlig ist. Eine bloße
Verschiebung des einzigen gleichmäßigen Aufnahmerasters mit freier Phase
hebt die Aliasmehrdeutigkeit nicht auf. Aussagen zu irrationalen Offsets
gelten für reelle Arithmetik, nicht als Nachweis für Binary64-Zeitgeber.
Die gedämpften Kosinusbeispiele sind mathematische Gegenproben mit bekannten
Signalparametern, keine zusätzlichen verrauschten Beobachtungen oder neuen
Studienseeds; ihre Punkte und Fehler bleiben von Studienmetriken getrennt.

Als eine begründete Anschlussrichtung wird ein echter Vergleich von
gleichmäßiger und ungleichmäßiger **Akquisition mit jeweils N=128** bei
gleicher Dauer, freier Grammatik, Suchprofil und unveränderter `accuracy`-Wahl
bewertet. Eine kontinuierliche stationäre exponentielle Kovarianz wäre dabei
eine ausdrücklich neue Erweiterung der bisherigen diskreten AR(1)-Annahme.
Ungleichmäßige Messzeitpunkte benötigen eine tatsächlich geeignete
Erfassungsmöglichkeit: Interpolierte vorhandene Werte, eine zweite
unabhängige Aufnahme oder ein stillschweigender Frequenzprior um die bekannte
Wahrheit beantworten diese Frage nicht. Ein konkretes Studienprotokoll,
Seeds, verrauschte Eingaben, Suchläufe und Erfolgskriterien werden hier
nicht festgelegt oder erzeugt.

## Ausstehende Nachweise

Nach der Ausführung werden Inventarzahlen, die drei vollständigen
Formelpaare und Rastervergleiche, analytische Gegenproben, unabhängige
Numerikprüfung, Plotprüfung, tatsächliche Kosten und Artefaktbindungen
nachgetragen. Rechengenauigkeit und Vollständigkeit sind getrennt von
wissenschaftlicher Bestätigung zu bewerten. Der Schluss wird auf die
tatsächlich nachgewiesene lokale Symmetrie und die begrenzte
Akquisitionsfrage beschränkt.
