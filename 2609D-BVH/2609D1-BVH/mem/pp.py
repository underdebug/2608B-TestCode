
triangles = mem('triangles[0]', None, 12)
print('triangles', triangles)

print(triangles.shape)


import gdb
para = gdb.parse_and_eval('triangles[0]')


-exec python import gdb; para=gdb.parse_and_eval('triangles._M_impl._M_start[1]'); gdb.write(str(para)+'\n')

para=gdb.parse_and_eval('triangles._M_impl._M_start[0]')
gdb.write(str(para)+'\n')

print(str(para))


import gdb
para = gdb.parse_and_eval('triangles')

for field in para.type.fields():
    gdb.write(field.name + " = " + str(para[field.name]) + "\n")

import gdb
tri = gdb.parse_and_eval(
    'triangles._M_impl._M_start[0]'
)

print(tri['v0'])
print(tri['v1'])
print(tri['v2'])



import gdb

data = []

for i in range(2):
    tri = gdb.parse_and_eval(
        f'triangles._M_impl._M_start[{i}]'
    )

    triangle = []

    for name in ['v0', 'v1', 'v2']:
        v = tri[name]

        triangle.append([
            float(v['x']),
            float(v['y']),
            float(v['z'])
        ])

    data.append(triangle)

gdb.write(str(data) + '\n')