
import numpy as np

print('tensor')

rho = 0.1
t = np.linspace(0, 1, 10)
a = np.sinh(rho * t)
b = np.sinh(rho)
print(a, b)

