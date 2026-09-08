# Dumps the kriging matrix A before and after invertMatrix() so
# mem/06.A_Ainv.py can verify A @ Ainv == I.
# Run from the project root: cuda-gdb -q -batch -x mem/06.dump_A.gdb ./test
source mem/mem.py
break main.cu:324
break main.cu:330
run
python data = mem('A', 'd', [121]); import numpy as np; np.save('mem/data/A_orig.npy', data)
continue
python mem('A', 'd', [121])
quit
