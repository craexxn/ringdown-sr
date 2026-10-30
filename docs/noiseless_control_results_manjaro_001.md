# Rauschfreie Kontrollserie auf Manjaro: Ergebnis 001

Ergebnisse vom 28.10.2026, ergänzt am 30.10.2026 um Callbackzähler und
technische Gegenprüfung. Die neun geplanten Zellen wurden mit Serienstatus
`completed` übermittelt. Alle 28 exportierten Kandidaten verfehlen die
vorab festgelegten Kurvenfehlergrenzen. Sechs der neun ursprünglichen
Auswahlen sind konstante Näherungen des Trainingsmittelwerts.

Die technische Ausführung ist laut Bericht abgeschlossen; eine brauchbare
Ringdown-Rekonstruktion ist mit dieser Konfiguration in dieser Serie nicht
erreicht. Die konkrete Ursache der Suchstagnation ist noch nicht bestimmt.

## Herkunft und Prüfgrenze

- Grundlage ist der eingefrorene [Methodenplan](noiseless_control_plan.md)
  aus PR #32, SHA-256
  `be41e704066c4b7c281ee92acb37960bea1f24b0f528aec9adabc4e87672b4dd`.
- Die [Implementierung](noiseless_control.md) wurde in
  [PR #34](https://github.com/craexxn/ringdown-sr/pull/34) nach KI-basiertem
  Implementierungsreview und gezieltem Nachreview übernommen.
  Geprüfter Stand: `76b2ffae9ee6f41d87547249d5aed83064b4c6bd`;
  vorgegebener Ausführungsstand: Mergecommit
  `bc80b4f07773ffb6d57a927ef3daaee34f9a7817`.
  Beide haben den Git-Dateibaum
  `94ae1c80e32bba89d2d1152a2c34d09d49fa795c`.
- Ausführungsgerät und Bezeichnung wurden als Manjaro übermittelt;
  Ausgabeordner ist `results/noiseless-control-001`.
- Primärgrundlage dieses Ergebnisprotokolls sind die vom Nutzer wörtlich
  eingefügte `summary.md` und der anschließend eingefügte lesende Auszug
  aus `report.json`. Dessen vorgeschaltete Prüfung aller Einträge des
  abschließenden Artefaktmanifests meldete `Prüfsummen OK`.
- Die vollständigen Originaldateien, binären Bäume, Quell- und
  Umgebungsmetadaten des Manjaro-Laufs wurden hier nicht unabhängig gelesen.
  Der lokale Manifestnachweis und der tatsächliche Ausführungsstand werden
  deshalb nicht als unabhängiger Audit der Geräteausführung ausgegeben.
  Prüfsummen belegen gespeicherte Konsistenz, keine externe Authentizität.

## Unveränderte Versuchsvorgaben

Ein rauschfreies Signal mit `A=1`, `f=250 Hz`, `tau=0,008 s`, `phi=0`,
128 Trainingswerten und `fs=4096 Hz`; gewöhnliche MSE ohne Kovarianz.
Die 889 Diagnosepunkte sind die sieben inneren Achtelstellen jedes
Trainingsintervalls. Sie und die Wahrheitsparameter bleiben außerhalb der
Suche und der ursprünglichen Auswahl.

Drei frische Suchläufe pro Seed mit `niterations=10/50/200`, zwei
Populationen zu 32 Individuen und 50 Zyklen pro Iteration, in der
festgelegten zyklischen Reihenfolge. Operatoren, Komplexitätsgrenze 20,
Konstantenoptimierung, Sekunden als Eingabeeinheit, harte Einheitenprüfung
und das Haswell-Profil mit Threadlimit 1 folgen dem Methodenplan.
Die Auswahl bleibt das Minimum des Trainingsverlusts mit Komplexität als
Gleichstandskriterium. Die Parameter `use_frequency` und
`use_frequency_in_tournament` sind beide `False`.

## Alle neun ursprünglichen Auswahlen

Alle Zellen sind `completed`. Die Fehler sind relativ zur Referenznorm;
angezeigte Zahlen sind gerundet. Vollständige Präzision bleibt im
Originalbericht. Der Kurvenmarker verlangt auf beiden Rastern zugleich
`relative_rms <= 0,001` und `relative_max <= 0,01`.

| Zelle | Seed | Iterationen | Kandidaten | Komplexität der Auswahl | Trainings-MSE | Trainings-RMS | Zwischenpunkte-RMS | Zwischenpunkte-Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 20261020 | 10 | 4 | 9 | 0,06788367531 | 0,996787601 | 1,000241926 | 0,938497967 |
| 2 | 20261020 | 50 | 9 | 19 | 0,06308046052 | 0,960876077 | 0,977218556 | 0,828400314 |
| 3 | 20261020 | 200 | 9 | 19 | 0,06096083849 | 0,944594515 | 0,964319184 | 0,798730206 |
| 4 | 20261021 | 50 | 1 | 1 | 0,06829567962 | 0,999807911 | 1,000107741 | 0,994851497 |
| 5 | 20261021 | 200 | 1 | 1 | 0,06829567962 | 0,999807911 | 1,000107741 | 0,994851497 |
| 6 | 20261021 | 10 | 1 | 1 | 0,06829567962 | 0,999807911 | 1,000107741 | 0,994851497 |
| 7 | 20261022 | 200 | 1 | 1 | 0,06829567962 | 0,999807911 | 1,000107741 | 0,994851497 |
| 8 | 20261022 | 10 | 1 | 1 | 0,06829567962 | 0,999807911 | 1,000107741 | 0,994851497 |
| 9 | 20261022 | 50 | 1 | 1 | 0,06829567962 | 0,999807911 | 1,000107741 | 0,994851497 |

Alle 28 exportierten Kandidaten haben `curve_marker=outside_tolerance`,
`structure_status=not_supported` mit erstem Grund
`exponential_factor_count` und Parameterstatus `not_assessed`.
Das sind 28 gespeicherte Frontkandidaten, keine 28 unabhängigen Läufe.
Der erste Strukturgrund ist keine vollständige Aufzählung aller
Struktureigenschaften. Die Kurvenfehler werden unabhängig davon beurteilt.

Für jedes der drei Budgets liegen drei vollständige Zellen vor. Die
Mediane der relativen Fehler betragen bei allen Budgets rund
`0,999807911` im Training und `1,000107741` auf den Zwischenpunkten.
Bei Seed `20261020` verbessern sich die ausgewählten Kurven etwas;
die anderen beiden Seeds liefern jeweils über alle Budgets dieselbe
Konstante. Gemeinsame Seeds machen die frischen Suchläufe weder zu
identischen Suchpräfixen noch zu Versuchen mit gleichen Rechenkosten.

## Übermittelte Formeln

Zelle 1:

```text
(t * ((t * 228.3372269552945) + -8.371992623162193)) + 0.061452766991601716
```

Zelle 2:

```text
sin(((t * 171.53551804157468) + -88.28134696466604) * sin((t * ((t * 530.2824573210376) + -4.444119497910336)) + -11.300944574814897)) + 0.9416696162428028
```

Zelle 3:

```text
sin(sin((t * ((t * 644.4450841486262) + -0.6194961365353331)) + -5.843057284572543) * ((t * 885.0553402308213) + -50.482448747304254)) + 0.9279183641310937
```

Zellen 4–6: `0.0051230090350108`.
Zellen 7–9: `0.0051230090376437`.
Dies sind übermittelte Anzeigegleichungen; die Originalbäume bleiben
maßgeblich für einen vollständigen Export-Replay.

## Laufzeiten

Sekunden, auf drei Nachkommastellen gerundet. `worker_setup` ist die
gespeicherte Worker-Vorbereitung; `fit_including_jit_and_python_exports`
enthält laut Feldbezeichnung JIT und Python-Exporte und ist keine isolierte
Evolutionszeit. Die Tabelle belegt weder die tatsächliche Zahl verschiedener
Ausdrücke noch vollständig absolvierte Backendzyklen.

| Zelle | Worker-Vorbereitung | Fit einschließlich JIT und Python-Exporten |
| --- | --- | --- |
| 1 | 7,786 | 29,093 |
| 2 | 5,430 | 29,506 |
| 3 | 5,398 | 37,001 |
| 4 | 5,387 | 28,150 |
| 5 | 5,493 | 28,987 |
| 6 | 5,461 | 28,104 |
| 7 | 5,431 | 29,048 |
| 8 | 5,504 | 28,447 |
| 9 | 5,507 | 28,532 |

## Zusätzliche lokale Nachrechnungen ohne Suche

Mit den eingefrorenen Datengeneratoren und gesperrten Python-Abhängigkeiten:

1. Die optimale konstante Trainingsvorhersage ist der Mittelwert
   `0,005123009037020716`, mit MSE `0,06829567962376913`.
   Die sechs konstanten Auswahlen stimmen damit bis auf numerische
   Optimierungsabweichungen überein. Eine Nullkurve hätte per Definition
   relativen RMS-Fehler 1 auf beiden Rastern.
2. Die drei übermittelten nicht konstanten Anzeigegleichungen wurden als
   NumPy-Ausdrücke auf den erneut erzeugten Referenzrastern ausgewertet.
   Sie reproduzieren die übermittelten RMS-/Maximalfehler und die MSE bis
   auf Float64-Rundung. Das ersetzt keinen Replay der originalen Bäume
   und ihrer hexadezimal gespeicherten Konstanten.
3. Ein ausdrücklich konstruierter Referenzbaum
   `1 * (exp(-125*t) * cos((2*pi*250)*t))` besitzt 11 Knoten und liegt damit
   innerhalb der Grenze 20. Seine Python-Diagnose ergibt auf beiden
   Rastern RMS-/Maximalfehler 0, `recognized`, bestandene Parameter-Replays
   und `parameter_match=matched`.
   Dieser Baum wurde keiner Suche als Startwert oder Kandidat übergeben.
   Das ist eine positive Diagnosekontrolle, kein freier Sucherfolg und
   kein neuer tatsächlicher Julia-Callback-Nachweis dieses Kontrollsignals.

Der beste ausgewählte Trainingsverlust liegt nur rund 10,74 Prozent
unter dem Verlust der optimalen Konstanten. Zusammen mit den großen
Zwischenpunktfehlern stützt dies den Befund einer schwachen Kurvenanpassung.

## Einordnung und nächster Entwicklungsschritt

Die schlechte Kurvenanpassung liegt bereits im rauschfreien Fall vor.
Ein erweiterter Strukturerkenner allein würde die hier gemessenen großen
Kurvenfehler nicht beheben. Die Ergebnisse belegen keine generelle
Unmachbarkeit freier symbolischer Regression und erlauben keine Aussage
über einen Vorteil von Kovarianzgewichtungen oder physikalische Identifikation.

Als Ursachen kommen insbesondere die numerische Darstellung der Zeit,
die Erreichbarkeit zulässiger Zwischenstrukturen unter der harten
Einheitenprüfung und die evolutionäre Vielfalt infrage. In Sekunden
benötigt der Referenzbaum die Koeffizienten `-125` und etwa `1570,796`;
zugleich sind die beiden genannten Mechanismen zur Häufigkeitsgewichtung
von Komplexitäten deaktiviert. Diese Beobachtungen begründen Hypothesen,
keinen kausalen Nachweis.

Die am 30.10.2026 zusätzlich übermittelten `callback_calls_during_fit`
aus den bestehenden `cell-*/result.json` zeigen bei jedem Seed mehr
Verlustaufrufe mit höherem nominalem Budget:

| Seed | 10 Iterationen | 50 Iterationen | 200 Iterationen |
| --- | --- | --- | --- |
| 20261020 | 28 311 | 230 917 | 1 179 348 |
| 20261021 | 15 600 | 48 261 | 167 829 |
| 20261022 | 9 584 | 42 239 | 159 598 |

Insgesamt sind dies 1 881 687 Callback-Aufrufe. Auch die sechs Zellen mit
konstantem Ergebnis haben jeweils viele Verlustaufrufe. Das spricht gegen
einen bloß ausgebliebenen Suchstart, erklärt aber noch nicht die
Stagnation. Die Zahlen zählen Aufrufe des Verlustcallbacks, einschließlich
solcher während der Konstantenoptimierung, keine verschiedenen Ausdrücke
und keine unabhängigen Wiederholungen. Sie belegen weder linear mit dem
Budget skalierende Rechenkosten noch die vollständige Absolvierung aller
Backendzyklen. Der separate Backend-Evaluationszähler ist nicht verfügbar.
Populationszustände und Logs wurden weiterhin nicht unabhängig gelesen;
eine einzelne Pareto-Konstante beweist keine vollständig konstante
Suchpopulation.

Die technische Gegenprüfung ist in der bestehenden
[Julia-Prüfung](../julia/test/runtests.jl) ergänzt. Sie erzeugt das feste
128-Punkte-Signal aus den analytischen Vorgaben und reicht den konstruierten
11-Knoten-Referenzbaum durch `SymbolicRegression.eval_loss` an
`RingdownSRSearch.objective` weiter, mit den ursprünglichen Einheiten und
der harten Einheitenprüfung. Eine optimale konstante Vorhersage wird gegen
ihre unabhängig berechnete MSE geprüft; `sin(t)` muss wegen seiner Einheiten
zurückgewiesen werden. Die Kontrolle führt weder Fit noch Suche oder
Konstantenoptimierung aus. Sie wird über den bestehenden Befehl
`scripts/check_julia_loss.py` im gepinnten Launcher ausgeführt, auch im
unveränderten CI-Schritt. Ihre Optionen bilden die für feste Bäume relevante
Grammatik, Komplexitätsgrenze und Einheiten-/Callbackregeln ab; sie laden
keine originalen Optionen oder Zustände des Manjaro-Laufs. Ein bestandener
Test belegt deshalb die Zulässigkeit der Referenz am geprüften Callback,
keine Erreichbarkeit durch die evolutionäre Suche und keinen unabhängigen
Audit der Manjaro-Artefakte.

Eine anschließende neue Suchserie benötigt eine separat festgelegte
Änderung und Vergleichsbedingung, etwa zur Zeitskalierung oder zur
Komplexitätsvielfalt. Mehrere Faktoren zugleich zu ändern würde ihre
Ursachenwirkung hier nicht trennen. Die ursprüngliche Serie, Auswahl,
Fehlergrenzen und der eingefrorene Methodenplan bleiben als Ausgangsbefund
erhalten. Die Rohartefakte sind gemeinsam mit ihrem abschließenden
`metadata.json`-Manifest aufzubewahren.

Das bekannte Achtelraster besitzt weiterhin seinen Alias-Blindfleck bei
Frequenzabständen `8*fs=32768 Hz`. Auch ein späterer Rastertreffer wäre
kein Nachweis für beliebige Zwischenzeiten; `physical_identification`
bleibt `not_assessed`.
