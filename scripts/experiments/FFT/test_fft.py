from processFFT import processFFT
import numpy as np
import matplotlib.pyplot as plt

processor = processFFT()

record_time = 5
freq_span = 500.0
freq_offset = 0.0
center_freq = 100.0

time_resolution = 1.0e-3

freqs = processor.computeFreqDomain( 
        record_time, 
        freq_span,  
        freq_offset, 
        center_freq
        )

timetags = np.linspace(0,5, 1e2)

pwr = processor.getPowerSpectrum(
        freqs, 
        timetags, 
        record_time, 
        time_resolution
        )

print pwr

plt.figure(1)
plt.subplot(2,1,1)
plt.plot(freqs, pwr)

plt.subplot(2,1,2)
plt.plot(timetags, np.ones(len(timetags)), 'o')

plt.show()



