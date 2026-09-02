
m_points = mem('m_points', None, None)
print('m_points2', m_points)


m_points = mem('m_points', None, None)
print('m_points', type(m_points), m_points)


m_coords = m_points['m_coords']
print('m_coords', type(m_coords), m_coords)

x = m_coords[0::2]
y = m_coords[1::2]

x = m_points['m_coords'][0::2]
y = m_points['m_coords'][1::2]

m_coords = mem('m_points.m_coords', None, None)
print('m_coords', type(m_coords), m_coords)

m_coords = mem('m_points.m_coords', None, 12)
print('m_coords', type(m_coords), m_coords)


vec = mem('vec', None, 12)
print('vec', type(vec), vec)