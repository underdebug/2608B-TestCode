
import os
import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

d = MEM('data', None, None)

dx = d['x']
dy = d['y']
dz = d['z']

fig = plt.figure(figsize=(10, 8), dpi=100)
ax = fig.add_subplot(111, projection='3d')
ax.plot(dx.flatten(), dy.flatten(), dz.flatten(), 'b.')
ax.plot_wireframe(dx, dy, dz)


c = MEM('control', None, None)

cx = c['x']
cy = c['y']
cz = c['z']

ax.plot(cx.flatten(), cy.flatten(), cz.flatten(), 'r.')
# ax.plot_wireframe(cx, cy, cz, 'r.')


# ax.set_box_aspect((
#     x.max() - x.min(),
#     y.max() - y.min(),
#     z.max() - z.min()
# ))
ax.set_box_aspect([np.ptp(a) for a in (dx, dy, dz)])


file = f'mem/figure/05.data_control.png';
plt.savefig(file, dpi=300, bbox_inches='tight')
print(os.path.abspath(file))
plt.show()

