# Minimal tvreg-style TV denoising in C++ (Linux)

Reproduces the core result of the **tvreg** package for the Gaussian (L2)
denoising case, using the **same model** and the **same algorithm** (split
Bregman) that tvreg uses.

## Model

    min_u   integral |grad u| dx   +   (lambda/2) integral (u - f)^2 dx

This is the `tvrestore lambda:<number>` denoising mode from the tvreg manual
(blur kernel K = identity, constant lambda). Convention matches the manual:
**smaller lambda = stronger denoising.**

## Files

- `pgm.h`            - tiny PGM image reader/writer (no dependencies)
- `make_testdata.cpp`- generates `clean.pgm` + `noisy.pgm` (reproducible)
- `tv_denoise.cpp`   - the split Bregman TV denoiser
- `psnr.cpp`         - reports MSE / PSNR between two images
- `CMakeLists.txt`, `run.sh`

## Build & run (Linux)

    cmake -B build
    cmake --build build

Then run either the script:

    ./run.sh

or manually:

    ./build/make_testdata                  # -> clean.pgm, noisy.pgm
    ./build/tv_denoise noisy.pgm denoised.pgm 20 80
    ./build/psnr clean.pgm denoised.pgm

`tv_denoise` arguments: `in.pgm out.pgm [lambda=20] [iters=80]`.

## Verified result (sigma=25 Gaussian noise, 256x256)

    noisy    vs clean:  PSNR = 20.6 dB
    lambda:5           PSNR = 33.2 dB   (strong denoising)
    lambda:20          PSNR = 29.9 dB
    lambda:80          PSNR = 22.7 dB   (weak denoising)

## Notes / how this maps to the full tvreg

- `gamma` in `tv_denoise.cpp` is tvreg's `gamma1` (default 5). It only affects
  convergence speed, not the minimizer.
- Boundaries use Neumann (symmetric) extension, as in tvreg.
- Not included (to keep it minimal): the blur kernel K (deconvolution), the
  inpainting domain D, the Laplace/Poisson noise models, spatially-varying
  lambda(x), color/vectorial TV, and Chan-Vese segmentation.
- Images are PGM here (dependency-free). tvreg uses BMP; convert with e.g.
  ImageMagick: `convert noisy.pgm noisy.bmp`.

## Debug vs Release build

The CMake project defaults to **Debug** and also supports **Release**:

    # Debug (default): -O0 -g3, AddressSanitizer + UBSan, active asserts,
    # and per-iteration energy/convergence diagnostics on stderr
    cmake -B build -DCMAKE_BUILD_TYPE=Debug
    cmake --build build
    ./build/tv_denoise noisy.pgm denoised.pgm 20 80

    # Release: -O2, no sanitizers, no diagnostics
    cmake -B build-release -DCMAKE_BUILD_TYPE=Release
    cmake --build build-release

Debug diagnostics look like:

    [debug] start  energy=10890.7
    [debug] iter 0  energy=6970.11  rel.change=0.359995
    [debug] iter 1  energy=6136.42  rel.change=0.119609
    ...

The energy is the discrete objective  sum|grad u| + (lambda/2) sum (u-f)^2;
it should decrease monotonically toward convergence.

To debug interactively:  gdb ./build/tv_denoise
Sanitizers abort with a diagnostic on any out-of-bounds access or UB.
