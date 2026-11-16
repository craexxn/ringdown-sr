# Begrenzter Rauschpilot: Manjaro 001

Quellenprüfung und Einordnung vom 16.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md).
Der [vorab beschlossene 144er-Pilot](noise_pilot_plan.md) ist vollständig
ausgeführt und lesend bestätigt: **144 abgeschlossene Suchen, 36 ursprüngliche
Paketausgaben, keine Ausfälle oder Timeouts**. Im beobachteten mittleren
primären Rekonstruktionsfehler zeigt die geschätzte Gewichtung keinen Vorteil
gegenüber gewöhnlicher MSE. Das ist ein begrenzter deskriptiver Befund bei
sechs Blöcken je Rauschmodell, kein allgemeiner Unterlegenheits- oder
Gleichwertigkeitsnachweis.

Alle 36 Primärwerte und sämtliche geplanten Paarungen sind verfügbar. Der
mittlere amplitudennormierte RMSE beträgt für gewöhnliche / bekannte /
geschätzte Gewichtung **1,624 / 1,666 / 1,666 %** bei weißem und
**2,412 / 2,406 / 2,742 %** bei AR(1)-Rauschen. Zusatzraster zeigen einzelne
deutliche Zwischenpunktspitzen, die der Trainingsfehler allein nicht beschreibt.
Sie werden unten separat berichtet und ändern keine Originalauswahl.

Die vollständige wissenschaftliche Aufrufzeit beträgt **47.491,474 s,
13 h 11 min 31 s**. Die eigene lesende Wiederholung bestätigt den gesamten
Serienbericht; alle vier Verify-Exportdateien sind bytegleich zum gelieferten
Verify-Export. Keine neuen Suchen oder Fits bei dieser Auswertung.

## Original, Protokoll und Quellenbindung

- Originalarchiv `noise-pilot-manjaro-001.tar.gz`: **92.167.501 Bytes**, am
  16.11.2026 aus den vier gelieferten Teilen 000–003 zusammengesetzt.
- Bestätigter SHA-256:
  `86a099ebe193669c945abbb918e8b18dd15b21b6341da44622bc1f6efdc69688`.
- 4.916 reguläre Dateien, 561 Verzeichnisse, 469.279.570 entpackte Dateibytes;
  keine Links, Spezialdateien, doppelten Namen oder unsicheren Pfade.
- Wissenschaftliche Wurzel `noise-pilot-manjaro-001` enthält Inputs, Serie,
  separaten Verify-Export und alle zugehörigen Aufrufmessungen. Die zweite
  Wurzel `noise-pilot-technical-manjaro-001` ist in allen 103 Dateien bytegleich
  zum zuvor geprüften technischen Original; dessen Nachweis bleibt im
  [Fortsetzungsstand](representation_implementation_status.md#technischer-manjaro-n128-nachweis-vom-15112026).
- Tatsächlicher sauberer Ausführungs- und eigener lesender Prüfcommit:
  `eb663a0bf008f7c8697ef7ec5386b3e11545a19f`, main nach PR92.
  Der spätere Dokumentationscommit ersetzt diesen Stand nicht.
- Eingefrorener Protokollcommit `27367a707b0f78c2d8e4ec397e0af6d958f5c527`,
  Plan-SHA `2a8e521b7729a668832ca02b0c8dd587d46ddec4010d7657d71e7b4d4d295fb8`.

Alle 173 Quellen einschließlich 63 Python-Paketquellen stimmen mit dem
Ausführungsstand überein. Die tatsächlichen Eltern-/Workerbelege aller 144
Suchprozesse sind sauber und konsistent mit ihren Vorbereitungen und dem
technischen Vorlauf: Python 3.12.14, Julia 1.13.1, PySR 2.6.0,
SymbolicRegression 2.5.1, Intel i7-1165G7, CPU-Affinität `[0]`, Julia-/GC-/BLAS-
Threads jeweils 1, interaktive Threads 0, Haswell-BLAS vor und nach der Suche.

Alle zwölf Seedzeilen stimmen mit dem Plan überein: 48 verschiedene Suchseeds,
jeweils innerhalb eines Falls zwischen drei eigenständigen Armaufrufen gepaart.
Die 144 Zeit-/Beobachtungsbindungen und 96 Kovarianzbindungen stimmen exakt
mit den vorab erzeugten Arrays überein. Je Worker ein frischer Suchaufruf,
1.000 tatsächlich abgeschlossene äußere Runden und 2.000 Populationszyklen;
lokal 300 Optimiereriterationen und fünf zusätzliche Neustarts,
Häufigkeitsschalter an, `should_simplify=false`. Kein Checkpointimport.
1.898 HOF-CSV-Zeilen stimmen in Reihenfolge, Gleichung, Komplexität und
Float64-Verlust mit den gespeicherten Endfronten überein. Das ist eine
Integritätsprüfung der Endfronten, keine zusätzliche Qualitätsauswahl.

## Primärmaß und gepaarte Vergleiche

O bezeichnet gewöhnliche MSE, K bekannte wahre Kovarianz und E geschätzte
Kovarianz. Das Primärmaß ist E_A = RMSE zur sauberen Wahrheit / |A| an den
128 Trainingszeiten. Die folgenden Tabellen verwenden diese dimensionslose
Größe; beispielsweise 0,02 entspricht 2 % der generierenden Amplitude.
Es geht um Rekonstruktion desselben Beobachtungsfensters, nicht um unabhängige
Generalisierung. Innerhalb eines Blocks werden Beobachtung und vier Suchseeds
gepaart; die beiden Rauschmodelle werden nicht miteinander gepaart oder gepoolt.

Primärer Kontrast ist E−O; negative Werte bedeuten kleineren Fehler mit
geschätzter Gewichtung. K−O und E−K sind vorab festgelegte Sekundärkontraste.
Alle Werte stammen von den unveränderten, allein nach nativem Trainingsverlust,
Komplexität und Mitgliedsposition gewählten Paketausgaben. Trainingsverluste
unterschiedlicher Gewichtungsarme werden nicht als gemeinsame Auswahlskala genutzt.

### Weißes Rauschen

| Block | O | K | E | E−O | K−O | E−K |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0,01384349 | 0,01480033 | 0,01727683 | 0,00343334 | 0,00095683 | 0,00247651 |
| 2 | 0,01793167 | 0,01772050 | 0,02463521 | 0,00670355 | -0,00021117 | 0,00691471 |
| 3 | 0,01613776 | 0,01463217 | 0,01192582 | -0,00421193 | -0,00150559 | -0,00270635 |
| 4 | 0,01489605 | 0,01505538 | 0,01538315 | 0,00048710 | 0,00015933 | 0,00032776 |
| 5 | 0,01743078 | 0,01907172 | 0,01567324 | -0,00175755 | 0,00164094 | -0,00339849 |
| 6 | 0,01719918 | 0,01867324 | 0,01505186 | -0,00214732 | 0,00147406 | -0,00362138 |

### AR(1)-Rauschen

| Block | O | K | E | E−O | K−O | E−K |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0,02985795 | 0,03230160 | 0,03610234 | 0,00624439 | 0,00244365 | 0,00380074 |
| 2 | 0,01481996 | 0,01413459 | 0,01944928 | 0,00462932 | -0,00068537 | 0,00531469 |
| 3 | 0,02172656 | 0,02117843 | 0,02195449 | 0,00022793 | -0,00054813 | 0,00077606 |
| 4 | 0,04105086 | 0,03835446 | 0,03609765 | -0,00495320 | -0,00269640 | -0,00225680 |
| 5 | 0,01572722 | 0,01400358 | 0,01310128 | -0,00262594 | -0,00172364 | -0,00090231 |
| 6 | 0,02155184 | 0,02436202 | 0,03778578 | 0,01623394 | 0,00281018 | 0,01342376 |

### Deskriptive Armstatistik

| Modell | Arm | Verfügbar/geplant | Mittel | Median | Min | Max | Stichproben-SD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| white | O | 6/6 | 0,01623982 | 0,01666847 | 0,01384349 | 0,01793167 | 0,00159748 |
| white | K | 6/6 | 0,01665889 | 0,01638794 | 0,01463217 | 0,01907172 | 0,00205618 |
| white | E | 6/6 | 0,01665769 | 0,01552819 | 0,01192582 | 0,02463521 | 0,00427989 |
| ar1 | O | 6/6 | 0,02412240 | 0,02163920 | 0,01481996 | 0,04105086 | 0,00988768 |
| ar1 | K | 6/6 | 0,02405578 | 0,02277022 | 0,01400358 | 0,03835446 | 0,00980097 |
| ar1 | E | 6/6 | 0,02741514 | 0,02902607 | 0,01310128 | 0,03778578 | 0,01055049 |

### Deskriptive Kontraststatistik

| Modell | Kontrast | Paare | Mittel | Median | Min | Max | SD | MCSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| white | E−O (primär) | 6/6 | 0,00041786 | -0,00063523 | -0,00421193 | 0,00670355 | 0,00403374 | 0,00164677 |
| white | K−O | 6/6 | 0,00041907 | 0,00055808 | -0,00150559 | 0,00164094 | 0,00118862 | 0,00048525 |
| white | E−K | 6/6 | -0,00000121 | -0,00118929 | -0,00362138 | 0,00691471 | 0,00414831 | 0,00169354 |
| ar1 | E−O (primär) | 6/6 | 0,00329274 | 0,00242863 | -0,00495320 | 0,01623394 | 0,00762093 | 0,00311123 |
| ar1 | K−O | 6/6 | -0,00006662 | -0,00061675 | -0,00269640 | 0,00281018 | 0,00222951 | 0,00091019 |
| ar1 | E−K | 6/6 | 0,00335936 | 0,00228840 | -0,00225680 | 0,01342376 | 0,00568659 | 0,00232154 |

E hat bei white in 3/6 und bei AR(1) in 2/6 Blöcken einen kleineren
Primärfehler als O. K liegt bei white in 2/6 und bei AR(1) in 4/6 Blöcken
unter O. Diese Zahlen beschreiben die Differenzrichtung, keine neue Erfolgsquote.
MCSE = SD(Differenz)/sqrt(6) ist bei sechs vollständigen Paaren berechenbar,
aber selbst eine unsichere Klein-n-Schätzung. Keine Signifikanzfreigabe,
Gleichwertigkeitsprüfung oder automatische Armwahl wird daraus abgeleitet.

## Zusatzraster, Beobachtungsfehler und klassische Kontrollen

Die folgenden vorab bestimmten Diagnosen verwenden 889 reguläre Zwischenpunkte
und 1.024 unabhängig erzeugte unregelmäßige Punkte. Mittel der sechs
amplitudennormierten RMS-Fehler und größter Maximalfehler über alle sechs
ausgewählten Ausgaben; das jeweilige Maximum kann aus einem anderen Block
stammen. Alle 36 Werte je Raster sind verfügbar. Keine zusätzliche Grenze
oder nachträgliche Entfernung eines Falls.

| Modell | Arm | Zwischen: mittl. RMSE/A | Zwischen: größtes Max/A | Unregelmäßig: mittl. RMSE/A | Unregelmäßig: größtes Max/A |
| --- | --- | --- | --- | --- | --- |
| white | O | 0,01543722 | 0,08997899 | 0,01558417 | 0,13060085 |
| white | K | 0,01849216 | 0,69303124 | 0,01721199 | 0,34669616 |
| white | E | 0,01672501 | 0,15504680 | 0,01671356 | 0,15535862 |
| ar1 | O | 0,02399855 | 0,14630173 | 0,02425226 | 0,30026672 |
| ar1 | K | 0,03785383 | 1,80947892 | 0,03655135 | 1,83037968 |
| ar1 | E | 0,02700665 | 0,12150997 | 0,02700430 | 0,12336612 |

Besonders deutlich ist **AR(1), Block 5, K**: Training E_A 0,01400358,
Zwischenraster-RMSE/A 0,09788362 und unregelmäßig 0,09003438; Maximalfehler/A
1,80948 beziehungsweise 1,83038. Die Originalformel ist überall definiert,
besitzt aber eine schnell veränderliche exponentielle Phasenmodulation; der
Familiennachweis bleibt `unresolved`. Die Maxima liegen bereits im ersten
Trainingsintervall: regelmäßig bei t=0,00006103515625 s, unregelmäßig bei
ungefähr t=0,0000358421935 s. Ein Definitionsnachweis allein garantiert also
keine gute Kurve zwischen den Trainingspunkten.

Bei **white, Block 6, K** liegen die Maximalfehler/A bei 0,69303 und 0,34670;
die Originalformel ist wegen einer Definitionslücke `proven_nonmember`.
Die Maxima liegen bei t=0,0045166015625 s beziehungsweise ungefähr
0,00452048517 s. Beide Werte wurden ausschließlich auf den vorab gespeicherten
Punkten nachgerechnet; keine zusätzliche Punktsuche.
Bei **AR(1), Block 6, O** erreicht das unregelmäßige Raster Max/A 0,30027,
während der vollständige Domainnachweis ungeklärt bleibt. Diese Unterschiede
bestätigen den Nutzen der getrennten Raster- und Domainprüfung; endliche
Rasterwerte beweisen keine überall gültige Originalfunktion.

Die gemeinsame MSE zum verrauschten Beobachtungsvektor und Q_true/N werden
nur nach Auswahl ausgewiesen. Die Tabelle zeigt Mittelwerte über sechs Fälle,
daneben den mittleren E_A der getrennten klassischen Ringdown-Referenzfits.
Alle 36 Referenzfits sind erfolgreich; ihr festes Familienvorwissen macht sie
zu diagnostischen Kontrollen, nicht zu einem austauschbaren SR-Arm.

| Modell | Arm | Mittlere Beobachtungs-MSE | Mittleres Q_true/N | Referenzfit: mittlerer E_A |
| --- | --- | --- | --- | --- |
| white | O | 0,00199774 | 0,95098928 | 0,01069905 |
| white | K | 0,00201135 | 0,95746776 | 0,01069905 |
| white | E | 0,00199209 | 0,94830045 | 0,01069905 |
| ar1 | O | 0,00138630 | 0,79196481 | 0,01450953 |
| ar1 | K | 0,00137805 | 0,77335596 | 0,01395888 |
| ar1 | E | 0,00147692 | 0,80252318 | 0,01433237 |

Es gibt keine Chi-Quadrat-Freiheitsgrad- oder Konfidenzbehauptung für die
frei gewählten SR-Modelle. Die Referenzfitparameter werden hier nicht in eine
neue physikalische Parametererfolgsregel umgedeutet.

## Klasse, Originalfamilie und Definitionsbereich

Alle **36 Originalausgaben sind D** auf der unveränderten rauschfreien Skala.
Diese verwendet Signal-RMS beziehungsweise Signalmaximum auf Training und
Zwischenraster, nicht die generierende Amplitude des Primärmaßes. D ist hier
eine beschreibende Einordnung, kein präregistriertes Nichtbestehen des Piloten.
Die frühere rauschfreie 8/10-Grenze gilt nicht für diesen Versuch.

Keine ausgewählte Originalformel ist als Mitglied der Ringdown-Familie
nachgewiesen: **34 `unresolved`, zwei `proven_nonmember`**. Die zwei
Nichtmitglieder sind white/Block 3/O und white/Block 6/K, jeweils wegen einer
nachgewiesenen Original-Definitionslücke. Der vollständige Domainnachweis
bleibt dort dennoch ungeklärt; eine bekannte Lücke ist bereits hinreichend
für Nichtzugehörigkeit. Eine gültige stetige Fortsetzung ist nicht nachgewiesen.
Zusätzlich bleiben white/Block 4/O und AR(1)/Block 6/O im Domainnachweis
ungeklärt; die übrigen **32 Originale sind überall definiert**.

Restschranken sind bei white/Block 1/E, white/Block 2/K und AR(1)/Block 1/O
nachgewiesen; sie ersetzen keinen Originalfamiliennachweis und ändern weder
Auswahl noch Klasse. Alle übrigen Restbefunde bleiben ungeklärt.
Physikalische Parameterübereinstimmung bleibt durchgängig **`not_assessed`**.
Keine offene Erkennerentwicklung, Formelreparatur oder zusätzliche Endfront-
Qualitätsauswahl wurde für günstigere Zahlen vorgenommen.

## Kovarianz und Hintergrund

Alle zwölf Schätzungen sind erfolgreich. Die eingefrorenen Hintergrundmengen
64/128/256 bei N=128 ergeben M_train/N=0,5. Alpha wird ausschließlich aus dem
Validierungs-Gaußscore bestimmt; kein Refit, Jitter oder Ersatz durch Wahrheit.
Die Tabelle zeigt den relativen Frobeniusfehler, geschätzte Kondition und
Kontrollscore-Differenz geschätzt minus wahr auf 256 unabhängigen Fenstern.
Der Score enthält Logdeterminante und mittlere Quadratik; kleiner ist besser.
Die Kontrollfenster beeinflussen Alpha nicht.

| Modell | Block | Alpha | Relativer Frobeniusfehler | Kondition geschätzt | Kontrollscore E−wahr |
| --- | --- | --- | --- | --- | --- |
| white | 1 | 1,0 | 0,017799 | 1,000000 | 0,043370 |
| white | 2 | 1,0 | 0,019631 | 1,000000 | 0,046120 |
| white | 3 | 1,0 | 0,019361 | 1,000000 | -0,012885 |
| white | 4 | 1,0 | 0,017268 | 1,000000 | -0,001658 |
| white | 5 | 1,0 | 0,003443 | 1,000000 | -0,000882 |
| white | 6 | 1,0 | 0,020341 | 1,000000 | 0,012981 |
| ar1 | 1 | 0,5 | 0,595413 | 10,845985 | 42,996041 |
| ar1 | 2 | 0,5 | 0,587396 | 10,279483 | 43,129698 |
| ar1 | 3 | 0,5 | 0,592536 | 10,456333 | 44,365797 |
| ar1 | 4 | 0,5 | 0,602863 | 9,950325 | 44,542677 |
| ar1 | 5 | 0,5 | 0,585968 | 10,267484 | 46,941236 |
| ar1 | 6 | 0,5 | 0,581442 | 10,654925 | 42,690391 |

Bei white wird sechsmal Alpha 1 gewählt; die geschätzte Matrix ist skalar
diagonal und hat Kondition 1 wie die wahre Matrix. Die mathematischen Verluste
von O/K/E sind hier proportional; unterschiedliche Rundung und Suchdynamik
können trotzdem unterschiedliche SR-Originalausgaben liefern. Ihre beobachteten
Unterschiede werden nicht als Vorteil eines Kovarianzmodells interpretiert.

Bei AR(1) wird sechsmal Alpha 0,5 gewählt; geschätzte Konditionen liegen
zwischen 9,95 und 10,85, die wahre bei 22,1554. Frobeniusfehler von 0,581–0,603
und höhere Kontrollscores kennzeichnen die Begrenzung dieses datenarmen
Schätzszenarios. Das beweist nicht, dass die gesamte SR-Fehlerdifferenz allein
durch Kovarianzschätzung verursacht wurde. Auch die bekannte Kovarianz bringt
im mittleren Trainings-Primärmaß nur einen sehr kleinen beobachteten Gewinn
gegenüber O und zeigt den genannten Zwischenpunktausreißer.

## Kosten und Vollständigkeit

Alle 144 geplanten Suchen sind ausgeführt und abgeschlossen; alle 36 Pakete
haben eine endliche ausgewählte Originalausgabe. Keine `fit_error`, `timeout`
oder `not_run`-Mitglieder, keine fehlenden Primärwerte und keine ausgefallenen
Referenzfits. Ausfallnenner bleibt sechs geplante Pakete je Modell und Arm.

Die folgende Tabelle summiert jeweils 24 Worker je Modell/Arm. Fitzeit ist
in der Workerzeit enthalten; die Werte nicht addieren. Verlustcallbacks sind
tatsächliche native Aufrufe einschließlich der lokalen Optimierung.

| Modell | Arm | Workerzeit / s | Enthaltene Fitzeit / s | Verlustcallbacks |
| --- | --- | --- | --- | --- |
| white | O | 5706,494 | 5363,809 | 703513460 |
| white | K | 10484,139 | 10116,256 | 730178520 |
| white | E | 10403,031 | 10039,124 | 728864502 |
| ar1 | O | 5815,551 | 5476,243 | 709474666 |
| ar1 | K | 7258,498 | 6898,549 | 661896045 |
| ar1 | E | 7513,228 | 7149,819 | 688410869 |

Insgesamt 47.180,941073 s Workerzeit, darin 45.043,799047 s Fitzeit und
4.222.338.062 Verlustcallbacks. Die zwölf vollständigen Fallaufrufe umfassen
47.353,816231 s und sind ihrerseits im vollständigen Serienaufruf enthalten.
Die feste Armreihenfolge O/K/E und dieser einzelne Rechner begrenzen die
Übertragbarkeit der Laufzeitvergleiche.

| Getrennter Aufruf | Wall-Zeit / s | CPU user / s | CPU system / s |
| --- | ---: | ---: | ---: |
| Wissenschaftliche Inputvorbereitung | 2,016814 | 1,492157 | 0,506086 |
| Wissenschaftliche Serie | 47491,473596 | 47163,266405 | 204,816771 |
| Ursprüngliche separate lesende Verifikation | 96,010385 | 83,994908 | 11,512891 |
| Eigene neue lesende Verifikation, gespeicherter Aufruf | 108,077573 | 95,165322 | 13,119709 |

Die technische Kontrolle mit 161,847172 s bleibt ein separater früherer
Aufruf. Einrichtung ist nicht Teil dieser wissenschaftlichen Serienmessung.
Der Scope der Serien-/Prüfaufrufe endet nach Veröffentlichung und Wiederherstellung
der Signalhandler; Schreiben der Aufrufdatei und finale Nachprüfungen sind
ausgenommen. Die gesamte neue CLI-Messung einschließlich Prozessstart betrug
109,909 s und ist kein zusätzlich zu addierender Prüfaufwand.

Größter Worker: 624,984177 s (white/Block 1/E, Mitglied 1), deutlich unter
1.800 s. Größter Dreierfall: 4.802,026982 s, unter 25.200 s. Keine Fristen
wurden nachträglich geändert. Präzise Serienstart-/Endzeitpunkte werden nicht
aus Dateizeitstempeln abgeleitet; die gespeicherte monotone Laufzeit ist maßgeblich.

## Eigene Prüfung und Aussagegrenzen

Die vollständige Repository-Verifikation lief auf sauberem `eb663a0`:

```bash
uv run --locked python scripts/run_noise_pilot.py verify \
  --inputs ORIGINAL/noise-pilot-manjaro-001/inputs \
  --technical ORIGINAL/noise-pilot-technical-manjaro-001 \
  --output ORIGINAL/noise-pilot-manjaro-001/series \
  --export NEUER_AUDITORDNER/verification
```

Ergebnis: `Noise-pilot series read-only verification passed; no fits or searches executed.`
Alle 4.916 Originaldateien und das Archiv blieben hashgleich. Die vier neuen
Verify-Exportdateien sind bytegleich; die getrennte neue Aufrufmessung besitzt
erwartungsgemäß eigene Kosten. Archivierte Programme oder Pickle-/Julia-
Suchzustände wurden nicht ausgeführt beziehungsweise deserialisiert.

Eine getrennte KI-basierte Gegenprüfung bestätigte 374 Prüfsummenmanifeste
mit 12.808 Hashbezügen, Quellen, tatsächliche Workerherkunft, Seeds,
Inputbindungen, native Iterationen, HOF-Zeilen und Kosten. Eine weitere
unabhängige Nachrechnung bestätigte alle 36 Primär-/Rasterauswertungen,
sechs Kontraste einschließlich SD/MCSE, zwölf Kovarianzschätzungen samt
Alpha-Auswahl und 36 Referenzfits durch lesenden Vorhersage-/Zielwert-Replay.
Hierfür wurden keine Repository-Auswertungs- oder Fitfunktionen importiert:
eigener JSON-Baumevaluator, NumPy/Standardbibliothek und bestehende Originalpunkte.
Größte absolute Abweichung beim Primärmaß 1,22 × 10⁻¹⁷, bei den
Zusatzrasterfehlern 2,23 × 10⁻¹⁶ und bei Referenzzielwerten 4,45 × 10⁻¹⁶.
Alle 36 D-Klassen wurden aus der eingefrorenen Regel nachgezählt; die beiden
bekannten affinen Nennernullstellen zusätzlich exakt nachgerechnet. Die
übrigen symbolischen Beweise wurden nicht unabhängig neu implementiert.
Diese Kontrollen ersetzen keine neue wissenschaftliche Replikation.

## Einordnung und nächster abgegrenzter Schritt

Der Pilot ist technisch vollständig und wissenschaftlich auswertbar, aber
liefert keinen beobachteten mittleren Vorteil geschätzter Gewichtung. Sechs
Blöcke auf einem bekannten Signal, einem Pegel und einer Hintergrundmenge
tragen keine allgemeine Rauschrobustheits-, Unterlegenheits- oder
Gleichwertigkeitsbehauptung. Die bekannten klassischen Fits haben zusätzliches
Familienvorwissen. Weder ihre Fehler noch die D-Klassen rechtfertigen eine
nachträgliche Änderung des SR-Auswahlverfahrens.

Gemäß vorab festgelegter Anschlussregel folgt ein **gesonderter Hauptstudienplan
zu Hintergrundmenge und Gewichtung**. Er muss relevante Effektgröße,
Präzisionsziel, neue unabhängige Fälle und Rechenumfang vor neuen Suchen
festlegen. Die gemessene Streuung ist nur eine unsichere Planungsinformation;
keine scheinbar präzise Fallzahl allein aus dem kleinen beobachteten Effekt.
Die dokumentierten Zwischenpunktspitzen müssen bei der Interpretation und
der prospektiven Endpunktfestlegung berücksichtigt werden. Ein größerer
Hintergrund kann die Kovarianzschätzung ändern, garantiert aber keinen
Vorteil der freien SR. Keine automatische Hauptstudie, neue Budgetstaffel,
Grammatik- oder Zeitkoordinatenoptimierung und keine neue Parameterbewertung.

Originalarchive bleiben unverändert. Gemeinsame Archivablage und unabhängige
hashgeprüfte Zweitkopie sind weiterhin unbestätigt; Zuordnung im
[Ergebnisindex](results_index.md#wissenschaftlicher-rauschpilot-manjaro-001).
Für diese abgeschlossene Serie fehlen keine weiteren Laufdateien.
GitHub-Uploads bleiben optional.
