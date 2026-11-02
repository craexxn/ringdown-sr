# Ergänzung zur Verifikation beobachteter Suchmitglieder

Stand und Annahme: 02.11.2026. Die Umsetzung dieser begrenzten Korrektur
ist beauftragt. Dieser Text ergänzt den unveränderten
[Suchbeobachtungsplan](search_trajectory_plan.md), insbesondere dessen
Abschnitte 5–7. Die ursprüngliche Planbindung bleibt erhalten; diese
Ergänzung erhält eine eigene SHA-256-Bindung im Laufzeitcode.
Die hier beschriebene Statusänderung gilt nur für neue Artefakte des
Beobachtungsformats `ringdown-sr-search-trajectory-2`.

## 1. Anlass und Aussagegrenzen

Der erste Manjaro-Lauf am Mergecommit
`41ccdd27aaa4ade56b509493089241d6695b9757` endete bei der nachgelagerten
Prüfung von Zelle 3. Das geprüfte Originalteilarchiv hat SHA-256
`08676ddc21c1820110ae425a68de3c5b954c8bef2022b816ca274c307041c873`.
Zellen 1 und 2 bestanden einschließlich ihres Originalpaarvergleichs;
Zellen 4–6 wurden nicht gestartet. Der Teilstand bleibt unverändert
`incomplete / failed`.

Unter 19.604 endlichen gespeicherten Verlusten in Zelle 3 wichen fünf von
der Python-Nachrechnung ab. Der anschließend übermittelte native Replay
derselben fünf Bäume zeigt zwei unterschiedliche Befunde:

- Bei zwei Bäumen stimmen gespeicherter Verlust und frischer Julia-Replay
  überein, die NumPy-Baumauswertung weicht ab. Die größte relative
  MSE-Abweichung auf Manjaro beträgt etwa 2,2315 %.
- Bei drei Bäumen weicht der gespeicherte Verlust von beiden aktuellen
  Replays ab. Ein bestimmter Vereinfachungsschritt oder veralteter
  Zwischenwert ist anhand der Aufnahmen nicht bewiesen.

Python reproduziert aus den gespeicherten nativen Vorhersagebits alle
fünf nativen MSE. Die acht endgültigen Frontkandidaten der Zelle bestehen
die bisherigen strengen Prüfungen. Vollständiger Nachweis und
Herkunftsabgrenzung stehen in [PR #47](https://github.com/craexxn/ringdown-sr/pull/47).
Die Befunde begründen keine Toleranzlockerung und keine Änderung der Suche.

## 2. Unveränderte Such- und Auswahlbedingungen

Operatoren, Knoten-/Tiefengrenzen, Seeds, Budgets, Trainingsdaten, Einheiten,
Häufigkeitsschalter, Optimierer, Auswahlregel und Erfolgstoleranzen bleiben
unverändert. Der Hook kopiert weiterhin ausschließlich vorhandene Werte;
er führt keine Bewertung, Optimierung oder Vereinfachung aus.

Die Nachrechnung erfolgt nach abgeschlossenem Fit. Der ursprüngliche
Backendverlust bleibt bitgetreu als gespeicherter Zustand erhalten.
Ein nachgerechneter Verlust überschreibt ihn nicht und wählt keine neue
Formel aus. Die Endfront und Originalauswahl behalten ihre bisherigen
strengen Prüfungen; das gilt auch für beobachtete Bäume, die in der Endfront
vorkommen.

## 3. Getrennte Nachweise je Baum und Vorkommen

Zusätzlich zu Rohaufnahmen und Einheitenstatus wird für jeden eindeutigen
Originalbaum ein nativer Trainingsreplay exportiert. Seine Vorhersagen und
sein Verlust werden als Float64-Bits gespeichert. Der Export bindet sich
an die tatsächlich konsumierten Trainings-, Rohaufnahme- und Einheitendateien.
Vor der Auswertung wird der native Baum bitgetreu zurückexportiert und
mit dem Originalbaum verglichen.

Für jedes Vorkommen sind getrennt erkennbar:

1. unveränderte gespeicherte Verlust-/Kostenbits, Ereignis, Quelle und Position;
2. aktueller nativer Verlust und native Vorhersagen des Originalbaums;
3. Python-MSE aus denselben nativen Vorhersagen;
4. eigenständige Python-Baumauswertung einschließlich Vorhersagevergleich;
5. Vergleichsergebnisse, konkrete Fehlergründe und numerische Differenzen.

Die bisherigen Verlusttoleranzen `rtol=1e-10, atol=0` und der bestehende
skalierte Vorhersagevergleich bleiben unverändert. Es wird keine zusätzliche
großzügigere Toleranz eingeführt. Endliche Auswertbarkeit allein genügt
nicht für einen positiven Befund.

## 4. Statusregeln und harte Fehler

| Befund | Behandlung |
| --- | --- |
| Vollständige, konsistente Nachweise; alle numerischen Vergleiche bestanden; endliche Kosten | Vorkommen `verified`; erst danach bestehende Kurven-/Parametergates anwenden. |
| Gespeicherter Backendverlust widerspricht aktuellem nativen Replay | Vorkommen `numerical_unresolved`, Differenz und Grund erhalten; kein positiver Marker. Keine Behauptung eines bestimmten Entstehungsmechanismus. |
| Nativer und eigenständiger Python-Baumreplay widersprechen sich | Vorkommen `numerical_unresolved`, Verlust- und Vorhersagevergleich getrennt berichten; kein positiver Marker. |
| Bekannte numerische Unauswertbarkeit, nichtendliche Werte oder unzulässige Einheiten | Mit konkretem Grund `not_assessed`; kein positiver Marker. |
| Fehlende/veränderte Dateien, fehlerhafte Prüfsummen oder Bindungen, unbekanntes Schema, fehlende/zusätzliche Bäume, falsche Ereignisse/Slots, negative endliche Verluste | Harter Verifikationsfehler; Serie stoppen und Abschluss sperren. |
| Behaupteter nativer Verlust passt nicht zur MSE seiner eigenen gespeicherten nativen Vorhersagen | Harter Verifikationsfehler, da der Replaynachweis intern widersprüchlich ist. |
| Endlicher gespeicherter Verlust bei nativ ausdrücklich ungültigen Einheiten | Bisherigen harten Widerspruch beibehalten. |
| Falsche Optionen/Seeds, widersprüchliche Endfront-/Residuen-/Auswahlangaben oder abweichendes Kontroll-/Beobachtungspaar | Bisheriger harter Verifikationsfehler; keine vergleichende Freigabe. |

Unerwartete Programmfehler werden nicht als numerische Unbestimmtheit
abgefangen. Bekannte numerische Gründe sind ausdrücklich begrenzt.
Prüfsummen bestätigen Konsistenz mit gebundenen Metadaten, keine externe
Authentizität gegen einen vollständigen Austausch aller Nachweise.

Ein Baum kann in verschiedenen Vorkommen unterschiedliche gespeicherte
Verluste besitzen. Deshalb werden Status und positive Zähler je Vorkommen
und Quelle geführt. Bei gemischten bestätigten und ungeklärten Vorkommen
bleiben bestätigte einzelne Vorkommen ausdrücklich zählbar; die gemeinsame
Baumdiagnose erhält jedoch keinen uneingeschränkten positiven Marker.
Baumformen, Population, Hall of Fame und Endfront bleiben getrennt.

## 5. Vollständigkeit und Serienabschluss

Numerisch ungeklärte Mitglieder werden weder entfernt noch stillschweigend
als bestätigt gezählt. Bericht und Kurzfassung nennen vollständige Nenner
sowie bestätigte, ungeklärte und nicht beurteilte Mitgliedspositionen.

Ein technisch vollständiger Abschluss verlangt weiterhin genau sechs
abgeschlossene Zellen, drei bestandene Originalpaarvergleiche, vollständige
Beobachtungsnachweise und bestandene Abschlussverifikation. Ein solcher
Abschluss bestätigt die vollständige Erfassung und Klassifikation;
er behauptet nicht die numerische Bestätigung jedes Mitglieds.
Ungeklärte Mitglieder begrenzen entsprechend die inhaltlichen Aussagen.
Die ursprünglichen Grenzen zu Auftreten, Pareto-Filterung, Aliasraster
und physikalischer Identifikation bleiben bestehen.

Alte Format-1-Pakete erhalten durch diese Ergänzung keinen nachträglichen
Format-2-Abschluss. Es gibt keine Wiederaufnahme des abgebrochenen Laufs.

## 6. Ressourcen und technische Prüfungen

Native Replays gehören zur nachgelagerten Auswertung. Ihre Laufzeit wird
gesondert erfasst. Objective-Callbackzahl, Originalergebnisse und
Zufallszustand dürfen sich durch den Export nicht ändern.

Die bestehenden Grenzen bleiben bestehen: 3600 Sekunden insgesamt,
höchstens 600 Sekunden je Worker und höchstens 256 MiB Beobachtungsdateien
je beobachteter Zelle. Die Dateigrenze umfasst gemeinsam Rohaufnahmen,
Einheitenstatus und native Replays. Fehlende, abgebrochene oder zu große
Exporte sind harte Fehler; keine Trunkierung oder automatische Wiederholung.

Vor Merge erforderlich:

- fünf gebundene Originalgegenfälle mit getrennten gespeicherten und
  nachgerechneten Werten, einschließlich plattformneutraler Prüfung der
  übermittelten Vorhersagebits;
- analytische erfolgreiche Kontrollen, gemischte Vorkommen und nichtendliche
  Gegenfälle; kein ungeklärtes Vorkommen darf positiv gezählt werden;
- Manipulationsfälle für Bindungen, Vorhersagen, native MSE, Quelldateien,
  Originalauswahl und späte Änderungen während Abschlussverifikation;
- native Roundtrips und Callback-/Zustandsschutz sowie bestehende technische
  Aus/an/aus-Integration; keine wissenschaftliche Serie in der CI;
- vollständige technische CI und gezielte KI-basierte Prüfung der neuen
  Status- und Abschlussregeln.

Die Korrektur autorisiert keine zusätzliche wissenschaftliche Serie.
Ein frischer Sechszellenlauf ist erst nach geprüftem Stand und Merge
gesondert zu entscheiden.
