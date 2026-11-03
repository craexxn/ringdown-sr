# Begrenzte Beobachtung der freien Suche

Der [angenommene Methodenplan](search_trajectory_plan.md) bindet genau sechs
frische 100/2-Suchen: je Entwicklungsseed ein Lauf ohne und ein Lauf mit
Beobachtung. Er erfasst zurückgegebene Populationen und die globale Hall of Fame.
Die ursprüngliche Front und Auswahl bleiben erhalten; aufgezeichnete
Zwischenbäume werden ausschließlich nach dem Fit diagnostiziert.

Die [gebundene Verifikationsergänzung](search_trajectory_replay_policy.md)
gilt für neue Format-2-Pakete. Sie unterscheidet gespeicherte Backendwerte,
aktuelle native Replays und Python-Baumauswertung. Der erste Format-1-Lauf
`trajectory-manjaro-001` bleibt als `incomplete / failed` erhalten.
Die Korrektur autorisiert keine automatische Wiederholung.

Die anschließend vereinbarte Serie `trajectory-manjaro-002` ist am 03.11.2026
abgeschlossen. Ihr [Originalarchiv ist geprüft](search_trajectory_results_manjaro_002.md):
sechs Zellen und drei Paarvergleiche bestanden; ungeklärte Mitglieder bleiben
entsprechend eingeschränkt. Die nachstehenden Befehle dokumentieren diesen
abgeschlossenen Lauf und sind kein Auftrag für einen erneuten Start.

## Technische Voraussetzungen

Vor der wissenschaftlichen Ausführung muss der Implementierungsstand die
vollständige technische CI bestehen. Dazu gehören Options- und Pluginprüfungen,
technische Aufnahmen mit RNG-/Zustandsschutz, Fehlergegenfälle und drei frische
aus/an/aus-Worker mit nur zwei Suchiterationen auf einem eigenen Achtpunkt-Signal.
Diese technischen Worker sind keine wissenschaftlichen Kontrollzellen.

Die wissenschaftliche Serie nutzt den bestehenden Manjaro/Linux-Pfad mit
Prozessgruppen und einem Gesamtzeitlimit. Haswell und vier Threadlimits auf 1
gelten nur für diese Diagnose. Python-/Julia-Pins und alle Trainingsrollen
bleiben unverändert.

Der lesende Eingang ist `representation-manjaro-001.tar.gz`, SHA-256
`a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
Der Treiber prüft dieses Originalarchiv einschließlich der eingefrorenen
Eingaben. Das neuere freie Budgetarchiv wird dafür nicht benötigt; dessen
weiterhin offener unabhängiger Audit wird durch die Beobachtungsserie nicht ersetzt.

## Abgeschlossene Ausführung auf Manjaro: trajectory-manjaro-002

Stand 03.11.2026: PR #48 ist übernommen. Die
[vollständige CI](https://github.com/craexxn/ringdown-sr/actions/runs/41437880627)
bestand am PR-Head `27d10fe`; dessen Dateibaum stimmt mit dem Mergecommit
`f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1` überein. Nach Merge und
Standabgleich wurde genau eine frische Serie an diesem Commit vereinbart.
Der verwendete Name lautet `trajectory-manjaro-002`; Ausführung und Audit
sind im Ergebnisbericht nachgewiesen. Das alte Verzeichnis und Teilarchiv
bleiben erhalten. Der reine Dokumentationsnachtrag war keine Voraussetzung
für den Lauf am festgelegten Commit.

Die folgenden Befehle im Repository-Stamm ausführen. Ein sauberes Checkout
ist erforderlich; bei lokalen Änderungen stoppt die Vorbereitung. Der
losgelöste Checkout bindet den geprüften Commit auch dann, wenn `main` später
weiterläuft oder bereits an ein anderes Worktree gebunden ist:

```bash
git status --short &&
git fetch origin &&
test -z "$(git status --porcelain=v1 --untracked-files=all)" &&
git switch --detach f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1 &&
test "$(git rev-parse HEAD)" = f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1 &&
env -u VIRTUAL_ENV uv sync --locked --dev --python 3.12.14 &&
env -u VIRTUAL_ENV uv run --locked --python 3.12.14 python scripts/run_python.py scripts/check_environment.py &&
printf '%s\n' 'a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db  results/representation-manjaro-001.tar.gz' | sha256sum --check --strict
```

Nur nach erfolgreicher Vorbereitung starten. Der Start prüft Commit und
Checkout nochmals sowie das Fehlen des neuen Ausgabeordners und Archivs.
Vorhandene Ausgaben nicht entfernen, um diese Prüfungen zu umgehen:

```bash
test "$(git rev-parse HEAD)" = f3c0cb49ff9213b651ad4cb4ce766958f0b1e2d1 &&
test -z "$(git status --porcelain=v1 --untracked-files=all)" &&
test ! -e results/trajectory-manjaro-002 &&
test ! -L results/trajectory-manjaro-002 &&
test ! -e results/trajectory-manjaro-002.tar.gz &&
test ! -L results/trajectory-manjaro-002.tar.gz &&
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked --python 3.12.14 python scripts/run_search_trajectory.py --archive results/representation-manjaro-001.tar.gz --label manjaro --output results/trajectory-manjaro-002
```

Keine Wiederaufnahme, Ersatzseeds oder automatische Wiederholung bei Fehlern.
Teilstände und Protokolle erhalten; Ursache vor einem gesondert beschlossenen
weiteren Vorgehen prüfen. Für die vereinbarte Serie gelten:

- insgesamt höchstens 3600 Sekunden einschließlich Vorprüfung, Auswertung
  und abschließender Verifikation;
- je Worker höchstens 600 Sekunden, zusätzlich begrenzt durch die Restzeit;
- je beobachteter Zelle höchstens 256 MiB Beobachtungsdateien, insgesamt
  höchstens 768 MiB; Überschreitungen führen zum Abbruch.

## Artefakte und Auswertung

`report.json` und `summary.md` führen alle sechs Zellen und ihre Zustände.
`checksums.json` gehört zum vollständig verifizierten Abschlusspaket.
Eine Fehler- oder Abbruchsituation darf keinen positiven Abschlussbericht
zurücklassen; die vergleichende Interpretation bleibt dann gesperrt.

Die Zellverzeichnisse enthalten die unveränderten Suchausgaben, Originalfronten,
Auswahlindizes, konkrete Backendoptionen, Seeds, Kontrollnachweise und Laufzeiten.
Hook-Zeit, nachgelagerte Einheitenprüfung, nativer Replay und Offlineauswertung werden
gesondert ausgewiesen. Die Fit-Zeit enthält JIT und Python-Exporte sowie
bei eingeschalteter Beobachtung deren Aufwand; sie ist keine reine Suchzeit.
Beobachtete Zellen enthalten zusätzlich `observations.jsonl` mit den rohen
Aufnahmen, `observation_units.json` mit der nachgelagerten Einheitenprüfung
und `observation_replays.json` mit nativen Verlust-/Vorhersagebits.
Der Replayexport bindet Trainingsdatei, Rohaufnahme und Einheitenstatus;
alle drei Beobachtungsdateien zählen gemeinsam gegen die 256-MiB-Grenze.
Die konstanten Float64-Bits bleiben in den Rohbäumen erhalten, auch für
nichtendliche Werte. Technische Auswertungen sind von unverändert aufbewahrten
Rohaufnahmen zu unterscheiden.

Die Auswertung berichtet Aufnahmen, Mitgliedspositionen und eindeutige Bäume
mit ihren jeweiligen Nennern. Population, Hall of Fame und endgültige
Frontzugehörigkeit sind getrennt. Fehlende Frontzugehörigkeit beweist kein
zeitliches Verschwinden. Eine spätere nicht zuordenbare Population belegt
ebenfalls kein Verschwinden aus der zuvor beobachteten Population.

Eine vergleichende Interpretation verlangt sechs vollständige Zellen,
drei bestandene Vergleiche der ursprünglichen Suchausgaben und eine bestandene
Abschlussverifikation. Für die Beobachtung erwartete Dateien und Laufzeiten
sind gesondert geprüft; die Originalfronten und Fit-Callbackzahlen müssen exakt
übereinstimmen. Zwischenbäume ersetzen niemals die ursprüngliche Auswahl.
Nichtendliche oder semantisch ungültige Mitglieder bleiben sichtbar und
können keinen positiven Rekonstruktionsbefund erzeugen.

Numerische Widersprüche zwischen gespeicherten und nachgerechneten Werten
werden pro Vorkommen als `numerical_unresolved` mit konkreten Gründen
erhalten. Kurzfassung und JSON nennen bestätigte, ungeklärte und nicht
beurteilte Mitgliedspositionen sowie ihre Nenner. Ein vollständiger Abschluss
bestätigt die Erfassung und Klassifikation; er bestätigt nicht jeden Baum
numerisch. Ein Baum mit gemischten bestätigten/ungeklärten Vorkommen erhält
keinen uneingeschränkten positiven Gesamtmarker.

Fehlende oder widersprüchliche Replaynachweise, beschädigte Dateien sowie
Fehler in Endfront, Originalauswahl oder Paarvergleich bleiben Abbruchgründe.
Native MSE und Python-MSE aus denselben nativen Vorhersagen müssen weiterhin
konsistent sein. Die bisherigen Toleranzen werden nicht gelockert.

Nach Beendigung des Prozesses auch einen etwaigen Teilstand archivieren.
Das Archiv darf nicht bereits existieren; bei einer fehlgeschlagenen
Archivierung den Fehler klären, bevor eine vorhandene Datei ersetzt wird:

```bash
test -d results/trajectory-manjaro-002 &&
test ! -e results/trajectory-manjaro-002.tar.gz &&
test ! -L results/trajectory-manjaro-002.tar.gz &&
tar -czf results/trajectory-manjaro-002.tar.gz -C results trajectory-manjaro-002 &&
sha256sum results/trajectory-manjaro-002.tar.gz
```

Die Prüfsumme dokumentiert die Konsistenz des Archivs, keine externe Authentizität.
Die Diagnose liefert einen deskriptiven Entwicklungsbefund; physikalische
Identifikation bleibt `not_assessed`, der Alias-Blindfleck bei `8*fs` bestehen.
Aktueller Implementierungs- und Prüfstand: [Fortsetzungsstand](representation_implementation_status.md).
