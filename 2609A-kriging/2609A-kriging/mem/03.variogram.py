

import os
import numpy as np

if "Path" in globals(): # c++ debug
    SavePath = Path

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
else: # python debug
    SavePath = 'data_t'
    os.makedirs(SavePath, exist_ok=True)     

    def mem(Name, Type=None, Size=None, Step=1):
        return np.load(f'data/{Name}.npy')

    import matplotlib
    matplotlib.use('QtAgg')
    import matplotlib.pyplot as plt

#---------------------------------------------------------------

N = 100  # parameter: max lag distance

# matches VariogramModel in main.cu: {'type': VG_SPHERICAL, 'nugget': 0.0, 'sill': 1.0, 'range': 30.0}
sill = 1.0
nugget = 0.0
range_ = 30.0
psill = sill - nugget

h = np.linspace(0, N, 2000)


def spherical(h):
    # m = {'type': 0, 'nugget': 0.0, 'sill': 1.0, 'range': 30.0}
    y = np.full_like(h, sill)
    mask = h < range_
    r = h[mask] / range_
    y[mask] = nugget + psill * (1.5 * r - 0.5 * r**3)
    y[h <= 0] = 0
    return y


def exponential(h):
    y = nugget + psill * (1 - np.exp(-3 * h / range_))
    y[h <= 0] = 0
    return y


def gaussian(h):
    r = h / range_
    y = nugget + psill * (1 - np.exp(-3 * r**2))
    y[h <= 0] = 0
    return y


fig, axes = plt.subplots(2, 2, figsize=(10, 8))

models = [
    ("Spherical", spherical),
    ("Exponential", exponential),
    ("Gaussian", gaussian),
]

for ax, (name, fn) in zip(axes.flat, models):
    ax.plot(h, fn(h), label=name)
    ax.axhline(sill, color="gray", linestyle="--", linewidth=1)
    ax.axhline(nugget, color="lightgray", linestyle=":", linewidth=1)
    ax.axvline(range_, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("h (lag distance)")
    ax.set_ylabel("y (semivariance)")
    ax.set_title(name)
    ax.grid(True, alpha=0.3)

ax4 = axes[1, 1]
for name, fn in models:
    ax4.plot(h, fn(h), label=name)
ax4.axhline(sill, color="gray", linestyle="--", linewidth=1, label="Sill")
ax4.axhline(nugget, color="lightgray", linestyle=":", linewidth=1, label="Nugget")
ax4.axvline(range_, color="gray", linestyle="--", linewidth=1)
ax4.set_xlabel("h (lag distance)")
ax4.set_ylabel("y (semivariance)")
ax4.set_title("All Models")
ax4.legend()
ax4.grid(True, alpha=0.3)

fig.suptitle("Variogram Models")
plt.tight_layout()

#---------------------------------------------------------------

if "Path" in globals(): # c++ debug
    file = f'{SavePath}/03.variogram.png';
    plt.savefig(file, dpi=300, bbox_inches='tight')

    import subprocess
    subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

else: # python debug
    plt.show()