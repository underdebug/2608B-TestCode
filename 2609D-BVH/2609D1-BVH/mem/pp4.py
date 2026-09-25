import gdb

# Get std::vector<Vec3_t>
vec = gdb.parse_and_eval('points')

# Get vector begin/end
start = vec['_M_impl']['_M_start']
finish = vec['_M_impl']['_M_finish']

# Number of Vec3_t
size = int(finish - start)

gdb.write("Point count = " + str(size) + "\n")

data = []

for i in range(size):

    # Get Vec3_t
    v = start[i]

    vec_data = []

    # Automatically get x, y, z
    for field in v.type.fields():

        name = field.name

        if name is None:
            continue

        value = float(v[name])

        vec_data.append(value)

    data.append(vec_data)

gdb.write(str(data) + "\n")