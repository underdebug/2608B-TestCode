
vE = mem('vE')
print('vE', vE)

vecPair = mem('vecPair')
print('vecPair[0]', vecPair[0])
print('vecPair[1]', vecPair[1])
print('vecPair', vecPair)


e1 = mem('e1', None, 12)
print('e1.type', len(e1), type(e1))

s1 = mem('s1', None, 12)
print('s1 finish', s1)

a = mem('a', None, 12)
print('a1 finish', a)

a = mem('a', 'double', 12)
print('a2 finish', a)

b = mem('b', 'double', 2)
print('b1 finish', b)

b = mem('b', None, 12)
print('b2 finish', b)

bb = mem('b2', None, 12)
print('bb2 finish', bb)

h_data1 = mem('h_data1', 'float', 12)
print('h_data1', h_data1)

d_data1 = mem('d_data1', 'float', 12)
print('d_data1', d_data1)


pairVec = mem('pairVec', None, None)
print('pairVec', pairVec)

pairVec = mem('pairVec', None, 12)
print('pairVec', pairVec)

print('test finish')

