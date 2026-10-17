# Ressourceninitialisierung: Auswirkungen und naechster Pose-Nachweis

> Kurzfassung: Untersuche zuerst 0x395E4F -> 0x394350, danach begrenzte Inventare von 0x3949A0 und 0x394000. Funktionale Aufgabe, relevante Felder und R-Weitergaben belegen; danach den kleinsten fehlenden Nachweis fuer einen gueltigen Posevergleich bestimmen.

Basis: `12b8050`, [vorheriger Ressourcenbefund](../evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md), F160–F162.
Dies setzt den vom Nutzer bestaetigten Auftrag um; keine Wiederaufnahme historischer Spielaufnahme-Auftraege.
Ergebnis und Grenzen: [Initialisierungsbefunde](../evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md).
Die Projektentscheidung fuer die folgende Beweisroute steht in
[Posevergleich: Voraussetzungen](../design/POSE_COMPARISON_READINESS_2026-10-17.md).

## Ziel

R=*(H+0xC) hat einen belegten Konstruktor-/Tabellenkandidaten. Vor der Produzentenrueckgabe uebergibt
Initializer 0x395CC0 R an drei Helfer: 0x395E4F -> 0x394350, 0x395E63 -> 0x3949A0, 0x395E7E -> 0x394000.
Klaere fuer diese begrenzten Pfade die erkennbare funktionale Aufgabe und relevante Auswirkungen auf R.
Ein vollstaendiges Verstaendnis aller Cachetypen ist keine pauschale Voraussetzung fuer jeden Posevergleich.

## Rollen und Arbeitsauftrag

Analyseagent: Verfolge eingehendes R, Objektbasis/Aliase, relevante Reads/Stores, Referenzaustausch/Freigabe,
Tabellenzeiger, Rueckgabebedingungen und Weitergaben von R beziehungsweise Teilzeigern. Beginne bei 0x394350;
die beiden anderen Helfer erhalten vergleichbare begrenzte Inventare. Benenne eine funktionale Teilaufgabe
nur soweit durch Datenfluss belegt; vermutete Typnamen oder Zwecke bleiben Hypothesen.

Kein automatischer rekursiver Abstieg. Fuer ein zentrales kleines Bindeglied muss der Nutzen fuer diese
Identitaets-/Lebensdauerfrage konkret sein; sonst dessen Call/RVA, Objekt-/Teilzeigerargument und Grenze nennen.
Kein direkter R+0-Store ist allein kein Beweis, dass alle fremden Aufrufe den Zustand unveraendert lassen.

Pruefagent: Eigener PE-Byte-/Argument-/Aliascheck, gezielte Gegenbeispiele, unabhaengige Pruefung der behaupteten
Funktionsaufgabe. Keine DB-Nutzung; Exporte und Originaldateien nur lesen. Relevante Werkzeugdefekte mit
ausfuehrbarer Gegenprobe melden, keine allgemeinen Refactor-Wunschlisten.

Projektleitung: Integriert gepruefte Befunde und Tests, aktualisiert STATE/Uebergabe und entscheidet nach diesem
Paket ueber den naechsten Beweisweg. Keine automatische Fortsetzung entlang jedes offenen Ressourcenaufrufs.

## Abnahme

- Buildidentitaet und reproduzierbare Funktion/RVA-/Argument-/Storebelege, gemeinsame finale Exporte.
- Direkte Befunde, bedingte Aussagen, Aliasunsicherheit und offene Callauswirkungen getrennt.
- Relevante Werkzeugtests normal/-O und unabhaengiger Review; bestehende Pruefwerkzeuge gezielt wiederverwenden.
- Regulaere spielfreie Checks und Dokumentationslint; native Checks nur bei betroffener eigener C++-Logik.
- Abschlussentscheidung: Tabellenfortbestand im belegten Bereich bestaetigt, konkrete Aenderung oder konkrete
  Restluecke. Kein unbewiesener universeller Zieltyp oder Ausschluss von Reentrancy.
- Separat beurteilen: Nachweise fuer lebende Pose-Puffer/Generationen, initialisierten Ausgabeumfang und
  kontrolliertes Sample-Beobachtungsfenster. Ein Cache-Komplettbeweis ersetzt diese Fragen nicht.

## Grenzen

Ein Agent allein nutzt die getrennte Ghidra-Kopie, ausschliesslich readOnly/noanalysis. Originalinstallation,
Rohdaten, kanonischer Audit und originale DB unveraendert. Kein Game-/DLL-Aufruf, Cache-Dump, neuer Observer,
Spielaufnahme, Installation, Performancepatch, Cache-/Skiplogik oder Freigabe historischer Zeiger.
Rohlistings bleiben lokal ignoriert; keine Binaries, Assets, dekompilierter Spielcode oder privaten Pfade in Git.
Lokaler Commit nach bestandener Abnahme; kein Push/PR in diesem Auftrag.
