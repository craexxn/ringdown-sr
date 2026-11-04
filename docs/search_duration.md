# Bedienung: Vergleich des äußeren Suchbudgets

Der [Methodenplan](search_duration_plan.md) wurde vor Implementierung am Commit
`194cfb499e8c53b8243d19c4d11d58a006baff95` eingefroren, SHA-256
`8906a66930848d733e5b2744d40c5fa9c4051db2b876e200908d74ae9ac0b75d`.
Die [Literaturgrundlage](search_duration_literature.md) begründet die
Budgetprüfung, keinen optimalen Iterationswert oder garantierten Erfolg.

Der erste Lauf blieb [beim Replay unvollständig](search_duration_results_manjaro_001.md).
Seit Format 2 gilt zusätzlich die vor Code eingefrorene
[Verifikationsergänzung](search_duration_verification_plan.md), Commit
`2a0b50926cd2983d0cd6cc1307ccc28d0a2822fa`, SHA-256
`b6f7cef2227eeacccf8156d02e8899e6fc83b7bd1f29735c1a402922a9d83062`.
Die zusätzlich gebundene [Tabellenpräzisierung](search_duration_table_loss_note.md)
trennt Pandas-CSV-Einlesen von nativer Reduktion: Commit
`fee62058992c84a9930aa765233ebdc095c54cb1`, SHA-256
`56c0807127ff208148df9057607c698218bf87b0cdcf73471b58add14485372c`.
Auch der [zweite Lauf](search_duration_results_manjaro_002.md) blieb unvollständig:
vier verifizierte Zellen, danach inkonsistenter gespeicherter nativer Verlust.
Format 3 bindet die [Abhilfe ohne automatische Vereinfachung](search_duration_simplification_plan.md),
Commit `f13d7687ddd06d5c68fbbf7ae5baa67639d74ca3`, SHA-256
`46fb2510957a4ee37d3f61e59291b8a5081db9ff64e7bd36a62aad0073901a0d`.
`should_simplify=false` gilt für alle Zellen. Die Formelsprache bleibt gleich,
die Suchtrajektorien können sich ändern; frühere Zellen werden nicht vermischt.
Auch [Lauf 003](search_duration_results_manjaro_003.md) ist nach vier
verifizierten Zellen unvollständig: Zelle 5 scheiterte diesmal beim
Python-/Julia-Vorhersagevergleich. Alle zehn CSV-Verluste werden nativ
bitgenau reproduziert; kleine Rundungsunterschiede überschreiten bei vier
CSV-Bäumen die Vorhersagegrenze. Die folgenden Startbefehle dokumentieren
den historischen Laufweg. Der separat geprüfte und mit #58 übernommene
[Methodenplan](search_duration_prediction_plan.md) wird in Format 4 umgesetzt:
Rundungsintervalle, unabhängige Breitenbegrenzung und erneute Elternnachrechnung.
Bindung an den erreichbaren Merge-Commit `9bff8a29030026dcdc2de52640556a73a57fe2a4`,
SHA-256 `2a215b6f178c085cad6611070124e09e929f35917eba66723f4522c1fe81393c`.
Der [Lauf 004](search_duration_results_manjaro_004.md) ist mit allen 20 Zellen
abgeschlossen und unabhängig nachgerechnet. Die Befehle unten dokumentieren
diesen abgeschlossenen Laufweg, keine Wiederholungsfreigabe.

20 frische Suchen kreuzen K/A mit 200/2.000 Suchiterationen bei denselben fünf
vorab festgelegten Seeds. Sie sind nach dem Teilstand nicht mehr vollständig
ungesehen. Konstantenoptimierung 100/2, Populationen, Daten,
Originalauswahl und Diagnosegrenzen bleiben gleich. Keine Wiederaufnahme
kurzer Läufe und keine Übernahme früherer Zellen als neue Kontrollen.

## Technische Voraussetzung

Die vollständige technische CI muss am dokumentierten Implementierungs-Head
bestanden sein. Ein späterer Merge ist nur bei bestätigter Baumgleichheit
derselbe geprüfte Dateistand. Kein eigenständiger Merge durch diesen Ablauf.
Bei einem Squash-Merge fehlen im lokalen `main`-Verlauf möglicherweise die
vor Code eingefrorenen Plankommits. Vor den lokalen Tests zusätzlich den
PR-Head dieser Änderung und den von #55 holen; der zweite Befehl erhält den
historischen Tabellenplan auch in einem frischen Checkout:

```bash
git fetch origin main
git fetch origin refs/pull/55/head:refs/remotes/origin/pr-55
```

Den neuen PR-Head ebenfalls in einer lokalen Remote-Referenz erhalten
(der konkrete Befehl steht im PR). Nach Merge den geprüften, baumgleichen
Stand mit `git switch --detach` verwenden; ein bereits in einem anderen
Worktree belegtes `main` muss nicht gewechselt werden. Eine unvollständige
Historie ist kein Grund, Planprüfungen zu überspringen.

Lokale technische Integration bei Bedarf:

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/check_search_duration_integration.py --output results/duration-technical-001
```

Sie prüft zehn native Optionsobjekte und 20 Pythonprofile, feste Referenzen
und Grammatikgegenfälle. Fünf frische Worker laufen ausschließlich am separaten
Achtpunkt-Signal `y=1+t`: K2, A2, K3, A3, K2. Der tatsächliche Aufruf an
`equation_search` wird auf das jeweilige Budget geprüft; beide K2-Fronten
müssen identisch sein. Dieser Test führt keine wissenschaftliche Zelle aus.

Zusätzlich prüft die volle CI mit `scripts/check_duration_replay.py` die zwei
früheren CSV-Bäume, die weiterhin abzulehnende Verlustabweichung aus Zelle 5
und einen unabhängigen Achtpunkt-Gegenfall für beide nativen
Vereinfachungspfade sowie die deaktivierte Simplify-Mutation, ohne Suche/Fit. Die Fixture ist ein ausdrücklich
nachträglicher Regressionstest, kein wiederhergestellter Originalbaumexport.

## Baumabhängige Vorhersageprüfung ab Format 4

`prediction_reference.py` verwendet die neue gepinnte Abhängigkeit
`gmpy2==2.2.2` für gerichtete MPFR-Operationen; Grundrechenarten, Binary64-
Rundung und Breitenentscheidungen verwenden exakte rationale Werte. Die
Referenz läuft direkt im jeweiligen Python-Prozess, auch im Elternprozess.
Daher entsteht weder ein zusätzlicher Referenzprozess noch ein neuer Julia-
Start pro Kandidat. Lokale MPFR-Kontexte werden nach jedem Aufruf restauriert;
die Float64-Rundungsumgebung der Suche bleibt unberührt. Die tatsächlich
verwendeten gmpy2-/MPFR-/GMP-Versionen werden in jedem Nachweis erfasst.

Die Konstruktion erhält ausschließlich vollständige validierte Bäume und
Zeitbits. Beobachtungen, tatsächliche Vorhersagen und Auswahl gehen nicht in
Intervall, Präzision oder Skala ein. Nach der ersten ausreichend engen
Einschließung aus 128/256/512/1024 Bit müssen beide tatsächlichen Vorhersagen
punktweise darin liegen. Die Regel ist keine allgemeine Bibliotheksgarantie.
Sie prüft Vereinbarkeit mit dem festgelegten Rundungsmodell, nicht die
Authentizität oder den tatsächlich durchlaufenen internen Rundungspfad.

`prediction_replay` enthält Quellen-/Planbindung, Baumhash, Zeitfingerprint,
Bibliotheksversionen, exakte Hex-Endpunkte, rationale Skala/Maximalbreite,
Präzisionsversuche und Mitgliedschaft. Der Elternprozess berechnet alles
für sämtliche Kandidaten neu und vergleicht den gespeicherten Beleg vollständig.
Es gibt keinen Cache. Bei einem unbestimmten oder fehlgeschlagenen Referenz-
nachweis hält der Worker zusätzlich `prediction_failure.json` fest und bricht ab.
Der Aufwand zählt unverändert in 600/7200 Sekunden einschließlich Elternarbeit.

Nur der dedizierte Worker-Hook, die explizite Dauervergleich-Option von
`parameter_export._candidate` und der zugehörige Verlustnachweis ersetzen den
alten Vorhersagevergleich. `_check_prediction_replay`, Parameter-, Alias-
und ältere Kontrollpfade bleiben unverändert. Verlustnachweise tragen im
neuen Pfad Version 2; ältere Aufrufer behalten Version 1. Die alte relative
Vorhersagegrenze ist im Format-4-Trainingspfad kein zusätzliches verstecktes Gate.

## Versionierte Verlustverifikation

Nur der neue Suchbudgetworker aktiviert `duration_replay.verify_loss_replay`;
der Standardadapter und ältere Kontrollpfade behalten ihre bisherige skalare
Prüfung. Jeder Kandidat erhält einen `loss_replay`-Nachweis. Der Elternprozess
prüft dessen Inhalt erneut einschließlich Tabellenverlust, unabhängiger
Python-MSE und Fehlergrenze. Fehlende oder veränderte Nachweise sperren die
Serie. Die Originalauswahl verwendet weiterhin den gespeicherten nativen
Trainingsverlust, keine korrigierte oder diagnostische MSE.
Der Tabellenwert bleibt als tatsächlich von PySR/Pandas gelesener Wert
erhalten; für ihn gilt der unveränderte Vergleich `rtol=1e-10, atol=0` zum
nativen Verlust. Die Gamma-Schranke prüft echte Reduktionswerte gegen ihre
Residuen, nicht zusätzlich die Rundung des CSV-Parsers.

Die rationale Schranke im gebundenen Plan ist ein Genauigkeitsvertrag einer
direkten Quadratsummenreduktion. Die vorhandene Python-Funktion verwendet
tatsächlich eine skalierte BLAS-Norm, Division durch sqrt(n) und Quadrieren;
sie wird nicht ersetzt. Ihr konkretes Ergebnis wird unabhängig gegen die
exakte rationale Quadratsumme geprüft. Es wird **keine allgemeine
Fehlergarantie für jede BLAS-Implementierung** vorausgesetzt. Überschreitet
ein Ergebnis die Schranke, bleibt es abgelehnt. Der normale Zahlenbereich
gilt auch für Quadrate und unnormalisierte Quadratsumme; Unter-/Überlauf wird
nicht durch einen absoluten Größenboden verdeckt.

Der optionale Strukturerkenner und die Parameterdiagnose tragen Version 2.
Sinusphasen behalten getrennte rationale Radiant- und Pi-Anteile; die
Umrechnung wird durch rationale Pi-Intervalle geprüft. Nur der neue
Suchbudget-Diagnosepfad aktiviert Produkte/Quotienten mit Sinus oder Kosinus.
Ältere Aufrufer nutzen weiterhin den bisherigen Erkenner. Beide numerischen
Parameterreplays, Kurvengrenzen und ursprüngliche Diagnosegates bleiben nötig.

## Historischer Laufweg: Serie 003 auf Manjaro

Im sauberen Checkout des geprüften Commits mit der bestehenden gepinnten
[Python-/Julia-Umgebung](julia_startup.md) prüfen:

```bash
git status --short
git rev-parse HEAD
sha256sum results/representation-manjaro-001.tar.gz
```

Erwarteter Eingangsarchivhash:
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Das frühere Originalarchiv ist Datenquelle; sein Code wird nicht ausgeführt.
Der Treiber prüft Archivhash und Float64-Bits selbst. Diagnosepunkte und
Wahrheit gelangen nicht an die Suchworker.

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_search_duration.py --archive results/representation-manjaro-001.tar.gz --output results/duration-manjaro-003 --label manjaro
```

Das Ausgabeverzeichnis muss neu sein. **600 Sekunden je Worker, insgesamt
7.200 Sekunden einschließlich Vorprüfungen und Abschlussverifikation.**
Die Gesamtgrenze ist keine Laufzeitprognose. Fehler oder Zeitüberschreitung
beenden die eigenen Prozessgruppen; Teilstände bleiben erhalten. Keine
automatischen Wiederholungen, Ersatzseeds oder Verlängerungen. Ein bestehender
fremder Timer wird nicht überschrieben. Dieser Pfad ist für Linux vorgesehen.

Nach Abschluss oder Abbruch unverändert sichern:

```bash
tar -czf results/duration-manjaro-003.tar.gz -C results duration-manjaro-003
sha256sum results/duration-manjaro-003.tar.gz
```

Bestehende Archive erhalten; gegebenenfalls einen neuen Sicherungsnamen
verwenden. Archivierung allein bedeutet keine bestandene Abschlussprüfung.

## Artefakte und Einordnung

- `plan.md`, getrennte Trainings-/Diagnosedateien und `runtime/` binden Plan,
  Eingaben und konsumierte Quellen. Ursprüngliche Verbrauchsanker bleiben
  gegenüber späterer Neuhashung maßgeblich.
- `options.json` enthält zehn native Seed-/Grammatikprofile und alle 20
  Pythonprofile. `references.json` prüft feste Syntax-/Einheiten-/Aliasfälle.
- `cell-01/` bis `cell-20/` erhalten vollständige Originalfronten, Auswahlindex,
  Bäume, Vorhersagen, Residuen, MSE, native Options-/Plugin-/BLAS-Nachweise.
  `search_invocation.json` bestätigt den einen abgeschlossenen Aufruf mit
  angefordertem Budget ohne Warmstart, Gewichte oder Startformeln.
- `report.json` und `summary.md` zeigen Originalauswahlen und getrennte
  Befunde. Vier Gruppen, 20 Seedpaare, Fehlerwerte mit Verfügbarkeit und
  endlichen Nennern, Erfolgswechsel und Kosten bleiben nachvollziehbar.
- `checksums.json` sichert Paketkonsistenz, keine externe Authentifizierung.
  Positive Berichte werden zuletzt veröffentlicht und bei Abschlussfehlern
  widerrufen.

Erst alle 20 verifizierten Zellen und eine bestandene Abschlussprüfung geben
Gruppenaggregate und Paardifferenzen frei. Bei einem Abbruch bleiben sie `null`;
verifizierte Einzelresultate bleiben sichtbar. Kein Reranking oder Nachfit.

Primär wird innerhalb jeder Grammatik die Erfolgszahl bei 2.000 mit jener
bei 200 verglichen. Mehr Erfolge plus mindestens eine neu erfolgreiche,
strukturell und im Parameterreplay unterstützte Originalauswahl sind ein
positives Entwicklungssignal. Eine bessere Approximation allein bestätigt
keine freie Strukturentdeckung. Die Grammatikunterschiede und ihre
Wechselwirkung mit dem Budget bleiben getrennt sichtbar.

Fünf vorab festgelegte, teilweise bereits gesehene Seeds am bekannten Signal
sind keine allgemeine Leistungsvalidierung.
Physikalische Identifikation bleibt `not_assessed`; der Alias-Blindfleck bei
`8*fs` bleibt bestehen. Weitere Tests werden erst anhand der neuen Ergebnisse
begründet und vor Ausführung festgelegt.

## Abgeschlossener Laufweg: Serie 004 auf Manjaro

Ausgeführt nach vollständiger CI, gezieltem KI-basiertem Implementierungsreview
und Squash-Merge von #59 im sauberen Stand
`79ff670b825efd8ba0e999edb983aec6f7e804ae`. Alle 20 Zellen liefen frisch;
keine Teilstände wurden fortgesetzt. Den Ergebnisordner und das Originalarchiv
erhalten. Die folgenden historischen Befehle sind keine Freigabe weiterer Suchen.

```bash
(
  set -e
  test -z "$(git status --porcelain=v1 --untracked-files=all)"
  export OPENBLAS_CORETYPE=Haswell
  export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
  export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
  env -u VIRTUAL_ENV uv sync --locked --dev --python 3.12.14
  env -u VIRTUAL_ENV uv run --locked --python 3.12.14 \
    python scripts/run_python.py scripts/check_environment.py
  env -u VIRTUAL_ENV uv run --locked --python 3.12.14 \
    pytest -q tests/test_prediction_reference.py tests/test_duration_verification.py \
    tests/test_search_duration_driver.py tests/test_search_duration.py
  printf '%s\n' \
    'a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db  results/representation-manjaro-001.tar.gz' \
    | sha256sum --check --strict
  test ! -e results/duration-manjaro-004
  test ! -e results/duration-manjaro-004.tar.gz
  run_status=0
  env -u VIRTUAL_ENV uv run --locked --python 3.12.14 \
    python scripts/run_search_duration.py \
    --archive results/representation-manjaro-001.tar.gz \
    --output results/duration-manjaro-004 --label manjaro || run_status=$?
  if test -d results/duration-manjaro-004; then
    tar -czf results/duration-manjaro-004.tar.gz -C results duration-manjaro-004
    sha256sum results/duration-manjaro-004.tar.gz
  fi
  exit "$run_status"
)
```

Mit der gemeinsamen Auswertung des vollständig verifizierten Laufs 004 ist
die vorgemerkte kurze Bestandsaufnahme zur gezielten Bereinigung jetzt fällig. Zuerst Code und Originalergebnisse sichern; danach nur konkrete
Wartungsprobleme mit kleinen getrennten Regressionen behandeln. Keine große
Umstrukturierung, keine Änderung numerischer Reihenfolge oder historischer
Lesbarkeit. Erfolgreiche technische Tests allein lösen diesen Folgeschritt
noch nicht aus.
