import numpy as np
import matplotlib.pylab as plt

x_list = np.random.rand(10)
y_list = np.random.rand(10)
plt.plot(x_list, y_list)
plt.savefig('./my.png')