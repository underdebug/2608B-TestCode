
import os
import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

d = MEM('t', None, None)

x = d['x']
y = d['y']
z = d['z']

print(x)
print(y)
print(z)    

fig = plt.figure(figsize=(10, 8), dpi=100)
ax = fig.add_subplot(111, projection='3d')
ax.plot(x.flatten(), y.flatten(), z.flatten(), 'b.')
ax.plot_wireframe(x, y, z)

# ax.set_box_aspect((
#     x.max() - x.min(),
#     y.max() - y.min(),
#     z.max() - z.min()
# ))
ax.set_box_aspect([np.ptp(a) for a in (x, y, z)])


file = f'mem/figure/01.points.png';
plt.savefig(file, dpi=300, bbox_inches='tight')
print(os.path.abspath(file))
plt.show()

