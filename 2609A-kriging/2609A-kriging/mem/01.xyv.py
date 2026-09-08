
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
n = 10

A = mem('A', None, [n+1, n+1])

print('A', A)

# plt.figure()
# plt.plot(dsx, dsy, '.', markersize=1)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.plot(dsx, dsy, dsv, '.', markersize=2)

dsv0 = [0] * len(dsv)
ax.plot(dsx, dsy, dsv0, '.', markersize=2)

# for i in range(512):
#     x = dsx[i]
#     y = dsy[i]
#     v = dsv[i]
#     ax.plot([x, x], [y, y], [0, v], '.')

#---------------------------------------------------------------

if "Path" in globals(): # c++ debug
    file = f'{SavePath}/02.main.png';
    plt.savefig(file, dpi=300, bbox_inches='tight')

    import subprocess
    subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

else: # python debug
    plt.show()