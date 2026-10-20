# Pose-Allocator: vorbelegte Bindung, Wechsel und Weiterleitung

> Kurzfassung: Die WorldPose-Allocatorslots haben belegte Defaultziele und lassen sich durch zwei getrennte Stores austauschen. Der Getter ist weder ein atomarer Paarsnapshot noch bei beliebigen Ausgabealiasen nebenwirkungsfrei. Der bekannte Free-Worker waehlt den zum Callzeitpunkt gelesenen Slot, nicht einen zur Geburt gespeicherten Callback. Damit sind konkrete Beobachtungspflichten klarer; vollstaendige selektive Ereignisabdeckung und sicheres Kopieren bleiben offen.

Datum 2026-10-18, Basis `e119eae`, F180–F182. [Vorab festgelegter Plan und Abnahme](../tasks/POSE_ALLOCATOR_BINDING_2026-10-18.md).
Vorgaenger: [Generation und Lesegrenze](POSE_GENERATION_READ_WINDOW_2026-10-18.md), F178/F179.
Nur Dateilesen und getrennte Ghidra-Kopie readOnly/noanalysis. Keine Originalausfuehrung, Hooks oder Aufnahme.

## Identitaet

Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, Basis `0x00400000`.
DLL SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`, Basis `0x50000000`.
Alle nachfolgenden Adressen sind DLL-RVAs, ausser ausdruecklich anders bezeichnet.

## 1. Initiale Dateiwerte und API

Das Slotpaar `0x64B48/0x64B4C` enthaelt in der Datei die VAs `0x50031150/0x50031220`.
Das sind Defaultkandidaten, keine Messung der aktuellen Laufzeitbindung.
Exports `_GrannyGetAllocator@8` bei `0x52870` und `_GrannySetAllocator@8` bei `0x52890` fuehren an
`0x5287A/0x5289A` mit unveraenderten zwei Argumenten zu Workern `0x318E0/0x31900`.

Die gepruefte Exe importiert NewWorldPose/FreeWorldPose, aber keinen benannten GetAllocator-/SetAllocator-Export.
Das schliesst dynamische Aufloesung, weitere Module, direkte interne Aufrufe oder Pointeraliase nicht aus.
Exportnamen und Defaultwerte ersetzen keine Herkunfts-/Lebensdauerbeobachtung ausgewaehlter Posen.

## 2. Was Aendern und Lesen genau leisten

- Setter `0x31900`: Argument 1 wird bei `0x31908` nach Slot `0x64B48`, Argument 2 bei `0x3190D` nach
  `0x64B4C` geschrieben. Der kleine Worker hat keine weiteren Calls, Validierung oder eigene Sperre.
  Diese zwei Stores sind keine gemeinsame atomare Paaroperation. Externe Synchronisation ist nicht untersucht.
- Getter `0x318E0`: Slot `0x64B48` wird bei `0x318E4` gelesen und bei `0x318EE` nach Ausgabeadresse 1
  geschrieben; danach Slot `0x64B4C` bei `0x318F0` gelesen und bei `0x318F5` nach Ausgabeadresse 2 geschrieben.
  Das ist kein atomarer Snapshot. Ausgabeadressen muessen zudem einen passenden Nichtaliasvertrag erfuellen.
- Konkrete Aliasgrenze: Zeigt Ausgabeadresse 1 hypothetisch auf Slot `0x64B4C`, kann der erste Getterstore
  dessen Wert vor dem zweiten Getterread veraendern. Das ist ein statischer Datenflussgegenfall, kein belegter
  Spielcaller und keine Behauptung ueber gueltige API-Nutzung im Originalspiel.
- Der Setter fuehrt selbst kein Free aus. Ein Bindungswechsel beendet deshalb nicht nachgewiesenermassen eine
  reale Allokation. Ein Beobachter kann seine Zuordnung konservativ verwerfen, muss das aber als Verlust
  eigener Gewissheit und nicht als gemessene Speicherfreigabe kennzeichnen.

Der vorhandene FreeWorldPose-Worker `0x467C0` liest Slot `0x64B4C` im indirekten Call `0x467CC`.
In diesem Pfad wird kein zur Geburt gespeicherter Callback rekonstruiert. Ein Wechsel zwischen Birth und Free
kann daher eine andere Callbackadresse waehlen. Andere Adressen beweisen weder inkompatible Speichervertraege
noch einen Enginefehler: kompatible Customcallbacks sind moeglich, aber hier nicht rekonstruiert.

## 3. Wie vollstaendig ist die Writerliste?

[PoseAllocatorReferences.java](../../ghidra_scripts/PoseAllocatorReferences.java) fragt alle **gespeicherten
Referenzen auf die beiden exakten Adressen** ab: Slot `0x64B48` hat 87 READ/1 WRITE, Slot `0x64B4C` 127 READ/1 WRITE.
Die zwei als direkte WRITE erkannten Stellen sind `0x31908/0x3190D`. Der alte Abbruch nach 12 Eintraegen wird
hier nicht verwendet; das neue Skript endet mit expliziten Vollstaendigkeitsmarkern, Budgetueberlauf ist ein Fehler.

Ein separater Scan aller rohdateigestuetzten PE-Sektionen findet jedes exakte 4-Byte-Vorkommen der beiden Slot-VAs:
88/128 Literalstellen. Jede entspricht hier genau einem der 216 gespeicherten Verweise. Damit ist die konkrete
Liste gegengeprueft; der Census ist **kein** vollstaendiger Writer-/Aliasnachweis. Ein errechneter Zeiger, ein
indirekter Store wie im Gettergegenfall oder eine externe Modulaktion muss diese absolute Konstante nicht tragen.
Der Scanner ist kein Disassembler: ein Treffer in beliebigen Daten waere zunaechst nur ein Literal.

## 4. Bekannter Defaultpfad zum Prozessheap

Default-Allocate `0x31150` erreicht Bridge `0x31920` an `0x31163`; Default-Free `0x31220` erreicht
Bridge `0x31940` an `0x3125C`. Deren gebundene Imports sind KERNEL32 `GetProcessHeap` (IAT `0x5501C`),
`HeapAlloc` (`0x55018`) und `HeapFree` (`0x55020`).

Die Bridges uebergeben an `0x3192E/0x3194E` jeweils `(GetProcessHeap-Return,0,eigenesArgument1)`.
Das Bindungsresultat ist klein und vollstaendig; es ist keine Rekonstruktion aller Allocatorbuchhaltung.
Insbesondere ist das Free-Bridgeargument nicht einfach die eingehende Poseadresse P: auf dem bekannten
gueltigen Defaultpfad liefert Helfer `0x31210` Header `P-32`, und `0x31258/0x3125C` leitet Headerfeld `+8` weiter.
Der umgebende Default-Free prueft/veraendert weitere Header-/Listenfelder; komplette Korruptions-, Fehler-,
Thread- und Reentranzvertraege sind nicht geschlossen. Customallocator muessen nicht diesen Header/Heap verwenden.
InPlace bleibt ein eigener fremder Speichervertrag, keine Default-New-Generation.

## 5. Ausfuehrbare Gegenbeispiele und Engineering-Entscheidung

Das bestehende eigene [Generationsmodell](../../tools/pose_generation_model.py) zeigt zusaetzlich rein synthetisch:

1. Geburt unter Callback A, spaeteres Free unter B: die Callbackidentitaet wird nicht automatisch pro Geburt bewahrt.
2. Zwischen den beiden Setterstores sowie zwischen Getterreads sind gemischte Paare moegliche Interleavings.
3. Gleiche Getterwerte vor/nach einem Intervall erkennen einen zwischenzeitlichen Wechsel und Rueckwechsel nicht.
4. Ein gezielt aliasierender Getter-Ausgabeparameter kann die Quelle des spaeteren Getterreads veraendern.

Das sind Gegenfaelle zu unbewiesenen Engineering-Annahmen, keine beobachteten Spielablaeufe. Jeder Modellbericht
bleibt `live_read_authorized=false`. Die Beispiele beweisen keine reale Nebenlaeufigkeit oder fehlende externe Sperre.

**Entscheidung:** Ein spaeterer Beobachter darf einen Callbacksnapshot nicht als Lifetime- oder Coveragebeweis
behandeln. Eine beobachtete Umkonfiguration ist eine gesonderte Unsicherheitsgrenze fuer seine Zuordnungen;
sie darf nicht einfach alte Births einem neuen Allocatorpaar zuordnen. Der bekannte FreeWorldPose-Eintritt
bleibt eine konservative Invalidierungsgrenze vor Weiterleitung, unabhaengig vom aktuellen Callbackziel.
Ob alle relevanten Freigaben ausgewaehlter H-Posen diese Grenze passieren, bleibt explizit offen.
Auch eine passende Callbackbindung garantiert kein gegen Free/Writer geschuetztes Kopierintervall.

## 6. Reproduktion und Abnahme

Bestehender Verifier bleibt Schema 2, behaelt alle vorherigen 70 Eintraege und ergaenzt zehn Funktionen:
80 Eintraege/93 Bereiche, sieben Exe-Imports/zwoelf Exporte, drei DLL-Heapimports, acht direkte Kanten,
zwei Allocatorslot-/vier Heap-IAT-Calls. Die Dateislotwerte und der gesamte Literalcensus werden separat geprueft.
Manifest-Census umfasst weiterhin beide Originalidentitaeten; Fingerprints sind keine semantische Vollstaendigkeit.

```text
python -I tools/test_pose_sample.py
python -I tools/test_pose_generation.py
python -I tools/pose_generation_model.py
python -I tools/pose_sample_verify.py --exe <eigene-exe> --dll <eigene-dll>
```

Tests/Verifier zusaetzlich mit `-O`. 18 Verifiertests und 19 Modelltests sowie Originaldatei-Gates bestanden
lokal in beiden Modi. Neue Tests lehnen fehlende Worker, veraenderte/vertauschte/abgeschnittene Slotwerte,
veraenderte Callbindungen und unpassende Literalinventare ab. Synthetische Censusfixtures pruefen unaligned
Datentreffer und behandeln Sektionsgrenzen ausdruecklich getrennt; sie behaupten keine echte Instruktionsreferenz.

Ghidra 12.1.4/JDK 21, getrennte Kopie, `-readOnly -noanalysis`. Nach Skriptpfad/Programmwahl:
`PoseAllocatorReferences.java <out.tsv>`; Ausgabe muss `# complete` und beide `# complete_exact_references` enthalten.
`PoseSampleExtent.java <output-dir>` mit folgenden VAs erzeugt den kanonischen neuen Batch:

```text
f:50052870 f:50052890 f:500318E0 f:50031900 f:50031150 f:50031220
f:50031920 f:50031940 f:50031210 f:50031290 d:50064B48:8
```

Kanonisch 11 Dateien/163 Bytezeilen unter lokal ignoriertem `build/pose-allocator-binding/canonical`;
Zwischenexporte `dll` sind kein zusaetzlicher finaler Nachweis. Der unabhaengige Pruefer bestaetigt Originalbytes,
Argument-/Slotbindungen, Literalcensus samt Digest, eigene Aliasgegenfaelle und Tests normal/-O.
Die Projektleitung pruefte zusaetzlich alle 93 Manifestbereiche, zwoelf Exporte und die neuen Heapimport-/
Defaultbindungen mit dem getrennten Audit-PE-Reader. Regulaere spielfreie Gesamtchecks: **16/16 bestanden**.
Der abschliessende unabhaengige Dokumentreview bestaetigt Zahlen, Reproduktion und Aussagegrenzen ohne
sachlichen Blocker. Native/Hub-Builds wurden mangels Aenderung nicht wiederholt; kein neuer GitHub-CI-Lauf.

Die vorab definierte Abnahme ist damit fuer diesen Baustein erfuellt: positive Bindungen sind reproduzierbar,
bekannte direkte Writer von offenen Aliaswegen getrennt, die Konsequenz fuer ausgewaehlte Generationen
benannt und eigene Gates/Gegenbeispiele geprueft. Die selektive Gesamtcoverage wurde nicht geschlossen und
wird ausdruecklich nicht als Erfolg behauptet. Dafuer ist der unten begrenzte konkrete Folgebeweis erforderlich.

**Warum dieser Baustein hilft:** Er ersetzt die pauschale Annahme einer festen Allocatorbindung durch konkrete
API-/Zeit-/Aliasbedingungen und verifizierbare Grenzen. Ein spaeterer nativer Beobachter kann daran seine
Konfigurations-/Invalidierungsregeln testen, bevor echte Poseadressen gelesen werden. Das reduziert falsche
Lifetime-Zuordnungen; es ist noch kein fertiger Beobachter, Performancegewinn oder Beweis gefahrloser Livezugriffe.

## Genau ein Folgebeweis

Den internen WorldPose-Bypass im Kontext `0xE080`, Calls `0xE165/0xE54D`, auf den Posezeiger begrenzen:
Ist das Free-Argument aus einer dort eigenen New-Instanz ableitbar oder kann es eine eingehende ausgewaehlte
H-Pose sein? Nur Erzeugungs-/Uebergabe-/Free-Zuordnung und konkrete offene Aliaskanten, kein gesamter Heap.
Das beantwortet die selektive Relevanz des globalen Bypasses. Das geschuetzte Writer-/Lesefenster bleibt separat.
