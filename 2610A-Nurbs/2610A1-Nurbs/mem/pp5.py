
def cpu_stdarray(para, Type=None, Size=None):
    Addr = int(para['_M_elems'].address)
    return cpu_memory(Addr, Type, Size)  

def cpu_stdpair(para, Type=None, Size=None):
    Addr = int(para.address)
    return cpu_memory(Addr, Type, Size)     
