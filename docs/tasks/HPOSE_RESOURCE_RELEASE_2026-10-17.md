# H-Pose: ein indirektes Ressourcen-Freigabeziel

> Kurzfassung: Genau den Call Exe RVA 0x38E428 von R=*(H+0xC) bis zu einem belegten Ziel verfolgen. Herkunftsbindung, Zielsemantik und offene indirekte Grenzen getrennt; nur statische Analyse, keine Spielausfuehrung oder Optimierung.

Basis: `183762c`; folgt auf F158/F159 und
[Cleanup/Abbau](../evidence/HPOSE_CLEANUP_2026-10-17.md).

Ergebnis: [Konstruktor-/Tabellenkandidat, bedingter Freigabepfad und genaue offene Herkunft](../evidence/HPOSE_RESOURCE_RELEASE_2026-10-17.md),
F160–F162. Der dynamische Call ist weiterhin nicht aufgeloest.

## Ziel und Umfang

Der Cleanup gibt H+0/+4/+8 an Granny-Free-Imports weiter. Danach dekrementiert er R+4 und ruft bei null
mit Kontext R und Argument 1 ueber Tabellen-Slot 0 auf. Der ausgewaehlte H-Zeiger wird erst spaeter genullt.
Dieser Auftrag schliesst genau die Ressourcen-Zielkante oder bezeichnet die verbleibende Herkunftsluecke.

- Verfolge die bekannte R-Herkunft im Erzeugungspfad, seine Uebergabe an H+0xC und belegte Tabellenstores.
- Pruefe dabei auch das enge Store-/Transferinventar der zwischen Konstruktion und Produzentenrueckgabe
  liegenden Initialisierung 0x395CC0. Ein Konstruktorstore allein beweist keinen spaeteren Tabellenwert.
- Verbinde die konkrete Tabelle mit Slot 0 und dem Ziel anhand von PE-Bytes/RVAs.
- Beschreibe dessen normalen Freigabepfad und hoechstens 1–3 zentrale Zielhelfer, soweit fuer diese Kante noetig.
- Trenne Zielkandidaten, bedingt bewiesene Bindung und vollstaendig geschlossene Pfadbindung.
- Bezeichne offene Callbacks, indirekte Ziele und Throw-/Reentrancy-/Threadgrenzen. Fehlende Xrefs beweisen keine
  Abwesenheit eines dynamischen Rueckrufs. Keine urspruenglichen Source-Typnamen erfinden.

Nicht enthalten: alle Aufrufer, allgemeine Asset-/Heapverwaltung, komplette Lebensdauer aller Modelle,
ein Ergebnisbeobachter oder Optimierungsimplementierung. Ein schmaler unbekannter Uebergang ist ein Ergebnis.

## Abnahme

Buildidentitaet und sauberer Ausgangsstand zuerst. Jede positive Kante hat Funktion/Modul/RVA,
Argument-/Storeherkunft und reproduzierbare Byte-/Tabellenpruefschritte. EXE-RVA und DLL-RVA getrennt halten.
Manifest/Fingerprints binden Byteorte, beweisen allein keine Semantik.

Neue eigene Werkzeuge testen Erfolg und relevante Manipulationen/fehlende Bindungen normal und unter -O.
Ein frischer Reviewer prueft entscheidende Daten-/Kontrollflusskanten mit eigener PE-Bytepruefung und ohne DB.
Projektleitung integriert Befunde, Reproduzierbarkeit, STATE und aktuelle Uebergabe und fuehrt die regulaeren
spielfreien Checks aus. Kein neuer nativer Baustein ohne begruendeten eigenen Vertrag.
Lokaler Commit nach zusammenhaengender gepruefter Abnahme; kein Push oder PR in diesem Auftrag.

## Prompt fuer den Forschungsagenten

Untersuche ausschliesslich den indirekten Freigabeaufruf Exe RVA 0x38E428. Lies zuerst AGENTS.md,
CLAUDE.md, STATE, PROJECT_LEAD_HANDOFF, die Analyse-Skill und die Creation-/Allocation-/Cleanup-Evidenz.
Pruefe Git- und Binäridentitaet. Behandle alle bisherigen Agentenaussagen als zu pruefende Behauptungen.

R kommt im bekannten Pfad aus dem Listenknoten und wird in H+0xC gespeichert. Verfolge seine Herkunft bis zu
einem belegten Tabellen-Slot-0-Ziel. Verwechsle einen passenden Loeschwrapper oder Klassennamen nicht mit einer
bewiesenen dynamischen Bindung. Erklaere, was der Zielpfad tatsaechlich freigibt und welche indirekten Kanten offen
bleiben. Wenn die Herkunft nicht geschlossen werden kann, liefere die konkrete Luecke und den kleinsten
zusaetzlichen Nachweis. Beruecksichtige unmittelbare Initialisierung nach dem Konstruktor und den getrennten
Cache-Trefferpfad; ein neuer Objektfall beweist nicht alle Cache-Rueckgaben. Begrenze zentrale Zielhelfer auf hoechstens drei.

Arbeite nur statisch auf der getrennten Ghidra-Kopie mit readOnly/noanalysis. Ein Agent hat den alleinigen
DB-Zugriff. Originalinstallation, Rohdaten, kanonischer Audit und originale DB bleiben unveraendert.
Keine Spiel-/DLL-Ausfuehrung, Aufnahme, Installation, Hooks, Cache-/Skiplogik oder Freigabe historischer Zeiger.
Rohlistings bleiben in ignorierten lokalen Ausgaben; keine Binaries, Assets, Rohdisassembly, dekompilierter Code
oder persoenliche absolute Pfade in Git oder Kontext.

Liefere strukturierte Belege, ein read-only Pruefwerkzeug mit versioniertem Manifest und sinnvollen negativen
Tests normal/-O, einen gemeinsamen finalen Export aller verwendeten Ziele und eine kurze Evidenzdatei.
Trenne statische Befunde, Hypothesen, eigene Testmodelle und nicht ausgefuehrte Pruefungen. Benenne genau
einen naechsten Versuch. Keine bestehenden Dateien oder Historien aendern; Integration und Commit uebernimmt
die Projektleitung nach unabhaengigem Review. Melde wichtige Ergebnisse und Luecken frueh.
