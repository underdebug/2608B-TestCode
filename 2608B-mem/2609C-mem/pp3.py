import numpy as np


class L(list):
     def __getitem__(self, key):
        if isinstance(key, str):
            fields = key.split('.')
            values = []
            for record in self:
                value = record
                for field in fields:
                    value = value[field]
                values.append(value)
            return np.asarray(values)
        return super().__getitem__(key)


   def __getitem__(self, key):
        if isinstance(key, str):
            fields = key.split('.')

            def get_field(record):
                for field in fields:
                    record = record[field]
                return record

            if isinstance(self.data, dict):
                return get_field(self.data)
            return np.asarray([get_field(record) for record in self.data])
        return self.data[key]


triangles = L(mem('triangles', None, 12))
print('triangles', triangles)

v0_x = triangles['v0.x']
v0_y = triangles['v0.y']

print('v0.x', v0_x)
print('v0.y', v0_y)
