# Einstieg für einen frischen Agenten

Stand 16.10.2026. Lies zuerst `INDEPENDENT_AUDIT_2026-10-16.md`. Der Auftrag ist abgeschlossen; dieser Handoff autorisiert **keine neue Spielaufnahme, Installation oder Produktionsänderung**.

Arbeitsordner: `<audit-workspace>`.
Eingänge ausschließlich lesen: `<RE-Projects>` mit SH2-Perf, Stronghold2AnalyseHub, Original/TEST und ghidra-projects. Kein Weiterarbeiten an den alten G2-/Produktionsaufträgen.

## Ergebnis

- Nachgerechnet: 126.632 Aggregationsfehler, 1.503 streng gefilterte stabile Zeigerreihen. Keine allgemeine Cache-Freigabe.
- Neu: `all_observed_same` ist kein allgemeiner Sample-zu-Sample-Uhrvergleich; ausgefallene Sample-Aggregation kann Pose-Ambiguität verbergen; 609 Schlussaufrufe ohne gespeicherte Frame-Zeile trotz null Frame-Drops.
- Neu statisch: Auswahl eines 20-Byte-Modell-/Pose-Datensatzes, unmittelbare Uhrquellen, `FreeCompletedModelControls` nach Sample und rekursiver Aufruf. Exe SHA-256 `f3ccdf9b…f32d34b`, zentrale RVA `0x0038E4D0`, Sample-Return `0x0038E6DF`; vollständige Hashes im Bericht.
- Genau eine Empfehlung: begrenzter tatsächlicher Pose-Ergebnisvergleich. Vorformulierter Versuch samt Vorbedingungen und Ergebnisentscheidungen im Bericht. Sichere Optimierung weiterhin nicht bewiesen.

## Reproduktion

Aus dem Arbeitsordner, Python 3.14 und PowerShell vorhanden:

```powershell
python -I .\analysis\audit_data.py
python -I .\analysis\observer_repro.py
python -I .\analysis\verify_binary.py
python -I .\analysis\audit_data.py --snapshot after
```

Erwartet/erhalten: A1 3 und G1 7 Dateien hashverifiziert; Differenz Metadaten minus Framezeilen Uhr 372 / Sample 187 / Deform 25 / Composite 25; neun Simulationstests OK; sechs ABI-/Import-/Exportprüfungen und 17 direkte Calls binär bestätigt; 190 Eingabedateien und beide Git-Zustände unverändert.

Alles inklusive erneuter Exporte aus der getrennten Ghidra-Kopie:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\analysis\run_audit.ps1 -ExportBinary
```

Ohne `-ExportBinary` werden die schon vorhandenen lokalen Exporte verwendet. Neue Exporte schreiben nur nach `work/binary`; die erste Ausführung an einem anderen lokalen Paketstand benötigt `-ExportBinary`. `run_audit.ps1` erstellt die Projektkopie nur, wenn sie fehlt. Ghidra liegt unter `%USERPROFILE%\Tools\ghidra_12.1.4_PUBLIC`; Pfad mit `-Ghidra` überschreibbar. Eingangsroot mit `-InputRoot` überschreibbar. Ein abweichender Snapshot/Quellhash muss bewusst neu auditiert werden, nicht automatisch überschrieben.

Die Simulationsdatei benutzt `workload_distribution.json` und `data_results.json`. Diese enthalten echte aggregierte Eingangsverteilungen. Reihenfolgen, Frames und zusätzliche Schlüssel sind synthetisch. Keine Rohdaten-/Adressdereferenzierung, kein exakter Ereignis-Replay, kein Latenztest. Nur semantisches Modell, keine fertige Beobachterimplementierung.

Der vorhandene native Hub-Test wurde als zusätzliche Prüfung in einem eigenen temporären Ordner ausgeführt; Log: `work/standin/result.txt`, Ergebnis 0 Fehler. Reproduktion ohne Arbeit in Bestandsordnern:

```powershell
$standin = Join-Path (Get-Location).Path 'work\standin-repeat'
New-Item -ItemType Directory -Force -Path "$standin\temp" | Out-Null
$build = '<RE-Projects>\Stronghold2AnalyseHub\build\Release'
Copy-Item -LiteralPath "$build\granny_observer_test.exe","$build\granny2.dll" -Destination $standin
$env:TEMP = "$standin\temp"
$env:TMP = "$standin\temp"
Push-Location $standin
try { & '.\granny_observer_test.exe'; if ($LASTEXITCODE -ne 0) { throw 'Native test failed' } }
finally { Pop-Location }
```

In einer separaten PowerShell ausführen; TEMP/TMP gelten dort nur für diese Sitzung. Das ist die **Fake**-Granny-DLL aus dem Hub-Testbuild, niemals die echte DLL aus der Spielinstallation. Der Test prüft seine enthaltene Beobachterkopie, nicht unmittelbar die installierte Hub-DLL.

## Zu erhaltender Stand

SH2-Perf `77af09e72f2e23434a32643454e9140367e73336`, Hub `32ebc38a05ea94cfc3fd831c1a12174b9a34f51c`, beide sauber. Seit dem Auftragsstand `02bce97` nur Audit-Auftrag/Statusdokumentation hinzugekommen. Originale, TEST, Rohaufnahmen und ursprüngliche Ghidra-Datenbank unverändert. `identity_before.json` / `identity_after.json` belegen den geprüften Umfang.

`analysis/` ist das kanonische Ergebnis. `outputs/analysis/` und das ZIP sind Auslieferungskopien; Binäranalyse-Arbeitsdateien unter `work/` sind lokal und nicht im ZIP. Die geplanten Puffergrenzen für einen nächsten Ergebnisvergleich sind noch nicht vollständig statisch validiert; daher ist der nächste Versuch ausdrücklich **vorformuliert, nicht aufnahmebereit**. Keine fehlende Messung durch Agentenmeinung ersetzen.
