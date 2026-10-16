# WORKSPACE — lokaler Arbeitsbereich `RE-Projects`

> Kurzfassung: Erwartete Ordnerstruktur neben diesem Repository (Hub, Spielkopien, Ghidra-Projekt), Zuständigkeiten, Weg einer Messung und Bauen/Prüfen. Übernommen aus der lokalen Übersicht `RE-Projects/README.md` (Stand 2026-10-15), für die Veröffentlichung verallgemeinert.

Die Werkzeuge (`tools/paths.py`) erwarten die Geschwister dieses Repositorys in einem gemeinsamen Elternordner, hier `RE-Projects` genannt. Der Elternordner ist selbst **kein** Git-Repository. Lokal heißt dieses Repository `SH2-Perf`; der vorgeschlagene öffentliche Name ist `Stronghold2PerformanceResearch` (der Ordnername darf abweichen, `paths.py` leitet alles aus der Lage des Repositorys ab).

## Ordner

| Ordner | Zuständigkeit | Git | Ändern? |
|---|---|---|---|
| `SH2-Perf/` (dieses Repo) | Dokumentation (`docs/`), Auswertungswerkzeuge (`tools/`), Ghidra-Skripte (`ghidra_scripts/`), Audit-Kopien (`audits/`), Rohaufnahmen (`captures/`, nicht in Git) und Kennzahlen (`data/`) | ja | ja |
| `Stronghold2AnalyseHub/` | Messbibliothek (Hub-DLL), d3d9-Proxy, Launcher, native Tests. Upstream `github.com/crycodebaby/Stronghold2AnalyseHub`; unsere Arbeit auf Branch `perf-metrics` | ja | ja, auf einem eigenen Branch |
| `Stronghold 2/` | eigene **Originalinstallation** (Steam, Version 1.5) | nein | **nie** (schreibgeschützt behandeln) |
| `Stronghold 2 - TEST/` | Kopie des Originals für alle Experimente: Proxy `d3d9.dll`, `Stronghold2AnalyseHub.dll`, `SH2Proxy.ini`, optional DXVK/LAA-Exe; Ausgabeordner `SH2Perf_out/` | nein | ja, nur über `tools/variant.py` |
| `ghidra-projects/` | Ghidra-Projekt `SH2` (Analyse von `Stronghold2.exe`, `dragonfly.dll`, `granny2.dll`) | nein | nur durch Ghidra; Analysen bevorzugt in einer Arbeitskopie; Sicherungen des geschlossenen Projekts als ZIP + `SHA256SUMS.txt` |

Ghidra und DXVK liegen außerhalb, unter `%USERPROFILE%\Tools\` ([SETUP.md](SETUP.md)). Spielinstallation, Rohaufnahmen und Ghidra-Datenbank sind nicht veröffentlicht; wer sie braucht, erzeugt sie aus der eigenen Spielkopie neu ([REPRODUCIBILITY.md](REPRODUCIBILITY.md)).

Innerhalb dieses Repositorys:

| Pfad | Inhalt |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Einstieg für Agenten (werkzeugneutral bzw. Routing-Tabelle) |
| `docs/STATE.md` | aktueller Stand, offene Aufgaben, nächster Schritt (**zuerst lesen**) |
| `docs/FINDINGS.md` | Fakten F### mit Status `[verifiziert]` / `[Hypothese]` / `[widerlegt]` und Beleg |
| `docs/DECISIONS.md` | Entscheidungen D### mit Begründung und verworfenen Alternativen |
| `docs/EXPERIMENTS.md` | Szenarien, Messprotokolle, Ergebnisse |
| `docs/FORMATS/` | Dateiformate (Spiel und Hub-Aufnahmen: `HUB_CAPTURE.md`) |
| `docs/SETUP.md` | Werkzeuge, Versionen, Build- und Testbefehle |
| `captures/` | Rohdaten (Bronze), nicht in Git; nur über Werkzeuge lesen. Bestehende Aufnahmen werden nicht verschoben |
| `data/index.jsonl`, `data/annotations/`, `data/silver/` | eine Kennzahlenzeile pro Aufnahme (Silber, aus Bronze + Annotationen ableitbar: `ingest.py rebuild`); Nutzerangaben in `annotations/`; `silver/` und `vtables.db` werden neu gebaut |

## Wie eine Messung entsteht

```
Spiel (TEST) ── d3d9.dll (Proxy) ──► lädt Stronghold2AnalyseHub.dll ──► Schalter (Config)
      Render-Thread: nur Zähler/Zeitstempel → Ring (wartefrei) ──► Capture-Thread ──► SH2Perf_out/
                                                                      SH2Perf_<ts>_frames.csv, _threads.csv,
                                                                      _samples.csv, Manifest, latest.json, Log
SH2Perf_out/ ── tools/ingest.py (prüfen → Staging → atomare Freigabe; Quellen bleiben) ──► captures/<capture_id>/
                                                              └─► data/silver + data/index.jsonl (Kennzahlen) ──► docs/
```

Aufnahmewege (alle schreiben nach `Stronghold 2 - TEST/SH2Perf_out/`):

| Weg | Bedienung |
|---|---|
| Hotkeys im Spiel | **F9** Aufnahme an/aus, **F8** Marker setzen, **F10** Histogramm zurücksetzen, **END** Hub deaktivieren. Ohne Overlay gibt F9 einen hohen Ton (Start) / tiefen Ton (Stopp) |
| Automatisch | Umgebungsvariable `SH2HUB_AUTORECORD=<Bilder>` (Tests, Stand-in-Programm) |
| Launcher (Rückfall) | `SH2Launcher.exe` startet das Spiel angehalten und injiziert die DLL (D004, durch den Proxy abgelöst) |
| Profiler | `variant.py sample module\|function` — separater Schalter, standardmäßig aus |

Schalter des Hub (D011), gesetzt mit `python -I tools/variant.py mode full|min` und `... switch <name> on|off|default` (liegt in `SH2Proxy.ini`; Umgebungsvariable `SH2HUB_<NAME>` hat Vorrang): `frametime`, `counters`, `poll`, `overlay`, `beep`; getrennt davon `sample` und `granny` (beide standardmäßig aus). Profile: `full` (Standard) und `min` (nur `frametime`). Details: Hub-README.

## Bauen und prüfen

```
cd Stronghold2AnalyseHub
cmake -S . -B build -A Win32            # nach jedem Commit neu (Commit-Id wird eingebaut)
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure -LE timing   # ohne Spiel
cd ..\SH2-Perf
python -I tools/run_checks.py           # alle spielfreien Python-Prüfungen + Doku-Lint
python -I tools/variant.py baseline     # nur mit eigener Spielkopie: Proxy + Hub-DLL in die TEST-Kopie kopieren
```

## Regeln

- `Stronghold 2/` (Original) bleibt unverändert; Experimente laufen nur in `Stronghold 2 - TEST/`.
- Keine bestehenden Aufnahmen oder Spielverzeichnisse verschieben oder umbenennen.
- Die Repositories enthalten nur eigenen Code und Doku: keine Spieldateien, Binaries, Ghidra-Datenbanken oder dekompilierten Code.
- Messwerkzeuge lesen nur; Hooks in Spielcode folgen erst aus Messdaten (D005).
- Beobachtung und Annahme getrennt halten (`[verifiziert]` / `[Hypothese]`); kein Performancegewinn ohne Vergleichsdaten.
- Rohlogs nur ohne persönliche Pfade weitergeben (D007).
