# Methoden- und Abnahmeplan: Interpretation erkannter Ringdown-Ausdrücke

Stand: 23.10.2026. **Entwurf für einen nachgelagerten Diagnosebaustein.**
Dieser Plan ergänzt den [SR-Methodenplan](symbolic_regression_method_plan.md)
und die [Alias-/Phasenreferenzen](alias_references.md). Er ist noch keine
Implementierung oder wissenschaftliche Identifikationsbewertung.

## 1. Ziel und Abgrenzung

Für einen Teil der exportierten SR-Bäume sollen Parameter eines erkannten
Ein-Moden-Ausdrucks nachvollziehbar abgeleitet werden:

$$
 h(t)=A\exp(bt)\cos(ct+d).
$$

Die Diagnose erfolgt nach der bestehenden verlustbasierten Auswahl.
Sie verwendet weder sauberes Signal noch wahre Parameter, zusätzliche
Fits oder Kontrollfenster. Alle ursprünglichen Kandidaten und der
ausgewählte Index bleiben erhalten. Ein nicht unterstützter Ausdruck
wird nicht nachträglich aus der Front entfernt oder schlechter gerankt.
Auch der Anteil erkannter Ausdrücke ist zunächst eine technische
Abdeckungsangabe des Erkenners, keine Rekonstruktionsquote.

Die erste Version erkennt ein begrenztes syntaktisches Muster. Sie löst
nicht das allgemeine Problem algebraischer Äquivalenz. Insbesondere
werden Sinusformen oder andere mathematisch gleichwertige Schreibweisen
außerhalb dieses Musters als `not_supported` ausgewiesen. Daraus folgt
keine physikalische Unzulässigkeit dieser Kandidaten.

## 2. Eingaben und unterstützte Struktur

Eingaben sind der bereits exportierte vollständige Baum mit hexadezimalen
Float64-Konstanten, gespeicherte Samples und Abtastrate. Der Parser prüft
Knotenart, endliche Konstanten, Variablenindex 1 sowie Operatornamen,
Index, Stelligkeit und Kinderzahl gegen die gespeicherte Grammatik.
Ungültige oder widersprüchliche Bäume sind Eingabefehler und werden nicht
als gewöhnliches `not_supported` verborgen. Ein Formel-Anzeigetext wird
nicht geparst; `sympify` oder `simplify` auf solchen Texten ist nicht nötig.

Vorgeschlagenes Muster:

- Der äußere Ausdruck ist ein Produkt aus genau einem `exp`- und einem
  `cos`-Faktor und beliebig vielen rein skalaren rationalen Faktoren.
  Fehlende Vorfaktoren bedeuten `A=1`. Die Reihenfolge und Klammerung
  ausschließlich dieser Produktknoten dürfen verschieden sein.
- Das Exponentialargument ist affin mit exakt verschwindendem konstantem
  Anteil: `b*t`. `exp(b*t+e)` mit `e != 0` bleibt vorerst nicht unterstützt;
  das Absorbieren von `exp(e)` in die Amplitude wird nicht eingeführt.
- Das Kosinusargument ist affin: `c*t+d`. `c` oder `d` dürfen exakt null
  sein. Ein fehlender Summand ist erlaubt.
- Ein affiner Teilbaum wird als Paar `(slope, intercept)` über exakten
  rationalen Zahlen gelesen. Erlaubt sind Konstanten, `t`, `+`, `-`,
  Multiplikation mit einem konstanten affinen Ausdruck sowie Division
  durch einen von `t` unabhängigen, exakt von null verschiedenen Ausdruck.
  Produkte zweier zeitabhängiger Faktoren und zeitabhängige Nenner werden
  nicht reduziert; auch `t/t` wird nicht gestrichen.
- Skalare Faktoren und affine Teilbäume enthalten nur `+`, `-`, `*`, `/`
  und Konstanten bzw. die dort erlaubte Variable. Weitere `exp`, `sin`
  oder `cos`, additive äußere Terme und mehrere Schwingungsmoden werden
  nicht unterstützt. Eine äußere Division des gesamten Produkts wird
  in Version 1 nicht umgeschrieben.

Jede gespeicherte Float64-Konstante wird zunächst als exakt die durch
ihre Bits deklarierte reelle Zahl behandelt. `Fraction` erhält daraus
die rationale Darstellung. Damit wird die mathematische Koeffizienten-
extraktion von einer vorzeitigen gerundeten Summation getrennt. Die
ursprüngliche Float64-Auswertungsreihenfolge ist damit **nicht** erhalten;
ihre numerische Vereinbarkeit wird zusätzlich geprüft (Abschnitt 5).
Die normalen Baumgrößen des Piloten begrenzen den anfänglichen Umfang;
ein außerhalb des gespeicherten Vertrags liegender Baum wird nicht
unbegrenzt rekursiv bearbeitet.

## 3. Rohe Parameter und Zustände

Der ursprüngliche Baum und seine Konstanten werden unverändert referenziert.
Zusätzlich werden die extrahierten rationalen Koeffizienten `A,b,c,d` mit
Zähler und Nenner als Dezimalzeichenfolgen gespeichert. Dies bezeichnet
mathematisch zusammengefasste Koeffizienten, keine nachoptimierten Werte.
Für eine Float64-Darstellung werden Rundung und Wertebereich geprüft.

| Größe | Ableitung und Bedeutung |
| --- | --- |
| Amplitude | Vorzeichenbehaftetes `A`; keine automatische Positivierung samt Phasenverschiebung |
| Abklingzeit | `tau=-1/b` ausschließlich bei `b<0`; bei `b=0` bzw. `b>0` stattdessen Kennzeichnung `undamped` bzw. `growing` |
| Rohe Frequenz | `nu=c/(2*pi)` und ihr Betrag; Frequenz des Ausdrucks, keine eindeutige erzeugende Frequenz |
| Rohe Phase | `d` vor jeder Periodenreduktion |
| Einheiten | `b,c`: `1/s`, `tau`: `s`, `nu`: `Hz`; `A,d` dimensionslos bei bisheriger Ausgabe |

Die Einheitendarstellung folgt dem erkannten Formansatz und den Sekunden
der Zeitvariable. Der bisherige Backend-Wildcard-Check wird dadurch nicht
zu einer eindeutigen Rekonstruktion aller ursprünglichen Konstanteneinheiten.

Zustände werden getrennt geführt: Struktur `recognized/not_supported`,
Exponentialform `decaying/undamped/growing`, Amplitude `zero/nonzero`,
numerischer Replay und Aliasinterpretation. Abgeleitete Zahlen tragen
jeweils einen Wert und einen Status; nicht bestimmbare Zahlen sind `null`
mit Grund. Ein strukturierter Erfolg darf keinen vollständigen numerischen
Erfolg vortäuschen. Nicht endliche JSON-Zahlen sind ausgeschlossen.

Bei exakt `A=0` werden Frequenz, Abklingzeit und Phase ausdrücklich als
aus diesen Samples nicht identifizierbar gekennzeichnet. Ein sehr kleiner
Wert wird nicht auf null gesetzt. Rundet ein von null verschiedener
Koeffizient oder eine Abklingzeit beim Export auf null bzw. außerhalb des
Float64-Bereichs, erhält diese Darstellung `numerical_unresolved`.
Auch eine durch Unterlauf entstandene Nullkurve belegt kein exakt `A=0`.

## 4. Alias- und Phasenreduktion mit Zuverlässigkeitsprüfung

Die Konvention aus Abschnitt 6.1 des SR-Methodenplans bleibt erhalten:

$$
 k=\lfloor\nu/f_s+1/2\rfloor,\quad q=\nu-kf_s,
 \qquad s=\begin{cases}-1&q<0\\1&q\ge0\end{cases},
$$

$$
 f_{\rm alias}=|q|,\qquad
 d_{\rm alias}=s d-2\pi\lfloor s d/(2\pi)+1/2\rfloor.
$$

Sie gilt für `t_j=j/fs`, `fs>0`, Zeitursprung null. Eine andere oder
unregelmäßige Zeitachse erhält in Version 1 keine Aliasinterpretation.
Die gespeicherten Float64-Zeiten werden gegen die erklärte Achse `j/fs`
geprüft; eine Toleranz darf fremde Achsen nicht zurechtrücken.
Nyquist ist eine Darstellung der negativen Restfrequenz `-fs/2`.

Wichtig ist die Unterscheidung zwischen einer ausdrücklich in Hz
deklarierten Frequenz und einer Baumkonstante `c`. Beispielsweise kann
die Float64-Rechnung `c=2*float(pi)*2048` und anschließend
`c/(2*float(pi))` exakt 2048 liefern, obwohl `c/(2*pi)` mit mathematischem
`pi` etwas darunter liegt. Die Hz-Referenzen allein sichern diese
Umrechnung daher nicht ab. Eine gerundete Grenzfrequenz ist kein Nachweis
einer exakten Degeneration.

Als konservativer Vorschlag für den reinen Diagnosebaustein:

1. `pi` wird durch rationale Unter-/Obergrenzen eingeschlossen. Dafür
   dient die Machin-Identität `pi=16*atan(1/5)-4*atan(1/239)` mit der
   alternierenden Potenzreihe für `atan`. Zwischen einer Partialsumme
   und der um den nächsten vorzeichenbehafteten Term ergänzten Summe
   liegt der exakte Wert; alle Rechnungen bleiben rational.
2. Es werden nacheinander 16, 32 und höchstens 64 Terme je Reihe benutzt.
   Das ist ein festes technisches Rechenbudget. Es begründet keinen
   Anspruch, jede endliche Float64-Eingabe reduzieren zu können.
3. Aus diesen Intervallen werden `nu`, `k`, `q`, `s` und die Phasenreduktion
   mit nach außen einschließender rationaler Intervallarithmetik
   bestimmt. Ein ganzzahliger Quotient oder ein Vorzeichen gilt erst
   dann als bestimmt, wenn das gesamte Intervall dieselbe Entscheidung
   liefert. Exakte Nullfälle werden separat behandelt.
4. Ein Float64-Ausgabewert gilt erst dann als bestimmt, wenn das gesamte
   Intervall in derselben Rundungszelle liegt. Die Zellgrenzen sind die
   exakten Mittelpunkte zu den benachbarten Float64-Zahlen. Eine lediglich
   gleich aussehende Dezimaldarstellung genügt nicht. Berührt ein Intervall
   eine Rundungsgrenze, darf die Version konservativ unbestimmt melden.
5. Rundet ein nachweislich innerer Aliaswert auf null oder Nyquist, darf
   daraus keine DC-/Nyquist-Degeneration werden: Aliaswerte bleiben dann
   `null` mit dem Grund `boundary_rounding`. Die Phasen-Konvention wird
   entsprechend gegen ein durch Rundung verschobenes Intervallende
   abgesichert. Keine Nähe-Toleranz ersetzt diese Entscheidungen.
6. Reicht das Budget nicht aus, lautet der Aliasstatus
   `numerical_unresolved`. Rohe Koeffizienten und gegebenenfalls bereits
   zuverlässig bestimmbare andere Parameter bleiben erhalten. Es gibt
   keinen stillen Float64-Modulo-Fallback.

Bei expliziter Hz-Eingabe ist `q` direkt rational bestimmbar; für die
Phase bleibt die `pi`-Reduktion erforderlich. Diese Schnittstelle wird
zur unabhängigen Prüfung der vorhandenen Hz-Referenzen vorgesehen.
Bauminterpretation und Hz-Hilfsfunktion müssen ihre Eingabebedeutung
unterschiedlich protokollieren.

Bei exaktem Alias null oder Nyquist sind `A` und Phase nicht getrennt
identifizierbar: Auf dem Raster wirkt nur `A*cos(d)`, gegebenenfalls mit
alternierendem Vorzeichen. Es wird kein eindeutig rekonstruierter
Parametervektor behauptet. Auch im Inneren bleibt insbesondere die
Mehrdeutigkeit zwischen Vorzeichen von `A` und Phasenverschiebung um `pi`;
die hier gewählte Erhaltung des Amplitudenvorzeichens ist eine Konvention.
Diese Kennzeichnungen sind keine vollständige Identifizierbarkeitsanalyse
für beliebige Fensterlängen oder Parameterkombinationen.

## 5. Numerische Nachrechnung bleibt erforderlich

Die exakte reelle Umformung ist kein Nachweis gleicher Float64-Auswertung.
Der Originalbaum wird in unveränderter Reihenfolge mit dem bestehenden
`evaluate_tree` ausgewertet. Getrennt werden die erkannte rohe Form und,
falls verfügbar, die Aliasform auf denselben gespeicherten Zeiten geprüft.
Nicht endliche Vorhersagen führen zu einer fehlgeschlagenen Nachrechnung.

Vorgeschlagen wird die bereits im Adapter verwendete normalisierte
Vorhersageprüfung: gemeinsame Skala `max(maxabs(original),maxabs(replay))`,
ohne feste absolute Untergrenze; dann `rtol=1e-12`, `atol=1e-14` in
normierten Einheiten. Bei Skala null müssen beide Kurven exakt null sein.
Skala, maximaler normierter Unterschied und Prüfergebnis werden gespeichert.
Der bestehende Julia-/Python-Replay des Originalbaums wird nicht ersetzt.

Dieses Budget ist eine technische Konsistenzvorgabe für den begrenzten
Adapter, keine wissenschaftliche Identifikationstoleranz und keine
Garantie zwischen oder außerhalb der gespeicherten Samples. Schlägt eine
Nachrechnung fehl, bleibt die mathematische Strukturerkennung dokumentiert,
ihre numerische Darstellung wird aber nicht als bestätigt ausgegeben.
Ein Lossvergleich allein genügt ausdrücklich nicht.

## 6. Ausgabe und Umsetzung in drei Schritten

1. **Strukturerkenner und rohe Koeffizienten:** reines Python-Modul ohne
   Julia-Start, Extraktion aus vollständigen Bäumen, Zustände und Tests.
2. **Parameter- und Aliasdiagnose:** abgesicherte Umrechnungen und
   Nachrechnung; die bereits vorhandenen Referenztabellen bleiben
   unabhängig vom produktiven Algorithmus.
3. **Lesender Export für gespeicherte Schema-3-Läufe:** neues externes
   Diagnosepaket im Format `ringdown-sr-parameter-diagnostics-1`, mit
   Kandidatenzuordnung, Quellprüfsummen, ursprünglicher Laufherkunft und
   separat erfasster Diagnoseumgebung. Der neue Ausgabeordner liegt
   außerhalb der Quelle und darf nicht vorhanden sein.

Die Diagnose soll alle Kandidaten der jeweiligen Front erfassen,
einschließlich `not_supported`, und den ursprünglichen `selected_index`
referenzieren. Die Quelldateien bleiben unverändert; insbesondere wird
ein dort gespeichertes `parameter_interpretation=not_attempted` nicht
nachträglich umgeschrieben. Eine automatische Integration in neue
Suchläufe wird gesondert entschieden.

## 7. Konkrete Abnahmekriterien

| Prüfung | Unabhängig vorgegebenes Ergebnis |
| --- | --- |
| Grundform | `2*exp(-125*t)*cos(512*t+0.25)` ergibt exakt `A=2`, `b=-125`, `c=512`, `d=1/4`, `tau=1/125 s`; rohe Frequenz ist `256/pi Hz` |
| Produktanordnung | Umgekehrte Faktoren und andere Produktklammerung ergeben dieselben rationalen Koeffizienten; ursprüngliche Bäume bleiben unverändert |
| Affine Argumente | `exp((-100)*t-25*t)*cos(256*t+256*t+0.25)` ergibt denselben Koeffizientensatz wie die Grundform ohne ihren Vorfaktor |
| Auswertungsreihenfolge | Der vorhandene Gegenfall `(1e16 + -1e16)+1` gegenüber `1e16+(-1e16+1)` als Teilbaum muss trotz gleicher reeller Reduktion getrennt numerisch geprüft werden; eine fehlgeschlagene Nachrechnung darf nicht als bestätigt erscheinen |
| Unterstützungsgrenzen | `sin`, eine äußere Summe, zwei Kosinusfaktoren, `exp(b*t+1)`, `t*t` im Argument und `t/t` bleiben mit konkretem Grund `not_supported` |
| Ungültige Bäume | Nicht endliche Konstanten, falscher Variablen-/Operatorindex, Stelligkeit oder Kinderzahl sind erkennbare Eingabefehler |
| Formzustände | Negative, null und positive `b` unterscheiden `decaying`, `undamped`, `growing`; keine positive Abklingzeit für `b>=0` erfinden |
| Amplitude | Negatives `A` bleibt negativ. Exaktes null, `1e-21` und ein erst bei Float64-Konversion unterlaufender rationaler Wert bleiben unterscheidbar |
| Hz-Referenzen | Die unabhängigen Vorgaben aus `test_alias_references.py` prüfen den neuen Reduzierer direkt, einschließlich negativer Frequenzen, Phasenumschlag und beider Nyquist-Nachbarn |
| Winkel statt Hz | `c=2*float(pi)*2048` darf nicht ungeprüft als exakt Nyquist klassifiziert werden; ebenso Gegensinn und Nachbarwerte prüfen |
| `pi`-Einschluss | Machin-Winkelidentität über rationale Tangensrechnung prüfen; gerade/ungerade Partialsumme und nächster Restterm müssen echte einschließende Grenzen bilden |
| Numerische Abwehr | Große Winkel/Frequenzen, beide Seiten von Faltungs- und Phasengrenzen sowie Rundungszellgrenzen führen zu korrekten Werten oder ausdrücklich unbestimmtem Status; niemals zu still verschobenen Grenzen |
| Degenerationen | Null/Nyquist und Amplitude null kennzeichnen die fehlende getrennte Identifizierbarkeit; `2*cos(pi/3)` und `cos(0)` sind dafür analytische Referenzen, keine Behauptung exakter Gleichheit beliebiger Float64-Phasenkonstanten |
| Kleine Signale | Vorzeichenfehler bei `1e-21` müssen am Vorhersagevergleich scheitern; gleich große Verluste verschiedener Residuen dürfen sie nicht verdecken |
| Zeitachse | Verschobener Ursprung und unregelmäßiges Raster erhalten keine Nullursprungs-Aliasdiagnose |
| Trennung | Veränderungen synthetischer Wahrheit, Fitparameter, Kontrollfenster oder einer anderen Front dürfen die Diagnose eines unveränderten Baums samt Zeiten nicht ändern |
| Export | Prüfsummen, Originalbaum, Auswahlindex und Eingabedateien bleiben erhalten; vorhandene Ausgaben werden abgelehnt; nicht unterstützte Kandidaten werden mit exportiert |

## 8. Review und Grenzen

Vor der Umsetzung sind besonders das begrenzte Erkennungsmuster, die
Trennung reeller Algebra und Float64-Replay, Intervall-/Rundungsregeln
sowie die Degenerationskennzeichnung methodisch zu prüfen. Die zusätzliche
Intervallarithmetik ist ein konservativer Vorschlag für verlässliche
Diagnosen; ihre Implementierung wird nicht durch dieses Dokument belegt.

Wissenschaftliche Formelauswahl, Generalisierung, SNR-Studien und die
Leistungsbewertung bleiben gesonderte Aufgaben. Die bisherigen Unterschiede
zwischen Manjaro und WSL2 werden durch diese Diagnose nicht erklärt.
Der direkte Vergleich ihrer ursprünglichen Ergebnisdaten bleibt offen.
