

e1 = mem('e1', None, 12)
print('e1.type', len(e1), type(e1), e1.tolist())

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

m_points = mem('m_points', None, 12)
print('m_points', m_points)

m_points = mem('m_points', None, None)
print('m_points2', m_points)


m_coords = m_points['m_coords']
print('m_coords', type(m_coords), m_coords)

x = m_coords[0::2]
y = m_coords[1::2]

x = m_points['m_coords'][0::2]
y = m_points['m_coords'][1::2]