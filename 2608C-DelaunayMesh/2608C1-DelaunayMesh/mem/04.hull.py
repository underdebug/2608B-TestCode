
#----------------------------------------------------------------------

import os
import numpy as np

if "Path" in globals():
    SavePath = Path
else:
    def mem(Name, Type=None, Size=None, Step=1):
        return np.load(f'data/{Name}.npy')

    SavePath = 'data_t'
    os.makedirs(SavePath, exist_ok=True)     

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np

#----------------------------------------------------------------------

hull_start = mem('hull_start')
print('hull_start', hull_start)

start = mem('start')
print('start', start)

m_points = mem('m_points', None, None)
# print('m_points', type(m_points), m_points)

m_coords = m_points['m_coords']
# print('m_coords', type(m_coords), m_coords)

x = m_coords[0::2]
y = m_coords[1::2]

x = m_points['m_coords'][0::2]
y = m_points['m_coords'][1::2]

print('len(x)', len(x))
print('len(y)', len(y))

plt.figure()
plt.plot(x, y, '.')


hull_next = mem('hull_next', None, None) 
hull_start = mem('hull_start', None, None) 
start = mem('start', None, None) 
print('start', start)

# print('hull_next', hull_next)

hull = [hull_start]
next = hull_next[hull_start] 

n = 0
while next != hull_start and n < 50:
    hull.append(next)
    next = hull_next[next] 
    n = n + 1

print('hull 1', hull)

INVALID_INDEX = 2**64 - 1

pairs = ' '.join(f'<{i}, {v}>' for i, v in enumerate(hull_next) if v != INVALID_INDEX)
print(f'hull: {pairs}')


# hull = [start]
# next = hull_next[start] 

# n = 0
# while next != start and n < 50:
#     hull.append(next)
#     next = hull_next[next] 
#     n = n + 1

# print('hull 2', hull)

# xx = x[hull]
# yy = y[hull]


m_hash_size = mem('m_hash_size', None, None) 
m_hash = mem('m_hash', None, m_hash_size) 
# print('m_hash', m_hash_size, m_hash)

INVALID_INDEX = 2**64 - 1

pairs = ' '.join(f'<{i}, {v}>' for i, v in enumerate(m_hash) if v != INVALID_INDEX)
print(f'm_hash {m_hash_size}: {pairs}')

# plt.plot(xx, yy, 'r.-')



# file = f'{SavePath}/04.hull.png';
# plt.savefig(file, dpi=300, bbox_inches='tight')

# import subprocess
# subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)



# return

# for i, (xi, yi) in enumerate(zip(x, y)):
#     plt.text(xi, yi, str(i), fontsize=5)

# # triangles
# triangles = mem('triangles')

# print(f'triangles({len(triangles)}), {triangles}')

# rng = np.random.default_rng(0) 

# print('size(len(triangles))', len(triangles))

# for i in range(0, len(triangles), 3):
#     tri = triangles[i:i + 3]
#     print(f'tri[{i}]', tri)
#     # xx = x[tri]
#     # yy = y[tri]

#     # plt.text(xx.mean(), yy.mean(), str(i // 3),
#     #          ha='center', va='center', fontsize=8)

#     # plt.fill(xx, yy, facecolor=rng.random(3), alpha=0.5, edgecolor='none')
#     # plt.plot(np.append(xx, xx[0]), np.append(yy, yy[0]), color='r', lw=1.0)

# # # halfedges
# # halfedges = mem('halfedges')

# # INVALID = np.iinfo(halfedges.dtype).max
# # he = halfedges.astype(np.int64)
# # he[halfedges == INVALID] = -1
# # halfedges = he

# # print(f'halfedges({len(halfedges)}), {halfedges}')

# # for e in range(0, len(triangles)):
# #     p = triangles[e]

# #     ne = e + 1 if e % 3 != 2 else e - 2
    
# #     q = triangles[ne]

# #     he = halfedges[e]

# #     t = 0.3
# #     x0 = x[p] * (1 - t) + x[q] * t
# #     y0 = y[p] * (1 - t) + y[q] * t

# #     plt.text(x0, y0, f'{e}/{he}')


# file = f'{SavePath}/04.hull.png';
# plt.savefig(file, dpi=300, bbox_inches='tight')

# import subprocess
# # subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

