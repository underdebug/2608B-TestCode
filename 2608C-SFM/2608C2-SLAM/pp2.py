
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

scanIdx = int(mem('scanIdx'))
n = int(mem('n'))
sz = size('h_map')

d_local = mem('d_local', 'f', [n, 2])
x1, y1 = d_local[:, 0], d_local[:, 1]

d_transformed = mem('d_transformed', 'f', [n, 2])
x2, y2 = d_transformed[:, 0], d_transformed[:, 1]

d_map = mem('d_map', 'f', [sz, 2])
x3, y3 = d_map[:, 0], d_map[:, 1]

fig, axes = plt.subplots(2, 2, figsize=(10, 10), sharex=True, sharey=True)

axes[0][0].plot(x1, y1, 'b.')
axes[0][1].plot(x2, y2, 'r.')
axes[1][0].plot(x3, y3, 'r.')
axes[1][1].axis('off')

fig.savefig(f'mem/figure[{scanIdx}].png', dpi=150, bbox_inches='tight')
plt.close(fig)

