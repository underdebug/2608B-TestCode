// main.cu -- TV denoising (moved here from tv_denoise.cpp)
// -----------------------------------------------------------------------------
// TV-regularized image denoising, using the SAME model and SAME algorithm as the
// tvreg package (Gaussian / L2 case, blur K = identity, constant lambda):
//
//     min_u   integral |grad u| dx   +   (lambda/2) integral (u - f)^2 dx
//
// Solved with the split Bregman method (Goldstein & Osher; the method tvreg
// uses). Introduce d ~ grad u and Bregman variable b, then alternate:
//
//   1. u-subproblem:  (lambda - gamma*Laplacian) u = lambda*f - gamma*div(d - b)
//                     -> one Gauss-Seidel sweep per outer iteration
//   2. d-subproblem:  d = shrink(grad u + b, 1/gamma)      (isotropic soft-threshold)
//   3. Bregman:       b = b + grad u - d
//
// gamma is tvreg's gamma1 constraint weight (default 5); it changes only the
// convergence speed, not the minimizer. Boundaries are Neumann (symmetric),
// matching tvreg's half-sample-symmetric extension.
//
// Run:   ./test   (edit IN_PATH / OUT_PATH / LAMBDA / ITERS below to change parameters)
// -----------------------------------------------------------------------------
#include "pgm.h"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <vector>

#ifdef TV_DEBUG
#include <cassert>
#include <cmath>
// Discrete objective:  sum |grad u| + (lambda/2) sum (u - f)^2
static double tv_energy(const std::vector<double>& u, const std::vector<double>& f,
                        int W, int H, double lambda) {
    double tv = 0.0, fid = 0.0;
    for (int y = 0; y < H; ++y)
    for (int x = 0; x < W; ++x) {
        double gx = (x + 1 < W) ? u[y * W + x + 1]     - u[y * W + x] : 0.0;
        double gy = (y + 1 < H) ? u[(y + 1) * W + x]   - u[y * W + x] : 0.0;
        tv += std::sqrt(gx * gx + gy * gy);
        double d = u[y * W + x] - f[y * W + x];
        fid += d * d;
    }
    return tv + 0.5 * lambda * fid;
}
#endif

int main() {
    const char*  IN_PATH  = "noisy.pgm";
    const char*  OUT_PATH = "denoised.pgm";
    const double lambda   = 20.0;   // smaller => stronger denoising
    const int    iters    = 80;
    const double gamma    = 5.0;    // tvreg default gamma1

    Image im;
    if (!readPGM(IN_PATH, im)) { std::cerr << "cannot read " << IN_PATH << "\n"; return 1; }
    const int W = im.W, H = im.H, N = W * H;

    std::vector<double> f(N), u(N);
    for (int i = 0; i < N; ++i) { f[i] = im.p[i] / 255.0; u[i] = f[i]; }   // work in [0,1]
    std::vector<double> dx(N, 0), dy(N, 0), bx(N, 0), by(N, 0);

    auto ID = [W](int x, int y) { return y * W + x; };
    const double denom = lambda + 4.0 * gamma;

#ifdef TV_DEBUG
    assert(N > 0 && "empty image");
    assert(lambda > 0.0 && "lambda must be positive");
    double Eprev = tv_energy(u, f, W, H, lambda);
    std::cerr << "[debug] start  energy=" << Eprev << "\n";
#endif

    for (int it = 0; it < iters; ++it) {
        // (1) u-subproblem: one in-place Gauss-Seidel sweep
        for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x) {
            double up = (x + 1 < W) ? u[ID(x + 1, y)] : u[ID(x, y)];
            double um = (x - 1 >= 0) ? u[ID(x - 1, y)] : u[ID(x, y)];
            double vp = (y + 1 < H) ? u[ID(x, y + 1)] : u[ID(x, y)];
            double vm = (y - 1 >= 0) ? u[ID(x, y - 1)] : u[ID(x, y)];

            double wx_here = dx[ID(x, y)] - bx[ID(x, y)];
            double wy_here = dy[ID(x, y)] - by[ID(x, y)];
            double wx_left = (x - 1 >= 0) ? dx[ID(x - 1, y)] - bx[ID(x - 1, y)] : 0.0;
            double wy_down = (y - 1 >= 0) ? dy[ID(x, y - 1)] - by[ID(x, y - 1)] : 0.0;
            double divw = (wx_here - wx_left) + (wy_here - wy_down);   // div(d - b)

            u[ID(x, y)] = (lambda * f[ID(x, y)] + gamma * (up + um + vp + vm)
                           - gamma * divw) / denom;
        }
        // (2) d-subproblem (isotropic shrinkage) + (3) Bregman update, fused
        for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x) {
            double gx = (x + 1 < W) ? u[ID(x + 1, y)] - u[ID(x, y)] : 0.0;  // forward diff
            double gy = (y + 1 < H) ? u[ID(x, y + 1)] - u[ID(x, y)] : 0.0;
            double ax = gx + bx[ID(x, y)];        // = grad u + b_old
            double ay = gy + by[ID(x, y)];
            double s  = std::sqrt(ax * ax + ay * ay);
            double sh = (s > 1e-12) ? std::max(s - 1.0 / gamma, 0.0) / s : 0.0;
            dx[ID(x, y)] = sh * ax;
            dy[ID(x, y)] = sh * ay;
            bx[ID(x, y)] = ax - dx[ID(x, y)];     // b_new = b_old + grad u - d
            by[ID(x, y)] = ay - dy[ID(x, y)];
        }
#ifdef TV_DEBUG
        double E = tv_energy(u, f, W, H, lambda);
        double rel = std::fabs(E - Eprev) / (std::fabs(Eprev) + 1e-12);
        std::cerr << "[debug] iter " << it << "  energy=" << E
                  << "  rel.change=" << rel << "\n";
        Eprev = E;
#endif
    }

    for (int i = 0; i < N; ++i) im.p[i] = u[i] * 255.0;
    if (!writePGM(OUT_PATH, im)) { std::cerr << "cannot write " << OUT_PATH << "\n"; return 1; }
    std::cout << "denoised " << IN_PATH << " -> " << OUT_PATH
              << "  (lambda=" << lambda << ", gamma=" << gamma << ", iters=" << iters << ")\n";
    return 0;
}
