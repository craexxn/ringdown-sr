# Methodenplan: baumabhängige Vorhersageverifikation

Ausarbeitung vom 04.11.2026 zum beauftragten Schritt 1: Prüfregel und
mathematische Begründung vor Implementierung. Grundlage ist der
[Audit von Lauf 003](search_duration_results_manjaro_003.md), übernommen mit
[PR #57](https://github.com/craexxn/ringdown-sr/pull/57) als
`4c49723e08f6deb9eb086922c1be546819f3408f`.
Dieser Plan wird separat versioniert. Er aktiviert keine neue Prüfung und
beauftragt weder Implementierung noch einen weiteren wissenschaftlichen Lauf.

## 1. Ziel, Geltung und Aussage

Die Prüfung soll bestätigen, dass beide gespeicherten/nachgerechneten
Float64-Vorhersagen in einem **vor Kenntnis dieser Vorhersagen konstruierten,
hinreichend engen Wertebereich** für denselben Originalbaum liegen. Ein
Rundungsunterschied einzelner Funktionen darf entsprechend seiner
Fortpflanzung im Baum wirken. Eine beliebig breite Einschließung genügt nicht.

Gemeint ist die Auswertung mit Rundung an den ursprünglichen Baumknoten,
nicht die exakte reelle Funktion nach algebraischer Vereinfachung. Beispiel:
`((t-1e16)-(-1e16))+1` kann in Float64 korrekt den Wert 1 liefern, obwohl die
reelle Formel `t+1` lautet. Die Referenz darf diese unterschiedliche Semantik
nicht verdecken. Suchbaum, Konstantenbits und Auswertungsreihenfolge bleiben
maßgeblich; keine Vereinfachung oder Neuparametrisierung.

Vorgesehen ist ausschließlich ein neuer Suchbudget-Verifikationspfad,
Serienformat 4. Er ersetzt dort den notwendigen festen Python-/Julia-
Vorhersagevergleich durch die unten definierte Einschließungsprüfung.
Der neue Vertrag gilt für **jeden Kandidaten und jeden Trainingspunkt**,
auch für ungewählte Kandidaten und bisher tolerierte Fälle. Er ist keine
monotone Lockerung: Ein alter Vergleich kann bestehen, während der neue
Referenznachweis scheitert oder unbestimmt bleibt. Frühere Formate bleiben
unverändert lesbar und verwenden ihren bisherigen Vertrag.

Ein positiver Befund heißt `compatible_with_bounded_rounding_model`:
beide Endwerte sind mit der engen, unabhängig berechneten Einschließung
vereinbar. Er beweist weder die tatsächliche interne Rundungsgeschichte noch
eine globale Fehlergarantie für NumPy/Julia, korrekte Physik, die exakte reelle
Formelauswertung oder eine vollständig stabile wissenschaftliche Klassifikation.

## 2. Festgelegtes lokales Rechenmodell

Für einen Trainingszeitpunkt sind alle Eingaben und Konstanten exakte reelle
Interpretationen ihrer Float64-Bits. Der Baum wird ausschließlich mit
`+`, `-`, `*`, `/`, `exp`, `sin`, `cos` und der vorhandenen Variablen gelesen.
Knotenmetadaten, Kindreihenfolge und Konstantenbits werden vorab validiert,
auch in scheinbar unwirksamen Teilbäumen. Beobachtungen, Wahrheit,
Diagnosepunkte und Kandidatenauswahl sind keine Eingaben des Referenzrechners.

Sei `RN64(x)` die Rundung des reellen x auf IEEE-Binary64, zum nächsten Wert
mit gerader Mantisse bei Gleichstand, einschließlich graduellen Unterlaufs.
Für elementare Rechenoperationen ist nur `RN64(op(a,b))` vorgesehen.
Für `exp`, `sin`, `cos` ist zusätzlich höchstens **ein benachbarter
Float64-Schritt** unter oder über `RN64(f(a))` vorgesehen, begrenzt auf den
Funktionswertebereich: `[0,+∞)` für exp, `[-1,1]` für sin/cos.

Dieses Nachbarbudget ist eine **festgelegte Genauigkeitsanforderung**, keine
behauptete universelle Bibliotheksgarantie. Es ist die kleinste nichttriviale
Erweiterung der Forderung nach identischer korrekter Rundung. Sie lässt die
bekannte Abweichung zweier benachbarter exp-Ergebnisse grundsätzlich zu,
ohne ein aus den Endabweichungen angepasstes rtol festzulegen. Ein Schritt
zum Nachbarn der korrekt gerundeten Zahl ist nicht gleichbedeutend mit
einem Fehler von höchstens einem ULP zum exakten Funktionswert; insbesondere
an Binadengrenzen gilt ausschließlich die obige Nachbardefinition.

Die neue Prüfung verlangt am Ende ausdrücklich die Zugehörigkeit beider
tatsächlichen Vorhersagen. Ein Ergebnis außerhalb bleibt abgelehnt, auch
wenn seine Abweichung als Bibliotheksrundung vermutet wird. Umgekehrt beweist
die Endwertzugehörigkeit keine lokalen Einzelschrittfehler: Fehler können
sich kompensieren. Diese Grenze ist im Nachweis auszuweisen.

Der Vergleich setzt die vorhandene binäre Knotenfolge voraus. Ungeprüfte
Umklammerung, Fast-Math, FMA-Kontraktion über Knotengrenzen oder ein anderer
Backendpfad werden nicht als zusätzliche erlaubte Varianten aufgenommen.
Die gepinnten Evaluationsquellen, `turbo=false`, `bumper=false` und feste
Rundungs-/Kontraktionsgegenfälle sind vor Aktivierung zu prüfen. Eine
Abweichung erfordert einen neuen Methodenentscheid, keine Suchprofiländerung
innerhalb dieses Plans.

## 3. Konstruktion der Einschließung

An jedem Knoten wird ein geschlossenes Intervall I mit Float64-Endpunkten
geführt; Vergleiche und Abstände interpretieren diese Endpunkte exakt.
Blätter starten als Punktintervalle ihrer ursprünglichen Bits.

Für ein binäres Rechenzeichen wird zunächst die reelle Intervallhülle J der
Operation auf den Kinderintervallen berechnet: Endpunktsummen/-differenzen,
Minimum/Maximum der vier Produkte beziehungsweise Quotienten.
Ein Nennerintervall, das null enthält, liefert keinen positiven Nachweis.
Danach wird J durch monotones `RN64` eingeschlossen:

```text
R([a,b]) = [RN64(a), RN64(b)]
I_binär = R(J)
```

Die binären Endpunktoperationen und ihre Rundungsentscheidungen können exakt
rational erfolgen. Die Implementierung darf stattdessen gerichtete
MPFR-Einschließungen verwenden, muss dann aber auch deren Unsicherheit
nach außen mitnehmen. Ein gerundeter Mittelpunkt ist keine Einschließung.

Für einen transzendenten Knoten wird J nach außen gerundet über den gesamten
Kindbereich gebildet und anschließend die Nachbarerweiterung angewandt:

```text
[q_lo,q_hi] = R(J)
I_transzendent = [prevfloat(q_lo), nextfloat(q_hi)] ∩ Wertebereich(f)
```

Bei exp genügt die Monotonie. Bei sin/cos müssen neben den Endpunkten alle
möglichen inneren Extrema berücksichtigt werden: sin bei `π/2+kπ`, cos bei
`kπ`. Die Lageprüfung verwendet nach außen gerundete Pi-Einschließungen;
kein Float64-Pi und keine ungeprüfte Modulo-Reduktion großer Argumente.
Möglicherweise enthaltene Extrema werden konservativ eingeschlossen.
Bei einem sicher vollständig überdeckten Zeitraum von `2π` ist `[-1,1]`
zulässig; ob daraus ein hinreichend enger Endnachweis folgt, entscheidet
die Breitenprüfung. Ungeklärte Perioden-/Paritätsentscheidungen dürfen keine
Extrema ausschließen.

Benötigt werden gerichtete MPFR-Operationen, vorzugsweise über BigFloat der
bereits gepinnten Julia-Umgebung. Eingaben sind exakte Float64-/Dyadenwerte,
keine erneut interpretierten verkürzten Dezimalformeln. Die Umwandlung nach
Binary64 muss dessen Exponentenbereich und Subnormalzahlen korrekt behandeln;
MPFR mit bloß 53 Mantissenbits emuliert diese Eigenschaften nicht automatisch.

Die Referenzpräzision folgt fest der Leiter **128, 256, 512, 1024 Bits**.
Auf jeder Stufe wird der gesamte Nachweis frisch aus Baum und Zeitbits
gebildet. Verwendet wird die erste Stufe mit endlichen Bereichen und
bestandener Breitenprüfung aus Abschnitt 4; die tatsächlichen Vorhersagen
beeinflussen weder Präzision, Budget noch Intervall. Reicht die Leiter nicht,
ist das Ergebnis `indeterminate`, ohne Ersatzverfahren. Die Leiter begrenzt
den Aufwand; sie ist keine Vollständigkeitsgarantie. Zwei übereinstimmende
hochpräzise Punktwerte allein ersetzen keine gerichtete Einschließung.

**Begründung durch Induktion:** Blätter enthalten die exakten Eingaben.
Enthalten Kinderintervalle zulässige Kinderwerte, enthält J alle zugehörigen
reellen Operationsergebnisse. Die monotone Rundung R und gegebenenfalls
Nachbarerweiterung enthalten alle nach dem festgelegten Modell zulässigen
Ergebnisse. Damit gilt die Einschließung auch an der Wurzel. Wiederholte
Teilbäume und Abhängigkeiten dürfen die Hülle verbreitern, aber nicht durch
unbewiesene Korrelationen verkleinern. Der Beweis ist bedingt auf das Modell;
die tatsächlichen Endwerte werden anschließend direkt geprüft.

## 4. Unabhängige Breitenbegrenzung und Entscheidung

Aus den **Referenzintervallen allein**, vor dem Lesen der Vorhersagen, setze
für alle n Trainingspunkte:

```text
I_i = [l_i,h_i]
w_i = h_i-l_i
S = max_i(max(abs(l_i),abs(h_i)))
u = 2^-53
```

Für `S>0` muss für jedes i exakt rational gelten:

```text
w_i^2 <= u*S^2
```

Dies begrenzt die Breite auf `sqrt(u)*S ≈ 1,054e-8*S`, ohne gerundeten
Schwellenvergleich, Einheitsgrößenboden oder Bezug zu beobachteten
Python-/Julia-Differenzen. `sqrt(u)` ist eine bewusst festgelegte
Qualitätsgrenze: Mindestens etwa die Hälfte der 53 binären Präzisionsstellen
soll auf der gemeinsamen Amplitudenskala aufgelöst bleiben. Das beschreibt
die Breite des zugelassenen Ergebnisbereichs, keine garantierten gültigen
Stellen gegenüber der ungerundeten reellen Funktion. Sie ist weder
ein Fehlergesetz der Bibliotheken noch aus den vier Fehlerfällen geschätzt.
Die wissenschaftlichen Grenzen `1e-3`/`1e-2` werden daraus nicht neu abgeleitet.
Andere Breitenbudgets erfordern eine ausdrücklich neue Planversion.

Die Referenzskala kann eine große Unsicherheit nicht beliebig verstecken.
Wird S an einem Endpunkt erreicht, liegt jeder darin eingeschlossene
Vorhersagevektor dort betragsmäßig mindestens bei `(1-sqrt(u))*S`.
Somit ist die maximale zulässige Differenz zweier eingeschlossener Vektoren
auch relativ zu deren tatsächlicher Maximalamplitude höchstens
`sqrt(u)/(1-sqrt(u))`. Diese Folgerung ist keine zusätzliche Zulassungsregel.

Nach dieser vorhersageunabhängigen Konstruktion müssen **beide** endlichen
Float64-Werte an jedem Punkt im zugehörigen I_i liegen. Es gibt keinen
zusätzlichen rtol-/atol-Aufschlag. Bei `S=0` sind alle Referenzintervalle exakt
`[0,0]` und beide Vorhersagevektoren müssen exakt null sein. Numerisch sind
`+0` und `-0` gleich; gespeicherte Baum-/Konstantenbits bleiben getrennt gebunden.

- `passed`: sämtliche Metadaten-, Bereichs-, Breiten- und Zugehörigkeitsprüfungen
  bestanden, Aussage wie in Abschnitt 1.
- `failed`: ungültige Eingaben/Belege oder mindestens ein tatsächlicher
  Vorhersagewert außerhalb eines gültigen engen Intervalls.
- `indeterminate`: keine hinreichend enge/definierte Einschließung innerhalb
  der Präzisions- und Ressourcenlimits. Das ist kein Beweis einer falschen Formel.

Nur `passed` erlaubt die weitere Zellverifikation. Fehlgeschlagene und
unbestimmte Nachweise stoppen die Serie; keine Auslassung einzelner Kandidaten.
Auch zwei identische Vorhersagevektoren umgehen den Referenznachweis nicht.

## 5. Null, Unterlauf, Überlauf und Ressourcen

Subnormale Vorhersagen sind nicht pauschal ungültig. Sie werden mit dem
tatsächlichen Binary64-Gitter eingeschlossen; positive subnormale MSE und
die anderen vom bestehenden Verlustvertrag ausgeschlossenen Reduktionsfälle
bleiben dagegen unverändert verboten. Keine Flush-to-zero-Annahme und kein
Abschneiden kleiner Werte zur Vermeidung einer Prüfung.

Sehr negative exp-Argumente dürfen mit einer vorab bewiesenen Schranke
behandelt werden: Für `x <= -1076` gilt `0 < exp(x) < 2^-1076`, weil `e>2`.
Diese Einschließung erzwingt die korrekte Rundung auf null vor der definierten
Nachbarerweiterung und vermeidet einen künstlichen MPFR-Exponentunterlauf.
Andere Kurzwege benötigen ebenso einen festen Beweis. Eine äußere Skalierung
oder Division wird anschließend regulär durch den Baum fortgepflanzt.
Für `x >= 1024` folgt aus `e>2` bereits `exp(x)>2^1024>floatmax`;
dieser Bereich wird vor einem potenziell extremen MPFR-Aufruf als möglicher
Überlauf gesperrt. Dazwischen werden gerichtete Werte regulär berechnet.

NaN, tatsächliche Unendlichkeit, nichtendliche Referenzgrenzen, potenzieller
Binary64-Überlauf oder ein möglicher Nullnenner ergeben keinen positiven
Nachweis. Insbesondere darf `nextfloat(floatmax)` nicht still auf floatmax
gekappt werden. Ein weiter Bereich kann durch höhere Referenzpräzision enger
werden; verbleibende Mehrdeutigkeit bleibt gesperrt. Vollständig verschwundene
Signale mit nur nichttrivialen Unsicherheitsintervallen können unbestimmt bleiben.

Alle Referenzarbeit zählt zu den bisherigen **600 Sekunden je Suchworker und
7200 Sekunden insgesamt**, einschließlich Elternprozess und Finalisierung.
Keine Erweiterung dieser Grenzen. Präzisions-/Rundungskontexte sind lokal
wiederherzustellen; sie dürfen weder Float64-Suche, Optimierer, RNG noch
andere Threads beeinflussen. Ein überwachter Referenzprozess muss von der
bestehenden Prozessgruppen-/Abbruchsicherung erfasst sein. Der technische
Nachweis muss zeigen, dass der Referenzaufwand mit den bisherigen Grenzen
vereinbar ist; andernfalls ist die Umsetzung noch nicht startfähig.

## 6. Unveränderte wissenschaftliche und numerische Verträge

Suchprofil einschließlich `should_simplify=false`, Grammatiken, Datenrollen,
Sekundenkoordinate, Seeds, 200/2000 Iterationen, 100/2-Optimierer,
Populationen, Häufigkeitsschalter, Haswell/Threadlimit 1 und serielle Ausführung
bleiben unverändert. Referenzarbeit erfolgt erst nach der Suche. Keine
Zustandsübernahme, Zusatzsuche, Konstantenanpassung oder Kandidatenumwahl.

Die [Verifikationsergänzung](search_duration_verification_plan.md),
[Tabellenregel](search_duration_table_loss_note.md) und
[Vereinfachungsabschaltung](search_duration_simplification_plan.md) bleiben
bis auf den hier ausdrücklich ersetzten Vorhersagevergleich bindend:
Baumrundreise, native Originalverluste, Tabellenvergleich, exakte
Residuenbits, Normalbereich, rationale eigene Reduktionsschranken und die
Schranke für den Verlustunterschied bleiben notwendige Bedingungen.
Das Referenzintervall ersetzt insbesondere keine Verlustprüfung.

Die alten Vorhersageabstände dürfen beschreibend protokolliert werden,
entscheiden im neuen Pfad aber nicht zusätzlich als verborgenes Legacy-Gate.
Der Austausch betrifft Worker, Verlustnachweis und Elternnachrechnung
derselben Python-/Julia-Trainingsvorhersagen. Er ist ausdrücklich **keine
globale Änderung** von `_check_prediction_replay`: Parameter-, Alias- und
Umformungsreplays sowie andere Kontrollpfade behalten ihre Regeln.
Jeder tatsächlich erreichte Aufruf ist vor Implementierung entsprechend
zuzuordnen; kein pauschales globales Monkeypatching.

Kurvenmarker, Struktur-/Parameterdiagnose und ihre Grenzwerte bleiben
unverändert. Die neue numerische Zulässigkeit kann beeinflussen, welche
Serien überhaupt vollständig verifizierbar sind; sie ist nicht bloß ein
Anzeigewechsel. Sie erweitert keinen Strukturerkenner und behauptet keine
Robustheit eines wissenschaftlichen Markers exakt an dessen Grenze.
`physical_identification` bleibt `not_assessed`, einschließlich `8*fs`-Blindfleck.

## 7. Nachweise, Elternprüfung und Planbindung

Der zukünftige Kandidatennachweis muss Format/Regelversion, exakten Baumhash,
Zeitgitter-Fingerprint, Quellen-/Planbindung, Präzisionsstufe, Referenz-
Bibliotheksversion, sämtliche Intervallendpunkte als exakte Hex-/Dyadenwerte,
Skala, Breiten- und Zugehörigkeitsstatus sowie präzise Fehlergründe enthalten.
Die Regelparameter Nachbarschritt 1, Präzisionsleiter und `u=2^-53` sind
unveränderliche Teile der Planversion, keine frei wählbaren Laufargumente.

Der Elternprozess berechnet die Referenz aus Originalbaum und konsumierten
Zeitbits neu, statt nur Workerintervalle oder einen Status zu übernehmen.
Er berechnet auch Pythonvorhersagen und alle bisherigen Verlustnachweise neu.
Das gilt für erste/spätere Zellen und alle ungewählten Kandidaten. Quellen,
Eingaben und Ergebnisse sind vor/nach der Nachrechnung gegen die ursprünglichen
Verbrauchsanker zu prüfen. Ein Cache wäre nur bei vollständigem Schlüssel aus
Baum-/Zeitbits, Plan, Referenzquellen und Laufzeitversion zulässig; geänderte
Belege dürfen keinen alten positiven Eintrag erben.

Übergeben werden ausschließlich validierte Baum-/Zeitdaten, keine
serialisierten Suchzustände oder ausführbaren Archivquellen. Der
Referenzrechner verwendet weder die numerische Suchzielfunktion noch deren
Callback, Optimierer oder RNG. Bestehende Aufrufnachweise dürfen durch die
zusätzliche Nachrechnung nicht verändert werden.

Numerische Vereinbarkeit ist kein Authentizitätsnachweis: Semantisch
äquivalente oder unterhalb der Auflösung liegende Änderungen sind nicht
allgemein durch einen Zahlentest erkennbar. Originalexport, Hashbindungen,
Baumrundreise und unveränderte Auswahl bleiben deshalb unabhängig erforderlich.

Bei einer später beauftragten Implementierung sind diese Planbytes durch
einen bereits vorhandenen Commit und SHA-256 zu binden. Das neue Dokument
wird dann ausdrücklich in die Liste laufzeitrelevanter Dokumente und deren
volle CI aufgenommen. Frühere eingefrorene Planbytes bleiben unverändert;
das neue Format erklärt die gezielte Ablösung ihres Vorhersagevertrags.
Im jetzigen reinen Plan-PR ist das Dokument noch nicht laufzeitkonsumiert.

## 8. Verbindlicher Prüfauftrag für eine spätere Umsetzung

1. Unabhängige Referenzfälle für exakte Blätter/Grundoperationen,
   Binadengrenzen, Halbwegsfälle mit gerader Rundung, benachbarte transzendente
   Ergebnisse, Null und Subnormalzahlen. Einschließung und Monotonie mit
   exakten rationalen oder separat formulierten gerichteten Referenzen prüfen;
   keine Erwartungswerte aus derselben Implementierungsroutine erzeugen.
2. Sinus-/Kosinusintervalle mit inneren Extrema, mehreren Perioden, großen
   Argumenten und unklaren Pi-Grenzen; Division nahe/über null; starke
   Auslöschung und Rundungsverstärkung. Endliche, aber zu breite Intervalle
   müssen auch bei identischen Vorhersagen unbestimmt bleiben.
3. Beidseitige Mitgliedschaft und rationale Breitenentscheidung unmittelbar
   innerhalb/außerhalb der Grenzen, bei sehr kleinen/großen Amplituden und
   exakter Null. Veränderte Vorhersagen dürfen Referenzskala, Budget oder
   Präzisionswahl nicht beeinflussen.
4. Alle zehn CSV-Bäume aus Lauf 003 fest nachrechnen, ausdrücklich mit den
   vier bislang abgelehnten Fällen. Kein Erfolg vorwegnehmen: Ein weiter
   abgelehnter Fall wird begründet, nicht durch erhöhtes Budget passend gemacht.
   Die 34 vollständigen Originalkandidaten sowie frühere Nähe-null- und
   Tabellenfälle prüfen. CSV-Rekonstruktionen bleiben nachträgliche Fixtures,
   keine wiederhergestellten nativen Originalexporte oder Originalauswahlen.
5. Falscher Operator, Konstante, Knotenfolge, Eingabebits, fehlender/falscher
   Referenzbeleg und manipulierte ungewählte Kandidaten; auch Fälle, in denen
   beide Auswertungen gleich falsch sind. Unveränderte Originalbindungen und
   tatsächlich außerhalb liegende Vorhersagen müssen diese Fehler abweisen.
   Der alte veraltete Verlust aus Lauf 002 bleibt gesperrt, selbst wenn der
   neue Vorhersagenachweis besteht.
6. Worker-/Elternvergleich, abgesicherte Plan- und Quellbindungen,
   Präzisionserschöpfung, Zeitlimit, Prozessabbruch und Fehler nach positivem
   Abschlussbericht. Aggregate und Abschlussmanifest bleiben bei Fehlern
   gesperrt; keine Abschlussfreigabe vor allen Nachrechnungen.
7. Unveränderte ältere Kontrollpfade und Parameter-/Aliasreplays; sämtliche
   technischen Python-/Julia-Prüfungen und bestehende kleinen Integrationen,
   ausdrücklich keine wissenschaftlichen Cloud-Suchen. Optionen und echte
   Suchaufrufe bleiben absolut gebunden, wiederholte technische Fronten gleich.

Ein gezieltes KI-basiertes Review soll anschließend insbesondere Modell versus
Bibliotheksgarantie, gerichtete Einschließung, unabhängige Breitenbegrenzung,
Unterlauf/Extrema, verbliebene Legacy-Aufrufe und die unveränderten
Verlust-/Auswahlverträge prüfen. Dieser Prüfauftrag ist keine Behauptung über
bereits implementierte oder bestandene Tests.

## 9. Abgewogene Alternativen und spätere Ausführung

Verworfen sind eine pauschale Erhöhung des bisherigen rtol/atol, ausschließlich
ein anderer Float64-Mathematikpfad, gleiche Python-/Julia-Werte als alleiniger
Nachweis und beliebig breite Intervalle. Ein hochpräziser ungerundeter
Gesamtbaum wäre eine andere Semantik; eine Änderung des nativen Suchkerns,
ein nachträgliches Vereinfachen oder privilegierte Ringdown-Formeln wären
andere Eingriffe. Keiner davon ist Teil dieses Plans.

Die neue Modellbreite und das Nachbarbudget sind offen benannte
Qualitätsentscheidungen. Die Induktionsbegründung garantiert die Einschließung
des Modells; sie macht diese Entscheidungen nicht zu empirisch optimalen
Werten und garantiert nicht, dass jede Suchfront zertifiziert werden kann.

Erst eine separat beauftragte Umsetzung mit vollständigen technischen
Nachweisen, gezieltem Review und manuellem Merge könnte einen neuen Manjaro-
Start vorbereiten. Dabei wären alle 20 Zellen unter derselben neuen
Verifikationsversion frisch auszuführen, ohne Wiederaufnahme oder Mischung
mit Lauf 003. Frühere Serien bleiben unvollständig; wiederverwendete Seeds
sind adaptive Entwicklung. Dieser Plan legt noch keinen Startbefehl oder
neuen Ergebnisordner an. WSL2, Parallelisierung, zusätzliche Budgets und
Strukturerweiterung bleiben außerhalb dieses Schritts.

## 10. Gelesene Quellen und ihre Tragweite

- **GNU MPFR-Handbuch 3.1.3**, Abschnitte „Rounding Modes“, Konversion und
  Exponentenbereich, gelesen als
  [Spiegel des GNU-Handbuchtexts](https://github.com/alisw/MPFR/blob/d0edb09adbf3386749aa73af887364ba9d34510b/doc/mpfr.texi).
  Es beschreibt korrekt gerundete Operationen, gerichtete Rundung und exakt
  interpretierte Operanden. Das ältere Handbuch belegt die Grundsemantik,
  nicht die konkrete installierte Bibliotheksversion; diese muss der spätere
  Nachweis erfassen. MPFRs eigener Exponentenbereich ist kein automatisches
  Binary64-Unterlaufmodell.
- **Julia 1.13.1**, [Handbuch zu Gleitkommazahlen](https://github.com/JuliaLang/julia/blob/v1.13.1/doc/src/manual/integers-and-floating-point-numbers.md)
  und [BigFloat-/MPFR-Anbindung](https://github.com/JuliaLang/julia/blob/v1.13.1/base/mpfr.jl),
  relevante Rundungs-/Konversions- und exp/sin/cos-Pfade gelesen. Belegt die
  verfügbare gerichtete Referenztechnik, keine richtige automatische
  Intervallbehandlung ganzer Formelbäume.
- **NumPy 2.5.3**, [exp/log-Evaluationsquellen](https://github.com/numpy/numpy/blob/v2.5.3/numpy/_core/src/umath/loops_exponent_log.dispatch.c.src),
  relevante Float64-Dispatch- und Näherungspfade gelesen. Unterschiedliche
  Auswertungspfade sind möglich. Dort genannte Float32-Fehlerzahlen werden
  ausdrücklich nicht als Float64-Garantie oder Nachweis des historischen
  CPU-Dispatchs verwendet.
- **DynamicExpressions 2.12.0**, gepinnter Baumhash
  `b1d03a3ec55e57eedfce3510659d2b0bbce16975`,
  [Evaluate.jl](https://github.com/SymbolicML/DynamicExpressions.jl/blob/v2.12.0/src/Evaluate.jl),
  installierte Nicht-Turbo-Knotenpfade einschließlich kombinierter Schleifen
  gelesen. Zusammen mit dem Projektadapter begründet dies die zu prüfende
  Originalreihenfolge; es ersetzt keine technischen Gegenprüfungen der
  tatsächlichen Compiler-/Rundungssemantik.

Die Intervallinduktion und Breitenfolgerung dieses Plans sind hier explizit
hergeleitet. Keine Quelle wird als Garantie für Sucherfolg, optimale Toleranz
oder vollständige Erkennung manipulierter Ergebnisse angeführt.
