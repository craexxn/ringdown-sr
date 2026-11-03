# Gebundene Verifikationsergänzung zum Suchbudgetvergleich

Angenommen am 03.11.2026 auf Grundlage des
[Audits von duration-manjaro-001](search_duration_results_manjaro_001.md)
und des anschließenden Auftrags zur Fortsetzung. Dieser Text wird vor der
Implementierung separat committed und durch Commit und SHA-256 gebunden.
Der [ursprüngliche Plan](search_duration_plan.md), frühere Pläne und Archive
bleiben unverändert. Die Ergänzung betrifft ausschließlich den Suchbudgetpfad
im neuen Format 2; ältere Pfade behalten ihre bisherigen Standards.

## 1. Problem und unveränderte Suche

Feste native Replays der acht CSV-Bäume aus Zelle 3 reproduzieren die
gespeicherten Verluste bitgenau. Bei Komplexität 11/13 unterscheiden sich
Python-/Julia-Vorhersagen höchstens um `1,11e-16`. Ein rein relativer Vergleich
unabhängiger MSE-Werte ist bei nahezu verschwindenden Residuen schlecht
konditioniert. Zusätzlich deckt der bisherige Erkenner `sin(...) / exp(...)`
nicht ab.

Zielfunktion, Originalbaum, Kandidatenreihenfolge, gespeicherter nativer
Trainingsverlust und Originalauswahl bleiben unverändert. Kein Nachfit und
keine diagnostische Ersatzwahl. Kurven-/Parametergrenzen, Grammatiken,
Optionen, Budgets, Datenrollen und Entscheidungsregeln des ursprünglichen
Plans bleiben bestehen. Die erweiterte diagnostische Abdeckung wird versioniert.

## 2. Getrennte Verlustprüfung ohne feste absolute Fehlerschwelle

Die neue Regel gilt ausdrücklich für gewöhnliche MSE, nicht für
Kovarianzverluste. Baumrundreise, endliche Vektoren und der bisherige
amplitudenbezogene Vorhersagevergleich bleiben erhalten (`rtol=1e-12`,
normalisierte `atol=1e-14`, kein Einheitsgrößenboden). Gespeicherter nativer
Verlust, nativer Replayverlust und Tabellenverlust werden weiterhin mit
`rtol=1e-10, atol=0` miteinander verglichen.

Zusätzlich wird jeder native Verlust gegen die nativen Residuen, die
Python-MSE gegen ihre eigenen Residuen geprüft. Beide Residuenvektoren werden
aus denselben Beobachtungen und der jeweiligen Vorhersage mit Float64-
Subtraktion gebildet. Gespeicherte native Residuen müssen weiterhin bitgenau
dazu passen. Für einen solchen Vektor r wird exakt rational berechnet:

```text
Q(r) = sum(Fraction(r_i)^2) / n
u = 2^-53; k = n+2; gamma_k = k*u/(1-k*u)
abs(Fraction(L)-Q(r)) <= gamma_k*Q(r)
```

Die Schranke deckt eine Rundung pro Quadrat, sequenzielle Summation und
Division konservativ ab; paarweise Summation oder FMA benötigen nicht mehr
Operationen. Vergleiche erfolgen rational, ohne gerundete Entscheidungsschwelle.
Geprüfter Gültigkeitsbereich: endliche Float64-Werte, positive Vektorlänge,
`k*u < 1`, keine nichtnormalen nichtnull Quadrate bzw. MSE und kein Überlauf.
Nicht darstellbare Fälle führen zum Abbruch, nicht zu einer absoluten
Toleranz. Exakt verschwindende Residuen verlangen exakt Verlust null.
Dies begründet die Reduktion, nicht die Genauigkeit transzendenter Funktionen;
deren Vorhersagevergleich bleibt eine separate notwendige Bedingung.

Für die bereits gerundeten Residuen r_J und r_P setze exakt
`e_i=Fraction(r_P_i)-Fraction(r_J_i)`. Dann muss zusätzlich gelten:

```text
D = sum(2*abs(r_J_i)*abs(e_i) + e_i^2) / n
abs(L_P-L_J) <= D + gamma_k*(Q(r_J)+Q(r_P))
```

Tatsächliche Residuenbits berücksichtigen Subtraktionsrundungen; die Gamma-
Terme decken Reduktionsrundungen ab. Alle eigenen Verlustprüfungen und der
Vorhersagevergleich müssen zusätzlich bestehen: eine große Differenz darf
keine falsche Einzel-MSE verdecken. Der Nachweis samt Tabellenverlust wird
pro Kandidat gespeichert und im Elternprozess erneut aus Originalbaum,
Beobachtungen und nativen Vorhersagen berechnet. Fehlende/geänderte Nachweise
führen zum Abbruch. Der alte Prüfungspfad bleibt außerhalb dieses Workers
Standard. Verworfen: pauschal größeres rtol/atol, umgeschriebene Verluste,
Ersatzwahl oder Freigabe allein wegen kleiner MSE.

## 3. Begrenzte Erkennung äquivalenter Formeln

Erweitert wird das Produktmuster um genau einen Exponentialfaktor im Zähler
oder Nenner, genau einen sin- oder cos-Faktor im Zähler und syntaktisch
zeitfreie rationale Skalare in Produkten/Quotienten. Exponentialargument:
affin, konstanter Anteil null; trigonometrisches Argument: affin.
`1/exp(b*t)` ergibt Rate -b; `sin(c*t+d)=cos(c*t+d-pi/2)` ergibt getrennte
exakte rationale Radiant- und Pi-Anteile. Gespeichertes float(pi) wird nicht
zu mathematischem Pi erklärt. Phase/Aliasreduktion verwenden die bestehenden
begrenzten rationalen Pi-Einschließungen; unaufgelöste Konversion bleibt
unbestimmt.

Keine allgemeine Vereinfachung. Äußere Summen, zusätzliche Exponential-/
Trigonometriefaktoren, trigonometrische Nenner, zeitabhängige Skalare,
Nullnenner, nichtaffine Argumente und Exponentialoffsets bleiben ausgeschlossen.
Alle Knoten werden vorab validiert, auch in Nullfaktoren. Originalbaum und
Float64-Auswertung bleiben erhalten. Mathematische Erkennung allein genügt
nicht: rohe und Aliasparameter müssen weiter gegen den Originalbaum bestehen.
Wachstums-, Nullamplituden- und Aliasgrenzen bleiben wirksam; physikalische
Identifikation bleibt `not_assessed`. Nur der neue Diagnosepfad aktiviert
diese Erweiterung.

## 4. Nachweise vor wissenschaftlicher Ausführung

- Unabhängige normale, exakte Null-, Nähe-null-, falsch skalierte,
  manipulierte und nicht darstellbare Verlustfälle. Falsche gespeicherte
  Verluste dürfen nicht wegen guter Python-Vorhersagen passieren. Fehlende
  und manipulierte Nachweise auch im Elternprozess prüfen.
- Exakte Koeffizienten-/Phasenreferenzen für Sinus, Kosinus, Quotienten,
  Vorzeichen, Aliasorientierung und ausgeschlossene Gegenfälle. Formal
  erkannte, numerisch abweichende Umformungen bleiben ohne positiven Marker.
- Die zwei gesicherten CSV-Bäume als ausdrücklich nachträgliche
  Regressionsfälle: feste native Auswertung, keine Suche/Optimierung. Herkunft
  und fehlender ursprünglicher Baumexport bleiben dokumentiert.
- Vollständige Python-/Julia-Prüfungen und technische Integration beider
  Grammatiken bei zwei/drei Iterationen am separaten Achtpunktfall. Wiederholte
  Kontrolle und Originalauswahl unverändert. Vollständige CI vor Merge;
  kein eigenständiger Merge und keine wissenschaftliche Cloud-Suche.

## 5. Späterer neuer Manjaro-Lauf

Vorbereitet wird duration-manjaro-002 nach Merge und bestandenen technischen
Prüfungen: alle 20 Prozesse frisch, 200/2000 Iterationen, beide Grammatiken,
dieselbe feste Reihenfolge und Seeds 20261103 bis 20261107. Kein Warmstart,
keine Übernahme alter Zellen, keine selektive Wiederholung und keine
Ersatzseeds. Bereits gesehene Ergebnisse machen diese Seeds nicht mehr zu
ungesehenen Kontrollen; es bleibt eine adaptive Entwicklungsprüfung am
bekannten Signal. Dieselbe Verifikationsversion gilt für alle Zellen.
600 Sekunden je Worker und 7200 Sekunden insgesamt einschließlich Elternarbeit
und Abschluss bleiben verbindlich.

Die alte Serie bleibt unvollständig. Neue Aggregate erst nach vollständiger
Verifikation aller 20 neuen Zellen. Keine automatische weitere Budgetstufe,
kein Hauptversuch und keine allgemeine Leistungsvalidierung. Wissenschaftliche
Ausführung auf Manjaro; dieser Implementierungsauftrag startet sie hier nicht.
