# Zusatzbewertung Stufe 2: Intervall- und Beweisvertrag

Stand: 05.11.2026. **Intervall, Beweisweg und Ressourcen am 05.11.2026
ausdrücklich beschlossen. Implementiert in
[PR #70](https://github.com/craexxn/ringdown-sr/pull/70); Review und Übernahme offen.**
Leitfadenphase 1, Bewertungsstufe 2 von 3. Die Umsetzung folgt der bestätigten
Übernahme von [PR #69](https://github.com/craexxn/ringdown-sr/pull/69).
Entscheidungen und tatsächlicher Arbeitsstand stehen im
[bestehenden Arbeitsdokument](representation_implementation_status.md).

Die Vorbereitung `assessment-preparation-2026-11-05`, insbesondere
`METHOD_CONTRACT.txt` Abschnitte 3–7, `PROOF_NOTES.txt` und die 36 synthetischen
Strukturbeispiele, dient als Referenz. Entscheidungen müssen aus den
verifizierten Originalbäumen folgen. Dokumentationstabellen und übermittelte
Einzelbewertungen sind keine Eingaben für den Erkenner.

## Ziel und unveränderte Datenrollen

Geprüft wird die bereits vorgegebene reelle Familie

\[
g(t)=\exp(-\gamma t)\,[a\cos(\omega t)+b\sin(\omega t)],
\qquad \gamma>0,\quad \omega>0,\quad a^2+b^2>0.
\]

Originalkonstanten sind die exakten rationalen Werte ihrer gespeicherten
Binary64-Bits. Abgeleitete Ausdrücke wie `sin(c)`, `cos(c)` und `exp(c)`
bleiben symbolisch exakt; Zahlenintervalle sind getrennte Nachweise.
Eine gespeicherte Float64-Näherung von pi wird niemals zu exaktem pi erklärt.
Neue Familiennachweise verwenden weder Wahrheit noch Seeds oder Kurvennoten.
Historische Erkenner, Originalauswahl, Kurvenwerte und Parameter-/Aliasangaben
bleiben erhalten; neue Parametermatches bleiben `not_assessed`.

## Beschluss: geschlossenes Prüfintervall

Beschlossen ist `[min(training_time_s), max(training_time_s)]` in Sekunden,
beide Enden eingeschlossen, mit exakt gespeicherten rationalen Endpunkten.
Für die vier historischen Serien ist dies `[0,127/4096]` Sekunden.
Zukünftige Läufe verwenden ihre tatsächlich gespeicherten und verifizierten
Trainingsendpunkte; die Zeitkoordinate muss Sekunden bedeuten.
Das Intervall muss positive Länge besitzen.

Damit wird keine Extrapolation bis zum nominalen Aufnahmeende `N/fs`
behauptet. Die Alternative eines vollen Aufnahmefensters benötigt einen
eigenen expliziten Intervallvertrag. Hebbare Lücken an den eingeschlossenen
Rändern benötigen den jeweils einseitigen endlichen Grenzwert.

## Beschluss: begrenzter Beweisweg und Ressourcen

Am 05.11.2026 wurden folgende begründete Umformungen auf einer Analysekopie
und die nachstehenden Grenzen ausdrücklich bestätigt:

- Exakte zeitunabhängige Konstanten und affine Argumente erkennen.
- Exponentialprodukte und -quotienten zusammenfassen; konstante Exponenten
  in die Amplitudenkoeffizienten übernehmen.
- Sinus-/Kosinus-Additionsregeln sowie gerade/ungerade Symmetrie verwenden.
- Nur nachweislich gleiche Dämpfungen und Frequenzen zusammenfassen;
  exakte Amplitudenauslöschung gesondert prüfen.
- Originale Definitionsbedingungen vor jeder Kürzung rekursiv erfassen.
  Konstante, affine, exponentielle und affine trigonometrische Nenner sowie
  Produkt-/Quotientenbedingungen behandeln. Nullstellen und ihre Lage im
  Intervall müssen bewiesen sein; ein Intervall, das null enthält, genügt nicht.
- Vorzeichen und Nichtnullwerte algebraisch oder durch gerichtete
  Mehrpräzisionsintervalle beweisen. Ein Intervall, das null enthält,
  beweist weder Gleichheit noch Ungleichheit zu null.

Jeder angewandte Beweisschritt hält Regel, Originalknotenpfad,
Vorher-/Nachherausdruck, Voraussetzungen und Definitionsbedingungen fest.
Nicht unterstützte Umformungen bleiben ungeklärt. Allgemeines CAS-Simplifizieren,
numerische Stichproben, Fits und ein ODE-Beweisverfahren ersetzen keinen Nachweis.

Beschlossene feste Grenzen je Originalformel:

| Größe | Grenze |
| --- | ---: |
| Originalbaum | unverändert höchstens 20 Knoten |
| Knoten je Analyseterm | 4.096 |
| Normalisierte Summanden | 256 |
| Nullstellenkandidaten insgesamt | 4.096 |
| Analyseschritte insgesamt | 10.000 |
| Bitlänge je rationalem Zähler/Nenner | 16.384 |
| Präzisionsstaffel für zertifizierte Intervalle | 128, 256, 512, 1.024 Bit |

Die Grenzen beschränken den Beweiser, nicht die mathematische Zielklasse.
Ihr Erreichen liefert `unresolved` mit Grund und vorhandenen Teilbelegen.
Es bedeutet weder Nichtzugehörigkeit noch eine zusätzliche Suchtoleranz.
Die Ressourcenfassung wird vor Anwendung versioniert. Größenprüfungen müssen
Expansionen rechtzeitig begrenzen; eine Prüfung erst nach unbeschränktem Aufbau
genügt nicht. Technische Exportabbrüche sperren weiter das gesamte Paket.

## Getrennte Befunde

Das vorbereitete Statusmodell unterscheidet:

- `algebraic_identity`: Identität auf dem nachweislich nichtleeren
  Originalbereich, bewiesene Nichtzugehörigkeit oder ungeklärt.
- `domain`: überall definiert, ausschließlich hebbare Lücken, nichthebbare
  Singularitäten, gemischte Fälle, nirgends definiert oder ungeklärt.
- `original_family`: Mitglied nur bei bewiesener Identität, erfüllten
  Parameterbedingungen und überall definiertem Original auf dem Intervall.
- `continuous_extension`: gesonderter Nachweis einer passenden stetigen
  Fortsetzung; kein Ersatz des Originalbaums und keine Reparatur seiner Domain.

Ein vollständig erfasster endlicher Ausschlussbereich und eine bewiesene stetige
Normalform können hebbare Lücken belegen. Unvollständige Ausschlussnachweise
erlauben keine pauschale Freigabe. Eine nirgends definierte Formel liefert
keinen positiven Identitätsbeweis und keine eindeutige Fortsetzung.
Nichtzugehörigkeit erfordert einen Gegenbeweis; eine nicht erkannte Form
bleibt ungeklärt. Aufwendige Mehrfrequenz- oder Chirpgegenbeweise dürfen
in dieser begrenzten Fassung ungeklärt bleiben.

## Versionen und Anbindung

Der neue Kern ist vom historischen Erkenner und den gerundeten
Vorhersagereplays getrennt. Er verwendet die Fassung
`ringdown-sr-structure-proof-1` und den
[maschinenlesbaren Vertrag](../data/structure_assessment_v1.json).
Die Ausgabefassungen sind `ringdown-sr-supplemental-assessment-2` für Archive
und `ringdown-sr-future-assessment-2` für Schema-3-Läufe; die jeweiligen
Einzelbewertungsschemas tragen ebenfalls Version 2. Fassung-1-Verträge und
veröffentlichte Ergebnisse bleiben erhalten. Rationalzahlen im neuen
Ausdrucksschema speichern kanonische Hexzeichenketten für Zähler und Nenner.

Die vorhandenen Exportbefehle aus dem
[Bewertungsvertrag](supplemental_assessment.md) erzeugen nun Fassung 2.
Sie bewerten weiterhin ausschließlich Originalauswahlen. Das Zeitintervall
wird aus den verifizierten Originaldaten abgeleitet und gemeinsam mit
Einzelnoten, getrennten Strukturbefunden und Nachweisen ausgegeben.
Bei neuen Läufen werden Vertrag, Ressourcen, Quellen und Intervall bereits
vor dem ersten Fit mit dem Snapshot gespeichert. Ein späterer Export eines
vollständigen Fassung-1-Snapshots bleibt möglich und ist ausdrücklich
`retrospective_upgrade_of_stage1_snapshot`, keine rückwirkende Vorabfestlegung.
Fehlende oder widersprüchliche Vorbereitungs-/Workerquellen bleiben gesperrt.
Die [lesende Anwendung auf alle 78 historischen Originalauswahlen](supplemental_structure_results_001.md)
ist dokumentiert; Originalkennzahlen und Kurvenklassen blieben unverändert.

## Umsetzung und Prüfung

Die neue Bewertungsfassung wird gesondert versioniert und an Originalquellen,
Intervall, Regeln, Ressourcen und Software gebunden. Sie ergänzt sowohl den
verifizierten historischen Import als auch zukünftige Schema-3-Auswertungen.
Bestehende Bewertungsfassungen und ihre Originalnachweise bleiben unterscheidbar.

Prüfungen umfassen explizit hergeleitete Identitäten, Randlücken,
verschachtelte Quotienten, undefinierte gekürzte Teilbäume, Nullamplituden,
wachsende/ungedämpfte Formen, benachbarte Binary64-Frequenzen,
symbolische Konstanten, unvollständige Domainnachweise und Ressourcenabbrüche.
Die vorbereiteten Fälle ergänzen unabhängig hergeleitete Gegenfälle.
Herkunft, Originalauswahl, Veröffentlichung und Widerruf bleiben geprüft.
Ein späterer eigener PR erhält die vollständige technische CI und wird zum
Review übergeben. Keine wissenschaftlichen Suchen oder eigenständigen Merges.

**Nächste ausstehende Stufe nach Übernahme dieser Umsetzung:** Stufe 3,
quantifizierte Zusatzterm-Diagnose. Restterme bleiben bis dahin `not_assessed`;
es wird keine Schwelle für Vernachlässigbarkeit eingeführt.
