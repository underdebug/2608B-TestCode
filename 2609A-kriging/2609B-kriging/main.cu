#include <cuda_runtime.h>
#include <iostream>
#include <cmath>
#include <vector>
#include <algorithm>
#include <utility>

using real_t = float;


// ============================================================
// Spherical variogram
// ============================================================

__host__ __device__
real_t sphericalVariogram(
    real_t distance,
    real_t nugget,
    real_t sill,
    real_t range)
{
    if (distance <= 0.0f)
        return 0.0f;

    if (distance >= range)
        return nugget + sill;

    real_t h = distance / range;

    return nugget +
           sill * (1.5f * h - 0.5f * h * h * h);
}


// ============================================================
// Solve linear system using Gaussian elimination
//
// A x = b
//
// n is small here: 13 x 13
// ============================================================

__device__
void solveLinearSystem(
    real_t* A,
    real_t* b,
    real_t* x,
    int n)
{
    // --------------------------------------------------------
    // Forward elimination
    // --------------------------------------------------------

    for (int k = 0; k < n; ++k)
    {
        // ----------------------------------------------------
        // Find pivot
        // ----------------------------------------------------

        int pivot = k;

        real_t maxValue = fabsf(A[k * n + k]);

        for (int i = k + 1; i < n; ++i)
        {
            real_t value =
                fabsf(A[i * n + k]);

            if (value > maxValue)
            {
                maxValue = value;
                pivot = i;
            }
        }

        // ----------------------------------------------------
        // Swap rows
        // ----------------------------------------------------

        if (pivot != k)
        {
            for (int j = k; j < n; ++j)
            {
                real_t temp =
                    A[k * n + j];

                A[k * n + j] =
                    A[pivot * n + j];

                A[pivot * n + j] =
                    temp;
            }

            real_t temp = b[k];

            b[k] = b[pivot];
            b[pivot] = temp;
        }

        // ----------------------------------------------------
        // Eliminate
        // ----------------------------------------------------

        for (int i = k + 1; i < n; ++i)
        {
            real_t factor =
                A[i * n + k] /
                A[k * n + k];

            for (int j = k; j < n; ++j)
            {
                A[i * n + j] -=
                    factor * A[k * n + j];
            }

            b[i] -=
                factor * b[k];
        }
    }


    // --------------------------------------------------------
    // Back substitution
    // --------------------------------------------------------

    for (int i = n - 1; i >= 0; --i)
    {
        real_t sum = b[i];

        for (int j = i + 1; j < n; ++j)
        {
            sum -=
                A[i * n + j] * x[j];
        }

        x[i] =
            sum / A[i * n + i];
    }
}


// ============================================================
// Ordinary Kriging CUDA kernel
//
// One thread = one query point
// ============================================================

__global__
void ordinaryKrigingKernel(

    const real_t* sx,
    const real_t* sy,
    const real_t* values,

    const real_t* qx,
    const real_t* qy,

    real_t* output,

    int numSamples,
    int numQueries,

    real_t nugget,
    real_t sill,
    real_t range)
{
    // --------------------------------------------------------
    // Query index
    // --------------------------------------------------------

    int tid =
        blockIdx.x * blockDim.x +
        threadIdx.x;

    if (tid >= numQueries)
        return;


    // --------------------------------------------------------
    // Query point
    // --------------------------------------------------------

    real_t x = qx[tid];
    real_t y = qy[tid];


    // --------------------------------------------------------
    // Ordinary Kriging matrix size
    //
    // N samples + 1 Lagrange multiplier
    // --------------------------------------------------------

    int n = numSamples + 1;


    // --------------------------------------------------------
    // Local matrix
    //
    // For your example:
    //
    // 12 samples
    // => 13 x 13 matrix
    // --------------------------------------------------------

    real_t A[13 * 13];
    real_t b[13];
    real_t solution[13];


    // --------------------------------------------------------
    // Build Kriging matrix
    // --------------------------------------------------------

    for (int i = 0; i < numSamples; ++i)
    {
        for (int j = 0; j < numSamples; ++j)
        {
            real_t dx =
                sx[i] - sx[j];

            real_t dy =
                sy[i] - sy[j];

            real_t distance =
                sqrtf(dx * dx + dy * dy);

            A[i * n + j] =
                sphericalVariogram(
                    distance,
                    nugget,
                    sill,
                    range);
        }

        // Ordinary Kriging constraint
        A[i * n + numSamples] = 1.0f;
    }


    // --------------------------------------------------------
    // Last row
    //
    // 1 1 1 ... 1 0
    // --------------------------------------------------------

    for (int j = 0; j < numSamples; ++j)
    {
        A[numSamples * n + j] = 1.0f;
    }

    A[numSamples * n + numSamples] = 0.0f;


    // --------------------------------------------------------
    // Build right-hand side
    //
    // gamma(sample_i, query)
    //
    // 1
    // --------------------------------------------------------

    for (int i = 0; i < numSamples; ++i)
    {
        real_t dx =
            sx[i] - x;

        real_t dy =
            sy[i] - y;

        real_t distance =
            sqrtf(dx * dx + dy * dy);

        b[i] =
            sphericalVariogram(
                distance,
                nugget,
                sill,
                range);
    }

    b[numSamples] = 1.0f;


    // --------------------------------------------------------
    // Solve:
    //
    // A * solution = b
    // --------------------------------------------------------

    solveLinearSystem(
        A,
        b,
        solution,
        n);


    // --------------------------------------------------------
    // solution[0 ... N-1]
    // are Kriging weights
    //
    // solution[N]
    // is Lagrange multiplier
    // --------------------------------------------------------

    real_t result = 0.0f;

    for (int i = 0; i < numSamples; ++i)
    {
        result +=
            solution[i] * values[i];
    }


    output[tid] = result;
}


// ============================================================
// CPU
// ============================================================

int main()
{
    // --------------------------------------------------------
    // 12 known points
    // --------------------------------------------------------

    real_t h_sx[] = {
        0.0f, 1.0f, 0.0f, 1.0f,
        0.5f, 0.2f, 0.8f, 0.5f,
        0.1f, 0.9f, 0.3f, 0.7f
    };

    real_t h_sy[] = {
        0.0f, 0.0f, 1.0f, 1.0f,
        0.5f, 0.8f, 0.2f, 0.1f,
        0.4f, 0.6f, 0.9f, 0.3f
    };

    real_t h_values[] = {
        10.0f, 20.0f, 30.0f, 40.0f,
        25.0f, 28.0f, 22.0f, 15.0f,
        18.0f, 35.0f, 32.0f, 27.0f
    };

    const int numSamples = 12;

    // --------------------------------------------------------
    // Variogram model parameters
    // --------------------------------------------------------

    real_t nugget = 0.0f;

    real_t sill = 80.0f;

    real_t range = 1.0f;

    // pair.first = lag distance h, pair.second = (Si - Sj)^2
    std::vector<std::pair<double, double>> R;
    for (int i = 0; i < numSamples; ++i) {
        for (int j = i + 1; j < numSamples; ++j) {
            double dx = h_sx[i] - h_sx[j];
            double dy = h_sy[i] - h_sy[j];
            double dv = h_values[i] - h_values[j];
            double l = std::sqrt(dx * dx + dy * dy);
            R.push_back(std::make_pair(l, dv * dv));
        }
    }

    std::sort(R.begin(), R.end(),
        [](const std::pair<double, double>& a, const std::pair<double, double>& b) {
            return a.first < b.first;
        });

    // Bin pairs into lag classes and compute the empirical semivariogram
    // γ*(h) = 1 / (2 * |N(h)|) * sum_{(i,j) in N(h)} (Si - Sj)^2
    const double binWidth = 0.1;
    std::vector<double> h;       // representative lag distance per bin
    std::vector<int> Ncount;     // |N(h)| per bin
    std::vector<double> gamma;      // empirical gamma*(h) per bin
    std::vector<double> variogram;  // model gamma(h) per bin, from sphericalVariogram

    size_t idx = 0;
    while (idx < R.size()) {
        double binStart = std::floor(R[idx].first / binWidth) * binWidth;
        double binEnd = binStart + binWidth;

        double lagSum = 0.0;
        double sqDiffSum = 0.0;
        int count = 0;

        while (idx < R.size() && R[idx].first < binEnd) {
            lagSum += R[idx].first;
            sqDiffSum += R[idx].second;
            ++count;
            ++idx;
        }

        if (count > 0) {
            h.push_back(lagSum / count);
            Ncount.push_back(count);
            gamma.push_back(sqDiffSum / (2.0 * count));
            variogram.push_back(sphericalVariogram(
                static_cast<real_t>(lagSum / count),
                nugget,
                sill,
                range));
        }
    }

    // --------------------------------------------------------
    // Smooth model curve over h in [0, 90]
    // --------------------------------------------------------

    double H[100];
    double V[100];

    for (int i = 0; i < 100; ++i) {
        H[i] = 1.5 * i / (100 - 1);
        V[i] = sphericalVariogram(
            static_cast<real_t>(H[i]),
            nugget,
            sill,
            range);
    }

    printf("Empirical vs model semivariogram:\n");
    for (size_t k = 0; k < h.size(); ++k) {
        printf("  h = %.4f  |N(h)| = %d  gamma*(h) = %.4f  variogram(h) = %.4f\n",
            h[k], Ncount[k], gamma[k], variogram[k]);
    }

    // --------------------------------------------------------
    // Query points
    // --------------------------------------------------------

    real_t h_qx[] = {
        0.5f, 0.25f, 0.75f, 0.1f,
        0.9f, 0.4f, 0.6f
    };

    real_t h_qy[] = {
        0.5f, 0.25f, 0.75f, 0.9f,
        0.1f, 0.6f, 0.4f
    };

    const int numQueries = 7;


    // --------------------------------------------------------
    // GPU memory
    // --------------------------------------------------------

    real_t* d_sx;
    real_t* d_sy;
    real_t* d_values;

    real_t* d_qx;
    real_t* d_qy;

    real_t* d_output;


    cudaMalloc(
        &d_sx,
        numSamples * sizeof(real_t));

    cudaMalloc(
        &d_sy,
        numSamples * sizeof(real_t));

    cudaMalloc(
        &d_values,
        numSamples * sizeof(real_t));

    cudaMalloc(
        &d_qx,
        numQueries * sizeof(real_t));

    cudaMalloc(
        &d_qy,
        numQueries * sizeof(real_t));

    cudaMalloc(
        &d_output,
        numQueries * sizeof(real_t));


    // --------------------------------------------------------
    // CPU -> GPU
    // --------------------------------------------------------

    cudaMemcpy(
        d_sx,
        h_sx,
        numSamples * sizeof(real_t),
        cudaMemcpyHostToDevice);

    cudaMemcpy(
        d_sy,
        h_sy,
        numSamples * sizeof(real_t),
        cudaMemcpyHostToDevice);

    cudaMemcpy(
        d_values,
        h_values,
        numSamples * sizeof(real_t),
        cudaMemcpyHostToDevice);

    cudaMemcpy(
        d_qx,
        h_qx,
        numQueries * sizeof(real_t),
        cudaMemcpyHostToDevice);

    cudaMemcpy(
        d_qy,
        h_qy,
        numQueries * sizeof(real_t),
        cudaMemcpyHostToDevice);


    // --------------------------------------------------------
    // Launch
    // --------------------------------------------------------

    int threadsPerBlock = 4;

    int blocks =
        (numQueries +
         threadsPerBlock - 1)
        / threadsPerBlock;


    ordinaryKrigingKernel<<<
        blocks,
        threadsPerBlock>>>(
            d_sx,
            d_sy,
            d_values,

            d_qx,
            d_qy,

            d_output,

            numSamples,
            numQueries,

            nugget,
            sill,
            range);


    cudaDeviceSynchronize();


    // --------------------------------------------------------
    // GPU -> CPU
    // --------------------------------------------------------

    real_t h_output[numQueries];

    cudaMemcpy(
        h_output,
        d_output,
        numQueries * sizeof(real_t),
        cudaMemcpyDeviceToHost);


    // --------------------------------------------------------
    // Print
    // --------------------------------------------------------

    for (int i = 0; i < numQueries; ++i)
    {
        std::cout
            << "Q("
            << h_qx[i]
            << ", "
            << h_qy[i]
            << ") = "
            << h_output[i]
            << std::endl;
    }


    // --------------------------------------------------------
    // Free
    // --------------------------------------------------------

    cudaFree(d_sx);
    cudaFree(d_sy);
    cudaFree(d_values);

    cudaFree(d_qx);
    cudaFree(d_qy);

    cudaFree(d_output);

    return 0;
}