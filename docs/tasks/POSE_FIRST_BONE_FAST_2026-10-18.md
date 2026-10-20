# Erste-Matrix-Schnellweg: Quellen, Ziel und Restloop

> Kurzfassung: Pruefe den bereits gebundenen Codeentry DLL 0x44F40 am Aufruf 0x1C8DB: drei Quellzweige, volle erste World-/Composite-Matrix und Zusammenspiel mit dem bei i=1 fortgesetzten Loop. Bestehende Kernelbelege wiederverwenden, keine gesamte Kurven- oder Trackrekonstruktion.

Basis `eb6b564`; [Spezialcallback](../evidence/POSE_SPECIAL_CALLBACK_2026-10-17.md), F171–F174,
und [Wissenskarte](../ANIMATION_KNOWLEDGE_MAP.md). DLL-Basis `0x50000000`, SHA-256
`94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`.
Adressen ohne Modulzusatz sind DLL-RVAs.

## Konkreter Vertrag

Unter den bisherigen Spezialzweigbedingungen, tatsaechlichem Callbackentry `0x1C780`, exaktem Modus
`*(n+0x20)==2` und lesbarem nichtnull Feld Track0+4 wird vor dem allgemeinen Countguard `0x44F40` aufgerufen.
Der Getter `0x44F30` liefert diesen Codeentry konstant. Welche gueltigen Quellen waehlen seine drei Zweige,
welche Bytes werden an World/Composite geschrieben, und was folgt fuer den gesamten selektierten Pfad?

- Callerargumente, Parentwahl, InverseBind und erste Ausgabeziele nachvollziehbar binden.
- Pro Quellzweig die Herkunft der Transformwerte oder die konkrete unbewiesene Produktionskante nennen.
- Slots `0x61A78`/`0x61A84` und bereits gepruefte vollstaendige 64-Byte-Kerne wiederverwenden; volle Stores
  getrennt von gueltigen Quellwerten, Ausrichtung, Kapazitaet und Hierarchie behandeln.
- Den ersten Schreibindex und danach i=1, C=min(B,BindingCount), Loopgrenze und Null-/Teilbereiche zusammensetzen.
- C=0 nicht allein wegen einer lokalen Sprungfolge als gueltiges End-to-End-Schreibgegenbeispiel deklarieren.
  Zugehoerige vorgelagerte Praedikate und lesbare Bone0-/Track0-Daten gehoeren zur gueltigen Domain.

## Nachweis und Grenzen

Ein Autor arbeitet exklusiv auf der getrennten Ghidra-Kopie, readOnly/noanalysis. Ein unabhaengiger Reviewer
prueft Originalbytes und Quell-/Zielbindungen ohne DB. Nur eigene Dokumentation und Werkzeuge in Git;
rohe Listings bleiben lokal ignoriert. Keine neuen Funktionen in der Datenbank anlegen.

Bestehenden Sample-Verifier nutzen; die 54 Eintraege/67 Bereiche enthalten den Schnellweg bereits.
Neue Fingerprints, Schemaaenderungen oder Tests nur bei tatsaechlich neuem Pruefbedarf, kein Verifierklon.
Semantische Praezisierung ohne neue Codebereiche ist ein vollwertiger Erkenntnisgewinn.
Finale Exporte, Identitaeten und vollstaendige Argumente dokumentieren. Relevante negative Gates normal/-O,
dateilesenden Verifier sowie regulaere spielfreie Checks ausfuehren; keine unveraenderten nativen Hosts neu bauen.

Abschluss: enger bedingter erster-Matrix-Vertrag und dessen Verbindung zum Restloop oder exakt benannte
Quell-/Writerluecke. STATE, Uebergabe und Wissenskarte nachziehen. Lokaler Commit nach Abnahme, kein Push/PR.
Originalinstallation, Rohaufnahmen, Auditreferenz und originale Ghidra-DB bleiben unveraendert. Keine Original-
ausfuehrung, neue Aufnahme, Observerimplementierung, historischen Pointerzugriffe, Cache-/Skiplogik oder
automatische Verfolgung aller indirekten Track-/Kurventypen.
