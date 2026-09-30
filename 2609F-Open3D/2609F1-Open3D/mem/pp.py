"""Display sphere2.ply using a basic Matplotlib 3D scatter plot."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def read_ascii_ply(filename):
    """Read XYZ and optional RGB from an ASCII PLY with vertices first."""
    with filename.open("r", encoding="ascii") as stream:
        if stream.readline().strip() != "ply":
            raise ValueError("Expected a PLY file")
        if stream.readline().strip() != "format ascii 1.0":
            raise ValueError("This viewer supports ASCII PLY files only")

        count = None
        element = None
        properties = []
        for line in stream:
            fields = line.split()
            if not fields:
                continue
            if fields[0] == "end_header":
                break
            if fields[0] == "element":
                element = fields[1]
                if count is None and element != "vertex":
                    raise ValueError("Expected vertices as the first PLY element")
                if element == "vertex":
                    count = int(fields[2])
            elif fields[0] == "property" and element == "vertex":
                if fields[1] == "list":
                    raise ValueError("List properties on vertices are unsupported")
                properties.append(fields[2])
        else:
            raise ValueError("Missing PLY end_header")

        if count is None or count <= 0:
            raise ValueError("No vertices in the PLY file")
        data = np.loadtxt(stream, max_rows=count, ndmin=2)
        if data.shape != (count, len(properties)):
            raise ValueError("PLY vertex data does not match its header")
        points = data[:, [properties.index(axis) for axis in ("x", "y", "z")]]
        if not np.isfinite(points).all():
            raise ValueError("Point coordinates must be finite")
        colors = "steelblue"
        if all(name in properties for name in ("red", "green", "blue")):
            colors = data[:, [properties.index(c) for c in ("red", "green", "blue")]]
            colors = np.clip(colors / 255.0, 0.0, 1.0)
        return points, colors


def main():
    filename = Path(__file__).resolve().parent.parent / "sphere2.ply"
    points, colors = read_ascii_ply(filename)
    print(f"Loaded {len(points):,} points from {filename}", flush=True)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(*points.T, c=colors, s=2, depthshade=False)
    ax.set(xlabel="X", ylabel="Y", zlabel="Z", title="Noisy thick sphere — 100,000 points")

    # Equal axis scales preserve the shapes while rotating the plot.
    center = (points.min(axis=0) + points.max(axis=0)) / 2
    radius = max(float(np.ptp(points, axis=0).max()) / 2, 0.01)
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=25, azim=-55)
    fig.tight_layout()
    output = Path(__file__).resolve().parent / "data" / "sphere2.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, bbox_inches="tight")
    print(f"Saved {output}", flush=True)
    plt.show()


if __name__ == "__main__":
    main()
