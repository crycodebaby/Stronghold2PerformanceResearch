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
        for binding in self.m['bindings']:
            b = b'B' * binding['length']
            self.blobs[int(binding['rva'], 16)] = b
            binding['sha256'] = hashlib.sha256(b).hexdigest()
    def read(self, rva, length):
        return self.blobs[rva]
    def rejected(self, m):
        with self.assertRaises(ValueError): v.verify(m, self.read)
    def test_success(self): v.verify(self.m, self.read)
    def test_identity_version(self):
        for key, val in [('version',True),('version',1),('version',3),('exe_sha256','0'*64),('dll_sha256','0'*64)]:
            m=copy.deepcopy(self.m);m[key]=val;self.rejected(m)
    def test_unknown_fields(self):
        for target in ('root','function','range','table','binding'):
            m=copy.deepcopy(self.m)
            d={'root':m,'function':m['functions'][0],'range':m['functions'][0]['ranges'][0],'table':m['table'],'binding':m['bindings'][0]}[target]
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
    def test_initializer_function_coverage(self):
        for rva in ('0x394350','0x3949a0','0x394000','0x3d8a20','0x25ef50'):
            m=copy.deepcopy(self.m)
            m['functions']=[f for f in m['functions'] if f['rva']!=rva]
            self.rejected(m)
    def test_binding_coverage(self):
        for change in ('missing','duplicate','unknown'):
            m=copy.deepcopy(self.m)
            if change=='missing':m['bindings'].pop()
            elif change=='duplicate':m['bindings'][1]=m['bindings'][0]
            else:m['bindings'][0]['name']='unknown'
            self.rejected(m)
    def test_binding_extent(self):
        for key,value in [('rva','0x395e40'),('length',True),('length',0),('length',22)]:
            m=copy.deepcopy(self.m);m['bindings'][0][key]=value;self.rejected(m)
    def test_binding_mutation(self):
        for binding in self.m['bindings']:
            rva=int(binding['rva'],16); original=self.blobs[rva]
            self.blobs[rva]=b'C'*len(original);self.rejected(self.m)
            self.blobs[rva]=original
        m=copy.deepcopy(self.m);m['bindings'][0]['sha256']='g'*64;self.rejected(m)
    def test_binding_reader_contract(self):
        first=int(self.m['bindings'][0]['rva'],16)
        for result in (b'',bytearray(b'B'*21),None):
            with self.assertRaises(ValueError):
                v.verify(self.m,lambda r,n: result if r==first else self.read(r,n))
    def test_unknown_binary_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake.exe';p.write_bytes(b'not a PE')
            for flags in (['-I'], ['-O', '-I']):
                result=subprocess.run([sys.executable,*flags,v.__file__,'--exe',str(p),'--dll',str(p)],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,1);self.assertIn('SHA-256 mismatch',result.stderr)
                self.assertNotIn('Traceback',result.stderr)

if __name__=='__main__':unittest.main()
