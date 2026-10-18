# Erste-Bone-Schnellroute: Zielbytes und getrennte Quellgueltigkeit

> Kurzfassung: Alle drei Quellzweige des bekannten Fastentrys 0x44F40 geben World0 und Composite0 an bekannte Writer weiter, die jeweils volle 64 Zielbytes schreiben. Die zweite Route benoetigt keine interne Transformtemporaere und hat einen engen gueltigen Parent-/InverseBind-Vertrag. In den beiden anderen Routen sind die Zielstores ebenfalls voll, aber die Initialisierung aller gelesenen Tempkomponenten ist nicht geschlossen. Das sind verschiedene Beweisstaerken, kein festgestellter Enginefehler.

Stand 2026-10-18, Ausgangscommit `eb6b564`, zu Beginn sauber. Identitaeten erneut dateilesend geprueft:
Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, Basis `0x00400000`;
DLL SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`, Basis `0x50000000`.
Alle folgenden Adressen sind **DLL-RVAs**, ausser ausdruecklich als VA/Exe gekennzeichnet.
Nur getrennte Ghidra-Kopie, Ghidra12.1.4/JDK21, `-readOnly -noanalysis`. Keine Originalausfuehrung,
Livebeobachtung, DB-Mutation, Installation oder native Implementierung. Lokaler Integrationscommit durch die
Projektleitung, kein Push. Gesamtchecks siehe Integrationsabnahme unten.
Grundlagen: [Wissenskarte](../ANIMATION_KNOWLEDGE_MAP.md), [Spezialcallback](POSE_SPECIAL_CALLBACK_2026-10-17.md),
[Slot-/Matrixvertrag](POSE_SAMPLE_EXTENT_2026-10-17.md).

## Erreichbarkeit und Callerargumente

Der Sample-Spezialzweig setzt weiterhin voraus: erster Listenknoten n mit `0x1B540(*(n+0))==true`,
und dessen naechster Knoten ist der Listen-Sentinel `head` oder dessen Kontrollpraedikat ist false.
Dies ist kein NULL-Endvergleich. Aus `D=*(n+0x18)` muss tatsaechlich der aktive Callbackentry `0x1C780`
gewaehlt werden. Die fruehere Descriptorherkunft aus dem Animationsbuilder ist bedingt; keine universelle
Erhaltung jeder lebenden Instanz/Tabellenbindung wird hier hinzugefuegt.

In diesem Callback gilt fuer gueltige nichtnegative Counts `C=min(B,T)`, mit B aus dem Sample und
`T=*(AB+0x20)`, `AB=*(n+0x1C)`. Der erste Fastaufruf liegt vor dem allgemeinen Countguard.
Seine genauen Bedingungen sind `*(n+0x20)==2` und nichtnull `X=*(TrackBase+4)`,
`TrackBase=*(AB+0x24)`. Der Vergleich mit2 ist exakt, kein Maskentest.
Eine lesbare Track0-Struktur beweist weder T>=1 noch die Allokationsherkunft des Trackarrays.

`0x44F30` liefert konstant VA `0x50044F40`; der anschliessende Call `0x1C8DB` hat folgende Argumentbindung:

1. K: lokaler Kontext des Callers, kein WorldPose-Header.
2. X: `*(Track0+4)`, ein weiterer Quellreferent; X ist **nicht Track0 selbst**.
3. Track0: erster88-Byte-Trackrecord.
4. Bone0+8: Resttransformquelle.
5. Bone0+0x4C: InverseBindquelle J.
6. Parent P: A bei `Bone0.parent==-1`, sonst `WorldBase+64*parent`.
7. WorldBase: Ziel World0, aus W+4.
8. CompositeBase: Ziel Composite0, aus W+8.

Die Bonequelle kommt aus `n+0xC -> I+0 -> M+4 -> S+8`. Gueltige Bone0-/Parentdaten und Kapazitaet fuer
Matrix0 sind eigene Voraussetzungen. Die Exe uebergibt zuvor R=S.N an Sample; R, B, T, C und HeaderN sind
verschiedene Groessen. Aus diesen Feldketten folgt kein universell gueltiger leerer oder nichtleerer Bereich.
Der Fastentry benutzt fuer seine Quellpraedikate `Q=X+0x14`; die Argumente3/4 sind keine alternative
Outputindexzuordnung. Outputindex ist in allen drei Fastzweigen0.

## Die drei Quellzweige

Beide kleinen Praedikate lesen `Z=*(Q+4)`, Formatbyte `f=*(uint8*)Z`.
Die folgenden Beschreibungen sind der konkrete Pruefvertrag, keine aus SDK-/Exportnamen abgeleitete Typdefinition:

- `0x33E0(Q)` ist true bei f=0 oder bei f=1 mit `*(Z+4)==0` und signed `*(Z+0xC)>0`.
- `0x3410(Q)` ist true bei f=2 oder bei f=1 mit `*(Z+4)==0` und `*(Z+0xC)==0`.
- Andere Zustaende sind false. Die dafuer tatsaechlich gelesenen Z-/Feldadressen muessen gueltig sein.
  Es wird keine allgemeine Abweisung korrupter/negativer Daten durch diese Praedikate behauptet.

**Route A:** `0x33E0(Q)==true`. `0x44F73` ruft
`0x3DE0(Q, *(K+0xC), U+0x20, VA 0x500608FC)`.
U ist eine lokale68-Byte-Transformtemporaere. Der Wrapper setzt U+0 auf4.
Danach ruft `0x44F93` Slot `0x61A84` mit `(U,P,J,CompositeBase,WorldBase)` und kehrt an `0x44FA0` zurueck.

**Route B:** erster Test false, `0x3410(Q)==true`. `0x44FC2` ruft direkt Slot `0x61A78` mit
`(P,J,CompositeBase,WorldBase)` und kehrt an `0x44FCF` zurueck. Keine U-Transformquelle und keine
Kurvenproduktion wird auf diesem Pfad gebraucht. Als beschreibende Wirkung, nicht als Typname:
World0 erhaelt die Parentmatrix; Composite0 wird aus InverseBind und dieser Worldmatrix aufgebaut.

**Route C:** beide Tests false. `0x44FEC` ruft
`0x44AC0(K,9,Q,U+0x20,VA 0x500608FC,0)`. Wieder setzt der Wrapper U+0 auf4.
Danach ruft `0x4500D` Slot `0x61A84` mit `(U,P,J,CompositeBase,WorldBase)` und kehrt an `0x4501A` zurueck.
Die9 ist ein Producerparameter, kein zusaetzlicher Outputmatrixcount. Der Inhalt des Defaultdatenreferenten
VA `0x500608FC` wird hier nicht als vollstaendig rekonstruierter Transformdefault vorausgesetzt.

## Volle Zielstores in allen drei Routen

Die pfadgetrennte Stackbindung ist wichtig: Composite ist der vorletzte, World der letzte Zielparameter.
Slot `0x61A78` waehlt unter dem bekannten aktiven Dispatch Scalar `0x15620` oder SSE `0x15B00`;
Slot `0x61A84` waehlt Scalar `0x156B0` oder SSE `0x15C50`.
Die vollstaendige64-Byte-Abdeckung dieser vier Kandidaten einschliesslich aller16 float32-Komponenten wurde
bereits geprueft. Parent-/InverseBind-/Worldargumente sind hier auf genau diese Zielbindungen zurueckgefuehrt.

Bei normal beendeten Calls, aktiven bekannten Slots, gueltig lesbaren benoetigten Quellbereichen und gueltigen
schreibbaren disjunkten Zielen schreiben deshalb **alle drei Routen** volle64 Bytes World0 und volle64 Bytes
Composite0. Es gibt im Fastwrapper weder einen Counttest noch eine Auswahl anderer Matrixindices.
Die verbleibende A/C-Quellgrenze bedeutet **nicht**, dass Destinationkomponenten ungeschrieben bleiben.
Vollstaendige CPU-Zielstores und semantisch gueltige/aus initialisierten Quellen erzeugte Transformwerte sind
jedoch verschiedene Aussagen. Fehlende Rueckkehr, FP-Ausnahme, Alias oder fremder Dispatch sind nicht durch
die Storeabdeckung ausgeschlossen.

Fuer Route B ist ein enger positiver Wertevertrag vorhanden: gueltige initialisierte Parent-/InverseBind-
Matrizen, passende affine Domain des bisherigen Compositevertrags, bekannte Writer und gueltige Ziele reichen
fuer die beschriebene World-/Compositebildung. Es ist keine Quelle aus einer unbewiesenen lokalen U beteiligt.

## Konkrete A/C-Quellinitialisierungsgrenze

Der Bezug auf die echte lokale Stackadresse wurde getrennt je Route nachvollzogen: bei Fastentry-ESP=E0
liegt U bei E0-68 dezimal; der an die Producer uebergebene Outputpointer liegt bei E0-36, also **U+0x20**.
Das sind neun float32-Plaetze bis einschliesslich U+0x40. Im Wrapper sind neben U.flags=4 keine Stores
belegt, die Translation U+4/+8/+0xC oder Quaternion U+0x10..+0x1C initialisieren.

Die Frage wurde pfadspezifisch fuer Flags4 geprueft, nicht durch Vereinigung beliebiger Helferreads:
Scalar `0x156B0 -> 0x155D0 -> 0x1AC0`, SSE `0x15C50 -> 0x1AC0`.
`0x1AC0` ruft `0x30310` mit Quaternionquelle U+0x10 **vor** seinem einzigen Test der Maske0x4
(`0x1AD2` vor `0x1ADC`). Bei Flags4 folgt der Scale-/Shearzweig ueber `0x2FD80`;
danach werden U+4/+8/+0xC ohne weiteren Flagdefault gelesen. Flags4 ersetzt diese Quellen also nicht
durch nachgewiesene Standardwerte. Die Bytes der Consumer waren schon im vorherigen Manifest enthalten.

`0x3DE0` waehlt einen datenformatabhaengigen indirekten Producer aus der Tabelle um RVA `0x60638`.
`0x44AC0` hat weitere interne Producer-/Samplingpfade; die im Wrapper ankommende falsche Antwort von
`0x3410(Q)` ist dabei bereits bekannt, sofern Q zwischen den Calls unveraendert bleibt.
Dieser begrenzte Auftrag beweist **nicht**, welche gesamten Speicherbereiche diese indirekten/weiteren
Producer schreiben, ob dabei weitere U-Felder definiert werden oder welche sonstige Herkunft diese Stackbytes
haben. Deshalb folgt aus der Wrapper-Teilinitialisierung kein belegter Enginefehler und aus einem normal
beendeten A/C-Aufruf keine voll rekonstruierte gueltige Transformquelle. Die offene Kante ist konkret der
Producervertrag fuer `(Q,Scalar,U+0x20,Defaultdaten)` beziehungsweise `(K,9,Q,U+0x20,Defaultdaten,0)`
bis zu den benoetigten U-Komponenten. Keine automatische Rekonstruktion aller Curve-/Trackfamilien.

Fuer einen reinen spaeteren Vergleich real erzeugter Ausgabebytes ist diese semantische Quellpflicht separat
zu behandeln: Die volle Zielbyteabdeckung ist belegt, ein eigener mathematischer Nachbau dadurch nicht.
Konkrete lebende Allokationsgeneration, erlaubte Kapazitaet und ein gesichertes Leseintervall bleiben auch fuer
einen Bytevergleich zwingend. Hier ist kein solcher Observer implementiert oder freigegeben.

## Zusammensetzung mit dem folgenden Loop

Nach dem Fastcall setzt `0x1C8DD..0x1C8F5` i=1 und rueckt Bone/Track/World/Composite auf Index1 vor;
der Countguard `0x1C8FC/0x1C8FE` folgt erst danach. Fuer die enge gueltige Domain **C>=1** gilt damit:

- Fast schreibt World0 und Composite0, je64 Bytes; Route B hat den oben beschriebenen positiven Wertevertrag,
  Route A/C die getrennte Sourcepflicht.
- Der allgemeine Loop verarbeitet i=1..C-1. Wenn jede dieser Iterationen die bereits gebundenen direkten Helfer
  `0x44DA0/0x44DE0` mit gueltigen Quellen und bekanntem Dispatch nimmt, schreibt sie beide vollstaendigen
  Matrizen an i. Bei C=1 ist dieser Restloop leer.
- Zusammen ist der **Zielbyte-Schreibbereich** beider Arrays `[0,64*C)` relativ zu ihrem jeweiligen Basezeiger.
  Fuer semantisch gueltige Werte ist bei Route B zusaetzlich der bisherige gueltige Restloopvertrag ausreichend;
  bei A/C bleibt die beschriebene Tempinitialisierung offen. Bei C<B gibt es keine implizite Ergaenzung `[C,B)`.

Bei C=0 liefert der allgemeine Abbruch allein weiterhin keinen NoWrite-Beweis: der Fastaufruf liegt davor.
Der lokale Codevertrag lautet nur, dass ein tatsaechlich ausgefuehrter, normal beendeter Fastentry mit seinen
Voraussetzungen Matrix0 schreibt. Dies ist **kein** nachgewiesenes gueltiges C=0-Sample-Schreibgegenbeispiel.
Insbesondere wird aus einem zufaellig lesbaren Bone0/Track0 weder logische Countgueltigkeit noch ausreichende
Posekapazitaet abgeleitet; vorgelagerter Kontrollzweig, aktive Descriptorbindung und konkrete Allokationen sind
gemeinsam zu pruefen. Der indirekte Restloop-Trackcallback `0x1C9C1 -> *(Track+8)` bleibt unveraendert offen.

## Reproduktion und gezielte Gates

Der bestehende [Verifier](../../tools/pose_sample_verify.py), [Manifest](../../tools/pose_sample_manifest.json)
und [Tests](../../tools/test_pose_sample.py) wurden um die vier tatsaechlich neu untersuchten Koerper
`0x33E0/0x3410/0x3DE0/0x44AC0` erweitert. Kein Verifierklon, **Schema2 unveraendert**.
Alle vorherigen54 Eintraege/67 Bereiche bleiben erhalten; jetzt58 Eintraege/71 Bereiche, weiterhin sechs
Imports/sechs Exportbindungen. Neue Tests verwerfen fehlende oder veraenderte Gates dieser vier Koerper.
Fingerprints und Praedikatnamen sind Identitaets-/Abdeckungsbelege, keine automatische Semantikverifikation.

Bestanden: `python -I tools/test_pose_sample.py` und `python -O -I tools/test_pose_sample.py`, jeweils13 Tests.
Die vorhandenen Unknown-Build-Kindprozesse laufen normal und mit **explizitem -O**.
Originaldateiverifier normal und mit `-O` bestanden; `game_executed=false` und
`unconditional_sample_initialized_span_proven=false` bleiben gesetzt. Keine Gesamtchecks durch den Bearbeiter.

Finale gemeinsame Exporte beider Module mit unveraenderter finaler Quelle
[PoseSampleExtent.java](../../ghidra_scripts/PoseSampleExtent.java), `-readOnly -noanalysis`, liegen lokal unter
`build/pose-first-bone-fast/final-exe` und `final-dll`. 578 Exe-/3054 DLL-Zeilen einschliesslich sechs
Datenzeilen wurden gegen Originaldateibytes verglichen. Identitaetsdateien enthalten SHA/Basis/Argumente.
Vollstaendige Argumente nach dem lokalen Ausgabeordner (**VAs**, keine RVAs):

```text
Stronghold2.exe:
f:0078E0A0 f:0078E4D0 d:00900A98:4 d:00900B10:4 d:00900AD4:4

granny2.dll:
f:5004F6D0 f:5004F700 f:50002A70 f:500469C0 f:50047060 f:50002460
f:50002630 f:5001B540 f:5003A5D0 f:50002840 f:5002E9E0 f:500322D0 f:50032300
f:50015440 f:500154B0 f:50015570 f:500155D0 f:50015600 f:50001AC0 f:5002FF60
f:50030310 f:5002FD80 f:50047920 f:5004F4D0 f:50002620 f:5004F4B0 f:50002570
r:50015620:50015CBF d:50061A78:16
f:50050F70 f:50050FD0 f:5001D040 f:5001D2B0 f:500023B0 f:500022C0
f:5001B570 f:5001C400 r:5001C780:5001CA40 f:5001C450 f:5001BFD0
f:50044F30 f:50044DA0 f:50044DE0 r:50044F40:5004501A
f:5001D980 f:50051130 f:5001BDB0 d:50061D58:28 d:50061ED0:28
f:500033E0 f:50003410 f:50003DE0 f:50044AC0
```

## Integrationsabnahme und Folgeprioritaet

Unabhaengiger Freeze-Review bestaetigt Caller-/Zieltuples, feste Entry-SP-Adressen, Praedikatfelder und den
Flag4-spezifischen Consumerpfad. Finale 578 Exe-/3054 DLL-Bytezeilen stimmen. Parent bestaetigt mit separatem
Audit-PE-Reader alle 71 Manifestbereiche sowie sechs Import-/sechs Exportbindungen; beide Originalfile-SHA
bleiben unveraendert. Originalverifier normal/-O und die 13-Test-Suite mit `-O` erneut bestanden.
`python -I tools/run_checks.py` integriert bestanden: 15/15 spielfreie Pruefgruppen inklusive Sample-Suite
und Dokumentationslint. `--audit`/`--e2e` nicht wiederholt, weil Hub/Observer unveraendert sind. Keine neuen
nativen Host-/Original-DLL-/Spielausfuehrungstests und kein neuer GitHub-CI-Lauf.

Projektentscheidung: nicht automatisch alle indirekten Producer rekonstruieren. Als Naechstes den konkreten
Gueltigkeitsvertrag einer begrenzten ersten-Matrix-Bytebeobachtung pruefen: identifizierbare lebende Generation,
ausreichende Kapazitaet und gesichertes Leseintervall. Ein unbekannter Nachweis bleibt unbekannt; hier entsteht
keine Freigabe fuer Livezugriffe. Erste-Matrix-Gleichheit ist keine Ganzpose-/Zustands-/Skipbehauptung.
Keine Observer-/Hookimplementierung, Originalausfuehrung oder neue Aufnahme in diesem Folgebeweis.
