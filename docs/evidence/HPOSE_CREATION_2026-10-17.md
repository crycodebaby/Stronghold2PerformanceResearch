# H-Pose: ein Erzeugungs- und Uebergabepfad

> Kurzfassung: Ein statischer Exe-Pfad verbindet Granny-Erzeugungsaufrufe mit H+0/+4/+8 und derselben Record-Auswahl O+0x4C. Recordanzahl, angeforderte Knochenzahl und Allokationskapazitaet bleiben getrennt. Keine vollstaendige Lebensdauer- oder Optimierungsfreigabe.

Datum: 2026-10-17. Forschungsbasis `822ceae`, Branch `hpose-creation-proof`, nur lokal. Hub unveraendert.
Ein frischer Sol-6.1-Agent untersuchte eine getrennte Ghidra-Kopie mit `-readOnly -noanalysis` und zusaetzlicher
Programmidentitaetspruefung. Der Projektleiter pruefte die Originaldatei-Hashes, drei Import-Aufrufziele und die
Rueckgabewertspeicherungen unabhaengig mit dem bisherigen PE-Parser nach; die lokalen exportierten Instruktionsbytes
stimmen mit den Exe-Dateibytes ueberein. Das ist keine formale Verifikation aller Kontrollpfade.

## Identitaet und Begriffe

- Exe SHA-256: `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, Basis `0x00400000`.
- DLL SHA-256: `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`, Basis `0x50000000`.
- Alle folgenden Codeadressen sind Exe-RVAs. O ist der eingehende Objektkontext in ECX, H ein 20-Byte-Datensatz.
  R, M und S bezeichnen weitere, voneinander getrennte Referenten; dies sind unsere Arbeitsnamen.
- H+4, WorldPose+4 und S+4 sind Felder verschiedener Objekte. Die gleichen numerischen Offsets machen sie nicht gleich.

## Direkt belegter Erzeugungspfad, Einstieg RVA 0x38E0A0

- `0x38E24B` bis `0x38E255`: Recordanzahl C aus der lokalen Variablen EBP-0x58 geht an `0x38DC70`,
  mit ECX = Adresse von O+0x18. Der Container hat relativ +0/+4/+8 die Bereichsgrenzen/Kapazitaetsgrenze;
  diese liegen damit bei O+0x18/+0x1C/+0x20, nicht bei H+0/+4/+8.
- `0x38E26A` bis `0x38E276`: H entsteht aus dem Bereichsbeginn und einem Recordoffset. R aus einem Listenknoten
  wird in H+0xC gespeichert. Herkunft und semantischer Typ dieser Ressource sind nicht vollstaendig aufgeloest.
- `0x38E27D`: `GrannyInstantiateModel`, IAT-RVA `0x500AAC`, erhaelt M = *(R+0xC).
  Sein Rueckgabewert geht bei `0x38E286` nach H+0.
- `0x38E292`: `GrannyNewWorldPose`, IAT-RVA `0x500AB0`, erhaelt N aus S+4, mit S = *(M+4).
  Rueckgabewert nach H+4 bei `0x38E29B`.
- `0x38E2A8`: `GrannyNewLocalPose`, IAT-RVA `0x500AB4`, bekommt N ueber dieselbe R/M/S-Feldkette.
  Rueckgabewert nach H+8 bei `0x38E2B4`.
- `0x38E2BA`: Modelluhr null; `0x38E2C0`: Recordoffset um 20 erhoeht; `0x38E2C4`: H+0x10 wird null.
  Die Bedeutung des letzten Felds ist offen. Diese Stores beweisen keinen erfolgreichen Allokatorrueckgabewert.
- `0x38E2D4` bis `0x38E2F2`: bei nichtleerem Bereich wird dessen Anfang nach O+0x4C geschrieben.

N wird als angeforderte Knochenzahl an die beiden Pose-Imports uebergeben. Die Feldkette passt zu einem Quellmodell
mit Skelettreferenz, beweist hier aber keine urspruenglichen C++-Typnamen. Es wurde kein Laufzeit-N gelesen.
C ist eine andere Groesse: angeforderte Anzahl der H-Datensaetze. Seine lokale Variable beginnt bei null; ein
Sonderpfad setzt eins, weitere Hilfer-/Listenverarbeitung folgt. Eine vollstaendige C/Listenlaengen-Invariante fehlt.

## Uebergang zur bekannten Auswahl

In `0x38E4D0` bezeichnet O wieder den jeweiligen eingehenden ECX-Kontext. O+0x18/+0x1C liefern Anfang und Ende;
die Anzahl wird durch vorzeichenbehaftete Division der Differenz durch 20 berechnet. Fuer einen nichtnegativen,
passenden Bereich nimmt der unsigned Vergleich an `0x38E51F`/`0x38E521` bei index < Anzahl den direkten Pfad.
`0x38E613` bis `0x38E61C` bilden H = Anfang + 20*index und speichern H nach O+0x4C; `0x38E61F` liest es wieder.
Der nachfolgende Samplepfad ist F149. Damit ist die gemeinsame Feld-/Datenflussstruktur belegt; nicht bewiesen ist,
dass jeder dynamische O-Aufruf durch genau diesen einen Erzeugungspfad initialisiert wurde.
Fuer einen ausgeschlossenen Index folgt ein geometrischer Ersatzpfad, der hier nicht nachgebaut wird.

## Drei Groessen und die offene Grenze

Recordanzahl C, logische Recordbytes C*20 und tatsaechliche Allokationskapazitaet sind verschieden.
`0x38DC70` ruft fuer Wachstum `0x38D6D0` an `0x38DCC1`; dieser erreicht `0x38D500` an `0x38D73E`.
Die tatsaechliche Bytezahl/Allokatorfehlerbehandlung dahinter ist noch nicht verfolgt.
Der fruehere World-Pose-Vertrag 16+128*N gilt fuer dessen getestete gueltige DLL-Eingaenge, nicht als heutiger
Beweis der Kapazitaet jedes Spielzeigers. Local-Pose-Allokationsbytes und initialisierte Ausgabeausdehnung bleiben offen.
Freigabe, Reuse, eindeutiger Besitzer und Generationsgrenzen sind nicht vollstaendig belegt. Weitere Importreferenzen
in `0x38ED30` wurden nur inventarisiert. Kein zweiter Erzeugungspfad und kein Soldatentyp werden daraus behauptet.

## Ausfuehrbare Nachweise

```text
python -I tools/hpose_creation_verify.py --exe <original-exe> --dll <original-dll>
python -O -I tools/hpose_creation_verify.py --exe <original-exe> --dll <original-dll>
python -I tools/test_hpose_creation.py
python -I tools/hpose_native.py
python -I tools/run_checks.py
```

Der PE-Pruefer liest nur Dateien: zwei Identitaeten, drei IAT-Namen/-Adressen, sieben Funktions- und acht
Kantenfingerprints aus `tools/hpose_creation_manifest.json`. Fehlende/doppelte Eintraege oder geaenderte Hashes
werden abgewiesen, auch mit optimiertem Python. Fingerprints bestaetigen die Byteorte, nicht deren semantische Deutung.
Sechs synthetische Python-Tests pruefen diese Schutzschichten ohne Spiel. Fuer die Ghidra-Nachpruefung auf eigener
geschlossener Projektkopie `hpose_creation.java` mit lokalem Ausgabeordner und den VAs `00900AAC`, `00900AB0`,
`00900AB4`, `0078E0A0`, `0078E4D0`, `0078DC70`, `0078DDC0`, `0078D040`, `0078D6D0`, `0078CF70` ausfuehren;
`-readOnly -noanalysis`, Scriptpfad `ghidra_scripts`. Rohlistings bleiben unter ignoriertem `build/hpose-creation/`.

Die eigene C++17-Vorbereitung hat eine 20-Byte-Feldprojektion mit Compilezeitpruefungen und ein allokationsfreies
Adress-ID-/Indexmodell. MSVC Win32 Release mit `/W4 /WX /permissive-`: 14 feste Grenzfaelle und 65 kleine
Bereichsfamilien, insgesamt 6.383 Pruefbedingungen ohne Fehler. Nur geordnete, durch 20 teilbare Bereiche mit
Differenz <= INT32_MAX und direktem index < Anzahl werden modelliert. Fehlerablehnung ist unser Vertrag; keine
Reproduktion des Ersatzpfads, keine Dereferenzierung, keine Originalausfuehrung oder Besitzgarantie.
[Native Anforderungen und spaetere Optimierungskriterien](../design/HPOSE_CPP_CONTRACT.md).

Abnahme des integrierten lokalen Stands: `run_checks.py` 10/10 (neun Python-Suiten einschliesslich sechs neuer
Verifier-Tests plus Doku-Lint), Verifier mit Originaldateien normal und mit `-O` erfolgreich. Der finale Ghidra-Exporter
wurde auf derselben getrennten Kopie erneut kompiliert/ausgefuehrt; alle sieben relevanten Funktionsfingerprints der
neuen Exporte stimmen mit dem versionierten Manifest ueberein. Ein zweiter frischer Sol-6.1-Pruefer wiederholte die
gezielten Verifier-/Native-Tests und fand im begrenzten Vertragsreview keinen relevanten Defekt. Er rekonstruierte
nicht nochmals die gesamte Ghidra-Semantik. Kein neuer Real-DLL-Ausfuehrungstest, Sanitizerlauf oder Performancevergleich.

## Genau ein naechster Versuch

Statisch `0x38D500` und seinen unmittelbaren Allokations-/Store-Helfer untersuchen: Wie wird die angeforderte
Kapazitaet zu Bytes, und welche Anfangs-/End-/Kapazitaetswerte entstehen am selben Container?
Bei indirekter unaufloesbarer Kante deren Ort und kleinstes Zusatzexperiment festhalten. Vollstaendige C-Herkunft
und Freigabe/Reuse bleiben getrennte Restfragen. Keine Aufnahme, Installation, Cache-/Skip-Logik oder Parallelisierung.
Die Originalinstallation, Rohdaten und originale Ghidra-Datenbank wurden nicht beschrieben; es wurde nichts gepusht.
