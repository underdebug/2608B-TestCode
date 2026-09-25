
import gdb

# Get std::vector<Triangle>
vec = gdb.parse_and_eval('triangles')

# Get vector begin/end pointers
start = vec['_M_impl']['_M_start']
finish = vec['_M_impl']['_M_finish']

# Number of triangles
size = int(finish - start)

gdb.write("Triangle count = " + str(size) + "\n")

data = []

# Loop through all triangles
for i in range(size):

    # Get Triangle i
    tri = start[i]

    triangle_data = []

    # Automatically get Triangle members: v0, v1, v2, ...
    for field in tri.type.fields():

        name = field.name

        # Skip unnamed fields
        if name is None:
            continue

        # Get Vec3
        v = tri[name]

        # Automatically get Vec3 members: x, y, z
        vec_data = []

        for vf in v.type.fields():

            vname = vf.name

            if vname is None:
                continue

            value = float(v[vname])

            vec_data.append(value)

        triangle_data.append(vec_data)

    data.append(triangle_data)

# Print result
gdb.write(str(data) + "\n")