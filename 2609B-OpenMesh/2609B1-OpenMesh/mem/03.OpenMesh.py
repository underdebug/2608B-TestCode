
#----------------------------------------------------------------------
# do not delete start
#----------------------------------------------------------------------

import os
import numpy as np

if "PATH" in globals():
    SavePath = PATH
    print('Path in globals()', os.path.abspath(SavePath))
else:
    SavePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_t')
    os.makedirs(SavePath, exist_ok=True) 
    print('Path not in globals()', os.path.abspath(SavePath))    

    def mem(Name, Type=None, Size=None, Step=1):
        return np.load(f'data/{Name}.npy')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# do not delete end
#----------------------------------------------------------------------

coords = mem('originalCoords')
triangles = mem('originalFaceIndices')

coords2 = mem('originalCoords2')
triangles2 = mem('originalFaceIndices2')

fig, axes = plt.subplots(1, 2, figsize=(12, 6))

def draw_mesh(ax, coords, triangles):
    x = coords[0::2]
    y = coords[1::2]

    print('len(x)', len(x))
    print('len(y)', len(y))

    ax.plot(x, y, '.')

    for i, (xi, yi) in enumerate(zip(x, y)):
        ax.text(xi, yi, str(i), fontsize=6)

    # triangles: flat vertex indices into x, y, 3 per face
    print(f'triangles({len(triangles)}), {triangles}')

    rng = np.random.default_rng(0)

    for i in range(0, len(triangles), 3):
        tri = triangles[i:i + 3]
        xx = x[tri]
        yy = y[tri]

        ax.fill(xx, yy, facecolor=rng.random(3), alpha=0.5, edgecolor='none')
        ax.plot(np.append(xx, xx[0]), np.append(yy, yy[0]), color='r', lw=1.0)

draw_mesh(axes[0], coords, triangles)
draw_mesh(axes[1], coords2, triangles2)


#----------------------------------------------------------------------
# do not delete start
#----------------------------------------------------------------------

file = f'{SavePath}/01.main2.png';
plt.savefig(file, dpi=300, bbox_inches='tight')

print(os.path.abspath(file))

import subprocess
subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

# do not delete end
#----------------------------------------------------------------------
