# Pose-Allocator: Bindung, Wechsel und Freigabegrenzen

> Kurzfassung: Belege, wie die beiden WorldPose-Allocatorslots vorbelegt und veraendert werden und wohin ihre bekannten Ziele weiterleiten. Liefere eine belastbare Entscheidung ueber die noch fehlende Ereignisabdeckung ausgewaehlter Generationen. Kein kompletter Heapnachbau und kein Live-Beobachter.

Basis `e119eae`, F178/F179; [vorheriger Nachweis](../evidence/POSE_GENERATION_READ_WINDOW_2026-10-18.md).
Projektleitung untersucht die getrennte Ghidra-Kopie exklusiv, readOnly/noanalysis. Ein erneut gestarteter
Pruefagent kontrolliert Dateibytes, Argumentbindungen, Schlussfolgerungen und Abnahme unabhaengig.

## Plan

1. Originalidentitaeten und sauberen Git-Stand pruefen; initiale Slotwerte und passende Exporte ermitteln.
2. Referenzen auf beide Slots ohne den alten 12-Zeilen-Abbruch inventarisieren. Gefundene direkte Stores,
   Aenderungs-API und bekannte Defaultziele eng verfolgen; Aliase und unbekannte Writer separat ausweisen.
3. An den bekannten Freigabepfaden beurteilen, ob die Freigabe den heutigen Slot oder einen zur Geburt
   gespeicherten Callback verwendet. Folgen eines Wechsels zwischen Birth und Free explizit begrenzen.
4. Bestehenden bytepruefenden Verifier erweitern; eigene negative Tests und ein kleiner synthetischer
   Gegenfall nur dann, wenn er eine neue Nachweisluecke klar demonstriert. Keine produktive Hooklogik.
5. Unabhaengige Gegenpruefung, Gesamtchecks, Befunde/Wissenskarte/Uebergabe und lokaler Commit.

## Abnahmekriterien vor Beginn

- Jede positive Binaeraussage hat Modulhash, RVA, konkrete Daten-/Call-/Storebindung und reproduzierbare
  Schritte. Ein Fingerprint beweist die Fundstelle, nicht automatisch die Interpretation.
- Initiale Slotwerte, bekannte direkte Writer und beobachtete Forwardingkanten sind getrennt. Vollstaendigkeit
  gilt hoechstens fuer die explizit gepruefte Referenz-/Scanmenge, nie automatisch fuer beliebige Pointeraliase.
- Fuer ausgewaehlte NewWorldPose-Generationen steht eine klare Entscheidung: welche bekannte Ereignisgrenze
  reicht unter welchen Annahmen, welche konkrete Umkonfiguration/Freigabe bleibt ungedeckt?
- Bestehende Gates bleiben erhalten. Neue Gates lehnen veraenderte/fehlende Belege ab; Tests laufen normal
  und mit `-O`, regulaere spielfreie Gesamtchecks bestehen. Der Pruefer versucht eigene Gegenbeispiele.
- Der Abschluss nennt den Wissensgewinn, offene Grenze, kleinsten Folgebeweis und praktische Bedeutung fuer
  einen spaeteren verlaesslichen Beobachter. Kein Performance- oder Sicherheitsgewinn allein aus gruenen Tests.

Originale/Rohdaten/Audit/originale Ghidra-DB unveraendert. Keine Originalausfuehrung, Aufnahme, Installation,
Livezugriffe, Hooks, Cache/Skip, Austauschimplementierung, Push oder PR. Ein praezise belegtes unbekanntes
Verhalten ist akzeptabel; blosse weitere Adresslisten ohne Entscheidung erfuellen die Abnahme nicht.

## Ergebnis

[Nachweis und Abnahmeprotokoll](../evidence/POSE_ALLOCATOR_BINDING_2026-10-18.md): F180–F182, konkrete
Konfigurations-/Alias-/Invalidierungsbedingungen, eigene Gegenbeispiele und gepruefte Bytebindungen.
18 Verifiertests/19 Modelltests normal/-O, Originaldatei-Gates und 16/16 Gesamtpruefgruppen bestanden;
unabhaengiger Code-/Byte-/Dokumentreview ohne verbleibenden sachlichen Blocker. Selektive Ereignisvollstaendigkeit
und geschuetztes Leseintervall bleiben offen; genau ein Folgebeweis grenzt die interne Bypass-Poseherkunft ein.
