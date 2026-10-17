"""Verify local H-record evidence fingerprints; never loads or executes game binaries."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

EXE_SHA = 'f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b'
REQUIRED_FUNCTIONS = {'0x38e0a0','0x38e4d0','0x38dc70','0x38ddc0','0x38d040','0x38d6d0','0x38cf70'}
REQUIRED_EDGES = {'create-instance':(0x38e270,24),'create-world':(0x38e288,22),'create-local':(0x38e29e,25),'record-step':(0x38e2c0,11),'initial-selection':(0x38e2d1,36),'index-check':(0x38e51f,8),'indexed-selection':(0x38e613,15),'resize-input':(0x38e24b,15)}
DLL_SHA = '94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd'

def checked_pe(path, expected):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('binary SHA-256 mismatch')
    if data[:2] != b'MZ':
        raise ValueError('missing MZ')
    pe = struct.unpack_from('<I', data, 60)[0]
    if data[pe:pe+4] != b'PE\0\0':
        raise ValueError('missing PE signature')
    machine, n = struct.unpack_from('<HH', data, pe+4)
    size = struct.unpack_from('<H', data, pe+20)[0]
    optional = pe+24
    if machine != 0x14c or struct.unpack_from('<H', data, optional)[0] != 0x10b:
        raise ValueError('requires PE32/x86')
    base = struct.unpack_from('<I', data, optional+28)[0]
    sections=[]
    for j in range(n):
        s=optional+size+j*40
        virtual_size,rva,raw_size,offset=struct.unpack_from('<IIII',data,s+8)
        sections.append((rva,raw_size,offset))
    def read(rva,length):
        for start,count,offset in sections:
            if start <= rva and length >= 0 and rva+length <= start+count:
                result=data[offset+rva-start:offset+rva-start+length]
                if len(result)!=length: raise ValueError('truncated section')
                return result
        raise ValueError('RVA outside raw section')
    imports={}
    directory,size_dir=struct.unpack_from('<II',data,optional+104)
    def cstring(rva):
        result=bytearray()
        for k in range(512):
            v=read(rva+k,1)[0]
            if v==0:return result.decode('ascii')
            result.append(v)
        raise ValueError('unterminated import name')
    if directory:
        for j in range(min(size_dir//20,4096)):
            original,stamp,chain,name,first=struct.unpack('<IIIII',read(directory+20*j,20))
            if not any((original,stamp,chain,name,first)):break
            module=cstring(name).lower()
            for k in range(65536):
                value=struct.unpack('<I',read((original or first)+4*k,4))[0]
                if value==0:break
                if value&0x80000000:continue
                imports[first+4*k]=(module,cstring(value+2))
            else:raise ValueError('import table budget exceeded')
        else:raise ValueError('import descriptors missing terminator')
    return read,base,imports

def validate_manifest(m):
    if not isinstance(m,dict) or m.get('exe_sha256')!=EXE_SHA or m.get('dll_sha256')!=DLL_SHA:
        raise ValueError('manifest identity mismatch')
    def sha(v):
        if not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v):
            raise ValueError('invalid SHA-256')
    def rva(v):
        if not isinstance(v,str) or not v.startswith('0x'):raise ValueError('invalid RVA')
        n=int(v,16)
        if n<0 or n>0xffffffff:raise ValueError('RVA outside uint32')
        return n
    def length(v):
        if type(v) is not int or not 0<v<=0xffffffff:raise ValueError('invalid length')
        return v
    fs=m.get('functions');es=m.get('edges')
    if not isinstance(fs,list) or len(fs)!=7 or not isinstance(es,list) or len(es)!=8:
        raise ValueError('manifest coverage mismatch')
    seen=set()
    for f in fs:
        if not isinstance(f,dict) or f.get('rva') not in REQUIRED_FUNCTIONS or f['rva'] in seen:
            raise ValueError('function coverage mismatch')
        seen.add(f['rva']);sha(f.get('sha256'))
        rs=f.get('ranges')
        if not isinstance(rs,list) or not rs:raise ValueError('empty function ranges')
        end=-1
        for item in rs:
            if not isinstance(item,dict):raise ValueError('invalid range')
            start=rva(item.get('rva'));n=length(item.get('length'))
            if start<end or start+n>0x100000000:raise ValueError('overlapping/overflow range')
            end=start+n
        if rs[0]['rva']!=f['rva']:raise ValueError('function entry mismatch')
    seen=set()
    for e in es:
        if not isinstance(e,dict) or e.get('label') not in REQUIRED_EDGES or e['label'] in seen:
            raise ValueError('edge coverage mismatch')
        seen.add(e['label']);sha(e.get('sha256'))
        if (rva(e.get('rva')),length(e.get('length')))!=REQUIRED_EDGES[e['label']]:
            raise ValueError('edge extent mismatch')
    return m

def verify_fingerprints(manifest,read):
    validate_manifest(manifest)
    for f in manifest['functions']:
        h=hashlib.sha256()
        for r in f['ranges']:h.update(read(int(r['rva'],16),r['length']))
        if h.hexdigest()!=f['sha256']:raise ValueError('fingerprint mismatch '+f['rva'])
    for e in manifest['edges']:
        if hashlib.sha256(read(int(e['rva'],16),e['length'])).hexdigest()!=e['sha256']:
            raise ValueError('edge fingerprint mismatch '+e['label'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',required=True)
    p.add_argument('--dll',required=True)
    p.add_argument('--manifest',default=str(Path(__file__).with_name('hpose_creation_manifest.json')))
    a=p.parse_args()
    read,base,imports=checked_pe(a.exe,EXE_SHA)
    checked_pe(a.dll,DLL_SHA)
    if base != 0x400000:raise ValueError('unexpected image base')
    manifest=json.loads(Path(a.manifest).read_text(encoding='utf-8'))
    expected_imports={0x500aac:'_GrannyInstantiateModel@4',0x500ab0:'_GrannyNewWorldPose@4',0x500ab4:'_GrannyNewLocalPose@4'}
    for rva,name in expected_imports.items():
        if imports.get(rva)!=('granny2.dll',name):raise ValueError('IAT identity mismatch')
    verify_fingerprints(manifest,read)
    print(json.dumps({'identity':'verified','iat_entries_verified':3,'function_fingerprints_verified':7,'edge_fingerprints_verified':8,'game_executed':False}))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,TypeError,struct.error,UnicodeError) as error:
        print('hpose_creation_verify: '+str(error),file=sys.stderr)
        sys.exit(1)
