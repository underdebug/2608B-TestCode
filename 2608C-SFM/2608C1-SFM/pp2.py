

Name = 'cloud'
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




Name = 'E'
p = cpu(Name)
print(p)


V = cpu('U')
print(V)

print(V.transpose())

print(V @ V.transpose())

print(V.transpose() @ V)




print(U.transpose() * U)


Name = 'U'
U = cpu(Name)
print(U)

print(U.transpose() * U)



E = cpu('E')
print(E)

U, S, Vt = np.linalg.svd(E)

print("U =\n", U)
print("S =", S)
print("V^T =\n", Vt)


print("U^T @ U =\n", U.T @ U)




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





Name = 'p2'
p1 = cpu(Name)

print(p1)

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




