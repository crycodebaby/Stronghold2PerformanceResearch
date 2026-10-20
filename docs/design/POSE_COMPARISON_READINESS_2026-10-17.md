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

## Fortschritt Spezialcallback und aktuelle Prioritaet

Der [Spezialcallback-Baustein](../evidence/POSE_SPECIAL_CALLBACK_2026-10-17.md), F171–F174, liefert einen
konstruktorbezogenen Descriptor-/Zielkandidaten und einen bedingten vollen World-/Composite-Praefix `[0,C)`
mit `C=min(B,BindingCount)`. Voraussetzung sind Schnellweg-Bypass und bekannte direkte Helfer in allen
Schleifendurchlaeufen. Es gibt keinen universellen Callbackspan; eine vorgelagerte erste-Matrix-Schnellroute
und indirekte Tracksampler bleiben offen. Tablewerte alleine ersetzen weiterhin keine konkrete Zielbindung.

Aktuelle Folgeprioritaet ist die kleine bekannte Schnellroute `0x1C8DB -> 0x44F40`, ihre drei Quellzweige,
ersten Matrixziele und Countinteraktion mit dem Restloop. Die vorherigen Folgeauftraege oben beschreiben ihre
jeweiligen Zwischenstaende. Keine automatische Komplettrekonstruktion aller Controls/Tracks. Die Fragen nach
gueltigen Quellen, beobachteten Generationen und Leseintervall werden dadurch nicht aufgehoben.

## Fortschritt Schnellroute: Byteabdeckung ist nicht Wertegueltigkeit

[F175–F177](../evidence/POSE_FIRST_BONE_FAST_2026-10-18.md) belegen fuer alle drei Fastzweige volle 64 Zielbytes
je World0/Composite0, bei bekannten Writerzielen und normal beendeter Ausfuehrung mit zulaessigen Speicherbereichen.
Route B hat den engen Parent-/InverseBind-Wertevertrag. Fuer A/C ist die Initialisierung gelesener lokaler
Transformkomponenten nicht geschlossen; daraus folgt weder ein Enginefehler noch eine ungeschriebene Zielmatrix.

Diese Unterscheidung praezisiert Punkt 2 des Vergleichsvertrags: Ein reiner Vergleich real erzeugter **Bytes**
braucht einen nachgewiesenen Schreibumfang, aber keinen vollstaendigen mathematischen Nachbau des Producers.
Semantisch gueltige Transformwerte und Ersetzbarkeit sind zusaetzliche Aussagen. Ein Vergleich nur der ersten
Matrix liefert zudem keine Gleichheitsaussage ueber die gesamte Pose oder den versteckten Zustand.

Aktuelle naechste Prioritaet ist deshalb ein begrenzter Gueltigkeitsvertrag fuer die erste World-/Composite-
Matrixbeobachtung: welche konkrete lebende Generation/Kapazitaet ist zuordenbar, welches Leseintervall sicher,
welche fehlenden Ereignisse/Reentrancy-/Threadfragen verhindern einen Zugriff? Nichtnull Zeiger und einfache
Vorher-/Nachherchecks genuegen weiter nicht. Noch keine Observer-/Hookimplementierung oder Aufnahme.
Die offenen A/C-Producer und Track+8 bleiben dokumentiert; keine automatische Rekonstruktion aller Formate.

## Fortschritt Generation und aktuelle verbleibende Grenze

[F178/F179](../evidence/POSE_GENERATION_READ_WINDOW_2026-10-18.md) binden New/Free an gemeinsame Worker und
konfigurierbare Allocatorslots. Konkrete interne Calls umgehen die Exportwrapper; globale Export-only-Coverage
ist damit widerlegt, nicht aber automatisch eine Luecke fuer jede ausgewaehlte Exe-H-Pose bewiesen.
Ein eigenes begrenztes synthetisches Modell prueft Generationen, gemeldete Luecken/ABA und Widersprueche.
Es erlaubt keine Live-Lesung und beweist keine echte Ereignisvollstaendigkeit. Quarantaene bewahrt mehrdeutige
Birthbereiche bis zum Epochwechsel; ein einzelnes Free macht sie nicht wieder vertrauenswuerdig.

Naechster begrenzter Beweis: Veraenderungs-/Weiterleitungspfade der Slots 0x64B48/0x64B4C fuer ausgewaehlte
NewWorldPose-Provenienz. Danach ist das Writer-/Lesefenster weiterhin separat zu schliessen: aktive Calls,
Metadatenlocks und abschliessende Generationstests allein schuetzen Originalspeicher nicht vor Free/Reuse
waehrend der Kopie. Keine Observerimplementierung, Aufnahme oder automatische Ausweitung auf den gesamten Heap.

## Fortschritt Allocator und selektive Folgefrage

[F180–F182](../evidence/POSE_ALLOCATOR_BINDING_2026-10-18.md) klaeren Dateidefaults, getrennte Setterstores/
Getterreads und Default-Heapweiterleitung. Ein API-Getter ist wegen moeglicher Ausgabealiase nicht generell
nebenwirkungsfrei; gleiche Vorher-/Nachherwerte schliessen Zwischenwechsel nicht aus. Ein Wechsel selbst
ist kein bewiesenes Free und beweist keine Inkompatibilitaet der Callbacks. Die eigene Beobachterzuordnung
benoetigt deshalb einen separaten Konfigurations-/Nichtaliasvertrag statt einer angenommenen festen Bindung.

Der bekannte WorldPose-Free-Eintritt bleibt vor Weiterleitung eine konservative Invalidierungsgrenze.
Naechster Beweis: Poseherkunft im internen New-/Free-Bypass 0xE080, Calls 0xE165/0xE54D. Das prueft die
selektive Relevanz fuer H-Posen, bevor die Fragestellung auf den ganzen Heap ausgeweitet wuerde.
Ein geschuetztes Kopierintervall und lueckenlose relevante Ereignisse sind weiterhin nicht nachgewiesen.

## Fortschritt interner Bypass und Contextgrenze

[F183–F185](../evidence/POSE_INTERNAL_PROVENANCE_2026-10-18.md) belegen die bedingte lokale Zuordnung zweier
New-Returns zu den Free-Argumenten im Kontext 0xE080. Unter unveraendertem Frame/Calling-Convention-Vertrag
ist dies ein eigener New-/Free-Pfad, keine direkte lokale Auswahl einer eingehenden H-Pose.
Erfolg, verschiedene lebende Allokationen und allgemeine Frame-/Referentenaliasfreiheit sind damit nicht bewiesen.

Bekannte Contextweitergabe 0x44DAB -> 0x2F5D0 hat in diesem Build keine eigenen Datenstores. Indirekt erhaelt
Track+8 an 0xE30C aber arg1=F-0x80 mit noch offenem Schreib-/Weitergabevertrag. Genau dieser Contextumfang
fuer einen konkreten Kandidaten ist der naechste begrenzte Beweis; keine komplette Trackmathematik.
Das sicher geschuetzte Lesen ausgewaehlter H-Posen bleibt eine separate Voraussetzung.
