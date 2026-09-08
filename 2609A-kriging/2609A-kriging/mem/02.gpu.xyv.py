
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

dsx = mem('sx', 'd', [512])
dsy = mem('sy', 'd', [512])
dsv = mem('v', 'd', [512])

# plt.figure()
# plt.plot(dsx, dsy, '.', markersize=1)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.plot(dsx, dsy, dsv, 'r.', markersize=2)

dsv0 = [0] * 512
ax.plot(dsx, dsy, dsv0, 'g.', markersize=2)

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