# Wissensbaustein: Granny-World-Pose und Composite-Matrizen

> Kurzfassung: Pose-Speichervertrag der lokalen Granny-DLL statisch geprüft und an eigenen Daten ausgeführt. Ein eigener affiner Composite-Helfer besteht Differentialtests, ist für allgemeine Float-Werte nachweislich nicht bitgleich. Auditkorrekturen sind reproduziert; Spielaufnahmen, Hub und Installationen wurden nicht verändert.

Stand 2026-10-16. Ausgangspunkt SH2-Perf `e2e4c8b`, `main`, sauber, kein Remote;
Hub `32ebc38a05ea94cfc3fd831c1a12174b9a34f51c`, `perf-metrics`, sauber.
Keine REA-MCP-Werkzeuge in dieser Sitzung; Ghidra 12.1.4 tatsächlich auf einer eigenen
Projektkopie mit `-readOnly -noanalysis` ausgeführt. Automatische Funktionsnamen sind
Adressetiketten. Die 30 Byte-Fingerprints sind Identitätsprüfungen, keine 30 verstandenen Algorithmen.

## Identität und Belegklassen

- Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, Basis `0x00400000`.
- Granny SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`, Basis `0x50000000`, PE32/x86.
- Alle Granny-RVAs unten beziehen sich ausschließlich auf diese DLL. `VA = Basis + RVA`.
- **Binärbefund:** PE-Exporte, Wrapper, Speicherzugriffe und Aufrufstellen; keine SDK-Deklaration aus dem Internet.
- **Eigene echte DLL-Laufzeit:** isolierter Win32-Host, eigene Speicher-/Skelettdaten, keine Spielassets.
- **Historische Spielmessung:** A1/G1, nur über verifizierte Dateien und den reproduzierten Audit.
- **Testmodell:** neun Python-Audittests; kein ausgeführter Produktions-Hook und kein Ereignis-Replay.

Die heutigen Original-/TEST-Dateihashes stimmen. G1 bindet den damaligen geladenen
Granny-Dateihash weiterhin nicht kryptografisch. Unser Testhost prüft Dateihash vor
dem Laden sowie geladenen Pfad und dessen Dateihash. Das schließt die historische Lücke nicht rückwirkend.

## Auditkorrekturen, jetzt nachgeprüft und integriert

Kanonische Referenz: unabhängiger Audit vom 16.10.2026, `analysis/` des externen
Auditordners. [Reproduktionswerkzeug](../../tools/recheck_granny_audit.py) prüft dessen
Skript-/Referenzhashes und den Hub-Quellhash, kopiert nur benötigte Eingänge nach
`build/knowledge-pose/audit-recheck/` und führt sie dort aus. Die Referenz bleibt unverändert.

- A1 drei und G1 sieben manifestierte Dateien erneut hash-/größenverifiziert.
- 126.632 fehlende Aggregationen = 64.622 Uhr + 62.010 Sample; gespeicherte Schlüssel sind keine Population.
- 1.503 streng gefilterte Pausenreihen bestätigt, zusätzlich `clock_changed=clock_noprev=0`,
  `clock_min=clock_max`, `clock_calls=sample_calls`. Nur diese Zusatzprüfung rettet den konkreten Befund.
- `all_observed_same` ist allgemein kein Sample-zu-Sample-Uhrvergleich. Beide Gegenrichtungen reproduziert.
- Ein ausgelassenes Sample kann eine echte zweite Pose-Zuordnung verbergen. Null `ambiguous` ist kein Eindeutigkeitsbeweis.
- Metadaten minus Framezeilen: Uhr 372, Sample 187, Deform 25, Composite 25 = **609 Schlussaufrufe**.
  `frame_rows_dropped=0` erfasst diesen nicht geschriebenen Schlussrest nicht.
- Objektmarker am Aufruf und Framemarker am Frame-Ende unterscheiden sich an Übergängen;
  Lebenszeit-/letzte-Wert-Felder werden zusätzlich phasenübergreifend wiederholt.
- Alter nativer Beobachtertest benutzt eine Fake-DLL; seine Weiterleitungsprüfung beweist keine Neutralität im Spiel.
- Neun Simulationstests, sechs alte ABI-/Importprüfungen, Sample-Return `0x0038E6DF`
  und 17 direkte Exe-Calls erneut erfolgreich geprüft. Keine erneute vollständige EXP-006/007-Auswertung.

Ein Snapshot nach den ersten eigenen neuen Dateien meldete erwartungsgemäß einen
geänderten SH2-Perf-Git-Status; die damals 191 fingerprinteten Bestandsdateien waren
noch alle unverändert. Der gekapselte Reproduktionslauf vergleicht seinen eigenen
Vorher-/Nachherstand erfolgreich. Spätere eigene Dokumentationsänderungen sind beabsichtigt.

Abschlussvergleich gegen den Sitzungseingang: 180 der 191 fingerprinteten Bestandsdateien
bytegleich; die elf Änderungen betreffen ausschließlich die hier beabsichtigte eigene
Dokumentation. Unverändert darunter alle 64 erfassten Hub-Dateien, 15 ursprüngliche
Ghidra-Dateien, zwei Original- und sechs TEST-Kerndateien sowie die erfassten Aufnahmen/
Annotationen. Das ist kein Vollhash aller installierten Assets. Die vier benutzten
Audit-Referenzdateien wurden vor/nach ihrer Reproduktion separat hashgeprüft.

## Verifizierter Speichervertrag

Ein World-Pose-Objekt enthält im geprüften x86-Build an `+0` einen int32-Knochenzähler N,
an `+4` den World-Matrixzeiger, an `+8` den Composite-Matrixzeiger. Die Headergröße ist
12 Bytes; die folgenden vier Bytes sind Ausrichtungspadding. Jede Matrix umfasst
16 float32-Werte, 64 Bytes; beide Arrays sind bei den geprüften Konstruktoren 16-Byte-ausgerichtet.

- `GetWorldPoseBoneCount`, RVA `0x4F9F0` → Worker `0x2E9E0`, liest `+0`.
- `GetWorldPose4x4Array`, `0x52B90` → `0x322D0`, liest `+4`.
- `GetWorldPoseComposite4x4Array`, `0x52BB0` → `0x32300`, liest `+8`.
- Die Getter liefern geliehene Zeiger, keine Kopien. Exportnamen teilen sich Adressen mit
  anders benannten Exporten; die Ghidra-Labels allein sind deshalb keine Semantikbelege.
- Einzelgetter `0x54450` / `0x54470` → `0x468C0` / `0x468E0`: 64-Byte-Schritt,
  null bei `index >= N`. **Statisch fehlt eine Untergrenzenprüfung**: negative Indizes
  sind kein gültiger Lesebereich. Der Host ruft sie nicht mit negativen Indizes auf.
- `GetResultingWorldPoseSize`, `0x54420` → `0x467E0`, und der Layouthelfer `0x46800`:
  für den geprüften Bereich `16 + 128*N` Bytes; World bei Basis+16,
  Composite bei Basis+16+64*N. Speicher ist für zwei volle Arrays nötig, nicht nur `N*64`.
- `NewWorldPoseInPlace`, `0x54430` → `0x46840`, übernimmt gültigen ausreichend großen
  eigenen Speicher ohne Größenargument. Es initialisiert Header/Zeiger/Zähler;
  Padding und Matrixdaten bleiben im Test unverändert. Allokiert bedeutet nicht berechnet.
- `NewWorldPose`, `0x54400` → `0x46790`, benutzt den Bibliotheksallokator;
  `FreeWorldPose`, `0x54410` → `0x467C0`, dessen Freigabepfad. Nur solche eigenen
  Bibliotheksallokationen wurden mit `FreeWorldPose` freigegeben.
- In-place-Speicher bleibt Eigentum des Hosts und wird vom Host freigegeben. Nach jeder
  zugehörigen Freigabe gelten sämtliche Getterzeiger als ungültig; keine Zugriffe nach Free.
- Die Layout-/Allokatorhelfer benutzen globalen Scratch-Zustand und konfigurierbare
  Allokatorzeiger. Reentranz/Threadsicherheit oder benutzerdefinierte Allokatoren sind nicht geprüft.

Nativ geprüft: N=0,1,2,3,15,16,17,63,64,65,217,257,1024,4096 plus 128 deterministische
Fälle in 1..257. Bei N=0 zeigen beide Arrays auf dieselbe leere Grenze; keine Matrix
darf dort gelesen werden. Keine Negativ-/Overflow-/OOM-/Fehlzeigerexperimente am Original.
Aus N allein folgt bei einem fremden oder korrupten Spielzeiger noch keine bestätigte Allokationsgrenze.

## Abgegrenzter Helfer und eigener Nachbau

Original: `GrannyBuildCompositeFromWorldPose(skeleton, first, count, pose)`,
Export-RVA `0x545E0`, `__stdcall`, `ret 16`; Worker `0x477D0`.
Dieser liest den Bonearrayzeiger aus `skeleton+8`, Schrittweite 152 Bytes,
jeweils die 64-Byte-Inverse-Bind-Matrix bei Bone+76. Über `0x15600` wird der
affine x87-Matrixhelfer `0x2FF60` aufgerufen. Das ist eine belegte Projektion
der gelesenen Skelettfelder, keine vollständige Granny-SDK-Typdefinition.

Eingangsbereich des Hosts: lebende disjunkte Puffer; 1 <= N <= 257;
0 <= first <= N; 0 <= count <= N-first; entsprechend viele eigene Bone-Datensätze.
Finite kanonisch affine Matrizen mit letzter Spalte `(0,0,0,1)`, freie Komponenten in [-8,8].
Die Skelett-/Posegrößen sind gleich. Kein Alias zwischen Quellmatrizen und Zielarray.
Nichtaffine Matrizen, NaN/Inf, Subnormalspezialfälle, übergroße Werte und ungültige Bereiche
sind außerhalb des nachgewiesenen Vertrags; nicht mit Assertions der DLL experimentiert.

Die mathematische Operation in Zeilenvektorkonvention lautet pro ausgewähltem Knochen:
`Composite = InverseBind * World`. Für die Translation wird die World-Translation addiert.
Die letzte Spalte des Ergebnisses ist kanonisch. Ein zusätzlicher unabhängiger Test
„Translation x=1, danach Skalierung x=2“ erwartet Translation 2 und trennt die Multiplikationsreihenfolge.

[Eigener Helfer](../../tools/granny_pose/pose_math.cpp): direkte affine Multiplikation in
C++-Schleifen, keine Übertragung der originalen x87-Auswertungsreihenfolge. Keine Allokation,
globalen Variablen oder Originalaufrufe. Der getestete Build benutzt scalar SSE `mulss`/`addss`;
Original `0x2FF60` benutzt x87. Das Original schreibt zusätzlich interne Profilingzähler/-zeiten;
diese Nebenwirkungen bildet der mathematische Helfer ausdrücklich nicht nach.

Der Originalaufruf erhält vollständige eigene gültige Daten. Der Host prüft mit Schutzseiten
und Canaries: Header, World-Array, Bone-Datensätze sowie nicht ausgewählte Composite-Matrizen
bleiben unverändert. Getestet werden auch leere Bereiche, Ende=N, Einzelelement und Teilbereiche.
Die Speicherbeobachtung deckt eigene Puffer ab, nicht beliebige globale Zustandsänderungen der DLL.

## Ergebnisse und vorab festgelegte Gleichheit

[Maschinenlesbares Ergebnis samt Gegenbeispiel und Quellhashes](POSE_CONTRACT_RESULTS.json).

- 142 Layout-/Allokationsfälle; 1.620 Differentialfälle, 14.923 ausgewählte Knochen,
  238.768 verglichene Komponenten, **0 Fehler** nach dem vorab festgelegten Kriterium.
- Je 540 Fälle: Identität, dyadische Werte (Vielfache 1/256 in [-8,8]), allgemeine float32-Werte in [-8,8].
- Im Identitäts-/dyadischen Korpus exakte Resultate, vorab unter Gleichsetzung von +0/-0 gefordert;
  tatsächlich wurden insgesamt null Vorzeichenunterschiede bei Null beobachtet.
- Allgemeiner Korpus: feste Schranke `abs(original-own) <= 8*FLT_EPSILON*max(1,sum_abs_terms)`;
  Summe enthält die drei Produktbeträge und bei Translation den zusätzlichen World-Term.
  Keine nachträglich gewählte Toleranz. Kein Beweis einer solchen Schranke für ungetestete Werte.
- 443 Fälle haben von null verschiedene Rundungsunterschiede; 27.497 Komponenten unterscheiden sich.
  Maximale absolute Abweichung `1.52587890625e-5`, maximale skalierte Abweichung `1.6808682276164078e-7`.
- Erstes Gegenbeispiel: Komponente 6, Original `-31.912008285522461`, eigener Helfer `-31.912010192871094`.
  Ein exaktes rationales Orakel bestätigt beim gespeicherten Beispiel den Originalwert als nächstes float32.
  Zusätzliche Zwischenrundungen/andere Additionsreihenfolge erklären die Grenze des eigenen Float-Helfers.
- FP-Steuermodi bleiben erhalten; MXCSR wechselt von 8064 auf 8096 (Inexact-Statusflag).
  Gleichheit aller IEEE-Statusflags wird deshalb ausdrücklich nicht behauptet.
- Zwei zusätzliche Integrationstests bestehen: rationales Rundungsorakel sowie Ablehnung einer
  manipulierten eigenen DLL-Kopie an Python- und nativer Hashschranke vor dem Laden.

**Urteil:** begrenzte Bibliothekslogik verständlich und selbst ausführbar nachgebaut;
keine universelle Bitgleichheit, vollständige Nebenwirkungsgleichheit oder Austauschfreigabe.
Keine Stronghold-Kampf-/KI-/Simulationslogik nachgebaut, kein Performancegewinn gemessen.

## Verbindung zum Spiel und verbleibende Grenze

Der unabhängig geprüfte Exe-Pfad RVA `0x38E4D0` wählt H aus 20-Byte-Datensätzen:
H+0 Instanz, H+4 World-Pose, H+8 Local-Pose. Uhr wird gesetzt, Sample kehrt bei
`0x38E6DF` zurück; bei `0x38E6E5` folgt `FreeCompletedModelControls`, später Rekursion.
Die Composite-Getterausgabe geht bei `0x38CA8C` / `0x36B75A` an die Deformation.

Granny-Sample `0x4F6D0` → `0x4F700` → `0x2A70` erreicht abhängig vom Kontrollpfad
u.a. World-Build-Worker `0x469C0` oder Restpfad `0x47060`. Diese benutzen die beiden
Arraygetter; die angeforderte Knochenzahl und die tatsächliche Posekapazität sind
verschiedene Größen. Dies ist statischer Datenfluss, kein ausgeführter echter Modell-Sampletest.
Unser Composite-Test beweist weder welche Matrizen jedes G1-Sample vollständig schreibt,
noch dass ein Sample das Original exakt über den hier getesteten Exportweg durchläuft.

Im Spiel sind konkreter Besitzer, Lifetime-/Reuse-Grenzen und eventuelle Teilbereichsnutzung
der H-Poseobjekte noch nicht vollständig aufgelöst. Die DLL-Lifetime im eigenen Host
ersetzt diesen Beleg nicht. Auch vollständige Outputgleichheit würde die Local-Pose-/Control-
Seiteneffekte und `FreeCompletedModelControls` nicht abdecken.

## Reproduktion

Aus SH2-Perf, ohne Spielstart oder Installation:

```powershell
python -I tools/granny_pose.py --verify-only
python -I tools/granny_pose.py
python -I tools/test_granny_pose.py
python -I tools/recheck_granny_audit.py --audit-root <lokaler-audit-ordner>
python -I tools/lint_docs.py
```

Native Voraussetzungen: MSVC 2022, CMake, Win32; keine Downloads oder SDK-Beschaffung.
Der Runner findet CMake auf PATH oder über den bestehenden Hub-Buildcache, baut getrennt
unter `build/knowledge-pose/native` mit `/fp:strict /W4 /WX`. Testhost und Python-Runner
verweigern eine andere DLL-Identität. Maschinenberichte und sämtliche Binärlistings bleiben lokal.
Eigene Quellen, dieser Bericht und das abgeleitete Ergebnis sind versionierbar; keine DLL/Assets/Disassembly im Git.

Für erneute Ghidra-Prüfung [PoseContract.java](../../ghidra_scripts/PoseContract.java)
auf eigener Kopie mit `-readOnly -noanalysis` verwenden. Argumente: Ausgabeordner,
Tiefe, VAs; die geprüften VAs ergeben sich aus Basis plus RVAs der
[Fingerprints](../../tools/granny_pose/verified_functions.json). Die Rohlistings dieser Sitzung
liegen in `build/knowledge-pose/binary` und `details`; kein geteiltes Ghidra-Projekt beschrieben.

## Genau ein priorisierter nächster Versuch

**H-Pose-Lebenszyklus in der Exe nachweisen, ausschließlich statisch mit vorhandenen Daten.**
Ausgehend von den IAT-Verwendungen von `NewWorldPose`, `FreeWorldPose`, `NewLocalPose`,
`FreeLocalPose` und `InstantiateModel` die Konstruktion/Übergabe/Freigabe genau der
20-Byte-H-Datensätze bis `O+0x18/+0x1c/+0x4c` verfolgen. Keine neue Aufnahme und
kein paralleler Beobachterumbau. Erwarteter Wert: belastbare Eigentums-/Kapazitätsgrenzen
für einen späteren kleinen Ergebnisvergleich, statt fremden Zeigern bloß wegen eines N-Felds zu vertrauen.

Gültigkeit: gleicher Exe-/DLL-Hash; alle behaupteten Store-/Free-/Übergabekanten mit RVA
und maschinenprüfbaren Bytes; Größenherkunft und Restlücken separat; keine Figurenzuordnung aus Namen.
Ergebnisentscheidungen: (a) eindeutige lokale Allokation/Freigabe samt Kapazität belegt →
Vertrag für diesen Pfad vervollständigen; (b) geteilter/recycelter Besitzer belegt →
Vergleiche benötigen dessen eigene Generation; (c) indirekte Übergabe nicht auflösbar →
gezielte offene Kante dokumentieren, keine Lifetime-Sicherheit behaupten.
Auch bei (a) ist noch kein installierbarer Ergebnisbeobachter fertig oder freigegeben.
