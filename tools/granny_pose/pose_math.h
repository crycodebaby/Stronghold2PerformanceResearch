#pragma once
#include <cstddef>

// Independent affine matrix implementation. Row-vector convention; row 3 is
// translation. Disjoint, finite, canonical affine inputs only (last column 0,0,0,1).
// The caller owns all arrays. No allocation, global state or original-library calls.
namespace own_pose {
struct Matrix { float v[16]; };
void composite(const Matrix* inverse_bind, const Matrix* world, Matrix* output,
               std::size_t first, std::size_t count);
}
