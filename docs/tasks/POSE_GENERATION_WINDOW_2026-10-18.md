# Posegeneration und Leseintervall

> Kurzfassung: Ordne Geburt, Kapazitaet und Invalidierung einer konkreten WorldPose-Generation den bisherigen Binaerpfaden zu. Pruefe das moegliche Matrix0-Leseintervall; demonstriere ABA, Ereignisluecken und ueberlappende Operationen spielfrei. Keine Hooks, Aufnahme oder Originalausfuehrung.

Basis `34e2513`; [Readiness](../design/POSE_COMPARISON_READINESS_2026-10-17.md), F150/F154–F159/F175–F177.
Ein Generationstoken bezeichnet eine beobachtete Allokationsinstanz, nicht bloss eine wiederverwendbare Adresse.
Eine konsistente Ereignisfolge allein beweist noch kein sicheres Lesen fremden Speichers.

## Nachweisumfang

- NewWorldPose-/FreeWorldPose-/InPlace-Grenzen erneut dateilesend/statisch pruefen; Bibliotheksworker,
  konfigurierbare Allocatorcallbacks und Export-only-Abdeckung unterscheiden.
- Nur bekannte direkte Worker-/Importpfade untersuchen, keine gesamte Heap-/Cache-Rekonstruktion.
- Numerische Kapazitaet aus beobachteter erfolgreicher Konstruktion, gleiche lebende Generation und eine
  unveraenderte Zuordnung verlangen; HeaderN oder gleicher Pointer sind kein Ersatz.
- Fastentry-Rueckkehr und Sample-Rueckkehr getrennt beurteilen. Aktive Originalargumente implizieren nur unter
  einem noch nachzuweisenden Lifetime-/Thread-/Aliasvertrag ein geeignetes Kopierfenster.
- Einen kleinen eigenen ereignisbasierten Testnachweis mit synthetischen Adress-IDs erstellen: erfolgreiche
  Zuordnung, Free-Eintritt, ABA, fehlender Lebenszyklus, vorbestehende Objekte, Overflow, Reentranz und konkurrierende
  Operationen. Das Modell liest keinen Spielspeicher und stellt keine Live-Leseerlaubnis aus.
- Wissenskarte/STATE/Uebergabe, genaue offene Grenze und kleinsten Folgebeweis aktualisieren.

## Abnahme und Grenzen

Bestehende dateilesende Binaerpruefer und Exportwerkzeuge wiederverwenden. Neue Gates nur fuer neue Belege;
eigene Tests normal und mit `-O`, danach regulaere spielfreie Gesamtchecks. Keine unveraenderten nativen Hosts neu bauen.
Originalinstallation, Rohdaten, kanonischer Audit und originale Ghidra-DB unveraendert; nur getrennte Kopie
readOnly/noanalysis. Keine Original-/DLL-Ausfuehrung, Hooks, Livezugriffe, Aufnahme, Cache/Skip oder Push.

Die vorgesehenen Unteragenten fielen zunaechst am Nutzungslimit aus. Die Projektleitung setzte die Arbeit fort;
nach Nutzerwunsch gelang der Neustart des Pruefers. Er pruefte finale Byteausgaben und eigenes Modell und fand
einen reproduzierbaren Modellfehler, der vor Abnahme korrigiert wurde. Getrennte PE-Reader bleiben zusaetzliche
technische Gegenpruefungen mit anderer Reichweite. Ergebnis und genaue Grenzen stehen im
[Nachweis](../evidence/POSE_GENERATION_READ_WINDOW_2026-10-18.md).
