# Pose-Sample: bedingter Schreibumfang von World und Composite

> Kurzfassung: Zwei direkte Worker schreiben auf ihren gueltigen, unten abgegrenzten Pfaden pro ausgewaehltem Knochen volle 64 Bytes in beide Arrays. Die bekannte Samplekante setzt den ersten Ausgabeindex auf null. HeaderN und normale Sample-Rueckkehr allein rechtfertigen trotzdem keine volle Outputlesung: Spezialcallback, Quellgueltigkeit, konkrete Allokationsgeneration und Leseintervall bleiben getrennte Beweisobligationen.

Stand 2026-10-17, Forschungsbasis `21c3af7`, ohne Spiel-/DLL-Ausfuehrung. Nur statische Analyse einer separaten
Ghidra-Kopie, `-readOnly -noanalysis`. Vorwissen: [Posevertrag](POSE_CONTRACT_2026-10-16.md),
[Erzeugung](HPOSE_CREATION_2026-10-17.md), [Readiness](../design/POSE_COMPARISON_READINESS_2026-10-17.md).
Keine Originaldatei, bestehende Rohaufnahme oder originale Ghidra-Datenbank beschrieben; kein Observer, Cache,
Hook, C++-Nachbau oder Installieren; lokaler Integrationscommit durch die Projektleitung, kein Push. Inventarisierte Koerper/Bytefingerprints sind keine entsprechende
Anzahl semantisch vollstaendig verstandener Funktionen.

## Identitaet und drei verschiedene Zaehler

- Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, Basis `0x00400000`.
- DLL SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`, Basis `0x50000000`.
- Alle Adressen sind **Modul-RVAs**, soweit nicht ausdruecklich VA genannt; VA = jeweilige Basis + RVA.
- `R` ist die angeforderte Sample-Knochenzahl, `B` der nach dem signed Vergleich in DLL `0x2AF7..0x2B00`
  verwendete Wert: fuer die gueltige Domain `R >= 0`, `S.N >= 0` gilt `B=min(R,S.N)`.
- `W.N` ist der WorldPose-Headerzaehler, kein Erfolgs-/Initialisierungszaehler. Die vorherige gueltige Konstruktion
  reserviert logisch beide N*64-Byte-Arrays (`16+128*N` gesamt); Header und Zeiger allein beweisen weder eine lebende
  fremde Allokation noch deren physische Reserve. Tatsaechliche Schreibindices ergeben sich aus dem gewaehlten Worker.

## Exe-Argumentbindung und bedingte Kapazitaetsrelation

Exe `0x38E6B7..0x38E6DF` bindet den ausgewaehlten H-Record an den Samplecall `0x38E6D9`, Return `0x38E6DF`.
Die fuenf Argumente sind `(I=H+0, R=S.N, A=lokale 64-Byte-Matrix, L=H+8, W=H+4)`;
die letzten drei bereits gestapelten Argumente bleiben ueber `GetSourceSkeleton` erhalten.
Der Import an Exe-IAT `0x500B10` ist `_GrannyGetSourceSkeleton@4`; der Import `0x500A98` ist
`_GrannySampleModelAnimationsAccelerated@20`. DLL-Export `0x4F4D0` -> `0x2620` liest
`S=*( *(I+0) +4)`, danach liest die Exe `S+4` fuer R.
Sample-Export `0x4F6D0` hat `ret 20`; `0x4F700` fuegt einen sechsten Parameter null hinzu und ruft `0x2A70`.
Dieser liest dasselbe S ueber I und klemmt R erneut gegen S.N. Die Getter geben keinen Sample-Erfolg zurueck.
Der Samplewrapper liefert hier keinen nachgewiesenen Erfolgsstatus; EAX am Return ist kein solcher Vertrag.

Im bekannten Erzeugungspfad Exe `0x38E27D..0x38E2B4` gehen `M=*(H.resource+0xC)` an InstantiateModel und
`Nalloc=*(*(M+4)+4)` als Zaehler an NewWorldPose/NewLocalPose; deren Returns werden H+0/+4/+8.
DLL `0x4F4B0` -> `0x2570` speichert bei erfolgreicher Instanzerzeugung M in I+0 (`0x258C`).
Damit passt dieselbe Quellfeldkette zur spaeteren Samplezahl. **Bedingte Gleichheit:** nur wenn derselbe erfolgreich
erzeugte H/I/M/S-Zusammenhang und derselbe Zaehler bis zum Call erhalten bleiben und W/L dieselben lebenden
erfolgreichen Allokationen sind, folgt `R=S.N=Nalloc=W.N=L.N`. Das ist keine alle dynamischen Aufrufe umfassende
Lebensdauer-/Unveraendertheitsinvariante. Ein geaenderter S-Zaehler oder ausgetauschtes H/W/L laesst diese Relation
offen; `0x47060` repariert oder prueft die WorldPose-Kapazitaet nicht.

## Sampleverzweigung und ihre Grenze

DLL `0x2A70` hat folgende begrenzte Struktur:

- `L==null`: Diagnosecall `0x2AD5`, danach Profiling/Epilog; kein direkter Matrixwriter in diesem Pfad.
  Das ist ein Fehlerpfad, kein Beispiel eines gueltig erfolgreichen Samples. Diagnose-/globale Aliase sind damit
  nicht universell ausgeschlossen.
- Liste aus `0x2630(I)=I+4`, erster Knoten ueber `head+0x14`. Leere Liste oder false beim Praedikat
  `0x1B540(first.control)` erreicht `0x2C52..0x2C5E` -> `0x47060(S,0,B,A,W)`.
- Bei true fuer die erste Kontrolle wird `K=0x3A5D0(S,0)` berechnet. Falls der naechste Knoten existiert und dessen
  Kontrolle ebenfalls das Praedikat erfuellt, folgt `0x2840(I,0,K,L,0,0)` an `0x2C03`, danach
  `0x469C0(S,0,B,0,K,L,A,W)` an `0x2C22`.
- Ansonsten folgt `0x2460(first.node,B,A,W,0)` an `0x2C44`. `0x2460` liest
  `D=*(first.node+0x18)`, `callback=*(D+0x10)` und springt bei nonnull dorthin, sonst lokales RET.
  Seine ersten fuenf Stackargumente bleiben erhalten. **Fuer diesen Spezialzweig wird kein World-/Composite-Span
  behauptet.** Welche Descriptor-/Callbackkombination in der gueltigen Domain hier ankommt und welche davon
  schreibt, ist nicht gebunden. Insbesondere wird aus lokalem Nullcallback-RET kein gueltiges End-to-End-Sample-
  Gegenbeispiel abgeleitet. Nach diesen drei Aufrufen folgt im geprueften `0x2A70` nur dessen Profiling/Epilog,
  kein direkter Fallbackwriter.

Das Praedikat `0x1B540` ist die tatsaechliche boolesche Verzweigung im Binärpfad; daraus wird kein vollstaendiger
semantischer Kontrolltyp abgeleitet. `0x2840` und dessen Control-/LocalPose-Quellen sind nicht als vollstaendige
gueltige Transformproduktion rekonstruiert. Vollstaendige Zielstores alleine beweisen keine semantisch gueltigen
Werte, wenn vorgelagerte LocalPose-/Kontrolldaten oder Elternmatrizen ungeprueft sind.

## Direkte Worker: Zielindices und Vorbedingungen

Prioritaet hat der konkrete Sample-Unterpfad mit erstem Bone-/Ausgabeindex `f=0` und Guardparameter `a=0`.
Der allgemeinere Adressbefund wird nur zur Trennung von Mapping und Schleifengrenze angegeben:

- `0x469C0(S,f,b,a,k,L,A,W)` prueft signed `a+k` in `[0,L.N]`, `f+b` in `[0,S.N]` und
  `f+b <= W.N` (`0x46A0B..0x46A63`). Die Fehlerzweige `0x46C59`, `0x46C84`, `0x46CB2` fuehren zur Diagnose
  und zum Epilog, vor der Matrixschleife. Einzelne nichtnegative f/b/a/k werden dabei nicht jeweils separat
  abgesichert; unsere gueltige Domain fordert sie ausdruecklich sowie ueberlauffreie Summen/Adressarithmetik.
- Bei `b=0` wird der Loop an `0x46B38..0x46B3A` uebersprungen. Sonst erfolgen genau b Iterationen
  (`0x46C38/0x46C44`), World/Compositeziele jeweils `+64`, Bonequelle `+152`, Localquellpointer `+80`.
  Localquelle beginnt bei `L.array+80*f` (`0x46B26..0x46B2F`), **nicht bei 80*a**. a ist hier nur als
  Guardaddend belegt. Solange k>0 wird diese Localquelle benutzt, danach die Resttransformquelle des jeweiligen
  Bones bei Bone+8; k wird jede Iteration dekrementiert. Gueltige Quellen benoetigen deshalb auch unabhaengig vom
  Guard die Localindices `f .. f+min(b,k)-1`. Im Sample f=a=0 reduziert sich dies auf `[0,min(B,K))`.
- `0x47060(S,f,b,A,W)` liest beide Arrayzeiger und beginnt ebenfalls mit Ausgabeindex f und Boneindex f.
  Er prueft weder S.N noch W.N gegen den verlangten Bereich. `b==0` ueberspringt an `0x47161..0x47165` die
  Matrixschleife; sonst genau b Iterationen (`0x47220/0x47229`), beide Ziele `+64`, Bonequelle `+152`.
  Quelle ist durchgehend Bone+8. Negative b und ungueltige Bereiche sind ausserhalb unseres Vertrags,
  keine sicher abgefangenen Leerausgaben.

Fuer beide Worker gilt: Ausgabeindices sind fortlaufend `f+i`, `0 <= i < b`. Das Parentfeld bei Bone+4 waehlt
die **gelesene** Eltern-Worldmatrix (`World[parent]`); Sentinel -1 waehlt A. Es ist kein Outputindex-Mapping.
Vorbedingungen fuer als gueltig gelesene Ergebnisse: lebende passend dimensionierte W/L/S-Objekte und Bonearrays;
beide disjunkten World-/Compositearrays einschliesslich erforderlicher 16-Byte-Ausrichtung; initialisierte gueltige
Quelltransforms und A; gueltige Elternhierarchie. Eltern muessen root oder bereits initialisiert sein: bei f=0
typischerweise kleinere Indices, bei f>0 koennen dazu Worldmatrizen vor f gehoeren. Die monotone Schleife beweist
keine allgemeine Hierarchievaliditaet. Keine unerlaubten Aliase mit Quellen, Headern, Stack, Profiling-/Dispatch-
Zustand; keine konkurrierenden oder verschachtelten Aenderungen. Diese Bedingungen werden nicht durch einen
fremden Header oder Fingerprint erfuellt. Nullarrayzeiger und zu kleine Kapazitaet werden nicht allgemein abgefangen.

## Dispatch und vollstaendige Byteabdeckung je Iteration

Die vier Slots DLL `0x61A78/0x61A7C/0x61A80/0x61A84` enthalten in der Datei zunaechst die Initialisierungsthunks
`0x156E0/0x15C90/0x15CA0/0x15CB0`. Sie rufen `0x156F0`, danach denselben jetzt gesetzten Slot.
`0x156F0` waehlt anhand `0x47920` entweder Scalar- oder SSE-Kandidaten. Die folgende Aussage ist bedingt auf
diese bekannten aktiven Zielbindungen und deren unveraenderten Gebrauch; globale Unveraendertheit ist nicht bewiesen.

- Transformflags genau 0, Slot `0x61A78`: Scalar-Codeentry `0x15620`, SSE-Codeentry `0x15B00`.
  Argumente `(Parent,InverseBind,CompositeDst,WorldDst)`.
- Flags genau 1, Slot `0x61A7C`: Scalar `0x15650`, SSE `0x15970`.
  Argumente `(Position,Parent,InverseBind,CompositeDst,WorldDst)`.
- Sonstige Flags mit `(flags & 0x4)==0`, Slot `0x61A80`: Scalar `0x15680`, SSE `0x15750`.
  Argumente `(Transform+4,Transform+0x10,Parent,InverseBind,CompositeDst,WorldDst)`.
- Flags mit `(flags & 0x4)!=0`, Slot `0x61A84`: Scalar `0x156B0`, SSE `0x15C50`.
  Argumente `(Transform,Parent,InverseBind,CompositeDst,WorldDst)`.

Die letzten beiden Argumente sind also **Composite zuerst, World zuletzt**. Der World-Schreibvorgang geht dem
Composite-Schreibvorgang voraus; dieser benutzt die eben erzeugte Worldmatrix.
Dies sind acht gebundene Codeentry-Kandidaten; mehrere sind in der Datenbank keine eigenstaendigen Funktionen.

Byteabdeckung, getrennt von mathematischer Wertgueltigkeit:

- Scalar `0x15620` ruft den vollen 16-dword-Copy `0x15440` fuer World; `0x15650` nutzt `0x154B0`, der zuerst
  die Matrixkomponenten kopiert und die Translation ersetzt, insgesamt alle 16 dwords. `0x15680` -> `0x15570`
  -> `0x155D0`, `0x156B0` -> `0x155D0`: interne Transformbildung `0x1AC0`, danach `0x2FF60` mit World als Ziel.
  Alle vier rufen abschliessend `0x15600` -> `0x2FF60` mit Composite als Ziel.
- `0x2FF60` schreibt alle zwoelf affinen Ergebnis-floats und die vier restlichen dwords bei +0xC/+0x1C/+0x2C
  (null) sowie +0x3C (eins). Es bleiben keine vier Padding-/Matrixkomponenten unbeschrieben.
- SSE `0x15750` schreibt World durch vier 16-Byte-Stores bei `0x15815/0x1583F/0x15866/0x15899`, Composite
  bei `0x15950/0x15953/0x15957/0x1595B`, jeweils Zieloffsets 0/+16/+32/+48.
- SSE `0x15970` schreibt alle World-dwords durch Kopien und ersetzte Translation, Composite durch vier
  16-Byte-Stores `0x15AE8..0x15AF3`; `0x15B00` kopiert alle 16 World-dwords und schreibt Composite durch
  vier 16-Byte-Stores `0x15C36..0x15C41`. Keine bedingten Spruenge innerhalb dieser drei Kandidatenkoerper.
- `0x15C50` bildet intern die Transformmatrix ueber `0x1AC0`, ruft `0x2FF60` zuerst mit World, danach mit
  Composite als Ziel. Die interne Quelle ist fuer gueltige Eingaben als voll gebaute Matrix vorausgesetzt;
  daraus entsteht kein Beweis beliebiger korrupter Transformdaten oder beliebiger FP-Ausnahmebehandlung.

Damit sind unter diesen Voraussetzungen **beide** halboffenen Schreibbereiche
`[WorldBase+64*f, WorldBase+64*(f+b))` und `[CompositeBase+64*f, CompositeBase+64*(f+b))`
voll beschrieben, jeweils alle 16 float32-Komponenten pro Matrix. Im konkreten direkten Samplepfad f=0,b=B:
World `[0,64*B)` und Composite `[0,64*B)` relativ zum jeweiligen Array. Diese beiden Spans sind verschieden.
`B<N` laesst den Rest des jeweiligen N-Arrays durch diese Worker unbeschrieben; keine fruehere Initialisierung
oder Erhaltung dieses Rests wird daraus abgeleitet. `B=0` schreibt keine Matrix, auch wenn N>0 ist. Bei N=0
ist der gueltige vollstaendige Bereich leer; gleiche Arraygrenzzeiger erlauben keine Matrixlesung.

Fuer den direkt abgegrenzten Restzweig des Samples ist damit ein **bedingter End-to-End-Span** bei gueltigen
Rest-/Hierarchiequellen vorhanden. Fuer den Mehrkontrollzweig gilt die Storeabdeckung, doch die gueltige
LocalPose-Produktion durch `0x2840` ist zusaetzlich offen. Fuer `0x2460` fehlt bereits der Writervertrag.
Es gibt deshalb keinen unbedingten vollen Sample-Span allein aus HeaderN und Return `0x38E6DF`.

## Reproduktion und maschinenpruefbare Grenzen

[Verifier](../../tools/pose_sample_verify.py), [Manifest](../../tools/pose_sample_manifest.json),
[neun synthetische Tests](../../tools/test_pose_sample.py),
[read-only Exporter](../../ghidra_scripts/PoseSampleExtent.java).
Der neue Verifier verwendet den bestehenden dateilesenden PE-Reader aus `hpose_creation_verify.py` und
`pe_info.py`, laedt die Originalmodule nicht. Strikte JSON-/Duplikat-/Schema-/Digestgates pinnen den kompletten
abgenommenen Manifestinhalt: zwei Identitaeten/Basen, 33 Evidenzeintraege/46 Bytebereiche, fuenf IAT-Namen und
drei Exportbindungen. Diese Schranken pruefen Identitaet/Abdeckung, nicht die semantische Deutung.

Ausgefuehrt und bestanden: `python -I tools/test_pose_sample.py` und `python -O -I tools/test_pose_sample.py`
(je 9 Tests); beide enthalten echte CLI-Kindprozesse fuer Unknown-Build-Ablehnung normal **und explizit -O**.
Verifier gegen beide Originaldateien normal und mit `-O` bestanden; `game_executed=false`,
`unconditional_sample_initialized_span_proven=false`. Kein Gesamttest durch den Bearbeiter; Integration beim Parent.

Finale gemeinsame Exporte je Modul liegen nur lokal unter `build/pose-sample-extent/final-exe` und `final-dll`.
577 Exe-/1956 DLL-Zeilen einschliesslich drei Datenzeilen wurden gegen Originaldateibytes verglichen.
Identitaetsdateien enthalten Basis, SHA, Argumentbereiche und vorhandene Funktionsnamen/-groessen.
Finale Scriptquelle wurde nach Argument-/Budget-/vollstaendiger Read-/Write-Fehlerhaertung fuer beide Module erneut
mit Ghidra 12.1.4, JDK21, `-process <Modul> -readOnly -noanalysis -postScript PoseSampleExtent.java` ausgefuehrt.
Argumente nach dem lokalen Ausgabeordner (VAs, keine RVAs):

```text
Stronghold2.exe:
f:0078E0A0 f:0078E4D0 d:00900A98:4 d:00900B10:4

granny2.dll:
f:5004F6D0 f:5004F700 f:50002A70 f:500469C0 f:50047060 f:50002460
f:50002630 f:5001B540 f:5003A5D0 f:50002840 f:5002E9E0 f:500322D0 f:50032300
f:50015440 f:500154B0 f:50015570 f:500155D0 f:50015600 f:50001AC0 f:5002FF60
f:50030310 f:5002FD80 f:50047920 f:5004F4D0 f:50002620 f:5004F4B0 f:50002570
r:50015620:50015CBF d:50061A78:16
```

## Genau ein minimaler Folgebeweis

Die Spezialkante DLL `0x2C44 -> 0x2460` fuer eine gueltige erste Kontrolle mit Praedikat `0x1B540=true` binden,
wenn der naechste Knoten fehlt oder dessen Kontrolle das Praedikat nicht erfuellt:
welcher Descriptor `D=*(first.node+0x18)` liefert dort `*(D+0x10)`, mit Argumenten
`(first.node,B,A,W,0)`, und welche World-/Compositebytes schreibt **dieser eine** gebundene Callback?
Ohne eindeutige Bindung am Descriptor endet der Beweis an diesem RVAs-/Parameter-Tupel; keine automatische
Rekonstruktion aller Controls. Das ersetzt weder die separate LocalPose-Quellgueltigkeit des Mehrkontrollpfads
noch konkrete Allokationsgeneration/Leseintervall fuer einen spaeteren Observer.

## Integrationsabnahme der Projektleitung

Neun synthetische Tests sowie der Verifier mit beiden Originaldateien normal und mit `-O` erneut bestanden.
Ein unabhaengiger Audit-PE-Reader bestaetigt alle 46 Manifestbereiche und fuenf Import-/drei Exportbindungen;
die beiden Originaldateien haben weiter die oben festgehaltenen SHA-256. Unabhaengiger Review bestaetigt auch
die finalen 577 Exe-/1956 DLL-Bytezeilen sowie Worker-/Helperargumente und die acht Kandidatenbindungen.
Die Korrektur der Localquelle von vermutetem 80*a auf belegtes 80*f erfolgte vor Abnahme; am bekannten
Sample-Unterpfad sind beide Parameter null. Die Flagentscheidung ist exakt Maske `0x4`, nicht Bitindex 4.
Native Quellen, Hub und Observer sind unveraendert; kein neuer nativer oder real-DLL-Hostlauf in diesem Paket.
Integriert: `python -I tools/run_checks.py` bestanden, 15/15 spielfreie Pruefgruppen inklusive neuer Suite und
Dokumentationslint. `--audit`/`--e2e` nicht wiederholt: Hub-/Observercode ist unveraendert. Kein neuer GitHub-CI-Lauf.
