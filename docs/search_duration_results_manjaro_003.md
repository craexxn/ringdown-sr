# Audit: dritter Manjaro-Suchbudgetlauf

Stand: 04.11.2026. Originalarchiv `duration-manjaro-003.tar.gz`, SHA-256
`c39fb68ba6d98729ae64df83dd50feb332117d2204e2b49e49044cd1ebed5147`.
Sauberer Ausführungscommit: `e501e9d83315289cb4c59716495e93aa25154ecd`,
Squash-Merge von [PR #56](https://github.com/craexxn/ringdown-sr/pull/56).
Der Dateibaum entspricht dem dort geprüften Head `be887730d9f57c5fbede914240b57a3724e5eb6d`.
Keine Suche, kein Fit und keine Optimierung im Audit; Archivcode sowie
serialisierte Julia-/Python-Zustände wurden nicht ausgeführt.

## Herkunft, Profil und Teilstand

Archivhash, alle 143 Dateien, 96 ursprünglichen Verbrauchsanker und 69
gebundenen Quellen gegen Ausführungscommit und vertrauenswürdigen Checkout
geprüft. Planbytes, getrennte Eingaben, native Vorprüfung und Referenzen
stimmen. Alle vier abgeschlossenen Zellen mit ihren 34 Originalkandidaten,
Verlustnachweisen, Auswahlen und Diagnosen wurden erneut verifiziert.
Zusätzlich wurden CSV-Bäume und skalare Auswertungen unabhängig geprüft.
Alle Originaldateien blieben unverändert. Das frühere Eingangsarchiv
`representation-manjaro-001.tar.gz` lag nicht erneut vor; seine enthaltenen
Datenkopien und deren Bindungen wurden geprüft.

`should_simplify=false` ist in den Pythonparametern und tatsächlichen nativen
Optionsfeldern aller fünf gestarteten Zellen bestätigt. Auch die nativen
Optionsfelder der fehlgeschlagenen Zelle stimmen mit ihrem Vorprüfungsprofil
überein. Die Abhilfe aus #56 war aktiv.

| Zelle | Grammatik | Iterationen | Auswahlindex | Trainings-MSE | diagnostischer relativer RMS | Kurve | unterstützte Struktur / Parameter |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | unrestricted | 200 | 8 | 4,909673428862387e-20 | 8,73335562729797e-10 | innerhalb | erkannt / passend |
| 2 | no_nested_trig | 200 | 8 | 1,3875429276608905e-22 | 4,6419150804282696e-11 | innerhalb | nicht unterstützt / nicht beurteilt |
| 3 | no_nested_trig | 2000 | 7 | 2,4740390175966485e-24 | 6,197698389354278e-12 | innerhalb | nicht unterstützt / nicht beurteilt |
| 4 | unrestricted | 2000 | 7 | 8,45954602316965e-28 | 1,1466631381783856e-13 | innerhalb | nicht unterstützt / nicht beurteilt |

Alle vier Zellen verwenden Seed 20261103; Auswahlindizes sind nullbasiert.
Die Kurvenmarker gelten für Trainings- und Diagnoseraster. Die drei
`not_supported`-Befunde entstehen an Grenzen des vorhandenen Strukturerkenners,
unter anderem bei konstanten Teilbäumen und mehreren Exponentialfaktoren.
Sie werden nicht nachträglich umklassifiziert. Abschalten der Vereinfachung
kann sowohl Suchverläufe als auch die für diesen Erkenner sichtbare Darstellung
verändern. Die bessere Approximation allein belegt keinen isolierten Effekt
der Änderung und keinen Budget- oder Grammatikvorteil.

Gesamtdauer bis Abbruch: 526,7217 Sekunden. Zelle 5 scheiterte, Zellen 6–20
blieben `planned`. `status=incomplete`, `final_verification=failed`;
Gruppenaggregate, Paardifferenzen und Gesamtentscheidung sind `null`, das
Abschlussmanifest fehlt. Physikalische Identifikation bleibt `not_assessed`.

## Exakt reproduzierter Vorhersageabbruch

Zelle 5: `no_nested_trig`, Seed 20261104, 200 Iterationen. Nach 46,8463 Sekunden
Fitzeit scheitert der Worker beim Vergleich unabhängiger Python- und nativer
Vorhersagen, vor der Verlustprüfung des betroffenen Kandidaten. Der erste
Fehler stammt aus CSV-Index 5, Komplexität 10:

```text
sin(-8757.12034629967 / exp(-0.179918543499894 * t)) / exp(1.3478622678308743)
```

Am nullbasierten Messpunkt 18, `t=18/4096=0.00439453125` Sekunden, reproduziert
die feste Nachrechnung exakt die gemeldeten normierten Werte
`0.8396216040170885` und `0.8396216040180767`.
Der Abstand `9.88209514e-13` übersteigt die dortige Grenze
`1e-14 + 1e-12 * abs(native) = 8.49621604e-13` um etwa 16,3 Prozent.
Die Normierung verwendet die gemeinsame maximale Vorhersageamplitude;
dieser Abstand ist kein unnormierter Signalfehler.

Die Zwischenwerte lokalisieren den ersten Unterschied bei der inneren
Exponentialfunktion. Bis zu deren Argument stimmen beide Auswertungen exakt:

| Größe am Messpunkt 18 | Python/NumPy | Julia |
| --- | --- | --- |
| `exp`-Argument, Float64-Hex | `-0x1.9e8846667be65p-11` | identisch |
| `exp`-Ergebnis, Float64-Hex | `0x1.ff98686aa5742p-1` | `0x1.ff98686aa5743p-1` |
| anschließender Quotient, Float64-Hex | `-0x1.11e0603109615p+13` | `-0x1.11e0603109614p+13` |

Die `exp`-Ergebnisse sind benachbarte Float64-Zahlen: Abstand ein ULP,
`1.1102230246251565e-16`. Unabhängige Rechnungen mit 100 und 200 Dezimalstellen
ergeben dieselbe Float64-Rundung wie Julia. Die Fehler zum hochpräzisen
`exp`-Wert betragen etwa 0,51936 ULP für NumPy und 0,48064 ULP für Julia.
Die Division mit der großen Konstante verstärkt den Abstand auf
`1.8189894035458565e-12` im Sinusargument. Anschließender Sinus, Skalierung und
Amplitudennormierung ergeben den gemeldeten Grenzübertritt.

Damit ist für diesen festen Fall eine verstärkte Rundungsabweichung
nachgewiesen. Es wurde weder eine Baumumformung noch eine veränderte Konstante
benötigt. Der geltende globale Vorhersagevertrag lehnt den Fall trotzdem ab;
seine wissenschaftlichen oder numerischen Anforderungen werden durch diesen
Audit nicht rückwirkend geändert.

## Alle zehn CSV-Formeln und nachgelagerte Verlustbedingungen

Die zehn Formeln wurden mit einem Parser für ausschließlich numerische
Literale, `t`, die vier Rechenoperationen und `exp/sin/cos` aufgebaut.
Baum-Rundreise, native Komplexität und Grammatik wurden geprüft. Die
Auswertung nutzt vertrauenswürdige Quellen und die gepinnte Umgebung
Python 3.12.14, PySR 2.6.0, Julia 1.13.1 und SymbolicRegression 2.5.1.

- Alle zehn nativen Replayverluste stimmen **bitgenau** mit den durch
  `float` gelesenen CSV-Verlusten überein. Auch die gesonderte Vergleichsregel
  für die tatsächlich durch Pandas gelesenen Werte besteht.
- Native und Python-Verluste bestehen jeweils die unveränderten rationalen
  Reduktions- und Normalbereichsprüfungen gegen ihre eigenen Residuen.
  Auch die aus den Residuen abgeleitete Schranke für den Unterschied beider
  Verluste besteht bei allen zehn Formeln.
- Der Vorhersagevergleich scheitert bei vier CSV-Bäumen: Indizes 5, 6, 7 und 9,
  Komplexitäten 10, 12, 14 und 19. Der erste Abbruch verdeckt drei weitere
  Fälle; allein eine Anpassung für den ersten Messpunkt wäre unzureichend.
- 81 Teilbäume der sechs trigonometrischen CSV-Formeln wurden nativ, mit NumPy
  und hochpräzise ausgewertet. Die 100-/200-stellige Gegenprüfung oben bezieht
  sich ausdrücklich auf die erste verursachende `exp`-Operation.

Die Verlustbedingungen wurden im Audit einzeln ausgewertet, ohne den
produktiven Vorhersagevergleich abzuschalten oder einen positiven
Gesamtnachweis zu erzeugen. Die frühere gespeicherte/native Verlustabweichung
aus Lauf 002 tritt bei diesen zehn CSV-Replays nicht auf. Dies beweist keine
allgemeine Fehlerfreiheit des Backends.

Zelle 5 enthält keinen vollständigen `result.json`-Export, keine positive
Zellverifikation und keinen abgeschlossenen Aufrufnachweis. Die aus CSV
rekonstruierten Bäume sind keine authentifizierten nativen Originalexporte;
eine ursprüngliche Auswahl wird nicht nachträglich behauptet. Der kleinste
CSV-Verlust ist `7.441267463949453e-11` bei Index 9. Dessen beschreibende
Kurvennachrechnung ergibt relativen RMS etwa `3.30e-5` auf Trainings- und
`3.37e-5` auf Diagnosedaten, aber keine unterstützte Struktur. Das ist weder
ein freigegebener Zellbefund noch ein Grund für Ersatzwahl.

## Nächster abgegrenzter Schritt: Vorschlag, noch keine Umsetzung

Die Befunde sprechen für eine gesondert begründete **baumabhängige
Vorhersageverifikation**. Eine konstante Toleranz am Endwert berücksichtigt
nicht, wie kleine Rundungsunterschiede einzelner Operationen durch den
konkreten Ausdruck verstärkt werden. Ein bloßer Wechsel von NumPy zu skalaren
Bibliotheksfunktionen wäre ebenfalls keine allgemeine Genauigkeitsgarantie.

Vor Implementierung wäre festzulegen, wie eine unabhängige hochpräzise oder
Intervallreferenz zulässige lokale Rundungsfehler und deren Fortpflanzung
begrenzt. Ein zulässiger Bereich darf nicht lediglich so breit aus der
beobachteten Differenz konstruiert werden, dass der Kandidat besteht.
Voraussetzungen der transzendenten Funktionen, Auslöschung, Nähe zu Polen,
Unter-/Überlauf und unbestimmte Fälle benötigen ausdrückliche Regeln.
Lässt sich keine hinreichend enge Schranke begründen, bleibt der Nachweis
gesperrt; der Suchalgorithmus und die wissenschaftlichen Kurvengrenzen sollen
dafür unverändert bleiben.

Der konkrete Vorschlag umfasst feste Gegenprüfungen aller zehn CSV-Bäume,
falscher Konstanten/Operatoren und tatsächlich inkonsistenter Verluste,
anschließend passende technische Integration und eine versionierte Planbindung.
Originalverluste, Kandidatenreihenfolge, Auswahl, Datenrollen und vollständige
Serienpflicht bleiben erhalten. Eine Lockerung der Verlustschranken,
nachträgliche Normalisierung der Bäume oder Umwahl ist nicht vorgeschlagen.
Ein erneuter wissenschaftlicher Lauf ist mit diesem Audit nicht freigegeben.

Die Grenzen des Strukturerkenners sind ein zusätzlicher, getrennt zu
behandelnder Befund. Eine Erweiterung könnte die wissenschaftliche
Erfolgsklassifikation verändern und wird nicht stillschweigend mit der
numerischen Abhilfe verbunden. Frühere Pläne und Archive bleiben unverändert.
