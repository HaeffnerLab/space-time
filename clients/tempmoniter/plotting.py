import scipy.fftpack as fp
import numpy as np
from matplotlib import pyplot as plt
from StringIO import StringIO
f = open('20140309spacetime_openanglevalve','r')
R = f.read()

TIME = np.genfromtxt(StringIO(R), delimiter="_")[:,1]
hour = (TIME - np.mod(TIME,10000))*1e-4
minute = (TIME - hour*1e4 - np.mod(TIME, 100))*1e-2
second = TIME - hour*1e4 - minute*1e2

elapsedtime = hour*3600 + minute*60 + second


temp = np.genfromtxt(StringIO(R), delimiter=" ")[:,0]

press = np.genfromtxt(StringIO(R), delimiter=" ")[:,1]*1e3

elapsedtime = (elapsedtime- elapsedtime[0])/3600

plt.subplot(2,1,1)
plt.plot(elapsedtime, press)
plt.xlabel('Elapsed Time (hours)')
plt.ylabel('Ion pump voltage (mV)')
 
plt.subplot(2,1,2)
plt.plot(elapsedtime, temp, 'r')
plt.xlabel('Elapsed Time (hours)')
plt.ylabel(r'Temperature $^\circ$(C)')

pressfft = np.fft.fft(press)
pressfft = np.abs(pressfft)**2
x = fp.fftfreq(press.size,1)

plt.subplot(4,1,3)
plt.plot(x[1:press.size/130],pressfft[1:press.size/130])
plt.xlabel('Frequency (Hz)')

#tempfft = np.fft.fft(temp)
#tempfft = np.abs(tempfft)**2
#x = fp.fftfreq(temp.size,1)

#plt.subplot(4,1,4)
#plt.plot(x[1:temp.size/130],20*np.log(tempfft[1:temp.size/130]),'r')
#plt.xlabel('Frequency (Hz)')
plt.gcf().subplots_adjust(bottom=0.05)

plt.show()

