
import os
import numpy as np

if "Path" in globals():
    SavePath = Path
else:
    SavePath = 'data_t'
    os.makedirs(SavePath, exist_ok=True)     

    def mem(Name, Type=None, Size=None, Step=1):
        return np.load(f'data/{Name}.npy')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

#----------------------------------------------------------------------

# --- read data (mem is your helper, untouched) ---
numSamples = mem('numSamples')
d_sx     = mem('d_sx', 'f', numSamples)
d_sy     = mem('d_sy', 'f', numSamples)
d_values = mem('d_values', 'f', numSamples)

numQueries = mem('numQueries')
d_qx     = mem('d_qx', 'f', numQueries)
d_qy     = mem('d_qy', 'f', numQueries)
d_output = mem('d_output', 'f', numQueries)

fig = plt.figure()

# --- subplot 1: 2D scatter with value labels ---
ax1 = fig.add_subplot(121)
ax1.plot(d_sx, d_sy, '*')
for i in range(numSamples):
    ax1.text(d_sx[i], d_sy[i], f'{d_values[i]:.1f}')

ax1.plot(d_qx, d_qy, 'r*')
for i in range(numQueries):
    ax1.text(d_qx[i], d_qy[i], f'{d_output[i]:.1f}')
ax1.set_title('Sample locations')


# --- subplot 2: 3D stems, value as height ---
ax2 = fig.add_subplot(122, projection='3d')
for x, y, v in zip(d_sx, d_sy, d_values):
    ax2.plot([x, x], [y, y], [0, v], '-', color='gray')  # stem to baseline
ax2.plot(d_sx, d_sy, d_values, '*')                      # marker on top

for x, y, v in zip(d_qx, d_qy, d_output):
    ax2.plot([x, x], [y, y], [0, v], 'r-', color='gray')  # stem to baseline
ax2.plot(d_qx, d_qy, d_output, 'r*')                      # marker on top
ax2.set_title('Sample values')


#----------------------------------------------------------------------

file = f'{SavePath}/01.main.png';
plt.savefig(file, dpi=300, bbox_inches='tight')

print(file)

import subprocess
subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

