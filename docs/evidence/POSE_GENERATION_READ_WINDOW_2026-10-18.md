# Posegeneration: Ereignisgrenzen und noch offenes Leseintervall

> Kurzfassung: WorldPose-New/Free laufen ueber gemeinsame interne Worker und konfigurierbare Allocatorcallbacks; Exporte allein erfassen nicht alle gefundenen Bibliotheksaufrufe. Ein eigenes spielfreies Modell unterscheidet Allokationsgenerationen, verwirft bekannte Luecken/ABA/Ueberlappung und zeigt die Grenze still fehlender Ereignisse. Ein konsistenter Modellverlauf ist keine Live-Leseerlaubnis; das konkrete sichere Kopierintervall ist weiter offen.

Datum 2026-10-18, Basis `34e2513`. [Auftrag](../tasks/POSE_GENERATION_WINDOW_2026-10-18.md),
[Readiness](../design/POSE_COMPARISON_READINESS_2026-10-17.md). Keine Original-/DLL-Ausfuehrung, Hooks,
Installation, Aufnahme oder historischen Pointerzugriffe. Getrennte Ghidra-Kopie readOnly/noanalysis.

## Identitaet und belegte Grenzen

Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, Basis `0x00400000`.
DLL SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`, Basis `0x50000000`.
Alle nachfolgenden Adressen sind DLL-RVAs, ausser ausdruecklich als Exe/VA bezeichnet.

- Export NewWorldPose `0x54400` ruft Worker `0x46790` an `0x54405`.
  Dieser uebergibt N an Groessenhelfer `0x467E0` (`0x46796`), dann dessen Ergebnis als viertes Argument an
  Allocatorslot `0x64B48` (`0x467A5`): `(Dateimetadaten,60,16,Groesse)`.
  Die 16 ist die verlangte Ausrichtung. `0x467AD` gibt N und den Allocatorreturn an den InPlace-Worker
  `0x46840`; dessen Return ist auch der NewWorker-Return. Ein Allocatoraufruf beweist keine erfolgreiche Reserve.
- Export FreeWorldPose `0x54410` ruft Worker `0x467C0` an `0x54415`.
  `0x467CC` delegiert an Slot `0x64B4C` mit `(Dateimetadaten,68,eingehenderPosezeiger)`.
  Die gewaehlten Callbackkoerper und eine dauerhafte unveraenderte Slotbindung sind hier nicht rekonstruiert.
- Ein weiterer direkter Bibliothekscaller, Ghidra-Eintrag `0xE080`, ruft NewWorker an `0xE165` und FreeWorker
  an `0xE54D` direkt, ohne die beiden Exportwrapper. Damit ist die globale Export-only-Abdeckung widerlegt.
  Es ist **nicht** bewiesen, dass gerade die aus dem bekannten Exe-H-Pfad beobachteten Posen ueber diesen
  anderen Kontext freigegeben werden. Selektive Coverage muss an den ausgewaehlten Generationen belegt werden.
- NewWorldPoseInPlace `0x54430 -> 0x46840` verwendet bereitgestellten Speicher. Das ist kein eigener
  Bibliotheks-Allokationsnachweis und kein automatisch zulaessiger FreeWorldPose-Partner.

Der wiederverwendete Layoutvertrag F150 liefert im geprueften gueltigen Bereich `16+128*N` Bytes, World bei
Pose+16, Composite bei Pose+16+64*N. Geburt einer ausgewaehlten Generation setzt einen beobachteten erfolgreichen
Konstruktorabschluss **und** einen gueltigen Allocator-/Speichervertrag voraus. Die gewuenschte Groesse oder
ein spaeter gelesener HeaderN beweisen das nicht. Bei N=0 existiert keine Matrix0.
F150 pruefte eigene Defaultallocator-Hosts; benutzerdefinierte Allocatoren, Reentranz und Threads waren ausgenommen.
[Frueherer Vertrag](POSE_CONTRACT_2026-10-16.md).

Die Referenzabfrage `AddressContext` ist auf 12 Referenzen je Ziel begrenzt; Callbackslot-Listen sind abgeschnitten.
Sie ist kein vollstaendiges Inventar aller Heapfreigaben oder indirekten Aufrufe. Die beiden konkreten
Worker-Bypasscalls sind zusaetzlich als direkte rel32-Kanten an Originalbytes geprueft.

## Ereignisvertrag fuer eine ausgewaehlte Generation

Dies ist ein eigener Engineering-Vertrag, keine bereits vorhandene Messung:

1. Nur vollstaendig zugeordnete erfolgreiche NewWorldPose-Abschluesse mit Herkunft/Kapazitaet aufnehmen.
   Vorbestehende oder nur ueber einen Header entdeckte Posen bleiben unbekannt; InPlace bleibt separat.
2. Jede Geburt erhaelt ein neues Token. Gleiche Adresse und gleicher N-Wert nach Freigabe ergeben eine neue
   Generation. Bei mehrdeutiger/ueberlappender Geburt keine Generation erfinden.
3. Beim relevanten Free-Eintritt vor der Weiterleitung invalidieren, nicht erst nach Callbackreturn oder dem
   spaeteren O+0x4C-Reset. Eine beobachtete Free-Absicht reicht zur konservativen Invalidierung auch dann,
   wenn ihre erfolgreiche Vollendung unklar bleibt.
4. Ein bekannter Ereignisverlust verwirft alle davon betroffenen Zuordnungen; im kleinen Modell globaler Epochwechsel.
   Stille, nicht gemeldete Verluste sind dadurch nicht automatisch erkannt.
5. Verschachtelte/konkurrierende Operationen derselben Generation werden unklar. Die reine Reihenfolge ihrer
   Logzeilen beweist keine echte Synchronisation. Auswahlbudget und verlorene Lebenszyklusereignisse trennen.

Die Hierarchie ist: numerisch passende Groesse < konsistente beobachtete Generation < vollstaendige relevante
Ereignisabdeckung < geschuetztes Leseintervall. Die ersten Stufen ersetzen die spaeteren nicht.

## Ausfuehrbarer eigener Nachweis

[pose_generation_model.py](../../tools/pose_generation_model.py) verarbeitet nur eigene synthetische Adress-/
Thread-IDs; kein Speicherzugriff, keine Originaldatei, keine Hooks, keine echten Aufnahmen und kein Snapshotcopy.
Hoechstens 16 gleichzeitig ausgewaehlte Records und 16 zusammengefuehrte Quarantaenebereiche, monotone
Generations-/Operationsnummern, Epochwechsel bei Luecken. Widerspruechliche erfolgreiche Births behalten beide
Bereiche bis zum expliziten Epochwechsel, auch nach einer einzelnen Free-Meldung. Quarantaeneueberlauf macht
die gesamte Zuordnung unklar bis zum Epochwechsel; Speicherbedarf waechst dadurch nicht unbegrenzt.
Python dient hier als spielfreies Testmodell, nicht als Produktionscode auf dem Spielthread.

- Positiver eigener Ablauf: Birth -> Operation -> Abschluss liefert `consistent_observed_sequence` und
  numerische Matrix0-Spannen. Das bestaetigt Modellmetadaten unter seinen Ereignisannahmen.
- ABA: Birth an A -> Operation -> Free(A) -> neuer Birth an A -> alter Abschluss wird `stale_generation`,
  obwohl Adresse und N vorher/nachher gleich sein koennen.
- Gemeldete Luecke: alle Tokens des alten Epochs werden ungueltig. Nested/Concurrent-Operationen und
  mehrdeutige Geburt machen die betroffene Zuordnung unklar.
- **Blindstelle:** Wird eine hypothetische Free-/Reuse-Sequenz gar nicht an das Modell geliefert, kann derselbe
  Metadatenverlauf konsistent erscheinen. Der Test erwartet dieses Ergebnis ausdruecklich. Es zeigt die externe
  Coveragepflicht, keine gemessene verheimlichte Spielaktion.
- Jede Antwort enthaelt `live_read_authorized=false`, auch positive eigene Ablaeufe. Es gibt keine positive
  Live-Sicherheitsentscheidung in diesem Modell. Das ist kein pauschal ablehnender Live-Pruefer, sondern eine
  getrennte Referenz fuer Ereigniszuordnung, deren externe Voraussetzungen bewusst nicht behauptet werden.

`python -I tools/pose_generation_model.py` erzeugt diese Gegenbeispiele als JSON.
[17 Tests](../../tools/test_pose_generation.py) pruefen ausserdem Budget, Nullkapazitaet, numerische Grenzen ohne
grosse Allokationen, Thread-/Ticketzuordnung und wiederholtes Reuse. Ein veraenderter Header ist kein Birth-Ereignis.
Eigene Python-Integer sind unbeschraenkt; eine spaetere native Umsetzung muss Token-/Epochueberlauf separat behandeln.

## Entscheidung zum Kopierfenster

**Statisch bekannt:** Nach normalem Abschluss von `0x44F40` sind unter den F175-Voraussetzungen World0 und
Composite0 jeweils 64 Bytes beschrieben. Im bekannten Caller beginnt der Restloop erst danach bei Index 1.
Das aeussere Sample-Return `Exe 0x38E6DF` liegt spaeter. Zwischen diesen Punkten duerfen nicht pauschal
unveraenderte Posen oder identische dynamische Generationen angenommen werden.

**Bedingt plausibler Kandidat:** Kopie direkt nach dem inneren Writer auf demselben Thread, mit expliziter
Zuordnung des Zielpaares zu einer lebenden ausgewaehlten WorldPose-Generation. Das reduziert die Zeit bis zur
Kopie; es beweist aber weder eine hinreichende Argumentlebensdauer noch Abwesenheit fremder Freigaben/Writer.
Aktiver Originalcall ist eine noch zu belegende Lifetimeannahme, kein Schutzmechanismus an sich.

**Nicht geschlossen:** Kein unbehandelter Free/Reuse und kein konkurrierender oder reentranter Writer waehrend
der ganzen128-Byte-Kopie. Ein Metadatenlock schuetzt ohne weitere Bindung nur eigene Metadaten, nicht den
Originalspeicher. Vorher-/Nachherpointer oder ein abschliessender Generationstest verhindern keinen bereits
erfolgten Zugriff auf freigegebenen Speicher und garantieren keine zusammengehoerige Matrixpaar-Kopie.

Deshalb kein Livezugriff und keine Observerimplementierung. Erste-Matrix-Bytegleichheit waere nur ein enges
Teilergebnis, keine Ganzpose-/versteckte-Zustands-/Cache-/Skipbehauptung.

## Reproduktion und Pruefung

Bestehender [Sample-Verifier](../../tools/pose_sample_verify.py) bleibt Schema2 und behaelt die bisherigen
58 Eintraege. Zwoelf neue Eintraege: neun Layout-/New-/Free-Funktionen, zwei direkte Callerbereiche und ein
Allocator-Slotpaar. Gesamt70 Eintraege/83 Bereiche, sieben Imports/zehn Exporte. Vier direkte Worker-/Layoutkanten
und zwei indirekte Allocatorslot-Calls werden zusaetzlich explizit dekodiert/geprueft.
Fingerprints sind Byte-/Ortsbelege; sie beweisen keine globale Caller- oder Aliasvollstaendigkeit.

Getrennte Ghidra-Kopie, Ghidra 12.1.4/JDK 21, `-readOnly -noanalysis`, vorhandener `PoseSampleExtent.java` unveraendert.
Finale Ausgaben lokal ignoriert unter `build/pose-generation-window/`: `exe`, `baseline-dll`, `dll`.
578 Exe-/3176 DLL-Bytezeilen gegen Originalbytes geprueft. DLL-Ziele sind auf zwei Batches verteilt, um das
64-Zielbudget unveraendert einzuhalten. Basisbatch: vollstaendige Argumente aus
[Fast-Evidenz](POSE_FIRST_BONE_FAST_2026-10-18.md). Zusaetzlicher DLL-Batch nach dem Ausgabeordner, als **VAs**:

```text
f:50054400 f:50054410 f:50054420 f:50054430 f:50046790 f:500467C0
f:500467E0 f:50046800 f:50046840 r:5000E165:5000E169 r:5000E54D:5000E551 d:50064B48:8
```

`AddressContext.java <out> 50046790 500467C0 50046840 50064B48 50064B4C` liefert die begrenzte Referenzliste.
Manuelle Nachpruefung: bei 0x467A5 vier Stackargumente (Groesse an Stelle 4), bei 0x467AD N/Allocatorreturn;
bei 0x467CC Poseparameter an Stelle 3. Die kleinen New-/Free-Worker wurden auch mit einem eigenen begrenzten
Stack-Argumentauswerter geprueft; Originalinstruktionen bleiben in den lokalen Listings.

Produktions-PE-Reader und separater Audit-PE-Reader bestaetigen alle 83 Manifestbereiche, sieben Import- und
zehn Exportbindungen; Original-SHA unveraendert. Das sind getrennte technische Bytekontrollen.
Der urspruengliche Agentenlauf scheiterte am Kontolimit; der erneut gestartete unabhaengige Pruefer bestaetigte
die kanonischen 65 DLL-/5 Exe-Ausgaben byteweise und pruefte das Modell normal/-O. Sein eigener Gegenfall fand
eine Modellschwaeche: ueberlappender Birth B wurde vergessen, wenn anschliessend nur Record A freigegeben wurde;
ein weiterer Birth B erschien wieder konsistent. Ein neuer Test reproduzierte den Fehler vor der Korrektur.
Die begrenzte Quarantaene schliesst ihn; der Pruefer bestaetigte seinen eigenen Gegenfall danach sowie 17 Tests
normal/-O. Das ist eine Werkzeugkorrektur, kein Spielbefund. Der abschliessende unabhaengige Dokumentreview
bestaetigt Zahlen, Reproduktion und Aussagegrenzen ohne sachlichen Blocker.

Abnahme lokal: `python -I tools/run_checks.py` besteht 16/16 Pruefgruppen. Modelltests (17), Verifiertests (15)
und Originaldatei-Verifier bestehen normal und mit `-O`; keine Originalfunktion wird ausgefuehrt. Kein neuer
nativer Build, kein Hub-/Observerumbau und kein GitHub-CI-Lauf in diesem Baustein.

## Genau ein Folgebeweis

Die Veraenderungs-/Weiterleitungspfade der Allocatorslots `0x64B48/0x64B4C` fuer die ausgewaehlte
NewWorldPose-Provenienz abgrenzen. Welche Umkonfiguration oder direktere Freigabe kann eine beobachtete
Generation unbemerkt beenden, und welche Ereignisgrenze wuerde das erkennen? Kein kompletter Heapnachbau.
Auch danach bleibt der separate Writer-/Readwindow-Nachweis erforderlich. Keine Hooks, Observer oder Aufnahme.
