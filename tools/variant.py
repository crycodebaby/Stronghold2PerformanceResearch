"""Switch the TEST copy between measurement variants.

Usage: python -I tools/variant.py <baseline|laa|dxvk|laa+dxvk|status>
       python -I tools/variant.py hub <on|off>
       python -I tools/variant.py sample <off|module|function>
       python -I tools/variant.py granny <on|off>
       python -I tools/variant.py mode <full|min>
       python -I tools/variant.py switch <frametime|counters|poll|overlay|beep> <on|off|default>
       python -I tools/variant.py plan [experiment=E] [protocol=P] [scenario=S] [game_speed=N] [paused=true|false] [key=] | clear

- Only touches the TEST copy (never the original folder).
- Every variant installs the hub loader (D009): the d3d9.dll proxy and
  Stronghold2AnalyseHub.dll from the hub build, plus SH2Proxy.ini.
  Re-run after rebuilding the hub to refresh the copies.
- LAA via tools/laa_patch.py logic (backup <exe>.orig kept).
- DXVK: copies DXVK x32 d3d9.dll as d3d9_dxvk.dll and sets target=d3d9_dxvk.dll
  in SH2Proxy.ini; without DXVK target=system. d3d9_dxvk.dll is only removed
  if it is byte-identical to the DXVK one.
- A d3d9.dll that is neither the proxy nor DXVK is never overwritten.
- hub on|off: switch in SH2Proxy.ini; off = proxy passes everything through, no hub.
- sample off|module|function: sampling profiler of the hub (render thread, writes *_samples.csv per
  recording; docs/design/SAMPLING_PROFILER.md). Default off.
- granny on|off: Granny import-boundary observer of the hub (EXP-008, docs/FORMATS/GRANNY_OBSERVER.md; patches six exe
  import slots, writes *_granny*.{json,csv} per recording). Separate from profiles; off is written explicitly (granny=0).
- mode full|min: hub measurement profile (D011). full = frame time + graphics counters + background polls +
  overlay (behaviour of hub builds before D011); min = frame time only. Clears single switches.
- switch <key> on|off|default: one hub switch in SH2Proxy.ini (read by the hub, env SH2HUB_<KEY> wins).
  frametime = Present hook + recording; counters = draw/state counters; poll = thread CPU + address space
  once per second while recording; overlay = ImGui window; beep = tone on recording start/stop.
- plan: what the NEXT recordings are planned to be (SH2Proxy.ini [plan], read by the hub when a recording starts and
  written into its manifest as origin "planned"). game_speed is a plain number (no range or meaning is assumed);
  paused is independent of the speed. `key=` removes one entry, `clear` all. Planned values are not observed values.
- Every change writes SH2Prepared.json next to the exe: the prepared state (variant, SHA-256 of exe/hub/proxy/DXVK/ini,
  plan, time). The hub copies it into each recording, so the software identity "at prepared start" travels with
  the capture (D012).
- Ensures steam_appid.txt (40960) exists so SteamAPI_Init works when the game
  is started directly (Steam client must be running).
"""
import configparser
import datetime
import filecmp
import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DXVK_D3D9, HUB_DLL, HUB_PROXY, TEST  # noqa: E402

# Module-level so tests can point them at a temporary folder.
TEST_DIR = TEST
DXVK_SRC = DXVK_D3D9
PROXY_SRC = HUB_PROXY
HUB_SRC = HUB_DLL
LAA_TOOL = Path(__file__).resolve().parent / "laa_patch.py"
STEAM_APPID = "40960"
DXVK_NAME = "d3d9_dxvk.dll"
INI_NAME = "SH2Proxy.ini"
PREPARED_NAME = "SH2Prepared.json"
PLAN_KEYS = ("experiment", "protocol", "scenario", "game_speed", "paused")
PREPARED_FILES = (("game_exe", "Stronghold2.exe"), ("hub_dll", "Stronghold2AnalyseHub.dll"),
                  ("d3d9_in_game_dir", "d3d9.dll"), ("d3d9_dxvk", "d3d9_dxvk.dll"), ("config_ini", INI_NAME))
PROXY_MARKER = b"SH2Proxy_RealModule"       # export name only the proxy has
VARIANTS = {"baseline": (False, False), "laa": (True, False),
            "dxvk": (False, True), "laa+dxvk": (True, True)}


def exe():
    return TEST_DIR / "Stronghold2.exe"


def same(a, b):
    return Path(a).exists() and Path(b).exists() and filecmp.cmp(a, b, shallow=False)


def is_proxy(path):
    return Path(path).exists() and PROXY_MARKER in Path(path).read_bytes()


def laa_enabled():
    data = exe().read_bytes()[:512]
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    return bool(struct.unpack_from("<H", data, pe + 22)[0] & 0x20)


def set_laa(on):
    if laa_enabled() != on:
        args = [sys.executable, "-I", str(LAA_TOOL), str(exe())] + ([] if on else ["--clear"])
        subprocess.run(args, check=True)


def read_ini():
    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read(TEST_DIR / INI_NAME, encoding="utf-8")
    return dict(cp["proxy"]) if cp.has_section("proxy") else {}


def read_plan():
    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read(TEST_DIR / INI_NAME, encoding="utf-8")
    return dict(cp["plan"]) if cp.has_section("plan") else {}


def _write_ini_file(proxy, plan):
    lines = ["; Written by SH2-Perf tools/variant.py; read by the d3d9.dll proxy (D009) and the hub (D011).",
             "; target=system | d3d9_dxvk.dll   hub=1 | 0   sample=off | module | function   optional: hubdll=, out=",
             "; hub switches: profile=full | min   frametime= counters= poll= overlay= beep=  (1 | 0)",
             "[proxy]"] + [f"{k}={v}" for k, v in proxy.items()]
    if plan:
        lines += ["; [plan] = planned conditions of the next recordings (variant.py plan); the hub copies them into the manifest",
                  "[plan]"] + [f"{k}={v}" for k, v in plan.items()]
    (TEST_DIR / INI_NAME).write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


def write_ini(**changes):
    """Update keys in SH2Proxy.ini, keeping keys set by hand (hubdll, out) and the [plan] section."""
    values = {"target": "system", "hub": "1", **read_ini(), **changes}
    values = {k: v for k, v in values.items() if v is not None}      # None removes a key
    _write_ini_file(values, read_plan())
    write_prepared("ini")


def parse_plan_value(key, value):
    """Check one plan entry; returns the text to store. game_speed: any finite number, no range or meaning assumed."""
    if key == "game_speed":
        try:
            v = float(value)
        except ValueError:
            sys.exit(f"game_speed {value!r} is not a number")
        if not math.isfinite(v):
            sys.exit(f"game_speed {value!r} is not a finite number")
        return str(int(v)) if v == int(v) else repr(v)
    if key == "paused":
        if value.lower() not in ("true", "false", "1", "0"):
            sys.exit("paused must be true or false")
        return "1" if value.lower() in ("true", "1") else "0"
    if "\n" in value or "\r" in value:
        sys.exit(f"{key}: no line breaks")
    return value


def set_plan(args):
    """args: ['clear'] or ['key=value', ...]; `key=` removes an entry."""
    plan = read_plan()
    if args == ["clear"]:
        plan = {}
    else:
        for item in args:
            key, sep, value = item.partition("=")
            if not sep or key not in PLAN_KEYS:
                sys.exit(f"plan: use key=value with key in {', '.join(PLAN_KEYS)}, or `clear`")
            if value == "":
                plan.pop(key, None)
            else:
                plan[key] = parse_plan_value(key, value)
    _write_ini_file({"target": "system", "hub": "1", **read_ini()}, plan)
    write_prepared("plan")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_prepared(command):
    """SH2Prepared.json: the prepared state of the TEST folder (D012). The hub copies it into every recording."""
    files = []
    for role, name in PREPARED_FILES:
        p = TEST_DIR / name
        if p.is_file():
            files.append({"role": role, "name": name, "size": p.stat().st_size, "sha256": _sha256(p)})
    try:
        name = current_variant()
        laa, dxvk = VARIANTS[name]
    except (OSError, KeyError, struct.error, IndexError):
        name = laa = dxvk = None
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    record = {"schema": "sh2perf.prepared-start", "version": 1, "tool": "variant.py", "command": command,
              "prepared_utc": now, "variant": name, "laa": laa, "dxvk": dxvk, "files": files, "plan": read_plan()}
    (TEST_DIR / PREPARED_NAME).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def set_sample(mode):
    if not is_proxy(TEST_DIR / "d3d9.dll"):
        sys.exit("proxy not installed - run a variant first, e.g. `variant.py baseline`")
    write_ini(sample=mode)


def set_granny(on):
    if not is_proxy(TEST_DIR / "d3d9.dll"):
        sys.exit("proxy not installed - run a variant first, e.g. `variant.py baseline`")
    write_ini(granny="1" if on else "0")


SWITCHES = ("frametime", "counters", "poll", "overlay", "beep")


def set_mode(profile):
    if not is_proxy(TEST_DIR / "d3d9.dll"):
        sys.exit("proxy not installed - run a variant first, e.g. `variant.py baseline`")
    write_ini(profile=profile, **{k: None for k in SWITCHES})


def set_switch(key, value):
    if not is_proxy(TEST_DIR / "d3d9.dll"):
        sys.exit("proxy not installed - run a variant first, e.g. `variant.py baseline`")
    write_ini(**{key: {"on": "1", "off": "0", "default": None}[value]})


def install_proxy():
    d3d9 = TEST_DIR / "d3d9.dll"
    if d3d9.exists() and not is_proxy(d3d9):
        if not same(d3d9, DXVK_SRC):
            sys.exit(f"{d3d9.name} in TEST is neither the proxy nor DXVK; not touching it")
        d3d9.unlink()                      # layout before D009: DXVK as d3d9.dll
    for src, name in ((PROXY_SRC, "d3d9.dll"), (HUB_SRC, "Stronghold2AnalyseHub.dll")):
        if not Path(src).exists():
            sys.exit(f"{Path(src).name} missing in the hub build - build it first (docs/SETUP.md)")
        if not same(src, TEST_DIR / name):
            shutil.copy2(src, TEST_DIR / name)


def set_dxvk(on):
    target = TEST_DIR / DXVK_NAME
    if on:
        shutil.copy2(DXVK_SRC, target)
        write_ini(target=DXVK_NAME)
        return
    if target.exists():
        if not same(target, DXVK_SRC):
            sys.exit(f"{target.name} in TEST is not the DXVK file; not removing it")
        target.unlink()
    write_ini(target="system")


def set_hub(on):
    if not is_proxy(TEST_DIR / "d3d9.dll"):
        sys.exit("proxy not installed - run a variant first, e.g. `variant.py baseline`")
    write_ini(hub="1" if on else "0")


def ensure_steam_appid():
    path = TEST_DIR / "steam_appid.txt"
    if not path.exists():
        path.write_text(STEAM_APPID)


def dxvk_active():
    d3d9 = TEST_DIR / "d3d9.dll"
    if d3d9.exists() and not is_proxy(d3d9):
        return same(d3d9, DXVK_SRC)        # layout before D009
    return read_ini().get("target", "system").lower() != "system"


def current_variant():
    """Variant name derived from the TEST folder state."""
    return {v: k for k, v in VARIANTS.items()}[(laa_enabled(), dxvk_active())]


def apply(variant):
    laa, dxvk = VARIANTS[variant]
    set_laa(laa)
    install_proxy()
    set_dxvk(dxvk)
    ensure_steam_appid()
    write_prepared(variant)


def status():
    proxy = TEST_DIR / "d3d9.dll"
    ini = read_ini()
    fresh = same(PROXY_SRC, proxy) and same(HUB_SRC, TEST_DIR / "Stronghold2AnalyseHub.dll")
    print(f"TEST={TEST_DIR}\nvariant={current_variant()}  LAA={laa_enabled()}  DXVK={dxvk_active()}")
    print(f"proxy={is_proxy(proxy)} (matches hub build: {fresh})  target={ini.get('target', '-')}"
          f"  hub={'on' if ini.get('hub', '1') != '0' else 'off'}  sample={ini.get('sample', 'off')}"
          f"  granny={ {'1': 'on', '0': 'off'}.get(ini.get('granny'), 'off (default)') }"
          f"  steam_appid={(TEST_DIR / 'steam_appid.txt').exists()}")
    switches = {k: ini[k] for k in SWITCHES if k in ini}
    print(f"hub profile={ini.get('profile', 'full')}  single switches={switches or 'none'}")
    print(f"plan={read_plan() or 'none (every plan value stays unknown in the manifest)'}")


def main():
    args = sys.argv[1:]
    if args[:1] == ["hub"] and len(args) == 2 and args[1] in ("on", "off"):
        set_hub(args[1] == "on")
    elif args[:1] == ["sample"] and len(args) == 2 and args[1] in ("off", "module", "function"):
        set_sample(args[1])
    elif args[:1] == ["granny"] and len(args) == 2 and args[1] in ("on", "off"):
        set_granny(args[1] == "on")
    elif args[:1] == ["mode"] and len(args) == 2 and args[1] in ("full", "min"):
        set_mode(args[1])
    elif args[:1] == ["switch"] and len(args) == 3 and args[1] in SWITCHES and args[2] in ("on", "off", "default"):
        set_switch(args[1], args[2])
    elif args[:1] == ["plan"] and len(args) >= 2:
        set_plan(args[1:])
    elif len(args) == 1 and args[0] in VARIANTS:
        apply(args[0])
    elif args != ["status"]:
        sys.exit(__doc__)
    status()


if __name__ == "__main__":
    main()
