 #!/usr/bin/env python
import labrad
import numpy as np
import time
from space_time.scripts.subsequences.resetDACs import reset_DACs
from treedict import TreeDict

#connect to LabRAD
try:
	cxn = labrad.connect()
except:
	print 'Please start LabRAD Manager'
	time.sleep(10)
	raise()

nodeDict = {
			#'node spacetime-exp-control':
			'node_spacetime_pc':
				['ParameterVault',
				'Pulser',
				'DAC Server', 
				'KEYSIGHT_33500B',
				'KEYSIGHT_33600A',
				'Data Vault', 
				'NormalPMTFlow',
				#'SD Tracker Global', # Turns out since this is running on the laser room computer, this is totally unneccessary!
				'ScriptScanner',
				],
			'node space-time-imaging':
				['GPIB Device Manager',
				'GPIB Bus',
				'Agilent Server',
				'Andor Server'
				]
	}

for node in nodeDict.keys(): #sets the order of opening
	#make sure all node servers are up
	pulser_on=True
	if not node in cxn.servers: print node + ' is not running'
	else:
		print '\n' + 'Working on ' + node + '\n'
		#if node server is up, start all possible servers on it that are not already running
		running_servers = np.asarray(cxn.servers[node].running_servers())
		for server in nodeDict[node]:
			if server in running_servers: 
				print server + ' is already running'
			else:
				print 'starting ' + server
				try:
					cxn.servers[node].start(server)
				except:
					print 'ERROR with ' + server
					if server == 'Pulser':
						pulser_on = False

#initialize DAC into correct set number after random startup flashes from advance trigger from the pulser
if pulser_on:
	parameters = TreeDict()
	pulser = cxn.pulser
	pulse_sequence = reset_DACs(parameters)										
	pulse_sequence.programSequence(pulser)
	pulser.start_number(1)
	pulser.wait_sequence_done()
	pulser.stop_sequence()



#time.sleep(10)

