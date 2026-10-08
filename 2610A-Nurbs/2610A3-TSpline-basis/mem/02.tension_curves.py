from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def tension_curve(t, rho):
    if rho == 0:
        return t  # Limit of sinh(rho * t) / sinh(rho) as rho approaches zero.
    return np.sinh(rho * t) / np.sinh(rho)


t = np.linspace(0, 1, 10)
rho_values = [0.1, 1.0, 10.0]

fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
for rho in rho_values:
    label = fr"$\rho = {rho:g}$"
    (line,) = axes[0].plot(t, np.sinh(rho * t), lw=2, label=label)
    color = line.get_color()
    axes[1].axhline(np.sinh(rho), color=color, lw=2, label=label)
    axes[2].plot(t, tension_curve(t, rho), color=color, lw=2, label=label)

expressions = [
    r"$\sinh(\rho t)$",
    r"$\sinh(\rho)$",
    r"$\sinh(\rho t) / \sinh(\rho)$",
]
for ax, expression in zip(axes, expressions):
    ax.set(xlim=(t[0], t[-1]), ylabel="Value", title=expression)
    ax.grid(alpha=0.25)
    ax.legend()
axes[-1].set_xlabel("t")
fig.tight_layout()

Path("figure").mkdir(exist_ok=True)
fig.savefig("figure/tension_curves.png", dpi=180)
plt.show()
