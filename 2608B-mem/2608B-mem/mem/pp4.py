
import os

SavePath = 'mem/data'

os.makedirs(SavePath, exist_ok=True) 

#-----------------------------------------------------------------

import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

#coords = mem('coords')
coords = mem('m_points.m_coords')

n = mem('n')
hull_start = mem('hull_start')
hull_prev = mem('hull_prev')
hull_next = mem('hull_next')
hull_tri = mem('hull_tri')

print('n', n)
print('hull_start', hull_start)
print('hull_prev', hull_prev)
print('hull_next', hull_next)
print('hull_tri', hull_tri)

# points

x = np.array(coords[0::2])
y = np.array(coords[1::2])

print('x', x)
print('y', y)

plt.figure()
plt.plot(x, y, '.')

for i, (xi, yi) in enumerate(zip(x, y)):
    plt.text(xi, yi, str(i))

# triangles
triangles = mem('triangles')

print(f'triangles({len(triangles)}), {triangles}')

rng = np.random.default_rng(0) 

for i in range(0, len(triangles), 3):
    tri = triangles[i:i + 3]
    xx = x[tri]
    yy = y[tri]

    plt.text(xx.mean(), yy.mean(), str(i // 3),
             ha='center', va='center', fontsize=8)

    plt.fill(xx, yy, facecolor=rng.random(3), alpha=0.5, edgecolor='none')

# hull

node = hull_start
hull = [node]
while (node := hull_next[node]) != hull_start:
    hull.append(node)

print('type(hull)', type(hull))

hull = np.array(hull, dtype=np.int32)

print('type(hull)', type(hull))

print('hull', hull)

xx = x[hull]
yy = y[hull]

print('xx', xx)
print('yy', yy)

plt.plot(np.r_[xx, xx[0]], np.r_[yy, yy[0]], 'b.-')
plt.plot(xx[0], yy[0], 'r*')
plt.plot(xx[-1], yy[-1], 'r+')

k = mem('k')

file = f'{SavePath}/triangles[{k}].png';
plt.savefig(file, dpi=300, bbox_inches='tight')

import subprocess
subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

