#---------------------------------------------------------------
# Do not remove beloving
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

n = 11

A = mem('A_Old', 'd', [n, n])
print('A', A)

A_1 = mem('A', 'd', [n, n])
print('A_1', A_1)

print('A * A_1', A @ A_1)

hsv = mem('hsv', 'd', [n, 1])
print('hsv', hsv)

hv = A_1 @ hsv
print('hv', hv)


dVal = mem('dVal', 'd', [n, n])
print('dVal', dVal)


hFast = mem('hFast', 'd', [n, n])
print('hFast', hFast)


outVal = mem('outVal', None, [12, 12])
print('outVal', outVal)


fig = plt.figure()

ax1 = fig.add_subplot(121)
ax1.plot(dsx, dsy, '.', markersize=1)

ax2 = fig.add_subplot(122, projection='3d')
ax2.plot(dsx, dsy, dsv, '.', markersize=2)

dsv0 = [0] * len(dsv)
ax2.plot(dsx, dsy, dsv0, '.', markersize=2)

#---------------------------------------------------------------
# Do not remove beloving
# if "Path" in globals(): # c++ debug
#     file = f'{SavePath}/02.main.png';
#     plt.savefig(file, dpi=300, bbox_inches='tight')

#     import subprocess
#     subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

# else: # python debug
#     plt.show()
#---------------------------------------------------------------
