# H-Pose: automatische native Abnahme

> Kurzfassung: Versionierter JSON-Bericht, strikte Fehlergates und atomische Erfolgsausgabe fuer den eigenen Win32-Test. CI-Schritt lokal vorbereitet, kein GitHub-Lauf oder Push. Keine neue Engine-Erkenntnis.

Datum: 2026-10-17. Lokale Basis `2059da1`, Branch `hpose-native-ci`. Dieser Werkzeugauftrag ergaenzt den
[Erzeugungs-/Auswahlnachweis](HPOSE_CREATION_2026-10-17.md). `record_range.h`, Pose-Mathematik, Hub und Spielverhalten
bleiben unveraendert. Die Allokationsgrenze hinter RVA `0x38D500` wurde hier nicht weiter untersucht.

## Ergebnisvertrag

Der eigene native Test schreibt genau ein JSON-Objekt auf stdout, nach Abschluss seiner Pruefungen:

```json
{"schema":"sh2perf.hpose-range-test","version":1,"completed":true,"checks":6383,"failures":0}
```

Die Anzahl 6383 beschreibt den aktuellen Teststand und ist keine festgeklemmte Runner-Schwelle. `checks` muss ein
positiver Integer sein, `failures` ein nichtnegativer Integer <= checks. Bool/Float sind keine Integerzaehler.
Schema/Version muessen bekannt sein, `completed` muss true sein. Doppelte Schluessel, mehrere JSON-Dokumente,
leere/beschaedigte Ausgabe, NaN/Infinity und Exponentenueberlauf zu nichtendlichen Werten werden abgewiesen.
Das sind Angaben unseres eigenen Tests, kein Beweis vollstaendiger Spiel-/Pose-Semantik.

`tools/hpose_native.py` akzeptiert Erfolg nur nach erfolgreichen Configure-/Build-/Host-Prozessen und gueltigem
Bericht mit failures=0. Ein Host kann vollstaendige Fehlertestergebnisse ausgeben und trotzdem korrekt scheitern.
Vor Tooldiscovery/Build/Start wird eine alte `build/hpose-native/results.json` entfernt. Erst nach Validierung und
Quell-/Host-Hashbildung wird eine neue Datei ueber eine eindeutige Tempdatei, flush/fsync und replace veroeffentlicht.
Fehler hinterlassen keine aktuelle Erfolgsausgabe; aktuelle Tempdateien werden im normalen Fehlerpfad entfernt.
Getrennte stdout-/stderr-Logs bleiben lokal. Pro Ausgabeverzeichnis ist genau ein gleichzeitiger Runner vorgesehen.

## Ausfuehrbare Abnahme

```text
python -I tools/test_hpose_native.py
python -O -I tools/test_hpose_native.py
python -I tools/hpose_native.py
python -I tools/run_checks.py
```

Ohne CMake auf PATH: `python -I tools/hpose_native.py --cmake <cmake-executable>`.
Der Runner nutzt keine Granny-/Hub-Helfer mehr. Fuer den nativen Lauf genuegen eigene Quellen, Python, MSVC und CMake;
die neue Python-Suite braucht auch keinen Compiler. Die mathematische Auswahl und Feldprojektion wurden nicht geaendert.

Zehn neue Tests bestehen normal und mit optimiertem Python. Sie nutzen eigene temporaere Fixtures und echte isolierte
Python-Kindprozesse fuer Prozess-/Ausgabegates. Configure-/Build-/Host-Exitfehler, Spawnfehler und echte Timeouts werden
getrennt geprueft. Fehler beim Schreiben, fsync und replace sind gezielt injiziert; die Tests verlangen, dass genau
das jeweilige Fehlergate erreicht wird. Kein alter Erfolgsbericht oder aktuelles temporaeres Ergebnis bleibt uebrig.

Ein frischer Sol-6.1-Reviewer fand zwei konkrete Randfaelle, die der Projektleiter mit zunaechst roten Regressionen
belegte und korrigierte: Temp-/Checkout-Dateien auf verschiedenen Laufwerken sowie JSON `extra:1e999`, das vorher
Infinity persistieren konnte. Danach bestehen beide Gegenproben; der Reviewer wiederholte sie unabhaengig, einschliesslich
eigener Tempfixture auf einem anderen Laufwerk. Provenienzschluessel sind relativ zum jeweiligen eigenen Repo.

Der native Lauf bestand zusaetzlich in einer neu angelegten minimalen Quellkopie aus sechs eigenen Dateien, ohne Hub,
Granny-Helfer, Spiel oder Ghidra. Die neue Python-Suite bestand dort ebenfalls. Der echte Win32-Host meldete
completed=true, 6383 Pruefbedingungen und 0 Fehler. Dies bleibt ein synthetischer Vertragstest.
Ein anschliessender echter CLI-Lauf mit absichtlich fehlendem CMake wurde mit Exit 1 ohne Traceback abgewiesen und
entfernte den vorherigen Erfolgsbericht; der folgende gueltige Lauf erstellte ihn wieder korrekt. Die Gesamtpruefung
`python -I tools/run_checks.py` besteht 11/11 Pruefgruppen. Der native CTest-Eintrag besteht 1/1.

## CI und Grenze

`.github/workflows/checks.yml` fuehrt nach den Python-Pruefungen den nativen Runner als regulaeren fehlschlagenden
Schritt aus, ohne continue-on-error oder manuelle Freigabe. Das bestehende windows-2022-Image bringt die benoetigte
Toolchain mit ([primaere Image-Dokumentation](https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md));
es wird keine zusaetzliche Toolchain installiert. Die Workflow-Datei ist lokal vorbereitet; kein neuer Online-CI-Lauf
wurde gestartet oder bestaetigt. Keine Remote-/Branchschutz-Einstellungen wurden geaendert.

Keine Original-Exe/DLL-Ausfuehrung, Rohdaten-/Installations-/Ghidra-Aenderung, Spielaufnahme, Pose-Ersetzung oder
Performanceaussage. Naechster getrennter Forschungsauftrag bleibt die tatsaechliche H-Container-Allokation hinter
`0x38D500`; keine weitere allgemeine Nachhaertungsrunde ist Voraussetzung dafuer.
