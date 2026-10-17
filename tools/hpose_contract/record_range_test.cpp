#include "record_range.h"
#include <cstdio>

namespace {
using hpose_contract::Status;
unsigned checks = 0;
unsigned failures = 0;
void check(bool condition, const char* description) {
    ++checks;
    if (!condition) {
        ++failures;
        std::fprintf(stderr, "FAIL: %s\n", description);
    }
}
struct Case {
    std::uint32_t begin, end, index;
    Status status;
    std::uint32_t count, address;
};
} // namespace

int main() {
    // Literal examples include byte-count/index boundaries and the signed /20
    // domain. No original DLL/EXE is loaded; no captured address is dereferenced.
    const Case cases[] = {
        {0x1000, 0x1000, 0, Status::index_out_of_range, 0, 0},
        {0x1000, 0x1014, 0, Status::selected, 1, 0x1000},
        {0x1000, 0x103c, 2, Status::selected, 3, 0x1028},
        {0x1000, 0x103c, 3, Status::index_out_of_range, 3, 0},
        {0x1000, 0x103c, 0xffffffff, Status::index_out_of_range, 3, 0},
        {0x2000, 0x1000, 0, Status::reversed_range, 0, 0},
        {0x1000, 0x1013, 0, Status::incomplete_record, 0, 0},
        {0x1000, 0x1015, 0, Status::incomplete_record, 0, 0},
        {0, 20, 0, Status::selected, 1, 0}, // arithmetic only, not a valid-pointer claim
        {0xffffffeb, 0xffffffff, 0, Status::selected, 1, 0xffffffeb},
        {0, 0x7ffffff8, 107374181, Status::selected, 107374182, 0x7fffffe4},
        {0, 0x7ffffff8, 107374182, Status::index_out_of_range, 107374182, 0},
        {0, 0x80000000, 0, Status::outside_signed_extent, 0, 0},
        {0, 0xfffffff0, 0, Status::outside_signed_extent, 0, 0},
    };
    for (const auto& item : cases) {
        const auto result = hpose_contract::select_record(item.begin, item.end, item.index);
        check(result.status == item.status && result.count == item.count && result.address == item.address,
              "literal range/index case");
    }
    // Exhaustive small valid ranges: address monotonicity, containment, count,
    // final-record/end equality, and rejection of the first invalid index.
    for (std::uint32_t count = 0; count <= 64; ++count) {
        const std::uint32_t end = 0x2000 + count * 20;
        std::uint32_t previous = 0;
        for (std::uint32_t index = 0; index < count; ++index) {
            const auto result = hpose_contract::select_record(0x2000, end, index);
            check(result.status == Status::selected && result.count == count, "valid selection/count");
            check(result.address >= 0x2000 && static_cast<std::uint64_t>(result.address) + 20 <= end,
                  "record within half-open range");
            check(index == 0 ? result.address == 0x2000 : result.address - previous == 20,
                  "consecutive records have stride 20");
            if (index + 1 == count) check(result.address + 20 == end, "last record ends at end");
            previous = result.address;
        }
        const auto invalid = hpose_contract::select_record(0x2000, end, count);
        check(invalid.status == Status::index_out_of_range && invalid.address == 0,
              "first excluded index is rejected");
    }
    std::printf("H-record own range model: %u checks, %u failures; no target memory access.\n", checks, failures);
    return failures ? 1 : 0;
}
