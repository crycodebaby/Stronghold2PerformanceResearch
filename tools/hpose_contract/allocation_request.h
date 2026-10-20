#pragma once
#include "record_range.h"

// Own numerical model of the verified 20-byte-record allocation request.
// This does not allocate, call the CRT, measure heap overhead or prove success.
namespace hpose_contract {
inline constexpr std::uint32_t max_requested_records = 0x0ccccccc;
static_assert(max_requested_records == (std::numeric_limits<std::uint32_t>::max)() / record_stride);

enum class RequestStatus { no_allocation, byte_request, exceeds_native_limit };
struct AllocationRequest {
    RequestStatus status;
    std::uint32_t bytes;
};

// The original can throw on excessive requests. Our status is an explicit own
// rejection contract, not an emulation of exception unwinding or a null result.
[[nodiscard]] constexpr AllocationRequest allocation_request(std::uint32_t records) noexcept {
    if (records == 0) return {RequestStatus::no_allocation, 0};
    if (records > max_requested_records) return {RequestStatus::exceeds_native_limit, 0};
    const auto bytes = static_cast<std::uint64_t>(records) * record_stride;
    return {RequestStatus::byte_request, static_cast<std::uint32_t>(bytes)};
}
} // namespace hpose_contract
