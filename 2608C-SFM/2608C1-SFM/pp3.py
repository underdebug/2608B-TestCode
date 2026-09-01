

Name = 'p2'
p1 = cpu(Name)

px = []
py = []
for i in range(size(Name)):
    px.append(p1[i]['x'])
    py.append(p1[i]['y'])

plt.figure()
plt.plot(px, py, '.')

plt.title('p2')

plt.gcf().canvas.manager.window.wm_geometry("1000x750")
plt.gcf().canvas.manager.set_window_title('p2')
plt.gcf().canvas.toolbar.pan() 

plt.show()


G = [None] * 4
for i in range(4):
    G[i] = cpu(f'G[{i}]')

plt.figure()
plt.plot(G[0], 'b-')
plt.plot(G[1], 'r-')
plt.plot(G[2], 'g-')
plt.plot(G[3], 'k-')

plt.title('G')
plt.show()

