"""Integration checks: reject tampered DLL before loading; check saved rounding witness.

Run tools/granny_pose.py first. Uses only its own temporary copy of the DLL.
Usage: python -I tools/test_granny_pose.py
"""
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths

OUT = paths.REPO / "build" / "knowledge-pose"


class HostEvidence(unittest.TestCase):
    def test_tampered_file_is_rejected_by_both_gates(self):
        host = OUT / "native" / "Release" / "pose_contract_host.exe"
        self.assertTrue(host.is_file(), "Run tools/granny_pose.py first")
        with tempfile.TemporaryDirectory(prefix="tamper-", dir=OUT) as temporary:
            directory = Path(temporary).resolve()
            self.assertTrue(directory.is_relative_to(OUT.resolve()))
            modified = bytearray((paths.ORIGINAL / "granny2.dll").read_bytes())
            modified[-1] ^= 1
            dll = directory / "changed.dll"
            dll.write_bytes(modified)
            report = directory / "must-not-exist.json"
            commands = [
                [sys.executable, "-I", str(paths.REPO / "tools" / "granny_pose.py"), "--verify-only", "--dll", str(dll)],
                [str(host), str(dll), str(report)],
            ]
            for command in commands:
                result = subprocess.run(command, capture_output=True, text=True, timeout=10, cwd=directory)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("SHA-256", result.stdout + result.stderr)
                self.assertFalse(report.exists())

    def test_rounding_witness_with_exact_rational_oracle(self):
        result = json.loads((OUT / "native-results.json").read_text())
        witness = result["counterexample"]
        j = witness["component"]
        row, col = divmod(j, 4)
        self.assertLess(col, 3)
        a, b = witness["inverse_bind"], witness["world"]
        exact = sum((Fraction(a[row * 4 + k]) * Fraction(b[k * 4 + col]) for k in range(3)), Fraction(0))
        if row == 3:
            exact += Fraction(b[12 + col])
        # The retained witness is not near a float64 midpoint: the rounded float32
        # and its neighbours bracket the exact rational, checked without tolerance.
        packed = struct.pack("<f", float(exact))
        bits = struct.unpack("<I", packed)[0]
        nearest = struct.unpack("<f", packed)[0]
        for neighbour_bits in [bits - 1, bits + 1]:
            neighbour = struct.unpack("<f", struct.pack("<I", neighbour_bits))[0]
            self.assertLess(abs(exact - Fraction(nearest)), abs(exact - Fraction(neighbour)))
        self.assertEqual(witness["original"][j], nearest)
        self.assertNotEqual(witness["own"][j], nearest)
        self.assertGreater(result["rounded_cases"], 0)
        self.assertEqual(result["failures"], 0)
        self.assertEqual(result["corpus_cases_identity_dyadic_general"], [540, 540, 540])


if __name__ == "__main__":
    unittest.main(verbosity=2)
