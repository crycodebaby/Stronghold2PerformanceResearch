# Sample-Ausgabe: gueltiger initialisierter Matrizenbereich

> Kurzfassung: Bestimme am bekannten Exe-/Granny-Samplepfad, welche World-/Composite-Matrixindices auf einem belegten normalen Pfad tatsaechlich geschrieben werden. Angeforderte Knochenzahl, Allokationskapazitaet und initialisierte Ausgabe getrennt; keine neue Originalausfuehrung oder Beobachterimplementierung.

Basis: `21c3af7`. Projektentscheidung:
[Voraussetzungen fuer einen Posevergleich](../design/POSE_COMPARISON_READINESS_2026-10-17.md).
Vorwissen: [DLL-Vertrag](../evidence/POSE_CONTRACT_2026-10-16.md), F149–F153,
[Erzeugungspfad](../evidence/HPOSE_CREATION_2026-10-17.md), F154/F155.

## Konkrete Frage

Exe Sample-Call RVA 0x38E6D9, Rueckkehr 0x38E6DF, fuehrt zum Granny-Export RVA 0x4F6D0
bei DLL-Basis 0x50000000. Fuer einen gueltigen betrachteten Aufruf: welche Matrizen in World- und
Composite-Arrays sind nachher initialisiert, und unter welchen Bedingungen?

Der bekannte Header-/Allokationsvertrag allein beantwortet diese Frage nicht. Konstruktion initialisiert
Matrixdaten nicht. Ein normaler Return, gleichbleibender Pointer oder gleiche Eingaben beweist keinen vollen
initialisierten N-Bereich und keine Gleichheit von Ergebnissen.

## Abgegrenzte Analyse

- Belege Exe-Argumente und Export-/Workerverbindung, inklusive Modulidentitaet und RVA/VA-Konvention.
- Trenne angeforderten Sample-count, allokiertes N und tatsaechliche Schleifengrenzen/Indexabbildung.
- Verfolge die relevante Writerkette, Stores, normale Verzweigungen und fruehe/Fehlerausgaenge. World und
  Composite separat; normale/partielle/leere Bereiche nur im belegten gueltigen Eingangsbereich.
- Belege innerhalb einer Matrix die tatsaechliche Schreibabdeckung der 64 Bytes/16 float32. Volle Stores
  allein garantieren keine definierten Ergebnisse aus unbekannten oder uninitialisierten Quellwerten.
- Eine lokale Callback-Nullkante ohne eigene Writes ist kein Sample-Gegenbeispiel, solange Vorgaenger,
  Nachfolger/Fallbacks und Erreichbarkeit im zugelassenen Eingangsbereich nicht geschlossen sind.
- Bezeichne initialisierten Bereich und unbekannte Bedingungen exakt. Keine ungepruefte Normalpfadformel
  fuer alle Eingaben/Callvarianten oder beliebige historische Spielpointer.
- Bei grosser Kernverzweigung einen konkreten Pfad/Writer begrenzen und offene Kante nennen; kein voller
  Animationsnachbau und keine Rueckkehr zum Cache-/Vptr-Komplettbeweis.

## Zusammenarbeit und Nachweis

Ein Analyseagent hat alleinigen Zugriff auf die getrennte Ghidra-Kopie, nur readOnly/noanalysis.
Ein unabhaengiger Reviewer prueft Exporte/Originalbytes, Argumente, Counts und Branch-/Indexbeziehungen ohne DB.
Projektleitung integriert neue Fakten, Reproduzierbarkeit und Uebergabe und bestimmt genau einen Folgebeweis.

Vorhandene PE-Reader/Exportwerkzeuge wiederverwenden. Ein neuer Pruefvertrag ist nur fuer die neue
moduluebergreifende Sample-/Writerfrage gerechtfertigt; keine weiteren gleichartigen Ressourcen-Verifierkopien.
Manifest-/Bytegates und relevante negative Tests normal/-O; ein Fingerprint bestaetigt Orte, nicht Semantik.
Finale Exporte je Modul mit allen verwendeten Zielen und vollstaendigen Argumenten dokumentieren.
Regulaere spielfreie Checks und Dokumentationslint; native Tests nur bei betroffener eigener C++-Logik.

## Grenzen und Abschluss

Originalinstallation, Rohdaten, kanonischer Audit und originale Ghidra-DB unveraendert. Keine Ausfuehrung
von Game-/DLL-Code, keine historischen Pointerzugriffe, Aufnahme, Installation, neuer Observer, Hook-/Cache-/
Skiplogik oder Performanceaussage. Rohlistings bleiben ignoriert lokal, eigene Werkzeuge und kuratierte Fakten in Git.

Abschluss: ein unter belegten Bedingungen initialisierter Bereich oder die genaue noch fehlende Writer-/Count-
Verbindung. Danach die kleinste verbleibende Gueltigkeits-/Lebensdauerfrage bestimmen. Kein Livevergleich
allein aufgrund dieses Ergebnisses. Lokaler Commit nach Abnahme; kein Push/PR in diesem Auftrag.
