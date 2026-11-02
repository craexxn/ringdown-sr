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

## Ausführung auf Manjaro nach Übernahme des geprüften Implementierungsstands

Ein neuer wissenschaftlicher Lauf benötigt nach Prüfung und Merge eine
gesonderte Freigabe und einen neuen Ausgabenamen. Die nachstehenden Befehle
beschreiben den ursprünglichen Ablauf; vorhandene Teilstände nicht entfernen
oder unter ihrem Namen erneut starten.

Ein sauberes Checkout ist erforderlich. Wenn `main` bereits an ein anderes
Worktree gebunden ist, kann dieses Checkout nach Prüfung lokaler Änderungen
auf den neuen Stand von `origin/main` losgelöst wechseln:

```bash
git status --short
git fetch origin
git switch --detach origin/main
env -u VIRTUAL_ENV uv sync --locked --dev --python 3.12.14
git rev-parse HEAD
git status --short
sha256sum results/representation-manjaro-001.tar.gz
```

Vor dem Start muss der angezeigte Commit den freigegebenen Implementierungsstand
enthalten. Vorhandene Ergebnisverzeichnisse werden abgelehnt.
Die folgenden Befehle enthalten keine zsh-Kommentarzeilen:

```bash
env -u VIRTUAL_ENV OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run --locked --python 3.12.14 python scripts/run_search_trajectory.py --archive results/representation-manjaro-001.tar.gz --label manjaro --output results/trajectory-manjaro-001
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

Ein vollständiges Paket lässt sich anschließend archivieren:

```bash
tar -czf results/trajectory-manjaro-001.tar.gz -C results trajectory-manjaro-001
sha256sum results/trajectory-manjaro-001.tar.gz
```

Die Prüfsumme dokumentiert die Konsistenz des Archivs, keine externe Authentizität.
Die Diagnose liefert einen deskriptiven Entwicklungsbefund; physikalische
Identifikation bleibt `not_assessed`, der Alias-Blindfleck bei `8*fs` bestehen.
Aktueller Implementierungs- und Prüfstand: [Fortsetzungsstand](representation_implementation_status.md).
