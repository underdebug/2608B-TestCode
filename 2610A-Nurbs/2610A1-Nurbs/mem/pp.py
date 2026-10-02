
#----------------------------------------------------------------------
# do not delete start
#----------------------------------------------------------------------

import os
import numpy as np

if "PATH" in globals():
    SavePath = PATH
    print('Path in globals()', os.path.abspath(SavePath))
else:
    SavePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_t')
    os.makedirs(SavePath, exist_ok=True) 
    print('Path not in globals()', os.path.abspath(SavePath))    

    def mem(Name, Type=None, Size=None, Step=1):
        return np.load(f'data/{Name}.npy')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# do not delete end
#----------------------------------------------------------------------

x = mem('x', None, None)
X = mem('X', None, None)

x1 = x[0::2]
y1 = x[1::2]

x2 = X[0::2]
y2 = X[1::2]

plt.figure()
plt.plot(x1, y1, 'b.-')
plt.plot(x2, y2, 'r.-')

#----------------------------------------------------------------------
# do not delete start
#----------------------------------------------------------------------

file = f'{SavePath}/01.main.png';
plt.savefig(file, dpi=300, bbox_inches='tight')

print(os.path.abspath(file))

import subprocess
subprocess.run(['xdg-open', file], stderr=subprocess.DEVNULL)

# do not delete end
#----------------------------------------------------------------------