# Kontextpflege: kleiner Einstieg fuer frische Projektleiter

> Kurzfassung: Einstieg auf Regeln, aktuellen Auftrag und gezielten Nachweiszugriff begrenzt; alte Texte vollstaendig archiviert. Frischer Lesetest ohne bisherigen Chatverlauf bestanden. Keine neue Spiel-/Binaeraussage und keine Codeaenderung.

Datum 2026-10-18; Forschungsbasis unveraendert `38d7e79`, F185. Dieser Baustein betrifft Dokumentation.

## Problem und Rollen

Die bisherigen Einstiegsdateien enthielten lange parallele Fortschrittschroniken, unterschiedliche fruehere
Folgeauftraege und Standardpfade, die fuer den aktiven Checkout nicht gelten. Ein neuer Agent sollte diese
Widersprueche nicht erst durch Einlesen des gesamten Chats rekonstruieren muessen.

- AGENTS: werkzeugneutrale Grenzen und kleine Lesereihenfolge.
- STATE: einziger aktueller Auftrag mit Startnachweis und letztem Forschungscheckpoint.
- PROJECT_LEAD_HANDOFF: dauerhafter Leitfaden fuer Quellenrollen, schrittweises Nachladen und Abnahme.
- HANDOFF: historischer Index, keine zweite aktive Auftragsliste.
- FINDINGS/evidence: fachliche Aussagen/Nachweise; Wissenskarte als optionaler verbundener Einstieg.
- PROJECT_LEAD_START_PROMPT: Vorlage ohne erneut festgeschriebene aktuelle RVAs/Auftraege.

Standardlayout und lokale Wirklichkeit sind jetzt getrennt. Persoenliche Pfade/Toolpositionen stehen nur in
ignoriertem `build/project-lead-handoff/LOCAL_ENVIRONMENT.json`; die ausgefuellte Promptfassung daneben.
Alle dort genannten Orte wurden dateilesend auf Existenz geprueft, Pythonlaufzeit/Gitposition festgehalten.
Connector-/MCP-Verfuegbarkeit, Programminhalte und kuenftige Dateiexistenz werden damit nicht garantiert.
Der Eintrag ist datiert; Git-Stand, Eingaben und Hashes vor Forschung selbst pruefen.

## Erhalt der Historie und Umfang

Die kanonischen Gittexte aus `38d7e79` von STATE, HANDOFF und PROJECT_LEAD_HANDOFF wurden jeweils unveraendert
nach `*_HISTORY_2026-10-18.md` uebernommen, mit vorangestelltem Archivhinweis. Gleicher docs-Ordner erhaelt
relative Links. Der alte kanonische Text ist als exakter Payload erhalten; neue aktive Dateien ersetzen ihn
nicht unbemerkt. Vergleich: Gitblob des jeweiligen Ausgangspfades gegen den Archivpayload zwischen Hinweis
und abschliessendem Archiv-Endkommentar,
bei Arbeitskopien mit normalisierten CRLF/LF. Alle drei Vergleiche bestanden.

Wortzaehlung der drei Kerndateien AGENTS.md, STATE.md, PROJECT_LEAD_HANDOFF.md mit Whitespace-Split:
vorher 7565, nachher 1286 Woerter, rund 83 % weniger verpflichtender Basiskontext in diesen Dateien.
Das ist **keine** Tokenmessung und keine Zusage gleicher Einsparung fuer jedes Modell. Aufgabe/Startnachweis
kommen gezielt hinzu; Archive, ganze FINDINGS und alte Audits sind kein automatischer Pflichtstart.

## Test ohne Chatverlauf

Ein neu gestarteter Sol-6.1-Pruefagent erhielt keinen bisherigen Chatverlauf, nur Repositoryort und Leseauftrag.
Er las die drei Kerndateien, die aktuelle Aufgabe, ihren Startnachweis und optional den lokalen Pfadindex.
Er sollte weder Forschung noch Tests/DB/Installation starten.

Er identifizierte korrekt:

- aktiven Checkout/Branch und das davon getrennte alte SH2-Perf-Archiv;
- genau die naechste E30C/Track+8-Contextfrage und die bedingte New-/Free-Startaussage;
- die offenen Allokations-/Lebensdauer-/Nichtalias-/Lesefensterpflichten und ausgesetztes G2;
- die getrennte Ghidra-Kopie statt eines blind abgeleiteten Geschwisterpfades;
- Abnahme, sinnvolle Prueferteilung und fehlende Garantie einer REA-MCP-Anbindung.

Kein Navigationsblocker. Er behandelte fruehere Testergebnisse als datierte Belege, nicht als eigene frische
Pruefung. Den sichtbaren Pythonlauncher hielt er korrekt noch nicht fuer einen Funktionsnachweis; der lokale
Pfadindex wurde daraufhin um den tatsaechlich benutzten Interpreter erweitert. Das ist ein praktischer
Lesetest, kein umfassender Agentenbenchmark und kein Ghidra-/REA-Funktionstest.

## Abschluss und Pflege

Promptvorlage und lokale ausgefuellte Fassung stimmen bis auf eingesetzten Repositorypfad ueberein.
Persoenlicher Pfadindex ist Git-ignoriert. Link-/Groessen-/Pfadlint und alle **16/16 regulaeren spielfreien
Pruefgruppen bestanden**. Keine Forschung, Original-/DLL-Ausfuehrung, Aufnahme, Installation oder
Hub-/Analysetool-Aenderung; kein neuer GitHub-CI-Lauf oder Push.

Kuenftig nur STATEs aktiven Scope/Checkpoint und die betroffene Evidenz/Kartenstation fortschreiben.
Keine neue parallele Chronik im Leitfaden. Historische Texte nur fuer konkrete Fragen nachladen.
