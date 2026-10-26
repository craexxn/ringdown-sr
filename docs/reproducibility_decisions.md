# Wiederholbarkeit und wissenschaftliche Robustheit

Stand: 26.10.2026. Entscheidungsvermerk zur ausdrücklich festgehaltenen
Frage: Müssen unterschiedliche Rechner exakt dieselben Ergebnisse liefern,
und schränkt ein gemeinsamer BLAS-Kern die symbolische Regression ein?

## Aktuelle Einordnung

Exakt gleiche Läufe sind ein nützliches Diagnoseziel. Sie helfen, Änderungen
an Code und Einstellungen von Änderungen der numerischen Umgebung zu trennen.
Wissenschaftliche Belastbarkeit setzt darüber hinaus voraus, dass die später
festzulegenden Aussagen über mehrere Seeds, Rauschrealisierungen und relevante
Rechenumgebungen stabil bleiben. Eine einzelne auf zwei Geräten bitgleiche
Front belegt diese Robustheit nicht. Unterschiedliche einzelne Fronten
widerlegen für sich genommen ebenfalls noch keine wissenschaftliche Aussage.

Diese Punkte werden getrennt beurteilt:

| Ziel | Was geprüft wird | Grenze |
| --- | --- | --- |
| Nachvollziehbarkeit | Daten, Code, Konfiguration, Seeds, Umgebung und Artefakte sind zuordenbar | Allein keine gleiche numerische Ausgabe |
| Exakte Wiederholbarkeit | Gleiche kontrollierte Eingaben und Einstellungen ergeben gleiche Fronten und Vorhersagebits | Begrenzt auf die geprüften Bedingungen |
| Numerische Nähe | Parameter, Verluste und Vorhersagen unterscheiden sich nur innerhalb fachlich begründeter Kriterien | Schwellen sind vor einer Bewertung zu begründen |
| Wissenschaftliche Robustheit | Aussagen über Rekonstruktionsqualität und Verfahren bleiben über den festgelegten Versuchsplan stabil | Noch keine abgeschlossene Leistungsstudie |

Bei freier symbolischer Regression können außerdem verschiedene Formeln
ähnliche Kurven erzeugen; bei Ringdown-Parametern sind die separat behandelten
Alias- und Identifizierbarkeitsfragen zu berücksichtigen. Ausdrucksidentität,
Kurvenähnlichkeit und physikalische Identifikation sind verschiedene Kriterien.

## Bedeutung von Haswell und Poollimit 1

`OPENBLAS_CORETYPE=Haswell` legt den von OpenBLAS gewählten Rechenkern fest.
Die vier gesetzten Threadvariablen begrenzen die zugehörigen Rechenpools.
Die Wirkung wird anhand der tatsächlich geladenen Bibliotheken geprüft;
sie folgt nicht allein aus dem Namen einer Umgebungsvariable.

Diese Diagnose verändert keine zugelassenen Operatoren, Formelgrößen,
Einheitenregeln, Ein-/Ausgangsdaten, Verlustformeln, Seeds oder nominellen
Suchbudgets. Sie schränkt den beschriebenen mathematischen Suchraum nicht ein.
Sie kann aber Rundung und Rechenreihenfolge, den daraus entstehenden
Suchverlauf und die Laufzeit beeinflussen. Gleiche nominelle Budgets sind
deshalb weiterhin kein Nachweis gleicher Rechenkosten. Ein späteres
Zeitbudget wäre von der Rechenumgebung besonders abhängig.

Bei Vergleichen muss die gewählte numerische Vorgabe auf alle verglichenen
Arme gleich angewendet und mit den Ergebnissen dokumentiert werden. Ein
gemeinsamer Kernname vereinheitlicht nicht sämtliche Julia-JIT-, GC-, CPU-
und Systembibliothekseigenschaften. Die geprüften CPU-/Bibliothekskombinationen
unterstützen Haswell; daraus folgt keine allgemeine Vorgabe für andere Geräte.

## Bisheriger Befund und offene Entscheidung

Die [festen Kontrollfälle](fixed_numerics_probe.md) stimmen unter bestätigtem
Haswell-Kern auf Manjaro und WSL2 bytegleich überein. Die neuen Basisläufe
reproduzieren die früheren Unterschiede. Ob diese Kontrolle auch die bisher
verschiedenen vollständigen freien Fronten vereinheitlicht, wurde inzwischen
für den eingefrorenen gewöhnlichen Weißrauscharm geprüft: Alle vier
Haswell-Läufe liefern auf den beiden Geräten dieselbe vollständige Front
mit sieben Kandidaten. [Bedingungen, Nachrechnung und Grenzen](symbolic_core_results.md)
sind gesondert dokumentiert. Die nativen freien Gegenbefunde stammen aus
früheren Paketen mit dem damaligen Diagnosetreiber; eine neue gepaarte freie
Baseline mit identischem umschlossenen Einstieg liegt nicht vor.

**Vorläufige Entscheidung:** Haswell und Poollimit 1 dienen diesem gezielten
Kontrollversuch. Sie sind noch keine dauerhaft beschlossene Anforderung an
das Forschungsprofil. Die regulären Standardeinstellungen des Piloten werden
dadurch nicht global geändert.

**Vor der Leistungsstudie offen zu entscheiden:** Welches numerische Profil
wird als Referenz verwendet, welche weiteren Umgebungen werden als
Robustheitskontrolle berücksichtigt und anhand welcher fachlich begründeten
Kriterien werden Abweichungen bewertet? Dazu gehören mehrere vorher
festgelegte Seeds und Rauschrealisierungen. Eine Entscheidung wird nicht
allein danach getroffen, welche Einstellung die schönste Formel liefert.

Grundlagen:

- [OpenBLAS: Laufzeitvariablen und Kernwahl](https://www.openmathlib.org/OpenBLAS/docs/runtime_variables/).
- [NumPy: Grenzen der RNG-Kompatibilität](https://numpy.org/doc/stable/reference/random/compatibility.html).
