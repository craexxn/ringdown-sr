# Bedienung: Trigonometrischer Grammatikvergleich

Der [angenommene Plan](trigonometric_grammar_plan.md) ist am Commit
`5de1a4a0bbb8282ac77f06e21f0314acaa99eade` eingefroren, SHA-256
`e8fe21344cedc93196d77e83918eb989907fe75e7cfa7219ee17d22661be70b5`.
Verglichen werden sechs frische freie Suchen: unbeschränkte Grammatik K gegen
A ohne trigonometrische Nachfahren unter `sin/cos`. Beide Arme verwenden
100/2, beide Häufigkeitsschalter und die ursprüngliche Sekundenkoordinate.
Eine Ringdown-Formel wird nicht vorgegeben. Dies ist ein Entwicklungsvergleich,
keine allgemeine Leistungsvalidierung oder Freigabe der Hauptversuche.

## Technische Prüfung

Im Projektordner mit dem bestehenden [Python-/Julia-Startweg](julia_startup.md):

```bash
env -u VIRTUAL_ENV uv run --locked ruff check .
env -u VIRTUAL_ENV uv run --locked ruff format --check .
env -u VIRTUAL_ENV uv run --locked pytest -q
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/check_trigonometric_grammar_integration.py --output results/grammar-technical-001
```

Die Integration prüft sechs Optionsobjekte ohne Fit, 28 native Syntaxfälle
(je Arm sechs erlaubte Formen und acht direkte/entfernte trigonometrische
Verschachtelungen), feste 250-/4346-/33018-Hz-Referenzen ohne Optimierung sowie
Einheiten-/Seed-/Profilgegenfälle. Danach folgen drei frische K–A–K-Worker
mit je zwei Suchiterationen am separaten Achtpunkt-Signal `y=1+t`.
Beide K-Originalfronten müssen identisch sein. A muss die Grammatikregel auf
allen exportierten Kandidaten einhalten. Keine wissenschaftliche Zelle läuft
in dieser Prüfung. Die vollständige technische CI bleibt zusätzlich erforderlich.

Eine gesonderte Optionsvorprüfung ist möglich:

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_python.py scripts/check_trigonometric_grammar_backend.py --mode options --output results/grammar-options-001.json
```

`--mode references` führt stattdessen Syntax- und numerische Referenzprüfungen
ohne Fit/Suche aus. Beide Vorprüfungen sind auch Bestandteil der späteren Serie.
Freie Worker starten danach separat und übernehmen keine Referenzbäume oder
RNG-Zustände. Der interne Profilworker ist kein eigenständiger Suchbefehl.

## Einmalige wissenschaftliche Serie auf Manjaro

Erst nach vollständig bestandener technischer CI am dokumentierten Head
ausführen. Den genauen Implementierungscommit aus dem PR verwenden; ein späterer
Merge ist nur bei bestätigter Baumgleichheit derselbe geprüfte Dateistand.
Kein automatischer Merge oder Start. Vor der Serie:

```bash
git status --short
git rev-parse HEAD
sha256sum results/representation-manjaro-001.tar.gz
```

Der Worktree muss sauber sein. Erwarteter Archivhash:
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Dieses frühere Originalarchiv dient nur als Datenquelle; kein Archivcode wird
ausgeführt. Der Treiber prüft Hash und Arraybits selbst. Diagnosegitter und
Wahrheitsparameter gehen nicht an die Suche.

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked python scripts/run_trigonometric_grammar.py --archive results/representation-manjaro-001.tar.gz --output results/grammar-manjaro-001 --label manjaro
```

Das neue Ausgabeverzeichnis darf noch nicht existieren. Es laufen genau die
sechs geplanten Zellen; nach Fehler/Abbruch keine automatische Wiederholung.
600 Sekunden je Suchworker, insgesamt 60 Minuten einschließlich Vorprüfungen,
Start, Export und Abschlussverifikation. Das ist eine Obergrenze und keine
Laufzeitprognose. Bei Ressourcen-/Verifikationsfehler bleiben Teilstände erhalten;
die eigenen Workerprozessgruppen werden beendet. Ein bestehender fremder
Wandzeittimer wird nicht überschrieben. Dieser Pfad ist für Linux/Manjaro vorgesehen.

Nach Abschluss oder Abbruch die vorhandenen Originalartefakte unverändert sichern:

```bash
tar -czf results/grammar-manjaro-001.tar.gz -C results grammar-manjaro-001
sha256sum results/grammar-manjaro-001.tar.gz
```

Existiert dieses Archiv bereits, einen neuen Sicherungsnamen verwenden und
das vorhandene Archiv erhalten. Ein Abbrucharchiv bleibt ein Teilbefund;
Archivierung bedeutet keine bestandene Abschlussprüfung.

## Artefakte und Aussagegrenzen

- `plan.md`, `training.npz`, `diagnostic.npz`, `runtime/`: gebundener Plan,
  getrennte Datenrollen und Laufzeitkopien. Vorher eingefrorene Quellen-/Pin-/
  Dateihashes werden vor und nach Verbrauch sowie abschließend geprüft.
- `options.json`, `references.json` und Logs: absolute native Optionsprüfung
  für jedes Profil/Seed, konkrete Plugins, unveränderte 100/2-Einstellungen,
  vollständige Verschachtelungspaare und native Referenz-/Syntaxfälle.
- `cell-01/` bis `cell-06/`: Requests, Profile, Manifeste, Originalfronten,
  Auswahlindex, ursprüngliche Bäume, Vorhersagen, Residuen, MSE, Backend- und
  BLAS-Nachweise. Kein Reranking oder Nachfit; Widersprüche stoppen.
- `report.json`, `summary.md`: getrennte Kurven-, Struktur-, Parameter- und
  Replaybefunde. Fehler auf beiden Rastern, endliche Nenner, Kosten pro Seed,
  A-minus-K-Differenzen und Erfolgswechsel. Die zusätzliche Nullauswertung
  nach Fit bleibt vom Fit-Callbackzähler getrennt. Keine neue Suchhistorie.
- `checksums.json`: Paketkonsistenz gegen ursprüngliche Anker, keine externe
  Authentifizierung der Ausführung. Konsistente nachträgliche Neuhashung ersetzt
  keine Verbrauchsanker. Positive Berichte werden erst nach vollständiger
  Abschlussprüfung veröffentlicht und bei Fehlern der Abschlussphase widerrufen.

Bei unvollständiger Serie bleiben Aggregate und Paardifferenzen `null`.
Verifizierte Einzelresultate bleiben sichtbar; gute ungewählte Kandidaten zählen
nicht als erfolgreiche Originalauswahl. `C_A > C_K` plus unterstützte abklingende
Struktur und bestandenes Parameterreplay derselben kurvenguten A-Auswahl ist
nur ein positives Entwicklungssignal. Ohne Vergleichsvorteil ist die Hypothese
nicht gestützt; kleinere Fehler ändern den primären Zählendpunkt nicht.
Der Plan legt die Weiterentscheidungen fest, keine davon startet automatisch
einen weiteren Lauf. `physical_identification` bleibt `not_assessed`, der
Alias-Blindfleck bei `8*fs` bleibt bestehen. Gleiche nominale Budgets bedeuten
keine gleiche verbrauchte Rechenzeit und keinen fertigen Hauptversuchsplan.
