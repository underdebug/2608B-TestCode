


k = mem('k', 'd', [2, 3])
print('k', k)

d = MEM('d', None, None)

x = d['x']
y = d['y']
z = d['z']

print(d['x'])


print(d.shape)

print(f'{d:0.3f}')



def cpu_stdarray(para, Type=None, Size=None):
    ftype = para.type.strip_typedefs().unqualified()
        
    Size_t = int(ftype.template_argument(1))
    if Size_t == 0:
        return np.array([])

    if Type is not None and Size is not None: # top priority
        return cpu_(para['_M_elems'], Type, Size)

    if Type is None:
        Type = str(ftype.template_argument(0).strip_typedefs().unqualified())

    Size = normalize_size(Size_t, Size)  

    if TYPE_MAP.find(Type) != -1:
        Addr = int(para['_M_elems'].address)
        return cpu_memory(Addr, Type, Size)
    else:
        results = []
        count = int(np.prod(Size))

        for i in range(count):
            results.append(cpu_(para['_M_elems'][i], None, None))

        return np.asarray(results).reshape(Size)




def cpu_stdarray(para, Type=None, Size=None):
    ftype = para.type.strip_typedefs().unqualified()
        
    Size_t = int(ftype.template_argument(1))
    if Size_t == 0:
        if LOG: PRINT('Size_t', Size_t)
        return np.array([])

    if Type is not None and Size is not None: # top priority
        if LOG: PRINT('top priority', 'Type', Type, 'Size', Size)
        return cpu_(para['_M_elems'], Type, Size)

    if Type is None:
        Type = str(ftype.template_argument(0).strip_typedefs().unqualified())
        if LOG: PRINT('para Type', Type)

    Size = normalize_size(Size_t, Size)  

    if Type in TYPE_MAP:
        if LOG: PRINT(f'{Type} in TYPE_MAP')
        Addr = int(para['_M_elems'].address)
        return cpu_memory(Addr, Type, Size)
        
    else:
        if LOG: PRINT(f'{Type} not in TYPE_MAP')
        results = []
        count = int(np.prod(Size))

        for i in range(count):
            if LOG: PRINT(f'cpu_stdarray, i = {i}, para = {para["_M_elems"][i]}')
            results.append(cpu_(para['_M_elems'][i], None, None))

        return np.asarray(results).reshape(Size)