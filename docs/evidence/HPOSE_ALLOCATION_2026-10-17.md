# H-Container: Kapazitaet, Byteanforderung und Transfer

> Kurzfassung: Ein statischer Pfad verbindet logische Recordanzahl, Wachstumsreserve, exakt 20*n angeforderte Bytes und die anschliessenden Containerstores. Physische Heapreserve, Poselebensdauer und Freigabegenerationen bleiben offen. Keine Spielausfuehrung oder Optimierung.

Datum: 2026-10-17. Forschungsbasis `deb556d`; [Arbeitsauftrag](../tasks/HPOSE_ALLOCATION_2026-10-17.md).
Folgt auf [Erzeugung/Auswahl](HPOSE_CREATION_2026-10-17.md). Alle Codeadressen sind Exe-RVAs.

## Identitaet und getrennte Groessen

- Exe SHA-256 `f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b`, Basis `0x00400000`.
- Granny SHA-256 `94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd`.
- V bezeichnet hier den Containerkontext, im bekannten Erzeugungspfad V = O+0x18. B=V[+0], E=V[+4], K=V[+8]
  sind Anfang, logisches Ende und Kapazitaetsende. Es sind keine H-/Posefelder.
- s=(E-B)/20 bezeichnet belegte Records, k=(K-B)/20 die Kapazitaet, t die angeforderte logische Anzahl und n die
  gewaehlt angeforderte Kapazitaet. Die fruehere Recordanzahl C wird hier t genannt; V ist eine andere Identitaet.
  Formeln fuer Bereichszaehler setzen geordnete, durch 20 teilbare, signed-repraesentierbare Differenzen voraus.

## Resize und Wachstumswahl

`0x38DC70` vergleicht s mit t. s==t laesst den Bereich unveraendert; s>t erreicht den hier nicht weiter untersuchten
Schrumpfhelfer `0x38CE90` (Call `0x38DCA6`, End-Store `0x38DCAF`). Bei s<t geht delta=t-s an Grow `0x38D6D0`
(Argument bei `0x38DCBE`, Call `0x38DCC1`). Mit M=0x0CCCCCCC gilt fuer gueltige s<=t<=M:

- Groessenfehlerpfad: unsigned s > M-delta erreicht den Import `std::_Xlength_error` bei `0x38D700`.
  M-delta ist Maschinenarithmetik, keine zusaetzliche allgemeine Validierung frei erfundener delta>M.
- needed=s+delta=t. Wenn needed<=k, wird nicht neu allokiert.
- Sonst h=k>>1, candidate=k+h falls k<=M-h, andernfalls candidate=0; n=max(needed,candidate).
  Call `0x38D73E` erreicht Reserve `0x38D500`. Es gibt somit eine Wachstumsreserve, keine pauschale Gleichheit n=t.

## Reserve und genaue Importgrenze

Reserve prueft n<=M bei `0x38D530`/`0x38D536`, sonst Fehlerimport bei `0x38D53D`.
Wenn die bestehende Kapazitaet bereits reicht, bleibt der Container unveraendert. Andernfalls ruft `0x38D563`
den Helfer `0x39A840` mit n auf. Der dabei uebergebene Kontext V+0xC ist weder H+0xC noch ein Posefeld;
der unmittelbare Helfer liest diesen ECX-Kontext nicht.

Der Helfer hat einen separaten n==0-Rueckgabepfad mit Ergebnis null. Fuer 1<=n<=M berechnet er exakt 20*n,
ohne lokalen Cookie oder Aufrundung, und ruft an `0x39A85F` den Thunk `0x40FBB6` auf. Dieser springt direkt
ueber IAT-RVA `0x500240`; die PE-Importtabelle benennt `msvcr100.dll`, `??2@YAPAXI@Z` (operator new(unsigned int)).
M=214748364 ergibt maximal 4294967280=0xFFFFFFF0 angeforderte Bytes, ohne Multiplikationsueberlauf.
Das beweist weder, dass eine solche Allokation praktisch moeglich ist, noch ihre tatsaechliche Heapreserve.

n>M oder ein null-Rueckgabewert des new-Aufrufs fuehren zum lokalen Fehlerpfad `0x39A86B` und zum
`_CxxThrowException`-Thunk `0x40FBBC` (Call `0x39A88F`, IAT `0x500244`). Der Exception-Konstruktorimport
liegt bei IAT `0x500218`; sein Source-Klassenname wird nicht rekonstruiert. Ein direkt aus dem CRT-new
kommender Throw und die Exception-/SEH-Abwicklung liegen ausserhalb dieses Nachweises.
Im gueltigen allokierenden Reservezweig n>k>=0 ist n==0 nicht erreichbar; der Nullfall des Einzelhelfers
beweist daher keinen akzeptierten null-Puffer bei einer vergroessernden Reserve.

## Erfolgreicher Transfer und Stores

Nach Rueckgabe A erreicht Call `0x38D581` den Helfer `0x38CF30`: pro altem Record werden fuenf 32-Bit-Werte
bei Offsets 0/4/8/12/16 in aufsteigender Reihenfolge kopiert, Quell-/Zielschritt jeweils 20. Die referenzierten
Granny-Objekte werden dabei nicht kopiert oder neu erzeugt. Das ist keine vollstaendige Lebensdauer-/Besitzgarantie.
Danach erreicht `0x38D5A6` bei altem B!=0 den unsized-delete-Thunk `0x40FB8C`, IAT `0x500224`, ohne Byteargument.
Erst danach folgen diese drei Stores am selben V-Kontext:

- `0x38D5BD`: V+8 = A+20*n, neues Kapazitaetsende.
- `0x38D5C3`: V+4 = A+20*s, bisheriges logisches Ende.
- `0x38D5C6`: V+0 = A, neuer Anfang.

Die Stores sind keine atomische Gesamtaktualisierung. Die Adressadditionen besitzen hier keinen lokalen Wrap-Test.
Resize initialisiert anschliessend seine t-s hinzugefuegten Records ueber `0x38D040` (Call `0x38DCF0`) mit fuenf
Nullfeldern, ohne Granny-Aufruf, und setzt das logische Ende bei `0x38DD18` auf B+20*t im aktuellen Puffer.
Reserve erhaelt s; Resize setzt t. Genutzte Bytes 20*t und angeforderte Kapazitaetsbytes 20*n sind verschieden.
Eine Arrayverlagerung aendert H-Adressen; kopierte Posezeigerwerte sind keine neue Posegeneration. Ob und wann
O+0x4C in allen Aufrufpfaden nachgefuehrt wird, ist hier nicht vollstaendig bewiesen. Kein UAF wird daraus behauptet.

## Reproduktion, eigenes Modell und Grenze

```text
python -I tools/hpose_allocation_verify.py --exe <original-exe> --dll <original-dll>
python -O -I tools/hpose_allocation_verify.py --exe <original-exe> --dll <original-dll>
python -I tools/test_hpose_allocation.py
python -I tools/hpose_native.py
python -I tools/run_checks.py
```

Neun versionierte Funktionsfingerprints und fuenf Importidentitaeten werden direkt gegen die PE geprueft.
Sieben neue synthetische Tests bestehen normal und unter -O, einschliesslich fehlender/doppelter Eintraege,
veraenderter Bytes, ungueltiger Bereiche und unbekannter Builds. Fingerprints bestaetigen Byteorte, nicht die Deutung.
Sol analysierte, der Projektleiter pruefte mit dem bisherigen unabhaengigen PE-Parser erneut alle 289 exportierten
Instruktionsbytes, direkte Aufrufkanten, Importthunks und die drei Storeziele. Ein frischer Reviewer rekonstruierte
Wachstumsformel, signed-Division und Storeausdruecke unabhaengig; kein relevanter Defekt im begrenzten Modell gefunden.

Ghidra-Reproduktion: bestehendes `hpose_creation.java` mit lokalem Ausgabeordner und VAs `0078D500`, `0078D6D0`,
`0078DC70`, `0079A840`, `0078CF30`, `0080FB8C`, `0080FBB6`, `0080FBBC`, `0078D040` auf der getrennten Kopie,
`-readOnly -noanalysis`. Der finale Export stimmt in allen neun Fingerprints mit dem Manifest ueberein.
Rohmaterial und lokale Ergebnisse bleiben in ignoriertem `build/hpose-allocation/`.

`allocation_request.h` ist ein eigenes, allokationsfreies Zahlenmodell fuer den Einzelhelfer: Nullanforderung,
gueltige 20*n-Anforderung oder eigener Ablehnungsstatus. Zehn zusaetzliche Literalgrenzfaelle bestehen im nativen
Host (jetzt 6393 Pruefbedingungen). Das modelliert weder den kompletten Growpfad noch Original-Throws/Allocatorausfuehrung.
Seine Byteanforderungsdomaene ist weiter als die signed-Bereichsdomaene von `select_record`; beide bleiben getrennt.

Integrierte lokale Abnahme: 12/12 regulaere Pruefgruppen bestanden; Originaldatei-Verifier auch mit optimiertem
Python erfolgreich; nativer Win32-Host mit 6393 Pruefbedingungen ohne Fehler und CTest 1/1 bestanden.
Keine neue GitHub-CI-Abnahme oder Performancepruefung wird damit behauptet.

Die PE benennt den nominalen CRT-Import. Geladene CRT-Identitaet, new-handler, nutzbare Blockgroesse sowie intern
committete/reservierte Heap-/OS-Groessen wurden nicht gemessen. Ebenso bleiben vollstaendige Listenherkunft,
Freigabe/Reuse und Pose-Ausgabegenerationen offen. Originaldateien, Rohdaten und originale Ghidra-DB unveraendert;
keine Originalausfuehrung, Spielaufnahme, Installation oder Performanceaussage.

## Genau ein naechster Versuch

Die drei Free-Imports fuer Instanz/World-/Local-Pose besitzen in der aktuellen Referenzinventur Aufrufstellen
`0x38E3F9`/`0x38E403`/`0x38E40D` im Kandidaten `0x38E3C0`. Dies ist nur eine Referenzinventur.
Als naechsten statischen Schritt deren Argumente bis zu H-Feldern und den zugehoerigen Aufrufern verfolgen:
welcher Cleanup-/Wiederverwendungspfad beendet welche Posen und was geschieht mit ausgewaehlten H-Zeigern?
CRT-Heap-Rundung bleibt externe Grenze; sie wird fuer diesen naechsten Besitz-/Lebensdauernachweis nicht priorisiert.
