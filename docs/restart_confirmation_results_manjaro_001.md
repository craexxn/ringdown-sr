# Unabhängige Neustartbestätigung auf Manjaro: Ergebnis 001

Quellenprüfung und Einordnung vom 12.11.2026, [Leitfadenphase 6](ringdown_recovery_roadmap.md).
Alle 150 geplanten Suchversuche sind abgeschlossen und lesend bestätigt.
Die vorab beschlossene praktische Grenze für das Neustartprofil ist **nicht
erreicht**: R erzielt 8/10, 10/10 und 4/10 gemeinsame A-/Originalfamilienerfolge;
gefordert sind mindestens 8/10 auf **jedem** Signal. Der negative Befund ist
kein technischer Abbruch. Alle drei Abschnitte und sämtliche Ausfälle bleiben
in der Auswertung; hier gab es keine ausgefallenen oder ausgelassenen Suchen.

| Signal | I: A / geplant | I: A plus Originalfamilie | R: A / geplant | R: A plus Originalfamilie | R erreicht 8/10 gemeinsam |
| --- | ---: | ---: | ---: | ---: | --- |
| anchor | 5/10 | 4/10 | 10/10 | 8/10 | Ja |
| variant_low | 7/10 | 5/10 | 10/10 | 10/10 | Ja |
| variant_high | 7/10 | 7/10 | 4/10 | 4/10 | Nein |

I ist eine frische Suche mit 2.000 äußeren Iterationen, R ein Paket aus vier
frischen 500er-Suchen. Jedes Paket liefert genau eine verlustbasiert ausgewählte
Ausgabe. 150 Suchversuche ergeben somit 60 Algorithmusergebnisse, keine 150
unabhängigen Paketbewertungen. Lokal bleiben 300 Optimiereriterationen und
**fünf zusätzliche lokale Neustarts** wirksam; dies sind keine vier globalen Suchen.

R verbessert die A-Zahl bei Anker und niedriger Variante, verschlechtert sie
aber bei der hohen Variante. Dort sind alle A-Ausgaben zugleich als gültige
Originalfamilie nachgewiesen; der Verlust lässt sich daher nicht mit offenen
Familienbeweisen erklären. Die Signale ändern mehrere Parameter gleichzeitig.
Aus diesem Vergleich folgt keine isolierte Frequenz-, Dämpfungs- oder
Amplitudenursache und kein allgemeiner Vorteil globaler Neustarts.

## Original, Herkunft und eingefrorene Bedingungen

- Original: `restart-confirmation-manjaro-001.tar.gz`, **81.098.904 Bytes**.
- Aus den drei unveränderten Teilen `part-000`, `part-001`, `part-002` in dieser
  Reihenfolge zusammengesetzt; kein neues Packen der Originalinhalte.
- Selbst berechnete SHA-256, identisch zur separat übermittelten Prüfsumme:
  `cc5eec6e2fd0a0407f2371c7d6b7591e84e9c2e2cc850b509ed201ba59003468`.
- 8.954 reguläre Dateien, 657.838.226 entpackte Dateibytes. Enthalten sind die
  drei wissenschaftlichen Abschnitte mit benachbarter `-call.json`, ihre gemeinsame
  Verifikation sowie der technische Vorlauf mit beiden Einzelverifikationen.
- Tatsächlicher sauberer Ausführungs- und lesender Prüfstand:
  [`c3da991f389a4ec55206539ebe02a9648d4474b8`](https://github.com/craexxn/ringdown-sr/commit/c3da991f389a4ec55206539ebe02a9648d4474b8),
  main nach PR81, mit der übernommenen PR80-Implementierung. Der spätere
  Dokumentationscommit ersetzt diesen Ausführungsstand nicht.
- [Eingefrorener Plan](restart_confirmation_plan.md),
  [Seeds und Konfiguration](../data/restart_confirmation_protocol.json),
  Eingaben und Erzeuger sind an `a1f498ac29c8c261422c29daa24f9560359214b2`
  gebunden. Keine historischen Wiederverwendungen, Checkpointfortsetzungen,
  Nachfits, zusätzlichen Seeds oder nachträglichen Auswahlregeln.

| Abschnitt | A / Frequenz / Abklingzeit / Phase | Vorbereitungsbeginn UTC | Berichtabschluss UTC | Gemessener Aufruf |
| --- | --- | --- | --- | ---: |
| confirmation-anchor-manjaro-001 | 1 / 250 Hz / 0,008 s / 0 | 09.11.2026 08:09:08 | 09.11.2026 11:53:33 | 13.468,294 s |
| confirmation-low-manjaro-001 | 0,5 / 210 Hz / 0,010 s / −0,5 | 09.11.2026 12:15:59 | 09.11.2026 16:12:11 | 14.174,598 s |
| confirmation-high-manjaro-001 | 0,8 / 320 Hz / 0,006 s / 0,4 | 10.11.2026 05:05:35 | 10.11.2026 08:40:27 | 12.895,286 s |

Zwei neue Parameterkombinationen innerhalb der bisherigen Transferbereiche,
keine zufällige Stichprobe des gesamten Signalraums. Je Signal zehn vorab
festgelegte gepaarte Blöcke; 120 verschiedene Suchseeds über alle Blöcke, wobei
I und das erste R-Mitglied jeweils denselben Seed verwenden. Alle Suchen sind
frisch. Allgemeine Grammatik, beide Häufigkeitsschalter an,
`should_simplify=false`, `warmup_maxsize_by=0.0` und übrige Optionen unverändert.
Beide Arme verwenden denselben Iterationsworker und gewöhnliche Trainings-MSE.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1 und gesperrte
Abhängigkeiten sind gebunden. Tatsächliche Workerbelege stimmen über alle
Abschnitte überein: Intel Core i7-1165G7, `tigerlake`, Affinität `[0]`, Julia
Default-/Interactive-/GC-Threads 1/0/1, BLAS 1. `OPENBLAS_CORETYPE=Haswell` bleibt
die getrennte BLAS-Vorgabe. Die Vorbereitung bindet 97 Quellen einschließlich
aller 47 Python-Paketdateien; je Abschnitt 1.003 Vorbereitungsbindungen und
2.855 Rohmanifest-Einträge. Native Herkunft, Adapter, tatsächliche Optionen,
Threadbelege, Aufrufwächter und alle Quellenbindungen wurden lesend geprüft.

## Paarungen, Unsicherheit und Beweisgrenzen

Die Kontraste zählen R gegenüber I. Beide Endpunkte bleiben getrennt; die
deskriptive Präferenz folgt der eingefrorenen Regel, bei ungleicher A-Zahl
zunächst der A-Zahl. Sie ist keine statistische Überlegenheitsentscheidung.

| Signal | A: Gewinne / Verluste / Gleichstände | A plus Originalfamilie: Gewinne / Verluste / Gleichstände | Deskriptive Präferenz |
| --- | --- | --- | --- |
| anchor | 5 / 0 / 5 | 5 / 1 / 4 | R |
| variant_low | 3 / 0 / 7 | 5 / 0 / 5 | R |
| variant_high | 0 / 3 / 7 | 0 / 3 / 7 | I |

Marginale exakte 95-%-Clopper–Pearson-Intervalle unter der Bernoulliannahme,
in Prozent gerundet; keine simultane Garantie und kein Nachweis von 80 % wahrer
Erfolgswahrscheinlichkeit. Keine gepoolte Erfolgsquote über die drei Signale.

| Signal / Arm | A: Zahl und Intervall | A plus Originalfamilie: Zahl und Intervall |
| --- | --- | --- |
| anchor / I | 5/10; [18,71; 81,29] | 4/10; [12,16; 73,76] |
| anchor / R | 10/10; [69,15; 100,00] | 8/10; [44,39; 97,48] |
| variant_low / I | 7/10; [34,75; 93,33] | 5/10; [18,71; 81,29] |
| variant_low / R | 10/10; [69,15; 100,00] | 10/10; [69,15; 100,00] |
| variant_high / I | 7/10; [34,75; 93,33] | 7/10; [34,75; 93,33] |
| variant_high / R | 4/10; [12,16; 73,76] | 4/10; [12,16; 73,76] |

Fünf A-Ausgaben besitzen keinen bestätigten Originalfamiliennachweis:

| Signal / Arm / Block / Zelle | Unveränderter Nachweisgrund | Restbefund |
| --- | --- | --- |
| anchor / R / 3 / 11 | `nonaffine_argument` | `unresolved` |
| anchor / I / 4 / 16 | `unsupported_normalized_factor` | `unresolved` |
| anchor / R / 9 / 44 | `multiple_modes_without_nonmembership_proof` | `bound_proven` für den regelbasiert bestimmten Rest |
| variant_low / I / 6 / 26 | `trigonometric_product_not_supported` | `unresolved` |
| variant_low / I / 8 / 36 | `trigonometric_product_not_supported` | `unresolved` |

Alle fünf Originale sind auf dem geschlossenen Prüfintervall überall definiert.
Ein begrenzter Rest bestätigt weder die gesamte Originalfamilie noch neue
physikalische Parameter. Offene Nachweise bleiben offen; keine Erkennererweiterung
oder nachträgliche Änderung der gemeinsamen Erfolgszahl.

Unter den 60 ausgewählten Algorithmusausgaben sind 57 Domains vollständig
nachgewiesen. Bei anchor/I/Block 7 (Zelle 35) und variant_high/R/Block 3 (Zelle 13)
belegt `original_domain_gap` die Nichtmitgliedschaft der Originale; ihre gesamte
Domainprüfung und Fortsetzung bleiben `unresolved`. Bei variant_low/I/Block 7
(Zelle 35) bleiben Domain, Familie und Fortsetzung ungeklärt. Keine dieser drei
Ausgaben ist A. Reststatus je Signal über seine 20 Ausgaben:
anchor 13 `bound_proven` / 7 `unresolved`, variant_low 15 / 5,
variant_high 11 / 9. Physikalische Parameterübereinstimmung bleibt überall
`not_assessed`; die Familienprüfung ersetzt keine Parameterdiagnose.

Die 150 gespeicherten Endfronten enthalten 1.755 Kandidaten (534 / 598 / 623).
In keiner der 80 Fronten mit Nicht-A-Originalauswahl ist ein anderer A-Kandidat
nachgewiesen. Auch in keinem der sechs Nicht-A-Pakete von variant_high befindet
sich ein A-Kandidat in einer der vier gespeicherten Mitgliedsfronten. Das spricht
in diesem begrenzten Bestand gegen die verlustbasierte Auswahl als unmittelbare
Ursache der verfehlten A-Zahl. Endfronten sind kein vollständiges Protokoll aller
während der Evolution erzeugten Formeln; die eigentliche Suchursache bleibt offen.

## Kontinuierliche Fehler und Zusatzraster

128 Trainingspunkte, 889 regelmäßige Zwischenpunkte und 1.024 vorab gespeicherte
unregelmäßige Punkte je Signal; separater PCG64-Seed 2026110601. Das Zusatzraster
verändert weder Such-RNG noch Auswahl oder Stopp. Es reduziert Blindstellen des
gemeinsamen regelmäßigen 1/32768-Sekunden-Rasters, ersetzt keinen Domainnachweis
und garantiert keine allgemeine Identifizierbarkeit. Kein neuer Bestehensmarker
und keine Änderung der A–D-Klassen.

Spannweiten der relativen RMS-/Maximalfehler über die zehn **ausgewählten**
Algorithmusausgaben je Signal/Arm, sechs signifikante Stellen. Alle Einzelwerte
auf sämtlichen Rastern bleiben im Originalbericht und bytegleichen Verify-Export
erhalten; die nachfolgende Spannweite ist kein zusätzliches Erfolgskriterium.

| Signal / Arm | Training RMS / Max: jeweils min–max | Zwischenpunkte RMS / Max: jeweils min–max | Zusatzraster RMS / Max: jeweils min–max |
| --- | --- | --- | --- |
| anchor / I | 1.26021e-12–0.0104694 / 6.8201e-13–0.00723022 | 1.29822e-12–0.0105909 / 6.86007e-13–0.00651058 | 1.29842e-12–0.0105976 / 6.85618e-13–0.00654262 |
| anchor / R | 2.77833e-12–4.99833e-10 / 1.4771e-12–3.48138e-10 | 2.86198e-12–5.14639e-10 / 1.51101e-12–3.54533e-10 | 2.86204e-12–5.14839e-10 / 1.5094e-12–3.54431e-10 |
| variant_low / I | 1.03421e-12–0.00650927 / 8.41327e-13–0.00557104 | 1.04418e-12–0.00643777 / 8.43769e-13–0.00542383 | 1.04418e-12–0.00644528 / 8.43436e-13–0.00550509 |
| variant_low / R | 3.22734e-12–1.8808e-08 / 3.21621e-12–2.35045e-08 | 3.27974e-12–1.8445e-08 / 3.21621e-12–2.28194e-08 | 3.28066e-12–1.84453e-08 / 3.21509e-12–2.28425e-08 |
| variant_high / I | 1.32318e-12–0.0359829 / 1.14087e-12–0.0361792 | 1.34337e-12–0.0354242 / 1.21647e-12–0.0349557 | 1.34122e-12–0.0354653 / 1.21481e-12–0.0350114 |
| variant_high / R | 1.47745e-12–0.0189203 / 1.18594e-12–0.0136978 | 1.48856e-12–0.0191063 / 1.20814e-12–0.0127623 | 1.48881e-12–0.0191126 / 1.20759e-12–0.0128044 |

## Kosten und Haltegründe

Alle 150 Zellen enden regulär mit `iteration_limit`: 120 nach 500, 30 nach
2.000 vollständigen äußeren Runden. Keine Workerzeitüberschreitungen,
Integritätsabbrüche, numerischen Ausfälle oder fehlenden Kosten. Sämtliche vier
R-Mitglieder gehen in die Paketkosten ein; neue Kosten sind gleich Algorithmuskosten.

| Signal / Arm | Verlustcallback-Aufrufe | Fitzeit | Workerzeit | Adapterzeit | Nutzer-/System-CPU |
| --- | ---: | ---: | ---: | ---: | ---: |
| anchor / I | 637.702.421 | 5.177,942 s | 5.359,816 s | 5.379,650 s | 5.314,750 / 17,400 s |
| anchor / R | 635.354.558 | 6.017,970 s | 6.744,157 s | 6.823,081 s | 6.664,374 / 37,195 s |
| variant_low / I | 709.197.332 | 5.502,981 s | 5.675,815 s | 5.694,661 s | 5.630,371 / 16,950 s |
| variant_low / R | 699.755.607 | 6.285,101 s | 6.982,727 s | 7.059,543 s | 6.901,578 / 37,012 s |
| variant_high / I | 611.108.678 | 5.012,399 s | 5.185,628 s | 5.204,708 s | 5.141,219 / 16,004 s |
| variant_high / R | 595.467.378 | 5.615,514 s | 6.317,459 s | 6.395,303 s | 6.241,885 / 35,834 s |

R benötigt gegenüber I je Signal **25,83 % / 23,03 % / 21,83 % mehr Workerzeit**,
bei **0,37 % / 1,33 % / 2,56 % weniger Verlustcallback-Aufrufen**. Gleiche Summen
äußerer Iterationen gleichen weder reale Laufzeit noch Callbackzahl an.
Beim dritten Signal verbindet sich die geringere A-Zahl mit höherer Workerzeit;
dieser Bestätigungsbefund belegt somit keinen allgemeinen Effizienzvorteil.

Die drei benachbarten Aufrufmessungen summieren sich auf **40.538,178 Sekunden**,
also rund **11 h 15 min 38 s**, ohne Pausen zwischen den Abschnitten. Gemessen
wird der Eintritt in `run` bis zur Rückkehr der Veröffentlichung, einschließlich
Vorbereitung und Auswertung, ohne abschließendes Timing-Schreiben und erneute
Schlussprüfungen. Die nachträgliche Gesamtverifikation und der technische Vorlauf
sind darin nicht enthalten. Worker-, Fit-, Adapter- und Aufrufzeiten überlappen
und werden nicht addiert. Reine Kompilierzeit bleibt `not_observed`.
Alle Aufrufe liegen unter ihren vorher festgelegten Sicherheitsfristen.

## Vollständige Paartabelle

P: `proven_member`, U: `unresolved`, N: `proven_nonmember`.
Zellnummern gelten innerhalb des jeweiligen Signalabschnitts. Der Startseed
trägt I und das erste R-Mitglied; der ausgewählte R-Seed ergibt sich aus der
hier genannten Zelle und den unveränderten Originalmetadaten.

| Signal | Block / Startseed | I: Zelle / Klasse / Familie | R: Zelle / Klasse / Familie |
| --- | --- | --- | --- |
| anchor | 1 / 1117798821 | 5 / C / U | 3 / A / P |
| anchor | 2 / 1030321884 | 6 / A / P | 7 / A / P |
| anchor | 3 / 1155310602 | 15 / A / P | 11 / A / U |
| anchor | 4 / 301169227 | 16 / A / U | 20 / A / P |
| anchor | 5 / 523115599 | 25 / A / P | 21 / A / P |
| anchor | 6 / 899582762 | 26 / A / P | 27 / A / P |
| anchor | 7 / 510801071 | 35 / B / N | 32 / A / P |
| anchor | 8 / 709640440 | 36 / B / U | 39 / A / P |
| anchor | 9 / 1254076998 | 45 / B / U | 44 / A / U |
| anchor | 10 / 264161231 | 46 / B / U | 49 / A / P |
| variant_low | 1 / 1305640932 | 5 / B / U | 2 / A / P |
| variant_low | 2 / 1993095220 | 6 / A / P | 8 / A / P |
| variant_low | 3 / 1487307782 | 15 / A / P | 11 / A / P |
| variant_low | 4 / 1777223471 | 16 / A / P | 18 / A / P |
| variant_low | 5 / 1912784921 | 25 / A / P | 21 / A / P |
| variant_low | 6 / 567202465 | 26 / A / U | 29 / A / P |
| variant_low | 7 / 764985921 | 35 / B / U | 34 / A / P |
| variant_low | 8 / 1505751406 | 36 / A / U | 38 / A / P |
| variant_low | 9 / 229996622 | 45 / A / P | 41 / A / P |
| variant_low | 10 / 1212598543 | 46 / B / U | 49 / A / P |
| variant_high | 1 / 2124380224 | 5 / B / U | 2 / C / U |
| variant_high | 2 / 1566525609 | 6 / A / P | 8 / A / P |
| variant_high | 3 / 1597386441 | 15 / A / P | 13 / C / N |
| variant_high | 4 / 1430097084 | 16 / A / P | 18 / A / P |
| variant_high | 5 / 1890814876 | 25 / C / U | 24 / B / U |
| variant_high | 6 / 1277676302 | 26 / A / P | 29 / C / U |
| variant_high | 7 / 61311292 | 35 / B / U | 31 / C / U |
| variant_high | 8 / 26025133 | 36 / A / P | 40 / C / U |
| variant_high | 9 / 1877582679 | 45 / A / P | 42 / A / P |
| variant_high | 10 / 1994531873 | 46 / A / P | 47 / A / P |

## Eigene Prüfung und Anschlussentscheidung

Am exakten sauberen Ausführungscommit wurde der unveränderte CLI-Laufweg
`scripts/run_restart_confirmation.py verify-series` auf alle drei Originalabschnitte
angewandt: **150 Zellen und 1.755 Frontkandidaten erfolgreich geprüft**, null
Suchaufrufe. Originalauswahl, verlustbasierte Paketwahl, Kurven-/Familien-/Restbefunde,
Kosten, Aufrufmessungen, Domains, Quellenbindung und gemeinsame Umgebung bestätigt.
Alle drei neu erzeugten Verify-Dateien sind **bytegleich** zum gelieferten
`restart-confirmation-manjaro-001-verification`-Export.

Der mitgelieferte technische Manjaro-Vorlauf ist ebenfalls lesend bestätigt:
sechs kleine abgeschlossene Worker, beide Einzelverifikationen und gemeinsame
technische Verifikation. Deren neun Verify-Dateien sind bytegleich nachgerechnet.
Die technischen Fixtures erhalten keine wissenschaftliche Übergangsentscheidung.
Ein erster eigener Leseversuch für Fixture B scheiterte am falsch geschriebenen
lokalen Julia-Pfad vor der Zellprüfung; sein gesperrter Ausgabeordner bleibt
erhalten. Mit korrigiertem Pfad und neuer Audit-ID bestanden Einzel- und
Gesamtverifikation. Dies war keine Wiederholung einer wissenschaftlichen Suche.

Zusätzlich wurden die Paketwahl und Kostenaddition unmittelbar aus den Zellen,
beide Erfolgszählungen und alle zwölf marginalen Intervalle unabhängig über
Binomialsummen nachgerechnet. Empfangsmanifest und abschließender Hashvergleich
bestätigen die Unverändertheit aller 8.954 Originaldateien und des komprimierten
Archivs. Keine neue Suche, kein Fit, keine neu ausgeführte native Formelauswertung
und kein Laden binärer Suchzustände. Die Python-/MPFR-Nachrechnung und Prüfung
gespeicherter nativer Belege sind keine Wiederholung der Evolution.
Prüfskripte, eigene Exporte und Belege im getrennten
[Auditpaket](results_index.md#lesende-verifikation-der-neustartbestätigung-001).

**Einordnung vom 12.11.2026:** Die unabhängige Serie bestätigt keine ausreichende
Wiederholbarkeit des Neustartprofils auf allen drei vorgesehenen Signalen.
Die 8/10-Grenze bleibt unverändert; weder nachträglicher Wechsel zum jeweils
besten Arm noch zusätzliche Seeds oder offenere Strukturregeln ersetzen die
verfehlte gemeinsame Entscheidung. I erreicht bei der hohen Variante ebenfalls
nur 7/10, und dieser Kontrollarm war nicht als Ersatz für die R-Grenze festgelegt.

Nächster abgegrenzter Schritt ist gemäß Leitfaden die Einordnung des Befunds und
Forschungsanspruchs mit der Betreuung: Grenzen freier SR oder stärkeres Vorwissen
als ausdrücklich neue Variante. Keine automatische neue Versuchsserie und kein
unmittelbarer Rauschpilot. Zeitnormalisierung bleibt eine nur begründet zu
entscheidende zweite Intervention innerhalb der bestehenden Begrenzung; diese
Auswertung erteilt keinen Laufauftrag. Ein Tuning an diesen Fällen würde ihre
Rolle als unberührte Bestätigung beenden.

Vor einem späteren Rauschpilot muss das tatsächlich beschlossene Profil bewusst
in den allgemeinen Laufweg übernommen und dort rauschfrei geprüft werden.
Struktur- und Konstantensuche müssen dieselbe Gewichtung verwenden. Der
Spezialtreiber bestätigt diesen gewichteten Laufweg nicht. Unabhängige Bestätigung
und Rauschpilot bleiben im zentralen Leitfaden, ohne die verfehlte Grenze zu übergehen.

Original und Audit sind verfügbare Arbeitskopien. Gemeinsamer Archivordner,
unabhängige Zweitkopie und SHA-256-Prüfung beider Kopien sind gemäß
[Archivregel](results_archiving.md) und [Index](results_index.md) noch zu bestätigen.
Kein erneutes Bereitstellen dieses Originals und keine Wiederholung der Serie nötig.
