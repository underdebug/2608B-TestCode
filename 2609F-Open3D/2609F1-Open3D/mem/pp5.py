
a = mem('a', None, 2)
print('a1 finish', a)

a = mem('a', 'double', 2)
print('a2 finish', a)

print(mem('d_triangles', None, 2))

print(mem('d_nodes', None, 2))


-exec python import sys; sys.path[:0]=["/home/roots/develop/2608B-TestCode-t/2609D-BVH/2609D1-BVH/mem","/home/roots/.vscode/extensions/local.mem-0.0.1"]; import importlib, mem; importlib.reload(mem); from mem import *;
-exec python import sys; sys.path[:0]=["/home/roots/develop/2608B-TestCode-t/2609D-BVH/2609D1-BVH/mem","/home/roots/.vscode/extensions/local.mem-0.0.1"]; import importlib, mem; importlib.reload(mem); from mem import *; 

python exec("print('d_triangles =', mem('d_triangles', None, 12))")

A = gpu('dir', None, 12)
print('A', A)