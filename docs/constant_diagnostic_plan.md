# Begrenzte Diagnose der Ringdown-Konstantenanpassung

Beschlossen am 30.10.2026 durch Nutzerannahme der Empfehlung aus dem
[übermittelten KI-basierten Methodenreview](representation_next_step_review.md#übermittelter-ki-basierter-reviewbefund).
Basis: PR #41, Merge `978738c38e36e7bcb82c83acb5ba85db6df078f0`.
Dieser Plan wird als Laufzeiteingabe mit Prüfsumme gesichert. Änderungen
benötigen vollständige CI und einen neuen Methodenbeschluss.

## Frage und Aussagegrenze

Kann der echte Mehrkonstantenpfad von SymbolicRegression 2.5.1 die bekannte
Ringdown-Struktur unter 20/2 von deklarierten abweichenden Starts anpassen?
Der Vergleich 100/2 untersucht ausschließlich einen diagnostischen Budgetfaktor.
Mögliche Befunde: Budgetbegrenzung, Startabhängigkeit, andere lokale Begrenzung
oder kein nachgewiesener Engpass für diese Fälle. Gute feste Fits erklären
weder Strukturentdeckung noch Strukturerhaltung in der freien Suche.

Optionen B (Suchverlauf), C (Übertragbarkeit), D (engere Modellklasse) und
E (Pause) wurden erwogen. A prüft zuerst eine offene technische Voraussetzung
mit begrenztem Aufwand. Danach folgt kein automatischer Folgeversuch.

## Daten, Baum und privilegierte Starts

Die unveränderten 128 Trainingswerte aus `representation-manjaro-001` werden
binär übernommen. Originalarchiv-SHA-256:
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Der Launcher liest das Archiv nur als Daten, prüft diese Identität und konsumiert
nur `training.npz` und `diagnostic.npz`; er führt keinen Archivcode aus.
Die 889 inneren Achtelpunkte bleiben ausschließlich nachgelagerte Diagnosen.

Ein einziger Baum: `A * (exp(b*t) * cos(c*t + phi))`, 13 Knoten,
Konstantenreihenfolge `A,b,c,phi`. `b=-1/tau`, `c=2*pi*f` werden einmalig
bei der Startbildung berechnet. Beide Zeitrollen in Sekunden. Alle vier
Konstanten bleiben frei, einschließlich der Phase. Keine zusätzliche Schranke.

| Start | A | f / Hz | tau / s | phi / rad |
| --- | --- | --- | --- | --- |
| L1 | 0,9 | 247,5 | 0,0072 | -0,1 |
| L2 | 1,1 | 252,5 | 0,0088 | 0,1 |
| L3 | 0,9 | 252,5 | 0,0088 | -0,1 |
| L4 | 1,1 | 247,5 | 0,0072 | 0,1 |

Entfernte Starts R1 bis R4: kartesisches Produkt in der Reihenfolge
`(128,T/8), (128,T/2), (512,T/8), (512,T/2)` für `(f,tau)`,
`T=128/4096 s`, `A=max(abs(y))`, `phi=pi/2`.
Die bekannten Strukturen und wahrheitsnahen Starts sind privilegierte
Methodenentwicklung. Keine Erfolgswahrscheinlichkeit oder unabhängige
Validierung wird aus diesem Startgitter geschätzt.

## Numerischer Pfad, Zufall und Reihenfolge

Direkter unveränderter Backendaufruf `SymbolicRegression.optimize_constants`,
bestehender voller Verlustcallback mit Einheitenprüfung, gewöhnliche MSE,
Float64, BFGS mit Backtracking, numerische Differentiation und bestehende
Abbruchtoleranzen. Zwei zusätzliche Neustarts vom ursprünglichen Startvektor.
Keine analytische Voranpassung, alternativen Solver oder Koordinaten.
Beide Häufigkeitsschalter aus; freies Suchbudget null.

Acht Starts, je drei Python-Seedkennungen 20261020/21/22 mit der bestehenden
PySR-Abbildung `RandomState(seed).randint(0, 2**31-1)`, je Budgets 20 und 100.
Jeder Aufruf verwendet ein frisches Xoshiro und einen frischen Prozess.
Die 24 Paare werden nach Start, dann Seed geordnet; erstes Paar 20 vor 100,
zweites 100 vor 20, danach abwechselnd. Insgesamt genau 48 Backendaufrufe,
höchstens 144 lokale Optimierungen; keine Wiederholung bis zum Erfolg.
Der Anfangszustand und die wirklichen Restartvektoren müssen je Paar gleich
sein. Dies rekonstruiert keinen fortgeschrittenen historischen Such-RNG.

Vor jedem Budgetprofil fünf feste Kontrollen ohne Optimierung: richtiger
Referenzbaum, optimale Konstante, dimensionswidriges `sin(t)`, Aliase 4346 und
33018 Hz. Optionen einschließlich konkreter Plugins werden vollständig gegen
das bestehende native Baselineobjekt geprüft. Erlaubte Unterschiede sind
Verlust-Verifikationshülle und beobachtender Optimierercallback sowie allein
für 100/2 die Iterationszahl. Die Beobachtung verändert weder RNG-Ausgaben
noch Optimiererentscheidungen. Diese Eigenschaft wird technisch gegengeprüft.

## Artefakte und Auswertung

Pro Aufruf: Anfrage, Daten-/Quell-/Laufzeitmanifest, Start- und Rückgabebaum,
Vorhersagen, Residuen, Anfangs-/Endverlust, RNG-Typ und Zustände, tatsächliche
Neustarts, lokale beobachtete Zustände, Callbackzahlen und Wandzeit.
Beobachtungswerte einschließlich nichtendlicher Zahlen werden verlustfrei
als Float64-Hexwerte gespeichert. Nicht verfügbare Konvergenz-/Abbruchinformationen
bleiben ausdrücklich `unavailable`; Callbackanzahl ist kein Solverstatus.
Der Backendpfad liefert nur das ausgewählte Ergebnis und den Evaluationszähler,
keine einzelnen abschließenden Optim-Resultate.

Auswahl unverändert durch das Backend: bester lokaler Trainingsverlust;
ohne strikte Verbesserung bleibt der Ausgangsbaum. Keine Auswahl anhand der
Wahrheit oder Zwischenpunkte und keine Auswahl des besten Seeds als Gesamtbefund.
Unabhängige Baumvorhersagen, Residuen und MSE jedes Rückgabebaums prüfen.
RMS und Maximalfehler auf beiden Rastern mit Grenzen 0,001 beziehungsweise
0,01. Rohe/aliasbezogene Parameter nur mit bestehenden Replay-Gates.
`physical_identification` bleibt `not_assessed`, insbesondere wegen des
bekannten Achtelraster-Blindflecks bei `8*fs`.

Gepaarte Differenzen 100 minus 20, getrennt nach L/R; alle Einzelbefunde und
Nenner erhalten. Quellen, Originaleingabe und konsumierte Dateien abschließend
gegen zuvor eingefrorene Bytes prüfen. Jede Abschlussabweichung sperrt sämtliche
Zusammenfassungen und Differenzen. Auch technische Fehler und unvollständige
Serien geben keine vollständige Gruppenstatistik frei.
Eine analytische Gradientenrechnung ist optional und kein weiterer Fitarm.

## Abbruch und Weiterentscheidung

60 Minuten Gesamtwandzeit einschließlich aller Prozessstarts, Vorprüfungen
und Verifikation. Ressourcenabbruch bleibt unvollständig, Teilstände bleiben
erhalten. Quellen-, Daten-, Options-, RNG- oder Replaywidersprüche stoppen
sofort. Nichtkonvergenz und schlechte Kurven sind Ergebnisse. Keine Ersatzläufe.
Haswell sowie OPENBLAS-/OMP-/MKL-/NUMEXPR-Threadlimit 1 für diesen Pfad;
allgemeine Suchprofile bleiben erhalten.

- Alle zwölf nahen Fälle bestehen unter 20/2: allgemeines lokales Versagen
  für diese Fälle nicht gestützt; nächste Strukturverlaufsfrage neu begründen.
- Nachweislich erreichtes Iterationslimit bei 20 und gute Kurven bei 100:
  Budgetbegrenzung für diese Fälle; spätere freie Intervention gesondert beschließen.
  Ohne verfügbaren Abbruchstatus nur Verbesserung unter größerem Budget berichten.
- Nahe Starts gut, entfernte schlecht: Startabhängigkeit; keine automatische
  Budgeterhöhung und keine Aussage über tatsächlich besuchte Suchstarts.
- Nahe Starts auch unter 100 schlecht oder vorzeitig mit großem Fehler gestoppt:
  keine weitere Eskalation; Parametrisierung/Forschungsumfang neu entscheiden.
- Gemischt oder technisch unklar: keine eindeutige Ursachenbehauptung, keine Zusatzserie.

Zwölf von zwölf ist ein konservatives Entwicklungsgate, keine statistische
Garantie. Für freie Ringdown-Rekonstruktion genügt ein positives Ergebnis
nicht als Gate zur Rausch-/Gewichtungsstudie. Eine engere Parameterfitfrage
benötigt einen ausdrücklichen Beschluss und den klassischen Referenzfit.
Die wissenschaftliche Serie wird später am geprüften Stand auf Manjaro gestartet;
Cloud/CI prüfen ausschließlich technische Referenzen außerhalb dieser 48 Fälle.
