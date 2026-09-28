

# import math
# import numpy as np

# def normalizeSize2(Size_mem, Size_read):   
#     if Size_read is None:
#         return Size_mem

#     Size_mem = np.atleast_1d(np.asarray(Size_mem))
#     Size_read = np.atleast_1d(np.asarray(Size_read))

#     Size_mem_p = math.prod(Size_mem)
#     Size_read_p = math.prod(Size_read)

#     if Size_mem_p >= Size_read_p:
#         return Size_read

#     Size = [1] * (len(Size_read))
#     for i in range(len(Size_read) - 1, -1, -1):
#         for j in range(Size_read[i]):
#             Size_new = Size.copy()
#             Size_new[i] = j + 1
#             Size_new_p = math.prod(Size_new)

#             if Size_new_p <= Size_mem_p:
#                 Size = Size_new
#             else:
#                 break
#     return Size

# Size_mem = 250
# Size_read = [2, 4, 3, 2]

# Size = normalizeSize2(Size_mem, Size_read)

# print('Size', Size)

points = mem('points', None, 12)
print('points', points)
