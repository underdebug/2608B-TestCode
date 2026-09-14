// psnr.cpp -- report MSE and PSNR (dB) between two PGM images.
// Build: g++ -O2 -std=c++11 psnr.cpp -o psnr
// Run:   ./psnr reference.pgm test.pgm
#include "pgm.h"
#include <cmath>
#include <iostream>

int main(int argc, char** argv) {
    if (argc < 3) { std::cerr << "usage: " << argv[0] << " a.pgm b.pgm\n"; return 1; }
    Image a, b;
    if (!readPGM(argv[1], a) || !readPGM(argv[2], b)) { std::cerr << "read error\n"; return 1; }
    if (a.W != b.W || a.H != b.H) { std::cerr << "size mismatch\n"; return 1; }
    const int N = a.W * a.H;
    double mse = 0.0;
    for (int i = 0; i < N; ++i) { double d = a.p[i] - b.p[i]; mse += d * d; }
    mse /= N;
    double psnr = (mse > 0) ? 10.0 * std::log10(255.0 * 255.0 / mse) : 99.0;
    std::cout << argv[1] << " vs " << argv[2]
              << ":  MSE=" << mse << "  PSNR=" << psnr << " dB\n";
    return 0;
}
