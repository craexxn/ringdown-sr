# Begrenzter Kreuzvergleich von Seeds und historischen Ausführungspfaden

Angenommener Diagnoseschritt vom 05.11.2026 nach dem
[Transferbefund](transfer_check_results_manjaro_001.md). Dieser Plan wird vor
der Implementierung durch Commit und SHA-256 gebunden. Er ergänzt genau zwei
frische Manjaro-Zellen; keine neue Budgetstaffel und keine Leistungsstudie.

## Frage und Auswahl vor Ausführung

Die äußere Staffel erreichte bei 500/300/5 fünf Kurvenerfolge mit den Seeds
20261201–20261205. Der frische anchor des Transferchecks erreicht mit
20261210–20261212 keinen. Die bisherigen Nachrechnungen bestätigen die
gespeicherten Ergebnisse, unterscheiden aber Seedabhängigkeit nicht kausal
von einer unentdeckten Änderung des Ausführungspfads.

Aus jedem ursprünglichen Block wird die erste passende Zelle gewählt,
ohne Auswahl nach besonders kleinem oder großem Fehler. Beide Zielrichtungen
und ihre Reihenfolge stehen vor Ausführung fest:

| Neue Zelle | Seed | Historische Referenz | Neuer Ausführungspfad |
| --- | --- | --- | --- |
| 1 | 20261201 | äußere Staffel, Zelle 2, 500 Iterationen, C=true | Transferpfad am Commit bc4025d |
| 2 | 20261210 | Transfer, Zelle 1 (anchor), C=false | Staffelpfad am Commit 5215c5e |

Die Gegenrichtungen liegen bereits als historische Originale vor. Es gibt
keine weiteren frischen Kontrollzellen, Ersatzseeds oder automatischen
Wiederholungen. Der Vergleich ist nach Kenntnis der Erfolge ausgewählt und
deshalb keine neue Schätzung einer Erfolgswahrscheinlichkeit.

## Unveränderte Daten und Suchparameter

Beide neuen Zellen verwenden ausschließlich den bekannten rauschfreien anchor:
A=1, f=250 Hz, tau=0,008 s, phi=0 rad. Die 128 Trainingszeiten bei 4.096 Hz
und alle Beobachtungen müssen bitgleich zwischen beiden Originalarchiven
und dem eingefrorenen Transferdatensatz sein. Ebenso die 889 getrennten
Zwischenpunkte und Diagnosewahrheiten. Keine Neugenerierung der Eingaben.

Unverändert: 500 äußere Iterationen, lokal maximal 300 Iterationen und fünf
zusätzliche Neustarts, allgemeine Grammatik, `should_simplify=false`,
Float64, Sekundenkoordinate, gewöhnliche MSE, beide Häufigkeitsschalter an,
zwei Populationen à 32, 50 Zyklen je Iteration, maxsize/maxdepth 20 und
Parsimony 0. Originalauswahl, Strukturerkenner, Parameterregeln,
native/Python-Verlustprüfungen, Normalbereich, MPFR-Vorhersagereferenz,
unabhängige Elternnachrechnung und tatsächlicher Suchaufrufschutz bleiben erhalten.
Genau ein frischer equation_search-Aufruf je Zelle; keine Warmstarts,
Nachfits, geratenen Startformeln oder Archivzustände.

## Historische Quellen und Referenzen

Ausführung aus sauberen, isolierten detached Git-Worktrees der beiden
Originalcommits, niemals aus Programmen oder serialisierten Zuständen der
Ergebnisarchive:

- Staffel: `5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4`,
  `scripts/run_outer_search_ladder_worker.py` und dessen ursprüngliche
  Quellen-/Laufzeitbindung.
- Transfer: `bc4025d13b4954dee779341026d282430521686a`,
  `scripts/run_transfer_check_worker.py` und dessen ursprüngliche Bindung.

Ein gemeinsamer Diagnoseaufruf steuert nur den einzelnen festen Seed und die
einmalige Zelle statt der historischen Vollserie. Native Optionsvorprüfung
für diesen Seed, unveränderte feste Referenzprüfungen und der jeweilige
Elternprüfpfad werden weiterverwendet. Historische Quellen werden nicht
gepatcht. Der Diagnoseadapter und sein Aufruf werden zusätzlich protokolliert.
Der Befund betrifft diese beiden historischen Workerpfade unter dem gemeinsamen
Einzelzelladapter, nicht sämtliche Abläufe der früheren Vollserien.

Beide vollständigen Originalarchive sind erforderlich und bleiben unverändert:

- `outer-ladder-manjaro-001.tar.gz`, SHA-256
  `ac7e841b79042e216d6aacae2961ffb8395f298bbcc7ecc11f1092c90b3deb40`.
- `transfer-manjaro-001.tar.gz`, SHA-256
  `e363fe1be629973a460fc6e2188bf680c21b2c5519d331bc7e257968dcaaa139`.

Vor einer neuen Suche: sichere Archivstruktur, vollständige Abschlussmanifeste,
saubere Herkunft am erwarteten Commit, festgelegte Referenzzellen, Datenbits,
native Optionen und gespeicherte Referenzkandidaten prüfen. Fehlende Historie
oder Originale führen zum Abbruch, nicht zum Abschalten von Prüfungen.

## Umgebung und Grenzen

Ausführung auf demselben Manjaro-Rechner wie beide Originale. Python 3.12.14,
Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1, Haswell und Threadlimit 1.
Die festgelegte Paketumgebung und die tatsächlich geladenen numerischen
Bibliotheken müssen zu beiden Referenzen passen; ausführungsabhängige Pfade,
Zeitstempel und Prozessnummern sind keine Gleichheitsmerkmale. Die archivierte
Maschinen-/Plattformangabe wird geprüft, ersetzt aber keine Hardwareidentität.
Bei abweichenden relevanten Umgebungsmerkmalen stoppt die Diagnose vor der
wissenschaftlichen Suche. Keine automatische Anpassung oder Ersatzreferenz.

Grenzen: **900 Sekunden je Suchworker, 3.600 Sekunden insgesamt** einschließlich
Quellenvorbereitung, Vorprüfung, Elternarbeit und Finalisierung. Keine
Laufzeitprognose. Nur selbst angelegte Hilfsworktrees dürfen ohne Force entfernt
werden; vorhandene Worktrees und unversionierte Dateien bleiben erhalten.
Fehler, Signale und Fristablauf erhalten sämtliche verfügbaren Teilstände
und sperren positive Gesamtbefunde. Ausgabeziel:
`results/seed-driver-crosscheck-manjaro-001.tar.gz`.

## Vorab festgelegte Gleichheitsmerkmale und Auswertung

Jede neue Front wird gegen ihre zugehörige historische Originalfront verglichen:

1. Vollständige Kandidatenzahl und ursprüngliche Reihenfolge; alle Originalbäume
   mit ihren Float64-Konstanten, Komplexitäten, nativen Verlustbits,
   Vorhersage-/Residualbits, Originalauswahlindex und aufgezeichnete RNG-Seeds.
2. Tatsächliche effektive Suchparameter und native Optionsfelder mit Ausnahme
   des Ausgabeorts; Zahl der Zielfunktionscallbacks während des Fits.
3. Kurvenmarker, unterstützte Struktur und Parameterbefund separat; unveränderte
   C-Grenzen RMS ≤ 0,001 und Maximum ≤ 0,01 auf beiden Rastern.

Keine Gleichheit ganzer JSON-Dateien mit unterschiedlichen Zeit-/Pfadangaben
fordern. Gemessene Laufzeiten getrennt ausgeben; sie sind kein deterministisches
Gleichheitskriterium. Ein gleicher C-Marker allein genügt nicht als Nachweis
gleicher Suchergebnisse.

- **Beide vollständigen Fronten und Suchmerkmale gleich:** Die beiden gezielten
  Gegenrichtungen reproduzieren die historischen Ergebnisse. Das spricht gegen
  einen Unterschied dieser Workerpfade als Erklärung und für Seedabhängigkeit
  in diesen Fällen. Kein Ausschluss aller technischen Ursachen, keine garantierte
  Robustheit und keine Aussage, welches größere Budget helfen würde.
- **Mindestens ein gültiger Unterschied:** Abweichung je Merkmal sichtbar machen,
  auch wenn C unverändert bleibt. Ein konkreter Ansatzpunkt für eine technische
  Ursachenanalyse, aber noch kein Beweis eines Codefehlers oder eines bestimmten
  Mechanismus; historischen Laufzeitkontext mit berücksichtigen.
- **Unvollständiger Lauf oder ungültiger Nachweis:** keine Zuordnung zu den
  beiden positiven Vergleichsaussagen; Teilstände vollständig archivieren.

Der Vergleich verändert keine ursprünglichen Ergebnisse und keine C-/S-Zählung
der abgeschlossenen Serien. Die Erkennungsgrenzen, der 8·fs-Blindfleck und
`physical_identification=not_assessed` bleiben bestehen. Danach den nächsten
Schritt begründen; keine automatische Suchoptimierung oder Budgeterhöhung.
Rauschpipeline, gebundenes Pilotdesign und Hauptversuchsplan bleiben vorgemerkt;
die Hauptstudie selbst ist nicht Teil dieses Auftrags.

## Technische Prüfung ohne wissenschaftliche Cloud-Suche

Gezielte Gegenfälle prüfen Archiv-/Quellenmanipulation, falsche Seeds oder
Budgets, Datenrollen, Umgebungsabweichungen, Gleichheitsmerkmale, Fehler,
Zeitgrenzen und gesperrte Teilberichte. Eine native Integration darf beide
historischen Workerpfade ausschließlich auf eigenen acht Punkten
t=j/8, y=1+t, mit Seed 73 und zwei äußeren Iterationen ausführen.
Die beiden vollständigen Kontrollfronten müssen übereinstimmen. Diese beiden
Miniworker sind technische Tests, keine der wissenschaftlichen Kreuzvergleichszellen.
