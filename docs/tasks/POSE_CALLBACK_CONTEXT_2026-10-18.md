# Trackcallback: Contextvertrag an 0xE30C

> Kurzfassung: Grenze fuer einen belegten Callbackkandidaten ein, was Argument 1 am indirekten Call DLL 0xE30C -> Track+8 liest, schreibt oder weitergibt. Keine komplette Kurvenmathematik oder Livebeobachtung.

Startbasis Forschung `38d7e79`, F183–F185, [Nachweis](../evidence/POSE_INTERNAL_PROVENANCE_2026-10-18.md).
STATE bestimmt, ob diese Aufgabe aktuell ist; dieses Dokument allein aktiviert keinen Auftrag.

## Frage und kleine Startmenge

Im E080-Kontext gehen eigene NewWorldPose-Returns ueber lokale Felder an Free. Diese direkte Zuordnung ist
an erhaltene Framefelder/Calling Convention gebunden. E30C erhaelt arg1=F-0x80; W-Felder liegen F-0x44/F-0x40.
Die bekannte direkte Contextkante 44DAB -> 2F5D0 ist in dieser DLL ein leerer Return. Die indirekte Kante bleibt offen.
F bezeichnet den lokalen EBP-Frame, keine Objektstruktur. Ein Feldabstand liefert keinen Schreibvertrag.

1. Arbeitsstand, Binaeridentitaeten und vorhandene Werkzeuge pruefen; ggf. privaten lokalen Pfadindex validieren.
2. Herkunft von Track+8 fuer genau einen begruendeten Kandidaten verfolgen. Dateitabellenwert, Konstruktorbindung
   und tatsaechlich aktives Laufzeitziel sind getrennte Aussagen; keine beliebige Funktion als Ziel einsetzen.
3. Fuer diesen Kandidaten arg1-Verwendung und abgeleitete Read-/Write-/Escape-Bereiche mit RVAs begrenzen.
   Context ist nicht automatisch arg7/8-World-/Composite-Ausgabe. Keine volle Transformsemantik behaupten.
4. Entscheiden, welche Frame-Nichtmutationsbedingung damit geschlossen/weiter offen ist. Kein Schluss von
   Pointeridentitaet auf lebende Generation, gueltige Werte oder sicheres Kopieren.

## Abnahme

- Reproduzierbare Identitaets-/Byte-/Argumentbelege und getrennte semantische Begruendung; ein unabhaengiger
  Pruefer versucht insbesondere eine falsche Zielbindung oder unbelegte Schreibspanne zu widerlegen.
- Positiver enger Schreibvertrag oder genaue offene Producer-/Alias-/Escape-Kante mit kleinstem Folgebeweis.
- Bestehende Verifier/Exporter wiederverwenden, kein zweites Framework. Neue Gates mit sinnvollen Ablehnungs-
  tests normal/-O; regulaere Gesamtchecks `python -I tools/run_checks.py` muessen bestehen.
- Befunde/Evidenz, STATE und betroffene Kartenstation aktualisieren; eigenen lokalen Commit mit Grenzen berichten.

## Grenzen

Nur statisch/dateilesend, getrennte Ghidra-Kopie readOnly/noanalysis; ein DB-Verantwortlicher. Keine neue Analyse,
Disassembly-/Funktionsanlage in der Datenbank, Original-/DLL-Ausfuehrung, Aufnahme, Hooks, Livezugriffe,
TEST-Installation, Cache/Skip, Austauschimplementierung, Push oder PR. Originale/Rohdaten/Audit unveraendert.
Kanonische vorhandene Exporte lokal unter `build/pose-internal-provenance/canonical`, ggf. frisch reproduzieren.
Rohlistings/Decompilertext bleiben ausserhalb des Kontextes/Git; keine historischen Zeiger dereferenzieren.
