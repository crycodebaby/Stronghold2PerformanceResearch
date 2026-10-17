# Projektübergabe: Stronghold 2 — belastbares Verständnis und gezielte Eingriffe

> Kurzfassung: Einstieg und Auftrag für einen neuen technischen Projektleiter. Ziel ist überprüfbares Wissen über abgegrenzte Stronghold-2-/Engine-Teilpfade bis zu testbaren eigenen Implementierungen und später belegten Performance-Eingriffen. Stand 2026-10-16; alte G2-Aufträge sind ausgesetzt, kein Performancegewinn nachgewiesen.

Fortschritt seit Erstellung: Der erste begrenzte Auftrag aus Abschnitt 8 ist bearbeitet;
[nativer Pose-Vertrag, eigener Composite-Helfer und Auditkorrekturen](evidence/POSE_CONTRACT_2026-10-16.md).
Der Nachbau ist im allgemeinen Float-Bereich nicht bitgleich. Für Fortsetzung zuerst
den aktuellen Anfang von [HANDOFF.md](HANDOFF.md) lesen: Exe-Pose-Besitz/Lebensdauer,
kein erneuter Start der hier historischen Erstauftragsliste und keine neue Aufnahme.

Veröffentlichung seit 2026-10-17: Beide Repositories sind öffentlich (Stand und Prüfungen in
[STATE.md](STATE.md) „Published state“). Die Angaben zu Remote, Push und Commit-Kennungen in Abschnitt 4 und 9
beschreiben den Stand dieser Übergabe vom 2026-10-16. Weitergearbeitet wird auf der öffentlichen, bereinigten
Forschungshistorie; zitierte lokale Kennungen löst [export/EXPORT_MAP.tsv](export/EXPORT_MAP.tsv) auf.
Der nächste Forschungsauftrag bleibt unverändert: Besitz und Lebensdauer der Exe-H-Pose-Datensätze.

Fortschritt 2026-10-17: [ein Erzeugungs-/Auswahlpfad](evidence/HPOSE_CREATION_2026-10-17.md) ist statisch
belegt (F154/F155), mit unabhaengiger Bytepruefung und eigener begrenzter C++-Adressarithmetik. Vollstaendige
Kapazitaet/Besitz/Freigabe/Reuse fehlen weiter. Der aktuelle HANDOFF grenzt als naechsten Schritt den Allokatorpfad
hinter RVA `0x38D500` ein; die untenstehende historische Erstauftragsliste nicht neu starten.

## 1. Rolle und Ziel

Übernimm die technische Projektleitung als Senior Reverse Engineer und Software Architect. Arbeite kritisch, selbstständig und ergebnisoffen. Frühere Agentenberichte sind zu überprüfende Aussagen; Nutzerbeobachtungen sind Kontext und teilweise bestätigte Abläufe, nicht automatisch gemessene Ursachen.

Das Ziel ist, Stronghold 2 so weit zu verstehen, dass wir konkrete Funktionen, Datenflüsse oder Logik belastbar beschreiben, gezielt untersuchen und kleine abgegrenzte Teile selbst implementieren sowie gegen das Original prüfen können. Dieses Wissen soll sichere, abschaltbare Performance-Verbesserungen ermöglichen.

Ein Nachbau bedeutet hier eine eigene Implementierung eines definierten Teilverhaltens. Er bedeutet weder automatisch vollständige Originalsemantik noch einen bereits austauschbaren Engine-Baustein. Ein Granny-Helfer ist Drittanbieterlogik; sein Nachbau darf nicht als Nachbau der Stronghold-Kampf- oder Simulationslogik bezeichnet werden.

Langfristiges Performanceziel bleibt: Original-Exe Steam 1.5 mit Drop-in-Erweiterung, Referenzspielstand mit 257 Einheiten bei Speed 90, mindestens 45 FPS im Mittel und 30 FPS beim definierten 1%-low. Noch nicht erreicht. Spielregeln, Speicherstände und Multiplayer-Verhalten sollen erhalten bleiben; deren Gleichheit ist bislang nicht umfassend geprüft.

Kein vollständiger Klon, kein 64-bit-Port und keine allgemeine Engine-Neuentwicklung in dieser Etappe.

## 2. Orte und Zugriffsgrenzen

Alle folgenden kurzen Projektpfade beziehen sich auf den Root von SH2-Perf.

- Arbeitsprojekt: SH2-Perf selbst — Dokumentation, eigene Werkzeuge, Ghidra-Skripte, Datenindex.
- ../Stronghold2AnalyseHub/ — eigener d3d9-Proxy, Hub und native Tests; Quelländerungen nur auf einem klar zugeordneten Arbeitsstand.
- ../Stronghold 2/ — Originalinstallation, ausschließlich lesen.
- ../Stronghold 2 - TEST/ — Testinstallation; zu Beginn nur lesen. Eine spätere Installation ist ein expliziter Arbeitsschritt mit geschlossenem Spiel, Sicherung, Build-Identität und Rückweg.
- ../ghidra-projects/ — vorhandene Ghidra-Datenbanken. Analysen vorzugsweise in getrennter Arbeitskopie; keine konkurrierenden Schreibzugriffe auf dieselbe Datenbank.
- captures/ — unveränderte Rohaufnahmen und Binäranalyse-Exporte; nicht in Git. Bestehende Quellen nicht verändern, löschen oder umbenennen.
- data/annotations/ — bestätigter Nutzerkontext; nicht durch Vermutungen ergänzen.
- data/silver/ und data/index.jsonl — abgeleitete Auswertungen, keine Ersatzquelle für Rohdaten.
- [audits/2026-10-16-independent/](../audits/2026-10-16-independent/README.md) — veröffentlichte Kopie von Bericht, Skripten und abgeleiteten Ergebnissen des separaten Audits, mit Herkunft und Änderungsliste (seit 2026-10-16 im Repository). Der ursprüngliche lokale Audit-Arbeitsordner (`analysis/` kanonisch, `work/` mit Binäranalyse-Exporten und Arbeitskopien) bleibt außerhalb des Repositorys; vollständige Reproduktion mit Rohdaten und Ghidra-Exporten nur dort bzw. mit eigener Spielinstallation. Als unveränderte Referenz behandeln.

Der Zugriff auf die Ordner dient dem lokalen Arbeiten. Ein GitHub-Clone des Hubs allein enthält weder unsere gesamte Projektkenntnis noch die Rohdaten oder Ghidra-Datenbanken.

## 3. Lesereihenfolge: begrenzter Einstieg

Zuerst anwendbare Projektanweisungen lesen, insbesondere [CLAUDE.md](../CLAUDE.md). Danach:

1. Diese Übergabe vollständig.
2. [STATE.md](STATE.md): aktueller Checkpoint und offene Arbeiten.
3. Nur den obersten aktuellen Abschnitt von [HANDOFF.md](HANDOFF.md); die folgenden alten Arbeitsaufträge nicht ausführen.
4. [Auditbericht](../audits/2026-10-16-independent/INDEPENDENT_AUDIT_2026-10-16.md) und [Audit-Handoff](../audits/2026-10-16-independent/HANDOFF.md).
5. [FINDINGS.md](FINDINGS.md), besonders F125–F147; [FUNCTIONS.md](FUNCTIONS.md); relevante EXP-006/007/008R-Abschnitte in [EXPERIMENTS.md](EXPERIMENTS.md).
6. Bei konkreter Arbeit: [Granny-Datenvertrag](FORMATS/GRANNY_OBSERVER.md), [DECISIONS.md](DECISIONS.md), [SETUP.md](SETUP.md), [Analysezustand EXP-007](evidence/ANALYSIS_STATE_EXP-007.md).
7. Dann nur die für den gewählten Auftrag nötigen Rohdaten, Quellen und Binärstellen.

Historische Zusammenfassungen können überholt sein. Ein Satz wie „Vorbereitung, noch kein Spieltest“ beschreibt teilweise eine frühere Etappe; der aktuelle Checkpoint hat Vorrang. Bei sachlichen Widersprüchen Belege prüfen, nicht einfach die jüngste Formulierung übernehmen.

## 4. Identität und Datenlage

Prüfe zu Beginn Git-Status, Branches, Änderungen und Binäridentität. Keine fremden Änderungen ungeprüft übernehmen oder committen.

- SH2-Perf zuletzt vor dieser Übergabe: ed6e5cf, Branch main, kein Remote.
- Hub: 32ebc38a05ea94cfc3fd831c1a12174b9a34f51c, Branch perf-metrics.
- Hub besitzt einen Upstream-Remote; keine Veröffentlichung oder Push ohne ausdrücklichen Auftrag.
- Exe SHA-256: f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b.
- Granny SHA-256 der geprüften lokalen Datei: 94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd.
- Aufnahmen binden den damaligen Granny-Dateihash noch nicht vollständig. Heutiger Dateihash und damalige aufgezeichnete Moduladressen sind unterschiedliche Belege.

Wichtige Eingänge:
- EXP-006: wiederholte Modul-Sampling-/Off-Kontrollen, IDs und Auswertung in EXPERIMENTS.
- EXP-007: Funktions-Sampling und geprüfte Funktionskarten.
- EXP-008R-A1: rec-20261015T121438Z-7d436886, Beobachter aus.
- EXP-008R-G1: rec-20261015T122211Z-dff71642, Beobachter an, Speed 90 und finaler Pauseabschnitt vom Nutzer bestätigt.
- Alter unvollständiger G1: rec-20261015T111010Z-d6bf1a9b; nicht mit dem korrigierten Build als ein Vergleichspaar vermischen.

## 5. Was über das Spiel belastbar bekannt ist

- Bestimmter Steam-1.5-Build, PE32/x86, Direct3D 9; Granny-Runtime 2.6.0.14. Original-Exe ohne LAA.
- Rund 40.216 automatisch inventarisierte Exe-Funktionen und viele RTTI-/Vtable-Zuordnungen. Diese Inventarisierung ist kein entsprechendes Maß semantischen Verständnisses.
- In der kontrollierten 257-Einheiten-Szene bei Speed 90: EXP-006 ohne Sampler etwa 32,8 ms laufend gegenüber 25,1 ms pausiert; Present-Thread etwa zu einem CPU-Kern ausgelastet.
- Granny ist in diesen Stichproben ein großer Kostenposten; konkrete SSE-Deformation und Kurvenhelfer sind lokalisiert. Angaben in Millisekunden aus Sampling sind Schätzungen und kein nachgewiesenes Einsparbudget.
- Der zusätzliche Laufend-/Pause-Aufwand liegt überwiegend in der Exe. Eine vollständige Aufteilung in Rendering, Simulation, Animation und Treiber ist nicht nachgewiesen.
- Enger Exe-Animationspfad FUN_0078E4D0: Auswahl eines 20-Byte-Modell-/Pose-Datensatzes, Uhr-/Matrixübergabe, Sampling, anschließender FreeCompletedModelControls-Aufruf und rekursive Verbindung.
- Während der bestätigten G1-Pause: 2.842 Sample- und 2.185 Deform-Aufrufe pro gespeichertem Frame.
- 1.503 streng gefilterte gespeicherte Zeigerreihen zeigen wiederholte gleiche beobachtete Werte. Andere Zeiger erhalten mehrfach pro Bild wechselnde Werte.
- Nicht bewiesen: gleiche verborgene Zustände, gleiche Pose-/Vertex-Ergebnisse, redundante Arbeit, sichere Ersetzbarkeit oder eine eindeutige Zuordnung eines Modellzeigers zu einem Soldaten.

Granny2.dll ist eine mitgelieferte Drittanbieterbibliothek für u.a. Animation und Deformation. granny_observer.cpp ist unser eigener Messcode. Ein Fehler des Beobachters ist kein Beweis eines Fehlers im Spiel oder der Bibliothek.

## 6. Was der Audit zusätzlich über unsere Messung gezeigt hat

Die folgenden Punkte sind im separaten Bericht belegt; die neun Simulationstests wurden auch im leitenden Chat erneut erfolgreich ausgeführt:

- G1 verliert 126.632 Instanzaggregationen; bestehende gespeicherte Schlüssel tragen dennoch bestimmte eng begrenzte Beobachtungen. Keine Extrapolation auf alle Modelle.
- all_observed_same ist nicht allgemein die Uhrgleichheit zwischen zwei Samples. Die konkrete 1.503er-Gruppe übersteht zusätzliche strengere Prüfungen.
- Fehlende Samples können eine tatsächlich mehrdeutige Pose-Verknüpfung verbergen; null ambiguous ist unter Verlusten kein Eindeutigkeitsbeweis.
- 609 Schlussaufrufe stehen in den Gesamtsummen, besitzen aber keine ausgegebene Frame-Zeile. Null gemeldete Frame-Drops erfasst diesen Fall nicht.
- Aufnahmephasen und Objektzeilen haben unterschiedliche Rand-/Aggregationssemantik.
- Natives Testprogramm nutzt eine Fake-Granny-DLL; es beweist nicht vollständige Verhaltensneutralität im echten Spiel.

Der Bericht liegt bislang separat. Trage geprüfte Korrekturen mit Quellenbezug in die Projekt-Wissensbasis ein, bevor du auf überholten allgemeinen Gleichheits-/Vollständigkeitsannahmen aufbaust. Keine pauschale Übernahme aller Agentenaussagen.

## 7. Zwei ausdrücklich verschiedene Spielsituationen

Aktueller Referenzfall: Singleplayer gegen KI, REAL_LAG_257 / LAG_217_Reiter, 217 berittene Bogenschützen + 20 Armbrustschützen + 20 Bogenschützen, bisher Speed 90.

Historischer Extremfall: Nutzerbericht über 1–2 FPS im Multiplayer gegen einen Menschen, große stark bebaute Karte mit vielen Ressourcen und mehreren hundert Truppen/vielen Rittern; genaue Anzahl unsicher, keine entsprechende Aufnahme vorhanden.

Der aktuelle Engpass erklärt diesen Multiplayerfall nicht automatisch. Netzwerk-/Synchronisationsanteile sind ebenfalls nicht getrennt. Keine Behauptung rekonstruierter Wegfindung, Kampflogik, KI oder deterministischen Multiplayerverhaltens aus Klassennamen.

F8-Marker erhalten ihre Bedeutung durch Ablauf und Nutzerkontext. Geplante, beobachtete und vom Nutzer bestätigte Geschwindigkeit/Pause getrennt halten. Weder große Schlachten durch Zufall abwarten noch den Nutzer Werkzeugfehler wiederholt manuell testen lassen.

## 8. Erster Auftrag als Projektleiter

Schließe zunächst einen begrenzten technischen Wissensbaustein ab. Kein neuer kompletter Analyse-Hub und kein Auftrag „verstehe die ganze Engine“.

Empfohlener Einstieg:
1. Auditkorrekturen nachprüfen und sauber integrieren.
2. Pose-Ausgabepuffer der vorhandenen Granny-Version untersuchen: Getter, Layout, gültige Größe, Besitzer, Lebenszeit und Änderungen durch den bekannten Aufrufpfad.
3. Einen kleinen ausführbaren Nachweis bzw. Testhost mit gültigen eigenen Daten erstellen. Vor dem Aufruf des Originals ABI und zulässigen Eingangsbereich belegen; historische Aufnahmezeiger nie dereferenzieren.
4. Entscheiden, ob der nächste Beweis besser durch einen kleinen Funktionsnachbau oder den vorgeschlagenen begrenzten Pose-Ergebnisvergleich entsteht. Genau einen dieser Folgepfade konkret bearbeiten; keine unverbundenen Großprojekte eröffnen.

Wenn ein kleiner Nachbau gewählt wird:
- Vorzugsweise ein bereits lokalisierter, ausreichend abgegrenzter Helfer mit relevanter Verbindung zum untersuchten Pfad.
- Spezifikation von Eingaben, Ausgaben, globalem Zustand, Speicherverhalten, Float-/Randfallsemantik und belegtem Eingangsbereich.
- Eigene nachvollziehbare Implementierung, getrennt vom Original; keine bloße Kopie von Ghidra-Pseudocode.
- Differentialtests Original gegen Nachbau mit gültigen normalen, Grenz- und reproduzierbar erzeugten Fällen. Vergleichskriterium vorab festlegen; bei Float-Abweichungen Ursachen und Grenzen erklären.
- Ergebnis nur für den geprüften Bereich formulieren. Gleichheit beobachteter Ausgaben allein beweist weder alle Seiteneffekte noch universelle Ersetzbarkeit.

Wenn Pose-Ergebnisvergleich gewählt wird:
- Höchstens 16 ausgewählte beobachtete Generationen; Uhr direkt Sample-zu-Sample vergleichen.
- Originalaufrufe weiterhin vollständig ausführen, keine Doppelberechnung und kein Überspringen.
- Nach dem Sample gültige Ausgabematrizen vergleichen; vorherige Auditgrenzen und Zustandsänderungen berücksichtigen.
- Lücken, Auswahl, Lesefehler, Lebenszeitunsicherheit und Schlussreste ausdrücklich ausweisen.
- Native Tests vor neuer Aufnahme. Das Protokoll im Audit ist ein Entwurf, noch kein installierbarer oder freigegebener Beobachter.

Ein begründetes Gegenbeispiel oder eine bewiesene Vertragsgrenze ist Erkenntnisgewinn. Eine unaufgelöste Stelle ist kein Anlass, ihren Zweck zu erfinden oder den Auftrag stillschweigend als erfolgreich abgeschlossen zu deklarieren.

## 9. Arbeitsorganisation und Abnahme

Du koordinierst die Arbeit und entscheidest, welche Unsicherheit als Nächstes geschlossen wird. Fokussierte Datenprüfung, Binäranalyse und Reproduktion können bei verfügbarem Tooling getrennt bearbeitet werden. Ein Verantwortlicher integriert; keine gleichzeitigen Produktionsänderungen oder Ghidra-Schreibzugriffe mehrerer Agenten.

Liefere für den ersten abgeschlossenen Wissensbaustein:
- Funktions-/Datenflussbeschreibung mit Modul-Hash und RVA, Beobachtung/Hypothese/offener Grenze.
- Reproduzierbares eigenes Werkzeug, Testprogramm oder kleiner Nachbau mit Befehlen und Ergebnissen.
- Nachweis, welche Aussagen aus Binäranalyse, Laufzeitdaten oder Testmodellen stammen.
- Genau einen priorisierten nächsten Versuch samt erwartbarem Erkenntniswert, Gültigkeitskriterien und möglichen Ergebnisentscheidungen.
- Aktualisierte FINDINGS/FUNCTIONS, soweit sachlich passend, STATE und kurzen aktuellen HANDOFF. Historie nicht unbemerkt umdeuten.

Prüfe verfügbare Werkzeuge über SETUP und tatsächliche Aufrufe. Ghidra 12.1.4, vorhandene Ghidra-Skripte und lokale Python-/Win32-Tests sind dokumentiert; REA-MCP ist nicht in jedem Chat verfügbar. Fehlende Werkzeuge benennen und verfügbare Alternativen nutzen.

Keine Originaldateien oder bestehenden Rohdaten ändern; keine Installation in TEST als beiläufigen Schritt. Jeder spätere Performance-Patch bleibt abschaltbar und wird erst nach Messnachweis beurteilt. Ein neuer Messbuild benötigt passende Kontrollen; kurze bestätigte Phasen und natürliche Erkundungssitzungen beantworten unterschiedliche Fragen.

Kein Push, keine Veröffentlichung von Spielassets, Binaries oder dekompiliertem Spielcode. Eigene Implementierungen, Berichte und Werkzeuge versionieren; Rohmaterial bleibt lokal. Nach Änderungen passende Tests und python -I tools/lint_docs.py ausführen. Persönliche absolute Pfade gehören nicht in die versionierte Doku.

Kommuniziere auf Deutsch: Ergebnis zuerst, dann Beleg und Grenze. Frage nur nach tatsächlich fehlendem Nutzerwissen. Fordere keine bereits lokal verfügbaren Dateien erneut an. Neue Spielaufnahmen erst, wenn die Messfrage konkret ist und die technische Vorbereitung geprüft wurde.

