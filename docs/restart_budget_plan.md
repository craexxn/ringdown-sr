# Entwicklungsprotokoll: vier mittlere gegen zwei längere globale Suchen

**Beschlossen am 12.11.2026, vor Implementierung getrennt versioniert.**
Bezugsstand `fbdb45003c777c878f833e08a2287b70daa00485`, main nach PR84.
Begrenzter Anschlussvergleich zu [Leitfadenphase 4](ringdown_recovery_roadmap.md),
keine neue Roadmap und keine unabhängige Bestätigung. Dieser Plan,
[Konfiguration und Seeds](../data/restart_budget_protocol.json),
[Eingaben](../data/restart_budget_inputs.npz) und
[Erzeuger](../scripts/prepare_restart_budget_inputs.py) werden gemeinsam vor
Implementierung versioniert und anschließend über Commit und SHA-256 gebunden.

## Frage und begründete Abgrenzung

Die [unabhängige Bestätigung](restart_confirmation_results_manjaro_001.md)
verfehlte die praktische Grenze auf der hohen Variante. Vier 500er-Suchen und
eine 2.000er-Suche haben signalabhängige Stärken; daraus folgt kein allgemeiner
Neustartvorteil. Der anschließende
[Zeitkoordinatenvergleich](time_coordinate_results_manjaro_001.md) ist gemischt:
u=32t verbessert die hohe, verschlechtert aber die niedrige Variante. Seine
zusätzlichen Beweisgrenzen erklären nicht den gesamten Kurvenkontrast.

Gemäß der datierten Anschlussentscheidung bleibt die **ursprüngliche physische
Zeit t** für beide neuen Budgetarme auf allen Signalen die gemeinsame Referenz.
Das isoliert die Budgetaufteilung, behauptet keinen Sieg von t und widerlegt
das U-Indiz nicht. Keine signalabhängige Koordinatenwahl, keine Kombination der
jeweils besten T-/U-Ausgaben und keine Veränderung bestehender Beweisgrenzen.

Verglichen werden je gepaartem Block:

| Arm | Vollständig frische globale Suchen | Äußere Iterationen je Suche | Summe äußerer Iterationen | Ausgewählte Ausgaben |
| --- | ---: | ---: | ---: | ---: |
| R | 4 | 1.000 | 4.000 | 1 |
| L | 2 | 2.000 | 4.000 | 1 |

Gleiche Iterationssummen bedeuten keine gleichen Rechenkosten. Beide Arme haben
mehrere Mitglieder; ein Paket liefert genau eine verlustbasiert ausgewählte
Ausgabe. Kein ungeprüfter Sprung zu 4 × 2.000, kein dritter Suchhebel und keine
offene Parameteroptimierung. Die Frage betrifft diese beiden konkreten Verfahren
und den begrenzten Entwicklungsbestand, nicht die allgemeine optimale Budgetwahl.

## Eingaben und endlicher Umfang

Die drei bisherigen Bestätigungssignale sind jetzt bekannte Entwicklungsfälle.
Eine spätere unabhängige Bestätigung benötigt unberührte Fälle. Neue Seeds allein
machen dieselben Signale nicht wieder zu unabhängigen Bestätigungsdaten.

| Signal | Amplitude | Frequenz | Abklingzeit | Phase | Gepaarte Blöcke | Frische Suchaufrufe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| anchor | 1 | 250 Hz | 0,008 s | 0 | 2 | 12 |
| variant_low | 0,5 | 210 Hz | 0,010 s | −0,5 | 2 | 12 |
| variant_high | 0,8 | 320 Hz | 0,006 s | 0,4 | 4 | 24 |

Insgesamt **acht gepaarte Blöcke, 48 neue Suchaufrufe und 16 Paketausgaben**.
Der Umfang entspricht der gezielten 2/2/4-Verteilung des vorangegangenen
Koordinatenversuchs: hohe Variante stärker vertreten, beide übrigen als
Gegenkontrollen. Kein Nachlegen von Seeds nach Zwischenbefunden.

Der gesamte Byteinhalt von `data/restart_confirmation_inputs.npz` am Bezugsstand
wird übernommen, einschließlich aller zwölf Arrayrollen; keine Neuberechnung
der Signalwahrheit. Training: 128 Punkte t=j/4096 Sekunden, j=0,…,127.
889 reguläre Zwischenpunkte, sieben je Intervall. Physisches Prüfintervall
[0,127/4096] Sekunden; Float64, Zeit in Sekunden, Ausgabe dimensionslos.
Signale und Rollen werden zusätzlich über die bestehenden Fingerprints gebunden.

Die 1.024 bereits konkret eingefrorenen unregelmäßigen Punkte und ihre
Signalwerte werden ebenfalls unverändert übernommen. Ursprüngliche Regel:
stratifizierte Ziehung mit getrenntem PCG64-Seed 2026110601, Ausschluss des
regelmäßigen 1/32768-Sekunden-Rasters. Gespeicherte Punkte vor jeder Suche
binden; keine Rastererzeugung im Suchprozess und keine Änderung seines RNG-Zustands.
Das Raster dient ausschließlich kontinuierlicher Zusatzdiagnose, erhält keine
neue Klassengrenze und ersetzt keinen Definitionsnachweis.

## Seeds, Paarung und Reihenfolge

Der Erzeuger zieht vor Implementierung **32 neue verschiedene positive
31-Bit-Seeds** mit PCG64, Generatorseed 2026111202. Ausgeschlossen werden alle
positiven 31-Bit-Ganzzahltokens in versioniertem Text unter data/docs/src/scripts/tests
am vollständigen Bezugscommit sowie doppelte Ziehungen. Ausschlussumfang und
Hash sind in der Konfiguration festgehalten. Das belegt Disjunktheit zu den dort
dokumentierten Werten, nicht zu unbekannten externen Versuchen.

Jeder Block besitzt vier vorab gespeicherte Seeds s0,s1,s2,s3. R verwendet
alle vier, L verwendet s0 und s1. Keine Seedüberschneidung zwischen Blöcken
oder Signalen. Die vollständigen Werte stehen in der gebundenen Konfiguration.
Die gemeinsame Verwendung von s0/s1 paart Starts; unterschiedliche Budgets
und Suchverläufe ergeben keine unabhängigen Einzelbeobachtungen innerhalb
eines Blocks. Bewertungs- und Nennergröße bleibt das Paket beziehungsweise Paar.

Alle sechs Suchaufrufe eines Blocks starten vollständig frisch. Insbesondere
ist ein 2.000er-Lauf mit demselben Seed keine Fortsetzung des 1.000er-Laufs:
kein Checkpoint, Warmstart, Frontimport, Wiederverwendung oder Nachfit.
In ungeraden Blöcken zuerst alle R-Mitglieder, dann alle L-Mitglieder;
in geraden Blöcken umgekehrt. Innerhalb jedes Arms feste Seedreihenfolge.
Die Reihenfolge wechselt pro Signal, reduziert aber nicht sämtliche Zeiteffekte.

Drei Abschnitte in der Reihenfolge anchor, variant_low, variant_high. Alle
geplanten Fälle einschließlich Ausfällen bleiben enthalten; Pausen zwischen
Abschnitten sind erlaubt. Keine zusätzlichen Ausführungen, kein Resume und
keine Mischung von Teilständen. Ein Abbruch erhält seine Artefakte/Teilkosten,
sperrt den Gesamtabschluss und braucht vor Wiederholung eine dokumentierte
Entscheidung sowie neue Lauf-ID.

## Festes Suchprofil und technische Grenzen

Lokal **300 Optimiereriterationen plus fünf zusätzliche lokale Neustarts**.
Globale Neustarts sind neue SR-Suchen und davon getrennt. Beide Häufigkeitsschalter
`use_frequency` und `use_frequency_in_tournament` eingeschaltet;
allgemeine Grammatik +, −, *, /, exp, sin, cos; `should_simplify=false`,
`warmup_maxsize_by=0.0`, Float64, gewöhnliche native Trainings-MSE,
zwei Populationen à 32, 50 Zyklen je äußerer Iteration, maxsize/maxdepth 20,
Parsimony 0, unveränderter Newton-/BFGS-Pfad, lokale Funktionsgrenze 10.000.
Alle übrigen Optionen entsprechen dem geprüften PR77-Iterationsworker.
Keine Templates, Grammatikeinschränkung oder nachträgliche Konstantenoptimierung.

Python 3.12.14, Julia 1.13.1, PySR 2.6.0, SymbolicRegression 2.5.1 und übrige
Sperrdateien unverändert. Manjaro, serielle Suche auf einer erlaubten CPU,
`OPENBLAS_CORETYPE=Haswell`, Julia Default-/Interactive-/GC-Threads 1/0/1,
BLAS und relevante Bibliotheken ein Thread. Eltern-/Workerherkunft, Adapter,
effektive Optionen und tatsächliche Quellen/CPU-/Threadbelege prüfen. Sämtliche
Abschnitte brauchen denselben sauberen Ausführungscommit und dieselbe numerische
Umgebung/Hardware. Keinen Quellenwechsel während einer Serie zulassen.

1.800 Sekunden Sicherheitsfrist pro Worker; 50.400 Sekunden je Signalabschnitt
einschließlich Vorbereitung und Abschluss. Das deckt höchstens 24 Workerfristen
plus zwei Stunden übrige Arbeit ab und ist keine Laufzeitprognose. Einzelverifikation
7.200 Sekunden, Gesamtverifikation 21.600 Sekunden. Reguläre Stopregel sind die
festen Iterationsbudgets, kein Zeitbudgetarm. Frühzeitige oder verspätete
Integritätsfehler und Fristverletzungen sperren beziehungsweise widerrufen Aggregate.

## Auswahl, Ausfälle und Kosten

Jeder Worker erhält seine ursprüngliche Auswahl aus der gespeicherten Endfront:
kleinste endliche native Trainings-MSE, danach native Originalkomplexität und
ursprünglicher Frontindex. Innerhalb eines Pakets werden ausschließlich diese
Originalauswahlen verglichen: kleinste endliche native Trainings-MSE, dann
Originalkomplexität, dann aufsteigender vorab zugewiesener Mitgliedsindex.
Kein Nachranking aller Formeln über Fronten hinweg. Ein Paket liefert genau
eine Ausgabe; ursprüngliche Mitglieder und alle zugehörigen Kosten bleiben erhalten.

Gewöhnliche nach dem bestehenden Vertrag zulässige numerische Fehler und
Worker-Timeouts bleiben als Mitgliedsausfälle im Nenner und Kostenbestand.
Nichtendliche Verluste sind nicht auswählbar. Ein Paket mit mindestens einer
zulässigen endlichen Originalauswahl wählt daraus; ohne solche Auswahl ist
das Paket ein erfolgloses Ergebnis. Alle geplanten Mitglieder werden ausgeführt,
auch nach einem guten Zwischenergebnis. Keine Ersatzseeds oder Wiederholungen.

Wächter-/Herkunftsfehler, unbekannte Fehler, Unterbrechungen und Gesamtfristen
sperren die Freigabe. Timeouts dürfen aufgezeichnete Integritätsfehler nicht
verdecken. Die erreichten Workerphasen bestimmen die erforderlichen
Herkunftsbelege; vorhandene Widersprüche werden stets abgelehnt. Lesende
Verifikation und spätes Widerrufen verwenden dieselben Grenzen.

Weder Auswahl noch vorzeitiger Abbruch verwenden Signalwahrheit, Kurvenklasse,
Familien-/Restbeweis oder Zusatzraster. „Passender Kandidat irgendwo in einer
gespeicherten Endfront vorhanden“ wird separat diagnostiziert und ersetzt keine
Originalauswahl. Endfronten sind kein vollständiges Evolutionsprotokoll.

Pro Mitglied, Paket, Paar, Arm und Signal: tatsächliche native Verlustcallback-
Aufrufe, Fit-/Worker-/Adapterzeiten, Nutzer-/System-CPU-Zeit. Vollständige
Abschnittsaufrufe einschließlich Vorbereitung und Veröffentlichung getrennt
messen; überlappende Zeiten nicht addieren. Keine historischen Kosten oder
Wiederverwendung: neu benötigter Aufwand entspricht dem gesamten Serienaufwand.
Fehlende Kosten bleiben unbekannt, niemals null. Unbeobachtete JIT-Zeiten oder
native Gesamtevaluierungszahlen nicht aus Callback-Zählern ableiten.

## Endpunkte und Anschlussregel

Je Signal/Arm A-Zahl und gemeinsame Zahl **A mit nachgewiesener gültiger
Originalfamilie** berichten; Nenner 2,2,4 Pakete. Paarweise Gewinne, Verluste
und Gleichstände beider Endpunkte, Domains/Fortsetzungen/ungeklärte Nachweise,
Ausfälle und sämtliche Kosten erhalten. Kontinuierliche relative RMS-/Maximalfehler
auf Training, Zwischenpunkten und Zusatzraster berichten. Originalauswahlen,
Bewertungsregeln und Ressourcen bleiben unverändert; neue Parameterübereinstimmung
bleibt `not_assessed` und folgt nicht aus Familienzugehörigkeit.

Erst alle drei unverändert lesend verifizierten Abschnitte erlauben die
folgende beschreibende Entwicklungsentscheidung:

1. **R als Entwicklungskandidat:** R hat auf jedem Signal mindestens so viele
   A-Ausgaben und gemeinsame A-/Familienerfolge wie L; mindestens eine gemeinsame
   Erfolgszahl ist größer.
2. **L als Entwicklungskandidat:** dasselbe Richtungskriterium mit vertauschten Armen.
3. **Zahlen unverändert:** beide Endpunkte auf allen Signalen gleich. Vollständig
   bekannte Kosten beschreibend vergleichen; sie ersetzen keinen Erfolgsnachweis.
4. **Gemischt/offen:** alle übrigen vollständigen Befunde. Kein Pooling, keine
   nachträgliche Punktzahl und keine zusätzliche Seedrunde bis zum gewünschten Erfolg.

Ein alleiniger A-Vorteil ohne strikten gemeinsamen A-/Familienvorteil erfüllt
keines der Richtungskriterien. Kosten sind kein nachträglicher Gleichstandsentscheid.

Keine neue 8/10-Grenze, kein Signifikanz-/Überlegenheitsnachweis aus diesen
kleinen gezielten Fällen und keine automatische Profilübernahme. Auch ein
gerichteter Kandidatenbefund benötigt die gemeinsame Einordnung von Kosten,
offenen Beweisen und wissenschaftlichen Grenzen. Danach begründete Entscheidung
mit der Betreuung über unabhängige Bestätigung auf unberührten Fällen oder
Begrenzung der erreichbaren Aussage; keine dritte Suchintervention anschließen.
Allgemeiner gewichteter Laufweg und Profilübernahme vor dem Rauschpilot bleiben
gesondert zu prüfen. Ein Rauschpilot ist durch diesen Entwicklungsvergleich
nicht freigegeben.

## Umsetzung, Prüfung und Archivierung

Vorhandene Adapter, Auswahl-/Bewertungs-/Archivverträge verwenden. Keine neue
allgemeine Infrastruktur und keine Änderung historischer Worker oder Protokolle.
Technische Fixtures deutlich getrennt von Wissenschaft: zwei künstliche
Achtpunkt-Signale, je ein Block mit vier Ein-Iterations- und zwei Zwei-Iterations-
Workern, insgesamt zwölf winzige Suchen. Beide Paketwahlen, alle Mitgliedskosten,
Einzel-/Gesamtverifikation und reguläres Iterationsende technisch prüfen;
keine wissenschaftliche Entwicklungsentscheidung aus Fixtures.

Gezielte Python-Gegenfälle für vollständigen Plan, Seedpaarung, Verlust-/Tieauswahl,
Ausfallnenner, unbekannte Kosten, Quellen-/Workerherkunft, Abschnitte und späten
Widerruf. Vollständige erforderliche technische CI vor Übernahme; Entwicklung
als Draft gemäß CI-Sparplan. Keine wissenschaftliche Serie in GitHub Actions.
Der konkrete Manjaro-Laufweg wird erst mit geprüfter Implementierung bereitgestellt;
die neuen wissenschaftlichen Suchen bleiben ein separater Ausführungsschritt.

Alle tatsächlichen Abschnitte, benachbarten Aufrufmessungen, technische Belege und
Gesamtverifikation gemeinsam archivieren. Original unverändert in gemeinsamer
Ablage und auf unabhängigem Datenträger beziehungsweise bestehendem Backup
erhalten; beide SHA-256 prüfen. Zuordnung und tatsächlichen Sicherungsstand im
[Ergebnisindex](results_index.md) gemäß [Archivregel](results_archiving.md)
führen. Keine großen Archive in Git; GitHub-Uploads optional.
