# MIT License

# Copyright (c) 2026 Mingjie Zhang (mingjie2026@gmail.com)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gdb
import subprocess
import os
import sys
import numpy as np
import inspect

LOG = 1

np.set_printoptions(linewidth=256)
np.set_printoptions(suppress=True)
Path = 'mem/data'
os.makedirs(Path, exist_ok=True) 

def PRINT(*args, **kwargs):
    print(inspect.currentframe().f_back.f_lineno, *args, **kwargs)

def get_pids(name):
    pids = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                parts = f.read().split(b"\x00")
            exe = os.path.basename(parts[0].decode(errors="ignore"))
            if exe == name:
                pids.append(int(pid))
        except (FileNotFoundError, PermissionError):
            continue

    if not pids:
        print(f"get_pids({name}) fail")
        sys.exit()
    return pids

def read_memory(pid, addr, size):
    with open(f"/proc/{pid}/mem", "rb", 0) as f:
        f.seek(addr)    
        return f.read(size)

def mon(app, addr, type, size):
    pid = get_pids(app)[0]
    addr_t = int(addr, 0) if isinstance(addr, str) else int(addr)

    shape = size if isinstance(size, (list, tuple)) else [size]
    data_size = 1
    for s in shape:
        data_size *= s
    data_size *= np.dtype(_CPU_MAP[type]).itemsize

    raw = read_memory(pid, addr_t, data_size)
    data = np.frombuffer(raw, dtype=_CPU_MAP[type])

    if len(shape) > 1:
        data = data.reshape(shape)
    return data


_CPU_MAP = {
    'unsigned char':            np.uint8,
    'char':                     np.int8,
    'unsigned short':           np.uint16,      
    'short':                    np.int16,
    'unsigned int':             np.uint32,        
    'int':                      np.int32,
    'unsigned long long':       np.uint64,
    'unsigned long':            np.dtype('L'),
    'float':                    np.float32,
    'double':                   np.float64,       
}

def read(Addr, Type, Size):
    shape = Size if isinstance(Size, (list, tuple)) else [Size]
    data_size = 1
    for s in shape:
        data_size *= int(s)
    data_size *= np.dtype(_CPU_MAP[Type]).itemsize

    inferior = gdb.selected_inferior()
    raw = inferior.read_memory(Addr, data_size)
    data = np.frombuffer(raw, dtype=_CPU_MAP[Type])

    if len(shape) > 1:
        data = data.reshape(shape)
    return data

def cpu(Name, Type=None, Size=None):   
    para = gdb.parse_and_eval(Name)
    t = para.type.strip_typedefs()
 
    while t.code in (gdb.TYPE_CODE_REF, gdb.TYPE_CODE_RVALUE_REF):
        para = para.referenced_value()
        t = para.type.strip_typedefs()

    if t.code == gdb.TYPE_CODE_PTR: # 1 
        if LOG: PRINT('str(t)', str(t))

        if "std::vector" in str(t): # vector
            para = para.dereference()
            Addr = int(para['_M_impl']['_M_start'])

            if Type is None:
                Type = next((k for k, v in _CPU_MAP.items() if k in str(t)), None)

            start = para['_M_impl']['_M_start']
            finish = para['_M_impl']['_M_finish']
            Size_t = int(finish - start)
            Size = Size_t if Size is None else min(Size, Size_t)

            return read(Addr, Type, Size)   

        elif "std::array" in str(t): # array
            para = para.dereference()
            Addr = int(para['_M_elems'].address)

            if Type is None:
                Type = next((k for k, v in _CPU_MAP.items() if k in str(t)), None)

            return read(Addr, Type, Size)

        elif "std::pair" in str(t): # pair
            para = para.dereference()
            Addr = int(para.address)

            if Type is None:
                Type = next((k for k, v in _CPU_MAP.items() if k in str(t)), None)

            Size = 2 if Size is None else min(Size, 2)

            return read(Addr, Type, Size)

        elif 'basic_string' in str(t): # string
            n = int(para['_M_string_length'])
            s = para['_M_dataplus']['_M_p'].string(length=n)
            return s

        elif Type is not None: # like int*
            Addr = int(para)

            if Type is None:
                Type = next((k for k, v in _CPU_MAP.items() if k in str(t)), None)

            return read(Addr, Type, Size)

        else:
            if Type is None: # Type:None like int*
                Type = next((k for k, v in _CPU_MAP.items() if k in str(t)), None)
        
            if Type is not None: # like float32*
                Addr = int(para)
                return read(Addr, Type, Size)

            else:
                para = para.dereference() # struct
                t = para.type.strip_typedefs()

                if LOG: PRINT('t.fields()', t.fields())
                results = {}
                for f in t.fields():
                    if LOG: PRINT('f.name', f.name)

                    if f.is_base_class or f.bitpos is None or not f.name:
                        continue;
                    
                    ftype = f.type.strip_typedefs().unqualified()
                    if ftype.code == gdb.TYPE_CODE_PTR: # struct pointer
                        if LOG: PRINT(f'{Name}->{f.name}', gdb.TYPE_CODE_PTR)
                        value = int(gdb.parse_and_eval(f'{Name}->{f.name}'))
                        if LOG: PRINT('value', type(value), value)

                    else: # struct elem
                        if LOG: PRINT(f'{Name}->{f.name}')
                        value = cpu(f'{Name}->{f.name}', None, Size)
                        if LOG: PRINT('value1', value)
                        value = np.asarray(value)
                        if value.size == 1:
                            value = value.item()
                        if LOG: PRINT('value2', value)

                    results[f.name] = value

                if LOG: PRINT('results', results)
                return results                
        
    elif t.code == gdb.TYPE_CODE_ARRAY: # 2   
        if Type is None:
            s = str(t.target().strip_typedefs().unqualified())
            Type = next((k for k, v in _CPU_MAP.items() if k in s), None)
    
        # get array size line int[2][3]
        et, dims = t, []
        while et.code == gdb.TYPE_CODE_ARRAY:
            lo, hi = et.range()
            dims.append(hi - lo + 1)
            et = et.target().strip_typedefs().unqualified()

        if Size is None:
            Size = dims
        else:
            total_dims = int(np.prod(dims))
            total_size = int(np.prod(Size))
            if(total_dims < total_size):
                Size = dims        
            
        if LOG: PRINT('dims', dims)

        if Type is not None:
            Addr = int(para.address)

            if Type is None: # Type:None like int*
                Type = next((k for k, v in _CPU_MAP.items() if k in str(t)), None)
        
            if LOG: PRINT(Addr, Type, Size)
            return read(Addr, Type, Size)  

        else:
            if LOG: PRINT('Type', Type)
            if len(Size) == 1:   
                results = [None] * Size[0]  
                for i in range(Size[0]):
                    results[i] = cpu(f'{Name}[{i}]')
                return results;

            elif len(Size) == 2:   
                results = [None] * (Size[0], Size[1])
                for i in range(Size[0]):
                    for j in range(Size[1]):
                        results[i][j] = cpu(f'{Name}[{i}][{j}]')
                return results;     

    elif t.code == gdb.TYPE_CODE_STRUCT: # 3
        if 'std::vector' in str(t):
            Addr = int(para['_M_impl']['_M_start'])

            if Type is None:
                s = str(t.template_argument(0))
                Type = next((k for k, v in _CPU_MAP.items() if k in s), None)

            start = para['_M_impl']['_M_start']
            finish = para['_M_impl']['_M_finish']
            Size_t = int(finish - start)
            Size = Size_t if Size is None else min(Size, Size_t)
                
            if Type is not None:                
                if LOG: PRINT('mem cpu read', Addr, Type, Size)
                return read(Addr, Type, Size)  

            else:
                results = {}
                for f in t.fields():
                    if f.is_base_class or f.bitpos is None or not f.name:
                        continue;

                    ftype = f.type.strip_typedefs().unqualified()
                    if ftype.code == gdb.TYPE_CODE_PTR:
                        if LOG: PRINT(f'{Name}.{f.name}', gdb.TYPE_CODE_PTR)
                        value = int(gdb.parse_and_eval(f'{Name}.{f.name}'))
                        if LOG: PRINT('value', type(value), value)

                    else:
                        if LOG: PRINT(f'{Name}.{f.name}')
                        value = cpu(f'{Name}.{f.name}', None, Size)
                        if LOG: PRINT('value1', value)
                        value = np.asarray(value)
                        if value.size == 1:
                            value = value.item()
                        if LOG: PRINT('value2', value)
                    results[f.name] = value

                if LOG: PRINT('results', results)
                return results

        elif 'std::array' in str(t):
            Addr = int(para['_M_elems'].address)
            return read(Addr, Type, Size)    

        elif 'std::pair' in str(t):
            Addr = int(para.address)
            return read(Addr, Type, Size)    

        elif 'Eigen::Matrix' in str(t): # Eigen::Matrix
            n = int(t.template_argument(1))
            d = para['m_storage']['m_data']
            Addr = int(d['array'][0].address)
            return read(Addr, Type, Size) 

        elif '::basic_string' in str(t): # std::string
            n = int(para['_M_string_length'])
            s = para['_M_dataplus']['_M_p'].string(length=n)
            return np.str_(s)        
            
        else:
            if LOG: PRINT('t.fields()', t.fields())

            results = {}
            for f in t.fields():
                if LOG: PRINT('f.name', f.name)
                if f.is_base_class or f.bitpos is None or not f.name:
                    continue
                
                ftype = f.type.strip_typedefs().unqualified()
                if ftype.code == gdb.TYPE_CODE_PTR:
                    if LOG: PRINT(f'{Name}.{f.name}', gdb.TYPE_CODE_PTR)
                    value = int(gdb.parse_and_eval(f'{Name}.{f.name}'))
                    if LOG: PRINT('TYPE_CODE_STRUCT value1', type(value), value)

                else:
                    if LOG: PRINT(f'{Name}.{f.name}')
                    value = cpu(f'{Name}.{f.name}', None, Size)
                    value = np.asarray(value)
                    if LOG: PRINT('value1', type(value), value)
                    if value.size == 1:
                        value = value.item()
                        if LOG: PRINT('value1 => 1', type(value), value)
                    if LOG: PRINT('TYPE_CODE_STRUCT value2', value)
                    if LOG: PRINT('value2', type(value), value)
                results[f.name] = value

            # results = {name: np.array(vals) for name, vals in results.items()}
            if LOG: PRINT('results', type(results), results)
            return results

    elif t.code == gdb.TYPE_CODE_INT: # 8
        if LOG: PRINT('t.code', gdb.TYPE_CODE_INT, 't.sizeof', t.sizeof)
        if t.sizeof == 1:
            return np.int8(para) if t.is_signed else np.uint8(para)
        elif t.sizeof == 2:
            return np.int16(para) if t.is_signed else np.uint16(para)
        elif t.sizeof == 4:
            return np.int32(para) if t.is_signed else np.uint32(para)
        else:
            return np.int64(para) if t.is_signed else np.uint64(para)

    elif t.code == gdb.TYPE_CODE_FLT: # 9
        if t.sizeof == 4:
            return np.float32(para)
        elif t.sizeof == 8:
            return np.float64(para)
        else:
            return np.longdouble(para)

    else:
        if LOG: PRINT(f"{name}({t.code}): fail")

    return None
    

_GPU_MAP = {
    'unsigned char':            np.uint8,
    'char':                     np.int8,
    'unsigned short':           np.uint16,      
    'short':                    np.int16,
    'unsigned int':             np.uint32,        
    'int':                      np.int32,
    'unsigned long long':       np.uint64,
    'unsigned long':            np.dtype('L'),
    'float':                    np.float32,
    'double':                   np.float64,       
}

def gpu(Name, Type=None, Size=None, Step = 1):  
    para = gdb.parse_and_eval(Name)
    t = para.type.strip_typedefs()

    while t.code in (gdb.TYPE_CODE_REF, gdb.TYPE_CODE_RVALUE_REF):
        para = para.referenced_value()
        t = para.type.strip_typedefs()   

    if t.code == gdb.TYPE_CODE_PTR: # 1 
        if Type is None:
            Type = str(t.target())

        type_t = next((v for k, v in _GPU_MAP.items() if k in Type), None)

        if type_t is None:
            PRINT(f'mem do not support {Type} fail')
            return None;
            
        size_t = Size if isinstance(Size, (list, tuple)) else [Size]

        data_size = int(np.prod(size_t, dtype=np.int64))
        data_size *= np.dtype(type_t).itemsize

        PRINT('Type', Type)
        
        if '@' not in str(t.target()):
            d_addr = int(para)

            expr = f"(unsigned char*)malloc({data_size})"
            if LOG: PRINT('expr', expr)

            h_addr = int(gdb.parse_and_eval(expr))

            if LOG: PRINT('h_addr', h_addr, 'd_addr', d_addr, 'data_size', data_size)

            expr = f"((int (*)(void*, const void*, size_t, int))cudaMemcpy)((void*){h_addr}, (void*){d_addr}, {data_size}, cudaMemcpyDeviceToHost)"
            ret = gdb.parse_and_eval(expr)

            inferior = gdb.selected_inferior()
            raw = inferior.read_memory(h_addr, data_size)
            data = np.frombuffer(raw, dtype=type_t).copy()

            expr = f"((void(*)(void*))free)((void*){h_addr})"
            gdb.parse_and_eval(expr)

        elif Step > 1 and len(shape) > 1:
            data = np.empty(shape, dtype=type_t)

            for i in range(0, shape[0], Step):
                for j in range(0, shape[1], Step):
                    data[i, j] = (para + i * shape[1] + j).dereference()

                    for di in range(Step): 
                        ii = i + di
                        if ii >= shape[0]:
                            continue

                        for dj in range(Step):
                            jj = j + dj
                            if jj >= shape[1]:
                                continue
                            
                            data[ii, jj] = data[i, j];

        else:
            total_size = data_size
            if data_size % 8 == 0:
                total_size = int(data_size / 8)
                total_data = np.empty(total_size, dtype=np.ulonglong)
                total_type = gdb.lookup_type("unsigned long long")
            elif data_size % 4 == 0:
                total_size = int(data_size / 4)
                total_data = np.empty(total_size, dtype=np.uint32)
                total_type = gdb.lookup_type("unsigned int")
            elif data_size % 2 == 0:
                total_size = int(data_size / 2)
                total_data = np.empty(total_size, dtype=np.uint16)
                total_type = gdb.lookup_type("unsigned short")    
            else:
                total_size = int(data_size)
                total_data = np.empty(total_size, dtype=np.uint8)
                total_type = gdb.lookup_type("unsigned char")  

            for i in range(total_size):
                total_offset = int(i * total_data.itemsize / para.type.target().sizeof)
                total_data[i] = (para + total_offset).cast(total_type.pointer()).dereference()
        
            data = total_data.view(type_t)


        if len(size_t) > 1:
            data = data.reshape(size_t)
        return data
  
    elif t.code == gdb.TYPE_CODE_INT: # 8
        if LOG: PRINT('t.code', gdb.TYPE_CODE_INT)
        if t.sizeof == 1:
            return np.int8(para) if t.is_signed else np.uint8(para)
        elif t.sizeof == 2:
            return np.int16(para) if t.is_signed else np.uint16(para)
        elif t.sizeof == 4:
            return np.int32(para) if t.is_signed else np.uint32(para)
        else:
            return np.int64(para) if t.is_signed else np.uint64(para)

    elif t.code == gdb.TYPE_CODE_FLT: # 9
        if t.sizeof == 4:
            return np.float32(para)
        elif t.sizeof == 8:
            return np.float64(para)
        else:
            return np.longdouble(para)

    else:
        if LOG: PRINT(f"{name}({t.code}): fail")

    return None
    
#------------------------------------------------------------------------
# mem
#------------------------------------------------------------------------

def _mem(Name, Type=None, Size=None, Step=1):
    _FULL_TYPE = {
        'uc':                   'unsigned char',
        'c':                    'char',
        'us':                   'unsigned short',
        's':                    'short',
        'ui':                   'unsigned int',
        'i':                    'int',
        'ull':                  'unsigned long long',
        'ul':                   'unsigned long',
        'f':                    'float',
        'd':                    'double',
    }

    if Type is not None and Type in _FULL_TYPE:
        Type = _FULL_TYPE[Type]  
    
    if Size is not None:
        Size = np.atleast_1d(np.asarray(Size))

    if LOG: PRINT('Type', Type, 'Size', Size)

    if Type == None and Size == None:
        if LOG: PRINT('mem cpu')
        data = cpu(Name, Type, Size)
        if LOG: PRINT('type(data)', type(data))
        if LOG: PRINT('mem cpu save', f'{Path}/{Name}.npy')
        np.save(f'{Path}/{Name}.npy', data) 
        return data

    if LOG: PRINT('Name', Name)

    if LOG: PRINT('repr(Name)', repr(Name))

    para = gdb.parse_and_eval(Name)

    t = para.type.strip_typedefs()

    if LOG: PRINT('para.type.strip_typedefs()', str(t))

    if '@' not in str(t):
        sym, is_field  = gdb.lookup_symbol("cudaPointerGetAttributes")
        if LOG: PRINT('sym', sym)

        try:
            buf = int(gdb.parse_and_eval("(void *) malloc(64)"))

            if LOG: PRINT(f"(int) cudaPointerGetAttributes((void *) {buf:#x}, {Name})")
            rc  = int(gdb.parse_and_eval(f"(int) cudaPointerGetAttributes((void *) {buf:#x}, {Name})"))

            t   = int(gdb.parse_and_eval(f"*(int *) {buf:#x}"))

            if LOG: PRINT("rc =", rc, " type =", t)
            if LOG: PRINT({0: "host-malloc", 1: "pinned", 2: "device", 3: "managed"}.get(t, "?"))

            gdb.parse_and_eval(f"(void) free((void *) {buf:#x})")

            if t in [2, 3]:
                if LOG: PRINT('mem gpu host')
                data = gpu(Name, Type, Size, Step)
                if LOG: PRINT('mem gpu host save', f'{Path}/{Name}.npy')
                np.save(f'{Path}/{Name}.npy', data) 
                return data
            else:
                if LOG: PRINT('mem cpu')
                data = cpu(Name, Type, Size)
                if LOG: PRINT('mem cpu save', f'{Path}/{Name}.npy')
                np.save(f'{Path}/{Name}.npy', data) 
                return data
                
        except gdb.error as e:
            if LOG: PRINT('pga failed:', e)
            if LOG: PRINT('mem cpu', Name, Type, Size)
            data = cpu(Name, Type, Size)
            if LOG: PRINT('data', type(data), data)
            if LOG: PRINT('mem cpu save', f'{Path}/{Name}.npy')
            np.save(f'{Path}/{Name}.npy', data) 
            return data
    else:        
        if LOG: PRINT('mem gpu device')
        data = gpu(Name, Type, Size, Step)
        if LOG: PRINT('mem gpu device save', type(data), f'{Path}/{Name}.npy')
        np.save(f'{Path}/{Name}.npy', data) 
        return data

    return None

def mem(Name, Type=None, Size=None, Step=1):
    if LOG:
        return _mem(Name, Type, Size, Step)
    else:
        try:
            data = _mem(Name, Type, Size, Step)
        except Exception:
            data = None
        return data
    
    return None

# Value  Constant                     Meaning
# -1     TYPE_CODE_BITSTRING          Bit string (deprecated, kept for compatibility)
# 1      TYPE_CODE_PTR                Pointer, e.g. T*
# 2      TYPE_CODE_ARRAY              Array, e.g. T[N]
# 3      TYPE_CODE_STRUCT             Struct or C++ class
# 4      TYPE_CODE_UNION              Union
# 5      TYPE_CODE_ENUM               Enumeration
# 6      TYPE_CODE_FLAGS              Bit-flags register type (e.g. eflags)
# 7      TYPE_CODE_FUNC               Function type
# 8      TYPE_CODE_INT                Integer (int, long, size_t, ...)
# 9      TYPE_CODE_FLT                Floating point (float, double)
# 10     TYPE_CODE_VOID               void
# 11     TYPE_CODE_SET                Set type (Pascal / Modula-2)
# 12     TYPE_CODE_RANGE              Range type (array index bounds, etc.)
# 13     TYPE_CODE_STRING             String type (Fortran-style, NOT char*)
# 14     TYPE_CODE_ERROR              Unrecognized / corrupt debug info
# 15     TYPE_CODE_METHOD             C++ member function type
# 16     TYPE_CODE_METHODPTR          Pointer to member function, void (T::*)()
# 17     TYPE_CODE_MEMBERPTR          Pointer to data member, int T::*
# 18     TYPE_CODE_REF                C++ lvalue reference, T&
# 19     TYPE_CODE_RVALUE_REF         C++ rvalue reference, T&&
# 20     TYPE_CODE_CHAR               Character type, char
# 21     TYPE_CODE_BOOL               Boolean, bool
# 22     TYPE_CODE_COMPLEX            Complex number, _Complex
# 23     TYPE_CODE_TYPEDEF            typedef / using alias (not yet stripped)
# 24     TYPE_CODE_NAMESPACE          C++ namespace
# 25     TYPE_CODE_DECFLOAT           Decimal float (_Decimal64, etc.)
# 26     TYPE_CODE_MODULE             Module (Fortran)
# 27     TYPE_CODE_INTERNAL_FUNCTION  GDB internal convenience function ($_strlen, ...)
# 28     TYPE_CODE_XMETHOD            Python-defined extension method (xmethod)
# 29     TYPE_CODE_FIXED_POINT        Fixed-point number type
# 30     TYPE_CODE_NAMELIST           Fortran namelist

# python3 -m mem mem.py

# Credit balance is too low
# unset ANTHROPIC_API_KEY
# echo "[$ANTHROPIC_API_KEY]"
# /login "Claude account with subscription"
# /status
# /usage

# r = subprocess.run(
#     # sudo sysctl kernel.yama.ptrace_scope=0
#     ["sudo", "sysctl", "kernel.yama.ptrace_scope=0"]#, capture_output=True, text=True
# )
# if r.returncode != 0:
#     print("sudo sysctl kernel.yama.ptrace_scope=0 fail")  
#     sys.exit()

# node --version
# npm --version
# sudo npm install -g @vscode/vsce
# ~/.vscode/extensions
# ~/.config/Code/User/keybindings.json
# Ctrl + Shift + P
# Reload Window
# Extension Development Host
# Extensions: Install from VSIX...