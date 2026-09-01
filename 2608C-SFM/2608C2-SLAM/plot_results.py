#!/usr/bin/env python3
"""
Loads data/estimated_traj.csv (written by slam.cu, or by reference_slam.py
if you're running the CPU version) plus the ground truth, aligns SLAM's
local starting frame to the world frame, prints error metrics, and saves a
plot comparing the two trajectories over the reconstructed map.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load(name):
    return np.genfromtxt(os.path.join(DATA_DIR, name), delimiter=",", skip_header=1)


def main():
    traj_file = sys.argv[1] if len(sys.argv) > 1 else "estimated_traj.csv"
    est = load(traj_file)
    gt = load("ground_truth_traj.csv")
    walls = load("walls.csv")

    # Align SLAM's local frame (starts at origin) to the world frame using
    # the known true starting pose -- SLAM has no absolute reference, so
    # comparing raw coordinates would just measure that arbitrary offset.
    th0 = gt[0, 2]
    c, s = np.cos(th0), np.sin(th0)
    R0 = np.array([[c, -s], [s, c]])
    est_world_xy = est[:, :2] @ R0.T + gt[0, :2]

    err = np.sqrt(((est_world_xy - gt[:, :2]) ** 2).sum(axis=1))
    print(f"Mean position error: {err.mean():.4f} m")
    print(f"Max position error:  {err.max():.4f} m")
    print(f"Final position error:{err[-1]:.4f} m")

    fig, ax = plt.subplots(figsize=(8, 6.4))
    for x1, y1, x2, y2 in walls:
        ax.plot([x1, x2], [y1, y2], color="black", linewidth=2)
    ax.plot(gt[:, 0], gt[:, 1], "g-", label="ground truth", linewidth=2)
    ax.plot(est_world_xy[:, 0], est_world_xy[:, 1], "r--", label="SLAM estimate",
             linewidth=2)
    ax.scatter(gt[0, 0], gt[0, 1], c="green", marker="o", s=80, zorder=5)
    ax.set_aspect("equal")
    ax.legend()
    ax.set_title(f"2D LIDAR SLAM (scan-to-map ICP)\nmean err {err.mean():.3f} m, "
                  f"final err {err[-1]:.3f} m")
    out_path = os.path.join(DATA_DIR, "result_plot.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved plot to {out_path}")


if __name__ == "__main__":
    main()
