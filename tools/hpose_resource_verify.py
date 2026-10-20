"""Read-only checks for bounded resource provenance and candidate release bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hpose_creation_verify import checked_pe, EXE_SHA, DLL_SHA
EXTENTS = {'0x2cf1d0': [{'rva': '0x2cf1d0', 'length': 438}], '0x38cf70': [{'rva': '0x38cf70', 'length': 92}], '0x38ddc0': [{'rva': '0x38ddc0', 'length': 732}], '0x38e0a0': [{'rva': '0x38e0a0', 'length': 794}], '0x38e3c0': [{'rva': '0x38e3c0', 'length': 261}], '0x395b30': [{'rva': '0x395b30', 'length': 203}], '0x395cc0': [{'rva': '0x395cc0', 'length': 520}, {'rva': '0x395ed0', 'length': 109}, {'rva': '0x395f40', 'length': 757}], '0x396240': [{'rva': '0x396240', 'length': 347}], '0x3963a0': [{'rva': '0x3963a0', 'length': 198}], '0x396470': [{'rva': '0x396470', 'length': 33}], '0x3bb320': [{'rva': '0x3bb320', 'length': 161}, {'rva': '0x3bb3d6', 'length': 37}], '0x3bb400': [{'rva': '0x3bb400', 'length': 1068}], '0x40fb8c': [{'rva': '0x40fb8c', 'length': 6}], '0x40fbb0': [{'rva': '0x40fbb0', 'length': 6}], '0x40fbb6': [{'rva': '0x40fbb6', 'length': 6}]}
EXTENTS.update({'0x25ef50': [{'rva': '0x25ef50', 'length': 90}], '0x394000': [{'rva': '0x394000', 'length': 838}], '0x394350': [{'rva': '0x394350', 'length': 282}, {'rva': '0x394470', 'length': 1322}], '0x3949a0': [{'rva': '0x3949a0', 'length': 400}], '0x3d8a20': [{'rva': '0x3d8a20', 'length': 125}]})
IMPORTS = {
 0x5000f0: ('msvcp100.dll', '?_Xlength_error@std@@YAXPBD@Z'),
 0x500218: ('msvcr100.dll', '??0exception@std@@QAE@ABQBD@Z'),
 0x50031c: ('msvcr100.dll', '_itoa'),
 0x500a60: ('granny2.dll', '_GrannyFreeMeshDeformer@4'),
 0x500a64: ('granny2.dll', '_GrannyFreeMeshBinding@4'),
 0x500b04: ('granny2.dll', '_GrannyFreeFile@4'),
 0x500984: ('dragonfly.dll', '?numberOfObjects@ReferenceCount@Dragonfly@@0IA'),
 0x500224: ('msvcr100.dll', '??3@YAXPAX@Z'),
 0x50024c: ('msvcr100.dll', 'memmove'),
}
BINDINGS = {
 'initializer_lightmap': (0x395e3f, 21),
 'initializer_normalmap': (0x395e5a, 14),
 'initializer_occlusion': (0x395e6e, 21),
 'lightmap_save_R': (0x394380, 6),
 'lightmap_reload_R': (0x39482a, 6),
 'lightmap_reserve_alias': (0x3948f9, 9),
 'lightmap_reserve_value': (0x39495a, 9),
 'normalmap_store': (0x394a9d, 6),
 'occlusion_store': (0x39415e, 9),
 'occlusion_fallback_store': (0x394290, 9),
 'reserve_context': (0x3d8a49, 9),
 'allocator_kills_context': (0x25ef53, 3),
 'extension_table': (0x5f22c0, 12),
 'extension_names': (0x5f22d8, 12),
 'normalmap_name': (0x5f22cc, 12),
 'lightmap_names': (0x5f4990, 68),
}

def keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError('unexpected manifest fields')

def verify(manifest, read):
    keys(manifest, ('version', 'exe_sha256', 'dll_sha256', 'functions', 'table', 'bindings'))
    if (type(manifest['version']) is not int or manifest['version'] != 2
            or manifest['exe_sha256'] != EXE_SHA or manifest['dll_sha256'] != DLL_SHA):
        raise ValueError('manifest identity/version mismatch')
    rows = manifest['functions']
    if type(rows) is not list or len(rows) != len(EXTENTS):
        raise ValueError('function coverage mismatch')
    seen = set()
    for row in rows:
        keys(row, ('rva', 'ranges', 'sha256'))
        rva = row['rva']
        if type(rva) is not str or rva not in EXTENTS or rva in seen:
            raise ValueError('function coverage mismatch')
        seen.add(rva)
        ranges = row['ranges']
        if type(ranges) is not list or len(ranges) != len(EXTENTS[rva]):
            raise ValueError('range coverage mismatch')
        digest = row['sha256']
        if (type(digest) is not str or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('invalid digest')
        h = hashlib.sha256()
        for item, expected in zip(ranges, EXTENTS[rva]):
            keys(item, ('rva', 'length'))
            if (type(item['rva']) is not str or type(item['length']) is not int
                    or item != expected):
                raise ValueError('range extent mismatch')
            data = read(int(item['rva'], 16), item['length'])
            if type(data) is not bytes or len(data) != item['length']:
                raise ValueError('short or invalid range read')
            h.update(data)
        if h.hexdigest() != digest:
            raise ValueError('fingerprint mismatch ' + rva)
    keys(manifest['table'], ('rva', 'value_va'))
    if manifest['table'] != {'rva': '0x5f49d4', 'value_va': '0x796470'}:
        raise ValueError('table binding mismatch')
    data = read(0x5f49d4, 4)
    if type(data) is not bytes or len(data) != 4 or data != struct.pack('<I', 0x796470):
        raise ValueError('table slot mismatch')
    bindings = manifest['bindings']
    if type(bindings) is not list or len(bindings) != len(BINDINGS):
        raise ValueError('binding coverage mismatch')
    seen = set()
    for binding in bindings:
        keys(binding, ('name', 'rva', 'length', 'sha256'))
        name = binding['name']
        if type(name) is not str or name not in BINDINGS or name in seen:
            raise ValueError('binding coverage mismatch')
        seen.add(name)
        rva, length = BINDINGS[name]
        if (type(binding['rva']) is not str or binding['rva'] != hex(rva)
                or type(binding['length']) is not int or binding['length'] != length):
            raise ValueError('binding extent mismatch')
        digest = binding['sha256']
        if (type(digest) is not str or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('invalid binding digest')
        data = read(rva, length)
        if type(data) is not bytes or len(data) != length:
            raise ValueError('short or invalid binding read')
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('binding fingerprint mismatch ' + name)

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', required=True)
    parser.add_argument('--dll', required=True)
    parser.add_argument('--manifest', default=str(Path(__file__).with_name('hpose_resource_manifest.json')))
    args = parser.parse_args()
    read, base, imports = checked_pe(args.exe, EXE_SHA)
    checked_pe(args.dll, DLL_SHA)
    if base != 0x400000 or any(imports.get(rva) != expected for rva, expected in IMPORTS.items()):
        raise ValueError('base/import mismatch')
    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    verify(manifest, read)
    print(json.dumps({'identity': 'verified', 'functions': len(EXTENTS), 'imports': len(IMPORTS),
                      'table_slots': 1, 'bindings': len(BINDINGS),
                      'dynamic_target_resolved': False, 'game_executed': False}))

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, struct.error, UnicodeError) as error:
        print('hpose_resource_verify: ' + str(error), file=sys.stderr)
        sys.exit(1)
