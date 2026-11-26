# Hauptserie v2 bei zu breiter Vorhersagereferenz

Festgelegt am 25.11.2026 nach dem Replayabbruch von `main-study-manjaro-001`
und vor einer neuen wissenschaftlichen Ausführung. Diese Ergänzung betrifft
die Ausfallregel der Hauptserie in Phase 7. Für Suchprofil, Eingabematrix,
Seeds, Schätzer, Auswahl unter zulässigen Ausgaben und Endpunkte gilt der
[gebundene Hauptplan](main_study_plan.md). Das numerische Modell, die vier
Präzisionsstufen und die Grenze der zulässigen Intervallbreite stehen im
[Referenzplan](search_duration_prediction_plan.md).

## Entscheidung für einen Arm in einem Block

Alle vier vorgesehenen Worker eines vorbereiteten Arms erhalten ihr festes
Suchbudget. Ergibt das Replay für mindestens einen Kandidaten eines Workers
ausschließlich `indeterminate` mit Grund `reference_width_exceeds_bound`,
ist das gesamte Viererpaket numerisch nicht auswertbar. Dazu muss der Befund
aus dem gespeicherten Originalbaum und den gebundenen Trainingszeiten
reproduzierbar sein. Auf allen vier Präzisionsstufen muss die Breite der
einzige Grund sein. Beide tatsächlichen Vorhersagevektoren müssen endlich
sein und in den Intervallen der letzten Stufe liegen. Die zu breite Referenz
behält auch dann den Status `indeterminate`. Skalarverluste und Tabellenwerte
sind für alle Kandidaten zu prüfen, für gewichtete Arme auch Whitening und
quadratische Form. Alle betroffenen Kandidaten müssen identifizierbar sein.
Eine Fehlermeldung allein ist kein Nachweis. Jeder zusätzliche Widerspruch und jeder ungeklärte
Replayfehler stoppt die Ausführung nach dem gebundenen Fehlervertrag.

Die Regel gilt für jeden der vier Arme und jede Kandidatenposition. Alle
vorgesehenen Mitglieder werden nach Plan ausgeführt und mit ihren Kosten
erfasst. Auch ein erfolgreicher anderer Worker kann den Verlustvergleich
innerhalb dieses Arms nicht mehr entscheiden. Der Paketbericht kennzeichnet
den Grund und die betroffenen Mitglieder und gibt keine Siegerformel aus.
Der nächste geplante Arm oder Block kann danach starten. Die getrennte lesende
Verifikation muss denselben Status und dieselbe fehlende Auswahl aus den
Originalbelegen ableiten können. Ein technischer Vorlauf verlangt weiterhin
acht vollständig erfolgreiche Worker.

## Konsequenzen für den Vergleich

Das betroffene Paket zählt als eine geplante, fehlende Ausgabe. Kurve,
relativer L2-Fehler und davon abhängige Aussagen bleiben für diesen Arm
unverfügbar. Das Paket und seine Suchkosten bleiben in der Ausfall- und
Kostenbilanz. Für E64 und E4096 werden alle vier Verfügbarkeitskombinationen
berichtet. Fehlerdifferenzen beziehen sich auf die tatsächlich verfügbaren
Paare. Es gibt weder Ersatzseeds noch einen zweiten Versuch für einen
einzelnen ausgefallenen Arm.

Der auslösende Kandidat hatte den kleinsten gespeicherten Trainingsverlust
seines Workers. Ein Überspringen dieses Kandidaten oder eine Auswahl allein
unter den drei übrigen Workern könnte den Sieger ändern. Eine Lockerung der
Intervallgrenze würde die Aussage über die numerische Reproduzierbarkeit für
alle Kandidaten ändern. Die Paketregel hält die Breitenprüfung verbindlich
und macht die fehlende Ausgabe im Methodenvergleich sichtbar.

## Geltungsbereich und Wiederholung

Die Regel gilt ab einer eigenen neuen Lauf-ID und wird vor den Hauptsuchen
mit der Vorbereitung gebunden. Die Wiederholung beginnt mit einem frischen
technischen Vorlauf und verwendet die vorgesehenen Hauptdaten und Seeds.
Erneut erzeugte Blöcke zählen jeweils einmal. Eine Wiederholung derselben
Daten liefert keine zusätzliche unabhängige Stichprobe. Lauf 001 bleibt als
unter seiner ursprünglichen Regel abgebrochener Versuch mit eigenen Kosten
und Belegen dokumentiert. Aus seinem unvollständigen Signalabschnitt werden
keine Fall- oder Paketergebnisse in die neue Serie übernommen.
