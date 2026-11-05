# Zusatzbewertung Stufe 3: Vertrag der quantifizierten Zusatzterm-Diagnose

Stand: 05.11.2026. **Mehrfachdiagnosen und begrenzte adaptive Intervallunterteilung
am 05.11.2026 ausdrücklich beschlossen; Implementierung folgt.** Leitfadenphase 1, Bewertungsstufe 3 von 3. Stufe 2 wurde
mit [PR #70](https://github.com/craexxn/ringdown-sr/pull/70) übernommen.
Der Auftrag erlaubt den Beginn während der vollständigen CI von PR #71.
Arbeitsstand und Entscheidungen stehen im
[bestehenden Fortsetzungsstand](representation_implementation_status.md).

Grundlage sind `METHOD_CONTRACT.txt`, Abschnitt 8, `PROOF_NOTES.txt`,
Abschnitt 7, und Fälle T118–T126 aus `assessment-preparation-2026-11-05`.
Das Paket liefert Vorschläge und Referenzfälle. Entscheidungen der späteren
Implementierung müssen aus den verifizierten Originalformeln entstehen.

## Bereits bindende Abgrenzung

Gesucht ist eine nachgewiesene Zerlegung `f = g0 + r` auf dem ursprünglichen
Definitionsbereich im geschlossenen Trainingszeitfenster. `g0` gehört zur
[bestehenden Ringdown-Zielklasse](supplemental_structure.md). Die exakten
Binary64-Konstanten und symbolischen reellen Koeffizienten bleiben erhalten.
Jeder Originalknoten und seine Definitionsbedingungen werden vor Umformungen
geprüft. Nirgends definierte Formeln liefern keinen positiven Zerlegungsbeleg.

Die Komponente entsteht regelbasiert: keine Fits, optimale Projektion,
Wahrheitsparameter, Seeds oder Auswahl nach Kurvenfehlern. Originalauswahl,
Formel, Kurvenklassen, bisherige Familien-/Domain-/Fortsetzungsbefunde und
historische Parameterangaben werden durch die Restdiagnose nicht ersetzt.
Ein Rest ungleich null beweist keine generelle Nichtzugehörigkeit zur Familie.
Neue Parametermatches bleiben `not_assessed`; eine neue Schwelle für
Vernachlässigbarkeit oder ein neuer Erfolgszähler sind nicht beauftragt.

## Beschluss: alle regelbasierten Grundterme getrennt diagnostizieren

Beschlossen ist folgende erste Fassung:

1. Die validierte Analysekopie mit den beschlossenen exakten Regeln
   normalisieren und begrenzt in Summanden entwickeln.
2. Erkennbare affine Exponential-/Sinus-/Kosinusanteile nach nachweislich
   gleicher Dämpfung und Frequenz gruppieren. Phasen und konstante Exponenten
   gehen exakt in die Amplitudenkoeffizienten ein. Exakte Auslöschung wird
   berücksichtigt; benachbarte Binary64-Frequenzen werden nicht gleichgesetzt.
3. Jede nach diesem Regelwerk ermittelte Gruppe mit bewiesener positiver
   Dämpfung/Frequenz und nicht verschwindender Gesamtamplitude separat als
   Grundterm diagnostizieren. Für jeden Grundterm bilden alle übrigen Anteile
   den jeweiligen Rest. Es gibt keine bevorzugte Gruppe oder neue Rangfolge.
4. Exakt gleiche Moden werden vor der Diagnose zusammengefasst. Nicht erkannte
   Anteile bleiben im Rest; nicht nachgewiesene Koeffizienten bleiben ungeklärt.
   Alle Kandidaten sind durch das Regelwerk bestimmt, nicht durch Signalwahrheit.
   Eine Vollständigkeit unter beliebigen mathematischen Zerlegungen wird nicht
   behauptet. Gibt es keinen belegten Grundterm, bleibt der Befund ungeklärt.

Die zunächst vorgeschlagene Beschränkung auf genau eine Gruppe wurde ausdrücklich
nicht gewählt: Mehrere mögliche Grundterme sollen getrennt diagnostiziert werden.
Der Umfang bleibt durch höchstens 256 normalisierte Summanden beschränkt.

## Beschluss: adaptive Schranken und getrennte Normierung

Eine zertifizierte obere Schranke `sup |r| <= B` entsteht durch gerichtete
Intervallarithmetik. Sie ist nicht zwingend das kleinstmögliche Supremum.
Die Variante ohne Intervallunterteilung wurde nicht gewählt. Beschlossen ist:

- Zunächst das ganze bereits gebundene Intervall prüfen.
- Kann dort keine endliche Schranke bewiesen werden, exakt in der Mitte
  halbieren und deterministisch von links nach rechts fortfahren.
- Höchstens Tiefe 8 und 256 Teilintervalle je Grundterm. Jede erfolgreiche
  Einschließung und die vollständige Intervallabdeckung werden protokolliert.
- Die Schranke des gesamten Intervalls ist das Maximum der bewiesenen
  Teilintervallschranken. Eine offene Teilregion verhindert den globalen Beleg.
- Eine bereits bewiesene endliche Schranke wird nicht weiter verkleinert.
  Es gibt keine Optimierung auf einen gewünschten Restbetrag.
- Gemeinsam höchstens 10.000 Analyseschritte für alle Grundterme einer
  Originalformel einschließlich Zerlegung und Normierung. Bei Erschöpfung
  bleiben noch offene Befunde ungeklärt; abgeschlossene Einzelbelege bleiben
  ausdrücklich als solche sichtbar. Keine neuen Budgets pro Komponente.

Die bestätigten Strukturgrenzen beschränken auch die separate Restanalyse: höchstens 20 Originalknoten, 4.096 Knoten je Analyseterm,
256 Summanden, 4.096 Nullstellenkandidaten, 10.000 Analyseschritte, 16.384 Bit je
rationalem Zähler/Nenner und Präzision 128/256/512/1.024 Bit. Die Schritte zählen
kumulativ innerhalb dieser Analyse; Wiederholungen erhalten kein neues Budget.
Ihre Übernahme für Stufe 3 ist mit dem Schrankenweg bestätigt.

Ein positiver Befund setzt konservativ die vollständige Originaldomainprüfung
mit nachgewiesen nichtleerem, dichtem Originalbereich voraus. Eine Schranke
bezieht sich ausdrücklich auf diesen Originalbereich. Eine Aussage auch an
ausgeschlossenen Stellen benötigt zusätzlich die bewiesene stetige Fortsetzung
und wird als solche bezeichnet. Ungeklärte Domain, Nennerintervalle mit null,
Ressourcenende oder nicht endliche Einschließungen werden nicht als Nullrest
oder als mathematische Unbeschränktheit ausgegeben.

Für jedes der beiden gespeicherten Referenzraster separat:

- relativer RMS-Beitrag höchstens `B / sqrt(sum(y_i^2)/N)`;
- relativer Maximumbeitrag höchstens `B / max(abs(y_i))`.

Die Normen beziehen sich auf die exakten Werte der gebundenen Referenzbits.
Positive Skalen und gerichtete Division müssen belegt sein. Fehlt eine gültige
positive Skala, bleibt die betreffende relative Angabe nicht bewertbar;
eine unabhängig bewiesene absolute Schranke bleibt davon unterscheidbar.
Die Referenz beeinflusst nur die Normierung, niemals die Auswahl von `g0`.
Die Schranke betrifft `Original minus Grundterm`, nicht den Fehler des
Grundterms gegenüber dem bekannten Signal. Insbesondere ist `B/max|y|`
keine RMS-Schranke. Eine praktisch kleine Schranke erzeugt keine neue
binäre Erfolgsaussage.

## Vorgesehene Integration und Prüfung

Ein eigener begrenzter Diagnosekern ergänzt beide vorhandenen Exportwege:
verifizierte historische Originalauswahlen und zukünftige Schema-3-Läufe.
Versionsfassung, Regelwerk, Ressourcen, Intervall, Quellen, exakte Zerlegung,
Schrankenbeleg und Referenzbindung werden vor Anwendung festgeschrieben.
Frühere Snapshots werden nur ausdrücklich retrospektiv ergänzt. Gespeicherte
Originalauswahl, Herkunftsprüfung, Veröffentlichung und Widerruf bleiben gültig.
Neue native Suchläufe sind dafür nicht vorgesehen; bestehende kleine technische
Kontrollen können den zusätzlichen Export prüfen.

Unabhängig zu begründende Gegenprüfungen:

- `g + epsilon`, `(exp(-t)+epsilon)*sin(2*t)` und exakt verschwindender Rest;
- gleiche Moden mit Addition/Auslöschung, verschiedene Moden und fast gleiche
  Frequenzen ohne toleranzbasierte Zusammenfassung;
- `epsilon*exp(1000*t)` als Gegenfall zum vermeintlich kleinen Koeffizienten;
- `epsilon/(t-c)`, einschließlich beider Intervallränder und zwischen Samples;
- ungeklärte bzw. leere Originaldomain trotz endlicher Float64-Vorhersagen;
- hebbare Lücken mit ausdrücklich getrenntem Fortsetzungsbefund;
- getrennte RMS-/Maximumskalen, Nullreferenz, fehlende Referenz und Grenzwerte;
- Ressourcenende, widersprüchliche Quellen sowie späte Änderungen an allen
  neu veröffentlichten Diagnosen und deren Widerruf.

Diese Liste ist ein Prüfplan. Sie behauptet keine bereits implementierten oder
bestandenen Stufe-3-Tests. Ein eigener PR wird nach Umsetzung und vollständiger
technischer Prüfung zum Review übergeben; kein eigenständiger Merge.
