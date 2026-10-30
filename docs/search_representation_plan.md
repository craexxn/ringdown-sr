# Methodenplan: Zeitdarstellung und Komplexitätshäufigkeiten

Stand: 30.10.2026. Entwurf für ein gezieltes KI-basiertes Methodenreview
vor Implementierung und Ausführung. Dieser Plan enthält keine neuen
Suchergebnisse. Er ergänzt den ursprünglichen, unverändert eingefrorenen
[Kontrollplan](noiseless_control_plan.md) und den
[Manjaro-Befund](noiseless_control_results_manjaro_001.md) aus PR #35.

## 1. Begrenzte Fragestellung

Verbessert jeweils eine der folgenden Änderungen die rauschfreie Suche
gegenüber einer frisch ausgeführten Baseline: eine vorab festgelegte
Zeitstreckung oder die gemeinsame Aktivierung der beiden Mechanismen für
Komplexitätshäufigkeiten? Die beiden Änderungen werden nicht kombiniert.
Ihr Zusammenwirken wird in dieser Serie nicht untersucht.

Die bisherigen neun Zellen bleiben ein eigener Entwicklungsbefund. In ihnen
verfehlen alle 28 exportierten Kandidaten die Kurvenfehlergrenzen; zugleich
zeigen die übermittelten Zähler insgesamt 1 881 687 Verlustaufrufe. Die
Callbackkontrolle aus PR #35 akzeptiert einen konstruierten Referenzbaum.
Das begründet eine Untersuchung des Suchverlaufs, noch keine konkrete
Ursachenerklärung.

Die neue Serie dient der Methodenentwicklung an einem bekannten Signal.
Die Wahl und Beurteilung der Varianten nutzt ausdrücklich diese
Entwicklungserfahrung. Das ist keine unabhängige Leistungsvalidierung und
kein Nachweis physikalischer Identifikation.

## 2. Drei vorab festgelegte Bedingungen

Die Suchkoordinate heißt hier `u` und wird weiterhin in Sekunden angegeben.
Der interne Variablenname eines gespeicherten Suchbaums darf erhalten bleiben;
seine Koordinatenbedeutung muss im Bericht ausdrücklich ausgewiesen sein.

| Kennung | Suchkoordinate | `use_frequency` | `use_frequency_in_tournament` |
| --- | --- | --- | --- |
| `baseline` | `u=t` | `False` | `False` |
| `time_stretch` | `u=32*t` | `False` | `False` |
| `complexity_frequency` | `u=t` | `True` | `True` |

`baseline` ist eine neue Suche im neuen Ausführungsstand. Sie wird nicht
durch einen alten Kandidaten ersetzt. Unterschiede zur früheren Serie
werden ausgewiesen und nicht durch Wiederholungen beseitigt.

Im dritten Arm bilden die zwei gemeinsam aktivierten Schalter einen
zusammengehörigen Faktor. Sie verwenden Auftretenshäufigkeiten von
Formelkomplexitäten; sie erhalten keine Information über die physikalische
Signalfrequenz. Es wird weder die Einzelwirkung jedes Schalters noch eine
garantierte Populationsvielfalt behauptet. Alle übrigen wirksamen
Bibliotheksvorgaben bleiben gleich und werden gespeichert. Durch die
Schalter verursachte Backendunterschiede müssen vorab konkret zugeordnet
werden; ein pauschales Ausblenden unpassender Optionen ist unzulässig.

## 3. Zeitstreckung ohne geänderte Einheitenregeln

Aus den ausschließlich messplanbezogenen Größen `N=128` und `fs=4096 Hz`
folgt die Fensterdauer `T=N/fs=0,03125 s`. Sie ist von der letzten Abtastzeit
`127/fs` zu unterscheiden. Mit der festen Referenzdauer `T_ref=1 s` wird
der dimensionslose Streckfaktor

$$
\alpha=T_{\mathrm{ref}}/T=32,\qquad u=\alpha t
$$

gebildet. Beide Koordinaten haben die Einheit Sekunden. Es findet kein
Übergang zu dimensionslosen Eingaben statt: Einheitenprüfung und
`dimensionless_constants_only=False` bleiben unverändert. Damit wird eine
Änderung der numerischen Zeitdarstellung von einer Lockerung der
Einheitenregeln getrennt.

Auf dem Trainingsraster gilt exakt `u_j=j/128 s`; die Suchabtastrate beträgt
`fs_u=fs/alpha=128 Hz`, die letzte Suchzeit `127/128 s`. Physikalische
Abtastrate, Zeiten und Beobachtungen bleiben unverändert gespeichert.
Der Faktor folgt weder aus `f0=250 Hz` noch aus `tau0=0,008 s`. Es gibt keine
Suche nach einem günstigen Skalierungsfaktor anhand der Ergebnisse.

Nur zur unabhängigen Herleitung und späteren Positivkontrolle:

$$
h(t)=e^{-125t}\cos(2\pi\,250t),\qquad
q(u)=e^{-(125/32)u}\cos((2\pi\,250/32)u).
$$

Der gestreckte Referenzbaum hat damit `b_u=-3,90625 s^-1`,
`f_u=7,8125 Hz`, `tau_u=0,256 s` und Winkelkoeffizient etwa
`49,087385 s^-1`. Mit expliziter Amplitude 1 besitzen beide
Referenzbäume 11 Knoten. Diese Formeln und Koeffizienten werden der freien
Suche weder als Vorlage noch als Startwerte übergeben. Die Streckung soll
die numerische Suchlandschaft ändern; identische Suchpräfixe oder identische
Erreichbarkeit aller beschränkten Bäume werden nicht behauptet.

## 4. Feste Daten, Budget und Reihenfolge

Physikalische Daten und Diagnosepunkte entsprechen exakt dem ursprünglichen
Plan: ein rauschfreies Signal, dieselben 128 Beobachtungen und 889 inneren
Achtelpunkte, gewöhnliche MSE und keine Kovarianz. Die Beobachtungswerte
werden einmalig erzeugt und in allen Zellen unverändert verwendet. Für die
Suche entstehen daraus ausschließlich die jeweilige Zeitkoordinate und
derselbe Beobachtungsvektor. Wahrheitsparameter und Diagnosepunkte bleiben
außerhalb von Suche, Startwerten und Kandidatenauswahl.

Jede Zelle ist eine frische Suche mit `niterations=200`, zwei Populationen,
32 Individuen je Population und 50 Zyklen pro Iteration. Der Vergleich
verwendet die drei bereits bekannten Entwicklungsseeds; sie sind keine
zurückgehaltenen Validierungsseeds. Die Reihenfolge ist zyklisch ausgeglichen:

| Zelle | Seed | Bedingung |
| --- | --- | --- |
| 1 | 20261020 | `baseline` |
| 2 | 20261020 | `time_stretch` |
| 3 | 20261020 | `complexity_frequency` |
| 4 | 20261021 | `time_stretch` |
| 5 | 20261021 | `complexity_frequency` |
| 6 | 20261021 | `baseline` |
| 7 | 20261022 | `complexity_frequency` |
| 8 | 20261022 | `baseline` |
| 9 | 20261022 | `time_stretch` |

Operatoren `+,-,*,/,exp,sin,cos`, Einheitskomplexitäten, Maximalgröße 20,
Float64, serielle deterministische Ausführung, konfiguriertes BFGS mit
20 Iterationen und zwei Neustarts, Parsimony 0 und alle übrigen bisherigen
Vorgaben bleiben
erhalten. Es gibt keine Templates, Wahrheitshinweise, Warmstarts oder
zusätzliche Operatorrestriktionen. Das bisherige Haswell-Profil mit
Threadlimit 1 wird für diese Serie beibehalten und tatsächlich geprüft.
Abhängigkeiten und Backendversionen werden nicht geändert.
Der vorhandene Newton-Sonderpfad des Backends für eine einzelne Konstante
bleibt ebenfalls unverändert.

Gemeinsame Seeds bedeuten keine identischen Mutationsfolgen oder gleichen
Rechenkosten. Callbackzahlen und Laufzeiten werden je Zelle gespeichert;
Callbackzahlen zählen auch Optimiereraufrufe und sind kein Maß für die
Zahl verschiedener Bäume. Zusätzliche Tracing-Plugins werden nicht
zugeschaltet, um die bisherige Suchbedingung nicht weiter zu verändern.

## 5. Originalauswahl, Kurven und physikalische Parameter

Alle exportierten Kandidaten bleiben in ihrer ursprünglichen Reihenfolge
erhalten. Auswahl ist ausschließlich das Minimum der gewöhnlichen
Trainings-MSE mit Komplexität als Gleichstandskriterium. Residuen und MSE
werden für jeden Kandidaten nachgerechnet. Ein interpretierbarerer oder
auf Diagnosepunkten besserer Kandidat ersetzt die Originalauswahl nicht.

Training und Zwischenpunkte werden immer durch den vollständigen
ursprünglichen Baum bewertet: physikalisch ist die Vorhersage
`q(alpha*t)`. Die Koordinatenänderung wird vor der Baumauswertung angewendet;
der Baum wird dafür nicht algebraisch umgeschrieben. Die bisherigen
relativen RMS-/Maximalfehler und Entwicklungsgrenzen bleiben unverändert:
auf beiden Rastern `relative_rms <= 0,001` und `relative_max <= 0,01`.
Nicht endliche oder nicht verfügbare Werte bleiben mit Gründen sichtbar.

Strukturerkennung und Parameterdiagnose des Suchbaums erfolgen zunächst
in seiner eigenen Zeitkoordinate mit `sample_rate_hz=fs_u`. Der originale
Diagnosebefund bleibt erhalten. Eine getrennte physikalische Darstellung
verwendet für verfügbare Felder:

$$
f_t=\alpha f_u,\qquad b_t=\alpha b_u,\qquad
\tau_t=\tau_u/\alpha,\qquad A_t=A_u,\quad\phi_t=\phi_u.
$$

Dasselbe gilt für Aliasfrequenzen, da gleichzeitig `fs=alpha*fs_u` gilt.
Nullpunkt und Zeitrichtung bleiben erhalten. Rohe signierte Frequenz,
Aliasklasse und Diagnosekoordinate werden getrennt ausgewiesen. Die
physikalischen Parameter werden zusätzlich auf dem unveränderten
physikalischen Trainingsraster nachgerechnet. Es gelten die bisherigen
Parametergrenzen und Gates: passende Struktur, abklingender und nichtnuller
Fall, verfügbare nicht degenerierte Aliasklasse sowie bestandene rohe und
Alias-Replays. Die komplexe Amplitude berücksichtigt Vorzeichen und Phase.
Über-/Unterlauf bei einer Umrechnung darf keine positive Markierung erzeugen.

Kurvenqualität, Strukturerkennung und physikalischer Parametermatch bleiben
getrennte Aussagen. `physical_identification` bleibt `not_assessed`.
Unzureichende Erkennerabdeckung darf einen guten Kurvenbefund nicht verdecken.
Das Achtelraster und sein Alias-Blindfleck bei physikalischen Abständen
`8*fs=32768 Hz` bleiben unverändert.

## 6. Verifikation, Artefakte und Abbruch

Vor den Suchläufen müssen feste Referenztests für beide Koordinaten
bestehen: Rasterabbildung, identische Beobachtungsbits, beide analytischen
Referenzbäume, MSE, Einheitenprüfung, Parameter-/Aliasrückrechnung sowie
die beiden bisherigen Alias-Gegenfälle `250+fs` und `250+8*fs`.
Die Tests benutzen weder Fit noch freie Suche. Die fachliche Implementierung
erhält einen eigenen Commit; der freigegebene Plan wird zuvor durch Commit
und SHA-256 eingefroren. Der alte Planhash bleibt unverändert.
Sobald der neue Treiber diesen Plan als Laufzeitdokument konsumiert, muss
er zusätzlich in die entsprechende Ausnahme der CI-Auswahl aufgenommen
werden.

Für jede Zelle werden Budget, Koordinatenfaktor, physikalische und Suchraster,
Anfrage, tatsächliche Backendoptionen und RNG-Angaben gegen die eigene
Bedingung geprüft, einschließlich der ersten Zelle. Die bereits behobenen
Seed-, Options-, Residuen- und Auswahlgegenfälle bleiben Regressionstests.
Ein bedingungsübergreifender Signaturvergleich darf nur bereits einzeln
verifizierte, ausdrücklich geplante Unterschiede ausnehmen.

Ein neuer exklusiver Ausgabeordner enthält alle neun geplanten Zustände,
die eingefrorenen physikalischen Daten, abgeleitete Suchkoordinaten, den
Plan, unveränderte Workerexporte und getrennte physikalische Diagnosen.
Quellen-, Datei-, Plan- und Datenprüfsummen sowie aktuelle Diagnoseherkunft
werden getrennt von den Workeraufnahmen gespeichert und abschließend
erneut geprüft. Vorhandene Ausgaben werden nicht überschrieben.

Bei Infrastruktur- oder Verifikationsfehlern stoppt die Serie; restliche
Zellen bleiben `planned`. Teilstände, Fehlergründe und Originalartefakte
bleiben erhalten. Es gibt keine automatische Wiederholung, Ersatzseeds oder
nachträgliche Reparatur von Verlusten und Auswahlindizes. Abschließende
Verifikationsfehler sperren die bedingungsbezogenen Zusammenfassungen.

## 7. Auswertung und Grenze des nächsten Schritts

Alle neun Auswahlen werden einzeln berichtet. Nur vollständige Bedingungen
mit drei Zellen erhalten deskriptive Minima, Mediane und Maxima mit
sichtbaren endlichen Nennern. Zusätzlich werden Kurvenmarker, Struktur-
und Parametermarkierungen separat gezählt sowie sämtliche Frontkandidaten
nach Struktur und Erstgrund beschrieben. Frontkandidaten sind keine
unabhängigen Wiederholungen. Es gibt keine p-Werte, belastbare
Erfolgswahrscheinlichkeit oder automatische Wahl eines Produktionsprofils.

Der Plan endet nach genau diesen neun Zellen und ihrer gemeinsamen
Auswertung. Bei weiterhin unzureichenden Kurven folgt eine bewusste
Entscheidung über weitere Ursachenprüfung oder Eingrenzung der Methode.
Bei guten Kurven und fehlender Strukturerkennung wird diese Begrenzung
separat untersucht. Ein vielversprechendes Profil muss anschließend mit
eingefrorenen Einstellungen an weiteren Signalparametern und getrennten
Validierungsfällen geprüft werden. Weitere Budgets, kombinierte Varianten
oder Rauschstudien sind keine automatische Fortsetzung dieser Serie.

## Quellen

- [Bisherige Suchparameter und Originalauswahl](../src/ringdown_sr/symbolic.py).
- [Julia-Verlustkern und harte Einheitenprüfung](../julia/src/RingdownSRLoss.jl).
- [Bisherige Fehler- und Parameterdiagnose](../src/ringdown_sr/noiseless_control.py).
- [PySR 2.6.0: Parameterbedeutung und Optionsübergabe](https://github.com/astroautomata/PySR/blob/v2.6.0/pysr/sr.py).
- [SymbolicRegression 2.5.1: Einheitenprüfung](https://github.com/astroautomata/SymbolicRegression.jl/blob/v2.5.1/src/DimensionalAnalysis.jl).
