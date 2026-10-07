"""Calculate cubic B-spline controls; draw data blue and controls red."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

d = [[{'x': -1.0, 'y': -1.0, 'z': 0.199}, {'x': -1.0, 'y': -0.778, 'z': 0.151}, {'x': -1.0, 'y': -0.556, 'z': 0.088}, {'x': -1.0, 'y': -0.333, 'z': 0.023}, {'x': -1.0, 'y': -0.111, 'z': -0.03}, {'x': -1.0, 'y': 0.111, 'z': -0.063}, {'x': -1.0, 'y': 0.333, 'z': -0.077}, {'x': -1.0, 'y': 0.556, 'z': -0.079}, {'x': -1.0, 'y': 0.778, 'z': -0.083}, {'x': -1.0, 'y': 1.0, 'z': -0.101}],
 [{'x': -0.778, 'y': -1.0, 'z': 0.367}, {'x': -0.778, 'y': -0.778, 'z': 0.266}, {'x': -0.778, 'y': -0.556, 'z': 0.089}, {'x': -0.778, 'y': -0.333, 'z': -0.098}, {'x': -0.778, 'y': -0.111, 'z': -0.226}, {'x': -0.778, 'y': 0.111, 'z': -0.252}, {'x': -0.778, 'y': 0.333, 'z': -0.176}, {'x': -0.778, 'y': 0.556, 'z': -0.041}, {'x': -0.778, 'y': 0.778, 'z': 0.084}, {'x': -0.778, 'y': 1.0, 'z': 0.134}],
 [{'x': -0.556, 'y': -1.0, 'z': 0.428}, {'x': -0.556, 'y': -0.778, 'z': 0.305}, {'x': -0.556, 'y': -0.556, 'z': 0.08}, {'x': -0.556, 'y': -0.333, 'z': -0.16}, {'x': -0.556, 'y': -0.111, 'z': -0.32}, {'x': -0.556, 'y': 0.111, 'z': -0.338}, {'x': -0.556, 'y': 0.333, 'z': -0.216}, {'x': -0.556, 'y': 0.556, 'z': -0.013}, {'x': -0.556, 'y': 0.778, 'z': 0.176}, {'x': -0.556, 'y': 1.0, 'z': 0.262}],
 [{'x': -0.333, 'y': -1.0, 'z': 0.342}, {'x': -0.333, 'y': -0.778, 'z': 0.242}, {'x': -0.333, 'y': -0.556, 'z': 0.056}, {'x': -0.333, 'y': -0.333, 'z': -0.142}, {'x': -0.333, 'y': -0.111, 'z': -0.273}, {'x': -0.333, 'y': 0.111, 'z': -0.284}, {'x': -0.333, 'y': 0.333, 'z': -0.176}, {'x': -0.333, 'y': 0.556, 'z': 0.0}, {'x': -0.333, 'y': 0.778, 'z': 0.165}, {'x': -0.333, 'y': 1.0, 'z': 0.242}],
 [{'x': -0.111, 'y': -1.0, 'z': 0.13}, {'x': -0.111, 'y': -0.778, 'z': 0.092}, {'x': -0.111, 'y': -0.556, 'z': 0.02}, {'x': -0.111, 'y': -0.333, 'z': -0.056}, {'x': -0.111, 'y': -0.111, 'z': -0.106}, {'x': -0.111, 'y': 0.111, 'z': -0.11}, {'x': -0.111, 'y': 0.333, 'z': -0.067}, {'x': -0.111, 'y': 0.556, 'z': 0.002}, {'x': -0.111, 'y': 0.778, 'z': 0.066}, {'x': -0.111, 'y': 1.0, 'z': 0.097}],
 [{'x': 0.111, 'y': -1.0, 'z': -0.13}, {'x': 0.111, 'y': -0.778, 'z': -0.092}, {'x': 0.111, 'y': -0.556, 'z': -0.02}, {'x': 0.111, 'y': -0.333, 'z': 0.056}, {'x': 0.111, 'y': -0.111, 'z': 0.106}, {'x': 0.111, 'y': 0.111, 'z': 0.11}, {'x': 0.111, 'y': 0.333, 'z': 0.067}, {'x': 0.111, 'y': 0.556, 'z': -0.002}, {'x': 0.111, 'y': 0.778, 'z': -0.066}, {'x': 0.111, 'y': 1.0, 'z': -0.097}],
 [{'x': 0.333, 'y': -1.0, 'z': -0.342}, {'x': 0.333, 'y': -0.778, 'z': -0.242}, {'x': 0.333, 'y': -0.556, 'z': -0.056}, {'x': 0.333, 'y': -0.333, 'z': 0.142}, {'x': 0.333, 'y': -0.111, 'z': 0.273}, {'x': 0.333, 'y': 0.111, 'z': 0.284}, {'x': 0.333, 'y': 0.333, 'z': 0.176}, {'x': 0.333, 'y': 0.556, 'z': -0.0}, {'x': 0.333, 'y': 0.778, 'z': -0.165}, {'x': 0.333, 'y': 1.0, 'z': -0.242}],
 [{'x': 0.556, 'y': -1.0, 'z': -0.428}, {'x': 0.556, 'y': -0.778, 'z': -0.305}, {'x': 0.556, 'y': -0.556, 'z': -0.08}, {'x': 0.556, 'y': -0.333, 'z': 0.16}, {'x': 0.556, 'y': -0.111, 'z': 0.32}, {'x': 0.556, 'y': 0.111, 'z': 0.338}, {'x': 0.556, 'y': 0.333, 'z': 0.216}, {'x': 0.556, 'y': 0.556, 'z': 0.013}, {'x': 0.556, 'y': 0.778, 'z': -0.176}, {'x': 0.556, 'y': 1.0, 'z': -0.262}],
 [{'x': 0.778, 'y': -1.0, 'z': -0.367}, {'x': 0.778, 'y': -0.778, 'z': -0.266}, {'x': 0.778, 'y': -0.556, 'z': -0.089}, {'x': 0.778, 'y': -0.333, 'z': 0.098}, {'x': 0.778, 'y': -0.111, 'z': 0.226}, {'x': 0.778, 'y': 0.111, 'z': 0.252}, {'x': 0.778, 'y': 0.333, 'z': 0.176}, {'x': 0.778, 'y': 0.556, 'z': 0.041}, {'x': 0.778, 'y': 0.778, 'z': -0.084}, {'x': 0.778, 'y': 1.0, 'z': -0.134}],
 [{'x': 1.0, 'y': -1.0, 'z': -0.199}, {'x': 1.0, 'y': -0.778, 'z': -0.151}, {'x': 1.0, 'y': -0.556, 'z': -0.088}, {'x': 1.0, 'y': -0.333, 'z': -0.023}, {'x': 1.0, 'y': -0.111, 'z': 0.03}, {'x': 1.0, 'y': 0.111, 'z': 0.063}, {'x': 1.0, 'y': 0.333, 'z': 0.077}, {'x': 1.0, 'y': 0.556, 'z': 0.079}, {'x': 1.0, 'y': 0.778, 'z': 0.083}, {'x': 1.0, 'y': 1.0, 'z': 0.101}]]

# Same exact clamped cubic knots as surface.hpp.
k = np.r_[np.zeros(4), np.arange(2, 8) / 9, np.ones(4)]


def basis(parameters):
    """Return one row of ten cubic basis values per parameter."""
    parameters = np.asarray(parameters, dtype=float).reshape(-1)
    b = ((parameters[:, None] >= k[:-1]) &
         (parameters[:, None] < k[1:])).astype(float)
    for degree in range(1, 4):
        for i in range(13 - degree):
            left = k[i + degree] - k[i]
            right = k[i + degree + 1] - k[i + 1]
            b[:, i] = (
                (parameters - k[i]) * b[:, i] / left if left else 0
            ) + (
                (k[i + degree + 1] - parameters) * b[:, i + 1] / right
                if right else 0
            )
    b = b[:, :10]
    b[parameters == 1] = 0
    b[parameters == 1, -1] = 1
    return b


def interpolate(data):
    """Solve D = A C A.T without explicitly inverting A."""
    data = np.asarray(data)
    if data.shape == (10, 10) and data.dtype == object:
        data = np.array([[[p[axis] for axis in ("x", "y", "z")]
                          for p in row] for row in data], dtype=float)
    else:
        data = np.asarray(data, dtype=float)
    if data.shape != (10, 10, 3):
        raise ValueError("Expected a 10 x 10 grid of three-dimensional points")
    a = basis(np.arange(10) / 9)
    # Solve along u: A T = D, for every column and coordinate.
    t = np.linalg.solve(a, data.reshape(10, -1)).reshape(data.shape)
    # Solve along v: A C.T = T.T, then restore the grid axes.
    c = np.linalg.solve(a, t.transpose(1, 0, 2).reshape(10, -1))
    return c.reshape(data.shape).transpose(1, 0, 2)


def main():
    data = np.array([[[p[axis] for axis in ("x", "y", "z")]
                      for p in row] for row in d], dtype=float)
    c = interpolate(data)
    a = basis(np.arange(10) / 9)
    reconstructed = np.einsum("ui,ijc,vj->uvc", a, c, a)
    error = np.linalg.norm(reconstructed - data, axis=2).max()
    print(f"Maximum interpolation error: {error:.3e}")
    output = Path(__file__).resolve().parent
    (output / "data").mkdir(parents=True, exist_ok=True)
    np.save(output / "data" / "display_control_points.npy", c)
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    for grid, color, label in ((data, "blue", "Data points d"),
                               (c, "red", "Control points c")):
        x, y, z = grid[..., 0], grid[..., 1], grid[..., 2]
        ax.scatter(x.ravel(), y.ravel(), z.ravel(), color=color, label=label)
        ax.plot_wireframe(x, y, z, color=color, alpha=0.5, linewidth=0.8)
    ax.set(xlabel="x", ylabel="y", zlabel="z",
           title="B-spline data and interpolated control grid")
    ax.set_box_aspect(np.ptp(np.concatenate((data, c)).reshape(-1, 3), axis=0))
    ax.legend()
    fig.tight_layout()
    (output / "figure").mkdir(parents=True, exist_ok=True)
    filename = output / "figure" / "display_control_points.png"
    fig.savefig(filename, dpi=180, bbox_inches="tight")
    print(f"Saved plot: {filename}")
    plt.show()


if __name__ == "__main__":
    main()
