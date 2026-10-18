"""Game-free identity, manifest and byte-gate tests; no original code execution."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pose_sample_verify as v


class PoseSampleTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(v.__file__).with_name('pose_sample_manifest.json')
        self.m = v.load_manifest(self.path)

    def test_complete_pinned_manifest(self):
        self.assertEqual(len(self.m['modules']), 2)
        self.assertEqual(sum(len(m['evidence']) for m in self.m['modules']), 70)

    def test_missing_duplicate_module_or_entry(self):
        mutations = [lambda m: m['modules'].pop(),
                     lambda m: m['modules'].__setitem__(1, copy.deepcopy(m['modules'][0])),
                     lambda m: m['modules'][1]['evidence'].pop(),
                     lambda m: m['modules'][1]['evidence'].append(copy.deepcopy(m['modules'][1]['evidence'][0]))]
        for mutation in mutations:
            m = copy.deepcopy(self.m)
            mutation(m)
            with self.assertRaises(ValueError):
                v.validate_manifest(m)

    def test_ranges_types_extent_digest_and_unknown_fields(self):
        for key, value in [('length', True), ('length', 0), ('length', -1), ('length', 65537),
                           ('length', '4'), ('length', 4.0), ('rva', '-1'),
                           ('rva', '0x100000000'), ('sha256', 'z' * 64), ('extra', 1)]:
            with self.subTest(key=key, value=value):
                m = copy.deepcopy(self.m)
                m['modules'][0]['evidence'][0]['ranges'][0][key] = value
                with self.assertRaises(ValueError):
                    v.validate_manifest(m)
        for key, value in [('schema', True), ('extra', 1)]:
            m = copy.deepcopy(self.m)
            m[key] = value
            with self.assertRaises(ValueError):
                v.validate_manifest(m)

    def test_overlapping_and_reordered_ranges(self):
        m = copy.deepcopy(self.m)
        rs = m['modules'][1]['evidence'][-1]['ranges']
        rs.append(copy.deepcopy(rs[0]))
        with self.assertRaises(ValueError):
            v.validate_manifest(m)
        m = copy.deepcopy(self.m)
        m['modules'].reverse()
        with self.assertRaises(ValueError):
            v.validate_manifest(m)

    def test_valid_looking_hash_change_and_module_swap_rejected(self):
        m = copy.deepcopy(self.m)
        m['modules'][1]['evidence'][0]['ranges'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            v.validate_manifest(m)
        m = copy.deepcopy(self.m)
        m['modules'][0]['image_base'] = '0x50000000'
        with self.assertRaises(ValueError):
            v.validate_manifest(m)

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'manifest.json'
            for raw in ['{"schema":1,"schema":1,"modules":[]}', '{"schema":NaN,"modules":[]}']:
                p.write_text(raw)
                with self.assertRaises(ValueError):
                    v.load_manifest(p)

    def test_byte_gate_valid_tamper_truncate_and_reader_failure(self):
        data = b'own synthetic bytes'
        mod = {'module': 'synthetic', 'evidence': [{'id': 'one', 'ranges': [
            {'rva': '0x1000', 'length': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}]}
        self.assertEqual(v.verify_bytes(mod, lambda r, n: data), 1)
        for wrong in [data[:-1], bytes(len(data)), data + b'x']:
            with self.assertRaises(ValueError):
                v.verify_bytes(mod, lambda r, n: wrong)
        def failed_read(r, n):
            raise ValueError('outside raw section')
        with self.assertRaises(ValueError):
            v.verify_bytes(mod, failed_read)

    def test_unknown_build_cli_normal_and_explicit_optimized(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'unknown.bin'
            p.write_bytes(b'own unknown fixture; not a game image')
            for flags in [[], ['-O']]:
                result = subprocess.run([sys.executable, *flags, '-I', v.__file__,
                                         '--exe', str(p), '--dll', str(p)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('SHA-256 mismatch', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(result.stdout, '')

    def test_invalid_manifest_cli_precedes_binary_read(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'manifest.json'
            p.write_text('{"schema":true,"modules":[]}')
            result = subprocess.run([sys.executable, '-O', '-I', v.__file__, '--manifest', str(p),
                                     '--exe', 'missing.exe', '--dll', 'missing.dll'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('manifest schema mismatch', result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_new_descriptor_and_callback_entries_required(self):
        required = {'dll': {'d-50061d58-28', 'd-50061ed0-28', 'f-500023b0',
                            'f-5001c400', 'r-5001c780-5001ca40', 'f-50044da0', 'f-50044de0'},
                    'exe': {'d-00900ad4-4'}}
        for mod in self.m['modules']:
            ids = {entry['id'] for entry in mod['evidence']}
            self.assertTrue(required[mod['module']] <= ids)
            for entry_id in required[mod['module']]:
                m = copy.deepcopy(self.m)
                target = next(x for x in m['modules'] if x['module'] == mod['module'])
                target['evidence'] = [x for x in target['evidence'] if x['id'] != entry_id]
                with self.assertRaises(ValueError):
                    v.validate_manifest(m)

    def test_new_table_hash_tamper_rejected(self):
        for entry_id in ['d-50061d58-28', 'd-50061ed0-28']:
            m = copy.deepcopy(self.m)
            entry = next(x for x in m['modules'][1]['evidence'] if x['id'] == entry_id)
            entry['ranges'][0]['sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                v.validate_manifest(m)

    def test_schema_one_and_new_callback_range_extent_rejected(self):
        m = copy.deepcopy(self.m)
        m['schema'] = 1
        with self.assertRaises(ValueError):
            v.validate_manifest(m)
        for delta in [-1, 1]:
            m = copy.deepcopy(self.m)
            entry = next(x for x in m['modules'][1]['evidence'] if x['id'] == 'r-5001c780-5001ca40')
            entry['ranges'][0]['length'] += delta
            with self.assertRaises(ValueError):
                v.validate_manifest(m)

    def test_first_bone_source_predicates_and_producers_required(self):
        required = {'f-500033e0', 'f-50003410', 'f-50003de0', 'f-50044ac0'}
        dll = next(mod for mod in self.m['modules'] if mod['module'] == 'dll')
        self.assertTrue(required <= {entry['id'] for entry in dll['evidence']})
        for entry_id in required:
            for mutation in ['remove', 'digest']:
                m = copy.deepcopy(self.m)
                mod = next(mod for mod in m['modules'] if mod['module'] == 'dll')
                entry = next(entry for entry in mod['evidence'] if entry['id'] == entry_id)
                if mutation == 'remove':
                    mod['evidence'].remove(entry)
                else:
                    entry['ranges'][0]['sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    v.validate_manifest(m)

    def test_lifetime_evidence_required(self):
        required = {'f-50054400', 'f-50054410', 'f-50054420', 'f-50054430',
                    'f-50046790', 'f-500467c0', 'f-500467e0', 'f-50046800', 'f-50046840',
                    'r-5000e165-5000e169', 'r-5000e54d-5000e551', 'd-50064b48-8'}
        dll = next(mod for mod in self.m['modules'] if mod['module'] == 'dll')
        self.assertTrue(required <= {entry['id'] for entry in dll['evidence']})
        for entry_id in required:
            m = copy.deepcopy(self.m)
            mod = next(mod for mod in m['modules'] if mod['module'] == 'dll')
            mod['evidence'] = [entry for entry in mod['evidence'] if entry['id'] != entry_id]
            with self.assertRaises(ValueError): v.validate_manifest(m)

    def test_worker_bypass_and_allocator_call_identity_gates(self):
        base = 0x50000000
        data = {site: b'\xe8' + struct.pack('<i', target-site-5) for site,target in v.LIFETIME_CALLS.items()}
        data.update({site: b'\xff\x15' + struct.pack('<I',base+slot) for site,slot in v.ALLOCATOR_CALLS.items()})
        v.verify_lifetime_edges(lambda r,n: data[r][:n], base)
        for site in data:
            for wrong in (b'', data[site][:-1], bytes(len(data[site])),
                          data[site][:-1] + bytes([data[site][-1] ^ 1])):
                with self.subTest(site=site,wrong=wrong):
                    with self.assertRaises(ValueError):
                        v.verify_lifetime_edges(lambda r,n: wrong if r==site else data[r][:n], base)


if __name__ == '__main__':
    unittest.main()
