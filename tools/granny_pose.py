"""Verify, build and run the isolated x86 Granny pose differential host.

Usage: python -I tools/granny_pose.py [--verify-only] [--dll PATH]
Requires local MSVC/CMake. Never installs into a game folder or starts the game.
Writes only build/knowledge-pose/native* and results.json; stdlib only.
"""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths
from pe_info import PE

SOURCE = paths.REPO / "tools" / "granny_pose"
OUT = paths.REPO / "build" / "knowledge-pose"
EXPORTS = {
    "_GrannyNewWorldPose@4": (0x54400, 4),
    "_GrannyFreeWorldPose@4": (0x54410, 4),
    "_GrannyGetResultingWorldPoseSize@4": (0x54420, 4),
    "_GrannyNewWorldPoseInPlace@8": (0x54430, 8),
    "_GrannyGetWorldPose4x4@8": (0x54450, 8),
    "_GrannyGetWorldPoseComposite4x4@8": (0x54470, 8),
    "_GrannyGetWorldPose4x4Array@4": (0x52B90, 4),
    "_GrannyGetWorldPoseComposite4x4Array@4": (0x52BB0, 4),
    "_GrannyGetWorldPoseBoneCount@4": (0x4F9F0, 4),
    "_GrannyBuildCompositeFromWorldPose@16": (0x545E0, 16),
}


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def verify(dll):
    spec = json.loads((SOURCE / "verified_functions.json").read_text())
    if sha(dll) != spec["granny_sha256"]:
        raise ValueError("Unsupported DLL SHA-256; no original call authorized by this contract")
    pe = PE(dll)
    if pe.machine != 0x14C or pe.magic != 0x10B:
        raise ValueError("Expected PE32/x86")
    u32 = lambda offset: struct.unpack_from("<I", pe.data, offset)[0]
    directory = pe.rva2off(pe.directory(0)[0])
    functions = pe.rva2off(u32(directory + 28))
    names = pe.rva2off(u32(directory + 32))
    ordinals = pe.rva2off(u32(directory + 36))
    exports = {}
    for i in range(u32(directory + 24)):
        name = pe.cstr(pe.rva2off(u32(names + i * 4)))
        ordinal = struct.unpack_from("<H", pe.data, ordinals + i * 2)[0]
        exports[name] = u32(functions + ordinal * 4)
    for name, (rva, pop) in EXPORTS.items():
        if exports.get(name) != rva:
            raise ValueError("Export mismatch: " + name)
        offset = pe.rva2off(rva)
        # Wrapper lengths are verified in full below; the RET suffix proves stack purge.
        fn = next(f for f in spec["functions"] if int(f["rva"], 16) == rva)
        if pe.data[offset + fn["size"] - 3:offset + fn["size"]] != b"\xc2" + struct.pack("<H", pop):
            raise ValueError("stdcall return mismatch: " + name)
    for fn in spec["functions"]:
        offset = pe.rva2off(int(fn["rva"], 16))
        if hashlib.sha256(pe.data[offset:offset + fn["size"]]).hexdigest() != fn["sha256"]:
            raise ValueError("Function evidence mismatch: " + fn["rva"])
    return {"granny_sha256": spec["granny_sha256"], "exports_checked": len(EXPORTS),
            "function_byte_fingerprints": len(spec["functions"]), "machine": "PE32/x86"}


def cmake_path():
    found = shutil.which("cmake")
    if found:
        return found
    cache = paths.HUB / "build" / "CMakeCache.txt"
    for line in cache.read_text().splitlines():
        if line.startswith("CMAKE_COMMAND:INTERNAL="):
            candidate = Path(line.partition("=")[2])
            if candidate.is_file():
                return str(candidate)
    raise FileNotFoundError("CMake unavailable; see docs/SETUP.md")


def run_logged(command, log):
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(command, cwd=OUT, stdout=output, stderr=subprocess.STDOUT, timeout=180)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}); see {log.relative_to(paths.REPO)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--dll", type=Path, default=paths.ORIGINAL / "granny2.dll")
    args = parser.parse_args()
    dll = args.dll.resolve()
    if not args.verify_only:
        OUT.mkdir(parents=True, exist_ok=True)
        for filename in ("results.json", "native-results.json"):
            (OUT / filename).unlink(missing_ok=True)
    evidence = verify(dll)  # All ABI/identity gates before loading/executing the DLL.
    print(f"Verified: {evidence['exports_checked']} exports/ret-pop counts, {evidence['function_byte_fingerprints']} function fingerprints; expected x86 DLL.")
    if args.verify_only:
        return
    cmake = cmake_path()
    build = OUT / "native"
    run_logged([cmake, "-S", str(SOURCE), "-B", str(build), "-A", "Win32"], OUT / "native-configure.log")
    run_logged([cmake, "--build", str(build), "--config", "Release"], OUT / "native-build.log")
    host = build / "Release" / "pose_contract_host.exe"
    report = OUT / "native-results.json"
    # Remove only our prior derived report, so a failed host cannot leave a stale success.
    report.unlink(missing_ok=True)
    run_logged([str(host), str(dll), str(report)], OUT / "native-run.log")
    native = json.loads(report.read_text())
    if sha(dll) != evidence["granny_sha256"] or native["failures"] != 0:
        raise ValueError("Post-run identity/result failure")
    evidence.update({"native": native, "host_sha256": sha(host), "sources": {
        str(p.relative_to(paths.REPO)).replace("\\", "/"): sha(p)
        for p in [Path(__file__).resolve(), paths.REPO / "tools" / "test_granny_pose.py",
                  paths.REPO / "tools" / "recheck_granny_audit.py",
                  paths.REPO / "ghidra_scripts" / "PoseContract.java", *sorted(SOURCE.iterdir())] if p.is_file()
    }})
    (OUT / "results.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Native: {native['layout_cases']} layout cases, {native['matrix_cases']} differential cases, {native['compared_components']} components; 0 failures.")
    print(f"Rounded cases: {native['rounded_cases']}; max absolute difference {native['max_abs_error']:.9g}. General bit identity is disproved for this own implementation.")
    print("Local report: build/knowledge-pose/results.json (synthetic inputs; no game capture/performance claim).")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        sys.exit(str(error))
