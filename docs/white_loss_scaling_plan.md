# Kontrollierter Pilot zur Verlustskalierung bei weißem Rauschen

Vorab festgelegt am 23.11.2026, Leitfadenphase 7. Dieser neue Entwicklungsversuch
folgt auf die [Folgestudienauswertung](noise_followup_results_manjaro_001.md).
Die bisherigen wissenschaftlichen Protokolle und Auswahlen bleiben unverändert.
Der Plan wird vor der ersten neuen numerischen Untersuchung versioniert und
vom Laufweg über seinen SHA-256 gebunden. Implementierungsfehler werden getrennt
protokolliert; eine Änderung dieses Designs verlangt einen neuen Plan.

## Frage und festgelegte Vergleiche

Für weißes Rauschen mit C = sigma² I gilt analytisch L_K = MSE / sigma².
Die bereits geprüften festen Kandidaten bestätigen diese Identität bis auf
Float64-Rundung. Offen ist, ob die endliche Konstantenoptimierung und freie
Suche durch diese positive Skalierung andere Ergebnisse liefern.

Verglichen werden in frischen Prozessen drei Arme mit identischen Daten:

- O (`ordinary`): gewöhnliche MSE im bisherigen vollständigen Fensterkern.
- S (`scaled`): derselbe MSE-Kern, anschließend Multiplikation mit
  c = 1 / (sigma * sigma); sigma und c zusätzlich als Float64-Hexwerte binden.
- K (`covariance`): bisheriger Cholesky-Pfad mit exakt (sigma * sigma) I.

S minus O ist der kontrollierte Skalierungskontrast. K minus S prüft den
numerischen Kovarianzpfad beim selben mathematischen Maßstab. Keine Annahme,
dass unterschiedliche Endformeln bereits einen bestimmten Mechanismus beweisen.
Keine Umstellung von Grammatik, Auswahlregel, Messraster oder Komplexitätsgrenze.

## Daten und feste Budgets

Zwei neue Entwicklungsfenster mit PCG64-Seeds 2026112301 und 2026112302;
je 128 gleichmäßige Zeiten t_i = i / 4096 s, i = 0,...,127.
Das bekannte Entwicklungssignal bleibt
`(11/12) * exp(-t/(1/150)) * cos(2*pi*265*t + 0.25)`.
sigma = (11/12) * 0.05. Unabhängige normale Rauschziehungen je Fenster;
die vollständig gleichen Beobachtungsbits gehen in O/S/K ein.
Diese Signalkonfiguration ist keine neue Bestätigungsbedingung.

Suchseeds sind 2026112311, 2026112312 und 2026112313; ihre PySR-Abbildung
auf den nativen Seed wird gespeichert. Profile: serial, Float64, zwei
Populationen zu 32 Individuen, 50 Zyklen pro äußerer Iteration, maximal 20
Knoten, bisherige Operatoren und `accuracy`-Auswahl. Konstantenoptimierung
300 Iterationen und fünf zusätzliche Neustarts, unveränderte Backendtoleranzen.
Zwei Fenster × drei Seeds × drei Arme × 100 äußere Iterationen = 18 Suchen.
Das erste vorbestimmte Tripel (Fenster 1, Seed 2026112311) wird einmal in
frischen Prozessen wiederholt: insgesamt 21 kurze Suchen. Die Wiederholung
ist ein Reproduzierbarkeitscheck und kein weiterer unabhängiger Fall.
Reihenfolge je Fenster/Seed zyklisch O/S/K, S/K/O, K/O/S.
Alle Prozesse begrenzt auf jeweils 1.800 s, serieller Gesamtlauf auf 21.600 s.
Keine Verlängerung nach Sichtung ungünstiger Resultate.

Vorab getrennte technische Kontrollen: native arithmetische Referenzen,
Optionsgegenfälle, instrumentierte/uninstrumentierte feste Optimierung sowie
kleine Prozesskontrollen mit eigenem linearem Achtpunkt-Signal. Sie zählen
nicht als wissenschaftliche Fenster oder zusätzliche Replikate.

## Feste Struktur vor freier Suche

Die Diagnose nutzt ausdrücklich die bekannte 13-Knoten-Struktur
`a * (exp(b*t) * cos(c*t + d))`; sie ist ein bekannter Familienfit,
keine freie Formelentdeckung. Vier daten-/rasterbasierte Anfangswerte:
a = max(abs(observed)), b = -1/tau, c = 2*pi*f, d = pi/2,
mit f in {128,512} Hz und tau in { (128/4096)/8, (128/4096)/2 } s,
in dieser kartesischen Reihenfolge. Keine Startwertsuche um die Wahrheit.
Pro Fenster, Start und Suchseed alle drei Arme: 72 lokale Diagnosen.
Initiale Konstanten, Xoshiro-Zustände und tatsächlich verwendete Neustartzüge
werden verglichen. Die Diagnose erfasst verfügbare Optimierertraces und
Aufrufzahlen; nicht vom Backend ausgegebene Stopgründe bleiben unbekannt.
Ein vorher festgelegter erster technischer Fall prüft, dass die Beobachtung
selbst Ergebnis und RNG-Zustand nicht ändert.

## Endpunkte, Nachrechnung und Entscheidung

Primär ist eine Mechanismusdiagnose, kein Signifikanztest für Formelqualität:
Skalierungsidentität an festen Bäumen; tatsächlich unterschiedliche lokale
Parameterpfade bei gleichen Starts/Zufallszügen; jeweilige MSE nach Rückskalierung;
Baselineverlust, Normierungsnenner, Rohverlust, Kosten und effektive Optionen.
In der Evolution gilt im gepinnten Backend die Baseline-Untergrenze 0,01;
ob sie in jedem neuen Fenster aktiv ist, wird gemessen. Der lokale Optimierer
erhält den rohen Verlust. g_abstol = 1e-8 bedeutet deshalb unterschiedliche
Gradientenschwellen in MSE-Einheiten; das allein beweist keine Stopursache.

Freie Suchen vergleichen vollständige ursprüngliche Fronten, Auswahl,
Trainings-MSE, Callbackzahlen und Kosten. Gleicher Seed belegt keine Gleichheit
späterer Zufallszüge oder Populationen nach divergierender Suche. Die gesamte
Startpopulation wird nur dann als identisch bezeichnet, wenn tatsächlich
aufgezeichnet; sonst beschränkt sich die Aussage auf identische Eingaben,
Optionen außerhalb des Verlustpfads und initiale Seeds.

Deskriptive Formelbewertung auf 889 gleichmäßigen und 1024 unabhängigen,
vorab erzeugten unregelmäßigen Zeiten im geschlossenen Trainingsintervall;
PCG64-Seed des unregelmäßigen Rasters 2026112391. RMSE/A und Maximalfehler/A,
alle ursprünglichen Formeln und Punktdaten ausgeben. Wahrheit ausschließlich
für diese nachgelagerte Bewertung, niemals für Suche oder Kandidatenauswahl.
Nur zwei unabhängige Rauschfenster: keine Populationseffekte/engen Intervalle
aus Suchseeds als vermeintlich unabhängigen Datenfällen ableiten.

Bei technischen Widersprüchen zuerst den Laufweg korrigieren und jeden
Fehlversuch erhalten. Bei gültigen Ergebnissen werden O/S- und S/K-Abweichungen
getrennt erklärt; keine automatische Umstellung des historischen Verlusts.
Erst anschließend wird genau eine begründete Struktur- oder Auswahlintervention
in einem eigenen, vor ihrer Ausführung festgelegten Plan konkretisiert.
Die bisherigen Alternativkandidaten und exakten Rasteraliase motivieren eine
Auswahl anhand zusätzlicher unabhängiger verrauschter Off-grid-Messwerte;
deren Informationsmehrbedarf muss ausdrücklich Teil des Vergleichs sein.
Keine pauschal kleinere Komplexitätsgrenze und kein erneuter pauschaler
`best`-Selektor, dessen früherer Vergleich ungünstig ausfiel.

## Quellen und Grenzen

- [Cranmer (2023), PySR](https://arxiv.org/abs/2305.01582): evolutionäre Suche,
  lokale Optimierung und Pareto-Auswahl sind getrennte Schritte.
- [Morris, White und Crowther (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/):
  Ziele, Datengenerierung, Methoden und Leistungsmaße vorab trennen.
- [VanderPlas (2018)](https://arxiv.org/abs/1703.09824): Raster und spektrales
  Fenster bestimmen Frequenzmehrdeutigkeiten; Teilmengen desselben gleichmäßigen
  Rasters beseitigen exakte Aliase nicht.
- Maßgeblich für die konkrete Skalierungsmechanik sind die gebundenen Quellen
  von SymbolicRegression 2.5.1 (`LossFunctions.jl`, `ConstantOptimization.jl`)
  und die tatsächlich erfassten Optionsobjekte, nicht eine allgemeine
  Aussage über sämtliche Versionen oder Optimierer.

Alle Ausfälle, nicht ausgeführten Zellen und gemessenen Kosten berichten;
verschachtelte Fit-/Workerzeiten nicht zur Gesamtlaufzeit addieren. Ein lesender
Verifier kontrolliert Quellen, Daten, vollständige Zellmenge, Formeln und
Nachrechnungen. Export getrennt von Rohresultaten; Originaldateien erhalten.
