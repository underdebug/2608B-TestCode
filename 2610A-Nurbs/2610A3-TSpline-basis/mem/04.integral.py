import numpy as np
from scipy.integrate import cumulative_trapezoid

x = np.array([0, 1, 2])
z = x ** 2

integral = cumulative_trapezoid(z, x, initial=0)
print('integral', integral)

x = np.array([1, 2, 3])
z = x ** 2 + 1

integral = cumulative_trapezoid(z, x, initial=0)
print('integral', integral)

