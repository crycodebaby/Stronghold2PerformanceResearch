"""Switch the TEST copy between measurement variants.

Usage: python -I tools/variant.py <baseline|laa|dxvk|laa+dxvk|status>
       python -I tools/variant.py hub <on|off>
       python -I tools/variant.py sample <off|module|function>

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
- Ensures steam_appid.txt (40960) exists so SteamAPI_Init works when the game
  is started directly (Steam client must be running).
"""
import configparser
import filecmp
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


def write_ini(**changes):
    """Update keys in SH2Proxy.ini, keeping keys set by hand (hubdll, out)."""
    values = {"target": "system", "hub": "1", **read_ini(), **changes}
    lines = ["; Written by SH2-Perf tools/variant.py; read by the d3d9.dll proxy (D009).",
             "; target=system | d3d9_dxvk.dll   hub=1 | 0   sample=off | module | function   optional: hubdll=, out=",
             "[proxy]"] + [f"{k}={v}" for k, v in values.items()]
    (TEST_DIR / INI_NAME).write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


def set_sample(mode):
    if not is_proxy(TEST_DIR / "d3d9.dll"):
        sys.exit("proxy not installed - run a variant first, e.g. `variant.py baseline`")
    write_ini(sample=mode)


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


def status():
    proxy = TEST_DIR / "d3d9.dll"
    ini = read_ini()
    fresh = same(PROXY_SRC, proxy) and same(HUB_SRC, TEST_DIR / "Stronghold2AnalyseHub.dll")
    print(f"TEST={TEST_DIR}\nvariant={current_variant()}  LAA={laa_enabled()}  DXVK={dxvk_active()}")
    print(f"proxy={is_proxy(proxy)} (matches hub build: {fresh})  target={ini.get('target', '-')}"
          f"  hub={'on' if ini.get('hub', '1') != '0' else 'off'}  sample={ini.get('sample', 'off')}"
          f"  steam_appid={(TEST_DIR / 'steam_appid.txt').exists()}")


def main():
    args = sys.argv[1:]
    if args[:1] == ["hub"] and len(args) == 2 and args[1] in ("on", "off"):
        set_hub(args[1] == "on")
    elif args[:1] == ["sample"] and len(args) == 2 and args[1] in ("off", "module", "function"):
        set_sample(args[1])
    elif len(args) == 1 and args[0] in VARIANTS:
        apply(args[0])
    elif args != ["status"]:
        sys.exit(__doc__)
    status()


if __name__ == "__main__":
    main()
