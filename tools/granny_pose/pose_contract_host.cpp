// Local x86 differential host. No game assets, historical pointers, hooks or SDK.
// Only the statically verified field projection consumed by this DLL is declared.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <float.h>
#include <xmmintrin.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include "pose_math.h"

using own_pose::Matrix;
struct Pose { int count; Matrix* world; Matrix* composite; };
struct BoneProjection { unsigned char prefix[76]; Matrix inverse; unsigned char tail[12]; };
struct SkeletonProjection { const char* name; int count; BoneProjection* bones; int trailing; };
static_assert(sizeof(void*) == 4 && sizeof(Pose) == 12 && sizeof(Matrix) == 64);
static_assert(sizeof(BoneProjection) == 152 && offsetof(BoneProjection, inverse) == 76);
static_assert(offsetof(SkeletonProjection, bones) == 8);
constexpr char expected_hash[] = "94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd";

[[noreturn]] void fail(const char* what) { std::fprintf(stderr, "FAIL: %s\n", what); std::exit(1); }
void require(bool ok, const char* what) { if (!ok) fail(what); }
std::string file_hash(const wchar_t* path) {
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    require(file != INVALID_HANDLE_VALUE, "open DLL for SHA-256");
    BCRYPT_ALG_HANDLE alg = nullptr; BCRYPT_HASH_HANDLE hash = nullptr;
    require(BCryptOpenAlgorithmProvider(&alg, BCRYPT_SHA256_ALGORITHM, nullptr, 0) == 0, "SHA-256 provider");
    DWORD length = 0, got = 0;
    require(BCryptGetProperty(alg, BCRYPT_OBJECT_LENGTH, reinterpret_cast<PUCHAR>(&length), sizeof(length), &got, 0) == 0, "hash object size");
    std::vector<unsigned char> object(length);
    require(BCryptCreateHash(alg, &hash, object.data(), length, nullptr, 0, 0) == 0, "create hash");
    std::array<unsigned char, 65536> buffer{};
    for (;;) {
        DWORD n = 0;
        require(ReadFile(file, buffer.data(), static_cast<DWORD>(buffer.size()), &n, nullptr) != 0, "hash read");
        if (!n) break;
        require(BCryptHashData(hash, buffer.data(), n, 0) == 0, "hash bytes");
    }
    std::array<unsigned char, 32> digest{};
    require(BCryptFinishHash(hash, digest.data(), static_cast<ULONG>(digest.size()), 0) == 0, "finish hash");
    BCryptDestroyHash(hash); BCryptCloseAlgorithmProvider(alg, 0); CloseHandle(file);
    const char* hex = "0123456789abcdef"; std::string result;
    for (unsigned char v : digest) { result += hex[v >> 4]; result += hex[v & 15]; }
    return result;
}
template<class T> T entry(HMODULE dll, const char* name) {
    FARPROC result = GetProcAddress(dll, name);
    require(result != nullptr, name);
    // MSVC's function-pointer warning is avoided by a representation copy.
    T typed{}; static_assert(sizeof(typed) == sizeof(result));
    std::memcpy(&typed, &result, sizeof(typed)); return typed;
}
struct Api {
    Pose* (__stdcall* make)(int);
    Pose* (__stdcall* in_place)(int, void*);
    void (__stdcall* free_pose)(Pose*);
    int (__stdcall* size)(int);
    int (__stdcall* count)(const Pose*);
    Matrix* (__stdcall* world)(const Pose*);
    Matrix* (__stdcall* composite)(const Pose*);
    Matrix* (__stdcall* world_bone)(const Pose*, int);
    Matrix* (__stdcall* composite_bone)(const Pose*, int);
    void (__stdcall* build)(const SkeletonProjection*, int, int, Pose*);
    explicit Api(HMODULE dll) :
      make(entry<decltype(make)>(dll, "_GrannyNewWorldPose@4")),
      in_place(entry<decltype(in_place)>(dll, "_GrannyNewWorldPoseInPlace@8")),
      free_pose(entry<decltype(free_pose)>(dll, "_GrannyFreeWorldPose@4")),
      size(entry<decltype(size)>(dll, "_GrannyGetResultingWorldPoseSize@4")),
      count(entry<decltype(count)>(dll, "_GrannyGetWorldPoseBoneCount@4")),
      world(entry<decltype(world)>(dll, "_GrannyGetWorldPose4x4Array@4")),
      composite(entry<decltype(composite)>(dll, "_GrannyGetWorldPoseComposite4x4Array@4")),
      world_bone(entry<decltype(world_bone)>(dll, "_GrannyGetWorldPose4x4@8")),
      composite_bone(entry<decltype(composite_bone)>(dll, "_GrannyGetWorldPoseComposite4x4@8")),
      build(entry<decltype(build)>(dll, "_GrannyBuildCompositeFromWorldPose@16")) {}
};
struct Guarded {
    void* reservation; unsigned char* committed; unsigned char* data; std::size_t prefix;
    explicit Guarded(std::size_t size) {
        SYSTEM_INFO info{}; GetSystemInfo(&info);
        std::size_t page = info.dwPageSize, bytes = ((size + 64 + page - 1) / page) * page;
        reservation = VirtualAlloc(nullptr, bytes + 2 * page, MEM_RESERVE, PAGE_NOACCESS);
        require(reservation != nullptr, "guard reservation");
        committed = static_cast<unsigned char*>(VirtualAlloc(static_cast<unsigned char*>(reservation) + page,
                                   bytes, MEM_COMMIT, PAGE_READWRITE));
        require(committed != nullptr, "guard commit");
        std::memset(committed, 0xa5, bytes);
        data = committed + bytes - size; prefix = static_cast<std::size_t>(data - committed);
        require((reinterpret_cast<std::uintptr_t>(data) & 15) == 0, "host alignment");
    }
    void check() const { for (std::size_t i = 0; i < prefix; ++i) require(committed[i] == 0xa5, "prefix canary"); }
    ~Guarded() { VirtualFree(reservation, 0, MEM_RELEASE); }
};
struct Statistics {
    std::uint64_t layout_cases = 0, matrix_cases = 0, bones = 0, components = 0;
    std::uint64_t exact_cases = 0, rounded_cases = 0, differing_components = 0;
    double max_abs = 0, max_scaled = 0;
    bool has_counterexample = false;
    Matrix example_a{}, example_b{}, example_original{}, example_own{};
    int example_component = 0;
    std::uint64_t corpus_cases[3]{};
    std::uint64_t signed_zero_differences = 0;
};
std::uint32_t rng_state = 0x53483226u;
std::uint32_t random32() { rng_state ^= rng_state << 13; rng_state ^= rng_state >> 17; rng_state ^= rng_state << 5; return rng_state; }
Matrix matrix(int kind) {
    Matrix result{};
    for (int row = 0; row < 4; ++row) for (int col = 0; col < 3; ++col) {
        if (kind == 0) result.v[row * 4 + col] = row == col ? 1.0f : 0.0f;
        else if (kind == 1) result.v[row * 4 + col] = static_cast<float>(static_cast<int>(random32() % 4097) - 2048) / 256.0f;
        else result.v[row * 4 + col] = static_cast<float>((static_cast<double>(random32()) / 4294967295.0) * 16.0 - 8.0);
    }
    result.v[15] = 1.0f; return result;
}
void layout(const Api& api, int n, Statistics& stats) {
    const int bytes = 16 + n * 128;
    require(api.size(n) == bytes, "required size formula");
    Guarded storage(static_cast<std::size_t>(bytes));
    Pose* pose = api.in_place(n, storage.data);
    require(pose == reinterpret_cast<Pose*>(storage.data), "in-place returns caller storage");
    require(pose->count == n && api.count(pose) == n, "pose bone count");
    require(reinterpret_cast<unsigned char*>(api.world(pose)) == storage.data + 16, "world offset");
    require(reinterpret_cast<unsigned char*>(api.composite(pose)) == storage.data + 16 + n * 64, "composite offset");
    require(api.world(pose) == pose->world && api.composite(pose) == pose->composite, "getter projection");
    for (int i = 12; i < bytes; ++i) require(storage.data[i] == 0xa5, "constructor leaves padding/matrix bytes uninitialized");
    for (int i = 0; i < n; ++i) {
        require(api.world_bone(pose, i) == pose->world + i, "world stride");
        require(api.composite_bone(pose, i) == pose->composite + i, "composite stride");
    }
    require(api.world_bone(pose, n) == nullptr && api.composite_bone(pose, n) == nullptr, "upper bound getter");
    storage.check();
    // A second allocation's lifetime is independent; never free in-place storage through Granny.
    Pose* other = api.make(n);
    require(other != nullptr && other != pose && api.count(other) == n, "owned allocation");
    require((reinterpret_cast<std::uintptr_t>(api.world(other)) & 15) == 0, "owned world alignment");
    require((reinterpret_cast<std::uintptr_t>(api.composite(other)) & 15) == 0, "owned composite alignment");
    api.free_pose(other); storage.check(); ++stats.layout_cases;
}
void differential(const Api& api, int n, int first, int count, int kind, Statistics& stats) {
    require(n > 0 && n <= 257 && first >= 0 && count >= 0 && first <= n && count <= n - first,
            "host input domain before original call");
    std::vector<BoneProjection> bones(static_cast<std::size_t>(n));
    std::vector<Matrix> inverse(static_cast<std::size_t>(n)), expected(static_cast<std::size_t>(n));
    SkeletonProjection skeleton{"own-generated", n, bones.data(), 0};
    Guarded storage(static_cast<std::size_t>(api.size(n)));
    Pose* pose = api.in_place(n, storage.data);
    for (int i = 0; i < n; ++i) {
        bones[i].inverse = inverse[i] = matrix(kind);
        pose->world[i] = matrix(kind);
        std::memset(&pose->composite[i], 0x5a, sizeof(Matrix));
        expected[i] = pose->composite[i];
    }
    std::vector<unsigned char> bone_snapshot(sizeof(BoneProjection) * bones.size());
    std::memcpy(bone_snapshot.data(), bones.data(), bone_snapshot.size());
    std::vector<unsigned char> pose_snapshot(storage.data, storage.data + api.size(n));
    const SkeletonProjection skeleton_snapshot = skeleton;
    own_pose::composite(inverse.data(), pose->world, expected.data(), static_cast<std::size_t>(first), static_cast<std::size_t>(count));
    api.build(&skeleton, first, count, pose);
    require(std::memcmp(&skeleton, &skeleton_snapshot, sizeof(skeleton)) == 0, "skeleton header preserved");
    require(std::memcmp(bones.data(), bone_snapshot.data(), bone_snapshot.size()) == 0, "bone records preserved");
    const std::size_t changed_begin = static_cast<std::size_t>(16 + n * 64 + first * 64);
    const std::size_t changed_end = changed_begin + static_cast<std::size_t>(count * 64);
    for (std::size_t i = 0; i < pose_snapshot.size(); ++i)
        if (i < changed_begin || i >= changed_end) require(storage.data[i] == pose_snapshot[i], "only selected composite bytes may change");
    bool bit_equal = true;
    for (int i = first; i < first + count; ++i) for (int j = 0; j < 16; ++j) {
        float original = pose->composite[i].v[j], own = expected[i].v[j];
        require(std::isfinite(original) && std::isfinite(own), "finite output");
        double scale = 0;
        if (j % 4 < 3) {
            for (int k = 0; k < 3; ++k)
                scale += std::abs(static_cast<double>(inverse[i].v[(j / 4) * 4 + k]) * pose->world[i].v[k * 4 + j % 4]);
            if (j / 4 == 3) scale += std::abs(static_cast<double>(pose->world[i].v[12 + j % 4]));
        }
        double error = std::abs(static_cast<double>(original) - own);
        // PREDECLARED criterion: 8 float32 eps * max(1, sum of absolute terms).
        double bound_scale = std::max(1.0, scale);
        require(error <= 8.0 * FLT_EPSILON * bound_scale, "predeclared numerical criterion");
        stats.max_abs = std::max(stats.max_abs, error); stats.max_scaled = std::max(stats.max_scaled, error / bound_scale);
        if (std::memcmp(&original, &own, sizeof(float)) != 0) {
            // +0/-0 are numerically identical. The exact corpus uses numerical zero equality.
            if (original == 0.0f && own == 0.0f) ++stats.signed_zero_differences;
            else {
                bit_equal = false; ++stats.differing_components;
                if (!stats.has_counterexample) {
                    stats.has_counterexample = true; stats.example_a = inverse[i]; stats.example_b = pose->world[i];
                    stats.example_original = pose->composite[i]; stats.example_own = expected[i]; stats.example_component = j;
                }
            }
        }
        ++stats.components;
    }
    if (kind != 2) require(bit_equal, "exact dyadic corpus (signed zero ignored)");
    if (bit_equal) ++stats.exact_cases; else ++stats.rounded_cases;
    storage.check(); ++stats.matrix_cases; ++stats.corpus_cases[kind]; stats.bones += static_cast<std::uint64_t>(count);
}
void known_noncommuting(const Api& api) {
    // Independent hand-computable oracle: translating x by 1, then scaling x by 2,
    // produces translation 2 (the opposite composition order produces 1).
    BoneProjection bone{}; bone.inverse = matrix(0); bone.inverse.v[12] = 1.0f;
    SkeletonProjection skeleton{"noncommuting-oracle", 1, &bone, 0};
    Pose* pose = api.make(1); require(pose != nullptr, "known-case allocation");
    pose->world[0] = matrix(0); pose->world[0].v[0] = 2.0f;
    Matrix own{}; own_pose::composite(&bone.inverse, pose->world, &own, 0, 1);
    api.build(&skeleton, 0, 1, pose);
    Matrix correct = matrix(0); correct.v[0] = 2.0f; correct.v[12] = 2.0f;
    require(std::memcmp(&pose->composite[0], &correct, sizeof(Matrix)) == 0, "original against noncommuting oracle");
    require(std::memcmp(&own, &correct, sizeof(Matrix)) == 0, "own against noncommuting oracle");
    api.free_pose(pose);
}
void dump_matrix(std::ofstream& file, const Matrix& matrix_value) {
    file << '[';
    for (int i = 0; i < 16; ++i) { if (i) file << ','; file << matrix_value.v[i]; }
    file << ']';
}
int wmain(int argc, wchar_t** argv) {
    if (argc != 3) { std::fprintf(stderr, "usage: pose_contract_host <absolute-granny-dll> <report.json>\n"); return 2; }
    require(std::filesystem::path(argv[1]).is_absolute(), "absolute DLL path required");
    require(file_hash(argv[1]) == expected_hash, "DLL SHA-256 before load");
    HMODULE dll = LoadLibraryExW(argv[1], nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    require(dll != nullptr, "load verified original Granny in isolated host");
    wchar_t loaded[MAX_PATH]{};
    require(GetModuleFileNameW(dll, loaded, MAX_PATH) > 0, "loaded module path");
    require(std::filesystem::equivalent(argv[1], loaded), "loaded module identity");
    require(file_hash(loaded) == expected_hash, "loaded module file SHA-256");
    Api api(dll); Statistics stats;
    unsigned int control_before = 0; _controlfp_s(&control_before, 0, 0);
    unsigned int mxcsr_before = _mm_getcsr();
    known_noncommuting(api);
    for (int n : {0, 1, 2, 3, 15, 16, 17, 63, 64, 65, 217, 257, 1024, 4096}) layout(api, n, stats);
    for (int repeat = 0; repeat < 128; ++repeat) layout(api, 1 + static_cast<int>(random32() % 257), stats);
    for (int kind = 0; kind < 3; ++kind) {
        for (int n : {1, 2, 3, 16, 64, 257}) {
            differential(api, n, 0, 0, kind, stats);
            differential(api, n, n, 0, kind, stats);
            differential(api, n, 0, n, kind, stats);
            differential(api, n, n - 1, 1, kind, stats);
            if (n > 2) differential(api, n, 1, n - 2, kind, stats);
        }
        for (int repeat = 0; repeat < 512; ++repeat) {
            int n = 1 + static_cast<int>(random32() % 64);
            int first = static_cast<int>(random32() % static_cast<unsigned int>(n + 1));
            int count = static_cast<int>(random32() % static_cast<unsigned int>(n - first + 1));
            differential(api, n, first, count, kind, stats);
        }
    }
    require(stats.has_counterexample, "random corpus must expose non-bit-exact reproduction");
    unsigned int control_after = 0; _controlfp_s(&control_after, 0, 0);
    unsigned int mxcsr_after = _mm_getcsr();
    // Compare control modes, allowing IEEE exception status flags to be raised.
    require((control_before & 0xffffffe0u) == (control_after & 0xffffffe0u), "floating point control mode unchanged");
    require((mxcsr_before & ~0x3fu) == (mxcsr_after & ~0x3fu), "MXCSR control mode unchanged");
    std::ofstream report{std::filesystem::path(argv[2])}; report.precision(17);
    report << "{\n\"schema\":\"sh2perf.pose-contract-host.v1\",\n\"granny_sha256\":\"" << expected_hash << "\",\n"
           << "\"seed\":1397240358,\n\"compiler_msc_full_ver\":" << _MSC_FULL_VER
           << ",\n\"pointer_bits\":32,\n\"layout_cases\":" << stats.layout_cases << ",\n\"matrix_cases\":" << stats.matrix_cases
           << ",\n\"selected_bones\":" << stats.bones << ",\n\"compared_components\":" << stats.components
           << ",\n\"exact_cases_ignoring_signed_zero\":" << stats.exact_cases << ",\n\"rounded_cases\":" << stats.rounded_cases
           << ",\n\"different_nonzero_components\":" << stats.differing_components << ",\n\"max_abs_error\":" << stats.max_abs
           << ",\n\"signed_zero_differences\":" << stats.signed_zero_differences
           << ",\n\"noncommuting_oracle_cases\":1,\n\"corpus_cases_identity_dyadic_general\":[" << stats.corpus_cases[0] << ',' << stats.corpus_cases[1] << ',' << stats.corpus_cases[2] << ']'
           << ",\n\"max_error_divided_by_sum_abs_terms\":" << stats.max_scaled
           << ",\n\"criterion\":\"abs(original-own) <= 8*FLT_EPSILON*max(1,sum_abs_terms); exact dyadics ignore signed zero\",\n"
           << "\"fp_control_before\":" << control_before << ",\n\"fp_control_after\":" << control_after
           << ",\n\"mxcsr_before\":" << mxcsr_before << ",\n\"mxcsr_after\":" << mxcsr_after
           << ",\n\"counterexample\":{\"component\":" << stats.example_component << ",\"inverse_bind\":";
    dump_matrix(report, stats.example_a); report << ",\"world\":"; dump_matrix(report, stats.example_b);
    report << ",\"original\":"; dump_matrix(report, stats.example_original); report << ",\"own\":"; dump_matrix(report, stats.example_own);
    report << "},\n\"failures\":0\n}\n";
    require(report.good(), "report write"); report.close(); require(!report.fail(), "report close");
    FreeLibrary(dll);
    std::printf("Pose contract: %llu layout cases, %llu differential cases, %llu components; 0 failures.\n",
                stats.layout_cases, stats.matrix_cases, stats.components);
    return 0;
}
