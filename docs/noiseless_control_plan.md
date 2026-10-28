# Methodenplan: rauschfreier Kontrollversuch der freien SR-Suche

Stand: 28.10.2026. **Entwurf zur unabhängigen Methodenprüfung vor der
Implementierung.** Dieser PR enthält Dokumentation. Der beschriebene
Kontrolltreiber und seine Versuche sind noch nicht implementiert oder ausgeführt.

Der Plan ergänzt den [SR-Methodenplan](symbolic_regression_method_plan.md),
den [Parameterinterpretationsplan](parameter_interpretation_plan.md) und den
[Entscheidungsvermerk zur Wiederholbarkeit](reproducibility_decisions.md).
Technische Bezugsbasis ist `5ec4c791de88a1d5e8ee51a18e71ef03b594111f`.
Eine Implementierung erhält einen eigenen geprüften Commit und eigene Herkunft.

## 1. Fragestellung und begrenzter Anspruch

**Fragestellung:** Welche Trainings- und Zwischen-Sample-Fehler sowie welche
Struktur- und Parameterdiagnosen liefert der unveränderte freie Suchansatz bei
einem eingefrorenen rauschfreien Ein-Moden-Signal, wenn ausschließlich das
nominelle Iterationsbudget über drei vorab festgelegte Suchstarts variiert wird?

Motivation ist die vom Nutzer am 28.10.2026 übermittelte Manjaro-Terminalausgabe:
20 AR(1)- und 27 Weißrauschkandidaten, davon 0 im begrenzten Muster erkannt.
46 erste Ablehnungsgründe waren `exponential_factor_count`, einer
`cosine_factor_count`. Die Auswahlformeln umfassten verschachtelte Funktionen
und rationale Zeitargumente. Dies ist eine Abdeckungsangabe des Erkenners,
keine allgemeine Rekonstruktionsquote und keine Auswertung unabhängiger
47 Experimente. Die übermittelten Exportprüfsummen wurden lokal als
bestanden gemeldet; die vollständigen Dateien wurden hier nicht erneut
unabhängig ausgelesen. Dieser Plan setzt keine bestätigte WSL2-Parameterdiagnose
voraus und erklärt keine historischen Rechnerunterschiede.

Der Versuch ist eine kleine Entwicklungsdiagnose mit einem Signal und drei
Seeds. Er untersucht keine Leistungsüberlegenheit der Kovarianzgewichtung,
keine SNR-Reihe, keine belastbare Erfolgswahrscheinlichkeit und keine
physikalische Identifikation. Der Vergleich mit den früheren verrauschten
Läufen wäre kein isolierter Rauscheffekt: Es handelt sich um eine neue
Kontrollbedingung. Hauptversuche und wissenschaftliche Formelauswahl bleiben
gesonderte Methodenentscheidungen.

## 2. Einmalig eingefrorene Daten

| Größe | Vorgeschlagener fester Wert |
| --- | --- |
| Amplitude `A0` | `1`, dimensionslos |
| Frequenz `f0` | `250 Hz` |
| Abklingzeit `tau0` | `0.008 s` |
| Phase `phi0` | `0 rad` |
| Abtastrate `fs` | `4096 Hz` |
| Anzahl Trainingssamples `N` | `128` |
| Trainingszeiten | `t[j] = j/fs`, `j = 0,...,127` |
| Hinzugefügtes Rauschen | keines; kein Rausch-RNG |
| SR-Eingaben | ausschließlich `time_s` und `observed = h0(time_s)` |
| Gewichtung | gewöhnliche MSE, `covariance=None` |

Das reelle Referenzsignal lautet

$$
h_0(t)=A_0 e^{-t/\tau_0}\cos(2\pi f_0t+\phi_0).
$$

Die Trainingsachse reicht von `0` bis `127/4096 = 0.031005859375 s`.
Das Samplingfenster hat die Dauer `N/fs = 0.03125 s` mit ausgeschlossenem
rechten Rand. Diese beiden Angaben werden nicht verwechselt.

Die bestehenden Funktionen `sample_times` und `ringdown_signal` erzeugen
die Float64-Referenz genau einmal auf dem Referenzrechner. Danach werden die
Arrays gespeichert, mit Form, dtype und kanonischen Little-Endian-Float64-
Bitprüfsummen identifiziert und für alle neun Suchen unverändert verwendet.
Kein Suchworker erzeugt das Signal erneut. Analytische Parameter und
Float64-Generierungsweg werden gemeinsam dokumentiert; sie werden nicht
als exakt dieselbe reelle Funktionsauswertung ausgegeben.

Es gibt keine Kovarianzschätzung, Hintergrundfenster oder klassischen Fits.
Bei exakt verschwindender Rauschvarianz wäre die wahre Rauschkovarianz
singulär. Eine künstliche Einheits- oder epsilon-Kovarianz würde einen unnötigen
Gewichtungs-/Rechenpfad einführen und wäre kein wahrer Nullrausch-Kovarianzarm.
Sie ist hier nicht vorgesehen.

Die ursprünglichen Signalparameter, spätere Diagnosepunkte und die
Strukturerkennung erreichen den Suchworker nicht. Der Worker erhält die
Zeitvariable weiterhin in Sekunden mit `X_units=["s"]` und `y_units="1"`.
Die bekannte Referenz dient der Datenerzeugung und nachgelagerten Diagnose,
nicht als Startformel oder Grundlage einer Neuauswahl.

## 3. Suchraum und Suchbedingungen

Der bestehende `run_search_arm`-Pfad bleibt die Suchgrundlage.
Außer `seed` und `niterations` gelten dieselben Vorgaben für alle neun Läufe:

| Merkmal | Unveränderte Vorgabe |
| --- | --- |
| Binäre Operatoren | `+,-,*,/` |
| Unäre Operatoren | `exp,sin,cos` |
| Maximalgröße | `maxsize=20`; vorhandenes Knotenmaß |
| Zeitdarstellung | Sekunden; keine neue Zeit- oder Zielskalierung |
| Strukturvorgabe | keine Vorlage, keine vorgeschriebene Ringdown-Grammatik |
| Anfangsformeln | `guesses=None` |
| Fortsetzung | `warm_start=False`; frischer Worker je Zelle |
| Präzision | Float64; `precision=64` |
| Ausführung | `parallelism="serial"`, `deterministic=True` |
| Konstantenoptimierung | BFGS, 20 Optimiereriterationen, 2 Neustarts |
| Zusätzliche Komplexitätsgewichte | `parsimony=0`; beide Häufigkeitsmechanismen aus |
| Populationen / Größe / Zyklen | `2 / 32 / 50` |
| Zusätzliche Strukturbeschränkungen | `constraints=None`, `nested_constraints=None` |
| Weitere Beschleunigung | `turbo=False`, `bumper=False` |
| Abbruch im Suchalgorithmus | `early_stop_condition=None`, `timeout_in_seconds=None`, `max_evals=None` |
| Nachträgliche Beispielauswahl | kleinster Trainingsverlust, dann kleinste Komplexität |

Die vollständigen angeforderten und effektiven PySR-/Backendoptionen werden
gespeichert und abgeglichen. Verbleibende Bibliotheksdefaults gelten
ausschließlich in den gesperrten Versionen; aktuelle Online-Defaults ersetzen
keine Projektvorgabe. Physikalische Zusatzstrafen, neue Operatorrestriktionen,
Reskalierung, Startpopulationen mit der wahren Formel und ein Ausbau des
Erkenners gehören nicht zu dieser Intervention.

Der Formelsuchraum enthält die Referenzstruktur grundsätzlich, schreibt
sie aber nicht vor. Beispielsweise ist ein Baum aus äußerem Vorfaktor,
Exponentialfaktor und Kosinusfaktor bei Phase null mit 11 Knoten darstellbar.
Die konkrete Float64-Baumauswertung bleibt von der Daten-Generierungsreihenfolge
getrennt; Darstellbarkeit beweist weder exakte numerische Gleichheit noch,
dass die Suche diese Struktur unter den vorgesehenen Budgets finden muss.

## 4. Neun vorab festgelegte Läufe

Nur `niterations` wird als Budgetfaktor variiert:

- B0: `10`, bisheriges nominelles Ausgangsbudget.
- B1: `50`.
- B2: `200`.

Die drei Suchseeds sind `20261020`, `20261021` und `20261022`.
Sie sind eine kleine feste Auswahl von Suchstarts, keine Poweranalyse oder
Garantie statistischer Unabhängigkeit. Derselbe Seed wird für die drei
Budgetstufen verwendet; reale Backend-Seeds werden zusätzlich gespeichert.

| Reihenfolge | Suchseed | niterations |
| ---: | ---: | ---: |
| 1 | 20261020 | 10 |
| 2 | 20261020 | 50 |
| 3 | 20261020 | 200 |
| 4 | 20261021 | 50 |
| 5 | 20261021 | 200 |
| 6 | 20261021 | 10 |
| 7 | 20261022 | 200 |
| 8 | 20261022 | 10 |
| 9 | 20261022 | 50 |

Alle Suchen starten sequenziell in frischen Prozessen. Die zyklische
Reihenfolge verteilt jede Budgetstufe einmal auf jede Position innerhalb
eines Seedblocks. Sie entfernt keine JIT-, Cache- oder Temperatureffekte;
aus den Zeiten wird deshalb kein reiner Algorithmus- oder Hardwarevergleich.

Ein großer Lauf ist keine Fortsetzung des kleinen. Ein gemeinsamer Seed
garantiert keinen identischen Suchpräfix bei anderem `niterations`.
Insbesondere können budgetabhängige Abläufe unterschiedliche Trajektorien
erzeugen; die Verluste müssen zwischen frischen Budgetläufen nicht monoton
fallen. Nominale Iterationen sind keine gemessenen Funktionsauswertungen
oder identischen Rechenkosten.

Es gibt keine datengesteuerte Erweiterung auf zusätzliche Seeds oder
Budgetstufen, kein Stoppen der Serie bei der ersten schönen Formel und keine
Auswahl des besten Seeds als Gesamtergebnis. Falls die Serie aus
Ressourcengründen abgebrochen wird, bleiben geplante, gestartete, vollständige,
fehlgeschlagene und abgebrochene Zellen getrennt. Es wird keine vollständige
Neun-Läufe-Auswertung behauptet. Verdeckte Wiederholungen oder Ersetzungen
ungünstiger Ergebnisse sind ausgeschlossen.

## 5. Numerisches Referenzprofil dieses Kontrollversuchs

**Zur Abnahme vorgeschlagen:** der vorhandene Manjaro-Rechner, auf dem die
Haswell-Kontrolle bereits ausgeführt wurde, mit bestätigtem Haswell-Kern
für NumPy, SciPy und Julia und Poollimits 1.

`OPENBLAS_CORETYPE=Haswell` und `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`,
`MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` jeweils `1` gelten vor Prozessstart.
Vor `fit` und nach dem Suchergebnisexport werden die tatsächlich geladenen
Bibliotheken mit den bestehenden Kontrollfunktionen geprüft und gespeichert.
Die reine Anwesenheit der Variablen genügt nicht. Alle neun Zellen müssen
dasselbe geprüfte Profil verwenden; fehlgeschlagene Kontrollen sind
Ausführungsfehler und werden nicht still mit einem anderen Kern fortgesetzt.

Das ist eine Vorgabe für diesen begrenzten Kontrollversuch, keine globale
Haswell-Umstellung und keine Festlegung des späteren Hauptversuchsprofils.
CPU-native Routinen bleiben verfügbar. Ein nativer oder zweiter Rechner
wird hier nicht als zusätzlicher Faktor zugemischt. Eine spätere gepaarte
Robustheitskontrolle ist gesondert zu planen. Laufzeitversionen und Projekt-
/Treiberquellen werden vor der Serie eingefroren; Wechsel während der Serie
erzeugen einen neuen Kontrollstand.

## 6. Nachgelagerte Bewertung

Zuerst werden vollständige Front und bestehender Auswahlindex eingefroren.
Danach erhalten alle Kandidaten Diagnosen; die ausgewählte Formel wird
zusätzlich gesondert berichtet. Die folgenden drei Bewertungen bleiben getrennt.

### 6.1 Kurvengenauigkeit

Für das Trainingsraster und das nachfolgend festgelegte Diagnoseraster
werden jeweils aus Originalbaum-Vorhersagen `p` und Referenzwerten `h0`
berechnet:

$$
E_{\mathrm{rms}} =
\sqrt{\frac{\sum_i (p_i-h_{0,i})^2}{\sum_i h_{0,i}^2}},
\qquad
E_{\max} =
\frac{\max_i |p_i-h_{0,i}|}{\max_i |h_{0,i}|}.
$$

Die Nenner verwenden ausschließlich das Referenzsignal, keine Kandidaten-
amplitude und keine absolute Untergrenze. Sie sind für diesen festen
nichtnullen Kontrollfall positiv. Die Berechnung muss gegen Überlauf
abgesichert sein; nicht endliche Vorhersagen werden nicht durch Kappung
oder Ersetzen zu endlichen Gütewerten. Kennzahlen sind dann `null` mit
diagnostischem Grund. Ein ungültiger Baum ist dagegen ein Eingabefehler.

**Zur Abnahme vorgeschlagene Entwicklungsmarkierung:** beide Raster müssen
endliche Werte, `E_rms <= 1e-3` und `E_max <= 1e-2` liefern. Dies bezeichnet
0,1 % relativen RMS-Fehler und höchstens 1 % relativen
Maximalfehler auf den jeweiligen endlichen Gittern. Die Werte sind bewusst
vorab vorgeschlagene technische Auflösungsziele im rauschfreien Pilot,
keine physikalischen Unsicherheiten oder Kriterien der Hauptstudie.
Kontinuierliche Fehlerwerte werden unabhängig von dieser Markierung berichtet.
Toleranzen werden nach Sichtung der Ergebnisse nicht nachträglich gelockert.

Die technischen Originalbaum-/Julia-Replaytoleranzen bleiben unverändert
und sind kein Ersatz für diese Kurvengütemaße.

### 6.2 Begrenzte Strukturerkennung

Der vorhandene Erkenner bleibt unverändert. Berichtet werden:

- Anzahl und Anteil `recognized` / `not_supported` pro Front.
- Erste Ablehnungsgründe und vollständige Kandidatenzuordnung.
- Strukturzustand der ursprünglichen Auswahl.
- Gesondert `decaying/undamped/growing` und `zero/nonzero`, sofern erkannt.
- `front_has_recognized` als reine Abdeckung, ohne neuen Auswahlindex.

`recognized` allein bescheinigt keine Dämpfung oder physikalische
Identifikation. Eine algebraisch gleichwertige Sinusform kann weiterhin
außerhalb des begrenzten Musters liegen. Ein Ergebnis von null erkannten
Strukturen wird nicht automatisch als null Rekonstruktionsleistung ausgegeben.

### 6.3 Parameterdiagnose und Aliasklasse

Die vorhandene Parameter-/Aliasdiagnose wird auf dem ursprünglichen
Trainingsraster ausgeführt. Originalparameter, Rohreplay, Aliasstatus,
Aliasreplay und Degenerationen bleiben getrennt erhalten.

Eine vergleichende Parametermarkierung wird nur beurteilt, wenn die Struktur
erkannt, die Form abklingend, die Amplitude exakt nicht null und alle
benötigten Felder numerisch verfügbar sind, beide Parameter-Replays bestehen
und die Aliasdiagnose `available` ohne DC-/Nyquist-Degeneration liefert.
Sonst lautet sie `not_assessed` mit Grund; vorhandene Teilinformationen
werden trotzdem berichtet.

Für beurteilbare Kandidaten werden vorgeschlagen:

$$
e_f = |f_{\mathrm{alias}}-f_0|/f_0,
\quad
e_\tau = |\tau-\tau_0|/\tau_0,
\quad
e_A = \bigl||A|-A_0\bigr|/A_0,
$$

$$
z=A e^{i\phi_{\mathrm{alias}}},\quad
z_0=A_0e^{i\phi_0}=1,\quad
e_z=|z-z_0|/A_0.
$$

Die gemeinsame komplexe Amplitude berücksichtigt die Vorzeichen-/Phasen-
mehrdeutigkeit: etwa `A=-1, phi=pi` beschreibt dieselbe Schwingung wie
`A=1, phi=0`. Der Export wird dazu weder positiviert noch umgeschrieben;
die Kennzahl verwendet die vorhandenen verfügbaren numerischen Felder.

**Zur Abnahme vorgeschlagene Markierung `matched`:** `e_f <= 1e-3` sowie
`e_tau, e_A, e_z <= 1e-2`. Sind alle erforderlichen Angaben beurteilbar,
aber mindestens eine Grenze überschritten, lautet sie `mismatched`.
Die kontinuierlichen Abweichungen werden zusätzlich ausgegeben.
Die Diagnosearithmetik muss auch hier gegen Über-/Unterlauf abgesichert sein;
für die komplexe Distanz ist eine skalierte Norm beziehungsweise `hypot`
geeignet. Ist eine benötigte Abweichung nicht verlässlich numerisch verfügbar,
lautet die Markierung `not_assessed` mit Grund und dem betroffenen Wert `null`.
Solche Fälle dürfen nicht durch Nullwerte als passend erscheinen.
Diese Grenzen sind vorläufige Entwicklungsauflösungen, keine Konfidenzintervalle.

Eine passende Aliasklasse beweist keine eindeutige ursprüngliche Frequenz.
Deshalb werden rohe signierte Frequenz und Aliasfrequenz gemeinsam berichtet,
und `physical_identification` bleibt `not_assessed`. Es gibt keinen
zusammengezogenen wissenschaftlichen Erfolgswert aus den drei Bewertungen.

## 7. Festes Zwischen-Sample-Raster

Zusätzlich wird das Signal einmalig auf den sieben inneren Achtelstellen
jedes Trainingsintervalls gespeichert:

$$
u_{j,m}=(j+m/8)/f_s,\qquad
j=0,\ldots,126,\quad m=1,\ldots,7.
$$

Das sind `127*7=889` Punkte strikt zwischen vorhandenen Trainingszeiten.
Sie überschneiden sich nicht mit dem Trainingsraster und liegen vollständig
innerhalb `[0,127/fs]`. Referenzwerte entstehen aus der analytischen
Signalfunktion, nicht aus einer Interpolation der Trainingswerte.

Nur die nachgelagerte Diagnose erhält dieses Raster und seine Referenzwerte.
Es steuert weder Suchverlust noch Auswahl, Seedwahl, Nachoptimierung,
Abbruch oder Rangfolge der Front. **Ausgewertet wird der vollständige
Originalbaum in seiner ursprünglichen binären Reihenfolge**, nicht die
nachträglich reduzierte Aliasform.

Beispiel: `250 Hz` und `4346 Hz = 250 Hz + fs` können auf dem
Trainingsraster dieselbe Schwingung ergeben; auf inneren Achtelstellen
unterscheiden sie sich. Ein Austausch durch die passende Aliasform würde
diesen Unterschied verdecken. Aliasreplay auf Trainingszeiten und
Originalbaum-Prüfung zwischen Samples sind verschiedene Nachweise.

Nicht endliche Zwischenwerte und große Fehler werden gesondert sichtbar.
Ein bestandenes endliches Gitter beweist jedoch keine Singularitätsfreiheit
zwischen sämtlichen reellen Zeitpunkten. Dieser begrenzte Versuch führt
keinen allgemeinen analytischen Polstellenprüfer ein und erklärt solche
Ausdrücke nicht allein aufgrund endlicher Rasterwerte für physikalisch zulässig.

Das Diagnoseraster ist weder ein unabhängig gezogenes Testsignal noch ein
Rausch- oder astrophysikalischer Generalisierungsnachweis. Jede nachfolgende
Methodenänderung nach Sichtung dieser Entwicklungsdiagnose benötigt später
eine davon getrennte Abschlussbewertung mit vorab festgelegten Daten.

## 8. Auswertung, Artefakte und technische Abnahme

Pro Budget werden alle drei Suchstarts mit ihren Einzelwerten gezeigt.
Für endliche Kurvenfehler sind Minimum, Median und Maximum als rein
deskriptive Angaben vorgesehen. Unterstützungs- und Markierungszahlen
werden als ganze Zahlen mit ihrer beurteilbaren bzw. geplanten Bezugsmenge
angegeben. Fehlende/abgebrochene Zellen bleiben sichtbar; eine unvollständige
Serie erhält keine vollständige Drei-Seeds-Zusammenfassung. Frontkandidaten
werden nicht als unabhängige Wiederholungen gezählt. Es gibt keine p-Werte,
keine Erfolgswahrscheinlichkeits-Schätzung aus drei Starts und keine
automatische Festlegung eines Produktionsbudgets.

Gespeichert werden mindestens:

| Ebene | Erforderliche Inhalte |
| --- | --- |
| Gesamtplan | Abgenommener Plan-/Implementierungscommit, Konfiguration, feste Reihenfolge und vollständige geplante Zellliste |
| Eingaben | Einmalige Float64-Trainings- und Diagnoseraster samt Referenzarrays, Generatorherkunft und Prüfsummen |
| Suchzelle | Bestehender Workerexport mit vollem Baum, hexadezimalen Konstanten, sämtlichen Kandidaten, Originalauswahl, Request und tatsächlichen Optionen |
| Numerik | Originale Eltern-/Workerherkunft und kontrollierte Bibliotheksaufnahmen vor Fit/nach Suche |
| Diagnosen | Kandidatenindex/-Quellhash, vorhandene Parameteranalyse, getrennte Kurvenmaße und Parametermarkierungen, Gründe fehlender Werte |
| Zusammenfassung | Lesbare Tabelle, maschinenlesbarer Bericht, alle Laufzustände und getrennte Diagnoseumgebung/-quellen |

Die neue Orchestrierung nutzt einzelne gewöhnliche Sucharme und benötigt
keine Erweiterung von Schema 3 um eine singuläre Nullrauschkovarianz.
Ein neuer Gesamtbericht ist ausdrücklich vom bestehenden
`ringdown-sr-parameter-diagnostics-1`-Export für vollständige gespeicherte
Schema-3-Läufe zu unterscheiden. Bestehende Formate und Dateien bleiben erhalten.

Technische Abnahme der späteren Implementierung umfasst:

1. Exakte Zugehörigkeit der neun Zellen, Datenidentität, Parameter-/Seedtreue
   und frische Worker ohne Fortsetzung.
2. Strikte Trennung von Trainingsdaten und Diagnosegittern; veränderte Wahrheit
   oder Diagnosen dürfen die gespeicherte Auswahl nicht ändern.
3. Geprüfte Haswell-/Poolbedingungen und vollständige Herkunft, einschließlich
   anfänglicher und abschließender Aufnahmen.
4. Unabhängige Referenzen für Rasterzahl/-grenzen, normierte Fehler und
   Vorzeichen-/Phasenmehrdeutigkeit; unveränderte alte Aliasreferenzen.
5. Gegenfälle mit passendem Alias auf dem Trainingsraster, aber anderem Verlauf
   zwischen Samples; fehlgeschlagene, nicht endliche und nicht beurteilbare
   Diagnosen bleiben unterscheidbar.
6. Exklusive Ausgaben, Quellen-/Eingabeprüfsummen und erhaltene Artefakte bei
   Fehlern oder Abbrüchen über die bestehenden Prozess-Behandlungspfade.
7. Regression der vorhandenen Suche, Auswahl, Parameterdiagnose und Ergebnisformate.

Das Auffinden der Zielstruktur ist **kein Bestehenskriterium der
Softwaretests**. Auch null passende Strukturen oder null passende Kurven
sind zulässige fachliche Ergebnisse einer technisch vollständig ausgeführten
Serie. Kein Test wird durch Erzwingen der wahren Formel oder nachträgliche
Toleranzänderung grün gemacht.

## 9. Review, Implementierung und spätere Entscheidungen

Vor der Implementierung sind durch das unabhängige Astra-Review zu prüfen:

- Reicht diese isolierte Bedingung aus, um die Budgetfrage sinnvoll zu erkunden?
- Sind Datenzugriff, eingefrorene Auswahl, Diagnosegitter und Aliasvergleich
  methodisch sauber getrennt?
- Sind neun Suchen, die drei Budgetstufen und das numerische Profil für diese
  Entwicklungsdiagnose angemessen begrenzt?
- Sind die ausdrücklich vorgeschlagenen Kurven- und Parameterauflösungen
  geeignet und korrekt als Entwicklungsmarkierungen eingeordnet?
- Werden Formabdeckung, numerische Konsistenz, Aliasklasse und physikalische
  Identifikation hinreichend auseinandergehalten?
- Sind Abbruchfälle und unvollständige Serien ohne Ergebnisverzerrung auswertbar?

Nach Methodenabnahme folgt ein eigener Implementierungs-PR mit passenden
Prüfungen. Erst danach werden die vereinbarten Kontrollläufe ausgeführt.
Implementierung und Schlussfolgerungen erhalten anschließend ein separates
Review. Die bestehende Repository-CI kann bei diesem Dokumentations-PR ihre
bisherigen Regressionstests ausführen; dies sind keine Ausführungen des
hier geplanten neuen Kontrollversuchs.

Ein Ausbau um Sinusformen, neue physikalische Grammatikbeschränkungen,
Ziel-/Zeitskalierung, Komplexitätsstrafen, mehr Budgets oder weitere
Kontrollsignale ist ein späterer gesonderter Methodenbeschluss.
Die aktuelle Fragestellung wird dadurch nicht stillschweigend erweitert.

## Quellen und Prüfumfang dieses Entwurfs

- Projektstand `5ec4c7`: [Signalfunktionen](../src/ringdown_sr/signals.py),
  [Suchadapter](../src/ringdown_sr/symbolic.py),
  [Suchbudget](../src/ringdown_sr/config.py) und
  [bestehende Kernkontrolle](../scripts/repeat_symbolic_arm.py).
- [Parameter-/Aliasdiagnose](parameter_diagnostics.md) und
  [lesender Export](parameter_export.md).
- [PySR 2.6.0, Python-Quelle](https://github.com/astroautomata/PySR/blob/v2.6.0/pysr/sr.py)
  als Versionsbezug der bestehenden Projektentscheidungen.
- [Offizielle PySR-API](https://ai.damtp.cam.ac.uk/pysr/api) zur allgemeinen
  Bedeutung von Iterationsbudget, Neustarts und Auswahl; deren aktuelle
  Defaults werden nicht in das gesperrte Projekt übernommen.

Gegen den über die GitHub-Verbindung gelesenen Projektstand wurden die
bestehenden Suchvorgaben und Schnittstellen abgeglichen. Rasterzählung,
Budget-/Seedzuordnung und relative Dokumentationslinks werden für den
Dokumentationsentwurf gesondert geprüft. Wegen nicht mehr verfügbarer
lokaler Ausführungsumgebung wurden dafür keine Python-/Julia-Projekttests,
freien Suchen oder neuen Kontrollläufe ausgeführt.
