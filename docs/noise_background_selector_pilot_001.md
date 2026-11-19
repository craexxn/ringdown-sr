# Lesender Auswahlpilot auf Hintergrundserie 002

Methodischer Entwicklungsvergleich vom 19.11.2026,
[Leitfadenphase 7](ringdown_recovery_roadmap.md). Ausgangspunkt sind die
[verifizierte Hintergrundserie](noise_background_results_manjaro_002.md)
und die [begrenzte Kandidatenprüfung](noise_background_candidates_manjaro_002.md).
Diese zeigte bereits gespeicherte Alternativen mit kleineren Zwischenpunktfehlern
bei höherem Trainingsverlust. Der vorliegende Pilot untersucht deshalb eine
einzige festgelegte alternative Auswahlregel auf sämtlichen gespeicherten Paketen.

**Negativer Entwicklungsbefund:** Die festgelegte Alternative erhöht in
allen zehn Modell-Arm-Gruppen den mittleren unregelmäßigen RMSE. Im
Fokus AR(1)/E1024 steigt er von **0,040713146 auf 0,087431990**,
gepaart im Mittel **+0,046718844**. Zwölf der 20 Paare werden auf diesem Maß
kleiner, acht größer; große Verschlechterungen bestimmen den höheren Mittelwert.
Für zwei der zuvor auffälligen Ausgaben sinken die Rasterfehler stark;
andere Ausgaben zeigen unter der Alternative große Zwischenpunktfehler. Daraus wird keine Übernahme dieser
Regel und kein Start einer langen Bestätigungsserie abgeleitet.

Der Pilot ist vollständig: **6.985 Kandidaten aus 520 Workern, 130 Pakete,
260 Ausgaben und 530.660 ausgewertete Punkte**, alle Rastermaße verfügbar.
Die alternative Regel wählt in allen 130 Paketen einen anderen Originalbaum;
die historischen Auswahlen und Dateien bleiben unverändert.

Umfang und Auswahlregel wurden vor Anwendung in `scope.json` festgelegt,
SHA-256 `119040430ace6ad80d788c6289e6fb03e5199e5fada1277e8949b3cf5afbd1ea`,
und als Dokumentationsstand
`2e538ec92142be4fd2f1d2fdf4883b7af7ce200f` vorab veröffentlicht.
Die bereits betrachteten Daten bleiben **retrospektive Entwicklungsdaten**.
Diese Festlegung macht sie weder prospektiv noch unabhängig.

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
Scores werden auf der gemeinsamen Front neu berechnet; bereits gespeicherte
Scores einzelner Worker werden nicht als gemeinsame Rangliste verwendet.

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

## Ergebnisse aller zehn Modell-Arm-Gruppen

Jede Tabelle enthält alle sechs vorab benannten Maße. `best` bezeichnet
in Tabellen und Artefakten **pooled_best**; Δ ist jeweils best−accuracy.
Alle Tabellenwerte sind durch die Signalamplitude |A| normiert und dimensionslos.
Die Mittel beider Regeln sowie Mittel, Median und Min/Max der gepaarten
Differenzen sind getrennt angegeben. Die Richtungszählung lautet
**kleiner / gleich / größer**; unverfügbare Paare gibt es in keiner Gruppe.
Die 20 beziehungsweise sechs Paare einer Gruppe bleiben der Nenner.
`Max` bezeichnet den Maximalfehler je Ausgabe; sein Mittel ist das Mittel
dieser Einzelmaxima und nicht die größte Spitze der gesamten Gruppe.

Die vollständigen Einzelstatistiken beider Regeln einschließlich ihrer
Mediane und Min/Max stehen in `group-summary.json` und `summary.json`.
Alle 130 Fall-Arm-Paare mit sechs Maßen, Quellenidentitäten, Verlusten,
Komplexitäten und Statusnennern stehen vollständig in `paired-metrics.csv`.
Die Tabellen sind deskriptiv und begründen weder unabhängige Erfolgsquoten
noch bestätigende Überlegenheitsaussagen.

### AR(1): jeweils 20 Paare

#### O

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,023913 | 0,019754 | -0,004159 | -0,002231 | -0,017443 | +0,002891 | 17 / 0 / 3 |
| Training Max | 0,071194 | 0,085190 | +0,013996 | +0,019718 | -0,050596 | +0,044745 | 5 / 0 / 15 |
| Regulär RMSE | 0,023735 | 0,035886 | +0,012151 | -0,002772 | -0,017757 | +0,336991 | 17 / 0 / 3 |
| Regulär Max | 0,071156 | 0,174534 | +0,103378 | +0,020094 | -0,050584 | +1,832651 | 5 / 0 / 15 |
| Unregelmäßig RMSE | 0,023736 | 0,034838 | +0,011102 | -0,002779 | -0,017760 | +0,316065 | 17 / 0 / 3 |
| Unregelmäßig Max | 0,071356 | 0,174471 | +0,103115 | +0,021477 | -0,050598 | +1,810828 | 5 / 0 / 15 |

#### K

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,024081 | 0,035522 | +0,011442 | +0,015497 | -0,009783 | +0,034515 | 7 / 0 / 13 |
| Training Max | 0,078642 | 0,161615 | +0,082973 | +0,101381 | -0,016937 | +0,181380 | 3 / 0 / 17 |
| Regulär RMSE | 0,042761 | 0,050348 | +0,007587 | +0,004118 | -0,249767 | +0,338381 | 10 / 0 / 10 |
| Regulär Max | 0,725024 | 0,250898 | -0,474125 | +0,023778 | -8,626383 | +1,956424 | 6 / 0 / 14 |
| Unregelmäßig RMSE | 0,049253 | 0,049567 | +0,000314 | +0,013067 | -0,492257 | +0,322594 | 9 / 0 / 11 |
| Unregelmäßig Max | 0,959246 | 0,247884 | -0,711362 | +0,023794 | -16,232602 | +1,888382 | 6 / 0 / 14 |

#### E64

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,026600 | 0,021529 | -0,005071 | -0,005161 | -0,017920 | +0,007738 | 18 / 0 / 2 |
| Training Max | 0,078781 | 0,090702 | +0,011921 | +0,015203 | -0,055914 | +0,094011 | 7 / 0 / 13 |
| Regulär RMSE | 0,026442 | 0,037832 | +0,011390 | -0,005183 | -0,017195 | +0,331256 | 17 / 0 / 3 |
| Regulär Max | 0,078283 | 0,178062 | +0,099779 | +0,021236 | -0,039529 | +1,765055 | 8 / 0 / 12 |
| Unregelmäßig RMSE | 0,026442 | 0,036825 | +0,010383 | -0,005176 | -0,017236 | +0,311092 | 17 / 0 / 3 |
| Unregelmäßig Max | 0,079039 | 0,181767 | +0,102728 | +0,021657 | -0,051272 | +1,818796 | 8 / 0 / 12 |

#### E256

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,026985 | 0,025807 | -0,001178 | -0,002926 | -0,018600 | +0,028876 | 14 / 0 / 6 |
| Training Max | 0,088868 | 0,109711 | +0,020843 | +0,011978 | -0,085095 | +0,186096 | 9 / 0 / 11 |
| Regulär RMSE | 0,026812 | 0,059154 | +0,032342 | -0,001641 | -0,014991 | +0,344389 | 14 / 0 / 6 |
| Regulär Max | 0,105809 | 0,292169 | +0,186360 | +0,021560 | -0,064873 | +1,867850 | 7 / 0 / 13 |
| Unregelmäßig RMSE | 0,026885 | 0,056227 | +0,029342 | -0,001639 | -0,015019 | +0,305302 | 14 / 0 / 6 |
| Unregelmäßig Max | 0,114774 | 0,288403 | +0,173629 | +0,021543 | -0,064379 | +1,766623 | 8 / 0 / 12 |

#### E1024

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,025346 | 0,028186 | +0,002840 | -0,001263 | -0,021846 | +0,030307 | 12 / 0 / 8 |
| Training Max | 0,073827 | 0,122691 | +0,048863 | +0,024524 | -0,044992 | +0,180617 | 6 / 0 / 14 |
| Regulär RMSE | 0,041318 | 0,090008 | +0,048690 | -0,001380 | -0,326897 | +0,336356 | 12 / 0 / 8 |
| Regulär Max | 0,158032 | 0,480119 | +0,322087 | +0,027442 | -1,684495 | +1,956591 | 6 / 0 / 14 |
| Unregelmäßig RMSE | 0,040713 | 0,087432 | +0,046719 | -0,001388 | -0,314537 | +0,327638 | 12 / 0 / 8 |
| Unregelmäßig Max | 0,162558 | 0,462081 | +0,299522 | +0,027479 | -1,769257 | +1,948070 | 5 / 0 / 15 |

### Weißes Rauschen: jeweils sechs Paare

#### O

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,016139 | 0,016467 | +0,000329 | +0,000256 | -0,002334 | +0,004103 | 2 / 0 / 4 |
| Training Max | 0,049674 | 0,083142 | +0,033469 | +0,033327 | +0,011958 | +0,052884 | 0 / 0 / 6 |
| Regulär RMSE | 0,015967 | 0,071690 | +0,055723 | +0,000434 | -0,002949 | +0,334016 | 3 / 0 / 3 |
| Regulär Max | 0,049038 | 0,383623 | +0,334584 | +0,037845 | +0,020494 | +1,826946 | 0 / 0 / 6 |
| Unregelmäßig RMSE | 0,015976 | 0,068273 | +0,052297 | +0,000420 | -0,002960 | +0,313531 | 3 / 0 / 3 |
| Unregelmäßig Max | 0,049912 | 0,385783 | +0,335871 | +0,039492 | +0,023206 | +1,830327 | 0 / 0 / 6 |

#### K

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,015865 | 0,016471 | +0,000606 | +0,001690 | -0,003659 | +0,004047 | 2 / 0 / 4 |
| Training Max | 0,049470 | 0,083158 | +0,033688 | +0,032321 | +0,015722 | +0,049293 | 0 / 0 / 6 |
| Regulär RMSE | 0,112526 | 0,185027 | +0,072502 | +0,002173 | -0,004430 | +0,336074 | 1 / 0 / 5 |
| Regulär Max | 0,508849 | 1,016265 | +0,507416 | +0,092265 | +0,019082 | +1,824614 | 0 / 0 / 6 |
| Unregelmäßig RMSE | 0,103627 | 0,171358 | +0,067731 | +0,005508 | -0,004435 | +0,315471 | 1 / 0 / 5 |
| Unregelmäßig Max | 0,485003 | 0,965871 | +0,480869 | +0,069377 | +0,022330 | +1,834720 | 0 / 0 / 6 |

#### E64

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,014325 | 0,016558 | +0,002234 | +0,001402 | -0,000179 | +0,004976 | 1 / 0 / 5 |
| Training Max | 0,046489 | 0,083276 | +0,036787 | +0,034377 | +0,019326 | +0,056105 | 0 / 0 / 6 |
| Regulär RMSE | 0,068692 | 0,129109 | +0,060417 | +0,003816 | -0,000911 | +0,343330 | 1 / 0 / 5 |
| Regulär Max | 0,348545 | 0,700301 | +0,351756 | +0,052841 | +0,015869 | +1,882298 | 0 / 0 / 6 |
| Unregelmäßig RMSE | 0,066801 | 0,122612 | +0,055811 | +0,002284 | -0,000920 | +0,327816 | 2 / 0 / 4 |
| Unregelmäßig Max | 0,359357 | 0,701540 | +0,342183 | +0,047313 | -0,038154 | +1,922570 | 1 / 0 / 5 |

#### E256

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,016105 | 0,016749 | +0,000644 | +0,000054 | -0,004186 | +0,005291 | 3 / 0 / 3 |
| Training Max | 0,056497 | 0,087674 | +0,031178 | +0,042277 | -0,022134 | +0,053820 | 1 / 0 / 5 |
| Regulär RMSE | 0,015773 | 0,127650 | +0,111877 | +0,002128 | -0,004865 | +0,340781 | 3 / 0 / 3 |
| Regulär Max | 0,054831 | 0,674309 | +0,619478 | +0,050354 | -0,015123 | +1,937066 | 1 / 0 / 5 |
| Unregelmäßig RMSE | 0,015788 | 0,118186 | +0,102397 | +0,002117 | -0,004875 | +0,320249 | 3 / 0 / 3 |
| Unregelmäßig Max | 0,056236 | 0,655018 | +0,598783 | +0,051703 | -0,020311 | +1,889460 | 1 / 0 / 5 |

#### E1024

| Maß / \|A\| | Mittel accuracy | Mittel best | Mittel Δ | Median Δ | Min Δ | Max Δ | Richtung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Training RMSE | 0,015592 | 0,016467 | +0,000875 | +0,000884 | -0,001337 | +0,003507 | 2 / 0 / 4 |
| Training Max | 0,046669 | 0,082343 | +0,035674 | +0,036768 | +0,009800 | +0,051504 | 0 / 0 / 6 |
| Regulär RMSE | 0,015464 | 0,129281 | +0,113817 | +0,001677 | -0,002032 | +0,341456 | 2 / 0 / 4 |
| Regulär Max | 0,045825 | 0,690226 | +0,644401 | +0,041329 | +0,004789 | +1,889368 | 0 / 0 / 6 |
| Unregelmäßig RMSE | 0,015471 | 0,123480 | +0,108009 | +0,001652 | -0,002031 | +0,325885 | 2 / 0 / 4 |
| Unregelmäßig Max | 0,046699 | 0,698468 | +0,651769 | +0,043584 | +0,008463 | +1,915594 | 0 / 0 / 6 |

Im Fokus AR(1)/E1024 steht dem positiven mittleren Unterschied
+0,046718844 ein Median von −0,001388042 gegenüber. Einzelne hohe Fehler
bleiben daher wesentlich. Auch bei O unter AR(1) haben 17/20 Paare kleinere
unregelmäßige RMSE, während der Mittelwert von 0,023735711 auf 0,034837624
steigt. Die Richtungsmehrheit ersetzt die Mittel- und Spitzenbetrachtung nicht.
Diese 20 beziehungsweise sechs bekannten Blöcke liefern keine neue unabhängige
Bestätigung über andere Signale oder Rauschbedingungen.

## Sechs zuvor diskutierte Ausgaben

Der Pfeil bezeichnet **accuracy → pooled_best** bei demselben gespeicherten
Kandidatenpool. Alle vier Zusatzrastermaße werden erhalten.

| Fall / Arm | RMSE unregelmäßig | RMSE regulär | Max unregelmäßig | Max regulär |
| --- | --- | --- | --- | --- |
| ar1-04 / E1024 | 0,334601 → 0,020064 | 0,346956 → 0,020059 | 1,861500 → 0,092243 | 1,776751 → 0,092255 |
| white-01 / E64 | 0,331551 → 0,330823 | 0,342934 → 0,354316 | 1,930188 → 1,892034 | 1,867137 → 1,933897 |
| white-03 / K | 0,315540 → 0,323749 | 0,354028 → 0,354261 | 1,726056 → 1,816723 | 1,840121 → 1,978335 |
| white-06 / K | 0,238915 → 0,321735 | 0,253850 → 0,352640 | 0,977952 → 1,829363 | 1,006982 → 1,986160 |
| ar1-18 / K | 0,511525 → 0,019268 | 0,086048 → 0,019273 | 16,310949 → 0,078347 | 2,431515 → 0,075955 |
| ar1-17 / K | 0,036263 → 0,048332 | 0,298079 → 0,048312 | 0,836123 → 0,231653 | 8,858003 → 0,231620 |

AR1-04/E1024 und AR1-18/K haben unter der Alternative auf beiden Rastern
wesentlich kleinere RMSE und Spitzen. White-01/E64 bleibt stark auffällig:
der unregelmäßige RMSE sinkt geringfügig, der reguläre RMSE steigt.
White-03/K und white-06/K werden auf beiden Zusatzrastern schlechter.
AR1-17/K hat einen kleineren regulären RMSE und kleinere Spitzen, aber
einen höheren unregelmäßigen RMSE. Damit ergeben auch die bereits bekannten
Problemfälle kein einheitlich günstiges Bild.

## Verschlechterungen vollständig erhalten

Die folgende Liste nennt **alle 50 Paare mit höherem unregelmäßigem RMSE**,
getrennt nach Modell und Arm. Sie ist keine gepoolte Ausfallquote.
Verschlechterungen der anderen fünf Maße stehen in den Gruppenzählungen und
für jedes Paar im vollständigen CSV, einschließlich Richtungswechseln zwischen
Rastern wie white-01/E64 und AR1-17/K.

| Modell | Arm | Anzahl | Sämtliche betroffenen Fälle |
| --- | --- | --- | --- |
| ar1 | O | 3 | ar1-07, ar1-19, ar1-20 |
| ar1 | K | 11 | ar1-01, ar1-02, ar1-05, ar1-10, ar1-11, ar1-12, ar1-13, ar1-14, ar1-15, ar1-16, ar1-17 |
| ar1 | E64 | 3 | ar1-03, ar1-12, ar1-20 |
| ar1 | E256 | 6 | ar1-05, ar1-10, ar1-11, ar1-12, ar1-13, ar1-19 |
| ar1 | E1024 | 8 | ar1-02, ar1-03, ar1-10, ar1-11, ar1-12, ar1-13, ar1-16, ar1-20 |
| white | O | 3 | white-01, white-02, white-06 |
| white | K | 5 | white-01, white-02, white-03, white-04, white-06 |
| white | E64 | 4 | white-02, white-03, white-05, white-06 |
| white | E256 | 3 | white-02, white-04, white-06 |
| white | E1024 | 4 | white-02, white-03, white-05, white-06 |

Die größte positive Änderung dieses Maßes ist white-03/E64:
0,014566400 → 0,342382254. Unter AR(1) ist es AR1-10/E1024:
0,018093776 → 0,345732012. Dieser Kandidat hat Komplexität 9 und zugleich
die größte Spitze aller alternativen Ausgaben, **2,004458467 |A| regulär**
und **1,995607088 |A| unregelmäßig**. Sein vollständiger Originaltext enthält
`cos(-53173.88303509549 * t)`: geringe Baumkomplexität begrenzt die Frequenz
nicht. Das ist eine Beschreibung der gespeicherten Formel, keine Einführung
eines Frequenzfilters oder einer nachträglichen Aliasumrechnung.

Weitere große Verschlechterungen betreffen beispielsweise AR1-11/E1024,
AR1-13/E1024, AR1-16/E1024 und AR1-20/O. Sämtliche 130 Paarplots bleiben
verfügbar; es werden keine Fälle entfernt, Schwellen angepasst oder andere
Heuristiken in diesen Pilot eingeschoben.

## Unveränderte Originalformeln ausgewählter Ausgaben

Die folgenden vollständigen Formeln zeigen die sechs zuvor diskutierten
Fall-Arme sowie nachträglich zur Erklärung die größte Verschlechterung je
Rauschmodell und die auffällige neue O-Ausgabe AR1-20. Diese Textauswahl
verändert keine Berechnung oder Auswahlregel; alle 260 Formeln stehen
vollständig in den separaten Ausgabe-JSON und `.formula.txt`-Dateien.
`mNN` ist 1-basiert, `cNNN` der nullbasierte ursprüngliche Kandidatenindex.
`t` bleibt in Sekunden. Vorhandene Divisionen und Baumstruktur werden
nicht vereinfacht; keine neue Domain- oder Familienfreigabe.

### ar1-04 / E1024

**accuracy, unveränderte historische Auswahl** — `ar1-04--estimated_1024--m01--c013`,
Suchseed `1008562290`, Komplexität 20:

```text
(cos(5.940473929766483 - (((exp(122.30191354295101 * t) * 2.9386242521385464) - -53118.27006769258) * t)) * exp(-135.03627776760692 * t)) / 1.15457182464067
```

**pooled_best, alternative Auswahl** — `ar1-04--estimated_1024--m02--c006`,
Suchseed `1905374137`, Komplexität 11:

```text
exp(t * -159.29719269672808) * sin(-136.32648792944914 + (1658.1818618281693 * t))
```

### white-01 / E64

**accuracy, unveränderte historische Auswahl** — `white-01--estimated_64--m02--c010`,
Suchseed `1697294631`, Komplexität 20:

```text
24.820423537229164 * ((-0.9644427726668939 + sin(0.3776976974791814 * (sin((t * 26565.516007289254) + -12.437764023114845) + -12.460720072636207))) * exp(-145.39699314872263 * t))
```

**pooled_best, alternative Auswahl** — `white-01--estimated_64--m02--c005`,
Suchseed `1697294631`, Komplexität 11:

```text
sin((t * 127027.574635221) + 45.255614051529705) * exp(t * -166.1151321647192)
```

### white-03 / K

**accuracy, unveränderte historische Auswahl** — `white-03--known_covariance--m04--c012`,
Suchseed `1790832426`, Komplexität 20:

```text
sin(exp(t * -161.53732296873838) * ((sin((t * -78874.77003967474) - 17.532198018765996) - (t * -10.270908290192056)) / 0.9485291541761623)) - 0.013847622661166948
```

**pooled_best, alternative Auswahl** — `white-03--known_covariance--m04--c007`,
Suchseed `1790832426`, Komplexität 11:

```text
exp(-158.38063458934548 * t) * sin((t * -104606.96875364197) - -20.142625367436434)
```

### white-06 / K

**accuracy, unveränderte historische Auswahl** — `white-06--known_covariance--m01--c011`,
Suchseed `1164831031`, Komplexität 20:

```text
((exp(-153.84509721506612 * t) / -0.5252274928335174) * cos((-7266.665398221601 * t) - 16.61947485081251)) * cos(365.0920683335862 - (-5594.918661652619 * t))
```

**pooled_best, alternative Auswahl** — `white-06--known_covariance--m01--c005`,
Suchseed `1164831031`, Komplexität 11:

```text
cos(119.6345822988216 - (t * -104613.869956716)) * exp(-161.76535886141548 * t)
```

### ar1-18 / K

**accuracy, unveränderte historische Auswahl** — `ar1-18--known_covariance--m02--c016`,
Suchseed `1488595906`, Komplexität 20:

```text
sin(exp(-0.6738614982681183 * t) * 2451.677993976513) * exp(t * ((t * -137.58024211952096) / (0.6930790158983643 + (t - 0.693741395011374))))
```

**pooled_best, alternative Auswahl** — `ar1-18--known_covariance--m01--c007`,
Suchseed `1461571083`, Komplexität 11:

```text
sin((t * -1652.063740587144) - 294.01987425696393) / exp(t * 155.03917254457528)
```

### ar1-17 / K

**accuracy, unveränderte historische Auswahl** — `ar1-17--known_covariance--m03--c013`,
Suchseed `579531758`, Komplexität 20:

```text
((-1.248017848584053e-5 / (0.0025019075523771816 - t)) + ((-0.007846766347782887 / (-0.007032147891488022 - t)) + -0.23295800028326924)) * cos((t / -0.0005999378981636545) - 0.1874457075958824)
```

**pooled_best, alternative Auswahl** — `ar1-17--known_covariance--m04--c004`,
Suchseed `1822901715`, Komplexität 9:

```text
exp(-165.15754058477265 * t) * cos(t * -1693.5173613076538)
```

### white-03 / E64

**accuracy, unveränderte historische Auswahl** — `white-03--estimated_64--m04--c011`,
Suchseed `1790832426`, Komplexität 20:

```text
sin(((cos((t * 1666.9889798941786) - 75.14478525352737) - (t / -0.09736237653047365)) * 1.0542638540109186) / exp(t * 161.53732334014086)) + -0.013847621897924864
```

**pooled_best, alternative Auswahl** — `white-03--estimated_64--m03--c006`,
Suchseed `1327216417`, Komplexität 11:

```text
exp(t * -158.38063349562285) * sin((t * -49808.59334865933) - -1.8485231790261236)
```

### ar1-10 / E1024

**accuracy, unveränderte historische Auswahl** — `ar1-10--estimated_1024--m03--c010`,
Suchseed `702735018`, Komplexität 17:

```text
((sin(-0.08022180070704832 / (t + 0.02643040008061821)) + 1.0214381657300762) * cos(0.23917434787591027 + (1663.906387728266 * t))) - -0.010389032009089775
```

**pooled_best, alternative Auswahl** — `ar1-10--estimated_1024--m04--c004`,
Suchseed `1536548225`, Komplexität 9:

```text
exp(-164.31644975794768 * t) * cos(-53173.88303509549 * t)
```

### ar1-20 / O

**accuracy, unveränderte historische Auswahl** — `ar1-20--ordinary--m04--c014`,
Suchseed `1931697111`, Komplexität 19:

```text
(cos((t + -0.0074161516930918905) / 0.0006062921864903537) * sin(-0.177825560223043 + (0.005442364919170415 / (t + 0.0037885035322206993)))) + (t * 0.3877269233198608)
```

**pooled_best, alternative Auswahl** — `ar1-20--ordinary--m03--c006`,
Suchseed `100106180`, Komplexität 11:

```text
sin((t * -24087.214826597487) - 42.0696900160896) * exp(t * -160.85771122997193)
```

## Ausgeführte technische Prüfungen und Kosten

Alle 6.985 Kandidaten sind an HOF-Text, Originalbaum, nativen Verlust,
Komplexität, Worker-/Seedzuordnung und ursprüngliche Quellen gebunden.
Die historischen 520 Workerwahlen und 130 Paketauswahlen werden exakt
reproduziert. Alle 130 gemeinsamen Fronten und alternativen Entscheidungen
stimmen mit den gebundenen PySR-Referenzfunktionen überein. Sieben gültige
Randfall-Fixtures prüfen Gleichstände, Nullverluste, Quotientenunterlauf und
Grenzwertüberlauf; neun ungültige Eingabefälle werden abgelehnt.
Die `+Infinity`-Serialisierung wurde hin und zurück geprüft; zehn analytische
Primitive prüfen die Baumoperationen. Insgesamt bestehen 34.244 Datenchecks.

Alle 130 Entscheidungen wurden in `selection-decisions.json` geschrieben,
bevor die Wahrheit ausgewertet wurde; SHA-256
`f4b787c83d925eaf1ae927f84524f8a0577248d1c38a246106600505ab253777`.
Dieser Auswahlabschnitt benötigte 6,456889 s und ist **in** der gesamten
Auditzeit von **17,898572 s** enthalten; die Zeiten werden nicht addiert.
Die Auditzeit umfasst den Export, ausgenommen abschließendes Schreiben von
Bericht und Manifest. CPU User/System: 13,350742/3,713227 s;
Prozess-Spitzen-RSS: 171.900 KiB. 2.758 konsumierte Originaldateien bleiben
vor und nach der Prüfung bytegleich. Dies sind Kosten des lesenden Piloten,
keine zusätzlichen Suchkosten der wissenschaftlichen Serie.

Auditor `audit_selectors.py`, SHA-256
`c275548410111537a104c4a702bbcbdf579b1ac6b4879c63d3c65b3ddc033704`;
Python 3.12.14, NumPy 2.5.3 und pandas 3.0.6.
Die PySR-Referenzfunktionen stammen aus der oben gebundenen Quelle;
PySR und Julia wurden nicht importiert. Alle 530.660 Punktwerte sind
verfügbar. Der Vergleich der accuracy-Maße mit dem ursprünglichen
Serienbericht weicht bei RMSE höchstens um 5,55×10⁻¹⁷ und bei Maximalfehlern
um 4,44×10⁻¹⁶ ab.

Die unabhängige Gegenprüfung `independent-check.json` ist bestanden,
SHA-256 `497b4b2a413fddf788adbef8b0bce4b77fd5b4de646ecdedb6b1acc4639d31e4`.
Sie bestimmt die gemeinsame Front durch paarweise Dominanzvergleiche aus
allen Originalzeilen, prüft die isolierten Bibliotheksfunktionen und fixiert
alle 260 Identitäten vor dem Lesen der Wahrheit. Kanonischer Originalbaum-
Evaluator, skalare Residuen und `hypot`-Normen bestätigen alle Punkte;
der Hauptauditor wird nicht importiert. 21 analytische Referenzfälle und
302.804 Checks bestehen. Alle 130 Paarzeilen und zehn Gruppen stimmen.

Alle 497.380 Zusatzvorhersagen sind bitgleich, alle 33.280 nativen
Trainingsvorhersagen bleiben erhalten. Größte absolute RMSE-Abweichung:
5,55×10⁻¹⁷; Maximalfehler zum neuen Export stimmen exakt. Die größte
Paar-/Aggregatabweichung beträgt 1,11×10⁻¹⁶; Prüftoleranzen absolut
2×10⁻¹⁵ und relativ 2×10⁻¹³. 1.048 Auditnutzdateien sind hashgeprüft,
und **alle 18.166 Originaldateien mit 2.027.757.507 Bytes bleiben unverändert**
gegenüber dem gebundenen Baseline-Manifest. Keine neue vollständige
wissenschaftliche Ausführung ist damit verbunden.

Gegenprüfer `independent-check.py`, SHA-256
`8552906e40d3b343f79c136302cbfb9b6e1bc36de972b00b4d035a26c0c58e62`.
Sein gemessener Lauf benötigt 31,870442 s ohne abschließendes Berichtsschreiben,
CPU User/System 23,043857/3,514805 s und Prozess-Spitzen-RSS 995.840 KiB.
Diese Gegenprüfung ist ein separater Aufruf und kein Anteil der oben genannten
Auditzeit. Die Prüfnachweise sind technische Reproduktionsbelege; sie ändern
nicht den retrospektiven Entwicklungsstatus der Daten.

## Grafischer Export und Archivierung

Die abgeschlossene portable Galerie `gallery/index.html` enthält alle
**130 Paarplots**, zehn Gruppenübersichten als PNG/SVG/CSV und zehn
verkleinerte Kontaktbögen. Alle 260 vollständigen Originalformeln und
530.660 Punktzeilen sind zugeordnet; die 780 Auswahl-JSON-, CSV- und
Formeldateien sind bytegleich übernommen. Alle 140 PNGs sind dekodierbar,
1.237 lokale Linkvorkommen geprüft. Die Darstellung verwendet vorhandene
Stützstellen und volle endliche Wertebereiche; Übersichtslinien verbinden
nur die beiden Auswahlen desselben Blocks. `gallery-inventory.json` bindet
Dateien, Kopien, Generator und tatsächlich gemessene Kosten.

Galeriearchiv `noise-background-manjaro-002-selector-pilot-gallery.zip`:
**82.658.247 Bytes**, 961 Dateien, SHA-256
`f4c76a959fc9ead7447cfc31cd4db54a7992f6f1a5868f097de16a56c0d12c5f`.
ZIP-CRC und Quellenkopien sind geprüft. Für den Transport liegen vier Teile
von höchstens 24 MiB und `selektor-galerie-helfer.zip` mit einem
Zusammenfügehelfer vor. Die tatsächlich exportierten Teile wurden damit
zum exakten Archivhash zusammengesetzt; ein bereits gültiges Archiv blieb
erhalten. Die Teilhashes und Helferbelege stehen in
`gallery-transport-verification.json`.

Der Galerieaufbau benötigte 58,846956 s ohne Inventar-/Manifestabschluss;
Verpackung, Aufteilung und Helferprüfung separat 14,897351 s ohne
abschließenden Transportbericht. Diese Aufrufe sind getrennt vom numerischen
Audit und sind keine neuen wissenschaftlichen Suchkosten. Generator-SHA-256:
`4ccee11727f7f1f8876d38eb98553fbb6e0ed35b5801161e482a19880aa7699a`.
Die unabhängige visuelle Gegenprüfung ist abgeschlossen: alle zehn
Gruppen-PNGs und zehn Kontaktbögen über 130 Paarvorschauen sowie acht
gezielte Paarplots in voller Auflösung wurden gesichtet. Das sind die sechs
bekannten auffälligen Fall-Arme und die neuen Gegenbeispiele white-03/E64
und ar1-10/E1024. Keine konkreten Darstellungsfehler festgestellt; alte und
neue große Abweichungen bleiben sichtbar. `visual-check.json`, SHA-256
`8fd75e1c5dc88dd79d296868452ebde63ba14eccb4bf5d417aca544e62de2e8c`,
bindet den tatsächlichen Umfang und alle gesichteten Dateien. Keine
Detailprüfung aller 130 Vollbilder; SVGs wurden nicht separat gerendert.

Das kompakte Nachweispaket
`noise-background-manjaro-002-selector-pilot-audit.zip` umfasst **6.362.393 Bytes**,
SHA-256 `91c729ff71ea6de13717d817dfd487660949f75c09d2e132f891de09bf6a6605`.
Es enthält 540 Nutzdateien plus internes Manifest: Scope, Audit- und
Gegenprüfprogramme, alle Frontinventare, 260 vollständige gewählte Kandidaten,
Paar-/Gruppenmetriken, Originalmanifest und numerische/visuelle Nachweise.
Die großen Punkt-CSV und Bilder bleiben im getrennten Galeriearchiv gebunden;
das kompakte Paket ersetzt weder dieses noch das ursprüngliche Studienarchiv.
Alle enthaltenen Hashes und ZIP-CRC sind geprüft, konsumierte Auditdateien
unverändert. Verpackung und Prüfung benötigten weitere 1,777073 s ohne
abschließenden Verpackungsbericht; `audit-bundle-verification.json` hält
die gemessenen Kosten getrennt fest.

Die Originalausgaben der abgeschlossenen wissenschaftlichen Serie bleiben
separat erhalten. Eine unabhängige Sicherung ist nach der
[Archivierungsrichtlinie](results_archiving.md) gesondert nachzuweisen.

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

Der feste Adapter liefert in diesen Entwicklungsdaten **keine tragfähige
Verbesserung für den vorgesehenen nächsten Methodenvergleich**. Das ist eine
inhaltliche Bewertung des vollständigen Befunds, kein nachträglich eingeführter
formaler Bestehensschwellenwert. Die beiden deutlich verbesserten alten
Problemfälle gleichen die neuen hohen Fehler nicht zu einer allgemein
günstigen Entwicklung aus. Insbesondere wird aus dem Ergebnis kein
Startauftrag für den zuvor erwogenen frischen 504-Worker-Vergleich abgeleitet.

Der vorhandene Befund stützt eine weitere methodische Klärung der
Zwischenpunktqualität und der Auswahl anhand von Trainingsverlust und
Komplexität. Er rechtfertigt keine unmittelbare Feinabstimmung des Faktors 1,5
auf denselben Ergebnissen, keine neue Frequenzgrenze und keine neue
Grammatikregel. Eine solche Intervention wäre ein eigener dokumentierter
Entwicklungsschritt. Jede spätere unabhängige Bestätigung benötigt neue,
vorher geplante Daten; historische Originalergebnisse und Protokolle bleiben
unverändert.
