# Interner WorldPose-Bypass: lokale New-/Free-Zuordnung

> Kurzfassung: Im DLL-Kontext 0xE080 werden zwei NewWorldPose-Returns lokal gespeichert und spaeter aus denselben zwei Feldern an Free uebergeben. Das ist ein bedingter direkter Herkunftsbeleg, kein universeller Lebensdauer-/Nichtaliasbeweis. Eine konkrete offene Kante ist der Framekontext des indirekten Trackcallbacks 0xE30C. Ein bekannter direkter Contextcallee ist in diesem Build ein leerer Returnstub.

Datum 2026-10-18, Basis `49936a3`, F183–F185. [Vorab-Scope und Abnahme](../tasks/POSE_INTERNAL_PROVENANCE_2026-10-18.md).
Vorgaenger [Allocatorbindung](POSE_ALLOCATOR_BINDING_2026-10-18.md), F178–F182.
Keine Originalausfuehrung, Hooks, Aufnahme, Installation oder Livezugriffe. Getrennte Ghidra-Kopie readOnly/noanalysis.

## Identitaet und Aufruferkontext

Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, Basis `0x00400000`.
DLL SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`, Basis `0x50000000`.
Alle folgenden Adressen sind DLL-RVAs; F bezeichnet den waehrend dieses Calls stabilen EBP-Framebezug.

Export `_GrannyCalculateLODErrorValues@16` bei `0x4FF60` ruft `0xE080` an `0x4FF74`.
Ein zweiter gespeicherter Caller ist `0xE5A0 -> 0xE080` an `0xE5DF`; Export
`_GrannyCalculateLODErrorValuesAllBindings@16` bei `0x4FF80` erreicht `0xE5A0` an `0x4FF94`.
Ein weiterer Caller von `0xE5A0`, Kontext `0xE8E0`, wurde nur als Referenz vermerkt, nicht weiter verfolgt.
Die bekannte Referenzliste verwendet AddressContext mit dessen 12-Referenzen-Grenze, kein globaler Callerbeweis.

Die gepruefte Exe hat keine benannten Imports der beiden CalculateLODErrorValues-Exporte. Das schliesst
dynamische Aufloesung, andere Module oder interne Callketten nicht aus. Exportnamen ordnen den Kontext ein;
sie beweisen weder dessen Laufzeithaeufigkeit noch ein vollstaendiges Verstaendnis des LOD-Algorithmus.

## Zwei New-Aufrufe und ihre Ablage

Der Groessenspill bei `0xE0E7`, F-8, stammt aus `*(Parameter1+0x20)`; er wird im geprueften lokalen Koerper
nicht erneut direkt beschrieben. Das ist die Groessenquelle, hier nicht automatisch eine Skelett-/Bonezahl.

Die Schleife initialisiert ihren Byteindex an `0xE152` mit 0, laedt den Groessenspill fuer New an `0xE15D`,
ruft den bekannten Worker `0x46790` an `0xE165` und speichert EAX direkt danach an `0xE16A` nach
`F-0x44+Index`. Der Index wird bei `0xE16E` um 4 erhoeht; Vergleich mit 8 bei `0xE174`, signed-JL
bei `0xE177` zurueck nach `0xE154`. Bei normaler Ausfuehrung entstehen zwei **gespeicherte Returns** W0/W1
in F-0x44/F-0x40. Companion-Returns eines anderen New-Helfers liegen getrennt in F-0x4C/F-0x48.

Zwei Calls beweisen keine zwei erfolgreichen Allokationen. Nichtnull, gueltige Kapazitaet, zwei verschiedene
Generationen und eine vom Frame getrennte Reserve erfordern weiterhin den Allocatorvertrag aus F150/F178–F182.
Insbesondere duerfen Nullreturns oder ein inkompatibler Customallocator nicht als zwei lebende Posen etikettiert werden.

## Welche Werte Free erreichen

Cleanup initialisiert seinen Byteindex an `0xE546` mit 0. `0xE548` laedt EDX aus `F-0x44+Index`,
`0xE54C` uebergibt EDX an Free-Worker `0x467C0` bei `0xE54D`. Stride 4 bei `0xE55C`, Vergleich mit 8
bei `0xE562`, signed-JL `0xE565 -> 0xE548`. Der direkte lokale Wertfluss ist damit W0, dann W1.

Die Inventur aller direkten Frameziele findet fuer diese zwei Felder nur den Store `0xE16A`; die andere
indexierte New-Ablage trifft den getrennten Companionbereich. Weitere direkte W-Feldreads liegen an
`0xE273/0xE355/0xE358`. Keine direkt erkannte LEA gibt die Adressen der beiden W-Felder selbst weiter.
Naehe von New und Free allein waere kein Beleg; entscheidend sind dieselbe Speicherform und die Indexgrenzen.

Ein eigener lokaler CFG-Abgleich ueber alle 458 vorhandenen Instruktionsknoten bestaetigt: Der Countstore
dominiert New; New und anschliessender Spill dominieren den betrachteten Free-Call. Die lokale Cleanup-
Indexinitialisierung dominiert ihn ebenfalls. Verschiedene fruehe Returns verlassen den Kontext; sie sind
kein Nachweis eines Frees ohne New. Berechnungspfade koennen zum gemeinsamen Cleanup springen.
Diese CFG-Aussagen modellieren Calls als normal zurueckkehrend. Exceptions, Longjmp, fremde Framewrites,
ABI-Verletzungen oder freigegebene Referenten werden damit nicht ausgeschlossen.

**Herkunftsentscheid:** Unter erhaltenem Frame/Calling-Convention-Vertrag und ohne fremde Mutation der zwei
Spills stammt dieses Free-Argument aus den eigenen New-Returns des Kontextes, nicht aus einem direkten lokalen
Spill eines eingehenden Posearguments. Das beweist keine uneingeschraenkte Adressverschiedenheit zu H-Posen und
keine bis Free erhaltene Lebensdauer. Referenten-Aliase, unbemerkte Free/Reuse und beliebige Callee-Effekte sind separat.

## Konkrete Context-Escape-Grenze

Die beiden erkannten LEA-aus-Frame-Weitergaben sind `0xE2D7/0xE308`: jeweils Adresse F-0x80 als
**Argument 1** des bekannten direkten Helfers `0xE2DB -> 0x44DA0` bzw. des indirekten Trackcalls `0xE30C`.
Das ist nicht automatisch ein World-/Composite-Ausgabeziel; deren Rollen sind andere Argumente (F174).
Ein Abstand von 60 Bytes zwischen F-0x80 und W0 allein beweist deshalb weder Ueberschreiben noch Nichtalias.

Die bekannte direkte Contextkante `0x44DAB -> 0x2F5D0` endet in diesem gehashten Build unmittelbar:
`0x2F5D0` ist genau ein Returnbyte, ohne eigene Datenstores oder weitere Calls. Diese konkrete Weitergabe
schreibt den Framekontext nicht. Daraus folgt keine allgemeine Aussage fuer jede indirekte Samplerfunktion.

Bei `0xE30C` bleibt das Ziel aus Track+8 ohne gebundenen Context-Schreibvertrag. Diese Uebergabe ist die
konkrete offene Framealiasgrenze, zusaetzlich zu gueltigen Output-/Allocator-/ABI-Bedingungen. Es wurde kein
Callback gefunden, der tatsaechlich die W-Felder ueberschreibt; ein solcher Spielablauf wird nicht behauptet.
Der kleinste Folgebeweis ist die Contextbedeutung/-Schreibspanne dieser Kante, nicht die gesamte Trackmathematik.

## Ausfuehrbare Pruefung und Reproduktion

Der bestehende Verifier behaelt Schema 2 und alle 80 bisherigen Eintraege; fuenf neue Funktionen kommen hinzu.
85 Eintraege/98 Bereiche, sieben Exe-Imports/14 Exporte, zwoelf direkte Kanten; bisherige Allocator-/Heapgates
und Literalcensus bleiben erhalten. Ein begrenzter eigener ModRM/SIB-Decoder prueft die konkreten Frame-MOVs,
Register/Index/Displacement und den Free-Argumentpush. Zwei Loopgates pruefen Zero/Stride/Limit/signed-JL.
Das ist ein selektiver Datenflussanker, kein allgemeiner x86-Interpreter und kein Alias-/CFG-Vollstaendigkeitsbeweis.
Der semantische Koerper-/Pfadreview bleibt ein eigener Nachweisschritt.

```text
python -I tools/test_pose_sample.py
python -I tools/pose_sample_verify.py --exe <eigene-exe> --dll <eigene-dll>
```

Beide auch mit `-O`: 21 Verifiertests und Originaldatei-Gates bestanden. Neue Tests lehnen fehlende Kontext-/
Caller-/Stubbelege, falsche Framebasis/Index/Sign/Displacements, abgeschnittene Instruktionen, falschen
Argumentpush und veraenderte Loopinitialisierung/Schrittweite/Grenze/Rueckkante ab.
Unbenutzte Lesepufferbytes hinter einer dekodierten Instruktion sind keine Displacementbytes; der Test trennt das.

Getrennte Ghidra-Kopie, 12.1.4/JDK 21, readOnly/noanalysis. `PoseSampleExtent.java <output-dir>` mit VAs:

```text
f:5000E080 f:5004FF60 f:5004FF80 f:5000E5A0 f:50044DA0 f:5002F5D0
```

Kanonisch sechs Dateien/538 Bytezeilen unter lokal ignoriertem `build/pose-internal-provenance/canonical`;
44DA0 ist ein bytegleich wiederverwendeter Beleg, keine sechste neue Manifestfunktion.
`AddressContext.java <out> 5000E080 5000E5A0` liefert den begrenzten Callerkontext.
Manuelle Pfadpruefung: erst Indexschleifen/Spilladressen, dann alle Framedestinationen und -Adressweitergaben,
danach New-/Free-Argumente, dominierende Pfade und die konkrete Context-Weitergabe pruefen.

Unabhaengiger Pruefer bestaetigt kanonische Originalbytes, Argument-/Pfadgrenzen und neue Gates/Tests normal/-O.
Die Projektleitung bestaetigt zusaetzlich alle 98 Manifestbereiche und Exportbindungen mit dem Audit-PE-Reader.
Regulaere spielfreie Gesamtchecks: **16/16 bestanden**. Abschliessender unabhaengiger Dokumentreview ohne
sachlichen Blocker; Zahlen, Reproduktion und Aussagegrenzen stimmen. Keine neue Original-/DLL-Ausfuehrung,
kein nativer/Hub-Build und kein GitHub-CI-Lauf in diesem Baustein.

## Ergebnis und Nutzen

Dieser konkrete globale Export-Bypass ist jetzt als bedingter eigener New-/Free-Kontext eingegrenzt.
Er ist kein positiver Nachweis, dass eine eingehende ausgewaehlte H-Pose hier freigegeben wird. Die verbleibende
Unsicherheit ist als konkrete Contextkante statt pauschal als beliebiger unbekannter Heap lokalisiert.
Das hilft, spaetere Lebenszyklusbeobachtung auf relevante Pfade zu begrenzen; es autorisiert noch keine Livekopie.
Keine Originalfunktion ausgefuehrt, keine Aufnahme, kein Performancegewinn, kein Cache-/Skip-/Observerumbau.
Damit ist die vorab definierte Teilbeweis-Abnahme erfuellt: direkte Herkunft ist bedingt belegt und die konkrete
verbleibende Alias-/Weitergabekante reproduzierbar eingegrenzt. Eine vollstaendige Nichtmutation oder globale
selektive Lifecycleabdeckung wird ausdruecklich nicht als geschlossen abgenommen.

Genau ein Folgebeweis: an `0xE30C -> Track+8` die Verwendung von Argument 1 (F-0x80) und dessen moegliche
Schreib-/Weitergabespanne fuer einen konkret belegten Callbackkandidaten pruefen. Keine vollstaendige
Kurvenrekonstruktion; ein eng belegter unbekannter Contextwriter bleibt zulaessiges Ergebnis.
