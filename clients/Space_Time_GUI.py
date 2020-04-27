from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks

class SPACETIME_GUI(QtGui.QMainWindow):
    def __init__(self, reactor, clipboard, parent=None):
        super(SPACETIME_GUI, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect_labrad()

    @inlineCallbacks
    def connect_labrad(self):
        from common.clients.connection import connection
        cxn = connection()
        yield cxn.connect()
        self.create_layout(cxn)

    def create_layout(self, cxn):


        centralWidget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout() 

        laser_room = self.makeLaserRoomWidget(reactor, cxn)
        laser_control = self.makeControlWidget(reactor, cxn)
        script_scannerv2 = self.makeScriptControlWidgetv2(reactor, cxn)
        histogram = self.make_histogram_widget(reactor, cxn)
        drift_tracker_global = self.makeDriftTrackerGlobalWidget(reactor, cxn)
        config_editor = self.make_config_editor_widget(reactor, cxn)

        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.addTab(laser_room,'&Laser Room')
        self.tabWidget.addTab(laser_control,'&Control')
        self.tabWidget.addTab(script_scannerv2, '&Script Scanner_v2')
        self.tabWidget.addTab(histogram, '&Readout Histogram')
        self.tabWidget.addTab(drift_tracker_global, '&Drift Tracker Global')
        self.tabWidget.addTab(config_editor, 'Config &Editor')



        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        #self.setWindowTitle('Spacetime GUI')

    def makeScriptControlWidget(self, reactor, cxn):
        widget = QtGui.QWidget()
        
        from common.clients.script_scanner_gui.script_scanner_gui import script_scanner_gui
        gridLayout = QtGui.QGridLayout()
       
        gridLayout.addWidget(script_scanner_gui(reactor))
        
        widget.setLayout(gridLayout)
        return widget

    def makeScriptControlWidgetv2(self, reactor, cxn):
        from common.devel.bum.gui_scriptscanner2.script_scanner_gui import script_scanner_gui
        widget = script_scanner_gui(reactor,cxn)

        return widget

    def makeLaserRoomWidget(self, reactor, cxn):
        widget = QtGui.QWidget()
 

        from common.clients.LASERDAC_CONTROL import DAC_Control as laserdac_control_widget
        from common.clients.multiplexer.MULTIPLEXER_CONTROL import multiplexerWidget
        #from common.clients.InjectionLock_GUI import InjectionLock_Control
        gridLayout = QtGui.QGridLayout()

        gridLayout.addWidget(laserdac_control_widget(reactor),             0,0)
        #gridLayout.addWidget(InjectionLock_Control(reactor),    1,0)
        gridLayout.addWidget(multiplexerWidget(reactor),        0,1)

        widget.setLayout(gridLayout)
        return widget

    def make_histogram_widget(self, reactor, cxn):
        histograms_tab = QtGui.QTabWidget()
        from common.clients.readout_histogram import readout_histogram
        pmt_readout = readout_histogram(reactor, cxn)
        histograms_tab.addTab(pmt_readout, "PMT")
        return histograms_tab
    
    def makeDriftTrackerWidget(self, reactor, cxn):
        dt_tab = QtGui.QTabWidget()
        from common.clients.drift_tracker.drift_tracker import drift_tracker
        tracker = drift_tracker(reactor, cxn)
        dt_tab.addTab(tracker,"Drift Tracker")
        return dt_tab

    def makeDriftTrackerGlobalWidget(self, reactor, cxn):
        dt_tab = QtGui.QTabWidget()
        from common.clients.drift_tracker_global.drift_tracker_global import drift_tracker_global
        tracker = drift_tracker_global(reactor, cxn)
        dt_tab.addTab(tracker,"Drift Tracker Global")
        return dt_tab
 
    def make_config_editor_widget(self, reactor, cxn):
        config_editor_tab = QtGui.QTabWidget()
        from common.clients.CONFIG_EDITOR import CONFIG_EDITOR
        config_editor = CONFIG_EDITOR(reactor, cxn)
        config_editor_tab.addTab(config_editor,"Config Editor")
        return config_editor_tab
       
    
    def makeControlWidget(self, reactor, cxn):
        widget = QtGui.QWidget()

        from common.clients.PMT_CONTROL    import pmtWidget
        from common.clients.SWITCH_CONTROL import switchWidget
        from common.clients.DDS_CONTROL    import DDS_CONTROL
        from ST_DAC_CONTROL import DAC_Control
        from quick_actions.quick_actions import actions_widget
        from rotation.rotation_control import rotation_widget
        from common.clients.LINETRIGGER_CONTROL import linetriggerWidget
        gridLayout = QtGui.QGridLayout()

        gridLayout.addWidget(switchWidget(reactor, cxn),        1,3,1,1)
        gridLayout.addWidget(pmtWidget(reactor),                0,3,1,1)
        gridLayout.addWidget(DDS_CONTROL(reactor, cxn),         0,4,4,2)
        gridLayout.addWidget(actions_widget(reactor, cxn),      3,3,2,1)
        gridLayout.addWidget(rotation_widget(reactor, cxn),     4,3,2,1)
        gridLayout.addWidget(DAC_Control(reactor),              0,0,7,3)
        gridLayout.addWidget(linetriggerWidget(reactor),        2,3,1,1)

        widget.setLayout(gridLayout)
        return widget

    def closeEvent(self, x):
        self.reactor.stop()
        

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    clipboard = a.clipboard()
    import common.clients.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    spacetimeGUI = SPACETIME_GUI(reactor, clipboard)
    spacetimeGUI.setWindowTitle('Space-Time GUI')
    spacetimeGUI.show()
    reactor.run()
