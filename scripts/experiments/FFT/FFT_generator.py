import numpy as np
import matplotlib.pyplot as plt

def split_array(tags,split_time):
    istart=0
    time_arrays = []
    i = 1
    for el in tags:
        if el > i*split_time:
            iend=tags.index(el)
            subarray = tags[istart:iend]
            time_arrays.append(subarray)
            istart = iend
            i += 1
    return time_arrays 

tagfile = '/home/space-time/LabRAD/common/abstractdevices/script_scanner/tags.csv'   
## compute relivent frequencies
startfreq = 0 #Hz
stopfreq = 20
record_time = 10. #s
freq_resolution = 1. #Hz
record_time_limit = 1/(4*freq_resolution)
averages = record_time / record_time_limit

freqs = []
for i in range(startfreq,stopfreq,int(freq_resolution)):
    freqs.append(float(i))

tags = np.genfromtxt(tagfile,delimiter=",")
times=[]
for el in tags:
    times.append(el)




tag_arrays = split_array(times,record_time_limit)


pwr = np.zeros_like(freqs)
for el in tag_arrays:

    mat = np.exp(-1.j*2.0*np.pi*np.outer(freqs, el))
    fft = mat.sum(axis=1)
    pwr += np.abs(fft)**2.0 
    del(mat,fft)
    
    
    
    
plt.plot(freqs,pwr)



fft2 = np.fft.fft(times,10**-6)
freq = np.fft.fftfreq(10**-6)
plt.plot(freq,abs(fft2)**2)
print freq
plt.show()

