"""Read-only PE/x86 byte checks for audit claims; stdlib, no binary execution."""
import argparse,hashlib,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]  # published copy: <RE-Projects>/SH2-Perf/audits/<this dir>
class PE:
    def __init__(self,p):
        self.path=p; self.b=p.read_bytes(); self.sha=hashlib.sha256(self.b).hexdigest()
        pe=self.u32(0x3c); assert self.b[pe:pe+4]==b'PE\0\0'
        self.machine=self.u16(pe+4); count=self.u16(pe+6); size=self.u16(pe+20); opt=pe+24
        assert self.machine==0x14c and self.u16(opt)==0x10b
        self.base=self.u32(opt+28); self.sections=[]
        for i in range(count):
            s=opt+size+40*i
            self.sections.append((self.u32(s+12),self.u32(s+8),self.u32(s+20),self.u32(s+16)))
        self.dirs=[(self.u32(opt+96+i*8),self.u32(opt+100+i*8)) for i in range(16)]
    def u16(self,n):return struct.unpack_from('<H',self.b,n)[0]
    def u32(self,n):return struct.unpack_from('<I',self.b,n)[0]
    def off(self,rva):
        for va,vs,raw,rs in self.sections:
            if va<=rva<va+max(vs,rs):
                assert rva-va<rs; return raw+rva-va
        raise ValueError(hex(rva))
    def data(self,rva,n):return self.b[self.off(rva):self.off(rva)+n]
    def string(self,rva):
        o=self.off(rva); return self.b[o:self.b.index(0,o)].decode('ascii')
    def imports(self):
        out={}; p=self.off(self.dirs[1][0])
        while self.u32(p+12):
            name=self.string(self.u32(p+12)); first=self.u32(p+16); lookup=self.u32(p) or first; n=0
            while True:
                v=self.u32(self.off(lookup+4*n))
                if not v:break
                label='ordinal:'+str(v&65535) if v&0x80000000 else self.string(v+2)
                out[label]={'dll':name,'iat_rva':first+4*n};n+=1
            p+=20
        return out
    def exports(self):
        p=self.off(self.dirs[0][0]); count=self.u32(p+24); funcs=self.u32(p+28); names=self.u32(p+32); ords=self.u32(p+36);out={}
        for i in range(count):
            name=self.string(self.u32(self.off(names+4*i))); ordinal=self.u16(self.off(ords+2*i))
            out[name]=self.u32(self.off(funcs+4*ordinal))
        return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT); args=ap.parse_args()
    exe=PE(args.root/'Stronghold 2'/'Stronghold2.exe'); granny=PE(args.root/'Stronghold 2'/'granny2.dll')
    assert exe.sha=='f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b'
    assert granny.sha=='94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd'
    imports=exe.imports(); exports=granny.exports()
    checks=[]
    for name,iat,rva,pop,ret in [
        ('_GrannySetModelClock@8',0x500ab8,0x4f4e0,8,0x4f4f2),
        ('_GrannySampleModelAnimationsAccelerated@20',0x500a98,0x4f6d0,20,0x4f6f1),
        ('_GrannyDeformVertices@24',0x500afc,0x52f90,24,0x52fb6),
        ('_GrannyGetWorldPoseComposite4x4Array@4',0x500af4,0x52bb0,4,0x52bbd),
        ('_GrannyFreeModelInstance@4',0x500aa0,0x4f4c0,4,0x4f4cb),
        ('_GrannyFreeMeshDeformer@4',0x500a60,0x52f80,4,0x52f8b)]:
        assert imports[name]['iat_rva']==iat and imports[name]['dll'].lower()=='granny2.dll'
        assert exports[name]==rva and granny.data(ret,3)==b'\xc2'+struct.pack('<H',pop)
        checks.append({'export':name,'iat_rva':hex(iat),'export_rva':hex(rva),'ret_rva':hex(ret),'callee_pop_bytes':pop})
    assert exe.data(0x38e6d9,6)==b'\xff\x15'+struct.pack('<I',0x900a98)
    assert 0x38e6d9+6==0x38e6df
    calls=[]
    for ln in (HERE.parent/'work'/'binary'/'exe'/'references.txt').read_text().splitlines():
        if ln.startswith('ROOT 0078c9e0'):break
        if ln.startswith('REF') and 'UNCONDITIONAL_CALL' in ln:
            parts=ln.split(); va=int(parts[1],16); b=exe.data(va-exe.base,5)
            assert b[0]==0xe8 and va+5+struct.unpack('<i',b[1:])[0]==0x78e4d0
            calls.append({'call_rva':hex(va-exe.base),'caller_rva':hex(int(parts[3].split('=')[1],16)-exe.base)})
    result={'exe_sha256':exe.sha,'granny_sha256':granny.sha,'exe_image_base':hex(exe.base),'granny_image_base':hex(granny.base),
            'machine':'x86/PE32','import_export_checks':checks,'direct_calls_to_rva_38e4d0':calls,
            'sample_return_rva':'0x38e6df','granny_import_count':sum(v['dll'].lower()=='granny2.dll' for v in imports.values())}
    (HERE/'binary_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'Binary identity, 6 import/export/pop-count checks, sample return site and {len(calls)} direct call sites verified against file bytes.')
    print('Distinct direct caller functions (including recursion):',len({x['caller_rva'] for x in calls}))

if __name__=='__main__': main()
