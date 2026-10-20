# H-record cleanup: Free-Felder, Traversal und Auswahlgrenze

> Kurzfassung: Statischer Teilnachweis: Cleanup uebergibt die drei Granny-Zeiger pro besuchtem H an ihre Free-Imports und setzt die Auswahl am normalen Funktionsende null. Ein direkter Abbaupfad gibt danach den H-Puffer frei. Keine allgemeine Besitz-, Generationen- oder Threadgarantie.

Datum: 2026-10-17. Basis `3932634`; [Auftrag](../tasks/HPOSE_CLEANUP_2026-10-17.md).
Vorgaenger: [Erzeugung/Auswahl](HPOSE_CREATION_2026-10-17.md), [Allokation/Transfer](HPOSE_ALLOCATION_2026-10-17.md).
Alle Codeadressen unten sind Exe-RVAs; Exportargumente im Reproduktionsabschnitt sind VAs.

## Identitaet und Evidenz

Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`,
Basis `0x00400000`; Granny SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`.
O bezeichnet denselben eingehenden Objektkontext des Cleanup, B=*(O+0x18), E=*(O+0x1C).
H bezeichnet einen 20-Byte-Record, R=*(H+0xC) eine getrennte Ressource.

Primaerbeleg: gemeinsame Ghidra-Exporte unter ignoriertem `build/hpose-cleanup/final-export-v2/`,
mit sechs Funktionsdateien (403 Instruktionen) und `xrefs.tsv`. Export nur auf getrennter Projektkopie,
`-readOnly -noanalysis`, kein Decompiler. `tools/hpose_cleanup_manifest.json` haelt sechs Bereichs-/SHA-Fingerprints;
`tools/hpose_cleanup_verify.py` prueft deren Bytes und sechs PE-Importidentitaeten mit dem vorhandenen PE-Pruefer.
Das bindet die Interpretation an Byteorte, ist kein formaler Semantikbeweis oder Laufzeitnachweis.

## Cleanup RVA 0x38E3C0

Zuerst ruft `0x38E3CC` den Helfer `0x38D8C0` mit O und Argument null auf. Dessen Nullzweig laeuft ueber die
Liste aus O+0xC: innere Knoten liefern Kontrollzeiger bei Knoten+8 an `GrannyFreeControl`
(IAT `0x500AD0`, Call `0x38D9A4`); anschliessend werden innere/aeussere Listenknoten mit nominalem CRT-delete
abgebaut und O+0x10 nullgesetzt. Das ist eine Kontrollbereinigung vor dem H-Abbau, kein Beweis vollstaendiger
Granny-interner Kontroll-/Besitzsemantik. Sein Nichtnullargument-Zweig gehoert nicht zum hier eintretenden Pfad.

Ab `0x38E3D1` wird (E-B)/20 mit signed Division gegen null berechnet. Bei Ergebnis null wird die
H-Free-Schleife uebersprungen (`0x38E3EB` nach `0x38E451`). Fuer einen geordneten, durch 20 teilbaren und
signed-repraesentierbaren Bereich besucht die Schleife H=B+20*i, beginnend i=0. Sie liest B zu Beginn jeder
Iteration neu (`0x38E3F0`), verwendet einen um 20 steigenden Offset (`0x38E445`) und berechnet die Anzahl nach
jeder Iteration aus erneut geladenem B/E (`0x38E42A` bis `0x38E443`). Der Ruecksprung `0x38E44D` ist unsigned
index<Anzahl. Nur bei unveraendertem gueltigem Bereich ergibt das jeden urspruenglichen Record genau einmal.
Es gibt keine lokale Pruefung von Teilbarkeit, Bereichsordnung oder signed Differenz; keine Behauptung fuer korrupte Bereiche.

Pro besuchtem H gilt die folgende direkte Argumentkette, ohne lokale Nullpruefung der drei Zeiger:

- `0x38E3F3`/`0x38E3F8`/`0x38E3F9`: H+0 an `GrannyFreeModelInstance`, IAT `0x500AA0`.
- `0x38E3FF`/`0x38E402`/`0x38E403`: H+4 an `GrannyFreeWorldPose`, IAT `0x500AA4`.
- `0x38E409`/`0x38E40C`/`0x38E40D`: H+8 an `GrannyFreeLocalPose`, IAT `0x500AA8`.

Die PE benennt die drei Imports als `_GrannyFreeModelInstance@4`, `_GrannyFreeWorldPose@4`,
`_GrannyFreeLocalPose@4` aus `granny2.dll`. Die Felder stimmen mit den drei Erzeugungsstores aus F154 ueberein.
Das ist die bislang fehlende Free-zu-H-Verbindung, keine Annahme aus Importreferenzen allein.

Danach wird R aus H+0xC geladen (`0x38E418`), ein ueber IAT `0x500984` geladener globaler Zaehler dekrementiert
(`0x38E41B`; PE-Import `dragonfly.dll`, `?numberOfObjects@ReferenceCount@Dragonfly@@0IA`) und R+4 dekrementiert (`0x38E41D`). Nur bei Ergebnis null folgt `0x38E428`: indirekter Call
ueber den ersten Zeiger der Tabelle an *R, mit Kontext R und Argument 1. Ziel und Seiteneffekte dieses Calls
sind offen. Kein Ursprungstyp oder eindeutiger Besitzer wird aus diesem Zaehler abgeleitet.

Nach Schleifenende vergleicht `0x38E457` B/E. Im nichtleeren Fall setzt `0x38E45B` einen Cursor auf E;
der folgende Vergleich E mit sich selbst springt bei `0x38E45F` direkt zum End-Store `0x38E487`.
Der dazwischenliegende fuenf-Feld-Copyloop ist damit auf diesem direkten Pfad unerreichbar.
Normal wird E=B gesetzt; B und O+0x20 werden hier nicht geaendert, der H-Puffer wird hier nicht geloescht.
Die drei H-Zeigerfelder werden lokal nicht nullgesetzt. Kein Live-Posebeweis fuer die weiterhin vorhandenen alten Bytes.

Bei O+8!=0 folgt ein aehnlicher Zaehlerabbau, offener Tabellen-Slot-0-Call an `0x38E4A3` bei Zaehler null,
anschliessend O+8=null (`0x38E4A5`). Call `0x38E4AA` erreicht `0x38D070`: Liste aus O+0x28, pro Knoten
Referent aus Knoten+0x4C, Zaehlerabbau und bei null offener Slot-0-Call `0x38D095` mit Argument 1;
Listenlinks/-zaehler werden zurueckgesetzt und Knoten geloescht. Knoten+0x4C ist hier ein anderes Objektfeld
als die ausgewaehlte H-Adresse in O+0x4C.

Erst nach normaler Rueckkehr dieser Helfer schreibt `0x38E4B1` O+0x4C=null, danach O+0x34=null
(`0x38E4B7`) und Byte O+0x48=1 (`0x38E4BA`). Der alte ausgewaehlte H-Zeiger wird somit nicht vor den
Free-Aufrufen invalidiert. Alle Aussagen ueber den Endzustand setzen normale Rueckkehr voraus;
Throw-/Unwind-Pfade, Callbacks, Reentrancy oder parallele Zugriffe sind nicht geschlossen.
Das zeitweise stehenbleibende Feld allein beweist keinen tatsaechlichen Zugriff nach Freigabe und keinen UAF.

## Direkter Abbaupfad und Auswahl

Ghidras gemeinsame Referenzinventur findet genau einen direkten Call auf `0x38E3C0`:
`0x38EC68` in `0x38EC30`, mit demselben O-Kontext. Nach normaler Rueckkehr folgt fuer B!=0
nominaler unsized CRT-delete an `0x38ECC9` ueber `0x40FB8C`, IAT `0x500224`
(`msvcr100.dll`, `??3@YAXPAX@Z`). Danach werden O+0x18/+0x1C/+0x20 bei `0x38ECD1`/`0x38ECD4`/`0x38ECD7`
nullgesetzt. Damit sind Granny-Objektfreigabe, logische Leerung, Auswahl-Reset und spaetere Arrayfreigabe
auf diesem Pfad getrennt und geordnet belegt. Andere Felder/Listen im Caller werden hier nicht als vollstaendige
Objektdestruktorsemantik rekonstruiert.

Ein begrenztes Bindeglied `0x38EEF0` ruft `0x38EC30` bei `0x38EEF6` mit demselben O auf und loescht O selbst
an `0x38EF02`, wenn das niederwertige Flagbit des Arguments gesetzt ist. Einzige Ghidra-Referenz auf diesen
Einstieg ist die Datenreferenz bei `0x5F45C8`. Dies passt zu einem virtuellen Loeschwrapper; aufloesbare
indirekte Aufrufer, vollstaendige dynamische Aufrufmenge und Source-Klassenname sind nicht bewiesen.

F155 verbindet O+0x4C mit H-Auswahl im bekannten Samplepfad. Hier ist dessen normaler Cleanup-Endzustand
belegt; es gibt keine Garantie, dass alle dynamischen Auswahlen aus genau dem bekannten Erzeugungspfad stammen,
oder dass keine andere Stelle ausgewaehlte/ausgeliehene H-/Posezeiger behaelt. Arrayverlagerung bleibt eine getrennte
H-Adressaenderung; identische Zeigerwerte beweisen keine gleiche Generation.

## Reproduktion und Pruefungen

```text
python -I tools/hpose_cleanup_verify.py --exe <original-exe> --dll <original-dll>
python -O -I tools/hpose_cleanup_verify.py --exe <original-exe> --dll <original-dll>
python -I tools/test_hpose_cleanup.py
python -O -I tools/test_hpose_cleanup.py
```

Finale integrierte lokale Gesamtabnahme auch nach dem sechsten Import-Pinning: 13/13 regulaere Pruefgruppen bestanden.
Beide Originaldatei-Verifier auch nach dem sechsten Import erfolgreich; acht synthetische Tests jeweils normal und mit -O bestanden.
Die Tests pruefen Erfolg, unbekannte Identitaeten/Versionen, fehlende/doppelte Funktionen, geaenderte Bytes,
ungueltige/ueberlappende Bereiche, kurze/ungueltige Leserueckgaben und CLI-Ablehnung unbekannter Builds.
Keine assert-basierte Schutzbedingung. Die Tests pruefen den Fingerprintvertrag, kein nachgebautes Spiel-Cleanup.

Ein frischer unabhaengiger Reviewer wiederholte beide Originaldatei-CLI-Laeufe und beide achtteiligen Testsuiten,
verglich alle 403 exportierten Instruktionsbytes mit einem unabhaengigen PE-Parser und pruefte die begrenzte
Datenfluss-/Kontrollflussdeutung. Keine relevante Abweichung gefunden. Parent bestaetigte separat beide Hashes,
403 Instruktionen des finalen Exports und die drei Free-IATs; der finale Originaldatei-Verifier mit allen sechs
Importen besteht normal und mit -O. Dies ersetzt keinen dynamischen Lebensdauernachweis.

Eigener nativer Quellcode unveraendert: kein weiterer C++-Build/CTest oder Real-DLL-Host fuer diesen Schritt.
Kein Audit-Recount, Hub-E2E-Lauf oder Spieltest erforderlich bzw. ausgefuehrt; kein Observer-/Hub-Code geaendert.
Fuer diesen Forschungsstand gibt es noch keinen neuen GitHub-CI-Lauf.

Finaler Ghidra-Aufruf: vorhandenes `hpose_creation.java`, Ausgabe `build/hpose-cleanup/final-export-v2`, Ziele
`0078E3C0 0078EC30 0078EEF0 0078D8C0 0078D070 0080FB8C 00900AA0 00900AA4 00900AA8 00900AD0 00900224 00900984`,
getrennte Kopie, `-readOnly -noanalysis`, Scriptpfad `ghidra_scripts`. Alle tatsaechlich verwendeten sechs
Funktionen und sechs IAT-Ziele sind in diesem gemeinsamen Export enthalten. Rohlistings bleiben lokal ignoriert.

## Verbleibende Grenze und genau ein naechster Schritt

Dieser Cleanup-Beleg reicht noch nicht als Freigabe fuer Posevergleiche ueber mehrere Spielaufrufe:
fehlend sind durchgaengige Generationenidentitaet einschliesslich Wiederverwendung, Lebensdauer aller ausgeliehenen
Zeiger, kompletter initialisierter Sample-Ausgabeumfang und Ausschluss konkurrierender/rekursiver Veraenderung.
Kein Game-/DLL-Aufruf, keine neue Aufnahme, Installation, Hookaenderung, native Lifetime-Implementierung oder Optimierung.

Genau ein minimaler naechster statischer Schritt: das Ziel des indirekten Calls `0x38E428` bestimmen,
indem ausschliesslich die bekannte Herkunft von R=*(H+0xC) bis zu dessen Tabellen-Slot 0 verfolgt wird.
Bedingung ist das gerade auf null dekrementierte R+4, Kontext R, Argument 1; der Call liegt nach den drei Granny-Frees
und vor dem Auswahl-Reset. Ziel ist die konkrete Ressourcenfreigabe-/Reentrancy-Grenze dieses einen Calls,
keine allgemeine Ausweitung auf alle Caller oder Heapinternas.
