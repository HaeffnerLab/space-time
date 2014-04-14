from pylab import *
import labrad
import numpy as np
from twisted.internet.defer import inlineCallbacks

class(file, dir):
   
    @inlineCallbacks
    def __init__(self):
        cxn = labrad.connect()
        dv = cxn.data_vault
        dv.cd ['',dir]
        dv.open(file)
        self.data = np.array(dv.get())
        
    def get_plot(self,self.data):
        x = self.data[:,0]
        y = self.data[:,1]
        self.wikiplot = plot(x,y)
        return self.wikiplot 

