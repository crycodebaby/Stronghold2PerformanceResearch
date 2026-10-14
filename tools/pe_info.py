"""PE summary: machine, timestamp, flags, sections, imports, optional exports.

Usage: python -I tools/pe_info.py <file> [--exports] [--imports]
Read-only. Works on PE32 and PE32+.
"""
import datetime
import struct
import sys

MACHINES = {0x14C: "i386", 0x8664: "x86-64", 0xAA64: "arm64"}


class PE:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        d = self.data
        self.pe = struct.unpack_from("<I", d, 0x3C)[0]
        if d[self.pe:self.pe + 4] != b"PE\0\0":
            raise ValueError("not a PE file")
        self.machine, self.nsec, self.timestamp = struct.unpack_from("<HHI", d, self.pe + 4)
        self.characteristics = struct.unpack_from("<H", d, self.pe + 22)[0]
        self.opt = self.pe + 24
        self.magic = struct.unpack_from("<H", d, self.opt)[0]
        self.is64 = self.magic == 0x20B
        self.linker = (d[self.opt + 2], d[self.opt + 3])
        self.dllchar = struct.unpack_from("<H", d, self.opt + 70)[0]
        self.datadir = self.opt + (112 if self.is64 else 96)
        so = self.opt + struct.unpack_from("<H", d, self.pe + 20)[0]
        self.sections = []
        for i in range(self.nsec):
            name, vs, va, rs, ro = struct.unpack_from("<8sIIII", d, so + 40 * i)
            self.sections.append((name.rstrip(b"\0").decode("latin1"), vs, va, rs, ro))

    def rva2off(self, rva):
        for _, vs, va, rs, ro in self.sections:
            if va <= rva < va + max(vs, rs):
                return rva - va + ro
        return None

    def cstr(self, off):
        return self.data[off:self.data.index(b"\0", off)].decode("latin1")

    def directory(self, idx):
        return struct.unpack_from("<II", self.data, self.datadir + 8 * idx)

    def exports(self):
        rva, _ = self.directory(0)
        if not rva:
            return []
        o = self.rva2off(rva)
        n = struct.unpack_from("<I", self.data, o + 24)[0]
        names = self.rva2off(struct.unpack_from("<I", self.data, o + 32)[0])
        return [self.cstr(self.rva2off(struct.unpack_from("<I", self.data, names + 4 * i)[0])) for i in range(n)]

    def imports(self):
        rva, _ = self.directory(1)
        result = {}
        if not rva:
            return result
        o = self.rva2off(rva)
        ptr = 8 if self.is64 else 4
        ordflag = 1 << (63 if self.is64 else 31)
        while True:
            oft, _, _, name, ft = struct.unpack_from("<5I", self.data, o)
            if name == 0:
                break
            fns = []
            t = self.rva2off(oft or ft)
            while True:
                v = struct.unpack_from("<Q" if self.is64 else "<I", self.data, t)[0]
                if v == 0:
                    break
                fns.append(f"#{v & 0xFFFF}" if v & ordflag else self.cstr(self.rva2off(v & 0x7FFFFFFF) + 2))
                t += ptr
            result[self.cstr(self.rva2off(name))] = fns
            o += 20
        return result


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pe = PE(sys.argv[1])
    ts = datetime.datetime.fromtimestamp(pe.timestamp, datetime.UTC)
    print(f"machine      0x{pe.machine:04x} ({MACHINES.get(pe.machine, '?')}) {'PE32+' if pe.is64 else 'PE32'}")
    print(f"timestamp    {ts:%Y-%m-%d %H:%M:%S} UTC  linker {pe.linker[0]}.{pe.linker[1]}")
    print(f"LAA          {bool(pe.characteristics & 0x20)}")
    print(f"ASLR/NX      {bool(pe.dllchar & 0x40)}/{bool(pe.dllchar & 0x100)}")
    for name, vs, va, rs, _ in pe.sections:
        print(f"section      {name:8} va=0x{va:08x} vsize={vs:>10} raw={rs:>10}")
    if "--imports" in sys.argv:
        for dll, fns in pe.imports().items():
            print(f"import       {dll:28} {len(fns):4}")
    if "--exports" in sys.argv:
        for e in pe.exports():
            print(f"export       {e}")


if __name__ == "__main__":
    main()
