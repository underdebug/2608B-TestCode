import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

print(plt.get_backend())    
print(plt.isinteractive()) 

data = np.load('query.npy')
print(data.shape)        

x, y = data[:, 0], data[:, 1]

plt.figure()
plt.plot(x, y, 'b.')
plt.axis('equal')          
plt.show(block=True)

