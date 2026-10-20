# Forschungscheckpoint F185: Veroeffentlichung und Abnahme

> Kurzfassung: Die bisher lokalen Nachweise/Werkzeuge bis F185 und der kompakte Projektleitungseinstieg werden ueber einen eigenen Forschungs-PR veroeffentlicht. Lokale spielfreie Checks und Win32-Vertrag bestehen; Merge setzt gruene GitHub-Pruefungen des finalen PR-Stands voraus. Kein Performance- oder Live-Lesebeweis.

Datum 2026-10-20. Quellcheckpoint `e47a59e95d8de1f123e7b7dc55d9d344f42c48ee`, Branch `hpose-allocation-proof`.
[PR #4](https://github.com/crycodebaby/Stronghold2PerformanceResearch/pull/4) enthaelt die Integration und
die zugeordneten GitHub-Checks. Den tatsaechlichen Mergecommit und finalen Status dort pruefen; diese Datei
behauptet keine zukuenftigen CI-Ergebnisse.

## Inhalt und Herkunft

Gegen Forschungs-main `898a394` liegen beim Start 18 lokale Commits ohne Rueckstand vor; Arbeitsbaum sauber.
Enthalten sind T2/CSV-Haertung, H-Pose-Erzeugung/Allokation/Cleanup/Ressourcenkandidaten, bedingte
Ausgabeschreibbereiche, Generations-/Allocator-/interne Provenienznachweise bis F185, eigene Verifier/Tests,
Win32-Adressarithmetik und Wissenskarte/Uebergabe. Die Publikationsnachpflege selbst aendert nur Dokumentation.

Die vorhandene bereinigte Forschungshistorie wird normal fortgesetzt. Merge-Commit statt Squash/Neuexport/
Rewrite erhaelt die in Evidenz referenzierten Forschungscommits. Discord-Warnungs-PR #3 bleibt ein separater Auftrag.

## Lokale Pruefung

- `python -I tools/run_checks.py`: am 2026-10-20 frisch 16/16 regulaere spielfreie Pruefgruppen bestanden.
- `python -I tools/hpose_native.py`: eigener Win32 Release-Host, 6393 Bedingungen/0 Fehler;
  abgeschlossener schema-1-JSON-Bericht unter ignoriertem `build/hpose-native/results.json`.
- Datum und Grenzen der frueheren Originaldatei-/Argumentgates stehen in den jeweiligen Nachweisen.
  Diese Veroeffentlichung fuehrt keine Originalfunktion oder Spiel-DLL aus und ersetzt diese Analysen nicht.
- Alle 18 ausstehenden Commits nutzen bei Autor/Committer noreply-Identitaeten. Schnellpruefung der
  hinzugefuegten Zeilen fand kein persoenliches Users-Pfadmuster. Die geaenderten versionierten Dateiinhalte
  umfassen rund 670 kB, keine Spielbinaries/Ghidra-Datenbanken. Das ist kein allgemeiner Geheimnisscanner.
- Lokaler persoenlicher Pfadindex und ausgefuellter Startprompt sind Git-ignoriert; deren generische
  Vorlage und die benoetigten Kontextdokumente werden veroeffentlicht. Rohdaten/Originale/DBs bleiben lokal.

## GitHub-Abnahme und Integrationsregel

Workflow `checks` auf dem finalen PR-Head muss sowohl Game-free checks als auch H-pose native contract
(Win32 Release) erfolgreich abschliessen. CI hat nur das Forschungsrepo: der dokumentierte Hub-abhaengige
Einzelfall in test_audit_workdir kann dort uebersprungen sein, nicht als durchgefuehrt ausgeben.
Keine benoetigte Originalinstallation oder Rohaufnahme und keine Abschwaechung eines Gates.

Der unveraenderte Quellcheckpoint `e47a59e` hat am 2026-10-20 bereits beide `checks`-Laeufe erfolgreich
abgeschlossen: [Branch-Push 39344767283](https://github.com/crycodebaby/Stronghold2PerformanceResearch/actions/runs/39344767283)
und [PR 39344779437](https://github.com/crycodebaby/Stronghold2PerformanceResearch/actions/runs/39344779437).
Diese datierten Ergebnisse gelten fuer diesen Head. Publikationsdokumentation wird danach mitaufgenommen;
deren finaler PR-Head und main-Merge sind separat zu pruefen, nicht durch die obigen Links abgedeckt.

Nach erfolgreicher PR-Pruefung normal per Merge-Commit integrieren und den daraus folgenden main-Pushlauf
ebenfalls pruefen. Finalen Commit, konkrete Runlinks und Testergebnisse im Veroeffentlichungsabschluss nennen.
Der neue Checkpoint ist ein Forschungsstand mit dokumentierten Grenzen, keine Performancefreigabe.

## Hub und naechste Forschung

Hub-checkout `026584a` hat zu Beginn keine lokalen Aenderungen. Dessen origin/main `f801530` ist zwei Commits
weiter, ausschliesslich Discord-CI/CONTRIBUTING; kein neuer Hub-Push oder Runtimebuild fuer diesen Auftrag.
Die Integrationsabnahme dieses Forschungs-PRs ersetzt keinen Hub-/Observer- oder Spieltest.

Aktueller Forschungsfolgeauftrag bleibt der [Callback-Contextvertrag](../tasks/POSE_CALLBACK_CONTEXT_2026-10-18.md)
an 0xE30C -> Track+8. Lebende Generation, vollstaendige relevante Ereignisse und geschuetztes Kopierintervall
sind weiter offen. Keine neue Aufnahme, Installation, Hooks, Livezugriffe, Cache-/Skiplogik oder Spieldateiaenderung.
