"""Set or clear IMAGE_FILE_LARGE_ADDRESS_AWARE on a COPY of Stronghold2.exe.

Usage: python -I tools/laa_patch.py <path-to-copy\\Stronghold2.exe> [--clear]
- Refuses any path inside the original game folder.
- Writes a backup <exe>.orig once (never overwritten).
- Recomputes the PE checksum.
"""
import os
import shutil
import struct
import sys

ORIGINAL_DIR = os.path.normcase(os.path.abspath(r"<RE-Projects>\Stronghold 2"))
LAA = 0x0020


def pe_checksum(data, checksum_off):
    total = 0
    for i in range(0, len(data) & ~1, 2):
        if i == checksum_off or i == checksum_off + 2:
            continue
        total += data[i] | (data[i + 1] << 8)
        total = (total & 0xFFFF) + (total >> 16)
    if len(data) & 1:
        total += data[-1]
        total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    return (total + len(data)) & 0xFFFFFFFF


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = os.path.abspath(sys.argv[1])
    if os.path.normcase(os.path.dirname(path)).startswith(ORIGINAL_DIR + os.sep) or \
            os.path.normcase(os.path.dirname(path)) == ORIGINAL_DIR:
        sys.exit("refusing to patch the ORIGINAL game folder; use the TEST copy")
    data = bytearray(open(path, "rb").read())
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    chars_off = pe + 22
    checksum_off = pe + 24 + 64
    before = struct.unpack_from("<H", data, chars_off)[0]
    after = before & ~LAA if "--clear" in sys.argv else before | LAA
    if before == after:
        print(f"no change: characteristics=0x{before:04x} LAA={bool(before & LAA)}")
        return
    backup = path + ".orig"
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
    struct.pack_into("<H", data, chars_off, after)
    struct.pack_into("<I", data, checksum_off, pe_checksum(data, checksum_off))
    open(path, "wb").write(data)
    print(f"characteristics 0x{before:04x} -> 0x{after:04x}  LAA={bool(after & LAA)}  backup={backup}")


if __name__ == "__main__":
    main()
