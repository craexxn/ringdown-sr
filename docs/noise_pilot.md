# Laufweg für den begrenzten Rauschpilot

Stand 14.11.2026, [Leitfadenphase 7](ringdown_recovery_roadmap.md).
Der [vor Implementierung beschlossene Plan](noise_pilot_plan.md) ist an Commit
`27367a707b0f78c2d8e4ec397e0af6d958f5c527` und SHA-256
`2a8e521b7729a668832ca02b0c8dd587d46ddec4010d7657d71e7b4d4d295fb8`
gebunden. PR91 ist als `899bf09756a0aa899827896fcf462afbd8752421` übernommen.
Der Plan bleibt unverändert; sein Abschnitt „Noch nicht implementiert“
beschreibt den Zustand zum Protokollbeschluss. Aktueller technischer Prüf- und
Übernahmestand: [Fortsetzungsstand](representation_implementation_status.md).

## Umsetzung und Aussagegrenzen

`run_noise_pilot.py prepare` bindet vor dem ersten Fit sämtliche zwölf Fälle:
Signal, Messrauschen, unabhängige Hintergrundrollen, Kovarianzen, konkrete
Zwischen-/Zusatzpunkte, hochpräzise Referenzkontrollen und Generatorzustände.
Der wissenschaftliche Lauf führt die feste Reihenfolge aus: Block 1–6,
ungerade white/ar1, gerade ar1/white; ordinary, bekannte, geschätzte Kovarianz;
je vier neue Worker. Kein automatischer Wiederholungs- oder Ersatzseedmodus.

Jeder Arm verwendet das bestätigte Profil mit viermal 1.000 äußeren Iterationen,
300 lokalen Optimiereriterationen und fünf zusätzlichen lokalen Neustarts.
Der Paketadapter entscheidet allein nach nativem Trainingsverlust, Komplexität
und Mitgliedsposition. Die bestehende native Gewichtung bestimmt sowohl
Struktursuche als auch Konstantenoptimierung. Erst nach dieser Originalauswahl
folgen die getrennten Diagnosen zur sauberen Wahrheit, A–D, Originalfamilie,
Definitionsbereich und Restterm. Parameterübereinstimmung bleibt `not_assessed`.

Gewöhnliche numerische Ausfälle bleiben im Nenner. Bei fehlender geschätzter
Kovarianz werden nur deren vier Mitglieder als `not_run` geführt; bei fehlenden
gemeinsamen Daten alle betroffenen Mitglieder. Klassische Referenzfits sind
separate Kontrollen mit den bestehenden Fitoptionen aus `pilot_confirmed_ar1.toml`.
Ihre bekannten numerischen Ausfälle stoppen keine gültigen SR-Arme.
Integritätsfehler, unbekannte Fehler und Unterbrechungen sperren den Abschluss.
Ein abgebrochener Ordner wird weder gelöscht noch fortgesetzt; ein ausdrücklich
beschlossener neuer Gesamtversuch braucht eine neue ID.

Die Einzelberichte enthalten Originalausgaben, vollständige Endfronten,
Workerherkunft, Kovarianz- und Eingabebindungen, Ausfälle und gemessene Kosten.
Der Gesamtbericht verlangt alle zwölf Fälle und denselben Ausführungscommit
sowie dieselbe numerische Umgebung wie der technische Vorlauf. Seine Auswertung
bleibt je Rauschmodell getrennt. Der Ausfall eines dritten Arms entfernt keine
vorhandene Paarung der beiden anderen. MCSE wird nur bei sechs vollständigen
Paaren ausgewiesen; keine automatische Armwahl oder neue Erfolgsgrenze.

Vollständige Aufrufmessungen umfassen Wall- und CPU-Zeit; ihr Scope benennt
die abschließende Messdatei und Nachprüfungen als ausgeschlossen. Vorbereitung,
technischer Vorlauf, wissenschaftliche Serie und lesender Prüfaufruf bleiben
getrennt. Teilzeiten von Workern/Paketen/Fällen sind in übergeordneten
Aufrufzeiten enthalten und dürfen nicht nochmals addiert werden. CPU-Zähler
erfassen den Elternprozess und tatsächlich eingesammelte Kindprozesse. Bei
unbekannter Worker-CPU nach hartem Abbruch kennzeichnet
`cpu_measurement_complete=false` die beobachtete Summe als Teilkosten; sie
wird nicht als vollständige CPU-Zeit ausgegeben. Ein abgebrochener Aufruf
behält seine Teilkosten; fehlende Werte werden nicht null.

## Manjaro: erst nach technischer Abnahme des Implementierungs-PRs

Für den endgültigen Stand einen eigenen sauberen Checkout verwenden. Nach
Übernahme des Implementierungs-PRs im vorhandenen Repository:

```bash
git fetch origin main
git worktree add --detach ../ringdown-noise-pilot-run origin/main
cd ../ringdown-noise-pilot-run
test -f scripts/check_noise_pilot.py
git status --short
git rev-parse HEAD
unset VIRTUAL_ENV
uv sync --locked --dev --python 3.12.14
```

Ein bereits vorhandenes Arbeitsverzeichnis nicht überschreiben. Während
Vorbereitung, Vorlauf, Suche und Verifikation den Checkout unverändert lassen.
Julia wird über den vorhandenen Launcher gebunden; eine fremde virtuelle
Umgebung wird nicht aktiviert. Einmalig erforderlicher Julia-Download und
JIT-Kompilation sind keine wissenschaftliche Suche.

### 1. Begrenzter technischer N128-Vorlauf

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
uv run --locked python scripts/check_noise_pilot.py \
  --output results/noise-pilot-technical-manjaro-001
uv run --locked python scripts/check_noise_pilot.py \
  --verify results/noise-pilot-technical-manjaro-001
test ! -e results/noise-pilot-technical-manjaro-001.tar.gz
tar -czf results/noise-pilot-technical-manjaro-001.tar.gz \
  -C results noise-pilot-technical-manjaro-001
tar -tzf results/noise-pilot-technical-manjaro-001.tar.gz > /dev/null
cd results
sha256sum noise-pilot-technical-manjaro-001.tar.gz \
  > noise-pilot-technical-manjaro-001.tar.gz.sha256
sha256sum -c noise-pilot-technical-manjaro-001.tar.gz.sha256
BASH
```

Dies sind drei einzelne Worker mit je zehn äußeren Iterationen, N=128 und
lokal 300/5. Jeder hat höchstens 600 Sekunden. Eigenes versioniertes Format,
eigene Eingaben und technische Seeds; die bisherigen Ein-Iterations-Prüfungen
behalten ihre Bedeutung. Abnahme verlangt tatsächliche erfolgreiche Worker
und Replay, keine Signalqualitätsgrenze. Erwartet werden `inputs/`,
`inputs-call.json`, die drei Armordner, `completion/` und die vollständige
technische Aufrufmessung. Der Vorlauf startet keine wissenschaftliche Serie.

Seine Ressourcenwerte vor dem wissenschaftlichen Start einordnen. Drei
Zehnerläufe sind keine garantierte Prognose für 144 Tausenderläufe. Eine
notwendige Friständerung benötigt einen begründeten Beschluss vor dem Start.

### 2. Wissenschaftliche Serie als separater Ausführungsschritt

Erst nach erfolgreichem Manjaro-Vorlauf und dessen Ressourcenprüfung. Dieselbe
Umgebung und derselbe Checkout bleiben bestehen. Der folgende Block bereitet
alle Fälle vor und führt anschließend sämtliche 144 geplanten Suchen ohne
interaktive Zwischenentscheidungen aus. Er überschreibt keine vorhandene ID.

```bash
bash <<'BASH'
set -euo pipefail
unset VIRTUAL_ENV
export OPENBLAS_CORETYPE=Haswell
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
test ! -e results/noise-pilot-manjaro-001
uv run --locked python scripts/run_noise_pilot.py prepare \
  --output results/noise-pilot-manjaro-001/inputs
uv run --locked python scripts/run_noise_pilot.py run \
  --inputs results/noise-pilot-manjaro-001/inputs \
  --technical results/noise-pilot-technical-manjaro-001 \
  --output results/noise-pilot-manjaro-001/series
BASH
```

Einzelne zulässige Suchausfälle werden berichtet und beenden die Serie nicht.
Bei Integritätsabbruch entstehen keine freigegebenen Gesamtwerte. Die Fristen
sind Betriebsgrenzen, keine gewünschte Laufzeit: 1.800 Sekunden pro Worker,
7.800 pro Viererpaket und 25.200 pro Dreiervergleich.

### 3. Fortschritt alle zehn Sekunden

In einem zweiten Terminal desselben Arbeitsverzeichnisses, ohne zusätzliche
Pakete oder Codeänderung:

```bash
watch -n 10 'cat results/noise-pilot-manjaro-001/series/run_state.json; find results/noise-pilot-manjaro-001/series/cases -name run_state.json -print -exec cat {} \;'
```

Die Anzeige liest nur Statusdateien. Ihr Abbruch mit Strg+C beendet allein
`watch`, sofern das separate Beobachtungsterminal aktiv ist.

### 4. Nach erfolgreichem Abschluss lesend verifizieren

```bash
env OPENBLAS_CORETYPE=Haswell \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --locked python scripts/run_noise_pilot.py verify \
  --inputs results/noise-pilot-manjaro-001/inputs \
  --technical results/noise-pilot-technical-manjaro-001 \
  --output results/noise-pilot-manjaro-001/series \
  --export results/noise-pilot-manjaro-001/verification
```

Keine neuen Fits oder Suchen. Der Verifikator prüft die ursprünglichen
Worker, Auswahl, Ausfälle, Eingaben, Quellen, alle zusätzlichen Bewertungen
und die serienweite Herkunft erneut. Der separate Export wiederholt die
inhaltlichen Abschlussbytes und erhält eigene Prüfkosten. Originale bleiben
unverändert.

### 5. Nach erfolgreicher Verifikation archivieren

Das technische Original gehört zur Gesamtbindung und wird zusammen mit der
wissenschaftlichen Serie erhalten:

```bash
bash <<'BASH'
set -euo pipefail
test ! -e results/noise-pilot-manjaro-001.tar.gz
tar -czf results/noise-pilot-manjaro-001.tar.gz -C results \
  noise-pilot-manjaro-001 noise-pilot-technical-manjaro-001
tar -tzf results/noise-pilot-manjaro-001.tar.gz > /dev/null
cd results
sha256sum noise-pilot-manjaro-001.tar.gz > noise-pilot-manjaro-001.tar.gz.sha256
sha256sum -c noise-pilot-manjaro-001.tar.gz.sha256
BASH
```

Erwartete wissenschaftliche Artefakte: globale `inputs/` samt
`inputs-call.json`, zwölf `series/cases/`-Ordner mit benachbarten
`-call.json`, je ausführbarem Arm vier Originalworker, Einzelabschlüsse,
`series/completion/`, `series-call.json`, lesender `verification/`-Export
und `verification-call.json`. Ein `not_run`-Arm erhält keinen erfundenen
Workerordner; seine geplanten Mitglieder stehen ausdrücklich im Fallbericht.

Archive unverändert im gemeinsamen Archivordner und als zweite Kopie auf
unabhängigem Datenträger oder im bestehenden Backup erhalten. Beide Kopien
am SHA-256 prüfen, Ablage und Sicherungsnachweise im bestehenden
[Ergebnisindex](results_index.md) ergänzen. Ein erzeugtes Archiv allein ist
noch keine bestätigte Sicherung; GitHub-Uploads bleiben optional.
