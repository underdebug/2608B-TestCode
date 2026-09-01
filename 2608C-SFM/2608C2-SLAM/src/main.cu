// slam.cu
// ---------------------------------------------------------------------------
// Minimal GPU-accelerated 2D LIDAR SLAM (scan-to-map ICP).
//
// What's actually running on the GPU:
//   1. transformKernel   - rotate+translate a scan's points by a candidate
//                           pose (one thread per point).
//   2. nearestNeighborKernel - for every (transformed) scan point, brute-force
//                           search the entire accumulated map for its closest
//                           point (one thread per query point, each thread
//                           scans the whole map). This is the O(n_scan *
//                           n_map) step that gets slower every frame as the
//                           map grows, and is exactly the part that benefits
//                           from parallelizing over n_scan threads.
//
// What stays on the host (deliberately -- these are tiny, sequential, and
// not worth a kernel):
//   - reading CSVs
//   - the 2D closed-form Kabsch/Horn rotation fit (a handful of sums over
//     <=90 correspondences per ICP iteration)
//   - the outer ICP iteration loop and the outer per-scan SLAM loop
//
// Build:
//   nvcc -O2 -arch=sm_70 src/slam.cu -o slam
//   (drop -arch or set it to match your GPU; sm_70+ covers anything from
//   Volta onward, use sm_60 for Pascal, sm_86 for Ampere, etc.)
//
// Run (from the slam_cuda/ directory, after generate_test_data.py has been
// run so data/ is populated):
//   ./slam data
//
// Output:
//   data/estimated_traj.csv  -- x,y,theta per scan, in the SLAM system's own
//                                frame (== world frame rotated/translated by
//                                wherever scan 0 happened to be -- see
//                                plot_results.py for how to compare this
//                                fairly against ground truth).
// ---------------------------------------------------------------------------

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <cfloat>
#include <cuda_runtime.h>

#define CUDA_CHECK(call)                                                     \
    do {                                                                     \
        cudaError_t err__ = (call);                                          \
        if (err__ != cudaSuccess) {                                          \
            fprintf(stderr, "CUDA error %s:%d: %s\n", __FILE__, __LINE__,    \
                    cudaGetErrorString(err__));                              \
            exit(EXIT_FAILURE);                                              \
        }                                                                    \
    } while (0)

struct Pose {
    float x = 0.f, y = 0.f, theta = 0.f;
};

// ----------------------------------------------------------------- kernels -

// Rotate+translate `n` points by `pose`. One thread per point.
__global__ void transformKernel(const float2 *in, int n, Pose pose,
                                 float2 *out) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;
    float c = cosf(pose.theta), s = sinf(pose.theta);
    float x = in[i].x, y = in[i].y;
    out[i].x = c * x - s * y + pose.x;
    out[i].y = s * x + c * y + pose.y;
}

// Brute-force nearest neighbor: for each of `nq` query points, find the
// closest of `nt` target points. One thread per query point; each thread
// scans the full target set. O(nq * nt) work, parallelized nq-wide.
__global__ void nearestNeighborKernel(const float2 *query, int nq,
                                       const float2 *target, int nt,
                                       int *bestIdx, float *bestDist2) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= nq) return;

    float qx = query[i].x, qy = query[i].y;
    float best = FLT_MAX;
    int besti = -1;
    for (int j = 0; j < nt; ++j) {
        float dx = qx - target[j].x;
        float dy = qy - target[j].y;
        float d2 = dx * dx + dy * dy;
        if (d2 < best) {
            best = d2;
            besti = j;
        }
    }
    bestIdx[i] = besti;
    bestDist2[i] = best;
}

// ------------------------------------------------------------------- I/O ---

static bool readManifest(const std::string &dir, int &nScans, int &ptsPerScan) {
    std::ifstream f(dir + "/manifest.csv");
    if (!f) return false;
    std::string line;
    std::getline(f, line);  // header
    std::getline(f, line);  // data
    std::stringstream ss(line);
    std::string a, b;
    std::getline(ss, a, ',');
    std::getline(ss, b, ',');
    nScans = std::atoi(a.c_str());
    ptsPerScan = std::atoi(b.c_str());
    return true;
}

static bool readScan(const std::string &dir, int idx, std::vector<float2> &pts) {
    char path[512];
    std::snprintf(path, sizeof(path), "%s/scan_%03d.csv", dir.c_str(), idx);
    std::ifstream f(path);
    if (!f) return false;
    pts.clear();
    std::string line;
    std::getline(f, line);  // header
    while (std::getline(f, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string a, b;
        std::getline(ss, a, ',');
        std::getline(ss, b, ',');
        float2 p;
        p.x = std::strtof(a.c_str(), nullptr);
        p.y = std::strtof(b.c_str(), nullptr);
        pts.push_back(p);
    }
    return true;
}

static void writeTrajectory(const std::string &dir,
                             const std::vector<Pose> &traj) {
    std::ofstream f(dir + "/estimated_traj.csv");
    f << "x,y,theta\n";
    for (const auto &p : traj)
        f << p.x << "," << p.y << "," << p.theta << "\n";
}

// ------------------------------------------------------- host-side Kabsch --

// Closed-form optimal 2D rigid transform (rotation + translation) mapping
// `src` onto `dst`, given point correspondences. Equivalent to 2D Kabsch/SVD
// but solved analytically (treat each point as a complex number; the
// optimal rotation is the angle of sum(conj(src_centered) * dst_centered)).
// Cheap enough (<=90 correspondences) that it isn't worth a kernel.
static Pose solveRigidTransform(const std::vector<float2> &src,
                                 const std::vector<float2> &dst) {
    size_t n = src.size();
    float2 srcC{0, 0}, dstC{0, 0};
    for (size_t i = 0; i < n; ++i) {
        srcC.x += src[i].x; srcC.y += src[i].y;
        dstC.x += dst[i].x; dstC.y += dst[i].y;
    }
    srcC.x /= n; srcC.y /= n;
    dstC.x /= n; dstC.y /= n;

    double Sxx = 0, Sxy = 0, Syx = 0, Syy = 0;
    for (size_t i = 0; i < n; ++i) {
        double px = src[i].x - srcC.x, py = src[i].y - srcC.y;
        double qx = dst[i].x - dstC.x, qy = dst[i].y - dstC.y;
        Sxx += px * qx;
        Sxy += px * qy;
        Syx += py * qx;
        Syy += py * qy;
    }
    double theta = std::atan2(Sxy - Syx, Sxx + Syy);
    double c = std::cos(theta), s = std::sin(theta);

    Pose pose;
    pose.theta = (float)theta;
    // t = dstCentroid - R * srcCentroid
    pose.x = dstC.x - (float)(c * srcC.x - s * srcC.y);
    pose.y = dstC.y - (float)(s * srcC.x + c * srcC.y);
    return pose;
}

// ---------------------------------------------------------------- main ----

int main(int argc, char **argv) {
    std::string dataDir = (argc > 1) ? argv[1] : "data";

    int nScans = 0, maxPtsPerScan = 0;
    if (!readManifest(dataDir, nScans, maxPtsPerScan)) {
        fprintf(stderr, "Could not read %s/manifest.csv\n", dataDir.c_str());
        return 1;
    }
    printf("Loaded manifest: %d scans, ~%d pts/scan\n", nScans, maxPtsPerScan);

    const int ICP_ITERS = 8;
    const float MAX_CORR_DIST = 0.6f;
    const float MAX_CORR_DIST2 = MAX_CORR_DIST * MAX_CORR_DIST;
    const int THREADS = 128;

    // Device buffers, sized once for the whole run.
    float2 *d_local, *d_transformed;
    int *d_idx;
    float *d_dist2;
    CUDA_CHECK(cudaMalloc(&d_local, maxPtsPerScan * sizeof(float2)));
    CUDA_CHECK(cudaMalloc(&d_transformed, maxPtsPerScan * sizeof(float2)));
    CUDA_CHECK(cudaMalloc(&d_idx, maxPtsPerScan * sizeof(int)));
    CUDA_CHECK(cudaMalloc(&d_dist2, maxPtsPerScan * sizeof(float)));

    size_t mapCapacity = (size_t)nScans * maxPtsPerScan;
    float2 *d_map;
    CUDA_CHECK(cudaMalloc(&d_map, mapCapacity * sizeof(float2)));
    std::vector<float2> h_map;  // host mirror, needed to gather correspondence targets
    h_map.reserve(mapCapacity);

    std::vector<Pose> trajectory;
    trajectory.reserve(nScans);

    cudaEvent_t evStart, evStop;
    CUDA_CHECK(cudaEventCreate(&evStart));
    CUDA_CHECK(cudaEventCreate(&evStop));
    CUDA_CHECK(cudaEventRecord(evStart));

    Pose pose;       // current pose estimate, world/SLAM frame
    Pose prevPose;   // pose one step back, for constant-velocity prediction

    std::vector<float2> h_local, h_transformed;
    std::vector<int> h_idx;
    std::vector<float> h_dist2;

    long long totalNNComparisons = 0;

    for (int scanIdx = 0; scanIdx < nScans; ++scanIdx) {
        if (!readScan(dataDir, scanIdx, h_local)) {
            fprintf(stderr, "Could not read scan %d\n", scanIdx);
            return 1;
        }
        int n = (int)h_local.size();
        h_transformed.resize(n);
        h_idx.resize(n);
        h_dist2.resize(n);

        CUDA_CHECK(cudaMemcpy(d_local, h_local.data(), n * sizeof(float2),
                               cudaMemcpyHostToDevice));

        if (scanIdx == 0) {
            pose = Pose{0.f, 0.f, 0.f};
        } else {
            // Constant-velocity initial guess: extrapolate the last
            // estimated motion instead of assuming the robot stood still.
            Pose guess = pose;
            if (scanIdx >= 2) {
                guess.x = pose.x + (pose.x - prevPose.x);
                guess.y = pose.y + (pose.y - prevPose.y);
                guess.theta = pose.theta + (pose.theta - prevPose.theta);
            }
            prevPose = pose;

            int mapCount = (int)h_map.size();
            int blocks = (n + THREADS - 1) / THREADS;

            Pose iterPose = guess;
            for (int iter = 0; iter < ICP_ITERS; ++iter) {
                transformKernel<<<blocks, THREADS>>>(d_local, n, iterPose,
                                                       d_transformed);
                CUDA_CHECK(cudaGetLastError());

                nearestNeighborKernel<<<blocks, THREADS>>>(
                    d_transformed, n, d_map, mapCount, d_idx, d_dist2);
                CUDA_CHECK(cudaGetLastError());
                totalNNComparisons += (long long)n * mapCount;

                CUDA_CHECK(cudaMemcpy(h_idx.data(), d_idx, n * sizeof(int),
                                       cudaMemcpyDeviceToHost));
                CUDA_CHECK(cudaMemcpy(h_dist2.data(), d_dist2, n * sizeof(float),
                                       cudaMemcpyDeviceToHost));

                std::vector<float2> src, dst;
                src.reserve(n); dst.reserve(n);
                for (int i = 0; i < n; ++i) {
                    if (h_idx[i] >= 0 && h_dist2[i] < MAX_CORR_DIST2) {
                        src.push_back(h_local[i]);
                        dst.push_back(h_map[h_idx[i]]);
                    }
                }
                if (src.size() < 5) break;  // not enough overlap, keep last good pose
                iterPose = solveRigidTransform(src, dst);
            }
            pose = iterPose;
        }

        trajectory.push_back(pose);

        // Fold this scan into the map at its final estimated pose.
        int blocks = (n + THREADS - 1) / THREADS;
        transformKernel<<<blocks, THREADS>>>(d_local, n, pose, d_transformed);
        CUDA_CHECK(cudaGetLastError());
        CUDA_CHECK(cudaMemcpy(h_transformed.data(), d_transformed,
                               n * sizeof(float2), cudaMemcpyDeviceToHost));

        size_t offset = h_map.size();
        h_map.insert(h_map.end(), h_transformed.begin(), h_transformed.end());
        CUDA_CHECK(cudaMemcpy(d_map + offset, h_transformed.data(),
                               n * sizeof(float2), cudaMemcpyHostToDevice));

        if (scanIdx % 10 == 0 || scanIdx == nScans - 1) {
            printf("scan %3d/%d  pose=(%.3f, %.3f, %.3f rad)  map_pts=%zu\n",
                   scanIdx, nScans - 1, pose.x, pose.y, pose.theta, h_map.size());
        }
    }

    CUDA_CHECK(cudaEventRecord(evStop));
    CUDA_CHECK(cudaEventSynchronize(evStop));
    float ms = 0.f;
    CUDA_CHECK(cudaEventElapsedTime(&ms, evStart, evStop));

    writeTrajectory(dataDir, trajectory);

    printf("\nDone. %d scans -> %zu map points.\n", nScans, h_map.size());
    printf("GPU time: %.2f ms   NN comparisons performed: %lld\n", ms,
           totalNNComparisons);
    printf("Wrote %s/estimated_traj.csv\n", dataDir.c_str());

    cudaFree(d_local);
    cudaFree(d_transformed);
    cudaFree(d_idx);
    cudaFree(d_dist2);
    cudaFree(d_map);
    cudaEventDestroy(evStart);
    cudaEventDestroy(evStop);
    return 0;
}
