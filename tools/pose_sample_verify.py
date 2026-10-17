"""Read-only identity/byte gates for the bounded sample write-extent evidence.

Does not load the DLL, execute game code, or establish runtime pointer validity.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hpose_creation_verify import checked_pe, EXE_SHA, DLL_SHA
from pe_info import PE

MANIFEST_SHA = 'c06dbf7b1a4a579f9bc45885b18e5df7c0403024292e858fd1e178087c12a4a5'
MODULES = {'exe': (EXE_SHA, 0x400000), 'dll': (DLL_SHA, 0x50000000)}
IMPORTS = {0x500a98: '_GrannySampleModelAnimationsAccelerated@20',
           0x500b10: '_GrannyGetSourceSkeleton@4', 0x500aac: '_GrannyInstantiateModel@4',
           0x500ab0: '_GrannyNewWorldPose@4', 0x500ab4: '_GrannyNewLocalPose@4',
           0x500ad4: '_GrannyPlayControlledAnimation@12'}
EXPORTS = {'_GrannySampleModelAnimationsAccelerated@20': 0x4f6d0,
           '_GrannyGetSourceSkeleton@4': 0x4f4d0, '_GrannyInstantiateModel@4': 0x4f4b0,
           '_GrannyPlayControlledAnimation@12': 0x50f70,
           '_GrannyEndControlledAnimation@4': 0x50fd0, '_GrannyPlayControlledPose@20': 0x51130}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def load_manifest(path):
    return validate_manifest(json.loads(Path(path).read_text(encoding='utf-8'),
                                       object_pairs_hook=unique_object,
                                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON'))))


def validate_manifest(m):
    if not isinstance(m, dict) or set(m) != {'schema', 'modules'} or type(m['schema']) is not int or m['schema'] != 2:
        raise ValueError('manifest schema mismatch')
    if not isinstance(m['modules'], list) or len(m['modules']) != 2:
        raise ValueError('module coverage mismatch')
    seen = set()
    for mod in m['modules']:
        if not isinstance(mod, dict) or set(mod) != {'module', 'sha256', 'image_base', 'evidence'}:
            raise ValueError('module schema mismatch')
        name = mod['module']
        if not isinstance(name, str) or name not in MODULES or name in seen:
            raise ValueError('module identity mismatch')
        seen.add(name)
        sha, base = MODULES[name]
        if mod['sha256'] != sha or mod['image_base'] != hex(base):
            raise ValueError('module identity mismatch')
        if not isinstance(mod['evidence'], list) or not mod['evidence']:
            raise ValueError('empty evidence')
        ids = set()
        for entry in mod['evidence']:
            if not isinstance(entry, dict) or set(entry) != {'id', 'ranges'}:
                raise ValueError('evidence schema mismatch')
            if not isinstance(entry['id'], str) or entry['id'] in ids:
                raise ValueError('duplicate evidence')
            ids.add(entry['id'])
            if not isinstance(entry['ranges'], list) or not entry['ranges']:
                raise ValueError('empty ranges')
            end = -1
            for r in entry['ranges']:
                if not isinstance(r, dict) or set(r) != {'rva', 'length', 'sha256'}:
                    raise ValueError('range schema mismatch')
                if not isinstance(r['rva'], str) or not r['rva'].startswith('0x'):
                    raise ValueError('invalid RVA')
                start = int(r['rva'], 16)
                n = r['length']
                if type(n) is not int or not 0 < n <= 65536 or start < end or start + n > 0x100000000:
                    raise ValueError('invalid range extent')
                end = start + n
                if not isinstance(r['sha256'], str) or len(r['sha256']) != 64 or any(c not in '0123456789abcdef' for c in r['sha256']):
                    raise ValueError('invalid digest')
    digest = hashlib.sha256(json.dumps(m, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if digest != MANIFEST_SHA:
        raise ValueError('manifest coverage/digest mismatch')
    return m


def verify_bytes(mod, read):
    count = 0
    for entry in mod['evidence']:
        for r in entry['ranges']:
            data = read(int(r['rva'], 16), r['length'])
            if len(data) != r['length'] or hashlib.sha256(data).hexdigest() != r['sha256']:
                raise ValueError('byte fingerprint mismatch: ' + mod['module'] + '/' + entry['id'])
            count += 1
    return count


def named_exports(path, read):
    directory, _ = PE(path).directory(0)
    header = read(directory, 40)
    nfunc, nnames, fns, names, ordinals = struct.unpack_from('<IIIII', header, 20)
    if not 0 < nnames <= nfunc <= 65536:
        raise ValueError('export table extent mismatch')
    result = {}
    for i in range(nnames):
        name_rva = struct.unpack('<I', read(names + i * 4, 4))[0]
        raw = bytearray()
        for j in range(512):
            v = read(name_rva + j, 1)[0]
            if not v:
                break
            raw.append(v)
        else:
            raise ValueError('unterminated export name')
        name = raw.decode('ascii')
        ordinal = struct.unpack('<H', read(ordinals + i * 2, 2))[0]
        if ordinal >= nfunc or name in result:
            raise ValueError('export identity mismatch')
        result[name] = struct.unpack('<I', read(fns + ordinal * 4, 4))[0]
    return result


def verify(exe, dll, manifest):
    validate_manifest(manifest)
    readers = {}
    for name, path in [('exe', exe), ('dll', dll)]:
        sha, expected_base = MODULES[name]
        read, base, imports = checked_pe(path, sha)
        if base != expected_base:
            raise ValueError('image base mismatch')
        readers[name] = read
        if name == 'exe' and any(imports.get(rva) != ('granny2.dll', symbol) for rva, symbol in IMPORTS.items()):
            raise ValueError('IAT identity mismatch')
    exports = named_exports(dll, readers['dll'])
    if any(exports.get(symbol) != rva for symbol, rva in EXPORTS.items()):
        raise ValueError('export identity mismatch')
    ranges = sum(verify_bytes(mod, readers[mod['module']]) for mod in manifest['modules'])
    return {'identity': 'verified', 'modules': 2, 'evidence_entries': 54, 'ranges': ranges,
            'imports': len(IMPORTS), 'exports': len(EXPORTS), 'game_executed': False,
            'unconditional_sample_initialized_span_proven': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', required=True, type=Path)
    p.add_argument('--dll', required=True, type=Path)
    p.add_argument('--manifest', type=Path, default=Path(__file__).with_name('pose_sample_manifest.json'))
    a = p.parse_args()
    print(json.dumps(verify(a.exe, a.dll, load_manifest(a.manifest))))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, struct.error, UnicodeError, IndexError) as error:
        print('pose_sample_verify: ' + str(error), file=sys.stderr)
        sys.exit(1)
