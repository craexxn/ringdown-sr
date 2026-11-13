# Neustartpakete auf Manjaro: Ergebnis 001

Quellenprüfung und Einordnung vom 13.11.2026, [Leitfadenphase 4](ringdown_recovery_roadmap.md).
Der vorab eingefrorene Vergleich **R: 4 × 1.000 gegen L: 2 × 2.000** ergibt
**`mixed`**. R gewinnt auf der niedrigen Variante einen A-/Familienerfolg;
L hat auf der hohen Variante einen gemeinsamen Erfolg mehr. Auf der hohen
Variante erreichen beide Verfahren in allen vier Blöcken eine A-Kurve.

| Signal | R: A / geplant | R: A plus Originalfamilie | L: A / geplant | L: A plus Originalfamilie |
| --- | ---: | ---: | ---: | ---: |
| anchor | 2/2 | 2/2 | 2/2 | 2/2 |
| variant_low | 2/2 | 2/2 | 1/2 | 1/2 |
| variant_high | 4/4 | 2/4 | 4/4 | 3/4 |

48 frische Suchen liefern **16 Paketausgaben**. Alle geplanten Mitglieder
enden regulär bei 1.000 beziehungsweise 2.000 äußeren Iterationen; keine
Ausfälle, ausgelassenen Mitglieder, historischen Übernahmen oder Nachfits.
Ursprüngliche Zeit t, lokal 300 Optimiereriterationen plus fünf zusätzliche
lokale Neustarts und übrige Optionen bleiben gleich. Die Paketwahl verwendet
ausschließlich den nativen Verlust der ursprünglichen Mitgliedsauswahl,
danach Originalkomplexität und vorab festgelegte Mitgliedsposition.

Diese zwei/zwei/vier gezielt gewählten Blöcke sind bekannte Entwicklungsfälle,
keine neue unabhängige Bestätigung. Die frühere verfehlte 8/10-Grenze bleibt
unverändert. Keine gepoolte Erfolgsquote oder nachträgliche Auswahl zwischen R/L.

## Original und Herkunft

- Original: `restart-budget-manjaro-001.tar.gz`, **27.824.763 Bytes**.
- Selbst bestätigte SHA-256, identisch zur übermittelten Prüfsumme:
  `fbddd9b45061c3668c089217c7194ca01942655de5608bdc2df649f1c87614e6`.
- 3.482 reguläre Dateien, 235.902.915 entpackte Dateibytes. Drei wissenschaftliche
  Abschnitte mit benachbarten `-call.json` und gemeinsamer Verifikation;
  technischer Vorlauf mit zwölf kleinen Workern, Aufrufmessungen und
  Einzel-/Gesamtprüfungen. Archivprogramme und serialisierte Suchzustände
  wurden für diesen Audit nicht ausgeführt.
- Tatsächlicher sauberer Ausführungsstand:
  [`680af98e4342dc831a6dcc995fe658d4fcbe942f`](https://github.com/craexxn/ringdown-sr/commit/680af98e4342dc831a6dcc995fe658d4fcbe942f),
  main nach [PR85](https://github.com/craexxn/ringdown-sr/pull/85).
  Die Ergebnisdokumentation ersetzt diesen Commit nicht.
- [Plan](restart_budget_plan.md), [Konfiguration/Seeds](../data/restart_budget_protocol.json),
  Eingaben und Erzeuger vor Implementierung in
  `2cb96a7fef73a05e6c45564292dbce2c3d7f1583` eingefroren. Originalauswahl,
  Grenzwerte, Beweisressourcen und Anschlussregel unverändert.

| Abschnitt | Beginn, Europe/Vienna | Berichtabschluss, Europe/Vienna | Gemessener vollständiger Aufruf |
| --- | --- | --- | ---: |
| restart-budget-anchor-manjaro-001 | 12.11.2026 18:51:04 | 12.11.2026 19:57:00 | 3.957,284 s |
| restart-budget-low-manjaro-001 | 12.11.2026 19:57:02 | 12.11.2026 21:15:00 | 4.678,543 s |
| restart-budget-high-manjaro-001 | 12.11.2026 21:15:01 | 12.11.2026 23:44:36 | 8.976,619 s |

Lokale Darstellung in MEZ/UTC+1 aus den unveränderten UTC-Metadaten.
Die gemessenen Abschnittsaufrufe ergeben zusammen **17.612,447 s,
4 h 53 min 32 s**, ohne Abschnittspausen, technischen Vorlauf und spätere
Verifikation. Vorbereitung und Veröffentlichung sind enthalten; abschließende
Aufrufdatei und Nachprüfungen liegen außerhalb der gespeicherten Messgrenze.
Diese Aufrufzeiten nicht mit den enthaltenen Fit-/Workerzeiten addieren.

Gemeinsame numerische Umgebung: Manjaro Linux 6.18.55-1, Intel Core i7-1165G7,
CPU-Affinität `[0]`, Julia Default-/Interactive-/GC-Threads 1/0/1, BLAS ein
Thread, Haswell-Kern; Python 3.12.14, Julia 1.13.1, PySR 2.6.0 und
SymbolicRegression 2.5.1. Alle fünf Vorbereitungen binden dieselben 102 Quellen
einschließlich aller 52 Python-Paketdateien an den sauberen Ausführungscommit.

## Paarungen und Grenzen der Originalformeln

| Signal | Block | R: gewählte Zelle, Klasse / Originalfamilie | L: gewählte Zelle, Klasse / Originalfamilie |
| --- | ---: | --- | --- |
| anchor | 1 | 2, A / nachgewiesen | 6, A / nachgewiesen |
| anchor | 2 | 10, A / nachgewiesen | 7, A / nachgewiesen |
| variant_low | 1 | 4, A / nachgewiesen | 6, A / nachgewiesen |
| variant_low | 2 | 12, A / nachgewiesen | 8, B / ungeklärt |
| variant_high | 1 | 3, A / ungeklärt, zusätzlicher Modus | 5, A / Original mit Definitionslücken |
| variant_high | 2 | 10, A / nachgewiesen | 7, A / nachgewiesen |
| variant_high | 3 | 14, A / Original mit Definitionslücken | 17, A / nachgewiesen |
| variant_high | 4 | 22, A / nachgewiesen | 20, A / nachgewiesen |

Die drei hohen A-Ausgaben ohne gültige Originalfamilie haben verschiedene Gründe:

- **R, Block 1, Zelle 3:** zum abklingenden Modus kommt ein oszillierender
  Zusatzterm mit nicht null gesetzter Amplitude `2.1143236978098242e-16`.
  Das Original ist auf dem ganzen Intervall definiert; der Familienstatus
  bleibt `unresolved` mit `multiple_modes_without_nonmembership_proof`.
  Der bestehende Resttermvertrag beweist für eine Ringdown-Komponente eine
  absolute Restobergrenze von rund `2,771e-16`. Der Zusatzterm wird
  weder entfernt noch aufgrund seiner kleinen Größe als exakt null behandelt.
- **L, Block 1, Zelle 5**, und **R, Block 3, Zelle 14:** verschachtelte
  Quotienten der Form Konstante / (Exponentialterm / trigonometrischer Term)
  besitzen jeweils 20 nachgewiesene entfernbare Definitionslücken an Nullstellen
  des inneren Nenners im Prüfintervall.
  Die Originale sind deshalb `proven_nonmember` mit `original_domain_gap`.
  Ihre stetigen Fortsetzungen sind nachgewiesene Ringdown-Familienmitglieder;
  der Restterm ist auf Originaldomain und Fortsetzung exakt null.
  Dies ersetzt nicht die geforderte Gültigkeit der tatsächlich ausgewählten
  Originalformel auf dem geschlossenen Prüfintervall.

Die einzige B-Paketausgabe, L/variant_low/Block 2, ist überall definiert,
besitzt aber eine rationale Hüllkurve; Familiennachweis
`unsupported_normalized_factor`, Restterm ungeklärt. Ihr relativer RMS-Fehler
liegt auf Training und Zwischenpunkten bei rund 0,002 statt höchstens 0,001
für Klasse A. Hier besteht ein Kurvenfehler, kein bloßer Familiennachweisengpass.
Neue physikalische Parameterübereinstimmungen bleiben überall `not_assessed`.

Der vor Beginn begrenzte Frontaudit umfasst alle **538 gespeicherten Kandidaten
in 48 Endfronten**. In keiner der 19 Fronten mit Nicht-A-Originalauswahl liegt
ein anderer A-Kandidat. R/variant_high/Block 1 besitzt eine andere A-/Familienformel
in derselben Front sowie ein anderes gültiges Originalmitglied seines Pakets
(Zelle 4). L/variant_high/Block 1 besitzt eine gültige andere Frontformel;
R/variant_high/Block 3 hat in seinem Paket keine gültige Originalfamilie
nachgewiesen. Diese Befunde ändern keine Originalauswahl. Eine gespeicherte
Endfront ist kein vollständiges Protokoll der Evolution. Alle 538 Originalbäume
haben höchstens 20 Knoten; hier besteht keine zusätzliche Kompositionsgrenze
wie im vorangegangenen u=32t-Versuch.

## Kontinuierliche Fehler der Paketausgaben

Relative RMS-/Maximalfehler der ursprünglichen ausgewählten Formeln, nur für
die Darstellung gerundet. 128 Trainings-, 889 reguläre Zwischen- und 1.024
vorab gebundene unregelmäßige Punkte je Ausgabe. Das Zusatzraster bleibt
diagnostisch, ohne neuen Bestehensmarker oder Ersatz eines Definitionsnachweises.

| Signal / Block / Arm | Training RMS / Max | Zwischenpunkte RMS / Max | Zusatzraster RMS / Max |
| --- | ---: | ---: | ---: |
| anchor / 1 / R | 8.719e-13 / 4.685e-13 | 8.984e-13 / 4.752e-13 | 8.986e-13 / 4.749e-13 |
| anchor / 1 / L | 8.719e-13 / 4.685e-13 | 8.984e-13 / 4.752e-13 | 8.986e-13 / 4.749e-13 |
| anchor / 2 / R | 8.634e-13 / 4.668e-13 | 8.892e-13 / 4.695e-13 | 8.894e-13 / 4.698e-13 |
| anchor / 2 / L | 6.590e-13 / 3.554e-13 | 6.789e-13 / 3.574e-13 | 6.789e-13 / 3.578e-13 |
| variant_low / 1 / R | 4.403e-12 / 4.872e-12 | 4.343e-12 / 4.673e-12 | 4.344e-12 / 4.673e-12 |
| variant_low / 1 / L | 3.718e-12 / 2.182e-12 | 3.768e-12 / 2.175e-12 | 3.769e-12 / 2.175e-12 |
| variant_low / 2 / R | 4.239e-11 / 2.442e-11 | 4.304e-11 / 2.429e-11 | 4.305e-11 / 2.429e-11 |
| variant_low / 2 / L | 2.008e-03 / 2.194e-03 | 1.960e-03 / 2.117e-03 | 1.962e-03 / 2.162e-03 |
| variant_high / 1 / R | 8.331e-12 / 4.444e-12 | 8.621e-12 / 4.605e-12 | 8.623e-12 / 4.598e-12 |
| variant_high / 1 / L | 1.132e-08 / 1.153e-08 | 1.171e-08 / 1.194e-08 | 1.172e-08 / 1.191e-08 |
| variant_high / 2 / R | 3.342e-12 / 2.632e-12 | 3.458e-12 / 2.723e-12 | 3.457e-12 / 2.719e-12 |
| variant_high / 2 / L | 1.302e-12 / 1.194e-12 | 1.309e-12 / 1.182e-12 | 1.309e-12 / 1.183e-12 |
| variant_high / 3 / R | 1.835e-07 / 2.123e-07 | 1.825e-07 / 2.266e-07 | 1.821e-07 / 2.262e-07 |
| variant_high / 3 / L | 1.672e-12 / 1.793e-12 | 1.719e-12 / 1.879e-12 | 1.716e-12 / 1.876e-12 |
| variant_high / 4 / R | 1.611e-12 / 9.525e-13 | 1.668e-12 / 1.007e-12 | 1.668e-12 / 1.005e-12 |
| variant_high / 4 / L | 1.611e-12 / 9.525e-13 | 1.668e-12 / 1.007e-12 | 1.668e-12 / 1.005e-12 |

## Beobachtete Kosten

Alle Mitgliederkosten einschließlich nicht ausgewählter Suchen sind enthalten.

| Signal | Arm | Worker s | Fit s | Adapter s | CPU Nutzer / System s | Verlustcallbacks |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| anchor | R | 2.042,886 | 1.909,853 | 2.057,058 | 2.022,723 / 8,613 | 240.520.440 |
| anchor | L | 1.630,403 | 1.564,441 | 1.637,413 | 1.616,298 / 6,205 | 200.774.036 |
| variant_low | R | 2.266,353 | 2.134,351 | 2.280,780 | 2.245,904 / 8,750 | 274.135.130 |
| variant_low | L | 2.123,456 | 2.057,368 | 2.130,694 | 2.106,667 / 6,479 | 276.978.193 |
| variant_high | R | 4.298,632 | 4.034,434 | 4.327,827 | 4.258,064 / 17,460 | 502.156.059 |
| variant_high | L | 4.096,215 | 3.964,214 | 4.110,725 | 4.063,362 / 13,058 | 513.265.215 |

R benötigt gegenüber L auf anchor/variant_low/variant_high **25,30 % / 6,73 % /
4,94 % mehr Workerzeit**. Die Verlustcallback-Zahlen sind auf anchor 19,80 %
höher, auf low/high dagegen 1,03 % / 2,16 % kleiner. Gleiche Summen äußerer
Iterationen bedeuten somit weder gleiche Workerzeit noch gleiche Callbackkosten.
Insgesamt 2.007.829.073 Verlustcallbacks und 16.457,945 s Workerzeit.
Alle sechs vorgesehenen Kostenfelder sind bekannt. Separate JIT-Zeiten und
ein nativer Gesamtzähler aller Evaluierungen sind nicht beobachtet; Callback-
Aufrufe nicht damit gleichsetzen. Kosten ändern die eingefrorene Entscheidung nicht.

## Tatsächlich ausgeführte Prüfung

Der unveränderte vollständige CLI-Gesamtverifikator auf dem exakten sauberen
Ausführungscommit bestätigt alle 48 wissenschaftlichen Zellen, 16 Paketausgaben,
Originalauswahlen, Herkunft, Eingaben, effektive Optionen, Iterationsabschlüsse,
Kosten und gemeinsame Umgebung. **Alle drei wissenschaftlichen Exportdateien
sind bytegleich** zum gelieferten Gesamtexport; keine neuen Suchaufrufe.

Die zwölf technischen Vorlaufworker sind separat bestätigt: beide Einzelprüfungen
über die reguläre CLI, die Gesamtprüfung über die unveränderte öffentliche
Funktion `restart_budget.verify(..., complete=True)`, wie im technischen Treiber.
Die wissenschaftliche Serien-CLI verlangt genau drei Quellen und kann die zwei
Fixtures nicht direkt annehmen. **Alle neun technischen Exportdateien sind
bytegleich**, vier technische Paketausgaben; keine neue wissenschaftliche
Entscheidung aus diesen Fixtures. Gemessene ursprüngliche technische
Abschnittsaufrufe 413,655 s und 398,243 s, Verlustcallbacks 85.038 und 62.355.

Alle fünf Vorbereitungen sowie sämtliche 102 gebundenen Quellen einschließlich
aller 52 Python-Paketdateien gegen Git und den sauberen Checkout geprüft.
Originalarchiv und alle 3.482 Dateien vor/nach der Prüfung unverändert.
Ein erster lokaler Leseversuch scheiterte vor der Verifikation am schreibgeschützten
Julia-Logcache. Mit ausschließlich dafür ergänztem Schreibrecht bestand die
unveränderte Prüfung; der gesperrte erste Versuch bleibt im Audit erhalten.
Dies ist weder ein wissenschaftlicher Abbruch noch eine Wiederholung der Suchen.

Unabhängige Nachzählung aus nativen Workerdateien bestätigt alle 48 Frontauswahlen,
16 Paketwahlen, 32 Seeds, acht Paarungen, 32 × 1.000 und 16 × 2.000 reguläre
Abschlüsse sowie alle sechs Pflichtkostenfelder. Die 32 neuen Seeds sind zusätzlich
gegen sämtliche 150 früheren Bestätigungssuchen disjunkt abgeglichen. Ein weiterer
Auswahl-/Bindungsaudit prüft 7.109 Bedingungen und 440 Originaldateien.

Zusätzlicher Frontaudit: sämtliche 538 ergänzenden Bewertungen mit unveränderten
Verträgen kanonisch JSON-identisch nachgerechnet. Ein eigener rekursiver
Float64-JSON-Baum-Replay mit Fehlernormen in Long-double-Präzision bestätigt
die Klassen aus Training und Zwischenpunkten sowie die kontinuierlichen Fehler
auf allen drei Rastern. Maximale
Metrikabweichung geteilt durch `max(1, |gespeicherter Wert|, |eigener Wert|)`:
`2,22 × 10⁻¹⁶`. Keine neue Familien- oder Parameterbeweisregel und keine Fits.

Die Implementierung ist nach vollständiger [CI 43213172104](https://github.com/craexxn/ringdown-sr/actions/runs/43213172104)
übernommen: 3.525 Pythonfälle, sämtliche nativen Prüfblöcke und zwölf neue
kleine Kontrollworker mit Einzel-/Gesamtprüfung bestanden. Alle drei Joblogs
bestätigen Checkout `0593b0883f553293553923334f994e2e22cb0cf9`; dessen Baum
`ae4b5ca05741d5be69d5c04273fb562de1f5932a` entspricht dem tatsächlichen
Ausführungsmerge. Diese technische Abnahme ist vom wissenschaftlichen Befund
und seiner lesenden Verifikation getrennt.

## Einordnung und nächster abgegrenzter Schritt

Die vier A-Ausgaben beider Verfahren auf der zuvor schwierigen hohen Variante
sind ein positiver beobachteter Kurvenbefund. Die verbleibende Differenz liegt
hier bei der Gültigkeit beziehungsweise dem Nachweis der Originalfamilie.
Wegen neuer Seeds, anderer Budgets und Paketauswahl folgt daraus keine kausale
Verbesserung gegenüber früheren 4 × 500 oder 1 × 2.000 und keine allgemeine
Erfolgswahrscheinlichkeit. Vorhandene gute Kandidaten sind keine zusätzlichen
Algorithmusergebnisse; Originalauswahlen und alle Kosten bleiben erhalten.

Die Richtungsregel bleibt **gemischt**: R gewinnt auf der niedrigen Variante,
L weist auf der hohen einen zusätzlichen gemeinsamen Erfolg auf. Eine rein
kurvenbasierte oder um Fortsetzungen erweiterte Erfolgsregel wäre eine neue
Auswertung; sie ersetzt nicht nachträglich den eingefrorenen Endpunkt.
Die bisherigen 8/10-Bestätigungsbefunde und ihre negative Entscheidung bleiben
unverändert. u=32t ist hier nicht untersucht und bleibt ein separater offener
Entwicklungsbefund, weder bestätigt noch verworfen.

Nach diesem begrenzten Entwicklungszyklus folgt gemäß Plan die Einordnung
mit der Betreuung: ausdrücklich ein Profil und den Anspruch einer unabhängigen
Bestätigung auf unberührten Fällen festlegen oder die erreichbare Aussage
begrenzen. Keine automatische neue Iterationsstaffel, zusätzliche Seedrunde,
dritte Suchintervention oder Freigabe des Rauschpiloten. Ein weiterer begrenzter
Koordinatenabgleich wäre gesondert zu begründen und vor Ausführung festzulegen.
Vor einem späteren Rauschpilot das ausgewählte Profil bewusst in den allgemeinen
Laufweg übernehmen; die Gewichtung muss Struktur- und Konstantensuche bestimmen.

Original und getrenntes Auditpaket sind im [Ergebnisindex](results_index.md#lesende-verifikation-des-neustartpaketvergleichs-001)
zugeordnet; Paket-Rücklesen gegen alle 137 Dateien und das Auditmanifest bestanden.
Gemeinsame dauerhafte Archivablage und unabhängig SHA-256-geprüfte
Zweitkopien bleiben gemäß [Archivregel](results_archiving.md) offen. Arbeitskopien
sind kein Sicherungsnachweis; GitHub-Uploads sind optional.
