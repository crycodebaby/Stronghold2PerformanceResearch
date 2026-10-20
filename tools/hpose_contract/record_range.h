#pragma once
#include <cstddef>
#include <cstdint>
#include <limits>
#include <type_traits>

// Own mathematical model of the verified direct in-range H-record selection.
// Address values are identifiers only. This code never reads target memory and
// does not establish allocation, ownership, alignment, or a live object.
namespace hpose_contract {
inline constexpr std::uint32_t record_stride = 20;
static_assert(sizeof(std::uint32_t) == 4);

// Field projection for our own copied data, not an overlay or owning engine type.
// Constructor stores prove these offsets; semantic role of field +0x10 is open.
struct RecordProjection32 {
    std::uint32_t instance_address;
    std::uint32_t world_pose_address;
    std::uint32_t local_pose_address;
    std::uint32_t resource_reference_address;
    std::uint32_t unknown_10;
};
static_assert(std::is_standard_layout_v<RecordProjection32>);
static_assert(std::is_trivially_copyable_v<RecordProjection32>);
static_assert(sizeof(RecordProjection32) == record_stride);
static_assert(offsetof(RecordProjection32, instance_address) == 0);
static_assert(offsetof(RecordProjection32, world_pose_address) == 4);
static_assert(offsetof(RecordProjection32, local_pose_address) == 8);
static_assert(offsetof(RecordProjection32, resource_reference_address) == 12);
static_assert(offsetof(RecordProjection32, unknown_10) == 16);

enum class Status {
    selected,
    reversed_range,
    outside_signed_extent,
    incomplete_record,
    index_out_of_range
};

struct Selection {
    Status status;
    std::uint32_t count;
    std::uint32_t address;
};

// Own rejection behavior is deliberately stronger than original machine code.
// In particular, the game's geometric fallback for an out-of-range index is
// outside this model, as are wrapped/signed-negative range differences.
[[nodiscard]] constexpr Selection select_record(std::uint32_t begin, std::uint32_t end,
                                                std::uint32_t index) noexcept {
    if (end < begin) return {Status::reversed_range, 0, 0};
    const auto bytes = static_cast<std::uint64_t>(end) - begin;
    if (bytes > static_cast<std::uint64_t>((std::numeric_limits<std::int32_t>::max)()))
        return {Status::outside_signed_extent, 0, 0};
    if (bytes % record_stride != 0) return {Status::incomplete_record, 0, 0};
    const auto count = static_cast<std::uint32_t>(bytes / record_stride);
    if (index >= count) return {Status::index_out_of_range, count, 0};
    // The checked domain guarantees address + record_stride <= end <= UINT32_MAX.
    const auto address = static_cast<std::uint64_t>(begin) + static_cast<std::uint64_t>(index) * record_stride;
    return {Status::selected, count, static_cast<std::uint32_t>(address)};
}
} // namespace hpose_contract
