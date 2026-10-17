# Entscheidungsgrundlage fuer einen begrenzten Posevergleich

> Kurzfassung: Die naechste Beweisfrage wird am gueltigen Beobachtungsfenster ausgerichtet. Vollstaendige Cache-/Klassenbindung ist keine universelle Vorbedingung; konkrete Lebensdauer, gueltige Ausgabe und Nebenlaeufigkeit bleiben nachzuweisen. Kein installierbarer Observer oder neuer Messlauf.

Stand: 2026-10-17. Engineering-Entscheidung der Projektleitung zum
[Initialisierungspaket](../tasks/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md), keine neuen Laufzeitbefunde.
Fruehere naechste Schritte in datierten Evidenzdateien bleiben historische Arbeitsentscheidungen.

## Was die bisherigen Belege tragen

- [Granny-Vertrag](../evidence/POSE_CONTRACT_2026-10-16.md): fuer den geprueften DLL-Build existieren
  World-Pose-Layout, geliehene Arrays, Allokationsgroessen und eigener Host mit gueltigen eigenen Daten.
  Allokation initialisiert die Matrixdaten nicht; der Header allein bestaetigt keine fremde lebende Allokation.
- [Erzeugung](../evidence/HPOSE_CREATION_2026-10-17.md) und
  [Cleanup](../evidence/HPOSE_CLEANUP_2026-10-17.md): ein Spielpfad uebergibt die H-Pose-Zeiger an die
  Konstruktor-/Free-Imports. Das ist keine vollstaendige Ereignishistorie aller dynamischen Objekte.
- [Arraytransfer](../evidence/HPOSE_ALLOCATION_2026-10-17.md): H-Recordadresse, gespeicherter Posezeiger
  und Posegeneration sind verschiedene Identitaeten. Arrayverlagerung erzeugt keine neue Pose.
- [Ressourcenbefund](../evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md): Konstruktor-/Tabellenkandidat und
  bedingter Ressourcenabbau sind bekannt; dynamisches Ziel und Cache-Hit-Herkunft bleiben teilweise offen.

## Fuer einen spaeteren Vergleich noch erforderlicher Vertrag

1. Konkrete Allokationsgeneration und gueltige Kapazitaet der ausgewaehlten Pose. Eine identische Adresse,
   gleicher Header oder nichtnull O+0x4C reicht nicht. Vor Beginn bereits existierende unzugeordnete Posen
   waeren unbekannt, bis eine geeignete Herkunft anderweitig nachgewiesen ist.
2. Initialisierter Ausgabeumfang nach genau dem betrachteten Sample. Angeforderte Knochenzahl,
   Allokationskapazitaet, World-/Composite-Arrays und tatsaechlich geschriebene Matrizen sind getrennt.
3. Gueltiges Leseintervall: keine unbehandelte Freigabe, Wiederverwendung oder konkurrierende/verschachtelte
   Aenderung zwischen Originalberechnung und Abschluss einer eigenen Kopie. Eine Vorher-/Nachherpruefung
   eines Zeigerwerts ist kein Nachweis gegen eine Freigabe waehrend des Lesens.
4. Zuordenbare Originalereignisse und explizite Unsicherheit bei Verlust, unbekanntem Eintritt oder
   unvollstaendigem Lebenszyklus. Der bekannte unzureichende Beobachter wird nicht wieder eingesetzt.
5. Vor Implementierung: begrenzte Auswahl, Speicherbudget, Verlust-/Abbruchregeln, Weiterleitungsneutralitaet
   und native Tests. Ein kuenftiger Messlauf waere ein eigener ausdruecklicher Arbeitsschritt.

## Was nicht pauschal vorab zu rekonstruieren ist

Vollstaendige Source-Klassen, saemtliche Cachetypen und die gesamte Ressourcen-Reentrancy muessen nicht
universell bekannt sein, wenn ein enger Nachweis die konkret beobachteten Pose-Allokationen und das Leseintervall
unabhaengig absichert. Ob dies fuer unseren Pfad gelingt, ist noch offen. Das ist eine alternative Beweisroute,
keine bestehende Freigabe fuer Livezugriffe. Ressourcenfragen bleiben dann wichtig, soweit sie dieses Intervall
oder dessen zugelassene Daten beeinflussen.

Ein allgemeiner Cachespeicherdump beantwortet Lebensdauer-/Reihenfolgefragen nicht automatisch. Eine kuenftige
gezielte Beobachtung muesste eine konkrete Entscheidung ermoeglichen; zunaechst wird nur deren Vertrag beurteilt.

## Entscheidung nach dem Initialisierungspaket

Das [abgeschlossene Inventar](../evidence/HPOSE_INITIALIZER_EFFECTS_2026-10-17.md), F163–F166, beschreibt optionale
Lightmap-/Normalmap-/Lights-Occlusion-Verweise und ihre direkten Speicherziele. In den untersuchten Helferkoerpern
wurden keine direkten Zugriffe auf R+0/+4/+0xC/+0x10 identifiziert; globale Lookup-Effekte bleiben offen.
Eine scheinbare Innenzeiger-Weitergabe wird durch den unbenutzten eingehenden Allocator-Kontext lokal geschlossen.

Kein automatischer Folgeauftrag fuer jede neu gefundene virtuelle Funktion. Die naechste statische Prioritaet
ist der gueltige und initialisierte World-/Composite-Ausgabeumfang am bekannten Samplepfad. Erst danach wird die kleinste
verbleibende Lebensdauer-/Beobachtungsfrage bestimmt. Dieses Dokument startet keine zusaetzliche Analyse,
Observerimplementierung, Spielaufnahme oder Originalausfuehrung im laufenden Initialisierungspaket.

## Fortschritt: bedingter Ausgabeumfang

Der [statische Sample-Baustein](../evidence/POSE_SAMPLE_EXTENT_2026-10-17.md) trennt jetzt vollstaendige
64-Byte-Stores pro World-/Composite-Matrix von deren Quellgueltigkeit und der Auswahl des tatsaechlichen
Writerpfads. Die zwei direkten Writer haben unterschiedliche Kapazitaetspruefungen. Der bekannte Spielaufruf
verwendet einen Startindex von null; eine allgemeine Worker-Indexsemantik wird daraus nicht abgeleitet.
Eine Kontroll-/Callbackkante und die Herkunft gueltiger Local-Pose-Werte verhindern weiterhin einen pauschalen
initialisierten Bereich allein aus dem Sample-Return. Dieser Fortschritt erfuellt Punkt 2 oben nur bedingt;
Generationen, Leseintervall und Ereignisvollstaendigkeit sind damit nicht geschlossen.

Genau naechster Beweis: die Spezialkante DLL `0x2C44 -> 0x2460` an einen belegten Descriptor und ein konkretes
Callbackziel binden, danach dessen Ausgabeumfang. Der Scope beginnt beim ersten Praedikat-true-Knoten,
wenn der naechste Knoten fehlt oder das Praedikat false liefert. Ein sauber lokalisierter unbekannter Producer
ist ein zulaessiger Abschluss. Keine automatische Ausweitung auf alle Controls oder LocalPose-Mathematik.
