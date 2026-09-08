
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

dsx = mem('dsx', 'd', [n])
dsy = mem('dsy', 'd', [n])
dsv = mem('dsv', 'd', [n])

fig = plt.figure()

ax1 = fig.add_subplot(121)
ax1.plot(dsx, dsy, '.', markersize=1)

ax2 = fig.add_subplot(122, projection='3d')
ax2.plot(dsx, dsy, dsv, '.', markersize=2)

dsv0 = [0] * len(dsv)
ax2.plot(dsx, dsy, dsv0, '.', markersize=2)

#---------------------------------------------------------------

if "Path" in globals(): # c++ debug
    file = f'{SavePath}/02.main.png';
    plt.savefig(file, dpi=300, bbox_inches='tight')

    import subprocess
    subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

else: # python debug
    plt.show()
