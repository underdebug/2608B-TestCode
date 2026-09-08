

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
# Two breakpoints needed:
#   main.cu:324 (A built, before invertMatrix) -> mem('A', ...) then save it as A_orig
#   main.cu:330 (right after invertMatrix)     -> mem('A', ...) overwrites A.npy with Ainv
# See mem/06.dump_A.gdb for a scripted way to do both in one run.

N = 11  # nSamples + 1

A    = mem('A_orig', 'd', [N * N]).reshape(N, N)   # original semivariogram matrix
Ainv = mem('A',      'd', [N * N]).reshape(N, N)   # A after invertMatrix() (in-place)

I_check = A @ Ainv
err = I_check - np.eye(N)
maxErr = np.max(np.abs(err))

fig, axes = plt.subplots(2, 2, figsize=(11, 9))

vmax = np.max(np.abs(A[:-1, :-1]))
im = axes[0, 0].imshow(A, cmap='viridis', vmin=0, vmax=vmax)
fig.colorbar(im, ax=axes[0, 0])
axes[0, 0].set_title('A (semivariogram + Lagrange border)')

im = axes[0, 1].imshow(Ainv, cmap='coolwarm')
fig.colorbar(im, ax=axes[0, 1])
axes[0, 1].set_title(r'$A^{-1}$')

im = axes[1, 0].imshow(I_check, cmap='coolwarm', vmin=-1, vmax=1)
fig.colorbar(im, ax=axes[1, 0])
axes[1, 0].set_title(r'$A \cdot A^{-1}$ (should be I)')

im = axes[1, 1].imshow(np.abs(err), cmap='inferno')
fig.colorbar(im, ax=axes[1, 1])
axes[1, 1].set_title(f'|A A^-1 - I|  (max {maxErr:.2e})')

fig.suptitle('Kriging matrix inversion check')
plt.tight_layout()

#---------------------------------------------------------------

if "Path" in globals(): # c++ debug
    file = f'{SavePath}/06.A_Ainv.png'
    plt.savefig(file, dpi=300, bbox_inches='tight')

    import subprocess
    subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

else: # python debug
    file = f'{SavePath}/06.A_Ainv.png'
    plt.savefig(file, dpi=150, bbox_inches='tight')
    print(file)
    print('max |A Ainv - I| =', maxErr)
