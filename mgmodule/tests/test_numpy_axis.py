import numpy as np

a = np.ones([5,4,3])
b = np.mean(a,axis=1)

print(b.shape)