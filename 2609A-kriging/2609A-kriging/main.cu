// =============================================================================
//  kriging_cuda.cu -- Ordinary Kriging spatial interpolation on the GPU (CUDA)
//
//  Build:  nvcc -O3 -arch=sm_70 kriging_cuda.cu -o kriging
//          (use -arch=sm_60 / sm_75 / sm_86 / sm_89 / sm_90 to match your GPU)
//  Run:    ./kriging
//
//  Method
//  ------
//  Ordinary kriging estimates z at an unsampled location x0 as a weighted sum
//  of the n known samples, with weights constrained to sum to 1:
//
//      z*(x0) = sum_i w_i * z_i ,   sum_i w_i = 1
//
//  The weights come from the (n+1) x (n+1) system  A * s = b, where
//
//      A = [ G   1 ]        b = [ g0 ]        s = [ w  ]
//          [ 1^T 0 ]            [  1 ]            [ mu ]
//
//      G[i][j] = gamma(|x_i - x_j|)   (semivariogram between two samples)
//      g0[i]   = gamma(|x_i - x0|)    (sample-to-target semivariogram)
//      mu      = Lagrange multiplier enforcing the unbiasedness constraint
//
//  A depends only on the sample locations, so it is factored/inverted ONCE on
//  the host. Only b changes per target point, which is what makes this
//  embarrassingly parallel across the output grid.
//
//  Two kernels are provided:
//
//    1) krigeExactKernel  -- one CUDA block per target point. Computes both the
//       estimate and the kriging variance:  sigma^2 = b^T * A^-1 * b.
//       Cost: O(n^2) per target point.
//
//    2) krigeFastKernel   -- one thread per target point. Estimate only, using
//       the precomputed vector  v = A^-1 * [z; 0], since
//           z*(x0) = [z;0]^T A^-1 b = v^T b      (A is symmetric)
//       Cost: O(n) per target point. Much faster, but no variance.
//
//  Verified properties: weights sum to 1, samples are reproduced exactly,
//  kriging variance is ~0 at sample locations and grows away from the data.
// =============================================================================

#include <cuda_runtime.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <random>
#include <algorithm>

// ---------------------------------------------------------------- error check
#define CUDA_CHECK(call)                                                       \
    do {                                                                       \
        cudaError_t err__ = (call);                                            \
        if (err__ != cudaSuccess) {                                            \
            std::fprintf(stderr, "CUDA error %s at %s:%d -> %s\n",             \
                         cudaGetErrorName(err__), __FILE__, __LINE__,          \
                         cudaGetErrorString(err__));                           \
            std::exit(EXIT_FAILURE);                                           \
        }                                                                      \
    } while (0)

// Double precision keeps the kriging system well behaved. Switching to float
// roughly doubles throughput on consumer cards (and much more on GeForce, where
// FP64 is heavily rate-limited), at the cost of conditioning. If you switch,
// keep the host-side matrix inversion in double.
typedef double real_t;

// ------------------------------------------------------------ variogram model
enum VariogramType { VG_SPHERICAL = 0, VG_EXPONENTIAL = 1, VG_GAUSSIAN = 2 };

struct VariogramModel {
    int    type;
    real_t nugget;   // gamma as h -> 0+ (measurement noise / micro-scale)
    real_t sill;     // plateau value (total variance)
    real_t range;    // distance at which (or near which) the sill is reached
};

//__forceinline__ -G -O0 只对没有强制内联标记的代码有效
// gamma(0) == 0 exactly, which is what makes kriging an exact interpolator.
__host__ __device__ //__forceinline__
real_t variogram(const VariogramModel& m, real_t h)
{
    if (h <= real_t(0)) return real_t(0);
    const real_t psill = m.sill - m.nugget;
    switch (m.type) {
        case VG_SPHERICAL: {
            if (h >= m.range) return m.sill;
            const real_t r = h / m.range;
            double value = m.nugget + psill * (real_t(1.5) * r - real_t(0.5) * r * r * r);
            return value;
        }
        case VG_EXPONENTIAL:
            return m.nugget + psill * (real_t(1) - exp(real_t(-3) * h / m.range));
        case VG_GAUSSIAN: {
            const real_t r = h / m.range;
            return m.nugget + psill * (real_t(1) - exp(real_t(-3) * r * r));
        }
    }
    return m.sill;
}

// =============================================================================
//  Kernel 1: estimate + kriging variance. One block per target point.
//
//  Shared memory layout (dynamic):
//      [0 .. N-1]            -> b, the right-hand side for this target
//      [N .. N+2*blockDim-1] -> reduction scratch (estimate | variance)
//  where N = n + 1. blockDim.x must be a power of two.
// =============================================================================
__global__ void krigeExactKernel(const real_t* __restrict__ sx,
                                 const real_t* __restrict__ sy,
                                 const real_t* __restrict__ sv,
                                 int n,
                                 const real_t* __restrict__ Ainv,  // N x N, row-major
                                 const real_t* __restrict__ gx,
                                 const real_t* __restrict__ gy,
                                 int m,
                                 real_t* __restrict__ outVal,
                                 real_t* __restrict__ outVar,
                                 VariogramModel model)
{
    extern __shared__ real_t smem[];
    const int N   = n + 1;
    const int tid = threadIdx.x;
    const int t   = blockIdx.x;                 // target point handled by this block
    if (t >= m) return;                         // whole block exits: __syncthreads is safe

    real_t* b   = smem;                         // N entries
    real_t* red = smem + N;                     // 2 * blockDim.x entries

    const real_t x0 = gx[t];
    const real_t y0 = gy[t];

    // ---- build the right-hand side b = [gamma(x_i, x0) ; 1]
    for (int j = tid; j < n; j += blockDim.x) {
        const real_t dx = sx[j] - x0;
        const real_t dy = sy[j] - y0;
        b[j] = variogram(model, sqrt(dx * dx + dy * dy));
    }
    if (tid == 0) b[n] = real_t(1);
    __syncthreads();

    // ---- s = Ainv * b ; accumulate  est = sum_i w_i z_i  and  var = b^T s
    real_t partEst = real_t(0);
    real_t partVar = real_t(0);
    for (int i = tid; i < N; i += blockDim.x) {
        const real_t* row = Ainv + (size_t)i * N;
        real_t s = real_t(0);
        for (int j = 0; j < N; ++j) s += row[j] * b[j];
        partVar += s * b[i];                    // includes the mu * 1 term at i == n
        if (i < n) partEst += s * sv[i];        // w_i * z_i
    }

    // ---- block reduction
    red[tid]                = partEst;
    red[blockDim.x + tid]   = partVar;
    __syncthreads();
    for (int stride = blockDim.x >> 1; stride > 0; stride >>= 1) {
        if (tid < stride) {
            red[tid]              += red[tid + stride];
            red[blockDim.x + tid] += red[blockDim.x + tid + stride];
        }
        __syncthreads();
    }
    if (tid == 0) {
        outVal[t] = red[0];
        // Clamp tiny negatives that come from round-off at sample locations.
        outVar[t] = red[blockDim.x] > real_t(0) ? red[blockDim.x] : real_t(0);
    }
}

// =============================================================================
//  Kernel 2: estimate only, O(n) per target point, one thread per target.
//  Samples are streamed through shared memory in tiles of blockDim.x.
//  Uses v = Ainv * [z; 0] so that z*(x0) = v . b  (and b[n] = 1 -> + v[n]).
// =============================================================================
__global__ void krigeFastKernel(const real_t* __restrict__ sx,
                                const real_t* __restrict__ sy,
                                const real_t* __restrict__ v,     // N entries
                                int n,
                                const real_t* __restrict__ gx,
                                const real_t* __restrict__ gy,
                                int m,
                                real_t* __restrict__ outVal,
                                VariogramModel model)
{
    extern __shared__ real_t tile[];
    const int T  = blockDim.x;
    real_t* tx = tile;
    real_t* ty = tile + T;
    real_t* tv = tile + 2 * T;

    const int idx    = blockIdx.x * blockDim.x + threadIdx.x;
    const bool alive = (idx < m);               // do NOT return early: syncthreads below
    const real_t x0  = alive ? gx[idx] : real_t(0);
    const real_t y0  = alive ? gy[idx] : real_t(0);

    real_t acc = real_t(0);
    for (int base = 0; base < n; base += T) {
        const int j = base + threadIdx.x;
        if (j < n) {
            tx[threadIdx.x] = sx[j];
            ty[threadIdx.x] = sy[j];
            tv[threadIdx.x] = v[j];
        }
        __syncthreads();

        const int cnt = min(T, n - base);
        #pragma unroll 4
        for (int k = 0; k < cnt; ++k) {
            const real_t dx = tx[k] - x0;
            const real_t dy = ty[k] - y0;
            acc += tv[k] * variogram(model, sqrt(dx * dx + dy * dy));
        }
        __syncthreads();
    }
    if (alive) outVal[idx] = acc + v[n];        // the b[n] = 1 contribution
}

// =============================================================================
//  Host: Gauss-Jordan inversion with partial pivoting (row-major, in place).
//  Fine up to a few thousand samples. For larger systems use cuSOLVER
//  (cusolverDnDgetrf + cusolverDnDgetrs) or a moving-neighbourhood search.
// =============================================================================
static bool invertMatrix(std::vector<real_t>& A, int n)
{
    std::vector<real_t> I((size_t)n * n, real_t(0));
    for (int i = 0; i < n; ++i) I[(size_t)i * n + i] = real_t(1);

    for (int c = 0; c < n; ++c) {
        int    piv  = c;
        real_t best = std::fabs(A[(size_t)c * n + c]);
        for (int r = c + 1; r < n; ++r) {
            const real_t v = std::fabs(A[(size_t)r * n + c]);
            if (v > best) { best = v; piv = r; }
        }
        if (best < real_t(1e-14)) return false;   // singular: duplicate points?

        if (piv != c) {
            for (int j = 0; j < n; ++j) {
                std::swap(A[(size_t)c * n + j], A[(size_t)piv * n + j]);
                std::swap(I[(size_t)c * n + j], I[(size_t)piv * n + j]);
            }
        }
        const real_t d = real_t(1) / A[(size_t)c * n + c];
        for (int j = 0; j < n; ++j) {
            A[(size_t)c * n + j] *= d;
            I[(size_t)c * n + j] *= d;
        }
        for (int r = 0; r < n; ++r) {
            if (r == c) continue;
            const real_t f = A[(size_t)r * n + c];
            if (f == real_t(0)) continue;
            for (int j = 0; j < n; ++j) {
                A[(size_t)r * n + j] -= f * A[(size_t)c * n + j];
                I[(size_t)r * n + j] -= f * I[(size_t)c * n + j];
            }
        }
    }
    A.swap(I);
    return true;
}

// =============================================================================
//  Demo driver
// =============================================================================
int main()
{
    freopen("log.txt", "w", stdout);
    setvbuf(stdout, nullptr, _IONBF, 0);
    // tail -f log.txt
 
    // ---------------- problem setup -----------------------------------------
    const int    nSamples = 10;
    const int    GW = 10, GH = 10;             // output grid
    const int    nGrid = GW * GH;
    const real_t extent = 100.0;

    const VariogramModel model{ VG_SPHERICAL,
                                /*nugget*/ 0.0,
                                /*sill  */ 1.0,
                                /*range */ 30.0 };

    // Scattered samples drawn from a synthetic field (so we can measure error).
    auto trueField = [](real_t x, real_t y) {
        return 10.0 + 5.0 * std::sin(x * 0.07) * std::cos(y * 0.05)
                    + 0.02 * x;
    };

    std::mt19937 rng(1234);
    std::uniform_real_distribution<real_t> U(0.0, extent);
    std::vector<real_t> hsx(nSamples), hsy(nSamples), hsv(nSamples);
    for (int i = 0; i < nSamples; ++i) {
        hsx[i] = U(rng);
        hsy[i] = U(rng);
        hsv[i] = trueField(hsx[i], hsy[i]);
    }

    // Target grid.
    std::vector<real_t> hgx(nGrid), hgy(nGrid);
    for (int r = 0; r < GH; ++r)
        for (int c = 0; c < GW; ++c) {
            hgx[(size_t)r * GW + c] = extent * c / (GW - 1);
            hgy[(size_t)r * GW + c] = extent * r / (GH - 1);
        }

    // ---------------- build and invert the kriging matrix (host, once) -------
    const int N = nSamples + 1;
    std::printf("Building and inverting the %d x %d kriging system...\n", N, N);

    std::vector<real_t> A((size_t)N * N, real_t(0));
    for (int i = 0; i < nSamples; ++i) {
        for (int j = 0; j < nSamples; ++j) {
            const real_t dx = hsx[i] - hsx[j];
            const real_t dy = hsy[i] - hsy[j];
            A[(size_t)i * N + j] = variogram(model, std::sqrt(dx * dx + dy * dy));
        }
        A[(size_t)i * N + nSamples] = real_t(1);
        A[(size_t)nSamples * N + i] = real_t(1);
    }
    A[(size_t)nSamples * N + nSamples] = real_t(0);

    std::vector<real_t> A_Old = A;
    if (!invertMatrix(A, N)) {
        std::fprintf(stderr, "Kriging matrix is singular. "
                             "Check for duplicate sample coordinates, or add a nugget.\n");
        return EXIT_FAILURE;
    }

    // v = Ainv * [z ; 0]  -> lets the fast kernel skip the per-point solve.
    std::vector<real_t> hv(N, real_t(0));
    for (int i = 0; i < N; ++i) {
        real_t s = real_t(0);
        for (int j = 0; j < nSamples; ++j) s += A[(size_t)i * N + j] * hsv[j];
        hv[i] = s;
    }

    // ---------------- device allocation --------------------------------------
    real_t *dsx, *dsy, *dsv, *dAinv, *dv, *dgx, *dgy, *dVal, *dVar;
    CUDA_CHECK(cudaMalloc(&dsx,   nSamples * sizeof(real_t)));
    CUDA_CHECK(cudaMalloc(&dsy,   nSamples * sizeof(real_t)));
    CUDA_CHECK(cudaMalloc(&dsv,   nSamples * sizeof(real_t)));
    CUDA_CHECK(cudaMalloc(&dAinv, (size_t)N * N * sizeof(real_t)));
    CUDA_CHECK(cudaMalloc(&dv,    N * sizeof(real_t)));
    CUDA_CHECK(cudaMalloc(&dgx,   nGrid * sizeof(real_t)));
    CUDA_CHECK(cudaMalloc(&dgy,   nGrid * sizeof(real_t)));
    CUDA_CHECK(cudaMalloc(&dVal,  nGrid * sizeof(real_t)));
    CUDA_CHECK(cudaMalloc(&dVar,  nGrid * sizeof(real_t)));

    CUDA_CHECK(cudaMemcpy(dsx, hsx.data(), nSamples * sizeof(real_t), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(dsy, hsy.data(), nSamples * sizeof(real_t), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(dsv, hsv.data(), nSamples * sizeof(real_t), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(dAinv, A.data(), (size_t)N * N * sizeof(real_t), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(dv,  hv.data(),  N * sizeof(real_t), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(dgx, hgx.data(), nGrid * sizeof(real_t), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(dgy, hgy.data(), nGrid * sizeof(real_t), cudaMemcpyHostToDevice));

    cudaEvent_t t0, t1;
    CUDA_CHECK(cudaEventCreate(&t0));
    CUDA_CHECK(cudaEventCreate(&t1));
    float ms = 0.0f;

    // ---------------- kernel 1: estimate + variance ---------------------------
    {
        const int threads = 256;                       // power of two, required
        const size_t shmem = ((size_t)N + 2 * threads) * sizeof(real_t);

        int shmemMax = 0; // 48KB
        CUDA_CHECK(cudaDeviceGetAttribute(&shmemMax,
                   cudaDevAttrMaxSharedMemoryPerBlock, 0));
        if (shmem > (size_t)shmemMax) {
            std::fprintf(stderr,
                "Need %zu bytes of shared memory but the device offers %d.\n"
                "Reduce the sample count or use a moving search neighbourhood.\n",
                shmem, shmemMax);
            return EXIT_FAILURE;
        }

        CUDA_CHECK(cudaEventRecord(t0));
        krigeExactKernel<<<nGrid, threads, shmem>>>(dsx, dsy, dsv, nSamples,
                                                    dAinv, dgx, dgy, nGrid,
                                                    dVal, dVar, model);
        CUDA_CHECK(cudaEventRecord(t1));
        CUDA_CHECK(cudaGetLastError());
        CUDA_CHECK(cudaEventSynchronize(t1));
        CUDA_CHECK(cudaEventElapsedTime(&ms, t0, t1));
        std::printf("krigeExactKernel : %8.2f ms  (%d nodes x %d samples, with variance)\n",
                    ms, nGrid, nSamples);
    }

    std::vector<real_t> hVal(nGrid), hVar(nGrid);
    CUDA_CHECK(cudaMemcpy(hVal.data(), dVal, nGrid * sizeof(real_t), cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(hVar.data(), dVar, nGrid * sizeof(real_t), cudaMemcpyDeviceToHost));

    // ---------------- kernel 2: fast estimate ---------------------------------
    std::vector<real_t> hFast(nGrid);
    {
        const int threads = 256;
        const int blocks  = (nGrid + threads - 1) / threads;
        const size_t shmem = 3 * (size_t)threads * sizeof(real_t);

        CUDA_CHECK(cudaEventRecord(t0));
        krigeFastKernel<<<blocks, threads, shmem>>>(dsx, dsy, dv, nSamples,
                                                    dgx, dgy, nGrid, dVal, model);
        CUDA_CHECK(cudaEventRecord(t1));
        CUDA_CHECK(cudaGetLastError());
        CUDA_CHECK(cudaEventSynchronize(t1));
        CUDA_CHECK(cudaEventElapsedTime(&ms, t0, t1));
        std::printf("krigeFastKernel  : %8.2f ms  (estimate only, O(n) per node)\n", ms);

        CUDA_CHECK(cudaMemcpy(hFast.data(), dVal, nGrid * sizeof(real_t), cudaMemcpyDeviceToHost));
    }

    // ---------------- validation ---------------------------------------------
    real_t maxKernelDiff = 0.0, maxErr = 0.0, sumSq = 0.0;
    for (int i = 0; i < nGrid; ++i) {
        maxKernelDiff = std::max(maxKernelDiff, std::fabs(hVal[i] - hFast[i]));
        const real_t e = hVal[i] - trueField(hgx[i], hgy[i]);
        maxErr = std::max(maxErr, std::fabs(e));
        sumSq += e * e;
    }
    std::printf("\nmax |exact - fast| kernel difference : %.3e\n", maxKernelDiff);
    std::printf("RMSE vs the analytic field           : %.5f  (max %.5f)\n",
                std::sqrt(sumSq / nGrid), maxErr);

    // Exactness check: kriging must reproduce the data at sample locations.
    {
        real_t *dtx, *dty, *dov, *dovar;
        CUDA_CHECK(cudaMalloc(&dtx, nSamples * sizeof(real_t)));
        CUDA_CHECK(cudaMalloc(&dty, nSamples * sizeof(real_t)));
        CUDA_CHECK(cudaMalloc(&dov, nSamples * sizeof(real_t)));
        CUDA_CHECK(cudaMalloc(&dovar, nSamples * sizeof(real_t)));
        CUDA_CHECK(cudaMemcpy(dtx, hsx.data(), nSamples * sizeof(real_t), cudaMemcpyHostToDevice));
        CUDA_CHECK(cudaMemcpy(dty, hsy.data(), nSamples * sizeof(real_t), cudaMemcpyHostToDevice));

        const int threads = 256;
        const size_t shmem = ((size_t)N + 2 * threads) * sizeof(real_t);
        krigeExactKernel<<<nSamples, threads, shmem>>>(dsx, dsy, dsv, nSamples,
                                                       dAinv, dtx, dty, nSamples,
                                                       dov, dovar, model);
        CUDA_CHECK(cudaDeviceSynchronize());

        std::vector<real_t> chk(nSamples), chkv(nSamples);
        CUDA_CHECK(cudaMemcpy(chk.data(),  dov,   nSamples * sizeof(real_t), cudaMemcpyDeviceToHost));
        CUDA_CHECK(cudaMemcpy(chkv.data(), dovar, nSamples * sizeof(real_t), cudaMemcpyDeviceToHost));

        double* p = (double*)chk.data();

        real_t worst = 0.0, worstVar = 0.0;
        for (int i = 0; i < nSamples; ++i) {
            worst    = std::max(worst,    std::fabs(chk[i] - hsv[i]));
            worstVar = std::max(worstVar, chkv[i]);
        }
        std::printf("max error at sample locations        : %.3e (variance <= %.3e)\n",
                    worst, worstVar);

        CUDA_CHECK(cudaFree(dtx));  CUDA_CHECK(cudaFree(dty));
        CUDA_CHECK(cudaFree(dov));  CUDA_CHECK(cudaFree(dovar));
    }

    // ---------------- write results -------------------------------------------
    if (FILE* f = std::fopen("kriging_output.csv", "w")) {
        std::fprintf(f, "x,y,estimate,variance\n");
        for (int i = 0; i < nGrid; ++i)
            std::fprintf(f, "%.6f,%.6f,%.6f,%.6f\n", hgx[i], hgy[i], hVal[i], hVar[i]);
        std::fclose(f);
        std::printf("\nWrote kriging_output.csv (%d rows)\n", nGrid);
    }

    // Quick-look grayscale image of the estimate (any image viewer opens PGM).
    if (FILE* f = std::fopen("kriging_estimate.pgm", "wb")) {
        const auto mm = std::minmax_element(hVal.begin(), hVal.end());
        const real_t lo = *mm.first, hi = *mm.second;
        std::fprintf(f, "P5\n%d %d\n255\n", GW, GH);
        for (int i = 0; i < nGrid; ++i) {
            const real_t s = (hi > lo) ? (hVal[i] - lo) / (hi - lo) : real_t(0);
            const unsigned char px = (unsigned char)(s * 255.0 + 0.5);
            std::fwrite(&px, 1, 1, f);
        }
        std::fclose(f);
        std::printf("Wrote kriging_estimate.pgm\n");
    }

    // ---------------- cleanup --------------------------------------------------
    CUDA_CHECK(cudaEventDestroy(t0));
    CUDA_CHECK(cudaEventDestroy(t1));
    for (real_t* p : {dsx, dsy, dsv, dAinv, dv, dgx, dgy, dVal, dVar})
        CUDA_CHECK(cudaFree(p));
    return EXIT_SUCCESS;
}