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
        self.assertEqual(sum(len(m['evidence']) for m in self.m['modules']), 85)

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
        data.update({site: b'\xff\x15' + struct.pack('<I',base+slot) for site,slot in v.HEAP_CALLS.items()})
        v.verify_lifetime_edges(lambda r,n: data[r][:n], base)
        for site in data:
            for wrong in (b'', data[site][:-1], bytes(len(data[site])),
                          data[site][:-1] + bytes([data[site][-1] ^ 1])):
                with self.subTest(site=site,wrong=wrong):
                    with self.assertRaises(ValueError):
                        v.verify_lifetime_edges(lambda r,n: wrong if r==site else data[r][:n], base)

    def test_allocator_workers_and_heap_forwarding_evidence_required(self):
        required = {'f-50052870', 'f-50052890', 'f-500318e0', 'f-50031900', 'f-50031150',
                    'f-50031220', 'f-50031920', 'f-50031940', 'f-50031210', 'f-50031290'}
        dll = next(mod for mod in self.m['modules'] if mod['module'] == 'dll')
        self.assertTrue(required <= {entry['id'] for entry in dll['evidence']})
        for entry_id in required:
            m = copy.deepcopy(self.m)
            mod = next(mod for mod in m['modules'] if mod['module'] == 'dll')
            mod['evidence'] = [entry for entry in mod['evidence'] if entry['id'] != entry_id]
            with self.assertRaises(ValueError): v.validate_manifest(m)

    def test_default_slot_pair_valid_changed_swapped_and_truncated(self):
        base = 0x50000000
        data = {slot: struct.pack('<I', base+target) for slot, target in v.ALLOCATOR_DEFAULTS.items()}
        v.verify_allocator_defaults(lambda r,n: data[r][:n], base)
        for slot in data:
            other = next(key for key in data if key != slot)
            for wrong in (b'', data[slot][:-1], data[other], bytes(4)):
                with self.assertRaises(ValueError):
                    v.verify_allocator_defaults(lambda r,n: wrong if r==slot else data[r][:n], base)

    def test_literal_census_counts_unaligned_data_without_decoding_and_never_crosses_sections(self):
        allocate = struct.pack('<I', 0x50064b48)
        release = struct.pack('<I', 0x50064b4c)
        sections = [(0x1000, b'x'+allocate+allocate), (0x2000, release),
                    (0x3000, allocate[:2]), (0x3002, allocate[2:])]
        expected = {'0x64b48': {'count': 2, 'literal_field_rvas': ['0x1001', '0x1005']},
                    '0x64b4c': {'count': 1, 'literal_field_rvas': ['0x2000']}}
        self.assertEqual(v.allocator_literals(iter(sections)), expected)
        # Matching a constant in arbitrary data is not itself a semantic read/write reference.
        for changed in ([], sections, [(0x1000, bytes(32))]):
            with self.assertRaises(ValueError): v.verify_allocator_literals(changed)

    def test_internal_context_caller_and_stub_entries_required(self):
        required = {'f-5000e080', 'f-5004ff60', 'f-5004ff80', 'f-5000e5a0', 'f-5002f5d0'}
        dll = next(mod for mod in self.m['modules'] if mod['module'] == 'dll')
        self.assertTrue(required <= {entry['id'] for entry in dll['evidence']})
        for entry_id in required:
            m = copy.deepcopy(self.m)
            mod = next(mod for mod in m['modules'] if mod['module'] == 'dll')
            mod['evidence'] = [entry for entry in mod['evidence'] if entry['id'] != entry_id]
            with self.assertRaises(ValueError): v.validate_manifest(m)

    def test_bounded_frame_decoder_signed_displacements_sib_and_unsupported_forms(self):
        self.assertEqual(v.decode_frame_mov(b'\x89\x45\x9c'),
                         {'write': True, 'register': 0, 'index': None, 'scale': 1, 'displacement': -100})
        fixture = b'\x8b\x94\x95' + struct.pack('<i', 1024)
        self.assertEqual(v.decode_frame_mov(fixture),
                         {'write': False, 'register': 2, 'index': 2, 'scale': 4, 'displacement': 1024})
        for bad in [fixture[:n] for n in range(len(fixture))] + [b'\x90\x45\x9c', b'\x89\xc0\x00',
                    b'\x89\x40\x00', b'\x89\x44\x24\x00']:
            with self.assertRaises(ValueError): v.decode_frame_mov(bad)

    def test_internal_spill_and_two_iteration_loop_gates_reject_changed_dataflow(self):
        data = {0xe16a: b'\x89\x44\x3d\xbc'+bytes(3),
                0xe548: b'\x8b\x54\x35\xbc'+bytes(3), 0xe54c: b'\x52'}
        for zero, advance, compare, branch, target, reg in [(0xe152, 0xe16e, 0xe174, 0xe177, 0xe154, 7),
                                                          (0xe546, 0xe55c, 0xe562, 0xe565, 0xe548, 6)]:
            data[zero] = bytes([0x33, 0xc0+9*reg])
            data[advance] = bytes([0x83, 0xc0+reg, 4])
            data[compare] = bytes([0x83, 0xf8+reg, 8])
            data[branch] = bytes([0x7c]) + struct.pack('b', target-branch-2)
        v.verify_internal_pose_spills(lambda r,n: data[r][:n])
        for site, fixture in data.items():
            # Frame moves consume four bytes; the seven-byte read includes following instructions.
            consumed = 4 if site in (0xe16a, 0xe548) else len(fixture)
            truncated = fixture[:consumed-1]
            mutations = [fixture[:i]+bytes([fixture[i] ^ 1])+fixture[i+1:] for i in range(consumed)]
            if consumed == 4: mutations.append(fixture[:3]+bytes([fixture[3] ^ 0x80])+fixture[4:])
            for wrong in [b'', bytes(len(fixture)), truncated, *mutations]:
                with self.subTest(site=site):
                    with self.assertRaises(ValueError):
                        v.verify_internal_pose_spills(lambda r,n: wrong if r==site else data[r][:n])


if __name__ == '__main__':
    unittest.main()
