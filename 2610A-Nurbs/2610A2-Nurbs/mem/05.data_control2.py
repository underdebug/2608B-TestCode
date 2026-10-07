
import os
import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

d = MEM('data', None, None)

dx = d['x']
dy = d['y']
dz = d['z']

c = MEM('control', None, None)

cx = c['x']
cy = c['y']
cz = c['z']


fig = plt.figure(figsize=(10, 8), dpi=100)
ax = fig.add_subplot(221, projection='3d')
ax.plot(dx.flatten(), dy.flatten(), dz.flatten(), 'b.')
ax.plot_wireframe(dx, dy, dz)

ax.plot(cx.flatten(), cy.flatten(), cz.flatten(), 'r.')
ax.plot_wireframe(cx, cy, cz)

ax.set_box_aspect([np.ptp(a) for a in (dx, dy, dz)])

ax = fig.add_subplot(222)
ax.plot(dx.flatten() - cx.flatten(), 'b.')

ax = fig.add_subplot(223)
ax.plot(dy.flatten() - cy.flatten(), 'b.')

ax = fig.add_subplot(224)
ax.plot(dz.flatten() - cz.flatten(), 'b.')


file = f'mem/figure/05.data_control2.png';
plt.savefig(file, dpi=300, bbox_inches='tight')
print(os.path.abspath(file))
plt.show()

