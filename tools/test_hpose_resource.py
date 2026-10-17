"""Synthetic manifest and byte-reader rejection tests; no game needed."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hpose_resource_verify as v

class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(Path(v.__file__).with_name('hpose_resource_manifest.json').read_text())
        self.blobs = {}
        for f in self.m['functions']:
            h = hashlib.sha256()
            for r in f['ranges']:
                b = b'X' * r['length']; self.blobs[int(r['rva'], 16)] = b; h.update(b)
            f['sha256'] = h.hexdigest()
        self.blobs[0x5f49d4] = struct.pack('<I', 0x796470)
    def read(self, rva, length):
        return self.blobs[rva]
    def rejected(self, m):
        with self.assertRaises(ValueError): v.verify(m, self.read)
    def test_success(self): v.verify(self.m, self.read)
    def test_identity_version(self):
        for key, val in [('version',True),('version',2),('exe_sha256','0'*64),('dll_sha256','0'*64)]:
            m=copy.deepcopy(self.m);m[key]=val;self.rejected(m)
    def test_unknown_fields(self):
        for target in ('root','function','range','table'):
            m=copy.deepcopy(self.m)
            d={'root':m,'function':m['functions'][0],'range':m['functions'][0]['ranges'][0],'table':m['table']}[target]
            d['extra']=1;self.rejected(m)
    def test_coverage(self):
        for change in ('missing','duplicate','unknown'):
            m=copy.deepcopy(self.m)
            if change=='missing':m['functions'].pop()
            elif change=='duplicate':m['functions'][1]=m['functions'][0]
            else:m['functions'][0]['rva']='0x123'
            self.rejected(m)
    def test_ranges(self):
        for key,val in [('length',True),('length',0),('length',2**32),('rva','0x0')]:
            m=copy.deepcopy(self.m);m['functions'][0]['ranges'][0][key]=val;self.rejected(m)
    def test_digest_and_changed_bytes(self):
        m=copy.deepcopy(self.m);m['functions'][0]['sha256']='z'*64;self.rejected(m)
        self.blobs[int(self.m['functions'][0]['rva'],16)]=b'Y'*len(self.blobs[int(self.m['functions'][0]['rva'],16)])
        self.rejected(self.m)
    def test_reader_contract(self):
        for result in (b'',bytearray(b'X'),None,'X'):
            with self.assertRaises(ValueError):v.verify(self.m,lambda *_:result)
    def test_table(self):
        m=copy.deepcopy(self.m);m['table']['value_va']='0x796471';self.rejected(m)
        self.blobs[0x5f49d4]=struct.pack('<I',0x796471);self.rejected(self.m)
    def test_duplicate_json(self):
        with self.assertRaises(ValueError):json.loads('{"version":1,"version":1}',object_pairs_hook=v.unique_object)
    def test_unknown_binary_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake.exe';p.write_bytes(b'not a PE')
            for flags in (['-I'], ['-O', '-I']):
                result=subprocess.run([sys.executable,*flags,v.__file__,'--exe',str(p),'--dll',str(p)],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,1);self.assertIn('SHA-256 mismatch',result.stderr)
                self.assertNotIn('Traceback',result.stderr)

if __name__=='__main__':unittest.main()
