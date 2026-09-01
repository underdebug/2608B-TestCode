#!/usr/bin/env python3
"""
Generates synthetic test data for the CUDA 2D LIDAR SLAM demo.

World: a rectangular room with a couple of interior walls, described as
line segments. A robot drives a loop-shaped path through the room. At each
time step it casts N lidar rays, computes the true range to the nearest
wall along each ray, adds sensor + odometry noise, and stores the resulting
scan (as x,y points in the ROBOT's local frame -- exactly what a real lidar
driver would hand you).

Outputs (all plain CSV, no header math needed on the CUDA side):
  data/walls.csv            -- x1,y1,x2,y2  (ground-truth map, for plotting only)
  data/ground_truth_traj.csv-- x,y,theta    (true robot pose per step, for eval only)
  data/scan_000.csv, scan_001.csv, ...      -- x,y points per scan, robot frame
  data/manifest.csv         -- num_scans,points_per_scan (so the CUDA program
                                knows how many files to read without parsing dirs)
"""

import numpy as np
import os

np.random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------- world ---
# Line segments (x1,y1,x2,y2) describing walls of a ~10x8 room plus one
# interior partition, in meters.
walls = np.array([
    [0, 0, 10, 0],
    [10, 0, 10, 8],
    [10, 8, 0, 8],
    [0, 8, 0, 0],
    [5, 0, 5, 5],   # interior partition (leaves a gap at the top for the loop)
], dtype=np.float64)

np.savetxt(os.path.join(OUT_DIR, "walls.csv"), walls, delimiter=",",
           header="x1,y1,x2,y2", comments="")

# ------------------------------------------------------------ robot path --
# A simple loop around the interior wall so scans overlap frame-to-frame
# (needed for scan-matching SLAM to have something to lock onto).
N_STEPS = 100
t = np.linspace(0, 2 * np.pi, N_STEPS, endpoint=False)
cx, cy, r = 5.0, 4.0, 3.2
xs = cx + r * np.cos(t)
ys = cy + r * np.sin(t)
thetas = t + np.pi / 2  # heading tangent to the loop

true_traj = np.stack([xs, ys, thetas], axis=1)
np.savetxt(os.path.join(OUT_DIR, "ground_truth_traj.csv"), true_traj,
           delimiter=",", header="x,y,theta", comments="")


def ray_segment_intersect(ox, oy, dx, dy, x1, y1, x2, y2):
    """Return distance t>=0 along ray (ox,oy)+t*(dx,dy) to segment, or inf."""
    sx, sy = x2 - x1, y2 - y1
    denom = dx * sy - dy * sx
    if abs(denom) < 1e-12:
        return np.inf
    t = ((x1 - ox) * sy - (y1 - oy) * sx) / denom
    u = ((x1 - ox) * dy - (y1 - oy) * dx) / denom
    if t >= 0 and 0 <= u <= 1:
        return t
    return np.inf


POINTS_PER_SCAN = 90       # lidar rays per scan
FOV = 2 * np.pi             # full 360-degree lidar
RANGE_NOISE_STD = 0.02      # meters
MAX_RANGE = 15.0

angles = np.linspace(0, FOV, POINTS_PER_SCAN, endpoint=False)

for i, (rx, ry, rtheta) in enumerate(true_traj):
    pts = []
    for a in angles:
        world_angle = rtheta + a
        dx, dy = np.cos(world_angle), np.sin(world_angle)
        best = MAX_RANGE
        for (x1, y1, x2, y2) in walls:
            d = ray_segment_intersect(rx, ry, dx, dy, x1, y1, x2, y2)
            if d < best:
                best = d
        if best < MAX_RANGE:
            noisy_range = max(0.0, best + np.random.normal(0, RANGE_NOISE_STD))
            # store in ROBOT LOCAL FRAME (angle relative to heading), like a real driver
            lx = noisy_range * np.cos(a)
            ly = noisy_range * np.sin(a)
            pts.append((lx, ly))
    pts = np.array(pts)
    np.savetxt(os.path.join(OUT_DIR, f"scan_{i:03d}.csv"), pts,
               delimiter=",", header="x,y", comments="")

with open(os.path.join(OUT_DIR, "manifest.csv"), "w") as f:
    f.write("num_scans,points_per_scan\n")
    f.write(f"{N_STEPS},{POINTS_PER_SCAN}\n")

print(f"Wrote {N_STEPS} scans (~{POINTS_PER_SCAN} pts each) to {OUT_DIR}")
