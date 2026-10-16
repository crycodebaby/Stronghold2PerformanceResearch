# Unabhängiger Audit: Stronghold 2 / Granny-Beobachter

Stand: 16.10.2026. Auftrag ausschließlich lesend gegenüber SH2-Perf, Hub, beiden Spielinstallationen, Aufnahmen und ursprünglichem Ghidra-Projekt.

**Was wissen wir jetzt zuverlässiger, was war möglicherweise falsch, und was ist die nächste Entscheidung?**

Die wiederholten Sampling-Aufrufe in der bestätigten Pause und die 1.503 eng gefilterten Zeigerreihen sind nachgerechnet. Die Tabellenverluste entwerten nicht automatisch jede Beobachtung eines bereits aufgenommenen Schlüssels. Sie verhindern aber Aussagen über die gesamte Modellpopulation und können sogar eine scheinbar eindeutige Deform-Zuordnung verbergen. Der Name `all_observed_same` darf nicht als allgemeiner Vergleich der Uhrwerte zweier Sampling-Aufrufe gelesen werden. Außerdem fehlen am Aufnahmeschluss Aufrufe in der Frame-Zuordnung, obwohl kein Frame-Zeilenverlust gemeldet wird.

Neu statisch belegt sind die Auswahl des Modell-/Pose-Datensatzes, mehrere unmittelbare Quellen des Uhrarguments, ein rekursiver Sampling-Pfad und ein Kontroll-Aufräumaufruf direkt nach dem Sampling. **Eine sichere Optimierung oder ein FPS-Gewinn ist weiterhin nicht nachgewiesen. Ein neuer, begrenzter Engine-Befund ist dagegen nachgewiesen.** Als genau einen nächsten Versuch empfehle ich einen engen Vergleich tatsächlich berechneter Pose-Ergebnisse, ohne einen Originalaufruf zu überspringen. Weitere Zeitlokalisierung hat anschließend Nutzen, beantwortet die derzeitige Korrektheitsfrage aber nicht.

## 1. Identität, Verfahren und unveränderte Eingänge

Eingangswurzel: `<RE-Projects>`. Audit-Arbeitsordner: `<audit-workspace>`.

- SH2-Perf: `77af09e72f2e23434a32643454e9140367e73336`, sauber. Gegenüber dem genannten `02bce97` ausschließlich zwei Dokumentationsdateien, 59 hinzugefügte Zeilen: Audit-Auftrag und Statusverweis. Kein späterer Beobachterfix.
- Hub: `32ebc38a05ea94cfc3fd831c1a12174b9a34f51c`, sauber; keine Differenz zum genannten Ausgangsstand.
- A1: `rec-20261015T121438Z-7d436886`, drei manifestierte Dateien; G1: `rec-20261015T122211Z-dff71642`, sieben. Größen und SHA-256 gegen Manifest sowie Importnachweis unabhängig geprüft. Die gemeinsamen Sitzungslogs haben keine Integritätsgarantie und tragen keine wesentliche Schlussfolgerung dieses Audits.
- `Stronghold2.exe`, Original und TEST, SHA-256 **`f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`**; PE32/x86, ImageBase `0x00400000`.
- `granny2.dll`, Original und TEST, SHA-256 **`94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`**; PE32/x86, ImageBase `0x50000000`.
- TEST-Hub **`4a56b62e5e9e2d4b8794860d95d74b898840c00c23144bc63e2bbc13c1724127`** und Proxy **`13c895196c175fd3cd963ba3b20ad84e92d4d9caf41cd2e1308eadfc84e24801`** stimmen mit G1 überein. Die heutigen INI-/Prepared-Dateien sind erwartungsgemäß andere als während G1; nicht zur Rekonstruktion der Aufnahme benutzt. Beide Aufnahme-Manifeste nennen denselben Hub-Build.

Identitätsgrenze: Die Aufnahme-Manifeste enthalten **keinen Session-SHA-256 von `granny2.dll`**. Dessen hier genannter Hash bindet die heutigen Original-/TEST-Dateien und das analysierte Ghidra-Programm; die aufgezeichneten Export-RVAs passen dazu. Eine kryptografisch lückenlose Bindung des damals geladenen Granny-Moduls an diesen Hash liefern A1/G1 aber nicht. Der nächste Versuch sollte den tatsächlich geladenen Modulpfad und Dateihash aufnehmen.

[`audit_data.py`](audit_data.py) importiert keine vorhandenen Analysebibliotheken, liest CSV/JSON mit der Python-Standardbibliothek und sichert seine Ergebnisse in [`data_results.json`](data_results.json). [`identity_before.json`](identity_before.json) und [`identity_after.json`](identity_after.json) vergleichen 190 relevante Dateien: sämtliche getrackten Dateien beider Repositories, die beiden importierten Aufnahmen, Annotationen, ausgewählte Spiel-/TEST-Dateien und das ursprüngliche Ghidra-Projekt. Diese Dateien und beide Git-Zustände sind am Ende unverändert. Das ist kein Vollhash aller Spielassets.

Ghidra 12.1.4 war tatsächlich verfügbar. Die Analyse lief auf einer eigenen Projektkopie unter `work/ghidra-copy`, zusätzlich mit `-readOnly -noanalysis`. Kein REA-MCP war in diesem Chat verfügbar oder nötig. Ein eigener PE-Leser verifiziert Modulidentitäten, sechs Import-/Exportadressen und Rücksprung-Konventionen sowie 17 direkte Aufrufstellen gegen die Binärbytes. Kein Spiel wurde gestartet, kein Engine-Patch erstellt, nichts installiert oder übertragen. Disassembly bleibt lokal in `work/binary`; kein dekompilierter Spielcode wurde übernommen.

## 2. Prüfung der tragenden Behauptungen

Die folgenden Dateinamen mit `SH2Perf_20261015_142211_` gehören zu G1. Die vollständigen Rechenwerte stehen in `data_results.json`, die unabhängigen Methoden in `audit_data.py`.

| Behauptung | Urteil, Nachrechnung und Grenze |
|---|---|
| G1 hat 2.542 intakte Frame-Datensätze. | **Bestätigt.** Beide Frame-Dateien stimmen in Frame-ID und Marker zeilenweise überein; Manifest-/Importhashes stimmen. Keine gemeldeten Dateischreib-, Frame-Ring- oder Offset-Lesefehler. Das bedeutet nicht vollständige Objektaggregation. |
| 126.632 Instanzaggregationen fehlen. | **Bestätigt.** 64.622 Uhr- plus 62.010 Sample-Aufrufe fehlen in den Vergleichskategorien. Zusammen exakt Metadatenverlust; nur Probe-Failures, keine Kapazitätsfehler. Objektzählersummen plus Verluste ergeben die Metadatengesamtsummen. |
| Erste Fehler bei Frame 911 / etwa +5,847 s. | **Bestätigt, Bezug präzisiert.** `t_s=5,9389`; erster gespeicherter Frame `t_s=0,0917`; Differenz 5,8472 s. 6.508 gespeicherte Schlüssel haben `first_frame <= 911`; ihre Reihenfolge innerhalb dieses Frames ist unbekannt. |
| Tabelle endet bei 8.134/8.192 Schlüsseln. | **Bestätigt.** 99,29 % Belegung, maximale Suchlänge 128. Eine Suche kann trotz freier Plätze außerhalb ihres Suchfensters scheitern. Die Fehlerzahl ist eine Aufrufzahl, keine Zahl fehlender Schlüssel. |
| Reine Uhr-Historie verdrängt Sample-Erfassung. | **Mechanismus bestätigt.** 5.919 gespeicherte Schlüssel haben in der gesamten Aufnahme keinen erfassten Sample-Aufruf, zusammen 203.180 Uhr-Aufrufe. Nur 2.215 gespeicherte Schlüssel wurden irgendwann gesampelt. Keine Aussage über Leaks oder wirkliche Objektanzahl. |
| Alle Pausenframes sind von Verlusten betroffen. | **Bestätigt.** Marker 3: 1.352/1.352 Frames, je 33 fehlende Uhr- und 33 fehlende Sample-Aggregationen, insgesamt 89.232. Marker 1: 26.281 Fehler in 804/864 Frames. Kein vollständiges Pausenfenster. |
| Die Aufrufzahlen vor dem Tabellenzugriff sind verwendbar. | **Bestätigt für die jeweils definierte Reichweite.** Pausenframe: immer 3.400 Uhr-, 2.842 Sample-, 2.185 Deform- und 2.185 Composite-Aufrufe. Marker-3-Framesummen: 3.842.384 Sample und 2.954.120 Deform. Gesamtmetadaten enthalten zusätzlich einen nicht als Frame ausgegebenen Schlussrest, siehe unten. |
| Aussagen über gespeicherte Schlüssel bleiben trotz neuer fehlender Schlüssel möglich. | **Eingeschränkt bestätigt.** Ein einmal eingefügter Schlüssel bleibt an seiner Position innerhalb der ursprünglichen 128er-Suchstrecke. Keine Löschung/Umplatzierung, auch bei Free. Spätere Find-/Lookup-Aufrufe desselben Schlüssels erreichen ihn weiterhin. Das sichert dessen beobachtete Import-Aufrufe; keine Aussage über verborgene Mutationen, unbeobachtete Freigaben oder auf andere Modelle bezogene Pose-Verknüpfungen. |
| 1.503 stabile Zeigerreihen in der Pause. | **Bestätigt als enges Argument-Beobachtungsergebnis.** Filter: `marker_slot=3`, `frees=used_after_free=0`, `sample_calls>1000`, `all_observed_same==sample_calls`. Zusätzlich unabhängig geprüft: in ALLEN 1.503 Reihen `clock_changed=clock_noprev=0`, `clock_min==clock_max`, `clock_calls==sample_calls`. 613 Reihen enthalten mehrfache Uhr-Aufrufe pro Frame. Dadurch übersteht dieser konkrete Befund den unten beschriebenen Fehler einer allgemeinen Interpretation von `all_observed_same`. |
| Beispiel `0x4E42CEBC`: 1.351 gleiche Sample-Aufrufe. | **Bestätigt.** 1.351 Sample- und Uhr-Aufrufe in jeweils 1.351 Objekt-Frames, Uhr 3995,64746, kein beobachteter Offset-/Pose-Zeigerwechsel. Ein historischer Zeigerwert, keine heute gültige Adresse. |
| Andere Zeiger ändern Uhr/Offset auch in Pause. | **Bestätigt.** 135 gefilterte Marker-3-Reihen haben `clock_changed>0`. `0x34A93C3C`: 35.142 Samples, 33.790 Wiederholungen innerhalb eines Frames, 70.284 geänderte Uhr-Aufrufe, 35.142 Offsetwechsel, letzte Knochenzahl 1. Rund 26 Samples pro Objekt-Frame, nicht exakt 26 in jedem gespeicherten Pausenframe. Die Objektzeile reicht bis Frame 3280; letzter gespeicherter Frame ist 3279. |
| Frees/Reuses sind angemessen getrennt. | **Eingeschränkt.** 708 gespeicherte Schlüssel mit Free, 1.128 gespeicherte Free-Ereignisse, 690 Schlüssel mit anschließend beobachteter Nutzung; 1.569 Free-Importaufrufe insgesamt. Die Differenz 441 betrifft Free-Aufrufe ohne gespeicherten Schlüssel zu diesem Zeitpunkt. Keine Ableitung von Live-Objekten oder logischen Figuren. `frees`/`used_after_free` gelten für die gesamte Zeigerzeile über alle Marker, nicht nur die jeweilige Phase. |
| Deform-Zuordnung in Pause: 2.947.360 same-frame, 6.760 none, null ambiguous. | **Zähler bestätigt, Schlussfolgerung eingeschränkt.** Das sind Klassifikationen des Beobachters. Ein nicht gespeichertes Modell kann dieselbe World-Pose sampeln; der frühe Rücksprung überspringt dann auch die Aktualisierung der Pose-Zuordnung. Null `ambiguous` beweist deshalb keine wirkliche Eindeutigkeit. Test 7 zeigt den Gegenfall. Sein Auftreten in G1 ist nicht nachgewiesen. |
| G1 minus A1 misst Beobachterkosten. | **Nicht belegt.** Mittelwerte bestätigen +0,7886 ms laufend und +0,5579 ms pausiert. Nur ein Off/On-Paar, keine Wiederholung/Rückkontrolle, andere Szenenzähler/Dauern. Kein kausaler Overhead-, Subsystem- oder Einsparungswert. |
| F136 / Cache oder „ein Sample pro Modell und Frame genügt“. | **Offen; pauschale Freigabe verworfen.** Weder Speicherinhalte noch Ergebnisse oder notwendige Seiteneffekte wurden gemessen. Mehrfachverwendung mit wechselnden Offsets ist direkt beobachtet. Flat-Sampling-Schätzungen aus EXP-007 sind keine gemessenen Funktionslaufzeiten und kein Einsparbudget; EXP-007 wurde hier nicht vollständig neu ausgewertet. |

Die Sample-Aggregation deckt in den gespeicherten Pausenframes **98,8388 % der Sample-Aufrufe** ab. Dieser exakt aus den Aufrufzählern berechenbare Wert ist ausdrücklich **keine Abdeckung von Modellobjekten**, keine repräsentative Stichprobe und keine Cachequote. Die 1.503 Reihen summieren 2.859.025 Samples im Objekt-Marker-Schema; daraus wird keine Quote der vollständigen Frame-Population gebildet.

### Neu: unzugeordneter Schlussrest und Phasengrenzen

Die Metadaten enthalten 8.859.975 Uhr- und 7.189.473 Sample-Aufrufe; die Frame-Datei 8.859.603 bzw. 7.189.286. Auch Deform und Composite unterscheiden sich jeweils um 25. **372 + 187 + 25 + 25 = 609 beobachtete Funktionsaufrufe besitzen keine gespeicherte Frame-Zeile.** Keine zusätzlichen Free-Aufrufe oder Tabellenfehler in diesem Rest.

Der Code erklärt dies: `OnFrameEnd` schreibt `t.cur` und leert es. `End` stoppt den Beobachter und schreibt Gesamt-/Objektdaten, schreibt aber ein zuletzt begonnenes `t.cur` nicht als partielle Schlusszeile. `frame_rows_dropped=0` erfasst diesen Fall nicht. Test 9 reproduziert ihn. Bestehende abgeschlossene Pausenframes bleiben verwendbar; eine Aussage „sämtliche Importaufrufe sind phasen-/framegenau enthalten“ wäre falsch.

Marker werden bei Objektaufruf und Frame-Ende getrennt gelesen. Nach Korrektur um Tabellenfehler sind Objekt- minus Frame-Phasensummen bei Uhr/Sample: Marker 0 `+63/0`, Marker 1 `+3212/+2571`, Marker 2 `-640/-297`, Marker 3 `-2263/-2087`; über alle Marker ergeben sich die Schlussreste `+372/+187`. Ohne Ereignisfolge lassen sich Übergangsaufrufe nicht exakt nachträglich umhängen. `first_frame`, `last_frame`, letzte Pose/Knochenzahl, Frees und Callsite-Felder werden zudem als Gesamtwerte in jeder Markerzeile wiederholt.

### Vier unterschiedliche Gleichheiten

1. **Uhrgleichheit:** aktuelle 32 Bit gleich denen des vorherigen beobachteten Uhr-Aufrufs.
2. **Sample-Argumentgleichheit:** Knochenzahl, 64 Offset-Bytes und beide Pose-Zeiger gleich denen des vorherigen Samples. Nicht einmal die Adresse des Offset-Puffers muss gleich sein; verglichen werden seine Inhalte.
3. **Speichergleichheit:** Inhalte hinter Modell-/Pose-/Deform-Zeigern gleich. Nicht erfasst, abgesehen von den 64 Offset-Bytes.
4. **Ergebnisgleichheit und Ersetzbarkeit:** berechnete Ausgaben sowie notwendige Seiteneffekte gleich. Nicht erfasst und aus 1/2 nicht ableitbar.

`all_observed_same` verbindet 2 mit der letzten Uhrvergleichsentscheidung im aktuellen Frame. Gegenbeispiel: `clock(10), sample(A); clock(20), clock(20), sample(A)` ergibt im bestehenden Verfahren beim zweiten Sample „alles gleich“, obwohl die Sample-Uhr von 10 auf 20 wechselt. Umgekehrt kann eine zwischenzeitliche Uhränderung die Flagge verwerfen, obwohl die Uhr beim nächsten Sample wieder den alten Wert hat. **Die dokumentierte enge Definition ist nicht falsch; ihre Lesart als Sample-zu-Sample-Uhrvergleich wäre falsch.** Die zusätzliche Nachprüfung `clock_changed=0` rettet die konkrete 1.503er-Aussage, nicht die allgemeine Cache-Idee.

Weiterer Randfall: Ein fehlerhaft gelesener Offset setzt dieselbe `offsetValid=0`-Repräsentation wie ein Null-Offset. Folgt ein Null-Offset, kann dieser als gleich gelten. Test 5 zeigt das; G1 hat null Offset-Lesefehler, der Befund erklärt seine Verluste nicht.

### Bildzeiten und Messbeeinflussung

| Phase | A1 | G1 |
|---|---:|---:|
| Laufend, Frames | 847 | 864 |
| Laufend, Summe Framezeiten / Mittel | 29,002 s / 34,2408 ms | 30,265 s / 35,0294 ms |
| Pause, Frames | 1.139 | 1.352 |
| Pause, Summe Framezeiten / Mittel | 28,983 s / 25,4464 ms | 35,158 s / 26,0043 ms |
| Pause, DIP / Primitive pro Frame | 2.504 / 525.497 | 2.492 / 522.749 |

G1-Mittel-FPS aus `1000/mean(frame_ms)`: 28,547 / 38,455. Mit dem vorhandenen Quantilverfahren (`sorted[round(p*(n-1))]`, schlimmstes `floor(n/100)` für 1%-low) ergeben sich p50 33,819 / 24,731 ms, p99 53,246 / 36,498 ms und 1%-low 16,284 / 25,529 FPS. Die dokumentierten gerundeten Zahlen stimmen. Das Audit speichert zusätzlich interpolierte Quantile und eine aufgerundete 1%-Gruppe, ausdrücklich getrennt; ihre Abweichungen sind keine Datenfehler.

Speed 90 und Pause Marker 3 stehen als `user_confirmed` in den Annotationen. Marker 1 ist die im Protokoll laufende Phase; eine gesonderte `phase_paused.1=false`-Annotation fehlt in G1. Konstante Primitive in Marker 3 stützen die Bestätigung, beweisen allein aber keinen Simulationszustand. Hardware-, Save-Datei- und perfekte Szenenidentität werden nicht hinzugedichtet.

In der Pause betreffen die vier großen Importklassen zusammen 10.612 Hook-Aufrufe pro Frame. Atomics, Schlüsselabfragen und Offsetkopien sind damit ein plausibler Messfaktor, aber kein aus diesen Daten isolierter Zeitwert. Das G1/A1-Paar und die Python-Simulation messen keine reine Hook-Latenz.

## 3. Begrenzter Engine-Pfad: was statisch neu feststeht

Alle nachstehenden **Exe-RVAs beziehen sich auf den oben vollständig angegebenen Exe-Hash**, alle Granny-RVAs auf den angegebenen Granny-Hash. Die historischen `FUN_…`-Namen bezeichnen Adressen, keine rekonstruierten Originalnamen. Disassembly-Belege: `work/binary/exe`, `work/binary/granny`, `work/binary/granny-workers`; Zusammenfassung der unabhängig überprüften Binärstellen in `binary_results.json`.

### Exe RVA `0x0038E4D0` (`FUN_0078E4D0`)

Die Funktion übernimmt einen Objektkontext O in ECX und vier Stackargumente: Matrixquelle, float32-Uhr, Auswahlindex und Flag. Das `ret 0x10` passt zu dieser Nutzung; Ghidras allgemeines Calling-Convention-Feld allein wurde nicht als Beweis verwendet.

- Bei RVA `0x0038E4E4` wird ECX nach EBX übernommen. `[O+0x18]` und `[O+0x1c]` begrenzen eine Folge von **20-Byte-Datensätzen**. Die Indexrechnung und Adressbildung an `0x0038E5F0–0x0038E61C` wählen einen Datensatz H und schreiben ihn nach `[O+0x4c]`.
- Ist der übergebene Index außerhalb des Bereichs, existiert eine Auswahlstrecke mit Abstand zu einer globalen Position und einem Aufruf bei `0x0038E5E9` zum Ziel RVA `0x003CE2E0`. Das ist Beleg einer abstandsabhängigen Auswahlstrecke, **noch kein gesicherter semantischer LOD-Name**.
- H enthält an `+0` den Modellinstanzzeiger, an `+4` die World-Pose und an `+8` die Local-Pose. O und die Granny-Modellinstanz sind daher ausdrücklich verschiedene Identitäten; auch H kann zwischen Aufrufen wechseln.
- Die Offsetmatrix liegt lokal bei EBP−0x44. Ein Zweig kopiert 16 DWORDs aus der übergebenen Matrixquelle (`0x0038E694–0x0038E69C`). Der andere benutzt `GrannyBuildCompositeTransform4x4` und Matrixmultiplikation (`0x0038E671`, `0x0038E685`), abhängig von H-verbundenen Daten und dem vierten Argument. Ein identischer Matrixquellenzeiger wäre deshalb kein ausreichender Cache-Schlüssel.
- Die Uhr wird aus Stackargument 2 geladen und als float32 an `GrannySetModelClock` übergeben (`0x0038E6A7–0x0038E6B1`). Danach werden H und seine Posefelder erneut geladen; die Knochenzahl kommt aus `GrannyGetSourceSkeleton(H[0])+4` (`0x0038E6C9–0x0038E6D7`).
- Sample-Importaufruf bei **`0x0038E6D9`**, sechs Byte lang, nächster Befehl **`0x0038E6DF`**. Genau dieser gespeicherte Sample-Rücksprung erscheint in allen 7.496 Objekt-Markerzeilen mit Samples. Das ist die dynamische Verbindung zur untersuchten Exe-Stelle; die CSV speichert den ersten Sample-Standort je Schlüssel, keine vollständige äußere Aufrufkette.
- Direkt danach folgt `GrannyFreeCompletedModelControls` bei **`0x0038E6E5`**. Ein Cache darf den Pfad somit nicht allein als reine Ausgabeberechnung betrachten.
- Anschließend wird eine verkettete Struktur über `[O+0x28]` durchlaufen. Ein verknüpfter Objektkontext aus `[Knoten+0x4c]`, ausgewählter Index, aus Transformdaten gebildete Matrix und dieselbe Uhr können zur **rekursiven** Selbstaufrufstelle **`0x0038E82F`** gelangen. Derselbe Import-Rücksprung unterscheidet Wurzel- und rekursive Aufrufe nicht.

### Unmittelbare Aufrufer: Uhr und geteilte Kontexte

17 direkte Call-Stellen in zwölf Funktionen einschließlich Selbstrekursion sind in der gespeicherten Ghidra-Analyse bekannt und gegen die wirklichen `E8`-Ziele im Exe geprüft. Das ist keine Behauptung, alle möglichen indirekten Aufrufer gefunden zu haben.

| Exe-Funktion / Call-RVA | Präziser nachgewiesene Herkunft |
|---|---|
| `FUN_007965E0`, Call `0x00396764` | Uhr aus globaler Exe-RVA **`0x006E8BD0`**, geladen bei `0x00396748`; O aus `[Kontext+0x10]`. Matrixquelle ist der Rückgabewert eines indirekten Aufrufs über den Slot `+0x44` des Objekts `[Kontext+0xc]`. **Die Bedeutung und das Laufzeitziel dieses Slots bleiben offen.** |
| `FUN_0076BF10`, Call `0x0036BF61` | Uhr aus eigenem Stackargument `[EBP+0x10]`, Matrixquelle aus `[EBP+0xc]`, O aus dem eigenen ECX-Kontext. Die Uhr ist bis zu dieser Grenze verfolgt, nicht bis zur gesamten Spielsimulation. |
| `FUN_0076B210`, Call `0x0036B6F6` | Konstanter Uhrwert 0, O aus `[ESI+0x14]`, Matrixquelle `ESI+0x1c`; bedingt durch Feld `+0x5c`. |
| `FUN_004D5630` / `FUN_004D59F0`, Calls `0x000D5774` / `0x000D5B51` | Beide laden O aus derselben globalen Exe-RVA **`0x00EB0830`** und übergeben 0 als Uhr sowie lokal gebildete Matrizen. Die Matrixbildung benutzt Felder des jeweiligen äußeren Kontexts. Ein modellbezogener Kontext ist damit nicht zwangsläufig an einen eindeutigen äußeren Kontext gebunden. |
| `FUN_00772FA0`, Calls `0x003731BA`, `0x00373266`, `0x00373307` | Gemeinsames Uhrargument `[EBP+0x28]`; verschiedene Objektkontexte. Die beiden späteren Matrixquellen stammen aus `GrannyGetWorldPose4x4` eines anderen Posekontexts. |

Die übrigen direkten Aufrufer sind in [`binary_results.json`](binary_results.json) inventarisiert; die Untersuchung wurde nicht zur Vollanalyse ihrer Fachlogik ausgeweitet. **Zugriffe auf dieselben globalen Modellkontext-Speicherstellen sind statisch belegt; deren Laufzeitbelegung und die Benutzung derselben konkreten Granny-Modellinstanz durch mehrere logische Soldaten in G1 bleiben offen.** Ein äußerer Kontext ist noch keine bewiesene Figuren-ID. Die Beobachtung rund 26 Samples auf einem Zeiger kann außerdem Rekursion, Anbauteile oder mehrere Render-Verwendungen enthalten.

Gezielte Auflösung der Grenze: In einem späteren begrenzten Ereignisfenster O, H, Sample-Instanz, äußerer Rücksprung, Rekursionstiefe und den tatsächlichen Ziel-RVA des Slots `+0x44` zusammen erfassen. Keine alten CSV-Adressen dereferenzieren und keinen ungesicherten Klassennamen zuweisen.

### Granny-Grenze, Weiterleitung und Deformation

Der eigene PE-Test bestätigt alle sechs dekorierten Exporte samt IAT-RVA und `ret N`: Uhr 8 Byte, Sample 20, Deform 24, Composite/Free jeweils 4. Sample ruft intern Granny-RVA `0x0004F700`, dieses mit einem zusätzlichen Nullargument `0x00002A70`. Diese Verbindung ist statisch; keine individuelle dynamische Zuordnung zu den EXP-007-Kurvenhelfern wurde aufgezeichnet.

Der Uhr-Worker bei Granny-RVA `0x00002640` schreibt Kontroll-Uhrfelder und akkumuliert die Differenz von neuer und bisheriger Uhr (`0x000026A0–0x000026B3`). Das ist keine reine Setter-Variable ohne weitere Zustandswirkung. Fehlende Control-APIs, veränderte Kontrolllisten/Weights/Clocks, dieselben Pose-Zeiger mit anderem Inhalt und Änderungen durch vorausgehende Samples bleiben plausible nicht beobachtete Eingaben. Ihr Auftreten bei den 1.503 Reihen ist nicht bewiesen.

Der Composite-Getter hat mehrere Exportnamen an derselben Adresse; das Ghidra-Label `_GrannyControlModelsNext@4` bezeichnet nicht exklusiv die Funktion. Der Exportabgleich bestätigt `_GrannyGetWorldPoseComposite4x4Array@4` an Granny-RVA `0x00052BB0`, dessen Worker `0x00032300` den Zeiger an `worldPose+8` zurückgibt.

Die bekannten Deform-Calls bei Exe-RVA `0x0038CA8C` und `0x0036B75A` benutzen diesen zurückgegebenen Matrixpuffer. Im ersten Fall kommt die World-Pose aus `[ [O+0x4c] +4 ]`; beim zweiten aus dem entsprechenden Halter des Kontexts `[ESI+0x14]`. Der Deformer ist ein anderer Zeiger, kein Modellargument. Der Worker bei Granny-RVA `0x00033D40` verzweigt zu indirekten Zielen `[deformer+8]` bzw. `[deformer+4]` (Call-RVAs `0x00033DAE` / `0x00033DCA`). **Welches dieser Ziele bei welchem G1-Ereignis zur Schleife RVA `0x00008810` führte, bleibt dynamisch unbewiesen.** Ein beobachteter Funktionszeiger plus vollständiger aktueller Pose-Verknüpfung würde diese konkrete Grenze schließen.

Im Hub erfolgen Zähleraktualisierung und Beobachtung vor den Originalaufrufen, beim Composite-Ergebnis danach. Jede der sechs Thunks enthält genau eine Originalweiterleitung; die Uhr wird als rohe 32 Bit transportiert, das Composite-Ergebnis zurückgegeben. Ein vorhandenes natives `granny_observer_test.exe` wurde zusammen mit seiner **Fake-Granny-DLL** in `work/standin` kopiert und dort mit lokalem TEMP ausgeführt: **0 Fehler**. Das unterstützt die ABI-/Weiterleitungsprüfung. Es ist weder ein Lauf mit dem echten Spiel noch ein Beweis vollständiger Verhaltensneutralität aller Instrumentierung; das vorhandene Testbinary wurde nicht neu gebaut.

## 4. Ausführbarer Reproduktionsnachweis

`python -I analysis\observer_repro.py` → **9 Tests, 0 Fehler**. Festgehalten in [`repro_results.json`](repro_results.json); Basis ist der tatsächliche Hub-Quelldateihash `2018c612b5ff372982655fbcb09c60c88cce5edadb4c4a124c2e743b2b96bcd8`. Ein abweichender Quellstand wird abgewiesen. Das ist eine nachvollziehbare Python-Übertragung der relevanten Regeln, kein ausgeführter Produktions-Hook.

| Test | Erwartetes und erhaltenes Ergebnis |
|---|---|
| 1: 129 gezielt kollidierende Schlüssel | Der 129. scheitert bereits bei **128/8.192** belegten Plätzen am Probe-Limit. Alle 128 gespeicherten Schlüssel bleiben auffindbar. Alternatives Vergleichsmodell erfasst 129 erste und 129 gleiche zweite Sample-Tupel. |
| 2: echte Schlüssel-/Häufigkeitsverteilung, synthetische Reihenfolge | 8.134 echte gespeicherte Schlüssel + **1.024 ausdrücklich synthetische** weitere Uhr-Schlüssel = **9.158** kumulierte Schlüssel. Uhr-Historie zuerst: nur **1.249/2.215** Sample-Schlüssel aufgenommen, gewichtete 2.900.150 Sample-Aufrufe verloren. Sample-Schlüssel zuerst: **2.215/2.215**, null Sampleverluste. Keine dieser Zahlen rekonstruiert die tatsächlichen 126.632 G1-Fehler. |
| 2: separates alternatives Stream-Modell | 203.180 echte aggregierte Uhr-only-Aufrufe in künstlichen Gruppen, 1.024 zusätzliche Uhr-Aufrufe, zwei künstliche Sample-Frames mit Wiederholungszahlen aus den Pausenaggregaten. **210.768 Uhr-, 6.564 Sample-Aufrufe; 2.215 unbekannte Erstvergleiche, 2.860 verschiedene, 1.489 gleiche beobachtete Tupel; keine Zustandsüberläufe/History-Evictions.** Sample-Historie bleibt bei 2.215 Schlüsseln. |
| 3: Uhrgleichheits-Gegenbeispiel | Das bestehende Flag kann trotz unterschiedlicher Sample-Uhr wahr sein und trotz gleicher Sample-Uhr falsch. Der Alternative-Vergleich benutzt die am jeweiligen Sample vorliegende Uhr. |
| 4: Free/Reuse und fehlender aktueller Uhr-Aufruf | Nach beobachtetem Free keine Gleichheitsübernahme; erste neue Vergleiche und fehlende aktuelle Uhr werden **unknown**, nicht gleich. |
| 5: fehlerhafter Offset gefolgt von null | Bestehender Ausdruck kann Gleichheit ergeben. Alternative unterscheidet null/Bytes/Leseverlust und meldet unknown. |
| 6: absichtlich zu kleine Budgets, Transportlücke, Schlussrest | Clock-Überlauf, History-Verdrängung, fehlende Uhr, Transportverlust und partieller Schlussrest erhalten getrennte Zähler. Transportlücke invalidiert Vergleiche, weil sie ein Free enthalten könnte. Alle vier Samples sind unknown. |
| 7: ausgelassener Sample-Aufruf auf gemeinsamer World-Pose | Bestehender Ablauf kann trotz zweitem Modell `link_frame` behalten. Belegt eine Grenze des Klassifikators, nicht deren tatsächliches Auftreten in G1. Die Alternative dieses Audits behauptet keine Pose-/Deform-Verknüpfung. |
| 8: unabhängiges Orakel, 30.000 deterministische Ereignisse | 11.991 Samples = **633 equal + 85 different + 11.273 unknown**. Jeder equal/different-Befund gegen eine unbeschränkte Vergleichshistorie geprüft. 8.041 History-Verdrängungen, 6.171 Clock-State-Überläufe und 593 Offsetfehler explizit ausgewiesen. |
| 9: Stop zwischen zwei Frame-Enden | Sieben Gesamtaufrufe, vier in abgeschlossener Frame-Zeile, drei im nicht geschriebenen Rest; alter Frame-Drop-Zähler bleibt null. |

**Echte Grundlage:** `workload_distribution.json` enthält ausschließlich die 8.134 erfassten Schlüssel mit tatsächlichen aggregierten Häufigkeiten. **Synthetisch:** Reihenfolge, Gruppen-/Framezuweisung, Zusatzschlüssel, Clockwerte und Simulationsargumente. Die Wiederholungsverteilung benutzt `floor(sample_calls/sample_frames)` pro gefilterter Pausenreihe; Phasengrenzen können diesen Quotienten verzerren. Sie ist ein Stressprofil, keine rekonstruierte pro-Frame-Verteilung. Schlüssel werden nur als Integer verwendet.

Das verbesserte Prinzip trennt vollständige Aufrufzähler, kurzlebige Uhr-Zustände und ausschließlich bei Sampling angelegte Vergleichshistorie. Speicherverdrängung führt zu einem kenntlich gemachten Neustart/unknown; Free invalidiert die Historie; ein Leseverlust ist kein Nullwert. Jede Sample-Entscheidung landet genau in equal/different/unknown. Gegen einen tatsächlichen Ereignisverlust helfen unabhängige Eingangszähler und ein ausdrücklich ungültiges Vergleichsfenster.

Die Python-Dictionaries sind bewusst eine semantische Referenz, **keine Empfehlung für Allokationen oder unbegrenzte Hash-Suchen im Hook**. Es gibt hier weder eine implementierte Produktionswarteschlange noch Messungen ihrer Latenz. Für Pose-Verknüpfungen wären zusätzlich generationssichere Zustände und eine Sperre/Invalidierung bei ausgelassenen Sample-Ereignissen nötig. Auch eine korrekte Alternative beweist nur Gleichheit der benannten beobachteten Tupel, niemals gleicher Speicherinhalte oder Engine-Ergebnisse.

## 5. Vergleich der zwei nächsten Wege und genau eine Empfehlung

| Weg | Erkenntniswert | Aufwand und Messbeeinflussung | Entscheidung |
|---|---|---|---|
| Enger Animations-/Ergebnisvergleich | Prüft die fehlende Verbindung zwischen gleichen beobachteten Sample-Eingaben und tatsächlichen Pose-Ausgaben. Ein Gegenbeispiel verwirft einen Cache-Schlüssel unmittelbar. | Begrenzte, nachprüfbare Puffergrenzen; kleine Auswahl aktueller Modellgenerationen; zusätzliche Kopien/Vergleiche nach ausgewählten Samples. Einfluss durch Menge und Rate begrenzbar, später kontrollieren. | **Empfohlen.** |
| Weitere Aufrufpfad-/Zeitlokalisierung | Verbindet äußere Kontexte/indirekte Ziele und misst möglicherweise inklusive Zeitanteile. Kann heißen Code priorisieren. | Stacks oder zusätzliche Eintritt-/Austrittsmessungen bei häufigen Aufrufen; Timer-/Rekursionsaufwand. Auch ein teurer Aufruf kann notwendig sein. | Für die gegenwärtige Entscheidung nachrangig. Kein paralleler nächster Aufnahmeauftrag. |

### Vorformulierter nächster Versuch: enger Ergebnisvergleich

**Frage:** Erzeugen wiederholte Samples am Exe-Rücksprung RVA `0x0038E6DF` innerhalb derselben beobachteten Modellgeneration bei identischem am Sample erfasstem Tupel tatsächlich bitgleiche World-/Composite-Pose-Matrizen? Gibt es ein Gegenbeispiel gerade bei mehrfacher Verwendung im selben Frame?

**Vorbereitung vor irgendeiner neuen Spielaufnahme:** Einen kleinen, getrennten Beobachterprototyp prüfen, der die hier nachgewiesenen Tabellen-, Uhrvergleichs- und Schlussrestprobleme nicht übernimmt. Keine komplette Neuerstellung des allgemeinen Hubs nötig. Die Längen/Layouts der ausgewählten Pose-Ausgabepuffer zuerst gegen diese Binärversion und vorhandene BoneCount-/Array-Getter verifizieren. Deren Exporte existieren; ihr vollständiger Puffervertrag ist in diesem Audit noch nicht untersucht. Falls dieser Nachweis fehlt, Versuch noch nicht aufnahmebereit. Native Weiterleitungs-/Free-/Kollisions-/Überlaufprüfungen einschließlich expliziter unvollständiger Schlussframes sind Pflicht.

**Auswahl und Reichweite:** Höchstens 16 aktuell beobachtete Modellgenerationen, deterministisch erst nach zehn vergleichbaren Samples zulassen, Gruppen getrennt nach einmaliger und mehrfacher Verwendung pro Frame. Aufnahmeadressen aus G1 niemals übernehmen. Auswahlregeln, abgewiesene Kandidaten, budgetbedingt nicht verglichene Aufrufe und nach Free neu vergebene Generationen mitzählen. Die Auswahl soll eine Aussage über diese Kandidaten liefern, keine Population hochrechnen. Speicher und Ausgaberate werden vorab fest begrenzt; Erreichen eines Limits invalidiert betroffene Vergleiche.

**Je ausgewähltem Sample erfassen:** monotone Ereignisnummer, Frame/Marker, Thread, Beginn/Ende bzw. partielle Aufnahmegrenze; Modellinstanz mit beobachteter Generation; aktuell bestätigte Uhrbits und Zahl zwischenzeitlicher Uhrwechsel; Knochenzahl; komplette Offset-Bytes einschließlich null/fault-Status; Local-/World-Pose-Zeiger; Sample-Return-RVA. Für die genaue Stelle zusätzlich nur den ohnehin bekannten aktuellen O-/H-Kontext, sofern ohne zusätzliche unbewiesene Dereferenzierung erfassbar. Keine breiten Stacktraces als zweites Teilprojekt.

**Nach dem unverändert ausgeführten Originalsample:** World- und Composite-Matrixarrays unmittelbar nach Rückkehr, vor `GrannyFreeCompletedModelControls`, in vorab dimensionierte private Vergleichspuffer kopieren. Umfang anhand aktuell geprüfter Pose-Knochenzahl/Allokationsgrenze validieren; weder blindes `bone_count*64` aus CSV noch rohe Struct-Paddingbytes. Bytevergleich über alle gültigen Matrizen, nicht nur Hashgleichheit. Bei Unterschied: Anzahl/erste Position unterschiedlicher Komponenten und begrenztes Belegpaar sichern; NaN/Inf und numerische Abweichung zusätzlich berichten, keine nachträglich gewählte Toleranz. Local-Pose-/Control-Seiteneffekte bleiben separate, klar benannte Grenzen. Kein Sample überspringen, keine zusätzliche doppelte Originalberechnung auslösen.

**Gültigkeit:** Alle Eingangszähler müssen mit equal/different/unknown/ausdrücklich ungeprüft samt Schlussrest aufgehen. Kein Gleichheitsurteil über Free, Identitätslücke, fehlende Uhr, falsche Puffergrenze, Lesefehler, Budget-/Queueverlust oder Threadwechsel hinweg. Ein positiver Kandidatenbefund braucht mindestens 100 gültige vergleichbare Paare pro ausgewählter Generation in der bestätigten Pause und eine unabhängige Wiederholung. Beginn/Ende und Markerränder getrennt auswerten. Erst nach bestandenen Offline-/nativen Tests den Nutzer um den begrenzten neuen Lauf mit passenden Off-Kontrollen bitten. Kein Lauf mit dem bekannten G1-Beobachter. Off/On-Zeiten dienen zunächst nur der Prüfung auf störenden Messeinfluss; bei relevantem Einfluss (vorab Grenzwert festlegen, etwa >5 % im wiederholten Kontrollvergleich) Umfang reduzieren, keine Einsparungsbehauptung daraus ableiten.

**Vorab festgelegte Schlussfolgerungen:**

- Gleiche beobachtete Tupel, unterschiedliche Ausgaben: dieser Cache-Schlüssel ist widerlegt; das erste valide Belegpaar reicht. Zuerst fehlende Zustandsdimension eingrenzen.
- Nur bei verändertem Kontext/Uhr/Offset unterschiedliche Ausgaben: ein Modellzeiger-/Frame-Schlüssel ist ungeeignet; differenzierter Schlüssel bleibt lediglich Kandidat.
- Alle gültigen Vergleichspaare gleich: eng begrenzter Output-Wiederholungsbefund. **Noch keine sichere Skip-/Cache-Freigabe**, weil Kontrollzustand, Local-Pose-Seiteneffekte, Lebenszeiten und Verbraucheranforderungen zusätzlich geprüft werden müssen. Erst danach wäre ein gesonderter ersetzender Versuch sinnvoll.
- Verlust, unsichere Identität, keine ausreichenden gleichen Paare oder störender Messeinfluss: Versuch ohne positiven Gleichheitsentscheid; keinen Anteil unbekannter Aufrufe als gleich ausweisen.

## 6. Prüfungen, Dateien und Einstieg

- `audit_data.py`: Manifest-/Import-/Binäridentität, unabhängige CSV-Nachrechnung, Filter, Grenzreste, Phasen, Verteilungsgrundlage.
- `observer_repro.py`: neun ausgeführte Tests einschließlich adversarialer Kollisionen, >8.192 Schlüsseln, Free/Reuse, mehrfachen Samples, Gegenbeispielen und Orakelvergleich.
- `AuditPath.java`: ausschließlich Instruktionen/Referenzen aus einer Ghidra-Arbeitskopie; keine Decompilation, keine Datenbankänderung im Original.
- `verify_binary.py`: sechs Import-/Export-/Stackbereinigungsprüfungen, Sample-Rücksprung und 17 direkte Call-Ziele gegen Binärbytes.
- `run_audit.ps1`: ausgeführt **mit und ohne `-ExportBinary`**, erfolgreich. Ergebnisse reproduzierbar; 190 geprüfte Eingabedateien und Git-Zustände unverändert.
- [`HANDOFF.md`](HANDOFF.md): kurze Befehle und Grenzen für den nächsten frischen Agenten.

Gesamtaufruf aus diesem Arbeitsordner: `powershell -NoProfile -ExecutionPolicy Bypass -File .\analysis\run_audit.ps1 -ExportBinary`. Python-Tests sind ohne Spielstart und ohne Ghidra ausführbar; der Binärteil braucht die lokalen Eingänge und entweder die bereits erzeugten lokalen Exporte oder Ghidra.

Quellstellen für den Beobachterbefund: `Stronghold2AnalyseHub/Stronghold2AnalyseHub/core/granny_observer.cpp`, Hash oben; `Hash/Find/Lookup` Zeilen 153–187, Uhr 206–233, Sample 235–286, Pose-Link 319–333, Free 354–369, Thunks 373–403, CSV-Felder 460–484, Frame-Ende 633–650, Stop 667–700. Ergänzend `core/capture.cpp` (Stop ruft `GrannyObserver::End` auf) und `core/metrics.cpp` (Frame-Ende und atomarer Marker). Zu prüfende frühere Aussagen: `SH2-Perf/docs/evidence/EXP-008R_G1_PARTIAL.md`, `docs/FORMATS/GRANNY_OBSERVER.md`, `docs/FINDINGS.md` F137–F139/F146 sowie der aktuelle Handoff-Anfang. Sie wurden nicht geändert.

Die Deliverable-Kopie unter `outputs/analysis` enthält eigenen Code, Bericht und abgeleitete Nachweise. Der lokale Disassembly- und Ghidra-Arbeitsbestand bleibt außerhalb des Pakets unter `work/`. Keine Veröffentlichung, kein Push und keine Produktionsänderung sind Bestandteil dieses Ergebnisses.
