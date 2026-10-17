# Pose-Spezialkante: Descriptorherkunft und ein begrenzter Writerpfad

> Kurzfassung: Ein Animations-Builderpfad setzt node+0x18 auf einen Descriptor mit Callbackentry RVA 0x1C780. Dessen begrenzter allgemeiner Loop kann ueber zwei bekannte Helfer volle World-/Composite-Matrizen fuer `[0,C)` schreiben, C=min(B,BindingCount). Das gilt unter expliziter Pfadauswahl, gueltigen Quellen und bekannter Dispatchbindung; es ist kein universeller Samplevertrag. Ein weiterer Track-Callback und eine vorgelagerte erste-Bone-Schnellroute bleiben getrennte Grenzen.

Stand 2026-10-17, Forschungsbasis `8200cde`, zu Beginn sauber. Keine Originalausfuehrung, Livebeobachtung,
Installation oder DB-Mutation; lokaler Integrationscommit durch die Projektleitung, kein Push. Ghidra 12.1.4/JDK21 ausschliesslich auf der getrennten Kopie,
`-readOnly -noanalysis`. Vorheriger [Samplevertrag](POSE_SAMPLE_EXTENT_2026-10-17.md) bleibt mit seinen datierten
Zaehlern unveraendert. Automatische Funktionsnamen und Dateizeiger sind keine dynamische Typ-/Zielgarantie.

## Identitaet und Scope

- Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, Basis `0x00400000`.
- DLL SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`, Basis `0x50000000`.
- Folgende Code-/Datenadressen sind **DLL-RVAs**, ausser ausdruecklich als Exe oder VA bezeichnet.
  W ist das WorldPose-Objekt, B der bereits im Sample gegen S.N geklemmte nichtnegative Wunschzaehler.
- Die Spezialkante `0x2C44 -> 0x2460` benutzt den ersten Listenknoten n. Vorbedingung des Zweigs:
  `0x1B540(*(n+0))` liefert true, und entweder `*(n+0x14)==head` oder das Praedikat fuer die Kontrolle des
  naechsten Knotens ist false. Das Ende ist ein **Sentinelvergleich**, kein behaupteter NULL-Knoten.
- Kontrolle `c=*(n+0)`, Modellinstanz `I=*(n+0xC)`, Descriptor `D=*(n+0x18)` und AnimationBinding
  `AB=*(n+0x1C)` sind verschiedene Referenten. `0x2460` liest `*(D+0x10)` und springt bei nonnull dorthin
  mit erhaltenen Argumenten `(n,B,A,W,0)`. Ein lokales Nullcallback-RET ist weiterhin kein gueltiges
  End-to-End-Gegenbeispiel und kein Sample-Erfolgssignal.

## Ein konkret belegter Descriptorproducer

`0x23B0(D,c,I,order,init)` fordert einen Knoten an; nur sein nichtnull-Allokationspfad ist hier gebunden.
Store `0x23D9` setzt n+0x18 auf D. `0x22C0` verbindet n mit der Kontrolle und der Modellliste:
n+0 = c (`0x22D0`), n+0xC = I (`0x22F7`), dazu die zwei getrennten Linkpaare. `order` steuert die Einordnung.
Ob dieser dynamische Knoten spaeter der erste ausgewaehlte Sampleknoten ist, bleibt eine Bedingung.
Anschliessend ruft `0x23F2` den optionalen Initializer `*(D+8)` mit `(n,init)` auf.

Der Export `GrannyPlayControlledAnimation` bei `0x50F70` -> `0x1D040` erreicht auf einem erfolgreichen
Builderpfad `0x1D2B0`; dessen Aufruf `0x1D40A` gibt D=`0x61D58` an `0x23B0`.
Der Exportname `GrannyEndControlledAnimation` bei `0x50FD0` bezeichnet hier denselben Builderabschlussworker;
aus dem Namen wird kein Beenden laufender Animationen behauptet.
Die Exe importiert PlayControlledAnimation an IAT-RVA `0x500AD4`; das beweist Relevanz des Pfads, keine
vollstaendige dynamische H-/Kontrollherkunft jedes Sampleaufrufs.

Im Originaldateiinhalt ist `*(0x61D58+8)=VA 0x5001C400` und
`*(0x61D58+0x10)=VA 0x5001C780`. Der Initializer `0x1C400` speichert direkt n+0x1C/+0x20/+0x24/+0x28,
darunter AB und weitere Quell-/Modusparameter. Kein direkter Store auf n+0x18 wurde in seinem Koerper gefunden.
Er ruft jedoch `0xDCF0` oder `0xD0D0` mit aus init gewonnenen Daten auf; n ist zuvor bereits verlinkt.
Diese eng inventarisierten Calls sind **keine** globale Alias-/Unveraendertheitsgarantie. Spaetere Erhaltung
von n, D, Tabelleninhalt und AB bis zum Sample ist nicht universell bewiesen.

Ein zweiter bekannter Producer ist nur zur Abgrenzung inventarisiert: `GrannyPlayControlledPose` bei `0x51130`
-> `0x1D980`, Aufruf `0x1D9C6`, D=`0x61ED0`, dessen +8/+0x10 in der Datei auf `0x1D7C0`/`0x1D8C0` zeigen.
Dieser andere Callback wurde nicht semantisch verfolgt. Zwei gefundene Producer sind keine vollstaendige
Menge aller Descriptor-/Controltypen. Der folgende Vertrag gilt ausschliesslich bei tatsaechlich aktivem
Callbackentry `0x1C780`, insbesondere nicht automatisch bei jedem Dateitabellenkandidaten.

## Callback 0x1C780: Count und Ausgabeadressen

Der Codeentry ist in dieser Ghidra-Datenbank kein eigener Funktionsdatensatz. Der begrenzt exportierte
Instruktionsbereich `0x1C780..0x1CA40` endet an seinem RET; spaetere Funktionslabels begruenden diese Grenze
nicht allein. Die Stores im Epilog gehen an den Profilingkontext, nicht direkt an W-Arrays.
Keine universelle Aliasfreiheit dieses Kontexts wird daraus gefolgert.

Der Callback liest W+4/W+8 direkt als World-/Compositebase. Aus `AB=*(n+0x1C)` kommen
`T=*(AB+0x20)` und `TrackBase=*(AB+0x24)`; signed Vergleich `0x1C88E/0x1C898` setzt fuer gueltige
nichtnegative B/T den effektiven Zaehler **C=min(B,T)**. Es gibt hier keinen entsprechenden Vergleich gegen
WorldPoseHeaderN. Eine gueltige Kapazitaet fuer C und lesbare Quellen muessen separat bestehen.

BoneBase kommt aus der Feldkette `n+0xC -> I+0 -> M+4 -> S+8`.
Boneindex i, Trackrecordindex i und Ausgabeindex i laufen fortlaufend ab null; Bone-/Trackstride sind 152/88 Bytes.
Das Bone-Parentfeld bei Bone+4 steuert die **gelesene** Elternmatrix: -1 -> A, sonst World[parent].
Es ist kein Remapping des Zielindex. InverseBindquelle ist Bone+0x4C, Bone-Resttransformquelle Bone+8.
Die Zielzeiger sind WorldBase+64*i und CompositeBase+64*i. Der vorherige Samplezaehler B, BindingCount T,
WorldPoseHeaderN und tatsaechlicher Schreibindex bleiben verschiedene Groessen.

## Begrenzter positiver allgemeiner Looppfad

Die erste-Bone-Schnellroute wird sicher umgangen, wenn `*(n+0x20)!=2`.
Alternativ umgeht `*(TrackBase+4)==null` diese Route, verlangt aber bereits einen gueltig lesbaren ersten
Trackrecord, auch wenn C=0 ist. Es handelt sich um einen **exakten Vergleich mit 2**, keinen Maskentest.
Nach diesem Bypass beginnt der allgemeine Loop mit i=0; `0x1C8FC/0x1C8FE` verlaesst ihn bei i>=C vor
dem ersten Matrixwriter. Fuer C>0 lautet der hier positiv abgegrenzte Pfad: **jede** Iteration waehlt einen
der beiden direkten Helfer, keine Iteration den offenen Trackcallback.

- Erster x87-Vergleich an `0x1C91A` vergleicht den bei `0x1C913` geladenen lokalen Float mit Track+0x10.
  Bei x87-Statusbit C0=0 wird die Verzweigung `0x1C922` nicht genommen und `0x44DA0` an `0x1C948` aufgerufen.
- Andernfalls folgt der zweite Vergleich an `0x1C953`, dessen Floatquelle bei `0x1C94F` geladen wird,
  ebenfalls gegen Track+0x10. Bei x87-Statusbit C0=0 wird `0x1C95D` nicht genommen und `0x44DE0` an `0x1C995` aufgerufen.
- Wenn auch diese Bedingung nicht gilt, folgt die separate offene Kante `0x1C9C1 -> *(Track+8)`.
  Die beiden Vergleichsfloats werden hier nicht semantisch als voll rekonstruierte Animations-/LOD-Groessen
  bezeichnet. Der Vertrag benennt die konkreten Branchbedingungen; gueltige finite Quellwerte bleiben Voraussetzung.

Gemeinsame gebundene Argumente beider direkten Helfer: arg3=Trackrecord, arg5=Bone+0x4C,
arg6=Parentmatrix, arg7=Worldziel, arg8=Compositeziel. Ihre weiteren Transform-/Samplingquellen bleiben gueltige
Eingangsbedingungen. `0x44DA0` ruft den bekannten Slot `0x61A84` an `0x44DC8` mit
`(Track+0x14,Parent,InverseBind,Compositeziel,Worldziel)`.
`0x44DE0` benutzt interne Transformproduktion ueber `0x44940`/`0x1690` und ruft denselben Slot an
`0x44E3F` mit `(interneTransformmatrix,Parent,InverseBind,Compositeziel,Worldziel)`.
Hier wird weder die gesamte Kurvenmathematik noch die Gueltigkeit beliebiger Trackdaten rekonstruiert.

Der bereits [gepruefte Slotvertrag](POSE_SAMPLE_EXTENT_2026-10-17.md) fuer `0x61A84` bindet Scalar `0x156B0`
oder SSE `0x15C50`: jeweils volle 64 Bytes World und danach volle 64 Bytes Composite, einschliesslich aller vier
affinen Restkomponenten. Das ist keine blosse Zwoelf-float-Teilabdeckung.
Unter diesen aktiven bekannten Slotzielen, gueltigen Quellen, Kapazitaet und normal beendeten Helferaufrufen
schreibt daher jede Iteration beide kompletten Matrixziele. Loopende `0x1C9CB..0x1C9DF` erhoeht Bone um152,
World/Composite jeweils um64, Track um88 und i um1; Ruecksprung solange i!=C.

**Ergebnis fuer diesen selektierten Callbackpfad:** World `[WorldBase,WorldBase+64*C)` und Composite
`[CompositeBase,CompositeBase+64*C)` sind voll beschrieben. Fuer C=0 ist dieser Matrixschreibbereich leer,
bei dem strengeren Bypass `n+0x20!=2` ohne vorangehende Track0-Matrixroute. Vorgelagerte gueltige Struktur-/
Binding-/Bonearray-Lesbarkeit ist weiterhin erforderlich. Bei C<B ist `[C,B)` von diesem Loop unbeschrieben;
eine fruehere Initialisierung wird nicht angenommen. Der Loop schreibt keine HeaderN-grosse Ergaenzung.

## Schnellroute und offene Trackkante

Bei `n+0x20==2` und nichtnull Track0+4 liegt die erste-Bone-Schnellroute **vor** dem allgemeinen Countguard.
Sie waehlt Parent ueber Bone0+4, ruft `0x44F30`, das konstant VA `0x50044F40` liefert, und danach diesen
Codeentry an `0x1C8DB`. Anschliessend beginnt der allgemeine Loop mit i=1.
Der exportierte kleine Kandidat `0x44F40..0x4501A` enthaelt drei Quellzweige und Weitergaben an die bekannten
Slots `0x61A78/0x61A84`; seine vollstaendige Quell-/Ausgabeinitialisierung wird hier nicht positiv abgenommen.
Der obige volle Span ist deshalb ausdruecklich auf den Bypasspfad beschraenkt.
**Der allgemeine Schleifenabbruch allein beweist kein NoWrite bei C=0.** Dies ist eine Beweisgrenze,
kein behauptetes gueltiges C=0-Schreibgegenbeispiel: Erreichbarkeit und Quellgueltigkeit muessen auch mit dem
vorgelagerten `0x1B540=true` und den Spezialzweigbedingungen zusammengesetzt werden.

Die groesste verbleibende konkrete Writergrenze ist `0x1C9C1 -> *(TrackBase+88*i+8)` aus
`AB=*(n+0x1C)`, `TrackBase=*(AB+0x24)`, mit den oben gebundenen Bone-/Parent-/Outputargumenten.
Dieser Zeiger wird nicht allein aus einem Exportnamen oder der Descriptor-Dateitabelle auf einen Writer
geschlossen. Seine Produktions-/Zielbindung wurde nicht weiter verfolgt. Keine automatische Rekursion durch
saemtliche Track-/Kurventypen. Ein anderer Descriptor bleibt ebenfalls ausserhalb dieses Callbackvertrags.

## Gueltigkeitsbedingungen fuer eine spaetere Lesung

Erforderlich sind dieselbe lebende Allokationsgeneration und ausreichende disjunkte World-/Compositearrays,
passende Ausrichtung, gueltige Bone-/Track-/Bindingquellen fuer die ausgefuehrten Pfade, gueltige A-/Parentmatrizen
und Elternreihenfolge sowie aktive bekannte Dispatchziele. Ein Parent muss root oder schon initialisiert sein;
der fortlaufende Zielindex alleine beweist dies nicht. Unerlaubte Aliase mit Headern, Stack, Quellen oder globalem
Profiling-/Dispatchzustand und konkurrierende/verschachtelte Aenderungen sind ausgeschlossen.
Der Nachweis der Erhaltung von n/D/AB und der Lebensdauer/Leseintervalle ist eine eigene Bedingung.
Vollstaendige Zielstores sind kein Nachweis semantisch gueltiger Werte bei unbewiesenen Quellen.
Keine vollstaendige Sample-/Engine-/Nebenwirkungsgleichheit, kein universeller HeaderN-Lesebereich.

## Reproduktion und Tests

Der **bestehende** [Verifier](../../tools/pose_sample_verify.py),
[Manifest](../../tools/pose_sample_manifest.json) und [Tests](../../tools/test_pose_sample.py) wurden erweitert;
kein zweiter Verifier. Schema 2 behaelt alle vorherigen 33 Eintraege/46 Bereiche und ergaenzt 21 Eintraege/21 Bereiche:
insgesamt 54 Eintraege/67 Bereiche, sechs Imports und sechs Exportbindungen. Der alte Evidenzstand bleibt datiert.
Strikte Schema-/Duplikat-/Digest-/Bytegates pinnen auch beide Descriptorbereiche, Nodeproducer, Initializer,
Callbackrange und direkte Helfer. Das beweist Byteidentitaet und Abdeckung, nicht die semantische Deutung.

Bestanden: `python -I tools/test_pose_sample.py` und `python -O -I tools/test_pose_sample.py`, jeweils 12 Tests;
darunter neue Ablehnung fehlender Descriptor-/Callbackbelege, manipulierter Tabellendigests und Callbackextent/
Schema1. Unknown-Build-CLI-Kindprozesse werden weiterhin normal und mit **explizitem -O** gestartet.
`pose_sample_verify.py --exe <Originalexe> --dll <Originaldll>` normal und mit `-O` bestanden;
`game_executed=false`, `unconditional_sample_initialized_span_proven=false` bleibt bestehen.
Keine Gesamtchecks durch den Bearbeiter, keine neuen nativen oder real-DLL-Ausfuehrungstests.

Finale gemeinsame Exporte beider Module mit unveraenderter finaler Quelle
[PoseSampleExtent.java](../../ghidra_scripts/PoseSampleExtent.java), Ghidra `-readOnly -noanalysis`, liegen
ignoriert unter `build/pose-special-callback/final-exe` und `final-dll`. 578 Exe-/2886 DLL-Zeilen einschliesslich
sechs Datenzeilen sind gegen Originaldateibytes verglichen. Identitaetsdateien protokollieren SHA/Basis/Argumente.
Vollstaendige Argumente nach dem lokalen Ausgabeordner (hier **VAs**):

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
```

Einzelne Codeentrys ohne Functionlabel sind durch eng begrenzte vorhandene Instruktionsranges exportiert;
keine Disassemblierung, Funktionsanlage oder Analyse in der Datenbank. Der unabhängige Reviewer hat keinen
Zugriff auf die Ghidra-Kopie und prueft Exporte/Originaldateibytes und die strukturierten Bindungen separat.

## Integrationsabnahme und genau eine Folgeprioritaet

Unabhaengiger Freeze-Review ohne offene Blocker: Descriptor-/Producerbindung, exakter Enumvergleich, Count,
Zielargumente, Strides und Wiederverwendung des alten Kernelvertrags getrennt geprueft. Alle 578/2886 Bytezeilen
stimmen. Parent bestaetigt zusaetzlich mit unabhaengigem Audit-PE-Reader alle 67 Manifestbereiche und sechs
Import-/sechs Exportbindungen; Originalfile-SHA bleiben unveraendert. Originalverifier normal/-O und die neue
12-Test-Suite mit `-O` erneut bestanden. Keine neue Originalausfuehrung.
`python -I tools/run_checks.py` integriert bestanden: 15/15 spielfreie Pruefgruppen inklusive der 12 neuen/alten
Sample-Tests und Dokumentationslint. `--audit`/`--e2e` nicht wiederholt, weil Hub-/Observercode unveraendert ist.
Kein neuer nativer Hostlauf oder GitHub-CI-Lauf; bereits vorhandene Resultate bleiben datiert.

Projektentscheidung: als Naechstes den bereits gebundenen kleinen Schnellweg `0x1C8DB -> 0x44F40` pruefen.
Seine drei Quellzweige und bekannten Slotweitergaben versprechen einen engeren Folgebeweis als eine sofortige
Rekonstruktion saemtlicher indirekter Tracksampler. Zu klaeren sind die volle erste Matrixausgabe, konkrete
Quellbedingungen und das Zusammenspiel mit i=1/C des anschliessenden Loops. Kein gueltiges C=0-Gegenbeispiel
allein aus lokalen Spruengen ableiten. Track+8 und reale Generation/Leseintervall bleiben gesondert offen.
