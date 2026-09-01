
#----------------------------------------------------------------------
a = info('a')
b = info('b')
c = info('c')
d = info('d')
e = cpu('e')
f = cpu('ff')
g = cpu('gg')

info('imgs')
for i in range(size('imgs')):
    info(f'imgs[{i}]')
    for j in range(size(f'imgs[{i}]')):
        data = cpu(f'imgs[{i}]')

img0 = cpu(f'imgs[0].rgb', 'uc', [480, 640, 3])
info('imgs[0]')
imtool(img0, 'imgs[0]')


info('corners')
for i in range(size('corners')):
    info(f'corners[{i}]')
    for j in range(size(f'corners[{i}]')):
        info(f'corners[{i}][{j}]')

info('descs')
for i in range(size('descs')):
    info(f'descs[{i}]')
    for j in range(size(f'descs[{i}]')):
        info(f'descs[{i}][{j}]')

info('R_prev')

data = cpu('R_prev')
print(data['m'])

data = cpu('R_prev.m', 'd', [3, 2])
print(data)
data = cpu('t_prev', 'd', 3)
print(data)

info('matches')
print(size('matches'))

n = size('matches')
data = cpu('matches', 'i', [n, 2])
print(data)

info('matches')
info('matches[0]')
data = cpu('matches[0]')
print(data)

info('idx')
print(size('idx'))
data = cpu('idx', 'd', size('idx'))
print(data)

data = cpu('E.m', 'd', [3, 3])
print(data)

info('T')
print(size('T.m'))
data = cpu('T.m', 'd', size('T.m'))
print(data)

info('pts')

data = cpu('pts', 'd', [8, 2])
print(data)

info('T1')

data = cpu('AtA', 'd', [9, 9])
print(data)

info('n1')


data = cpu('U.m', 'd', size('U.m'))
print(data)

data = cpu('S', 'd', size('S'))
print(data)

data = cpu('R_cur.m', 'd', size('R_cur.m'))
print(data)

print(size('R_cur.m'))

print(type('imgs[0].rgb'))
print(size('imgs[0].rgb'))

data = cpu('imgs[0].rgb')
print(data)

data = cpu('R_cur.m')
print(data)


type('R_cur.m')

p1 = cpu('p1')
p2 = cpu('p2')

#----------------------------------------------------------------------



Name = 'R'
PRINT(f'type({Name}) = ', type(Name))
PRINT(f'size({Name}) = ', size(Name))
PRINT(cpu(Name))

for i in range(2):
    Name = f'Rs[{i}]'
    PRINT(f'type({Name}) = ', type(Name))
    PRINT(f'size({Name}) = ', len(Name))
    PRINT(cpu(Name))


Name = 't'
PRINT(f'type({Name}) = ', type(Name))
PRINT(f'size({Name}) = ', size(Name))
PRINT(cpu(Name))

for i in range(2):
    Name = f'ts[{i}]'
    PRINT(f'type({Name}) = ', type(Name))
    PRINT(f'size({Name}) = ', len(Name))
    PRINT(cpu(Name))


Name = 'ts[ri]'
PRINT(f'type({Name}) = ', type(Name))
PRINT(f'size({Name}) = ', len(Name))
PRINT(cpu(Name))

    

Name = 'p1'
PRINT(f'type({Name}) = ', type(Name))
PRINT(f'size({Name}) = ', size(Name))
PRINT(cpu(Name))




Name = 'p1'
p1 = cpu(Name)

px = []
py = []
for i in range(size(Name)):
    px.append(p1[i]['x'])
    py.append(p1[i]['y'])

plt.figure()
plt.plot(px, py, '.')
plt.title(Name)




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




#----------------------------------------------------------------------



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

#----------------------------------------------------------------------
Name = 'cloud'
p = cpu(Name)

px = []
py = []
pz = []
for i in range(size(Name)):
    px.append(p[i]['x'])
    py.append(p[i]['y'])
    pz.append(p[i]['z'])

plt.figure()
plt.gcf().add_subplot(111, projection='3d')
plt.plot(px, py, pz, '.')
plt.title(Name)

plt.show()

#----------------------------------------------------------------------

#----------------------------------------------------------------------

#----------------------------------------------------------------------

#----------------------------------------------------------------------

#----------------------------------------------------------------------

#----------------------------------------------------------------------

#----------------------------------------------------------------------

#----------------------------------------------------------------------

#----------------------------------------------------------------------

#----------------------------------------------------------------------

#----------------------------------------------------------------------

