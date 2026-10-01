
# Outside the kernel: stop in main after cudaMemcpy(d_triangles, ...)
# and before cudaFree(d_triangles). Size counts Triangle objects (two).
# Inside traceKernel or traverseBVH: the same pointer is named triangles.

triangle_name = 'd_triangles'
d_triangles = mem(triangle_name, None, 2)
print('d_triangles', d_triangles)
