
#------------------------------------------------------------------------
# mem
#------------------------------------------------------------------------

import gdb
import subprocess
import os
import sys
import numpy as np
import inspect

np.set_printoptions(linewidth=256)
np.set_printoptions(suppress=True)

os.makedirs('mem', exist_ok=True) 

LOG = 0

def PRINT(*args, **kwargs):
    print(inspect.currentframe().f_back.f_lineno, *args, **kwargs)

typeMap = {
    'char':                     [np.int8,       1],
    'c':                        [np.int8,       1],
    'unsigned char':            [np.uint8,      1],
    'uc':                       [np.uint8,      1],
    'short':                    [np.int16,      2],
    's':                        [np.int16,      2],
    'unsigned short':           [np.uint16,     2],
    'us':                       [np.uint16,     2],
    'int':                      [np.int32,      4],
    'i':                        [np.int32,      4],
    'unsigned int':             [np.uint32,     4],
    'ui':                       [np.uint32,     4],
    'float':                    [np.float32,    4],
    'f':                        [np.float32,    4],
    'double':                   [np.float64,    8],
    'd':                        [np.float64,    8],
}

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
    r = subprocess.run(
        # sudo sysctl kernel.yama.ptrace_scope=0
        ["sudo", "sysctl", "kernel.yama.ptrace_scope=0"]#, capture_output=True, text=True
    )
    if r.returncode != 0:
        print("sudo sysctl kernel.yama.ptrace_scope=0 fail")  
        sys.exit()

    pid = get_pids(app)[0]
    addr_t = int(addr, 0) if isinstance(addr, str) else int(addr)

    shape = size if isinstance(size, (list, tuple)) else [size]
    data_size = 1
    for s in shape:
        data_size *= s
    data_size *= typeMap[type][1]

    raw = read_memory(pid, addr_t, data_size)
    data = np.frombuffer(raw, dtype=typeMap[type][0])

    if len(shape) > 1:
        data = data.reshape(shape)
    return data

#------------------------------------------------------------------------
# cpu
#------------------------------------------------------------------------

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

def info(name):
    print(f'({name}, ----------------')

    para = gdb.parse_and_eval(name)
    t = para.type.strip_typedefs()

    while t.code in (gdb.TYPE_CODE_REF, gdb.TYPE_CODE_RVALUE_REF):
        para = para.referenced_value()
        t = para.type.strip_typedefs()

    if t.code == gdb.TYPE_CODE_ARRAY: # 2
        PRINT(f'{name}({t.code}) = {str(t)}')

    elif t.code == gdb.TYPE_CODE_STRUCT: # 3
        if str(t).startswith("std::vector") or str(t).startswith("const std::vector"):
            data_type = str(t.template_argument(0).strip_typedefs())
            start = para['_M_impl']['_M_start']
            finish = para['_M_impl']['_M_finish']
            data_size = int(finish - start)

            PRINT(f'{name}({t.code}) = [{data_type}, {data_size}]')

        elif str(t).startswith("std::array") or str(t).startswith("const std::array"):
            data_type = str(t.template_argument(0).strip_typedefs())
            data_size = int(t.template_argument(1))

            PRINT(f'{name}({t.code}) = [{data_type}, {data_size}]')

        elif str(t).startswith("std::pair") or str(t).startswith("const std::pair"):
            first_type = str(t.template_argument(0).strip_typedefs())
            second_type = str(t.template_argument(1).strip_typedefs())

            first_val = para['first']
            second_val = para['second']

            PRINT(f'{name}({t.code}) = [{first_type}, {first_val}; {second_type}, {second_val}]')

        else:
            for f in t.fields():
                info(f'{name}.{f.name}')

    elif t.code == gdb.TYPE_CODE_INT: # 8
        value = int(para)
        PRINT(f'{name}({t.code}) = {value}')

    elif t.code == gdb.TYPE_CODE_FLT: # 9
        value = float(para)
        PRINT(f'{name}({t.code}) = {value}')

    else:
        PRINT(f"{name}({t.code}): fail")

def type(Name):
    para = gdb.parse_and_eval(Name)
    t = para.type.strip_typedefs()

    while t.code in (gdb.TYPE_CODE_REF, gdb.TYPE_CODE_RVALUE_REF):
        para = para.referenced_value()
        t = para.type.strip_typedefs()

    if t.code == gdb.TYPE_CODE_ARRAY: # 2
        while t.code == gdb.TYPE_CODE_ARRAY:
            t = t.target()

        if LOG: PRINT('type : ', str(t.strip_typedefs()) )

        return str(t.strip_typedefs())
    
    elif t.code in (gdb.TYPE_CODE_PTR, gdb.TYPE_CODE_TYPEDEF): # 1 23
        while t.code in (gdb.TYPE_CODE_PTR, gdb.TYPE_CODE_TYPEDEF):
            t = t.target()

        if LOG: PRINT('type : ', str(t.strip_typedefs()) )

        return str(t.strip_typedefs())

    elif t.code == gdb.TYPE_CODE_STRUCT: # 3
        try:
            elem_type = t.template_argument(0)
            if LOG: PRINT('type : ', str(elem_type))

            return str(elem_type)

        except Exception:
            if len(t.fields()) == 1:
                return type(f'{Name}.{t.fields()[0].name}');

            type_str = str(t.strip_typedefs())
            if type_str.startswith('const '):
                type_str = type_str[len('const '):]

            if LOG: PRINT('type : ', type_str)
            return type_str

    if LOG: PRINT('type : ', str(t.strip_typedefs()))
    return str(t.strip_typedefs())

def size(Name):
    para = gdb.parse_and_eval(Name)
    t = para.type.strip_typedefs()

    while t.code in (gdb.TYPE_CODE_REF, gdb.TYPE_CODE_RVALUE_REF):
        para = para.referenced_value()
        t = para.type.strip_typedefs()

    if LOG: PRINT(f'{Name}({t.code}): {str(t)}')

    if t.code == gdb.TYPE_CODE_ARRAY: # 2
        dims = []
        while t.code == gdb.TYPE_CODE_ARRAY:
            low, high = t.range()
            dims.append(high - low + 1)
            t = t.target()

        return dims[0] if len(dims) == 1 else dims

    elif t.code == gdb.TYPE_CODE_STRUCT: # 3
        if str(t).startswith("std::vector") or str(t).startswith("const std::vector"):
            start = para['_M_impl']['_M_start']
            finish = para['_M_impl']['_M_finish']
            return int(finish - start)

        elif str(t).startswith("std::array") or str(t).startswith("const std::array"):
            return int(t.template_argument(1))

        elif str(t).startswith("std::pair") or str(t).startswith("const std::pair"):
            return 2

        else:
            if len(t.fields()) == 1:
                return size(f'{Name}.{t.fields()[0].name}');

            return 1

    return 1;

def cpu(Name, Type=None, Size=None):   
    """
    r = subprocess.run(
        # sudo sysctl kernel.yama.ptrace_scope=0
        ["sudo", "sysctl", "kernel.yama.ptrace_scope=0"]#, capture_output=True, text=True
    )
    if r.returncode != 0:
        print("sudo sysctl kernel.yama.ptrace_scope=0 fail")  
        sys.exit()
    """
    if Type == None:
        Type = type(Name)

    if Size == None:
        Size = size(Name)

    para = gdb.parse_and_eval(Name)
    t = para.type.strip_typedefs()

    while t.code in (gdb.TYPE_CODE_REF, gdb.TYPE_CODE_RVALUE_REF):
        para = para.referenced_value()
        t = para.type.strip_typedefs()

    if t.code == gdb.TYPE_CODE_PTR: # 1                                  
        if str(t).startswith("std::vector") or str(t).startswith("const std::vector"):
            para = para.dereference()
            data_addr = int(para['_M_impl']['_M_start'])

        elif str(t).startswith("std::array") or str(t).startswith("const std::array"):
            para = para.dereference()
            data_addr = int(para['_M_elems'].address)

        elif str(t).startswith("std::pair") or str(t).startswith("const std::pair"):
            para = para.dereference()
            data_addr = int(para.address)

        else:
            para = int(para)

    elif t.code == gdb.TYPE_CODE_ARRAY: # 2    
        if Type not in typeMap:
            if len(Size) == 1:   
                results = [None] * Size  
                for i in range(Size[0]):
                    results[i] = cpu(f'{Name}[{i}]')
                return results;

            elif len(Size) == 2:   
                results = [None] * (Size[0], Size[1])
                for i in range(Size[0]):
                    for j in range(Size[1]):
                        results[i][j] = cpu(f'{Name}[{i}][{j}]')
                return results;

        data_addr = int(para.address)

    elif t.code == gdb.TYPE_CODE_STRUCT: # 3
        if str(t).startswith("std::vector") or str(t).startswith("const std::vector"):
            if Type not in typeMap:
                if LOG: PRINT('Size', Size)

                results = [None] * Size
                for i in range(Size):
                    results[i] = cpu(f'{Name}[{i}]')
                return results;
                
            data_addr = int(para['_M_impl']['_M_start'])

        elif str(t).startswith("std::array") or str(t).startswith("const std::array"):
            data_addr = int(para['_M_elems'].address)

        elif str(t).startswith("std::pair") or str(t).startswith("const std::pair"):
            data_addr = int(para.address)

        else:
            if len(t.fields()) == 1:
                if LOG: PRINT(f'{Name}.{t.fields()[0].name}')
                return cpu(f'{Name}.{t.fields()[0].name}', Type, Size);

            return para

    elif t.code == gdb.TYPE_CODE_INT: # 8
        return int(para);

    elif t.code == gdb.TYPE_CODE_FLT: # 9
        return para

    else:
        PRINT(f"{name}({t.code}): fail")

    shape = Size if isinstance(Size, (list, tuple)) else [Size]
    data_size = 1
    for s in shape:
        data_size *= s
    data_size *= typeMap[Type][1]

    inferior = gdb.selected_inferior()
    raw = inferior.read_memory(data_addr, data_size)
    data = np.frombuffer(raw, dtype=typeMap[Type][0])

    if len(shape) > 1:
        data = data.reshape(shape)
    return data
    
#------------------------------------------------------------------------
# gpu
#------------------------------------------------------------------------

def gpu(Name, Type, Size, Step = 1):  
    para = gdb.parse_and_eval(Name)

    shape = Size if isinstance(Size, (list, tuple)) else [Size]
    data_size = 1
    for s in shape:
        data_size *= s
    data_size *= typeMap[Type][1]

    type_target = para.type.target() 
    if '@' not in str(type_target):
        d_addr = int(para)

        expr = f"(unsigned char*)malloc({data_size})"
        h_addr = int(gdb.parse_and_eval(expr))

        expr = f"((int (*)(void*, const void*, size_t, int))cudaMemcpy)((void*){h_addr}, (void*){d_addr}, {data_size}, cudaMemcpyDeviceToHost)"
        ret = gdb.parse_and_eval(expr)

        inferior = gdb.selected_inferior()
        raw = inferior.read_memory(h_addr, data_size)
        data = np.frombuffer(raw, dtype=typeMap[Type][0]).copy()

        expr = f"((void(*)(void*))free)((void*){h_addr})"
        gdb.parse_and_eval(expr)

    elif Step > 1 and len(shape) > 1:
        data = np.empty(shape, dtype=typeMap[Type][0])

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
     
        data = total_data.view(typeMap[Type][0])


    if len(shape) > 1:
        data = data.reshape(shape)
    return data

#------------------------------------------------------------------------
# mem
#------------------------------------------------------------------------

def mem(Name, Type=None, Size=None, Step=1):
    if Type == None or Size == None:
        if LOG: PRINT('mem cpu')
        data = cpu(Name, Type, Size)
        np.save(f'mem/{Name}.npy', data) 
        return data

    para = gdb.parse_and_eval(Name)
    t = para.type.strip_typedefs()

    if '@' not in str(t):
        buf = int(gdb.parse_and_eval("(void *) malloc(64)"))
        rc  = int(gdb.parse_and_eval(f"(int) cudaPointerGetAttributes((void *) {buf:#x}, {Name})"))
        t   = int(gdb.parse_and_eval(f"*(int *) {buf:#x}"))

        if LOG: PRINT("rc =", rc, " type =", t)
        if LOG: PRINT({0: "host-malloc", 1: "pinned", 2: "device", 3: "managed"}.get(t, "?"))

        gdb.parse_and_eval(f"(void) free((void *) {buf:#x})")

        if t in [2, 3]:
            if LOG: PRINT('mem gpu host')
            data = gpu(Name, Type, Size, Step)
            np.save(f'mem/{Name}.npy', data) 
            return data
        else:
            if LOG: PRINT('mem cpu')
            data = cpu(Name, Type, Size)
            np.save(f'mem/{Name}.npy', data) 
            return data
        
    if LOG: PRINT('mem gpu device')
    data = gpu(Name, Type, Size, Step)
    np.save(f'mem/{Name}.npy', data) 
    return data

'''
#------------------------------------------------------------------------
Credit balance is too low
unset ANTHROPIC_API_KEY
echo "[$ANTHROPIC_API_KEY]"
/login "Claude account with subscription"
/status
/usage

#------------------------------------------------------------------------
Jul 15 2026:

-exec source /home/roots/mem/pp.py

import os
import sys
import importlib

mem_dir = os.path.abspath('/home/roots/mem')
if mem_dir not in sys.path: sys.path.insert(0, mem_dir)

import mem
importlib.reload(mem)

#from mem import cpu, gpu, imtool, plot, addr
from mem import*

addr('A')
img = cpu('inputImg', 'uc', [480, 640])
imtool(img)

#------------------------------------------------------------------------
Jul 16 2026:

1)
~/.vscode/extensions

extension.js
package.json

node --version
npm --version

sudo npm install -g @vscode/vsce

bash install.sh

vsce package --allow-missing-repository --skip-license
code --uninstall-extension local.f8comma
code --install-extension f8comma-0.0.1.vsix

Or:
Ctrl + Shit + P
Extensions: Install from VSIX...

2)
/home/roots/.config/Code/User/keybindings.json

    {
    	"key": "f7",
    	"command": "editor.debug.action.selectionToRepl",
    	"when": "editorHasSelection && inDebugMode"
    },
    {
        "key": "f8",
        "command": "f8run.comma",
        "when": "editorTextFocus && inDebugMode"
    }

3)
Ctrl + Shift + P
Reload Window

Or:
Ctrl + Shift + P
Extension Development Host

#------------------------------------------------------------------------
'''
