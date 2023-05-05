from PyQt4 import QtGui, uic
import os
#from common.clients.connection import connection
from twisted.internet.defer import inlineCallbacks
from labrad.units import WithUnit
import time


class actions_widget(QtGui.QWidget):
    def __init__(self,reactor,cxn = None, parent=None):
        super(actions_widget, self).__init__(parent)
        self.reactor = reactor
        self.cxn = cxn
        QtGui.QDialog.__init__(self)
        self.use_second_397 = False

        #self.second_397_DC_box = QtGui.QCheckBox('Second 397 DC') #used if there are two doppler cooling beams
        #self.second_397_SD_box = QtGui.QCheckBox('Second 397 SD')
        # self.loading_button = QtGui.QPushButton('Loading')
        self.fromload_button = QtGui.QPushButton('From Loading')
    	self.fromdc_button = QtGui.QPushButton('From Doppler Cooling')
    	self.fromstate_button = QtGui.QPushButton('From State Detection')
        self.toload_button = QtGui.QPushButton('To Loading')
    	self.todc_button = QtGui.QPushButton('To Doppler Cooling')
    	self.tostate_button = QtGui.QPushButton('To State Detection')

        self.eject_button = QtGui.QPushButton('EJECT ION')
        #widget_ui.__init__(self)
    
    	#self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
    
    	layout = QtGui.QGridLayout()
    	layout.addWidget(self.fromload_button, 0, 0)
        layout.addWidget(self.toload_button, 0, 1)
    	layout.addWidget(self.fromdc_button, 1, 0)
    	layout.addWidget(self.todc_button, 1, 1)
    	layout.addWidget(self.fromstate_button, 2, 0)
    	layout.addWidget(self.tostate_button, 2, 1)
        layout.addWidget(self.eject_button, 3, 0)
        #layout.addWidget(self.second_397_DC_box, 3, 0) #used if there are two doppler cooling beams
        #layout.addWidget(self.second_397_SD_box, 3, 1)
    
    	self.setLayout(layout)

        self.connect()   
        
        #self.initialize_check_boxes()        
    
    @inlineCallbacks
    def connect(self):
        from labrad.units import WithUnit
        from labrad.types import Error
        self.WithUnit = WithUnit
        self.Error = Error
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            self.connect_layout()
        except Exception, e:
            print e
            self.setDisabled(True)
    
    def connect_layout(self):
        # self.loading_button.pressed.connect(self.loading)
        self.fromload_button.pressed.connect(self.on_from_loading)
        self.fromdc_button.pressed.connect(self.on_from_dc)
        self.fromstate_button.pressed.connect(self.on_from_state)
        self.toload_button.pressed.connect(self.on_to_loading)
        self.todc_button.pressed.connect(self.on_to_dc)
        self.tostate_button.pressed.connect(self.on_to_state)

        self.eject_button.pressed.connect(self.on_eject_ion)
        #self.second_397_DC_box.stateChanged.connect(self.include_second_397_DC) #used if there are two doppler cooling beams   
        #self.second_397_SD_box.stateChanged.connect(self.include_second_397_SD)   
        
    @inlineCallbacks
    def initialize_check_boxes(self):
        pass
        # pv = yield self.cxn.get_server('ParameterVault')
        #DC_state = yield pv.get_parameter(('DopplerCooling','doppler_cooling_include_second_397')) #used if there are two doppler cooling beams
        #SD_state = yield pv.get_parameter(('StateReadout','state_readout_include_second_397'))
        #yield self.second_397_DC_box.setChecked(DC_state)   
        #yield self.second_397_SD_box.setChecked(SD_state)             
    
    # @inlineCallbacks
    # def loading(self):

    #     pulser = yield self.cxn.get_server('Pulser')
    #     ampl397 = self.WithUnit(-5.0, 'dBm')
    #     ampl397DP = self.WithUnit(-7.0, 'dBm')
    #     ampl866 = self.WithUnit(-7.0, 'dBm')
    #     freq397 = self.WithUnit(180.0, 'MHz')
    #     freq397DP = self.WithUnit(183.0, 'MHz')
    #     freq866 = self.WithUnit(80.0, 'MHz')
        
    #     yield pulser.frequency('866DP', freq866)
    #     yield pulser.amplitude('866DP', ampl866)
    #     yield pulser.frequency('397DP', freq397)
    #     yield pulser.amplitude('397DP', ampl397)
    #     yield pulser.frequency('397DP', freq397DP)
    #     yield pulser.amplitude('397DP', ampl397DP)

    #     return

    def on_eject_ion(self):
        # Bring up a window to confirm ion ejection
        w = QtGui.QWidget()
        msg = QtGui.QMessageBox(w)
        msg.setIcon(QtGui.QMessageBox.Warning)
        msg.setWindowTitle("You pressed eject!")
        msg.setText("Are you sure you want to eject the ion(s)?")
        msg.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        yesbutton = msg.button(QtGui.QMessageBox.Yes)
        yesbutton.setText('...Do it.')
        nobutton = msg.button(QtGui.QMessageBox.No)
        nobutton.setText('Nooo!')
	   # If yes, call eject_ion(), defined below, to eject the ion. Otherwise, do nothing.
        result = msg.exec_()
        if result == QtGui.QMessageBox.Yes:
            self.eject_ion()
        else:
            pass

    @inlineCallbacks
    def eject_ion(self):
        linear_397 = '397DP'
        #linear_397 = yield pv.get_parameter(('StatePreparation','channel_397_linear'))
        pulser = yield self.cxn.get_server('Pulser')
        freq397 = yield pulser.frequency(linear_397)

        yield pulser.frequency(linear_397, WithUnit(260.0,'MHz'))
        time.sleep(1)
        yield pulser.frequency(linear_397, freq397)


    @inlineCallbacks
    def on_to_loading(self):
        ss = yield self.cxn.get_server('ScriptScanner')
        linear_397 = '397DP'
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pulser.amplitude(linear_397)
        #ampl397 = yield pulser.amplitude('397DP')
        #ampl397DP = yield pulser.amplitude('397DP')
        ampl866 = yield pulser.amplitude('866DP')
        freq397 = yield pulser.frequency(linear_397)
        #freq397 = yield pulser.frequency('397DP')
        #freq397DP = yield pulser.frequency('397DP')
        freq866 = yield pulser.frequency('866DP')
        #use_second_397_SD = yield pv.get_parameter(('StateReadout','state_readout_include_second_397'))
        yield ss.set_parameter('Loading','loading_amplitude_397',ampl397)
        yield ss.set_parameter('Loading','loading_amplitude_866',ampl866)
        yield ss.set_parameter('Loading','loading_frequency_397',freq397)
        yield ss.set_parameter('Loading','loading_frequency_866',freq866)
        #if use_second_397_SD:   #used if there are two doppler cooling beams
        #    yield pv.set_parameter('StateReadout','state_readout_amplitude_397DP',ampl397DP)
        #    yield pv.set_parameter('StateReadout','state_readout_frequency_397DP',freq397DP)
    
    @inlineCallbacks
    def on_to_state(self):
        ss = yield self.cxn.get_server('ScriptScanner')
        linear_397 = '397DP'
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pulser.amplitude(linear_397)
        #ampl397 = yield pulser.amplitude('397DP')
        #ampl397DP = yield pulser.amplitude('397DP')
        ampl866 = yield pulser.amplitude('866DP')
        freq397 = yield pulser.frequency(linear_397)
        #freq397 = yield pulser.frequency('397DP')
        #freq397DP = yield pulser.frequency('397DP')
        freq866 = yield pulser.frequency('866DP')
        #use_second_397_SD = yield pv.get_parameter(('StateReadout','state_readout_include_second_397'))
        yield ss.set_parameter('StateReadout','state_readout_amplitude_397',ampl397)
        yield ss.set_parameter('StateReadout','state_readout_amplitude_866',ampl866)
        yield ss.set_parameter('StateReadout','state_readout_frequency_397',freq397)
        yield ss.set_parameter('StateReadout','state_readout_frequency_866',freq866)
        #if use_second_397_SD:   #used if there are two doppler cooling beams
        #    yield pv.set_parameter('StateReadout','state_readout_amplitude_397DP',ampl397DP)
        #    yield pv.set_parameter('StateReadout','state_readout_frequency_397DP',freq397DP)
    
    @inlineCallbacks
    def on_to_dc(self):
        ss = yield self.cxn.get_server('ScriptScanner')
        linear_397 = '397DP'
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pulser.amplitude(linear_397)        
        #ampl397 = yield pulser.amplitude('397DP')
        #ampl397DP = yield pulser.amplitude('397DP')
        ampl866 = yield pulser.amplitude('866DP')
        freq397 = yield pulser.frequency(linear_397)       
        #freq397 = yield pulser.frequency('397DP')
        #freq397DP = yield pulser.frequency('397DP')
        freq866 = yield pulser.frequency('866DP')
        #use_second_397_DC = yield pv.get_parameter(('DopplerCooling','doppler_cooling_include_second_397'))
        yield ss.set_parameter('DopplerCooling','doppler_cooling_amplitude_397',ampl397)
        #yield pv.set_parameter('DopplerCooling','doppler_cooling_amplitude_397DP',ampl397DP)
        yield ss.set_parameter('DopplerCooling','doppler_cooling_amplitude_866',ampl866)
        yield ss.set_parameter('DopplerCooling','doppler_cooling_frequency_397',freq397)
        #yield pv.set_parameter('DopplerCooling','doppler_cooling_frequency_397DP',freq397DP)
        yield ss.set_parameter('DopplerCooling','doppler_cooling_frequency_866',freq866)
        #if use_second_397_DC:   #used if there are two doppler cooling beams
        #    yield pv.set_parameter('DopplerCooling','doppler_cooling_amplitude_397DP',ampl397DP)
        #    yield pv.set_parameter('DopplerCooling','doppler_cooling_frequency_397DP',freq397DP)


    @inlineCallbacks
    def on_from_loading(self):
        ss = yield self.cxn.get_server('ScriptScanner')
        linear_397 = '397DP'
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield ss.get_parameter(('Loading','loading_amplitude_397'))
        #ampl397DP = yield pv.get_parameter(('DopplerCooling','doppler_cooling_amplitude_397DP'))
        ampl866 = yield ss.get_parameter(('Loading','loading_amplitude_866'))
        freq397 = yield ss.get_parameter(('Loading','loading_frequency_397'))
        #freq397DP = yield pv.get_parameter(('DopplerCooling','doppler_cooling_frequency_397DP'))
        freq866 = yield ss.get_parameter(('Loading','loading_frequency_866'))
        #doppler_cooling_with_second_397 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_include_second_397'))
        yield pulser.frequency('866DP', freq866)
        yield pulser.amplitude('866DP', ampl866)
        yield pulser.frequency(linear_397, freq397)
        yield pulser.amplitude(linear_397, ampl397)
        #if doppler_cooling_with_second_397: #used if there are two doppler cooling beams
        #    yield pulser.frequency('397DP', freq397DP)
        #    yield pulser.amplitude('397DP', ampl397DP)

        
    @inlineCallbacks
    def on_from_dc(self):
        ss = yield self.cxn.get_server('ScriptScanner')
        linear_397 = '397DP'
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield ss.get_parameter(('DopplerCooling','doppler_cooling_amplitude_397'))
        #ampl397DP = yield pv.get_parameter(('DopplerCooling','doppler_cooling_amplitude_397DP'))
        ampl866 = yield ss.get_parameter(('DopplerCooling','doppler_cooling_amplitude_866'))
        freq397 = yield ss.get_parameter(('DopplerCooling','doppler_cooling_frequency_397'))
        #freq397DP = yield pv.get_parameter(('DopplerCooling','doppler_cooling_frequency_397DP'))
        freq866 = yield ss.get_parameter(('DopplerCooling','doppler_cooling_frequency_866'))
        #doppler_cooling_with_second_397 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_include_second_397'))
        yield pulser.frequency('866DP', freq866)
        yield pulser.amplitude('866DP', ampl866)
        yield pulser.frequency(linear_397, freq397)
        yield pulser.amplitude(linear_397, ampl397)
        #if doppler_cooling_with_second_397: #used if there are two doppler cooling beams
        #    yield pulser.frequency('397DP', freq397DP)
        #    yield pulser.amplitude('397DP', ampl397DP)
    
    @inlineCallbacks
    def on_from_state(self):
        ss = yield self.cxn.get_server('ScriptScanner')
        linear_397 = '397DP'
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield ss.get_parameter(('StateReadout','state_readout_amplitude_397'))
        #ampl397DP = yield pv.get_parameter(('StateReadout','state_readout_amplitude_397DP'))
        ampl866 = yield ss.get_parameter(('StateReadout','state_readout_amplitude_866'))
        freq397 = yield ss.get_parameter(('StateReadout','state_readout_frequency_397'))
        #freq397DP = yield pv.get_parameter(('StateReadout','state_readout_frequency_397DP'))
        freq866 = yield ss.get_parameter(('StateReadout','state_readout_frequency_866'))
        #state_readout_with_second_397 = yield pv.get_parameter(('StateReadout','state_readout_include_second_397'))
        yield pulser.frequency('866DP', freq866)
        yield pulser.amplitude('866DP', ampl866)
        yield pulser.frequency(linear_397, freq397)
        yield pulser.amplitude(linear_397, ampl397)
        #if state_readout_with_second_397: #used if there are two doppler cooling beams
        #    yield pulser.frequency('397DP', freq397DP)
        #    yield pulser.amplitude('397DP', ampl397DP)
        
    #@inlineCallbacks   
    #def include_second_397_DC(self, event):    #used if there are two doppler cooling beams
    #    pv = yield self.cxn.get_server('ParameterVault')
    #    self.use_second_397_DC = yield self.second_397_DC_box.isChecked()
    #    yield pv.set_parameter('DopplerCooling','doppler_cooling_include_second_397', self.use_second_397_DC)
        
    #@inlineCallbacks
    #def include_second_397_SD(self, event):
    #    pv = yield self.cxn.get_server('ParameterVault')
    #    self.use_second_397_SD = yield self.second_397_SD_box.isChecked()
    #    yield pv.set_parameter('StateReadout','state_readout_include_second_397', self.use_second_397_SD)
    
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
    
    def closeEvent(self, x):
        self.reactor.stop()  
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    from common.clients.connection import connection
    from labrad.units import WithUnit
    electrodes = actions_widget(reactor)
    electrodes.show()
    reactor.run()
