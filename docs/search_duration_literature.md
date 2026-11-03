# Suchaufwand: Literaturgrundlage für den begrenzten Budgetvergleich

Stand: 03.11.2026. Nach dem negativen [Grammatikvergleich](trigonometric_grammar_results_manjaro_001.md)
ist ein Vergleich größeren Suchaufwands angenommen. Hier wird die gezielte
Primärquellenrecherche dokumentiert; keine systematische Literaturübersicht
und keine Reproduktion publizierter Experimente. Die konkret genannten
Volltextabschnitte wurden gelesen, nicht sämtliche Anhänge oder Implementierungen.

## 1. Primärbelege und Übertragungsgrenzen

### Cranmer (2023): PySR und EmpiricalBench

*Interpretable Machine Learning for Science with PySR and SymbolicRegression.jl*,
[arXiv:2305.01582v3](https://arxiv.org/html/2305.01582v3), Abschnitte 2.1,
2.2 und 3.2.1.

EmpiricalBench gestattet jeder Methode bis zu eine Stunde Suche auf acht
AMD-Rome-Kernen. PySR verbindet Evolution, Vereinfachung, Konstantenanpassung
und Migration zwischen Populationen. Der Artikel erläutert zudem, dass
redundante Zwischenformen für spätere Mutationen nützlich sein können.

Das liefert einen Größenordnungs- und Mechanismusbezug, keine Mindestlaufzeit
für unseren Ringdown. Hardware, Datensätze, Profile und Auswertung unterscheiden
sich. Insbesondere betrachtet EmpiricalBench ganze Fronten; unser primärer
Endpunkt bleibt die vorab definierte Originalauswahl. Eine Stunde auf acht
Kernen wird nicht in eine vermeintlich äquivalente Manjaro-Laufzeit umgerechnet.

### Aldeia et al. (2025): SRBench 2025

*Call for Action: Towards the Next Generation of Symbolic Regression Benchmark*,
[arXiv:2505.03977v1](https://arxiv.org/html/2505.03977v1), Abschnitte 3.2–3.4;
[DOI 10.1145/3712255.3734309](https://doi.org/10.1145/3712255.3734309).

Das Protokoll trennt sechs Stunden Hyperparametersuche von einer Stunde
abschließendem Training je Lauf. Es verwendet 30 feste, unterschiedliche Seeds
pro Datensatz, einen CPU-Kern und gegebenenfalls GPUs für unterstützte Methoden.
Hardware und Ressourcen werden kontrolliert. Ein Teil der Auswertung fasst
über das beste Ergebnis mehrerer Läufe zusammen.

Wir übernehmen daraus transparente Grenzen, getrennte Entwicklungsaufwände
und vollständige Berichte über Wiederholungen. Wir übernehmen weder die
Best-of-30-Auswahl noch die Behauptung, fünf Seeds seien für eine Leistungsstudie
ausreichend. Fünf Seeds sind hier ein begrenzter Entwicklungsumfang. Die
Literaturbudgets garantieren keine Verbesserung durch längere Suche.

### Tenachi, Ibata und Diakogiannis (2023): PhySO-Lernverläufe

*Deep symbolic regression for physics guided by units constraints: toward the
automated discovery of physical laws*,
[arXiv:2303.03192v2](https://arxiv.org/html/2303.03192v2), IV.4 und Einleitung V;
[DOI 10.3847/1538-4357/ad014c](https://doi.org/10.3847/1538-4357/ad014c).

Die Lernverläufe zeigen Verbesserungen mit Iterationen, gelegentliches
Entkommen aus lokalen Minima und problem-/hyperparameterabhängige Konvergenz.
Für die Fallstudien sind bis zu zehn Millionen Ausdrucksversuche vorgesehen;
die angegebene Größenordnung von vier Stunden mit mehreren Kernen betrifft
den schwierigsten Fall. PhySO lernt eine Erzeugungsverteilung und nutzt andere
Vorannahmen, einschließlich Einheiten freier Konstanten.

Das begründet die Untersuchung von Budgetabhängigkeit, keine direkte
Übertragung auf PySR. Weder PhySO-Iterationen noch Ausdrucksversuche entsprechen
unseren Suchiterationen oder Verlustcallbacks. Ein späterer Stillstand wäre
ebenfalls ein Ergebnis. Hier wird keine zusätzliche Suchhistorie instrumentiert.

## 2. Was unser Budget tatsächlich verändert

Die [PySR-2.6.0-API](https://pysr.ai/v2.6.0/api) unterscheidet `niterations`,
`ncycles_per_iteration`, Populationen, Populationsgröße und Zeitlimit.
Die installierte gepinnte Quelle wurde zusätzlich direkt gelesen:
[PySR v2.6.0, sr.py](https://github.com/astroautomata/PySR/blob/v2.6.0/pysr/sr.py)
übergibt `int(self.niterations)` an `equation_search`; der
[Backendpfad v2.5.1](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/SymbolicRegression.jl)
initialisiert das Schleifenbudget mit `niterations * populations`.
Die Größenaufwärmung bleibt mit `warmup_maxsize_by=0` deaktiviert.

200 gegen 2.000 Iterationen bedeuten bei sonst gleichem Profil zehnfaches
nominales äußeres Suchbudget. Das ist weder zehnfache Wandzeit noch zehnmal
so viele unabhängige Formeln. Die lokale Konstantenoptimierung bleibt 100/2.
Mehr äußere Suche verursacht allerdings zusätzliche Aufrufe dieser gleichen
Optimierung. Start, Julia-Kompilierung und Export werden separat berücksichtigt.

Die früheren 55–58 Sekunden je Zelle beziehungsweise 371 Sekunden insgesamt
belegen ungenutzten Spielraum zur vereinbarten Ressourcengrenze, keine
Laufzeitprognose für andere Seeds oder Budgets. Eine bloße Erhöhung der
Abbruchgrenze verlängert eine bei 200 Iterationen endende Suche nicht.

## 3. Eigene methodische Folgerung

Der Faktor zehn und fünf neue Seeds sind bewusst gewählte Projektgrößen,
keine aus einem Paper abgeleiteten Optimalwerte. Zwei Budgets unter beiden
Grammatiken erlauben, Budgetwirkung innerhalb jeder Grammatik und den
Grammatikunterschied bei jedem Budget getrennt zu beschreiben. Neue Seeds
am bereits bekannten Signal ergeben keine unabhängige Signalvalidierung.

Der [angenommene Plan](search_duration_plan.md) begrenzt die Serie auf 20
frische Prozesse, 600 Sekunden je Worker und ausdrücklich gewählte zwei
Stunden insgesamt. Die bisherige Vergleichsauswertung wird nicht umgedeutet;
eine Regel wird nicht wegen eines nachträglich ausgesuchten Einzelbaums zum
Standard. Über spätere Tests wird anhand der vollständigen neuen Befunde
entschieden. Neue Solver, Populationsgrößen, Operatoren und Nachfits werden
nicht gleichzeitig ergänzt.
