
import numpy as np

import matplotlib.pylab as plt

from numpy import genfromtxt


#start = 357
#stop = start + 7

#start = 377
#stop = start + 10

start = 387 
stop = start + 10

cut1 = 500
cut2 = 1200
	
y = []

for k in range(start, stop):

	path = '/home/space-time/LabRAD/data/QuickMeasurements.dir/FFT.dir/'

	hlp = genfromtxt(path + '00' + str(k) + ' - FFT.csv', delimiter=',')

	#y = y + [hlp[0:50]]
	y = y + [hlp[cut1:cut2]]

y = np.array(y)

Ez = np.linspace(-0.2, 0.6, stop - start + 1)



d = np.zeros([y.shape[0],y.shape[1]])

for k in range(y.shape[0]):

	d[k] = y[k, :, 1]

xarr = y[0, :, 0]

xarr = xarr - 4.61e6

plt.pcolor(xarr, Ez, d)
plt.colorbar()

#plt.imshow(d)

#plt.axes().set_aspect('equal')

plt.axes().set_aspect(1000.0)
print d

#plt.plot(y[0, :, 0], y[0, :, 1])

plt.show()



