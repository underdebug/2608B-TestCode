

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
# Break after "validation" block in main.cu (once hVal/hVar/hFast/hsx/hsy/hsv
# /hgx/hgy exist) and press the mem keybinding, or just run this file after
# dumping those variables with mem().

GW, GH = 10, 10  # must match main.cu

sx = mem('hsx', 'd', [10])
sy = mem('hsy', 'd', [10])
sv = mem('hsv', 'd', [10])

gx = mem('hgx', 'd', [GW * GH])
gy = mem('hgy', 'd', [GW * GH])

val  = mem('hVal',  'd', [GW * GH])   # krigeExactKernel estimate
var  = mem('hVar',  'd', [GW * GH])   # kriging variance
fast = mem('hFast', 'd', [GW * GH])   # krigeFastKernel estimate

valGrid  = np.asarray(val).reshape(GH, GW)
varGrid  = np.asarray(var).reshape(GH, GW)
diffGrid = np.asarray(val).reshape(GH, GW) - np.asarray(fast).reshape(GH, GW)

extent = [gx.min(), gx.max(), gy.min(), gy.max()]

fig, axes = plt.subplots(2, 2, figsize=(11, 9))

# ---- estimate heatmap + samples -----------------------------------------
ax = axes[0, 0]
im = ax.imshow(valGrid, origin='lower', extent=extent, cmap='viridis', aspect='auto')
sc = ax.scatter(sx, sy, c=sv, cmap='viridis', edgecolors='white', linewidths=1, s=60)
fig.colorbar(im, ax=ax, label='z estimate')
ax.set_title('Kriging estimate (exact kernel)')
ax.set_xlabel('x')
ax.set_ylabel('y')

# ---- variance heatmap -----------------------------------------------------
ax = axes[0, 1]
im = ax.imshow(varGrid, origin='lower', extent=extent, cmap='magma', aspect='auto')
ax.scatter(sx, sy, c='black', s=40, marker='x')
fig.colorbar(im, ax=ax, label='kriging variance')
ax.set_title('Kriging variance (0 at samples)')
ax.set_xlabel('x')
ax.set_ylabel('y')

# ---- exact vs fast kernel difference --------------------------------------
ax = axes[1, 0]
im = ax.imshow(diffGrid, origin='lower', extent=extent, cmap='coolwarm', aspect='auto')
fig.colorbar(im, ax=ax, label='exact - fast')
ax.set_title(f'Exact vs fast kernel diff (max {np.max(np.abs(diffGrid)):.2e})')
ax.set_xlabel('x')
ax.set_ylabel('y')

# ---- sample values (input data) -------------------------------------------
ax = axes[1, 1]
sc = ax.scatter(sx, sy, c=sv, cmap='viridis', s=120, edgecolors='black')
for i, (x, y, v) in enumerate(zip(sx, sy, sv)):
    ax.annotate(f'{v:.1f}', (x, y), textcoords='offset points', xytext=(5, 5), fontsize=8)
fig.colorbar(sc, ax=ax, label='sample value')
ax.set_title(f'{len(sx)} input samples')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_xlim(extent[0], extent[1])
ax.set_ylim(extent[2], extent[3])

fig.suptitle('Ordinary Kriging Result')
plt.tight_layout()

#---------------------------------------------------------------

if "Path" in globals(): # c++ debug
    file = f'{SavePath}/05.kriging_result.png'
    plt.savefig(file, dpi=300, bbox_inches='tight')

    import subprocess
    subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

else: # python debug
    file = f'{SavePath}/05.kriging_result.png'
    plt.savefig(file, dpi=150, bbox_inches='tight')
    print(file)
