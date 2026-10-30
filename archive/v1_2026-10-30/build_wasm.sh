#!/bin/bash
# Compiles wasm/kernels.c -> extension/model.wasm (the CNN's hot loops, WebAssembly + SIMD).
# Needs emscripten (brew install emscripten). Only re-run after editing kernels.c.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
emcc "$HERE/wasm/kernels.c" -O3 -msimd128 --no-entry -s STANDALONE_WASM \
  -s INITIAL_MEMORY=33554432 -s ALLOW_MEMORY_GROWTH=0 \
  -s EXPORTED_FUNCTIONS=_conv3x3_relu,_maxpool2,_mean_height,_linear,_alloc,_release \
  -o "$HERE/extension/model.wasm"
echo "built $HERE/extension/model.wasm ($(du -h "$HERE/extension/model.wasm" | cut -f1))"
