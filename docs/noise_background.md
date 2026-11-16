# Laufweg für die begrenzte Hintergrundstudie

Stand 16.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md).
Der [beschlossene Plan](noise_background_plan.md) ist unverändert an Commit
`0c4b52868d8cc9809f38db02fe066ab540bcfeb3` und SHA-256
`d3bb289cf4a2ac75a31f88c34721ca72da348c5af6d9d6a3917d4a6cc90f52f7`
gebunden. PR94 ist als `8b8b3569dd78ca2282704d2799d81fe1d73bfb42`
übernommen. Sein eingefrorener Hinweis „noch nicht implementiert“ bezeichnet
den Stand des Protokollbeschlusses; aktuelle Umsetzung und Prüfbelege stehen
im [Fortsetzungsstand](representation_implementation_status.md).

Der neue Laufweg ist mit [PR #95](https://github.com/craexxn/ringdown-sr/pull/95)
nach vollständiger Ready-CI ausdrücklich freigegeben und als
`bd42634b888c2dbaa5a92726b9a1f9851c766a48` übernommen. Der technische
Manjaro-Vorlauf `noise-background-preflight-manjaro-001` ist einschließlich
aller fünf Worker, Originalformeln, Punktdaten und Plots lesend bestätigt.
Die Ressourcenbelege geben keinen Anlass zur Änderung der festgelegten Fristen;
Prüfkosten und Aussagegrenzen stehen im
[Fortsetzungsstand](representation_implementation_status.md), Archivhash und
offener Sicherungsstand im [Ergebnisindex](results_index.md).

**Nächster Schritt ist der separate wissenschaftliche Start ab Abschnitt 3
im unveränderten, bereits geprüften Manjaro-Worktree.** Setup und Vorlauf für
diesen Lauf nicht wiederholen. Noch keine wissenschaftliche Suche dieser
Studie ist gestartet. Die folgenden Befehle ändern keine Methodenparameter;
ein späterer Dokumentationscommit ersetzt den gebundenen Ausführungsstand nicht.

## Umfang und feste Grenzen

20 frische AR(1)- und sechs frische white-Blöcke erhalten jeweils fünf Arme:
O, K, E64, E256 und E1024. Ein Viererpaket mit 1.000 äußeren Iterationen je
Mitglied und lokal 300/5 liefert genau eine Originalausgabe: insgesamt
520 geplante Suchen und 130 Paketausgaben. O/K werden je Block nur einmal
ausgeführt. Die drei E-Arme verwenden exakt verschachtelte Präfixe eines
1.024er-Trainingspools; Validierung 128 und Kontrolle 256 bleiben getrennt.

`run_noise_background.py prepare` bindet alle 26 Fälle vor dem ersten Fit
oder Suchaufruf, einschließlich Originalarrays, Seeds, Kovarianzen,
hochpräziser Signalreferenzen und festem Zusatzraster. `run` arbeitet die
eingefrorene Reihenfolge vollständig ab. Endliche native Trainingsverluste,
Komplexität und Mitgliedsposition bestimmen die Paketauswahl. Wahrheit,
Rasterfehler, Familie und Plots sind keine Auswahl- oder Stoppkriterien.

Primär ist künftig der amplitudennormierte Fehler auf den vorab gespeicherten
1.024 unregelmäßigen Punkten, Kontrast E1024 minus O unter AR(1). Der
historische Trainingsendpunkt des 144er-Piloten bleibt unverändert. Alle
acht Kontraste, geplante Nenner 20/6, Ausfälle, kontinuierliche Rasterfehler,
Struktur-/Domainbefunde und Kosten bleiben getrennt. Unsicherheitsintervalle
sind approximativ und marginal; kein automatischer Sieger oder neuer
Bestehensmarker. Details und Anschlussregeln stehen ausschließlich im Plan.

`verify`, `plots` und `technical-plots` lesen vorhandene Ergebnisse; sie
starten keine Fits oder Suchen. Plotexporte erhalten sämtliche geplanten
Ausgaben, auch Ausfälle, vollständige unveränderte Originalformeln und
zugeordnete CSV-/JSON-Werte. Native Trainingsvorhersage und Replay an den
gebundenen Rastern bleiben unterscheidbar. Gezeichnete Verbindungslinien
sind kein Nachweis des Funktionsverlaufs zwischen den Punkten.

## 1. Nach technischer Übernahme einen festen Manjaro-Checkout einrichten

Dieser Schritt ist für `noise-background-preflight-manjaro-001` bereits
abgeschlossen. Die Befehle dokumentieren den festen Ausführungsstand für eine
neue Einrichtung. Im bestehenden Repository starten; ein vorhandenes
Laufverzeichnis nicht überschreiben.

```bash
bash <<'BASH'
set -euo pipefail
task_commit='bd42634b888c2dbaa5a92726b9a1f9851c766a48'
git fetch origin main
git cat-file -e "$task_commit^{commit}"
git worktree add --detach ../ringdown-noise-background-run "$task_commit"
cd ../ringdown-noise-background-run
test "$(git rev-parse HEAD)" = "$task_commit"
test -z "$(git status --porcelain)"
test -f scripts/check_noise_background.py
test -f scripts/run_noise_background.py
unset VIRTUAL_ENV
uv sync --locked --dev --python 3.12.14
git rev-parse HEAD
BASH
```

Alle folgenden Befehle laufen im neuen Verzeichnis
`ringdown-noise-background-run`. Während Vorlauf, wissenschaftlicher Serie
und Verifikation weder `git pull` noch Commitwechsel oder erneutes `uv sync`.
Vorlauf und wissenschaftliche Vorbereitung müssen denselben sauberen Commit
und dieselbe numerische Umgebung binden. Ein späterer reiner Dokumentations-
commit ist dafür ebenfalls ein anderer Stand. Laufartefakte unter `results/`
und die lokale `.venv` sind ignoriert und machen den Git-Arbeitsbaum nicht schmutzig.

## 2. Begrenzter technischer N128-Vorlauf, Verifikation und Plotexport

Dieser Schritt verwendet nur die eigenen technischen Seeds und je einen
Zehnerworker für O/K/E64/E256/E1024. N=128, lokal 300/5; höchstens 600 Sekunden
pro Worker und 7.200 Sekunden für den vollständigen Vorlauf. Signalqualität
ist kein Abnahmekriterium. Der Code muss vor diesem Manjaro-Schritt bereits
lokal, per Review und vollständiger CI abgenommen und übernommen sein.

```bash
bash <<'BASH'
set -euo pipefail
test -f scripts/check_noise_background.py
test "$(git rev-parse HEAD)" = 'bd42634b888c2dbaa5a92726b9a1f9851c766a48'
test -z "$(git status --porcelain)"
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
task_preflight=results/noise-background-preflight-manjaro-001
test ! -e "$task_preflight"
test ! -e "$task_preflight.tar.gz"
uv run --locked python scripts/check_noise_background.py \
  --output "$task_preflight/technical"
uv run --locked python scripts/check_noise_background.py \
  --verify "$task_preflight/technical"
uv run --locked python scripts/run_noise_background.py technical-plots \
  --technical "$task_preflight/technical" \
  --export "$task_preflight/plots"
tar -czf "$task_preflight.tar.gz" -C results noise-background-preflight-manjaro-001
tar -tzf "$task_preflight.tar.gz" > /dev/null
cd results
sha256sum noise-background-preflight-manjaro-001.tar.gz \
  > noise-background-preflight-manjaro-001.tar.gz.sha256
sha256sum -c noise-background-preflight-manjaro-001.tar.gz.sha256
BASH
```

Der gemeinsame Vorlaufordner enthält das technische Original unter
`technical/`, dessen `inputs/`, `inputs-call.json`, fünf Armordner,
Abschluss und `technical_call.json` sowie den separaten `plots/`-Export.
Keine Plotdateien in den streng geprüften technischen Originalordner schreiben.
Das Archiv enthält den gesamten Vorlauf-Elternordner und damit auch seine
Aufrufdateien und Plotbelege.

Vor dem wissenschaftlichen Start Worker-/Aufrufzeiten, Speicherbelege und
Vollständigkeit dieses Vorlaufs einordnen. Fünf Zehnerläufe garantieren keine
Laufzeit für 520 Tausenderläufe. Die rund 46,14 extrapolierten Worker-Stunden
aus dem Pilot sind eine unsichere Orientierung; sie schließen Vorbereitung,
Referenzfits, Abschluss, Plotexport und Verifikation nicht vollständig ein.
Notwendige Friständerungen sind vor den wissenschaftlichen Suchen zu begründen
und zu versionieren. Der Vorlaufblock startet die Serie deshalb nicht automatisch.

## 3. Nach bestätigtem Ressourcenbefund die gesamte Serie starten

Der technische Vorlauf und seine Ressourcenbewertung sind abgeschlossen.
Dieser separate Block bereitet zuerst alle 26 Fälle vor und arbeitet dann
alle 520 geplanten Suchen ohne interaktive Zwischenwahl ab. Im selben sauberen
Worktree mit unveränderter numerischer Umgebung ausführen; den technischen
Originalordner erhalten. `--no-sync` verhindert eine erneute Umgebungsanpassung.

```bash
bash <<'BASH'
set -euo pipefail
test "$(git rev-parse HEAD)" = 'bd42634b888c2dbaa5a92726b9a1f9851c766a48'
test -z "$(git status --porcelain)"
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
task_study=results/noise-background-manjaro-001
task_technical=results/noise-background-preflight-manjaro-001/technical
test -d "$task_technical"
test ! -e "$task_study"
test ! -e "$task_study.tar.gz"
test ! -e "$task_study.tar.gz.sha256"
uv run --locked --no-sync python scripts/check_noise_background.py --verify "$task_technical"
uv run --locked --no-sync python scripts/run_noise_background.py prepare \
  --output "$task_study/inputs"
uv run --locked --no-sync python scripts/run_noise_background.py run \
  --inputs "$task_study/inputs" \
  --technical "$task_technical" \
  --output "$task_study/series"
BASH
```

Zulässige numerische Ausfälle bleiben im Nenner und in den Kosten. Sie sind
von Integritätsfehlern, unbekannten Fehlern und Unterbrechungen getrennt; diese
sperren den Gesamtabschluss. Keine automatische Wiederholung oder Fortsetzung
eines abgebrochenen Ausgabeordners. Originale erhalten und einen Abbruch zuerst
einordnen; eine neue ID oder ein neuer Lauf ist eine eigene Entscheidung.

Die Betriebsgrenzen sind 1.800 Sekunden je Worker, 7.800 je Paket, 40.800 je
Fünfarmfall und 1.075.200 für die Gesamtserie; Vorbereitung 2.400, separate
Gesamtverifikation 14.400 Sekunden. Diese Grenzen sind keine erwarteten
Laufzeiten. Auch eine späte Fristverletzung widerruft die Veröffentlichung.

## 4. Lesende Fortschrittsanzeige mit zehn Sekunden Abstand

In einem zweiten Terminal im selben Laufverzeichnis starten. Der Monitor
ändert keine Laufdateien und benötigt nur Python 3. Er zeigt abgeschlossene
Fallverarbeitung, den aktiven Arm und dessen Mitgliedsstatus. Ein abgeschlossener
Fall kann zulässige Ausfälle enthalten; `finished` bedeutet zunächst nur, dass
der betreffende Worker beendet ist. Die Erfolgsbewertung steht erst im verifizierten
Abschluss. Strg+C in diesem zweiten Terminal beendet ausschließlich den Monitor.

```bash
unset VIRTUAL_ENV
uv run --locked --no-sync python - <<'PY'
from datetime import datetime
import json
from pathlib import Path
import time

root = Path("results/noise-background-manjaro-001/series")

def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}

try:
    while True:
        state = read(root / "run_state.json")
        cases = state.get("cases", [])
        done = sum(case.get("status") == "completed" for case in cases)
        print("\033[2J\033[H", end="")
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print(f"Serie: {state.get('status', 'noch keine Statusdatei')}")
        print(f"Abgeschlossene Fälle: {done}/26\n")
        for case in cases:
            case_root = root / "cases" / case["id"]
            detail = read(case_root / "run_state.json")
            arm = detail.get("arm") if case.get("status") == "running" else None
            line = f"{case['id']:9}  {case.get('status', '?'):10}"
            if arm:
                package = read(case_root / "symbolic" / arm / "run_state.json")
                members = package.get("members", [])
                line += f"  {arm}: " + ", ".join(
                    f"{index}={status}" for index, status in enumerate(members, 1)
                )
            print(line)
        print("\nNur lesend; nächstes Update in 10 Sekunden.", flush=True)
        time.sleep(10)
except KeyboardInterrupt:
    pass
PY
```

## 5. Nach Abschluss lesend verifizieren, grafisch auswerten und archivieren

Der folgende Block stoppt bei jedem Fehler. Erst nach erfolgreicher
Gesamtverifikation und Plotveröffentlichung wird das Archiv erzeugt. Vorhandene
Exports oder Archive nicht überschreiben; für eine spätere zusätzliche
Nachprüfung einen neuen Exportpfad verwenden.

```bash
bash <<'BASH'
set -euo pipefail
test "$(git rev-parse HEAD)" = 'bd42634b888c2dbaa5a92726b9a1f9851c766a48'
test -z "$(git status --porcelain)"
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
task_study=results/noise-background-manjaro-001
task_preflight=results/noise-background-preflight-manjaro-001
test -f "$task_study/series/completion/assessment_report.json"
test ! -e "$task_study/verification"
test ! -e "$task_study/plots"
test ! -e "$task_study.tar.gz"
test ! -e "$task_study.tar.gz.sha256"
uv run --locked --no-sync python scripts/run_noise_background.py verify \
  --inputs "$task_study/inputs" \
  --technical "$task_preflight/technical" \
  --output "$task_study/series" \
  --export "$task_study/verification"
uv run --locked --no-sync python scripts/run_noise_background.py plots \
  --inputs "$task_study/inputs" \
  --technical "$task_preflight/technical" \
  --output "$task_study/series" \
  --export "$task_study/plots"
tar -czf "$task_study.tar.gz" -C results \
  noise-background-manjaro-001 noise-background-preflight-manjaro-001
tar -tzf "$task_study.tar.gz" > /dev/null
cd results
sha256sum noise-background-manjaro-001.tar.gz > noise-background-manjaro-001.tar.gz.sha256
sha256sum -c noise-background-manjaro-001.tar.gz.sha256
BASH
```

Erwartete wissenschaftliche Artefakte: `inputs/` und `inputs-call.json`,
26 Fallordner unter `series/cases/` samt benachbarten `-call.json`, Originalworker
der tatsächlich ausgeführten Arme, Fall-/Serienabschlüsse, `series-call.json`,
`verification/` mit `verification-call.json` sowie `plots/` mit Grafiken,
vollständigen Formeln und gebundenen Plotdaten. Ein `not_run`-Arm bekommt
keinen erfundenen Workerordner; seine vier geplanten Mitglieder bleiben im
Fallbericht sichtbar. Das Archiv umfasst beide vollständigen Elternordner,
einschließlich des technischen Originals und seiner gesonderten Grafiken.

Originalarchive unverändert im gemeinsamen Archivordner und als unabhängige
Zweitkopie auf einem anderen Datenträger oder im bestehenden Backup erhalten.
Beide Kopien am SHA-256 prüfen und tatsächliche Ablage/Sicherung im bestehenden
[Ergebnisindex](results_index.md) dokumentieren. Ein lokal erzeugtes Archiv
oder mehrere Transportteile belegen allein keine unabhängige Sicherung.
GitHub-Uploads bleiben optional; große Archive nicht in Git aufnehmen.
