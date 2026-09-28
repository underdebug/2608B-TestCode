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
import math

LOG = 0 # 9/27 2026

np.set_printoptions(linewidth=200)
np.set_printoptions(suppress=True)

if "__file__" in globals():
    PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
else:
    PATH = os.path.abspath('mem/data')
os.makedirs(PATH, exist_ok=True)

def PRINT(*args, **kwargs):
    print(inspect.currentframe().f_back.f_lineno, *args, **kwargs)

def get_pids(name):
    pids = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as field:
                parts = field.read_memory().split(b"\x00")
            exe = os.PATH.basename(parts[0].decode(errors="ignore"))
            if exe == name:
                pids.append(int(pid))
        except (FileNotFoundError, PermissionError):
            continue

    if not pids:
        print(f'get_pids({name}) fail')
        sys.exit()
    return pids

def mon(app, addr, type, size):
    pid = get_pids(app)[0]
    addr_t = int(addr, 0) if isinstance(addr, str) else int(addr)

    shape = size if isinstance(size, (list, tuple)) else [size]
    data_size = 1
    for s in shape:
        data_size *= s
    data_size *= np.dtype(_CPU_MAP[type]).itemsize

    with open(f'/proc/{pid}/mem', 'rb', 0) as field:
        field.seek(addr_t)    
        return field.read_memory(data_size)

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
    'unsigned long':            np.dtype('L'),
    'unsigned long long':       np.uint64,
    'float':                    np.float32,
    'double':                   np.float64,       
}

def normalize_size(Size_mem, Size_read):   
    if Size_read is None:
        return Size_mem

    Size_mem = np.atleast_1d(np.asarray(Size_mem))
    Size_read = np.atleast_1d(np.asarray(Size_read))

    Size_mem_p = math.prod(Size_mem)
    Size_read_p = math.prod(Size_read)

    if Size_mem_p >= Size_read_p:
        return Size_read

    Size = [1] * (len(Size_read))
    for i in range(len(Size_read) - 1, -1, -1):
        for j in range(Size_read[i]):
            Size_new = Size.copy()
            Size_new[i] = j + 1
            Size_new_p = math.prod(Size_new)

            if Size_new_p <= Size_mem_p:
                Size = Size_new
            else:
                break
    return Size

def read_memory(Addr, Type, Size):
    # data_size = math.prod(int(s) for s in (Size if isinstance(Size, (list, tuple)) else [Size]))
    Size = np.atleast_1d(np.asarray(Size))
    data_size = math.prod(Size)
    data_size *= np.dtype(_CPU_MAP[Type]).itemsize

    inferior = gdb.selected_inferior()
    raw = inferior.read_memory(Addr, data_size)
    data = np.frombuffer(raw, dtype=_CPU_MAP[Type])

    data = data.reshape(Size)
    return data

def parse_ptr(para, Type=None, Size=None):
    ftype = para.type.strip_typedefs()

    if Type is None:
        Type = next((k for k, v in _CPU_MAP.items() if k in str(ftype)), None)

    Addr = int(para)
    return read_memory(Addr, Type, Size)

def parse_array(para, Type=None, Size=None):
    ftype = para.type.strip_typedefs()

    if Type is not None and Size is not None: # top priority
        Addr = int(para.address)
        return read_memory(Addr, Type, Size)  

    if Type is None:
        s = str(ftype.target().strip_typedefs().unqualified())
        Type = next((k for k, v in _CPU_MAP.items() if s.startswith(k)), None)

    # get array size line int[2][3]
    et, dims = ftype, []
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
            Type = next((k for k, v in _CPU_MAP.items() if k in str(ftype)), None)
    
        if LOG: PRINT(Addr, Type, Size)
        return read_memory(Addr, Type, Size)  

    else:
        if LOG: PRINT('Type', Type)
        if len(Size) == 1:   
            results = [None] * Size[0]  
            for i in range(Size[0]):
                results[i] = _cpu(para[i])
            return results;

        elif len(Size) == 2:
            results = [[None] * Size[1] for _ in range(Size[0])]
            for i in range(Size[0]):
                for j in range(Size[1]):
                    results[i][j] = _cpu(para[i][j])
            return results; 

def parse_stdvector(para, Type=None, Size=None):
    ftype = para.type.strip_typedefs()

    start = para['_M_impl']['_M_start']
    finish = para['_M_impl']['_M_finish']
    Size_t = int(finish - start)

    if Size_t == 0:
        if LOG: PRINT('gdb.TYPE_CODE_STRUCT, Size_t', Size_t, 'Size', Size)
        return np.array([])

    if Type is not None and Size is not None: # top priority
        if LOG: PRINT('gdb.TYPE_CODE_STRUCT, start =', start, ',Type =', Type, ',Size =', Size)
        return read_memory(start, Type, Size)    
    
    if LOG: PRINT('gdb.TYPE_CODE_STRUCT type', str(ftype.template_argument(0).strip_typedefs()))
    if Type is None:
        s = str(ftype.template_argument(0).strip_typedefs())
        Type = next((k for k, v in _CPU_MAP.items() if s.startswith(k)), None)    

    if LOG: PRINT('gdb.TYPE_CODE_STRUCT, Size_t', Size_t, 'Size >', Size)
    Size = normalize_size(Size_t, Size)
    if LOG: PRINT('gdb.TYPE_CODE_STRUCT, start', start, 'Type', Type, 'Size <', Size)

    if Type is not None:                
        return read_memory(start, Type, Size)  

    results = []
    for i in range(int(np.atleast_1d(Size)[0])):
        struct = start[i]

        result = {}
        for field in struct.type.fields():
            ftype2 = field.type.strip_typedefs().unqualified()

            if ftype2.code in {
                gdb.TYPE_CODE_INT,
                gdb.TYPE_CODE_FLT,
                gdb.TYPE_CODE_BOOL,
                gdb.TYPE_CODE_ENUM,
                gdb.TYPE_CODE_ARRAY,
                gdb.TYPE_CODE_STRUCT,
            }:
                result[field.name] = _cpu(struct[field.name], None, None)

            elif ftype2.code == gdb.TYPE_CODE_PTR:
                result[field.name] = int(struct[field.name])

        results.append(result)

    return results

    #         # fields() returns metadata; decode the member value instead.
    #         result = _cpu(struct[field.name], None, None)
    #         results.setdefault(field.name, []).append(result)

    # return results

def parse_stdarray(para, Type=None, Size=None):
    Addr = int(para['_M_elems'].address)
    return read_memory(Addr, Type, Size)  

def parse_stdpair(para, Type=None, Size=None):
    Addr = int(para.address)
    return read_memory(Addr, Type, Size)     

def parse_struct(para, Type=None, Size=None):
    ftype = para.type.strip_typedefs()

    results = {}
    for field in ftype.fields():
        ftype2 = field.type.strip_typedefs().unqualified()
        para2 = para[field.name]      

        if ftype2.code in {
                gdb.TYPE_CODE_INT,
                gdb.TYPE_CODE_FLT,
                gdb.TYPE_CODE_BOOL,
                gdb.TYPE_CODE_ENUM,
                gdb.TYPE_CODE_ARRAY,
                gdb.TYPE_CODE_STRUCT,
            }:
            results[field.name] = _cpu(para2, None, None)

        elif ftype2.code == gdb.TYPE_CODE_PTR:
            results[field.name] = int(para2)

    return results

def _cpu(para, Type=None, Size=None):
    ftype = para.type.strip_typedefs()
 
    while ftype.code in (gdb.TYPE_CODE_REF, gdb.TYPE_CODE_RVALUE_REF):
        para = para.referenced_value()
        ftype = para.type.strip_typedefs()

    ftype = ftype.unqualified()

    if ftype.code == gdb.TYPE_CODE_PTR: # 1
        if LOG: PRINT('str(ftype)', str(ftype))
    
        if int(para) == 0:
            return None

        target_type = ftype.target().strip_typedefs().unqualified()
        if target_type.code == gdb.TYPE_CODE_STRUCT:
            return _cpu(para.dereference(), Type, Size)

        return parse_ptr(para, Type, Size)

    elif ftype.code == gdb.TYPE_CODE_ARRAY: # 2
        return parse_array(para, Type, Size)

    elif ftype.code == gdb.TYPE_CODE_STRUCT: # 3
        if str(ftype).startswith('std::vector'):
            return parse_stdvector(para, Type, Size)

        elif str(ftype).startswith('std::array'):
            return parse_stdarray(para, Type, Size)

        elif str(ftype).startswith('std::pair'):
            return parse_stdpair(para, Type, Size)

        elif 'Eigen::Matrix' in str(ftype): # Eigen::Matrix
            n = int(ftype.template_argument(1))
            d = para['m_storage']['m_data']
            Addr = int(d['array'][0].address)
            return read_memory(Addr, Type, Size) 
        
        elif '::basic_string' in str(ftype): # std::string
            n = int(para['_M_string_length'])
            s = para['_M_dataplus']['_M_p'].string(length=n)
            return np.str_(s)  

        else:
            return parse_struct(para, Type, Size)
    
    elif ftype.code == gdb.TYPE_CODE_ENUM: # 5
        if ftype.sizeof == 1:
            return np.int8(para) if ftype.is_signed else np.uint8(para)
        elif ftype.sizeof == 2:
            return np.int16(para) if ftype.is_signed else np.uint16(para)
        elif ftype.sizeof == 4:
            return np.int32(para) if ftype.is_signed else np.uint32(para)
        elif ftype.sizeof == 8:
            return np.int64(para) if ftype.is_signed else np.uint64(para)
        else:
            return value

    elif ftype.code == gdb.TYPE_CODE_INT: # 8
        if LOG: PRINT('ftype.code', gdb.TYPE_CODE_INT, 'ftype.sizeof', ftype.sizeof)
        if ftype.sizeof == 1:
            return np.int8(para) if ftype.is_signed else np.uint8(para)
        elif ftype.sizeof == 2:
            return np.int16(para) if ftype.is_signed else np.uint16(para)
        elif ftype.sizeof == 4:
            return np.int32(para) if ftype.is_signed else np.uint32(para)
        else:
            return np.int64(para) if ftype.is_signed else np.uint64(para)

    elif ftype.code == gdb.TYPE_CODE_FLT: # 9
        if ftype.sizeof == 4:
            return np.float32(para)
        elif ftype.sizeof == 8:
            return np.float64(para)
        else:
            return np.longdouble(para)

    elif ftype.code == gdb.TYPE_CODE_BOOL: # 21
        return np.bool_(int(para))

def cpu(Name, Type=None, Size=None):   
    para = gdb.parse_and_eval(Name)
    return _cpu(para, Type, Size)  

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
    ftype = para.type.strip_typedefs()

    while ftype.code in (gdb.TYPE_CODE_REF, gdb.TYPE_CODE_RVALUE_REF):
        para = para.referenced_value()
        ftype = para.type.strip_typedefs()   

    if ftype.code == gdb.TYPE_CODE_PTR: # 1 
        if Type is None:
            Type = str(ftype.target())

        type_t = next((v for k, v in _GPU_MAP.items() if k in Type), None)

        if type_t is None:
            PRINT(f'mem do not support {Type} fail')
            return None;
            
        data_size = int(np.prod(Size, dtype=np.int64))
        data_size *= np.dtype(type_t).itemsize

        if LOG: PRINT('Type', Type)
        
        if '@' not in str(ftype.target()):
            d_addr = int(para)

            expr = f'((unsigned char*)malloc({data_size}))'
            if LOG: PRINT('expr', expr)

            h_addr = int(gdb.parse_and_eval(expr))

            if LOG: PRINT('h_addr', h_addr, 'd_addr', d_addr, 'data_size', data_size)

            expr = f'((int (*)(void*, const void*, size_t, int))cudaMemcpy)((void*){h_addr}, (void*){d_addr}, {data_size}, cudaMemcpyDeviceToHost)'
            ret = gdb.parse_and_eval(expr)

            inferior = gdb.selected_inferior()
            raw = inferior.read_memory(h_addr, data_size)
            data = np.frombuffer(raw, dtype=type_t).copy()

            expr = f'((void(*)(void*))free)((void*){h_addr})'
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

        if LOG: PRINT('Size =', Size, 'len(Size)', len(Size))
        if len(Size) > 1:
            data = data.reshape(Size)
        return data
  
    elif ftype.code == gdb.TYPE_CODE_INT: # 8
        if LOG: PRINT('ftype.code', gdb.TYPE_CODE_INT, 'ftype.sizeof', ftype.sizeof)
        if ftype.sizeof == 1:
            return np.int8(para) if ftype.is_signed else np.uint8(para)
        elif ftype.sizeof == 2:
            return np.int16(para) if ftype.is_signed else np.uint16(para)
        elif ftype.sizeof == 4:
            return np.int32(para) if ftype.is_signed else np.uint32(para)
        else:
            return np.int64(para) if ftype.is_signed else np.uint64(para)

    elif ftype.code == gdb.TYPE_CODE_FLT: # 9
        if LOG: PRINT('ftype.code', gdb.TYPE_CODE_INT, 'ftype.sizeof', ftype.sizeof)
        if ftype.sizeof == 4:
            return np.float32(para)
        elif ftype.sizeof == 8:
            return np.float64(para)
        else:
            return np.longdouble(para)

    else:
        if LOG: PRINT(f'{name}({ftype.code}): fail')

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

    if LOG: PRINT('Name', Name, 'Type', Type, 'Size', Size, 'Step', Step)

    para = gdb.parse_and_eval(Name)

    ftype = para.type.strip_typedefs()

    if LOG: PRINT('para.type.strip_typedefs()', str(ftype))

    if '@' not in str(ftype):
        sym, is_field  = gdb.lookup_symbol("cudaPointerGetAttributes")
        if LOG: PRINT('sym', sym)

        try:
            buf = int(gdb.parse_and_eval("(void *) malloc(64)"))

            if LOG: PRINT(f'(int) cudaPointerGetAttributes((void *) {buf:#x}, {Name})')
            rc  = int(gdb.parse_and_eval(f'(int) cudaPointerGetAttributes((void *) {buf:#x}, {Name})'))

            attr   = int(gdb.parse_and_eval(f'*(int *) {buf:#x}'))

            if LOG: PRINT(f'rc = {rc}, type = {attr}')
            if LOG: PRINT({0: 'host-malloc', 1: 'pinned', 2: 'device', 3: 'managed'}.get(attr, '?'))

            gdb.parse_and_eval(f'(void) free((void *) {buf:#x})')

            if attr in [2, 3]:
                if LOG: PRINT('mem gpu host', Name, Type, Size, Step)
                data = gpu(Name, Type, Size, Step)
                if LOG: PRINT('mem gpu host save', f'{PATH}/{Name}.npy')
                np.save(f'{PATH}/{Name}.npy', data) 
                return data
            else:
                if LOG: PRINT('mem cpu', Name, Type, Size)
                data = cpu(Name, Type, Size)
                if LOG: PRINT('mem cpu save', f'{PATH}/{Name}.npy')
                np.save(f'{PATH}/{Name}.npy', data) 
                return data
                
        except gdb.error as e:
            if LOG: PRINT('pga failed:', e)
            if LOG: PRINT('mem cpu', Name, Type, Size)
            data = cpu(Name, Type, Size)
            if LOG: PRINT('data', type(data), data)
            if LOG: PRINT('mem cpu save', f'{PATH}/{Name}.npy')
            np.save(f'{PATH}/{Name}.npy', data) 
            return data
    else:        
        if LOG: PRINT('mem gpu device')
        data = gpu(Name, Type, Size, Step)
        if LOG: PRINT('mem gpu device save', type(data), f'{PATH}/{Name}.npy')
        np.save(f'{PATH}/{Name}.npy', data) 
        return data

    return None

def mem(Name, Type=None, Size=None, Step=1):
    if LOG:
        data = _mem(Name, Type, Size, Step)

    else:
        try:
            data = _mem(Name, Type, Size, Step)
        except Exception:
            data = None
            
    return data
    
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
