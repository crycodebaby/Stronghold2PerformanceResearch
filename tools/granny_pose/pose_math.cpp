#include "pose_math.h"

namespace own_pose {
void composite(const Matrix* inverse_bind, const Matrix* world, Matrix* output,
               std::size_t first, std::size_t count) {
    // Express the affine operation from its mathematical contract, with ordinary
    // float32 products/sums. Deliberately no transcription of x87 evaluation order.
    for (std::size_t i = first; i < first + count; ++i) {
        const Matrix& a = inverse_bind[i];
        const Matrix& b = world[i];
        Matrix c{};
        for (int row = 0; row < 4; ++row) {
            for (int col = 0; col < 3; ++col) {
                float sum = 0.0f;
                for (int k = 0; k < 3; ++k) sum += a.v[row * 4 + k] * b.v[k * 4 + col];
                if (row == 3) sum += b.v[12 + col];
                c.v[row * 4 + col] = sum;
            }
        }
        c.v[15] = 1.0f;
        output[i] = c;
    }
}
}
