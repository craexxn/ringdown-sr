# Technische Präzisierung: Tabellenverlust ist kein weiterer Reduktionslauf

Stand: 03.11.2026. Ergänzung zur vor Code gebundenen
[Verifikationsregel](search_duration_verification_plan.md), ohne Änderung ihrer
nativen Verlust- oder Vorhersageschranken. Dieser Befund wird vor der
Implementierungskorrektur separat committed und zusätzlich durch SHA-256
gebunden. Die bisherigen Pläne bleiben unverändert.

Die lokale technische Integration am Implementierungscommit
`ab32fcf527b3db0a910aed881b4a257509033ab9` besteht für K2/A2 und scheitert bei
K3 am Achtpunkt-Signal `y=1+t`. Der betroffene CSV-Eintrag lautet:

```text
4,0.008261169598036541,"exp(t * 0.8401887737401458)"
```

Die gepinnte PySR-Version 2.6.0 liest in `_read_equation_file` mit
`pandas.read_csv(StringIO(buf))` ohne Roundtrip-Präzisionsoption. Der exakt
reproduzierte Tabellenwert ist `0.0082611695980365`. Sein relativer Abstand
zur aus NumPy-Vorhersagen exakt rational berechneten MSE beträgt etwa
`5,53e-15`; die Reduktionsschranke für acht Residuen beträgt `1,11e-15`.
Die Dezimalzeichenfolge selbst, mit Python float gelesen, liegt dagegen
innerhalb dieser Schranke. Das ist ein anderer Verarbeitungsschritt als
eine MSE-Reduktion und erklärt die zusätzliche Ablehnung.

Der Tabellenwert bleibt als tatsächlich gelesener Wert gespeichert und wird
weiter mit dem ursprünglichen Vertrag `rtol=1e-10, atol=0` gegen den nativen
Verlust geprüft. Er wird nicht zusätzlich als eigenständige native Reduktion
behandelt. Die exakte rationale Gamma-Prüfung bleibt unverändert für den
gespeicherten nativen Verlust, nativen Replayverlust und die unabhängige
Python-MSE, jeweils gegen ihre eigenen Residuen. Vorhersageprüfung,
Residuenbits, Fehlerzerlegung, Auswahllogik und Erfolgsschwellen bleiben
ebenfalls unverändert. Im Kandidatennachweis ist die Rolle des Tabellenwerts
als PySR-/Pandas-CSV-Wert ausdrücklich gekennzeichnet.

Keine Änderung an Pandas, PySR, CSV-Dateien, Suchaufrufen oder Zielfunktion.
Die Schranke wird nicht vergrößert. Ein separater Gegenfall muss einen
Tabellenwert außerhalb des alten relativen Vertrags weiterhin ablehnen;
falsche echte Verluste innerhalb dieses gröberen Tabellenvertrags müssen
weiter an der strengeren Residuenprüfung scheitern.

Der fehlgeschlagene technische Lauf bleibt erhalten. Nach Korrektur werden
die vollständige technische Integration und CI am neuen Commit ausgeführt.
Keine wissenschaftliche Serie wurde hierfür begonnen.
