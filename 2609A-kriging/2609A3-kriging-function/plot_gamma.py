#----------------------------------------------------------------------
# do not delete start
#----------------------------------------------------------------------

import os
import numpy as np

if "Path" in globals():
    SavePath = path
    print('Path in globals()', os.path.abspath(SavePath))
else:
    SavePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_t')
    os.makedirs(SavePath, exist_ok=True) 
    print('Path not in globals()', os.path.abspath(SavePath))    

    def mem(Name, Type=None, Size=None, Step=1):
        return np.load(f'data/{Name}.npy')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# do not delete end
#----------------------------------------------------------------------


from pathlib import Path

# import numpy as np
# import matplotlib.pyplot as plt

# Shared parameters. For exponential and Gaussian, r is a scale parameter.
c0, c, r = 0.0, 1.0, 1.0


def spherical(h, c0=0.0, c=1.0, r=1.0):
    """Spherical curve, reaching the sill c0 + c at h = r."""
    if r <= 0:
        raise ValueError('r must be positive')
    x = np.asarray(h) / r
    return c0 + c * np.where(x <= 1, 1.5 * x - 0.5 * x**3, 1.0)


def exponential(h, c0=0.0, c=1.0, r=1.0):
    """Exponential curve with scale r."""
    if r <= 0:
        raise ValueError('r must be positive')
    return c0 + c * (1 - np.exp(-np.asarray(h) / r))


def gaussian(h, c0=0.0, c=1.0, r=1.0):
    """Gaussian curve with scale r."""
    if r <= 0:
        raise ValueError('r must be positive')
    return c0 + c * (1 - np.exp(-(np.asarray(h) / r)**2))


h = np.linspace(0, 3 * r, 600)
models = [
    ('Spherical', spherical, 'royalblue',
        r'$\gamma(h)=c_0+c[1.5(h/r)-0.5(h/r)^3],\quad 0\leq h\leq r$'
        + '\n' + r'$\gamma(h)=c_0+c,\quad h>r$'),
    ('Exponential', exponential, 'darkorange',
        r'$\gamma(h)=c_0+c[1-e^{-h/r}]$'),
    ('Gaussian', gaussian, 'seagreen',
        r'$\gamma(h)=c_0+c[1-e^{-(h/r)^2}]$'),
]
fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
comparison = axes[1, 1]
for ax, (name, function, color, equation) in zip(axes.flat, models):
    values = function(h, c0, c, r)
    ax.plot(h, values, color=color, linewidth=2.5)
    ax.set_title(name + '\n' + equation, fontsize=11)
    comparison.plot(h, values, color=color, linewidth=2.5, label=name)

comparison.set_title('Comparison of all three models', fontsize=12)
comparison.legend(loc='lower right')
for ax in axes.flat:
    ax.set(xlabel='Distance h', ylabel=r'$\gamma(h)$', xlim=(0, 3 * r))
    ax.axhline(c0 + c, color='gray', linestyle='--', linewidth=1, alpha=0.6)
    ax.grid(True, alpha=0.3)

fig.suptitle(f'Three different functions ($c_0={c0:g},\\ c={c:g},\\ r={r:g}$)',
                fontsize=16)
fig.tight_layout()
# output_path = Path(__file__).resolve().parent / 'outputs' / 'plot_gamma.png'
# output_path.parent.mkdir(parents=True, exist_ok=True)
# fig.savefig(output_path, dpi=180)
# print(f'Saved plot to {output_path}')
if plt.get_backend().lower() != 'agg':
    plt.show()

#----------------------------------------------------------------------
# do not delete start
#----------------------------------------------------------------------

file = f'{SavePath}/01.KriginFunction.png';
plt.savefig(file, dpi=300, bbox_inches='tight')

print(os.path.abspath(file))

import subprocess
subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

# do not delete end
#----------------------------------------------------------------------

