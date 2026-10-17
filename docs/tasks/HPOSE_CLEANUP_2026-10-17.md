# H-Pose: begrenzter Cleanup- und Lebensdauerpfad

> Kurzfassung: Verfolge den Cleanup-Kandidaten RVA 0x38E3C0 bis zu den H-Feldern, direkten Aufrufern und ausgewahlten H-Zeigern. Nur statische Belege und eigene spielfreie Tests; keine allgemeine Lebensdauer- oder Optimierungsfreigabe.

Basis: `3932634`, auf der offentlichen Forschungshistorie. Vorganger:
[Allokation und Transfer](../evidence/HPOSE_ALLOCATION_2026-10-17.md), F156/F157.

Abgeschlossener Teilnachweis und offene Grenze:
[Cleanup, direkter Abbaupfad und genau ein Folgeversuch](../evidence/HPOSE_CLEANUP_2026-10-17.md), F158/F159.

## Frage und Abnahme

- Welche konkreten Argumente erreichen die drei Granny-Free-Imports bei 0x38E3F9/0x38E403/0x38E40D?
- Welcher Bereich wird durchlaufen und was wird anschliessend geleert, freigegeben oder zuruckgesetzt?
- Welche direkten Aufrufer sind bytegestutzt belegt; was geschieht im belegten Pfad mit O+0x4C?
- Welche Lebensdauergrenze ist damit geschlossen und welche Voraussetzungen fehlen fur einen lesenden Posevergleich?

Jede positive Verbindung braucht Buildidentitat, Funktion/RVA, Argument-/Storeherkunft und reproduzierbare
Prufschritte. Ein Importxref ist nur Inventur. Indirekte Aufrufer, Fehlerpfade und Generationen bleiben getrennt,
wenn sie statisch nicht aufgelost werden konnen. Ein sauber abgegrenztes unbekanntes Verhalten ist ein Ergebnis.

## Grenzen

Nur getrennte Ghidra-Kopie, read-only/noanalysis, und explizite read-only PE-Prufung der Originaldateien.
Keine Spielausfuhrung, Aufnahme, Installation, Hook-/Observeranderung, Skip-/Cachelogik oder eigene Freigabe
historischer Zeiger. Originalinstallation, Rohdaten, kanonischer Audit und originale Ghidra-Datenbank unverandert.
Keine Rohdisassembly oder dekompilierter Spielcode in Git; lokale Analyseausgaben bleiben unter ignoriertem build/.

Ein Agent untersucht den Pfad und erstellt neue Prufwerkzeuge, ein unabhangiger Reviewer pruft die entscheidenden
Verbindungen ohne gleichzeitigen Zugriff auf die Ghidra-Kopie. Projektleitung integriert Befunde und Ubergabe.
Abnahme: gezielte negative/positive Werkzeugtests normal und unter -O, reale read-only Binargates,
integrierte spielfreie Prufgruppen und Dokumentationslint. Native Prufung nur bei betroffener eigener C++-Logik.
Kein Push/PR im Rahmen dieses Forschungsauftrags; lokale Commits nach gepruftem Teilabschluss.
