"""Synthetic rejection checks; no game files or compiler required."""
import copy
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hpose_allocation_verify import verify, FUNCTIONS, EXE_SHA, DLL_SHA


class Verification(unittest.TestCase):
    def setUp(self):
        self.manifest = {'version': 1, 'exe_sha256': EXE_SHA, 'dll_sha256': DLL_SHA,
                         'functions': [{'rva': rva, 'ranges': [{'rva': rva, 'length': 1}],
                                        'sha256': hashlib.sha256(b'x').hexdigest()}
                                       for rva in sorted(FUNCTIONS)]}

    def test_success(self):
        verify(self.manifest, lambda r, n: b'x')

    def test_reject_coverage_and_identity(self):
        for key, value in [('functions', []), ('exe_sha256', '0'*64), ('dll_sha256', '0'*64),
                           ('version', 2), ('version', True), ('version', 1.0)]:
            m = copy.deepcopy(self.manifest)
            m[key] = value
            with self.assertRaises(ValueError):
                verify(m, lambda r, n: b'x')

    def test_reject_duplicates(self):
        m = copy.deepcopy(self.manifest)
        m['functions'][0] = m['functions'][1]
        with self.assertRaises(ValueError):
            verify(m, lambda r, n: b'x')

    def test_reject_bytes(self):
        with self.assertRaises(ValueError):
            verify(self.manifest, lambda r, n: b'y')

    def test_reject_extents(self):
        for bad in [0, -1, True, 0x100000001]:
            m = copy.deepcopy(self.manifest)
            m['functions'][0]['ranges'][0]['length'] = bad
            with self.assertRaises(ValueError):
                verify(m, lambda r, n: b'x')

    def test_reject_overlapping_ranges(self):
        m = copy.deepcopy(self.manifest)
        m['functions'][0]['ranges'] *= 2
        with self.assertRaises(ValueError):
            verify(m, lambda r, n: b'x')

    def test_cli_unknown_build_rejected_normal_and_optimized(self):
        tool = Path(__file__).with_name('hpose_allocation_verify.py')
        with tempfile.TemporaryDirectory(prefix='hpose_unknown_') as temporary:
            own = Path(temporary) / 'unknown.bin'
            own.write_bytes(b'own unknown build, not a game binary')
            for flags in (['-I'], ['-O', '-I']):
                result = subprocess.run([sys.executable, *flags, str(tool), '--exe', str(own), '--dll', str(own)],
                                        capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('SHA-256 mismatch', result.stderr)
                self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
