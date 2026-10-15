"""End-to-end check of provenance and import without the game (D012): real d3d9 proxy + real hub DLL +
D3D9 stand-in program, `variant.py` for the prepared state and plan, then `ingest.py` into a temp bronze/silver.

Usage: python -I tools/e2e_standin.py [<work dir>] [--keep] [--hub-build <dir>] [--deactivate-only [--repeat N]]
(default work dir: a new temp folder, removed afterwards unless --keep; --hub-build compares another build of the hub;
--deactivate-only runs just the END-key deactivation check N times and prints how often the program ended cleanly)
Needs the hub build (docs/SETUP.md: build/Release/{d3d9.dll, Stronghold2AnalyseHub.dll, standin_d3d9.exe}); a window flashes
for a few seconds. Never touches the TEST copy, captures/, data/ or the original folder.

Sequence: a fourth session deactivates the hub with the END key while the program keeps running (injected key press; needs
an interactive desktop - if the key does not arrive the check says so and does not pass). Three game sessions (nothing planned / game_speed=30 / game_speed=90 + paused, last one in `min` mode), a hub DLL
swapped after the recordings, then import of all three. Prints one line per check and exits 1 if one fails.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
import variant  # noqa: E402

TOOLS = Path(__file__).resolve().parent
failures = []


def check(cond, text):
    print(("ok    " if cond else "FAIL  ") + text)
    if not cond:
        failures.append(text)


def press_end():
    """Inject a real END key press (the hub polls GetAsyncKeyState(VK_END)); Windows only."""
    import ctypes
    user32 = ctypes.windll.user32
    user32.keybd_event(0x23, 0x4F, 1, 0)           # VK_END, extended key
    user32.keybd_event(0x23, 0x4F, 1 | 2, 0)       # key up


def deactivation_check(test, out, check):
    """Manual hub deactivation (END) after a recording, while the program goes on rendering: orderly end, no crash, no deferral. The DLL stays loaded."""
    import time
    for p in out.glob("*"):
        if p.name.startswith("SH2Perf_") or p.name in ("latest.json", "Stronghold2AnalyseHub.log"):
            p.unlink()
    variant.set_plan(["clear"])
    variant.set_mode("full")
    env = dict(os.environ, SH2HUB_OUT=str(out), SH2HUB_AUTORECORD="150")
    proc = subprocess.Popen([str(test / "Stronghold2.exe"), "2500", "4"], cwd=test, env=env, stdout=subprocess.PIPE, text=True)
    deadline = time.time() + 60
    while time.time() < deadline and not any("finalized" in p.read_text() for p in out.glob("*_manifest.json")):
        time.sleep(0.2)
    check(any("finalized" in p.read_text() for p in out.glob("*_manifest.json")), "recording finalized before the deactivation")
    press_end()
    log = out / "Stronghold2AnalyseHub.log"
    for _ in range(100):
        if log.exists() and "Hub deactivated" in log.read_text(errors="replace"):
            break
        time.sleep(0.2)
    text = log.read_text(errors="replace") if log.exists() else ""
    check("VK_END pressed" in text, "END key reached the hub (injected key press)")
    check("Hub deactivated" in text and "Deactivation DEFERRED" not in text, "orderly deactivation, no deferral")
    try:
        proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
    check(proc.returncode == 0, f"the program kept running after the deactivation and ended normally (exit {proc.returncode})")


def main():
    argv = sys.argv[1:]
    keep = "--keep" in argv
    build = paths.HUB_BUILD
    repeat = 1
    for flag in ("--hub-build", "--repeat"):
        if flag in argv:
            i = argv.index(flag)
            value = argv.pop(i + 1)
            argv.pop(i)
            if flag == "--hub-build":
                build = Path(value)
            else:
                repeat = int(value)
    deactivate_only = "--deactivate-only" in argv
    args = [a for a in argv if not a.startswith("--")]
    work = Path(args[0]) if args else Path(tempfile.mkdtemp(prefix="sh2_e2e_"))
    work.mkdir(parents=True, exist_ok=True)
    test, out, repo = work / "TEST", work / "out", work / "repo"
    for d in (test, out):
        d.mkdir(exist_ok=True)
    for need in ("d3d9.dll", "Stronghold2AnalyseHub.dll", "standin_d3d9.exe"):
        if not (build / need).exists():
            sys.exit(f"{need} missing in the hub build ({build.name}); build the hub first (docs/SETUP.md)")
    shutil.copy2(build / "standin_d3d9.exe", test / "Stronghold2.exe")
    variant.TEST_DIR, variant.PROXY_SRC, variant.HUB_SRC = test, build / "d3d9.dll", build / "Stronghold2AnalyseHub.dll"
    variant.apply("baseline")

    if deactivate_only:
        ok = 0
        for n in range(repeat):
            failures.clear()
            deactivation_check(test, out, check)
            ok += not failures
        print(f"deactivation check: {ok} of {repeat} runs clean (hub build: {build})")
        shutil.rmtree(work, ignore_errors=True) if not keep else None
        sys.exit(0 if ok == repeat else 1)

    def play(plan, mode):
        variant.set_plan(plan)
        variant.set_mode(mode)
        env = dict(os.environ, SH2HUB_OUT=str(out), SH2HUB_AUTORECORD="250")
        r = subprocess.run([str(test / "Stronghold2.exe"), "700", "3"], cwd=test, env=env, capture_output=True, text=True, timeout=180)
        check(r.returncode == 0, f"stand-in session ran ({plan}, {mode})")

    play(["clear"], "full")
    play(["experiment=E2E", "protocol=smoke", "game_speed=30"], "full")
    play(["game_speed=90", "paused=1"], "min")
    manifests = sorted(out.glob("*_manifest.json"))
    check(len(manifests) == 3, f"three manifests written ({len(manifests)})")
    m = [json.loads(p.read_text()) for p in manifests]
    check(len({x["capture_id"] for x in m}) == 3, "three distinct capture ids")
    check(all(x["status"] == "finalized" and x["technical_quality"]["capture_ok"] for x in m), "all finalized and capture_ok")
    check([x["game"]["game_speed"]["value"] for x in m] == [None, 30, 90], "game speed unknown / 30 / 90")
    check(m[0]["game"]["game_speed"]["origin"] == "unknown" and m[2]["game"]["paused"]["value"] is True, "unknown stays unknown; pause recorded apart")
    check([x["switches"]["counters"]["value"] for x in m] == [True, True, False], "switches differ per recording (full, full, min)")
    check(all(len(f["sha256"]) == 64 for x in m for f in x["software"]["files"]), "software hashes are full SHA-256")
    latest = json.loads((out / "latest.json").read_text())
    check(latest["capture_id"] == m[2]["capture_id"] and latest["manifest"] == manifests[2].name, "latest.json points only at the newest")

    hub_in_test = test / "Stronghold2AnalyseHub.dll"
    hub_in_test.write_bytes(hub_in_test.read_bytes() + b"swapped after the recordings")
    sources = {p.name: p.stat().st_size for p in out.iterdir()}
    env = dict(os.environ, SH2PERF_NO_HARDWARE="1")
    base = [sys.executable, "-I", str(TOOLS / "ingest.py")]
    common = ["--src", str(out), "--captures", str(repo / "captures"), "--index", str(repo / "data" / "index.jsonl")]
    for stamp in (p.name.split("_")[1] + "_" + p.name.split("_")[2] for p in manifests):
        r = subprocess.run(base + ["import", *common, "--game-dir", str(test), "--recording", stamp], capture_output=True, text=True, env=env)
        check(r.returncode == 0, f"import {stamp}")
    r = subprocess.run(base + ["import", *common, "--game-dir", str(test), "--recording", manifests[0].name.split("_")[1] + "_" + manifests[0].name.split("_")[2]],
                       capture_output=True, text=True, env=env)
    check("already imported" in r.stdout, "repeat import changes nothing")
    check({p.name: p.stat().st_size for p in out.iterdir()} == sources, "sources untouched")
    idx = [json.loads(line) for line in (repo / "data" / "index.jsonl").read_text().splitlines()]
    check(len(idx) == 3, "three index lines, no duplicate")
    first = json.loads((repo / "data" / "silver" / m[0]["capture_id"] / "summary.json").read_text())
    check(first["software"]["files"]["Stronghold2AnalyseHub.dll"] == {f["name"]: f["sha256"] for f in m[0]["software"]["files"]}["Stronghold2AnalyseHub.dll"],
          "recorded hub DLL hash kept as identity")
    check(first["software"].get("changed_after_capture") == {"Stronghold2AnalyseHub.dll": "changed"}, "swapped hub DLL flagged")
    check(idx[2]["modes"]["counters"] is False and idx[2]["total"]["dip"] is None, "min-mode recording: counters null, not 0")
    deactivation_check(test, out, check)
    if keep:
        print(f"work folder kept: {work}")
    else:
        shutil.rmtree(work, ignore_errors=True)
    print("E2E OK" if not failures else f"E2E FAILED ({len(failures)})")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
