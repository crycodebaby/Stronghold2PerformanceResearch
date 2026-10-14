// granny_raw: decompress a GR2 file to an uncompressed ("raw") GR2 using the
// game's own granny2.dll at runtime. Local use only; never redistribute the DLL
// or converted assets.
//
// Build (x86 Developer prompt):  cl /O2 /EHsc granny_raw.cpp
// Usage: granny_raw.exe <dir-with-granny2.dll> <in.gr2> <out.gr2>
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <cstdio>

using ConvertFileToRaw_t = int(__stdcall*)(const char*, const char*);
using GetVersionString_t = const char*(__stdcall*)();

int main(int argc, char** argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: granny_raw <dir-with-granny2.dll> <in.gr2> <out.gr2>\n");
        return 2;
    }
    char dllPath[MAX_PATH];
    snprintf(dllPath, sizeof(dllPath), "%s\\granny2.dll", argv[1]);
    HMODULE granny = LoadLibraryA(dllPath);
    if (!granny) {
        fprintf(stderr, "LoadLibrary(%s) failed: %lu\n", dllPath, GetLastError());
        return 1;
    }
    auto version = reinterpret_cast<GetVersionString_t>(GetProcAddress(granny, "_GrannyGetVersionString@0"));
    auto convert = reinterpret_cast<ConvertFileToRaw_t>(GetProcAddress(granny, "_GrannyConvertFileToRaw@8"));
    if (!convert) {
        fprintf(stderr, "_GrannyConvertFileToRaw@8 not found\n");
        return 1;
    }
    printf("granny2.dll version: %s\n", version ? version() : "?");
    const int ok = convert(argv[2], argv[3]);
    printf("ConvertFileToRaw(%s -> %s) = %d\n", argv[2], argv[3], ok);
    return ok ? 0 : 1;
}
