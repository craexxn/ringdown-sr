# Äußere Suchbudgets bei festem lokalem Profil 300/5

Angenommener Entwicklungsvergleich vom 04.11.2026. Die vier Budgets und das
lokale Profil sind beauftragt; als Abbruchgrenzen sind vier Stunden insgesamt
und 30 Minuten je Worker gewählt. Dieser Plan wird vor Implementierung durch
Commit und SHA-256 gebunden. Wissenschaftliche Ausführung ausschließlich auf
Manjaro; hier Vorbereitung und technische Prüfungen.

## Frage und vorhandener Befund

Der [lokale Vergleich](local_optimizer_results_manjaro_001.md) ergab bei 200
äußeren Iterationen für 100/2, 300/2, 100/5 und 300/5 jeweils 1/5, 2/5, 2/5 und
3/5 Kurvenerfolge; vollständig unterstützte Rekonstruktionen jeweils 1/5.
300/5 benötigte rund 32 % mehr summierte Zellzeit als 100/2 und verlor dessen
einzigen erfolgreichen Seed. Es ist ein gewähltes Arbeitsprofil, kein Optimum.

Frage: Wie ändern sich Kurvengüte, Zahl vollständig unterstützter
Originalauswahlen und Aufwand bei 200, 500, 2.000 und 5.000 äußeren Iterationen
unter unverändertem 300/5-Profil? Das ist ein Ein-Faktor-Vergleich. Er prüft
keine Überlegenheit von 300/5 gegenüber 100/2 bei größeren äußeren Budgets.
Die Gesamtzahl unterstützter Rekonstruktionen wird ausdrücklich getrennt von
Kurvenerfolgen und dem Auftreten eines neuen unterstützten Seeds betrachtet.

Die [bisherige Literaturauswertung](search_duration_literature.md) begründet
Ressourcenprüfungen, keinen optimalen Iterationswert. Die Staffel ist eine
begrenzte Entwicklungsentscheidung, keine Literaturkonstante. 10.000 gehört
nicht zu dieser Serie; kein automatisches Erhöhen von Budget oder Umfang.

## Unverändertes Suchprofil und Datenrollen

In jeder Zelle genau ein frischer equation_search-Aufruf. Allgemeine Grammatik
mit +, −, ×, ÷, exp, sin und cos, keine zusätzliche trigonometrische
Verschachtelungssperre. `should_simplify=false`, beide Häufigkeitsschalter an,
Float64, Sekundenkoordinate, gewöhnliche MSE, zwei Populationen à 32,
50 Zyklen je Iteration, maxsize/maxdepth 20, Parsimony 0. Keine Warmstarts,
Startformeln, Templates, Nachfits oder zusätzlichen Suchaufrufe.

Konstantenoptimierung unverändert aus #61: maximal 300 lokale Iterationen,
fünf zusätzliche gestörte Neustarts, insgesamt sechs Versuche; vorhandener
Newton-Sonderpfad beziehungsweise BFGS/Backtracking und 10.000 lokale
Funktionsaufrufe. Alle übrigen nativen Optionen, Plugins, Toleranzen,
Einheiten und Auswahlregeln bleiben erhalten. Es wird derselbe native
LocalOptimizerBudget-Wrapper für `local_300_5` verwendet, dessen numerische
Zielfunktion unverändert delegiert wird. Äußere Iterationen sind ein Argument
des tatsächlichen equation_search-Aufrufs, kein natives Optionsfeld.

Eingang: `representation-manjaro-001.tar.gz`, SHA-256
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
128 originale Trainingswerte t=j/4096 mit A=1, f=250 Hz, tau=0,008 s und phi=0.
Nur Zeiten und Beobachtungen gelangen an Suchworker; Wahrheit und 889 innere
Achtelpunkte bleiben im getrennten Referenz-/Diagnosepfad. Gleiche eingefrorene
Datenbits; keine Auswahl anhand der Signalwahrheit oder Zwischenpunkte.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0 und SymbolicRegression 2.5.1 bleiben
gepinnt. Seriell/deterministisch, Haswell und Threadlimit 1; keine parallelen
wissenschaftlichen Worker. Neue Seedkennungen machen das bekannte, adaptiv
untersuchte Signal nicht zu unabhängigen Validierungsdaten.

## 20 frische Zellen und Ressourcen

Fünf vorab festgelegte, bislang wissenschaftlich ungenutzte Seedkennungen:
20261201, 20261202, 20261203, 20261204 und 20261205. Alle vier Budgets verwenden
dieselben fünf Kennungen, jeweils in eigenem frischem Prozess. Die 200er-
Kontrollen werden neu ausgeführt; keine Übernahme historischer Zellen oder
Fortsetzung gespeicherter Suchzustände. Gleiche Seeds behaupten keine
identischen Suchtrajektorien bei unterschiedlichen Budgets.

| Seed | Reihenfolge der äußeren Iterationen |
| --- | --- |
| 20261201 | 200, 500, 5.000, 2.000 |
| 20261202 | 500, 2.000, 200, 5.000 |
| 20261203 | 2.000, 5.000, 500, 200 |
| 20261204 | 5.000, 200, 2.000, 500 |
| 20261205 | 200, 500, 5.000, 2.000 |

Die ersten vier Blöcke gleichen Positionen und alle zwölf gerichteten
Nachbarschaftspaare aus. Der fünfte wiederholt den ersten; die verbleibende
Positionsasymmetrie wird nicht als vollständiger Ausgleich bezeichnet.

Grenzen: **1.800 Sekunden je Suchworker, 14.400 Sekunden insgesamt**,
einschließlich Vorprüfung, Elternnachrechnung und Finalisierung. Alle Budgets
haben dieselbe Workergrenze. Es sind Abbruchgrenzen, keine Laufzeitprognose.
Die gemessenen Mittel der Zellzeit lagen zuvor bei rund 58/202 Sekunden für
100/2 mit 200/2.000 äußeren Iterationen und rund 74 Sekunden für 300/5 mit 200.
Die Grenze von 600 Sekunden wird für 5.000 nicht ungeprüft beibehalten. Aus
diesen verschiedenen Serien folgt keine belastbare lineare Laufzeitprognose
für 300/5 bei 5.000; die gewählte Reserve ist eine organisatorische Festlegung.

Fehler, Fristablauf und Signale stoppen eigene Prozessgruppen und bewahren
Teilstände. Keine Wiederholung, Ersatzseeds, automatische Verlängerung oder
Teilgruppenfreigabe. Eine gültige schlechte Auswahl bleibt ein Ergebnis.
Bei unvollständiger Serie bleiben alle Aggregate und Vergleiche gesperrt.

## Auswahl, Endpunkte und vollständige Kontraste

Originalauswahl unverändert: minimale native Trainings-MSE, dann Komplexität,
dann erste Originalposition bei Gleichstand. Alle Kandidaten, Reihenfolgen,
Bäume, Verluste, Vorhersagen und Residuen erhalten. Getrennte Verlust-,
Normalbereichs-, MPFR-Vorhersage-, Parameter- und Aliasprüfungen bleiben
unverändert, einschließlich unabhängiger Elternnachrechnung aller Kandidaten.
Keine Lockerung, diagnostische Neuauswahl oder Erweiterung des Strukturerkenners.

Zwei getrennte Zählendpunkte je Budget b, jeweils Nenner fünf:

- C_b: Originalauswahl erfüllt auf Training und Zwischenpunkten jeweils
  relativen RMS ≤ 0,001 und relativen Maximalfehler ≤ 0,01.
- S_b: dieselbe Auswahl erfüllt zusätzlich die vorhandene Strukturerkennung,
  passende Parameter und beide Replays. Frequenzgrenze 1e-3, übrige vorhandene
  Parametergrenzen 1e-2; physikalische Identifikation bleibt `not_assessed`.

S ist damit eine Teilmenge von C. Unverfügbare oder fehlgeschlagene Diagnosen
erzeugen keinen positiven Befund. Nicht unterstützte Struktur ist kein Beweis
algebraischer Unmöglichkeit. Gute ungewählte Kandidaten zählen separat.

Alle folgenden fünf gerichteten Kontraste sind festgelegt, je fünf Seedpaare:
500−200, 2.000−500, 5.000−2.000, 2.000−200 und 5.000−200. Das sind die drei
benachbarten Budgetstufen und alle drei Vergleiche mit der frischen Baseline,
wobei 500−200 nur einmal vorkommt. Insgesamt 25 Paaraufzeichnungen; keine
25 unabhängigen Wiederholungen und keine Auswahl nur günstiger Kontraste.

Für jeden Kontrast beide C und S, beide Differenzen sowie je alle vier
0→0/0→1/1→0/1→1-Wechsel ausweisen. Zusätzlich alle kontinuierlichen Fehler
beider Raster, Parameterstatus, endliche Nenner und ursprüngliche Kosten
beider Zellen samt Zeitdifferenz/-verhältnis, sofern verfügbar.
Einordnung ausschließlich als deskriptive Richtung beider Zählendpunkte:

- `curve_and_supported_count_gain`: Delta C > 0 und Delta S > 0.
- `supported_count_gain_only`: Delta S > 0 und Delta C ≤ 0.
- `curve_count_gain_only`: Delta C > 0 und Delta S ≤ 0.
- `no_count_gain`: beide Differenzen ≤ 0.

Negative Werte und gegenläufige Effekte bleiben sichtbar. Bei gleichem S
belegt ein neu unterstützter Seed mit gleichzeitigem Verlust keinen Anstieg
der Gesamtzahl. Das präzisiert den Endpunkt dieses neuen Plans; die frühere
Regel `supported_structure_gain` und historische Befunde werden nicht geändert.
Keine automatische Gewinnerwahl, Signifikanzbehauptung oder allgemeine
Erfolgswahrscheinlichkeit aus fünf adaptiven Seeds.

Pro Budget alle fünf Originalauswahlen, Struktur-/Parameterstatus,
Minima/Mediane/Maxima mit Nennern und Aufwand ausgeben. Zellzeit enthält
Armaufruf und Elternverifikation; status.json.total_wall_seconds enthält
bereits Elternvorbereitung und Ergebnislesen. Fitzeit enthält JIT/Export;
Callbacks sind keine eindeutigen Bäume oder Optimiererschritte. Kein allgemeiner
Kostenfaktor wird aus nominalen Iterationen abgeleitet.

## Begrenzte Umsetzung, Prüfung und Fortsetzung

Eigener versionierter Adapter und Planbindung, bestehender Lebenszyklus und
nativer 300/5-Wrapper. Fünf echte native Seed-/Profiloptionen, alle 20 Python-
Suchprofile und drei feste Einheiten-/Aliasreferenzen vorab prüfen. Falsches
100/2-Profil und falscher Seed müssen vor dem numerischen Callback scheitern.
Der tatsächliche Suchaufruf wird pro Zelle auf das unverändert durchgereichte
Budget und frischen Zustand geprüft, einschließlich der ersten Zelle.

Technische Integration auf separaten acht Punkten y=1+t: fünf frische Worker
mit äußeren Budgets 2, 3, 4, 5 und erneut 2 bei konstant 300/5. Die wiederholte
Kontrollfront muss identisch sein. Keine wissenschaftliche Zelle in der Cloud.
Gezielte Python-Gegenfälle prüfen alle Budgetfelder, getrennte C-/S-Wechsel,
unverfügbare Diagnosen, Originalauswahl, sämtliche Kandidatennachweise,
Zeitgrenzen, späte Manipulation und Widerruf nach positivem Berichtsrename.
Vorhandene vollständige CI bleibt erforderlich. Frühere Pläne, Profile und
Defaults bleiben erhalten; keine große Umstrukturierung oder neue Abhängigkeit.

Nach Auswertung begründetes Profil für den Transfercheck ableiten. Ein
ausbleibender S-Zuwachs wird ausdrücklich berichtet; kein automatischer
10.000er-Lauf. Falls Suchprobleme oder Grenzen der Strukturerkennung entscheidend
bleiben, einen begrenzten nächsten Schritt benennen. Der 8·fs-Blindfleck bleibt
bestehen. Die vorgemerkte Pilotroute und Planungsziele 8./9. sowie etwa
15. November bleiben erhalten; die Hauptstudie gehört nicht zu diesem Auftrag.
