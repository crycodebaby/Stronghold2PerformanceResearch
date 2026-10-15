"""Switch the TEST copy between measurement variants.

Usage: python -I tools/variant.py <baseline|laa|dxvk|laa+dxvk|status>

- Only touches the TEST copy (never the original folder).
- LAA via tools/laa_patch.py logic (backup <exe>.orig kept).
- DXVK: copies DXVK x32 d3d9.dll into the TEST folder; removes it again only
  if the file there is byte-identical to the DXVK one.
- Ensures steam_appid.txt (40960) exists so SteamAPI_Init works when the game
  is started directly via SH2Launcher (Steam client must be running).
"""
import filecmp
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DXVK_D3D9, TEST  # noqa: E402

TEST_DIR = str(TEST)
EXE = os.path.join(TEST_DIR, "Stronghold2.exe")
LAA_TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laa_patch.py")
STEAM_APPID = "40960"


def laa_enabled():
    data = open(EXE, "rb").read(512)
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    return bool(struct.unpack_from("<H", data, pe + 22)[0] & 0x20)


def set_laa(on):
    if laa_enabled() != on:
        args = [sys.executable, "-I", LAA_TOOL, EXE] + ([] if on else ["--clear"])
        subprocess.run(args, check=True)


def set_dxvk(on):
    target = os.path.join(TEST_DIR, "d3d9.dll")
    if on:
        shutil.copy2(DXVK_D3D9, target)
    elif os.path.exists(target):
        if not filecmp.cmp(target, DXVK_D3D9, shallow=False):
            sys.exit(f"{target} is not the DXVK file; not removing it")
        os.remove(target)


def ensure_steam_appid():
    path = os.path.join(TEST_DIR, "steam_appid.txt")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(STEAM_APPID)


def current_variant():
    """Variant name derived from the TEST folder state."""
    dxvk = os.path.exists(os.path.join(TEST_DIR, "d3d9.dll"))
    return {(False, False): "baseline", (True, False): "laa",
            (False, True): "dxvk", (True, True): "laa+dxvk"}[(laa_enabled(), dxvk)]


def status():
    dxvk = os.path.exists(os.path.join(TEST_DIR, "d3d9.dll"))
    print(f"TEST={TEST_DIR}\nLAA={laa_enabled()}  DXVK={dxvk}  "
          f"steam_appid={os.path.exists(os.path.join(TEST_DIR, 'steam_appid.txt'))}")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    variant = sys.argv[1]
    wanted = {"baseline": (False, False), "laa": (True, False),
              "dxvk": (False, True), "laa+dxvk": (True, True)}
    if variant != "status":
        if variant not in wanted:
            sys.exit(__doc__)
        laa, dxvk = wanted[variant]
        set_laa(laa)
        set_dxvk(dxvk)
        ensure_steam_appid()
    status()


if __name__ == "__main__":
    main()
