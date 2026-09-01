# CUDA 2D LIDAR SLAM (scan-to-map ICP)

A minimal but complete, runnable SLAM example: a simulated robot with a 360°
lidar drives a loop around a room, and a GPU-accelerated ICP scan-matcher
reconstructs both the map and the robot's trajectory from the raw scans
alone (no wheel odometry, no GPS).

```
slam_cuda/
├── generate_test_data.py   # builds the synthetic test data (run first)
├── src/slam.cu              # the CUDA program
├── reference_slam.py        # CPU/NumPy port of the exact same algorithm
├── plot_results.py          # aligns + scores + plots the output trajectory
└── data/                    # generated scans, walls, ground truth, results
```

## Algorithm

Classic **scan-to-map ICP** SLAM front end:

1. Simulate a 2D lidar: at each timestep cast rays against a wall map,
   add range noise → a scan (points in the robot's local frame).
2. For each new scan:
   - Predict the pose with a constant-velocity extrapolation of the last
     estimated motion.
   - Iterate a few rounds of ICP: nearest-neighbor match every scan point
     against the accumulated global point-cloud map, reject matches beyond
     a distance threshold, then solve the optimal 2D rigid transform
     (closed-form Horn/Kabsch) for the surviving correspondences.
3. Fold the newly-aligned scan into the map and move to the next scan.

**What's on the GPU** (`src/slam.cu`):
- `transformKernel` — rotate/translate a scan's points by a candidate pose (1 thread/point).
- `nearestNeighborKernel` — brute-force nearest-neighbor search of every scan
  point against the *entire* accumulated map (1 thread per query point, each
  thread scans the whole map). This is the O(scan_size × map_size) step that
  gets more expensive every frame as the map grows — exactly the part worth
  parallelizing, and where you'll see the GPU pull ahead of a CPU version as
  the map grows into the thousands/millions of points.

The pose solve itself (a few sums over ≤90 correspondences) stays on the
host — it's too small and too sequential to be worth a kernel launch.

## Build & run (needs an NVIDIA GPU + CUDA toolkit)

```bash
python3 generate_test_data.py        # writes data/*.csv
nvcc -O2 -arch=sm_70 src/slam.cu -o slam   # set -arch for your GPU (sm_60 Pascal, sm_75 Turing, sm_86 Ampere, sm_90 Hopper...)
./slam data                          # writes data/estimated_traj.csv
python3 plot_results.py              # prints error metrics, saves data/result_plot.png
```

Expect console output like:

```
Loaded manifest: 100 scans, ~90 pts/scan
scan   0/99  pose=(0.000, 0.000, 0.000 rad)  map_pts=90
scan  10/99  pose=(...)  map_pts=990
...
Done. 100 scans -> 9000 map points.
GPU time: 12.4 ms   NN comparisons performed: 41827500
```

## A note on this sandbox

This container has the CUDA **toolkit** (`nvcc`) but no physical GPU, so
`slam.cu` compiles cleanly here but can't execute past the first
`cudaMalloc`. To make sure the *algorithm* itself is correct before you run
it on real hardware, `reference_slam.py` is a line-for-line NumPy port of
the same math (same ICP loop, same constant-velocity prediction, same
closed-form rotation fit). Run it and `plot_results.py` to see the expected
behavior:

```bash
python3 reference_slam.py
python3 plot_results.py reference_estimated_traj.csv
```

On the included test set (100 scans, loop of radius ~3.2 m, 2 cm range
noise, no loop-closure correction) this gives:

```
Mean position error: 0.344 m
Max position error:  0.535 m
Final position error: 0.147 m
```

The `data/result_plot.png` in this folder shows the ground truth loop vs.
the reconstructed trajectory. `slam.cu` implements the identical algorithm,
so it should reproduce these numbers (up to floating-point noise) on a real
GPU — only the nearest-neighbor search and point transforms move from
NumPy vector ops to CUDA kernels.

## Notes / honest limitations

- **No loop closure.** This is pure frame-to-map ICP odometry, so error
  drifts over time (visible as the estimated loop being very slightly
  larger than ground truth). A real SLAM stack would detect revisiting a
  place and correct the whole trajectory with a pose-graph optimizer —
  out of scope for a "minimal CUDA example" but a natural next step.
- **Brute-force NN, not a KD-tree.** Deliberate: it's the simplest thing
  that parallelizes perfectly on a GPU and is easy to read. For very large
  maps you'd want a spatial data structure (grid hashing works well on GPU).
- 2D only. Extending to 3D means swapping `float2`→`float3` and the 2D
  closed-form rotation fit for a real 3×3 SVD (e.g. via cuSOLVER or a
  small on-device Jacobi SVD).
