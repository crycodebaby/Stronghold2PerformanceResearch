# STATE

> Kurzfassung: Einziger aktueller Forschungsauftrag, letzter Nachweis und naechste Abnahme. Historische Fortschrittsberichte werden nicht zum Sitzungsstart geladen.

Stand: 2026-10-18. Letzter Forschungscheckpoint `38d7e79`, Branch zuletzt `hpose-allocation-proof`.
HEAD/Arbeitsbaum am Start selbst pruefen; Dokumentpflege kann danach committed sein. Kein Performancegewinn nachgewiesen.

## Current status (the only current order)

Ziel: abgegrenzte Spiel-/Engine-Logik belastbar verstehen, kleine eigene Teile gegen das Original pruefen,
danach gezielt Performance verbessern. Aktuell Animation/Pose, kein kompletter Engine-Nachbau.
Langfristiges Messziel: REAL_LAG_257, Speed 90, mindestens 45 FPS Mittel/30 FPS 1%-low; nicht erreicht.

**Naechster Auftrag:** [Contextvertrag an DLL 0xE30C -> Track+8](tasks/POSE_CALLBACK_CONTEXT_2026-10-18.md).
Fuer einen konkret belegten Callbackkandidaten die Read-/Write-/Weitergabespanne von Argument 1
(lokaler Context F-0x80) pruefen. Keine komplette Kurven-/Heaprekonstruktion. Ein praezise belegtes
unbekanntes Verhalten mit kleinstem Folgebeweis ist ein zulaessiger Abschluss.

**Startnachweis:** [Interne Poseherkunft, F183–F185](evidence/POSE_INTERNAL_PROVENANCE_2026-10-18.md).
E080 speichert zwei eigene NewWorldPose-Returns und laedt dieselben lokalen Felder fuer Free.
Das gilt bedingt auf unveraenderte Framefelder/gueltigen Calling-Convention-Vertrag, nicht als Lebensdauer-
oder H-Pose-Nichtaliasgarantie. Zwei Calls beweisen keine zwei erfolgreichen Allokationen.
Bekannte Contextkante 44DAB -> 2F5D0 ist in dieser DLL ein leerer Return; indirekter E30C bleibt offen.
Argument 1 ist nicht automatisch World-/Composite-Ausgabeziel. Ein Feldabstand beweist keine Schreibspanne.

## Erhaltener Wissensstand und Grenzen

- [Wissenskarte](ANIMATION_KNOWLEDGE_MAP.md): Einstieg ueber belegte Stationen, bei Bedarf; Fakten bis F185.
- Geschriebene Zielbytes, gueltige Transformwerte, lebende Generation und geschuetztes Leseintervall sind
  verschiedene Nachweise. Sicheres Live-Lesen und vollstaendige relevante Ereignisabdeckung bleiben offen.
- F136 (redundante Arbeit bei unveraenderten beobachteten Eingaben) bleibt Hypothese. Kein Cache/Skip.
- Letzte Spielaufnahme EXP-008R-G1 hat 126632 Instanzaggregationsverluste. Aussetzen von G2 bleibt bestehen;
  [Auditkorrekturen F148](evidence/POSE_CONTRACT_2026-10-16.md) nur laden, wenn Messdaten bewertet werden.
- Gruene eigene Pruefer validieren die genannten Gates/Modelle, nicht pauschal Ghidra/REA oder Engine-Verstaendnis.

## Checkpoint und Abnahme

Bei `38d7e79`: 16/16 regulaere spielfreie Pruefgruppen; 21 Sample-Verifiertests und Originaldatei-Gates
normal/-O bestanden. Unabhaengiger Byte-/Argument-/Code-/Dokumentreview ohne sachlichen Blocker.
Sample-Verifier Schema 2: 85 Eintraege/98 Bereiche, sieben Exe-Imports/14 Exporte, zwoelf direkte Kanten;
Allocator-/Heap-/Literalgates erhalten. Generationstestmodell unveraendert (19 Tests).
Keine Originalausfuehrung, neue Aufnahme, nativer/Hub-Umbau oder neuer GitHub-CI-Lauf in diesem Checkpoint.

Fuer den Folgebaustein gelten Abnahme und Grenzen in der verlinkten Aufgabe. Pflicht nach Aenderungen:
`python -I tools/run_checks.py`; --audit/--e2e bei Hub-/Observerbezug. Neue Gates zusaetzlich normal/-O.
Nachweis, Grenzen, genau einen Folgebeweis und diesen aktuellen Stand aktualisieren; lokalen Commit setzen.

## Arbeitsstand und Navigation

- Forschungsrepo und Hub sind oeffentlich; juengste Forschung ist nur lokal. Kein Push/PR in diesem Auftrag.
  [Veroeffentlichung/Reproduktion](REPRODUCIBILITY.md) enthaelt datierte Remote-/CI-Staende, keine Liveabfrage.
- Bereinigte oeffentliche Forschungshistorie normal fortsetzen; kein Neuexport/Rewrite oder Merge des alten Archivs.
- Lokale Pfade aus `build/project-lead-handoff/LOCAL_ENVIRONMENT.json`, falls vorhanden, selbst validieren.
  [WORKSPACE](WORKSPACE.md) und tools/paths.py beschreiben ein Standardlayout, nicht jeden lokalen Checkout.
- [Leitungsleitfaden](PROJECT_LEAD_HANDOFF.md): Kontext-/Nachweis-/Delegationsregeln.
- [Vorheriger STATE](STATE_HISTORY_2026-10-18.md) und [alte Uebergaben](HANDOFF.md): Historie, kein Auftrag.

Pflege: Nur aktuellen Auftrag, relevante Grenzen und letzten Checkpoint hier halten. Vorherige Detailergebnisse
stehen in Evidenz/FINDINGS; keine wachsende zweite Chronik anhaengen.
