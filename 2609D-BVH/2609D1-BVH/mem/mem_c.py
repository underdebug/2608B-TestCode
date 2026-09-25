# import inspect

# def print(*args, **kwargs):
#     print('LINE', inspect.currentframe().f_back.f_lineno, *args, **kwargs)

e1 = mem('e1', None, 12)
print('e1.type', len(e1), type(e1), e1)

s1 = mem('s1', None, 12)
print('s1 finish', s1)

a = mem('a', None, 2)
print('a1 finish', a)

a = mem('a', 'double', 2)
print('a2 finish', a)

print(inspect.currentframe().f_back.f_lineno, 'b')
b = mem('b', 'double', 2)
print('b1 finish', b)

b = mem('b', None, 12)
print('b2 finish', b)

print('m_coords')
bb = mem('b2', None, 12)
print('bb2 finish', bb)

print('h_data1')
h_data1 = mem('h_data1', 'float', 12)
print('h_data1', h_data1)

d_data1 = mem('d_data1', 'float', 12)
print('d_data1', d_data1)

m_points = mem('m_points', None, 12)
print('m_points', m_points)

m_points = mem('m_points', None, None)
print('m_points2', m_points)

print('m_coords')
m_coords = m_points['m_coords']
print('m_coords', type(m_coords), m_coords)

x = m_coords[0::2]
y = m_coords[1::2]

x = m_points['m_coords'][0::2]
y = m_points['m_coords'][1::2]

print('triangles')
triangles = mem('triangles', 'f', [2, 2, 3])
print('triangles', triangles)

triangles = mem('triangles', None, 12)
print(type(triangles))
print('triangles', triangles)
print('triangles', triangles['v0.x'])
# print('triangles', triangles.item()['v0.x'])


points = mem('points', None, 12)
print('points', points)

print('type(points)', type(points))

# print('points', points.item()['x'])

results = {}
results.setdefault('a.b', []).append(1)
results.setdefault('a.b', []).append(2)
print(type(results))
print('results', results)

results = {k: np.array(v) for k, v in results.items()}
results = np.asarray(results)

print('results', results)

