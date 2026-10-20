"""Read-only fingerprint check of the bounded H-container allocation path."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hpose_creation_verify import checked_pe, EXE_SHA, DLL_SHA

FUNCTIONS = {'0x38d500', '0x38d6d0', '0x38dc70', '0x39a840',
             '0x38cf30', '0x38d040', '0x40fb8c', '0x40fbb6', '0x40fbbc'}
IMPORTS = {
    0x5000f0: ('msvcp100.dll', '?_Xlength_error@std@@YAXPBD@Z'),
    0x500218: ('msvcr100.dll', '??0exception@std@@QAE@ABQBD@Z'),
    0x500224: ('msvcr100.dll', '??3@YAXPAX@Z'),
    0x500240: ('msvcr100.dll', '??2@YAPAXI@Z'),
    0x500244: ('msvcr100.dll', '_CxxThrowException'),
}


def verify(manifest, read):
    if (not isinstance(manifest, dict) or type(manifest.get('version')) is not int or manifest['version'] != 1
            or manifest.get('exe_sha256') != EXE_SHA
            or manifest.get('dll_sha256') != DLL_SHA):
        raise ValueError('manifest identity/version mismatch')
    rows = manifest.get('functions')
    if not isinstance(rows, list) or len(rows) != len(FUNCTIONS):
        raise ValueError('function coverage mismatch')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get('rva') not in FUNCTIONS or row['rva'] in seen:
            raise ValueError('function coverage mismatch')
        seen.add(row['rva'])
        ranges = row.get('ranges')
        if not isinstance(ranges, list) or not ranges:
            raise ValueError('missing ranges')
        digest = row.get('sha256')
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('invalid digest')
        h = hashlib.sha256()
        end = -1
        for item in ranges:
            start = item.get('rva') if isinstance(item, dict) else None
            length = item.get('length') if isinstance(item, dict) else None
            if not isinstance(start, str) or not start.startswith('0x'):
                raise ValueError('invalid range RVA')
            start = int(start, 16)
            if type(length) is not int or length <= 0 or start < 0 or start < end or start + length > 0x100000000:
                raise ValueError('invalid range extent')
            end = start + length
            h.update(read(start, length))
        if ranges[0]['rva'] != row['rva']:
            raise ValueError('entry mismatch')
        if h.hexdigest() != digest:
            raise ValueError('fingerprint mismatch ' + row['rva'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', required=True)
    p.add_argument('--dll', required=True)
    p.add_argument('--manifest', default=str(Path(__file__).with_name('hpose_allocation_manifest.json')))
    a = p.parse_args()
    read, base, imports = checked_pe(a.exe, EXE_SHA)
    checked_pe(a.dll, DLL_SHA)
    if base != 0x400000 or any(imports.get(rva) != value for rva, value in IMPORTS.items()):
        raise ValueError('image base/import identity mismatch')
    verify(json.loads(Path(a.manifest).read_text(encoding='utf-8')), read)
    print(json.dumps({'identity': 'verified', 'functions': 9, 'imports': 5, 'game_executed': False}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, struct.error, UnicodeError) as error:
        print('hpose_allocation_verify: ' + str(error), file=sys.stderr)
        sys.exit(1)
