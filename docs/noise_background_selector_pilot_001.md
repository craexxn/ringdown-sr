# Lesender Auswahlpilot auf Hintergrundserie 002

Methodischer Entwicklungsvergleich vom 19.11.2026,
[Leitfadenphase 7](ringdown_recovery_roadmap.md). Ausgangspunkt sind die
[verifizierte Hintergrundserie](noise_background_results_manjaro_002.md)
und die [begrenzte Kandidatenprüfung](noise_background_candidates_manjaro_002.md).
Diese zeigte bereits gespeicherte Alternativen mit kleineren Zwischenpunktfehlern
bei höherem Trainingsverlust. Der vorliegende Pilot untersucht deshalb eine
einzige festgelegte alternative Auswahlregel auf sämtlichen gespeicherten Paketen.

**Planstand vor der Auswertung:** Umfang und Auswahlregel sind in `scope.json`
festgelegt, SHA-256
`119040430ace6ad80d788c6289e6fb03e5199e5fada1277e8949b3cf5afbd1ea`.
Die folgenden Regeln werden vor dem numerischen Methodenvergleich dokumentiert;
Ergebnisse und tatsächlich abgeschlossene Prüfungen werden anschließend ergänzt.
Die bereits betrachteten Daten bleiben **retrospektive Entwicklungsdaten**.
Eine jetzt festgelegte Auswertung macht sie weder prospektiv noch unabhängig.

## Vollständiger Umfang und unveränderte Originale

Der Pilot umfasst alle **130 ursprünglichen Pakete aus 520 Workern**:
20 AR(1)- und sechs weiße Rauschblöcke, jeweils fünf Gewichtungsarme
O, K, E64, E256 und E1024. Pro Paket werden alle Kandidaten aus den vier
gespeicherten Endfronten eingelesen. HOF-Zeile, native Verlustzahl,
Komplexität, vollständige Originalformel, Binary64-Baum, Workerposition,
Kandidatenzeile und Seed bleiben an ihre Originalquellen gebunden.
Gespeicherte Endfronten sind keine vollständige Suchhistorie.

Zwei Auswahlen je Paket ergeben **260 geplante Ausgaben**. Die historische
Auswahl heißt hier `accuracy`; der alternative Adapter heißt `pooled_best`.
Beide bezeichnen eine lesende Auswahl vorhandener Originalbäume. Die
historischen Ergebnisdateien und eingefrorenen Versuchsprotokolle bleiben
unverändert; es werden keine Fits, Suchen oder Parameteranpassungen ausgeführt.

Native Verluste müssen endlich und nichtnegativ sein, Komplexitäten positive
ganze Zahlen. Ein ungültiger Eintrag bricht den Pilot ausdrücklich ab;
Kandidaten werden nicht stillschweigend aus der Auswahl entfernt.

## Eine festgelegte Auswahlalternative

### Historische Auswahl `accuracy`

Über alle vier Endfronten wird das kleinste Tupel
`(nativer Verlust, Komplexität, Mitgliedsposition, Kandidatenzeile)` gewählt.
Mitgliedspositionen sind 1-basiert, Kandidatenzeilen 0-basiert.
Dies muss jede gespeicherte Worker- und Paketauswahl exakt reproduzieren.

### Gemeinsame Front aus vier gespeicherten Workern

Für jede Komplexität bleibt der Kandidat mit kleinstem Tupel
`(nativer Verlust, Mitgliedsposition, Kandidatenzeile)`.
Nach aufsteigender Komplexität bleibt der erste Punkt und danach nur jeder
Punkt, dessen Verlust sämtliche vorherigen Komplexitätsstufen strikt
unterschreitet. Das ergibt eine nach Verlust und Komplexität gefilterte
gemeinsame Front. Nicht übernommene Zeilen bleiben im ursprünglichen Inventar.

**Dieses Zusammenführen ist ein neuer expliziter Adapter.** Es ist kein
bereits bestehender PySR-Modus zur Auswahl über vier unabhängige Worker.
Die anschließende Regel orientiert sich an `idx_model_selection` und
`calculate_scores` aus PySR 2.6.0, `pysr/sr.py`, Zeilen 3401–3453,
Quellen-SHA-256
`0a7e10fb0e74c4c4c5d98dc06b9be2716c5d62d3c6cea3a469b4eff9ab839bb5`.

### Regel `pooled_best`

Der erste Punkt der gemeinsamen Front erhält Score 0. Für nachfolgende
positive Verluste L und vorangehenden Verlust L_prev gilt in Binary64:

```text
score = -numpy.log(L / L_prev) / (complexity - complexity_prev)
```

Eine nachfolgende Verlustzahl null erhält Score `+Infinity`, entsprechend
PySR. Unterlauf des Verlustquotienten kann ebenfalls `+Infinity` ergeben
und bleibt sichtbar. Die Zulässigkeitsgrenze lautet
`L <= 1.5 * global_min_loss`, mit Binary64-Vergleich. Der Faktor 1,5 stammt
aus der gebundenen Bibliotheksregel; er wird auf diesen Daten nicht angepasst.
Bei Überlauf der Grenze zu `+Infinity` sind alle endlichen Verluste zulässig.
Ein globales Minimum null lässt den niedrigstkomplexen Nullverlustpunkt zu;
weitere Nullverlustpunkte sind keine strikten Frontverbesserungen.

Unter den zulässigen Punkten wird der höchste Score gewählt. Gleiche Scores
wählen den ersten Punkt der aufsteigend sortierten Front; Mitglied und Zeile
sind durch die vorherigen Schritte bereits eindeutig. Es gibt keine
numerische Gleichstandstoleranz. Nichtfinite positive Scores oder Grenzen
werden als Zeichenkette `+Infinity` geschrieben, niemals als ungültige
numerische JSON-Literale.

Die beiden Kandidatenidentitäten werden je Paket aus Verlust und Komplexität
ausgewählt und gespeichert, **bevor** die Wahrheit für deren Auswertung
gelesen oder bewertet wird. Die Wahrheit steuert weder Rückfallregel noch
erneute Auswahl. Eine nachträgliche Anpassung dieser einen Alternative ist
nicht Teil dieses Piloten.

## Festgelegte Auswertung und grafischer Umfang

Je gewähltem Originalbaum werden die vorhandenen 128 Trainings-, 889 regulären
Zwischen- und 1.024 unregelmäßigen Punkte verwendet. Native Trainingsvorhersagen
bleiben erhalten; auf den beiden Zusatzrastern wird der unveränderte Baum
lesend ausgewertet. Keine neuen Stützstellen, geglätteten Ersatzformeln oder
numerischen Spitzensuchen. `t` ist physische Zeit in Sekunden; Fehler zur
sauberen Wahrheit werden durch |A| normiert.

Erfasst werden RMSE, maximaler Absolutfehler und vollständige Endlichkeitsnenner
pro Raster. Ist eine Vorhersage oder ein Residuum nicht endlich, bleibt das
ganze Rastermaß unverfügbar; kein Ersatz durch die endliche Teilmenge.
Jede der 260 geplanten Ausgaben bleibt mit ihrem Status sichtbar. Aggregate,
die fehlende Werte benötigen, bleiben unverfügbar.

AR(1) mit 20 und white mit sechs Fällen werden getrennt für alle fünf Arme
berichtet. Der Fokus liegt auf dem unregelmäßigen RMSE für AR(1)/E1024;
alle weiteren Gruppen und Maße bleiben erhalten. Berichtet werden gepaarte
Differenzen `pooled_best minus accuracy`, Mittel, Median, Min/Max sowie
Zahlen kleinerer, gleicher und größerer Paare. Negative Differenzen bedeuten
kleineren Fehler unter `pooled_best`. Es werden keine neuen bestätigenden
Grenzwerte, p-Werte oder Konfidenzaussagen eingeführt.

Die vollständigen 130 Paarzeilen, beide unveränderten Originalformeln und
zugehörigen Punktdaten gehören zur getrennten grafischen Ausgabe. Alle
sechs zuvor diskutierten auffälligen Ausgaben werden beschrieben, ohne den
Pilot darauf einzuschränken. Verbesserungen, Verschlechterungen, Spitzen
und unverfügbare Werte bleiben sichtbar.

## Quellenbindung und Aussagegrenzen

Originalarchiv `noise-background-manjaro-002-plots-recovered.tar.gz`, SHA-256
`b2a4ace2d9097099822ab524377537dae24d59c7ba59e137de11ae5ba3e4214d`;
ursprünglicher Ausführungscommit
`bd42634b888c2dbaa5a92726b9a1f9851c766a48`.
Serienbericht-SHA-256:
`659f60e8521ba21d012ce3d2202d556e666c1f1cc8b01cf7452cc7f81dc6fdd3`.
Dokumentarische Ausgangsfassung der Kandidatenprüfung:
`c7964457aa06296cd6e48ab7d1df72f30ab81888`.
Das bereits geprüfte Originalmanifest hat SHA-256
`c78905263585dd77ab18634c64ff8940a428a2a5a15d787a3b7b8f063fe3efa5`.

Die Ausgaben sind gepaart auf 130 vorhandenen Kandidatenpools innerhalb von
26 Rauschblöcken; es sind keine 260 unabhängigen Beobachtungen. Endliche
Rasterwerte beweisen weder kontinuierliche Gültigkeit noch Familien- oder
Domainzugehörigkeit. Es werden keine neuen Strukturzertifikate vergeben.

Der Entwicklungsvergleich soll eine Entscheidung über einen späteren frischen
Methodenvergleich informieren. Er übernimmt keine Methode automatisch und
startet keine lange wissenschaftliche Serie. Änderungen an der hier festgelegten
Alternative benötigen einen gesondert dokumentierten Vergleich; eine
unabhängige Bestätigung benötigt neue, vorher geplante Daten.
