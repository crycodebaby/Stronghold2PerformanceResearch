# Spezialpfad: Descriptor, Callback und Poseausgabe

> Kurzfassung: Binde die indirekte Kante DLL 0x2C44 -> 0x2460 an ihre konkrete Descriptorherkunft und den bedingten World-/Composite-Schreibumfang. Keine Rekonstruktion aller Controls, Originalausfuehrung oder neue Aufnahme.

Basis `8200cde`; vorheriger [Schreibumfang](../evidence/POSE_SAMPLE_EXTENT_2026-10-17.md), F167–F170.
Alle DLL-Adressen sind RVAs bei Basis `0x50000000` und SHA-256
`94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`.

## Frage und zulaessiger Abschluss

Im bekannten Sampleworker `0x2A70` ist das erste Kontrollpraedikat `0x1B540` true; der naechste Knoten fehlt
oder dessen Kontrolle erfuellt dieses Praedikat nicht. Dann ruft `0x2C44` den Wrapper `0x2460` mit
`(first.node,B,A,W,0)` auf. Welche Herkunft hat `D=*(first.node+0x18)`, welche konkrete Funktion liefert
`*(D+0x10)`, und welche World-/Compositeindices und Matrixbytes schreibt dieser Pfad?

Ein Tabellenkandidat allein beweist keine dynamische Zielbindung. Die Uebergabe vom Erzeuger bis zum
verwendeten Descriptor muss belegt oder die konkrete verbleibende Store-/Aliasluecke benannt werden.
Ist die Zielmenge nicht eng schliessbar, ein begrenztes Inventar und genau die offene Herkunftskante liefern.
Keine automatische Ausweitung auf alle Controltypen, Animationsmathematik oder Ressourcen-Caches.

## Nachweis

- Binär-/Arbeitsidentitaet erneut pruefen; getrennte Ghidra-Kopie nur readOnly/noanalysis.
- Einen zusammenhaengenden Descriptor-/Zuweisungs-/Callbackpfad belegen, Funktion/RVA und reproduzierbare
  Argumente nennen. Herkunft, beobachtete Stores und bedingte dynamische Folgerung trennen.
- Am gebundenen Callback Argumente und Zielarrays, Count-/Indexrelation, Teil-/Nullbereiche, fruehe Ausgaenge
  und weitergereichte Writer vergleichen. Bestehende direkte Writerbelege wiederverwenden.
- Vollstaendige 64-Byte-Stores getrennt von initialisierten Quellwerten, Kapazitaet, Parentordnung, Generation,
  Dispatch und Leseintervall behandeln. Aus Nullcallback-RET folgt kein gueltiges Sample-Gegenbeispiel.
- Bestehenden Sample-Verifier/Manifest/Tests erweitern; kein neuer gleichartiger Verifier. Nur eigene Werkzeuge,
  kuratierte Fakten und Fingerprints in Git, keine Originalpseudocode-/Assemblylistings.

## Zusammenarbeit und Abnahme

Ein Autor besitzt den exklusiven Zugriff auf die getrennte DB. Ein unabhaengiger Reviewer prueft Originalbytes,
Descriptor-/Argumentbindungen und semantische Grenzen ohne DB-Zugriff. Projektleitung integriert STATE,
FINDINGS, Funktionen und Uebergabe; lokale Commits erst nach Abnahme. Kein Push/PR.

Finale Exporte und Argumentlisten dokumentieren, gezielte negative Tests normal und mit `-O`, dateilesenden
Verifier gegen passende Originaldateien sowie regulaere spielfreie Checks ausfuehren. Fingerprints bestaetigen
Identitaet/Abdeckung, nicht automatisch die semantische Interpretation. Keine nativen Wiederholungstests ohne
betroffene eigene C++-Logik, kein Audit-/E2E-Neulauf bei unveraendertem Hub/Observer.

Originalinstallation, Rohaufnahmen, Auditreferenz und originale Ghidra-DB bleiben unveraendert. Keine Spiel-/
DLL-Ausfuehrung, historischen Pointerzugriffe, Observer, Installation oder Cache-/Skiplogik. Abschluss ist ein
belastbarer bedingter Callbackvertrag oder eine genau lokalisierte offene Verbindung samt kleinstem Folgebeweis.
