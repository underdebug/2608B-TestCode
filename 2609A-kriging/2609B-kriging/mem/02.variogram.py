
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


# A = mem('A', 'f', [13, 13])
# print('A = ', A)

h = mem('h')
gamma = mem('gamma')
variogram = mem('variogram')

H = mem('H')
V = mem('V')

#----------------------------------------------------------------------

fig = plt.figure()

ax1 = fig.add_subplot(121)
ax1.plot(h, gamma, 'bo-', label='empirical gamma*(h)')
ax1.plot(h, variogram, 'rs-', label='model variogram(h)')
ax1.set_xlabel('h (lag distance)')
ax1.set_ylabel('semivariance')
ax1.set_title('Empirical vs model semivariogram')
ax1.legend()

ax2 = fig.add_subplot(122)
ax2.plot(H, V, 'g-', label='variogram(H)')
ax2.set_xlabel('H (lag distance)')
ax2.set_ylabel('semivariance')
ax2.set_title('Model semivariogram')
ax2.legend()

#----------------------------------------------------------------------

file = f'{SavePath}/02.variogram.png';
plt.savefig(file, dpi=300, bbox_inches='tight')

print(file)

import subprocess
subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

