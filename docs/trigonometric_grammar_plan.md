# Methodenplan: Trigonometrische Verschachtelung in der freien Suche

Angenommen am 03.11.2026 nach der ausdrücklichen Zustimmung zum begrenzten
Vergleich und zur anschließenden Ausführung auf Manjaro. Dieser Plan legt die
konkrete Reihenfolge und den technischen Nachweis des angenommenen Vorschlags
fest. Vor Implementierung wird er durch Commit und SHA-256 gebunden.
Implementierung, technische Prüfung und wissenschaftliche Ausführung bleiben
getrennt. Hier wird die einmalige Manjaro-Serie vorbereitet, keine
wissenschaftliche Suchzelle in der Cloud ausgeführt. Kein eigenständiger Merge.

## 1. Begründung, Frage und Vorwissen

Grundlage ist die [Literaturabwägung](free_form_method_assessment.md) am Commit
`114bb24dd983c0316c89379bc9477bed5835655a` und der abgeschlossene
[Beobachtungsbefund](search_trajectory_results_manjaro_002.md).
Die früheren numerischen Audits sind übernommene Nachweise, keine in diesem
Arbeitsschritt wiederholten Prüfungen. Gute feste Fits unter 100/2 belegen
keine freie Strukturentdeckung; keine erfolgreiche Originalauswahl liegt vor.
Die Piloten identifizieren verschachtelte Trigonometrie nicht als Ursache.
Petersen et al. berichten sogar schlechtere GP-Ergebnisse unter einem
Regelbündel ([Primärquelle, Anhang C](https://arxiv.org/html/1912.04871v4)).
Die einzelne Regel wird wegen ihres begrenzten, erklärbaren Eingriffs geprüft,
nicht wegen einer belegten Erfolgsprognose. Solverwechsel, Backendwechsel,
weitere Budgets und Beobachter bleiben zurückgestellt.

Hypothese: Bei sonst gleichem 100/2-Häufigkeitsprofil erhöht das Verbot
trigonometrischer Nachfahren unter `sin/cos` die Zahl erfolgreicher
Originalauswahlen gegenüber einer frischen unbeschränkten Kontrolle.
Das betrifft den gesamten Suchprozess, keinen isolierten Mutationsmechanismus.

Frei bleibt die Kombination allgemeiner Operatoren und Konstanten. Der
zusätzliche Syntaxprior schließt beispielsweise `sin(a*t+sin(b*t))` aus,
auch bei arithmetischen Knoten zwischen den trigonometrischen Operatoren.
Er erzwingt weder Produkt, Exponentialhülle, Dämpfung, konstante Frequenz noch
eine bestimmte Konstantenzahl. Phasenmodulation wird eingeschränkt; algebraische
Äquivalenzklassen werden nicht vollständig ausgeschlossen. Ein bekannter
Ringdown-Baum bleibt ausschließlich privilegierte Referenz und Diagnose.

Der Versuch ist adaptive Entwicklung an einem bekannten Signal und drei
bekannten Seeds. Keine unabhängige Validierung, Leistungsstudie oder
physikalische Identifikation. Für die späteren Kovarianzarme des Exposés muss
ein vorab gewähltes Verfahren mit gleichen Operatoren, Regeln, Auswahl und
fairen Rechenzeitbudgets gelten. Dieser Vorversuch gibt Hauptversuche nicht frei.

## 2. Daten und genau eine Intervention

Die unveränderten 128 Trainingswerte und 889 inneren Achtelpunkte stammen aus
dem bisherigen Originalarchiv `representation-manjaro-001.tar.gz`, SHA-256
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Der bestehende Leser prüft Archividentität und Arraybits. Archivcode wird nicht
ausgeführt. Training: `t_j=j/4096 s`, `j=0,...,127`; bekanntes Signal `A=1`,
`f=250 Hz`, `tau=0,008 s`, `phi=0`, Fenster `128/4096 s`.
Freie Worker erhalten ausschließlich Trainingszeiten und Beobachtungen,
`X_units=["s"]`, `y_units="1"`, `covariance=None`. Wahrheitsparameter,
Diagnosepunkte und Referenzbäume gelangen weder in Initialisierung noch Auswahl.

| Arm | Kennung | PySR `nested_constraints` |
| --- | --- | --- |
| K: Kontrolle | `unrestricted` | `None` |
| A: Intervention | `no_nested_trig` | `{"sin": {"sin": 0, "cos": 0}, "cos": {"sin": 0, "cos": 0}}` |

Alle vier geordneten Paare sind erfasst, einschließlich entfernter Nachfahren.
`exp`, Division, Phasen, Produkte und freie Konstanten bleiben möglich.
Die tatsächliche Bibliotheksprüfung und ihre Wirkung auf erzeugte Kandidaten
werden geprüft. Allgemeine Adapterdefaults und alte Kontrollpfade bleiben erhalten.

Beide Arme: `+,-,*,/,exp,sin,cos`, Einheitskomplexitäten, maxsize 20,
effektives maxdepth 20, Parsimony 0, beide Häufigkeitsschalter `True`,
100 lokale Optimiereriterationen, zwei zusätzliche Neustarts, unveränderte
Toleranzen und Auswertungsgrenzen. Bei einer Konstanten bleibt Newton, bei
mehreren BFGS mit Backtracking; numerische Differentiation und bisherige
Start-/Restartbehandlung. Float64, seriell/deterministisch, ursprüngliche
Sekunden, `dimensionless_constants_only=False`, `warm_start=False`,
`guesses=None`; keine Templates, Zielskalierung oder Tracing-Plugins.
Ein gemeinsamer überprüfter Verlustwrapper darf nur die Profile verifizieren
und delegiert die Numerik unverändert an den bisherigen Verlustpfad.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1;
Haswell und Threadlimit 1 für OpenBLAS/OMP/MKL/NumExpr gelten kontrollspezifisch.
Keine Änderung von Pins, Proxy oder TLS. Wissenschaftliche Ausführung auf
Manjaro am sauberen, technisch geprüften und dokumentierten Commit.

## 3. Umfang, Reihenfolge und Aufwand

| Zelle | Seed | Arm |
| --- | ---: | --- |
| 1 | 20261020 | `unrestricted` |
| 2 | 20261020 | `no_nested_trig` |
| 3 | 20261021 | `no_nested_trig` |
| 4 | 20261021 | `unrestricted` |
| 5 | 20261022 | `unrestricted` |
| 6 | 20261022 | `no_nested_trig` |

Sechs frische Prozesse; historische Läufe ersetzen keine Kontrolle. Die
Paarreihenfolge wechselt mit unvermeidlicher 2:1-Asymmetrie. Gemeinsame Seeds
erzwingen keine gemeinsamen Zufallspräfixe, Mutationen oder Neustartvektoren.
Der Backendseed wird absolut gegen die bestehende PySR-Abbildung geprüft.

Je Zelle 200 Suchiterationen, zwei Populationen zu 32 Individuen, 50 Zyklen,
600 Sekunden Workerlimit. Gesamtlimit **60 Minuten** einschließlich
serienbezogener Vorprüfungen, Starts und Abschlussverifikation.
Gleiche nominale Grenzen bedeuten keine gleichen verbrauchten Rechenkosten.
Abgelehnte Mutationen, Optimierung, JIT und Export können den Aufwand verändern.
Gemessene Zeiten und bestehende Callback-/Evaluationszähler getrennt berichten;
keine neue Suchhistorieninstrumentierung. Die Implementierungs- und CI-Arbeit
gehört nicht in das 60-Minuten-Limit der wissenschaftlichen Serie.

Nach sechs Zellen endet der Versuch unabhängig vom Ergebnis. Fehler,
Ressourcenabbruch, SIGINT oder SIGTERM sichern Teilstände und stoppen die
eigenen Workerprozessgruppen. Keine automatischen Wiederholungen, Ersatzseeds,
Budgeterhöhungen, Nachfits oder zusätzlichen Arme. Eine gültige schlechte
Formel ist ein Ergebnis, kein technischer Fehler.

## 4. Auswahl, Verifikation und Endpunkte

Alle Pareto-Kandidaten mit ursprünglicher Reihenfolge und Auswahlindex sichern.
Auswahl: kleinste gewöhnliche Trainings-MSE, dann kleinste Komplexität,
bei weiterem Gleichstand erster Originalindex. Keine Ersatzwahl. Vorhersagen,
Residuen und MSE des unveränderten Baums nachrechnen; Widersprüche stoppen.
Für A zusätzlich alle exportierten Bäume auf die konkrete Syntaxregel prüfen.

Primärer deskriptiver Endpunkt: Zahl `C_K` beziehungsweise `C_A` der drei
Originalauswahlen je Arm, die auf Training **und** Achtelraster jeweils
`relative_rms <= 0.001` und `relative_max <= 0.01` erfüllen.
Struktur, Abklingen, Parameter und Replays getrennt berichten. Parametergrenzen
bleiben Frequenz `1e-3`, Abklingzeit `1e-2`, Amplitude und komplexe Amplitude
`1e-2`, einschließlich bestehender Alias-/Verfügbarkeitsgates. `not_supported`
ist kein algebraischer Unmöglichkeitsbeweis. `physical_identification` bleibt
`not_assessed`; der Blindfleck bei `8*fs` bleibt bestehen.

Je Originalauswahl Fehler beider Raster, Originalbaum, Komplexität, Status und
Aufwand zeigen. Je Arm Minima/Mediane/Maxima mit endlichen Nennern; je Seed
Differenzen A minus K mit beiden Ausgangswerten, Erfolgswechsel und getrennten
Parameterstatus. Nicht verfügbare Größen bleiben `null` mit Grund.
Gute ungewählte Kandidaten separat ausweisen, niemals als Auswahlerfolg zählen.

Aggregate und Paardifferenzen erst nach sechs vollständig geprüften Zellen
und bestandener Abschlussverifikation veröffentlichen. Sonst bleiben geprüfte
Einzelresultate erhalten, Vergleich und positive Gesamtaussage gesperrt.
Keine p-Werte, Erfolgswahrscheinlichkeiten oder allgemeinen Überlegenheitsbehauptungen.

## 5. Technischer Nachweis und Bindungen

Eigener isolierter Pfad mit manifestierten Quellen, Pins, Plan und Eingabebits.
Vorbereitung und Suchworker sind getrennte frische Prozesse. Keine Weitergabe
von Referenzbäumen, Vorprüfungszuständen oder RNG-Zuständen an freie Suchen.

Vor wissenschaftlicher Ausführung erforderlich:

1. Sechs native Optionsobjekte ohne Suche/Fit absolut prüfen, einschließlich
   aller Felder, Plugins, Seeds, Optimierertoleranzen und der tatsächlichen
   Verschachtelungsstruktur. Nur einzeln verifizierte Regel-, Seed- und
   Ausgabepfaddifferenzen beim armübergreifenden Vergleich zulassen.
2. Zulässige Bäume sowie alle vier verbotenen direkten und entfernten
   trigonometrischen Paare gegen den echten Backendprüfer testen. Kontrolle
   akzeptiert diese Syntax; A lehnt sie ab. Feste 250-/4346-/33018-Hz-Referenzen,
   Einheitengegenfälle und numerische Verlust-/Exportreplays unter beiden
   Profilen ohne Optimierung prüfen. Falsche Seeds/Profile müssen scheitern.
3. Kleine echte K–A–K-Worker mit zwei Suchiterationen am gesonderten
   Achtpunkt-Signal `y=1+t`; die beiden K-Originalfronten müssen übereinstimmen.
   Keine wissenschaftliche Zelle als Integrationstest. Manipulations-, Abbruch-
   und Berichtssperrentests sowie vollständige technische CI vor Übergabe.

Quellen und konsumierte Dateien vor/nach Verbrauch und abschließend gegen
vorher eingefrorene Bytes prüfen. Konsistente Neuhashung ersetzt diese Anker
nicht. Geladene BLAS-Pools vor/nach Fit kontrollieren. Positiven Bericht erst
nach abschließender Hash- und Zeitprüfung veröffentlichen; spätere Fehler in
der Abschlussphase widerrufen ihn. Verifizierte Artefakte und Logs bleiben
erhalten. Der neue Plan gehört ausdrücklich zu den Laufzeitdokumenten mit
vollständiger CI; die sechs bisherigen eingefrorenen Pläne bleiben unverändert.

## 6. Entscheidungsregel

Voraussetzung ist ein vollständiger technisch verifizierter Vergleich.

| Ergebnis | Konsequenz |
| --- | --- |
| `C_A > C_K` und mindestens eine kurvengute A-Originalauswahl mit unterstützter abklingender Struktur und bestandenem Parameterreplay | Positives Entwicklungssignal; ausschließlich einen getrennten Übertragbarkeitsplan erwägen. Kein Produktionsprofil, keine Hauptversuchsfreigabe. |
| `C_A > C_K`, aber ohne diesen Strukturnachweis | Verbesserte Approximation; freier Strukturanspruch offen. Kein automatischer Erkennerumbau oder Nachfit. |
| `C_A <= C_K`, auch bei kleineren kontinuierlichen Fehlern | Hypothese des Vergleichs nicht gestützt; A nicht übernehmen. Ende dieses Versuchs; weiteres Vorgehen ausdrücklich neu abwägen. |
| Nur ungewählte Kandidaten gut oder alle sechs Zellen ohne Erfolg | Originalauswahl beibehalten; negative/limitierte Befunde sichern. Keine weitere Restriktionsstufe oder Wiederholung. |
| Unvollständig oder Verifikation fehlgeschlagen | Kein abgeschlossener Vergleich; Teilbefund sichern, Ursache und weiteres Vorgehen gesondert entscheiden. |

„Mindestens eine“ ist ein schwaches organisatorisches Entwicklungssignal,
kein statistisch begründetes Leistungsgate. Pause bedeutet hier Unterbrechung
weiterer freier Suchversuche bis zu einer neuen begründeten Entscheidung,
nicht Ersatz des Forschungsziels durch die bekannte Formel oder Abbruch der
Masterarbeit. Auswahlverfahren, Hintergrunddesign, Übertragbarkeit und der
frühere Budgetarchiv-Audit bleiben eigene offene Fragen.
