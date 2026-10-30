// Hot loops of the captcha CNN, compiled to WebAssembly with SIMD (see build_wasm.sh).
// model.js calls these; all tensors are float32 planes in the module's own memory.
#include <stdlib.h>
#include <string.h>
#include <wasm_simd128.h>

#define EXPORT __attribute__((visibility("default")))

// 3x3 convolution, padding 1, then ReLU.  in: c planes h*w;  weight: outC*c*9;  out: outC planes h*w
EXPORT void conv3x3_relu(const float *in, int c, int h, int w,
                         const float *weight, const float *bias, int outC, float *out) {
    int wr = (w + 15) & ~15;   // row length rounded up to the 16-wide inner block
    int ws = wr + 4;           // padded row stride, room for the block to read past the right edge
    int hs = h + 2;
    float *pad = calloc((size_t)c * hs * ws, sizeof(float));   // zero border = padding 1
    float *row = malloc(sizeof(float) * wr);
    for (int i = 0; i < c; i++)
        for (int y = 0; y < h; y++)
            memcpy(pad + (size_t)i * hs * ws + (y + 1) * ws + 1, in + (size_t)i * h * w + y * w, sizeof(float) * w);

    for (int o = 0; o < outC; o++) {
        const float *ko = weight + (size_t)o * c * 9;
        float *dst = out + (size_t)o * h * w;
        for (int y = 0; y < h; y++) {
            for (int x0 = 0; x0 < wr; x0 += 16) {
                v128_t a0 = wasm_f32x4_splat(bias[o]), a1 = a0, a2 = a0, a3 = a0;
                for (int i = 0; i < c; i++) {
                    const float *base = pad + (size_t)i * hs * ws + y * ws + x0;
                    const float *k = ko + i * 9;
                    for (int ky = 0; ky < 3; ky++) {
                        const float *r = base + ky * ws;
                        for (int kx = 0; kx < 3; kx++) {
                            v128_t kv = wasm_f32x4_splat(k[ky * 3 + kx]);
                            const float *p = r + kx;
                            a0 = wasm_f32x4_add(a0, wasm_f32x4_mul(kv, wasm_v128_load(p)));
                            a1 = wasm_f32x4_add(a1, wasm_f32x4_mul(kv, wasm_v128_load(p + 4)));
                            a2 = wasm_f32x4_add(a2, wasm_f32x4_mul(kv, wasm_v128_load(p + 8)));
                            a3 = wasm_f32x4_add(a3, wasm_f32x4_mul(kv, wasm_v128_load(p + 12)));
                        }
                    }
                }
                wasm_v128_store(row + x0, a0);
                wasm_v128_store(row + x0 + 4, a1);
                wasm_v128_store(row + x0 + 8, a2);
                wasm_v128_store(row + x0 + 12, a3);
            }
            for (int x = 0; x < w; x++) dst[y * w + x] = row[x] > 0 ? row[x] : 0;
        }
    }
    free(row);
    free(pad);
}

// 2x2 max-pool, stride 2 (odd edges dropped, like PyTorch).  out: c planes (h/2)*(w/2)
EXPORT void maxpool2(const float *in, int c, int h, int w, float *out) {
    int ho = h / 2, wo = w / 2;
    for (int ch = 0; ch < c; ch++)
        for (int r = 0; r < ho; r++)
            for (int col = 0; col < wo; col++) {
                const float *p = in + (size_t)ch * h * w + 2 * r * w + 2 * col;
                float m = p[0];
                if (p[1] > m) m = p[1];
                if (p[w] > m) m = p[w];
                if (p[w + 1] > m) m = p[w + 1];
                out[((size_t)ch * ho + r) * wo + col] = m;
            }
}

// average over height: c planes h*w -> c*w, flattened channel-major like PyTorch's Flatten
EXPORT void mean_height(const float *in, int c, int h, int w, float *out) {
    for (int ch = 0; ch < c; ch++)
        for (int col = 0; col < w; col++) {
            float s = 0;
            for (int r = 0; r < h; r++) s += in[((size_t)ch * h + r) * w + col];
            out[ch * w + col] = s / h;
        }
}

// out[n] = bias + weight[n x m] . in[m], optional ReLU
EXPORT void linear(const float *in, int m, const float *weight, const float *bias, int n, int relu, float *out) {
    for (int o = 0; o < n; o++) {
        const float *row = weight + (size_t)o * m;
        v128_t acc = wasm_f32x4_splat(0);
        int i = 0;
        for (; i + 4 <= m; i += 4)
            acc = wasm_f32x4_add(acc, wasm_f32x4_mul(wasm_v128_load(row + i), wasm_v128_load(in + i)));
        float s = bias[o] + wasm_f32x4_extract_lane(acc, 0) + wasm_f32x4_extract_lane(acc, 1)
                          + wasm_f32x4_extract_lane(acc, 2) + wasm_f32x4_extract_lane(acc, 3);
        for (; i < m; i++) s += row[i] * in[i];
        out[o] = relu && s < 0 ? 0 : s;
    }
}

EXPORT void *alloc(int bytes) { return malloc(bytes); }
EXPORT void release(void *p) { free(p); }
