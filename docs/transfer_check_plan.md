# Begrenzter Transfercheck bei 500 äußeren Iterationen und lokal 300/5

Angenommener Folgeschritt vom 04.11.2026 nach der
[äußeren Iterationsstaffel](outer_search_ladder_results_manjaro_001.md).
Plan und Eingangsdaten werden vor der Implementierung durch Commit und
SHA-256 gebunden. Wissenschaftliche Ausführung einmalig auf Manjaro;
hier Datenvorbereitung und technische Kontrollen, keine wissenschaftliche Suche.

## Grundlage, Frage und notwendige Anpassungen

500 äußere Iterationen erreichten am bekannten Signal bei lokal 300/5 fünf
Kurvenerfolge unter fünf neuen Seeds. 2.000 und 5.000 brachten dort keinen
zusätzlichen Kurvenerfolg, aber rund 3,05-/6,24-mal die summierte Zellzeit.
Die formale Strukturwertung wird durch die begrenzte Erkennungsabdeckung
beeinflusst. 500/300/5 ist deshalb ein Arbeitsprofil, kein allgemeines Optimum.

Frage: Wie empfindlich sind Kurvengüte, unterstützte Rekonstruktion und
Parameterbefund dieses festen Profils gegenüber einzelnen Signaländerungen
und einem gemeinsamen Transferfall? Drei Seeds je Bedingung sind ein kleiner
Entwicklungscheck, keine Leistungsvalidierung oder statistisch belastbare
Erfolgswahrscheinlichkeit. Der bekannte Referenzfall wird frisch ausgeführt.

Vorhanden sind der serielle Treiber, native Options- und Aufrufprüfungen,
Originalauswahl, unabhängige Kandidatenprüfungen und sichere Finalisierung.
Notwendig sind nur unterschiedliche eingefrorene Eingaben je Bedingung,
die Referenzparameter je Signal und passende Berichte. Der Strukturerkenner
wird nicht erweitert; keine große Umstrukturierung oder neue Abhängigkeit.
Ein weiterer 500/1.000-Vergleich und der optionale 300/2-Anschluss bleiben
zurückgestellt und würden eine eigene begründete Festlegung benötigen.

## Feste Signale und Datenrollen

Alle Signale folgen A exp(−t/tau) cos(2πft + phi), A dimensionslos,
t und tau in Sekunden, f in Hertz und phi in Radiant. Keine Rauschzugabe.
128 Trainingspunkte t=j/4096, j=0,…,127; Fensterlänge 128/4096 s,
rechter Endpunkt ausgeschlossen. Getrennte Diagnose: 889 innere Achtelpunkte
t=(j+k/8)/4096, j=0,…,126, k=1,…,7. Keine Extrapolationsprüfung.

| Kennung | A | f / Hz | tau / s | phi / rad | Zweck |
| --- | --- | --- | --- | --- | --- |
| anchor | 1 | 250 | 0,008 | 0 | Frischer bekannter Referenzfall |
| frequency | 1 | 417 | 0,008 | 0 | Höhere Frequenz allein |
| decay | 1 | 250 | 0,004 | 0 | Schnellere Abnahme allein |
| phase | 1 | 250 | 0,008 | 0,7 | Nichtverschwindende Phase allein |
| amplitude | 0,4 | 250 | 0,008 | 0 | Kleinere Amplitude allein |
| combined | 0,6 | 180 | 0,012 | −0,9 | Gemeinsame Änderung aller vier Parameter |

Die Werte liegen unter Nyquist und verändern die Schwingungszahl, sichtbare
Abnahme, Startphase beziehungsweise Skala innerhalb desselben Fensters.
Sie wurden ohne Such- oder Fitvorversuche gewählt. Dies ist kein vollständiges
Faktordesign; der gemeinsame Fall isoliert keine einzelne Parameterwirkung.

Eingaben: [NPZ](../data/transfer_check_inputs.npz), SHA-256
`e4de71bb6aa5cb5e3afc72914466b997adb2ef6438bbe38d7baa421a85bd2628`;
[Manifest](../data/transfer_check_inputs.json), SHA-256
`54f7ddb7b524640e20911ae3fe69334d3fd31d25d9c9fab69d132e1ade9d1773`.
Das Manifest bindet Reihenfolge, Parameter, Float64-Datenbits und Generator.
Einmalige Erzeugung mit dem bestehenden Signalpfad; 6.102 Werte wurden
unabhängig mit 100 Dezimalstellen geprüft, maximale absolute Abweichung
geteilt durch A etwa 1,14e-15. Laufzeit konsumiert die gebundenen Bytes,
keine plattformabhängige Neugenerierung. Das frühere Eingangsarchiv
representation-manjaro-001.tar.gz wird hierfür nicht benötigt.

Suchworker erhalten ausschließlich die Trainingszeiten und Beobachtungen der
aktuellen Bedingung. Referenzparameter und Zwischenpunkte bleiben im
Eltern-/Diagnosepfad. Keine Auswahl oder Optimierung anhand der Signalwahrheit;
keine Übernahme früherer Fronten, Suchzustände oder erfolgreicher Formeln.

## Suchprofil, Reihenfolge und Ressourcen

Jede Zelle startet einen frischen Prozess und genau einen equation_search-Aufruf
mit 500 äußeren Iterationen. Lokales Profil 300/5: maximal 300 Iterationen und
fünf zusätzliche gestörte Neustarts; vorhandener Newton-Sonderpfad bzw.
BFGS/Backtracking und 10.000 lokale Funktionsaufrufe. Unveränderte numerische
Zielfunktion über LocalOptimizerBudget, gewöhnliche MSE, Sekundenkoordinate,
Float64, allgemeine Grammatik mit +, −, ×, ÷, exp, sin und cos,
`should_simplify=false`, beide Häufigkeitsschalter an, zwei Populationen à 32,
50 Zyklen je Iteration, maxsize/maxdepth 20 und Parsimony 0.
Alle übrigen Optionen, Plugins, Toleranzen und Auswahlregeln bleiben erhalten.
Keine Warmstarts, Templates, Nachfits oder weiteren Suchaufrufe.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1;
Haswell, Threadlimit 1, seriell/deterministisch. Drei bislang im Projekt
wissenschaftlich ungenutzte Seedkennungen, gepaart über die sechs Bedingungen:

| Seed | Feste Reihenfolge |
| --- | --- |
| 20261210 | anchor, frequency, decay, phase, amplitude, combined |
| 20261211 | decay, phase, amplitude, combined, anchor, frequency |
| 20261212 | amplitude, combined, anchor, frequency, decay, phase |

Insgesamt **18 frische Zellen**. Jede Bedingung steht an drei verschiedenen
Positionen; kein vollständiger Positions- oder Nachbarschaftsausgleich.
Gleiche Seeds bedeuten bei anderen Daten keine identischen Suchtrajektorien.

Abbruchgrenzen: **900 Sekunden je Worker und 7.200 Sekunden insgesamt**,
einschließlich Vorprüfung, Elternarbeit und Finalisierung. Die bisherige
500er-Gruppe benötigte median rund 133 Sekunden je Zelle; daraus folgt keine
Laufzeitgarantie für neue Signale. Grenzen sind organisatorische Reserven,
keine Laufzeitprognose. Fehler, Signale und Fristablauf erhalten Teilstände,
stoppen eigene Prozesse und sperren alle Aggregate. Keine Wiederholung,
Ersatzseeds, automatische Verlängerung oder Freigabe von Teilgruppen.

## Auswahl, getrennte Endpunkte und Auswertung

Originalauswahl: minimale native Trainings-MSE, dann Komplexität und erste
Originalposition. Sämtliche Kandidaten, Reihenfolgen, Bäume, Vorhersagen,
Residuen und Verluste bleiben erhalten. Native/Python-Verlustprüfung,
Normalbereichssperre, MPFR-Vorhersagereferenz und unabhängige Elternnachrechnung
aller Kandidaten bleiben ebenso erhalten wie getrennte Parameter-/Aliasreplays.
Keine gelockerten Prüfungen, diagnostische Neuauswahl oder neue Strukturregeln.

Je Signal zwei getrennte Zählendpunkte mit Nenner drei:

- C: Originalauswahl erfüllt auf Training und Zwischenpunkten jeweils
  relativen RMS ≤ 0,001 und relativen Maximalfehler ≤ 0,01.
- S: Dieselbe Auswahl erfüllt zusätzlich die vorhandene Strukturerkennung,
  passende Parameter und beide Replays. Frequenzfehler relativ zum jeweiligen
  f ≤ 1e-3; tau, Amplitude und komplexe Amplitude jeweils ≤ 1e-2.

Parameter werden gegen die jeweilige Wahrheit (A0,f0,tau0,phi0) beurteilt:
|f−f0|/f0, |tau−tau0|/tau0, ||A|−A0|/A0 und
|A exp(i phi)−A0 exp(i phi0)|/A0. Alle Referenzamplituden sind positiv.
Die komplexe Amplitude behandelt Phase modulo 2π und die äquivalente
Darstellung mit negativem A. Verwendet werden die bisherigen kanonischen
Aliasparameter und Verfügbarkeitsgates. Für A0=1 und phi0=0 bleibt die alte
Regel erhalten. Nicht unterstützte Strukturen oder fehlgeschlagene bzw.
unbestimmte Replays liefern keinen positiven Parameter-/S-Befund.
Physikalische Identifikation bleibt `not_assessed`.

Bericht: alle Originalauswahlen, C/S und getrennte Struktur-/Parameterstatus,
Fehler auf beiden Rastern mit endlichen Nennern sowie Laufzeit und Callbacks
je Zelle/Signal. Dazu fünf vorab festgelegte Kontraste jeder Variante gegen
anchor bei gleichen Seeds, insgesamt 15 Paare; alle Richtungen bleiben sichtbar.
Keine automatische Gewinnerwahl oder gemeinsame Erfolgsquote über heterogene
Signale. Gute ungewählte Kandidaten werden separat gezählt, ersetzen keine Auswahl.

Die bekannte begrenzte Erkennungsabdeckung und der 8·fs-Blindfleck bleiben
dokumentiert. Ein kleineres S kann Erkennungsgrenzen widerspiegeln und belegt
allein keinen physikalischen Strukturverlust. Eine spätere algebraische
Diagnose wäre ausdrücklich nachträglich, ohne Umklassifikation dieser Serie.

## Konsequenzen und Abgrenzung

Nach vollständiger Verifikation werden Schwierigkeiten pro Signal und Seed
einschließlich Aufwand und Unsicherheit beschrieben. Ein begrenzter nächster
Schritt wird aus dem Befund begründet; keine automatische Budgeterhöhung.
Danach sind die vorhandene Rausch-/Kovarianzpipeline, ein kompaktes festes
Pilotdesign und die Pilotauswertung mit Hauptversuchsplan vorgesehen.
Die Hauptstudie selbst, WSL2, Parallelisierung und größere Bereinigung sind
nicht Teil dieses Schritts. Zwischenbewertung am 8./9. November und Pilot
etwa bis 15. November bleiben Planungsziele, keine Erfolgsgarantie.
