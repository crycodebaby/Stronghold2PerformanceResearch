# Auftrag: unabhängige Gegenprüfung des Animationspfads

> Kurzfassung: Vollständiger Auftrag für einen frischen Agenten: vorhandene Evidenz unabhängig prüfen, einen engen Engine-Pfad klären, Beobachterfehler reproduzieren und einen entscheidenden Folgeversuch formulieren. Keine Produktionsänderung oder neue Spielaufnahme.

Du arbeitest als unabhängiger Senior Reverse Engineer und Performance Engineer in einem eigenen lokalen Analysechat. Bestehende Stronghold-2-Repositories sind ausschließlich lesende Quellen; alle neuen Ergebnisse und eigenen Skripte liegen im neuen Chat-Arbeitsordner. Dies ist ein frischer Auftrag: Prüfe die bisherige Arbeit kritisch und ergebnisoffen. Frühere Agentenberichte sind zu prüfende Aussagen, keine Autorität.

Ziel
Entscheide anhand vorhandener Binärdateien, Aufnahmen und Code: Verstehen wir den beobachteten Granny-Animationspfad richtig, und welcher kleinste nächste Versuch kann eine sichere Optimierung bestätigen oder widerlegen? Liefere zusätzlich einen ausführbaren Nachweis des aktuellen Beobachterproblems. Ein belegter Irrtum oder ein begründetes Verwerfen unserer Cache-Idee ist ein wertvolles Ergebnis. Ein FPS-Gewinn ist in diesem Auftrag keine zugesicherte Abnahme.

Arbeitsorte (relativ zum Root des SH2-Perf-Projekts; dort starten)
- Eingangsprojekt (nur lesen): .
- Hub: ../Stronghold2AnalyseHub
- Spiel original: ../Stronghold 2 (nur lesen)
- Testinstallation: ../Stronghold 2 - TEST (in diesem Auftrag nur lesen)
- Ghidra-Projekte: ../ghidra-projects

Start
Lies zuerst anwendbare AGENTS.md/CLAUDE.md, dann im SH2-Perf-Projekt docs/STATE.md, den obersten aktuellen Abschnitt von docs/HANDOFF.md, docs/evidence/EXP-008R_G1_PARTIAL.md und docs/FORMATS/GRANNY_OBSERVER.md. Weitere Dateien gezielt über diese Wegweiser. Ältere operative Aufträge im Handoff sind Kontext; führe insbesondere G2 oder die dort vorgeschlagene Produktionskorrektur nicht automatisch aus. Prüfe Git-Status, Binär- und Aufnahmeidentität. Ausgangsstand beim Formulieren: SH2-Perf 02bce97, Hub 32ebc38; spätere Änderungen zuerst einordnen und erhalten.

Kontext, unabhängig nachzuprüfen
Stronghold 2 Steam 1.5, x86. Ziel später: Original-Exe mit abschaltbarer Drop-in-Erweiterung, Referenzszene 257 Einheiten bei Speed 90, mindestens 45 FPS durchschnittlich / 30 FPS 1% low, unverändertes Spielverhalten.
EXP-007 Flat-Sampling zeigt u.a. Granny-Vertex-Deformation FUN_50008810 und Kurvenhelfer; daraus geschätzte Millisekunden sind keine direkt gemessenen Funktionslaufzeiten oder sicher einsparbare Zeit.
EXP-008R:
- A1 ohne Beobachter: rec-20261015T121438Z-7d436886.
- G1 mit Beobachter: rec-20261015T122211Z-dff71642, Speed 90 und finaler Pauseabschnitt vom Nutzer bestätigt.
G1 hat intakte Frame-Dateien, aber 126.632 fehlgeschlagene Instanzaggregationen. Daher keine vollständige Grundgesamtheit und keine allgemeine Cache-Freigabe. Berichtet wurden 1.503 erfasste Zeigerreihen mit wiederholt gleichen beobachteten Eingaben sowie andere mehrfach pro Bild benutzte Zeiger mit wechselnden Uhrwerten/Offsets. F136 bleibt Hypothese.

Arbeitspaket 1: Evidenz und Beobachter unabhängig prüfen
Rechne die tragenden Aussagen aus Rohdaten nach: Verluste/Abdeckung, Call-Zähler, Filter und Gleichheitsvergleiche, Zeigerwiederverwendung, Phasenzuordnung, Messbeeinflussung. Prüfe insbesondere, ob Aussagen über bereits gespeicherte Zeiger trotz fehlender neuer Zeiger wirklich zulässig sind. Suche Gegenbeispiele und unterscheide Uhrgleichheit, Argumentgleichheit, gleiche Speicherinhalte und gleiche Ergebnisse. Prüfe relevante Hook-Signaturen, Aufrufkonventionen und Weiterleitung, soweit für die Schlussfolgerung nötig. Keine Vollprüfung des gesamten Hubs.

Arbeitspaket 2: Einen konkreten Engine-Pfad klären
Untersuche gezielt FUN_0078E4D0 und seine unmittelbaren relevanten Aufrufer, den Sample-Rücksprung RVA 0x0038E6DF und bei Bedarf die bekannten Deform-Aufrufstellen. Kläre so weit statisch belegbar:
- Woher kommen Modellzeiger, Uhrargument, Offset und Pose-Objekte?
- Gibt es Belege für Nutzung eines Modellobjekts durch mehrere logische Figuren?
- Welche weiteren Eingaben oder Änderungen können gleiche beobachtete Argumente bei unterschiedlichen Ergebnissen erklären?
Trenne statische Verbindung von dynamisch beobachteter Verbindung. Verwende Modul-Hash plus RVA; keine erfundenen Originalnamen. Nicht vollständige Dragonfly-Engine oder sämtliche Funktionen analysieren. Bei nicht auflösbaren indirekten Verbindungen dokumentiere die Grenze und eine gezielte Prüfmöglichkeit.

Arbeitspaket 3: Ausführbarer Nachweis ohne neue Spielaufnahme
Erstelle einen kleinen reproduzierbaren Test oder eine Simulation, der/die den relevanten Tabellenfehler unabhängig nachweist und das vorgeschlagene Prinzip für einen besseren Beobachter prüft. Berücksichtige >8.192 kumulierte Zeigerschlüssel, viele Uhr-Aufrufe ohne beobachtetes Sampling, mehrfaches Sampling pro Bild, beobachtetes Free/Reuse und kollidierende Schlüssel. Nutze die echten Verteilungen als Grundlage, markiere synthetische Reihenfolgen aber ausdrücklich.
Die CSVs sind aggregiert: Behaupte keinen exakten Ereignis-Replay, wenn die Aufrufreihenfolge fehlt. Alte aufgezeichnete Zeiger niemals als gültige Speicheradressen dereferenzieren. Ein Simulator beweist keine reale Hook-Latenz oder reale Engine-Identität. Zeige einen Fehlerfall im bestehenden Verfahren und prüfe, dass die vorgeschlagene Alternative keine Verluste oder Gleichheiten stillschweigend verschweigt. Keine vollständige Neuentwicklung des Produktionsbeobachters.

Erlaubte Mittel und Arbeitsweise
Arbeite selbstständig bis zum prüfbaren Ergebnis. Nutze vorhandene Analysewerkzeuge, Ghidra/REA, Disassembly, lokale Testprogramme, Skripte und Primärdokumentation nach Bedarf; prüfe tatsächliche Verfügbarkeit statt Fähigkeiten zu erfinden. Keine vertraulichen Spieldateien oder Rohlogs an externe Dienste übertragen. Keine kostenpflichtigen Dienste buchen. Falls ein Werkzeug fehlt, nutze verfügbare Alternativen und dokumentiere, welche Aussage dadurch offenbleibt. Änderungen an einer Ghidra-Datenbank nur in einer getrennten Arbeitskopie; Originalprojekt nicht verändern.

Änderungsumfang
Erzeuge eigene Audit-Skripte, Tests und INDEPENDENT_AUDIT_2026-10-16.md unter analysis/ im neuen Chat-Arbeitsordner, außerdem einen kurzen HANDOFF.md mit Ausführungsbefehlen. Alle bestehenden Repositories, deren Dokumentation, Produktionscode, Analysewerkzeuge, Originalspiel, TEST-Konfiguration und Rohaufnahmen bleiben unverändert. Werkzeuge mit Schreibwirkung auf diese Bestände nicht ausführen. Die Ergebnisse werden später separat geprüft und integriert. Artefakte aus Binäranalyse lokal halten; keinen dekompilierten Spielcode ins Repository übernehmen. Vorhandene Änderungen erhalten. Kein Push, keine Installation in TEST, keine neuen manuellen Spielaufnahmen und kein Engine-Patch. Stand-in-Tests ausschließlich in getrennten temporären Arbeitsordnern.

Abnahme
1. Nachrechenbare Bewertung der tragenden bisherigen Behauptungen: bestätigt, eingeschränkt, widerlegt oder offen; jeweils Quelle, Methode und Grenze.
2. Mindestens eine präziser belegte Verbindung im untersuchten Animationspfad oder eine konkrete, belegte Grenze ihrer Auflösbarkeit.
3. Ausführbarer Reproduktionsnachweis mit dokumentiertem Befehl, erwarteten/erhaltenen Ergebnissen und klarer Grenze zwischen echten Daten und synthetischem Test.
4. Vergleich zweier nächster Wege: enger Animations-/Ergebnisvergleich oder weitere Aufrufpfad-/Zeitlokalisierung. Empfiehl genau einen nach Erkenntniswert, Aufwand und Messbeeinflussung.
5. Der empfohlene nächste Versuch ist vorformuliert: Frage, zu erfassende Werte, Gültigkeitskriterien und welche möglichen Ergebnisse welche Schlussfolgerung erlauben. Keine erneute Aufnahme mit bekannt unzureichendem Beobachter.
6. Relevante Prüfungen ausführen und Bericht, Dateiverweise sowie Reproduktionsbefehle prüfen. Bericht und Startpunkt für einen weiteren frischen Agenten im eigenen Arbeitsordner speichern. Kein Abschluss nur mit einem allgemeinen Plan.

Abschluss für den Nutzer auf Deutsch
Beginne mit: Was wissen wir jetzt zuverlässiger, was war möglicherweise falsch, und was ist die nächste Entscheidung? Nenne entscheidende Befunde statt einer Werkzeugchronik. Belege keine Behauptung mit bloßer Agentenmeinung. Sage ausdrücklich, wenn weder eine sichere Optimierung noch ein neuer Engine-Befund nachweisbar ist. Dann ist eine belegte Eingrenzung samt Reproduktion das Ergebnis.

