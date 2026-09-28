import numpy as np


class L(list):
    def __init__(self, data):
        self._single_record = isinstance(data, dict)
        super().__init__([data] if self._single_record else data)

    def __getitem__(self, key):
        if isinstance(key, str):
            fields = key.split('.')
            values = []

            for record in self:
                value = record
                for field in fields:
                    value = value[field]
                values.append(value)

            return values[0] if self._single_record else np.asarray(values)

        return super().__getitem__(key)

    def __repr__(self):
        if self._single_record:
            return repr(super().__getitem__(0))
        return super().__repr__()


# 列表：收集所有三角形的字段
triangles = mem('triangles', None, 12)
print('triangles', triangles)

print(len(L(triangles)))

v0_x = L(triangles)['v0.x']
v0_y = L(triangles)['v0.y']

print('v0.x', v0_x)
print('v0.y', v0_y)

# 字典：直接读取字段
m_points = L(mem('m_points', None, 12))
print('m_points', m_points)
print('m_coords', m_points['m_coords'])