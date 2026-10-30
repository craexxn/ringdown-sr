# Zeitdarstellungs-Kontrollserie auf Manjaro: Ergebnis 001

Ausführung und unabhängige Nachrechnung vom 30.10.2026. Alle neun Zellen
sind abgeschlossen; die abschließende Verifikation ist bestanden.

**Befund:** Die gemeinsam aktivierten Komplexitätshäufigkeitsschalter liefern
bei allen drei Entwicklungsseeds deutlich kleinere Fehler als die jeweilige
frische Baseline. Die Zeitstreckung verbessert die Trainings-MSE bei zwei
Seeds; beim dritten bleibt eine numerisch gleiche konstante Näherung.
Keiner der 57 exportierten Kandidaten erfüllt die eingefrorenen Kurvengrenzen.
Der begrenzte Erkenner unterstützt keine der gefundenen Strukturen;
physikalische Parameter und Identifikation bleiben `not_assessed`.

## Originalquelle und Ausführungsstand

- Vom Nutzer übermitteltes vollständiges Originalarchiv:
  `representation-manjaro-001.tar.gz`, 726.125 Bytes. Seine tatsächliche
  SHA-256 wurde vor dem Entpacken gegen die übermittelte Prüfsumme bestätigt:
  `a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db`.
- Aufgezeichneter Ausführungscommit:
  `4057caaffd9c4de5791ded14431c6e289db75b73`, sauberes Git-Arbeitsverzeichnis.
  Das ist der Merge von [PR #39](https://github.com/craexxn/ringdown-sr/pull/39).
  Der [Reviewabschluss](representation_implementation_status.md) betrifft den
  baumgleichen PR-Head `cfe44bfb84baef9238f52609ba1030eaa4416ed7` gegen
  `909942d3f3910ea20df1703dd12421abe4867a4e`.
- Aufgezeichnete Gerätebezeichnung `manjaro`, Python 3.12.14, Julia 1.13.1,
  PySR 2.6.0 und SymbolicRegression 2.5.1. Die geladenen NumPy-, SciPy- und
  Julia-Pools sind mit Haswell und Threadlimit 1 protokolliert.
- Aufgezeichnete Serienzeit: 12:42:13 bis 12:49:29 Uhr Europe/Vienna,
  entsprechend 435,462 Sekunden einschließlich Vorprüfungen und Workerstarts.
- Serienstatus `completed`, neunmal `completed`,
  `final_verification=passed`; alle drei Bedingungen und sechs Seed-Paare
  sind vollständig auswertbar. Keine Ersatzläufe oder Ersatzseeds im Archiv.

Prüfsummen und Metadaten belegen Konsistenz des übermittelten Pakets;
sie sind keine externe Authentifizierung des Geräts oder vollständiger RNG-Zustände.
Der Audit startet weder Julia noch Fit, Optimierung oder freie Suche.

## Unveränderte Vorgaben

Grundlage ist der eingefrorene [Methodenplan](search_representation_plan.md),
SHA-256 `16cfe818c312fb5bb0a6c594505ad76ba41e41bd7f4a37decc245677c6b8ad86`.
Auch der alte Planhash bleibt unverändert.

Ein rauschfreies Signal mit `A=1`, `f=250 Hz`, `tau=0,008 s`, `phi=0`;
128 Trainingswerte bei 4096 Hz sowie 889 innere Achtelpunkte zur Diagnose.
Beide Koordinaten bleiben Sekunden. Die Suche erhält ausschließlich ihre
Zeitkoordinate und dieselben Beobachtungsbits. Wahrheit, Diagnosepunkte und
Referenzbäume bleiben außerhalb von Suche und Auswahl.

Die drei Bedingungen sind frische Baseline, `u=32*t` und beide gemeinsam
aktivierten Häufigkeitsschalter. Es gibt keinen kombinierten Arm. Je Bedingung
bestehen drei frische Zellen mit den Seeds 20261020, 20261021 und 20261022,
200 Iterationen, zwei Populationen zu 32 Individuen und 50 Zyklen je Iteration
in der festgelegten zyklischen Reihenfolge. Operatoren, Einheitenregeln,
Maximalgröße 20 und Konstantenoptimierung folgen dem Plan.

## Unabhängiger Audit der Originalartefakte

Selbst ausgeführt, nicht aus der gespeicherten Erfolgsmarkierung abgeleitet:

1. Archivprüfsumme und sichere Dateistruktur geprüft: 249 Archiveinträge,
   davon 219 reguläre Dateien. Alle 218 Einträge des abschließenden
   Artefaktmanifests einschließlich vollständiger Abdeckung bestätigt;
   `metadata.json` ist selbst nicht Teil dieses Manifests.
2. Alle 41 Quell-/Pin-/Planprüfsummen mit den vertrauenswürdigen Repositorydateien
   und zusätzlich mit `git show` am Ausführungscommit verglichen. Laufzeitkopien,
   native Julia-Kopien, eingefrorene Dateien und alle Worker-Manifeste geprüft.
   Archivierte Python-/Julia-Dateien wurden als Daten verglichen und nicht
   als Auditcode importiert oder ausgeführt.
3. Vollständige Zellreihenfolge, Budgets, Anfragen, Sekundenkoordinaten,
   Beobachtungsbits und Referenzraster nachgerechnet. Physikalische Referenzdaten
   sind bitgleich mit dem erneut erzeugten eingefrorenen Generator.
4. Gespeicherte Vorprüfungsprotokolle für neun Optionsobjekte mit je 68 Feldern
   und neun native Referenzfälle geprüft. Alle Zelloptionen, Seeds und konkreten
   Pluginfelder mit ihren jeweiligen Sollwerten und Vorprüfungen abgeglichen.
   Haswell-Aufnahmen vor/nach den Workern und die Callbackzähler erneut geprüft.
   Das sind Prüfungen der archivierten Backendnachweise, keine neuen Julia-Läufe.
5. Sämtliche 57 Originalbäume erneut ausgewertet, zunächst mit dem bestehenden
   strengen Verifikationspfad, zusätzlich mit einem unabhängig geschriebenen
   Bauminterpreter ohne Auswertung der Anzeigegleichungen. Gespeicherte
   Residuen gegen `Beobachtung - gespeicherte Vorhersage` bitgenau geprüft.
   Trainings-MSE zusätzlich mit `math.fsum(residuum**2)/128` nachgerechnet.
   Beide physikalischen Raster verwenden den vollständigen Baum `q(alpha*t)`.
6. Originalauswahl aus gespeicherten Trainingsverlusten und Komplexitäten
   bestätigt. Alle Kandidaten und Indizes blieben erhalten. Fehlerwerte auf
   beiden Rastern unabhängig aus Quadratsummen und Maximalbeträgen gebildet.
   Struktur-/Parameterdiagnosen mit dem bestehenden begrenzten Erkenner
   reproduziert; kein neuer unabhängiger Strukturerkenner behauptet.
7. Alle Gruppenstatistiken, sechs Seed-Differenzen und Statusangaben aus den
   nachgerechneten Zellen reproduziert; den lesbaren Markdownbericht nach
   benannten Abschnitten und Zahlenwerten abgeglichen. JSON sortiert Dictionarykeys,
   während Markdown deren ursprüngliche Reihenfolge darstellt; diese reine
   Darstellungsreihenfolge wurde beim Textabgleich normalisiert.
8. Abschließend alle 219 Originaldateihashes erneut geprüft: keine Änderung
   an extrahierten Originalartefakten während des Audits.

Die zusätzlichen numerischen Replayvergleiche bestanden die bestehenden
Vorhersage-/MSE-Verträge. Für nachgerechnete Berichtswerte wurde mit
`rtol=1e-12`, `atol=1e-14` verglichen; für Baum-MSE mit `rtol=1e-10`,
`atol=0`. Das sind Auditvergleiche und keine Änderungen der wissenschaftlichen
Erfolgsschwellen. Diese bleiben auf beiden Rastern `relative_rms <= 0,001`
und `relative_max <= 0,01`.

## Alle neun ursprünglichen Auswahlen

Zahlen sind hier gerundet; volle Präzision bleibt im Originalarchiv.
Alle Indizes sind nullbasiert. Alle Zellen haben Status `completed`.

| Zelle | Seed | Bedingung | Front | Auswahlindex | Knoten | Trainings-MSE | Training RMS | Zwischenpunkte RMS | Zwischenpunkte Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 20261020 | baseline | 9 | 8 | 19 | 0.06096083849 | 0.944594515 | 0.964319184 | 0.798730206 |
| 2 | 20261020 | time_stretch | 10 | 9 | 20 | 0.03880046098 | 0.753595673 | 0.774250129 | 0.750997616 |
| 3 | 20261020 | complexity_frequency | 6 | 5 | 13 | 0.006275840088 | 0.303079029 | 0.301459174 | 0.323264978 |
| 4 | 20261021 | time_stretch | 12 | 11 | 20 | 0.02436094355 | 0.597127409 | 0.683165819 | 1.62740674 |
| 5 | 20261021 | complexity_frequency | 7 | 6 | 19 | 0.002515000237 | 0.191862001 | 0.197413154 | 0.106958607 |
| 6 | 20261021 | baseline | 1 | 0 | 1 | 0.06829567962 | 0.999807911 | 1.00010774 | 0.994851497 |
| 7 | 20261022 | complexity_frequency | 10 | 9 | 17 | 0.002035415473 | 0.172602264 | 0.177798471 | 0.118497837 |
| 8 | 20261022 | baseline | 1 | 0 | 1 | 0.06829567962 | 0.999807911 | 1.00010774 | 0.994851497 |
| 9 | 20261022 | time_stretch | 1 | 0 | 1 | 0.06829567962 | 0.999807911 | 1.00010774 | 0.994851497 |

Alle neun Auswahlen und alle 57 Frontkandidaten sind `outside_tolerance`.
Alle 57 Strukturdiagnosen sind `not_supported`: 52-mal erster Grund
`exponential_factor_count`, fünfmal `cosine_factor_count`. Ein erster
Ablehnungsgrund ist keine vollständige Beschreibung des Baums. Es gibt
keinen positiven Parameterbefund; die Fehlerfelder dafür bleiben null.
Die 57 Frontkandidaten sind keine 57 unabhängigen Suchläufe.

## Deskriptiver Vergleich der Bedingungen

Je drei vollständige Zellen; alle nachstehenden Fehlerkennzahlen haben
Nenner 3/3 endlich. Die Minima/Mediane/Maxima beziehen sich auf die
Originalauswahlen, nicht auf eine nachträgliche Auswahl nach Diagnosequalität.

| Bedingung | Trainings-MSE min / median / max | Zwischenpunkte RMS min / median / max | Zwischenpunkte Max min / median / max |
| --- | --- | --- | --- |
| baseline | 0.0609608385 / 0.0682956796 / 0.0682956796 | 0.964319184 / 1.00010774 / 1.00010774 | 0.798730206 / 0.994851497 / 0.994851497 |
| time_stretch | 0.0243609435 / 0.038800461 / 0.0682956796 | 0.683165819 / 0.774250129 / 1.00010774 | 0.750997616 / 0.994851497 / 1.62740674 |
| complexity_frequency | 0.00203541547 / 0.00251500024 / 0.00627584009 | 0.177798471 / 0.197413154 / 0.301459174 | 0.106958607 / 0.118497837 / 0.323264978 |

Alle drei Bedingungen haben null Auswahlen mit bestandenem Kurvenmarker,
null unterstützte Strukturen und null positive Parameterbefunde.
Parameterfehler haben daher Nenner 0/3 und werden nicht als Nullfehler ersetzt.

## Differenzen zur frischen Baseline je Seed

`Delta = Variante - Baseline`. Negative Fehlerdifferenzen bedeuten Verbesserung.
Beide Ausgangswerte stehen in der Neun-Zellen-Tabelle und in den Originalberichten.
Alle 30 folgenden Fehlerdifferenzen sind verfügbar. Parameterdifferenzen bleiben
bei allen sechs Paaren `not_assessed` mit Grund; es gibt keine statistische
Signifikanzprüfung und keine Annahme identischer Mutationsfolgen.

| Seed | Variante | Delta MSE | Delta Training RMS | Delta Training Max | Delta Zwischenpunkte RMS | Delta Zwischenpunkte Max |
| --- | --- | --- | --- | --- | --- | --- |
| 20261020 | time_stretch | -0.02216037752 | -0.190998842 | -0.04294981514 | -0.1900690547 | -0.04773258989 |
| 20261020 | complexity_frequency | -0.05468499841 | -0.6415154853 | -0.4656549065 | -0.6628600102 | -0.475465228 |
| 20261021 | time_stretch | -0.04393473608 | -0.4026805027 | -0.4789603847 | -0.316941922 | 0.6325552437 |
| 20261021 | complexity_frequency | -0.06578067939 | -0.8079459107 | -0.8907978929 | -0.8026945874 | -0.8878928895 |
| 20261022 | time_stretch | 0 | 0 | -4.540035015e-12 | 2.746691763e-13 | -4.562572542e-12 |
| 20261022 | complexity_frequency | -0.06626026415 | -0.8272056468 | -0.8761611289 | -0.8223092697 | -0.8763536599 |

Die Häufigkeitsschalter senken die Trainings-MSE gegenüber der frischen Baseline
um 89,7 %, 96,3 % und 97,0 %. Auf den Zwischenpunkten liegt ihr relativer
RMS-Fehler bei 0,1778 bis 0,3015, weiterhin deutlich oberhalb der Grenze 0,001;
der relative Maximalfehler liegt bei 0,1070 bis 0,3233 statt höchstens 0,01.
Damit ist eine Verbesserung der Approximation beobachtet, keine erfolgreiche
freie Ringdown-Formelrekonstruktion.

Zeitstreckung senkt die Trainings-MSE bei den ersten beiden Seeds um 36,4 %
und 64,3 %. Bei Seed 20261021 wächst zugleich der Zwischenpunkte-Maximalfehler
auf 1,6274. Beim dritten Seed ist die Trainings-MSE gleich; Differenzen von
etwa 1e-12 in einzelnen weiteren Fehlermaßen werden nicht als Verbesserung
interpretiert. Die Zeitstreckung liefert in dieser Serie keinen gleichmäßig
besseren Verlauf auf beiden Rastern.

## Aufgezeichneter Aufwand

Fitzeiten enthalten laut Feldbezeichnung JIT und Python-Exporte und sind keine
isolierte Evolutionszeit. Callbackzahlen enthalten unter anderem
Konstantenoptimierung und zählen keine verschiedenen Bäume.

| Zelle | Callbackaufrufe im Fit | Gesamtzähler | Fitzeit in Sekunden |
| --- | --- | --- | --- |
| 1 | 1179348 | 1179349 | 33.989 |
| 2 | 762941 | 762942 | 41.537 |
| 3 | 301956 | 301957 | 32.009 |
| 4 | 1303611 | 1303612 | 41.634 |
| 5 | 290350 | 290351 | 32.022 |
| 6 | 167829 | 167830 | 30.609 |
| 7 | 392602 | 392603 | 32.522 |
| 8 | 159598 | 159599 | 31.292 |
| 9 | 153170 | 153171 | 30.442 |

Insgesamt 4.711.405 Fit-Callbackaufrufe und 4.711.414 Gesamtaufrufe.
Die neun zusätzlichen Aufrufe sind die bestehenden Nullkurvenprüfungen
nach dem Fit. Die archivierten Backend-Gesamtevaluationszähler bleiben
`unavailable`; daraus wird keine weitere Evaluationszahl abgeleitet.

| Bedingung | Frontkandidaten | Fit-Callbackaufrufe | Summe Fitzeiten in Sekunden |
| --- | --- | --- | --- |
| baseline | 11 | 1506775 | 95.891 |
| time_stretch | 23 | 2219722 | 113.614 |
| complexity_frequency | 23 | 984908 | 96.553 |

Gemeinsame Seeds erzeugen weder identische Rechenkosten noch identische
Suchpräfixe. Die Aufwandssummen begründen keine allgemeine Aussage zur
Geschwindigkeit oder Populationsvielfalt eines Profils.

## Grenzen und nächster abgegrenzter Schritt

Die geplante Serie ist vollständig abgeschlossen. Die freien Suchläufe wurden
hier nicht wiederholt; Quellen, Pläne und Originalartefakte blieben unverändert.
Die drei bekannten Entwicklungsseeds an einem bekannten Signal begründen
keine unabhängige Leistungsvalidierung. Der Alias-Blindfleck des Achtelrasters
bei `8*fs=32768 Hz` bleibt bestehen.

Dass der begrenzte Erkenner alle Kandidaten ablehnt, ist separat von den
zu großen Kurvenfehlern zu bewerten. Hier verfehlen bereits die Kurven die
festen Grenzen; der Befund kann deshalb nicht allein auf eine Begrenzung
des Erkenners zurückgeführt werden.

Als nächster Schritt ist bewusst zu entscheiden, welche weitere Ursachenprüfung
oder Eingrenzung der Methode verfolgt wird. Die [offene Entscheidungsgrundlage
mit Review-Prompt](representation_next_step_review.md) bereitet diese Entscheidung
vor und enthält noch keinen beschlossenen neuen Versuchsplan. Die Häufigkeitsschalter sind in
dieser Serie ein günstigerer Entwicklungsbefund, noch kein freigegebenes
Produktionsprofil. Mehr Budget, neue Seeds, kombinierte Arme, geänderte
Grenzen oder Rauschstudien sind keine automatische Fortsetzung.

## Reproduzierbarer Auszug der unabhängigen Zahlenprüfung

Der folgende lesende Auszug reproduziert MSE und relative Fehler aus allen
Originalbäumen und druckt nur die ursprünglichen Auswahlen. Er startet keine
Suche und ersetzt nicht die oben beschriebenen Manifest-/Quell-/Diagnoseprüfungen.
Der Archivpfad ist bei Bedarf an den unveränderten Originalspeicherort anzupassen.

```bash
uv run --locked python - results/representation-manjaro-001.tar.gz <<'PY_AUDIT'
import hashlib
import io
import json
import math
import sys
import tarfile
from pathlib import Path

import numpy as np

path = Path(sys.argv[1])
assert hashlib.sha256(path.read_bytes()).hexdigest() == (
    "a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db"
)


def predict(node, time):
    if node["kind"] == "constant":
        return np.full_like(time, float.fromhex(node["value_hex"]))
    if node["kind"] == "variable":
        assert node["index"] == 1
        return time
    values = [predict(child, time) for child in node["children"]]
    unary = {"exp": np.exp, "sin": np.sin, "cos": np.cos}
    binary = {"+": np.add, "-": np.subtract, "*": np.multiply, "/": np.divide}
    return (unary if node["arity"] == 1 else binary)[node["operator"]](*values)


def energy(values):
    return math.fsum(float(value) ** 2 for value in values)


with tarfile.open(path, "r:gz") as archive:
    def read(name):
        return archive.extractfile("representation-manjaro-001/" + name).read()

    report = json.loads(read("report.json"))
    with np.load(io.BytesIO(read("training.npz")), allow_pickle=False) as data:
        time, observed = data["time_s"], data["observed"]
    with np.load(io.BytesIO(read("diagnostic.npz")), allow_pickle=False) as data:
        inner, truth = data["diagnostic_time_s"], data["diagnostic_truth"]
    for cell in report["cells"]:
        front = json.loads(read(cell["directory"] + "/result.json"))
        selected = min(range(len(front["candidates"])), key=lambda index: (
            front["candidates"][index]["loss"],
            front["candidates"][index]["complexity"],
        ))
        assert selected == front["selected_index"]
        scale = 32 if cell["condition"] == "time_stretch" else 1
        for index, candidate in enumerate(front["candidates"]):
            training_residual = observed - predict(candidate["tree"], scale * time)
            mse = energy(training_residual) / len(time)
            assert math.isclose(mse, candidate["loss"], rel_tol=1e-10, abs_tol=0)
            residual = truth - predict(candidate["tree"], scale * inner)
            rms = math.sqrt(energy(residual) / energy(truth))
            maximum = max(abs(residual)) / max(abs(truth))
            if index == selected:
                print(cell["number"], cell["condition"], mse, rms, maximum)
PY_AUDIT
```
