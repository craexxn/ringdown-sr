# Zusatzbewertung Stufe 2: verifizierte Originalauswahlen

Stand: 05.11.2026. Retrospektive Anwendung der beschlossenen Strukturprüfung;
Leitfadenphase 1, Bewertungsstufe 2. Vier Originalarchive, 78 verifizierte
Originalauswahlen und 18 getrennte ursprüngliche Gruppen. Keine neue Auswahl,
kein Fit und keine wissenschaftliche Suche.

Anwendungscommit: `3aceb638f9a648caab4019008cb5beeba336f1a2`.
Bewertungsfassung `ringdown-sr-supplemental-assessment-2`,
Beweisfassung `ringdown-sr-structure-proof-1`.
Das geschlossene Intervall ist für alle Fälle exakt `[0,127/4096]` Sekunden;
es stammt aus den verifizierten Trainingsdaten. Regeln und Grenzen stehen im
[Strukturvertrag](supplemental_structure.md).

Die vier vollständigen Archive wurden erneut über den lesenden Import gebunden.
Alle 78 Originalidentitäten, ausgewählten Kandidaten, historischen Kennzahlen und
Kurvennoten stimmen mit der abgeschlossenen
[Stufe-1-Auswertung](supplemental_assessment_results_001.md) überein.
Die übernommenen historischen Serienberichte bleiben unverändert.

Eine separate Auswertung mit SymPy 1.14.0 bestätigte alle 40 ausgegebenen
positiven algebraischen Identitäten exakt aus den Originalbäumen und den neuen
symbolischen Koeffizienten. Diese Kontrolle verwendet keine Erkennerentscheidung
als mathematischen Beweis und bestätigt keine Originaldomain durch CAS-Kürzung.
Die Zahl 40 beschreibt den Kontrollumfang, keine gepoolte Erfolgsquote.

## Getrennte Originalgruppen

Mitgliedschaft verlangt zusätzlich zur Identität eine lückenlose Originaldomain.
Ein positiver Fortsetzungsbefund repariert das Original nicht. Ungeklärte Fälle
bleiben im geplanten Nenner; Kurve, Familie und Parameter werden nicht zu einer
neuen Erfolgszahl zusammengezogen.

| Serie / Signal / Bedingung / äußeres Budget | Nenner | Original Mitglied | Original Nichtmitglied | Original ungeklärt | Original nicht bewertet | Fortsetzung Mitglied |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| duration-manjaro-004 / anchor / unrestricted / 200 | 5 | 3 | 0 | 2 | 0 | 0 |
| duration-manjaro-004 / anchor / no_nested_trig / 200 | 5 | 1 | 1 | 3 | 0 | 0 |
| duration-manjaro-004 / anchor / no_nested_trig / 2000 | 5 | 3 | 0 | 2 | 0 | 0 |
| duration-manjaro-004 / anchor / unrestricted / 2000 | 5 | 3 | 0 | 2 | 0 | 0 |
| local-optimizer-manjaro-001 / anchor / local_100_2 / 200 | 5 | 1 | 1 | 3 | 0 | 0 |
| local-optimizer-manjaro-001 / anchor / local_300_2 / 200 | 5 | 2 | 1 | 2 | 0 | 0 |
| local-optimizer-manjaro-001 / anchor / local_300_5 / 200 | 5 | 2 | 1 | 2 | 0 | 1 |
| local-optimizer-manjaro-001 / anchor / local_100_5 / 200 | 5 | 1 | 1 | 3 | 0 | 0 |
| outer-ladder-manjaro-001 / anchor / local_300_5 / 200 | 5 | 1 | 0 | 4 | 0 | 0 |
| outer-ladder-manjaro-001 / anchor / local_300_5 / 500 | 5 | 5 | 0 | 0 | 0 | 0 |
| outer-ladder-manjaro-001 / anchor / local_300_5 / 5000 | 5 | 5 | 0 | 0 | 0 | 0 |
| outer-ladder-manjaro-001 / anchor / local_300_5 / 2000 | 5 | 5 | 0 | 0 | 0 | 0 |
| transfer-manjaro-001 / anchor / local_300_5 / 500 | 3 | 0 | 0 | 3 | 0 | 0 |
| transfer-manjaro-001 / frequency / local_300_5 / 500 | 3 | 1 | 0 | 2 | 0 | 0 |
| transfer-manjaro-001 / decay / local_300_5 / 500 | 3 | 1 | 1 | 1 | 0 | 0 |
| transfer-manjaro-001 / phase / local_300_5 / 500 | 3 | 2 | 0 | 1 | 0 | 0 |
| transfer-manjaro-001 / amplitude / local_300_5 / 500 | 3 | 0 | 1 | 2 | 0 | 1 |
| transfer-manjaro-001 / combined / local_300_5 / 500 | 3 | 2 | 0 | 1 | 0 | 0 |

## Einzelbefunde

`proven_on_original_domain` bezeichnet eine bewiesene algebraische Identität
auf dem nichtleeren Originalbereich. `original_domain_gap` begründet die
Nichtmitgliedschaft der Originalfunktion auf dem ganzen Prüfintervall, nicht
die algebraische Nichtzugehörigkeit ihrer Fortsetzung.

| Serie | Zelle | Kurve | Identität | Domain | Originalfamilie | Fortsetzung |
| --- | --- | --- | --- | --- | --- | --- |
| duration-manjaro-004 | cell-01 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| duration-manjaro-004 | cell-02 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| duration-manjaro-004 | cell-03 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| duration-manjaro-004 | cell-04 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| duration-manjaro-004 | cell-05 | A | unresolved | defined_everywhere | unresolved | not_applicable |
| duration-manjaro-004 | cell-06 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| duration-manjaro-004 | cell-07 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| duration-manjaro-004 | cell-08 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| duration-manjaro-004 | cell-09 | A | unresolved | defined_everywhere | unresolved | not_applicable |
| duration-manjaro-004 | cell-10 | C | unresolved | unresolved | unresolved | unresolved |
| duration-manjaro-004 | cell-11 | D | unresolved | removable_holes | proven_nonmember | unresolved |
| duration-manjaro-004 | cell-12 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| duration-manjaro-004 | cell-13 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| duration-manjaro-004 | cell-14 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| duration-manjaro-004 | cell-15 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| duration-manjaro-004 | cell-16 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| duration-manjaro-004 | cell-17 | C | unresolved | defined_everywhere | unresolved | not_applicable |
| duration-manjaro-004 | cell-18 | D | unresolved | unresolved | unresolved | unresolved |
| duration-manjaro-004 | cell-19 | C | unresolved | defined_everywhere | unresolved | not_applicable |
| duration-manjaro-004 | cell-20 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| local-optimizer-manjaro-001 | cell-01 | C | unresolved | defined_everywhere | unresolved | not_applicable |
| local-optimizer-manjaro-001 | cell-02 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| local-optimizer-manjaro-001 | cell-03 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| local-optimizer-manjaro-001 | cell-04 | C | unresolved | unresolved | proven_nonmember | unresolved |
| local-optimizer-manjaro-001 | cell-05 | C | unresolved | removable_holes | proven_nonmember | unresolved |
| local-optimizer-manjaro-001 | cell-06 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| local-optimizer-manjaro-001 | cell-07 | C | unresolved | removable_holes | proven_nonmember | unresolved |
| local-optimizer-manjaro-001 | cell-08 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| local-optimizer-manjaro-001 | cell-09 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| local-optimizer-manjaro-001 | cell-10 | A | proven_on_original_domain | removable_holes | proven_nonmember | proven_member |
| local-optimizer-manjaro-001 | cell-11 | C | unresolved | defined_everywhere | unresolved | not_applicable |
| local-optimizer-manjaro-001 | cell-12 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| local-optimizer-manjaro-001 | cell-13 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| local-optimizer-manjaro-001 | cell-14 | C | unresolved | defined_everywhere | unresolved | not_applicable |
| local-optimizer-manjaro-001 | cell-15 | B | unresolved | unresolved | unresolved | unresolved |
| local-optimizer-manjaro-001 | cell-16 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| local-optimizer-manjaro-001 | cell-17 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| local-optimizer-manjaro-001 | cell-18 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| local-optimizer-manjaro-001 | cell-19 | C | unresolved | defined_everywhere | unresolved | not_applicable |
| local-optimizer-manjaro-001 | cell-20 | A | unresolved | defined_everywhere | unresolved | not_applicable |
| outer-ladder-manjaro-001 | cell-01 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| outer-ladder-manjaro-001 | cell-02 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-03 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-04 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-05 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-06 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-07 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| outer-ladder-manjaro-001 | cell-08 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-09 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-10 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-11 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-12 | B | unresolved | defined_everywhere | unresolved | not_applicable |
| outer-ladder-manjaro-001 | cell-13 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-14 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| outer-ladder-manjaro-001 | cell-15 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-16 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-17 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-18 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-19 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| outer-ladder-manjaro-001 | cell-20 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| transfer-manjaro-001 | cell-01 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| transfer-manjaro-001 | cell-02 | C | unresolved | defined_everywhere | unresolved | not_applicable |
| transfer-manjaro-001 | cell-03 | C | unresolved | unresolved | proven_nonmember | unresolved |
| transfer-manjaro-001 | cell-04 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| transfer-manjaro-001 | cell-05 | A | proven_on_original_domain | removable_holes | proven_nonmember | proven_member |
| transfer-manjaro-001 | cell-06 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| transfer-manjaro-001 | cell-07 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| transfer-manjaro-001 | cell-08 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| transfer-manjaro-001 | cell-09 | B | unresolved | defined_everywhere | unresolved | not_applicable |
| transfer-manjaro-001 | cell-10 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| transfer-manjaro-001 | cell-11 | C | unresolved | defined_everywhere | unresolved | not_applicable |
| transfer-manjaro-001 | cell-12 | C | unresolved | unresolved | unresolved | unresolved |
| transfer-manjaro-001 | cell-13 | C | unresolved | defined_everywhere | unresolved | not_applicable |
| transfer-manjaro-001 | cell-14 | B | unresolved | defined_everywhere | unresolved | not_applicable |
| transfer-manjaro-001 | cell-15 | D | unresolved | defined_everywhere | unresolved | not_applicable |
| transfer-manjaro-001 | cell-16 | A | proven_on_original_domain | defined_everywhere | proven_member | not_applicable |
| transfer-manjaro-001 | cell-17 | B | unresolved | defined_everywhere | unresolved | not_applicable |
| transfer-manjaro-001 | cell-18 | D | unresolved | defined_everywhere | unresolved | not_applicable |

## Grenzen und ungeklärte Nachweise

Die begrenzte Fassung behauptet bei nicht unterstützten Faktoren, nichtaffinen
Argumenten, trigonometrischen Produkten oder nicht bewiesenen mehreren Moden
keine Nichtzugehörigkeit. Unvollständig bewiesene Nennerbedingungen sperren den
globalen Identitäts-/Fortsetzungsnachweis. Ein Ressourcenabbruch bleibt ungeklärt;
das beschlossene Budget wird nicht nachträglich zur Verbesserung der Zahlen erhöht.

| Grund eines ungeklärten Identitätsnachweises | Fälle |
| --- | ---: |
| `analysis_step_limit` | 1 |
| `multiple_modes_without_nonmembership_proof` | 1 |
| `nonaffine_argument` | 9 |
| `original_domain_nonempty_not_proven` | 5 |
| `trigonometric_product_not_supported` | 6 |
| `unsupported_normalized_factor` | 16 |

Die Parameter-/Aliasbefunde stammen unverändert aus den Originalen. Neue
Parametermatches und Restterm-Diagnosen bleiben `not_assessed`. Vollständige
Kandidaten, exakte Koeffizienten, Definitionsbedingungen, Beweisschritte,
Intervallzertifikate und Ressourcenverbrauch stehen in `assessment_records.json`.

## Artefakte und Fortsetzung

Lokales vollständiges Paket: `results/supplemental-structure-all-001.tar.gz`.
SHA-256: `cc52de459a4c250b4e70f9290898f9c0b9011e1182dccfc16dd47f8a40c19356`.
Größe: 2017428 Bytes. Das vollständige Manifest mit sieben
gebundenen Dateien wurde geprüft; Bericht `completed`, Korpus `complete`,
keine `ASSESSMENT_LOCKED`-Datei.

| Datei | SHA-256 |
| --- | --- |
| `assessment_records.json` | `da38b8d6ee08937cfca9400edcc6fd9e03bf97a4cc8489e05dd880bf3e58ca35` |
| `assessment_report.json` | `0658e3519b46e31bebc9d0309d234f8248b6e2e831c37879fe49c6761e73d71d` |
| `assessment_summary.md` | `d4f9769cc2436377b2d18188b99ae5d40d9f37d431837bd42bd27fe1092918d8` |
| `duration-manjaro-004-historical-report.json` | `ba6ff1c5b1e8981898006d33f9f73934edbc234f00460f4283bd33889712ecb1` |
| `local-optimizer-manjaro-001-historical-report.json` | `a635585b09809eb2be3ec5b9bc006d83da2a0fa5f208822e934c3b82887e1e83` |
| `outer-ladder-manjaro-001-historical-report.json` | `b8920254f1bbe63619663d70871d992fcb19e016d15330fca8f7657c0653ca77` |
| `transfer-manjaro-001-historical-report.json` | `365a0e9cc3d6af48c512973b7649f5866c2769bf3c2a63914989d2cf3e78813c` |

Technische Prüfungen, PR und Übergabe stehen im
[bestehenden Arbeitsdokument](representation_implementation_status.md).
**Nächste ausstehende Stufe nach bestätigter Übernahme:** Stufe 3, quantifizierte
Zusatzterm-Diagnose. Deren Zerlegungsregeln und Schranken sind vorher zu klären.
Keine automatische neue Suchserie oder Budgeterhöhung.
