import numpy as np
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from RabiFlopping import RabiFlopping
from sqip.scripts.experiments.CalibrationScans.fitters import rate_from_flops_fitter
import math



class flop(RabiFlopping):

	scannable_params = {
        'RabiFlopping.duration':  [(0., 200., 10., 'us'), 'rabi'],
        				}


	@classmethod
	def run_finally(cls, cxn, parameter_dict, data, data_x):
		data = data.sum(1) ##'1' takes data from first ion. Only needs to be altered if working with multiple ions
		ex=data
		t=data_x

		trap_freq = parameter_dict.TrapFrequencies.axial_frequency['Hz']  
		heat_time = parameter_dict.Heating.background_heating_time 

		fitter = rate_from_flops_fitter()

		if heat_time == 0:
			global time_2pi
			# time_2pi = fitter.calc_2pitime(t,ex)
			time_2pi = 20

		excitation_scaling = 0.99
		sideband_order=1
		nbar,nbarerr,time_2pi,excitation_scaling = fitter.fit_single_flop(heat_time,t,ex,trap_freq,time_2pi,excitation_scaling,sideband_order)
		print "time, pitime:"
		print heat_time, time_2pi 
		if math.isnan(nbarerr):
			nbar=0
			nbarerr=0

		return nbar,nbarerr



class Heating_Rate_BlueRabi(pulse_sequence):

	scannable_params = {'Heating.background_heating_time': [(0., 5., 1, 'ms'), 'heatingrate']}

	sequence = flop