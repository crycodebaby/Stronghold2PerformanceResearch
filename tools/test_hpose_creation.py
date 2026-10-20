"""Game-free schema, PE and fail-closed tests for bounded H-record evidence."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import hpose_creation_verify as v

class HposeCreationTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads(Path(v.__file__).with_name('hpose_creation_manifest.json').read_text())
    def test_complete_manifest(self):v.validate_manifest(self.manifest)
    def test_missing_and_duplicate_entries(self):
        for key in ('functions','edges'):
            for mode in ('empty','missing','duplicate'):
                with self.subTest(key=key,mode=mode):
                    m=copy.deepcopy(self.manifest)
                    if mode=='empty':m[key]=[]
                    elif mode=='missing':m[key].pop()
                    else:m[key][-1]=copy.deepcopy(m[key][0])
                    with self.assertRaises(ValueError):v.validate_manifest(m)
    def test_invalid_schema(self):
        for field,value in [('length',0),('length',True),('length',-1),('length','2'),('rva','garbage')]:
            m=copy.deepcopy(self.manifest);m['functions'][0]['ranges'][0][field]=value
            with self.assertRaises(ValueError):v.validate_manifest(m)
        m=copy.deepcopy(self.manifest);m['edges'][0]['length']+=1
        with self.assertRaises(ValueError):v.validate_manifest(m)
        m=copy.deepcopy(self.manifest);m['functions'][0]['sha256']='z'*64
        with self.assertRaises(ValueError):v.validate_manifest(m)
    def test_fingerprints_and_tamper(self):
        m=copy.deepcopy(self.manifest)
        read=lambda r,n: bytes([r%251])*n
        for f in m['functions']:
            f['sha256']=hashlib.sha256(b''.join(read(int(r['rva'],16),r['length']) for r in f['ranges'])).hexdigest()
        for e in m['edges']:e['sha256']=hashlib.sha256(read(int(e['rva'],16),e['length'])).hexdigest()
        v.verify_fingerprints(m,read)
        bad=copy.deepcopy(m);bad['functions'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):v.verify_fingerprints(bad,read)
        bad=copy.deepcopy(m);bad['edges'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):v.verify_fingerprints(bad,read)
    def test_synthetic_pe_and_unknown_build(self):
        b=bytearray(1024);b[:2]=b'MZ';struct.pack_into('<I',b,60,128);b[128:132]=b'PE\0\0'
        struct.pack_into('<HH',b,132,0x14c,1);struct.pack_into('<H',b,148,224)
        struct.pack_into('<H',b,152,0x10b);struct.pack_into('<I',b,180,0x400000)
        struct.pack_into('<IIII',b,384,512,0x1000,512,512)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fixture.exe';p.write_bytes(b);sha=hashlib.sha256(b).hexdigest()
            read,base,imports=v.checked_pe(p,sha);self.assertEqual(read(0x1000,4),b'\0'*4);self.assertEqual(base,0x400000)
            with self.assertRaises(ValueError):read(0x11ff,2)
            with self.assertRaises(ValueError):v.checked_pe(p,'0'*64)
            b[132]=0;p.write_bytes(b)
            with self.assertRaises(ValueError):v.checked_pe(p,hashlib.sha256(b).hexdigest())
    def test_optimized_cli_rejects_without_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'unknown.exe';p.write_bytes(b'own synthetic unknown build')
            r=subprocess.run([sys.executable,'-O','-I',v.__file__,'--exe',str(p),'--dll',str(p)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertIn('SHA-256 mismatch',r.stderr);self.assertNotIn('Traceback',r.stderr)

if __name__=='__main__':unittest.main()
