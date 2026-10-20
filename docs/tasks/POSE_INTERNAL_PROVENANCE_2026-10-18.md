# Interner WorldPose-Bypass: Welche Pose erreicht Free?

> Kurzfassung: Verfolge im DLL-Kontext 0xE080 den WorldPose-Zeiger vom New-Call 0xE165 bis Free 0xE54D. Entscheide, welche Herkunft belegt ist und ob dieser konkrete Bypass ausgewaehlte H-Posen betreffen kann. Keine globale Alias- oder Heaprekonstruktion.

Basis `49936a3`, F178–F182; [Ausgangspunkt](../evidence/POSE_ALLOCATOR_BINDING_2026-10-18.md).

## Vorgehen und Abnahme

1. Originalidentitaet/sauberen Arbeitsstand pruefen. Vorhandene Funktion auf getrennter Ghidra-Kopie
   readOnly/noanalysis exportieren; keine Disassembly-/Analyse-/Funktionsanlage im Projekt.
2. Herkunft des New-Groessenarguments, Ablage des Returns und alle lokalen Definitionen des Free-Arguments
   im geprueften Kontrollfluss erfassen. New-/Free-Naehe allein ist kein Identitaetsbeweis.
3. Eigene New-Instanz, eingehende Pose und moegliche Alias-/Escape-Kanten trennen. Erfolg/Rueckkehr,
   alternative Pfade und Calls, die den gehaltenen Zeiger erhalten, explizit begrenzen.
4. Positive Datenflussbindungen mit RVA/Bytes/Pfad belegen. Bestehenden Verifier erweitern und neue
   Ablehnungstests normal/-O ausfuehren; keine Testzahl als Ersatz fuer Binaerinterpretation darstellen.
5. Unabhaengige Byte-/Pfadgegenpruefung, regulaere Gesamtchecks, Befunde/Wissenskarte/Uebergabe und lokaler Commit.

Erfolgreich ist ein belegter Herkunftsentscheid fuer **diesen** Free-Call oder eine konkret lokalisierte offene
Definition/Aliaskante samt kleinstem Folgebeweis. Eine eigene New-Pose im Pfad beweist ohne Allocatorvertrag
keine absolute Adressverschiedenheit zu jeder anderen Pose. Eine bestandene Bytepruefung beweist Fundstellen;
die Argument-/Pfadbegruendung muss getrennt vorliegen.

Originale/Rohdaten/Audit/originale Ghidra-DB unveraendert. Keine Originalausfuehrung, Livezugriffe, Hooks,
Aufnahme, Installation, Cache/Skip, Austauschimplementierung, Push oder PR. Geschuetztes Kopierfenster und
vollstaendige relevante Ereignisabdeckung werden nicht automatisch durch diesen Teilbeweis geschlossen.

## Ergebnis

[Nachweis und Abnahme](../evidence/POSE_INTERNAL_PROVENANCE_2026-10-18.md): F183–F185, bedingter direkter
New-/Free-Herkunftsentscheid und konkrete Contextaliasgrenze. 21 Verifiertests/Originaldatei-Gates normal/-O,
16/16 Gesamtpruefgruppen und unabhaengiger Byte-/Argument-/Code-/Dokumentreview bestanden.
Der kleinste Folgebeweis betrifft arg1Context an 0xE30C -> Track+8 fuer einen konkreten Kandidaten.
