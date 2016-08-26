



import labrad
import time
import numpy as np
import os

cxn = labrad.connect()

dac = cxn.dac_server



for k in np.linspace(-0.2, 0.6, 10):

	print 'Voltage: ' + str(k)

	mv = dac.get_multipole_values()
	

	time.sleep(2)

	# make dictionary out of tupel list
	mv_dict = {}
	[mv_dict.update({n:v}) for n,v in mv]

	mv_dict['Ez'] = k

	dac.set_multipole_values(mv_dict.items())

	print mv

	time.sleep(1)

	os.system('python ../experiments/FFT/fft_spectrum.py')


