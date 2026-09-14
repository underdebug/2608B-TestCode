#!/bin/sh
# Build everything, generate test data, denoise, and report quality.
set -e

cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build

echo
echo "==== generating test data ===="
./make_testdata

echo
echo "==== running TV denoising (split Bregman) ===="
./tv_denoise noisy.pgm denoised.pgm 20 80

echo
echo "==== quality (PSNR vs clean ground truth) ===="
./psnr clean.pgm noisy.pgm
./psnr clean.pgm denoised.pgm

echo
echo "Done. Outputs: clean.pgm, noisy.pgm, denoised.pgm"
echo "Tip: smaller lambda = stronger denoising. Try:  ./tv_denoise noisy.pgm out.pgm 10 120"
