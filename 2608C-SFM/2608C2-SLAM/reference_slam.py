#!/usr/bin/env python3
"""
CPU reference implementation of the same scan-to-map ICP SLAM algorithm
that slam.cu implements on the GPU. Used to validate correctness (which
parts are cheap to check on CPU, i.e. everything except raw NN-search
throughput) before trusting the CUDA port.

Algorithm per new scan:
  1. Transform the raw local-frame scan points using the pose estimate
     carried over from the previous step (initial guess).
  2. Nearest-neighbor match each transformed point against the accumulated
     global map (brute force -- this is the O(N*M) step CUDA parallelizes).
  3. Reject correspondences farther than a distance threshold (outlier
     rejection, handles the "no wall behind" case near doorways).
  4. Solve the optimal 2D rigid transform (Kabsch/SVD) mapping the ORIGINAL
     local-frame scan points to their matched map points.
  5. Repeat 2-4 for a few ICP iterations, refining the pose.
  6. Transform the scan into the global frame with the converged pose and
     append it to the map. Record the pose as this step's SLAM estimate.
"""

import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_manifest():
    arr = np.genfromtxt(os.path.join(DATA_DIR, "manifest.csv"), delimiter=",",
                         skip_header=1)
    return int(arr[0]), int(arr[1])


def load_scan(i):
    return np.genfromtxt(os.path.join(DATA_DIR, f"scan_{i:03d}.csv"),
                          delimiter=",", skip_header=1)


def transform_pts(pts, pose):
    x, y, th = pose
    c, s = np.cos(th), np.sin(th)
    R = np.array([[c, -s], [s, c]])
    return pts @ R.T + np.array([x, y])


def nearest_neighbors(query, target):
    """Brute-force NN: for each query point, index+distance of closest target point."""
    d2 = ((query[:, None, :] - target[None, :, :]) ** 2).sum(axis=2)
    idx = np.argmin(d2, axis=1)
    dist = np.sqrt(d2[np.arange(len(query)), idx])
    return idx, dist


def kabsch_2d(src, dst):
    """Optimal rigid transform (R,t) minimizing ||R*src + t - dst||^2."""
    src_c = src.mean(axis=0)
    dst_c = dst.mean(axis=0)
    src0 = src - src_c
    dst0 = dst - dst_c
    H = src0.T @ dst0
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, d])
    R = Vt.T @ D @ U.T
    t = dst_c - R @ src_c
    theta = np.arctan2(R[1, 0], R[0, 0])
    x, y = t
    return np.array([x, y, theta])


def icp(local_pts, global_map, pose_init, iters=8, max_corr_dist=0.6):
    pose = pose_init.copy()
    for _ in range(iters):
        transformed = transform_pts(local_pts, pose)
        idx, dist = nearest_neighbors(transformed, global_map)
        mask = dist < max_corr_dist
        if mask.sum() < 5:
            break
        pose = kabsch_2d(local_pts[mask], global_map[idx[mask]])
    return pose


def main():
    n_scans, _ = load_manifest()

    scan0 = load_scan(0)
    pose = np.array([0.0, 0.0, 0.0])
    global_map = transform_pts(scan0, pose).copy()

    est_traj = [pose.copy()]
    prev_pose = pose.copy()

    for i in range(1, n_scans):
        scan = load_scan(i)
        # constant-velocity motion prediction as the ICP initial guess
        # (a real system would use wheel odometry / IMU here; we don't have
        # either, so we extrapolate the last estimated motion instead of
        # naively assuming the robot didn't move)
        if i >= 2:
            vel = pose - prev_pose
            init_guess = pose + vel
        else:
            init_guess = pose
        prev_pose = pose.copy()

        pose = icp(scan, global_map, pose_init=init_guess)
        est_traj.append(pose.copy())
        global_map = np.vstack([global_map, transform_pts(scan, pose)])

    est_traj = np.array(est_traj)
    np.savetxt(os.path.join(DATA_DIR, "reference_estimated_traj.csv"),
               est_traj, delimiter=",", header="x,y,theta", comments="")

    gt = np.genfromtxt(os.path.join(DATA_DIR, "ground_truth_traj.csv"),
                        delimiter=",", skip_header=1)
    # SLAM only recovers pose up to the arbitrary frame it started in
    # (est_traj[0] == origin by construction). Align that frame to the
    # world frame using the known true starting pose before comparing --
    # this is standard practice ("align to first pose"), not cheating:
    # a real SLAM stack's output is always relative to wherever it booted.
    th0 = gt[0, 2]
    c, s = np.cos(th0), np.sin(th0)
    R0 = np.array([[c, -s], [s, c]])
    est_world_xy = est_traj[:, :2] @ R0.T + gt[0, :2]
    err = np.sqrt(((est_world_xy - gt[:, :2]) ** 2).sum(axis=1))
    print(f"Scans processed:        {n_scans}")
    print(f"Final map size:         {len(global_map)} points")
    print(f"Mean position error:    {err.mean():.4f} m")
    print(f"Max position error:     {err.max():.4f} m")
    print(f"Final position error:   {err[-1]:.4f} m")


if __name__ == "__main__":
    main()
