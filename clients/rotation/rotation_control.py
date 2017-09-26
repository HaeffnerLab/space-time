from PyQt4 import QtGui, uic, QtCore
import os
from common.clients.connection import connection
from twisted.internet.defer import inlineCallbacks
from common.clients.qtui.QCustomSpinBox import QCustomSpinBox


class TextChangingButton(QtGui.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed""" 
    def __init__(self, parent = None):
        super(TextChangingButton, self).__init__(parent)
        self.setCheckable(False)
        self.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=10))
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        #connect signal for appearance changing
        self.toggled.connect(self.setAppearance)
        self.setAppearance(self.isDown())
    
    def set_value_no_signal(self, down):
        self.blockSignals(True)
        self.setChecked(down)
        self.setAppearance(down)
        self.blockSignals(False)
    
    def setAppearance(self, down):
        if down:
            self.setText('ON')
            self.setPalette(QtGui.QPalette(QtCore.Qt.darkGreen))
        else:
            self.setText('OFF')
            self.setPalette(QtGui.QPalette(QtCore.Qt.black))
    
    def sizeHint(self):
        return QtCore.QSize(37, 26)


class rotation_widget(QtGui.QWidget):
    
    def __init__(self,reactor,cxn = None, parent=None):
        super(rotation_widget, self).__init__(parent)
        self.reactor = reactor
        self.cxn = cxn      
        QtGui.QDialog.__init__(self)
        self.connect()  

    @inlineCallbacks
    def connect(self):
        from labrad.units import WithUnit
        from labrad.types import Error
        self.WithUnit = WithUnit
        self.Error = Error
        #from labrad.wrappers import connectAsync
        #self.cxn = yield connectAsync()
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        self.server = yield self.cxn.get_server('keysight_33500b')

        self.channel_state = 0

        try:
            yield self.set_up_GUI()
        except Exception, e:
            print e
        
        try:
            self.connect_layout()
        except Exception, e:
            print e
            self.setDisabled(True)
    
    @inlineCallbacks       
    def set_up_GUI(self):
        pv = yield self.cxn.get_server('ParameterVault')

        self.frequency = QtGui.QDoubleSpinBox()
        self.frequency.setSuffix(' kHz')
        freq = yield pv.get_parameter('RotationCW','drive_frequency')
        self.frequency.setRange(0.0,1.0e3)
        self.frequency.setValue(freq['kHz'])  
        self.frequency.setDecimals(6)
        self.frequency.setKeyboardTracking(False)

        self.phase = QtGui.QDoubleSpinBox()
        self.phase.setSuffix(' degrees')
        phi = yield pv.get_parameter('RotationCW','start_phase')
        self.phase.setRange(0.0,360.0)
        self.phase.setValue(phi['deg'])
        self.phase.setDecimals(1)
        self.phase.setKeyboardTracking(False)
               
        self.amplitude = QtGui.QDoubleSpinBox()
        self.amplitude.setSuffix(' Vpp')
        amp = yield pv.get_parameter('RotationCW','voltage_pp')
        self.amplitude.setRange(0.0,14.0)
        self.amplitude.setValue(amp['V'])
        self.amplitude.setDecimals(2)
        self.amplitude.setKeyboardTracking(False)
        
        self.state_button = TextChangingButton()
        self.state_button.setCheckable(False)
 
        self.reset_button = QtGui.QPushButton('')
        
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
    
        layout = QtGui.QGridLayout()
        label = QtGui.QLabel("Sinusoid Status")
        layout.addWidget(label, 0, 0)
        layout.addWidget(self.state_button, 0, 1)
        label = QtGui.QLabel("Frequency")
        layout.addWidget(label, 1, 0)
        layout.addWidget(self.frequency, 1, 1)
        label = QtGui.QLabel("Amplitude")
        layout.addWidget(label, 2, 0)
        layout.addWidget(self.amplitude, 2, 1)
        label = QtGui.QLabel("Phase")
        layout.addWidget(label, 3, 0)
        layout.addWidget(self.phase, 3, 1)
        #label = QtGui.QLabel("Reset CW")
        #layout.addWidget(label, 4, 0)
        #layout.addWidget(self.reset_button, 4, 1)

        self.setLayout(layout)
        
    def connect_layout(self):
        self.state_button.pressed.connect(self.toggle_channels)
        self.frequency.valueChanged.connect(self.update_awg)
        self.amplitude.valueChanged.connect(self.update_awg)
        self.phase.valueChanged.connect(self.update_awg)
        # self.state_button.pressed.connect(self.toggle_channels)
        # self.frequency.valueChanged.connect(self.frequency_changed)
        # self.amplitude.valueChanged.connect(self.amplitude_changed)
        # self.phase.valueChanged.connect(self.phase_changed)
        # self.reset_button.pressed.connect(self.reset_to_cw)
    
    @inlineCallbacks   
    def toggle_channels(self):
        #self.server = yield self.cxn.get_server('keysight_33500b')
        try:
            if self.channel_state:
                self.channel_state = 0 
                yield self.server.set_state(1, 0)
                yield self.server.set_state(2, 0)
                self.state_button.setAppearance(0)
            else: 
                self.channel_state = 1 
                yield self.server.set_state(1, 1)
                yield self.server.set_state(2, 1)
                self.state_button.setAppearance(1)
                self.server.update_awg(self.frequency.value()*1e3,self.amplitude.value(),self.phase.value())
            #if self.frequency.value != 0:
                #yield self.server.sync_phases()
        except Exception, e:
                print e
             
    @inlineCallbacks
    def update_awg(self,value):
        pv = yield self.cxn.get_server('ParameterVault')
        try:
            yield pv.set_parameter('RotationCW','drive_frequency',self.WithUnit(self.frequency.value(),'kHz'))
            yield pv.set_parameter('RotationCW','start_phase',self.WithUnit(self.phase.value(),'deg'))
            yield pv.set_parameter('RotationCW','voltage_pp',self.WithUnit(self.amplitude.value(),'V'))
            yield self.server.update_awg(self.frequency.value()*1e3,self.amplitude.value(),self.phase.value())
        except Exception,e:
            print e


    # @inlineCallbacks           
    # def frequency_changed(self, freq):
    #     try:
    #         yield self.server.set_freq(1, freq*1e3)
    #         yield self.server.set_freq(2, freq*1e3)
    #         yield self.server.sync_phases()
    #     except Exception, e:
    #             print e

    # @inlineCallbacks               
    # def amplitude_changed(self, amp):
    #     try:
    #         yield self.server.set_amplitude(1, amp,self.frequency.value())
    #         yield self.server.set_amplitude(2, amp,self.frequency.value())
    #         yield self.server.sync_phases()
    #     except Exception, e:
    #             print e
                
    # @inlineCallbacks   
    # def phase_changed(self, phase):
    #     #val = self.T.Value(freq, 'kHz')
    #     try:
    #         yield self.server.set_phase(1, phase)
    #         yield self.server.set_phase(2, phase+90.)
    #         yield self.server.sync_phases()
    #     except Exception, e:
    #             print e
                
    # @inlineCallbacks
    # def reset_to_cw(self):
    #     if self.frequency.value() != 0.0:
    #         yield self.server.to_sin(1)
    #         yield self.server.to_sin(2)
    #         yield self.amplitude_changed(self.amplitude.value())
    #         yield self.phase_changed(self.phase.value())
    #         yield self.frequency_changed(self.frequency.value())
    #     else:
    #         yield self.server.to_sin(1,self.amplitude.value(),self.phase.value())
    #         yield self.server.to_sin(2,self.amplitude.value(),self.phase.value())
                
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
    rotationwidget = rotation_widget(reactor)
    rotationwidget.show()
    reactor.run()
