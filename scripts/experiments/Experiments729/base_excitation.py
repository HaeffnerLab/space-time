from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm
from space_time.scripts.experiments.Camera.ion_state_detector import ion_state_detector
from labrad.units import WithUnit
import numpy
import time
       
class base_excitation(experiment):
    name = ''  
    excitation_required_parameters = [
                            ('OpticalPumping','frequency_selection'),
                            ('OpticalPumping','manual_frequency_729'),
                            ('OpticalPumping','line_selection'),
                            
                            ('OpticalPumpingAux','aux_op_line_selection'),
                            ('OpticalPumpingAux','aux_op_enable'),
                            
                            ('SidebandCooling','frequency_selection'),
                            ('SidebandCooling','manual_frequency_729'),
                            ('SidebandCooling','line_selection'),
                            ('SidebandCooling','sideband_selection'),
                            
                            ('SequentialSBCooling', 'stage2_sideband_selection'),
                            ('SequentialSBCooling', 'stage3_sideband_selection'),
                            ('SequentialSBCooling', 'stage4_sideband_selection'),
                            ('SequentialSBCooling', 'stage5_sideband_selection'),

                            ('RotationalPumping','frequency_selection'),
                            ('RotationalPumping','manual_frequency_729'),
                            ('RotationalPumping','line_selection'),
                            ('RotationalPumping','sideband_selection'),

                            ('ScrambleGroundState','frequency_selection'),
                            ('ScrambleGroundState','manual_frequency_729'),
                            ('ScrambleGroundState','line_selection'),

                            ('TrapFrequencies','rotation_frequency'),
                            ('TrapFrequencies','axial_frequency'),
                            ('TrapFrequencies','radial_frequency_1'),
                            ('TrapFrequencies','radial_frequency_2'),
                            ('TrapFrequencies','rf_drive_frequency'),
                            ('StateReadout', 'repeat_each_measurement'),
                            ('StateReadout', 'state_readout_threshold'),

                            ('StateReadout', 'use_camera_for_readout'),
                            #('StateReadout', 'state_readout_duration'),
                            ('StateReadout', 'pmt_readout_duration'),
                            ('StateReadout', 'camera_readout_duration'),
                            ('StateReadout', 'excitation_prob'),
                            ('StateReadout', 'pmt_mode'),
                            ('StateReadout', 'threshold_list'),
                            
                            ('IonsOnCamera','ion_number'),
                            ('IonsOnCamera','vertical_min'),
                            ('IonsOnCamera','vertical_max'),
                            ('IonsOnCamera','vertical_bin'),
                            ('IonsOnCamera','horizontal_min'),
                            ('IonsOnCamera','horizontal_max'),
                            ('IonsOnCamera','horizontal_bin'),
                            
                            ('IonsOnCamera','fit_amplitude'),
                            ('IonsOnCamera','fit_background_level'),
                            ('IonsOnCamera','fit_center_horizontal'),
                            ('IonsOnCamera','fit_center_vertical'),
                            ('IonsOnCamera','fit_rotation_angle'),
                            ('IonsOnCamera','fit_sigma'),
                            ('IonsOnCamera','fit_spacing'),
                           ]
    pulse_sequence = None
    
    @classmethod
    def all_required_parameters(cls):
        params = set(cls.excitation_required_parameters)
        params = params.union(set(cls.pulse_sequence.all_required_parameters()))
        params = list(params)
        params.remove(('OpticalPumping', 'optical_pumping_frequency_729'))
        params.remove(('SidebandCooling', 'sideband_cooling_frequency_729'))
        params.remove(('SequentialSBCooling', 'stage2_frequency_729'))
        params.remove(('SequentialSBCooling', 'stage3_frequency_729'))
        params.remove(('SequentialSBCooling', 'stage4_frequency_729'))
        params.remove(('SequentialSBCooling', 'stage5_frequency_729'))
        #params.remove(('RotationalPumping','rotational_pumping_frequency_729'))
        params.remove(('ScrambleGroundState','excitation_frequency'))
        params.remove(('OpticalPumpingAux', 'aux_optical_frequency_729'))
        params.remove(('StateReadout', 'state_readout_duration'))
        #params.remove(('SequentialSBCooling', 'frequency'))
        return params
    
    def initialize(self, cxn, context, ident, use_camera_override=None):
        self.pulser = cxn.pulser
        self.drift_tracker = cxn.sd_tracker
        self.dv = cxn.data_vault
        self.total_readouts = []
        self.readout_save_context = cxn.context()
        self.histogram_save_context = cxn.context()
        self.readout_save_iteration = 0
        
        self.use_camera = self.parameters.StateReadout.use_camera_for_readout
        self.excitation_prob = self.parameters.StateReadout.excitation_prob
        
        self.setup_sequence_parameters()
        self.setup_initial_switches()
        self.setup_data_vault()
        if use_camera_override != None:
            self.use_camera=use_camera_override
        if self.use_camera:
            self.initialize_camera(cxn)

        self.plotted_seq = False
            
    def initialize_camera(self, cxn):
        self.total_camera_confidences = []
        p = self.parameters.IonsOnCamera
        from lmfit import Parameters as lmfit_Parameters
        self.camera = cxn.andor_server
        self.fitter = ion_state_detector(int(p.ion_number))
        self.camera_initially_live_display = self.camera.is_live_display_running()
        self.camera.abort_acquisition()
        self.initial_exposure = self.camera.get_exposure_time()
        exposure = self.parameters.StateReadout.state_readout_duration
        self.camera.set_exposure_time(exposure)
        self.initial_region = self.camera.get_image_region()
        self.image_region = [
                             int(p.horizontal_bin),
                             int(p.vertical_bin),
                             int(p.horizontal_min),
                             int(p.horizontal_max),
                             int(p.vertical_min),
                             int(p.vertical_max),
                             ]
        self.fit_parameters = lmfit_Parameters()
        self.fit_parameters.add('ion_number', value = int(p.ion_number))
        self.fit_parameters.add('background_level', value = p.fit_background_level)
        self.fit_parameters.add('amplitude', value = p.fit_amplitude)
        self.fit_parameters.add('rotation_angle', p.fit_rotation_angle)
        self.fit_parameters.add('center_x', value = p.fit_center_horizontal)
        self.fit_parameters.add('center_y', value = p.fit_center_vertical)
        self.fit_parameters.add('spacing', value = p.fit_spacing)
        self.fit_parameters.add('sigma', value = p.fit_sigma)
        x_axis = numpy.arange(self.image_region[2], self.image_region[3] + 1, self.image_region[0])
        y_axis = numpy.arange(self.image_region[4], self.image_region[5] + 1, self.image_region[1])
        xx,yy = numpy.meshgrid(x_axis, y_axis)
        self.fitter.set_fitted_parameters(self.fit_parameters, xx, yy)
        self.camera.set_image_region(*self.image_region)
        self.camera.set_acquisition_mode('Kinetics')
        self.initial_trigger_mode = self.camera.get_trigger_mode()
        self.camera.set_trigger_mode('External')
        
    def setup_data_vault(self):
        localtime = time.localtime()
        self.datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
        self.save_directory = ['','Experiments']
        self.save_directory.extend([self.name])
        self.save_directory.extend(dirappend)
        self.dv.cd(self.save_directory ,True, context = self.readout_save_context)
        self.dv.new('Readout {}'.format(self.datasetNameAppend),[('Iteration', 'Arb')],[('Readout Counts','Arb','Arb')], context = self.readout_save_context)        
    
    def setup_sequence_parameters(self):
        op = self.parameters.OpticalPumping
        sp = self.parameters.StatePreparation

        optical_pumping_frequency = cm.frequency_from_line_selection(op.frequency_selection, op.manual_frequency_729, op.line_selection, self.drift_tracker)#, sp.optical_pumping_enable)
        self.parameters['OpticalPumping.optical_pumping_frequency_729'] = optical_pumping_frequency

        aux = self.parameters.OpticalPumpingAux
        aux_optical_pumping_frequency = cm.frequency_from_line_selection('auto', WithUnit(0,'MHz'),  aux.aux_op_line_selection, self.drift_tracker, aux.aux_op_enable)
        self.parameters['OpticalPumpingAux.aux_optical_frequency_729'] = aux_optical_pumping_frequency

        sc = self.parameters.SidebandCooling
        sideband_cooling_frequency = cm.frequency_from_line_selection(sc.frequency_selection, sc.manual_frequency_729, sc.line_selection, self.drift_tracker)#, sp.sideband_cooling_enable)
        trap = self.parameters.TrapFrequencies
        if sc.frequency_selection == 'auto': 
            #trap = self.parameters.TrapFrequencies
            sideband_cooling_frequency = cm.add_sidebands(sideband_cooling_frequency, sc.sideband_selection, trap)
        self.parameters['SidebandCooling.sideband_cooling_frequency_729'] = sideband_cooling_frequency
        #print "sbc"
        #print sideband_cooling_frequency

        rp = self.parameters.RotationalPumping
        rotational_pumping_frequency = cm.frequency_from_line_selection(rp.frequency_selection, rp.manual_frequency_729, rp.line_selection, self.drift_tracker, sp.rotational_sideband_cooling_enable)
        trap = self.parameters.TrapFrequencies
        if rp.frequency_selection == 'auto': 
            rotational_pumping_frequency = cm.add_sidebands(rotational_pumping_frequency, rp.sideband_selection, trap)
        self.parameters['RotationalPumping.rotational_pumping_frequency_729'] = rotational_pumping_frequency

        sc2 = self.parameters.SequentialSBCooling
        sc2freq = cm.frequency_from_line_selection(sc.frequency_selection, sc.manual_frequency_729, sc.line_selection, self.drift_tracker, sp.sideband_cooling_enable)
        stage2_freq = cm.add_sidebands(sc2freq, sc2.stage2_sideband_selection, trap)
        stage3_freq = cm.add_sidebands(sc2freq, sc2.stage3_sideband_selection, trap)
        stage4_freq = cm.add_sidebands(sc2freq, sc2.stage4_sideband_selection, trap)
        stage5_freq = cm.add_sidebands(sc2freq, sc2.stage5_sideband_selection, trap)
        self.parameters['SequentialSBCooling.stage2_frequency_729'] = stage2_freq
        self.parameters['SequentialSBCooling.stage3_frequency_729'] = stage3_freq
        self.parameters['SequentialSBCooling.stage4_frequency_729'] = stage4_freq
        self.parameters['SequentialSBCooling.stage5_frequency_729'] = stage5_freq

        sgs = self.parameters.ScrambleGroundState
        scramble_frequency = cm.frequency_from_line_selection(sgs.frequency_selection, sgs.manual_frequency_729, sgs.line_selection, self.drift_tracker, sp.scramble_ground_state_enable)   
        self.parameters['ScrambleGroundState.excitation_frequency'] = scramble_frequency

        # set state readout time
        if self.use_camera:
            self.parameters['StateReadout.state_readout_duration'] = self.parameters.StateReadout.camera_readout_duration
        else:
            self.parameters['StateReadout.state_readout_duration'] = self.parameters.StateReadout.pmt_readout_duration
    
    def setup_initial_switches(self):
        #self.pulser.switch_manual('crystallization',  False)
        #switch off 729 at the beginning
        self.pulser.output('729horiz', False)
        self.pulser.output('729vert', False)
    
    def plot_current_sequence(self, cxn):
        from common.okfpgaservers.pulser.pulse_sequences.plot_sequence import SequencePlotter
        dds = cxn.pulser.human_readable_dds()
        ttl = cxn.pulser.human_readable_ttl()
        channels = cxn.pulser.get_channels()
        sp = SequencePlotter(ttl, dds.aslist, channels)
        sp.makePlot()
        
    def run(self, cxn, context):
        # set state readout time
        if self.use_camera:
            self.parameters['StateReadout.state_readout_duration'] = self.parameters.StateReadout.camera_readout_duration
        else:
            self.parameters['StateReadout.state_readout_duration'] = self.parameters.StateReadout.pmt_readout_duration
        threshold = int(self.parameters.StateReadout.state_readout_threshold)
        
        self.pmt_mode = self.parameters.StateReadout.pmt_mode
        
        repetitions = int(self.parameters.StateReadout.repeat_each_measurement)
        pulse_sequence = self.pulse_sequence(self.parameters)
                
        pulse_sequence.programSequence(self.pulser)
        self.use_camera = self.parameters.StateReadout.use_camera_for_readout

        if self.use_camera:
            self.camera.set_number_kinetics(repetitions)
            self.camera.start_acquisition()
            
 
 
        ########################

        #print "test"
        #
        #if self.plotted_seq == False:
        #    self.plot_current_sequence(cxn)
        #    self.plotted_seq = True

        #ttl = cxn.pulser.human_readable_ttl()
        #dds = cxn.pulser.human_readable_dds()

        #for k in ttl:
        #    print k
        #    #print(k + "\n")

        #for k in dds:
        #    print k


        #######################


        self.pulser.start_number(repetitions)
        
        self.pulser.wait_sequence_done()
        
        self.pulser.stop_sequence()


       
        
#original code       
#        if not self.use_camera:
#            #print "not using camera!"
#            #get percentage of the excitation using the PMT threshold
#            readouts = self.pulser.get_readout_counts()
#            
#           
#        
#            self.save_data(readouts)            
#            if len(readouts):
#                perc_excited = numpy.count_nonzero(readouts <= threshold) / float(len(readouts))
#            else:
#                #got no readouts
#                perc_excited = -1.0
 #           
  #          if self.excitation_prob:
   #             ion_state = [perc_excited]
    #        else:
    #            ion_state = [numpy.sum(readouts) / float(len(readouts))]
     #           # print readouts
      #          
       #         
       
#code for multiple ions
        if not self.use_camera:
            #get percentage of the excitation using the PMT threshold
            readouts = self.pulser.get_readout_counts()
            self.save_data(readouts)            
            if len(readouts):
                if self.pmt_mode == 'simple': exci = numpy.count_nonzero(readouts <= threshold) / float(len(readouts))
                if self.pmt_mode == 'number_dark': exci, states = self.count_dark(readouts)
                if self.pmt_mode == 'calc_parity': exci, states = self.calc_parity(readouts)
                if self.pmt_mode == 'exci_and_parity': exci, states = self.exci_and_parity(readouts)
                #print self.pmt_mode
            else:
                #got no readouts
                exci = -1.0
                
                
            if self.excitation_prob:
                ion_state = [exci]
            else:
                ion_state = [numpy.sum(readouts) / float(len(readouts))]
                # print readouts         
                
        
        else:
            #get the percentage of excitation using the camera state readout
            proceed = self.camera.wait_for_kinetic()
            if not proceed:
                self.camera.abort_acquisition()
                
                self.finalize(cxn, context)
                raise Exception ("Did not get all kinetic images from camera")
            images = self.camera.get_acquired_data(repetitions)
            self.camera.abort_acquisition()
            x_pixels = int( (self.image_region[3] - self.image_region[2] + 1.) / (self.image_region[0]) )
            y_pixels = int(self.image_region[5] - self.image_region[4] + 1.) / (self.image_region[1])
            images = numpy.reshape(images, (repetitions, y_pixels, x_pixels))
            readouts, confidences = self.fitter.state_detection(images)
            ion_state = 1 - readouts.mean(axis = 0)
            #useful for debugging, saving the images
#             numpy.save('readout {}'.format(int(time.time())), images)
            self.save_confidences(confidences)
                    
            
        return ion_state, readouts    
    
    @property
    def output_size(self):
        if self.use_camera:
            return int(self.parameters.IonsOnCamera.ion_number)
        else:
            return 1

    def count_dark(self, readouts):
#        import IPython
        thresholds = self.parameters.StateReadout.threshold_list
        thresholds = thresholds[1]
        #thresholds.append(0)
        thresholds = sorted(thresholds)
        #print numpy.array(readouts)
        num_ions = len(thresholds)
        print thresholds
        binned = numpy.histogram(readouts, bins=[0]+thresholds + [5000])[0]
        #IPython.embed()
        #print binned
        N = float(len(readouts))
        binned = binned/N
        print binned, range(num_ions+1)
        mean = (1-numpy.dot(binned, range(num_ions+1))/num_ions) # avg number of excited ions
        return mean, binned

    def calc_parity(self, readouts):
#        import IPython
        thresholds = self.parameters.StateReadout.threshold_list
        thresholds = thresholds[1]
        #thresholds.append(0)
        thresholds = sorted(thresholds)
        #print numpy.array(readouts)
        num_ions = len(thresholds)

        binned = numpy.histogram(readouts, bins=[0]+thresholds + [5000])[0]
        #IPython.embed()
        #print binned
        N = float(len(readouts))
        binned = binned/N
        parity = numpy.dot(binned, [1,-1,1]) #
        return parity, binned

    def exci_and_parity(self, readouts):
        thresholds = self.parameters.StateReadout.threshold_list
        thresholds = thresholds[1]
        #thresholds.append(0)
        thresholds = sorted(thresholds)
        #print numpy.array(readouts)
        num_ions = len(thresholds)
        binned = numpy.histogram(readouts, bins=[0]+thresholds + [5000])[0]
        #IPython.embed()
        #print binned
        N = float(len(readouts))
        binned = binned/N

        mean = (1-numpy.dot(binned, range(num_ions+1))/num_ions) # avg number of excited ions
        parity = numpy.dot(binned, [1,-1,1]) #
        return [mean, parity], binned
    
    
    def finalize(self, cxn, context):
        if self.use_camera:
            #if used the camera, return it to the original settings
            self.camera.set_trigger_mode(self.initial_trigger_mode)
            self.camera.set_exposure_time(self.initial_exposure)
            self.camera.set_image_region(self.initial_region)
            if self.camera_initially_live_display:
                self.camera.start_live_display()

    def save_data(self, readouts):
        #save the current readouts
        iters = numpy.ones_like(readouts) * self.readout_save_iteration
        self.dv.add(numpy.vstack((iters, readouts)).transpose(), context = self.readout_save_context)
        self.readout_save_iteration += 1
        self.total_readouts.extend(readouts)
        if (len(self.total_readouts) >= 500):
            hist, bins = numpy.histogram(self.total_readouts, 50)
            self.dv.cd(self.save_directory ,True, context = self.histogram_save_context)
            self.dv.new('Histogram {}'.format(self.datasetNameAppend),[('Counts', 'Arb')],[('Occurence','Arb','Arb')], context = self.histogram_save_context )
            self.dv.add(numpy.vstack((bins[0:-1],hist)).transpose(), context = self.histogram_save_context )
            self.dv.add_parameter('Histogram729', True, context = self.histogram_save_context )
            self.total_readouts = []
    
    def save_confidences(self, confidences):
        '''
        saves confidences readings for the camera state detection
        '''
        self.total_camera_confidences.extend(confidences)
        if (len(self.total_camera_confidences) >= 300):
            hist, bins = numpy.histogram(self.total_camera_confidences, 30)
            self.dv.cd(self.save_directory ,True, context = self.histogram_save_context)
            self.dv.new('Histogram Camera {}'.format(self.datasetNameAppend),[('Counts', 'Arb')],[('Occurence','Arb','Arb')], context = self.histogram_save_context )
            self.dv.add(numpy.vstack((bins[0:-1],hist)).transpose(), context = self.histogram_save_context )
            self.dv.add_parameter('HistogramCameraConfidence', True, context = self.histogram_save_context )
            self.total_camera_confidences = []
